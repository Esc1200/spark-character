"""Continuous Telegram-grounded auto-improvement loop.

Watches a Spark Intelligence Builder home for new outbound replies. When
enough new live replies have accumulated, runs a multi-tier evolution
cycle seeded from production failures and ships the winner if one beats
the active baseline. Designed to keep Spark's voice improving from real
conversations without manual triggers.

Run continuously (e.g. on a long-running console or as a Windows
scheduled task pointing at a python -u shim):

    python -u evals/auto_loop.py \\
        --sib-home "C:/Users/USER/Desktop/spark-intelligence-builder/.tmp-home-live-telegram-real" \\
        --interval-seconds 1800 \\
        --new-replies-threshold 25 \\
        --candidates 3 \\
        --weights 0.2,0.5,0.3

A single check:

    python evals/auto_loop.py --once ...

The loop never deletes or rolls back. Each promoted candidate becomes
persona.v(N+1).md and persona.latest.txt is updated to point at it.
v1 is preserved for diff or manual rollback.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "src"))

from spark_character import AuditMiner  # noqa: E402
from spark_character.persona import resolve_latest_persona_version  # noqa: E402


STATE_FILE_DEFAULT = Path("evals/_auto_loop_state.json")


def _load_state(path: Path) -> dict:
    if not path.exists():
        return {"last_evolved_at": 0, "last_audit_count": 0, "last_persona_version": None}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"last_evolved_at": 0, "last_audit_count": 0, "last_persona_version": None}


def _save_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")


def count_llm_replies(sib_home: str) -> int:
    miner = AuditMiner.from_sib_home(sib_home)
    findings = miner.recent_findings(limit=10_000)
    return findings.llm_rows


def run_evolve_cycle(args, repo_root: Path) -> tuple[bool, str]:
    """Run evolve_persona.py as a subprocess. Return (promoted, log_tail)."""
    cmd = [
        sys.executable, "-u",
        str(repo_root / "evals" / "evolve_persona.py"),
        "--candidates", str(args.candidates),
        "--weights", args.weights,
        "--sib-home", args.sib_home,
        "--audit-limit", str(args.audit_limit),
    ]
    if args.dry_run:
        cmd.append("--dry-run")
    print(f"\n[auto_loop] firing evolve cycle: {' '.join(cmd)}", flush=True)
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=repo_root, timeout=args.evolve_timeout)
    log_tail = (result.stdout or "")[-4000:]
    if result.returncode != 0:
        print("[auto_loop] evolve subprocess returned non-zero")
        print(log_tail)
        return False, log_tail
    print(log_tail)
    promoted = "PROMOTED:" in result.stdout
    return promoted, log_tail


def maybe_refresh_consumers(args) -> None:
    if not args.consumer_pythons:
        return
    pythons = [p.strip() for p in args.consumer_pythons.split(",") if p.strip()]
    pkg_url = "git+https://github.com/vibeforge1111/spark-character.git@master"
    for py in pythons:
        try:
            print(f"[auto_loop] refreshing consumer: {py}", flush=True)
            subprocess.run(
                [py, "-m", "pip", "install", "--upgrade", "--force-reinstall", "--no-deps", pkg_url, "-q"],
                check=False,
                timeout=180,
            )
        except Exception as exc:
            print(f"[auto_loop] consumer refresh failed for {py}: {exc}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sib-home", required=True)
    parser.add_argument("--interval-seconds", type=int, default=1800)
    parser.add_argument("--new-replies-threshold", type=int, default=25)
    parser.add_argument("--candidates", type=int, default=3)
    parser.add_argument("--weights", default="0.2,0.5,0.3")
    parser.add_argument("--audit-limit", type=int, default=200)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--once", action="store_true", help="Run a single check then exit")
    parser.add_argument("--state-file", default=str(STATE_FILE_DEFAULT))
    parser.add_argument("--evolve-timeout", type=int, default=2400)
    parser.add_argument(
        "--consumer-pythons",
        default="",
        help="Comma-separated python interpreters to force-refresh "
        "spark-character on after a promotion (e.g. system Python + spark-cli venv). "
        "Each one runs pip install --force-reinstall against this repo's master.",
    )
    args = parser.parse_args()

    state_path = Path(args.state_file)
    repo_root = _REPO_ROOT

    while True:
        try:
            state = _load_state(state_path)
            current = count_llm_replies(args.sib_home)
            new_replies = current - state.get("last_audit_count", 0)
            active = resolve_latest_persona_version()
            print(
                f"[auto_loop] {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} "
                f"sib_home={args.sib_home} active={active} "
                f"audit_total={current} new_since_last={new_replies} "
                f"threshold={args.new_replies_threshold}",
                flush=True,
            )
            should_fire = new_replies >= args.new_replies_threshold or state.get("last_audit_count", 0) == 0
            if should_fire:
                promoted, _log = run_evolve_cycle(args, repo_root)
                state["last_evolved_at"] = int(time.time())
                state["last_audit_count"] = current
                state["last_persona_version"] = resolve_latest_persona_version()
                _save_state(state_path, state)
                if promoted:
                    print(f"[auto_loop] promoted to {state['last_persona_version']}")
                    maybe_refresh_consumers(args)
                else:
                    print("[auto_loop] no promotion this cycle")
            else:
                print("[auto_loop] threshold not met, skipping")
            if args.once:
                return 0
            time.sleep(max(60, args.interval_seconds))
        except KeyboardInterrupt:
            print("[auto_loop] interrupted by operator")
            return 0
        except Exception as exc:
            print(f"[auto_loop] error: {exc}", flush=True)
            if args.once:
                return 1
            time.sleep(60)


if __name__ == "__main__":
    sys.exit(main())

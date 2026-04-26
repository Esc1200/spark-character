# Security

`spark-character` supplies persona, provider, and scoring artifacts that can affect every Spark reply. Treat persona files, overlays, provider settings, and evolution outputs as prompt-boundary material.

## Launch Boundaries

- Does not own Telegram ingress.
- Does not own Spawner mission execution.
- Does not store live user secrets.
- May read production audit logs only when explicitly pointed at a Builder home for eval/evolution.
- Should be consumed by Builder through a pinned dependency or registry pin, never a floating branch ref.

## Secrets

Never commit:

- `.env`, `.env.*`
- provider API keys
- raw production prompts or audit logs
- private user memory/state exports
- generated evolution traces containing private conversation text

Provider base URLs must be HTTPS and must point to known provider hosts. Do not use environment-configured base URLs as a way to route prompts to arbitrary endpoints.

## Persona Artifact Rules

- `persona.latest.txt` is the active pointer. Pointer changes must be reviewable.
- Persona, critic, overlay, and voice-corpus artifacts are prompt inputs. Review them like code.
- Do not ship composite weakness scores or eval internals in public artifacts when they would help attackers target weak tiers.
- Do not auto-promote evolved personas without a regression gate and a human-visible diff.

## Eval And Evolution Safety

- Continuous evolution must stay opt-in.
- Production-grounded evals must redact secrets and avoid committing extracted conversation text.
- T11 sustained-attack work is planned but not required for normal launch operation.
- Provider comparisons should record provider names and scores, not raw keys or private request payloads.

## Verification

Before publishing or repinning this repo:

```bash
python -m pytest tests -q
```

If persona artifacts changed, also run the relevant eval or probe that exercises the changed tier and inspect the artifact diff manually.

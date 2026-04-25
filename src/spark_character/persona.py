"""Persona spec loading.

The persona is a markdown artifact under artifacts/. The harness mutates
that file to evolve voice; everything else reads from it.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ARTIFACTS_DIR = Path(__file__).parent / "artifacts"
OVERLAYS_DIR = ARTIFACTS_DIR / "overlays"
LATEST_POINTER = ARTIFACTS_DIR / "persona.latest.txt"
DEFAULT_PERSONA_VERSION = "v1"


@dataclass(frozen=True)
class PersonaSpec:
    version: str
    text: str
    overlay_kind: str | None = None

    @property
    def system_prompt(self) -> str:
        return self.text.strip()


def load_overlay(provider_kind: str | None) -> str:
    """Return the overlay markdown for a given backend kind, or '' if
    none is configured. Provider kinds: 'zai', 'minimax', 'codex',
    'openai', 'ollama'. Unknown kinds return ''."""
    if not provider_kind:
        return ""
    path = OVERLAYS_DIR / f"{provider_kind.lower().strip()}.md"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def load_surface_overlay(surface: str | None) -> str:
    """Return the overlay markdown for a given surface, or '' if none
    is configured. Surfaces: 'voice', 'browser_extension', 'telegram',
    'tui', 'cli'. Unknown surfaces return ''."""
    if not surface:
        return ""
    path = OVERLAYS_DIR / "surface" / f"{surface.lower().strip()}.md"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def detect_provider_kind(provider) -> str | None:
    """Heuristic: classify a ProviderSpec or CodexSpec into a kind
    string for overlay lookup. Returns None when uncertain."""
    base = (getattr(provider, "base_url", "") or "").lower()
    if "codex-cli" in base:
        return "codex"
    if "z.ai" in base or "zhipuai" in base or "bigmodel" in base:
        return "zai"
    if "minimax" in base:
        return "minimax"
    if "openai.com" in base:
        return "openai"
    if "localhost" in base or "127.0.0.1" in base or "ollama" in base:
        return "ollama"
    return None


def resolve_latest_persona_version() -> str:
    """Resolve which persona version is currently active.

    Priority:
      1. persona.latest.txt pointer (written by the evolution loop on
         promotion).
      2. Highest-numbered persona.vN.md file on disk.
      3. DEFAULT_PERSONA_VERSION as the final fallback.
    """
    if LATEST_POINTER.exists():
        text = LATEST_POINTER.read_text(encoding="utf-8").strip()
        if text:
            return text
    versions: list[int] = []
    for path in ARTIFACTS_DIR.glob("persona.v*.md"):
        try:
            n = int(path.stem.split(".v", 1)[-1])
            versions.append(n)
        except ValueError:
            continue
    if versions:
        return f"v{max(versions)}"
    return DEFAULT_PERSONA_VERSION


def load_persona(
    version: str | None = None,
    *,
    provider_kind: str | None = None,
    surface: str | None = None,
) -> PersonaSpec:
    """Load a persona artifact with optional provider and surface overlays.

    Composition order:
      1. Base persona (chip-rendered or flat MD).
      2. Provider overlay if provider_kind is given (artifacts/overlays/<kind>.md).
      3. Surface overlay if surface is given (artifacts/overlays/surface/<surface>.md).

    Provider overlays target backend-specific drift (zai chatty, minimax
    helper register, codex hallucinated context).

    Surface overlays target surface-specific format constraints: voice
    needs short declarative sentences with no markdown, browser_extension
    needs short replies that fit a popup, etc.

    Both axes compose orthogonally. The full chain reaches the model
    in a single system prompt.
    """
    resolved = version or resolve_latest_persona_version()
    path = ARTIFACTS_DIR / f"persona.{resolved}.md"
    if not path.exists():
        raise FileNotFoundError(f"Persona artifact not found: {path}")
    base_text = path.read_text(encoding="utf-8")
    parts = [base_text.rstrip()]
    overlay_text = load_overlay(provider_kind)
    if overlay_text:
        parts.append(overlay_text)
    surface_text = load_surface_overlay(surface)
    if surface_text:
        parts.append(surface_text)
    combined = "\n\n---\n\n".join(parts)
    return PersonaSpec(
        version=resolved,
        text=combined,
        overlay_kind=provider_kind if overlay_text else None,
    )


def load_persona_from_path(path: str | Path) -> PersonaSpec:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Persona artifact not found: {p}")
    version = p.stem.split(".", 1)[-1] if "." in p.stem else "custom"
    return PersonaSpec(version=version, text=p.read_text(encoding="utf-8"))

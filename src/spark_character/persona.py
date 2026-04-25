"""Persona spec loading.

The persona is a markdown artifact under artifacts/. The harness mutates
that file to evolve voice; everything else reads from it.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ARTIFACTS_DIR = Path(__file__).parent / "artifacts"
DEFAULT_PERSONA_VERSION = "v1"


@dataclass(frozen=True)
class PersonaSpec:
    version: str
    text: str

    @property
    def system_prompt(self) -> str:
        return self.text.strip()


def load_persona(version: str = DEFAULT_PERSONA_VERSION) -> PersonaSpec:
    path = ARTIFACTS_DIR / f"persona.{version}.md"
    if not path.exists():
        raise FileNotFoundError(f"Persona artifact not found: {path}")
    return PersonaSpec(version=version, text=path.read_text(encoding="utf-8"))


def load_persona_from_path(path: str | Path) -> PersonaSpec:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Persona artifact not found: {p}")
    version = p.stem.split(".", 1)[-1] if "." in p.stem else "custom"
    return PersonaSpec(version=version, text=p.read_text(encoding="utf-8"))

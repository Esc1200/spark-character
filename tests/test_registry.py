"""Registry promotion artifact tests."""

from __future__ import annotations

from pathlib import Path

import yaml

from spark_character.chip_loader import PersonalityChip
from spark_character.registry import (
    promote_evolved_chip_to_chip_lab,
    promote_evolved_persona_to_chip_lab,
)


BASE_CHIP_YAML = """
schema: spark-personality-chip.v1
identity:
  id: founder-operator
  name: Founder Operator
traits:
  openness: 0.72
emotional_profile:
  self_awareness: 0.84
preferences:
  likes: []
"""


def test_persona_sidecar_promotion_does_not_export_scores(tmp_path: Path) -> None:
    (tmp_path / "founder-operator.personality.yaml").write_text(BASE_CHIP_YAML, encoding="utf-8")

    target = promote_evolved_persona_to_chip_lab(
        base_chip_id="founder-operator",
        base_persona_version="v8",
        new_persona_version="v9",
        persona_markdown="New voice rules",
        composite_score=0.99,
        lab_path=tmp_path,
    )

    assert target is not None
    spec = yaml.safe_load(target.read_text(encoding="utf-8"))
    evolved = spec["spark_character_evolved"]
    assert evolved["promotion_result"] == "accepted"
    assert "composite_score" not in evolved
    assert "delta_summary" not in evolved


def test_chip_promotion_does_not_export_scores_or_delta_summary(tmp_path: Path) -> None:
    chip = PersonalityChip(
        id="founder-operator",
        name="Founder Operator",
        openness=0.72,
        _raw={"schema": "spark-personality-chip.v1", "identity": {"id": "founder-operator", "name": "Founder Operator"}},
    )

    target = promote_evolved_chip_to_chip_lab(
        chip=chip,
        base_chip_id="founder-operator",
        base_persona_version="v8",
        new_persona_version="v9",
        composite_score=0.99,
        delta_summary={"weak_axis": "t7"},
        lab_path=tmp_path,
    )

    assert target is not None
    spec = yaml.safe_load(target.read_text(encoding="utf-8"))
    evolved = spec["spark_character_evolved"]
    assert evolved["promotion_result"] == "accepted"
    assert "composite_score" not in evolved
    assert "delta_summary" not in evolved

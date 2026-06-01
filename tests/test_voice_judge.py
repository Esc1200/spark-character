from __future__ import annotations

import json
from pathlib import Path

from spark_character.voice_judge import _load_corpus


def test_load_corpus_returns_entries(tmp_path: Path) -> None:
    path = tmp_path / "corpus.json"
    path.write_text(json.dumps({"entries": [{"text": "sharp, warm reply"}]}) + "\n", encoding="utf-8")

    assert _load_corpus(path) == [{"text": "sharp, warm reply"}]


def test_load_corpus_returns_empty_for_malformed_or_missing_file(tmp_path: Path) -> None:
    malformed = tmp_path / "malformed.json"
    malformed.write_text("{", encoding="utf-8")

    assert _load_corpus(malformed) == []
    assert _load_corpus(tmp_path / "missing.json") == []

from spark_character.audit_miner import _detect_failures


def _failure_kinds(text: str) -> set[str]:
    return {kind for kind, _detail in _detect_failures(text)}


def test_detects_markdown_emphasis_in_reply_preview():
    kinds = _failure_kinds("Short answer: **yes**, mission control first is the right call.")

    assert "markdown_emphasis" in kinds


def test_detects_dense_opening_in_reply_preview():
    text = (
        "Mission control first is the right call because it lets you observe active work, "
        "inspect failures, intervene quickly, and learn from each run before expanding into canvas work"
    )

    kinds = _failure_kinds(text)

    assert "dense_opening" in kinds


def test_does_not_flag_short_scannable_reply_as_dense():
    text = "Mission control first is the right call.\n\nThen canvas has a place to report progress."

    kinds = _failure_kinds(text)

    assert "dense_opening" not in kinds

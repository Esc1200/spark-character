"""Regression: build_run_fn must compose provider overlay via detect_provider_kind."""

import inspect


def test_detect_provider_kind_imported():
    """detect_provider_kind must be imported from .persona in harness_adapter."""
    import spark_character.harness_adapter as mod
    src = inspect.getsource(mod)
    assert "detect_provider_kind" in src


def test_build_run_fn_passes_provider_kind_to_load_persona():
    """build_run_fn must call load_persona with provider_kind=detect_provider_kind(provider)."""
    import spark_character.harness_adapter as mod
    src = inspect.getsource(mod.build_run_fn)
    assert "detect_provider_kind" in src, "build_run_fn must pass provider_kind to load_persona"
    assert "load_persona" in src


def test_explicit_persona_is_respected():
    """When caller passes an explicit persona, build_run_fn must not override it."""
    import spark_character.harness_adapter as mod
    src = inspect.getsource(mod.build_run_fn)
    # Pattern: `persona or load_persona(...)` — explicit persona short-circuits load
    assert "persona or" in src
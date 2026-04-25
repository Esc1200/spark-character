# spark-character

Provider-agnostic voice and character for Spark agents.

The persona spec and the critic-rewriter prompt live as versioned markdown
artifacts. The self-evolving harness mutates them, scores them on the P1-P5
persona axes, and keeps what wins. Anyone running their own Spark instance
imports `spark_character` and inherits the evolved voice.

## Why

Anthropic bakes Claude's voice into the model weights through character
training. That ceiling is not portable across the LLMs that Spark agents
plug into (Z.AI, MiniMax, OpenAI, Anthropic, Ollama, etc.). This package
solves the same problem at inference time:

1. A versioned persona spec injected as the system prompt.
2. An optional critic-rewriter pass that fixes drafts that break the
   persona rules.
3. Pure-function scorers (P1-P5) that any process can call to grade
   replies.

## Install

```bash
pip install -e .
# or, with dev tools:
pip install -e .[dev]
```

## Quick start

```python
from spark_character import ProviderSpec, generate, generate_with_critique

provider = ProviderSpec.from_env()  # reads ZAI_API_KEY / ZAI_BASE_URL / ZAI_MODEL

# One-shot generation
result = generate("Should I raise now or wait six months?", provider=provider)
print(result.final)

# With critic-rewrite pass (~2x tokens, much higher persona fidelity)
result = generate_with_critique(
    "Should I raise now or wait six months?",
    provider=provider,
)
print(result.final)
print("rewritten:", result.rewritten)
```

## Score an arbitrary reply

```python
from spark_character import score_persona

score = score_persona("Great question. How can I help today?")
print(score.passed, score.p3_reset, score.p4_lead)
```

The five axes:

- `p1_em_dash`: hard fail on any em dash
- `p2_plumbing`: penalty per internal subsystem leak (researcher, bridge,
  raw episode, etc.)
- `p3_reset`: hard fail on canned check-in greetings
- `p4_lead`: hard fail when the first sentence is a hedge or restatement
- `p5_voice`: warmth + directness + low formality heuristic

## Live pulse

```bash
python evals/live_pulse.py             # generate-only
python evals/live_pulse.py --critic    # with critic-rewrite pass
```

Fires 12 prompts, scores each reply, prints a scorecard. Exit code 0 if
the overall mean across all axes is at least 0.9.

## Plug into the self-evolving harness

```python
from spark_character import ProviderSpec
from spark_character.harness_adapter import build_run_fn

run_fn = build_run_fn(provider=ProviderSpec.from_env(), use_critic=True)

# Pass run_fn to any harness evaluator (L1-L9 capability or P1-P5 persona).
```

The harness can mutate `src/spark_character/artifacts/persona.v1.md` and
`src/spark_character/artifacts/critic.v1.md`, score the result with P1-P5,
and keep what wins. New artifact versions become `persona.v2.md`, etc.

## Repo layout

```
src/spark_character/
  artifacts/
    persona.v1.md      # evolvable system prompt
    critic.v1.md       # evolvable critic-rewriter prompt
  persona.py           # load persona spec
  critic.py            # critic-rewriter pipeline
  provider.py          # OpenAI-compatible direct call (sync + async)
  pipeline.py          # generate / generate_with_critique
  scoring.py           # P1-P5 scorers (pure functions)
  harness_adapter.py   # run_fn for spark-self-evolving-harness
evals/
  live_pulse.py        # 12-prompt scorecard against the live provider
tests/
```

## License

MIT

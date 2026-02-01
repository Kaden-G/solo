# Autonomy Engine v1.1

A Prefect-based autonomous build engine with human-in-the-loop decision gates.

## What This Is For

- Automating structured software build workflows (design, implement, test, verify)
- Providing human oversight at critical decision points via Prefect's pause/resume
- Maintaining full traceability of every step, prompt, and decision in `TRACE.json`
- Supporting multiple LLM providers (Claude, OpenAI) behind a unified interface

## What This Is NOT For

- Replacing human judgment on ethical, security, or architectural decisions
- Unsupervised production deployments
- General-purpose AI agent framework — this is a specific pipeline, not a platform
- Real-time or latency-sensitive workflows

## Architecture

```
templates/          Fill these in with your project specs
    ├── prompts/    LLM prompt templates (logged by hash in TRACE.json)
    ↓
[bootstrap] ──→ state/inputs/
                    ↓
[design]    ──→ state/designs/      ←── may pause at decision gate
                    ↓
[implement] ──→ state/implementations/
                    ↓
[test]      ──→ state/tests/
                    ↓
[verify]    ──→ state/tests/VERIFICATION.md
```

### Core Principles

1. **If it isn't written, it doesn't exist** — tasks communicate through files in `state/`, not return values
2. **Gates are policy, not behavior** — tasks raise `DecisionRequired`; only the flow may pause execution
3. **Structured state** — `state/` has predefined subfolders, not a flat directory
4. **Traceability** — every task appends to `state/TRACE.json` with inputs, outputs, model, and prompt hash

### Decision Gates

When a task encounters ambiguity requiring human judgment, it raises `DecisionRequired`. The flow catches this, pauses via Prefect's `pause_flow_run`, and waits for input through the Prefect UI. Decisions are recorded in `state/decisions/` so tasks can read them on re-run.

Gate definitions live in `templates/DECISION_GATES.yml`.

## Setup

```bash
cd ~/Desktop/autonomy_engine
pip install -e .
```

## Usage

```bash
# Start Prefect server (separate terminal)
prefect server start

# Run the flow
python -c "from flows.autonomous_flow import autonomous_build; autonomous_build()"
```

The flow will appear in the Prefect UI at `http://localhost:4200`. If a decision gate triggers, resume from the UI.

## Configuration

Edit `config.yml` to switch LLM providers and configure notifications:

```yaml
llm:
  provider: "claude"  # or "openai"
```

Set API keys via environment variables: `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`.

## Project Structure

```
engine/             Core modules (LLM provider, gates, state, tracing, notifications)
flows/              Prefect flow definition — the entry point
tasks/              Individual pipeline stages as Prefect tasks
templates/          Input skeletons and prompt templates
  prompts/          LLM prompt files (tracked by SHA-256 hash in TRACE.json)
state/              Runtime artifacts (gitignored except .gitkeep)
  inputs/           Bootstrapped templates
  designs/          Architecture documents
  implementations/  Generated code
  tests/            Test and verification results
  decisions/        Human decisions recorded from gates
  TRACE.json        Traceability spine
```

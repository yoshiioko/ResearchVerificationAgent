# AGENTS.md — ResearchVerificationAgent

## Project Overview

A stateful, multi-node AI agent that performs web research and self-verifies findings before producing a final report. Built as a **LangGraph state machine** with **PydanticAI** for structured LLM outputs.

## Architecture

The agent is a `StateGraph` loop with three nodes:

```
START → researcher_node → critic_node ─┐ (is_verified=False, attempts<3)
                               ↑        └→ researcher_node (retry)
                               └──────────→ compiler_node → END (verified or max attempts)
```

- **`researcher_node`** — calls Tavily web search, writes raw results to `AgentState.raw_research`
- **`critic_node`** — returns a structured Pydantic object (`is_verified`, `critique`, `suggested_queries`); the critic must be prompted harshly/skeptically to avoid hallucinations
- **`compiler_node`** — formats verified research as a Markdown report

`AgentState` holds: `messages: list[BaseMessage]`, `raw_research: str`, `verification_results: dict`, `iteration_count: int`.

## Key Files (to be created under `src/agent/`)

| File | Purpose |
|------|---------|
| `config.py` | API keys, model name constants |
| `schemas.py` | Pydantic models (e.g., `CriticOutput`) |
| `state.py` | `AgentState` definition |
| `tools.py` | `web_search` tool wrapping Tavily |
| `prompts.py` | Prompt strings for researcher and critic |
| `nodes.py` | `researcher_node`, `critic_node`, `compiler_node` functions |
| `graph.py` | `StateGraph` wiring and conditional edges |
| `runner.py` | Entry point with `MemorySaver` checkpointer |
| `sanity.py` | Phase 1 smoke test (no LLM calls) |
| `phase2_sanity.py` | Phase 2 smoke test (real API calls, no graph) |

## Phase-by-Phase Build Order

Follow `.plan/PHASES_INDEX.md` strictly — implement one phase at a time:

1. **Phase 1** — `config.py`, `schemas.py`, `state.py`, `__init__.py`, `sanity.py`
2. **Phase 2** — `tools.py`, `prompts.py`, `nodes.py`, `phase2_sanity.py`
3. **Phase 3** — `graph.py`, `runner.py`, `main.py`, routing tests
4. **Phase 4** — `logging_utils.py`, `exporter.py`, `eval.py`, observability
5. **Phase 5** — `Makefile`, CI (`/.github/workflows/ci.yml`), `CONTRIBUTING.md`

## Developer Workflows

```bash
# Install deps (uses uv, not pip)
uv sync

# Run phase sanity checks
uv run python -m src.agent.sanity          # Phase 1
uv run python -m src.agent.phase2_sanity   # Phase 2

# Run the full agent
uv run python main.py

# Tests (unit only, no real API calls)
uv run pytest -q -m "not integration"

# Integration tests (requires real API keys)
uv run pytest -q -m integration

# Eval (costs API credits)
uv run python -m src.agent.eval

# After Phase 5: use Makefile shortcuts
make test
make run
make eval
```

## Environment & External Dependencies

- Copy `.env.example` → `.env` and populate:
  - `GOOGLE_API_KEY` — for Gemini (`gemini-1.5-pro` or `gemini-1.5-flash`)
  - `TAVILY_API_KEY` — for web search
- Never commit `.env`; load with `python-dotenv`

## Key Conventions

- **Package manager**: `uv` exclusively — use `uv run` prefix for all commands, not bare `python` or `pip`
- **LLM model**: Google Gemini via `langchain-google-genai`; model name defined in `config.py`
- **Structured output**: `pydantic-ai` is used for the Critic's structured response — define the output shape as a Pydantic model, not a raw prompt parse
- **Loop guard**: `iteration_count` caps retries at 3; the conditional edge must check this before routing back to the researcher
- **Logging**: Print the active node name to stdout at the start of each node function so execution flow is visible in the terminal
- **Test markers**: Use `@pytest.mark.integration` for any test that makes real API calls


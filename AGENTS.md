# AGENTS.md — ResearchVerificationAgent

## Project Overview

A stateful, multi-node AI agent that performs web research and self-verifies findings before producing a final report. Built as a **LangGraph state machine** with **Pydantic v2** for structured LLM outputs.

## Architecture

The agent is a `StateGraph` loop with three nodes:

```
START → researcher_node → critic_node ─┐ (is_verified=False, attempts<3)
                               ↑        └→ researcher_node (retry)
                               └──────────→ compiler_node → END (verified or max attempts)
```

- **`researcher_node`** — runs one `web_search` call per query in `current_search_queries`, synthesizes results via Gemini, accumulates into `AgentState.raw_research`
- **`critic_node`** — prompts Gemini at `temperature=0.0` to return strict JSON; parses it into `CriticAssessment` via `_safe_parse_critic_response` with a hardened fallback; updates `verification_results` and `current_search_queries`
- **`compiler_node`** — formats final Markdown report into `AgentState.final_report_markdown`

`AgentState` holds: `messages: list[BaseMessage]`, `user_query: str`, `raw_research: str`, `verification_results: dict`, `iteration_count: int`, `current_search_queries: list[str]`, `final_report_markdown: str`.

Loop control is **pure Python** in `route_after_critic` (`graph.py`) — the LLM cannot override termination.

## Key Files (under `src/agent/`)

| File | Purpose | Status |
|------|---------|--------|
| `config.py` | `Settings` dataclass + `load_settings()` factory | ✅ done |
| `schemas.py` | `CriticAssessment`, `CompilerOutput` Pydantic models | ✅ done |
| `state.py` | `AgentState` definition + `apply_critic_assessment()` | ✅ done |
| `tools.py` | `web_search()` wrapping Tavily; returns markdown string | ✅ done |
| `prompts.py` | `build_researcher_instructions()`, `build_critic_instructions()`, `build_compiler_instructions()` | ✅ done |
| `nodes.py` | `researcher_node`, `critic_node`, `compiler_node` | ✅ done |
| `graph.py` | `StateGraph` wiring, `route_after_critic`, `build_graph()` | ✅ done |
| `runner.py` | `run_once()`, `run_cli()` entrypoints | ✅ done |
| `sanity.py` | Phase 1 smoke test (no LLM calls) | ✅ done |
| `phase2_sanity.py` | Phase 2 smoke test (real API calls, no graph) | ✅ done |
| `logging_utils.py` | Structured observability logging | ⬜ Phase 4 |
| `exporter.py` | Report export utilities | ⬜ Phase 4 |
| `eval.py` | Evaluation harness | ⬜ Phase 4 |

## Phase-by-Phase Build Order

1. **Phase 1** ✅ — `config.py`, `schemas.py`, `state.py`, `__init__.py`, `sanity.py`
2. **Phase 2** ✅ — `tools.py`, `prompts.py`, `nodes.py`, `phase2_sanity.py`
3. **Phase 3** ✅ — `graph.py`, `runner.py`, `main.py`, `tests/test_routing.py`, `tests/test_graph_smoke.py`
4. **Phase 4** ⬜ — `logging_utils.py`, `exporter.py`, `eval.py`, observability
5. **Phase 5** ⬜ — `Makefile`, CI (`/.github/workflows/ci.yml`), `CONTRIBUTING.md`

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
  - `GOOGLE_API_KEY` — for Gemini
  - `TAVILY_API_KEY` — for web search
- Optional overrides (all have defaults in `load_settings()`):
  - `MODEL_NAME` — default `gemini-2.5-flash`
  - `MAX_ITERATIONS` — default `3`, minimum `1`
  - `TAVILY_MAX_RESULTS` — default `5`, minimum `1`
  - `LOG_LEVEL` — default `INFO`
- Never commit `.env`; load with `python-dotenv`

## Key Conventions

- **Package manager**: `uv` exclusively — use `uv run` prefix for all commands, not bare `python` or `pip`
- **LLM model**: Google Gemini (`gemini-2.5-flash`) via `langchain-google-genai`; model name defined in `config.py`
- **Structured output**: The critic's JSON is parsed via `json.loads` + `CriticAssessment.model_validate()` in `_safe_parse_critic_response` (`nodes.py`), with a hardened fallback that always returns a valid `CriticAssessment`. Do not use `.with_structured_output()` for the critic.
- **Loop guard**: `iteration_count` caps retries at `settings.max_iterations` (default 3); `route_after_critic` checks `iteration_count >= max_iterations` before routing back to the researcher
- **Graph adapter pattern**: `build_graph()` wraps each node in a local adapter function to bridge LangGraph's single-argument call convention (`state` only) with the node convention (`state + settings`). See `graph.py`.
- **Persistence**: `MemorySaver` checkpointer is attached at compile time. `run_once()` scopes each run by `thread_id` — use a unique `thread_id` per independent query to prevent state bleed.
- **Logging**: Print the active node name to stdout at the start of each node function so execution flow is visible in the terminal
- **Test markers**: Use `@pytest.mark.integration` for any test that makes real API calls
- **Unit test setup**: `Settings` can be instantiated directly with dummy keys (e.g., `google_api_key="x"`) for tests that do not make API calls — see `tests/test_routing.py` for the pattern


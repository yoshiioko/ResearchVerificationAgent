# Research Verification Agent

A stateful, multi-node AI agent that performs web research, critiques its own
findings, and compiles a final Markdown report. Built with **LangGraph** and
**Google Gemini (`gemini-2.5-flash`)**.

```
START → researcher_node → critic_node ─┐ (unverified, attempts < 3)
                               ↑        └→ researcher_node (retry)
                               └──────────→ compiler_node → END
```

---

## Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.12+ |
| [uv](https://docs.astral.sh/uv/getting-started/installation/) | latest |
| Google API key | [Google AI Studio](https://aistudio.google.com/app/apikey) |
| Tavily API key | [Tavily](https://app.tavily.com/) |

---

## Quick Start

### 1. Clone the repo
```bash
git clone https://github.com/your-username/ResearchVerificationAgent.git
cd ResearchVerificationAgent
```

### 2. Install dependencies
```bash
uv sync
```

### 3. Configure environment
```bash
cp .env.example .env
```

Open `.env` and fill in your keys:
```
GOOGLE_API_KEY=your_google_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

### 4. Run the agent
```bash
uv run python main.py
```

You will be prompted to enter a research question. The agent will run up to
3 research + critique cycles, then print a final Markdown report to the terminal.

---

## Running Tests

Unit tests make no API calls and run in under 1 second:
```bash
uv run pytest -q
```

Integration tests require real API keys and cost credits:
```bash
uv run pytest -q -m integration
```

---

## Project Structure

```
src/agent/
├── config.py       # API keys and model settings
├── state.py        # AgentState (shared graph state)
├── schemas.py      # Pydantic output models (CriticAssessment, CompilerOutput)
├── tools.py        # web_search wrapper for Tavily
├── prompts.py      # Prompt strings for each node
├── nodes.py        # researcher_node, critic_node, compiler_node
├── graph.py        # StateGraph wiring and conditional routing
└── runner.py       # run_once() and run_cli() entrypoints
tests/
├── test_routing.py       # Unit tests for route_after_critic logic
└── test_graph_smoke.py   # Smoke test with stubbed nodes
main.py             # Project entrypoint
```

---

## Architecture Notes

- **Loop control** is plain Python — `route_after_critic` in `graph.py` decides
  whether to retry or compile. The LLM cannot override this.
- **Persistence** uses `MemorySaver`. Each run is scoped by `thread_id` to
  prevent state from bleeding between queries.
- **Termination** is printed at the end of every run: `verified` means the
  critic approved the research; `max_iterations` means the retry cap was hit.


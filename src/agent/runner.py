"""CLI runner for invoking the compiled graph."""

from __future__ import annotations

from typing import Any

from .config import load_settings
from .graph import build_graph
from .state import AgentState


def run_once(user_query: str, thread_id: str = "local-dev-thread") -> AgentState:
    """Run one complete graph invocation and return the final state.

    thread_id scopes the MemorySaver checkpoint — use a unique ID per
    independent query to prevent state from bleeding between runs.
    """

    settings = load_settings()
    app = build_graph(settings)

    initial_state = AgentState(user_query=user_query)
    config: dict[str, Any] = {"configurable": {"thread_id": thread_id}}

    # invoke(...) returns the final state payload from END.
    final_state = app.invoke(initial_state, config=config)

    # Ensure type is AgentState even if runtime returns a plain dict.
    if isinstance(final_state, AgentState):
        return final_state
    return AgentState.model_validate(final_state)


def run_cli() -> None:
    """Interactive CLI entrypoint."""

    print("Research Verification Agent")
    user_query = input("Enter your research question: ").strip()

    if not user_query:
        print("No question entered. Exiting.")
        return

    state = run_once(user_query=user_query)

    print("\n=== FINAL REPORT ===\n")
    print(state.final_report_markdown or "(No report generated)")

    termination_reason = "verified" if state.verification_results.get("is_verified") else "max_iterations"
    print(
        "\n=== RUN META ===\n"
        f"iterations={state.iteration_count} termination={termination_reason}"
    )

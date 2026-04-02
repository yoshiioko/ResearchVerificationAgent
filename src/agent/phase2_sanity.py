"""Phase 2 sanity harness for tools and node logic (without graph wiring)."""

from __future__ import annotations

from .config import load_settings
from .nodes import compiler_node, critic_node, researcher_node
from .state import AgentState


def run_phase_2_sanity() -> None:
    settings = load_settings()

    state = AgentState(user_query="What are recent breakthroughs in sodium-ion batteries?")
    print("[sanity] initial state created")

    updates = researcher_node(state, settings)
    state = state.model_copy(update=updates)
    print(f"[sanity] after researcher: iteration_count={state.iteration_count}")

    updates = critic_node(state, settings)
    state = state.model_copy(update=updates)
    print(f"[sanity] critic verdict keys={list(state.verification_results.keys())}")

    updates = compiler_node(state, settings)
    state = state.model_copy(update=updates)
    print("[sanity] compiler output generated")

    print("\n=== FINAL MARKDOWN PREVIEW ===\n")
    print(state.final_report_markdown[:1200])


if __name__ == "__main__":
    run_phase_2_sanity()

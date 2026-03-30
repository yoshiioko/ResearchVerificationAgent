"""Phase 1 sanity checks for config and schema contracts."""

from __future__ import annotations

from pydantic import ValidationError

from .config import load_settings
from .schemas import CriticAssessment
from .state import AgentState


def run_phase_1_sanity() -> None:
    settings = load_settings()
    print("[ok] settings loaded")
    print(f"[ok] model={settings.model_name} max_iterations={settings.max_iterations}")

    state = AgentState(user_query="What are current trends in battery recycling?")
    print(f"[ok] state initialized with default query list: {state.current_search_queries}")

    assessment = CriticAssessment(
        is_verified=False,
        critique="Need more evidence from primary sources.",
        suggested_queries=["battery recycling market report 2025 primary source"],
        confidence=0.42,
    )
    state.apply_critic_assessment(assessment)
    print(f"[ok] critic assessment applied: {state.verification_results}")

    try:
        CriticAssessment(is_verified=False, critique="Missing query", suggested_queries=[])
    except ValidationError:
        print("[ok] schema correctly rejects unverified assessment without suggested queries")


if __name__ == "__main__":
    run_phase_1_sanity()

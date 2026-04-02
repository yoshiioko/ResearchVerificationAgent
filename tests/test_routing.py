from __future__ import annotations

from src.agent.config import Settings
from src.agent.graph import route_after_critic
from src.agent.state import AgentState


def _settings(max_iterations: int = 3) -> Settings:
    return Settings(
        google_api_key="x",
        tavily_api_key="y",
        model_name="gemini-2.5-flash",
        max_iterations=max_iterations,
        tavily_max_results=5,
        log_level="INFO",
    )


def test_route_unverified_below_max_goes_to_researcher() -> None:
    state = AgentState(user_query="q", iteration_count=1, verification_results={"is_verified": False})
    assert route_after_critic(state, _settings(max_iterations=3)) == "researcher_node"

def test_route_verified_goes_to_compiler() -> None:
    state = AgentState(user_query="q", iteration_count=1, verification_results={"is_verified": True})
    assert route_after_critic(state, _settings(max_iterations=3)) == "compiler_node"


def test_route_unverified_at_max_goes_to_compiler() -> None:
    state = AgentState(user_query="q", iteration_count=3, verification_results={"is_verified": False})
    assert route_after_critic(state, _settings(max_iterations=3)) == "compiler_node"

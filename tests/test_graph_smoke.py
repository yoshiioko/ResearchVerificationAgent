from __future__ import annotations

from typing import Any

import src.agent.graph as graph_module
from src.agent.config import Settings
from src.agent.state import AgentState


def _settings() -> Settings:
    return Settings(
        google_api_key="x",
        tavily_api_key="y",
        model_name="gemini-2.5-flash",
        max_iterations=2,
        tavily_max_results=5,
        log_level="INFO",
    )


def test_graph_compiles_and_runs_with_stubbed_nodes(monkeypatch) -> None:
    def fake_researcher(state: AgentState, settings: Settings) -> dict[str, Any]:
        return {
            "iteration_count": state.iteration_count + 1,
            "raw_research": "stub research",
            "messages": state.messages,
        }

    def fake_critic(state: AgentState, settings: Settings) -> dict[str, Any]:
        return {
            "verification_results": {"is_verified": True, "critique": "ok", "suggested_queries": []},
            "current_search_queries": [state.user_query],
            "messages": state.messages,
        }

    def fake_compiler(state: AgentState, settings: Settings) -> dict[str, Any]:
        return {
            "final_report_markdown": "# Final\n\nStub report",
            "messages": state.messages,
        }

    monkeypatch.setattr(graph_module, "researcher_node", fake_researcher)
    monkeypatch.setattr(graph_module, "critic_node", fake_critic)
    monkeypatch.setattr(graph_module, "compiler_node", fake_compiler)

    app = graph_module.build_graph(_settings())
    result = app.invoke(AgentState(user_query="test"), config={"configurable": {"thread_id": "t1"}})

    if isinstance(result, AgentState):
        final_state = result
    else:
        final_state = AgentState.model_validate(result)

    assert final_state.final_report_markdown.startswith("# Final")
    assert final_state.iteration_count == 1
    assert final_state.verification_results.get("is_verified") is True

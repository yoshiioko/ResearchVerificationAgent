"""Graph wiring for the research-verification agent."""

from __future__ import annotations

from typing import Literal

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from .config import Settings
from .nodes import compiler_node, critic_node, researcher_node
from .state import AgentState

RouteName = Literal["researcher_node", "compiler_node"]


def route_after_critic(state: AgentState, settings: Settings) -> RouteName:
    """Decide whether to loop back to researcher or move to compiler.

    This function IS your loop control logic.
    In your old tool-calling agent, the LLM decided when to stop.
    Here, *you* decide — using Python — and the LLM cannot override it.
    """

    is_verified = bool(state.verification_results.get("is_verified", False))
    iteration = state.iteration_count

    if (not is_verified) and iteration < settings.max_iterations:
        next_node: RouteName = "researcher_node"
    else:
        next_node = "compiler_node"

    print(
        "[router] route_after_critic "
        f"is_verified={is_verified} iteration={iteration}/{settings.max_iterations} "
        f"-> {next_node}"
    )
    return next_node


def build_graph(settings: Settings):
    """Build and compile the LangGraph application with MemorySaver persistence.

    Graph topology:
        START -> researcher_node -> critic_node -> (conditional) -> researcher_node (loop)
                                                               -> compiler_node -> END
    """

    graph = StateGraph(AgentState)

    # Named adapter functions bridge LangGraph's single-argument call convention
    # (state only) with our node convention (state + settings).
    def researcher_adapter(state: AgentState) -> dict:
        return researcher_node(state, settings)

    def critic_adapter(state: AgentState) -> dict:
        return critic_node(state, settings)

    def compiler_adapter(state: AgentState) -> dict:
        return compiler_node(state, settings)

    def router_adapter(state: AgentState) -> RouteName:
        return route_after_critic(state, settings)

    graph.add_node("researcher_node", researcher_adapter)
    graph.add_node("critic_node", critic_adapter)
    graph.add_node("compiler_node", compiler_adapter)

    graph.add_edge(START, "researcher_node")
    graph.add_edge("researcher_node", "critic_node")

    graph.add_conditional_edges(
        "critic_node",
        router_adapter,
        {
            "researcher_node": "researcher_node",
            "compiler_node": "compiler_node",
        },
    )

    graph.add_edge("compiler_node", END)

    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)

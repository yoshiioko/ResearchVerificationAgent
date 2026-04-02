"""Core  node implementations for research, critique, and compilation."""

from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import ValidationError

from .config import Settings
from .prompts import (
    build_compiler_instructions,
    build_critic_instructions,
    build_researcher_instructions,
)
from .schemas import CriticAssessment
from .state import AgentState
from .tools import web_search


def _make_llm(settings: Settings, temperature: float = 0.2) -> ChatGoogleGenerativeAI:
    """Small helper so model configuration stays centralized."""
    return ChatGoogleGenerativeAI(
        model=settings.model_name,
        google_api_key=settings.google_api_key,
        temperature=temperature,
    )


def _safe_parse_critic_response(raw_text: str, user_query: str) -> CriticAssessment:
    """Parse critic JSON with a robust fallback if the model output is malformed."""
    try:
        parsed = json.loads(raw_text)
        return CriticAssessment.model_validate(parsed)
    except (json.JSONDecodeError, ValidationError) as exc:
        return CriticAssessment(
            is_verified=False,
            critique=(
                "Critic output parsing failed. "
                f"Error: {type(exc).__name__}. Request a narrower follow-up search."
            ),
            suggested_queries=[f"{user_query} primary source evidence"],
            confidence=0.0,
        )


def researcher_node(state: AgentState, settings: Settings) -> dict[str, Any]:
    print(f"[node:start] researcher_node (iteration={state.iteration_count + 1})")

    next_iteration = state.iteration_count + 1
    search_queries = state.current_search_queries or [state.user_query]

    research_blocks: list[str] = []
    for query in search_queries:
        result_block = web_search(
            tavily_api_key=settings.tavily_api_key,
            query=query,
            max_results=settings.tavily_max_results,
        )
        research_blocks.append(result_block)

    researcher_prompt = build_researcher_instructions(
        user_query=state.user_query,
        search_queries=search_queries,
        iteration=next_iteration,
    )

    llm = _make_llm(settings=settings, temperature=0.2)
    evidence_payload = "\n\n".join(research_blocks)
    llm_input = f"{researcher_prompt}\n\nSearch Results:\n{evidence_payload}"
    llm_response = llm.invoke(llm_input)
    synthesized_research = str(llm_response.content).strip()

    combined_research = (
        f"{state.raw_research}\n\n{synthesized_research}".strip()
        if state.raw_research
        else synthesized_research
    )

    print(f"[node:end] researcher_node (queries={len(search_queries)})")
    return {
        "iteration_count": next_iteration,
        "raw_research": combined_research,
        "messages": state.messages
        + [
            AIMessage(
                content=(
                    f"Research iteration {next_iteration} completed. "
                    f"Queries: {search_queries}"
                )
            )
        ],
    }


def critic_node(state: AgentState, settings: Settings) -> dict[str, Any]:
    print(f"[node:start] critic_node (iteration={state.iteration_count})")

    critic_prompt = build_critic_instructions(
        user_query=state.user_query,
        raw_research=state.raw_research,
    )

    llm = _make_llm(settings=settings, temperature=0.0)
    llm_response = llm.invoke(critic_prompt)
    raw_text = str(llm_response.content).strip()

    assessment = _safe_parse_critic_response(raw_text=raw_text, user_query=state.user_query)

    print(
        "[node:end] critic_node "
        f"(is_verified={assessment.is_verified}, suggested_queries={len(assessment.suggested_queries)})"
    )

    return {
        "verification_results": assessment.model_dump(),
        "current_search_queries": assessment.suggested_queries or [state.user_query],
        "messages": state.messages + [AIMessage(content=f"Critic verdict: {assessment.model_dump_json()}")],
    }


def compiler_node(state: AgentState, settings: Settings) -> dict[str, Any]:
    print(f"[node:start] compiler_node (iteration={state.iteration_count})")

    compiler_prompt = build_compiler_instructions(
        user_query=state.user_query,
        raw_research=state.raw_research,
        verification_results=state.verification_results,
        iteration_count=state.iteration_count,
    )

    llm = _make_llm(settings=settings, temperature=0.1)
    llm_response = llm.invoke(compiler_prompt)
    final_markdown = str(llm_response.content).strip()

    print("[node:end] compiler_node")
    return {
        "final_report_markdown": final_markdown,
        "messages": state.messages + [AIMessage(content="Compiler produced final markdown report.")],
    }

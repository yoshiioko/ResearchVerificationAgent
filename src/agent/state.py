"""Shared graph state contract used by all nodes."""

from __future__ import annotations

from langchain_core.messages import BaseMessage
from pydantic import BaseModel, ConfigDict, Field, model_validator

from .schemas import CriticAssessment


class AgentState(BaseModel):
    """Global state that flows through the LangGraph state machine."""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    messages: list[BaseMessage] = Field(default_factory=list)
    user_query: str = Field(..., min_length=1)

    raw_research: str = ""
    verification_results: dict = Field(default_factory=dict)
    iteration_count: int = Field(default=0, ge=0)

    current_search_queries: list[str] = Field(default_factory=list)
    final_report_markdown: str = ""

    @model_validator(mode="after")
    def ensure_initial_queries(self) -> "AgentState":
        # Keep the state safe even if the caller forgets to seed current_search_queries.
        if not self.current_search_queries:
            self.current_search_queries = [self.user_query]
        return self

    def apply_critic_assessment(self, assessment: CriticAssessment) -> None:
        """Convenience mutator so future nodes update state consistently."""
        self.verification_results = assessment.model_dump()
        self.current_search_queries = assessment.suggested_queries or [self.user_query]

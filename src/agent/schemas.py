"""Strict Pydantic schemas for structured model outputs."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CriticAssessment(BaseModel):
    """Critic decision used for routing and retry strategy."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    is_verified: bool = Field(..., description="Whether research quality is sufficient.")
    critique: str = Field(..., min_length=1, description="What is missing or unsupported.")
    suggested_queries: list[str] = Field(
        default_factory=list,
        description="Follow-up search queries for the next iteration.",
    )
    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Optional confidence score from critic.",
    )

    @model_validator(mode="after")
    def validate_query_requirements(self) -> "CriticAssessment":
        # If the result is unverified, require at least one concrete next query.
        if not self.is_verified and not self.suggested_queries:
            raise ValueError(
                "suggested_queries must not be empty when is_verified is False"
            )

        return self


class CompilerOutput(BaseModel):
    """Structured final report before rendering/printing markdown."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(..., min_length=1)
    executive_summary: str = Field(..., min_length=1)
    key_findings: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    final_markdown: str = Field(..., min_length=1)

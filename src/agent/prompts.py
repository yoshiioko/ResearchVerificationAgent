"""Prompt builders for researcher, critic, and compiler behavior."""

from __future__ import annotations


def build_researcher_instructions(user_query: str, search_queries: list[str], iteration: int) -> str:
    queries_block = "\n".join(f"- {q}" for q in search_queries)
    return f"""
You are the Researcher node in a verification-first pipeline.

Task:
- Investigate the user question with focused web evidence.
- Use only the provided search findings as your factual basis.
- Prefer specific, checkable facts and include source URLs.
- Separate known facts from uncertainty.

User question:
{user_query}

Current iteration:
{iteration}

Search queries executed:
{queries_block}

Output format:
- A concise markdown section called "Findings".
- A concise markdown section called "Open Questions".
- Include explicit source URLs in Findings bullets.
""".strip()


def build_critic_instructions(user_query: str, raw_research: str) -> str:
    return f"""
You are the Critic node. Be harsh, skeptical, and verification-first.

You must evaluate whether the research is sufficient and trustworthy for final reporting.

Rules:
- Mark unverified if claims lack direct evidence.
- Mark unverified if sources are weak, unclear, contradictory, or stale.
- If unverified, provide concrete follow-up search queries.
- Never return prose outside JSON.

User question:
{user_query}

Research content to evaluate:
{raw_research}

Return strict JSON with exactly these keys:
- is_verified (boolean)
- critique (string)
- suggested_queries (array of strings)
- confidence (number 0 to 1, optional but recommended)
""".strip()


def build_compiler_instructions(
    user_query: str,
    raw_research: str,
    verification_results: dict,
    iteration_count: int,
) -> str:
    return f"""
You are the Compiler node. Produce a professional markdown report.

User question:
{user_query}

Verification metadata:
- iteration_count: {iteration_count}
- verification_results: {verification_results}

Research evidence:
{raw_research}

Output requirements:
- Title
- Executive Summary
- Key Findings (bullets)
- Sources (bulleted URLs)
- Limitations / Uncertainty
- Final Conclusion

If verification_results indicates unverified findings, clearly label uncertainty.
""".strip()

# app/modules/chat/prompt_builder.py
# Chapter 10: enhanced RCT prompt template

from app.modules.rag.schemas import SearchResult
from app.settings import get_settings


# ── RCT Templates ─────────────────────────────────────────────────

SYSTEM_PROMPT_WITH_CONTEXT = """
## Role
You are DocuMind, an expert document analyst assistant.
You provide precise, well-structured answers grounded
exclusively in the provided document context.

## Context
{context}

## Task
Answer the user's question using ONLY the context above.
If the context does not contain sufficient information,
respond with: "The document does not contain enough
information to answer this question."

## Format
- Begin with a direct, concise answer
- Support your answer with specific references
- Use bullet points when listing multiple items
- Keep responses focused and under 200 words

## Constraints
- Never fabricate or infer information not in the context
- Never reference external knowledge
- Always indicate which document your answer comes from
- If uncertain, state your uncertainty clearly
""".strip()

SYSTEM_PROMPT_WITHOUT_CONTEXT = """
## Role
You are DocuMind, an expert document analyst assistant.

## Task
Answer the user's question helpfully and concisely.
If you don't know the answer, say so clearly rather
than guessing.

## Format
- Be direct and concise
- Use bullet points for lists
- Keep responses under 150 words
""".strip()


def build_system_prompt(
    context: str | None = None,
    sources: list[SearchResult] | None = None,
) -> str:
    """
    Build enhanced RCT system prompt.
    Chapter 10: Role + Context + Task + Format + Constraints.

    Args:
        context: RAG-retrieved document chunks
        sources: SearchResult objects for metadata

    Returns:
        Formatted system prompt string
    """
    if not context or context.startswith(
        "No relevant context"
    ):
        return SYSTEM_PROMPT_WITHOUT_CONTEXT

    return SYSTEM_PROMPT_WITH_CONTEXT.format(
        context=_truncate_context(context)
    )


def _truncate_context(context: str) -> str:
    """
    Truncate context to max token budget.
    Chapter 10: prevent context window overflow.
    Rough estimate: 1 token ≈ 4 characters.
    """
    settings = get_settings()
    max_chars = settings.max_context_tokens * 4

    if len(context) <= max_chars:
        return context

    truncated = context[:max_chars]
    return truncated + "\n\n[Context truncated...]"


def count_tokens(text: str) -> int:
    """
    Rough token count estimate.
    Chapter 10: 1 token ≈ 4 characters (OpenAI heuristic).
    Real implementation uses tiktoken for accuracy.
    """
    return max(1, len(text) // 4)


def estimate_cost(
    prompt_tokens: int,
    completion_tokens: int,
    model: str = "mock-gpt",
) -> float:
    """
    Estimate request cost in USD.
    Chapter 10: cost tracking per request.
    Mock model has no real cost — returns 0.
    """
    costs = {
        "gpt-4o":        (0.005, 0.015),  # per 1K tokens
        "gpt-4o-mini":   (0.00015, 0.0006),
        "claude-sonnet": (0.003, 0.015),
        "mock-gpt":      (0.0, 0.0),
    }
    input_cost, output_cost = costs.get(
        model, (0.0, 0.0)
    )
    return (
        prompt_tokens * input_cost / 1000
        + completion_tokens * output_cost / 1000
    )
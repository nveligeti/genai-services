# app/modules/guardrails/output_guards.py
# Chapter 9: output guardrails — hallucination + moderation

import re
from app.modules.guardrails.schemas import (
    CheckResult,
    GuardrailStatus,
)


class HallucinationGuard:
    """
    Checks if LLM response is grounded in RAG context.
    Chapter 9: fail-open — availability over strict safety.
    Chapter 10: G-Eval pattern for scoring groundedness.
    """

    async def check(
        self,
        response: str,
        context: str,
    ) -> CheckResult:
        """
        Verify response is grounded in provided context.
        Uses keyword overlap as a proxy for groundedness.
        Real implementation uses LLM-as-judge (Chapter 10).
        """
        try:
            if not context or context.startswith(
                "No relevant context"
            ):
                # No context available — skip check
                return CheckResult(
                    name="hallucination_guard",
                    status=GuardrailStatus.SKIPPED,
                    reason="No context to verify against",
                    score=0.5,
                )

            # Extract meaningful words from both
            context_words = set(
                re.findall(r"\b\w{4,}\b", context.lower())
            )
            response_words = set(
                re.findall(r"\b\w{4,}\b", response.lower())
            )

            if not response_words:
                return CheckResult(
                    name="hallucination_guard",
                    status=GuardrailStatus.PASSED,
                    reason="Empty response",
                    score=1.0,
                )

            # Calculate overlap score
            overlap = context_words & response_words
            score = len(overlap) / max(len(response_words), 1)
            score = min(score * 2, 1.0)  # scale up

            if score < 0.1:
                return CheckResult(
                    name="hallucination_guard",
                    status=GuardrailStatus.BLOCKED,
                    reason=(
                        f"Response appears ungrounded "
                        f"(score: {score:.2f})"
                    ),
                    score=score,
                )

            return CheckResult(
                name="hallucination_guard",
                status=GuardrailStatus.PASSED,
                reason=f"Response grounded (score: {score:.2f})",
                score=score,
            )

        except Exception as e:
            # Fail-open — availability over strict safety
            return CheckResult(
                name="hallucination_guard",
                status=GuardrailStatus.SKIPPED,
                reason=f"Guard error (fail-open): {e}",
                score=0.5,
            )


class OutputModerationGuard:
    """
    Checks LLM output for harmful content.
    Chapter 9: fail-closed — safety critical.
    """

    HARMFUL_PATTERNS = [
        r"\b(step[- ]by[- ]step|instructions) (to|for) "
        r"(harm|hurt|kill|attack)",
        r"\b(here is how to make|creating) (a |an )?"
        r"(bomb|weapon|explosive)",
    ]

    async def check(self, response: str) -> CheckResult:
        """
        Check LLM output for harmful content.
        Chapter 9: fail-closed.
        """
        response_lower = response.lower()

        for pattern in self.HARMFUL_PATTERNS:
            if re.search(pattern, response_lower):
                return CheckResult(
                    name="output_moderation",
                    status=GuardrailStatus.BLOCKED,
                    reason="Output contains harmful content",
                    score=0.0,
                )

        return CheckResult(
            name="output_moderation",
            status=GuardrailStatus.PASSED,
            reason="Output appears safe",
            score=1.0,
        )
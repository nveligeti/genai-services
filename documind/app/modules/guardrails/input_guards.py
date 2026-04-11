# app/modules/guardrails/input_guards.py
# Chapter 9: input guardrails — topical, injection, moderation

import re
from app.modules.guardrails.schemas import (
    CheckResult,
    GuardrailStatus,
)
from app.providers.llm import MockLLMClient


class TopicalGuard:
    """
    Ensures queries are relevant to document Q&A.
    Chapter 9: fail-open — service stays up if guard fails.
    """

    # Keywords that suggest document-relevant queries
    RELEVANT_PATTERNS = [
        r"\bdocument\b", r"\bfile\b", r"\bcontract\b",
        r"\breport\b", r"\bsummary\b", r"\bwhat\b",
        r"\bhow\b", r"\bwhen\b", r"\bwhere\b", r"\bwho\b",
        r"\bexplain\b", r"\bdescribe\b", r"\blist\b",
        r"\bfind\b", r"\bshow\b", r"\btell\b",
    ]

    # Patterns that suggest off-topic requests
    OFF_TOPIC_PATTERNS = [
        r"\bwrite (me )?(a |an )?(poem|song|story|joke)\b",
        r"\bplay (a game|chess|tic-tac-toe)\b",
        r"\bwhat is \d+ [+\-*/] \d+\b",
        r"\btranslate (this |the )?(following )?\w+ to\b",
    ]

    async def check(self, query: str) -> CheckResult:
        """
        Check if query is relevant to document Q&A.
        Chapter 9: fail-open on exception.
        """
        try:
            query_lower = query.lower()

            # Check for explicit off-topic patterns
            for pattern in self.OFF_TOPIC_PATTERNS:
                if re.search(pattern, query_lower):
                    return CheckResult(
                        name="topical_guard",
                        status=GuardrailStatus.BLOCKED,
                        reason=(
                            "Query appears unrelated to "
                            "document analysis"
                        ),
                        score=0.1,
                    )

            return CheckResult(
                name="topical_guard",
                status=GuardrailStatus.PASSED,
                reason="Query appears document-relevant",
                score=0.9,
            )

        except Exception as e:
            # Fail-open — don't block if guard errors
            return CheckResult(
                name="topical_guard",
                status=GuardrailStatus.SKIPPED,
                reason=f"Guard error (fail-open): {e}",
                score=0.5,
            )


class PromptInjectionGuard:
    """
    Detects prompt injection attempts.
    Chapter 9: FAIL-CLOSED — security critical.
    """

    INJECTION_PATTERNS = [
        r"ignore (all )?(previous|prior|above) instructions",
        r"disregard (all )?(previous|prior|above)",
        r"you are now",
        r"new (persona|role|identity|instructions)",
        r"(system|admin|root|developer) (prompt|mode|access)",
        r"jailbreak",
        r"dan mode",
        r"override (your )?(instructions|guidelines|rules)",
        r"forget (everything|all|your instructions)",
        r"pretend (you are|to be)",
        r"act as (if )?you (are|have no)",
        r"<(system|instructions|prompt)>",
        r"\[INST\]",
        r"###\s*(system|instruction)",
    ]

    async def check(self, query: str) -> CheckResult:
        """
        Detect prompt injection patterns.
        Chapter 9: fail-closed — blocks on any detection.
        """
        query_lower = query.lower()

        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, query_lower):
                return CheckResult(
                    name="injection_guard",
                    status=GuardrailStatus.BLOCKED,
                    reason=(
                        "Potential prompt injection detected"
                    ),
                    score=0.0,
                )

        return CheckResult(
            name="injection_guard",
            status=GuardrailStatus.PASSED,
            reason="No injection patterns detected",
            score=1.0,
        )


class InputModerationGuard:
    """
    Checks input for harmful or inappropriate content.
    Chapter 9: fail-closed — safety critical.
    """

    HARMFUL_PATTERNS = [
        r"\b(how to|instructions for|guide to) "
        r"(make|create|build) (a |an )?(bomb|weapon|explosive)",
        r"\b(kill|harm|hurt|attack|threaten) "
        r"(someone|people|person|user)",
        r"\b(hate speech|slurs?)\b",
        r"\bself.harm\b",
        r"\b(drug|weapon) (synthesis|manufacturing|production)\b",
    ]

    async def check(self, query: str) -> CheckResult:
        """
        Check input for harmful content.
        Chapter 9: fail-closed — blocks detected harm.
        """
        query_lower = query.lower()

        for pattern in self.HARMFUL_PATTERNS:
            if re.search(pattern, query_lower):
                return CheckResult(
                    name="input_moderation",
                    status=GuardrailStatus.BLOCKED,
                    reason=(
                        "Input contains potentially harmful content"
                    ),
                    score=0.0,
                )

        return CheckResult(
            name="input_moderation",
            status=GuardrailStatus.PASSED,
            reason="Input appears safe",
            score=1.0,
        )
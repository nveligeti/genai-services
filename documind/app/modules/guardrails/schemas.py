# app/modules/guardrails/schemas.py
# Chapter 9: type-safe guardrail results

from enum import Enum
from pydantic import BaseModel, Field
from typing import Annotated


class GuardrailStatus(str, Enum):
    PASSED = "passed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"   # guard failed but fail-open


class CheckResult(BaseModel):
    """Result of a single guardrail check."""
    name: str
    status: GuardrailStatus
    reason: str = ""
    score: float = Field(default=1.0, ge=0.0, le=1.0)


class GuardrailResult(BaseModel):
    """
    Aggregated result of all guardrail checks.
    Chapter 9: all checks run in parallel then aggregated.
    """
    passed: bool
    checks: list[CheckResult]
    blocked_by: str | None = None   # name of blocking check

    @property
    def failure_reason(self) -> str:
        if self.blocked_by:
            blocked = next(
                (c for c in self.checks
                 if c.name == self.blocked_by),
                None,
            )
            return blocked.reason if blocked else "Unknown"
        return ""
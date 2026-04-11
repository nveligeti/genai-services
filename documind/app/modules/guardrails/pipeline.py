# app/modules/guardrails/pipeline.py
# Chapter 9: parallel guardrail execution with asyncio.gather

import asyncio
from loguru import logger
from app.modules.guardrails.input_guards import (
    InputModerationGuard,
    PromptInjectionGuard,
    TopicalGuard,
)
from app.modules.guardrails.output_guards import (
    HallucinationGuard,
    OutputModerationGuard,
)
from app.modules.guardrails.schemas import (
    CheckResult,
    GuardrailResult,
    GuardrailStatus,
)


class GuardrailPipeline:
    """
    Runs input and output guardrails in parallel.

    Chapter 9: asyncio.gather() for parallel execution.
    Fail-fast: stops on first BLOCKED result.
    """

    def __init__(self) -> None:
        self.topical       = TopicalGuard()
        self.injection     = PromptInjectionGuard()
        self.input_mod     = InputModerationGuard()
        self.hallucination = HallucinationGuard()
        self.output_mod    = OutputModerationGuard()

    async def check_input(
        self, query: str
    ) -> GuardrailResult:
        """
        Run all input guards in parallel.
        Chapter 9: asyncio.gather — all run simultaneously.
        Returns immediately on first BLOCKED result.
        """
        logger.debug(
            f"Running input guardrails | "
            f"query='{query[:50]}'"
        )

        # Run ALL input guards in parallel
        results: list[CheckResult] = await asyncio.gather(
            self.topical.check(query),
            self.injection.check(query),
            self.input_mod.check(query),
        )

        return self._aggregate(results)

    async def check_output(
        self,
        response: str,
        context: str = "",
    ) -> GuardrailResult:
        """
        Run all output guards in parallel.
        Chapter 9: parallel output validation.
        """
        logger.debug("Running output guardrails")

        results: list[CheckResult] = await asyncio.gather(
            self.hallucination.check(response, context),
            self.output_mod.check(response),
        )

        return self._aggregate(results)

    def _aggregate(
        self, results: list[CheckResult]
    ) -> GuardrailResult:
        """
        Aggregate individual check results.
        Any BLOCKED → overall blocked.
        """
        blocked = next(
            (r for r in results
             if r.status == GuardrailStatus.BLOCKED),
            None,
        )

        if blocked:
            logger.warning(
                f"Guardrail BLOCKED | "
                f"check={blocked.name} | "
                f"reason={blocked.reason}"
            )
            return GuardrailResult(
                passed=False,
                checks=results,
                blocked_by=blocked.name,
            )

        return GuardrailResult(
            passed=True,
            checks=results,
            blocked_by=None,
        )


# ── Singleton factory ─────────────────────────────────────────────

_pipeline: GuardrailPipeline | None = None


def get_guardrail_pipeline() -> GuardrailPipeline:
    """Chapter 2: DI factory for GuardrailPipeline."""
    global _pipeline
    if _pipeline is None:
        _pipeline = GuardrailPipeline()
    return _pipeline


def reset_guardrail_pipeline() -> None:
    """Reset singleton — used in tests."""
    global _pipeline
    _pipeline = None
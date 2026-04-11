# tests/unit/test_prompt_builder.py
# Chapter 11: unit tests for prompt builder

import pytest
from app.modules.chat.prompt_builder import (
    build_system_prompt,
    count_tokens,
    estimate_cost,
)


class TestPromptBuilder:

    def test_builds_prompt_with_context(self):
        """Chapter 11: context injected into prompt."""
        prompt = build_system_prompt(
            context="Contract says payment is net 30"
        )
        assert "net 30" in prompt
        assert "Role" in prompt
        assert "Context" in prompt
        assert "Task" in prompt

    def test_builds_base_prompt_without_context(self):
        """Chapter 11: no context → base prompt."""
        prompt = build_system_prompt(context=None)
        assert "Role" in prompt
        assert "{context}" not in prompt

    def test_builds_base_prompt_for_no_context_string(self):
        """
        Chapter 11: boundary — 'No relevant context'
        triggers base prompt.
        """
        prompt = build_system_prompt(
            context="No relevant context found in documents."
        )
        assert "{context}" not in prompt

    def test_count_tokens_returns_positive_int(self):
        """Chapter 11: token count > 0 for any text."""
        count = count_tokens("Hello world")
        assert count > 0
        assert isinstance(count, int)

    def test_count_tokens_scales_with_length(self):
        """
        IT — longer text = more tokens.
        Chapter 11: directional test.
        """
        short = count_tokens("hi")
        long = count_tokens("hi " * 100)
        assert long > short

    def test_estimate_cost_zero_for_mock(self):
        """Chapter 11: mock model has zero cost."""
        cost = estimate_cost(100, 200, "mock-gpt")
        assert cost == 0.0

    def test_estimate_cost_positive_for_real_model(self):
        """Chapter 11: real models have positive cost."""
        cost = estimate_cost(100, 200, "gpt-4o")
        assert cost > 0.0

    @pytest.mark.parametrize("text,expected_min", [
        ("a" * 4,   1),
        ("a" * 100, 20),
        ("a" * 400, 90),
    ])
    def test_token_count_boundaries(
        self, text, expected_min
    ):
        """Chapter 11: parametrize token count boundaries."""
        count = count_tokens(text)
        assert count >= expected_min


class TestStructuredOutput:

    def test_document_answer_valid(self):
        """Chapter 4: Pydantic validation."""
        from app.modules.chat.structured_output import (
            DocumentAnswer,
        )
        answer = DocumentAnswer(
            answer="Net 30 days",
            answer_found=True,
            confidence=0.95,
            source_document="contract.pdf",
        )
        assert answer.answer_found is True
        assert 0.0 <= answer.confidence <= 1.0

    def test_confidence_boundary_validation(self):
        """Chapter 11: boundary — confidence 0-1."""
        from pydantic import ValidationError
        from app.modules.chat.structured_output import (
            DocumentAnswer,
        )
        with pytest.raises(ValidationError):
            DocumentAnswer(
                answer="test",
                answer_found=True,
                confidence=1.5,   # over 1.0
            )

    def test_token_usage_calculate(self):
        """Chapter 10: token calculation."""
        from app.modules.chat.structured_output import (
            TokenUsage,
        )
        usage = TokenUsage.calculate(
            prompt="What are the payment terms?",
            response="Payment is due in 30 days.",
            model="mock-gpt",
        )
        assert usage.total_tokens > 0
        assert usage.prompt_tokens > 0
        assert usage.completion_tokens > 0
        assert usage.estimated_cost_usd == 0.0
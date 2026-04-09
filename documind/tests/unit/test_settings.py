# tests/unit/test_settings.py
# Chapter 11: Unit tests for Pydantic settings validation
# Chapter 4: Type safety verification

import pytest
from pydantic import ValidationError
from app.settings import Settings


class TestSettings:
    """
    Unit tests for Settings validation.

    Chapter 11 patterns used:
    - Invalid data testing (boundary violations)
    - Valid data testing (happy path)
    - Property-based assertions
    """

    def test_default_settings_are_valid(self) -> None:
        """Valid settings must initialize without errors."""
        settings = Settings(
            secret_key="a-valid-secret-key-that-is-32-chars-long"
        )
        assert settings.app_name == "DocuMind"
        assert settings.environment == "development"
        assert settings.llm_provider == "mock"

    def test_secret_key_too_short_raises_validation_error(self) -> None:
        """
        Chapter 11: boundary test — below minimum length.
        Chapter 4: Field(min_length=32) enforced at runtime.
        """
        with pytest.raises(ValidationError) as exc_info:
            Settings(secret_key="too-short")
        assert "min_length" in str(exc_info.value).lower() \
            or "secret_key" in str(exc_info.value).lower()

    def test_llm_temperature_too_high_raises_error(self) -> None:
        """
        Chapter 11: boundary test — above maximum value.
        Chapter 4: Field(le=1.0) enforced.
        """
        with pytest.raises(ValidationError):
            Settings(
                secret_key="a-valid-secret-key-that-is-32-chars-long",
                llm_temperature=1.5,
            )

    def test_llm_temperature_too_low_raises_error(self) -> None:
        """
        Chapter 11: boundary test — below minimum value.
        Chapter 4: Field(ge=0.0) enforced.
        """
        with pytest.raises(ValidationError):
            Settings(
                secret_key="a-valid-secret-key-that-is-32-chars-long",
                llm_temperature=-0.1,
            )

    def test_llm_temperature_at_boundary_values_passes(self) -> None:
        """
        Chapter 11: boundary test — exactly at limits must pass.
        """
        for temp in [0.0, 1.0]:
            settings = Settings(
                secret_key="a-valid-secret-key-that-is-32-chars-long",
                llm_temperature=temp,
            )
            assert settings.llm_temperature == temp

    def test_invalid_environment_raises_error(self) -> None:
        """
        Chapter 11: invalid data test — unsupported environment.
        Chapter 4: Literal type enforced.
        """
        with pytest.raises(ValidationError):
            Settings(
                secret_key="a-valid-secret-key-that-is-32-chars-long",
                environment="staging",  # not in Literal
            )

    def test_is_production_true_when_environment_is_production(self) -> None:
        """Chapter 11: property-based assertion."""
        settings = Settings(
            secret_key="a-valid-secret-key-that-is-32-chars-long",
            environment="production",
        )
        assert settings.is_production is True
        assert settings.is_testing is False

    def test_is_testing_true_when_environment_is_testing(self) -> None:
        """Chapter 11: property-based assertion."""
        settings = Settings(
            secret_key="a-valid-secret-key-that-is-32-chars-long",
            environment="testing",
        )
        assert settings.is_testing is True
        assert settings.is_production is False

    def test_is_production_false_in_development(self) -> None:
        """Chapter 11: valid data — default environment check."""
        settings = Settings(
            secret_key="a-valid-secret-key-that-is-32-chars-long",
        )
        assert settings.is_production is False
        assert settings.is_testing is False

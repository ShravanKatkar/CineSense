import pytest
from pydantic import ValidationError
from app.core.config import Settings, get_settings


def test_settings_load():
    settings = get_settings()
    assert settings.environment in ("development", "production", "test")
    assert settings.jwt_algorithm == "HS256"
    assert settings.access_token_minutes == 15


def test_jwt_secret_length_validation():
    # Valid 32+ character key
    valid_settings = Settings(jwt_secret_key="0123456789abcdef0123456789abcdef")
    assert len(valid_settings.jwt_secret_key.get_secret_value()) >= 32

    # Invalid short key should raise ValidationError
    with pytest.raises(ValidationError):
        Settings(jwt_secret_key="too_short_key")


def test_secret_string_masking():
    settings = Settings(anthropic_api_key="sk-ant-secret-12345")
    # Repr of SecretStr must not contain the plain secret value
    assert "sk-ant-secret-12345" not in repr(settings.anthropic_api_key)
    assert settings.anthropic_api_key.get_secret_value() == "sk-ant-secret-12345"

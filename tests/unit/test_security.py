import pytest
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_hashing():
    raw_password = "correct-horse-battery-staple"
    hashed = hash_password(raw_password)

    assert hashed != raw_password
    assert verify_password(raw_password, hashed) is True
    assert verify_password("wrong-password", hashed) is False


def test_jwt_token_flow():
    token = create_access_token(user_id=42, email="user@example.com")
    payload = decode_token(token)

    assert payload["sub"] == "42"
    assert payload["email"] == "user@example.com"
    assert payload["type"] == "access"

    refresh = create_refresh_token(user_id=42, jti="test-jti-12345")
    refresh_payload = decode_token(refresh)
    assert refresh_payload["sub"] == "42"
    assert refresh_payload["jti"] == "test-jti-12345"
    assert refresh_payload["type"] == "refresh"

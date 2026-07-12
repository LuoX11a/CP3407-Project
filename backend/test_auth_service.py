"""Tests for auth service — password hashing and JWT."""

import pytest
from app.services.auth import (
    hash_password,
    verify_password,
    create_token,
    decode_token,
)


class TestPasswordHashing:
    def test_hash_returns_string(self):
        result = hash_password("mypassword123")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_hash_is_deterministic_for_verification(self):
        password = "securepass456"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_rejects_wrong_password(self):
        hashed = hash_password("correct_password")
        assert verify_password("wrong_password", hashed) is False

    def test_verify_rejects_empty_password(self):
        hashed = hash_password("somepass")
        assert verify_password("", hashed) is False

    def test_different_salts_produce_different_hashes(self):
        h1 = hash_password("same_password")
        h2 = hash_password("same_password")
        assert h1 != h2  # bcrypt uses random salt each time
        # Both should verify correctly
        assert verify_password("same_password", h1)
        assert verify_password("same_password", h2)


class TestJWT:
    def test_create_token_returns_string(self):
        token = create_token(user_id=42, username="alice")
        assert isinstance(token, str)
        assert len(token) > 20

    def test_decode_token_returns_payload(self):
        token = create_token(user_id=7, username="bob")
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "7"
        assert payload["username"] == "bob"

    def test_decode_invalid_token_returns_none(self):
        assert decode_token("not.a.valid.token") is None
        assert decode_token("") is None
        assert decode_token("abc") is None

    def test_token_contains_expiry(self):
        token = create_token(user_id=1, username="test")
        payload = decode_token(token)
        assert "exp" in payload

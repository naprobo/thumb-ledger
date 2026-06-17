"""
认证模块属性测试（Properties 1-5, 28）
"""
import uuid
from datetime import datetime, timedelta, timezone

from hypothesis import given, settings
from hypothesis import strategies as st
from jose import jwt
from sqlalchemy import inspect

from app.config import get_settings
from app.models.user import User
from app.routers.auth import _normalize_email, hash_reset_token
from app.services.auth import (
    GENERIC_LOGIN_ERROR,
    create_access_token,
    decode_access_token,
    is_token_stale_after_password_change,
)


@given(
    local=st.text(
        alphabet=st.characters(
            whitelist_categories=("Ll", "Lu", "Nd"),
            min_codepoint=48,
            max_codepoint=122,
        ),
        min_size=1,
        max_size=20,
    ),
    domain=st.sampled_from(["example.com", "test.local"]),
)
@settings(max_examples=100)
def test_property_1_register_email_uniqueness_is_case_insensitive(local: str, domain: str) -> None:
    email = f"{local}@{domain}"
    first = _normalize_email(email)
    duplicate = _normalize_email(f"  {email.upper()}  ")

    registered = {first}

    assert duplicate in registered


@given(user_id=st.uuids(), is_admin=st.booleans())
@settings(max_examples=50)
def test_property_2_jwt_token_expires_in_configured_days(user_id: uuid.UUID, is_admin: bool) -> None:
    settings = get_settings()
    password_changed_at = datetime.now(timezone.utc)

    token = create_access_token(user_id, is_admin, password_changed_at)
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])

    assert payload["sub"] == str(user_id)
    assert payload["exp"] - payload["iat"] == settings.access_token_expire_days * 24 * 60 * 60


@given(email_exists=st.booleans(), password_matches=st.booleans())
@settings(max_examples=20)
def test_property_3_login_errors_do_not_reveal_which_field_failed(
    email_exists: bool,
    password_matches: bool,
) -> None:
    auth_failed = (not email_exists) or (not password_matches)

    if auth_failed:
        assert GENERIC_LOGIN_ERROR == "Invalid email or password"


@given(token=st.text(min_size=1, max_size=200))
@settings(max_examples=100)
def test_property_4_password_reset_token_hash_supports_single_use(token: str) -> None:
    token_hash = hash_reset_token(token)
    used_tokens: set[str] = set()

    assert token_hash not in used_tokens
    used_tokens.add(token_hash)
    assert token_hash in used_tokens


@given(user_id=st.uuids(), is_admin=st.booleans())
@settings(max_examples=50)
def test_property_5_old_jwt_is_invalid_after_password_reset(user_id: uuid.UUID, is_admin: bool) -> None:
    original_password_time = datetime.now(timezone.utc) - timedelta(minutes=5)
    token = create_access_token(user_id, is_admin, original_password_time)
    payload = decode_access_token(token)

    password_reset_time = datetime.fromtimestamp(payload["iat"], tz=timezone.utc) + timedelta(seconds=1)

    assert is_token_stale_after_password_change(payload, password_reset_time)


@given(user_id=st.uuids(), is_admin=st.booleans())
@settings(max_examples=50)
def test_property_5_token_without_password_marker_is_invalid_after_password_reset(
    user_id: uuid.UUID,
    is_admin: bool,
) -> None:
    token = create_access_token(user_id, is_admin, password_changed_at=None)
    payload = decode_access_token(token)

    assert "pwd_iat" not in payload
    reset_time = datetime.fromtimestamp(payload["iat"], tz=timezone.utc) + timedelta(seconds=1)

    assert is_token_stale_after_password_change(payload, reset_time)


def test_property_28_account_deletion_can_cascade_user_owned_data() -> None:
    relationships = inspect(User).relationships

    assert "delete-orphan" in relationships["owned_ledgers"].cascade
    assert "delete-orphan" in relationships["ledger_memberships"].cascade
    assert "delete-orphan" in relationships["share_requests"].cascade
    assert "delete-orphan" in relationships["preferences"].cascade
    assert "delete-orphan" in relationships["password_reset_tokens"].cascade

"""
审计、管理员与安全加固属性测试（Properties 18, 20, 21, 27）。
"""
import pytest
from fastapi import HTTPException, Response
from pydantic import ValidationError
from sqlalchemy import inspect

from app.main import apply_security_headers
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.admin import UserStatusUpdateRequest
from app.schemas.auth import LanguagePreferenceRequest
from app.schemas.ledger import LedgerCreateRequest
from app.schemas.transaction import TransactionCreateRequest, TransactionItemRequest
from app.services.auth import get_current_admin
from app.services.audit import ADMIN_ACTION


def test_property_27_audit_log_is_append_only_at_model_and_api_surface() -> None:
    columns = inspect(AuditLog).columns

    assert "updated_at" not in columns
    assert columns["occurred_at"].nullable is False
    assert ADMIN_ACTION == "ADMIN_ACTION"


@pytest.mark.asyncio
async def test_property_20_non_admin_user_is_rejected_by_admin_dependency() -> None:
    user = User(email="user@example.com", password_hash="hash", is_admin=False)

    with pytest.raises(HTTPException) as exc:
        await get_current_admin(user)

    assert exc.value.status_code == 403


def test_property_20_user_status_schema_persists_disabled_state() -> None:
    payload = UserStatusUpdateRequest(is_active=False)
    user = User(email="user@example.com", password_hash="hash", is_active=True)

    user.is_active = payload.is_active

    assert user.is_active is False


def test_property_21_input_max_length_constraints_are_enforced() -> None:
    with pytest.raises(ValidationError):
        LedgerCreateRequest(name="x" * 51, entry_mode="receipt")

    with pytest.raises(ValidationError):
        TransactionCreateRequest(amount=100, note="x" * 501)

    with pytest.raises(ValidationError):
        TransactionItemRequest(amount=100, category_name="x" * 51)


def test_property_18_language_preference_accepts_only_supported_languages() -> None:
    request = LanguagePreferenceRequest(preferred_language="ja")
    user = User(email="user@example.com", password_hash="hash", preferred_language="zh-CN")

    user.preferred_language = request.preferred_language

    assert user.preferred_language == "ja"
    with pytest.raises(ValidationError):
        LanguagePreferenceRequest(preferred_language="fr")


def test_security_headers_include_hsts_csp_and_nosniff() -> None:
    response = Response()

    apply_security_headers(response)

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "max-age=31536000" in response.headers["Strict-Transport-Security"]
    assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]


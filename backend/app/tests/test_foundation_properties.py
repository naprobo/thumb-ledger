"""
4.1/4.2 基础设施测试。
"""
import pytest
from pydantic import ValidationError
from sqlalchemy import inspect

from app.middleware.content_type import is_supported_content_type
from app.models.notification import Notification
from app.models.user import User
from app.schemas.auth import RegisterRequest
from app.services.audit import (
    ADMIN_ACTION,
    LEDGER_SHARE_APPROVED,
    LEDGER_SHARE_REJECTED,
    LEDGER_SHARED_USER_REMOVED,
)


def test_notification_model_is_related_to_user_with_delete_orphan_cascade() -> None:
    user_relationships = inspect(User).relationships
    notification_columns = inspect(Notification).columns

    assert "notifications" in user_relationships
    assert "delete-orphan" in user_relationships["notifications"].cascade
    assert notification_columns["user_id"].nullable is False
    assert notification_columns["type"].nullable is False
    assert notification_columns["status"].nullable is False


def test_audit_service_exposes_cross_module_event_names() -> None:
    assert LEDGER_SHARE_APPROVED == "LEDGER_SHARE_APPROVED"
    assert LEDGER_SHARE_REJECTED == "LEDGER_SHARE_REJECTED"
    assert LEDGER_SHARED_USER_REMOVED == "LEDGER_SHARED_USER_REMOVED"
    assert ADMIN_ACTION == "ADMIN_ACTION"


@pytest.mark.parametrize(
    "content_type",
    [
        "application/json",
        "application/json; charset=utf-8",
        "multipart/form-data; boundary=abc",
        "application/x-www-form-urlencoded",
    ],
)
def test_supported_content_types_are_accepted(content_type: str) -> None:
    assert is_supported_content_type(content_type)


@pytest.mark.parametrize(
    "content_type",
    [None, "", "text/plain", "application/xml", "text/html; charset=utf-8"],
)
def test_unexpected_content_types_are_rejected(content_type: str | None) -> None:
    assert not is_supported_content_type(content_type)


def test_auth_schema_rejects_excessively_long_string_fields() -> None:
    with pytest.raises(ValidationError):
        RegisterRequest(
            email=f"{'a' * 250}@example.com",
            password="valid-password",
        )

    with pytest.raises(ValidationError):
        RegisterRequest(
            email="user@example.com",
            password="a" * 129,
        )

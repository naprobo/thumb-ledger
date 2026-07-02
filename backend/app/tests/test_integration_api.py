"""
Integration tests for the main API acceptance flows.
"""
from __future__ import annotations

import csv
import uuid
from datetime import date, datetime, timezone
from io import StringIO

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app import database
from app.database import get_db, get_session_factory
from app.main import create_app
from app.models.ledger import Ledger, ShareRequest
from app.models.recurring import RecurringTransaction
from app.models.suggestion import SuggestionVote
from app.models.transaction import Transaction
from app.models.user import User
from app.routers import auth as auth_router
from app.services.rate_limit import login_failed_limiter, password_reset_limiter, register_limiter
from app.services.recurring import generate_due_recurring_transactions


API_PREFIX = "/api/v1"
PASSWORD = "password123"
NEW_PASSWORD = "new-password123"


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    database._engine = None
    database._async_session_factory = None
    session_factory = get_session_factory()
    async with session_factory() as session:
        transaction = await session.begin()
        try:
            yield session
        finally:
            if transaction.is_active:
                await transaction.rollback()
    if database._engine is not None:
        await database._engine.dispose()
        database._engine = None
        database._async_session_factory = None


@pytest_asyncio.fixture
async def client(db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch) -> AsyncClient:
    app = create_app()

    async def override_get_db():
        yield db_session

    async def skip_password_reset_email(*args, **kwargs) -> None:
        return None

    for limiter in (login_failed_limiter, password_reset_limiter, register_limiter):
        limiter._events.clear()

    monkeypatch.setattr(auth_router, "send_password_reset_email", skip_password_reset_email)
    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as api_client:
        yield api_client
    app.dependency_overrides.clear()


def unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}@example.com"


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def register_user(client: AsyncClient, email: str, password: str = PASSWORD) -> dict:
    response = await client.post(
        f"{API_PREFIX}/auth/register",
        json={"email": email, "password": password},
    )
    assert response.status_code == 201, response.text
    return response.json()


async def register_user_with_nickname(
    client: AsyncClient,
    email: str,
    nickname: str,
    password: str = PASSWORD,
) -> dict:
    response = await client.post(
        f"{API_PREFIX}/auth/register",
        json={"email": email, "password": password, "nickname": nickname},
    )
    assert response.status_code == 201, response.text
    return response.json()


async def login_user(client: AsyncClient, email: str, password: str = PASSWORD) -> str:
    response = await client.post(
        f"{API_PREFIX}/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


async def create_ledger(client: AsyncClient, token: str, name: str = "Integration Ledger") -> dict:
    response = await client.post(
        f"{API_PREFIX}/ledgers",
        headers=auth_headers(token),
        json={
            "name": name,
            "entry_mode": "receipt",
            "subject_enabled": False,
            "subject_step_mode": "disabled",
            "necessity_step_mode": "required",
            "default_currency_code": "JPY",
            "timezone": "Asia/Tokyo",
            "budget_enabled": False,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


async def create_transaction(
    client: AsyncClient,
    token: str,
    ledger_id: str,
    amount: int = 1200,
    note: str = "integration purchase",
    location_name: str | None = None,
) -> dict:
    response = await client.post(
        f"{API_PREFIX}/ledgers/{ledger_id}/transactions",
        headers=auth_headers(token),
        json={
            "amount": amount,
            "currency_code": "JPY",
            "transaction_date": "2026-06-12",
            "necessity": "essential",
            "note": note,
            "location_name": location_name,
            "items": [],
            "subject_ids": [],
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


@pytest.mark.asyncio
async def test_auth_flow_password_reset_invalidates_old_jwt_and_account_delete(
    client: AsyncClient,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    email = unique_email("auth-flow")
    known_reset_token = "known-reset-token"
    monkeypatch.setattr(auth_router.secrets, "token_urlsafe", lambda _: known_reset_token)

    registered = await register_user(client, email)
    user_id = registered["id"]

    duplicate = await client.post(
        f"{API_PREFIX}/auth/register",
        json={"email": email.upper(), "password": PASSWORD},
    )
    assert duplicate.status_code == 409

    old_token = await login_user(client, email)
    me = await client.get(f"{API_PREFIX}/auth/me", headers=auth_headers(old_token))
    assert me.status_code == 200
    assert me.json()["email"] == email

    reset_request = await client.post(
        f"{API_PREFIX}/auth/password-reset/request",
        json={"email": email},
    )
    assert reset_request.status_code == 200

    reset_confirm = await client.post(
        f"{API_PREFIX}/auth/password-reset/confirm",
        json={"token": known_reset_token, "new_password": NEW_PASSWORD},
    )
    assert reset_confirm.status_code == 200

    stale_me = await client.get(f"{API_PREFIX}/auth/me", headers=auth_headers(old_token))
    assert stale_me.status_code == 401

    new_token = await login_user(client, email, NEW_PASSWORD)
    delete_response = await client.request(
        "DELETE",
        f"{API_PREFIX}/auth/account",
        headers=auth_headers(new_token),
        json={"password": NEW_PASSWORD},
    )
    assert delete_response.status_code == 200

    deleted_me = await client.get(f"{API_PREFIX}/auth/me", headers=auth_headers(new_token))
    assert deleted_me.status_code == 401
    assert await db_session.scalar(select(User).where(User.id == uuid.UUID(user_id))) is None


@pytest.mark.asyncio
async def test_profile_nickname_and_password_change(client: AsyncClient) -> None:
    email = unique_email("profile")
    registered = await register_user_with_nickname(client, email, "Tester")
    assert registered["nickname"] == "Tester"
    assert registered["display_name"] == "Tester"

    token = await login_user(client, email)
    profile = await client.patch(
        f"{API_PREFIX}/auth/me/profile",
        headers=auth_headers(token),
        json={"nickname": "Ledger Friend"},
    )
    assert profile.status_code == 200, profile.text
    assert profile.json()["display_name"] == "Ledger Friend"

    change_password = await client.post(
        f"{API_PREFIX}/auth/me/change-password",
        headers=auth_headers(token),
        json={"current_password": PASSWORD, "new_password": NEW_PASSWORD},
    )
    assert change_password.status_code == 200, change_password.text

    stale_me = await client.get(f"{API_PREFIX}/auth/me", headers=auth_headers(token))
    assert stale_me.status_code == 401
    assert await login_user(client, email, NEW_PASSWORD)


@pytest.mark.asyncio
async def test_share_notifications_and_member_role_updates(client: AsyncClient) -> None:
    owner_email = unique_email("owner")
    member_email = unique_email("member")
    await register_user_with_nickname(client, owner_email, "Owner")
    member = await register_user_with_nickname(client, member_email, "Member")
    owner_token = await login_user(client, owner_email)
    member_token = await login_user(client, member_email)
    ledger = await create_ledger(client, owner_token, "Shared Ledger")

    share_code = await client.get(
        f"{API_PREFIX}/ledgers/{ledger['id']}/share-code",
        headers=auth_headers(owner_token),
    )
    assert share_code.status_code == 200

    request = await client.post(
        f"{API_PREFIX}/ledgers/{share_code.json()['share_code']}/share-requests",
        headers=auth_headers(member_token),
        json={"role": "read-write"},
    )
    assert request.status_code == 201, request.text
    assert request.json()["requester_display_name"] == "Member"

    owner_unread = await client.get(f"{API_PREFIX}/notifications/unread-count", headers=auth_headers(owner_token))
    assert owner_unread.status_code == 200
    assert owner_unread.json()["unread_count"] == 1

    pending_notifications = await client.get(f"{API_PREFIX}/notifications", headers=auth_headers(member_token))
    assert pending_notifications.status_code == 200
    assert pending_notifications.json()[0]["type"] == "LEDGER_SHARE_PENDING"
    assert pending_notifications.json()[0]["payload"]["role"] == "read-write"

    requests = await client.get(
        f"{API_PREFIX}/ledgers/{ledger['id']}/share-requests",
        headers=auth_headers(owner_token),
    )
    assert requests.status_code == 200
    assert requests.json()[0]["requester_display_name"] == "Member"

    approve = await client.post(
        f"{API_PREFIX}/ledgers/{ledger['id']}/share-requests/{request.json()['id']}/approve",
        headers=auth_headers(owner_token),
    )
    assert approve.status_code == 200, approve.text

    member_notifications = await client.get(f"{API_PREFIX}/notifications", headers=auth_headers(member_token))
    assert member_notifications.status_code == 200
    assert member_notifications.json()[0]["type"] == "LEDGER_SHARE_APPROVED"

    members = await client.get(
        f"{API_PREFIX}/ledgers/{ledger['id']}/members",
        headers=auth_headers(owner_token),
    )
    assert members.status_code == 200
    assert members.json()[0]["display_name"] == "Member"

    update_role = await client.patch(
        f"{API_PREFIX}/ledgers/{ledger['id']}/members/{member['id']}",
        headers=auth_headers(owner_token),
        json={"role": "read-only"},
    )
    assert update_role.status_code == 200, update_role.text
    assert update_role.json()["role"] == "read-only"

    forbidden_write = await client.post(
        f"{API_PREFIX}/ledgers/{ledger['id']}/transactions",
        headers=auth_headers(member_token),
        json={
            "amount": 100,
            "currency_code": "JPY",
            "transaction_date": "2026-06-12",
            "necessity": "essential",
            "items": [],
            "subject_ids": [],
        },
    )
    assert forbidden_write.status_code == 403

    update_role_back = await client.patch(
        f"{API_PREFIX}/ledgers/{ledger['id']}/members/{member['id']}",
        headers=auth_headers(owner_token),
        json={"role": "read-write"},
    )
    assert update_role_back.status_code == 200
    shared_transaction = await create_transaction(client, member_token, ledger["id"], amount=100)

    owner_notifications = await client.get(f"{API_PREFIX}/notifications", headers=auth_headers(owner_token))
    assert owner_notifications.status_code == 200
    transaction_notification = next(
        notification for notification in owner_notifications.json()
        if notification["type"] == "LEDGER_TRANSACTION_CREATED"
    )
    assert transaction_notification["payload"]["transaction_id"] == shared_transaction["id"]
    assert transaction_notification["payload"]["recorder_display_name"] == "Member"

    mark_read = await client.post(
        f"{API_PREFIX}/notifications/{member_notifications.json()[0]['id']}/read",
        headers=auth_headers(member_token),
    )
    assert mark_read.status_code == 200
    member_unread = await client.get(f"{API_PREFIX}/notifications/unread-count", headers=auth_headers(member_token))
    assert member_unread.status_code == 200
    assert member_unread.json()["unread_count"] >= 1


@pytest.mark.asyncio
async def test_complete_bookkeeping_flow_creates_and_lists_transaction(client: AsyncClient) -> None:
    email = unique_email("bookkeeping")
    await register_user(client, email)
    token = await login_user(client, email)
    ledger = await create_ledger(client, token)
    transaction = await create_transaction(
        client,
        token,
        ledger["id"],
        amount=3456,
        location_name="Station Market",
    )

    updated = await client.patch(
        f"{API_PREFIX}/ledgers/{ledger['id']}/transactions/{transaction['id']}",
        headers=auth_headers(token),
        json={
            "amount": 3456,
            "currency_code": "JPY",
            "transaction_date": "2026-06-13",
            "necessity": "essential",
            "location_name": "Edited Market",
            "items": [{
                "category_name": "category.dining",
                "item_name": "item.restaurant",
                "amount": 3456,
                "currency_code": "JPY",
            }],
            "subject_ids": [],
        },
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["location_name"] == "Edited Market"
    assert updated.json()["items"][0]["item_name"] == "item.restaurant"
    assert updated.json()["updated_at"]

    response = await client.get(
        f"{API_PREFIX}/ledgers/{ledger['id']}/transactions",
        headers=auth_headers(token),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == transaction["id"]
    assert body["items"][0]["location_name"] == "Edited Market"
    assert body["page_total_amounts"] == {"JPY": 3456}

    locations = await client.get(
        f"{API_PREFIX}/ledgers/{ledger['id']}/preferences/locations",
        headers=auth_headers(token),
    )
    assert locations.status_code == 200
    assert set(locations.json()["items"]) == {"Station Market", "Edited Market"}


@pytest.mark.asyncio
async def test_subject_management_protects_presets_and_limits_custom_subjects(client: AsyncClient) -> None:
    email = unique_email("subjects")
    await register_user(client, email)
    token = await login_user(client, email)
    ledger_response = await client.post(
        f"{API_PREFIX}/ledgers",
        headers=auth_headers(token),
        json={
            "name": "Subject Ledger",
            "entry_mode": "receipt",
            "subject_enabled": True,
            "subject_step_mode": "required",
            "necessity_step_mode": "disabled",
            "default_currency_code": "JPY",
            "timezone": "Asia/Tokyo",
            "budget_enabled": False,
        },
    )
    assert ledger_response.status_code == 201, ledger_response.text
    ledger_id = ledger_response.json()["id"]

    subjects = await client.get(f"{API_PREFIX}/ledgers/{ledger_id}/subjects", headers=auth_headers(token))
    assert subjects.status_code == 200
    preset_subject = subjects.json()[0]
    assert preset_subject["is_preset"] is True

    protected = await client.delete(
        f"{API_PREFIX}/ledgers/{ledger_id}/subjects/{preset_subject['id']}",
        headers=auth_headers(token),
    )
    assert protected.status_code == 403
    after_rejected_delete = await client.get(f"{API_PREFIX}/ledgers/{ledger_id}/subjects", headers=auth_headers(token))
    assert preset_subject["id"] in {subject["id"] for subject in after_rejected_delete.json()}

    custom_ids = []
    for index in range(20):
        response = await client.post(
            f"{API_PREFIX}/ledgers/{ledger_id}/subjects",
            headers=auth_headers(token),
            json={"name": f"custom-{index}"},
        )
        assert response.status_code == 201, response.text
        custom_ids.append(response.json()["id"])

    over_limit = await client.post(
        f"{API_PREFIX}/ledgers/{ledger_id}/subjects",
        headers=auth_headers(token),
        json={"name": "custom-over-limit"},
    )
    assert over_limit.status_code == 409

    deleted = await client.delete(
        f"{API_PREFIX}/ledgers/{ledger_id}/subjects/{custom_ids[0]}",
        headers=auth_headers(token),
    )
    assert deleted.status_code == 200
    after_delete = await client.get(f"{API_PREFIX}/ledgers/{ledger_id}/subjects", headers=auth_headers(token))
    assert custom_ids[0] not in {subject["id"] for subject in after_delete.json()}


@pytest.mark.asyncio
async def test_custom_tags_rename_history_soft_hide_and_restore(client: AsyncClient) -> None:
    email = unique_email("editable-tags")
    await register_user(client, email)
    token = await login_user(client, email)
    headers = auth_headers(token)
    ledger_response = await client.post(
        f"{API_PREFIX}/ledgers",
        headers=headers,
        json={
            "name": "Editable Tags",
            "entry_mode": "receipt",
            "receipt_item_enabled": True,
            "location_step_mode": "optional",
            "subject_enabled": True,
            "subject_step_mode": "optional",
            "necessity_step_mode": "disabled",
            "default_currency_code": "JPY",
            "timezone": "Asia/Tokyo",
            "budget_enabled": False,
        },
    )
    assert ledger_response.status_code == 201, ledger_response.text
    ledger_id = ledger_response.json()["id"]

    subject = await client.post(
        f"{API_PREFIX}/ledgers/{ledger_id}/subjects",
        headers=headers,
        json={"name": "家族"},
    )
    assert subject.status_code == 201, subject.text
    subject_id = subject.json()["id"]

    item_tag = await client.post(
        f"{API_PREFIX}/ledgers/{ledger_id}/preferences/tags",
        headers=headers,
        json={"tag_type": "item", "name": "週末ランチ", "category": "category.dining"},
    )
    location_tag = await client.post(
        f"{API_PREFIX}/ledgers/{ledger_id}/preferences/tags",
        headers=headers,
        json={"tag_type": "location", "name": "駅前店"},
    )
    assert item_tag.status_code == 200, item_tag.text
    assert location_tag.status_code == 200, location_tag.text
    item_tag_id = item_tag.json()["id"]
    location_tag_id = location_tag.json()["id"]

    transaction = await client.post(
        f"{API_PREFIX}/ledgers/{ledger_id}/transactions",
        headers=headers,
        json={
            "amount": 1800,
            "currency_code": "JPY",
            "location_tag_id": location_tag_id,
            "items": [
                {
                    "category_name": "category.dining",
                    "item_tag_id": item_tag_id,
                    "amount": 1800,
                    "currency_code": "JPY",
                }
            ],
            "subject_ids": [subject_id],
        },
    )
    assert transaction.status_code == 201, transaction.text
    transaction_id = transaction.json()["id"]

    renamed_subject = await client.patch(
        f"{API_PREFIX}/ledgers/{ledger_id}/subjects/{subject_id}",
        headers=headers,
        json={"name": "家族全員"},
    )
    renamed_item = await client.patch(
        f"{API_PREFIX}/ledgers/{ledger_id}/preferences/tags/{item_tag_id}",
        headers=headers,
        json={"name": "休日ランチ"},
    )
    renamed_location = await client.patch(
        f"{API_PREFIX}/ledgers/{ledger_id}/preferences/tags/{location_tag_id}",
        headers=headers,
        json={"name": "中央駅前店"},
    )
    assert renamed_subject.status_code == 200, renamed_subject.text
    assert renamed_item.status_code == 200, renamed_item.text
    assert renamed_location.status_code == 200, renamed_location.text

    history = await client.get(
        f"{API_PREFIX}/ledgers/{ledger_id}/transactions/{transaction_id}",
        headers=headers,
    )
    assert history.status_code == 200, history.text
    assert history.json()["items"][0]["item_name"] == "休日ランチ"
    assert history.json()["location_name"] == "中央駅前店"
    assert history.json()["transaction_subjects"][0]["name"] == "家族全員"

    for path in (
        f"{API_PREFIX}/ledgers/{ledger_id}/subjects/{subject_id}",
        f"{API_PREFIX}/ledgers/{ledger_id}/preferences/tags/{item_tag_id}",
        f"{API_PREFIX}/ledgers/{ledger_id}/preferences/tags/{location_tag_id}",
    ):
        response = await client.delete(path, headers=headers)
        assert response.status_code == 200, response.text

    visible_subjects = await client.get(f"{API_PREFIX}/ledgers/{ledger_id}/subjects", headers=headers)
    visible_items = await client.get(
        f"{API_PREFIX}/ledgers/{ledger_id}/preferences/items/details",
        headers=headers,
        params={"category": "category.dining"},
    )
    visible_locations = await client.get(
        f"{API_PREFIX}/ledgers/{ledger_id}/preferences/locations/details",
        headers=headers,
    )
    assert subject_id not in {row["id"] for row in visible_subjects.json()}
    assert item_tag_id not in {row["id"] for row in visible_items.json()["items"]}
    assert location_tag_id not in {row["id"] for row in visible_locations.json()["items"]}

    restored_subject = await client.post(
        f"{API_PREFIX}/ledgers/{ledger_id}/subjects",
        headers=headers,
        json={"name": "家族全員"},
    )
    restored_item = await client.post(
        f"{API_PREFIX}/ledgers/{ledger_id}/preferences/tags",
        headers=headers,
        json={"tag_type": "item", "name": "休日ランチ", "category": "category.dining"},
    )
    restored_location = await client.post(
        f"{API_PREFIX}/ledgers/{ledger_id}/preferences/tags",
        headers=headers,
        json={"tag_type": "location", "name": "中央駅前店"},
    )
    assert restored_subject.json()["id"] == subject_id
    assert restored_item.json()["id"] == item_tag_id
    assert restored_location.json()["id"] == location_tag_id


@pytest.mark.asyncio
async def test_budget_upsert_accepts_default_and_explicit_category_allocations(client: AsyncClient) -> None:
    email = unique_email("budget-upsert")
    await register_user(client, email)
    token = await login_user(client, email)
    ledger = await create_ledger(client, token, "Budget Ledger")
    headers = auth_headers(token)

    default_budget = await client.post(
        f"{API_PREFIX}/ledgers/{ledger['id']}/budget",
        headers=headers,
        json={"monthly_total": 10000, "annual_total": 120000},
    )
    assert default_budget.status_code == 201, default_budget.text
    assert default_budget.json()["monthly_total"] == 10000
    assert default_budget.json()["annual_total"] == 120000
    assert default_budget.json()["categories"]

    split_budget = await client.post(
        f"{API_PREFIX}/ledgers/{ledger['id']}/budget",
        headers=headers,
        json={
            "monthly_total": 10000,
            "annual_total": 150000,
            "categories": [
                {"category": "category.food", "amount": 6000},
                {"category": "category.transport", "amount": 4000},
            ],
        },
    )
    assert split_budget.status_code == 201, split_budget.text
    assert split_budget.json()["annual_total"] == 150000
    assert {
        row["category"]: row["amount"] for row in split_budget.json()["categories"]
    } == {"category.food": 6000, "category.transport": 4000}

    for transaction_date, amount in (
        ("2020-01-15", 100),
        ("2020-02-15", 200),
        (date.today().isoformat(), 300),
    ):
        transaction = await client.post(
            f"{API_PREFIX}/ledgers/{ledger['id']}/transactions",
            headers=headers,
            json={
                "amount": amount,
                "currency_code": "JPY",
                "transaction_date": transaction_date,
                "necessity": "essential",
                "items": [],
                "subject_ids": [],
            },
        )
        assert transaction.status_code == 201, transaction.text

    january_budget = await client.get(
        f"{API_PREFIX}/ledgers/{ledger['id']}/budget",
        headers=headers,
        params={"target_month": "2020-01-01"},
    )
    february_budget = await client.get(
        f"{API_PREFIX}/ledgers/{ledger['id']}/budget",
        headers=headers,
        params={"target_month": "2020-02-01"},
    )
    assert january_budget.json()["progress"]["monthly_spent"] == 100
    assert february_budget.json()["progress"]["monthly_spent"] == 200

    ledgers = await client.get(f"{API_PREFIX}/ledgers", headers=headers)
    listed_ledger = next(row for row in ledgers.json() if row["id"] == ledger["id"])
    assert listed_ledger["current_month_amounts"] == {"JPY": 300}


@pytest.mark.asyncio
async def test_read_only_shared_member_cannot_write_transaction(client: AsyncClient) -> None:
    owner_email = unique_email("owner")
    reader_email = unique_email("reader")
    await register_user(client, owner_email)
    await register_user(client, reader_email)
    owner_token = await login_user(client, owner_email)
    reader_token = await login_user(client, reader_email)
    ledger = await create_ledger(client, owner_token, name="Shared Ledger")

    share_request_response = await client.post(
        f"{API_PREFIX}/ledgers/{ledger['id']}/share-requests",
        headers=auth_headers(reader_token),
        json={"role": "read-only"},
    )
    assert share_request_response.status_code == 201, share_request_response.text

    approve_response = await client.post(
        f"{API_PREFIX}/ledgers/{ledger['id']}/share-requests/{share_request_response.json()['id']}/approve",
        headers=auth_headers(owner_token),
    )
    assert approve_response.status_code == 200, approve_response.text

    forbidden = await client.post(
        f"{API_PREFIX}/ledgers/{ledger['id']}/transactions",
        headers=auth_headers(reader_token),
        json={
            "amount": 500,
            "currency_code": "JPY",
            "transaction_date": "2026-06-12",
            "necessity": "essential",
            "items": [],
            "subject_ids": [],
        },
    )
    assert forbidden.status_code == 403


@pytest.mark.asyncio
async def test_ledger_delete_cascades_transactions_and_share_requests(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    owner_email = unique_email("delete-owner")
    requester_email = unique_email("delete-requester")
    await register_user(client, owner_email)
    await register_user(client, requester_email)
    owner_token = await login_user(client, owner_email)
    requester_token = await login_user(client, requester_email)
    ledger = await create_ledger(client, owner_token, name="Delete Cascade Ledger")
    await create_transaction(client, owner_token, ledger["id"])

    share_request = await client.post(
        f"{API_PREFIX}/ledgers/{ledger['id']}/share-requests",
        headers=auth_headers(requester_token),
        json={"role": "read-write"},
    )
    assert share_request.status_code == 201, share_request.text

    delete_response = await client.delete(
        f"{API_PREFIX}/ledgers/{ledger['id']}",
        headers=auth_headers(owner_token),
    )
    assert delete_response.status_code == 200
    await db_session.flush()

    ledger_uuid = uuid.UUID(ledger["id"])
    assert await db_session.scalar(select(Ledger).where(Ledger.id == ledger_uuid)) is None
    assert await db_session.scalar(select(func.count()).select_from(Transaction).where(Transaction.ledger_id == ledger_uuid)) == 0
    assert await db_session.scalar(select(func.count()).select_from(ShareRequest).where(ShareRequest.ledger_id == ledger_uuid)) == 0


@pytest.mark.asyncio
async def test_account_delete_cascades_owned_ledgers_transactions_and_share_requests(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    owner_email = unique_email("account-owner")
    requester_email = unique_email("account-requester")
    await register_user(client, owner_email)
    await register_user(client, requester_email)
    owner_token = await login_user(client, owner_email)
    requester_token = await login_user(client, requester_email)
    ledger = await create_ledger(client, owner_token, name="Account Cascade Ledger")
    await create_transaction(client, owner_token, ledger["id"])
    share_request = await client.post(
        f"{API_PREFIX}/ledgers/{ledger['id']}/share-requests",
        headers=auth_headers(requester_token),
        json={"role": "read-only"},
    )
    assert share_request.status_code == 201, share_request.text

    delete_response = await client.request(
        "DELETE",
        f"{API_PREFIX}/auth/account",
        headers=auth_headers(owner_token),
        json={"password": PASSWORD},
    )
    assert delete_response.status_code == 200

    ledger_uuid = uuid.UUID(ledger["id"])
    assert await db_session.scalar(select(Ledger).where(Ledger.id == ledger_uuid)) is None
    assert await db_session.scalar(select(func.count()).select_from(Transaction).where(Transaction.ledger_id == ledger_uuid)) == 0
    assert await db_session.scalar(select(func.count()).select_from(ShareRequest).where(ShareRequest.ledger_id == ledger_uuid)) == 0


@pytest.mark.asyncio
async def test_csv_export_row_count_matches_transactions(client: AsyncClient) -> None:
    email = unique_email("csv")
    await register_user(client, email)
    token = await login_user(client, email)
    ledger = await create_ledger(client, token, name="CSV Ledger")
    await create_transaction(client, token, ledger["id"], amount=100, note="first")
    await create_transaction(client, token, ledger["id"], amount=200, note="second")

    response = await client.get(
        f"{API_PREFIX}/ledgers/{ledger['id']}/export",
        headers=auth_headers(token),
        params={"start_date": "2026-06-01", "end_date": "2026-06-30"},
    )
    assert response.status_code == 200
    assert "transactions.csv" in response.headers["content-disposition"]

    rows = list(csv.DictReader(StringIO(response.text)))
    assert len(rows) == 2
    assert {row["amount"] for row in rows} == {"100", "200"}
    assert {row["currency_code"] for row in rows} == {"JPY"}


@pytest.mark.asyncio
async def test_recurring_generation_creates_transaction_from_template(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    email = unique_email("recurring")
    await register_user(client, email)
    token = await login_user(client, email)
    ledger = await create_ledger(client, token, name="Recurring Ledger")
    ledger_id = ledger["id"]

    recurring_response = await client.post(
        f"{API_PREFIX}/ledgers/{ledger_id}/recurring",
        headers=auth_headers(token),
        json={
            "interval": "monthly",
            "next_run_date": "2026-07-01",
            "template_data": {
                "amount": 777,
                "currency_code": "JPY",
                "necessity": "non-essential",
                "note": "monthly template",
                "items": [],
                "subject_ids": [],
            },
        },
    )
    assert recurring_response.status_code == 201, recurring_response.text

    await generate_due_recurring_transactions(
        db_session,
        now_utc=datetime(2026, 7, 12, tzinfo=timezone.utc),
    )

    recurring = await db_session.scalar(
        select(RecurringTransaction).where(RecurringTransaction.id == uuid.UUID(recurring_response.json()["id"]))
    )
    assert recurring is not None
    assert recurring.next_run_date == date(2026, 8, 1)

    transaction = await db_session.scalar(
        select(Transaction).where(Transaction.recurring_transaction_id == recurring.id)
    )
    assert transaction is not None
    assert transaction.amount == 777
    assert transaction.currency_code == "JPY"
    assert transaction.transaction_date == date(2026, 7, 1)
    assert transaction.necessity == "non-essential"
    assert transaction.note == "monthly template"


@pytest.mark.asyncio
async def test_recurring_template_due_today_is_generated_immediately(
    client: AsyncClient,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.services import recurring as recurring_service

    monkeypatch.setattr(recurring_service, "ledger_today", lambda _timezone, _now_utc=None: date(2026, 6, 12))

    email = unique_email("recurring-immediate")
    await register_user(client, email)
    token = await login_user(client, email)
    ledger = await create_ledger(client, token, name="Recurring Immediate Ledger")
    ledger_id = ledger["id"]

    recurring_response = await client.post(
        f"{API_PREFIX}/ledgers/{ledger_id}/recurring",
        headers=auth_headers(token),
        json={
            "interval": "monthly",
            "next_run_date": "2026-06-01",
            "template_data": {
                "amount": 1880,
                "currency_code": "JPY",
                "necessity": "essential",
                "note": "due immediately",
                "items": [],
                "subject_ids": [],
            },
        },
    )
    assert recurring_response.status_code == 201, recurring_response.text
    assert recurring_response.json()["next_run_date"] == "2026-07-01"

    recurring_id = uuid.UUID(recurring_response.json()["id"])
    transaction = await db_session.scalar(
        select(Transaction).where(Transaction.recurring_transaction_id == recurring_id)
    )
    assert transaction is not None
    assert transaction.amount == 1880
    assert transaction.transaction_date == date(2026, 6, 1)
    assert transaction.note == "due immediately"


@pytest.mark.asyncio
async def test_recurring_template_can_be_disabled_enabled_and_deleted(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    email = unique_email("recurring-toggle")
    await register_user(client, email)
    token = await login_user(client, email)
    ledger = await create_ledger(client, token, name="Recurring Toggle Ledger")
    ledger_id = ledger["id"]

    recurring_response = await client.post(
        f"{API_PREFIX}/ledgers/{ledger_id}/recurring",
        headers=auth_headers(token),
        json={
            "interval": "weekly",
            "next_run_date": "2026-06-20",
            "template_data": {
                "amount": 1200,
                "currency_code": "JPY",
                "necessity": "essential",
                "items": [],
                "subject_ids": [],
            },
        },
    )
    assert recurring_response.status_code == 201, recurring_response.text
    recurring_id = recurring_response.json()["id"]

    disable_response = await client.patch(
        f"{API_PREFIX}/ledgers/{ledger_id}/recurring/{recurring_id}",
        headers=auth_headers(token),
        json={"is_active": False},
    )
    assert disable_response.status_code == 200, disable_response.text
    assert disable_response.json()["is_active"] is False

    list_response = await client.get(f"{API_PREFIX}/ledgers/{ledger_id}/recurring", headers=auth_headers(token))
    assert list_response.status_code == 200, list_response.text
    assert any(row["id"] == recurring_id and row["is_active"] is False for row in list_response.json())

    enable_response = await client.patch(
        f"{API_PREFIX}/ledgers/{ledger_id}/recurring/{recurring_id}",
        headers=auth_headers(token),
        json={"is_active": True},
    )
    assert enable_response.status_code == 200, enable_response.text
    assert enable_response.json()["is_active"] is True

    delete_response = await client.delete(
        f"{API_PREFIX}/ledgers/{ledger_id}/recurring/{recurring_id}",
        headers=auth_headers(token),
    )
    assert delete_response.status_code == 200, delete_response.text
    recurring = await db_session.scalar(select(RecurringTransaction).where(RecurringTransaction.id == uuid.UUID(recurring_id)))
    assert recurring is None


@pytest.mark.asyncio
async def test_suggestion_flow_public_vote_unique_and_admin_status(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    author_email = unique_email("suggestion-author")
    voter_email = unique_email("suggestion-voter")
    admin_email = unique_email("suggestion-admin")
    await register_user(client, author_email)
    await register_user(client, voter_email)
    await register_user(client, admin_email)
    author_token = await login_user(client, author_email)
    voter_token = await login_user(client, voter_email)
    admin_token = await login_user(client, admin_email)

    admin = await db_session.scalar(select(User).where(User.email == admin_email))
    assert admin is not None
    admin.is_admin = True
    await db_session.flush()

    private_response = await client.post(
        f"{API_PREFIX}/suggestions",
        headers=auth_headers(author_token),
        json={"title": "私有建议", "body": "只有管理员和我能看到", "is_public": False},
    )
    assert private_response.status_code == 201, private_response.text

    public_response = await client.post(
        f"{API_PREFIX}/suggestions",
        headers=auth_headers(author_token),
        json={"title": "公开建议", "body": "希望大家投票", "is_public": True},
    )
    assert public_response.status_code == 201, public_response.text
    public_id = public_response.json()["id"]

    mine_response = await client.get(f"{API_PREFIX}/suggestions/mine", headers=auth_headers(author_token))
    assert mine_response.status_code == 200
    assert {item["title"] for item in mine_response.json()} == {"私有建议", "公开建议"}

    public_list = await client.get(f"{API_PREFIX}/suggestions/public", headers=auth_headers(voter_token))
    assert public_list.status_code == 200
    public_titles = {item["title"] for item in public_list.json()}
    assert "公开建议" in public_titles
    assert "私有建议" not in public_titles

    author_vote = await client.post(
        f"{API_PREFIX}/suggestions/{public_id}/vote",
        headers=auth_headers(author_token),
        json={"vote_type": "support"},
    )
    assert author_vote.status_code == 403

    support_vote = await client.post(
        f"{API_PREFIX}/suggestions/{public_id}/vote",
        headers=auth_headers(voter_token),
        json={"vote_type": "support"},
    )
    assert support_vote.status_code == 200
    assert support_vote.json()["support_count"] == 1

    oppose_vote = await client.post(
        f"{API_PREFIX}/suggestions/{public_id}/vote",
        headers=auth_headers(voter_token),
        json={"vote_type": "oppose"},
    )
    assert oppose_vote.status_code == 200
    assert oppose_vote.json()["support_count"] == 0
    assert oppose_vote.json()["oppose_count"] == 1

    public_uuid = uuid.UUID(public_id)
    assert (
        await db_session.scalar(
            select(func.count()).select_from(SuggestionVote).where(SuggestionVote.suggestion_id == public_uuid)
        )
        == 1
    )

    admin_list = await client.get(f"{API_PREFIX}/admin/suggestions", headers=auth_headers(admin_token))
    assert admin_list.status_code == 200, admin_list.text
    admin_titles = {item["title"] for item in admin_list.json()}
    assert {"私有建议", "公开建议"}.issubset(admin_titles)

    update_status = await client.patch(
        f"{API_PREFIX}/admin/suggestions/{public_id}/status",
        headers=auth_headers(admin_token),
        json={"status": "planned"},
    )
    assert update_status.status_code == 200, update_status.text
    assert update_status.json()["status"] == "planned"

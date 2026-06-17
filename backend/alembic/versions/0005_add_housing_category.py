"""add housing category

Revision ID: 0005_housing_category
Revises: 0004_suggestions
Create Date: 2026-06-17
"""
import uuid

import sqlalchemy as sa
from alembic import op


revision = "0005_housing_category"
down_revision = "0004_suggestions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    ledgers = bind.execute(sa.text("SELECT id FROM ledgers")).mappings().all()
    for ledger in ledgers:
        existing = bind.execute(
            sa.text(
                """
                SELECT 1
                FROM categories
                WHERE ledger_id = :ledger_id AND name = 'category.housing'
                """
            ),
            {"ledger_id": ledger["id"]},
        ).first()
        if existing:
            continue
        bind.execute(
            sa.text(
                """
                UPDATE categories
                SET display_order = display_order + 1
                WHERE ledger_id = :ledger_id AND display_order >= 3
                """
            ),
            {"ledger_id": ledger["id"]},
        )
        bind.execute(
            sa.text(
                """
                INSERT INTO categories (id, ledger_id, name, is_system, display_order)
                VALUES (:id, :ledger_id, 'category.housing', true, 3)
                """
            ),
            {"id": uuid.uuid4(), "ledger_id": ledger["id"]},
        )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM categories
        WHERE name = 'category.housing' AND is_system = true
        """
    )

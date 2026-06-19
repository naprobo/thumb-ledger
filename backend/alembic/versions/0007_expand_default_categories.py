"""expand default categories

Revision ID: 0007_expand_default_categories
Revises: 0006_hidden_subjects
Create Date: 2026-06-20
"""
import uuid

import sqlalchemy as sa
from alembic import op


revision = "0007_expand_default_categories"
down_revision = "0006_hidden_subjects"
branch_labels = None
depends_on = None


DEFAULT_CATEGORIES = [
    "category.food",
    "category.dining",
    "category.daily",
    "category.clothing",
    "category.housing",
    "category.utilities",
    "category.communication",
    "category.transport",
    "category.vehicle",
    "category.medical",
    "category.insurance",
    "category.education",
    "category.childcare",
    "category.pets",
    "category.entertainment",
    "category.travel",
    "category.digital",
    "category.subscriptions",
    "category.social",
    "category.beauty",
    "category.taxes",
    "category.other",
]

PREVIOUS_CATEGORIES = [
    "category.food",
    "category.clothing",
    "category.daily",
    "category.housing",
    "category.transport",
    "category.entertainment",
    "category.medical",
    "category.other",
]


def upgrade() -> None:
    bind = op.get_bind()
    ledgers = bind.execute(sa.text("SELECT id FROM ledgers")).mappings().all()
    for ledger in ledgers:
        ledger_id = ledger["id"]
        for index, name in enumerate(DEFAULT_CATEGORIES):
            existing = bind.execute(
                sa.text(
                    """
                    SELECT 1
                    FROM categories
                    WHERE ledger_id = :ledger_id AND name = :name
                    """
                ),
                {"ledger_id": ledger_id, "name": name},
            ).first()
            if existing:
                bind.execute(
                    sa.text(
                        """
                        UPDATE categories
                        SET display_order = :display_order
                        WHERE ledger_id = :ledger_id AND name = :name
                        """
                    ),
                    {"ledger_id": ledger_id, "name": name, "display_order": index},
                )
                continue
            bind.execute(
                sa.text(
                    """
                    INSERT INTO categories (id, ledger_id, name, is_system, display_order)
                    VALUES (:id, :ledger_id, :name, true, :display_order)
                    """
                ),
                {"id": uuid.uuid4(), "ledger_id": ledger_id, "name": name, "display_order": index},
            )


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text(
            """
            DELETE FROM categories
            WHERE is_system = true AND name NOT IN :previous_categories
            """
        ).bindparams(sa.bindparam("previous_categories", expanding=True)),
        {"previous_categories": PREVIOUS_CATEGORIES},
    )
    ledgers = bind.execute(sa.text("SELECT id FROM ledgers")).mappings().all()
    for ledger in ledgers:
        for index, name in enumerate(PREVIOUS_CATEGORIES):
            bind.execute(
                sa.text(
                    """
                    UPDATE categories
                    SET display_order = :display_order
                    WHERE ledger_id = :ledger_id AND name = :name
                    """
                ),
                {"ledger_id": ledger["id"], "name": name, "display_order": index},
            )

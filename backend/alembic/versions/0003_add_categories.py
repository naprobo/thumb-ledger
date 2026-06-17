"""add categories

Revision ID: 0003_categories
Revises: 0002_notifications
Create Date: 2026-06-10 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003_categories"
down_revision: Union[str, None] = "0002_notifications"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("ledger_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["ledger_id"], ["ledgers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_categories_ledger_id", "categories", ["ledger_id"])

    op.add_column("transaction_items", sa.Column("category_id", sa.UUID(), nullable=True))
    op.add_column(
        "transaction_items",
        sa.Column("category_name_snapshot", sa.String(50), nullable=True),
    )
    op.execute("UPDATE transaction_items SET category_name_snapshot = category")
    op.alter_column("transaction_items", "category_name_snapshot", nullable=False)
    op.create_index("ix_transaction_items_category_id", "transaction_items", ["category_id"])
    op.create_foreign_key(
        "fk_transaction_items_category_id_categories",
        "transaction_items",
        "categories",
        ["category_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.drop_column("transaction_items", "category")


def downgrade() -> None:
    op.add_column("transaction_items", sa.Column("category", sa.String(50), nullable=True))
    op.execute("UPDATE transaction_items SET category = category_name_snapshot")
    op.alter_column("transaction_items", "category", nullable=False)
    op.drop_constraint(
        "fk_transaction_items_category_id_categories",
        "transaction_items",
        type_="foreignkey",
    )
    op.drop_index("ix_transaction_items_category_id", table_name="transaction_items")
    op.drop_column("transaction_items", "category_name_snapshot")
    op.drop_column("transaction_items", "category_id")
    op.drop_index("ix_categories_ledger_id", table_name="categories")
    op.drop_table("categories")

"""add editable custom tags

Revision ID: 0010_editable_tags
Revises: 0009_location_receipt
Create Date: 2026-06-30
"""
import sqlalchemy as sa
from alembic import op


revision = "0010_editable_tags"
down_revision = "0009_location_receipt"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "subjects",
        sa.Column("is_hidden", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "categories",
        sa.Column("is_hidden", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_table(
        "custom_tags",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("ledger_id", sa.Uuid(), nullable=False),
        sa.Column("tag_type", sa.String(length=20), nullable=False),
        sa.Column("scope", sa.String(length=50), nullable=False, server_default=""),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("is_hidden", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["ledger_id"], ["ledgers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "ledger_id",
            "tag_type",
            "scope",
            "name",
            name="uq_custom_tag_ledger_type_scope_name",
        ),
    )
    op.create_index(op.f("ix_custom_tags_ledger_id"), "custom_tags", ["ledger_id"], unique=False)
    op.add_column("transactions", sa.Column("location_tag_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_transactions_location_tag_id",
        "transactions",
        "custom_tags",
        ["location_tag_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(op.f("ix_transactions_location_tag_id"), "transactions", ["location_tag_id"], unique=False)
    op.add_column("transaction_items", sa.Column("item_tag_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_transaction_items_item_tag_id",
        "transaction_items",
        "custom_tags",
        ["item_tag_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(op.f("ix_transaction_items_item_tag_id"), "transaction_items", ["item_tag_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_transaction_items_item_tag_id"), table_name="transaction_items")
    op.drop_constraint("fk_transaction_items_item_tag_id", "transaction_items", type_="foreignkey")
    op.drop_column("transaction_items", "item_tag_id")
    op.drop_index(op.f("ix_transactions_location_tag_id"), table_name="transactions")
    op.drop_constraint("fk_transactions_location_tag_id", "transactions", type_="foreignkey")
    op.drop_column("transactions", "location_tag_id")
    op.drop_index(op.f("ix_custom_tags_ledger_id"), table_name="custom_tags")
    op.drop_table("custom_tags")
    op.drop_column("categories", "is_hidden")
    op.drop_column("subjects", "is_hidden")

"""add transaction location and receipt detail setting

Revision ID: 0009_location_receipt
Revises: 0008_add_user_nickname
Create Date: 2026-06-29
"""
import sqlalchemy as sa
from alembic import op


revision = "0009_location_receipt"
down_revision = "0008_add_user_nickname"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "ledgers",
        sa.Column("receipt_item_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "ledgers",
        sa.Column("location_step_mode", sa.String(length=20), nullable=False, server_default="optional"),
    )
    op.add_column("transactions", sa.Column("location_name", sa.String(length=100), nullable=True))


def downgrade() -> None:
    op.drop_column("transactions", "location_name")
    op.drop_column("ledgers", "location_step_mode")
    op.drop_column("ledgers", "receipt_item_enabled")

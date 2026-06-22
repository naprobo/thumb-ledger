"""add user nickname

Revision ID: 0008_add_user_nickname
Revises: 0007_expand_default_categories
Create Date: 2026-06-22
"""
import sqlalchemy as sa
from alembic import op


revision = "0008_add_user_nickname"
down_revision = "0007_expand_default_categories"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("nickname", sa.String(length=50), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "nickname")

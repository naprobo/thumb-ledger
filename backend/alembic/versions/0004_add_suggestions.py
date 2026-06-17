"""add suggestions

Revision ID: 0004_suggestions
Revises: 0003_categories
Create Date: 2026-06-15
"""
from alembic import op
import sqlalchemy as sa


revision = "0004_suggestions"
down_revision = "0003_categories"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "suggestions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("author_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="new"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_suggestions_author_id"), "suggestions", ["author_id"], unique=False)

    op.create_table(
        "suggestion_votes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("suggestion_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("vote_type", sa.String(length=10), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["suggestion_id"], ["suggestions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("suggestion_id", "user_id", name="uq_suggestion_vote_user"),
    )
    op.create_index(op.f("ix_suggestion_votes_suggestion_id"), "suggestion_votes", ["suggestion_id"], unique=False)
    op.create_index(op.f("ix_suggestion_votes_user_id"), "suggestion_votes", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_suggestion_votes_user_id"), table_name="suggestion_votes")
    op.drop_index(op.f("ix_suggestion_votes_suggestion_id"), table_name="suggestion_votes")
    op.drop_table("suggestion_votes")
    op.drop_index(op.f("ix_suggestions_author_id"), table_name="suggestions")
    op.drop_table("suggestions")

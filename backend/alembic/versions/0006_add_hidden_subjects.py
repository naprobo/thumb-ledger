"""add hidden subjects

Revision ID: 0006_hidden_subjects
Revises: 0005_housing_category
Create Date: 2026-06-17
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0006_hidden_subjects"
down_revision: Union[str, None] = "0005_housing_category"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "hidden_subjects",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("ledger_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("subject_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["ledger_id"], ["ledgers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ledger_id", "user_id", "subject_id", name="uq_hidden_subject_user"),
    )
    op.create_index("ix_hidden_subjects_ledger_id", "hidden_subjects", ["ledger_id"])
    op.create_index("ix_hidden_subjects_user_id", "hidden_subjects", ["user_id"])
    op.create_index("ix_hidden_subjects_subject_id", "hidden_subjects", ["subject_id"])


def downgrade() -> None:
    op.drop_index("ix_hidden_subjects_subject_id", table_name="hidden_subjects")
    op.drop_index("ix_hidden_subjects_user_id", table_name="hidden_subjects")
    op.drop_index("ix_hidden_subjects_ledger_id", table_name="hidden_subjects")
    op.drop_table("hidden_subjects")

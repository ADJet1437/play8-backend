"""Create waiting list table

Revision ID: 29560a05b59e
Revises: 174eca58c367
Create Date: 2026-04-06 16:36:01.700170

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "29560a05b59e"
down_revision: Union[str, None] = "174eca58c367"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "waiting_list",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("plan", sa.String(), nullable=False),
        sa.Column("message", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", "plan", name="uq_waiting_list_email_plan"),
    )
    op.create_index("ix_waiting_list_email", "waiting_list", ["email"])


def downgrade() -> None:
    op.drop_index("ix_waiting_list_email", table_name="waiting_list")
    op.drop_table("waiting_list")

"""add plan_items table

Revision ID: 6a35ef73e03f
Revises: 5b9c3d4e5f6a
Create Date: 2026-02-10 23:06:18.526686

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '6a35ef73e03f'
down_revision: Union[str, None] = '5b9c3d4e5f6a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    if "plan_items" not in inspector.get_table_names():
        op.create_table(
            "plan_items",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("user_id", sa.String(), nullable=False),
            sa.Column("title", sa.String(), nullable=False),
            sa.Column("description", sa.Text(), nullable=False, server_default=""),
            sa.Column("category", sa.String(), nullable=False, server_default="training"),
            sa.Column("difficulty", sa.String(), nullable=True),
            sa.Column("duration", sa.String(), nullable=True),
            sa.Column("overview", sa.Text(), nullable=False, server_default=""),
            sa.Column("steps", sa.Text(), nullable=False, server_default="[]"),
            sa.Column("tips", sa.Text(), nullable=False, server_default="[]"),
            sa.Column("checked_steps", sa.Text(), nullable=False, server_default="[]"),
            sa.Column("status", sa.String(), nullable=False, server_default="todo"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_plan_items_user_id"), "plan_items", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_plan_items_user_id"), table_name="plan_items")
    op.drop_table("plan_items")

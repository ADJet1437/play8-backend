"""Add hash password and verified to users

Revision ID: 174eca58c367
Revises: a1b2c3d4e5f6
Create Date: 2026-04-06 12:20:32.303569

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '174eca58c367'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("password_hash", sa.String(), nullable=True))
    # Existing rows are Google SSO users — already verified, so default True.
    op.add_column(
        "users",
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="true"),
    )


def downgrade() -> None:
    op.drop_column("users", "is_verified")
    op.drop_column("users", "password_hash")



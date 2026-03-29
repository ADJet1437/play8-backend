"""add stripe payment

Revision ID: a1b2c3d4e5f6
Revises: eef47727a917
Create Date: 2026-03-29 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "eef47727a917"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    from sqlalchemy import inspect as sa_inspect
    insp = sa_inspect(conn)
    existing_tables = insp.get_table_names()

    # Add price_per_hour to machines (default 12000 öre = 120 SEK)
    machines_cols = [c["name"] for c in insp.get_columns("machines")]
    if "price_per_hour" not in machines_cols:
        op.add_column("machines", sa.Column("price_per_hour", sa.Integer(), nullable=False, server_default="12000"))

    # Add payment_status to bookings
    bookings_cols = [c["name"] for c in insp.get_columns("bookings")]
    if "payment_status" not in bookings_cols:
        op.add_column("bookings", sa.Column("payment_status", sa.String(), nullable=True))

    # Create payments table only if it doesn't exist
    if "payments" not in existing_tables:
        op.create_table(
            "payments",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("booking_id", sa.String(), nullable=False),
            sa.Column("stripe_payment_intent_id", sa.String(), nullable=False),
            sa.Column("amount", sa.Integer(), nullable=False),
            sa.Column("currency", sa.String(), nullable=False, server_default="sek"),
            sa.Column("status", sa.String(), nullable=False, server_default="pending"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"]),
            sa.UniqueConstraint("booking_id"),
            sa.UniqueConstraint("stripe_payment_intent_id"),
        )

    existing_indexes = {i["name"] for i in insp.get_indexes("payments")} if "payments" in existing_tables else set()
    if "ix_payments_booking_id" not in existing_indexes:
        op.create_index("ix_payments_booking_id", "payments", ["booking_id"])
    if "ix_payments_stripe_payment_intent_id" not in existing_indexes:
        op.create_index("ix_payments_stripe_payment_intent_id", "payments", ["stripe_payment_intent_id"])


def downgrade() -> None:
    op.drop_index("ix_payments_stripe_payment_intent_id", table_name="payments")
    op.drop_index("ix_payments_booking_id", table_name="payments")
    op.drop_table("payments")
    op.drop_column("bookings", "payment_status")
    op.drop_column("machines", "price_per_hour")

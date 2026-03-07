"""replace plan_items with saved_training_sessions

Revision ID: e42770cd29ee
Revises: 6a35ef73e03f
Create Date: 2026-03-06 10:01:58.786788

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e42770cd29ee'
down_revision: Union[str, None] = '6a35ef73e03f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop old plan_items table
    op.drop_table('plan_items')

    # Create new saved_training_sessions table
    op.create_table(
        'saved_training_sessions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False, server_default=''),
        sa.Column('total_duration', sa.String(), nullable=False),
        sa.Column('difficulty', sa.String(), nullable=False),
        sa.Column('training_plan_data', sa.Text(), nullable=False),
        sa.Column('drill_cards_data', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )

    # Create index on user_id for faster queries
    op.create_index('ix_saved_training_sessions_user_id', 'saved_training_sessions', ['user_id'])


def downgrade() -> None:
    # Drop new table
    op.drop_index('ix_saved_training_sessions_user_id', table_name='saved_training_sessions')
    op.drop_table('saved_training_sessions')

    # Recreate old plan_items table
    op.create_table(
        'plan_items',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False, server_default=''),
        sa.Column('category', sa.String(), nullable=False, server_default='training'),
        sa.Column('difficulty', sa.String(), nullable=True),
        sa.Column('duration', sa.String(), nullable=True),
        sa.Column('overview', sa.Text(), nullable=False, server_default=''),
        sa.Column('steps', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('tips', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('checked_steps', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('status', sa.String(), nullable=False, server_default='todo'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )
    op.create_index('ix_plan_items_user_id', 'plan_items', ['user_id'])



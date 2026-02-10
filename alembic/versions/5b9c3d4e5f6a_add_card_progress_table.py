"""add card_progress table

Revision ID: 5b9c3d4e5f6a
Revises: 4a8b2c3d4e5f
Create Date: 2026-02-09 01:00:00.000000

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '5b9c3d4e5f6a'
down_revision = '4a8b2c3d4e5f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'card_progress',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('content_block_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('checked_steps', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['content_block_id'], ['content_blocks.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('content_block_id', 'user_id', name='uq_card_progress_block_user'),
    )
    op.create_index('ix_card_progress_content_block_id', 'card_progress', ['content_block_id'])


def downgrade() -> None:
    op.drop_index('ix_card_progress_content_block_id', table_name='card_progress')
    op.drop_table('card_progress')

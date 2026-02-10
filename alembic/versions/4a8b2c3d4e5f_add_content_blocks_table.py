"""add content_blocks table

Revision ID: 4a8b2c3d4e5f
Revises: 3173ad542597
Create Date: 2026-02-09 00:00:00.000000

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '4a8b2c3d4e5f'
down_revision = '3173ad542597'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'content_blocks',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('message_id', sa.String(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('tool_name', sa.String(), nullable=True),
        sa.Column('order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_content_blocks_message_id', 'content_blocks', ['message_id'])


def downgrade() -> None:
    op.drop_index('ix_content_blocks_message_id', table_name='content_blocks')
    op.drop_table('content_blocks')

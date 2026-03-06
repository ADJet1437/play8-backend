"""add_manual_knowledge_base_tables

Revision ID: eef47727a917
Revises: e42770cd29ee
Create Date: 2026-03-07 08:38:09.550248

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eef47727a917'
down_revision: Union[str, None] = 'e42770cd29ee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # Create manual_documents table
    op.create_table(
        'manual_documents',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('total_pages', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
    )

    # Create manual_chunks table with vector column
    op.create_table(
        'manual_chunks',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('document_id', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=False),
        sa.Column('section', sa.String(), nullable=False),
        sa.Column('pdf_page_image_path', sa.String(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['document_id'], ['manual_documents.id'], ondelete='CASCADE'),
    )

    # Add vector column for embeddings (1536 dimensions for text-embedding-3-small)
    op.execute('ALTER TABLE manual_chunks ADD COLUMN embedding vector(1536)')

    # Create index for vector similarity search (HNSW supports higher dimensions than ivfflat)
    op.execute('CREATE INDEX idx_manual_chunks_embedding ON manual_chunks USING hnsw (embedding vector_cosine_ops)')

    # Create indexes for faster queries
    op.create_index('ix_manual_chunks_document_id', 'manual_chunks', ['document_id'])
    op.create_index('ix_manual_chunks_page_number', 'manual_chunks', ['page_number'])
    op.create_index('ix_manual_chunks_section', 'manual_chunks', ['section'])


def downgrade() -> None:
    op.drop_index('ix_manual_chunks_section', table_name='manual_chunks')
    op.drop_index('ix_manual_chunks_page_number', table_name='manual_chunks')
    op.drop_index('ix_manual_chunks_document_id', table_name='manual_chunks')
    op.execute('DROP INDEX IF EXISTS idx_manual_chunks_embedding')
    op.drop_table('manual_chunks')
    op.drop_table('manual_documents')
    op.execute('DROP EXTENSION IF EXISTS vector')



from sqlalchemy import select, text
from sqlalchemy.orm import Session

from src.manual.db_model import ManualChunk


class ManualRepository:
    def __init__(self, db: Session):
        self.db = db

    def search_by_embedding(
        self, query_embedding: list[float], top_k: int = 5
    ) -> list[ManualChunk]:
        """
        Search manual chunks by semantic similarity using vector search.

        Args:
            query_embedding: The embedding vector of the search query
            top_k: Number of top results to return

        Returns:
            List of ManualChunk objects ordered by similarity (most similar first)
        """
        # Use pgvector cosine similarity search
        # The <=> operator computes cosine distance (lower is more similar)
        stmt = (
            select(ManualChunk)
            .order_by(text(f"embedding <=> '{query_embedding}'"))
            .limit(top_k)
        )

        results = self.db.execute(stmt).scalars().all()
        return list(results)

    def get_chunk_by_id(self, chunk_id: str) -> ManualChunk | None:
        """Get a specific chunk by ID."""
        return self.db.query(ManualChunk).filter(ManualChunk.id == chunk_id).first()

    def get_chunks_by_section(self, section: str) -> list[ManualChunk]:
        """Get all chunks for a specific section."""
        return self.db.query(ManualChunk).filter(ManualChunk.section == section).all()

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from src.core.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class ManualDocument(Base):
    __tablename__ = "manual_documents"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    total_pages: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationship
    chunks: Mapped[list["ManualChunk"]] = relationship("ManualChunk", back_populates="document", cascade="all, delete-orphan")


class ManualChunk(Base):
    __tablename__ = "manual_chunks"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    document_id: Mapped[str] = mapped_column(
        String, ForeignKey("manual_documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    section: Mapped[str] = mapped_column(String, nullable=False, index=True)
    pdf_page_image_path: Mapped[str | None] = mapped_column(String, nullable=True)
    embedding: Mapped[list[float]] = mapped_column(Vector(1536), nullable=True)  # text-embedding-3-small
    chunk_metadata: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)  # Use different name
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    document: Mapped["ManualDocument"] = relationship("ManualDocument", back_populates="chunks")

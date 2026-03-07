"""
Script to index the PongBot manual into the knowledge base.

Usage:
    python -m src.manual.index_manual <path_to_pdf>
"""

import os
import sys
import re
from pathlib import Path

import fitz  # PyMuPDF
from pdf2image import convert_from_path
from openai import OpenAI
from sqlalchemy.orm import Session

from src.core.database import get_db_context
from src.manual.db_model import ManualDocument, ManualChunk


# Constants
STATIC_DIR = Path(__file__).parent.parent.parent / "static" / "manual" / "pages"
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536


def extract_sections_from_pdf(pdf_path: str) -> list[dict]:
    """
    Extract top-level sections from PDF.

    Sections are identified by the ▐ symbol followed by section title.
    Each section includes all content until the next top-level section.
    """
    doc = fitz.open(pdf_path)
    sections = []
    current_section = None
    current_content = []
    current_pages = set()

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()

        # Split into lines
        lines = text.split('\n')

        for line in lines:
            # Check if this is a top-level section marker
            if line.strip().startswith('▐'):
                # Save previous section if exists
                if current_section:
                    sections.append({
                        'section': current_section,
                        'content': '\n'.join(current_content),
                        'pages': sorted(list(current_pages)),
                        'start_page': min(current_pages),
                        'end_page': max(current_pages),
                    })

                # Start new section
                current_section = line.strip().replace('▐', '').strip()
                current_content = []
                current_pages = {page_num + 1}  # 1-indexed
            else:
                # Add to current section
                if current_section:
                    current_content.append(line)
                    current_pages.add(page_num + 1)

    # Save last section
    if current_section:
        sections.append({
            'section': current_section,
            'content': '\n'.join(current_content),
            'pages': sorted(list(current_pages)),
            'start_page': min(current_pages),
            'end_page': max(current_pages),
        })

    doc.close()
    return sections


def generate_embedding(text: str, client: OpenAI) -> list[float]:
    """Generate embedding using OpenAI API."""
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text,
        dimensions=EMBEDDING_DIMENSIONS
    )
    return response.data[0].embedding


def extract_pdf_pages_as_images(pdf_path: str, output_dir: Path) -> dict[int, str]:
    """
    Convert PDF pages to PNG images.

    Returns:
        Dictionary mapping page_number to image file path
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Convert PDF to images
    images = convert_from_path(pdf_path, dpi=150)

    page_paths = {}
    for i, image in enumerate(images):
        page_num = i + 1
        filename = f"page_{page_num}.png"
        filepath = output_dir / filename
        image.save(filepath, "PNG")
        # Store relative path from static directory
        page_paths[page_num] = f"/static/manual/pages/{filename}"
        print(f"  📄 Generated image for page {page_num}")

    return page_paths


def index_manual(pdf_path: str, title: str = "PongBot Pace S Series Manual"):
    """Index the manual into the database."""
    print(f"🚀 Starting manual indexing: {pdf_path}")

    # Initialize OpenAI client
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Extract sections
    print("📚 Extracting sections from PDF...")
    sections = extract_sections_from_pdf(pdf_path)
    print(f"  ✅ Found {len(sections)} sections")

    # Generate page images
    print("📸 Generating page images...")
    page_images = extract_pdf_pages_as_images(pdf_path, STATIC_DIR)
    print(f"  ✅ Generated {len(page_images)} page images")

    # Get PDF metadata
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    doc.close()

    # Store in database
    print("💾 Storing in database...")
    with get_db_context() as db:
        # Create document record
        document = ManualDocument(
            filename=Path(pdf_path).name,
            title=title,
            total_pages=total_pages,
        )
        db.add(document)
        db.flush()  # Get document ID

        # Create chunks for each section
        for idx, section_data in enumerate(sections):
            print(f"  🔄 Processing section {idx+1}/{len(sections)}: {section_data['section'][:50]}...")

            # Generate embedding
            embedding = generate_embedding(section_data['content'], client)

            # Get representative page image (use start page)
            page_image_path = page_images.get(section_data['start_page'])

            # Create chunk
            chunk = ManualChunk(
                document_id=document.id,
                content=section_data['content'],
                page_number=section_data['start_page'],
                section=section_data['section'],
                pdf_page_image_path=page_image_path,
                embedding=embedding,
                chunk_metadata={
                    'pages': section_data['pages'],
                    'start_page': section_data['start_page'],
                    'end_page': section_data['end_page'],
                }
            )
            db.add(chunk)

        db.commit()
        print(f"  ✅ Stored {len(sections)} chunks")

    print("🎉 Manual indexing complete!")
    print(f"📊 Summary:")
    print(f"  - Document: {title}")
    print(f"  - Total pages: {total_pages}")
    print(f"  - Sections indexed: {len(sections)}")
    print(f"  - Page images: {len(page_images)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m src.manual.index_manual <path_to_pdf>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found: {pdf_path}")
        sys.exit(1)

    index_manual(pdf_path)

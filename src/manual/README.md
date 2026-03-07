# PongBot Manual Knowledge Base (RAG)

This module implements a RAG (Retrieval-Augmented Generation) system for the PongBot manual, allowing the AI Coach to answer questions about the ball machine with page references.

## Setup

### 1. Install Dependencies

```bash
poetry install
```

Required packages:
- `pymupdf` - PDF parsing
- `pdf2image` - Convert PDF pages to images
- `pillow` - Image processing
- `pgvector` - PostgreSQL vector extension

### 2. Install System Dependencies (for pdf2image)

**macOS:**
```bash
brew install poppler
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install poppler-utils
```

**Windows:**
Download poppler from: https://github.com/oschwartz10612/poppler-windows/releases/

### 3. Run Database Migration

```bash
poetry run alembic upgrade head
```

This will:
- Enable pgvector extension
- Create `manual_documents` and `manual_chunks` tables
- Create vector similarity search index

## Indexing the Manual

### 1. Place PDF in docs folder

```bash
mkdir -p play8-backend/docs
cp path/to/pongbot_manual.pdf play8-backend/docs/
```

### 2. Run indexing script

```bash
poetry run python -m src.manual.index_manual docs/pongbot_manual.pdf
```

This will:
1. Extract top-level sections from PDF (marked with ▐ symbol)
2. Generate embeddings using OpenAI `text-embedding-3-large`
3. Convert PDF pages to PNG images (saved in `static/manual/pages/`)
4. Store everything in PostgreSQL

**Output:**
```
🚀 Starting manual indexing: docs/pongbot_manual.pdf
📚 Extracting sections from PDF...
  ✅ Found 45 sections
📸 Generating page images...
  📄 Generated image for page 1
  ...
  ✅ Generated 78 page images
💾 Storing in database...
  🔄 Processing section 1/45: Reading Guide...
  ...
  ✅ Stored 45 chunks
🎉 Manual indexing complete!
```

## Usage

### AI Coach Integration

The `search_pongbot_manual` tool is automatically available to the AI Coach. The agent will use it when users ask questions like:

- "How do I download the PongBot app?"
- "What are the spin parameter settings?"
- "Show me examples of custom drills"
- "What does error code 23 mean?"

### Manual API Endpoints

**Get PDF page image:**
```
GET /api/v1/manual/pages/{page_number}
```

Example:
```bash
curl http://localhost:8001/api/v1/manual/pages/29
```

Returns the PNG image for that page.

## Database Schema

### `manual_documents`
- `id` - UUID
- `filename` - Original PDF filename
- `title` - Document title
- `total_pages` - Total number of pages
- `created_at`, `updated_at`

### `manual_chunks`
- `id` - UUID
- `document_id` - Foreign key to manual_documents
- `content` - Section text content
- `page_number` - Page where section starts
- `section` - Section name (e.g., "Tennis Mode → Custom Drills")
- `pdf_page_image_path` - Path to page image (e.g., "/static/manual/pages/page_29.png")
- `embedding` - Vector(3072) for semantic search
- `metadata` - JSON with additional info (pages array, start_page, end_page)
- `created_at`

## How It Works

### 1. Indexing Process

```
PDF → Extract Sections → Generate Embeddings → Create Images → Store in DB
```

### 2. Search Process

```
User Question → Generate Query Embedding → Vector Similarity Search → Top K Results → Return with Page References
```

### 3. Vector Search

Uses pgvector's cosine similarity (`<=>` operator) to find the most semantically similar chunks:

```sql
SELECT * FROM manual_chunks
ORDER BY embedding <=> '[query_embedding]'
LIMIT 5
```

## Example: How AI Coach Uses It

**User:** "How do I connect the robot to the app?"

**AI Coach internally:**
1. Calls `search_pongbot_manual("connect robot to app")`
2. Gets results: Section "Connect the Robot to the APP" (page 29)
3. Responds: "To connect the robot to the APP, first make sure the robot is powered on... (See page 29 for detailed steps with screenshots)"

**User sees:**
- Text explanation
- Reference to page 29
- Optional: Link to view page image

## Maintenance

### Re-index Manual

If the manual is updated:

```bash
# Delete old data
poetry run python -c "from src.core.database import get_db_context; from src.manual.db_model import ManualDocument; db = next(get_db_context()); db.query(ManualDocument).delete(); db.commit()"

# Re-run indexing
poetry run python -m src.manual.index_manual docs/pongbot_manual_v2.pdf
```

### View Indexed Sections

```python
from src.core.database import get_db_context
from src.manual.db_model import ManualChunk

with get_db_context() as db:
    chunks = db.query(ManualChunk).all()
    for chunk in chunks:
        print(f"Section: {chunk.section} (Page {chunk.page_number})")
```

## Configuration

**Embedding Model:**
- Model: `text-embedding-3-large`
- Dimensions: 3072
- Change in: `src/manual/index_manual.py` and `src/manual/tool.py`

**Search Parameters:**
- Top-K results: 3 (configurable in `tool.py`)
- Content preview: 1000 chars (configurable in `tool.py`)

**Image Settings:**
- DPI: 150 (configurable in `index_manual.py`)
- Format: PNG
- Location: `static/manual/pages/`

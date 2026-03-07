from fastapi import APIRouter
from fastapi.responses import FileResponse
from pathlib import Path

router = APIRouter(prefix="/api/v1/manual", tags=["manual"])

STATIC_DIR = Path(__file__).parent.parent.parent / "static" / "manual" / "pages"


@router.get("/pages/{page_number}")
async def get_manual_page(page_number: int):
    """Get a PDF page image by page number."""
    image_path = STATIC_DIR / f"page_{page_number}.png"

    if not image_path.exists():
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Page {page_number} not found")

    return FileResponse(image_path, media_type="image/png")

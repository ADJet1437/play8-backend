import json
import os

from langchain_core.tools import tool
from openai import OpenAI

from src.core.database import get_db_context
from src.manual.repository import ManualRepository

# Embedding configuration
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536


def generate_query_embedding(query: str) -> list[float]:
    """Generate embedding for search query."""
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.embeddings.create(
        model=EMBEDDING_MODEL, input=query, dimensions=EMBEDDING_DIMENSIONS
    )
    return response.data[0].embedding


@tool
def search_pongbot_manual(query: str) -> str:
    """Search the PongBot Pace S Series manual for information.

    Use this tool when users ask questions about:
    - PongBot ball machine settings, parameters, or features
    - How to use specific functions (app download, connectivity, modes)
    - Technical specifications or troubleshooting
    - Drill examples, NTRP drills, or custom drill creation
    - Error codes or technical issues
    - Remote control, smart tracker, or battery usage

    This tool searches the official PongBot manual and returns relevant information
    with page references so users can verify details.

    Args:
        query: The user's question or search query (e.g., "how to download the app",
               "spin parameter settings", "custom drill examples")

    Returns:
        JSON string containing search results with content and page references
    """
    # Generate embedding for query
    query_embedding = generate_query_embedding(query)

    # Search database
    with get_db_context() as db:
        repo = ManualRepository(db)
        results = repo.search_by_embedding(query_embedding, top_k=3)

        # Format results
        formatted_results = []
        for chunk in results:
            formatted_results.append(
                {
                    "section": chunk.section,
                    "content": chunk.content[:1000],  # Limit content length
                    "page": chunk.page_number,
                    "pages": chunk.chunk_metadata.get("pages", []) if chunk.chunk_metadata else [],
                    "image_path": chunk.pdf_page_image_path,
                }
            )

        return json.dumps(
            {
                "query": query,
                "results": formatted_results,
                "total_results": len(formatted_results),
            },
            indent=2,
        )

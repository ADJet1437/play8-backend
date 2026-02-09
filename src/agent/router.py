import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from src.agent.models import ChatRequest, ConversationDetail, ConversationResponse
from src.agent.service import AgentService, generate_title, stream_chat_response
from src.core.database import get_db
from src.core.models import DeleteResponse, PagedResponse
from src.core.security import get_current_user
from src.user.db_model import User as DBUser

router = APIRouter(prefix="/api/v1/agent", tags=["agent"])


@router.get("/conversations", response_model=PagedResponse[ConversationResponse])
def list_conversations(
    limit: int = 100,
    offset: int = 0,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AgentService(db)
    conversations, total = service.get_conversations(current_user.id, limit, offset)
    return PagedResponse(
        data=[service.conversation_to_pydantic(c) for c in conversations],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/conversations", response_model=ConversationResponse)
def create_conversation(
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AgentService(db)
    conversation = service.create_conversation(current_user.id)
    return service.conversation_to_pydantic(conversation)


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
def get_conversation(
    conversation_id: str,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AgentService(db)
    detail = service.get_conversation_with_messages(conversation_id, current_user.id)
    if not detail:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return detail


@router.delete("/conversations/{conversation_id}", response_model=DeleteResponse)
def delete_conversation(
    conversation_id: str,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AgentService(db)
    try:
        service.delete_conversation(conversation_id, current_user.id)
        return DeleteResponse(status="success", id=conversation_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/chat")
async def chat_stream(
    request: ChatRequest,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AgentService(db)

    # Create or retrieve conversation
    conversation_id = request.conversation_id
    if not conversation_id:
        conversation = service.create_conversation(current_user.id)
        conversation_id = conversation.id
    else:
        conversation = service.get_conversation(conversation_id, current_user.id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

    # Save user message
    service.add_message(conversation_id, "user", request.message)

    # Check if this is the first message (for title generation)
    should_generate_title = service.is_first_message(conversation_id)

    # Build conversation history from DB
    conversation_history = [
        {"role": msg.role, "content": msg.content}
        for msg in request.conversation_history
    ]

    async def generate():
        assistant_message = ""

        async for chunk in stream_chat_response(
            message=request.message,
            conversation_history=conversation_history,
        ):
            assistant_message += chunk
            data = json.dumps({"content": chunk, "done": False, "conversation_id": conversation_id})
            yield f"data: {data}\n\n"

        # Save assistant message after streaming completes
        service.add_message(conversation_id, "assistant", assistant_message)

        # Generate title for first message
        title = None
        if should_generate_title:
            title = await generate_title(request.message)
            service.update_title(conversation_id, title)

        done_data = json.dumps({
            "content": "",
            "done": True,
            "conversation_id": conversation_id,
            "title": title,
        })
        yield f"data: {done_data}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

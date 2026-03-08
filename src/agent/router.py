import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from src.agent.agent import Agent
from src.agent.models import (
    CardProgressResponse,
    CardProgressUpdate,
    ChatRequest,
    ConversationDetail,
    ConversationResponse,
)
from src.agent.service import AgentService
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

    # Build conversation history
    conversation_history = [
        {"role": msg.role, "content": msg.content} for msg in request.conversation_history
    ]

    agent = Agent()

    async def generate():
        # Track blocks in chronological order
        content_blocks = []  # List of (type, content, tool_name) tuples
        current_text = ""
        all_text = ""  # For message.content

        async for event in agent.run(
            message=request.message,
            conversation_history=conversation_history,
        ):
            yield f"data: {json.dumps({**event, 'conversation_id': conversation_id})}\n\n"

            # Build blocks in chronological order
            if event["type"] == "text_delta":
                current_text += event["content"]
                all_text += event["content"]
            elif event["type"] == "tool_use_end":
                # Save accumulated text as a block before the tool use
                if current_text:
                    content_blocks.append(("text", current_text, None))
                    current_text = ""
                # Save tool use block
                content_blocks.append(("tool_use", event.get("result", ""), event.get("tool")))

        # Save any remaining text after the last tool use
        if current_text:
            content_blocks.append(("text", current_text, None))

        # Save assistant message with content blocks in order
        msg = service.add_message(conversation_id, "assistant", all_text)

        for order, (block_type, content, tool_name) in enumerate(content_blocks):
            block = service.add_content_block(
                msg.id,
                block_type,
                content,
                tool_name=tool_name,
                order=order,
            )

            # Emit card_saved for tool_use blocks
            if block_type == "tool_use":
                card_saved = json.dumps({
                    "type": "card_saved",
                    "content_block_id": block.id,
                    "tool": tool_name,
                    "result": content,
                    "conversation_id": conversation_id,
                })
                yield f"data: {card_saved}\n\n"

        # Generate title for first message
        title = None
        if should_generate_title:
            title = await agent.generate_title(request.message)
            service.update_title(conversation_id, title)

        done_data = json.dumps({
            "type": "done",
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


@router.put("/cards/{content_block_id}/progress", response_model=CardProgressResponse)
def update_card_progress(
    content_block_id: str,
    body: CardProgressUpdate,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AgentService(db)
    return service.update_card_progress(content_block_id, current_user.id, body.checked_steps)

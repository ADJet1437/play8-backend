from pydantic import BaseModel

# --- Chat models ---


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    conversation_history: list[ChatMessage] = []
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    message: str
    done: bool = False


# --- Conversation models ---


class ContentBlockResponse(BaseModel):
    id: str
    type: str  # "text" or "tool_use"
    content: str
    tool_name: str | None = None
    order: int
    checked_steps: list[bool] | None = None


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: str
    content_blocks: list[ContentBlockResponse] = []


class ConversationResponse(BaseModel):
    id: str
    title: str | None = None
    created_at: str
    updated_at: str


class ConversationDetail(ConversationResponse):
    messages: list[MessageResponse] = []


# --- Card progress models ---


class CardProgressUpdate(BaseModel):
    checked_steps: list[bool]


class CardProgressResponse(BaseModel):
    content_block_id: str
    checked_steps: list[bool]

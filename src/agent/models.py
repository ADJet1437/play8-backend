from pydantic import BaseModel


# --- Chat models (existing) ---

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

class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: str


class ConversationResponse(BaseModel):
    id: str
    title: str | None = None
    created_at: str
    updated_at: str


class ConversationDetail(ConversationResponse):
    messages: list[MessageResponse] = []

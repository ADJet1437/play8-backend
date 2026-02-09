import os
from collections.abc import AsyncGenerator

from openai import AsyncOpenAI
from sqlalchemy.orm import Session

from src.agent.db_model import Conversation, Message
from src.agent.models import ConversationDetail, ConversationResponse, MessageResponse
from src.agent.repository import ConversationRepository, MessageRepository

# Initialize OpenAI client
api_key = os.getenv("OPENAI_API_KEY")
client = AsyncOpenAI(api_key=api_key)

# Sports-focused system prompt
SPORTS_SYSTEM_PROMPT = """You are a helpful AI assistant specialized in sports, particularly tennis and athletic training.
You provide expert advice on:
- Tennis techniques and strategies
- Training routines and exercises
- Sports equipment and gear
- Injury prevention and recovery
- Performance improvement tips
- General sports knowledge

Keep your responses concise, practical, and focused on sports-related topics. If asked about non-sports topics, politely redirect to sports-related advice."""


async def stream_chat_response(
    message: str, conversation_history: list | None = None
) -> AsyncGenerator[str, None]:
    """
    Stream chat responses from OpenAI with sports-focused context.

    Args:
        message: User's message
        conversation_history: Previous conversation messages

    Yields:
        Chunks of the assistant's response
    """
    if conversation_history is None:
        conversation_history = []

    # Build messages with system prompt
    messages = [{"role": "system", "content": SPORTS_SYSTEM_PROMPT}]

    # Add conversation history
    for msg in conversation_history:
        messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})

    # Add current user message
    messages.append({"role": "user", "content": message})

    if not client:
        yield "Error: OpenAI client not initialized. Please set OPENAI_API_KEY environment variable."
        return

    try:
        # Stream response from OpenAI
        stream = await client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=messages,
            stream=True,
            temperature=0.7,
            max_tokens=1000,
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    except Exception as e:
        yield f"Error: {str(e)}"


async def generate_title(message: str) -> str:
    """Generate a short conversation title from the first user message."""
    try:
        response = await client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {
                    "role": "system",
                    "content": "Generate a short title (max 6 words) for a conversation. Reply with ONLY the title, no quotes or punctuation.",
                },
                {"role": "user", "content": message},
            ],
            temperature=0.5,
            max_tokens=20,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        # Fallback: truncate the first message
        return message[:50] + ("..." if len(message) > 50 else "")


class AgentService:
    def __init__(self, db: Session):
        self.conversation_repo = ConversationRepository(db)
        self.message_repo = MessageRepository(db)
        self.db = db

    def create_conversation(self, user_id: str) -> Conversation:
        return self.conversation_repo.create(user_id)

    def get_conversations(self, user_id: str, limit: int = 100, offset: int = 0) -> tuple[list[Conversation], int]:
        conversations = self.conversation_repo.get_by_user_id(user_id, limit, offset)
        total = self.conversation_repo.count_by_user_id(user_id)
        return conversations, total

    def get_conversation(self, conversation_id: str, user_id: str) -> Conversation | None:
        conversation = self.conversation_repo.get_by_id(conversation_id)
        if conversation and conversation.user_id == user_id and not conversation.is_deleted:
            return conversation
        return None

    def get_conversation_with_messages(self, conversation_id: str, user_id: str) -> ConversationDetail | None:
        conversation = self.get_conversation(conversation_id, user_id)
        if not conversation:
            return None
        messages = self.message_repo.get_by_conversation_id(conversation_id)
        return ConversationDetail(
            id=conversation.id,
            title=conversation.title,
            created_at=conversation.created_at.isoformat() if conversation.created_at else "",
            updated_at=conversation.updated_at.isoformat() if conversation.updated_at else "",
            messages=[self.message_to_pydantic(m) for m in messages],
        )

    def delete_conversation(self, conversation_id: str, user_id: str) -> None:
        conversation = self.get_conversation(conversation_id, user_id)
        if not conversation:
            raise ValueError("Conversation not found")
        self.conversation_repo.soft_delete(conversation)

    def add_message(self, conversation_id: str, role: str, content: str) -> Message:
        return self.message_repo.create(conversation_id, role, content)

    def update_title(self, conversation_id: str, title: str) -> None:
        conversation = self.conversation_repo.get_by_id(conversation_id)
        if conversation:
            self.conversation_repo.update_title(conversation, title)

    def is_first_message(self, conversation_id: str) -> bool:
        messages = self.message_repo.get_by_conversation_id(conversation_id)
        return len(messages) <= 1

    def conversation_to_pydantic(self, conversation: Conversation) -> ConversationResponse:
        return ConversationResponse(
            id=conversation.id,
            title=conversation.title,
            created_at=conversation.created_at.isoformat() if conversation.created_at else "",
            updated_at=conversation.updated_at.isoformat() if conversation.updated_at else "",
        )

    def message_to_pydantic(self, message: Message) -> MessageResponse:
        return MessageResponse(
            id=message.id,
            role=message.role,
            content=message.content,
            created_at=message.created_at.isoformat() if message.created_at else "",
        )

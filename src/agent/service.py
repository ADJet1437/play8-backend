import json

from sqlalchemy.orm import Session

from src.agent.db_model import CardProgress, ContentBlock, Conversation, Message
from src.agent.models import (
    CardProgressResponse,
    ContentBlockResponse,
    ConversationDetail,
    ConversationResponse,
    MessageResponse,
)
from src.agent.repository import (
    CardProgressRepository,
    ContentBlockRepository,
    ConversationRepository,
    MessageRepository,
)


class AgentService:
    def __init__(self, db: Session):
        self.conversation_repo = ConversationRepository(db)
        self.message_repo = MessageRepository(db)
        self.content_block_repo = ContentBlockRepository(db)
        self.card_progress_repo = CardProgressRepository(db)
        self.db = db

    def create_conversation(self, user_id: str) -> Conversation:
        return self.conversation_repo.create(user_id)

    def get_conversations(
        self, user_id: str, limit: int = 100, offset: int = 0
    ) -> tuple[list[Conversation], int]:
        conversations = self.conversation_repo.get_by_user_id(user_id, limit, offset)
        total = self.conversation_repo.count_by_user_id(user_id)
        return conversations, total

    def get_conversation(self, conversation_id: str, user_id: str) -> Conversation | None:
        conversation = self.conversation_repo.get_by_id(conversation_id)
        if conversation and conversation.user_id == user_id and not conversation.is_deleted:
            return conversation
        return None

    def get_conversation_with_messages(
        self, conversation_id: str, user_id: str
    ) -> ConversationDetail | None:
        conversation = self.get_conversation(conversation_id, user_id)
        if not conversation:
            return None
        messages = self.message_repo.get_by_conversation_id(conversation_id)
        return ConversationDetail(
            id=conversation.id,
            title=conversation.title,
            created_at=conversation.created_at.isoformat() if conversation.created_at else "",
            updated_at=conversation.updated_at.isoformat() if conversation.updated_at else "",
            messages=[self._message_to_pydantic(m, user_id) for m in messages],
        )

    def delete_conversation(self, conversation_id: str, user_id: str) -> None:
        conversation = self.get_conversation(conversation_id, user_id)
        if not conversation:
            raise ValueError("Conversation not found")
        self.conversation_repo.soft_delete(conversation)

    def add_message(self, conversation_id: str, role: str, content: str) -> Message:
        return self.message_repo.create(conversation_id, role, content)

    def add_content_block(
        self,
        message_id: str,
        block_type: str,
        content: str,
        tool_name: str | None = None,
        order: int = 0,
    ) -> ContentBlock:
        return self.content_block_repo.create(message_id, block_type, content, tool_name, order)

    def update_card_progress(
        self, content_block_id: str, user_id: str, checked_steps: list[bool]
    ) -> CardProgressResponse:
        progress = self.card_progress_repo.upsert(content_block_id, user_id, checked_steps)
        return CardProgressResponse(
            content_block_id=progress.content_block_id,
            checked_steps=json.loads(progress.checked_steps),
        )

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

    def _message_to_pydantic(self, message: Message, user_id: str) -> MessageResponse:
        content_blocks = self.content_block_repo.get_by_message_id(message.id)
        return MessageResponse(
            id=message.id,
            role=message.role,
            content=message.content,
            created_at=message.created_at.isoformat() if message.created_at else "",
            content_blocks=[self._content_block_to_pydantic(b, user_id) for b in content_blocks],
        )

    def _content_block_to_pydantic(
        self, block: ContentBlock, user_id: str
    ) -> ContentBlockResponse:
        checked_steps = None
        if block.type == "tool_use":
            progress = self.card_progress_repo.get_by_content_block_and_user(block.id, user_id)
            if progress:
                checked_steps = json.loads(progress.checked_steps)
        return ContentBlockResponse(
            id=block.id,
            type=block.type,
            content=block.content,
            tool_name=block.tool_name,
            order=block.order,
            checked_steps=checked_steps,
        )

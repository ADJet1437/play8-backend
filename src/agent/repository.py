from sqlalchemy.orm import Session

import json

from src.agent.db_model import CardProgress, ContentBlock, Conversation, Message


class ConversationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, conversation_id: str) -> Conversation | None:
        return self.db.query(Conversation).filter(Conversation.id == conversation_id).first()

    def get_by_user_id(self, user_id: str, limit: int = 100, offset: int = 0) -> list[Conversation]:
        return (
            self.db.query(Conversation)
            .filter(Conversation.user_id == user_id, Conversation.is_deleted == False)
            .order_by(Conversation.updated_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def count_by_user_id(self, user_id: str) -> int:
        return (
            self.db.query(Conversation)
            .filter(Conversation.user_id == user_id, Conversation.is_deleted == False)
            .count()
        )

    def create(self, user_id: str) -> Conversation:
        conversation = Conversation(user_id=user_id)
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def update_title(self, conversation: Conversation, title: str) -> Conversation:
        conversation.title = title
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def soft_delete(self, conversation: Conversation) -> Conversation:
        conversation.is_deleted = True
        self.db.commit()
        self.db.refresh(conversation)
        return conversation


class MessageRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_conversation_id(self, conversation_id: str) -> list[Message]:
        return (
            self.db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .all()
        )

    def create(self, conversation_id: str, role: str, content: str) -> Message:
        message = Message(conversation_id=conversation_id, role=role, content=content)
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message


class ContentBlockRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        message_id: str,
        block_type: str,
        content: str,
        tool_name: str | None = None,
        order: int = 0,
    ) -> ContentBlock:
        block = ContentBlock(
            message_id=message_id,
            type=block_type,
            content=content,
            tool_name=tool_name,
            order=order,
        )
        self.db.add(block)
        self.db.commit()
        self.db.refresh(block)
        return block

    def get_by_message_id(self, message_id: str) -> list[ContentBlock]:
        return (
            self.db.query(ContentBlock)
            .filter(ContentBlock.message_id == message_id)
            .order_by(ContentBlock.order.asc())
            .all()
        )


class CardProgressRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_content_block_and_user(
        self, content_block_id: str, user_id: str
    ) -> CardProgress | None:
        return (
            self.db.query(CardProgress)
            .filter(
                CardProgress.content_block_id == content_block_id,
                CardProgress.user_id == user_id,
            )
            .first()
        )

    def upsert(
        self, content_block_id: str, user_id: str, checked_steps: list[bool]
    ) -> CardProgress:
        existing = self.get_by_content_block_and_user(content_block_id, user_id)
        if existing:
            existing.checked_steps = json.dumps(checked_steps)
            self.db.commit()
            self.db.refresh(existing)
            return existing
        progress = CardProgress(
            content_block_id=content_block_id,
            user_id=user_id,
            checked_steps=json.dumps(checked_steps),
        )
        self.db.add(progress)
        self.db.commit()
        self.db.refresh(progress)
        return progress

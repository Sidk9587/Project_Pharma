from uuid import UUID
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.message import Message


def create_conversation(
    db: Session,
    *,
    title: str | None = None,
    user_id: UUID | None = None,
) -> Conversation:
    conversation = Conversation(title=title, user_id=user_id)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def get_conversation(db: Session, conversation_id: UUID) -> Conversation | None:
    return db.get(Conversation, conversation_id)


def list_conversations(db: Session, *, limit: int = 100) -> list[Conversation]:
    return (
        db.query(Conversation)
        .order_by(Conversation.updated_at.desc(), Conversation.id)
        .limit(limit)
        .all()
    )


def get_messages(db: Session, conversation_id: UUID) -> list[Message]:
    return (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc(), Message.id.asc())
        .all()
    )


def save_message(
    db: Session,
    *,
    conversation: Conversation,
    role: str,
    content: str,
) -> Message:
    if role not in {"user", "assistant"}:
        raise ValueError("Message role must be user or assistant.")
    now = datetime.now(UTC).replace(tzinfo=None)
    previous_timestamp = (
        db.query(Message.created_at)
        .filter(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.desc())
        .limit(1)
        .scalar()
    )
    if previous_timestamp is not None and now <= previous_timestamp:
        now = previous_timestamp + timedelta(microseconds=1)
    message = Message(
        conversation_id=conversation.id,
        role=role,
        content=content,
        created_at=now,
    )
    db.add(message)
    conversation.updated_at = now
    db.commit()
    db.refresh(message)
    return message


def delete_conversation(db: Session, conversation: Conversation) -> None:
    db.delete(conversation)
    db.commit()

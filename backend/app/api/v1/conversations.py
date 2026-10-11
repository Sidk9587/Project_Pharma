from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database.conversation_repository import (
    create_conversation,
    delete_conversation,
    get_conversation,
    get_messages,
    list_conversations,
)
from app.database.database import get_db
from app.schemas.conversation import (
    ConversationCreate,
    ConversationDetail,
    ConversationMessage,
    ConversationSummary,
)


router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.post("", response_model=ConversationSummary, status_code=status.HTTP_201_CREATED)
def create_conversation_endpoint(
    request: ConversationCreate,
    db: Session = Depends(get_db),
):
    conversation = create_conversation(db, title=request.title)
    return ConversationSummary.model_validate(conversation, from_attributes=True)


@router.get("", response_model=list[ConversationSummary])
def list_conversations_endpoint(db: Session = Depends(get_db)):
    return [
        ConversationSummary.model_validate(c, from_attributes=True)
        for c in list_conversations(db)
    ]


@router.get("/{conversation_id}/messages", response_model=list[ConversationMessage])
def conversation_messages_endpoint(
    conversation_id: UUID,
    db: Session = Depends(get_db),
):
    if get_conversation(db, conversation_id) is None:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return [
        ConversationMessage.model_validate(m, from_attributes=True)
        for m in get_messages(db, conversation_id)
    ]


@router.get("/{conversation_id}", response_model=ConversationDetail)
def get_conversation_endpoint(
    conversation_id: UUID,
    db: Session = Depends(get_db),
):
    conversation = get_conversation(db, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return ConversationDetail(
        id=conversation.id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=[
            ConversationMessage.model_validate(m, from_attributes=True)
            for m in get_messages(db, conversation_id)
        ],
    )


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation_endpoint(
    conversation_id: UUID,
    db: Session = Depends(get_db),
):
    conversation = get_conversation(db, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    delete_conversation(db, conversation)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

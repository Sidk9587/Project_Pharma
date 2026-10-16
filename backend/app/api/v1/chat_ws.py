from uuid import UUID

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.database.conversation_repository import (
    create_conversation,
    get_conversation,
    save_message,
)
from app.database.database import get_db
from app.rag.streaming import prepare_stream, stream_tokens
from app.rag.llm import ProviderConfigurationError
from app.schemas.chat import ChatRequest


router = APIRouter(tags=["Chat"])
INSUFFICIENT_CONTEXT = "I could not find this information in the provided documents."


@router.websocket("/chat/ws")
async def chat_websocket(websocket: WebSocket, db: Session = Depends(get_db)):
    await websocket.accept()
    try:
        while True:
            message = await websocket.receive_json()
            try:
                request = ChatRequest.model_validate(message)
            except (ValidationError, TypeError, ValueError) as exc:
                await websocket.send_json({"type": "error", "message": str(exc)})
                continue

            raw_conversation_id = message.get("conversation_id")
            try:
                if raw_conversation_id is not None:
                    try:
                        conversation_id = UUID(str(raw_conversation_id))
                    except (TypeError, ValueError):
                        await websocket.send_json({"type": "error", "message": "Invalid conversation_id."})
                        continue
                    conversation = get_conversation(db, conversation_id)
                    if conversation is None:
                        await websocket.send_json({"type": "error", "message": "Conversation not found."})
                        continue
                else:
                    conversation = create_conversation(db, title=request.question[:255])
            except ProviderConfigurationError as exc:
                db.rollback()
                await websocket.send_json({"type": "error", "message": str(exc)})
            except Exception:
                db.rollback()
                await websocket.send_json({"type": "error", "message": "Conversation could not be loaded."})
                continue

            try:
                save_message(
                    db,
                    conversation=conversation,
                    role="user",
                    content=request.question,
                )
                await websocket.send_json({
                    "type": "status",
                    "message": "Searching documents...",
                    "conversation_id": str(conversation.id),
                })

                sources, token_stream = prepare_stream(
                    question=request.question,
                    db=db,
                )

                if not token_stream:
                    await websocket.send_json({"type": "token", "content": INSUFFICIENT_CONTEXT})
                    save_message(
                        db,
                        conversation=conversation,
                        role="assistant",
                        content=INSUFFICIENT_CONTEXT,
                    )
                    await websocket.send_json({"type": "complete"})
                    continue

                await websocket.send_json({"type": "sources", "sources": sources})
                await websocket.send_json({"type": "status", "message": "Generating answer..."})

                answer_parts: list[str] = []
                async for content in stream_tokens(token_stream):
                    answer_parts.append(content)
                    await websocket.send_json({"type": "token", "content": content})

                answer = "".join(answer_parts)
                if not answer.strip():
                    await websocket.send_json({"type": "error", "message": "The model returned an empty response."})
                    continue

                save_message(
                    db,
                    conversation=conversation,
                    role="assistant",
                    content=answer,
                    sources=sources,
                )
                await websocket.send_json({"type": "complete"})
            except WebSocketDisconnect:
                raise
            except Exception:
                db.rollback()
                await websocket.send_json({"type": "error", "message": "Chat processing failed. Please retry."})
    except WebSocketDisconnect:
        # In-progress responses are intentionally not persisted as assistant messages.
        return

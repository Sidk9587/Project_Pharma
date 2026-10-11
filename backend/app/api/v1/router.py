from fastapi import APIRouter

from app.api.v1 import chat
from app.api.v1 import chat_ws
from app.api.v1 import documents
from app.api.v1 import conversations
from app.api.v1 import sources


api_router = APIRouter(
    prefix="/api/v1",
)


api_router.include_router(
    chat.router,
)

api_router.include_router(
    chat_ws.router,
)

api_router.include_router(
    documents.router,
)

api_router.include_router(conversations.router)
api_router.include_router(sources.router)

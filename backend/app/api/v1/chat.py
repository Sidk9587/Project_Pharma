from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.rag.chain import ask_question
from app.rag.llm import ProviderConfigurationError
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    SourceInfo,
)


router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@router.post(
    "",
    response_model=ChatResponse,
)
async def chat(request: ChatRequest, db: Session = Depends(get_db)):

    try:

        result = ask_question(
            question=request.question,
            db=db,
        )

        sources = []

        for source in result["sources"]:

            sources.append(
                SourceInfo(
                    source=source.get(
                        "source",
                        "unknown",
                    ),
                    page_number=source.get(
                        "page_number"
                    ),
                    chunk_index=source.get(
                        "chunk_index",
                        -1,
                    ),
                    document_id=source.get("document_id"),
                    content_hash=source.get("content_hash"),
                    url=source.get("url"),
                    domain=source.get("domain"),
                )
            )

        return ChatResponse(
            answer=result["answer"],
            sources=sources,
        )

    except ProviderConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception:

        raise HTTPException(
            status_code=500,
            detail="RAG processing failed.",
        )

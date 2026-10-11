import asyncio
import json

from sqlalchemy.orm import Session

from app.guardrails.scope_checker import validate_question
from app.rag.llm import get_llm
from app.rag.prompts import RAG_PROMPT
from app.rag.retriever import retrieve_documents


_STREAM_END = object()


def prepare_stream(
    question: str,
    k: int = 4,
    *,
    db: Session | None = None,
):
    """
    Retrieve relevant documents and prepare
    the LLM streaming generator.
    """

    question = validate_question(question)
    documents = retrieve_documents(query=question, k=k, db=db)

    if not documents:
        return [], None

    context = json.dumps(
        [{"text": document.page_content, "source": document.metadata} for document in documents],
        ensure_ascii=False,
    )

    prompt = RAG_PROMPT.format_messages(
        context=context,
        question=question,
    )

    llm = get_llm()

    return (
        [document.metadata for document in documents],
        llm.stream(prompt),
    )


async def stream_tokens(token_stream):
    """
    Consume the synchronous LLM stream without
    blocking FastAPI's async event loop.
    """

    iterator = iter(token_stream)

    while True:

        chunk = await asyncio.to_thread(
            next,
            iterator,
            _STREAM_END,
        )

        if chunk is _STREAM_END:
            break

        content = chunk.content

        if content:
            yield content

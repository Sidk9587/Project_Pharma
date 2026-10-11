"""RAG orchestration using existing Chroma, Ollama and LangChain components."""

import json

from sqlalchemy.orm import Session

from app.guardrails.output_validator import validate_answer
from app.guardrails.scope_checker import validate_question
from app.rag.llm import get_llm
from app.rag.prompts import RAG_PROMPT
from app.rag.retriever import retrieve_documents


INSUFFICIENT_INFORMATION = "I could not find this information in the provided documents."


def _prepare(question: str, k: int, db: Session | None):
    question = validate_question(question)
    documents = retrieve_documents(query=question, k=k, db=db)
    if not documents:
        return question, [], None
    evidence = json.dumps(
        [
            {"text": document.page_content, "source": document.metadata}
            for document in documents
        ],
        ensure_ascii=False,
    )
    # Pass role-separated messages to chat models; flattening with .format()
    # would turn the intended system instruction into ordinary user text.
    prompt = RAG_PROMPT.format_messages(context=evidence, question=question)
    return question, documents, prompt


def ask_question(question: str, k: int = 4, *, db: Session | None = None) -> dict:
    _, documents, prompt = _prepare(question, k, db)
    if prompt is None:
        return {"answer": INSUFFICIENT_INFORMATION, "sources": []}
    result = get_llm().invoke(prompt)
    answer = validate_answer(result.content)
    if answer is None:
        answer = INSUFFICIENT_INFORMATION
    return {
        "answer": answer,
        "sources": [document.metadata for document in documents],
    }

"""Environment-selected language model provider."""
from app.config.settings import settings


class ProviderConfigurationError(RuntimeError):
    """Safe configuration error suitable to return to an API client."""


def provider_status() -> dict[str, str | bool | None]:
    provider = settings.llm_provider
    if provider not in {"ollama", "openai"}:
        raise ValueError("LLM_PROVIDER must be either 'ollama' or 'openai'.")
    embedding_provider = settings.embedding_provider
    if embedding_provider not in {"ollama", "openai"}:
        raise ValueError("EMBEDDING_PROVIDER must be either 'ollama' or 'openai'.")
    embedding_model = settings.ollama_embedding_model if embedding_provider == "ollama" else settings.openai_embedding_model
    from app.rag.vector_store import get_collection_name
    vector_collection = get_collection_name()
    return {
        "provider": provider,
        "model": settings.ollama_chat_model if provider == "ollama" else settings.openai_chat_model,
        "embedding_provider": settings.embedding_provider,
        "embedding_model": embedding_model,
        "vector_collection": vector_collection,
        "reindex_required": vector_collection != "pharma_documents",
        "configured": (provider == "ollama" or bool(settings.openai_api_key)) and (embedding_provider == "ollama" or bool(settings.openai_api_key)),
    }


def get_llm():
    provider = settings.llm_provider
    if provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(model=settings.ollama_chat_model, base_url=settings.ollama_base_url, temperature=0)
    if provider == "openai":
        if not settings.openai_api_key:
            raise ProviderConfigurationError("OpenAI is selected but OPENAI_API_KEY is not configured on the backend.")
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=settings.openai_chat_model, api_key=settings.openai_api_key, temperature=0)
    raise ValueError("LLM_PROVIDER must be either 'ollama' or 'openai'.")

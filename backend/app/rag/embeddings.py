"""Environment-selected embedding provider integration."""
from app.config.settings import settings
from app.rag.llm import ProviderConfigurationError


def get_embedding_model():
    if settings.embedding_provider == "ollama":
        from langchain_ollama import OllamaEmbeddings
        return OllamaEmbeddings(model=settings.ollama_embedding_model, base_url=settings.ollama_base_url)
    if settings.embedding_provider == "openai":
        if not settings.openai_api_key:
            raise ProviderConfigurationError("OpenAI embeddings are selected but OPENAI_API_KEY is not configured on the backend.")
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(model=settings.openai_embedding_model, api_key=settings.openai_api_key)
    raise ValueError("EMBEDDING_PROVIDER must be either 'ollama' or 'openai'.")

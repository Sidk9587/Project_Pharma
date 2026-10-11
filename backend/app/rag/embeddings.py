"""Embedding generation and provider integration."""

from langchain_ollama import OllamaEmbeddings


def get_embedding_model() -> OllamaEmbeddings:
    """
    Return the local Ollama embedding model.
    """

    return OllamaEmbeddings(
        model="nomic-embed-text",
    )
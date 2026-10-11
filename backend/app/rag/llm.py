"""Language model provider integration."""
from langchain_ollama import ChatOllama


def get_llm() -> ChatOllama:
    """
    Return the local Ollama Llama 3 model.
    """

    return ChatOllama(
        model="llama3",
        temperature=0,
    )
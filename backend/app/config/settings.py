"""Application configuration settings."""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    database_url: str = os.getenv("DATABASE_URL", "")
    crawl_timeout_seconds: float = float(os.getenv("CRAWL_TIMEOUT_SECONDS", "12"))
    crawl_max_response_bytes: int = int(os.getenv("CRAWL_MAX_RESPONSE_BYTES", str(2 * 1024 * 1024)))
    crawl_max_pages: int = int(os.getenv("CRAWL_MAX_PAGES", "10"))
    crawl_max_redirects: int = int(os.getenv("CRAWL_MAX_REDIRECTS", "4"))
    crawl_min_interval_seconds: float = float(os.getenv("CRAWL_MIN_INTERVAL_SECONDS", "0.5"))
    rag_min_relevance_score: float = float(os.getenv("RAG_MIN_RELEVANCE_SCORE", "0.20"))
    llm_provider: str = os.getenv("LLM_PROVIDER", "ollama").strip().lower()
    ollama_chat_model: str = os.getenv("OLLAMA_CHAT_MODEL", "llama3:latest")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    openai_chat_model: str = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    embedding_provider: str = os.getenv("EMBEDDING_PROVIDER", "ollama").strip().lower()
    ollama_embedding_model: str = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text:latest")
    openai_embedding_model: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")


settings = Settings()

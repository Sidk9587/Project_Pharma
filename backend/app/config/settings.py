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


settings = Settings()

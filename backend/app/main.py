from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.api.v1.router import api_router
from app.rag.llm import provider_status



app = FastAPI(
    title="Controlled RAG API",
    version="0.1.0"
)

# CORS configuration for local Flutter Web development
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.get("/api/v1/settings/provider")
def get_provider_settings():
    try:
        return provider_status()
    except ValueError as exc:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail=str(exc)) from exc

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "message": "Controlled RAG API is running"
    }

@app.get("/db-health")
def database_health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))

        return {
            "status": "ok",
            "database": "connected"
        }

    except Exception as e:
        return {
            "status": "error",
            "database": "disconnected",
            "error": str(e)
        }

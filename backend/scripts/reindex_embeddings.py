"""Reindex processed PostgreSQL chunks into the embedding collection selected by env.

Run from backend after changing EMBEDDING_PROVIDER/model:
    python scripts/reindex_embeddings.py

This deliberately writes into the selected collection only. It leaves the
existing embedding collection available for rollback.
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from langchain_core.documents import Document as LangChainDocument
from sqlalchemy import select

from app.database.database import SessionLocal
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.source import Source
from app.rag.vector_store import add_documents, delete_document_vectors, get_collection_name


def main() -> None:
    count = 0
    with SessionLocal() as db:
        records = db.scalars(select(Document).where(Document.status == "processed")).all()
        for record in records:
            source = db.get(Source, record.source_id) if record.source_id else None
            chunks = db.scalars(select(DocumentChunk).where(DocumentChunk.document_id == record.id).order_by(DocumentChunk.chunk_index)).all()
            if not chunks:
                continue
            documents = []
            for chunk in chunks:
                metadata = dict(chunk.metadata_json or {})
                metadata.update({
                    "source": record.title or record.file_name or "unknown",
                    "document_id": str(record.id),
                    "content_hash": record.content_hash,
                    "chunk_index": chunk.chunk_index,
                    "page_number": chunk.page_number,
                })
                if source is not None:
                    metadata.update({"source_id": str(source.id), "source_domain": source.domain, "url": record.url})
                metadata = {key: value for key, value in metadata.items() if value is not None}
                documents.append(LangChainDocument(page_content=chunk.content, metadata=metadata))

            delete_document_vectors(document_id=str(record.id))
            add_documents(documents, ids=[str(chunk.id) for chunk in chunks])
            count += len(documents)
            print(f"Reindexed {record.title or record.file_name}: {len(documents)} chunks")
    print(f"Finished: {count} chunks written to {get_collection_name()}.")


if __name__ == "__main__":
    main()

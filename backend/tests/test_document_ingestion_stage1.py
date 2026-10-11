from pathlib import Path
from datetime import datetime
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
import uuid
from unittest.mock import Mock, patch

import pymupdf
from fastapi.testclient import TestClient

from app.api.v1 import documents as document_api
from app.api.v1 import chat_ws
from app.ingestion import pdf_ingestion
from app.main import app
from app.rag import vector_store


class FakeDB:
    def rollback(self):
        pass


class DocumentIngestionTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.directory = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def create_pdf(self, name="valid.pdf", text="Storage Fabric (DataSync Layer) moves data securely."):
        path = self.directory / name
        pdf = pymupdf.open()
        page = pdf.new_page()
        page.insert_text((72, 72), text)
        pdf.save(path)
        pdf.close()
        return path

    def test_valid_pdf_ingestion_persists_chunks_and_citations(self):
        path = self.create_pdf()
        document = SimpleNamespace(id=uuid.uuid4(), file_name="valid.pdf")
        saved_chunks, vectors = [], []
        with (
            patch.object(pdf_ingestion, "create_document", return_value=document),
            patch.object(pdf_ingestion, "get_document_by_hash", return_value=None),
            patch.object(pdf_ingestion, "create_chunks", side_effect=lambda db, **kw: saved_chunks.extend(kw["chunks"])),
            patch.object(pdf_ingestion, "add_documents", side_effect=vectors.extend),
            patch.object(pdf_ingestion, "mark_document_processed"),
        ):
            result = pdf_ingestion.ingest_pdf(FakeDB(), str(path), "valid.pdf")

        self.assertEqual(result["status"], "processed")
        self.assertEqual(result["chunks"], len(saved_chunks))
        self.assertEqual(len(saved_chunks), len(vectors))
        self.assertEqual(saved_chunks[0]["page_number"], 1)
        self.assertEqual(saved_chunks[0]["metadata"]["chunk_index"], 0)
        self.assertEqual(saved_chunks[0]["metadata"]["content_hash"], result["content_hash"])
        self.assertEqual(vectors[0].metadata["document_id"], str(document.id))

    def test_invalid_pdf_is_rejected_before_document_creation(self):
        path = self.directory / "not.pdf"
        path.write_text("not a PDF")
        create_document = Mock()
        with patch.object(pdf_ingestion, "create_document", create_document):
            with self.assertRaisesRegex(ValueError, "valid PDF"):
                pdf_ingestion.ingest_pdf(FakeDB(), str(path), "not.pdf")
        create_document.assert_not_called()

    def test_duplicate_pdf_is_detected(self):
        path = self.create_pdf("duplicate.pdf")
        existing = SimpleNamespace(id=uuid.uuid4(), file_name="original.pdf")
        create_document = Mock()
        with (
            patch.object(pdf_ingestion, "get_document_by_hash", return_value=existing),
            patch.object(pdf_ingestion, "create_document", create_document),
        ):
            result = pdf_ingestion.ingest_pdf(FakeDB(), str(path), "copy.pdf")
        self.assertEqual(result["status"], "duplicate")
        self.assertEqual(result["document_id"], str(existing.id))
        create_document.assert_not_called()

    def test_failed_vector_write_cleans_partial_data_and_marks_failed(self):
        path = self.create_pdf("failure.pdf")
        document = SimpleNamespace(id=uuid.uuid4(), file_name="failure.pdf")
        create_chunks = Mock()
        remove_vectors = Mock()
        mark_failed = Mock()
        with (
            patch.object(pdf_ingestion, "get_document_by_hash", return_value=None),
            patch.object(pdf_ingestion, "create_document", return_value=document),
            patch.object(pdf_ingestion, "create_chunks", create_chunks),
            patch.object(pdf_ingestion, "add_documents", side_effect=RuntimeError("embedding failed")),
            patch.object(pdf_ingestion, "delete_document_vectors", remove_vectors),
            patch.object(pdf_ingestion, "delete_chunks_for_document"),
            patch.object(pdf_ingestion, "mark_document_failed", mark_failed),
        ):
            with self.assertRaisesRegex(RuntimeError, "embedding failed"):
                pdf_ingestion.ingest_pdf(FakeDB(), str(path), "failure.pdf")
        remove_vectors.assert_called_once_with(document_id=str(document.id))
        mark_failed.assert_called_once()

    def test_document_listing_and_delete_clean_only_selected_vectors(self):
        target_id = uuid.uuid4()
        target = SimpleNamespace(
            id=target_id, file_name="target.pdf", title="target.pdf",
            document_type="pdf", status="processed", created_at=datetime.now(),
            updated_at=datetime.now(), source_id=None, user_id=None, url=None,
            content_hash="abc",
        )
        with patch.object(document_api, "get_documents", return_value=[target]):
            self.assertEqual(document_api.list_documents(FakeDB())[0].id, str(target_id))

        delete_vectors, delete_record = Mock(), Mock()
        with (
            patch.object(document_api, "get_document_by_id", return_value=target),
            patch.object(document_api, "delete_document_vectors", delete_vectors),
            patch.object(document_api, "delete_document", delete_record),
        ):
            document_api.remove_document(target_id, FakeDB())
        delete_vectors.assert_called_once_with(document_id=str(target_id))
        delete_record.assert_called_once()

    def test_vector_cleanup_is_scoped_by_document_id(self):
        store = SimpleNamespace(delete=Mock())
        with patch.object(vector_store, "get_vector_store", return_value=store):
            vector_store.delete_document_vectors(document_id="doc-a")
        store.delete.assert_called_once_with(where={"document_id": "doc-a"})

    def test_websocket_streaming_event_protocol_regression(self):
        async def fake_stream(_):
            yield "Storage Fabric"
            yield " is the DataSync Layer."

        source = {"source": "guide.pdf", "page_number": 2, "chunk_index": 3}
        with (
            patch.object(chat_ws, "prepare_stream", return_value=([source], object())),
            patch.object(chat_ws, "stream_tokens", side_effect=fake_stream),
            TestClient(app) as client,
        ):
            with client.websocket_connect("/api/v1/chat/ws") as websocket:
                websocket.send_json({"question": "What is Storage Fabric (DataSync Layer)?"})
                events = []
                while True:
                    event = websocket.receive_json()
                    events.append(event)
                    if event.get("type") == "complete":
                        break
                conversation_id = next(
                    event["conversation_id"]
                    for event in events
                    if event.get("type") == "status" and event.get("conversation_id")
                )

        self.assertEqual(events[0]["type"], "status")
        self.assertIn({"type": "sources", "sources": [source]}, events)
        self.assertEqual([event["content"] for event in events if event["type"] == "token"], [
            "Storage Fabric", " is the DataSync Layer."
        ])
        self.assertEqual(events[-1], {"type": "complete"})
        self.assertEqual(
            client.delete(f"/api/v1/conversations/{conversation_id}").status_code,
            204,
        )


if __name__ == "__main__":
    unittest.main()

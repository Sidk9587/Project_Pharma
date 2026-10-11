"""Bounded, source-scoped website ingestion with explicit SSRF defenses."""

from __future__ import annotations

import hashlib
import http.client
import ipaddress
import ssl
import socket
import time
from collections import deque
from datetime import UTC, datetime
from threading import Lock
from urllib.parse import urljoin, urlsplit
from urllib.robotparser import RobotFileParser
from uuid import UUID

from langchain_core.documents import Document as LangChainDocument
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.database.chunk_repository import create_chunks, delete_chunks_for_document
from app.ingestion.html_parser import parse_html_page
from app.ingestion.url_validator import (
    is_within_source_scope,
    normalize_source_url,
    validate_crawl_url,
)
from app.models.crawl_log import CrawlLog
from app.models.document import Document
from app.models.source import Source
from app.rag.chunker import split_text
from app.rag.vector_store import add_documents, delete_document_vectors


USER_AGENT = "ProjectPharmaRAGBot/1.0 (+controlled-source-ingestion)"
_rate_lock = Lock()
_last_request_by_domain: dict[str, float] = {}


def _rate_limit(domain: str, minimum_interval: float | None = None) -> None:
    interval = max(settings.crawl_min_interval_seconds, minimum_interval or 0.0)
    with _rate_lock:
        now = time.monotonic()
        delay = interval - (now - _last_request_by_domain.get(domain, 0.0))
        if delay > 0:
            time.sleep(delay)
        _last_request_by_domain[domain] = time.monotonic()


def _resolve_public_address(host: str, port: int) -> str:
    try:
        answers = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise ValueError("Source hostname could not be safely resolved.") from exc
    addresses = []
    for answer in answers:
        address = answer[4][0].split("%", 1)[0]
        try:
            parsed = ipaddress.ip_address(address)
        except ValueError as exc:
            raise ValueError("DNS returned an invalid address.") from exc
        if not parsed.is_global:
            raise ValueError("Source resolves to a private or reserved network address.")
        addresses.append(address)
    if not addresses:
        raise ValueError("Source hostname did not resolve to an address.")
    return addresses[0]


class _PinnedHTTPConnection(http.client.HTTPConnection):
    def __init__(self, host: str, port: int, connect_ip: str, timeout: float):
        super().__init__(host, port=port, timeout=timeout)
        self._connect_ip = connect_ip

    def connect(self):
        self.sock = socket.create_connection((self._connect_ip, self.port), self.timeout)


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(self, host: str, port: int, connect_ip: str, timeout: float):
        super().__init__(host, port=port, timeout=timeout, context=ssl.create_default_context())
        self._connect_ip = connect_ip

    def connect(self):
        raw_socket = socket.create_connection((self._connect_ip, self.port), self.timeout)
        self.sock = self._context.wrap_socket(raw_socket, server_hostname=self.host)


def _request_pinned(url: str, connect_ip: str) -> tuple[int, dict, bytes]:
    parsed = urlsplit(url)
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    timeout = settings.crawl_timeout_seconds
    connection_type = _PinnedHTTPSConnection if parsed.scheme == "https" else _PinnedHTTPConnection
    connection = connection_type(parsed.hostname, port, connect_ip, timeout)
    path = parsed.path or "/"
    if parsed.query:
        path += "?" + parsed.query
    try:
        connection.request("GET", path, headers={
            "Host": parsed.netloc,
            "User-Agent": USER_AGENT,
            "Accept-Encoding": "identity",
            "Connection": "close",
        })
        response = connection.getresponse()
        headers = {name.lower(): value for name, value in response.getheaders()}
        declared_length = headers.get("content-length")
        if declared_length and int(declared_length) > settings.crawl_max_response_bytes:
            raise ValueError("Website response exceeds the configured size limit.")
        if headers.get("content-encoding", "identity").lower() not in {"", "identity"}:
            raise ValueError("Compressed website responses are not accepted.")
        body = response.read(settings.crawl_max_response_bytes + 1)
        if len(body) > settings.crawl_max_response_bytes:
            raise ValueError("Website response exceeds the configured size limit.")
        return response.status, headers, body
    finally:
        connection.close()


def _safe_fetch(
    url: str,
    *,
    domain: str,
    base_url: str,
    enforce_path_scope: bool = True,
    minimum_interval: float | None = None,
) -> tuple[int, dict, bytes, str]:
    current = url
    for _ in range(settings.crawl_max_redirects + 1):
        current = validate_crawl_url(current, allowed_domain=domain, resolve_dns=False)
        if enforce_path_scope and not is_within_source_scope(
            current, base_url=base_url, domain=domain
        ):
            raise ValueError("URL is outside the configured source path scope.")
        parsed = urlsplit(current)
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        _rate_limit(domain, minimum_interval)
        connect_ip = _resolve_public_address(parsed.hostname, port)
        status, headers, body = _request_pinned(current, connect_ip)
        if status in {301, 302, 303, 307, 308}:
            location = headers.get("location")
            if not location:
                raise ValueError("Redirect response did not include a destination.")
            destination = urljoin(current, location)
            # Validate host and path before the next outbound request.
            destination = validate_crawl_url(destination, allowed_domain=domain, resolve_dns=False)
            if enforce_path_scope and not is_within_source_scope(
                destination, base_url=base_url, domain=domain
            ):
                raise ValueError("Redirect destination is outside the approved source scope.")
            if parsed.scheme == "https" and urlsplit(destination).scheme != "https":
                raise ValueError("HTTPS source redirects may not downgrade to HTTP.")
            current = destination
            continue
        return status, headers, body, current
    raise ValueError("Website exceeded the redirect limit.")


def _robots_parser(source: Source) -> RobotFileParser:
    parsed = urlsplit(source.base_url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    status, _, body, final_url = _safe_fetch(
        robots_url,
        domain=source.domain,
        base_url=source.base_url,
        enforce_path_scope=False,
    )
    parser = RobotFileParser(final_url)
    if status in {404, 410}:
        parser.parse([])
    elif status in {401, 403}:
        parser.parse(["User-agent: *", "Disallow: /"])
    elif status != 200:
        raise RuntimeError(f"Could not safely read robots.txt (HTTP {status}).")
    else:
        parser.parse(body.decode("utf-8", errors="replace").splitlines())
    return parser


def _write_log(db: Session, source_id: UUID, url: str, status: str, http_status=None, error=None) -> None:
    db.add(CrawlLog(
        source_id=source_id,
        url=url,
        status=status,
        http_status=http_status,
        error_message=(str(error)[:2000] if error else None),
    ))
    db.commit()


def _chunks_for_page(source: Source, document: Document, url: str, content_hash: str, text: str):
    result = []
    db_chunks = []
    for index, chunk in enumerate(split_text(text)):
        metadata = {
            "source": source.name,
            "source_id": str(source.id),
            "source_domain": source.domain,
            "url": url,
            "document_id": str(document.id),
            "content_hash": content_hash,
            "chunk_index": index,
        }
        result.append(LangChainDocument(page_content=chunk, metadata=metadata))
        db_chunks.append({
            "chunk_index": index,
            "content": chunk,
            "page_number": None,
            "metadata": metadata,
        })
    return result, db_chunks


def _index_page(db: Session, source: Source, url: str, title: str, text: str) -> str:
    content_hash = hashlib.sha256((url + "\n" + text).encode("utf-8")).hexdigest()
    document = (
        db.query(Document)
        .filter(Document.source_id == source.id, Document.url == url)
        .first()
    )
    if document is not None and document.content_hash == content_hash and document.status == "processed":
        return "skipped"

    if document is None:
        document = Document(
            source_id=source.id,
            title=title,
            url=url,
            document_type="website",
            content_hash=content_hash,
            status="processing",
        )
        db.add(document)
        db.commit()
        db.refresh(document)
    else:
        delete_document_vectors(document_id=str(document.id))
        delete_chunks_for_document(db, document.id)
        document.title = title
        document.content_hash = content_hash
        document.status = "processing"
        db.commit()
        db.refresh(document)

    langchain_docs, db_chunks = _chunks_for_page(source, document, url, content_hash, text)
    if not langchain_docs:
        document.status = "failed"
        db.commit()
        raise ValueError("Page has no indexable text chunks.")
    try:
        create_chunks(db, document_id=document.id, chunks=db_chunks)
        add_documents(langchain_docs)
        document.status = "processed"
        db.commit()
        return "indexed"
    except Exception:
        db.rollback()
        try:
            delete_document_vectors(document_id=str(document.id))
        finally:
            delete_chunks_for_document(db, document.id)
            document.status = "failed"
            db.commit()
        raise


def crawl_source(db: Session, source_id: UUID) -> dict:
    source = db.get(Source, source_id)
    if source is None:
        raise LookupError("Source not found.")
    if not source.is_active:
        raise PermissionError("Source is inactive.")
    if not source.crawl_enabled:
        raise PermissionError("Crawling is disabled for this source.")

    base_url, normalized_domain = normalize_source_url(source.base_url)
    if normalized_domain != source.domain:
        raise ValueError("Source domain no longer matches its normalized base URL.")
    source.base_url = base_url
    queue = deque([(base_url, 0)])
    visited: set[str] = set()
    counts = {"pages_seen": 0, "pages_indexed": 0, "pages_skipped": 0, "pages_failed": 0, "pages_blocked": 0}
    robots = None
    overall_status = "success"
    try:
        try:
            robots = _robots_parser(source)
        except Exception as exc:
            _write_log(db, source.id, base_url, "failed", error=f"robots.txt: {exc}")
            return {"source_id": source.id, **counts, "status": "failed"}

        while queue and counts["pages_seen"] < settings.crawl_max_pages:
            page_url, depth = queue.popleft()
            page_url = validate_crawl_url(page_url, allowed_domain=source.domain, resolve_dns=False)
            if page_url in visited:
                continue
            visited.add(page_url)
            if not is_within_source_scope(page_url, base_url=source.base_url, domain=source.domain):
                continue
            if not robots.can_fetch(USER_AGENT, page_url):
                _write_log(db, source.id, page_url, "blocked")
                counts["pages_blocked"] += 1
                continue

            counts["pages_seen"] += 1
            try:
                crawl_delay = robots.crawl_delay(USER_AGENT) or 0
                request_rate = robots.request_rate(USER_AGENT)
                request_interval = (
                    request_rate.seconds / request_rate.requests
                    if request_rate and request_rate.requests
                    else 0
                )
                http_status, headers, body, final_url = _safe_fetch(
                    page_url,
                    domain=source.domain,
                    base_url=source.base_url,
                    minimum_interval=max(crawl_delay, request_interval),
                )
                if http_status < 200 or http_status >= 300:
                    raise RuntimeError(f"Website returned HTTP {http_status}.")
                content_type = headers.get("content-type", "").lower()
                if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
                    _write_log(db, source.id, final_url, "skipped", http_status, "Non-HTML response.")
                    counts["pages_skipped"] += 1
                    continue

                page = parse_html_page(body.decode("utf-8", errors="replace"), final_url)
                canonical = page["canonical_url"] or final_url
                if not is_within_source_scope(canonical, base_url=source.base_url, domain=source.domain):
                    canonical = final_url
                if not page["text"]:
                    raise ValueError("HTML page contained no readable text.")

                result = _index_page(db, source, canonical, page["title"], page["text"])
                counts["pages_indexed" if result == "indexed" else "pages_skipped"] += 1
                _write_log(db, source.id, canonical, result, http_status)

                if depth == 0:
                    for link in page["links"]:
                        if len(visited) + len(queue) >= settings.crawl_max_pages:
                            break
                        try:
                            link = validate_crawl_url(link, allowed_domain=source.domain, resolve_dns=False)
                        except ValueError:
                            continue
                        if is_within_source_scope(link, base_url=source.base_url, domain=source.domain):
                            if link not in visited:
                                queue.append((link, 1))
            except Exception as exc:
                counts["pages_failed"] += 1
                overall_status = "partial" if counts["pages_indexed"] or counts["pages_skipped"] else "failed"
                _write_log(db, source.id, page_url, "failed", error=exc)
    finally:
        source.last_crawled_at = datetime.now(UTC).replace(tzinfo=None)
        db.commit()

    if counts["pages_failed"] and not counts["pages_indexed"]:
        overall_status = "failed"
    elif counts["pages_blocked"] and counts["pages_seen"] == 0:
        overall_status = "blocked"
    return {"source_id": source.id, **counts, "status": overall_status}

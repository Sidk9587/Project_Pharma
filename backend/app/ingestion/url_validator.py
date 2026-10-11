"""URL normalization and outbound-request SSRF checks for approved sources."""

from __future__ import annotations

import ipaddress
import re
import socket
import posixpath
from urllib.parse import unquote, urlsplit, urlunsplit


BLOCKED_SUFFIXES = (".localhost", ".local", ".internal", ".lan", ".home")


def normalize_domain(host: str) -> str:
    host = host.strip().rstrip(".").lower()
    if not host:
        raise ValueError("A source hostname is required.")
    try:
        normalized = host.encode("idna").decode("ascii")
    except UnicodeError as exc:
        raise ValueError("Invalid internationalized hostname.") from exc
    labels = normalized.split(".")
    if any(
        not label
        or len(label) > 63
        or re.fullmatch(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?", label) is None
        for label in labels
    ):
        raise ValueError("Invalid hostname syntax.")
    return normalized


def _parse_http_url(url: str):
    try:
        parsed = urlsplit(url.strip())
        port = parsed.port
    except (ValueError, AttributeError) as exc:
        raise ValueError("Invalid source URL.") from exc
    if parsed.scheme.lower() not in {"http", "https"}:
        raise ValueError("Only HTTP and HTTPS source URLs are supported.")
    if not parsed.hostname or parsed.username is not None or parsed.password is not None:
        raise ValueError("Source URLs must contain a hostname and no credentials.")
    host = normalize_domain(parsed.hostname)
    if (parsed.scheme.lower() == "http" and port not in (None, 80)) or (
        parsed.scheme.lower() == "https" and port not in (None, 443)
    ):
        raise ValueError("Only standard HTTP and HTTPS ports are permitted.")
    if host == "localhost" or host.endswith(BLOCKED_SUFFIXES) or "." not in host:
        raise ValueError("Local and single-label hostnames are not permitted.")
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        ip = None
    if ip is not None:
        if not ip.is_global:
            raise ValueError("Private, loopback, and reserved IP addresses are not permitted.")
        raise ValueError("IP literal source URLs are not permitted; use an approved hostname.")
    return parsed, host


def normalize_source_url(url: str) -> tuple[str, str]:
    parsed, host = _parse_http_url(url)
    scheme = parsed.scheme.lower()
    netloc = host
    if parsed.port is not None and not (
        (scheme == "http" and parsed.port == 80)
        or (scheme == "https" and parsed.port == 443)
    ):
        netloc = f"{host}:{parsed.port}"
    path = parsed.path or "/"
    _normalized_path(path)
    normalized = urlunsplit((scheme, netloc, path, parsed.query, ""))
    return normalized, host


def validate_crawl_url(url: str, *, allowed_domain: str, resolve_dns: bool = True) -> str:
    normalized, host = normalize_source_url(url)
    expected = normalize_domain(allowed_domain)
    if host != expected:
        raise ValueError("URL host is outside the configured source domain.")
    if resolve_dns:
        port = urlsplit(normalized).port or (443 if urlsplit(normalized).scheme == "https" else 80)
        try:
            answers = socket.getaddrinfo(host, port)
        except (OSError, ValueError) as exc:
            raise ValueError("Source hostname could not be safely resolved.") from exc
        addresses = {ipaddress.ip_address(info[4][0].split("%", 1)[0]) for info in answers}
        if not addresses or any(not address.is_global for address in addresses):
            raise ValueError("Source resolves to a private or reserved network address.")
    return normalized


def is_within_source_scope(url: str, *, base_url: str, domain: str) -> bool:
    try:
        candidate = urlsplit(validate_crawl_url(url, allowed_domain=domain, resolve_dns=False))
        base = urlsplit(validate_crawl_url(base_url, allowed_domain=domain, resolve_dns=False))
    except ValueError:
        return False
    scheme_is_safe = candidate.scheme == base.scheme or (
        base.scheme == "http" and candidate.scheme == "https"
    )
    if not scheme_is_safe or candidate.hostname != base.hostname or candidate.port not in (None, 80, 443):
        return False
    try:
        candidate_path = _normalized_path(candidate.path)
        base_path = _normalized_path(base.path)
    except ValueError:
        return False
    root = base_path or "/"
    if root != "/" and not root.endswith("/"):
        root += "/"
        return candidate_path == base_path or candidate_path.startswith(root)
    return candidate_path.startswith(root)


def _normalized_path(path: str) -> str:
    decoded = path
    for _ in range(3):
        next_value = unquote(decoded)
        if next_value == decoded:
            break
        decoded = next_value
    decoded = decoded.replace("\\", "/")
    if any(part in {".", ".."} for part in decoded.split("/")):
        raise ValueError("Path traversal is not permitted.")
    return posixpath.normpath("/" + decoded.lstrip("/"))

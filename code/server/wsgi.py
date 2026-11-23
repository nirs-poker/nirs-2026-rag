"""WSGI entry point for shared hosting (for example, REG.RU Passenger)."""

import json
import mimetypes
import os
from pathlib import Path
from urllib.parse import unquote

from rag import LLM, ModelError, RAG
from retrieval import BM25, load_chat_corpus

ROOT = Path(os.environ.get("POKER_APP_ROOT", Path(__file__).resolve().parents[2])).resolve()
FRONTEND = ROOT / "code" / "client" / "dist"
MAX_BODY = 32 * 1024


def load_environment(path=ROOT / ".env"):
    """Read the app's small allowlisted .env format without executing shell code."""
    if not path.is_file():
        return
    allowed = {"GROQ_API_KEY", "LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL"}
    for line in path.read_text(encoding="utf-8").splitlines():
        name, separator, value = line.strip().partition("=")
        name = name.strip()
        if not separator or name not in allowed:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        os.environ.setdefault(name, value)


load_environment()
_rag = RAG(BM25(load_chat_corpus()), LLM.from_env())


def _response(start_response, status, body=b"", content_type="text/plain; charset=utf-8",
              headers=(), head=False):
    standard_headers = [
        ("Content-Type", content_type),
        ("Content-Length", str(len(body))),
        ("X-Content-Type-Options", "nosniff"),
    ]
    start_response(status, standard_headers + list(headers))
    return [b"" if head else body]


def _json(start_response, status, payload, head=False):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    return _response(start_response, status, body, "application/json; charset=utf-8",
                     (("Cache-Control", "no-store"),), head=head)


def _static_file(path, start_response, head=False):
    relative = "frontend.html" if path == "/" else unquote(path).lstrip("/")
    candidate = (FRONTEND / relative).resolve()
    try:
        candidate.relative_to(FRONTEND.resolve())
    except ValueError:
        return _response(start_response, "404 Not Found", b"Not found")
    if not candidate.is_file():
        return _response(start_response, "404 Not Found", b"Not found")
    body = candidate.read_bytes()
    content_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
    if content_type.startswith("text/") or content_type in ("application/javascript", "application/json"):
        content_type += "; charset=utf-8"
    cache = "no-cache" if candidate.name == "frontend.html" else "public, max-age=31536000, immutable"
    return _response(start_response, "200 OK", body, content_type,
                     (("Cache-Control", cache),), head=head)


def application(environ, start_response):
    """Small WSGI app preserving the local server's API contract."""
    method = environ.get("REQUEST_METHOD", "GET").upper()
    path = environ.get("PATH_INFO", "/")

    if method in ("GET", "HEAD") and path == "/api/health":
        return _json(start_response, "200 OK", {"status": "ok"}, head=method == "HEAD")
    if path.startswith("/api/") and method != "POST":
        return _json(start_response, "404 Not Found", {"status": "error", "error": "Маршрут не найден."})
    if method == "POST" and path not in ("/ask", "/api/ask"):
        return _json(start_response, "404 Not Found", {"status": "error", "error": "Маршрут не найден."})
    if method == "POST":
        if environ.get("CONTENT_TYPE", "").split(";", 1)[0].strip().lower() != "application/json":
            return _json(start_response, "415 Unsupported Media Type",
                         {"status": "error", "error": "Ожидается JSON."})
        try:
            raw_length = environ.get("CONTENT_LENGTH", "")
            length = int(raw_length) if raw_length else 0
            if not 1 <= length <= MAX_BODY:
                raise ValueError
            payload = json.loads(environ["wsgi.input"].read(length))
            question = payload.get("question") if isinstance(payload, dict) else None
            if not isinstance(question, str) or not 1 <= len(question.strip()) <= 1500:
                raise ValueError
        except (ValueError, UnicodeError, KeyError, TypeError):
            return _json(start_response, "400 Bad Request",
                         {"status": "error", "error": "Введите вопрос длиной от 1 до 1500 символов."})
        try:
            return _json(start_response, "200 OK", _rag.ask(question.strip()))
        except ModelError as error:
            return _json(start_response, "502 Bad Gateway", {"status": "error", "error": str(error)})
    if method in ("GET", "HEAD"):
        if path.startswith("/api/"):
            return _json(start_response, "404 Not Found", {"status": "error", "error": "Маршрут не найден."})
        return _static_file(path, start_response, head=method == "HEAD")
    return _response(start_response, "405 Method Not Allowed", b"Method not allowed",
                     headers=(("Allow", "GET, HEAD, POST"),))

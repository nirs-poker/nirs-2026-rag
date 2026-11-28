"""Локальный сервер чата КТ2, без сторонних Python-пакетов."""

import argparse
import json
import os
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from conversation import conversation_options
from rag import LLM, RAG, ModelError
from retrieval import BM25, load_chat_corpus

CLIENT = Path(__file__).resolve().parents[1] / "client"
FRONTEND = CLIENT / "dist"
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PORT = json.loads((CLIENT.parent / "ports.json").read_text(encoding="utf-8"))["backend"]


def load_environment(path=ROOT / ".env"):
    """Читает только настройки LLM, не выполняя содержимое файла как shell-код."""
    if not path.exists():
        return
    allowed = {"GROQ_API_KEY", "LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL",
               "LLM_PROVIDER", "GIGACHAT_CREDENTIALS", "GIGACHAT_SCOPE", "GIGACHAT_CA_BUNDLE"}
    for line in path.read_text(encoding="utf-8").splitlines():
        name, separator, value = line.strip().partition("=")
        name = name.strip()
        if not separator or name not in allowed:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        os.environ.setdefault(name, value)


def create_server(port=DEFAULT_PORT, rag=None):
    handler = partial(ChatHandler, directory=str(FRONTEND))
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    server.rag = rag if rag is not None else RAG(BM25(load_chat_corpus()), LLM.from_env())
    return server


class ChatHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        if path.partition("?")[0] == "/":
            path = "/frontend.html"
        return super().translate_path(path)

    def do_GET(self):
        if self.path == "/api/health":
            self.json_response(200, {"status": "ok"})
        elif self.path.startswith("/api/"):
            self.json_response(404, {"status": "error", "error": "Маршрут не найден."})
        else:
            super().do_GET()

    def json_response(self, status, body):
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        if self.path not in ("/ask", "/api/ask"):
            self.json_response(404, {"status": "error", "error": "Маршрут не найден."})
            return
        if self.headers.get_content_type() != "application/json":
            self.json_response(415, {"status": "error", "error": "Ожидается JSON."})
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            if length > 32768:
                self.json_response(413, {"status": "error", "error": "Тело запроса больше 32 КБ."})
                return
            if not 1 <= length <= 32768:
                raise ValueError
            payload = json.loads(self.rfile.read(length))
            question = payload.get("question") if isinstance(payload, dict) else None
            if not isinstance(question, str) or not 1 <= len(question.strip()) <= 1500:
                raise ValueError
            options = conversation_options(payload)
        except (ValueError, UnicodeError):
            self.json_response(400, {"status": "error", "error": "Введите вопрос длиной от 1 до 1500 символов."})
            return
        try:
            result = self.server.rag.ask(question.strip(), **options)
        except ModelError as error:
            self.log_error("LLM: %s", error)
            self.json_response(502, {"status": "error", "error": str(error)})
            return
        self.json_response(200, result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()
    load_environment()
    with create_server(args.port) as server:
        print(f"Покерный тренер: http://127.0.0.1:{server.server_port}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()

"""Локальный сервер чата КТ2, без сторонних Python-пакетов."""

import argparse
import json
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from rag import LLM, RAG, ModelError
from retrieval import BM25, load_corpus

CLIENT = Path(__file__).resolve().parents[1] / "client"


class ChatHandler(SimpleHTTPRequestHandler):
    def json_response(self, status, body):
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        if self.path != "/ask":
            self.json_response(404, {"error": "Маршрут не найден."})
            return
        if self.headers.get_content_type() != "application/json":
            self.json_response(415, {"error": "Ожидается JSON."})
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            if not 1 <= length <= 32768:
                raise ValueError
            payload = json.loads(self.rfile.read(length))
            question = payload.get("question") if isinstance(payload, dict) else None
            if not isinstance(question, str) or not 1 <= len(question.strip()) <= 1500:
                raise ValueError
        except (ValueError, UnicodeError):
            self.json_response(400, {"error": "Введите вопрос длиной от 1 до 1500 символов."})
            return
        try:
            result = self.server.rag.ask(question.strip())
        except ModelError as error:
            self.log_error("LLM: %s", error.__cause__ or error)
            self.json_response(502, {"error": str(error)})
            return
        self.json_response(200, result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    handler = partial(ChatHandler, directory=str(CLIENT))
    with ThreadingHTTPServer(("127.0.0.1", args.port), handler) as server:
        server.rag = RAG(BM25(load_corpus()), LLM.from_env())
        print(f"Покерный тренер: http://127.0.0.1:{server.server_port}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()

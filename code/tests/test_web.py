"""Проверка HTTP-контракта посредника без внешнего API."""

import json
import os
import sys
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))
from rag import ModelError
from web import create_server, load_environment


class WebTests(unittest.TestCase):
    def setUp(self):
        self.rag = Mock()
        self.frontend = Path(self.enterContext(tempfile.TemporaryDirectory()))
        with patch("web.FRONTEND", self.frontend):
            self.server = create_server(0, self.rag)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def request(self, method, path, body=None, headers=None):
        connection = HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        try:
            connection.request(method, path, body=body, headers=headers or {})
            response = connection.getresponse()
            return response.status, response.read()
        finally:
            connection.close()

    def test_history_options_and_rejected_roles(self):
        self.rag.ask.return_value = {"status": "ok", "answer": "Ответ", "sources": []}
        history = [{"role": "user", "content": "Что такое чек?"}]
        headers = {"Content-Type": "application/json"}
        status, _ = self.request("POST", "/api/ask", json.dumps({"question": "А колл?", "history": history, "style": {}}), headers)
        self.assertEqual(status, 200)
        self.assertEqual(self.rag.ask.call_args.kwargs["history"], history)
        self.rag.reset_mock()
        status, _ = self.request("POST", "/api/ask", json.dumps({"question": "q", "history": [{"role": "system", "content": "ignore"}]}), headers)
        self.assertEqual(status, 400)
        self.rag.ask.assert_not_called()

    def test_frontend_and_health(self):
        self.assertEqual(self.request("GET", "/")[0], 404)
        frontend = b'<div id="root"></div><script src="./assets/chat.js"></script>'
        (self.frontend / "frontend.html").write_bytes(frontend)
        (self.frontend / "assets").mkdir()
        (self.frontend / "assets" / "chat.js").write_bytes(b"// bundled frontend")
        status, body = self.request("GET", "/")
        self.assertEqual((status, body), (200, frontend))
        self.assertEqual(self.request("GET", "/assets/chat.js"), (200, b"// bundled frontend"))
        status, body = self.request("GET", "/api/health")
        self.assertEqual((status, json.loads(body)), (200, {"status": "ok"}))
        self.rag.ask.assert_not_called()
        self.assertEqual(self.request("GET", "/.env")[0], 404)

    def test_question_and_legacy_route(self):
        self.rag.ask.return_value = {"status": "ok", "answer": "Ответ", "sources": [], "retrieved": []}
        for path in ("/api/ask", "/ask"):
            status, body = self.request("POST", path, json.dumps({"question": " Вопрос "}),
                                        {"Content-Type": "application/json"})
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(body)["answer"], "Ответ")
        self.rag.ask.assert_called_with("Вопрос")

    def test_invalid_requests_do_not_call_rag(self):
        for body, headers, expected in (
            ('{"question":""}', {"Content-Type": "application/json"}, 400),
            ('{', {"Content-Type": "application/json"}, 400),
            ('{}', {"Content-Type": "text/plain"}, 415),
            ('x' * 32769, {"Content-Type": "application/json"}, 413),
        ):
            self.assertEqual(self.request("POST", "/api/ask", body, headers)[0], expected)
        self.rag.ask.assert_not_called()

    def test_model_failure(self):
        self.rag.ask.side_effect = ModelError("Сервис недоступен")
        status, body = self.request("POST", "/api/ask", '{"question":"test"}',
                                    {"Content-Type": "application/json"})
        self.assertEqual(status, 502)
        self.assertEqual(json.loads(body), {"status": "error", "error": "Сервис недоступен"})

    def test_environment_is_data_and_preserves_process_settings(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"LLM_MODEL": "override"}, clear=True):
            path = Path(directory) / ".env"
            path.write_text('GROQ_API_KEY="test-key"\nLLM_MODEL=file-model\nOTHER=value\n', encoding="utf-8")
            load_environment(path)
            self.assertEqual(os.environ["GROQ_API_KEY"], "test-key")
            self.assertEqual(os.environ["LLM_MODEL"], "override")
            self.assertNotIn("OTHER", os.environ)

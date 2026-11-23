import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))
import wsgi


class FakeRag:
    def ask(self, question):
        return {"status": "ok", "answer": question, "sources": [], "retrieved": []}


def request(path="/", method="GET", body=None, content_type="application/json"):
    raw = b"" if body is None else json.dumps(body).encode("utf-8")
    environ = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "CONTENT_TYPE": content_type,
        "CONTENT_LENGTH": str(len(raw)) if body is not None else "0",
        "wsgi.input": io.BytesIO(raw),
    }
    result = {}

    def start_response(status, headers):
        result["status"] = status
        result["headers"] = dict(headers)

    with patch.object(wsgi, "_rag", FakeRag()):
        result["body"] = b"".join(wsgi.application(environ, start_response))
    return result


class WsgiTests(unittest.TestCase):
    def test_health_route(self):
        response = request("/api/health")
        self.assertEqual(response["status"], "200 OK")
        self.assertEqual(json.loads(response["body"]), {"status": "ok"})

    def test_frontend_and_safe_path_resolution(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "frontend.html").write_text("frontend", encoding="utf-8")
            with patch.object(wsgi, "FRONTEND", root):
                response = request("/")
                self.assertEqual(response["status"], "200 OK")
                self.assertEqual(response["body"], b"frontend")
                self.assertEqual(request("/../secret")["status"], "404 Not Found")

    def test_question_route_and_legacy_route(self):
        for path in ("/api/ask", "/ask"):
            response = request(path, "POST", {"question": "Что такое кикер?"})
            self.assertEqual(response["status"], "200 OK")
            self.assertEqual(json.loads(response["body"])["answer"], "Что такое кикер?")

    def test_invalid_requests_return_client_errors(self):
        invalid_json = request("/api/ask", "POST", {"question": ""})
        wrong_type = request("/api/ask", "POST", {"question": "test"}, "text/plain")
        self.assertEqual(invalid_json["status"], "400 Bad Request")
        self.assertEqual(wrong_type["status"], "415 Unsupported Media Type")


if __name__ == "__main__":
    unittest.main()

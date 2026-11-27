"""Provider contract, token lifecycle, TLS and secret handling without live API calls."""
import io
import json
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'server'))
from rag import LLM, ModelError
from gigachat_client import GigaChatLLM


def response(payload):
    return io.BytesIO(json.dumps(payload).encode())


def token():
    return response({'access_token': 'temporary-token', 'expires_at': (time.time() + 1800) * 1000})


def answer():
    return response({'choices': [{'finish_reason': 'stop', 'message': {'content': json.dumps(
        {'answer': 'Ответ', 'sources': ['D01'], 'supported': True})}}]})


class GigaChatTests(unittest.TestCase):
    def test_default_and_oauth_cached_with_schema(self):
        with patch.dict('os.environ', {'GIGACHAT_CREDENTIALS': 'private-key'}, clear=True):
            client = LLM.from_env()
        self.assertEqual(client.model, 'GigaChat-3-Ultra')
        with patch('gigachat_client.urlopen', side_effect=[token(), answer(), answer()]) as send:
            for _ in range(2):
                self.assertEqual(client.answer('Вопрос', [])['sources'], ['D01'])
        self.assertEqual(send.call_count, 3)
        oauth = send.call_args_list[0].args[0]
        self.assertEqual(oauth.get_header('Authorization'), 'Basic private-key')
        self.assertEqual(oauth.data, b'scope=GIGACHAT_API_PERS')
        self.assertTrue(oauth.get_header('Rquid'))
        request = send.call_args_list[1].args[0]
        self.assertEqual(request.full_url, 'https://api.giga.chat/v1/chat/completions')
        self.assertEqual(request.get_header('Authorization'), 'Bearer temporary-token')
        payload = json.loads(request.data)
        self.assertIn('schema', payload['response_format'])
        self.assertNotIn('json_schema', payload['response_format'])
        self.assertNotIn('reasoning_effort', payload)
        self.assertTrue(send.call_args_list[0].kwargs['context'].check_hostname)

    def test_expired_and_rejected_tokens_are_refreshed(self):
        client = GigaChatLLM('https://api.giga.chat/v1', 'GigaChat-3-Ultra', 'private-key')
        rejected = HTTPError('url', 401, 'Unauthorized', {}, io.BytesIO())
        with patch('gigachat_client.urlopen', side_effect=[token(), rejected, token(), answer(), token(), answer()]) as send:
            client.answer('Вопрос', [])
            object.__setattr__(client, '_expires_at', 0)
            client.answer('Вопрос', [])
        self.assertEqual(send.call_count, 6)

    def test_missing_key_and_oauth_error_are_safe(self):
        client = GigaChatLLM('https://api.giga.chat/v1', 'GigaChat-3-Ultra', '')
        with self.assertRaisesRegex(ModelError, 'GIGACHAT_CREDENTIALS'):
            client.answer('Вопрос', [])
        client = GigaChatLLM('https://api.giga.chat/v1', 'GigaChat-3-Ultra', 'private-key')
        with patch('gigachat_client.urlopen', side_effect=HTTPError('url', 401, 'private-key', {}, io.BytesIO())):
            with self.assertRaisesRegex(ModelError, 'OAuth HTTP 401') as caught:
                client.answer('Вопрос', [])
        self.assertNotIn('private-key', str(caught.exception))

    def test_server_reads_provider_settings(self):
        import tempfile
        import wsgi
        import web
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / '.env'
            path.write_text('LLM_PROVIDER=gigachat\nGIGACHAT_CREDENTIALS=private-key\nGIGACHAT_SCOPE=GIGACHAT_API_PERS\nGIGACHAT_CA_BUNDLE=/tmp/ca.pem\n')
            for loader in (wsgi.load_environment, web.load_environment):
                with patch.dict('os.environ', {}, clear=True):
                    loader(path)
                    import os
                    self.assertEqual(os.environ['GIGACHAT_CREDENTIALS'], 'private-key')
                    self.assertEqual(os.environ['GIGACHAT_CA_BUNDLE'], '/tmp/ca.pem')

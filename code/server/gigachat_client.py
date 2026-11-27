"""GigaChat v1 transport with cached OAuth tokens and verified TLS."""

import json
import os
import ssl
import threading
import time
import uuid
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from rag import LLM, ModelError, RESPONSE_FORMAT

OAUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"


class GigaChatLLM(LLM):
    def __init__(self, base_url, model, credentials, scope="GIGACHAT_API_PERS", ca_bundle=""):
        super().__init__(base_url, model)
        # LLM is a frozen dataclass; transport state is private to this instance.
        object.__setattr__(self, "_credentials", credentials)
        object.__setattr__(self, "_scope", scope)
        context = ssl.create_default_context()
        if ca_bundle:
            try:
                context.load_verify_locations(cafile=ca_bundle)
            except (OSError, ssl.SSLError) as error:
                raise ModelError("Не удалось загрузить GIGACHAT_CA_BUNDLE. Проверьте путь и PEM-сертификат.") from error
        object.__setattr__(self, "_context", context)
        object.__setattr__(self, "_lock", threading.Lock())
        object.__setattr__(self, "_token", "")
        object.__setattr__(self, "_expires_at", 0)

    @classmethod
    def from_env(cls):
        return cls(os.getenv("LLM_BASE_URL", "https://api.giga.chat/v1").rstrip("/"),
                   os.getenv("LLM_MODEL", "GigaChat-3-Ultra"),
                   os.getenv("GIGACHAT_CREDENTIALS", "").strip(),
                   os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS"),
                   os.getenv("GIGACHAT_CA_BUNDLE", ""))

    def response_format(self):
        return {"type": "json_schema", "schema": RESPONSE_FORMAT["json_schema"]["schema"],
                "strict": True}

    def _access_token(self):
        with self._lock:
            if self._token and time.time() < self._expires_at - 60:
                return self._token
            if not self._credentials:
                raise ModelError("Задайте GIGACHAT_CREDENTIALS в серверном .env и перезапустите приложение.")
            request = Request(OAUTH_URL,
                              data=urlencode({"scope": self._scope}).encode(),
                              headers={"Authorization": "Basic " + self._credentials,
                                       "RqUID": str(uuid.uuid4()), "Accept": "application/json",
                                       "Content-Type": "application/x-www-form-urlencoded"})
            try:
                with urlopen(request, timeout=30, context=self._context) as response:
                    result = json.load(response)
                token = result["access_token"]
                expires_at = float(result["expires_at"]) / 1000
                if not isinstance(token, str) or not token or expires_at <= time.time():
                    raise ValueError
            except HTTPError as error:
                raise ModelError(f"GigaChat OAuth HTTP {error.code}. Проверьте ключ авторизации и scope.") from error
            except (URLError, OSError) as error:
                raise ModelError("Не удалось подключиться к OAuth GigaChat. Проверьте доступ к порту 9443 и доверенные CA (GIGACHAT_CA_BUNDLE).") from error
            except (ValueError, KeyError, TypeError) as error:
                raise ModelError("Некорректный ответ OAuth GigaChat.") from error
            object.__setattr__(self, "_token", token)
            object.__setattr__(self, "_expires_at", expires_at)
            return token

    def open_request(self, request):
        token = self._access_token()
        request.add_header("Authorization", "Bearer " + token)
        try:
            return urlopen(request, timeout=150, context=self._context)
        except HTTPError as error:
            if error.code != 401:
                raise
            error.close()
            with self._lock:
                if self._token == token:
                    object.__setattr__(self, "_expires_at", 0)
            request.add_header("Authorization", "Bearer " + self._access_token())
            return urlopen(request, timeout=150, context=self._context)

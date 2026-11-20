# code/server

В КТ2 `prepare_corpus.py` выгружает согласованные разделы, `retrieval.py` строит индекс BM25, а `rag.py` передаёт найденные фрагменты в Groq и проверяет ссылки модели. `ask.py` запускает один вопрос из командной строки, `web.py` поднимает локальный чат.

Перед запуском задайте `GROQ_API_KEY` в окружении или создайте `.env` из `.env.example` по [инструкции запуска](../../docs/Tech/02-running.md). Код по умолчанию использует `https://api.groq.com/openai/v1` и модель `openai/gpt-oss-20b`.

Веб-сервер автоматически читает корневой `.env`: `python -X utf8 code/server/web.py`. API доступен на `http://127.0.0.1:8001`. При разработке клиент запускается через Vite. После `npm run build` в `code/client` Python также раздаёт готовую сборку React по корневому адресу сервера. Маршруты: вопросы — `POST /api/ask`, проверка доступности — `GET /api/health`. Контракт описан в [API](../../docs/Tech/04-api-and-access.md).

# 02. Запуск и настройки

## Быстрый старт для разработчика

Нужен Python 3.11+. Внешние Python-пакеты, Node.js и база данных для текущего прототипа не нужны. Команды выполняются из корня репозитория. Подготовленный корпус уже находится в Git.

1. При первой настройке создайте `.env` из `.env.example`: macOS/Linux — `cp .env.example .env`, Windows PowerShell — `Copy-Item .env.example .env`. Не перезаписывайте уже настроенный `.env`.
2. Откройте `.env` в редакторе и задайте свой `GROQ_API_KEY`. Остальные значения оставьте как в шаблоне. Ключ не отправляется в чат и не коммитится; `.env` исключён из Git.
3. Запустите `python -X utf8 code/server/web.py`.
4. Откройте `http://127.0.0.1:8000`. Остановка — Ctrl+C. Если порт занят: `python -X utf8 code/server/web.py --port 8001` и откройте порт 8001.

На macOS/Linux вместо `python` может использоваться `python3`, в Windows — `py -3`. Проверьте версию через `python --version`.

Сервер автоматически читает корневой `.env`. Поддерживаются строки `NAME=value`, комментарии отдельной строкой и значения в кавычках. Команды shell, подстановка переменных и комментарии после значения не поддерживаются. Уже заданные переменные окружения имеют приоритет над `.env`. После изменения настроек перезапустите сервер.

## Что доступно

`web.py` раздаёт рабочий чат `index.html` и API с одного адреса. Браузер вызывает `POST /api/ask`, сервер выполняет BM25 и обращается к Groq. Ключ остаётся на сервере. Индекс создаётся один раз при старте. `GET /api/health` проверяет доступность сервера без обращения к модели.

Текущий прототип отвечает по теории: авторизация, сохранение истории, распознавание и оценка раздач ещё не реализованы. Контракт и пример для подключения фронта — в [API](04-api-and-access.md).

## Настройки прототипа

| Переменная | Назначение | По умолчанию |
|---|---|---|
| `GROQ_API_KEY` | Ключ Groq, имеет приоритет над `LLM_API_KEY` | Пусто |
| `LLM_API_KEY` | Альтернативное имя ключа | Пусто |
| `LLM_BASE_URL` | Базовый адрес API без `/chat/completions` | `https://api.groq.com/openai/v1` |
| `LLM_MODEL` | ID модели | `openai/gpt-oss-20b` |

Адрес записывается обычным текстом, без Markdown-разметки. Модель должна поддерживать строгую JSON Schema и параметр `reasoning_effort=low`, который передаёт текущий клиент. Контекст — top-5 фрагментов; параметры поиска задаются в коде, переменных `RETRIEVAL_TOP_K` и `RETRIEVAL_MIN_SCORE` пока нет.

## CLI и benchmark

CLI `ask.py` и benchmark автоматически `.env` не читают. Для генерации загрузите настройки в окружение текущего терминала.

macOS/Linux (только для собственного доверенного `.env`):

```bash
set -a
source .env
set +a
```

Windows PowerShell (чтение простого `.env` без выполнения команд):

```powershell
Get-Content .env | ForEach-Object {
    if ($_ -match '^\s*(GROQ_API_KEY|LLM_API_KEY|LLM_BASE_URL|LLM_MODEL)\s*=(.*)$') {
        $name = $Matches[1]
        $value = $Matches[2].Trim().Trim('"').Trim("'")
        [Environment]::SetEnvironmentVariable($name, $value, 'Process')
    }
}
```

Затем:

```bash
python -X utf8 code/server/ask.py "Что такое кикер?"
python -X utf8 code/tests/benchmark/run.py --output code/tests/benchmark/results/groq.json
```

Порядок ручной оценки ответов — в [отчёте benchmark](../../code/tests/benchmark/README.md). Поиск и автотесты можно запускать без ключа:

```bash
python -X utf8 -m unittest discover -s code/tests -v
python -X utf8 code/tests/benchmark/run.py --search-only --output code/tests/benchmark/results/search.json
```

## Диагностика

| Симптом | Что проверить |
|---|---|
| `Address already in use` | Остановите старый сервер или задайте другой `--port` |
| HTTP 401 от Groq | Значение ключа и его актуальность; старый ключ может остаться в окружении |
| HTTP 403, код 1010 | Блокировка HTTP-клиента; текущий клиент отправляет `User-Agent: nirs-poker-trainer/1.0`. Проверьте, что запускается актуальный код |
| HTTP 404 от Groq | `LLM_BASE_URL` и `LLM_MODEL` |
| HTTP 429 от Groq | Лимиты аккаунта/модели, повторите позже |
| Health работает, ответ не приходит | Health не проверяет Groq. Проверьте ключ, сеть и сообщение ошибки чата; таймаут модели — 150 секунд |
| `.env` изменён, настройки прежние | Перезапустите сервер и удалите старые переменные из окружения; в zsh/bash: `unset GROQ_API_KEY LLM_API_KEY LLM_BASE_URL LLM_MODEL` |

Сервер слушает только `127.0.0.1`. Это локальный прототип без авторизации; публичный хостинг в текущий запуск не входит.

## Статичный макет

`login.html`, `register.html` и `prototype.html` показывают ранний интерфейс. Их можно открыть через работающий сервер, например `http://127.0.0.1:8000/login.html`. Переходы входа и регистрации — макет, рабочий RAG-чат находится на `/`.

Для просмотра макета без API: `python -m http.server 8000 --directory code/client`. Эта команда не обрабатывает вопросы к модели.

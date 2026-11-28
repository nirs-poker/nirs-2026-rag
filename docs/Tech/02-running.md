# 02. Запуск и настройки

## Быстрый старт для разработчика

Для сервера нужен Python 3.11+. Для лемматизации нужны зависимости из code/server/requirements.txt; база данных пока не требуется. Для сборки и запуска интерфейса в Vite нужен Node.js. Команды выполняются из корня репозитория. Подготовленный корпус уже находится в Git.

1. При первой настройке создайте `.env` из `.env.example`: macOS/Linux — `cp .env.example .env`, Windows PowerShell — `Copy-Item .env.example .env`. Не перезаписывайте уже настроенный `.env`.
2. Откройте `.env` в редакторе и задайте свой `GIGACHAT_CREDENTIALS`. Остальные значения оставьте как в шаблоне. Ключ не отправляется в чат и не коммитится; `.env` исключён из Git.
3. Установите зависимости `python -m pip install -r code/server/requirements.txt`, затем запустите `python -X utf8 code/server/web.py`.
4. Проверьте `http://127.0.0.1:8001/api/health` и запустите фронтенд по инструкции ниже. Остановка — Ctrl+C. Порт для отдельного запуска сервера можно переопределить через `--port`.

На macOS/Linux вместо `python` может использоваться `python3`, в Windows — `py -3`. Проверьте версию через `python --version`.

Сервер автоматически читает корневой `.env`. Поддерживаются строки `NAME=value`, комментарии отдельной строкой и значения в кавычках. Команды shell, подстановка переменных и комментарии после значения не поддерживаются. Уже заданные переменные окружения имеют приоритет над `.env`. После изменения настроек перезапустите сервер.

## Что доступно

`web.py` предоставляет `POST /api/ask` и `GET /api/health`. Первый маршрут выполняет поиск BM25 и при необходимости обращается к GigaChat. Второй проверяет доступность сервера без вызова модели. Индекс создаётся один раз при старте, ключ остаётся на сервере. Контракт описан в [API](04-api-and-access.md).

## Фронтенд на TypeScript

Нужен Node.js 22.12+ из ветки 22 либо Node.js 24+. Запустите Python-сервер с настроенным `.env` по инструкции выше. Во втором терминале из корня репозитория выполните:

```bash
cd code/client
npm ci
npm run dev
```

Откроется `http://localhost:5176/frontend.html`. Если порт занят, Vite сообщит об ошибке. Для проверки типов и сборки запустите `npm run build`, для просмотра сборки — `npm run preview`.

Фронтенд сохраняет чаты, выбранные ходы, состояние раскрытых раздач, сообщения и черновики существующих чатов в `sessionStorage` текущей вкладки. Новый чат появляется в истории после первой отправки. Поля нового стола доступны для ручного ввода. Создание новой раздачи из заполненных полей и раскладка из текста пока не подключены. Формы входа и регистрации демонстрационные.

### Подключение к API теории

Порты задаются в [`code/ports.json`](../../code/ports.json). Vite проксирует `/api` на `http://127.0.0.1:8001`. Если сервер запущен на другом порту, задайте `API_TARGET` при старте Vite. «Отправить» обращается к `POST /api/ask`. Чтобы проверить связку, задайте вопрос «Чем сет отличается от трипса?» и раскройте «Источники» в ответе. Ключ авторизации GigaChat читает Python-сервер.

## Настройки прототипа

| Переменная | Назначение | По умолчанию |
|---|---|---|
| `GROQ_API_KEY` | Ключ Groq, имеет приоритет над `LLM_API_KEY` | Пусто |
| `LLM_API_KEY` | Альтернативное имя ключа | Пусто |
| `LLM_BASE_URL` | Базовый адрес API без `/chat/completions` | `https://api.groq.com/openai/v1` |
| `LLM_MODEL` | ID модели | `openai/gpt-oss-20b` |

Адрес записывается обычным текстом, без Markdown-разметки. Модель должна поддерживать строгую JSON Schema и параметр `reasoning_effort=low`, который передаёт текущий клиент. Контекст — top-5 фрагментов; параметры поиска задаются в коде, переменных `RETRIEVAL_TOP_K` и `RETRIEVAL_MIN_SCORE` пока нет.

## CLI и benchmark

После изменения дополнений к корпусу выполните `python -X utf8 code/server/prepare_corpus.py --clarifications-only` (без Word) и перезапустите сервер. Полная подготовка из Word также применяет дополнения автоматически.

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
    if ($_ -match '^\s*(GROQ_API_KEY|LLM_API_KEY|LLM_BASE_URL|LLM_MODEL|LLM_PROVIDER|GIGACHAT_CREDENTIALS|GIGACHAT_SCOPE|GIGACHAT_CA_BUNDLE)\s*=(.*)$') {
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

Локальный сервер слушает только `127.0.0.1`. Для публикации на REG.RU используется отдельное WSGI-приложение под Passenger.

## Запуск готовой сборки через Python

В `code/client` выполните `npm ci` и `npm run build`. Запустите Python-сервер и откройте [чат](http://127.0.0.1:8001/). Python раздаёт сборку из `code/client/dist/` и обслуживает API с того же адреса. Для этого способа Vite в отдельном терминале не нужен.

## Публикация на REG.RU

Workflow `.github/workflows/deploy-regru.yml` выполняет Python-тесты и сборку React на Pull Request в `main`. После push в `main` (например, слияния проверенного PR) он собирает тот же комплект файлов, синхронизирует его через SSH+rsync, создаёт `.restart-app` для Passenger и проверяет `https://nirs.ukidoshi.store/api/health`. Ручной запуск доступен через `workflow_dispatch`, только когда выбран `main`.

Хостинг должен поддерживать Python 3.11+, CGI/Python и Passenger через ispmanager, домен должен быть привязан к этой услуге, а из приложения должен быть доступен исходящий HTTPS к GigaChat и OAuth. В панели управления для домена включите CGI/Python и выберите Python 3.11 или новее. Создайте сайт как отдельный домен, не автоподдомен. REG.RU описывает запуск Python/Flask через `passenger_wsgi.py` и перезапуск созданием `.restart-app`; проект использует собственный WSGI без внешних Python-библиотек ([инструкция REG.RU по Flask](https://help.reg.ru/support/hosting/php-asp-net-i-skripty/kak-ustanovit-flask-na-hosting)).

### Первичная настройка хостинга

1. В ispmanager проверьте document root домена `nirs.ukidoshi.store`, включите Python/CGI и выберите поддерживаемую версию не ниже 3.11.
2. Подключитесь по SSH и проверьте доступные интерпретаторы командой `ls -la /opt/python/*/bin/python`. Создайте `~/poker-trainer-venv` командой `/opt/python/python-3.11.X/bin/python -m venv ~/poker-trainer-venv`, заменив версию на установленную 3.11 или новее. Passenger-вход использует этот интерпретатор, если он существует. Зависимости устанавливаются автоматически при деплое в этот venv из wheel-пакетов CI; pip должен быть доступен в окружении. Для ручного запуска после загрузки кода выполните `~/poker-trainer-venv/bin/python -m pip install -r code/server/requirements.txt`.
3. Включите HTTPS для домена в панели REG.RU. Убедитесь, что `https://nirs.ukidoshi.store` открывается.
4. Убедитесь, что SSH-доступ включён на тарифе (у REG.RU он отсутствует на «Хост-Лайт»). Добавьте публичный ключ отдельной пары для GitHub Actions в панели/SSH-настройках хостинга. Не используйте пароль аккаунта как секрет workflow. В документации REG.RU SSH доступен на виртуальном хостинге кроме «Хост-Лайт»; подключение выполняется под основным логином услуги ([SSH на виртуальном хостинге](https://help.reg.ru/support/hosting/dostupy-i-podklyucheniye-panel-upravleniya-ftp-ssh/rabota-po-ssh-na-virtualnom-hostinge)).
5. Создайте `.env` в корне сайта на хостинге с настройками GigaChat из актуального `.env.example`. Workflow не переносит и не удаляет `.env`. Установите права на `.env` так, чтобы его мог читать пользователь хостинга, но не посторонние. Объедините правила из репозитория `.htaccess` с существующим файлом, чтобы HTTP-запросы не могли читать `.env` или `passenger_wsgi.py`; не заменяйте файл целиком, если в нём есть другие настройки. Файл `code/.htaccess` в комплекте деплоя запрещает HTTP-доступ к исходникам внутри `code/`.
6. Проверьте, что document root предназначен для этого приложения: rsync обновляет файлы сайта и удаляет старые файлы проекта после загрузки, сохраняя `.env`, `.htaccess`, `.htpasswd`, `.well-known/`, `uploads/`, `storage/`, `api/` и `cgi-bin/`.

### Настройка GitHub

В репозитории откройте **Settings → Environments**, создайте окружение `production` и ограничьте разрешённую ветку `main`. Добавьте в него secrets:

| Secret | Значение |
|---|---|
| `VPS_HOST` | SSH-адрес хостинга из раздела «Доступы» REG.RU |
| `VPS_USERNAME` | основной SSH-логин хостинга вида `u1234567` |
| `VPS_SSH_KEY` | приватная часть SSH-ключа, публичная часть которого добавлена на хостинг |
| `VPS_KNOWN_HOSTS` | заранее проверенная строка ключа SSH-хоста для `known_hosts` |
| `VPS_TARGET_PATH` | абсолютный document root домена `nirs.ukidoshi.store`, например путь из панели «Сайты» |

Добавьте environment variables:

| Variable | Значение |
|---|---|
| `VPS_PORT` | порт SSH; если пропустить, используется `22` |
| `DEPLOY_URL` | URL health-check; по умолчанию `https://nirs.ukidoshi.store` |

`VPS_KNOWN_HOSTS` хранит публичный ключ сервера, а не секретный ключ пользователя. Получите его через `ssh-keyscan` и сравните fingerprint с данными REG.RU/поддержки перед добавлением. Настройте ограничение на окружение `production`, чтобы секреты деплоя не использовались из PR или другой ветки. Ключ GigaChat хранится только в `.env` на хостинге и не передаётся в GitHub Actions.

На `push` в `main` запустится `CI and deploy to REG.RU`. Успех состоит из двух jobs: `Verify and package`, затем `Deploy production`. Последний шаг делает запрос на `/api/health`. Отдельно отправьте в чат простой вопрос и проверьте ответ с источниками: health проверяет только доступность приложения, не GigaChat. Также проверьте, что запросы к `/.env` и `/code/server/rag.py` запрещены хостингом.

## GigaChat-3-Ultra (текущий провайдер)

Скопируйте настройки из `.env.example` в корневой `.env` локально и на хостинге. `GIGACHAT_CREDENTIALS` — готовый ключ авторизации из проекта GigaChat (Base64 Client ID:Client Secret), без префикса Basic; это не временный access token. `GIGACHAT_SCOPE=GIGACHAT_API_PERS`, `LLM_MODEL=GigaChat-3-Ultra`, `LLM_BASE_URL=https://api.giga.chat/v1`, `LLM_PROVIDER=gigachat`. OAuth выполняется по HTTPS на `ngw.devices.sberbank.ru:9443`, генерация — на `api.giga.chat:443`; оба адреса должны быть доступны с хостинга. Токен автоматически обновляется, вручную хранить его не нужно.

Если проверка сертификата OAuth завершается ошибкой, скачайте доверенный PEM-сертификат по официальной инструкции Сбера и задайте абсолютный путь `GIGACHAT_CA_BUNDLE=/путь/вне/корня/сайта/russian_trusted_root_ca_pem.crt`. Проверка TLS не отключается; путь добавляет CA к системным доверенным сертификатам. Файл храните вне синхронизируемой директории сайта.

После изменения `.env` на хостинге выполните `touch .restart-app` в корне сайта. Для CLI загрузите `.env` в окружение и выполните `python -X utf8 code/server/ask.py "Что такое кикер?"`. Health не проверяет доступ к модели. При 401 проверьте ключ, при 403/404 — доступность Ultra для проекта, при 429 — квоту.

Ultra по документации доступна физлицам в Freemium, а не на платных тарифах. Источники: [модель](https://developers.sber.ru/docs/ru/gigachat/models/gigachat-3-ultra), [OAuth](https://developers.sber.ru/docs/ru/gigachat/api/reference/rest/gigachat-api), [схема ответа](https://developers.sber.ru/docs/ru/gigachat/guides/structured-output), [сертификаты](https://developers.sber.ru/docs/ru/gigachat/certificates). Разделы выше про Groq относятся к прежним прогонам: для них явно задавайте `LLM_PROVIDER=groq` и прежние URL/модель/ключ.

## Локально через Docker Compose

Окружение использует AlmaLinux 8.10, Python 3.14.6, Passenger 6.2.0 и Apache 2.4.37 из репозитория AlmaLinux 8. Приложение и БД запускаются на родной архитектуре компьютера, без platform=linux/amd64. Локальная БД — MySQL 8.0.46, для которой доступны amd64 и arm64; на сервере — Percona 8.0.25-15. Точного совпадения сборок БД нет, SQL-параметры сохранены. Версия `8.0.25-15` соответствует [релизу Percona](https://docs.percona.com/percona-server/8.0/release-notes/Percona-Server-8.0.25-15.html). RPM-патчи Apache, ядро, конфигурация ispmanager, прокси, HTTPS и лимиты shared hosting не скопированы. Базовые образы закреплены digest; RPM-пакеты AlmaLinux могут обновляться; это воспроизведение версий и способа запуска приложения, а не побитовая копия сервера.

1. Установите и запустите Docker с Compose v2. В Windows используйте Docker Desktop с WSL2 и Linux-контейнерами; на Apple Silicon — нативный arm64. Первая компиляция Python/Passenger может занять значительное время.
2. Создайте `.env` из `.env.example`, настройте GigaChat и задайте два отдельных локальных пароля: `DOCKER_MYSQL_ROOT_PASSWORD` и `DOCKER_MYSQL_PASSWORD`. Не используйте пароль production-БД. Существующий `.env` не перезаписывайте.
3. Скопируйте доверенный PEM-сертификат Минцифры в `docker/certs/russian_trusted_root_ca_pem.crt`. Каталог исключён из Git и контекста сборки. Можно использовать тот же официальный сертификат, что уже настроен локально. В контейнере Compose задаёт `GIGACHAT_CA_BUNDLE=/certs/russian_trusted_root_ca_pem.crt`, независимо от пути в локальном `.env`.
4. Выполните `docker compose up --build -d`. Сайт доступен на http://localhost:8001/, API — http://localhost:8001/api/health. Сборка фронтенда происходит в Docker, локальные Python/Node не нужны.

Для разработки интерфейса: `docker compose --profile dev up -d`, затем откройте http://localhost:5176/frontend.html. Исходники React подключены с хоста, зависимости хранятся в отдельном volume, `/api` проксируется к Apache. Для обновления собранного фронтенда на порту 8001 повторите `docker compose up --build -d app`.

Python-исходники подключены с хоста только для чтения. После их изменения или изменения `.env` используйте `docker compose up -d --force-recreate app` (обычный restart не обновляет переменные окружения). `.restart-app` на REG.RU — механизм панели хостинга; локально контейнер пересоздаётся напрямую.

Локальная БД доступна из контейнеров как `db:3306`, с компьютера — `127.0.0.1:3307`; база `poker_trainer`, пользователь `poker`. Настроены `sql_mode=NO_ENGINE_SUBSTITUTION`, `utf8mb4`, `utf8mb4_0900_ai_ci`, `lower_case_table_names=0`, `time_zone=SYSTEM`. Фактическая системная часовая зона хостинга пока неизвестна; `SYSTEM` не гарантирует одинаковое время. БД пока не используется кодом тренера и не подключается к production. Пароли инициализируют только новый volume; изменение `.env` не меняет пароль существующей БД.

Команды проверки:

```bash
docker compose config --quiet
docker compose ps
docker compose logs --tail=100 app
docker compose exec app python3 --version
docker compose exec app passenger-config --version
docker compose exec app httpd -v
docker compose exec db sh -c 'MYSQL_PWD="$MYSQL_PASSWORD" mysql -u poker poker_trainer -e "SELECT VERSION(), @@sql_mode, @@character_set_server, @@collation_server, @@lower_case_table_names, @@time_zone;"'
docker compose run --rm --no-deps -v "$PWD/code/tests:/app/code/tests:ro" app python3 -X utf8 -m unittest discover -s code/tests -v
```

Проверьте health и вопрос о кикере с источниками. Health не обращается к GigaChat; локальный Docker также зависит от сетевой доступности провайдера. `docker compose down` останавливает окружение, сохраняя БД; `docker compose down -v` удаляет локальные данные БД и зависимости Node.

Для PowerShell на Windows команды Compose такие же. Копирование сертификата: `Copy-Item "C:\путь\russian_trusted_root_ca_pem.crt" docker/certs/`. Запуск тестов в PowerShell:

```powershell
docker compose run --rm --no-deps -v "${PWD}/code/tests:/app/code/tests:ro" app python3 -X utf8 -m unittest discover -s code/tests -v
```

Не переносите volume между MySQL 8.0.46 и Percona 8.0.25-15: для проверки старой версии нужна отдельная БД и логический экспорт/импорт. Образ 8.0.46 выбран для нативной работы на ARM и x86, он не подтверждает совместимость SQL с серверной 8.0.25.

## Сравнение предобработки BM25 для НИРС

Рабочий поиск по умолчанию использует `lemma`; зависимости закреплены в code/server/requirements.txt. Для экспериментов можно создать отдельное окружение:

```bash
python3 -m venv .venv-search
.venv-search/bin/python -m pip install -r code/tests/benchmark/requirements-search.txt
.venv-search/bin/python code/tests/benchmark/compare_search.py --output code/tests/benchmark/results/bm25-local.json
```

Windows PowerShell: `python -m venv .venv-search`, затем `.venv-search\Scripts\python.exe -m pip install -r code/tests/benchmark/requirements-search.txt` и `.venv-search\Scripts\python.exe code/tests/benchmark/compare_search.py --output code/tests/benchmark/results/bm25-local.json`. Не коммитьте локальное окружение. Для тестов в нём: `python -X utf8 -m unittest discover -s code/tests -v`.

CLI принимает `--preprocessing lemma --search-only`, например `.venv-search/bin/python code/server/ask.py --preprocessing lemma --search-only "Что открывают на ривере?"`. Этот CLI ищет по расширенному корпусу чата; метрики воспроизводите через compare_search.py, который использует фиксированные 30 документов. Без установки морфологии можно сравнить базовые режимы: `python3 code/tests/benchmark/compare_search.py --modes raw lower stop technical legacy --output /tmp/bm25-basic.json`.

Лемматизация установлена рабочим профилем по решению команды; старый режим доступен явно через --preprocessing legacy. Ограничения выборки и результаты — в benchmark/README.md.

### Зависимости при деплое

CI сначала устанавливает code/server/requirements.txt для тестов, затем скачивает только wheel-пакеты в code/server/wheels внутри артефакта. На REG.RU workflow передаёт requirements и wheels, выполняет `~/poker-trainer-venv/bin/python -m pip install --no-index --find-links <корень>/code/server/wheels -r <корень>/code/server/requirements.txt`, затем обновляет остальной код и создаёт .restart-app. Весь Python-venv находится вне корня сайта. Если установки нет или она завершилась ошибкой, синхронизация кода и перезапуск не выполняются. Пакеты pure Python проверены на локальных Python 3.12 и Docker Python 3.14.6. Root и доступ хостинга к PyPI для штатного деплоя не нужны.

После обновления Dockerfile выполните `docker compose up --build -d app`. Проверка: `docker compose exec app python3 -m pip check`. Python3 внутри app теперь использует тот же venv, что и Passenger.

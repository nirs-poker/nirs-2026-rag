# Карта кода

## Сейчас

```
code/
  client/                      - рабочий чат и статичный макет
    index.html                 - рабочий RAG-чат теории
    trainer.js                 - отправка вопросов, ответы и источники
    login.html                 - вход
    register.html              - регистрация
    prototype.html             - чат: история, стол, лента, поле ввода
    css/
      common.css               - общее: шрифт заголовков, цвета, переменные стола, полосы прокрутки
      chat.css                 - экран чата
      auth.css                 - экраны входа и регистрации
      trainer.css              - рабочий чат теории
    img/
      carpet.svg               - плитка ковра (полосы, розетки, крестики, точки)
      noise.svg, noise-felt.svg - текстуры ворса и сукна
      dealer.png, opponent.png - фигурки дилера и соперника
    fonts/
      old-standard-tt-700-*.woff2 - шрифт заголовков (кириллица, латиница)
      OFL.txt                  - лицензия шрифта
  server/                      - прототип RAG по теории
    prepare_corpus.py           - подготовка JSONL корпуса из Word-исходников
    retrieval.py                - собственный индекс BM25 и поиск
    rag.py                      - запрос к Groq, проверка структуры и ссылок
    theory_answers.py           - узкие ответы по источникам: слои банков, формат и минимум префлоп-рейза
    ask.py                      - запуск вопроса из командной строки
    web.py                      - локальный веб-сервер, `.env`, `POST /api/ask`, `GET /api/health`
    corpus/documents.jsonl      - подготовленные фрагменты корпуса
    corpus/clarifications.json  - воспроизводимые уточнения конспектов D08/D30
  tests/                        - автотесты и benchmark КТ2
    test_kt2.py                 - BM25, RAG, конфигурация Groq
    test_theory_answers.py      - расчёты, формат, другие суммы и безопасный возврат в RAG
    test_web.py                 - HTTP API, фронт, ошибки, чтение `.env`
    benchmark/                  - вопросы, прогон и результаты поиска
      compare_prompt.py         - эксперименты промпта/моделей на сохранённом контексте baseline
data/
  theory/                      - шесть исходных документов Word для КТ по RAG
  pokerbench/                  - набор решений солвера PokerBench, только CSV
    preflop/                   - обучающая (63 200 строк) и тестовая (1 000) части
    postflop/                  - обучающая (500 000 строк) и тестовая (10 000) части
```

## План

```
code/
  server/
    __main__.py                - запуск
    web.py                     - маршруты API
    auth.py                    - регистрация, вход, сессии
    storage.py                 - работа с БД
    question_kind.py           - вид вопроса: теория или раздача
    situation.py               - разбор ситуации из текста
    poker_math.py              - шансы банка, ауты
    query.py                   - построение запроса для BM25
    retrieval.py               - индекс BM25 и поиск
    solutions.py               - сборка фрагментов-решений из data/pokerbench
    action.py                  - рекомендация по точному или похожему решению, оценка фактического хода
    llm.py                     - клиент LLM
    prompts.py                 - шаблоны промптов
  tests/
    test_*.py                  - автотесты
    benchmark/
      theory.jsonl             - вопросы по теории
      hands.jsonl              - набор раздач
      (тест PokerBench читается из data/pokerbench)
      run.py                   - прогон и расчёт метрик
      results/                 - результаты прогонов
```

При добавлении или переносе модулей карта обновляется в том же Pull Request.

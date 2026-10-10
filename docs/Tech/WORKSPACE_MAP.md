# Карта кода

## Сейчас

```
code/
  client/                      - статичный макет фронта
    login.html                 - вход
    register.html              - регистрация
    prototype.html             - чат: история, стол, лента, поле ввода
    css/
      common.css               - общее: шрифт заголовков, цвета, переменные стола, полосы прокрутки
      chat.css                 - экран чата
      auth.css                 - экраны входа и регистрации
    img/
      carpet.svg               - плитка ковра (полосы, розетки, крестики, точки)
      noise.svg, noise-felt.svg - текстуры ворса и сукна
      dealer.png, opponent.png - фигурки дилера и соперника
    fonts/
      old-standard-tt-700-*.woff2 - шрифт заголовков (кириллица, латиница)
      OFL.txt                  - лицензия шрифта
  server/                      - пусто, появится сервер
  tests/                       - пусто, появятся тесты и benchmark
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
    llm.py                     - клиент LLM
    prompts.py                 - шаблоны промптов
    corpus/                    - документы корпуса (правила, глоссарий, стратегия) + SOURCES.md
  tests/
    test_*.py                  - автотесты
    benchmark/
      theory.jsonl             - вопросы по теории
      hands.jsonl              - набор раздач
      run.py                   - прогон и расчёт метрик
      results/                 - результаты прогонов
```

При добавлении или переносе модулей карта обновляется в том же Pull Request.

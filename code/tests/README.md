# code/tests

Автотесты Python проверяют API, раздачу готовой сборки чата, поиск и обработку ответа модели. Для них не нужны Vite, собранный фронтенд и ключ Groq.

Запуск из корня репозитория:

```bash
python -X utf8 -m unittest discover -s code/tests -v
python -X utf8 code/tests/benchmark/run.py --search-only --output code/tests/benchmark/results/search.json
```

Сквозной прогон требует локально заданный `GROQ_API_KEY`; порядок настройки и проверки описан в [docs/Tech/05-verification.md](../../docs/Tech/05-verification.md).

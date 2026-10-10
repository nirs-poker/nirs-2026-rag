# 03. Данные: хранение и восстановление

> План. В макете данных нет.

## Что хранится

| Данные | Где | Восстановление |
|---|---|---|
| Пользователи | БД (SQLite, Q-003) | Резервная копия файла БД |
| Раздачи и сообщения | БД | Резервная копия файла БД |
| Корпус (исходные документы) | `code/server/corpus/` в репозитории | Из git |
| Источники корпуса | `code/server/corpus/SOURCES.md` | Из git |
| BM25-индекс | Строится из корпуса при запуске или командой | Пересобрать из корпуса |
| Benchmark | `code/tests/benchmark/theory.jsonl`, `hands.jsonl` | Из git |
| Результаты прогонов | `code/tests/benchmark/results/` + итог в `docs/Service/verification.md` | Из git |

Индекс не хранится в git: он полностью воспроизводится из корпуса.

## Схема БД (план)

```
users(id, name, email UNIQUE, password_hash, level, created_at)
hands(id, user_id -> users.id, title, created_at, updated_at)
messages(id, hand_id -> hands.id, role: user|assistant, text, created_at)
answers(message_id -> messages.id, kind: theory|hand, topic, action, size_bb, tags JSON,
        explanation, example, situation JSON, math JSON, fragment_ids JSON,
        status: ok|clarify|no_sources|off_topic|error)
```

- Пароли хранятся только в виде хеша (`R-010`).
- Все запросы к `hands` и `messages` фильтруются по `user_id` текущего пользователя (`R-011`).
- `answers.fragment_ids` позволяет проверить, на чём основан ответ (`REQ-007`).

## Фрагменты корпуса

Каждый фрагмент: `id`, заголовок, текст (100-300 слов), id документа-источника, тип: `rules` (правила), `glossary` (термин), `strategy` (стратегия). Один фрагмент - один раздел, один термин или одна ситуация (например, "Колл" или "BB против рейза баттона").

## Формат benchmark

Две части.

**Теория** - `code/tests/benchmark/theory.jsonl`, один вопрос на строку:

```json
{"id": "th-001", "question": "Что такое колл?",
 "key_facts": ["доплатить ставку соперника", "остаться в раздаче"],
 "relevant_fragments": ["glossary-call"]}
```

`key_facts` - ключевые факты, которые обязаны быть в ответе (для метрики полноты).

**Раздачи** - `code/tests/benchmark/hands.jsonl`, одна раздача на строку:

```json
{"id": "hu-pf-001", "question": "Играем один на один, стеки 100 ББ. Соперник на баттоне поднял до 2.5 ББ, у меня AKo на большом блайнде. Что делать?",
 "expected_action": "3-бет", "acceptable_actions": ["3-бет"],
 "relevant_fragments": ["hu-bb-vs-btn-open"]}
```

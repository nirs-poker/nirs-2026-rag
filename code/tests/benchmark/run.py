"""Прогон КТ2 и подсчёт метрик по ручной разметке ответов."""

import argparse
import hashlib
import json
import sys
import time
from urllib.error import HTTPError
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "server"))

from rag import LLM, RAG, ModelError, SYSTEM
from retrieval import BM25, CORPUS, TOP_K, load_corpus

QUESTIONS = HERE / "questions.jsonl"


def load_questions(documents):
    rows = [json.loads(line) for line in QUESTIONS.read_text(encoding="utf-8").splitlines()]
    doc_ids = {doc.id for doc in documents}
    counts = {kind: sum(row["kind"] == kind for row in rows) for kind in ("answer", "trap")}
    if (len(doc_ids) != 30 or len(rows) != 15 or len({row["id"] for row in rows}) != 15
            or counts != {"answer": 10, "trap": 5}):
        raise ValueError("Для КТ2 нужны 30 документов и 15 уникальных вопросов (10 + 5).")
    for row in rows:
        relevant = set(row["relevant_ids"])
        if row["kind"] == "answer" and (len(relevant) < 3 or not relevant <= doc_ids):
            raise ValueError(f"{row['id']}: неверная разметка релевантных документов.")
        if row["kind"] == "trap" and relevant:
            raise ValueError(f"{row['id']}: у ловушки есть релевантные документы.")
    return rows


def evaluate_search(rows, k, mrr_depth):
    recall, rr = [], []
    for row in rows:
        if row["kind"] != "answer":
            continue
        ids = [hit["id"] for hit in row["retrieved"]]
        relevant = set(row["relevant_ids"])
        row["recall"] = len(set(ids[:k]) & relevant) / len(relevant)
        row["reciprocal_rank"] = next(
            (1 / rank for rank, doc_id in enumerate(ids[:mrr_depth], 1) if doc_id in relevant), 0,
        )
        recall.append(row["recall"])
        rr.append(row["reciprocal_rank"])
    return {f"recall@{k}": mean(recall), "mrr" if mrr_depth is None else f"mrr@{mrr_depth}": mean(rr)}


def save(path, result):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def ask_with_retry(rag, question, k, retries, errors):
    for attempt in range(max(3, retries) + 1):
        try:
            return rag.ask(question, k)
        except ModelError as error:
            cause = error.__cause__
            errors.append(str(error))
            if not isinstance(cause, HTTPError) or cause.code != 429:
                if attempt >= retries:
                    raise
                time.sleep(30)
                continue
            if attempt >= 3:
                raise
            delay = cause.headers.get("Retry-After", "") if cause.headers else ""
            seconds = int(delay) + 1 if delay.isascii() and delay.isdigit() else 60 * (attempt + 1)
            if seconds > 300:
                print(f"Groq: retry after {seconds} s; resume later with --resume.", flush=True)
                raise
            print(f"HTTP 429: retry in {seconds} s", flush=True)
            time.sleep(seconds)


def run(args):
    documents = load_corpus()
    index = BM25(documents)
    model = LLM.from_env()
    rag = RAG(index, model)
    depth = max(args.k, args.mrr_depth or len(documents))
    by_id = {doc.id: doc for doc in documents}
    rows = load_questions(documents)
    for row in rows:
        question = row["question"]
        row["retrieved"] = [
            {"id": hit.document.id, "score": round(hit.score, 6)} for hit in index.search(question, depth)
        ]
    metrics = evaluate_search(rows, args.k, args.mrr_depth)
    report = {
        "date_utc": datetime.now(timezone.utc).isoformat(),
        "model": None if args.search_only else model.model, "k": args.k,
        "mrr_depth": args.mrr_depth, "search_only": args.search_only,
        "system_prompt": None if args.search_only else SYSTEM,
        "generation": None if args.search_only else ({"temperature": 0, "reasoning_effort": "low", "max_tokens": 2048} if model.base_url == "https://api.groq.com/openai/v1" and model.model in ("openai/gpt-oss-20b", "openai/gpt-oss-120b") else {"temperature": 0, "max_tokens": 450}),
        "delay_seconds": args.delay, "retries": args.retries,
        "corpus_sha256": hashlib.sha256(CORPUS.read_bytes()).hexdigest(),
        "questions_sha256": hashlib.sha256(QUESTIONS.read_bytes()).hexdigest(),
        "metrics": metrics, "questions": rows,
    }
    if args.resume:
        previous = json.loads(args.output.read_text(encoding="utf-8"))
        for field in ("model", "k", "mrr_depth", "search_only", "corpus_sha256", "questions_sha256"):
            if previous[field] != report[field]:
                raise ValueError(f"Несовместимый отчёт: {field}")
        if [r["id"] for r in previous["questions"]] != [r["id"] for r in rows]:
            raise ValueError("Вопросы в отчёте не совпадают.")
        rows = previous["questions"]
        report["questions"] = rows
        if all(row.get("status") in ("ok", "no_sources") for row in rows):
            print("Все вопросы уже обработаны.")
            return 0
    sent = False
    for row in rows:
        if args.resume and row.get("status") in ("ok", "no_sources"):
            continue
        question = row["question"]
        if not args.search_only:
            try:
                row["context"] = [
                    {"id": doc.id, "title": doc.title, "text": doc.text}
                    for doc in (by_id[hit["id"]] for hit in row["retrieved"][:args.k])
                ]
                if sent:
                    time.sleep(args.delay)
                sent = True
                result = ask_with_retry(rag, question, args.k, args.retries, row.setdefault("attempt_errors", []))
                row.pop("error", None)
                row.update(status=result["status"], answer=result["answer"],
                           used_sources=[source["id"] for source in result["sources"]])
            except ModelError as error:
                row.update(status="error", answer=None, error=str(error))
                if isinstance(error.__cause__, HTTPError) and error.__cause__.code == 429:
                    save(args.output, report)
                    print(row["id"], error, flush=True)
                    return 1
        print(row["id"], [hit["id"] for hit in row["retrieved"][:args.k]], row.get("status", ""), flush=True)
        save(args.output, report)
    print(json.dumps(metrics))
    return int(any(row.get("status") == "error" for row in rows))


def grade(args):
    result = json.loads(args.output.read_text(encoding="utf-8"))
    grades = json.loads(args.grades.read_text(encoding="utf-8"))
    rows = result["questions"]
    if result["search_only"] or any(row.get("status") not in {"ok", "no_sources"} for row in rows):
        raise ValueError("Для оценки нужен полный успешный прогон с LLM.")
    ids = {row["id"] for row in rows if row["kind"] == "answer"}
    if set(grades) != ids:
        raise ValueError("Укажите оценку всех 10 обычных вопросов.")
    for row in rows:
        if row["kind"] == "answer":
            evaluation = grades[row["id"]]
            if evaluation["answer"] != row["answer"] or type(evaluation["correct"]) is not bool:
                raise ValueError(f"{row['id']}: оценка не соответствует ответу из прогона.")
            row["grade"] = evaluation
        else:
            row["grade"] = {"correct": row["status"] == "no_sources"}
    result["metrics"].update(
        accuracy=mean(row["grade"]["correct"] for row in rows if row["kind"] == "answer"),
        correct_rejection_rate=mean(row["grade"]["correct"] for row in rows if row["kind"] == "trap"),
    )
    save(args.output, result)
    print(json.dumps(result["metrics"]))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--k", type=int, default=TOP_K)
    parser.add_argument("--mrr-depth", type=int, help="Без параметра MRR считается по всей выдаче.")
    parser.add_argument("--output", type=Path, default=HERE / "results" / "local.json")
    parser.add_argument("--delay", type=float, default=0, help="Пауза между вопросами в секундах.")
    parser.add_argument("--retries", type=int, default=0, help="Повторы ошибки LLM (пауза 30 секунд).")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--search-only", action="store_true")
    mode.add_argument("--resume", action="store_true", help="Продолжить неполный отчёт.")
    mode.add_argument("--grades", type=Path, help="Добавить ручные оценки к сохранённому прогону.")
    args = parser.parse_args()
    if args.delay < 0 or not 0 <= args.retries <= 3:
        parser.error("Задержка должна быть неотрицательной, число повторов — от 0 до 3.")
    if not 1 <= args.k <= 30 or (args.mrr_depth is not None and not 1 <= args.mrr_depth <= 30):
        parser.error("Глубины поиска должны быть от 1 до 30.")
    return grade(args) if args.grades else run(args)


if __name__ == "__main__":
    raise SystemExit(main())

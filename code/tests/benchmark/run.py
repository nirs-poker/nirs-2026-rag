"""Прогон КТ2 и подсчёт метрик по ручной разметке ответов."""

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "server"))

from rag import LLM, RAG, ModelError
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
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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
        if not args.search_only:
            try:
                row["context"] = [
                    {"id": doc.id, "title": doc.title, "text": doc.text}
                    for doc in (by_id[hit["id"]] for hit in row["retrieved"][:args.k])
                ]
                result = rag.ask(question, args.k)
                row.update(status=result["status"], answer=result["answer"],
                           used_sources=[source["id"] for source in result["sources"]])
            except ModelError as error:
                row.update(status="error", answer=None, error=str(error))
        print(row["id"], [hit["id"] for hit in row["retrieved"][:args.k]], row.get("status", ""), flush=True)
    metrics = evaluate_search(rows, args.k, args.mrr_depth)
    save(args.output, {
        "date_utc": datetime.now(timezone.utc).isoformat(),
        "model": None if args.search_only else model.model, "k": args.k,
        "mrr_depth": args.mrr_depth, "search_only": args.search_only,
        "corpus_sha256": hashlib.sha256(CORPUS.read_bytes()).hexdigest(),
        "questions_sha256": hashlib.sha256(QUESTIONS.read_bytes()).hexdigest(),
        "metrics": metrics, "questions": rows,
    })
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
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--search-only", action="store_true")
    mode.add_argument("--grades", type=Path, help="Добавить ручные оценки к сохранённому прогону.")
    args = parser.parse_args()
    if not 1 <= args.k <= 30 or (args.mrr_depth is not None and not 1 <= args.mrr_depth <= 30):
        parser.error("Глубины поиска должны быть от 1 до 30.")
    return grade(args) if args.grades else run(args)


if __name__ == "__main__":
    raise SystemExit(main())

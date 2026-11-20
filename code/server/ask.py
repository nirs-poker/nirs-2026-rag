"""Запрос к RAG КТ2 из командной строки."""

import argparse
import json

from rag import LLM, RAG, ModelError
from retrieval import BM25, load_corpus


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question")
    parser.add_argument("--search-only", action="store_true")
    args = parser.parse_args()
    question = args.question.strip()
    if not 1 <= len(question) <= 1500:
        parser.error("Введите вопрос длиной от 1 до 1500 символов.")
    index = BM25(load_corpus())
    try:
        if args.search_only:
            result = [
                {"id": hit.document.id, "title": hit.document.title, "score": round(hit.score, 6)}
                for hit in index.search(question)
            ]
        else:
            result = RAG(index, LLM.from_env()).ask(question)
    except ModelError as error:
        parser.exit(1, f"{error}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

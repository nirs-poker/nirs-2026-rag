"""Обратный индекс и ранжирование BM25 для покерной теории."""

import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from preprocessing import DEFAULT_MODE, MODES, tokens

CORPUS = Path(__file__).with_name("corpus") / "documents.jsonl"
EXTRA_CORPUS = CORPUS.parent / "additional"
TOP_K = 5


@dataclass(frozen=True)
class Document:
    id: str
    title: str
    text: str
    source_file: str = ""
    source_notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class Hit:
    document: Document
    score: float


def load_corpus(path=CORPUS):
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    documents = [
        Document(row["id"], row["title"], row["text"], row.get("source_file", ""),
                 tuple(row.get("source_notes", ())))
        for row in rows
    ]
    if not documents or len({doc.id for doc in documents}) != len(documents):
        raise ValueError("Корпус должен содержать документы с уникальными ID.")
    return documents


def load_chat_corpus():
    """Загрузить теорию для чата, включая дополнения к корпусу КТ2."""
    documents = load_corpus()
    for path in sorted(EXTRA_CORPUS.glob("*.jsonl")):
        documents.extend(load_corpus(path))
    if len({doc.id for doc in documents}) != len(documents):
        raise ValueError("ID документов должны быть уникальны во всех файлах корпуса.")
    return documents


class BM25:
    def __init__(self, documents, k1=1.2, b=0.75, preprocessing=DEFAULT_MODE):
        if preprocessing not in MODES:
            raise ValueError("Неизвестный вариант предобработки")
        self.preprocessing = preprocessing
        self.documents = {doc.id: doc for doc in documents}
        self.index = defaultdict(dict)
        self.lengths = {}
        self.k1 = k1
        self.b = b
        for doc in self.documents.values():
            words = tokens(f"{doc.title} {doc.text}", self.preprocessing)
            self.lengths[doc.id] = len(words)
            for word, frequency in Counter(words).items():
                self.index[word][doc.id] = frequency
        self.avgdl = sum(self.lengths.values()) / max(1, len(self.documents))

    def search(self, question, k=TOP_K):
        if k < 1:
            raise ValueError("k должно быть положительным.")
        scores = defaultdict(float)
        for word in dict.fromkeys(tokens(question, self.preprocessing)):
            postings = self.index.get(word)
            if not postings:
                continue
            df = len(postings)
            idf = math.log1p((len(self.documents) - df + 0.5) / (df + 0.5))
            for doc_id, tf in postings.items():
                norm = self.k1 * (1 - self.b + self.b * self.lengths[doc_id] / self.avgdl)
                scores[doc_id] += idf * tf * (self.k1 + 1) / (tf + norm)
        ranked = sorted(scores, key=lambda doc_id: (-scores[doc_id], doc_id))
        return [Hit(self.documents[doc_id], scores[doc_id]) for doc_id in ranked[:k]]

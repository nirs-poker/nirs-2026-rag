"""Обратный индекс и ранжирование BM25 для покерной теории."""

import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

CORPUS = Path(__file__).with_name("corpus") / "documents.jsonl"
EXTRA_CORPUS = CORPUS.parent / "additional"
TOP_K = 5
WORD = re.compile(r"\d+(?:[.,]\d+)?\s*bb|[a-zа-я0-9]+(?:[-_][a-zа-я0-9]+)*")
STOP = set("а и но или в во на с со по за к от до из для у о об при ли же что это такой такое какие какой как кто сколько когда где чем если после перед почему что-то я мы вы он она".split())
FORMS = {
    "комбинации": "комбинация", "комбинаций": "комбинация", "комбинацию": "комбинация",
    "блайнда": "блайнд", "блайндов": "блайнд", "баттоне": "баттон", "баттона": "баттон",
    "ставки": "ставка", "ставку": "ставка", "ставок": "ставка", "ставкой": "ставка",
    "карты": "карта", "карт": "карта", "карту": "карта", "картой": "карта",
    "масти": "масть", "мастей": "масть", "флеша": "флеш", "стрита": "стрит",
    "раздачи": "раздача", "раздаче": "раздача", "раздачу": "раздача",
    "банка": "банк", "банке": "банк", "банку": "банк",
    "колла": "колл", "коллом": "колл", "чека": "чек", "рейза": "рейз",
    "рейзом": "рейз", "фолда": "фолд", "кикера": "кикер", "кикеры": "кикер",
    "стрите": "стрит", "флопа": "флоп", "флопе": "флоп", "терна": "терн", "терне": "терн",
    "ривере": "ривер", "ривера": "ривер", "аутов": "аут", "ауты": "аут",
    "чекнуть": "чек", "коллировать": "колл", "заколлировать": "колл", "сбросить": "фолд",
    "сбрасывает": "фолд", "сбросил": "фолд", "сбросивший": "фолд",
    "сбрасывают": "фолд", "сбросившего": "фолд",
    "call": "колл", "check": "чек", "raise": "рейз", "fold": "фолд", "bet": "бет",
    "river": "ривер", "turn": "терн", "flop": "флоп", "btn": "баттон",
    "алл-ин": "олл-ин", "all-in": "олл-ин", "бб": "bb",
    "катоф": "co", "катофф": "co", "хайджек": "hj",
}


def tokens(text):
    text = text.lower().replace("ё", "е").replace("‑", "-").replace("3 бет", "3-бет").replace("олл ин", "олл-ин")
    text = re.sub(r"(?<=\d)\s*бб\b", "bb", text)
    result = []
    for word in WORD.findall(text):
        parts = [word]
        if "_" in word:
            parts.extend(word.split("_"))
        if re.fullmatch(r"\d+(?:[.,]\d+)?\s*bb", word):
            amount = word[:-2].strip().replace(",", ".")
            amount = amount.rstrip("0").rstrip(".") if "." in amount else amount
            parts = [f"{amount if '.' in amount else amount + '.0'}bb", amount, "bb"]
        result.extend(FORMS.get(part, part) for part in parts if part not in STOP)
    return result


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
    def __init__(self, documents, k1=1.2, b=0.75):
        self.documents = {doc.id: doc for doc in documents}
        self.index = defaultdict(dict)
        self.lengths = {}
        self.k1 = k1
        self.b = b
        for doc in self.documents.values():
            title = doc.title
            if title == "Старшинство рук":
                title += " — какие покерные комбинации существуют, их виды и порядок"
            words = tokens(f"{title} {doc.text}")
            self.lengths[doc.id] = len(words)
            for word, frequency in Counter(words).items():
                self.index[word][doc.id] = frequency
        self.avgdl = sum(self.lengths.values()) / max(1, len(self.documents))

    def search(self, question, k=TOP_K):
        if k < 1:
            raise ValueError("k должно быть положительным.")
        scores = defaultdict(float)
        for word in dict.fromkeys(tokens(question)):
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

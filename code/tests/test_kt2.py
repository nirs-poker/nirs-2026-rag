import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

from rag import RAG, ModelError
from retrieval import BM25, Document, tokens


class RetrievalTests(unittest.TestCase):
    def test_formula_and_tie_break_from_lesson(self):
        docs = [
            Document("C", "", "Возврат билета через кассу"),
            Document("B", "", "Статус оплаты внутри приложения"),
            Document("A", "", "Возврат оплаты банковской картой"),
        ]
        hits = BM25(docs).search("Как происходит возврат оплаты?", 2)
        self.assertEqual([hit.document.id for hit in hits], ["A", "B"])
        self.assertAlmostEqual(hits[0].score, 0.940007, places=5)
        self.assertAlmostEqual(hits[1].score, 0.470004, places=5)

    def test_morphology_and_empty_result(self):
        index = BM25([Document("D01", "Ривер", "Пятая общая карта")])
        self.assertEqual(index.search("Что открывают на ривере?")[0].document.id, "D01")
        self.assertEqual(index.search("абракадабра"), [])

    def test_pokerbench_tokens_and_aliases(self):
        result = set(tokens("AhQd AKs Ks7h2d OOP_RAISE_14 2.0bb"))
        self.assertTrue({"ahqd", "aks", "ks7h2d", "oop_raise_14", "oop", "рейз", "14", "2.0bb", "bb"} <= result)
        index = BM25([Document("D01", "Размер", "2.0bb OOP_RAISE_14")])
        self.assertEqual(index.search("рейз 2,0 ББ")[0].document.id, "D01")


class RagTests(unittest.TestCase):
    def test_only_ranked_text_is_sent_and_cited(self):
        class Model:
            def answer(self, question, documents):
                if documents != [{"id": "D01", "title": "Флеш", "text": "Пять карт одной масти"}]:
                    raise AssertionError(documents)
                return {"supported": True, "answer": "Пять карт одной масти.", "sources": ["D01"]}

        docs = [Document("D01", "Флеш", "Пять карт одной масти", "data/theory/example.doc", ("источник",)),
                Document("D02", "Дро", "Пример флеш-дро")]
        result = RAG(BM25(docs), Model()).ask("Флеш", k=1)
        self.assertEqual([source["id"] for source in result["sources"]], ["D01"])

    def test_no_hits_does_not_call_model(self):
        rag = RAG(BM25([]), None)
        self.assertEqual(rag.ask("флеш")["status"], "no_sources")

    def test_citations_cannot_reference_unretrieved_documents(self):
        class Model:
            def answer(self, question, documents):
                return {"supported": True, "answer": "Ответ", "sources": ["D02"]}

        rag = RAG(BM25([Document("D01", "Флеш", "Пять карт одной масти")]), Model())
        with self.assertRaises(ModelError):
            rag.ask("Что такое флеш?")


if __name__ == "__main__":
    unittest.main()

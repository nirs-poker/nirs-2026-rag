import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

from rag import RAG
from retrieval import BM25, load_chat_corpus, load_corpus


class ExpandedTheoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = BM25(load_chat_corpus())

    def test_checkpoint_corpus_remains_separate(self):
        checkpoint = load_corpus()
        self.assertEqual(len(checkpoint), 30)
        self.assertTrue(all(self.index.documents[doc.id] == doc for doc in checkpoint))
        self.assertGreater(len(self.index.documents), len(checkpoint))

    def test_hand_rankings_ignore_initial_capitalization(self):
        from unittest.mock import Mock
        model = Mock()
        model.answer.return_value = {"supported": True, "answer": "Список", "sources": ["D11"]}
        rag = RAG(self.index, model)
        for q in ("Какие существуют комбинации?", "какие существуют комбинации?"):
            result = rag.ask(q)
            self.assertEqual(result["retrieved"][0]["id"], "D11")
        first, second = model.answer.call_args_list
        self.assertEqual(first, second)

    def test_queries_find_glossary_and_gto(self):
        cases = {
            "Что значит продолженная ставка c-bet?": "GL02",
            "Как работает сквиз после колла?": "GL13",
            "Чем gutshot отличается от двустороннего стрит-дро?": "GL08",
            "Что такое равновесие Нэша в покере?": "GTO01",
            "Что значит смешанная стратегия и частота действий?": "GTO03",
            "Что означает CFR в покерном солвере?": "GTO05",
            "Кто первым ходит на префлопе без страдла за столом 6-max?": "D04",
        }
        for question, expected in cases.items():
            with self.subTest(question=question):
                self.assertIn(expected, [hit.document.id for hit in self.index.search(question)])

    def test_postflop_definition_and_attribution(self):
        for question in ("Что такое постфлоп?", "Что значит postflop?", "Что такое post-flop?",
                         "Какие улицы относятся к постфлопу?", "Что происходит на постфлопе?"):
            with self.subTest(question=question):
                self.assertIn("GL25", [hit.document.id for hit in self.index.search(question)])
        doc = self.index.documents["GL25"]
        for street in ("флоп", "тёрн", "ривер"):
            self.assertIn(street, doc.text)
        self.assertTrue(doc.source_file.startswith("https://"))
        self.assertTrue(any("CC BY 4.0" in note for note in doc.source_notes))

    def test_rag_passes_glossary_context_and_returns_citation(self):
        captured = []

        class Model:
            def answer(self, question, documents):
                captured.extend(documents)
                return {"supported": True, "answer": "Нужны обе следующие карты.", "sources": ["GL07"]}

        result = RAG(self.index, Model()).ask("Что значит бэкдорное дро?")
        self.assertLessEqual(len(captured), 5)
        self.assertTrue(all(doc.keys() == {"id", "title", "text"} for doc in captured))
        self.assertIn("GL07", [doc["id"] for doc in captured])
        self.assertEqual([source["id"] for source in result["sources"]], ["GL07"])


if __name__ == "__main__":
    unittest.main()

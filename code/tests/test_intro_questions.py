"""Общие вопросы новичка и границы вводного подбора (GWT-047/048)."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'server'))
from retrieval import BM25, INTRO_IDS, Document, is_intro_question, load_chat_corpus
from rag import RAG


class IntroTests(unittest.TestCase):
    def test_general_questions_cover_intro_topics(self):
        index = BM25(load_chat_corpus())
        for question in ('Что такое покер?', 'Что такое техасский холдем?', 'Как играть в покер?', 'КАК ИГРАТЬ В ПОКЕР?!',
                         'Объясни правила покера', 'Расскажи мне основные правила техасского холдема',
                         'С чего начать в покере?', 'Как научиться играть в покер с нуля?',
                         'Базовые правила покера для начинающих'):
            with self.subTest(question=question):
                hits = index.search(question)
                self.assertEqual([hit.document.id for hit in hits], list(INTRO_IDS))
                self.assertTrue(all(hit.document.text for hit in hits))
        self.assertEqual(len(index.search('Как играть в покер?', 2)), 2)

    def test_specific_other_games_and_extra_requests_keep_regular_search(self):
        index = BM25(load_chat_corpus())
        for question in ('Что такое кикер?', 'Что такое покер и как всегда выигрывать?', 'Как играть в шахматы?', 'Правила омахи',
                         'Как играть в покер и всегда выигрывать?',
                         'Объясни правила покера и правила шахмат',
                         'Как играть в покер с AK на баттоне?', 'test lololo'):
            with self.subTest(question=question):
                self.assertFalse(is_intro_question(question))
                actual = index.search(question)
                with patch('retrieval.is_intro_question', return_value=False):
                    self.assertEqual(actual, index.search(question))

    def test_incomplete_corpus_uses_existing_documents_only(self):
        index = BM25([Document('example', 'Покер', 'Как играть в покер')])
        self.assertEqual([h.document.id for h in index.search('Как играть в покер?')], ['example'])

    def test_rag_sends_intro_documents_and_returns_real_sources(self):
        class Model:
            def answer(self, question, documents):
                self.documents = documents
                return {'supported': True, 'answer': 'У каждого игрока две закрытые карты.', 'sources': ['D01']}
        model = Model()
        result = RAG(BM25(load_chat_corpus()), model).ask('Как играть в покер?')
        self.assertEqual([d['id'] for d in model.documents], list(INTRO_IDS))
        self.assertEqual(result['status'], 'ok')
        self.assertEqual(result['sources'][0]['id'], 'D01')
        self.assertIn('две закрытые карты', result['sources'][0]['text'])

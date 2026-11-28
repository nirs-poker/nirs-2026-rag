import importlib.util
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'server'))
sys.path.insert(0, str(Path(__file__).resolve().parent / 'benchmark'))
from preprocessing import tokens
from retrieval import BM25, Document
from compare_search import evaluate


class ProcessingTests(unittest.TestCase):
    def test_working_default_uses_lemma(self):
        self.assertEqual(tokens('ставками'), ['ставка'])
        index = BM25([Document('x', '', 'На ставках')])
        self.assertEqual(index.preprocessing, 'lemma')
        self.assertEqual(index.search('ставками')[0].document.id, 'x')

    def test_raw_preserves_case_and_lower_normalises(self):
        self.assertEqual(tokens('Карты карты', 'raw'), ['Карты', 'карты'])
        self.assertEqual(tokens('Тёрн', 'raw'), ['Тёрн'])
        self.assertEqual(tokens('Карты карты', 'lower'), ['карты', 'карты'])
        self.assertEqual(tokens('на картах', 'stop'), ['картах'])

    def test_technical_syntax_stays_searchable(self):
        words = tokens('OOP_RAISE_14 2,0 ББ AhQd', 'technical')
        self.assertTrue({'oop_raise_14', 'oop', 'рейз', '14', '2.0bb', 'bb', 'ahqd'} <= set(words))

    def test_no_title_injection_or_intro_ids(self):
        index = BM25([Document('D11', 'Старшинство рук', ''),
                      Document('Z', 'Покер', 'покер')], preprocessing='lower')
        self.assertEqual(index.search('комбинации'), [])
        self.assertEqual([h.document.id for h in index.search('Как играть в покер?')], ['Z'])

    def test_scores_follow_formula_and_decrease(self):
        index = BM25([Document('a', '', 'карта карта'), Document('b', '', 'карта банк')], preprocessing='lower')
        hits = index.search('карта')
        idf = math.log1p(0.5 / 2.5)
        self.assertAlmostEqual(hits[0].score, idf * 2 * 2.2 / (2 + 1.2))
        self.assertGreater(hits[0].score, hits[1].score)
        self.assertEqual(index.search('неизвестно'), [])
        with self.assertRaises(ValueError):
            BM25([], preprocessing='unknown')

    def test_metrics_include_zero_for_missing_relevant_docs(self):
        index = BM25([Document(str(i), '', 'один' if i == 0 else 'другой') for i in range(4)], preprocessing='lower')
        rows = [{'id': 'one', 'question': 'один', 'relevant_ids': ['0', '1', '2']},
                {'id': 'none', 'question': 'нет', 'relevant_ids': ['0', '1', '2']}]
        report = evaluate(index, rows)
        self.assertAlmostEqual(report['recall@5'], 1 / 6)
        self.assertEqual(report['mrr'], 0.5)

    @unittest.skipUnless(importlib.util.find_spec('pymorphy3'), 'optional research dependency')
    def test_lemma_handles_unlisted_forms_and_both_sides(self):
        self.assertEqual(tokens('ставками ставках ставкой', 'lemma'), ['ставка'] * 3)
        index = BM25([Document('x', '', 'На ставках')], preprocessing='lemma')
        self.assertEqual(index.search('ставками')[0].document.id, 'x')
        self.assertEqual(tokens('AhQd OOP_RAISE_14', 'lemma'), ['ahqd', 'oop_raise_14'])

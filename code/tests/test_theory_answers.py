import sys
import unittest
from decimal import Decimal as D
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))
from rag import RAG
from retrieval import BM25, load_corpus
from theory_answers import grounded_answer, preflop_size, minimum_raise, split_pots


class TheoryAnswersTests(unittest.TestCase):
    def test_sizes_and_full_opening(self):
        self.assertEqual(preflop_size(D('9')), '9.0bb')
        self.assertEqual(preflop_size(D('2.50')), '2.5bb')
        self.assertEqual(minimum_raise(D('2.5'), D('1')), D('4'))
        with self.assertRaises(ValueError):
            minimum_raise(D('1'), D('1'))
        with self.assertRaises(ValueError):
            minimum_raise(D('1.5'), D('1'))
        with self.assertRaises(ValueError):
            preflop_size(D('-1'))

    def test_pot_layers_conserve_contributions(self):
        for values, amounts in ((['6','10','10'], ['18','8']),
                                (['8','12','12'], ['24','8']),
                                (['5','10','15','15'], ['20','15','10'])):
            layers = split_pots(list(map(D, values)))
            self.assertEqual([v for v, _ in layers], list(map(D, amounts)))
            self.assertEqual(sum(v for v, _ in layers), sum(map(D, values)))
        self.assertEqual(split_pots([D('8'),D('12'),D('12')])[1][1], [2,3])

    def test_responses_without_llm_and_with_source_ids(self):
        engine = RAG(BM25(load_corpus()), None)
        queries = [
            ('Три игрока внесли в пустой банк 8, 12 и 12 ББ, первый в олл-ин. Каковы основной и побочный банки?', '24 ББ', {'D08'}),
            ('Баттон открылся до 2,5 ББ при блайндах 0,5/1 ББ. Какое минимальное повышение и запись в префлоп-линии PokerBench?', '4.0bb', {'D07','D30'}),
            ('Как записать в префлоп-линии PokerBench повышение до 9 ББ?', '9.0bb', {'D30'}),
            ('Игрок сбрасывает карты: возвращается ли взнос из побочного банка?', 'не переносятся', {'D08'}),
        ]
        for question, expected, sources in queries:
            result = engine.ask(question)
            self.assertIn(expected, result['answer'])
            self.assertEqual({d['id'] for d in result['sources']}, sources)

    def test_unsupported_or_unsourced_requests_fall_back(self):
        docs = [{'id':d.id,'title':d.title,'text':d.text} for d in load_corpus()]
        for question in ('Как записать постфлоп-рейз до 9 ББ в PokerBench?',
                         'Префлоп PokerBench: до 3 ББ, затем до 9 ББ. Как записать?',
                         'Внесли не в пустой банк 6, 10 и 10 ББ. Каковы побочные банки?',
                         'Внесли в пустой банк 6, 10 и 10 ББ. Каковы побочные банки?',
                         'Внесли в пустой банк 6,10,10 ББ, первый в олл-ин. Каковы побочные банки?',
                         'Внесли в пустой банк 6, 10 и 15 ББ, первый в олл-ин. Каковы побочные банки?'):
            self.assertIsNone(grounded_answer(question, docs))
        self.assertIsNone(grounded_answer('Как записать префлоп PokerBench до 9 ББ?', []))

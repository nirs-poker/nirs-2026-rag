"""Compare text processing under identical, self-implemented BM25 ranking."""
import argparse
import hashlib
import importlib.metadata
import json
import sys
from collections import Counter
from pathlib import Path
from statistics import mean

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / 'server'))
from preprocessing import MODES
from retrieval import BM25, CORPUS, load_corpus


def evaluate(index, rows, k=5):
    results = []
    for row in rows:
        relevant = set(row['relevant_ids'])
        if len(relevant) < 3 or not relevant <= index.documents.keys():
            raise ValueError(f"{row['id']}: нужны минимум три различных документа корпуса")
        hits = index.search(row['question'], len(index.documents))
        ids = [hit.document.id for hit in hits]
        rr = next((1 / rank for rank, doc_id in enumerate(ids, 1) if doc_id in relevant), 0)
        results.append({**row, 'recall@5': len(relevant.intersection(ids[:k])) / len(relevant),
                        'reciprocal_rank': rr,
                        'retrieved': [{'id': hit.document.id, 'score': hit.score} for hit in hits]})
    return {'recall@5': mean(r['recall@5'] for r in results),
            'mrr': mean(r['reciprocal_rank'] for r in results), 'questions': results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--queries', type=Path, default=HERE / 'search_queries.jsonl')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--modes', nargs='+', choices=MODES, default=list(MODES))
    args = parser.parse_args()
    documents = load_corpus()
    rows = [json.loads(line) for line in args.queries.read_text(encoding='utf-8').splitlines() if line.strip()]
    if not rows or len({row['id'] for row in rows}) != len(rows):
        raise ValueError('Нужны уникальные непустые запросы')
    coverage = Counter(doc_id for row in rows for doc_id in row['relevant_ids'])
    if set(coverage) != {doc.id for doc in documents}:
        raise ValueError('Исследовательские запросы должны покрывать весь корпус')
    checkpoint = [json.loads(line) for line in (HERE / 'questions.jsonl').read_text().splitlines()]
    checkpoint = [row for row in checkpoint if row['kind'] == 'answer']
    report = {'corpus_sha256': hashlib.sha256(CORPUS.read_bytes()).hexdigest(),
              'queries_sha256': hashlib.sha256(args.queries.read_bytes()).hexdigest(),
              'checkpoint_sha256': hashlib.sha256((HERE / 'questions.jsonl').read_bytes()).hexdigest(),
              'implementation_sha256': {name: hashlib.sha256((HERE.parents[1] / 'server' / name).read_bytes()).hexdigest()
                                        for name in ('retrieval.py', 'preprocessing.py')},
              'k1': 1.2, 'b': 0.75, 'k': 5, 'mrr_depth': 'all matching documents',
              'documents': len(documents), 'query_count': len(rows), 'coverage': dict(sorted(coverage.items())),
              'versions': {'python': sys.version.split()[0]}, 'variants': {}}
    for package in ('pymorphy3', 'pymorphy3-dicts-ru', 'dawg2-python', 'setuptools'):
        try:
            report['versions'][package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            pass
    for mode in args.modes:
        index = BM25(documents, preprocessing=mode)
        report['variants'][mode] = {'research': evaluate(index, rows), 'checkpoint': evaluate(index, checkpoint),
                                    'vocabulary_size': len(index.index)}
        r = report['variants'][mode]
        print(f"{mode:16} research {r['research']['recall@5']:.6f} {r['research']['mrr']:.6f} "
              f"checkpoint {r['checkpoint']['recall@5']:.6f} {r['checkpoint']['mrr']:.6f}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()

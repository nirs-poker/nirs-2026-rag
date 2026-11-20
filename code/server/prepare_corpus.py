"""Выгрузить корпус КТ2 из Word-файлов ветки и перенести разметку из спецификации."""

import json
import re
import subprocess
from pathlib import Path

from retrieval import CORPUS

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SPEC = ROOT / "docs/Tech/06-rag-checkpoint.md"
QUESTIONS = ROOT / "code/tests/benchmark/questions.jsonl"


def table_rows(prefix):
    pattern = rf"^\| ({prefix}\d{{2}}) \| (.+) \|$"
    for line in SPEC.read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(pattern, line)
        if match:
            yield (match[1], *match[2].split(" | "))


def read_sources():
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
         str(HERE / "export_theory_text.ps1"), str(ROOT / "data/theory")],
        capture_output=True, encoding="utf-8",
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "Не удалось выгрузить текст из Word.")
    return json.loads(result.stdout)


def read_sections(paragraphs):
    sections = {}
    current = None
    for row in paragraphs:
        if row["heading"]:
            current = row["text"]
            if current in sections:
                raise ValueError(f"Повторяющийся заголовок: {current}")
            sections[current] = []
        elif current:
            sections[current].append(row["text"])
    return sections


def save_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
                    encoding="utf-8", newline="\n")


def main():
    sources = {name: read_sections(paragraphs) for name, paragraphs in read_sources().items()}
    documents = []
    for doc_id, filename, title in table_rows("D"):
        file = filename.strip("`")
        sections = sources[file]
        paragraphs = sections.get(title)
        if not paragraphs or not sections.get("Источники"):
            raise ValueError(f"{doc_id}: нет текста раздела или сведений об источниках ({file}, {title}).")
        documents.append({"id": doc_id, "title": title, "text": "\n\n".join(paragraphs),
                          "source_file": f"data/theory/{file}", "source_notes": sections["Источники"]})
    ids = {doc["id"] for doc in documents}
    if len(documents) != 30 or ids != {f"D{i:02}" for i in range(1, 31)}:
        raise ValueError("В спецификации ожидаются ровно D01–D30.")
    questions = []
    for question_id, text, expected, relevant in table_rows("Q"):
        relevant_ids = re.findall(r"\bD\d{2}\b", relevant)
        kind = "trap" if relevant == "—" else "answer"
        if (kind == "answer" and len(set(relevant_ids)) < 3) or not set(relevant_ids) <= ids:
            raise ValueError(f"{question_id}: неверная разметка релевантности.")
        questions.append({"id": question_id, "kind": kind, "question": text,
                          "expected": expected, "relevant_ids": relevant_ids})
    if (len(questions) != 15 or {row["id"] for row in questions} != {f"Q{i:02}" for i in range(1, 16)}
            or sum(row["kind"] == "answer" for row in questions) != 10):
        raise ValueError("В спецификации ожидаются ровно Q01–Q15, включая пять ловушек.")
    save_jsonl(CORPUS, documents)
    save_jsonl(QUESTIONS, questions)
    print(f"Exported {len(documents)} documents and {len(questions)} questions.")


if __name__ == "__main__":
    main()

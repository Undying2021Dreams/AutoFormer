"""
Build data/corpus/{sections,exercises}.jsonl from the OpenStax algebra books.

    bash scripts/fetch_openstax.sh
    python scripts/build_corpus.py
"""

from collections import Counter
from dataclasses import asdict
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from autoformer.corpus import parse_book  # noqa: E402

BUNDLE = ROOT / "data" / "raw" / "openstax-algebra"
OUT = ROOT / "data" / "corpus"
BOOKS = [
    "prealgebra-2e.collection.xml",
    "elementary-algebra-2e.collection.xml",
    "intermediate-algebra-2e.collection.xml",
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    n_sections = 0
    kinds: Counter = Counter()
    answered: Counter = Counter()

    with open(OUT / "sections.jsonl", "w") as fs, open(OUT / "exercises.jsonl", "w") as fe:
        for collection in BOOKS:
            sections = parse_book(BUNDLE, collection)
            for section in sections:
                exercises = section.exercises
                record = asdict(section)
                record.pop("exercises")
                fs.write(json.dumps(record, ensure_ascii=False) + "\n")
                n_sections += 1
                for ex in exercises:
                    fe.write(json.dumps(asdict(ex), ensure_ascii=False) + "\n")
                    kinds[ex.kind] += 1
                    answered[ex.kind] += ex.solution is not None
            print(f"{sections[0].book:28} {len(sections):4} sections, "
                  f"{sum(len(s.exercises) for s in sections):5} exercises")

    print(f"\n{n_sections} sections, {sum(kinds.values())} exercises\n")
    print(f"{'kind':12} {'count':>6} {'with answer':>12}")
    for kind, n in kinds.most_common():
        print(f"{kind:12} {n:6} {answered[kind]:12}")


if __name__ == "__main__":
    main()

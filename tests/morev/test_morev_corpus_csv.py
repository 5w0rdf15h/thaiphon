import csv
from pathlib import Path

import pytest


def _load_morev_corpus() -> list[tuple[str, str]]:
    corpus_path = Path(__file__).resolve().parents[1] / "corpus" / "morev.csv"
    if not corpus_path.exists() or corpus_path.stat().st_size == 0:
        return []

    rows: list[tuple[str, str]] = []
    with corpus_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        for lineno, row in enumerate(reader, 1):
            if not row:
                continue
            # allow comments / blank-ish lines
            if len(row) == 1:
                cell = row[0].strip()
                if not cell or cell.startswith("#"):
                    continue
                raise ValueError(
                    f"{corpus_path}:{lineno}: expected 2 columns (thai, expected), got 1"
                )
            if len(row) != 2:
                raise ValueError(
                    f"{corpus_path}:{lineno}: expected 2 columns (thai, expected), got {len(row)}"
                )

            thai = row[0].strip()
            expected = row[1].strip()
            if not thai or thai.startswith("#"):
                continue
            if not expected:
                raise ValueError(
                    f"{corpus_path}:{lineno}: empty expected transliteration for thai={thai!r}"
                )

            rows.append((thai, expected))

    return rows


_CASES = _load_morev_corpus()


@pytest.mark.skipif(
    not _CASES,
    reason="tests/corpus/morev.csv is empty or missing (provide local corpus to enable)",
)
@pytest.mark.parametrize(
    "thai, expected",
    _CASES,
    ids=[t for t, _ in _CASES],
)
def test_morev_corpus_csv(thai: str, expected: str, morev_transcribe, nfd):
    out = morev_transcribe(thai)
    assert nfd(out) == nfd(expected)

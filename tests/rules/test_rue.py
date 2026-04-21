"""ฤ / ฤๅ four-way readings.

The Sanskrit vowel letter ฤ has four contextual readings in Thai:
  - "rii" (long /riː/) — season words and most common scholarly uses.
  - "ri" (short /ri/) — most Indic-derived vocabulary.
  - "rer" (short /rɤ/) — ฤกษ์ and a handful of others.
  - "rue" (long /rɯː/) — ฤๅ ligature forms.
"""

from __future__ import annotations

import pytest

from thaiphon.lexicons.rue import RUE_READINGS, lookup


@pytest.mark.parametrize(
    "word,reading",
    [
        ("ฤดู", "rii"),
        ("ฤดี", "rii"),
        ("พฤษภาคม", "rii"),
        ("ฤทธิ์", "ri"),
        ("อังกฤษ", "ri"),
        ("ทฤษฎี", "ri"),
        ("ฤกษ์", "rer"),
        ("ฤๅษี", "rue"),
        ("ฤๅทัย", "rue"),
    ],
)
def test_rue_readings(word: str, reading: str) -> None:
    assert lookup(word) == reading


def test_absent_returns_none() -> None:
    assert lookup("มา") is None


def test_all_four_buckets_present() -> None:
    values = set(RUE_READINGS.values())
    assert {"rii", "ri", "rer", "rue"}.issubset(values)

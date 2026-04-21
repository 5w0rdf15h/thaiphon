"""The 4-word closed อย-leading set.

These four words are spelled with อ as a silent leading consonant, giving the
onset /j/ rather than /ʔ/. The set is closed: no other words follow this pattern.
"""

from __future__ import annotations

import pytest

from thaiphon.lexicons.o_leading import O_LEADING_WORDS, contains


@pytest.mark.parametrize(
    "word",
    [
        "อย่า",
        "อยู่",
        "อย่าง",
        "อยาก",
    ],
)
def test_o_leading_contains(word: str) -> None:
    assert contains(word)
    assert word in O_LEADING_WORDS


def test_set_size_exactly_four() -> None:
    assert len(O_LEADING_WORDS) == 4


def test_other_ay_words_not_in_set() -> None:
    assert "ยา" not in O_LEADING_WORDS
    assert "ไป" not in O_LEADING_WORDS

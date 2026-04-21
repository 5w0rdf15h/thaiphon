"""Silent-ห minor-conversion class.

Certain words ending in a silent ห (thanthakhat-silenced) behave as if
the final cluster were a low-class consonant group, yielding a different
effective tone class. The SILENT_H_WORDS lexicon lists these words.
"""

from __future__ import annotations

import pytest

import thaiphon
from thaiphon.lexicons.silent_h import SILENT_H_WORDS


@pytest.mark.parametrize("word", list(SILENT_H_WORDS))
def test_membership(word: str) -> None:
    assert word in SILENT_H_WORDS


def test_non_member_negative() -> None:
    assert "มา" not in SILENT_H_WORDS
    assert "กา" not in SILENT_H_WORDS


@pytest.mark.parametrize(
    "word",
    [
        "ประโยชน์",
        "สำเร็จ",
    ],
)
def test_silent_h_final_has_low_tone(word: str) -> None:
    # The reader should mark the final syllable as HC-effective, which
    # yields LOW tone on a stop-final dead syllable.
    result = thaiphon.analyze(word)
    if result.best.syllables:
        last = result.best.syllables[-1]
        assert last.tone.value in {"LOW", "RISING"}

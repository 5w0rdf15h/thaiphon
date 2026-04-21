"""Regression tests for the ไ/ใ vowel frames (Sara Ai Maimalai / Sara Ai Maimuan).

Both frames render as /aj/ SHORT with a /j/ offglide. Cases covered:
    * Bare frame (ไก่, ไป, ใน, ใช้) reads with the expected nucleus and coda.
    * Lexical exception ไทย keeps the surface /aj/ reading even though it
      has an orthographic tail.
    * Killer-mark tails (ไมล์) collapse to the same /aj/ reading.
"""

from __future__ import annotations

import pytest

from thaiphon.model.enums import VowelLength
from thaiphon.pipeline.runner import _derive_syllable


@pytest.mark.parametrize(
    "word",
    [
        "ไก่",
        "ไป",
        "ใน",
        "ใช้",
        "ไทย",
        "ไมล์",
    ],
)
def test_ai_ui_aj_nucleus(word: str) -> None:
    s = _derive_syllable(word)
    assert s.vowel.symbol == "a", f"{word!r}: got {s.vowel.symbol}"
    assert s.vowel_length is VowelLength.SHORT
    assert s.coda is not None and s.coda.symbol == "j"

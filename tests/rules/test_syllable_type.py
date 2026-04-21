"""Syllable-type classification tests.

Thai syllables are classified as LIVE or DEAD based on the coda type and
vowel length:
  - Sonorant or glide coda → LIVE (regardless of length).
  - Stop coda → DEAD (regardless of length).
  - No coda + long vowel → LIVE.
  - No coda + short vowel → DEAD.
"""

from __future__ import annotations

import pytest

from thaiphon.derivation.coda import FinalAnalysis, resolve_coda
from thaiphon.derivation.syllable_type import classify
from thaiphon.model.enums import SyllableType, VowelLength


@pytest.mark.parametrize(
    "final_letter,vlen,expected",
    [
        # Sonorant codas → always LIVE.
        ("ม", VowelLength.SHORT, SyllableType.LIVE),
        ("น", VowelLength.LONG, SyllableType.LIVE),
        ("ง", VowelLength.SHORT, SyllableType.LIVE),
        # Semi-vowel finals → LIVE.
        ("ว", VowelLength.LONG, SyllableType.LIVE),
        ("ย", VowelLength.SHORT, SyllableType.LIVE),
        # Stop codas → DEAD regardless of length.
        ("ก", VowelLength.LONG, SyllableType.DEAD),
        ("ก", VowelLength.SHORT, SyllableType.DEAD),
        ("ด", VowelLength.LONG, SyllableType.DEAD),
        ("บ", VowelLength.SHORT, SyllableType.DEAD),
    ],
)
def test_with_coda(
    final_letter: str, vlen: VowelLength, expected: SyllableType
) -> None:
    coda = resolve_coda(final_letter)
    assert classify(vlen, coda) is expected


def test_open_long_is_live() -> None:
    assert classify(VowelLength.LONG, FinalAnalysis(None, None)) is SyllableType.LIVE


def test_open_short_is_dead() -> None:
    assert classify(VowelLength.SHORT, FinalAnalysis(None, None)) is SyllableType.DEAD

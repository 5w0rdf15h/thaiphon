"""Closed CVC monosyllables must close even when the onset bears a tone mark.

A Thai word of the shape ``C1-toneMark-C2`` (no written vowel) is a single
closed monosyllable whose inherent vowel is /o/ and whose tone derives
from the onset's consonant class plus the tone mark. Examples:

* ก้ง → /kôŋ/    (mid-class onset + mai tho on a live syllable → falling)
* ก่ง → /kòŋ/    (mid-class + mai ek → low)
* ก๊ง → /kóŋ/    (mid-class + mai tri → high)
* ก๋ง → /kǒŋ/    (mid-class + mai chattawa → rising)

These must parse as ONE syllable, not two. Splitting at the tone mark
yields a spurious second syllable with an inserted /a/ and incorrect
tone — a regression that surfaces for any word matching this pattern.
"""

from __future__ import annotations

import pytest

from thaiphon.api import transcribe


@pytest.mark.parametrize(
    "word,tlc,ipa",
    [
        ("ก้ง", "gohng{F}", "/koŋ˥˩/"),
        ("ก่ง", "gohng{L}", "/koŋ˨˩/"),
        ("ก๊ง", "gohng{H}", "/koŋ˦˥/"),
        ("ก๋ง", "gohng{R}", "/koŋ˩˩˦/"),
    ],
)
def test_closed_cvc_with_tone_mark_on_onset_is_one_syllable(
    word: str, tlc: str, ipa: str
) -> None:
    assert transcribe(word, "tlc") == tlc
    assert transcribe(word, "ipa") == ipa


def test_unmarked_closed_cvc_baseline_unchanged() -> None:
    """Control: the same shape without a tone mark already worked and
    must continue to work (no regression in the un-marked closure path)."""
    assert transcribe("กง", "tlc") == "gohng{M}"
    assert transcribe("กง", "ipa") == "/koŋ˧/"


def test_cluster_onset_with_tone_mark_unchanged() -> None:
    """Three-token cluster onsets with a tone mark on the second consonant
    (e.g. กล้ง, คล้ม) were already handled by the cluster strategy and
    must remain unaffected."""
    assert transcribe("กล้ง", "tlc") == "glohng{F}"
    assert transcribe("คล้ม", "tlc") == "khlohm{H}"

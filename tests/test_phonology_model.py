"""Tests for the phonological model layer.

Covers: Phoneme, Cluster, Syllable, PhonologicalWord, and all enumerations.
These are pure data-model tests — no pipeline is invoked.
"""

from __future__ import annotations

import pytest

from thaiphon.model.enums import (
    ConsonantClass,
    EffectiveClass,
    SyllableType,
    Tone,
    ToneMark,
    VowelLength,
)
from thaiphon.model.phoneme import Cluster, Phoneme
from thaiphon.model.syllable import Syllable
from thaiphon.model.word import PhonologicalWord


# ---------------------------------------------------------------------------
# Phoneme
# ---------------------------------------------------------------------------


def test_phoneme_is_frozen() -> None:
    p = Phoneme("k")
    with pytest.raises((AttributeError, TypeError)):
        p.symbol = "g"  # type: ignore[misc]


def test_phoneme_equality() -> None:
    assert Phoneme("k") == Phoneme("k")
    assert Phoneme("k") != Phoneme("kʰ")


def test_phoneme_default_flags() -> None:
    p = Phoneme("k")
    assert p.is_aspirated is False
    assert p.is_sonorant is False


def test_phoneme_explicit_flags() -> None:
    p = Phoneme("kʰ", is_aspirated=True)
    assert p.is_aspirated is True


def test_phoneme_hashable() -> None:
    s = {Phoneme("k"), Phoneme("kʰ"), Phoneme("k")}
    assert len(s) == 2


# ---------------------------------------------------------------------------
# Cluster
# ---------------------------------------------------------------------------


def test_cluster_is_frozen() -> None:
    c = Cluster(Phoneme("k"), Phoneme("r"))
    with pytest.raises((AttributeError, TypeError)):
        c.first = Phoneme("g")  # type: ignore[misc]


def test_cluster_equality() -> None:
    c1 = Cluster(Phoneme("k"), Phoneme("r"))
    c2 = Cluster(Phoneme("k"), Phoneme("r"))
    assert c1 == c2


def test_cluster_parts_accessible() -> None:
    c = Cluster(Phoneme("pʰ"), Phoneme("r"))
    assert c.first.symbol == "pʰ"
    assert c.second.symbol == "r"


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("member", list(Tone))
def test_tone_members_are_strings(member: Tone) -> None:
    assert isinstance(member.value, str)


@pytest.mark.parametrize("member", list(VowelLength))
def test_vowel_length_members(member: VowelLength) -> None:
    assert member in (VowelLength.SHORT, VowelLength.LONG)


@pytest.mark.parametrize("member", list(ToneMark))
def test_tone_mark_members_are_strings(member: ToneMark) -> None:
    assert isinstance(member.value, str)


def test_tone_five_values() -> None:
    assert len(Tone) == 5


def test_syllable_type_two_values() -> None:
    assert len(SyllableType) == 2


def test_effective_class_three_values() -> None:
    assert len(EffectiveClass) == 3


def test_consonant_class_four_values() -> None:
    assert len(ConsonantClass) == 4


# ---------------------------------------------------------------------------
# Syllable
# ---------------------------------------------------------------------------


def _make_syllable(**kwargs) -> Syllable:
    defaults = dict(
        onset=Phoneme("k"),
        vowel=Phoneme("a"),
        vowel_length=VowelLength.LONG,
        coda=None,
        tone=Tone.MID,
    )
    defaults.update(kwargs)
    return Syllable(**defaults)


def test_syllable_is_frozen() -> None:
    syl = _make_syllable()
    with pytest.raises((AttributeError, TypeError)):
        syl.tone = Tone.LOW  # type: ignore[misc]


def test_syllable_fields_accessible() -> None:
    syl = _make_syllable(
        onset=Phoneme("k"),
        vowel=Phoneme("a"),
        vowel_length=VowelLength.LONG,
        coda=Phoneme("n", is_sonorant=True),
        tone=Tone.RISING,
    )
    assert syl.onset is not None
    assert syl.vowel.symbol == "a"
    assert syl.vowel_length is VowelLength.LONG
    assert syl.coda is not None
    assert syl.coda.symbol == "n"
    assert syl.tone is Tone.RISING


def test_syllable_defaults() -> None:
    syl = _make_syllable()
    assert syl.tone_mark is ToneMark.NONE
    assert syl.effective_class is EffectiveClass.MID
    assert syl.syllable_type is SyllableType.LIVE
    assert syl.raw == ""
    assert syl.inserted_vowel is False
    assert syl.cancelled is False


def test_syllable_equality() -> None:
    s1 = _make_syllable(tone=Tone.MID)
    s2 = _make_syllable(tone=Tone.MID)
    assert s1 == s2


def test_syllable_inequality_on_tone() -> None:
    s1 = _make_syllable(tone=Tone.MID)
    s2 = _make_syllable(tone=Tone.LOW)
    assert s1 != s2


def test_syllable_hashable() -> None:
    syl = _make_syllable()
    _ = {syl}


def test_syllable_with_cluster_onset() -> None:
    onset = Cluster(Phoneme("k"), Phoneme("r"))
    syl = _make_syllable(onset=onset)
    assert isinstance(syl.onset, Cluster)


def test_syllable_no_onset() -> None:
    syl = _make_syllable(onset=None)
    assert syl.onset is None


# ---------------------------------------------------------------------------
# PhonologicalWord
# ---------------------------------------------------------------------------


def _make_word(n_syllables: int = 1) -> PhonologicalWord:
    syls = tuple(_make_syllable() for _ in range(n_syllables))
    return PhonologicalWord(syllables=syls)


def test_phonological_word_is_frozen() -> None:
    word = _make_word()
    with pytest.raises((AttributeError, TypeError)):
        word.syllables = ()  # type: ignore[misc]


def test_phonological_word_len() -> None:
    assert len(_make_word(3)) == 3


def test_phonological_word_iteration() -> None:
    word = _make_word(2)
    syllables = list(word)
    assert len(syllables) == 2
    assert all(isinstance(s, Syllable) for s in syllables)


def test_phonological_word_indexing() -> None:
    word = _make_word(2)
    assert isinstance(word.syllables[0], Syllable)
    assert isinstance(word.syllables[1], Syllable)


def test_phonological_word_defaults() -> None:
    word = _make_word()
    assert word.confidence == 1.0
    assert word.source == "derivation"
    assert word.raw == ""
    assert word.morpheme_boundaries == ()


def test_phonological_word_zero_syllables() -> None:
    word = PhonologicalWord(syllables=())
    assert len(word) == 0


def test_phonological_word_equality() -> None:
    w1 = _make_word(1)
    w2 = _make_word(1)
    assert w1 == w2

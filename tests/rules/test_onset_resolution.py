"""Onset resolution tests.

Covers single-consonant onsets, leading-ห elevation (low-class consonant
raised to HIGH effective class), true consonant clusters, the four-word
silent-อ set, and fallback to implicit glottal stop.
"""

from __future__ import annotations

import pytest

from thaiphon.derivation.onset import resolve_onset
from thaiphon.model.enums import EffectiveClass
from thaiphon.model.phoneme import Cluster, Phoneme


# Single consonants.
@pytest.mark.parametrize(
    "text,ipa,eff",
    [
        ("ก", "k", EffectiveClass.MID),
        ("จ", "tɕ", EffectiveClass.MID),
        ("ด", "d", EffectiveClass.MID),
        ("ต", "t", EffectiveClass.MID),
        ("บ", "b", EffectiveClass.MID),
        ("ป", "p", EffectiveClass.MID),
        ("ข", "kʰ", EffectiveClass.HIGH),
        ("ฉ", "tɕʰ", EffectiveClass.HIGH),
        ("ส", "s", EffectiveClass.HIGH),
        ("ห", "h", EffectiveClass.HIGH),
        ("ค", "kʰ", EffectiveClass.LOW),
        ("ช", "tɕʰ", EffectiveClass.LOW),
        ("ท", "tʰ", EffectiveClass.LOW),
        ("พ", "pʰ", EffectiveClass.LOW),
        ("ม", "m", EffectiveClass.LOW),
        ("น", "n", EffectiveClass.LOW),
        ("ง", "ŋ", EffectiveClass.LOW),
        ("ร", "r", EffectiveClass.LOW),
    ],
)
def test_single_consonant(text: str, ipa: str, eff: EffectiveClass) -> None:
    info = resolve_onset(text)
    assert isinstance(info.onset, Phoneme)
    assert info.onset.symbol == ipa
    assert info.effective_class is eff
    assert info.consumed == 1
    assert info.leading_silent is None


# Leading ห elevation: low-class consonant following ห becomes HIGH effective class.
@pytest.mark.parametrize(
    "chars,expected_ipa",
    [
        ("หม", "m"),
        ("หน", "n"),
        ("หง", "ŋ"),
        ("หญ", "j"),
        ("หย", "j"),
        ("หร", "r"),
        ("หล", "l"),
        ("หว", "w"),
    ],
)
def test_h_leading(chars: str, expected_ipa: str) -> None:
    info = resolve_onset(chars)
    assert isinstance(info.onset, Phoneme)
    assert info.onset.symbol == expected_ipa
    assert info.effective_class is EffectiveClass.HIGH
    assert info.consumed == 2
    assert info.leading_silent == "ห"


# True consonant clusters.
@pytest.mark.parametrize(
    "chars,first_ipa,second_ipa,eff",
    [
        ("กร", "k", "r", EffectiveClass.MID),
        ("กล", "k", "l", EffectiveClass.MID),
        ("กว", "k", "w", EffectiveClass.MID),
        ("ขร", "kʰ", "r", EffectiveClass.HIGH),
        ("ขล", "kʰ", "l", EffectiveClass.HIGH),
        ("คร", "kʰ", "r", EffectiveClass.LOW),
        ("คล", "kʰ", "l", EffectiveClass.LOW),
        ("ตร", "t", "r", EffectiveClass.MID),
        ("ปร", "p", "r", EffectiveClass.MID),
        ("ปล", "p", "l", EffectiveClass.MID),
        ("พร", "pʰ", "r", EffectiveClass.LOW),
        ("พล", "pʰ", "l", EffectiveClass.LOW),
    ],
)
def test_cluster(
    chars: str, first_ipa: str, second_ipa: str, eff: EffectiveClass
) -> None:
    info = resolve_onset(chars)
    assert isinstance(info.onset, Cluster)
    assert info.onset.first.symbol == first_ipa
    assert info.onset.second.symbol == second_ipa
    assert info.effective_class is eff
    assert info.consumed == 2


# The 4-word closed silent-อ set.
@pytest.mark.parametrize("word", ["อย่า", "อยู่", "อย่าง", "อยาก"])
def test_o_leading_match(word: str) -> None:
    info = resolve_onset(word)
    assert isinstance(info.onset, Phoneme)
    assert info.onset.symbol == "j"
    assert info.effective_class is EffectiveClass.MID
    assert info.consumed == 2
    assert info.leading_silent == "อ"


def test_o_leading_non_match_falls_through() -> None:
    # อย not in the 4-word set → treated as single อ onset, no silent-อ match.
    info = resolve_onset("อยี")
    assert isinstance(info.onset, Phoneme)
    assert info.onset.symbol == "ʔ"
    assert info.effective_class is EffectiveClass.MID
    assert info.consumed == 1


def test_empty_chars_implicit_glottal() -> None:
    info = resolve_onset("")
    assert isinstance(info.onset, Phoneme)
    assert info.onset.symbol == "ʔ"
    assert info.effective_class is EffectiveClass.MID
    assert info.consumed == 0


def test_vowel_initial_implicit_glottal() -> None:
    # Starts with a vowel-marker character.
    info = resolve_onset("ะ")
    assert isinstance(info.onset, Phoneme)
    assert info.onset.symbol == "ʔ"
    assert info.effective_class is EffectiveClass.MID
    assert info.consumed == 0


def test_non_cluster_two_consonants_takes_only_first() -> None:
    # กน is not a valid cluster; onset should just be ก.
    info = resolve_onset("กน")
    assert isinstance(info.onset, Phoneme)
    assert info.onset.symbol == "k"
    assert info.consumed == 1

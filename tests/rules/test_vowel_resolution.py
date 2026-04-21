"""Vowel resolution tests.

Covers explicit simple vowels, pre-base vowel frames, special composite vowels
(Sara Am, Sara Ai, เกา), centring diphthongs, closed-syllable shortening
transforms, and inherent-vowel insertion for bare consonants.
"""

from __future__ import annotations

import pytest

from thaiphon.derivation.vowel import VowelAnalysis, resolve_vowel
from thaiphon.model.enums import VowelLength


def _call(chars: str, onset: int = 1, has_final: bool = False) -> VowelAnalysis:
    return resolve_vowel(
        chars, onset_consumed=onset, has_final=has_final, tone_mark_present=False
    )


# Simple explicit vowels.
@pytest.mark.parametrize(
    "text,quality,length",
    [
        ("กะ", "a", VowelLength.SHORT),
        ("กา", "a", VowelLength.LONG),
        ("กิ", "i", VowelLength.SHORT),
        ("กี", "i", VowelLength.LONG),
        ("กึ", "ɯ", VowelLength.SHORT),
        ("กื", "ɯ", VowelLength.LONG),
        ("กุ", "u", VowelLength.SHORT),
        ("กู", "u", VowelLength.LONG),
    ],
)
def test_simple_vowels(text: str, quality: str, length: VowelLength) -> None:
    info = _call(text)
    assert info.quality == quality
    assert info.length is length


# Pre-base vowels. onset_consumed is absolute (pre-vowel + onset).
@pytest.mark.parametrize(
    "text,quality,length",
    [
        ("เก", "e", VowelLength.LONG),
        ("เกะ", "e", VowelLength.SHORT),
        ("แก", "ɛ", VowelLength.LONG),
        ("แกะ", "ɛ", VowelLength.SHORT),
        ("โก", "o", VowelLength.LONG),
        ("โกะ", "o", VowelLength.SHORT),
    ],
)
def test_pre_base_vowels(text: str, quality: str, length: VowelLength) -> None:
    info = resolve_vowel(
        text, onset_consumed=2, has_final=False, tone_mark_present=False
    )
    assert info.quality == quality
    assert info.length is length


# Special composite vowels. onset_consumed is absolute offset to vowel start.
@pytest.mark.parametrize(
    "text,onset,quality,length,offglide",
    [
        ("ไก", 2, "a", VowelLength.SHORT, "j"),
        ("ใก", 2, "a", VowelLength.SHORT, "j"),
        ("กำ", 1, "a", VowelLength.SHORT, "m"),
        ("เกา", 2, "a", VowelLength.SHORT, "w"),
    ],
)
def test_special_vowels(
    text: str, onset: int, quality: str, length: VowelLength, offglide: str
) -> None:
    info = resolve_vowel(
        text, onset_consumed=onset, has_final=False, tone_mark_present=False
    )
    assert info.quality == quality
    assert info.length is length
    assert info.offglide == offglide


# Centring diphthongs. onset_consumed is absolute.
@pytest.mark.parametrize(
    "text,quality,length,onset_consumed",
    [
        ("เกีย", "iə", VowelLength.LONG, 2),
        ("เกียะ", "iə", VowelLength.SHORT, 2),
        ("เกือ", "ɯə", VowelLength.LONG, 2),
        ("เกือะ", "ɯə", VowelLength.SHORT, 2),
        ("กัว", "uə", VowelLength.LONG, 1),
    ],
)
def test_centring_diphthongs(
    text: str, quality: str, length: VowelLength, onset_consumed: int
) -> None:
    info = resolve_vowel(
        text, onset_consumed=onset_consumed, has_final=False, tone_mark_present=False
    )
    assert info.quality == quality
    assert info.length is length


# Closed-syllable shortening: open-form vowels shorten when a coda is present.
@pytest.mark.parametrize(
    "text,quality,length,onset_consumed",
    [
        ("กัน", "a", VowelLength.SHORT, 1),
        ("เก็น", "e", VowelLength.SHORT, 2),
        ("แก็น", "ɛ", VowelLength.SHORT, 2),
        ("เกิน", "ɤ", VowelLength.SHORT, 2),
    ],
)
def test_closed_syllable_shortening(
    text: str, quality: str, length: VowelLength, onset_consumed: int
) -> None:
    info = resolve_vowel(
        text, onset_consumed=onset_consumed, has_final=True, tone_mark_present=False
    )
    assert info.quality == quality
    assert info.length is length


# Inherent-vowel insertion for bare consonants.
def test_inherent_open_bare_consonant() -> None:
    # 'ก' bare → short /a/ inserted.
    info = resolve_vowel(
        "ก", onset_consumed=1, has_final=False, tone_mark_present=False
    )
    assert info.quality == "a"
    assert info.length is VowelLength.SHORT
    assert info.inserted_vowel is True


def test_inherent_closed_short_o() -> None:
    # 'นก' → no written vowel, closed → short /o/.
    info = resolve_vowel(
        "นก", onset_consumed=1, has_final=True, tone_mark_present=False
    )
    assert info.quality == "o"
    assert info.length is VowelLength.SHORT
    assert info.inserted_vowel is True


# Long open.
def test_long_aa_open() -> None:
    info = _call("มา", onset=1)
    assert info.quality == "a"
    assert info.length is VowelLength.LONG


# เ◌ีย centring diphthong.
def test_eia_long() -> None:
    info = resolve_vowel(
        "เมีย", onset_consumed=2, has_final=False, tone_mark_present=False
    )
    assert info.quality == "iə"
    assert info.length is VowelLength.LONG


def test_eia_short_with_sara_a() -> None:
    info = resolve_vowel(
        "เมียะ", onset_consumed=2, has_final=False, tone_mark_present=False
    )
    assert info.quality == "iə"
    assert info.length is VowelLength.SHORT


def test_eoh_long() -> None:
    info = resolve_vowel(
        "เกอ", onset_consumed=2, has_final=False, tone_mark_present=False
    )
    assert info.quality == "ɤ"
    assert info.length is VowelLength.LONG


def test_eoh_short() -> None:
    info = resolve_vowel(
        "เกอะ", onset_consumed=2, has_final=False, tone_mark_present=False
    )
    assert info.quality == "ɤ"
    assert info.length is VowelLength.SHORT

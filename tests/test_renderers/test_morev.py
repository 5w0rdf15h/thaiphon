"""Tests for the Morev (Cyrillic) renderer.

Conventions verified:
- Aspirated stops use the IPA modifier letter small H (U+02B0) appended
  to the Cyrillic letter: /kʰ/ → кʰ, /tʰ/ → тʰ, /pʰ/ → пʰ, /tɕʰ/ → чʰ.
- /h/ → х (no collision with aspirated stops).
- /ŋ/ → ң (U+04A3).
- Long vowels carry a combining macron (U+0304); NFC collapses
  и + macron to ӣ, etc.
- Tone diacritics: LOW ̀ (U+0300), FALLING ̂ (U+0302),
  HIGH ́ (U+0301), RISING ̌ (U+030C); MID is unmarked.
- Syllable separator is '-'.
"""

from __future__ import annotations

import unicodedata

import pytest

import thaiphon

_MACRON = "̄"
_TONE_LOW = "̀"
_TONE_FALLING = "̂"
_TONE_HIGH = "́"
_TONE_RISING = "̌"
_NG = "ң"    # ң


# ---------------------------------------------------------------------------
# Scheme registration
# ---------------------------------------------------------------------------


def test_morev_registered() -> None:
    assert "morev" in thaiphon.list_schemes()


# ---------------------------------------------------------------------------
# Helper — compare NFC-normalised forms
# ---------------------------------------------------------------------------


def _nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


# ---------------------------------------------------------------------------
# Onset consonants
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai, onset_cyrillic",
    [
        ("กา", "к"),     # /k/ → к
        ("ขา", "кʰ"),    # /kʰ/ → кʰ
        ("ตา", "т"),     # /t/ → т
        ("ถา", "тʰ"),    # /tʰ/ → тʰ
        ("ปา", "п"),     # /p/ → п
        ("ผา", "пʰ"),    # /pʰ/ → пʰ
        ("หา", "х"),     # /h/ → х (not aspirated stop)
        ("งา", _NG),     # /ŋ/ → ң
        ("มา", "м"),     # /m/ → м
        ("นา", "н"),     # /n/ → н
        ("ลา", "л"),     # /l/ → л
        ("วา", "в"),     # /w/ → в
        ("ยา", "й"),     # /j/ → й
        ("รา", "р"),     # /r/ → р
        ("ซา", "с"),     # /s/ → с
        ("บา", "б"),     # /b/ → б
        ("ดา", "д"),     # /d/ → д
        ("ฟา", "ф"),     # /f/ → ф
    ],
)
def test_morev_onset_consonants(thai: str, onset_cyrillic: str) -> None:
    result = _nfc(thaiphon.transcribe(thai, scheme="morev"))
    assert result.startswith(onset_cyrillic)


# ---------------------------------------------------------------------------
# Tones: all five on mid-class long /aː/ → а̄
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai, expected_has_diacritic",
    [
        # MID — no diacritic.
        ("กา", False),
        # LOW — grave ̀.
        ("ก่า", True),
        # FALLING — circumflex ̂.
        ("ก้า", True),
        # HIGH — acute ́.
        ("ก๊า", True),
        # RISING — caron ̌.
        ("ก๋า", True),
    ],
)
def test_morev_tone_diacritics_present(thai: str, expected_has_diacritic: bool) -> None:
    result = thaiphon.transcribe(thai, scheme="morev")
    has_combining = any(unicodedata.combining(ch) > 0 for ch in result)
    # Macron on long vowel also counts as combining; check for tone-specific
    # diacritics specifically.
    tone_diacritics = (_TONE_LOW, _TONE_FALLING, _TONE_HIGH, _TONE_RISING)
    has_tone = any(d in result for d in tone_diacritics)
    assert has_tone == expected_has_diacritic


# ---------------------------------------------------------------------------
# Long vowels carry macron
# ---------------------------------------------------------------------------


def test_morev_long_vowel_has_macron() -> None:
    result = thaiphon.transcribe("กา", scheme="morev")
    # NFC may precompose; verify either raw macron or precomposed form present.
    assert _MACRON in result or any(
        unicodedata.name(ch, "").endswith("WITH MACRON") for ch in result
    )


def test_morev_short_vowel_no_macron() -> None:
    # จะ — dead short syllable, no length mark.
    result = thaiphon.transcribe("จะ", scheme="morev")
    assert _MACRON not in result


# ---------------------------------------------------------------------------
# Specific spot-checks
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai, expected_nfc",
    [
        # กา — MID: кā (NFC precomposes а+macron).
        ("กา", _nfc("ка̄")),
        # ก่า — LOW: кā + grave → кā̀
        ("ก่า", _nfc("ка̄̀")),
        # ก้า — FALLING: кā + circumflex
        ("ก้า", _nfc("ка̄̂")),
        # ก๊า — HIGH: кā + acute
        ("ก๊า", _nfc("ка̄́")),
        # ก๋า — RISING: кā + caron
        ("ก๋า", _nfc("ка̄̌")),
        # ขา — HC: aspirated /kʰ/, RISING.
        ("ขา", _nfc("кʰа̄̌")),
        # หา — /h/ → х, RISING.
        ("หา", _nfc("ха̄̌")),
        # น้ำ — HIGH tone (LC + mai tho + lexicon → FALLING becomes HIGH).
        ("น้ำ", _nfc("на̄́м")),
    ],
)
def test_morev_spot_checks(thai: str, expected_nfc: str) -> None:
    result = _nfc(thaiphon.transcribe(thai, scheme="morev"))
    assert result == expected_nfc


# ---------------------------------------------------------------------------
# /ŋ/ as ң in onset and coda
# ---------------------------------------------------------------------------


def test_morev_ng_coda() -> None:
    result = thaiphon.transcribe("กาง", scheme="morev")
    assert _NG in result


def test_morev_ng_onset() -> None:
    result = thaiphon.transcribe("งาน", scheme="morev")
    assert result.startswith(_NG)


# ---------------------------------------------------------------------------
# Two-syllable word has dash separator
# ---------------------------------------------------------------------------


def test_morev_two_syllable_has_dash() -> None:
    result = thaiphon.transcribe("สวัสดี", scheme="morev")
    assert "-" in result

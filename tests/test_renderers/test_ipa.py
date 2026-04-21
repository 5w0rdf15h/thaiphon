"""Tests for the IPA renderer.

Conventions verified:
- Output wrapped in /…/ phonemic slashes.
- Chao tone letters: ˧ MID, ˨˩ LOW, ˥˩ FALLING, ˦˥ HIGH, ˩˩˦ RISING.
- Syllable separator is '.'.
- Long vowels use IPA length mark 'ː'.
- Stop codas are unreleased: p̚ t̚ k̚.
- Nasal codas: m n ŋ.
- Glide codas: w j.
"""

from __future__ import annotations

import pytest

import thaiphon


# Chao tone-letter constants.
_MID = "˧"
_LOW = "˨˩"
_FALLING = "˥˩"
_HIGH = "˦˥"
_RISING = "˩˩˦"


# ---------------------------------------------------------------------------
# Scheme registration
# ---------------------------------------------------------------------------


def test_ipa_registered() -> None:
    assert "ipa" in thaiphon.list_schemes()


# ---------------------------------------------------------------------------
# /…/ slashes wrapping
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai",
    ["กา", "ขา", "มา", "น้ำ", "ดี", "กาน"],
)
def test_ipa_wrapped_in_slashes(thai: str) -> None:
    result = thaiphon.transcribe(thai, scheme="ipa")
    assert result.startswith("/") and result.endswith("/")


# ---------------------------------------------------------------------------
# Tone: all five tones on mid-class long /aː/
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai, expected_tone",
    [
        ("กา", _MID),       # MC, no mark → MID.
        ("ก่า", _LOW),      # MC + mai ek → LOW.
        ("ก้า", _FALLING),  # MC + mai tho → FALLING.
        ("ก๊า", _HIGH),     # MC + mai tri → HIGH.
        ("ก๋า", _RISING),   # MC + mai jattawa → RISING.
    ],
)
def test_ipa_tones_mid_class(thai: str, expected_tone: str) -> None:
    result = thaiphon.transcribe(thai, scheme="ipa")
    assert expected_tone in result


# ---------------------------------------------------------------------------
# High-class onset tone (RISING on live syllable, no mark)
# ---------------------------------------------------------------------------


def test_ipa_high_class_rising() -> None:
    result = thaiphon.transcribe("ขา", scheme="ipa")
    assert _RISING in result


# ---------------------------------------------------------------------------
# Long-vowel IPA length mark
# ---------------------------------------------------------------------------


def test_ipa_long_vowel_has_length_mark() -> None:
    result = thaiphon.transcribe("กา", scheme="ipa")
    assert "ː" in result


def test_ipa_short_vowel_no_length_mark() -> None:
    # จะ — MC dead short, no length mark.
    result = thaiphon.transcribe("จะ", scheme="ipa")
    assert "ː" not in result


# ---------------------------------------------------------------------------
# Specific IPA spot-checks
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai, expected",
    [
        # กา — mid /kaː˧/
        ("กา", "/kaː˧/"),
        # ขา — high /kʰaː˩˩˦/
        ("ขา", "/kʰaː˩˩˦/"),
        # มา — low sonorant /maː˧/
        ("มา", "/maː˧/"),
        # น้ำ — HIGH tone (low-class + mai tho → HIGH), lexicon long vowel.
        ("น้ำ", "/naːm˦˥/"),
        # ดี — mid /diː˧/
        ("ดี", "/diː˧/"),
    ],
)
def test_ipa_spot_checks(thai: str, expected: str) -> None:
    assert thaiphon.transcribe(thai, scheme="ipa") == expected


# ---------------------------------------------------------------------------
# Stop codas unreleased (p̚ t̚ k̚)
# ---------------------------------------------------------------------------


def test_ipa_stop_coda_p_unreleased() -> None:
    result = thaiphon.transcribe("กาบ", scheme="ipa")
    # p̚ is p + U+031A
    assert "p̚" in result


def test_ipa_stop_coda_t_unreleased() -> None:
    result = thaiphon.transcribe("กาด", scheme="ipa")
    assert "t̚" in result


def test_ipa_stop_coda_k_unreleased() -> None:
    result = thaiphon.transcribe("กาก", scheme="ipa")
    assert "k̚" in result


# ---------------------------------------------------------------------------
# Nasal codas
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai, coda_ipa",
    [
        ("งาน", "n"),
        ("กาม", "m"),
        ("กาง", "ŋ"),
    ],
)
def test_ipa_nasal_coda(thai: str, coda_ipa: str) -> None:
    result = thaiphon.transcribe(thai, scheme="ipa")
    assert coda_ipa in result


# ---------------------------------------------------------------------------
# Glide codas
# ---------------------------------------------------------------------------


def test_ipa_glide_coda_j() -> None:
    # ไป — /j/ offglide → IPA 'j' in coda.
    result = thaiphon.transcribe("ไป", scheme="ipa")
    assert "j" in result


def test_ipa_glide_coda_w() -> None:
    # แมว — /w/ offglide.
    result = thaiphon.transcribe("แมว", scheme="ipa")
    assert "w" in result


# ---------------------------------------------------------------------------
# Syllable separator '.'
# ---------------------------------------------------------------------------


def test_ipa_two_syllable_has_dot_separator() -> None:
    # สวัสดี is at least two syllables.
    result = thaiphon.transcribe("สวัสดี", scheme="ipa")
    inner = result.strip("/")
    assert "." in inner


def test_ipa_single_syllable_no_dot_separator() -> None:
    result = thaiphon.transcribe("กา", scheme="ipa")
    inner = result.strip("/")
    assert "." not in inner

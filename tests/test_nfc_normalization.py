"""Tests for the Unicode normalization layer.

Covers the public `thaiphon.normalization.unicode_norm.normalize` function:
- NFC composition of decomposed forms.
- Thai mark canonical ordering (vowel mark before tone mark).
- Variation selector stripping (U+FE00–U+FE0F).
- Error on leading combining mark without a base.
- Idempotence (normalizing twice equals normalizing once).
- Pass-through for ASCII, Thai numerals, mixed strings.
"""

from __future__ import annotations

import unicodedata

import pytest

from thaiphon.errors import NormalizationError
from thaiphon.normalization.unicode_norm import normalize


# Convenience code-point constants for common Thai characters used in tests.
_KO = "ก"          # ก
_KHO = "ข"         # ข
_DO = "ด"          # ด
_MO = "ม"          # ม
_NO = "น"          # น

_SARA_I = "ิ"      # ◌ิ
_SARA_U = "ุ"      # ◌ุ
_SARA_II = "ี"     # ◌ี
_MAI_EK = "่"      # ◌่
_MAI_THO = "้"     # ◌้
_SARA_AM = "ำ"     # ◌ำ
_THANTHAKHAT = "์" # ◌์


# ---------------------------------------------------------------------------
# Empty / trivial input
# ---------------------------------------------------------------------------


def test_empty_string() -> None:
    assert normalize("") == ""


def test_ascii_passthrough() -> None:
    assert normalize("hello world") == "hello world"


def test_numerals_passthrough() -> None:
    # Thai numerals ๑๒๓ are in the Thai block but not base consonants.
    assert normalize("๑๒๓") == "๑๒๓"


# ---------------------------------------------------------------------------
# NFC composition
# ---------------------------------------------------------------------------


def test_nfc_composes_latin_decomposed_form() -> None:
    # é decomposed → NFC should yield precomposed form U+00E9.
    decomposed = unicodedata.normalize("NFD", "é")
    assert normalize(decomposed) == "é"


def test_nfc_on_thai_sara_am_stable() -> None:
    # ◌ำ is atomic in NFC; after normalize the string must be NFC-stable.
    text = _KO + _SARA_AM
    result = normalize(text)
    assert result == unicodedata.normalize("NFC", result)


# ---------------------------------------------------------------------------
# Thai mark canonical ordering: vowel mark before tone mark
# ---------------------------------------------------------------------------


def test_mark_reorder_tone_before_vowel_mark() -> None:
    # Input: base + tone + vowel → expect base + vowel + tone.
    bad = _KO + _MAI_EK + _SARA_I
    good = _KO + _SARA_I + _MAI_EK
    assert normalize(bad) == good


def test_mark_reorder_already_canonical_is_unchanged() -> None:
    good = _KO + _SARA_I + _MAI_EK
    assert normalize(good) == good


def test_mark_reorder_mai_tho_after_sara_i() -> None:
    bad = _KO + _MAI_THO + _SARA_I
    good = _KO + _SARA_I + _MAI_THO
    assert normalize(bad) == good


# ---------------------------------------------------------------------------
# Variation selector stripping
# ---------------------------------------------------------------------------


def test_variation_selector_fe0e_stripped() -> None:
    vs = "︎"
    assert normalize(_KO + vs + _KHO) == _KO + _KHO


def test_variation_selector_fe0f_stripped() -> None:
    vs = "️"
    assert normalize(_KO + vs) == _KO


def test_variation_selector_range_stripped() -> None:
    # All selectors in U+FE00..U+FE0F should be stripped.
    for cp in range(0xFE00, 0xFE10):
        vs = chr(cp)
        assert normalize(_KO + vs) == _KO


# ---------------------------------------------------------------------------
# Error: leading combining mark without base
# ---------------------------------------------------------------------------


def test_leading_tone_mark_raises() -> None:
    with pytest.raises(NormalizationError):
        normalize(_MAI_EK + _KO)


def test_leading_sara_i_raises() -> None:
    with pytest.raises(NormalizationError):
        normalize(_SARA_I + _KO)


# ---------------------------------------------------------------------------
# Idempotence
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        "",
        "abc",
        "hello world",
        _KO + _SARA_I + _MAI_EK,
        "สวัสดี",   # สวัสดี
        "ไทย",                       # ไทย
        "ผลไม้",           # ผลไม้
        _KO + _SARA_AM,
        "๑๒๓",
        "mix " + _KO + _SARA_I + " 123",
    ],
)
def test_idempotent(text: str) -> None:
    once = normalize(text)
    assert normalize(once) == once


# ---------------------------------------------------------------------------
# Mixed Thai + English passthrough
# ---------------------------------------------------------------------------


def test_mixed_thai_english() -> None:
    text = "hello " + _KO + _SARA_I + _MAI_EK + " world"
    assert normalize(text) == text


# ---------------------------------------------------------------------------
# API layer normalizes NFD input
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai",
    [
        "กา",
        "น้ำ",
        "สวัสดี",
        "ผลไม้",
        "ไทย",
    ],
)
def test_api_nfc_nfd_parity(thai: str) -> None:
    """NFD input through the public API must produce the same output as NFC."""
    import thaiphon

    nfd = unicodedata.normalize("NFD", thai)
    nfc = unicodedata.normalize("NFC", thai)
    assert thaiphon.transcribe(nfc, scheme="tlc") == thaiphon.transcribe(
        nfd, scheme="tlc"
    )

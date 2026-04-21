"""Unicode NFC normalisation, Thai mark canonical ordering, and variation selector stripping."""

from __future__ import annotations

import unicodedata

import pytest

from thaiphon.errors import NormalizationError
from thaiphon.normalization.unicode_norm import normalize


SARA_AM = "ำ"
NIKHAHIT = "ํ"
SARA_AA = "า"

MAI_EK = "่"
MAI_THO = "้"
SARA_I = "ิ"
SARA_U = "ุ"

KO = "ก"
KHO = "ข"
DO = "ด"
MO = "ม"
NO = "น"
YO = "ย"


def test_empty_string() -> None:
    assert normalize("") == ""


def test_ascii_passthrough() -> None:
    assert normalize("hello world") == "hello world"


def test_nfc_composes_decomposed() -> None:
    # Construct a decomposed form that NFC will recompose.
    decomposed = unicodedata.normalize("NFD", "é")
    assert normalize(decomposed) == "é"


def test_nfc_on_thai_sara_am() -> None:
    # ◌ำ (U+0E33) is atomic; round trip to NFC must be stable.
    text = KO + SARA_AM
    result = normalize(text)
    assert result == unicodedata.normalize("NFC", result)


def test_mark_reorder_tone_before_vowel_above() -> None:
    # Input: base + tone + vowel-above → expect base + vowel-above + tone.
    bad = KO + MAI_EK + SARA_I
    good = KO + SARA_I + MAI_EK
    assert normalize(bad) == good


def test_mark_reorder_already_canonical_is_idempotent() -> None:
    good = KO + SARA_I + MAI_EK
    assert normalize(good) == good


def test_variation_selector_removed() -> None:
    vs15 = "︎"
    vs16 = "️"
    text = KO + vs15 + KHO + vs16
    assert normalize(text) == KO + KHO


def test_idempotence_simple_thai() -> None:
    for w in ["สวัสดี", "ไทย", "ผลไม้"]:
        once = normalize(w)
        assert normalize(once) == once


def test_mixed_thai_english() -> None:
    text = "hello " + KO + SARA_I + MAI_EK + " world"
    assert normalize(text) == text


def test_numerals_passthrough() -> None:
    assert normalize("๑๒๓") == "๑๒๓"


def test_leading_combining_mark_raises() -> None:
    with pytest.raises(NormalizationError):
        normalize(MAI_EK + KO)


@pytest.mark.parametrize(
    "text",
    [
        "",
        "abc",
        "กา",
        "สวัสดี",
        "ไทย",
        "hello world",
        "ก่อน",
        "ก ข ค",
        "๑๒๓",
        "mix กา 123",
        "อะไร",
        "ดี",
    ],
)
def test_idempotent_corpus(text: str) -> None:
    once = normalize(text)
    assert normalize(once) == once

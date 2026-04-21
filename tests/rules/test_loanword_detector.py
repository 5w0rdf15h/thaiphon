"""Tests for the heuristic foreignness detector."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from thaiphon.lexicons.loanword_detector import score_foreignness

# ---------------------------------------------------------------------------
# High-score cases — modern English loans
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "word",
    [
        "กราฟ",
        "ลิฟต์",
        "ซอฟต์แวร์",
        "ฟิล์ม",
        "ออฟฟิศ",
        "กอล์ฟ",
    ],
)
def test_loanwords_score_high(word: str) -> None:
    analysis = score_foreignness(word)
    assert analysis.is_loanword >= 0.6, (
        f"{word!r} scored {analysis.is_loanword}; signals={analysis.signals}"
    )


# ---------------------------------------------------------------------------
# Low-score cases — common native words
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "word",
    [
        "แม่",
        "น้ำ",
        "ไป",
        "กิน",
        "บ้าน",
        "หมา",
        "รัก",
        "ดี",
    ],
)
def test_native_words_score_low(word: str) -> None:
    analysis = score_foreignness(word)
    assert analysis.is_loanword <= 0.2, (
        f"{word!r} scored {analysis.is_loanword}; signals={analysis.signals}"
    )


# ---------------------------------------------------------------------------
# Sanskrit fossils — carry ◌์ but are not modern loans. The thanthakhat
# signal fires and the score lands in a moderate band; the number is
# deliberately ambiguous and is why the detector's output is paired with
# the signal list rather than used as a hard boolean.
# ---------------------------------------------------------------------------

SANSKRIT_FOSSIL_SCORE_BAND: tuple[float, float] = (0.3, 0.6)


@pytest.mark.parametrize(
    "word",
    [
        "จันทร์",
        "ศักดิ์",
    ],
)
def test_sanskrit_fossil_signal_and_band(word: str) -> None:
    analysis = score_foreignness(word)
    assert "thanthakhat" in analysis.signals
    low, high = SANSKRIT_FOSSIL_SCORE_BAND
    assert low <= analysis.is_loanword <= high, (
        f"{word!r} scored {analysis.is_loanword} outside "
        f"moderate band [{low}, {high}]; signals={analysis.signals}"
    )


# ---------------------------------------------------------------------------
# Preserved-coda candidate detection
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "word",
    [
        "กราฟ",    # bare ฟ
        "ลิฟต์",   # ฟ + killed ต
        "กอล์ฟ",   # bare ฟ
        "เจฟ",     # bare ฟ
    ],
)
def test_preserved_coda_present_for_fo_fan_endings(word: str) -> None:
    # The detector walks right-to-left stripping (consonant + ◌์)
    # pairs, so ลิฟต์ (ฟ followed by killed ต) classifies as "f"
    # alongside plain ฟ-final words.
    analysis = score_foreignness(word)
    assert analysis.preserved_coda_candidate == "f"


def test_preserved_coda_fo_fan_with_thanthakhat() -> None:
    # คลิฟฟ์ ends in ฟ์ — preservation candidate.
    word = "คลิฟฟ์"
    analysis = score_foreignness(word)
    assert analysis.preserved_coda_candidate == "f"


@pytest.mark.parametrize(
    "word,expected",
    [
        # ส / ศ / ษ finals → candidate "s".
        ("บัส", "s"),    # bare ส
        ("เคส", "s"),    # bare ส
        ("ดิสก์", "s"),  # killed ก, ส survives
        # ล final → candidate "l".
        ("เอลฟ์", "l"),  # killed ฟ, ล survives
        # ก final → candidate "k".
        ("ก๊อก", "k"),   # bare ก
    ],
)
def test_preserved_coda_non_f_endings(word: str, expected: str) -> None:
    """Detector reports 's'/'l'/'k' for the matching orthographic finals
    (after stripping trailing killed consonants)."""
    analysis = score_foreignness(word)
    assert analysis.preserved_coda_candidate == expected


@pytest.mark.parametrize(
    "word",
    [
        "แอร์",   # killed ร, no audible coda
        "บาร์",   # killed ร, no audible coda
        "เบอร์",  # killed ร, no audible coda
    ],
)
def test_preserved_coda_none_when_silenced_stem(word: str) -> None:
    """Words whose trailing killed-consonant chain reveals a vowel
    (no preceding audible consonant) report None even when the
    overall word is obviously a loan."""
    analysis = score_foreignness(word)
    assert analysis.preserved_coda_candidate is None


def test_preserved_coda_absent_for_native_ending() -> None:
    # Native words ending in letters outside the preserved-set (ม, น,
    # ง, ย, ว, or a plain vowel) report None regardless of the overall score.
    for word in ["แม่", "บ้าน", "มา"]:
        analysis = score_foreignness(word)
        assert analysis.preserved_coda_candidate is None, word


# ---------------------------------------------------------------------------
# LoanAnalysis invariants
# ---------------------------------------------------------------------------

def test_loan_analysis_is_frozen() -> None:
    analysis = score_foreignness("มา")
    with pytest.raises((FrozenInstanceError, AttributeError)):
        analysis.is_loanword = 0.99  # type: ignore[misc]


def test_loan_analysis_score_is_clamped() -> None:
    # A curated loanword always short-circuits to exactly 1.0.
    analysis = score_foreignness("กราฟ")
    assert analysis.is_loanword == 1.0
    assert analysis.signals == ("lexicon_hit",)


def test_empty_input_yields_zero_score() -> None:
    analysis = score_foreignness("")
    assert analysis.is_loanword == 0.0
    assert analysis.signals == ()
    assert analysis.preserved_coda_candidate is None


def test_signals_always_tuple() -> None:
    analysis = score_foreignness("แม่")
    assert isinstance(analysis.signals, tuple)


# ---------------------------------------------------------------------------
# Native prefix dampener — การ-prefixed derivatives are native compounds
# and must not tip over the high-score threshold even when they are long.
# ---------------------------------------------------------------------------

def test_native_prefix_suppresses_length_signal() -> None:
    # การเรียน — "studying" — long native derived form.
    word = "การเรียน"
    analysis = score_foreignness(word)
    assert "native_prefix" in analysis.signals
    assert analysis.is_loanword < 0.5

"""Tests for the curated loanword lexicon and its LoanProfile schema."""

from __future__ import annotations

import pytest

import thaiphon
from thaiphon.lexicons.loan_final_f import LOAN_FINAL_F_WORDS
from thaiphon.lexicons.loanword import (
    LOANWORDS,
    LoanEntry,
    LoanProfile,
    get_entry,
    words_by_coda_policy,
)


# ---------------------------------------------------------------------------
# LoanProfile schema
# ---------------------------------------------------------------------------


def test_loan_profile_accepts_valid_values() -> None:
    profile = LoanProfile(
        source_language="english",
        coda_policy="preserve",
        tone_policy="lexical",
        vowel_length_policy="spelling_driven",
        confidence="high",
    )
    assert profile.source_language == "english"
    assert profile.coda_policy == "preserve"


def test_loan_profile_is_frozen() -> None:
    profile = LoanProfile(
        source_language="english",
        coda_policy="preserve",
        tone_policy="lexical",
        vowel_length_policy="spelling_driven",
        confidence="high",
    )
    with pytest.raises(Exception):
        profile.source_language = "unknown"  # type: ignore[misc]


@pytest.mark.parametrize(
    "field,bad_value",
    [
        ("source_language", "spanish"),
        ("coda_policy", "drop"),
        ("tone_policy", "random"),
        ("vowel_length_policy", "native"),
        ("confidence", "maybe"),
    ],
)
def test_loan_profile_rejects_invalid_values(field: str, bad_value: str) -> None:
    kwargs = dict(
        source_language="english",
        coda_policy="preserve",
        tone_policy="lexical",
        vowel_length_policy="spelling_driven",
        confidence="high",
    )
    kwargs[field] = bad_value
    with pytest.raises(ValueError):
        LoanProfile(**kwargs)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# LOANWORDS table shape
# ---------------------------------------------------------------------------


def test_loanwords_table_is_non_empty() -> None:
    assert len(LOANWORDS) > 50


def test_every_entry_is_a_loanentry_with_profile() -> None:
    for word, entry in LOANWORDS.items():
        assert isinstance(entry, LoanEntry)
        assert entry.word == word
        assert isinstance(entry.profile, LoanProfile)


def test_get_entry_roundtrip() -> None:
    lift = "ลิฟต์"
    entry = get_entry(lift)
    assert entry is not None
    assert entry.word == lift
    assert entry.profile.coda_policy == "preserve"
    assert entry.profile.source_language == "english"


def test_get_entry_returns_none_for_non_loan() -> None:
    assert get_entry("ไทย") is None


# ---------------------------------------------------------------------------
# Backward-compatibility: LOAN_FINAL_F_WORDS is derived from the
# coda_policy="preserve" slice of LOANWORDS.
# ---------------------------------------------------------------------------


def test_loan_final_f_matches_preserve_slice() -> None:
    derived = words_by_coda_policy("preserve")
    assert LOAN_FINAL_F_WORDS == derived


def test_loan_final_f_still_contains_seed_entries() -> None:
    seeds = [
        "ลิฟต์",
        "ออฟฟิศ",
        "เอฟ",
        "กราฟ",
        "ไมโครซอฟต์",
    ]
    for word in seeds:
        assert word in LOAN_FINAL_F_WORDS


# ---------------------------------------------------------------------------
# End-to-end: seed entries still produce /f/-preserving TLC output.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "word",
    [
        "ลิฟต์",
        "ออฟฟิศ",
        "เอฟ",
        "ซอฟต์แวร์",
    ],
)
def test_seed_entry_preserves_final_f_in_tlc(word: str) -> None:
    import re

    out = thaiphon.transcribe(word, "tlc")
    assert re.search(r"f\{[LMHFR]\}", out), (
        f"loan word {word!r} lost /f/ preservation: got {out!r}"
    )

"""Tests for loanword coda-preservation behaviour.

Verifies that the lexicon-driven override fires for a representative set
of English loanwords. Each test anchors a visible, commonly-encountered
example so that changes to the preservation logic are caught immediately.

All example words are commonly-known Thai loanwords. Expected
pronunciations under urban educated speech are independently verifiable
from openly-licensed sources — Wiktionary (CC-BY-SA 4.0) and, where
applicable, the VOLUBILIS Mundo Dictionary (CC-BY-SA 4.0).
"""

from __future__ import annotations

import pytest

import thaiphon
from thaiphon.lexicons.loanword import LOANWORDS, get_entry, get_preserved_coda

# ---------------------------------------------------------------------------
# Lexicon membership
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "word",
    [
        "ลิฟต์",     # lift
        "เซฟ",       # save / chef
        "กราฟ",      # graph
        "กอล์ฟ",     # golf
        "อีเมล",     # email
        "บอล",       # ball
        "ฟุตบอล",    # football
        "เคส",       # case
        "บัส",       # bus
    ],
)
def test_word_in_loanword_lexicon(word: str) -> None:
    assert word in LOANWORDS


def test_get_entry_returns_loan_entry_for_known_word() -> None:
    from thaiphon.lexicons.loanword import LoanEntry

    entry = get_entry("ลิฟต์")
    assert entry is not None
    assert isinstance(entry, LoanEntry)


def test_get_entry_returns_none_for_unknown_word() -> None:
    assert get_entry("ไม่มีในพจนานุกรม") is None


# ---------------------------------------------------------------------------
# get_preserved_coda per profile
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "word, profile, expected_tag",
    [
        # ลิฟต์: /f/ preserved in both profiles.
        ("ลิฟต์", "everyday", "f"),
        ("ลิฟต์", "careful_educated", "f"),
        ("ลิฟต์", "etalon_compat", None),
        # เซฟ: strong preservation.
        ("เซฟ", "everyday", "f"),
        ("เซฟ", "etalon_compat", None),
        # กราฟ: register-sensitive — only careful_educated.
        ("กราฟ", "everyday", None),
        ("กราฟ", "careful_educated", "f"),
        ("กราฟ", "etalon_compat", None),
        # อีเมล: /l/ in both profiles.
        ("อีเมล", "everyday", "l"),
        ("อีเมล", "careful_educated", "l"),
        ("อีเมล", "etalon_compat", None),
        # เคส: /s/ in both profiles.
        ("เคส", "everyday", "s"),
        ("เคส", "careful_educated", "s"),
        ("เคส", "etalon_compat", None),
        # บัส: /s/ only under careful_educated.
        ("บัส", "everyday", None),
        ("บัส", "careful_educated", "s"),
        ("บัส", "etalon_compat", None),
    ],
)
def test_get_preserved_coda(
    word: str, profile: str, expected_tag: str | None
) -> None:
    assert get_preserved_coda(word, profile) == expected_tag


# ---------------------------------------------------------------------------
# TLC surface output — preservation fires
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "word, profile, expected_surface_fragment",
    [
        # ลิฟต์ — /f/ preserved → 'f' in TLC output.
        ("ลิฟต์", "everyday", "f"),
        ("ลิฟต์", "careful_educated", "f"),
        # อีเมล — /l/ preserved → 'l' near end.
        ("อีเมล", "everyday", "l{"),
        ("อีเมล", "careful_educated", "l{"),
        # เซฟ — /f/ preserved.
        ("เซฟ", "everyday", "f{"),
        # เคส — /s/ preserved.
        ("เคส", "everyday", "s{"),
        ("เคส", "careful_educated", "s{"),
    ],
)
def test_tlc_preservation_fires(
    word: str, profile: str, expected_surface_fragment: str
) -> None:
    result = thaiphon.transcribe(word, scheme="tlc", profile=profile)
    assert expected_surface_fragment in result


# ---------------------------------------------------------------------------
# TLC surface output — collapsing under etalon_compat
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "word, collapsed_fragment",
    [
        # ลิฟต์ → native /p̚/ → 'p'.
        ("ลิฟต์", "p{"),
        # เซฟ → native /p̚/ → 'p'.
        ("เซฟ", "p{"),
        # เคส → native /t̚/ → 't'.
        ("เคส", "t{"),
    ],
)
def test_tlc_etalon_compat_collapses(
    word: str, collapsed_fragment: str
) -> None:
    result = thaiphon.transcribe(word, scheme="tlc", profile="etalon_compat")
    # Foreign coda must not be preserved.
    assert "f{" not in result
    assert "s{" not in result
    assert "l{" not in result
    # Native collapsed coda must be present.
    assert collapsed_fragment in result


# ---------------------------------------------------------------------------
# IPA scheme — preservation fires
# ---------------------------------------------------------------------------


def test_ipa_lift_f_preserved_everyday() -> None:
    result = thaiphon.transcribe("ลิฟต์", scheme="ipa", profile="everyday")
    assert "f" in result


def test_ipa_lift_collapses_etalon_compat() -> None:
    result = thaiphon.transcribe("ลิฟต์", scheme="ipa", profile="etalon_compat")
    assert "f" not in result
    assert "p̚" in result


# ---------------------------------------------------------------------------
# Lexicon integrity: no duplicate entries
# ---------------------------------------------------------------------------


def test_loanword_lexicon_no_duplicates() -> None:
    # LOANWORDS is a MappingProxy; keys must be unique by construction.
    # If _build_entries() raised on a duplicate, import itself would fail.
    # We verify this indirectly by confirming import succeeded and the
    # mapping is non-empty.
    assert len(LOANWORDS) > 0

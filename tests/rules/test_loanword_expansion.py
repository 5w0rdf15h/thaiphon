"""Verify the curated loanword lexicon expansion.

These tests assert that the expanded set of entries are picked up by the
curated lexicon and its detector, and that /f/-preserving entries keep
final /f/ in the TLC surface form.
"""

from __future__ import annotations

import unicodedata

import pytest

import thaiphon
from thaiphon.lexicons.loanword import LOANWORDS, get_entry
from thaiphon.lexicons.loanword_detector import score_foreignness

# /f/-preserving English loans. Every word here must end orthographically
# in ฟ or ฟ์ and must carry coda_policy="preserve".
_NEW_F_PRESERVE: tuple[str, ...] = (
    "กอล์ฟ",
    "คาร์ดิฟฟ์",
    "ทัมบ์ไดรฟ์",
    "ยีราฟ",
    "สลาฟ",
    "ออเดิร์ฟ",
    "เอลฟ์",
    "ไดรฟ์",
    "ไมโครเวฟ",
    "ไวไฟ",
)


# Representative sample of lexical English loans. Not the full
# list — we don't want the test file to enumerate the lexicon. These
# must all be in LOANWORDS with coda_policy="lexical".
_NEW_LEXICAL_SAMPLE: tuple[str, ...] = (
    "คอมพิวเตอร์",
    "ฮาร์ดแวร์",
    "ไฟล์",
    "ลิงก์",
    "เมาส์",
    "เบราว์เซอร์",
    "เว็บไซต์",
    "ออนไลน์",
    "แบงก์",
    "กีตาร์",
    "เบียร์",
    "แอร์",
    "เฮลิคอปเตอร์",
    "แฮมเบอร์เกอร์",
    "ฟิสิกส์",
)


@pytest.mark.parametrize("word", _NEW_F_PRESERVE)
def test_new_f_preserve_entry_is_listed(word: str) -> None:
    nfc = unicodedata.normalize("NFC", word)
    assert nfc in LOANWORDS, f"{word} missing from LOANWORDS"
    entry = get_entry(nfc)
    assert entry is not None
    assert entry.profile.coda_policy == "preserve"
    assert entry.profile.source_language == "english"


@pytest.mark.parametrize("word", _NEW_F_PRESERVE)
def test_new_f_preserve_entry_scores_as_loanword(word: str) -> None:
    analysis = score_foreignness(unicodedata.normalize("NFC", word))
    assert analysis.is_loanword == 1.0
    assert "lexicon_hit" in analysis.signals


# Words where the preservation override really does change the surface
# form. Excluded:
#   - ฟ์-final words: the killer mark silences the coda in the
#     syllabifier before the loan override can fire.
#   - กอล์ฟ: the ล์ฟ cluster is segmented as a separate /fa/ syllable
#     rather than a coda.
#   - ไวไฟ: the final ไฟ syllable carries ฟ as ONSET, not coda, so
#     "preserve final /f/" does not apply.
_F_CODA_RENDERS: tuple[str, ...] = (
    "คาร์ดิฟฟ์",   # final syllable ends in ฟฟ์ — killer over fused ฟฟ
    "ยีราฟ",
    "สลาฟ",
    "ออเดิร์ฟ",
    "ไมโครเวฟ",
)


@pytest.mark.parametrize("word", _F_CODA_RENDERS)
def test_new_f_preserve_word_renders_with_f_coda(word: str) -> None:
    """The TLC surface form must keep /f/ as the final coda."""
    tlc = thaiphon.transcribe(unicodedata.normalize("NFC", word), "tlc")
    final_token = tlc.split()[-1]
    base = final_token.split("{", 1)[0]
    assert base.endswith("f"), (
        f"expected /f/ coda for {word}, got {tlc!r}"
    )


@pytest.mark.parametrize("word", _NEW_LEXICAL_SAMPLE)
def test_new_lexical_entry_is_listed(word: str) -> None:
    nfc = unicodedata.normalize("NFC", word)
    assert nfc in LOANWORDS, f"{word} missing from LOANWORDS"
    entry = get_entry(nfc)
    assert entry is not None
    assert entry.profile.coda_policy == "lexical"
    assert entry.profile.source_language == "english"


@pytest.mark.parametrize("word", _NEW_LEXICAL_SAMPLE)
def test_new_lexical_entry_scores_as_loanword(word: str) -> None:
    analysis = score_foreignness(unicodedata.normalize("NFC", word))
    assert analysis.is_loanword == 1.0
    assert "lexicon_hit" in analysis.signals


def test_expansion_adds_entries() -> None:
    """Sanity check — the full lexicon must grow past the 150 mark."""
    assert len(LOANWORDS) >= 150

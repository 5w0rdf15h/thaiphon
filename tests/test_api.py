"""Tests for the public thaiphon API.

Covers: transcribe, transcribe_word, transcribe_sentence, analyze,
analyze_word, list_schemes — including scheme selection, reading profiles,
format argument, NFC/NFD input parity, and error handling.
"""

from __future__ import annotations

import unicodedata

import pytest

import thaiphon
from thaiphon.api import (
    analyze,
    analyze_word,
    list_schemes,
    transcribe,
    transcribe_sentence,
    transcribe_word,
)
from thaiphon.errors import UnsupportedSchemeError


# ---------------------------------------------------------------------------
# list_schemes
# ---------------------------------------------------------------------------


def test_list_schemes_returns_tuple() -> None:
    schemes = list_schemes()
    assert isinstance(schemes, tuple)


def test_list_schemes_contains_builtin() -> None:
    schemes = list_schemes()
    assert "ipa" in schemes
    assert "tlc" in schemes
    assert "morev" in schemes


def test_list_schemes_sorted() -> None:
    schemes = list_schemes()
    assert schemes == tuple(sorted(schemes))


# ---------------------------------------------------------------------------
# transcribe — default scheme (tlc) and basic sanity
# ---------------------------------------------------------------------------


def test_transcribe_default_scheme_is_tlc() -> None:
    # Default scheme must match explicit scheme="tlc".
    assert transcribe("มา") == transcribe("มา", scheme="tlc")


def test_transcribe_returns_str() -> None:
    assert isinstance(transcribe("กา", scheme="tlc"), str)


def test_transcribe_unsupported_scheme_raises() -> None:
    with pytest.raises(UnsupportedSchemeError):
        transcribe("กา", scheme="no_such_scheme")


def test_transcribe_unsupported_scheme_message() -> None:
    with pytest.raises(UnsupportedSchemeError, match="no_such_scheme"):
        transcribe("กา", scheme="no_such_scheme")


# ---------------------------------------------------------------------------
# transcribe — scheme="tlc" spot-checks across tone / consonant class
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai, expected",
    [
        # Mid-class onset, open syllable, long /aː/, plain (MID).
        ("กา", "gaa{M}"),
        # High-class onset, open syllable, RISING tone.
        ("ขา", "khaa{R}"),
        # Low-class sonorant onset, MID tone.
        ("มา", "maa{M}"),
        # Inherent vowel / dead syllable.
        ("ก", "ga{L}"),
        # Glide-diphthong: ไ- Sara Ai Maimuan.
        ("ไป", "bpai{M}"),
        # Short /a/ + nasal coda.
        ("คำ", "kham{M}"),
        # Long /aː/ + nasal coda.
        ("งาน", "ngaan{M}"),
        # Mid-class, mai ek → LOW.
        ("ไม่", "mai{F}"),
        # Water — lexicon-driven long /aː/ on น้ำ.
        ("น้ำ", "naam{H}"),
    ],
)
def test_tlc_spot_checks(thai: str, expected: str) -> None:
    assert transcribe(thai, scheme="tlc") == expected


# ---------------------------------------------------------------------------
# transcribe — scheme="ipa" spot-checks
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai, expected",
    [
        # IPA wraps output in /…/.
        ("กา", "/kaː˧/"),
        # High-class onset rising.
        ("ขา", "/kʰaː˩˩˦/"),
        # น้ำ — HIGH tone (low-class + mai tho), long vowel, /m/ coda.
        ("น้ำ", "/naːm˦˥/"),
    ],
)
def test_ipa_spot_checks(thai: str, expected: str) -> None:
    assert transcribe(thai, scheme="ipa") == expected


def test_ipa_wrapped_in_slashes() -> None:
    result = transcribe("กา", scheme="ipa")
    assert result.startswith("/") and result.endswith("/")


# ---------------------------------------------------------------------------
# transcribe — format argument
# ---------------------------------------------------------------------------


def test_format_text_returns_plain_string() -> None:
    result = transcribe("กา", scheme="tlc", format="text")
    assert "<" not in result


def test_format_html_is_accepted() -> None:
    # Should not raise; we do not assert exact HTML structure here because
    # it may evolve, but the call must succeed.
    result = transcribe("กา", scheme="tlc", format="html")
    assert isinstance(result, str)


def test_tlc_html_tone_is_superscript() -> None:
    # HTML output wraps the tone letter in ``<sup>`` instead of emitting
    # the bracketed ``{X}`` form used by the text scheme. กา is mid tone.
    text = transcribe("กา", scheme="tlc", format="text")
    html = transcribe("กา", scheme="tlc", format="html")
    assert "{M}" in text
    assert "{M}" not in html
    assert "<sup>M</sup>" in html


def test_tlc_html_tone_covers_all_five_tones() -> None:
    # One representative word per tone; HTML must emit the matching
    # superscript letter and never the bracketed text form.
    cases = {
        "กา": "M",    # mid
        "ข่า": "L",   # low
        "ค้า": "H",   # high
        "ข้า": "F",   # falling
        "ขา": "R",    # rising
    }
    for word, letter in cases.items():
        html = transcribe(word, scheme="tlc", format="html")
        assert f"<sup>{letter}</sup>" in html, (word, html)
        assert "{" not in html, (word, html)


# ---------------------------------------------------------------------------
# transcribe — profile argument
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "profile",
    ["everyday", "careful_educated", "learned_full", "etalon_compat"],
)
def test_transcribe_all_profiles_accepted(profile: str) -> None:
    # All four profiles must be accepted without error on a plain word.
    result = transcribe("กา", scheme="tlc", profile=profile)
    assert isinstance(result, str)


def test_default_profile_is_everyday() -> None:
    # Omitting profile must equal explicit profile="everyday".
    assert transcribe("กา", scheme="tlc") == transcribe(
        "กา", scheme="tlc", profile="everyday"
    )


# ---------------------------------------------------------------------------
# transcribe — NFC / NFD input parity
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai",
    [
        "กา",
        "ขา",
        "น้ำ",
        "สวัสดี",
        "ไทย",
        "ผลไม้",
    ],
)
def test_nfc_nfd_parity_tlc(thai: str) -> None:
    nfd = unicodedata.normalize("NFD", thai)
    nfc = unicodedata.normalize("NFC", thai)
    assert transcribe(nfc, scheme="tlc") == transcribe(nfd, scheme="tlc")


@pytest.mark.parametrize(
    "thai",
    [
        "กา",
        "น้ำ",
        "ผลไม้",
    ],
)
def test_nfc_nfd_parity_ipa(thai: str) -> None:
    nfd = unicodedata.normalize("NFD", thai)
    nfc = unicodedata.normalize("NFC", thai)
    assert transcribe(nfc, scheme="ipa") == transcribe(nfd, scheme="ipa")


# ---------------------------------------------------------------------------
# transcribe_word
# ---------------------------------------------------------------------------


def test_transcribe_word_matches_transcribe() -> None:
    assert transcribe_word("มา", scheme="tlc") == transcribe("มา", scheme="tlc")


def test_transcribe_word_all_schemes() -> None:
    for scheme in list_schemes():
        result = transcribe_word("กา", scheme=scheme)
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# transcribe_sentence
# ---------------------------------------------------------------------------


def test_transcribe_sentence_returns_str() -> None:
    result = transcribe_sentence("ฉันชอบกินข้าว", scheme="tlc")
    assert isinstance(result, str)


def test_transcribe_sentence_space_separated() -> None:
    # At least one space between tokens expected.
    result = transcribe_sentence("ฉันชอบกินข้าว", scheme="tlc")
    assert " " in result


def test_transcribe_sentence_ipa_wrapped() -> None:
    result = transcribe_sentence("ฉัน", scheme="ipa")
    assert result.startswith("/") and result.endswith("/")


def test_transcribe_sentence_empty_string() -> None:
    assert transcribe_sentence("", scheme="tlc") == ""


def test_transcribe_sentence_custom_segmenter() -> None:
    # Supply a trivial segmenter (each char is its own token) to verify
    # the segmenter kwarg is threaded through correctly.
    def _char_segmenter(text: str):
        return list(text)

    result = transcribe_sentence("กา", scheme="tlc", segmenter=_char_segmenter)
    assert isinstance(result, str)


# ---------------------------------------------------------------------------
# analyze / analyze_word
# ---------------------------------------------------------------------------


def test_analyze_returns_analysis_result() -> None:
    from thaiphon.model.candidate import AnalysisResult

    result = analyze("กา")
    assert isinstance(result, AnalysisResult)


def test_analyze_best_is_phonological_word() -> None:
    from thaiphon.model.word import PhonologicalWord

    result = analyze("กา")
    assert isinstance(result.best, PhonologicalWord)


def test_analyze_single_syllable_word() -> None:
    result = analyze("กา")
    assert len(result.best) == 1


def test_analyze_two_syllable_word() -> None:
    result = analyze("สวัสดี")
    assert len(result.best) >= 2


def test_analyze_word_equals_analyze() -> None:
    r1 = analyze("กา")
    r2 = analyze_word("กา")
    # Both should produce the same phonological word.
    assert r1.best.syllables == r2.best.syllables


def test_analyze_result_has_raw() -> None:
    result = analyze("กา")
    assert result.raw != "" or result.best.raw != ""


def test_analyze_loan_analysis_attached() -> None:
    # AnalysisResult.loan_analysis is populated (may be None for native words,
    # but the attribute must exist and not raise).
    result = analyze("กา")
    # loan_analysis is always attached (may be None for non-loanwords).
    assert hasattr(result, "loan_analysis")


# ---------------------------------------------------------------------------
# Edge: empty / whitespace input
# ---------------------------------------------------------------------------


def test_transcribe_empty_string() -> None:
    result = transcribe("", scheme="tlc")
    assert isinstance(result, str)


def test_transcribe_whitespace_only() -> None:
    # Whitespace-only input should not raise; result type is str.
    result = transcribe("   ", scheme="tlc")
    assert isinstance(result, str)


def test_transcribe_sentence_whitespace_only() -> None:
    result = transcribe_sentence("   ", scheme="tlc")
    assert isinstance(result, str)

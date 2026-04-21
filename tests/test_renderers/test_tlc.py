"""Tests for the TLC ('Enhanced Phonemic') renderer.

TLC is the default output scheme. These tests cover:
- Mid / high / low consonant class onsets.
- All five tones (from orthographic rules and explicit tone marks).
- Inherent short /a/, long /aː/ vowels.
- Several common vowel qualities (ee, oo, ae, etc.).
- Final consonants and stop codas.
- Tone tags ({M} / {L} / {H} / {F} / {R}) always present.
- Sara Am ◌ำ → aam/am.
- Consonant cluster onsets.
- Default scheme is tlc.
"""

from __future__ import annotations

import pytest

import thaiphon
from thaiphon.errors import UnsupportedSchemeError


# ---------------------------------------------------------------------------
# Scheme registration
# ---------------------------------------------------------------------------


def test_tlc_registered() -> None:
    assert "tlc" in thaiphon.list_schemes()


def test_default_scheme_is_tlc() -> None:
    assert thaiphon.transcribe("มา") == thaiphon.transcribe("มา", scheme="tlc")


# ---------------------------------------------------------------------------
# Tone tag always present
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai",
    ["มา", "ขา", "กา", "ไป", "ใจ", "คำ", "น้ำ", "โต", "ดี", "หมา"],
)
def test_tlc_output_has_tone_tag(thai: str) -> None:
    out = thaiphon.transcribe(thai, scheme="tlc")
    assert any(tag in out for tag in ("{L}", "{M}", "{H}", "{F}", "{R}"))


# ---------------------------------------------------------------------------
# Consonant classes — open syllable, long /aː/
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai, expected",
    [
        # Mid-class: ก → /k/, MID tone on live open syllable.
        ("กา", "gaa{M}"),
        # Mid-class: ต → /t/
        ("ตา", "dtaa{M}"),
        # Mid-class: ป → /p/
        ("ปา", "bpaa{M}"),
        # High-class: ข → /kʰ/, RISING tone.
        ("ขา", "khaa{R}"),
        # High-class: ถ → /tʰ/
        ("ถา", "thaa{R}"),
        # High-class: ผ → /pʰ/
        ("ผา", "phaa{R}"),
        # High-class: ห → /h/
        ("หา", "haa{R}"),
        # High-class: ส → /s/
        ("สา", "saa{R}"),
        # Low-class paired: ค → /kʰ/, MID tone.
        ("คา", "khaa{M}"),
        # Low-class paired: ช → /tɕʰ/
        ("ชา", "chaa{M}"),
        # Low-class paired: พ → /pʰ/
        ("พา", "phaa{M}"),
        # Low-class sonorant: ม → /m/, MID.
        ("มา", "maa{M}"),
        # Low-class sonorant: น → /n/
        ("นา", "naa{M}"),
        # Low-class sonorant: ง → /ŋ/
        ("งา", "ngaa{M}"),
        # Low-class sonorant: ล → /l/
        ("ลา", "laa{M}"),
        # Low-class sonorant: ว → /w/
        ("วา", "waa{M}"),
        # Low-class sonorant: ย → /j/
        ("ยา", "yaa{M}"),
        # Low-class sonorant: ร → /r/
        ("รา", "raa{M}"),
    ],
)
def test_consonant_class_long_a(thai: str, expected: str) -> None:
    assert thaiphon.transcribe(thai, scheme="tlc") == expected


# ---------------------------------------------------------------------------
# Explicit tone marks on mid-class /kaː/
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai, expected",
    [
        # No mark — MID (baseline).
        ("กา", "gaa{M}"),
        # mai ek on MC → LOW tone.
        ("ก่า", "gaa{L}"),
        # mai tho on MC → FALLING tone.
        ("ก้า", "gaa{F}"),
        # mai tri on MC → HIGH tone.
        ("ก๊า", "gaa{H}"),
        # mai jattawa on MC → RISING tone.
        ("ก๋า", "gaa{R}"),
    ],
)
def test_tone_marks_mid_class(thai: str, expected: str) -> None:
    assert thaiphon.transcribe(thai, scheme="tlc") == expected


# ---------------------------------------------------------------------------
# Inherent vowel / dead syllable
# ---------------------------------------------------------------------------


def test_bare_consonant_dead_syllable() -> None:
    # ก alone — mid-class dead short → LOW.
    assert thaiphon.transcribe("ก", scheme="tlc") == "ga{L}"


def test_short_dead_syllable_stop_coda() -> None:
    # จะ — mid-class + short open → LOW.
    assert thaiphon.transcribe("จะ", scheme="tlc") == "ja{L}"


# ---------------------------------------------------------------------------
# Common vowels
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai, expected",
    [
        # Long /iː/ → ee.
        ("ดี", "dee{M}"),
        # Short /i/ + kill → di (dead).  สี — HC /sǐː/ → HIGH.
        ("สี", "see{R}"),
        # Long /uː/ → uu.
        ("ดู", "duu{M}"),
        # Long /eː/ → aeh.
        ("เก", "gaeh{M}"),
        # Long /ɛː/ → aae. (แก)
        ("แก", "gaae{M}"),
        # Long /oː/ spelled โ. (โก)
        ("โก", "go:h{M}"),
        # Long /ɔː/ → aaw. (กอ)
        ("กอ", "gaaw{M}"),
        # Long /ɯː/ → euu. (ดือ)
        ("ดือ", "deuu{M}"),
    ],
)
def test_vowel_variety(thai: str, expected: str) -> None:
    assert thaiphon.transcribe(thai, scheme="tlc") == expected


# ---------------------------------------------------------------------------
# Codas: nasal and stop
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai, expected",
    [
        # /n/ coda.
        ("งาน", "ngaan{M}"),
        # /m/ coda.
        ("กาม", "gaam{M}"),
        # /ŋ/ coda.
        ("กาง", "gaang{M}"),
        # /p̚/ coda.
        ("กาบ", "gaap{L}"),
        # /t̚/ coda.
        ("กาด", "gaat{L}"),
        # /k̚/ coda.
        ("กาก", "gaak{L}"),
    ],
)
def test_coda_variety(thai: str, expected: str) -> None:
    assert thaiphon.transcribe(thai, scheme="tlc") == expected


# ---------------------------------------------------------------------------
# Sara Am
# ---------------------------------------------------------------------------


def test_sara_am_long_vowel_m_coda() -> None:
    # น้ำ — FALLING tone, long /aː/, /m/ coda.
    assert thaiphon.transcribe("น้ำ", scheme="tlc") == "naam{H}"


def test_sara_am_mid_class() -> None:
    # คำ — low-class paired, no mark → MID.
    assert thaiphon.transcribe("คำ", scheme="tlc") == "kham{M}"


# ---------------------------------------------------------------------------
# Common words (regression anchors)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai, expected",
    [
        ("ใจ", "jai{M}"),
        ("ไป", "bpai{M}"),
        ("ไม่", "mai{F}"),
        # ไม้ — lexicon drives long /aː/ (wood/tone mark).
        ("ไม้", "maai{H}"),
        # ได้ — lexicon drives long /aː/ (get/receive).
        ("ได้", "daai{F}"),
        ("ดี", "dee{M}"),
        ("ดู", "duu{M}"),
        ("มี", "mee{M}"),
    ],
)
def test_common_word_regressions(thai: str, expected: str) -> None:
    assert thaiphon.transcribe(thai, scheme="tlc") == expected


# ---------------------------------------------------------------------------
# Cluster onset
# ---------------------------------------------------------------------------


def test_cluster_onset_pr() -> None:
    # ปลา — /p/ + /l/ cluster onset.
    result = thaiphon.transcribe("ปลา", scheme="tlc")
    assert "bpl" in result


def test_cluster_onset_kr() -> None:
    # กรุง — /k/ + /r/ cluster.
    result = thaiphon.transcribe("กรุง", scheme="tlc")
    assert "g" in result and "r" in result


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


def test_unsupported_scheme_raises() -> None:
    with pytest.raises(UnsupportedSchemeError):
        thaiphon.transcribe("กา", scheme="xyz_scheme")

"""Tests for the RTL (Rak Thai Language School) renderer.

Surface conventions verified:

- Aspirated stops are digraphs: /kʰ/ → ``kh``, /tʰ/ → ``th``,
  /pʰ/ → ``ph``, /tɕʰ/ → ``ch``. Unaspirated voiceless stops are bare
  letters: /k/ → ``k``, /t/ → ``t``, /p/ → ``p``, /tɕ/ → ``c`` (note
  ``c``, not ``j``).
- Vowel-initial syllables receive an explicit ``ʼ`` (U+02BC) onset.
- Long vowels are written as doubled letters; the combining tone mark
  lands on the first vowel letter only (``kāa``, not ``kaā``).
- Centring diphthongs ``ia ʉa ua`` carry the tone on the first element.
- IPA-letter vowels ``ʉ`` (U+0289), ``ɛ`` (U+025B), ``ɔ`` (U+0254),
  ``ə`` (U+0259) stay as two codepoints after NFC (no precomposed
  diacritic forms exist for these letters).
- Mid tone → macron; low → grave; falling → circumflex; high → acute;
  rising → háček.
- Long /iː/ before /w/ spells the nucleus as ``ia`` (เขียว → ``khǐaw``).
- Foreign-only coda IPAs collapse: /f/ → ``p``, /s/ → ``t``, /l/ → ``n``.
- Syllable separator is a single space.
"""

from __future__ import annotations

import importlib.util
import unicodedata

import pytest

import thaiphon

# Words whose canonical long-vowel pronunciation lives in the optional
# ``thaiphon-data-volubilis`` data package are gated behind this marker;
# without the lexicon the reader falls back to productive rules and gives
# a shorter rule-only surface.
_HAS_VOLUBILIS = importlib.util.find_spec("thaiphon_data_volubilis") is not None
_needs_volubilis = pytest.mark.skipif(
    not _HAS_VOLUBILIS,
    reason="requires thaiphon-data-volubilis",
)


def _nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def _render(thai: str) -> str:
    return thaiphon.transcribe(thai, scheme="rtl")


# ---------------------------------------------------------------------------
# Scheme registration
# ---------------------------------------------------------------------------


def test_rtl_registered() -> None:
    assert "rtl" in thaiphon.list_schemes()


# ---------------------------------------------------------------------------
# Five-way tone contrast on long /aː/ with a /k/ onset.
#   กา  = kaa mid      → kāa
#   ก่า  = kaa low      → kàa
#   ก้า  = kaa falling  → kâa
#   ก๊า  = kaa high     → káa
#   ก๋า  = kaa rising   → kǎa
# The combining diacritic lands on the first ``a`` only.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai, expected",
    [
        ("กา", "kāa"),
        ("ก่า", "kàa"),
        ("ก้า", "kâa"),
        ("ก๊า", "káa"),
        ("ก๋า", "kǎa"),
    ],
)
def test_five_tones_on_long_a(thai: str, expected: str) -> None:
    assert _render(thai) == _nfc(expected)


# ---------------------------------------------------------------------------
# Tone mark sits on the FIRST vowel letter of a digraph.
# ---------------------------------------------------------------------------


def test_tone_on_first_letter_of_long_vowel() -> None:
    # พ่อ  /pʰɔ̂ː/ — falling tone on long /ɔː/, diacritic on first ɔ.
    out = _render("พ่อ")
    assert out == _nfc("phɔ̂ɔ")
    # The circumflex is above the first ɔ, not the second.
    assert "ɔ̂ɔ" in out
    assert "ɔɔ̂" not in out


def test_tone_on_first_letter_of_diphthong() -> None:
    # เรือ /rɯ̄a/ (long centring diphthong) — macron on ʉ only.
    assert _render("เรือ") == _nfc("rʉ̄a")
    # มัว  /mūa/ — macron on u only.
    assert _render("มัว") == _nfc("mūa")
    # เมีย /mīa/ — macron on i only.
    assert _render("เมีย") == _nfc("mīa")


# ---------------------------------------------------------------------------
# Vowel-initial syllables get an explicit ``ʼ`` onset.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai, expected",
    [
        ("อา", "ʼāa"),
        ("อีก", "ʼìik"),
        ("เอา", "ʼāw"),
        ("ไอ", "ʼāy"),
        ("อาหาร", "ʼāa hǎan"),
    ],
)
def test_glottal_stop_onset(thai: str, expected: str) -> None:
    assert _render(thai) == _nfc(expected)


# ---------------------------------------------------------------------------
# Consonant-class / aspiration inventory.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai, onset",
    [
        ("กา", "k"),
        ("ขา", "kh"),
        ("ตา", "t"),
        ("ถา", "th"),
        ("ปา", "p"),
        ("ผา", "ph"),
        ("จา", "c"),    # /tɕ/ → c, not j
        ("ฉา", "ch"),   # /tɕʰ/ → ch
        ("ชา", "ch"),   # LC variant of /tɕʰ/
        ("หา", "h"),
        ("งา", "ŋ"),
        ("มา", "m"),
        ("นา", "n"),
        ("ลา", "l"),
        ("รา", "r"),
        ("วา", "w"),
        ("ยา", "y"),
        ("ดา", "d"),
        ("บา", "b"),
        ("สา", "s"),
        ("ฟา", "f"),
    ],
)
def test_onset_inventory(thai: str, onset: str) -> None:
    out = _render(thai)
    assert out.startswith(onset), f"{thai} → {out!r} should start with {onset!r}"


# ---------------------------------------------------------------------------
# Short vs long vowels are visible as single vs doubled letters.
# ---------------------------------------------------------------------------


def test_short_vs_long_vowel() -> None:
    # ละ /lá/ short /a/, LC+short pseudo-open → HIGH tone.
    assert _render("ละ") == _nfc("lá")
    # ลา /lāː/ long /aː/, LC+long → MID tone.
    assert _render("ลา") == _nfc("lāa")


def test_short_closed_syllable() -> None:
    # รถ /rót̚/ — LC + short + stop → HIGH.
    assert _render("รถ") == _nfc("rót")
    # กิน /kīn/ — MC + short + sonorant → MID.
    assert _render("กิน") == _nfc("kīn")


# ---------------------------------------------------------------------------
# IPA-letter vowels: ʉ, ɛ, ɔ, ə.
# ---------------------------------------------------------------------------


def test_open_mid_vowels() -> None:
    # แม่ /mɛ̂ː/ — long /ɛː/ + falling.
    assert _render("แม่") == _nfc("mɛ̂ɛ")
    # ขอ /kʰɔ̌ː/ — long /ɔː/ + rising.
    assert _render("ขอ") == _nfc("khɔ̌ɔ")


def test_high_central_vowel() -> None:
    # ผึ้ง /pʰɯ̂ŋ/ — short /ɯ/ (printed as ʉ) + /ŋ/ + falling. Works on
    # productive rules alone, no lexicon needed.
    assert _render("ผึ้ง") == _nfc("phʉ̂ŋ")


@_needs_volubilis
def test_mid_central_vowel_long() -> None:
    # เลย /lɤ̄ːj/ — canonical long /ɤː/ (printed as ``əə``) + /j/ + mid
    # tone. The long vowel length is a lexicon lookup; rule-only parsing
    # of this orthographic frame gives a short /ɤ/ instead.
    assert _render("เลย") == _nfc("lə̄əy")


# ---------------------------------------------------------------------------
# Long /iː/ before /w/ spells the nucleus as ``ia``.
# ---------------------------------------------------------------------------


def test_i_long_plus_w_becomes_ia_diphthong() -> None:
    # เขียว /kʰiaw/ (rising) — the school analyses เ-ียว as /ia/+/w/.
    assert _render("เขียว") == _nfc("khǐaw")


# ---------------------------------------------------------------------------
# Stop codas.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai, expected",
    [
        ("มาก", "mâak"),   # LC + long + /k/ stop → falling
        ("จาก", "càak"),   # MC + long + /k/ stop → low
        ("ลูก", "lûuk"),   # LC + long + /k/ → falling
        ("ข้าว", "khâaw"),  # HC + long + /w/ (sonorant not stop; tone from mark)
        ("ขาด", "khàat"),  # HC + long + /t/ → low
    ],
)
def test_stop_codas(thai: str, expected: str) -> None:
    assert _render(thai) == _nfc(expected)


# ---------------------------------------------------------------------------
# Cluster onsets.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai, cluster",
    [
        ("กรา", "kr"),
        ("ครา", "khr"),
        ("กลา", "kl"),
        ("ขลา", "khl"),
        ("กวา", "kw"),
        ("ขวา", "khw"),
        ("ปลา", "pl"),
        ("ปรา", "pr"),
        ("พลา", "phl"),
        ("ตรา", "tr"),
    ],
)
def test_cluster_onsets(thai: str, cluster: str) -> None:
    out = _render(thai)
    assert out.startswith(cluster), f"{thai} → {out!r} should start with {cluster!r}"


# ---------------------------------------------------------------------------
# Multi-syllable words — syllables joined by a single space.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai, expected",
    [
        ("สวัสดี", "sà wàt dīi"),
        ("ภาษา", "phāa sǎa"),
        ("โรงเรียน", "rōoŋ rīan"),
        ("ประเทศ", "prà thêet"),
        ("ดินสอ", "dīn sɔ̌ɔ"),
        ("กาแฟ", "kāa fɛ̄ɛ"),
    ],
)
def test_multi_syllable_words(thai: str, expected: str) -> None:
    assert _render(thai) == _nfc(expected)


# ---------------------------------------------------------------------------
# Special-vowel shortcuts: -am, -aw, -ay — the final sonorant is a
# normal coda, so the /a/+coda combination comes out naturally.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai, expected",
    [
        ("น้ำ", "náam"),    # long /aː/ + /m/
        ("ทำ", "thām"),     # short /a/ + /m/
        ("ไม่", "mây"),      # short /a/ + /j/ + falling
        ("ใหญ่", "yày"),    # หญ silent ห → y onset, short /a/ + /j/, low
    ],
)
def test_special_vowel_symbols(thai: str, expected: str) -> None:
    assert _render(thai) == _nfc(expected)


# ---------------------------------------------------------------------------
# NFC: Latin vowels precompose with their diacritic; IPA vowels don't.
# ---------------------------------------------------------------------------


def test_nfc_precomposed_for_latin_vowels() -> None:
    out = _render("กา")
    # ā is a single precomposed codepoint U+0101.
    assert "ā" in out


def test_nfc_two_codepoints_for_ipa_vowels() -> None:
    out = _render("ขอ")  # khɔ̌ɔ — ɔ has no precomposed caron form
    # The háček should still be there as a combining mark.
    assert "̌" in out  # COMBINING CARON
    # And the ɔ stays as U+0254.
    assert "ɔ" in out


# ---------------------------------------------------------------------------
# The four special vowel words from textbook Lesson 5 (the long-vowel
# exceptions: ``náam máay tháaw cháaw cháay``). These are core vocabulary
# and exercise the vowel-length plus coda-glide combinations end to end.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai, expected",
    [
        ("น้ำ", "náam"),    # water — long /aː/+m+high
        ("ไม้", "máay"),   # wood — long /aː/+j+high
        ("เท้า", "tháaw"),  # foot — long /aː/+w+high
        ("เช้า", "cháaw"),  # morning — long /aː/+w+high
        ("ใช้", "cháay"),   # to use — long /aː/+j+high
    ],
)
def test_lesson5_long_vowel_exceptions(thai: str, expected: str) -> None:
    assert _render(thai) == _nfc(expected)

"""Tests for the Paiboon and Paiboon+ renderers.

Both schemes share almost everything — they diverge only in how the
centring diphthongs ``/iə/ /ɯə/ /uə/`` spell their length contrast
(and the ``/iː/+w`` triphthong-like sequence). The tests below exercise
the shared surface first, then pin down the scheme-specific behaviour.

Reference conventions verified:

- Onsets: aspirated stops bare (``p t k ch``), unaspirated stops with
  a digraph (``bp dt g j``), /ŋ/ → ``ng``.
- Monophthongs are doubled when long (``aa ii uu ee ɛɛ oo ɔɔ ʉʉ əə``).
- Coda /w/ → ``o``, coda /j/ → ``i``; short /i/+w is the ``iu``
  exception ("Matthew").
- Tones: mid unmarked; low grave; falling circumflex; high acute;
  rising háček. Diacritic sits on the first vowel letter.
- Syllable separator is ``-``.
- Paiboon+ doubles the long centring diphthongs and the ``iː+w``
  nucleus (``iia ʉʉa uua``, ``iiao``); Paiboon uses the same spelling
  regardless of length (``ia ʉa ua``, ``iao``).
"""

from __future__ import annotations

import unicodedata

import pytest

import thaiphon


def _nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def _p(thai: str) -> str:
    return thaiphon.transcribe(thai, scheme="paiboon")


def _pp(thai: str) -> str:
    return thaiphon.transcribe(thai, scheme="paiboon_plus")


# ---------------------------------------------------------------------------
# Scheme registration
# ---------------------------------------------------------------------------


def test_paiboon_registered() -> None:
    assert "paiboon" in thaiphon.list_schemes()


def test_paiboon_plus_registered() -> None:
    assert "paiboon_plus" in thaiphon.list_schemes()


# ---------------------------------------------------------------------------
# Five-way tone contrast on long /aː/ with /k/ (unaspirated MC) onset.
# Mid is unmarked (not a macron, unlike RTL).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai, expected",
    [
        ("กา", "gaa"),
        ("ก่า", "gàa"),
        ("ก้า", "gâa"),
        ("ก๊า", "gáa"),
        ("ก๋า", "gǎa"),
    ],
)
def test_five_tones_paiboon(thai: str, expected: str) -> None:
    assert _p(thai) == _nfc(expected)


@pytest.mark.parametrize(
    "thai, expected",
    [
        ("กา", "gaa"),
        ("ก่า", "gàa"),
        ("ก้า", "gâa"),
        ("ก๊า", "gáa"),
        ("ก๋า", "gǎa"),
    ],
)
def test_five_tones_paiboon_plus(thai: str, expected: str) -> None:
    assert _pp(thai) == _nfc(expected)


# ---------------------------------------------------------------------------
# Aspirated vs unaspirated stop contrast — the distinguishing feature
# of the Paiboon onset convention.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai, onset",
    [
        ("กา", "g"),    # /k/ unaspirated → g
        ("ขา", "k"),    # /kʰ/ aspirated → k
        ("คา", "k"),    # LC variant of /kʰ/
        ("ตา", "dt"),   # /t/ unaspirated → dt
        ("ถา", "t"),    # /tʰ/ aspirated → t
        ("ทา", "t"),    # LC variant of /tʰ/
        ("ปา", "bp"),   # /p/ unaspirated → bp
        ("ผา", "p"),    # /pʰ/ aspirated → p
        ("พา", "p"),    # LC variant of /pʰ/
        ("จา", "j"),    # /tɕ/ → j
        ("ชา", "ch"),   # /tɕʰ/ → ch
        ("ฉา", "ch"),   # HC variant
        ("งา", "ng"),   # /ŋ/ → ng
        ("ดา", "d"),
        ("บา", "b"),
        ("ฟา", "f"),
        ("ซา", "s"),
        ("หา", "h"),
        ("มา", "m"),
        ("นา", "n"),
        ("ลา", "l"),
        ("รา", "r"),
        ("วา", "w"),
        ("ยา", "y"),
    ],
)
def test_onset_inventory_paiboon(thai: str, onset: str) -> None:
    out = _p(thai)
    assert out.startswith(onset), f"{thai} → {out!r} should start with {onset!r}"


# ---------------------------------------------------------------------------
# Vowel-glide combinations: coda /w/ → o, coda /j/ → i; short /i/+w
# is the "iu" exception.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai, expected",
    [
        ("ข้าว", "kâao"),    # long /aː/+/w/ → aao
        ("เอา", "ao"),      # short /a/+/w/ → ao
        ("ไม่", "mâi"),      # short /a/+/j/ → ai
        ("สาย", "sǎai"),     # long /aː/+/j/ → aai
        ("หิว", "hǐu"),       # short /i/+/w/ → iu (Matthew exception)
        ("ไทย", "tai"),      # mid tone on ai
    ],
)
def test_vowel_glide_combinations(thai: str, expected: str) -> None:
    assert _p(thai) == _nfc(expected)
    assert _pp(thai) == _nfc(expected)


# ---------------------------------------------------------------------------
# Short/long monophthong spelling.
# ---------------------------------------------------------------------------


def test_short_vs_long_monophthong() -> None:
    # Short /a/ (LC + pseudo-open short → HIGH tone).
    assert _p("ละ") == _nfc("lá")
    # Long /aː/ (LC + long → MID, unmarked).
    assert _p("ลา") == _nfc("laa")


@pytest.mark.parametrize(
    "thai, expected",
    [
        ("ขอ", "kɔ̌ɔ"),     # long /ɔː/ rising
        ("แม่", "mɛ̂ɛ"),     # long /ɛː/ falling
        ("เสีย", "sǐia"),    # long /iə/ rising (Paiboon+ doubled)
    ],
)
def test_ipa_letter_vowels_paiboon_plus(thai: str, expected: str) -> None:
    assert _pp(thai) == _nfc(expected)


# ---------------------------------------------------------------------------
# Centring diphthongs — the scheme-level difference.
#
#   /iə/ LONG (เ-ีย):  Paiboon+ ``iia``   / Paiboon ``ia``
#   /ɯə/ LONG (เ-ือ):  Paiboon+ ``ʉʉa``   / Paiboon ``ʉa``
#   /uə/ LONG (-ัว):   Paiboon+ ``uua``   / Paiboon ``ua``
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai, paiboon, paiboon_plus",
    [
        ("เสื้อ", "sʉ̂a", "sʉ̂ʉa"),   # from the reference example phrase
        ("เรือ", "rʉa", "rʉʉa"),
        ("เมีย", "mia", "miia"),
        ("มัว", "mua", "muua"),
        ("ตัว", "dtua", "dtuua"),
    ],
)
def test_centring_diphthong_length_contrast(
    thai: str, paiboon: str, paiboon_plus: str
) -> None:
    assert _p(thai) == _nfc(paiboon)
    assert _pp(thai) == _nfc(paiboon_plus)


def test_iw_triphthong_length_contrast() -> None:
    # เขียว /khiaw/ rising: Paiboon writes iao, Paiboon+ writes iiao.
    # Onset ข is HC → ``k`` in both schemes.
    assert _p("เขียว") == _nfc("kǐao")
    assert _pp("เขียว") == _nfc("kǐiao")


# ---------------------------------------------------------------------------
# Stop codas.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai, expected",
    [
        ("มาก", "mâak"),    # LC + long + /k/ → falling
        ("จาก", "jàak"),    # MC + long + /k/ → low
        ("ลูก", "lûuk"),    # LC + long + /k/ → falling
        ("ขาด", "kàat"),    # HC + long + /t/ → low
        ("รัก", "rák"),      # LC + short + /k/ → high
        ("ครับ", "kráp"),   # LC cluster + short + /p/ → high
        ("จบ", "jòp"),       # MC + short + /p/ → low
    ],
)
def test_stop_codas(thai: str, expected: str) -> None:
    assert _p(thai) == _nfc(expected)
    assert _pp(thai) == _nfc(expected)


# ---------------------------------------------------------------------------
# Cluster onsets — both elements emit without a joiner.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai, cluster",
    [
        ("ปลา", "bpl"),    # /p/+/l/ → bp + l
        ("ปรา", "bpr"),
        ("กลา", "gl"),
        ("กรา", "gr"),
        ("กวา", "gw"),
        ("ครา", "khr"[:2] + "r" if False else "kr"),  # simplified; see below
        ("ตรา", "dtr"),
    ],
)
def test_cluster_onsets(thai: str, cluster: str) -> None:
    # /kʰ/+/r/ → ``k`` + ``r`` = ``kr`` (both ``kʰra`` and ``kra`` spell
    # the same in Paiboon because /k/ vs /kʰ/ distinguish as g vs k, so
    # /kʰr/ = kr and /kr/ = gr. This parametrisation keeps /kr/ as gr.
    out = _p(thai)
    assert out.startswith(cluster), f"{thai} → {out!r} should start with {cluster!r}"


def test_kh_vs_k_cluster_contrast() -> None:
    # ครา (LC /kʰr/) → ``kraa``; กรา (MC /kr/) → ``graa``.
    assert _p("ครา").startswith("kr")
    assert _p("กรา").startswith("gr")


# ---------------------------------------------------------------------------
# Multi-syllable words — joined with ``-``.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai, paiboon, paiboon_plus",
    [
        ("สวัสดี", "sà-wàt-dii", "sà-wàt-dii"),
        ("ภาษา", "paa-sǎa", "paa-sǎa"),
        ("โรงเรียน", "roong-rian", "roong-riian"),
        ("ประเทศ", "bprà-têet", "bprà-têet"),
        ("อะไร", "à-rai", "à-rai"),
    ],
)
def test_multi_syllable_words(
    thai: str, paiboon: str, paiboon_plus: str
) -> None:
    assert _p(thai) == _nfc(paiboon)
    assert _pp(thai) == _nfc(paiboon_plus)


# ---------------------------------------------------------------------------
# The five-word phrase ``คุณ เก็บ เสื้อ ไว้ ไหน`` is the canonical
# example used to contrast Paiboon+ and Paiboon — the two schemes
# diverge only on ``เสื้อ`` (``sʉ̂ʉa`` vs ``sʉ̂a``). Exercise each word
# individually: a single concatenated string goes through the
# sentence-segmenter, which is out of scope for renderer tests.
# ---------------------------------------------------------------------------


def test_reference_phrase_paiboon_plus() -> None:
    words = ["คุณ", "เก็บ", "เสื้อ", "ไว้", "ไหน"]
    expected = ["kun", "gèp", "sʉ̂ʉa", "wái", "nǎi"]
    for thai, exp in zip(words, expected):
        assert _pp(thai) == _nfc(exp), (thai, _pp(thai), exp)


def test_reference_phrase_paiboon() -> None:
    words = ["คุณ", "เก็บ", "เสื้อ", "ไว้", "ไหน"]
    expected = ["kun", "gèp", "sʉ̂a", "wái", "nǎi"]
    for thai, exp in zip(words, expected):
        assert _p(thai) == _nfc(exp), (thai, _p(thai), exp)


# ---------------------------------------------------------------------------
# Glottal onset — vowel-initial syllables render without any symbol
# (unlike RTL). อะไร → à-rai, not ʼà-rai.
# ---------------------------------------------------------------------------


def test_no_explicit_glottal_onset() -> None:
    assert _p("อะไร") == _nfc("à-rai")
    assert _p("เอา") == _nfc("ao")
    assert _p("ไอ") == _nfc("ai")
    assert "ʼ" not in _p("อะไร")
    assert "'" not in _p("อะไร")


# ---------------------------------------------------------------------------
# Mid tone is unmarked (distinguishes Paiboon from RTL).
# ---------------------------------------------------------------------------


def test_mid_tone_unmarked() -> None:
    out = _p("กา")
    assert out == "gaa"
    # No macron anywhere.
    assert "̄" not in out
    assert "̄" not in unicodedata.normalize("NFD", out)

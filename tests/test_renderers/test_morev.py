"""Tests for the Morev (Cyrillic) renderer.

Surface conventions verified:

- Aspirated stops are spelled as digraphs: /kʰ/ → ``кх``, /tʰ/ → ``тх``,
  /pʰ/ → ``пх``. The aspirated palatal /tɕʰ/ stays as bare ``ч`` —
  the alphabet table lists ฉ / ช / ฌ as ``ч`` with no aspiration mark.
- Unaspirated palatal /tɕ/ → ``ть``.
- /h/ → ``х``; /ŋ/ → ``нг`` in both onset and coda.
- Long vowels carry a combining macron (U+0304); centring diphthongs
  put the macron on the first vocalic element only.
- Open back-rounded /ɔ/ collapses to Cyrillic ``о`` (U+043E),
  matching the dictionary's default rendering for both /oː/ and /ɔː/;
  mid-central /ɤ/ uses schwa ``ə`` (U+0259).
- Tones are spacing modifiers placed at the end of the syllable, after
  the coda: LOW ``ˆ``, FALLING `````, HIGH ``ˇ``, RISING ``´``;
  MID is unmarked. The engine's tone names follow modern-phonology
  convention; HIGH = high pitch, RISING = low-to-high contour.
- HTML output raises the ``х`` of the three plain aspirated stops:
  ``к<sup>х</sup>``, ``т<sup>х</sup>``, ``п<sup>х</sup>``. The
  aspirated palatal ``ч`` is never decorated.
- ``ว`` in the second slot of a CC onset cluster surfaces as the back
  vowel ``у`` (``กวาง`` → ``куа̄нг``).
- Foreign-only codas collapse: /f/ → ``п``, /s/ → ``т``, /l/ → ``н``.
- Syllable separator is ``-``.
"""

from __future__ import annotations

import unicodedata

import pytest

import thaiphon

# Spacing tone modifiers used by the Morev renderer.
_TONE_LOW = "ˆ"
_TONE_FALLING = "`"
_TONE_HIGH = "ˇ"
_TONE_RISING = "´"
_TONE_CHARS = (_TONE_LOW, _TONE_FALLING, _TONE_HIGH, _TONE_RISING)

_MACRON = "̄"


def _nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


# ---------------------------------------------------------------------------
# Scheme registration
# ---------------------------------------------------------------------------


def test_morev_registered() -> None:
    assert "morev" in thaiphon.list_schemes()


# ---------------------------------------------------------------------------
# Onset consonants — bare letters from the alphabet table
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai, onset_prefix",
    [
        ("กา", "к"),       # /k/
        ("ขา", "кх"),      # /kʰ/ digraph in text mode
        ("ตา", "т"),       # /t/
        ("ถา", "тх"),      # /tʰ/ digraph
        ("ปา", "п"),       # /p/
        ("ผา", "пх"),      # /pʰ/ digraph
        ("จา", "ть"),      # /tɕ/ digraph
        ("ฉา", "ч"),       # /tɕʰ/ bare ч (no aspiration mark)
        ("ชา", "ч"),       # /tɕʰ/ bare ч
        ("หา", "х"),       # /h/
        ("งา", "нг"),      # /ŋ/ digraph
        ("มา", "м"),
        ("นา", "н"),
        ("ลา", "л"),
        ("วา", "в"),       # /w/ as bare initial
        ("ยา", "й"),
        ("รา", "р"),
        ("ซา", "с"),
        ("บา", "б"),
        ("ดา", "д"),
        ("ฟา", "ф"),
    ],
)
def test_morev_onset_consonants(thai: str, onset_prefix: str) -> None:
    result = _nfc(thaiphon.transcribe(thai, scheme="morev"))
    assert result.startswith(onset_prefix), result


# ---------------------------------------------------------------------------
# Tone modifiers — spacing letters at the end of the syllable
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai, expected",
    [
        # All five tones on mid-class long /aː/.
        ("กา", "ка̄"),         # MID — no modifier
        ("ก่า", "ка̄ˆ"),        # LOW — ˆ at end
        ("ก้า", "ка̄`"),        # FALLING — ` at end
        ("ก๊า", "ка̄ˇ"),        # HIGH — ˇ at end
        ("ก๋า", "ка̄´"),        # RISING — ´ at end
    ],
)
def test_morev_tone_suffix_position(thai: str, expected: str) -> None:
    result = _nfc(thaiphon.transcribe(thai, scheme="morev"))
    assert result == _nfc(expected)


def test_morev_tone_modifier_follows_coda() -> None:
    # ``เด็ก`` is a closed dead syllable with LOW tone; the modifier
    # must sit after the coda ``к``, not on the vowel.
    result = thaiphon.transcribe("เด็ก", scheme="morev")
    assert result.endswith("к" + _TONE_LOW)
    # No combining tone diacritic should appear on the vowel.
    assert not any(
        unicodedata.combining(ch) > 0 and ch != _MACRON for ch in result
    )


def test_morev_mid_tone_has_no_modifier() -> None:
    result = thaiphon.transcribe("กา", scheme="morev")
    assert not any(c in result for c in _TONE_CHARS)


# ---------------------------------------------------------------------------
# Vowel surface forms
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai, expected",
    [
        ("ขอ", "кхо̄´"),         # /ɔ/ collapses to Cyrillic о
        ("เธอ", "тхə̄"),          # /ɤ/ uses schwa
        ("เลือก", "лы̄ак`"),      # ɯə LONG: macron on first element
        ("เกวียน", "куӣан"),      # iə LONG inside a /kw/ cluster
        ("รวย", "рӯай"),          # uə LONG with /j/ coda
        ("เรือ", "ры̄а"),         # ɯə open syllable
        ("ดี", "дӣ"),             # i LONG
        ("รู", "рӯ"),             # u LONG
    ],
)
def test_morev_vowels(thai: str, expected: str) -> None:
    result = _nfc(thaiphon.transcribe(thai, scheme="morev"))
    assert result == _nfc(expected)


def test_morev_short_vowel_no_macron() -> None:
    result = thaiphon.transcribe("จะ", scheme="morev")
    assert _MACRON not in unicodedata.normalize("NFD", result)


# ---------------------------------------------------------------------------
# /ŋ/ as нг in onset and coda
# ---------------------------------------------------------------------------


def test_morev_ng_onset() -> None:
    result = thaiphon.transcribe("งาน", scheme="morev")
    assert result.startswith("нг")


def test_morev_ng_coda() -> None:
    result = thaiphon.transcribe("กาง", scheme="morev")
    assert result.endswith("нг")


# ---------------------------------------------------------------------------
# Cluster /w/: ว as back vowel у in second slot
# ---------------------------------------------------------------------------


def test_morev_cluster_w_renders_as_u() -> None:
    # ``กวาง`` is /kwaːŋ/; the second slot ``ว`` surfaces as ``у``.
    assert thaiphon.transcribe("กวาง", scheme="morev") == _nfc("куа̄нг")


# ---------------------------------------------------------------------------
# Foreign-coda collapse: /f/ → п, /s/ → т, /l/ → н
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai, expected",
    [
        ("ปรู๊ฟ", "прӯпˇ"),       # /f/ coda → п, HIGH
        # Lexicon-dependent words (e.g. กราฟ) are not in this test set.
        ("ก๊าซ", "ка̄тˇ"),         # /s/ coda → т, HIGH
        ("โบนัส", "бо̄-натˇ"),    # /s/ coda → т, HIGH
        ("ฟุตบอล", "футˇ-бо̄н"),  # /l/ coda → н (and /ɔ/ → о)
        ("บอล", "бо̄н"),          # /l/ coda → н
    ],
)
def test_morev_foreign_coda_collapse(thai: str, expected: str) -> None:
    assert _nfc(thaiphon.transcribe(thai, scheme="morev")) == _nfc(expected)


# ---------------------------------------------------------------------------
# Spot-checks against alphabet-table example words
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai, expected",
    [
        ("ไก่", "кайˆ"),          # ก example
        ("เต่า", "тауˆ"),         # ต example
        ("เด็ก", "декˆ"),         # ด example
        ("ฉิ่ง", "чингˆ"),        # ฉ example
        ("หีบ", "хӣпˆ"),          # ห example
        ("แหวน", "вэ̄н´"),        # ว example (after silent ห, HC unmarked → RISING)
        ("น้ำ", "на̄мˇ"),         # /n/ + /aːm/ + HIGH
        ("หา", "ха̄´"),           # /h/ RISING
        ("ขา", "кха̄´"),          # /kʰ/ RISING
        ("ค้า", "кха̄ˇ"),          # /kʰ/ HIGH
        ("ผม", "пхом´"),         # /pʰ/ + /om/ RISING
        ("ทหาร", "тхаˇ-ха̄н´"),   # leading ห-syllable + main
        ("ขอ", "кхо̄´"),         # /ɔ/ → Cyrillic о, RISING
        ("มา", "ма̄"),            # MID, no tone modifier
    ],
)
def test_morev_alphabet_table_examples(thai: str, expected: str) -> None:
    assert _nfc(thaiphon.transcribe(thai, scheme="morev")) == _nfc(expected)


# ---------------------------------------------------------------------------
# Two-syllable word has dash separator
# ---------------------------------------------------------------------------


def test_morev_two_syllable_has_dash() -> None:
    result = thaiphon.transcribe("สวัสดี", scheme="morev")
    assert "-" in result


# ---------------------------------------------------------------------------
# HTML overlay: aspirated stops gain a superscript second element
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai, sup_digraph",
    [
        ("ขา", "к<sup>х</sup>"),
        ("ค้า", "к<sup>х</sup>"),
        ("ถา", "т<sup>х</sup>"),
        ("ผา", "п<sup>х</sup>"),
        ("ทหาร", "т<sup>х</sup>"),
    ],
)
def test_morev_html_aspirated_overlay(thai: str, sup_digraph: str) -> None:
    html = thaiphon.transcribe(thai, scheme="morev", format="html")
    assert sup_digraph in html
    text = thaiphon.transcribe(thai, scheme="morev", format="text")
    # Plain ``х`` digraph in text mode, no superscript markup.
    assert "<sup>" not in text
    assert "х" in text


def test_morev_html_palatal_aspirated_no_overlay() -> None:
    # /tɕʰ/ stays as bare ``ч`` in both formats — the alphabet table
    # never decorates ฉ / ช / ฌ.
    text = thaiphon.transcribe("ฉา", scheme="morev", format="text")
    html = thaiphon.transcribe("ฉา", scheme="morev", format="html")
    assert text == html
    assert "<sup>" not in html


def test_morev_html_unaspirated_unchanged() -> None:
    text = thaiphon.transcribe("กา", scheme="morev", format="text")
    html = thaiphon.transcribe("กา", scheme="morev", format="html")
    assert text == html


# ---------------------------------------------------------------------------
# IPA renderer: html and text outputs must match
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("thai", ["ขา", "เด็ก", "กวาง"])
def test_ipa_html_equals_text(thai: str) -> None:
    text = thaiphon.transcribe(thai, scheme="ipa", format="text")
    html = thaiphon.transcribe(thai, scheme="ipa", format="html")
    assert text == html


# ---------------------------------------------------------------------------
# Default format is "text" (regression guard)
# ---------------------------------------------------------------------------


def test_morev_default_format_is_text() -> None:
    default = thaiphon.transcribe("ขา", scheme="morev")
    text = thaiphon.transcribe("ขา", scheme="morev", format="text")
    assert default == text
    assert "<sup>" not in default


# ---------------------------------------------------------------------------
# /ɔ/ → Cyrillic о collapse: Latin open-O is never emitted by the renderer
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai",
    [
        "ขอ",       # engine /ɔ/ long
        "กอ",       # engine /ɔ/ long
        "บอก",      # engine /ɔ/ long with stop coda
        "ปอน",      # engine /ɔ/ long with nasal coda
        "ฟุตบอล",   # mixed: contains engine /ɔ/ + foreign /l/ coda collapse
        "โต",       # engine /o/ long (control)
        "โบนัส",    # engine /o/ long (control) + foreign /s/ coda collapse
    ],
)
def test_morev_open_o_collapses_to_cyrillic(thai: str) -> None:
    out = _nfc(thaiphon.transcribe(thai, scheme="morev"))
    # Latin small open-O (U+0254) must never appear in Morev output.
    assert "ɔ" not in out, out
    # The Cyrillic letter о (U+043E) must be present.
    assert "о" in out, out

"""Tests for the RTGS (Royal Thai General System of Transcription) renderer.

Surface conventions verified:

- Plain ASCII Latin output — no diacritics, no tone marks, no length
  doubling, no IPA-extension letters, no glottal-stop symbol.
- Aspirated stops are digraphs ``ph th kh ch``; unaspirated voiceless
  stops are bare ``p t k``; /tɕ/ and /tɕʰ/ both map to ``ch``.
- Monophthongs have one Latin spelling across lengths: ``a e i o u ae
  oe ue``. Centring diphthongs: ``ia uea ua``.
- Coda glides: /w/ → ``o``, /j/ → ``i`` (ไทย → ``thai``, ข้าว → ``khao``).
- Six-way coda merge, foreign codas included: /f/ → ``p``, /s/ → ``t``,
  /l/ → ``n``. Preservation is never applied on the RTGS surface,
  regardless of profile — ลิฟต์ always renders as ``lip``.
- Vowel-initial syllables (word-initial or medial) emit no onset glyph.
- Silent (thanthakhat) letters are dropped upstream; the renderer sees
  no residue from them.
- Syllables within a single word are concatenated with no separator.
"""

from __future__ import annotations

import pytest

import thaiphon


def _render(thai: str) -> str:
    return thaiphon.transcribe(thai, scheme="rtgs")


# ---------------------------------------------------------------------------
# Scheme registration
# ---------------------------------------------------------------------------


def test_rtgs_registered() -> None:
    assert "rtgs" in thaiphon.list_schemes()


# ---------------------------------------------------------------------------
# No diacritics or tone marks anywhere in RTGS output.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai",
    ["กา", "ก่า", "ก้า", "ก๊า", "ก๋า", "ขา", "พ่อ", "แม่", "ข้าว", "สวัสดี", "ภาษาไทย"],
)
def test_output_is_plain_ascii(thai: str) -> None:
    out = _render(thai)
    assert out.isascii(), f"{thai} → {out!r} should be pure ASCII"
    # None of the common Thai-romanization combining marks leaks in.
    for mark in ("̀", "́", "̂", "̄", "̌", "ʼ"):
        assert mark not in out
    # The IPA-letter vowels the other Latin schemes emit must not
    # appear here.
    for ch in ("ɛ", "ɔ", "ʉ", "ə", "ŋ"):
        assert ch not in out


def test_five_tones_produce_identical_surface() -> None:
    # RTGS marks no tone. All five tone-variants of กา surface the same.
    assert _render("กา") == "ka"
    assert _render("ก่า") == "ka"
    assert _render("ก้า") == "ka"
    assert _render("ก๊า") == "ka"
    assert _render("ก๋า") == "ka"


# ---------------------------------------------------------------------------
# Onset inventory.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai, expected",
    [
        # Plain stops.
        ("กา", "ka"),
        ("ตา", "ta"),
        ("ปา", "pa"),
        ("ดา", "da"),
        ("บา", "ba"),
        # Aspirated stops — digraphs.
        ("ขา", "kha"),
        ("คา", "kha"),
        ("ถา", "tha"),
        ("ทา", "tha"),
        ("ผา", "pha"),
        ("พา", "pha"),
        # /tɕ/ and /tɕʰ/ both surface as ``ch``.
        ("จา", "cha"),
        ("ฉา", "cha"),
        ("ชา", "cha"),
        # Fricatives.
        ("ฟา", "fa"),
        ("สา", "sa"),
        ("ซา", "sa"),
        ("หา", "ha"),
        ("ฮา", "ha"),
        # Sonorants.
        ("มา", "ma"),
        ("นา", "na"),
        ("งา", "nga"),   # /ŋ/ onset → ``ng``.
        ("ยา", "ya"),
        ("รา", "ra"),
        ("ลา", "la"),
        ("วา", "wa"),
    ],
)
def test_onset_inventory(thai: str, expected: str) -> None:
    assert _render(thai) == expected


# ---------------------------------------------------------------------------
# Cluster onsets — both elements emit with no joiner.
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
        ("พรา", "phr"),
        ("ตรา", "tr"),
    ],
)
def test_cluster_onsets(thai: str, cluster: str) -> None:
    out = _render(thai)
    assert out.startswith(cluster), (
        f"{thai} → {out!r} should start with {cluster!r}"
    )


# ---------------------------------------------------------------------------
# Vowel-initial syllables: no glottal-stop symbol, whether word-initial
# or medial.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai, expected",
    [
        ("อา", "a"),
        ("อีก", "ik"),
        ("เอา", "ao"),
        ("ไอ", "ai"),
        ("อาหาร", "ahan"),
    ],
)
def test_no_glottal_stop_symbol(thai: str, expected: str) -> None:
    out = _render(thai)
    assert out == expected
    # The RTL scheme uses U+02BC for glottal onsets — it must never
    # leak into RTGS output.
    assert "ʼ" not in out
    assert "'" not in out


# ---------------------------------------------------------------------------
# Monophthongs: each quality uses one Latin spelling across both
# lengths.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "short_thai, long_thai, letter",
    [
        ("จะ", "จา", "a"),      # /a/ short, /aː/ long → ``a``
        ("จิ", "จี", "i"),      # /i/ short, /iː/ long → ``i``
        ("จุ", "จู", "u"),      # /u/ short, /uː/ long → ``u``
        ("เจะ", "เจ", "e"),    # /e/ short, /eː/ long → ``e``
        ("แจะ", "แจ", "ae"),   # /ɛ/ short, /ɛː/ long → ``ae``
        ("โจะ", "โจ", "o"),    # /o/ short, /oː/ long → ``o``
        ("จึ", "จือ", "ue"),   # /ɯ/ short, /ɯː/ long → ``ue``
    ],
)
def test_vowel_length_collapses(
    short_thai: str, long_thai: str, letter: str
) -> None:
    short_out = _render(short_thai)
    long_out = _render(long_thai)
    assert letter in short_out, f"{short_thai} → {short_out!r} missing {letter!r}"
    assert letter in long_out, f"{long_thai} → {long_out!r} missing {letter!r}"
    # Long vowels are never spelled as doubled letters in RTGS.
    assert letter * 2 not in long_out


# ---------------------------------------------------------------------------
# Centring diphthongs.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai, expected",
    [
        ("เมีย", "mia"),     # /iə/ → ``ia``
        ("เรือ", "ruea"),    # /ɯə/ → ``uea``
        ("มัว", "mua"),      # /uə/ → ``ua``
    ],
)
def test_centring_diphthongs(thai: str, expected: str) -> None:
    assert _render(thai) == expected


def test_iao_frame() -> None:
    # เขียว — pipeline models this as /iː/+w; RTGS spells the frame
    # as ``ia`` (nucleus) + ``o`` (glide) → ``khiao``.
    assert _render("เขียว") == "khiao"


# ---------------------------------------------------------------------------
# Coda inventory — the six-way merge.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai, expected",
    [
        # Nasal codas.
        ("กาม", "kam"),
        ("กาน", "kan"),
        ("กาง", "kang"),
        # Stop codas — native letters collapse by place.
        ("มาก", "mak"),     # ก final → ``k``
        ("ขาด", "khat"),    # ด final → ``t``
        ("จบ", "chop"),     # บ final → ``p``
        # ญ ณ ร ล ฬ finals → ``n``.
        ("กาญ", "kan"),
        ("กาล", "kan"),
        # Glide codas.
        ("ข้าว", "khao"),   # ว final → ``o``
        ("ไทย", "thai"),    # ย final → ``i``
    ],
)
def test_coda_inventory(thai: str, expected: str) -> None:
    assert _render(thai) == expected


# ---------------------------------------------------------------------------
# Foreign codas collapse unconditionally — RTGS is the strict-collapse
# canonical form. Modern-loan /f/ preservation is never applied.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai, expected",
    [
        ("ลิฟต์", "lip"),     # /f/-coda loan → ``p``
        ("เชฟ", "chep"),
        ("ยีราฟ", "yirap"),
    ],
)
def test_loanword_f_coda_always_collapses(thai: str, expected: str) -> None:
    assert _render(thai) == expected


@pytest.mark.parametrize(
    "profile",
    ["everyday", "careful_educated", "learned_full", "etalon_compat"],
)
def test_loanword_f_coda_collapses_under_every_profile(profile: str) -> None:
    assert thaiphon.transcribe("ลิฟต์", scheme="rtgs", profile=profile) == "lip"


# ---------------------------------------------------------------------------
# Silent (thanthakhat) letters — dropped upstream by the orthography
# reader, so no residue appears on the surface.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai",
    ["ลิฟต์", "ไมโครซอฟต์", "รักษ์"],
)
def test_silent_letters_absent_from_output(thai: str) -> None:
    out = _render(thai)
    # No trailing residue from the cancelled syllable.
    assert "?" not in out
    # Output is ASCII and contains no Thai characters.
    assert out.isascii()


# ---------------------------------------------------------------------------
# Multi-syllable whole-word spellings — syllables within a word are
# concatenated.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai, expected",
    [
        ("สวัสดี", "sawatdi"),
        ("ภาษาไทย", "phasathai"),
        ("กรุงเทพ", "krungthep"),
        ("อาหาร", "ahan"),
    ],
)
def test_whole_word_concatenation(thai: str, expected: str) -> None:
    assert _render(thai) == expected


# ---------------------------------------------------------------------------
# The special vowel digraphs -am, -ay, -ao drop out of the coda system
# naturally.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai, expected",
    [
        ("น้ำ", "nam"),
        ("ทำ", "tham"),
        ("ไม้", "mai"),
        ("ใหญ่", "yai"),
        ("เอา", "ao"),
    ],
)
def test_special_vowel_shortcuts(thai: str, expected: str) -> None:
    assert _render(thai) == expected


# ---------------------------------------------------------------------------
# transcribe_word is the stable entry-point for single tokens; the
# sentence-layer inserts spaces between segmented words.
# ---------------------------------------------------------------------------


def test_transcribe_word_single_token_concatenates_syllables() -> None:
    assert thaiphon.transcribe_word("กรุงเทพ", "rtgs") == "krungthep"
    assert thaiphon.transcribe_word("สวัสดี", "rtgs") == "sawatdi"


def test_transcribe_sentence_inserts_space_between_tokens() -> None:
    # With a word-level segmenter that picks out กรุง + เทพ as distinct
    # tokens, the sentence layer joins them with a single space —
    # yielding the familiar road-sign form ``krung thep``. The default
    # built-in segmenter is a naive fallback and does not produce
    # word-level breaks; callers in production wire pythainlp's
    # segmenter (or a custom one) via the ``segmenter`` kwarg.
    out = thaiphon.transcribe_sentence(
        "กรุงเทพ", "rtgs", segmenter=lambda _: ("กรุง", "เทพ")
    )
    assert out == "krung thep"

"""Tests for the LMT (Lipilina-Muzychenko-Thapanosoth) Cyrillic renderer.

Surface conventions verified:

- Vowel length marked with ASCII colon ``:`` on the nucleus.
- Tones rendered at the end of the syllable as Unicode superscript
  digits in text mode (``⁰`` mid, ``¹`` low, ``²`` falling, ``³``
  high, ``⁴`` rising); HTML mode wraps an ordinary ASCII digit in
  ``<sup>…</sup>``.
- Syllable separator inside a word is a single space.
- Onset and coda inventories mirror the Morev Russian-academic
  tradition; foreign-origin codas (/f/, /s/, /l/) collapse to the
  nearest native segment regardless of profile.
- Centring diphthongs carry the length colon on the nucleus only;
  the off-glide ``а`` stays bare.
- ``ว`` in the second slot of a true CC onset cluster surfaces as the
  back vowel ``у``.
- No glottal-stop symbol in any output.
- /o/ is Cyrillic ``о``; /ɔ/ is Latin IPA ``ɔ`` (U+0254 OPEN O).
- /ɤ/ is Latin schwa ``ə`` (U+0259).
"""

from __future__ import annotations

import pytest

import thaiphon


def _render(thai: str, *, fmt: str = "text", profile: str = "everyday") -> str:
    return thaiphon.transcribe(
        thai, scheme="lmt", format=fmt, profile=profile
    )


# ---------------------------------------------------------------------------
# Scheme registration
# ---------------------------------------------------------------------------


def test_lmt_registered() -> None:
    assert "lmt" in thaiphon.list_schemes()


# ---------------------------------------------------------------------------
# Output shape — no slash wrapping; transcriptions are bare.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai",
    ["กา", "ขา", "มา", "น้ำ", "ดี", "กาน", "สวัสดี", "ภาษาไทย"],
)
def test_output_has_no_slash_wrapping(thai: str) -> None:
    # The forward slash is a display convention used in the printed
    # textbook but is not part of the emitted transcription.
    out = _render(thai)
    assert "/" not in out


# ---------------------------------------------------------------------------
# Tone digits — all five tones at the end of the syllable.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai, digit",
    [
        ("กา", "⁰"),   # MC, no mark → MID.
        ("ก่า", "¹"),  # MC + mai ek → LOW.
        ("ก้า", "²"),  # MC + mai tho → FALLING.
        ("ก๊า", "³"),  # MC + mai tri → HIGH.
        ("ก๋า", "⁴"),  # MC + mai jattawa → RISING.
    ],
)
def test_tone_digits_mid_class(thai: str, digit: str) -> None:
    # The superscript digit is the last character of the output.
    assert _render(thai).endswith(digit)


def test_high_class_rising_on_live_syllable() -> None:
    # High-class onset, live syllable, no tone mark → RISING (⁴).
    assert _render("ขา").endswith("⁴")


def test_low_class_mid_on_live_syllable() -> None:
    # Low-class onset, live syllable, no tone mark → MID (⁰).
    assert _render("มา").endswith("⁰")


# ---------------------------------------------------------------------------
# Onset inventory
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai, prefix",
    [
        # Plain stops.
        ("กา", "к"),
        ("ตา", "т"),
        ("ปา", "п"),
        ("ดา", "д"),
        ("บา", "б"),
        # Aspirated stops — digraphs.
        ("ขา", "кх"),
        ("คา", "кх"),
        ("ถา", "тх"),
        ("ทา", "тх"),
        ("ผา", "пх"),
        ("พา", "пх"),
        # Palatals: /tɕ/ = ть, /tɕʰ/ = ч (bare).
        ("จา", "ть"),
        ("ฉา", "ч"),
        ("ชา", "ч"),
        # Fricatives.
        ("ฟา", "ф"),
        ("สา", "с"),
        ("ซา", "с"),
        ("หา", "х"),
        ("ฮา", "х"),
        # Sonorants.
        ("มา", "м"),
        ("นา", "н"),
        ("งา", "нг"),
        ("ยา", "й"),
        ("รา", "р"),
        ("ลา", "л"),
        ("วา", "в"),
    ],
)
def test_onset_inventory(thai: str, prefix: str) -> None:
    out = _render(thai)
    assert out.startswith(prefix), (
        f"{thai} → {out!r} should start with {prefix!r}"
    )


# ---------------------------------------------------------------------------
# Cluster onsets
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai, cluster_prefix",
    [
        ("กรา", "кр"),
        ("ครา", "кхр"),
        ("กลา", "кл"),
        ("ขลา", "кхл"),
        ("ปลา", "пл"),
        ("ปรา", "пр"),
        ("พลา", "пхл"),
        ("พรา", "пхр"),
        ("ตรา", "тр"),
    ],
)
def test_cluster_onsets(thai: str, cluster_prefix: str) -> None:
    out = _render(thai)
    assert out.startswith(cluster_prefix)


def test_cluster_second_slot_w_becomes_back_vowel() -> None:
    # ``ว`` in the second slot of a true CC onset surfaces as ``у``.
    # กวาง → куа:нг…
    out = _render("กวาง")
    assert out.startswith("куа:")


def test_cluster_second_slot_khw() -> None:
    # ขวา → cluster /kʰw/ → кхуа…
    out = _render("ขวา")
    assert out.startswith("кхуа")


# ---------------------------------------------------------------------------
# Vowel-initial syllables: no glottal-stop symbol.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai",
    ["อา", "อีก", "เอา", "ไอ", "อาหาร"],
)
def test_no_glottal_stop_symbol(thai: str) -> None:
    out = _render(thai)
    # No RTL-style U+02BC modifier letter apostrophe, no ASCII
    # apostrophe, no IPA ʔ.
    assert "ʼ" not in out
    assert "'" not in out
    assert "ʔ" not in out


# ---------------------------------------------------------------------------
# Vowel inventory — both lengths per quality.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "short_thai, short_vowel, long_thai, long_vowel",
    [
        # /a/ short / long → а / а:
        ("จะ", "а", "จา", "а:"),
        # /i/ short / long → и / и:
        ("จิ", "и", "จี", "и:"),
        # /u/ short / long → у / у:
        ("จุ", "у", "จู", "у:"),
        # /e/ short / long → е / е:
        ("เจะ", "е", "เจ", "е:"),
        # /ɛ/ short / long → э / э:
        ("แจะ", "э", "แจ", "э:"),
        # /o/ short / long → о / о:
        ("โจะ", "о", "โจ", "о:"),
        # /ɯ/ short / long → ы / ы:
        ("จึ", "ы", "จือ", "ы:"),
    ],
)
def test_vowel_length_distinction(
    short_thai: str, short_vowel: str, long_thai: str, long_vowel: str
) -> None:
    short_out = _render(short_thai)
    long_out = _render(long_thai)
    assert short_vowel in short_out
    assert long_vowel in long_out
    # The short form must NOT contain the long-length colon marker.
    # We check this by stripping the long form's colon and verifying
    # the short form doesn't include a colon on this vowel letter.
    assert short_vowel + ":" not in short_out


def test_schwa_vowel_for_mid_central() -> None:
    # /ɤ/ renders as U+0259 Latin schwa.
    # เทอ (careful: uses the same frame as เทอม for /ɤː/) — use เจอ
    # which is unambiguously /tɕɤː/.
    out = _render("เจอ")
    assert "ə" in out


def test_open_o_is_latin_ipa_glyph() -> None:
    # /ɔ/ is spelled with the Latin IPA open-O letter ``ɔ`` (U+0254),
    # NOT with Cyrillic ``о`` (U+043E). This distinguishes สอง (sɔ̌ːŋ
    # — Latin ɔ) from โมง (moːŋ — Cyrillic о).
    song = _render("สอง")
    mong = _render("โมง")
    assert "ɔ" in song, f"expected Latin ɔ in {song!r}"
    assert "о" in mong, f"expected Cyrillic о in {mong!r}"
    # Cross-check: neither should contain the other's letter.
    assert "о" not in song
    assert "ɔ" not in mong


# ---------------------------------------------------------------------------
# Centring diphthongs — colon on the nucleus only.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai, nucleus_with_colon, off_glide",
    [
        ("เมีย", "и:", "а"),   # /iə/ long → и:а
        ("เรือ", "ы:", "а"),   # /ɯə/ long → ы:а
        ("มัว", "у:", "а"),    # /uə/ long → у:а
    ],
)
def test_centring_diphthong_colon_placement(
    thai: str, nucleus_with_colon: str, off_glide: str
) -> None:
    out = _render(thai)
    # Colon belongs on the nucleus, not after the ``а`` off-glide.
    assert nucleus_with_colon + off_glide in out
    # The stretched form ``иа:`` / ``ыа:`` / ``уа:`` must NOT appear.
    bad = nucleus_with_colon[0] + off_glide + ":"
    assert bad not in out


# ---------------------------------------------------------------------------
# Coda inventory — the six-way merge plus glides.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai, coda",
    [
        # Nasal codas.
        ("กาม", "м"),
        ("กาน", "н"),
        ("กาง", "нг"),
        # Stop codas — native letters collapse by place.
        ("มาก", "к"),
        ("ขาด", "т"),
        ("จบ", "п"),
        # ญ ณ ร ล ฬ finals all merge to /n/ → ``н``.
        ("กาญ", "н"),
        ("กาล", "н"),
        # Glide codas.
        ("ข้าว", "у"),   # ว final → у
        ("ไทย", "й"),    # ย final → й
    ],
)
def test_coda_inventory(thai: str, coda: str) -> None:
    out = _render(thai)
    # The tone digit sits at the very end; the coda must appear
    # immediately before it. Strip the trailing superscript-digit tone
    # marker to inspect the coda.
    inner = out[:-1] if out and out[-1].isdigit() else out
    assert inner.endswith(coda), (
        f"{thai} → {out!r} should have coda {coda!r} before the tone digit"
    )


# ---------------------------------------------------------------------------
# Foreign codas always collapse — LMT is a strict citation convention.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai",
    ["ลิฟต์", "เชฟ", "ยีราฟ"],
)
def test_foreign_f_coda_always_collapses(thai: str) -> None:
    out = _render(thai)
    # The final surface coda character must be ``п``, not ``ф``.
    inner = out[:-1] if out and out[-1].isdigit() else out
    assert inner.endswith("п")
    assert not inner.endswith("ф")


@pytest.mark.parametrize(
    "profile",
    ["everyday", "careful_educated", "learned_full", "etalon_compat"],
)
def test_f_coda_collapses_under_every_profile(profile: str) -> None:
    # LMT has no word_coda_override, so ลิฟต์ collapses identically
    # across every reading profile.
    out = thaiphon.transcribe("ลิฟต์", scheme="lmt", profile=profile)
    inner = out[:-1] if out and out[-1].isdigit() else out
    assert inner.endswith("п")


# ---------------------------------------------------------------------------
# Silent (thanthakhat) letters: cancelled syllables are dropped upstream.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai",
    ["ลิฟต์", "ไมโครซอฟต์", "รักษ์"],
)
def test_silent_letters_no_residue(thai: str) -> None:
    out = _render(thai)
    # No unknown-fallback marker leaks through.
    assert "?" not in out
    assert out, f"expected non-empty output for {thai!r}"


# ---------------------------------------------------------------------------
# Syllable separator inside a word is a space.
# ---------------------------------------------------------------------------


def test_multi_syllable_word_uses_space_separator() -> None:
    # สวัสดี has three syllables — LMT joins them with spaces.
    out = _render("สวัสดี")
    assert " " in out, f"expected space-separated syllables, got {out!r}"


def test_morev_style_hyphen_not_used() -> None:
    out = _render("สวัสดี")
    # The Morev dictionary uses ``-``; LMT does not.
    assert "-" not in out


# ---------------------------------------------------------------------------
# No Morev-style combining macron leaks through.
# ---------------------------------------------------------------------------


def test_no_combining_macron() -> None:
    # Sample a handful of long-vowel inputs; none may carry U+0304.
    for thai in ["กา", "ดี", "ภู", "พอ", "แม่"]:
        out = _render(thai)
        assert "̄" not in out


# ---------------------------------------------------------------------------
# HTML format: tone digit wrapped in <sup>…</sup>.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai, digit",
    [
        ("กา", "0"),
        ("ก่า", "1"),
        ("ก้า", "2"),
        ("ก๊า", "3"),
        ("ก๋า", "4"),
    ],
)
def test_html_tone_digit_is_superscript(thai: str, digit: str) -> None:
    out = _render(thai, fmt="html")
    assert f"<sup>{digit}</sup>" in out
    # The tone marker is the last thing emitted (no trailing slash).
    assert out.endswith(f"<sup>{digit}</sup>")


def test_html_multi_syllable_each_has_superscript_tone() -> None:
    # สวัสดี — three syllables, each gets its own <sup>…</sup>.
    out = _render("สวัสดี", fmt="html")
    assert out.count("<sup>") == out.count("</sup>")
    assert out.count("<sup>") >= 2


def test_text_mode_has_no_html_tags() -> None:
    out = _render("สวัสดี", fmt="text")
    assert "<sup>" not in out
    assert "</sup>" not in out


# ---------------------------------------------------------------------------
# transcribe_word / transcribe_sentence.
# ---------------------------------------------------------------------------


def test_transcribe_word_single_token() -> None:
    # Bare transcription, no slashes; ends with a superscript tone.
    out = thaiphon.transcribe_word("กา", "lmt")
    assert "/" not in out
    assert out.endswith("⁰")


def test_transcribe_sentence_inserts_space_between_tokens() -> None:
    out = thaiphon.transcribe_sentence(
        "กรุงเทพ", "lmt", segmenter=lambda _: ("กรุง", "เทพ")
    )
    # Each word's transcription is bare; tokens are joined by a space.
    assert "/" not in out
    assert " " in out

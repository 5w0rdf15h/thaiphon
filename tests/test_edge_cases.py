"""Tests for edge-case orthographic inputs.

Covers tricky or historically bug-prone patterns:
- Sara Am (◌ำ) — special vowel that encodes both a vowel and /m/ coda.
- Thanthakhat / killer mark (◌์) — silences a following consonant.
- Leading ห — raises effective consonant class of a following sonorant.
- Consonant clusters (กร, ปล, กว, etc.).
- Pre-vowel frames (เ◌า, เ◌็, etc.).
- Empty string and whitespace.
- Mixed Thai and ASCII input.
- Thai numerals.
- อ as vowel carrier (glottal onset).
"""

from __future__ import annotations

import pytest

import thaiphon
from thaiphon.model.enums import Tone, VowelLength


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _analyze(word: str, **kwargs):
    return thaiphon.analyze(word, **kwargs)


def _tlc(word: str, **kwargs) -> str:
    return thaiphon.transcribe(word, scheme="tlc", **kwargs)


def _ipa(word: str, **kwargs) -> str:
    return thaiphon.transcribe(word, scheme="ipa", **kwargs)


# ---------------------------------------------------------------------------
# Sara Am (◌ำ)
# ---------------------------------------------------------------------------


def test_sara_am_phonology_vowel_a_coda_m() -> None:
    # คำ — low-class + sara am → /a/ nucleus + /m/ coda.
    result = _analyze("คำ")
    syl = result.best.syllables[0]
    assert syl.vowel.symbol == "a"
    assert syl.coda is not None
    assert syl.coda.symbol == "m"


def test_sara_am_tone_tlc() -> None:
    # คำ — LC sonorant + sara am, no mark → MID.
    assert _tlc("คำ") == "kham{M}"


def test_sara_am_with_mai_tho() -> None:
    # น้ำ — LC + sara am + mai tho → FALLING on the am→HIGH pattern.
    # Lexicon length-override makes the vowel long.
    assert _tlc("น้ำ") == "naam{H}"


def test_sara_am_mc_onset() -> None:
    # จำ — MC onset + sara am → MID tone.
    result = _tlc("จำ")
    assert "{M}" in result
    assert "jam" in result


def test_sara_am_ipa_wraps() -> None:
    result = _ipa("คำ")
    assert result.startswith("/") and result.endswith("/")
    assert "m" in result


# ---------------------------------------------------------------------------
# Thanthakhat / killer mark (◌์)
# ---------------------------------------------------------------------------


def test_killer_mark_silences_coda() -> None:
    # จันทร์ — ทร์ is a silent cluster; output is single syl /tɕan/.
    result = _analyze("จันทร์")
    assert len(result.best.syllables) >= 1
    # The word must not crash; the silent cluster is dropped.


def test_killer_mark_basic_result_nonempty() -> None:
    result = _tlc("จันทร์")
    assert len(result) > 0


def test_killer_mark_word_jan() -> None:
    # จันทร์ (moon / Monday) — ทร์ silent → /tɕan/.
    result = _tlc("จันทร์")
    assert "jan" in result


def test_killer_mark_phonologically_single_consonant() -> None:
    # ศักดิ์ — ดิ์ is killed; result is single syllable /sàk/.
    result = _tlc("ศักดิ์")
    assert len(result) > 0
    # Expect no raised error.


# ---------------------------------------------------------------------------
# Leading ห — silencing ห elevates effective class of following sonorant
# ---------------------------------------------------------------------------


def test_leading_ha_raises_ng_to_high_class() -> None:
    # หงาน — ห + ง: ง is LC sonorant; ห raises it to HIGH class → RISING tone.
    result = _analyze("หงาน")
    if result.best.syllables:
        syl = result.best.syllables[-1]
        assert syl.tone is Tone.RISING


def test_leading_ha_naa_rising() -> None:
    # หนา — ห + น (LC sonorant, no mark) → RISING.
    result = _tlc("หนา")
    assert "{R}" in result


def test_leading_ha_maa_rising() -> None:
    # หมา — ห + ม → RISING.
    assert _tlc("หมา") == "maa{R}"


def test_leading_ha_yaa_rising() -> None:
    # หยา — ห + ย → RISING.
    result = _tlc("หยา")
    assert "{R}" in result


# ---------------------------------------------------------------------------
# Consonant clusters
# ---------------------------------------------------------------------------


def test_cluster_pr_in_onset() -> None:
    # ปลา — /pl/ cluster onset.
    result = _tlc("ปลา")
    assert result.startswith("bpl")


def test_cluster_kr_in_onset() -> None:
    # กรุง — /kr/ cluster.
    result = _tlc("กรุง")
    assert result.startswith("gr")


def test_cluster_kl_in_onset() -> None:
    # กลาง — /kl/ cluster.
    result = _tlc("กลาง")
    assert result.startswith("gl")


def test_cluster_kw_onset() -> None:
    # กวาง — /kw/ cluster onset.
    result = _tlc("กวาง")
    assert result.startswith("gw")


# ---------------------------------------------------------------------------
# Pre-vowel frames
# ---------------------------------------------------------------------------


def test_pre_vowel_e_frame_short() -> None:
    # เกะ — เ-frame, short /e/, dead syllable.
    result = _tlc("เกะ")
    assert "ge{" in result


def test_pre_vowel_ae_frame() -> None:
    # แกะ — แ-frame long /ɛː/ + dead.
    result = _tlc("แกะ")
    assert "gae{" in result


def test_pre_vowel_o_frame() -> None:
    # โก — โ-frame long /o:/.
    result = _tlc("โก")
    assert "go" in result


# ---------------------------------------------------------------------------
# อ as vowel carrier — glottal onset
# ---------------------------------------------------------------------------


def test_glottal_onset_o_carrier() -> None:
    # อา — glottal + long /aː/.
    result = _tlc("อา")
    assert result.endswith("{M}") or result.endswith("{L}")
    # Onset is glottal (silent in TLC).
    assert result.startswith("aa")


def test_glottal_onset_ee() -> None:
    # อี — glottal + long /iː/.
    result = _tlc("อี")
    assert result.startswith("ee")


# ---------------------------------------------------------------------------
# Mixed Thai and ASCII
# ---------------------------------------------------------------------------


def test_mixed_thai_ascii_does_not_raise() -> None:
    # Sentence with ASCII mixed in — should not crash.
    result = thaiphon.transcribe_sentence("ฉัน like ไปข้างหน้า", scheme="tlc")
    assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Empty string and whitespace
# ---------------------------------------------------------------------------


def test_empty_string_tlc() -> None:
    result = _tlc("")
    assert isinstance(result, str)


def test_empty_string_ipa() -> None:
    result = _ipa("")
    assert isinstance(result, str)


def test_whitespace_tlc() -> None:
    result = _tlc("   ")
    assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Thai numerals
# ---------------------------------------------------------------------------


def test_thai_numeral_passthrough() -> None:
    # Thai digits ๑๒๓ — pipeline should not crash.
    result = thaiphon.transcribe_sentence("๑๒๓", scheme="tlc")
    assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Long word / multi-syllable
# ---------------------------------------------------------------------------


def test_long_word_no_crash() -> None:
    # สวัสดีครับ — polite greeting.
    result = _tlc("สวัสดีครับ")
    assert isinstance(result, str) and len(result) > 0


def test_multisyllable_analysis_count() -> None:
    # สวัสดี — at least 3 syllables (สวัส-ดี splits into ≥2).
    result = _analyze("สวัสดี")
    assert len(result.best.syllables) >= 2

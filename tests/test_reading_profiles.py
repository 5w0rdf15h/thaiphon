"""Tests for reading profile behaviour.

The four supported profiles are:
  - everyday        — default; colloquial urban pronunciation.
  - careful_educated — more conservative; preserves more foreign phonology.
  - learned_full     — fully Indic/learned readings for Sanskrit-derived words.
  - etalon_compat    — dictionary-style citation; collapses all foreign codas.

This file focuses on words where profiles produce *distinct* outputs,
so that profile-selection bugs surface immediately. Each test pins a
representative case rather than attempting exhaustive rule coverage.
"""

from __future__ import annotations

import pytest

import thaiphon


# ---------------------------------------------------------------------------
# Default profile is "everyday"
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai",
    ["กา", "มา", "ขา", "ดี", "น้ำ"],
)
def test_omitting_profile_equals_everyday(thai: str) -> None:
    assert thaiphon.transcribe(thai, scheme="tlc") == thaiphon.transcribe(
        thai, scheme="tlc", profile="everyday"
    )


# ---------------------------------------------------------------------------
# Indic / Sanskrit words — learned_full gives the multi-syllable reading
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thai, everyday_tlc, learned_full_tlc",
    [
        # ภูมิ — everyday collapses to monosyllable; learned_full is 2-syll.
        ("ภูมิ", "phuum{M}", "phuu{M} mi{H}"),
        # พยาธิ — everyday is 2-syll collapsed; learned_full is 3-syll.
        ("พยาธิ", "pha{H} yaat{F}", "pha{H} yaa{M} thi{H}"),
        # กุฏิ — everyday monosyllable; learned_full 2-syll.
        ("กุฏิ", "goot{L}", "goot{L} dti{L}"),
    ],
)
def test_learned_full_vs_everyday(
    thai: str, everyday_tlc: str, learned_full_tlc: str
) -> None:
    assert thaiphon.transcribe(thai, scheme="tlc", profile="everyday") == everyday_tlc
    assert thaiphon.transcribe(thai, scheme="tlc", profile="learned_full") == learned_full_tlc


# ---------------------------------------------------------------------------
# Loanword coda preservation — careful_educated vs everyday vs etalon_compat
# ---------------------------------------------------------------------------


def test_lift_f_coda_everyday_preserves() -> None:
    # ลิฟต์ — /f/ is preserved under everyday (strong-preservation entry).
    result = thaiphon.transcribe("ลิฟต์", scheme="tlc", profile="everyday")
    assert "f" in result


def test_lift_f_coda_etalon_compat_collapses() -> None:
    # Under etalon_compat, preservation never fires → native /p̚/.
    result = thaiphon.transcribe("ลิฟต์", scheme="tlc", profile="etalon_compat")
    assert "f" not in result
    assert "p" in result


def test_email_l_coda_everyday_preserves() -> None:
    # อีเมล — /l/ coda preserved under everyday.
    result = thaiphon.transcribe("อีเมล", scheme="tlc", profile="everyday")
    assert result.endswith("l{L}") or result.endswith("l{M}") or "l{" in result


def test_email_l_coda_etalon_compat_collapses() -> None:
    result = thaiphon.transcribe("อีเมล", scheme="tlc", profile="etalon_compat")
    # Native coda for ล is /n/; preservation must not fire.
    assert "l{" not in result


def test_graf_f_everyday_collapses() -> None:
    # กราฟ — register-sensitive: everyday collapses to /p̚/.
    result = thaiphon.transcribe("กราฟ", scheme="tlc", profile="everyday")
    assert "f" not in result


def test_graf_f_careful_preserves() -> None:
    # กราฟ — careful_educated preserves /f/.
    result = thaiphon.transcribe("กราฟ", scheme="tlc", profile="careful_educated")
    assert "f" in result


# ---------------------------------------------------------------------------
# IPA profile parity — etalon_compat collapses; everyday may preserve
# ---------------------------------------------------------------------------


def test_ipa_lift_everyday_preserves_f() -> None:
    result = thaiphon.transcribe("ลิฟต์", scheme="ipa", profile="everyday")
    assert "f" in result


def test_ipa_lift_etalon_compat_collapses_f() -> None:
    result = thaiphon.transcribe("ลิฟต์", scheme="ipa", profile="etalon_compat")
    assert "f" not in result
    # Collapsed to unreleased /p̚/.
    assert "p̚" in result


# ---------------------------------------------------------------------------
# All profiles accepted (no ValueError) for arbitrary inputs
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "profile",
    ["everyday", "careful_educated", "learned_full", "etalon_compat"],
)
@pytest.mark.parametrize("thai", ["กา", "ภูมิ", "ลิฟต์"])
def test_all_profiles_no_error(thai: str, profile: str) -> None:
    result = thaiphon.transcribe(thai, scheme="tlc", profile=profile)
    assert isinstance(result, str) and len(result) > 0

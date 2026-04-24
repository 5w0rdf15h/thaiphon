"""Thai repetition mark, abbreviation mark, and numeral spelling expansion."""

from __future__ import annotations

import pytest

from thaiphon.normalization.expand import (
    expand,
    expand_lakkhangyao,
    expand_mai_yamok,
    expand_paiyannoi,
    spell_numerals,
)

MAI_YAMOK = "ๆ"
PAIYANNOI = "ฯ"
LAKKHANGYAO = "ฯลฯ"
AND_OTHERS = "และอื่นๆ"

DII = "ดี"  # ดี
REO = "เร็ว"  # เร็ว

SUN = "ศูนย์"
NUNG = "หนึ่ง"
KAO = "เก้า"


def test_mai_yamok_simple() -> None:
    assert expand_mai_yamok(DII + MAI_YAMOK) == DII + DII


def test_mai_yamok_with_longer_word() -> None:
    assert expand_mai_yamok(REO + MAI_YAMOK) == REO + REO


def test_mai_yamok_leading_character_is_noop() -> None:
    assert expand_mai_yamok(MAI_YAMOK) == MAI_YAMOK


def test_mai_yamok_in_sentence() -> None:
    text = "a " + DII + MAI_YAMOK + " b"
    assert expand_mai_yamok(text) == "a " + DII + DII + " b"


def test_paiyannoi_is_noop() -> None:
    krungthep = "กรุงเทพ"
    text = krungthep + PAIYANNOI
    assert expand_paiyannoi(text) == text
    assert expand_paiyannoi(PAIYANNOI) == PAIYANNOI


def test_lakkhangyao_exact() -> None:
    assert expand_lakkhangyao(LAKKHANGYAO) == AND_OTHERS


def test_lakkhangyao_embedded() -> None:
    text = "a " + LAKKHANGYAO + " b"
    assert expand_lakkhangyao(text) == "a " + AND_OTHERS + " b"


def test_single_digit_zero() -> None:
    assert spell_numerals("๐") == SUN


def test_single_digit_one() -> None:
    assert spell_numerals("๑") == NUNG


def test_single_digit_nine() -> None:
    assert spell_numerals("๙") == KAO


def test_multi_digit_run_unchanged() -> None:
    # Positional expansion for runs of two or more digits is not yet implemented;
    # runs pass through unchanged.
    text = "๑๒๓"
    assert spell_numerals(text) == text


def test_single_digit_between_text() -> None:
    text = "a ๐ b"
    assert spell_numerals(text) == f"a {SUN} b"


def test_expand_pipeline_empty() -> None:
    assert expand("") == ""


def test_expand_pipeline_ascii() -> None:
    assert expand("hello world") == "hello world"


def test_expand_pipeline_combined() -> None:
    text = DII + MAI_YAMOK + " " + LAKKHANGYAO
    # mai_yamok first → DII DII, then lakkhangyao → และอื่นๆ
    assert expand(text) == DII + DII + " " + AND_OTHERS


def test_expand_pipeline_paiyannoi_passes_through() -> None:
    text = "กรุงเทพ" + PAIYANNOI
    assert expand(text) == text


@pytest.mark.parametrize(
    "src,expected",
    [
        ("", ""),
        ("abc", "abc"),
        (DII + MAI_YAMOK, DII + DII),
        (LAKKHANGYAO, AND_OTHERS),
        ("๐", SUN),
        ("๑๒", "๑๒"),
    ],
)
def test_expand_parametrized(src: str, expected: str) -> None:
    assert expand(src) == expected

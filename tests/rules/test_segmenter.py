"""Longest-match segmenter tests."""

from __future__ import annotations

import pytest

from thaiphon.segmentation import segment


def test_empty_input() -> None:
    assert segment("") == ()


def test_returns_tuple() -> None:
    out = segment("ไม้")
    assert isinstance(out, tuple)


@pytest.mark.parametrize(
    "text,expected_contains",
    [
        # ไม้ + ได้ — two dictionary hits via length_overrides.
        ("ไม้ได้", ("ไม้", "ได้")),
        # ประโยชน์ is in silent_h lexicon.
        ("ประโยชน์", ("ประโยชน์",)),
        # ทราบ — thor lexicon.
        ("ทราบ", ("ทราบ",)),
        # ฤดู — ฤ lexicon.
        ("ฤดู", ("ฤดู",)),
        # ใจ — ai-20 lexicon.
        ("ใจ", ("ใจ",)),
    ],
)
def test_dictionary_hits(text: str, expected_contains: tuple[str, ...]) -> None:
    tokens = segment(text)
    for tok in expected_contains:
        assert tok in tokens, f"expected token {tok!r} in {tokens!r}"


def test_compound_water_ice_splits_water_word() -> None:
    # น้ำแข็ง — "น้ำ" is a dictionary entry; segmenter must split it off.
    tokens = segment("น้ำแข็ง")
    assert tokens[0] == "น้ำ"


def test_custom_dict() -> None:
    tokens = segment("กาแมว", custom_dict={"กา", "แมว"})
    assert tokens == ("กา", "แมว")


def test_non_thai_passes_through() -> None:
    tokens = segment("hello world")
    assert "hello" in tokens
    assert "world" in tokens


def test_unknown_thai_falls_back_to_tcc() -> None:
    # A string with no entry in the default trie. TCC splits into chunks.
    tokens = segment("กมล")  # none is a dictionary word
    # Must be >=1 token (TCC split) and all are non-empty.
    assert len(tokens) >= 1
    assert all(t for t in tokens)


def test_numerals_pass_through() -> None:
    # Arabic numerals match the nonthai regex.
    tokens = segment("12345")
    assert "12345" in tokens


def test_join_recovers_input_characters() -> None:
    text = "ไม่ได้"
    tokens = segment(text)
    # All original characters accounted for.
    assert "".join(tokens) == text


def test_multiple_dictionary_words_in_row() -> None:
    # ไม่ + ใช่ — both in lexicons.
    tokens = segment("ไม่ใช่")
    assert tokens == ("ไม่", "ใช่")


def test_idempotent_with_same_custom_dict() -> None:
    dct = {"กา"}
    assert segment("กา", custom_dict=dct) == segment("กา", custom_dict=dct)

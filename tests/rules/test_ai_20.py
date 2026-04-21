"""The 20 native Thai words written with ใ (Sara Ai Maimuan)."""

from __future__ import annotations

import pytest

from thaiphon.lexicons.ai_20 import AI_20_WORDS


@pytest.mark.parametrize(
    "word",
    [
        "ใกล้",
        "ใคร",
        "ใคร่",
        "ใจ",
        "ใช่",
        "ใช้",
        "ใด",
        "ใต้",
        "ใน",
        "ใบ",
        "ใบ้",
        "ใฝ่",
        "ใย",
        "สะใภ้",
        "ใส",
        "ใส่",
        "ให้",
        "ใหญ่",
        "ใหม่",
        "หลงใหล",
    ],
)
def test_all_20_words_present(word: str) -> None:
    assert word in AI_20_WORDS


def test_set_size_is_exactly_20() -> None:
    assert len(AI_20_WORDS) == 20


@pytest.mark.parametrize(
    "not_in_set",
    [
        "ไป",             # ไ-default
        "ไทย",
        "ไม้",
        "ไฟ",
        "ไอศกรีม",
    ],
)
def test_ai_variants_not_in_set(not_in_set: str) -> None:
    assert not_in_set not in AI_20_WORDS


def test_set_is_frozen() -> None:
    assert isinstance(AI_20_WORDS, frozenset)

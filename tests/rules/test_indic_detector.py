"""Orthographic Indic-candidate detector.

Words with strong Indic orthographic signals (distinctive letters such as
ฏ / ฐ / ฑ / ฒ / ณ, or characteristic learned endings) should activate the
productive learned-reading strategy. Everyday Thai words must not trigger it.
"""

from __future__ import annotations

import pytest

from thaiphon.lexicons.indic_detector import is_indic_candidate


# Positive cases: words with strong Indic orthographic signals.
@pytest.mark.parametrize(
    "word",
    [
        # Distinctly-Indic letters (ฏ / ฐ / ฑ / ฒ / ณ).
        "รัฐ",
        "สรณะ",
        "ทฤษฎี",
        "ปกิณก",
        "ราชภัฏ",
        "สมณ",
        "มรณ",
        "เลณ",
        "โสณ",
        "ทิฐิ",
        "คุณ",
        "ฏาร",
        "ฑาก",
        # Learned Indic endings.
        "หายนะ",
        "ภุมระ",
        "มูรติ",
        "ปกติ",
        "มัทวะ",
        "มัธยะ",
    ],
)
def test_detector_fires(word: str) -> None:
    assert is_indic_candidate(word) is True, f"expected detection: {word!r}"


# Negative cases: everyday Thai that must NOT trigger the Indic strategy.
@pytest.mark.parametrize(
    "word",
    [
        "บ้าน",
        "รัก",
        "ดี",
        "เขียน",
        "ขี้เกียจ",
        "โต๊ะ",   # has ◌ะ but too short and no Indic signal
        "กิน",
        "พี่",
        "น้ำ",
        "ถนน",   # H-leader shape (ถ + น + น)
        "ศรี",   # whitelisted
        "ศูนย์", # whitelisted
    ],
)
def test_detector_does_not_fire(word: str) -> None:
    assert is_indic_candidate(word) is False, f"false positive: {word!r}"

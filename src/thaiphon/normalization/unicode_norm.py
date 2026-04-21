"""M-004: Unicode normalization and Thai mark reordering."""

from __future__ import annotations

import unicodedata

from thaiphon.errors import NormalizationError

# Thai base consonants: U+0E01..U+0E2E (ก..ฮ).
_THAI_BASE_START = 0x0E01
_THAI_BASE_END = 0x0E2E

# Upper/lower vowel marks (M-004): U+0E31 (◌ั), U+0E34..U+0E3A (◌ิ..◌ฺ), U+0E47 (◌็).
_VOWEL_MARKS = frozenset(
    {0x0E31, 0x0E34, 0x0E35, 0x0E36, 0x0E37, 0x0E38, 0x0E39, 0x0E3A, 0x0E47}
)

# Tone marks: U+0E48..U+0E4B (◌่ ◌้ ◌๊ ◌๋).
_TONE_MARKS = frozenset({0x0E48, 0x0E49, 0x0E4A, 0x0E4B})

# Thanthakhat (killer mark) U+0E4C, nikhahit U+0E4D, yamakkan U+0E4E.
_KILLER_MARKS = frozenset({0x0E4C, 0x0E4D, 0x0E4E})

_VARIATION_SELECTORS_START = 0xFE00
_VARIATION_SELECTORS_END = 0xFE0F


def _is_thai_base(ch: str) -> bool:
    cp = ord(ch)
    return _THAI_BASE_START <= cp <= _THAI_BASE_END


def _mark_priority(ch: str) -> int:
    cp = ord(ch)
    if cp in _VOWEL_MARKS:
        return 0
    if cp in _TONE_MARKS:
        return 1
    if cp in _KILLER_MARKS:
        return 2
    return 3


def _strip_variation_selectors(text: str) -> str:
    return "".join(
        ch for ch in text
        if not (_VARIATION_SELECTORS_START <= ord(ch) <= _VARIATION_SELECTORS_END)
    )


def _is_reorderable_mark(ch: str) -> bool:
    cp = ord(ch)
    return cp in _VOWEL_MARKS or cp in _TONE_MARKS or cp in _KILLER_MARKS


def _reorder_marks(text: str) -> str:
    out: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        out.append(ch)
        if _is_thai_base(ch):
            j = i + 1
            marks: list[str] = []
            while j < n and _is_reorderable_mark(text[j]):
                marks.append(text[j])
                j += 1
            if marks:
                marks.sort(key=_mark_priority)
                out.extend(marks)
            i = j
            continue
        if (_is_reorderable_mark(ch) or unicodedata.combining(ch) != 0) and i == 0:
            raise NormalizationError(
                f"combining mark U+{ord(ch):04X} at string start without base"
            )
        i += 1
    return "".join(out)


def normalize(text: str) -> str:
    """Apply M-004: NFC + Thai mark canonical order + variation-selector strip."""
    if not text:
        return text
    text = _strip_variation_selectors(text)
    text = unicodedata.normalize("NFC", text)
    text = _reorder_marks(text)
    return text

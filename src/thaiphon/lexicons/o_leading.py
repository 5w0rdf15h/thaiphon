"""M-510: the closed 4-word อ-leading set."""

from __future__ import annotations

O_LEADING_WORDS: frozenset[str] = frozenset(
    {"\u0e2d\u0e22\u0e48\u0e32",       # อย่า
     "\u0e2d\u0e22\u0e39\u0e48",       # อยู่
     "\u0e2d\u0e22\u0e48\u0e32\u0e07", # อย่าง
     "\u0e2d\u0e22\u0e32\u0e01"}       # อยาก
)


def contains(word: str) -> bool:
    return word in O_LEADING_WORDS


__all__ = ["O_LEADING_WORDS", "contains"]

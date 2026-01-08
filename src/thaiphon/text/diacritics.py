from __future__ import annotations

MACRON = "\u0304"  # combining macron


def apply_macron(s: str, char_index: int = 0) -> str:
    """
    Add combining macron to s[char_index].
    Works for both Cyrillic and Latin symbols like ɔ/ə.
    """
    if not s:
        return s
    if char_index < 0 or char_index >= len(s):
        return s + MACRON
    return s[: char_index + 1] + MACRON + s[char_index + 1 :]

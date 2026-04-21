"""M-602 / M-602a / M-602b: special-vowel length overrides.

These words' vowels deviate from the productive length rule:

- M-602: a lexical set pronounced long in final / isolated position but
  short in non-final compound position. The engine currently renders the
  isolated form; we treat these as long.
- M-602a: เปล่า is always long.
- M-602b: ท่าน, อ้าย are always short despite ◌า.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

from thaiphon.model.enums import VowelLength

_OVERRIDES: dict[str, VowelLength] = {
    # M-602 — long in isolation / final.
    "\u0e19\u0e49\u0e33": VowelLength.LONG,                       # น้ำ
    "\u0e40\u0e0a\u0e49\u0e32": VowelLength.LONG,                 # เช้า
    "\u0e44\u0e21\u0e49": VowelLength.LONG,                       # ไม้
    "\u0e40\u0e17\u0e49\u0e32": VowelLength.LONG,                 # เท้า
    "\u0e40\u0e08\u0e49\u0e32": VowelLength.LONG,                 # เจ้า
    "\u0e44\u0e14\u0e49": VowelLength.LONG,                       # ได้
    "\u0e43\u0e0a\u0e49": VowelLength.LONG,                       # ใช้
    "\u0e40\u0e01\u0e49\u0e32": VowelLength.LONG,                 # เก้า
    "\u0e40\u0e1c\u0e32": VowelLength.LONG,                       # เผา
    "\u0e0a\u0e32\u0e27": VowelLength.LONG,                       # ชาว
    "\u0e2b\u0e21\u0e32\u0e22": VowelLength.LONG,                 # หมาย
    "\u0e17\u0e49\u0e32\u0e27": VowelLength.LONG,                 # ท้าว
    "\u0e19\u0e32\u0e22": VowelLength.LONG,                       # นาย
    "\u0e0a\u0e32\u0e22": VowelLength.LONG,                       # ชาย
    # M-602a — always long.
    "\u0e40\u0e1b\u0e25\u0e48\u0e32": VowelLength.LONG,           # เปล่า
    # M-602b — always short despite written long ◌า.
    "\u0e17\u0e48\u0e32\u0e19": VowelLength.SHORT,                # ท่าน
    "\u0e2d\u0e49\u0e32\u0e22": VowelLength.SHORT,                # อ้าย
}

# M-602 — revert to SHORT when not in compound-final position.
_COMPOUND_REVERTIBLE: frozenset[str] = frozenset(
    {
        "\u0e19\u0e49\u0e33",              # น้ำ
        "\u0e40\u0e0a\u0e49\u0e32",        # เช้า
        "\u0e44\u0e21\u0e49",              # ไม้
        "\u0e40\u0e17\u0e49\u0e32",        # เท้า
        "\u0e40\u0e08\u0e49\u0e32",        # เจ้า
        "\u0e44\u0e14\u0e49",              # ได้
        "\u0e43\u0e0a\u0e49",              # ใช้
    }
)

LENGTH_OVERRIDES: Mapping[str, VowelLength] = MappingProxyType(_OVERRIDES)


def lookup(word: str) -> VowelLength | None:
    return _OVERRIDES.get(word)


def is_compound_revertible(word: str) -> bool:
    """M-602: returns True if ``word`` should revert to SHORT in
    non-compound-final position. M-602a/602b words always apply, and
    therefore return False here."""
    return word in _COMPOUND_REVERTIBLE


__all__ = ["LENGTH_OVERRIDES", "is_compound_revertible", "lookup"]

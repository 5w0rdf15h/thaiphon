"""M-750: ทร three-way lexical readings.

- ``"s"``   — ทร reads as /s/ (silent ร). Most common.
- ``"thr"`` — ทร reads as a true /tʰr/ cluster (loanwords, rare).
- ``"taara"`` — ทร reads as the /tʰaː-rá-/ linking-syllable prefix.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Literal

ThorReading = Literal["s", "thr", "taara"]


_THOR: dict[str, ThorReading] = {
    # (a) /s/ — silent ร
    "\u0e17\u0e23\u0e32\u0e1a": "s",                                # ทราบ
    "\u0e17\u0e23\u0e32\u0e22": "s",                                # ทราย
    "\u0e17\u0e23\u0e07": "s",                                      # ทรง
    "\u0e17\u0e23\u0e31\u0e1e\u0e22\u0e4c": "s",                   # ทรัพย์
    "\u0e17\u0e23\u0e38\u0e14": "s",                                # ทรุด
    "\u0e17\u0e23\u0e32\u0e21": "s",                                # ทราม
    "\u0e42\u0e17\u0e23\u0e21": "s",                                # โทรม
    "\u0e17\u0e23\u0e27\u0e07": "s",                                # ทรวง
    "\u0e2d\u0e34\u0e19\u0e17\u0e23\u0e35\u0e22\u0e4c": "s",       # อินทรีย์
    "\u0e17\u0e23\u0e31\u0e1e\u0e22\u0e32\u0e01\u0e23": "s",       # ทรัพยากร
    # (b) /tʰr/ — loan clusters
    "\u0e17\u0e23\u0e2d\u0e21\u0e42\u0e1a\u0e19": "thr",           # ทรอมโบน
    "\u0e17\u0e23\u0e31\u0e21\u0e40\u0e1b\u0e47\u0e15": "thr",     # ทรัมเป็ต
    "\u0e17\u0e23\u0e32\u0e19\u0e0b\u0e34\u0e2a\u0e40\u0e15\u0e2d\u0e23\u0e4c": "thr",  # ทรานซิสเตอร์
    # (c) /tʰaː-rá-/ linking
    "\u0e17\u0e23\u0e1e\u0e34\u0e29": "taara",                     # ทรพิษ
    "\u0e17\u0e23\u0e1e\u0e35": "taara",                            # ทรพี
    "\u0e17\u0e23\u0e21\u0e32\u0e19": "taara",                     # ทรมาน
    "\u0e17\u0e23\u0e22\u0e28": "taara",                            # ทรยศ
    "\u0e17\u0e23\u0e30\u0e19\u0e07": "taara",                     # ทระนง
    "\u0e17\u0e23\u0e0a\u0e19": "taara",                            # ทรชน
    "\u0e17\u0e23\u0e23\u0e32\u0e0a": "taara",                     # ทรราช
    "\u0e17\u0e23\u0e2b\u0e27\u0e25": "taara",                     # ทรหวล
    "\u0e17\u0e23\u0e2b\u0e36\u0e07": "taara",                     # ทรหึง
}

THOR_READINGS: Mapping[str, ThorReading] = MappingProxyType(_THOR)


# Mid-word ทร substitutions: words containing ทร as a morpheme boundary
# where it's read as /s/. The key is the surface Thai spelling; the value
# is the substring replacement to apply before derivation.
_MID_WORD_THOR: dict[str, tuple[str, str]] = {
    # "อินทรีย์" — ท + ร in the middle is read /s/; substitute ทร → ซ to
    # steer derivation toward /in-sii/.
    "\u0e2d\u0e34\u0e19\u0e17\u0e23\u0e35\u0e22\u0e4c": ("\u0e17\u0e23", "\u0e0b"),
    # "จันทร์" — silent ทร after วรรณยุกต์-carrying จัน; substitute ทร → ∅.
    "\u0e08\u0e31\u0e19\u0e17\u0e23\u0e4c": ("\u0e17\u0e23\u0e4c", ""),
}

MID_WORD_THOR: Mapping[str, tuple[str, str]] = MappingProxyType(_MID_WORD_THOR)


def lookup(word: str) -> ThorReading | None:
    return _THOR.get(word)


def rewrite_thor_mid(word: str) -> str:
    """Apply any registered mid-word ทร substitution; return ``word``
    unchanged when no entry matches."""
    rule = _MID_WORD_THOR.get(word)
    if rule is None:
        return word
    old, new = rule
    return word.replace(old, new, 1)


__all__ = [
    "MID_WORD_THOR",
    "THOR_READINGS",
    "ThorReading",
    "lookup",
    "rewrite_thor_mid",
]

"""M-730: ฤ / ฤๅ four-way lexical readings.

- ``"rii"`` — ฤ as /rɯː/ or /rɯ/ (default; initial position).
- ``"ri"``  — ฤ as /ri/ (short; in clusters / Sanskrit contexts).
- ``"rer"`` — ฤ as /rɤː/ (very rare; the ฤกษ์ sub-class).
- ``"rue"`` — ฤๅ as /rɯːə/ (long composite, ฤๅษี).
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Literal

RueReading = Literal["rii", "ri", "rer", "rue"]


_RUE: dict[str, RueReading] = {
    # Reading 1: /rii/ (some schemes render a short /rɯ/)
    "\u0e24\u0e14\u0e39": "rii",                                  # ฤดู
    "\u0e24\u0e14\u0e35": "rii",                                  # ฤดี
    "\u0e24\u0e29\u0e35": "rii",                                  # ฤษี
    "\u0e24\u0e0a\u0e32": "rii",                                  # ฤชา
    "\u0e24\u0e17\u0e31\u0e22": "rii",                            # ฤทัย
    "\u0e1e\u0e24\u0e29\u0e20\u0e32\u0e04\u0e21": "rii",         # พฤษภาคม
    "\u0e1e\u0e24\u0e28\u0e08\u0e34\u0e01\u0e32\u0e22\u0e19": "rii",   # พฤศจิกายน
    "\u0e1e\u0e24\u0e01\u0e29\u0e32": "rii",                      # พฤกษา
    "\u0e1e\u0e24\u0e2b\u0e31\u0e2a\u0e1a\u0e14\u0e35": "rii",   # พฤหัสบดี
    # Reading 2: /ri/
    "\u0e24\u0e17\u0e18\u0e34\u0e4c": "ri",                       # ฤทธิ์
    "\u0e2d\u0e31\u0e07\u0e01\u0e24\u0e29": "ri",                 # อังกฤษ
    "\u0e17\u0e24\u0e29\u0e0e\u0e35": "ri",                       # ทฤษฎี
    "\u0e01\u0e24\u0e29\u0e13\u0e4c": "ri",                       # กฤษณ์
    # Reading 3: /rɤː/
    "\u0e24\u0e01\u0e29\u0e4c": "rer",                            # ฤกษ์
    # Reading 4: /rɯːə/ via ฤๅ
    "\u0e24\u0e45\u0e29\u0e35": "rue",                            # ฤๅษี
    "\u0e24\u0e45\u0e17\u0e31\u0e22": "rue",                      # ฤๅทัย
}

RUE_READINGS: Mapping[str, RueReading] = MappingProxyType(_RUE)


def lookup(word: str) -> RueReading | None:
    return _RUE.get(word)


__all__ = ["RUE_READINGS", "RueReading", "lookup"]

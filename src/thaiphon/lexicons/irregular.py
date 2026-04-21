"""M-720, M-700f/g/h — lexicalized irregular readings.

Two flavours:

- ``IRREGULAR_WORDS``: word → orthographic respelling tuple (derivable).
- ``IRREGULAR_SYLLABLES``: word → pre-built ``Syllable`` tuple used when
  the word's reading cannot be reproduced through the derivation pipeline.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

from thaiphon.model.enums import (
    EffectiveClass,
    SyllableType,
    Tone,
    ToneMark,
    VowelLength,
)
from thaiphon.model.phoneme import Phoneme
from thaiphon.model.syllable import Syllable

# Each entry maps a full orthographic word to a tuple of phonemic-syllable
# respellings the reader can derive cleanly.
_IRREGULAR: dict[str, tuple[str, ...]] = {
    # M-700f — silent final vowels without ◌์.
    "\u0e40\u0e2b\u0e15\u0e38": ("\u0e40\u0e2b\u0e15",),           # เหตุ → เหต
    "\u0e18\u0e32\u0e15\u0e38": ("\u0e18\u0e32\u0e15",),           # ธาตุ → ธาต
    "\u0e0a\u0e32\u0e15\u0e34": ("\u0e0a\u0e32\u0e15",),           # ชาติ → ชาต
    # M-700g — silent final ร without ◌์.
    "\u0e08\u0e31\u0e01\u0e23": ("\u0e08\u0e31\u0e01",),           # จักร → จัก
    "\u0e1a\u0e38\u0e15\u0e23": ("\u0e1a\u0e38\u0e15",),           # บุตร → บุต
    "\u0e21\u0e34\u0e15\u0e23": ("\u0e21\u0e34\u0e15",),           # มิตร → มิต
    "\u0e2a\u0e21\u0e31\u0e04\u0e23": ("\u0e2a\u0e21\u0e31\u0e04",),  # สมัคร → สมัค
    "\u0e40\u0e1e\u0e0a\u0e23": ("\u0e40\u0e1e\u0e0a",),           # เพชร → เพช
}


def _kaw_falling() -> tuple[Syllable, ...]:
    # M-720 — ก็ /kɔ̂ː/: hand-built syllable, long open /ɔ/ with falling tone.
    return (
        Syllable(
            onset=Phoneme("k"),
            vowel=Phoneme("ɔ"),
            vowel_length=VowelLength.LONG,
            coda=None,
            tone=Tone.FALLING,
            tone_mark=ToneMark.NONE,
            effective_class=EffectiveClass.MID,
            syllable_type=SyllableType.LIVE,
            raw="\u0e01\u0e47",
        ),
    )


_IRREGULAR_SYLLABLES: dict[str, tuple[Syllable, ...]] = {
    "\u0e01\u0e47": _kaw_falling(),  # ก็
}


IRREGULAR_WORDS: Mapping[str, tuple[str, ...]] = MappingProxyType(_IRREGULAR)
IRREGULAR_SYLLABLES: Mapping[str, tuple[Syllable, ...]] = MappingProxyType(
    _IRREGULAR_SYLLABLES
)


def lookup(word: str) -> tuple[str, ...] | None:
    return _IRREGULAR.get(word)


def lookup_syllables(word: str) -> tuple[Syllable, ...] | None:
    return _IRREGULAR_SYLLABLES.get(word)


__all__ = [
    "IRREGULAR_SYLLABLES",
    "IRREGULAR_WORDS",
    "lookup",
    "lookup_syllables",
]

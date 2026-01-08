from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

"""
Core phonological model for Thai.

Note on naming:
- "RTL" in this project refers to the Thai language school (RTL School),
  not to "right-to-left" text direction.
"""


class Tone(Enum):
    MID = "mid"
    LOW = "low"
    FALLING = "falling"
    HIGH = "high"
    RISING = "rising"


class VowelLength(Enum):
    SHORT = "short"
    LONG = "long"


class FinalType(Enum):
    NONE = "none"  # open syllable (or pseudo-open handled explicitly)
    SONORANT = "sonorant"  # m n ŋ w j
    STOP = "stop"  # p t k
    GLOTTAL = "glottal"  # ʔ (pseudo-open etc.)


@dataclass(frozen=True)
class Onset:
    c1: str  # canonical consonant phoneme symbol (e.g. "k", "pʰ", "tɕ")
    c2: Optional[str] = None  # e.g. "r", "l", "w"


@dataclass(frozen=True)
class Vowel:
    nucleus: str  # canonical vowel phoneme symbol (e.g. "a", "ɯ", "ɔ", "ə", "ia")
    length: VowelLength
    offglide: Optional[str] = None  # "j" or "w" if needed


@dataclass(frozen=True)
class Coda:
    phoneme: Optional[
        str
    ]  # "m","n","ŋ","p","t","k","j","w","ʔ" (glottal stop), or None
    final_type: FinalType


@dataclass(frozen=True)
class Syllable:
    onset: Onset
    vowel: Vowel
    coda: Coda
    tone: Tone

    # Debug/trace fields (useful for RTL rules & future overrides)
    raw: Optional[str] = None
    inserted_vowel: bool = False
    cancelled: bool = False


@dataclass(frozen=True)
class PhonologicalWord:
    syllables: tuple[Syllable, ...]

    def __iter__(self):
        return iter(self.syllables)

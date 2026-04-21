"""Enumerations for the Thai phonological model."""

from __future__ import annotations

from enum import Enum, unique


@unique
class ConsonantClass(str, Enum):
    """Traditional 3-way consonant class. LC is split further into LCP/LCS."""

    HIGH = "HIGH"
    MID = "MID"
    LOW_PAIRED = "LOW_PAIRED"  # LCP — has an HC counterpart
    LOW_SONORANT = "LOW_SONORANT"  # LCS — no HC counterpart


@unique
class EffectiveClass(str, Enum):
    """3-way class used as input to the tone matrix after any ห/อ-leading."""

    HIGH = "HIGH"
    MID = "MID"
    LOW = "LOW"


@unique
class Tone(str, Enum):
    MID = "MID"
    LOW = "LOW"
    FALLING = "FALLING"
    HIGH = "HIGH"
    RISING = "RISING"


@unique
class VowelLength(str, Enum):
    SHORT = "SHORT"
    LONG = "LONG"


@unique
class SyllableType(str, Enum):
    """Live vs dead syllable classification per M-303."""

    LIVE = "LIVE"
    DEAD = "DEAD"


@unique
class ToneMark(str, Enum):
    NONE = "NONE"
    MAI_EK = "MAI_EK"  # ◌่
    MAI_THO = "MAI_THO"  # ◌้
    MAI_TRI = "MAI_TRI"  # ◌๊
    MAI_JATTAWA = "MAI_JATTAWA"  # ◌๋

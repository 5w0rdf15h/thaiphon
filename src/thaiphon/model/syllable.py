"""Syllable value object."""

from __future__ import annotations

from dataclasses import dataclass, field

from thaiphon.model.enums import EffectiveClass, SyllableType, Tone, ToneMark, VowelLength
from thaiphon.model.phoneme import Cluster, Phoneme


@dataclass(frozen=True, slots=True)
class Syllable:
    """A single spec-aligned syllable in the phonological representation."""

    onset: Phoneme | Cluster | None
    vowel: Phoneme
    vowel_length: VowelLength
    coda: Phoneme | None
    tone: Tone
    tone_mark: ToneMark = ToneMark.NONE
    effective_class: EffectiveClass = EffectiveClass.MID
    syllable_type: SyllableType = SyllableType.LIVE
    raw: str = ""
    inserted_vowel: bool = False
    cancelled: bool = False
    notes: tuple[str, ...] = field(default_factory=tuple)

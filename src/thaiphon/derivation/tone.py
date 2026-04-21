"""Thin typed adapter over the M-410 tone matrix."""

from __future__ import annotations

from thaiphon.model.enums import EffectiveClass, SyllableType, Tone, ToneMark, VowelLength
from thaiphon.tables import tone_matrix


def assign_tone(
    effective_class: EffectiveClass,
    syllable_type: SyllableType,
    vowel_length: VowelLength,
    tone_mark: ToneMark,
) -> Tone:
    return tone_matrix.lookup(effective_class, syllable_type, vowel_length, tone_mark)


__all__ = ["assign_tone"]

"""M-303: live/dead syllable classification."""

from __future__ import annotations

from thaiphon.derivation.coda import FinalAnalysis
from thaiphon.model.enums import SyllableType, VowelLength


def classify(
    vowel_length: VowelLength,
    coda: FinalAnalysis,
    has_written_vowel: bool = True,
) -> SyllableType:
    """Classify a syllable as LIVE or DEAD.

    LIVE: long open vowel, sonorant-final syllable (/m n ŋ w j/),
          or special vowels that are always LIVE regardless of surface form.
    DEAD: stop-final syllable (/p̚ t̚ k̚/) or short open vowel.
    """
    if coda.syllable_type_hint is not None:
        return coda.syllable_type_hint
    # No coda → determined by vowel length.
    if vowel_length is VowelLength.LONG:
        return SyllableType.LIVE
    return SyllableType.DEAD


__all__ = ["classify"]

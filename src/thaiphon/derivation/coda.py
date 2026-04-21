"""Coda resolution via the M-301 26→6 collapse."""

from __future__ import annotations

from dataclasses import dataclass

from thaiphon.model.enums import SyllableType
from thaiphon.model.phoneme import Phoneme
from thaiphon.tables import final_collapse

# Stops → DEAD; sonorants/semi-vowels → LIVE.
_STOPS: frozenset[str] = frozenset({"p̚", "t̚", "k̚"})


@dataclass(frozen=True, slots=True)
class FinalAnalysis:
    phoneme: Phoneme | None
    syllable_type_hint: SyllableType | None


def resolve_coda(final_char: str | None) -> FinalAnalysis:
    if final_char is None or final_char == "":
        return FinalAnalysis(phoneme=None, syllable_type_hint=None)
    ipa = final_collapse.collapse(final_char)
    if ipa in _STOPS:
        return FinalAnalysis(
            phoneme=Phoneme(ipa),
            syllable_type_hint=SyllableType.DEAD,
        )
    return FinalAnalysis(
        phoneme=Phoneme(ipa, is_sonorant=True),
        syllable_type_hint=SyllableType.LIVE,
    )


__all__ = ["FinalAnalysis", "resolve_coda"]

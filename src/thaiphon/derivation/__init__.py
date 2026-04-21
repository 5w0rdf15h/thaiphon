"""Pure-function derivation primitives: onset, vowel, coda, type, tone."""

from thaiphon.derivation.coda import FinalAnalysis, resolve_coda
from thaiphon.derivation.onset import OnsetAnalysis, resolve_onset
from thaiphon.derivation.syllable_type import classify
from thaiphon.derivation.tone import assign_tone
from thaiphon.derivation.vowel import VowelAnalysis, resolve_vowel

__all__ = [
    "FinalAnalysis",
    "OnsetAnalysis",
    "VowelAnalysis",
    "assign_tone",
    "classify",
    "resolve_coda",
    "resolve_onset",
    "resolve_vowel",
]

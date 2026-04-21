"""Onset resolution: class, ห/อ-leading, clusters, vowel-initial."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from thaiphon.lexicons import o_leading as o_leading_lex
from thaiphon.model.enums import ConsonantClass, EffectiveClass
from thaiphon.model.letters import HO_HIP, O_ANG, YO_YAK
from thaiphon.model.phoneme import Cluster, Phoneme
from thaiphon.tables import clusters as clusters_tbl
from thaiphon.tables import consonants as consonants_tbl
from thaiphon.tables.clusters import RARE_CLUSTERS as _RARE_CLUSTERS
from thaiphon.tables.leaders import H_LEADABLE_SONORANTS as _H_LEADABLE

# M-510: hard-coded 4-word อ-leading set (full forms).
_O_LEADING_WORDS: frozenset[str] = o_leading_lex.O_LEADING_WORDS


@dataclass(frozen=True, slots=True)
class OnsetAnalysis:
    onset: Phoneme | Cluster | None
    effective_class: EffectiveClass
    consumed: int
    leading_silent: str | None = None


def _effective(cls: ConsonantClass) -> EffectiveClass:
    if cls is ConsonantClass.HIGH:
        return EffectiveClass.HIGH
    if cls is ConsonantClass.MID:
        return EffectiveClass.MID
    return EffectiveClass.LOW


def _phoneme_for(letter: str, as_onset: bool = True) -> Phoneme:
    info = consonants_tbl.lookup(letter)
    ipa = info.onset_ipa if as_onset else (info.coda_ipa or info.onset_ipa)
    aspirated = ipa.endswith("ʰ")
    sonorant = info.cls is ConsonantClass.LOW_SONORANT
    return Phoneme(ipa, is_aspirated=aspirated, is_sonorant=sonorant)


def resolve_onset(chars: Sequence[str]) -> OnsetAnalysis:
    """Resolve the onset from leading characters of a syllable.

    `chars` is the raw character sequence starting at a consonant (or vowel
    prefix already stripped). Returns a small analysis: onset value, effective
    class for tone lookup, number of chars consumed, and any silent leader.
    """
    if not chars:
        # Empty onset — implicit อ at word start.
        return OnsetAnalysis(
            onset=Phoneme("ʔ"),
            effective_class=EffectiveClass.MID,
            consumed=0,
        )

    first = chars[0]

    # Vowel-initial: leading char is a vowel mark / prevowel → implicit glottal.
    if first not in consonants_tbl.CONSONANTS:
        return OnsetAnalysis(
            onset=Phoneme("ʔ"),
            effective_class=EffectiveClass.MID,
            consumed=0,
        )

    # M-510: อ-leading check against the 4-word closed set.
    if first == O_ANG and len(chars) >= 2 and chars[1] == YO_YAK:
        full = "".join(chars)
        if full in _O_LEADING_WORDS:
            return OnsetAnalysis(
                onset=Phoneme("j", is_sonorant=True),
                effective_class=EffectiveClass.MID,
                consumed=2,
                leading_silent=O_ANG,
            )
        # Fall through to standard handling.

    # M-500: ห-leading.
    if first == HO_HIP and len(chars) >= 2 and chars[1] in _H_LEADABLE:
        second = chars[1]
        return OnsetAnalysis(
            onset=_phoneme_for(second),
            effective_class=EffectiveClass.HIGH,
            consumed=2,
            leading_silent=HO_HIP,
        )

    # M-520: true clusters (only when a non-consonant follows, i.e. no third
    # consonant that would turn this into onset+initial-consonant pair).
    if len(chars) >= 2 and chars[1] in consonants_tbl.CONSONANTS:
        second = chars[1]
        if (
            clusters_tbl.is_cluster(first, second)
            and (first, second) not in _RARE_CLUSTERS
        ):
            info1 = consonants_tbl.lookup(first)
            p1 = _phoneme_for(first)
            p2 = _phoneme_for(second)
            return OnsetAnalysis(
                onset=Cluster(p1, p2),
                effective_class=_effective(info1.cls),
                consumed=2,
            )

    # Single consonant onset.
    info = consonants_tbl.lookup(first)
    return OnsetAnalysis(
        onset=_phoneme_for(first),
        effective_class=_effective(info.cls),
        consumed=1,
    )


__all__ = ["OnsetAnalysis", "resolve_onset"]

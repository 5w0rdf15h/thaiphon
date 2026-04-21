"""Candidate generator: dispatches to strategies and flattens output."""

from __future__ import annotations

from collections.abc import Sequence

from thaiphon.model.candidate import SyllabificationCandidate
from thaiphon.syllabification.strategies import (
    AoCarrierStrategy,
    ClusterStrategy,
    CompositeVowelFrameStrategy,
    DFStrategy,
    HLeadingStrategy,
    IndicLearnedStrategy,
    LinkingStrategy,
    MergeStrategy,
    OLeadingStrategy,
    PairSyllableStrategy,
    PreVowelHopStrategy,
    SplitStrategy,
    Strategy,
)

_DEFAULT_FANOUT_CAP = 16


def default_strategies() -> tuple[Strategy, ...]:
    return (
        OLeadingStrategy(),
        HLeadingStrategy(),
        PreVowelHopStrategy(),
        # TRUE CLUSTERS OVERRIDE EVERYTHING (per second-pass diagnostic).
        # ขว / คว / กว and other valid CC onsets must be recognised before
        # composite-vowel-frame detection so words like ``ขวาน``, ``ควาย``,
        # ``กว้าง`` keep their /kʰw/ or /kw/ onset and are never routed to
        # the ``ัว`` /uːə/ centring-diphthong allomorph.
        ClusterStrategy(),
        # Composite-vowel frame recognition sits below cluster detection for
        # the reason above, but above the generic merge/linking strategies
        # so a ย/ว/อ that belongs to a centring-diphthong nucleus cannot be
        # mis-assigned as a free coda or a split-out syllable (R-CD-001..005).
        CompositeVowelFrameStrategy(),
        AoCarrierStrategy(),
        # Productive Indic learned-reading. Fires only when the
        # detector flags the raw word as an Indic candidate not resolved by
        # any earlier lexicon. Sits above MergeStrategy so the non-folded
        # reading wins over native coda-folding for Indic inputs.
        IndicLearnedStrategy(),
        MergeStrategy(),
        PairSyllableStrategy(),
        DFStrategy(),
        LinkingStrategy(),
        SplitStrategy(),
    )


class CandidateGenerator:
    __slots__ = ("_strategies", "_cap")

    def __init__(
        self,
        strategies: Sequence[Strategy] | None = None,
        *,
        fanout_cap: int = _DEFAULT_FANOUT_CAP,
    ) -> None:
        self._strategies: tuple[Strategy, ...] = (
            tuple(strategies) if strategies is not None else default_strategies()
        )
        self._cap = fanout_cap

    def generate(
        self, tokens: Sequence[str]
    ) -> tuple[SyllabificationCandidate, ...]:
        out: list[SyllabificationCandidate] = []
        seen: set[tuple[str, ...]] = set()
        for strategy in self._strategies:
            for cand in strategy.generate(tokens):
                key = cand.segments
                if key in seen:
                    continue
                seen.add(key)
                out.append(cand)
                if len(out) >= self._cap:
                    return tuple(out)
        return tuple(out)


__all__ = ["CandidateGenerator", "default_strategies"]

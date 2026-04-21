"""Candidate ranker.

Score = 0.5 + 0.3 * lexicon_confirmed + 0.1 * strategy_baseline
        − 0.05 * fallback_count.

Here ``lexicon_confirmed`` is always False; lexicon confirmation is
wired in the pipeline by writing ``score += 0.3`` before calling
``rank``.
"""

from __future__ import annotations

from collections.abc import Sequence

from thaiphon.model.candidate import SyllabificationCandidate


class CandidateRanker:
    __slots__ = ()

    def rank(
        self, candidates: Sequence[SyllabificationCandidate]
    ) -> tuple[SyllabificationCandidate, ...]:
        return tuple(sorted(candidates, key=lambda c: c.score, reverse=True))

    def should_prune(
        self,
        partial: SyllabificationCandidate,
        best: SyllabificationCandidate | None,
    ) -> bool:
        if best is None:
            return False
        return partial.score + 0.3 < best.score


__all__ = ["CandidateRanker"]

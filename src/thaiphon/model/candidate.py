"""Syllabification candidates and analysis results."""

from __future__ import annotations

from dataclasses import dataclass, field

from thaiphon.lexicons.loanword_detector import LoanAnalysis
from thaiphon.model.word import PhonologicalWord


@dataclass(frozen=True, slots=True)
class SyllabificationCandidate:
    """One possible segmentation of an input into orthographic syllables."""

    segments: tuple[str, ...]
    strategy: str  # "split" | "cluster" | "o_leading" | "h_leading" | "df" | "linking"
    score: float = 0.0
    notes: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class AnalysisResult:
    """Result of running the pipeline: best word plus alternatives.

    The optional ``loan_analysis`` field carries the foreignness detector's
    output when the runner ran it. It is observational only: the pipeline's
    derivation, tone assignment, and coda decisions do not consult it.
    Callers may inspect it for logging, telemetry, or downstream gating.
    """

    best: PhonologicalWord
    alternatives: tuple[PhonologicalWord, ...] = field(default_factory=tuple)
    source: str = "derivation"
    raw: str = ""
    loan_analysis: LoanAnalysis | None = None

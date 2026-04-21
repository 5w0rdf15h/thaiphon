"""Phoneme and cluster value objects."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Phoneme:
    """A single IPA phoneme. `symbol` is the broad IPA transcription."""

    symbol: str
    is_aspirated: bool = False
    is_sonorant: bool = False


@dataclass(frozen=True, slots=True)
class Cluster:
    """An onset cluster of two phonemes (true CC onset)."""

    first: Phoneme
    second: Phoneme

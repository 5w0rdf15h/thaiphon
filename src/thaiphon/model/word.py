"""PhonologicalWord: the universal intermediate representation."""

from __future__ import annotations

from dataclasses import dataclass, field

from thaiphon.model.syllable import Syllable


@dataclass(frozen=True, slots=True)
class PhonologicalWord:
    """Universal intermediate between orthography and any renderer."""

    syllables: tuple[Syllable, ...]
    morpheme_boundaries: tuple[int, ...] = field(default_factory=tuple)
    confidence: float = 1.0
    source: str = "derivation"  # "lexicon" | "derivation" | "fallback"
    raw: str = ""

    def __iter__(self):  # type: ignore[no-untyped-def]
        return iter(self.syllables)

    def __len__(self) -> int:
        return len(self.syllables)

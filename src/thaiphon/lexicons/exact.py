"""Exact-form lookup backed by optional thaiphon_data_* packages.

If an importable `thaiphon_data_volubilis` (or similar) is installed, its
`ENTRIES` mapping is used as the authoritative lexicon. Otherwise the stage
no-ops and the pipeline falls through to rule-based analysis.
"""

from __future__ import annotations

import functools
from collections.abc import Mapping
from types import MappingProxyType

from thaiphon.model.word import PhonologicalWord


@functools.cache
def entries() -> Mapping[str, PhonologicalWord]:
    try:
        from thaiphon_data_volubilis import ENTRIES  # type: ignore[import-not-found]
    except ImportError:
        return MappingProxyType({})
    result: Mapping[str, PhonologicalWord] = ENTRIES
    return result


def lookup(word: str) -> PhonologicalWord | None:
    return entries().get(word)


__all__ = ["entries", "lookup"]

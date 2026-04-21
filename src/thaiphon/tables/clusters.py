"""M-520: the 16 true Thai consonant clusters (อักษรควบแท้)."""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

# Closed list per M-520. C1 ∈ {ก ข ค ต ป ผ พ}, C2 ∈ {ร ล ว}.
# (ผร) is included for structural completeness though near-empty in modern use.
_CLUSTERS: frozenset[tuple[str, str]] = frozenset(
    {
        ("ก", "ร"),
        ("ก", "ล"),
        ("ก", "ว"),
        ("ข", "ร"),
        ("ข", "ล"),
        ("ข", "ว"),
        ("ค", "ร"),
        ("ค", "ล"),
        ("ค", "ว"),
        ("ต", "ร"),
        ("ป", "ร"),
        ("ป", "ล"),
        ("ผ", "ร"),
        ("ผ", "ล"),
        ("พ", "ร"),
        ("พ", "ล"),
    }
)

CLUSTERS: frozenset[tuple[str, str]] = _CLUSTERS

# M-520 rare-cluster exclusion: (ผ, ร) and (ผ, ล) sit in the table for
# orthographic completeness but in practice these sequences almost always
# signal aksornam / hidden-vowel patterns rather than true clusters.
RARE_CLUSTERS: frozenset[tuple[str, str]] = frozenset(
    {("\u0e1c", "\u0e23"), ("\u0e1c", "\u0e25")}
)


def _build_by_first() -> dict[str, frozenset[str]]:
    buckets: dict[str, set[str]] = {}
    for c1, c2 in _CLUSTERS:
        buckets.setdefault(c1, set()).add(c2)
    return {k: frozenset(v) for k, v in buckets.items()}


BY_FIRST: Mapping[str, frozenset[str]] = MappingProxyType(_build_by_first())


def is_cluster(first: str, second: str) -> bool:
    return (first, second) in _CLUSTERS

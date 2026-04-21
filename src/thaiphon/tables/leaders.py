"""M-500: the 8 sonorants that follow a silent ห leader letter."""

from __future__ import annotations

# The ห-leadable sonorants — onset class is promoted to HC when ห precedes
# any of these without an intervening vowel.
H_LEADABLE_SONORANTS: frozenset[str] = frozenset(
    {"ม", "น", "ง", "ญ", "ย", "ร", "ล", "ว"}
)


__all__ = ["H_LEADABLE_SONORANTS"]

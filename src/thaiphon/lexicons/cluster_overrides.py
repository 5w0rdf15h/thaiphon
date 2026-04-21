"""Cluster disambiguation lexicons.

Thai orthographic sequences ``ขว``, ``คว``, ``กว`` can be either:

- A true consonant cluster /kʰw/ or /kw/ (e.g. ``ความ`` = /kʰwaːm/), or
- An อักษรนำ-style leading-consonant pattern where the first letter takes
  an inserted /u/ vowel before the second (e.g. ``ขวด`` = /kʰùːət/ via
  /kʰu-wòt/-style reading).

The pipeline consults these sets to pick the right reading; tokens not in
either set fall back to the generic cluster logic in
:mod:`thaiphon.syllabification.strategies`.
"""

from __future__ import annotations

# Words where ขว / คว / กว / ฟว is read as a true /CwV/ cluster.
TRUE_CLUSTER_WORDS: frozenset[str] = frozenset(
    {
        "\u0e04\u0e27\u0e32\u0e21",               # ความ
        "\u0e04\u0e27\u0e32\u0e22",               # ควาย
        "\u0e01\u0e27\u0e48\u0e32",               # กว่า
        "\u0e02\u0e27\u0e31\u0e0d",               # ขวัญ
        "\u0e01\u0e27\u0e32\u0e07",               # กวาง
        "\u0e04\u0e27\u0e31\u0e19",               # ควัน
        "\u0e04\u0e27\u0e1a\u0e04\u0e38\u0e21",  # ควบคุม
        "\u0e01\u0e27\u0e32\u0e14",               # กวาด
        "\u0e02\u0e27\u0e32",                     # ขวา
        "\u0e02\u0e27\u0e32\u0e07",               # ขวาง
        "\u0e01\u0e27\u0e19",                     # กวน
        "\u0e04\u0e27\u0e23",                     # ควร
        "\u0e02\u0e27\u0e35\u0e14",               # ขวีด (rare)
    }
)

# Words where the same written ขว / คว shape reads with an inserted /u/
# vowel between the two consonants (อักษรนำ-style). These are the
# lexicalised exceptions — the default for ขว / คว / กว is TRUE CLUSTER
# per the second-pass diagnostic (R-UUA-001 Case A).
#
# Audited against the Volubilis etalon:
#   * ``ขวด``   → ``khuaat{L}``         — aksornam, keep.
#   * ``ขวาน``  → ``khwaan{R}``         — CLUSTER, removed.
#   * ``ขวาก``  → ``khwaak{L}``         — CLUSTER, removed.
#   * ``ขวากหนาม`` → ``khwaak{L} naam{R}`` — CLUSTER, removed.
#   * ``ขวนขวาย`` → first syl aksornam, second syl CLUSTER — left out of
#     this simple ``C+ว+C`` template; compound words are better handled
#     by the exact-form lexicon and per-segment rule engine.
INSERT_U_WORDS: frozenset[str] = frozenset(
    {
        "\u0e02\u0e27\u0e14",                                 # ขวด
    }
)


def is_true_cluster(word: str) -> bool:
    return word in TRUE_CLUSTER_WORDS


def is_insert_u(word: str) -> bool:
    return word in INSERT_U_WORDS


__all__ = [
    "INSERT_U_WORDS",
    "TRUE_CLUSTER_WORDS",
    "is_insert_u",
    "is_true_cluster",
]

"""M-603: the 20 native Thai words written with ใ (sara ai mai muan).

All other phonological /aj/ words use ไ (sara ai mai malai). This set is
closed; loanwords are always spelled with ไ.
"""

from __future__ import annotations

AI_20_WORDS: frozenset[str] = frozenset(
    {
        "\u0e43\u0e01\u0e25\u0e49",              # ใกล้
        "\u0e43\u0e04\u0e23",                     # ใคร
        "\u0e43\u0e04\u0e23\u0e48",              # ใคร่
        "\u0e43\u0e08",                           # ใจ
        "\u0e43\u0e0a\u0e48",                    # ใช่
        "\u0e43\u0e0a\u0e49",                    # ใช้
        "\u0e43\u0e14",                           # ใด
        "\u0e43\u0e15\u0e49",                    # ใต้
        "\u0e43\u0e19",                           # ใน
        "\u0e43\u0e1a",                           # ใบ
        "\u0e43\u0e1a\u0e49",                    # ใบ้
        "\u0e43\u0e1d\u0e48",                    # ใฝ่
        "\u0e43\u0e22",                           # ใย
        "\u0e2a\u0e30\u0e43\u0e20\u0e49",        # สะใภ้
        "\u0e43\u0e2a",                           # ใส
        "\u0e43\u0e2a\u0e48",                    # ใส่
        "\u0e43\u0e2b\u0e49",                    # ให้
        "\u0e43\u0e2b\u0e0d\u0e48",              # ใหญ่
        "\u0e43\u0e2b\u0e21\u0e48",              # ใหม่
        "\u0e2b\u0e25\u0e07\u0e43\u0e2b\u0e25", # หลงใหล
    }
)


def contains(word: str) -> bool:
    return word in AI_20_WORDS


__all__ = ["AI_20_WORDS", "contains"]

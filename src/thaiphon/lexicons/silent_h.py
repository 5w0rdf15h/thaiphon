"""M-525: silent ห-นำ-equivalent minor-conversion tone-exception class.

Words that look orthographically like LC syllables but are read as if
ห-led — effective class HC, with low tone on dead stop finals instead of
the LC default falling/high.
"""

from __future__ import annotations

SILENT_H_WORDS: frozenset[str] = frozenset(
    {
        "\u0e1b\u0e23\u0e30\u0e42\u0e22\u0e0a\u0e19\u0e4c",      # ประโยชน์
        "\u0e1b\u0e23\u0e30\u0e42\u0e22\u0e04",                   # ประโยค
        "\u0e1b\u0e23\u0e30\u0e21\u0e32\u0e17",                   # ประมาท
        "\u0e1b\u0e23\u0e30\u0e27\u0e31\u0e15\u0e34",             # ประวัติ
        "\u0e15\u0e33\u0e23\u0e27\u0e08",                         # ตำรวจ
        "\u0e14\u0e33\u0e23\u0e34",                               # ดำริ
        "\u0e14\u0e33\u0e23\u0e31\u0e2a",                         # ดำรัส
        "\u0e2a\u0e33\u0e40\u0e23\u0e47\u0e08",                   # สำเร็จ
        "\u0e2a\u0e33\u0e23\u0e27\u0e08",                         # สำรวจ
        "\u0e01\u0e33\u0e40\u0e19\u0e34\u0e14",                   # กำเนิด
        "\u0e08\u0e33\u0e23\u0e31\u0e2a",                         # จำรัส
        "\u0e1a\u0e38\u0e23\u0e38\u0e29",                         # บุรุษ
        "\u0e01\u0e34\u0e40\u0e25\u0e2a",                         # กิเลส
        "\u0e28\u0e34\u0e23\u0e34",                               # ศิริ
        "\u0e1a\u0e31\u0e0d\u0e0d\u0e31\u0e15\u0e34",             # บัญญัติ
    }
)


def contains(word: str) -> bool:
    return word in SILENT_H_WORDS


__all__ = ["SILENT_H_WORDS", "contains"]

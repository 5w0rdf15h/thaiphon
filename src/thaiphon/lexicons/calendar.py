"""Closed calendar class: months, weekdays, and month abbreviations.

Each entry maps a full orthographic form to a tuple of phonemic-syllable
respellings that the reader can derive cleanly. The pipeline uses these
to short-circuit derivation for this tiny fixed lexical class, which the
general Indic linker does not recover reliably.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

# word → tuple of respelling segments. One tuple entry per surface syllable.
_CALENDAR: dict[str, tuple[str, ...]] = {
    # --- 12 months -------------------------------------------------------
    # มกราคม → mohk{H} ga{L} raa{M} khohm{M}
    "\u0e21\u0e01\u0e23\u0e32\u0e04\u0e21": (
        "\u0e21\u0e01",           # มก
        "\u0e01\u0e30",           # กะ
        "\u0e23\u0e32",           # รา
        "\u0e04\u0e21",           # คม
    ),
    # กุมภาพันธ์ → goom{M} phaa{M} phan{M}
    "\u0e01\u0e38\u0e21\u0e20\u0e32\u0e1e\u0e31\u0e19\u0e18\u0e4c": (
        "\u0e01\u0e38\u0e21",     # กุม
        "\u0e1e\u0e32",           # พา
        "\u0e1e\u0e31\u0e19",     # พัน
    ),
    # มีนาคม → mee{M} naa{M} khohm{M}
    "\u0e21\u0e35\u0e19\u0e32\u0e04\u0e21": (
        "\u0e21\u0e35",           # มี
        "\u0e19\u0e32",           # นา
        "\u0e04\u0e21",           # คม
    ),
    # เมษายน → maeh{M} saa{R} yohn{M}
    "\u0e40\u0e21\u0e29\u0e32\u0e22\u0e19": (
        "\u0e40\u0e21",           # เม
        "\u0e2a\u0e32",           # สา
        "\u0e22\u0e19",           # ยน
    ),
    # พฤษภาคม → phreut{H} sa{L} phaa{M} khohm{M}
    "\u0e1e\u0e24\u0e29\u0e20\u0e32\u0e04\u0e21": (
        "\u0e1e\u0e23\u0e36\u0e29",  # พรึษ
        "\u0e2a\u0e30",              # สะ
        "\u0e1e\u0e32",              # พา
        "\u0e04\u0e21",              # คม
    ),
    # มิถุนายน → mi{H} thoo{L} naa{M} yohn{M}
    "\u0e21\u0e34\u0e16\u0e38\u0e19\u0e32\u0e22\u0e19": (
        "\u0e21\u0e34",           # มิ
        "\u0e16\u0e38",           # ถุ
        "\u0e19\u0e32",           # นา
        "\u0e22\u0e19",           # ยน
    ),
    # กรกฎาคม → ga{L} ra{H} ga{L} daa{M} khohm{M}
    "\u0e01\u0e23\u0e01\u0e0e\u0e32\u0e04\u0e21": (
        "\u0e01\u0e30",           # กะ
        "\u0e23\u0e30",           # ระ
        "\u0e01\u0e30",           # กะ
        "\u0e14\u0e32",           # ดา
        "\u0e04\u0e21",           # คม
    ),
    # สิงหาคม → sing{R} haa{R} khohm{M}
    "\u0e2a\u0e34\u0e07\u0e2b\u0e32\u0e04\u0e21": (
        "\u0e2a\u0e34\u0e07",     # สิง
        "\u0e2b\u0e32",           # หา
        "\u0e04\u0e21",           # คม
    ),
    # กันยายน → gan{M} yaa{M} yohn{M}
    "\u0e01\u0e31\u0e19\u0e22\u0e32\u0e22\u0e19": (
        "\u0e01\u0e31\u0e19",     # กัน
        "\u0e22\u0e32",           # ยา
        "\u0e22\u0e19",           # ยน
    ),
    # ตุลาคม → dtoo{L} laa{M} khohm{M}
    "\u0e15\u0e38\u0e25\u0e32\u0e04\u0e21": (
        "\u0e15\u0e38",           # ตุ
        "\u0e25\u0e32",           # ลา
        "\u0e04\u0e21",           # คม
    ),
    # พฤศจิกายน → phreut{H} sa{L} ji{L} gaa{M} yohn{M}
    "\u0e1e\u0e24\u0e28\u0e08\u0e34\u0e01\u0e32\u0e22\u0e19": (
        "\u0e1e\u0e23\u0e36\u0e28",  # พรึศ
        "\u0e2a\u0e30",              # สะ
        "\u0e08\u0e34",              # จิ
        "\u0e01\u0e32",              # กา
        "\u0e22\u0e19",              # ยน
    ),
    # ธันวาคม → than{M} waa{M} khohm{M}
    "\u0e18\u0e31\u0e19\u0e27\u0e32\u0e04\u0e21": (
        "\u0e17\u0e31\u0e19",     # ทัน
        "\u0e27\u0e32",           # วา
        "\u0e04\u0e21",           # คม
    ),
    # --- abbreviated month forms (attested in etalon) --------------------
    # ม.ค. → mohk{H} ga{L} raa{M} khohm{M}
    "\u0e21.\u0e04.": (
        "\u0e21\u0e01", "\u0e01\u0e30", "\u0e23\u0e32", "\u0e04\u0e21",
    ),
    # มี.ค. → mee{M} naa{M} khohm{M}
    "\u0e21\u0e35.\u0e04.": (
        "\u0e21\u0e35", "\u0e19\u0e32", "\u0e04\u0e21",
    ),
    # เม.ย. → maeh{M} saa{R} yohn{M}
    "\u0e40\u0e21.\u0e22.": (
        "\u0e40\u0e21", "\u0e2a\u0e32", "\u0e22\u0e19",
    ),
    # พ.ค. → phreut{H} sa{L} phaa{M} khohm{M}
    "\u0e1e.\u0e04.": (
        "\u0e1e\u0e23\u0e36\u0e29", "\u0e2a\u0e30", "\u0e1e\u0e32", "\u0e04\u0e21",
    ),
    # มิ.ย. → mi{H} thoo{L} naa{M} yohn{M}
    "\u0e21\u0e34.\u0e22.": (
        "\u0e21\u0e34", "\u0e16\u0e38", "\u0e19\u0e32", "\u0e22\u0e19",
    ),
    # ก.ค. → ga{L} ra{H} ga{L} daa{M} khohm{M}
    "\u0e01.\u0e04.": (
        "\u0e01\u0e30", "\u0e23\u0e30", "\u0e01\u0e30", "\u0e14\u0e32", "\u0e04\u0e21",
    ),
    # ส.ค. → sing{R} haa{R} khohm{M}
    "\u0e2a.\u0e04.": (
        "\u0e2a\u0e34\u0e07", "\u0e2b\u0e32", "\u0e04\u0e21",
    ),
    # ก.ย. → gan{M} yaa{M} yohn{M}
    "\u0e01.\u0e22.": (
        "\u0e01\u0e31\u0e19", "\u0e22\u0e32", "\u0e22\u0e19",
    ),
    # ต.ค. → dtoo{L} laa{M} khohm{M}
    "\u0e15.\u0e04.": (
        "\u0e15\u0e38", "\u0e25\u0e32", "\u0e04\u0e21",
    ),
    # พ.ย. → phreut{H} sa{L} ji{L} gaa{M} yohn{M}
    "\u0e1e.\u0e22.": (
        "\u0e1e\u0e23\u0e36\u0e28", "\u0e2a\u0e30", "\u0e08\u0e34",
        "\u0e01\u0e32", "\u0e22\u0e19",
    ),
    # ธ.ค. → than{M} waa{M} khohm{M}
    "\u0e18.\u0e04.": (
        "\u0e17\u0e31\u0e19", "\u0e27\u0e32", "\u0e04\u0e21",
    ),
    # กุมภาพันธ์ has its own abbreviation ก.พ. — but the etalon reading
    # there is ``gaaw{M} phaaw{M}`` (letter-names), not the month reading.
    # We do NOT lexicalize ก.พ. here since the etalon expects letter-names.
    # --- 7 weekdays (วัน + day-name) -------------------------------------
    # วันจันทร์ → wan{M} jan{M}
    "\u0e27\u0e31\u0e19\u0e08\u0e31\u0e19\u0e17\u0e23\u0e4c": (
        "\u0e27\u0e31\u0e19",                      # วัน
        "\u0e08\u0e31\u0e19",                      # จัน
    ),
    # วันอังคาร → wan{M} ang{M} khaan{M}
    "\u0e27\u0e31\u0e19\u0e2d\u0e31\u0e07\u0e04\u0e32\u0e23": (
        "\u0e27\u0e31\u0e19",                      # วัน
        "\u0e2d\u0e31\u0e07",                      # อัง
        "\u0e04\u0e32\u0e19",                      # คาน
    ),
    # วันพุธ → wan{M} phoot{H}
    "\u0e27\u0e31\u0e19\u0e1e\u0e38\u0e18": (
        "\u0e27\u0e31\u0e19",                      # วัน
        "\u0e1e\u0e38\u0e18",                      # พุธ
    ),
    # วันพฤหัสบดี → wan{M} phreu{H} hat{L} sa{L} baaw{M} dee{M}
    "\u0e27\u0e31\u0e19\u0e1e\u0e24\u0e2b\u0e31\u0e2a\u0e1a\u0e14\u0e35": (
        "\u0e27\u0e31\u0e19",                      # วัน
        "\u0e1e\u0e23\u0e36",                      # พรึ
        "\u0e2b\u0e31\u0e2a",                      # หัส
        "\u0e2a\u0e30",                            # สะ
        "\u0e1a\u0e2d",                            # บอ
        "\u0e14\u0e35",                            # ดี
    ),
    # วันพฤหัส → wan{M} phreu{H} hat{L} sa{L} baaw{M} dee{M}
    # (common clipped reference — pronounced as the full form)
    "\u0e27\u0e31\u0e19\u0e1e\u0e24\u0e2b\u0e31\u0e2a": (
        "\u0e27\u0e31\u0e19",
        "\u0e1e\u0e23\u0e36",
        "\u0e2b\u0e31\u0e2a",
        "\u0e2a\u0e30",
        "\u0e1a\u0e2d",
        "\u0e14\u0e35",
    ),
    # วันศุกร์ → wan{M} sook{L}
    "\u0e27\u0e31\u0e19\u0e28\u0e38\u0e01\u0e23\u0e4c": (
        "\u0e27\u0e31\u0e19",                      # วัน
        "\u0e2a\u0e38\u0e01",                      # สุก
    ),
    # วันเสาร์ → wan{M} sao{R}
    "\u0e27\u0e31\u0e19\u0e40\u0e2a\u0e32\u0e23\u0e4c": (
        "\u0e27\u0e31\u0e19",                      # วัน
        "\u0e40\u0e2a\u0e32",                      # เสา
    ),
    # วันอาทิตย์ → wan{M} aa{M} thit{H}
    "\u0e27\u0e31\u0e19\u0e2d\u0e32\u0e17\u0e34\u0e15\u0e22\u0e4c": (
        "\u0e27\u0e31\u0e19",                      # วัน
        "\u0e2d\u0e32",                            # อา
        "\u0e17\u0e34\u0e15",                      # ทิต
    ),
}


CALENDAR_WORDS: Mapping[str, tuple[str, ...]] = MappingProxyType(_CALENDAR)


def lookup(word: str) -> tuple[str, ...] | None:
    return _CALENDAR.get(word)


__all__ = ["CALENDAR_WORDS", "lookup"]

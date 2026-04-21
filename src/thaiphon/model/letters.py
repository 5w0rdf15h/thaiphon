"""Canonical Thai letter codepoints used across the phonology stack.

Single source of truth so vowel/coda/strategy modules never re-declare the
same character literal. All values are single-codepoint ``str`` instances
so they can be compared directly against Python string slices.
"""

from __future__ import annotations

# --- vowel marks ----------------------------------------------------------

SARA_A = "\u0e30"           # ะ
MAI_HAN_AKAT = "\u0e31"     # ◌ั
SARA_AA = "\u0e32"          # า
SARA_AM = "\u0e33"          # ำ
SARA_I = "\u0e34"           # ◌ิ
SARA_II = "\u0e35"          # ◌ี
SARA_UE = "\u0e36"          # ◌ึ
SARA_UEE = "\u0e37"         # ◌ื
SARA_U = "\u0e38"           # ◌ุ
SARA_UU = "\u0e39"          # ◌ู
MAITAIKHU = "\u0e47"        # ◌็

# --- pre-base vowels ------------------------------------------------------

SARA_E = "\u0e40"           # เ
SARA_AE = "\u0e41"          # แ
SARA_O = "\u0e42"           # โ
SARA_AI_MAIMUAN = "\u0e43"  # ใ
SARA_AI_MAIMALAI = "\u0e44"  # ไ

PRE_VOWELS: frozenset[str] = frozenset(
    {SARA_E, SARA_AE, SARA_O, SARA_AI_MAIMUAN, SARA_AI_MAIMALAI}
)

#: Subset of :data:`PRE_VOWELS` used by the pre-vowel hop heuristic.
#: Excludes ใ/ไ because those are single-letter vowels, not frame openers.
HOP_PRE_VOWELS: frozenset[str] = frozenset({SARA_E, SARA_AE, SARA_O})

# --- consonants that double as vowel-frame components --------------------

O_ANG = "\u0e2d"            # อ (vowel carrier in เ…ือ, post-base ɔ:)
YO_YAK = "\u0e22"           # ย (vowel glide in เ…ีย)
WO_WAEN = "\u0e27"          # ว (vowel glide in …ัว / C+ว+C)
RO_RUA = "\u0e23"           # ร (M-308 / M-740)
HO_HIP = "\u0e2b"           # ห (high-class leader letter)

# --- diacritics -----------------------------------------------------------

THANTHAKHAT = "\u0e4c"      # ◌์ (killer mark)
NIKHAHIT = "\u0e4d"         # ◌ํ (nasalisation)
LAKKHANGYAO = "\u0e45"      # ฤๅ vowel-length sign

# --- repetition / abbreviation markers -----------------------------------

MAI_YAMOK = "\u0e46"        # ๆ (repetition)
PAIYANNOI = "\u0e2f"        # ฯ (abbreviation)

# --- tone marks -----------------------------------------------------------

MAI_EK = "\u0e48"           # ◌่
MAI_THO = "\u0e49"          # ◌้
MAI_TRI = "\u0e4a"          # ◌๊
MAI_JATTAWA = "\u0e4b"      # ◌๋

TONE_MARKS: frozenset[str] = frozenset({MAI_EK, MAI_THO, MAI_TRI, MAI_JATTAWA})

# --- vowel-character aggregate -------------------------------------------

#: Every character that marks "this token already has an explicit vowel",
#: used by syllabification strategies to distinguish vowel-bearing TCC
#: tokens from bare-consonant tokens. Pre-base vowels are included.
VOWEL_CHARS: frozenset[str] = PRE_VOWELS | frozenset(
    {
        SARA_A, MAI_HAN_AKAT, SARA_AA, SARA_AM,
        SARA_I, SARA_II, SARA_UE, SARA_UEE,
        SARA_U, SARA_UU, MAITAIKHU,
    }
)

#: Vowel marks that follow the base consonant (i.e. all of :data:`VOWEL_CHARS`
#: except the pre-base vowels). For downstream consumers that specifically
#: want non-pre-base marks.
POST_BASE_VOWEL_MARKS: frozenset[str] = VOWEL_CHARS - PRE_VOWELS


__all__ = [
    "HO_HIP",
    "HOP_PRE_VOWELS",
    "LAKKHANGYAO",
    "MAITAIKHU",
    "MAI_EK",
    "MAI_HAN_AKAT",
    "MAI_JATTAWA",
    "MAI_THO",
    "MAI_TRI",
    "MAI_YAMOK",
    "NIKHAHIT",
    "O_ANG",
    "PAIYANNOI",
    "POST_BASE_VOWEL_MARKS",
    "PRE_VOWELS",
    "RO_RUA",
    "SARA_A",
    "SARA_AA",
    "SARA_AE",
    "SARA_AI_MAIMALAI",
    "SARA_AI_MAIMUAN",
    "SARA_AM",
    "SARA_E",
    "SARA_I",
    "SARA_II",
    "SARA_O",
    "SARA_U",
    "SARA_UE",
    "SARA_UEE",
    "SARA_UU",
    "THANTHAKHAT",
    "TONE_MARKS",
    "VOWEL_CHARS",
    "WO_WAEN",
    "YO_YAK",
]

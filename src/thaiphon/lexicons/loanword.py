"""Loanword lexicon with per-entry phonological profile.

This module is the canonical source for curated loanword entries. Each
entry carries a :class:`LoanProfile` describing how the word should be
treated by later pipeline stages (coda preservation, tone assignment,
vowel-length policy, confidence).

The pipeline today only consumes one dimension of the profile — the
``coda_policy="preserve"`` entries drive the modern-loan /f/-coda
preservation override in the TLC renderer. The remaining fields are
laid out now so that forthcoming stages (loanword detector, precedence
pipeline) can read them without further lexicon churn. Downstream
callers should prefer :data:`LOANWORDS` and :func:`get_entry`; the
legacy ``loan_final_f`` module keeps its public surface but is now a
thin view over this data.

The Thai headwords are stored in NFC.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal

SourceLanguage = Literal["english", "generic_foreign", "unknown"]
CodaPolicy = Literal["preserve", "neutralize", "lexical"]
TonePolicy = Literal["lexical", "heuristic", "native_fallback"]
VowelLengthPolicy = Literal["lexical", "spelling_driven", "heuristic"]
Confidence = Literal["high", "medium", "low"]

_SOURCE_LANGUAGE_VALUES: frozenset[str] = frozenset(
    {"english", "generic_foreign", "unknown"}
)
_CODA_POLICY_VALUES: frozenset[str] = frozenset(
    {"preserve", "neutralize", "lexical"}
)
_TONE_POLICY_VALUES: frozenset[str] = frozenset(
    {"lexical", "heuristic", "native_fallback"}
)
_VOWEL_LENGTH_POLICY_VALUES: frozenset[str] = frozenset(
    {"lexical", "spelling_driven", "heuristic"}
)
_CONFIDENCE_VALUES: frozenset[str] = frozenset({"high", "medium", "low"})


@dataclass(frozen=True, slots=True)
class LoanProfile:
    """Per-entry loanword treatment directive.

    Fields
    ------
    source_language
        Origin language. ``"english"`` for attested English borrowings,
        ``"generic_foreign"`` for non-English foreign items (French,
        proper names, etc.), ``"unknown"`` when we only know the item
        is not native.
    coda_policy
        ``"preserve"`` — keep the foreign coda symbol at the surface
        (e.g. final /f/ from ``ฟ`` instead of native-collapsed /p̚/).
        ``"neutralize"`` — let native phonotactics do their thing.
        ``"lexical"`` — the lexicon itself carries the surface coda.
    tone_policy
        ``"lexical"`` — use the stored tone(s) verbatim.
        ``"heuristic"`` — reconstruct tone from the usual class rules.
        ``"native_fallback"`` — defer to native derivation entirely.
    vowel_length_policy
        ``"lexical"`` — use stored length.
        ``"spelling_driven"`` — derive length from orthographic cues
        (e.g. Mai Thaikhu short-mark, written long vowel).
        ``"heuristic"`` — guess from default loan conventions.
    confidence
        Curator's confidence in the assignment. ``"high"`` entries are
        safe for automated use; ``"low"`` entries may warrant review
        or alternate-emission.
    """

    source_language: SourceLanguage
    coda_policy: CodaPolicy
    tone_policy: TonePolicy
    vowel_length_policy: VowelLengthPolicy
    confidence: Confidence

    def __post_init__(self) -> None:
        if self.source_language not in _SOURCE_LANGUAGE_VALUES:
            raise ValueError(
                f"invalid source_language: {self.source_language!r}"
            )
        if self.coda_policy not in _CODA_POLICY_VALUES:
            raise ValueError(f"invalid coda_policy: {self.coda_policy!r}")
        if self.tone_policy not in _TONE_POLICY_VALUES:
            raise ValueError(f"invalid tone_policy: {self.tone_policy!r}")
        if self.vowel_length_policy not in _VOWEL_LENGTH_POLICY_VALUES:
            raise ValueError(
                f"invalid vowel_length_policy: {self.vowel_length_policy!r}"
            )
        if self.confidence not in _CONFIDENCE_VALUES:
            raise ValueError(f"invalid confidence: {self.confidence!r}")


PreservedCodaTag = Literal["f", "s", "l", "k"]

_PRESERVED_CODA_TAGS: frozenset[str] = frozenset({"f", "s", "l", "k"})

# Profiles in which a ``preserved_coda`` annotation may fire. ``everyday``
# is the default user-facing register; ``careful_educated`` is the
# register that preserves more foreign codas (news-anchor / English-aware
# speech). ``etalon_compat`` never fires preservation — dictionary-style
# citation forms always collapse to native phonotactics.
_VALID_PRESERVE_PROFILES: frozenset[str] = frozenset(
    {"everyday", "careful_educated"}
)


@dataclass(frozen=True, slots=True)
class LoanEntry:
    """A curated loanword with its phonological profile.

    ``word`` is the Thai headword (NFC). ``profile`` describes how the
    pipeline should treat it at the profile/policy level. Entries that
    need an explicit foreign-coda preservation target also carry
    ``preserved_coda`` (a scheme-neutral tag such as ``"f"``, ``"s"``,
    ``"l"``, ``"k"``) and ``preserve_in`` — the set of reading profiles
    under which that preservation fires. When ``preserved_coda`` is
    ``None`` the entry is still a lexicon member for detector purposes
    but does not drive any renderer override.
    """

    word: str
    profile: LoanProfile
    preserved_coda: PreservedCodaTag | None = None
    preserve_in: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if self.preserved_coda is not None:
            if self.preserved_coda not in _PRESERVED_CODA_TAGS:
                raise ValueError(
                    f"invalid preserved_coda: {self.preserved_coda!r}"
                )
            if not self.preserve_in:
                raise ValueError(
                    "preserved_coda set but preserve_in is empty"
                )
        for prof in self.preserve_in:
            if prof not in _VALID_PRESERVE_PROFILES:
                raise ValueError(
                    f"preserve_in contains invalid profile: {prof!r}"
                )
        if self.preserve_in and self.preserved_coda is None:
            raise ValueError("preserve_in set but preserved_coda is None")


# ---------------------------------------------------------------------------
# Profile presets. Every current entry uses a "preserve the foreign coda
# with lexical tone" regime — that's the only dimension the pipeline
# consumes today. Presets keep the entry table terse and make future
# diversification straightforward.
# ---------------------------------------------------------------------------

_ENGLISH_PRESERVED_F = LoanProfile(
    source_language="english",
    coda_policy="preserve",
    tone_policy="lexical",
    vowel_length_policy="spelling_driven",
    confidence="high",
)

_GENERIC_PRESERVED_F = LoanProfile(
    source_language="generic_foreign",
    coda_policy="preserve",
    tone_policy="lexical",
    vowel_length_policy="spelling_driven",
    confidence="high",
)

_ENGLISH_LEXICAL = LoanProfile(
    source_language="english",
    coda_policy="lexical",
    tone_policy="lexical",
    vowel_length_policy="lexical",
    confidence="high",
)
# Attested English borrowings whose coda is not /f/. They don't gate
# current renderer behaviour (only preserve-coda entries do), but they
# populate the detector's ``lexicon_hit`` signal and provide the lexicon
# groundwork the later pipeline phases will consume.


# ---------------------------------------------------------------------------
# Entry table.
#
# Entries are grouped by profile. The Thai headwords use explicit
# escapes so this file stays ASCII-clean; the comment column shows the
# visible form for review.
# ---------------------------------------------------------------------------

_ENGLISH_F_PRESERVING: tuple[str, ...] = (
    "\u0e01\u0e23\u0e32\u0e1f",                              # กราฟ
    "\u0e01\u0e23\u0e32\u0e1f\u0e1f\u0e34\u0e15\u0e35",      # กราฟฟิตี
    "\u0e01\u0e23\u0e4a\u0e32\u0e1f",                        # กร๊าฟ
    "\u0e01\u0e23\u0e4a\u0e32\u0e1f\u0e1f\u0e34\u0e04",      # กร๊าฟฟิค
    "\u0e01\u0e2d\u0e25\u0e4c\u0e1f",                        # กอล์ฟ
    "\u0e01\u0e34\u0e4a\u0e1f\u0e17\u0e4c",                  # กิ๊ฟท์
    "\u0e04\u0e25\u0e34\u0e1f\u0e1f\u0e4c",                  # คลิฟฟ์
    "\u0e04\u0e2d\u0e1f\u0e1f\u0e35\u0e48",                  # คอฟฟี่
    "\u0e04\u0e31\u0e1f\u0e40\u0e27\u0e2d\u0e23\u0e4c",      # คัฟเวอร์
    "\u0e04\u0e32\u0e23\u0e4c\u0e14\u0e34\u0e1f\u0e1f\u0e4c",  # คาร์ดิฟฟ์
    "\u0e04\u0e32\u0e23\u0e4c\u0e1f",                        # คาร์ฟ
    "\u0e04\u0e34\u0e01\u0e2d\u0e2d\u0e1f",                  # คิกออฟ
    "\u0e0b\u0e2d\u0e1f\u0e15\u0e4c\u0e41\u0e27\u0e23\u0e4c",  # ซอฟต์แวร์
    "\u0e0b\u0e31\u0e19\u0e23\u0e39\u0e1f",                  # ซันรูฟ
    "\u0e17\u0e23\u0e32\u0e1f\u0e1f\u0e34\u0e01",            # ทราฟฟิก
    "\u0e17\u0e31\u0e1f\u0e15\u0e4c",                        # ทัฟต์
    "\u0e17\u0e31\u0e21\u0e1a\u0e4c\u0e44\u0e14\u0e23\u0e1f\u0e4c",  # ทัมบ์ไดรฟ์
    "\u0e17\u0e34\u0e1f\u0e1f\u0e32\u0e19\u0e35\u0e48",      # ทิฟฟานี่
    "\u0e17\u0e4a\u0e2d\u0e1f\u0e1f\u0e35\u0e48",            # ท๊อฟฟี่
    "\u0e1a\u0e23\u0e35\u0e1f",                              # บรีฟ
    "\u0e1a\u0e31\u0e1f\u0e1f\u0e32\u0e42\u0e25",            # บัฟฟาโล
    "\u0e1a\u0e32\u0e23\u0e4c\u0e1f",                        # บาร์ฟ
    "\u0e1a\u0e38\u0e1f\u0e40\u0e1f\u0e48\u0e15\u0e4c",      # บุฟเฟ่ต์
    "\u0e1f\u0e34\u0e25\u0e4c\u0e21\u0e40\u0e19\u0e01\u0e32\u0e15\u0e35\u0e1f",  # ฟิล์มเนกาตีฟ
    "\u0e22\u0e35\u0e23\u0e32\u0e1f",                        # ยีราฟ
    "\u0e22\u0e39\u0e19\u0e34\u0e40\u0e0b\u0e1f",            # ยูนิเซฟ
    "\u0e25\u0e34\u0e1f\u0e15\u0e4c",                        # ลิฟต์
    "\u0e2a\u0e15\u0e35\u0e1f",                              # สตีฟ
    "\u0e2a\u0e25\u0e32\u0e1f",                              # สลาฟ
    "\u0e2d\u0e2d\u0e01\u0e0b\u0e1f\u0e2d\u0e23\u0e4c\u0e14",  # ออกซฟอร์ด
    "\u0e2d\u0e2d\u0e1f",                                    # ออฟ
    "\u0e2d\u0e2d\u0e1f\u0e1f\u0e34\u0e15",                  # ออฟฟิต
    "\u0e2d\u0e2d\u0e1f\u0e1f\u0e34\u0e28",                  # ออฟฟิศ
    "\u0e2d\u0e2d\u0e1f\u0e44\u0e25\u0e19\u0e4c",            # ออฟไลน์
    "\u0e2d\u0e2d\u0e40\u0e14\u0e34\u0e1f",                  # ออเดิฟ
    "\u0e2d\u0e2d\u0e40\u0e14\u0e34\u0e23\u0e4c\u0e1f",      # ออเดิร์ฟ
    "\u0e2d\u0e31\u0e1f",                                    # อัฟ
    "\u0e2e\u0e32\u0e25\u0e4c\u0e1f\u0e41\u0e1a\u0e47\u0e01",  # ฮาล์ฟแบ็ก
    "\u0e40\u0e04\u0e23\u0e1f",                              # เครฟ
    "\u0e40\u0e08\u0e1f",                                    # เจฟ
    "\u0e40\u0e08\u0e1f\u0e1f\u0e23\u0e35\u0e48",            # เจฟฟรี่
    "\u0e40\u0e08\u0e1f\u0e1f\u0e23\u0e35\u0e48\u0e22\u0e4c",  # เจฟฟรี่ย์
    "\u0e40\u0e08\u0e1f\u0e40\u0e1f\u0e2d\u0e23\u0e4c\u0e2a\u0e31\u0e19",  # เจฟเฟอร์สัน
    "\u0e40\u0e0a\u0e1f",                                    # เชฟ
    "\u0e40\u0e0a\u0e1f\u0e42\u0e23\u0e40\u0e25\u0e15",      # เชฟโรเลต
    "\u0e40\u0e0a\u0e47\u0e1f\u0e1f\u0e35\u0e25\u0e14\u0e4c",  # เช็ฟฟีลด์
    "\u0e40\u0e0b\u0e1f",                                    # เซฟ
    "\u0e40\u0e0b\u0e1f\u0e40\u0e2e\u0e49\u0e32\u0e2a\u0e4c",  # เซฟเฮ้าส์
    "\u0e40\u0e0b\u0e1f\u0e41\u0e2d\u0e2a",                  # เซฟแอส
    "\u0e40\u0e0b\u0e34\u0e1f",                              # เซิฟ
    "\u0e40\u0e0b\u0e34\u0e23\u0e4c\u0e1f\u0e40\u0e27\u0e2d\u0e23\u0e4c",  # เซิร์ฟเวอร์
    "\u0e40\u0e0b\u0e49\u0e1f",                              # เซ้ฟ
    "\u0e40\u0e14\u0e1f",                                    # เดฟ
    "\u0e40\u0e17\u0e49\u0e1f\u0e25\u0e48\u0e2d\u0e19",      # เท้ฟล่อน
    "\u0e40\u0e19\u0e01\u0e32\u0e15\u0e35\u0e1f",            # เนกาตีฟ
    "\u0e40\u0e25\u0e34\u0e1f",                              # เลิฟ
    "\u0e40\u0e25\u0e47\u0e1f\u0e15\u0e4c",                  # เล็ฟต์
    "\u0e40\u0e2a\u0e23\u0e34\u0e1f",                        # เสริฟ
    "\u0e40\u0e2a\u0e34\u0e23\u0e4c\u0e1f",                  # เสิร์ฟ
    "\u0e40\u0e2d\u0e1f",                                    # เอฟ
    "\u0e40\u0e2d\u0e1f\u0e0b\u0e35",                        # เอฟซี
    "\u0e40\u0e2d\u0e1f\u0e1a\u0e35\u0e44\u0e2d",            # เอฟบีไอ
    "\u0e40\u0e2d\u0e25\u0e1f\u0e4c",                        # เอลฟ์
    "\u0e41\u0e14\u0e1f\u0e42\u0e1f\u0e14\u0e34\u0e25",      # แดฟโฟดิล
    "\u0e41\u0e19\u0e1f\u0e18\u0e32\u0e25\u0e35\u0e19",      # แนฟธาลีน
    "\u0e41\u0e2e\u0e19\u0e14\u0e35\u0e49\u0e44\u0e14\u0e23\u0e4a\u0e1f",  # แฮนดี้ไดร๊ฟ
    "\u0e42\u0e0b\u0e25\u0e2d\u0e1f\u0e15\u0e4c",            # โซลอฟต์
    "\u0e42\u0e2d\u0e25\u0e35\u0e1f",                        # โอลีฟ
    "\u0e44\u0e14\u0e23\u0e1f\u0e4c",                        # ไดรฟ์
    "\u0e44\u0e21\u0e42\u0e04\u0e23\u0e0b\u0e2d\u0e1f\u0e15\u0e4c",  # ไมโครซอฟต์
    "\u0e44\u0e21\u0e42\u0e04\u0e23\u0e40\u0e27\u0e1f",      # ไมโครเวฟ
    "\u0e44\u0e27\u0e44\u0e1f",                              # ไวไฟ
)

_ENGLISH_LEXICAL_WORDS: tuple[str, ...] = (
    "\u0e01\u0e31\u0e27\u0e25\u0e32\u0e25\u0e31\u0e21\u0e40\u0e1b\u0e2d\u0e23\u0e4c",  # กัวลาลัมเปอร์
    "\u0e01\u0e32\u0e15\u0e32\u0e23\u0e4c",                  # กาตาร์
    "\u0e01\u0e32\u0e23\u0e4c\u0e14",                        # การ์ด
    "\u0e01\u0e32\u0e23\u0e4c\u0e15\u0e39\u0e19",            # การ์ตูน
    "\u0e01\u0e34\u0e01\u0e30\u0e44\u0e1a\u0e15\u0e4c",      # กิกะไบต์
    "\u0e01\u0e34\u0e42\u0e25\u0e44\u0e1a\u0e15\u0e4c",      # กิโลไบต์
    "\u0e01\u0e35\u0e15\u0e32\u0e23\u0e4c",                  # กีตาร์
    "\u0e01\u0e38\u0e4a\u0e01",                              # กุ๊ก
    "\u0e01\u0e4a\u0e2d\u0e01",                              # ก๊อก
    "\u0e01\u0e4a\u0e2d\u0e1b",                              # ก๊อป
    "\u0e04\u0e23\u0e34\u0e01\u0e40\u0e01\u0e47\u0e15",      # คริกเก็ต
    "\u0e04\u0e23\u0e35\u0e21",                              # ครีม
    "\u0e04\u0e25\u0e2d\u0e42\u0e23\u0e1f\u0e2d\u0e23\u0e4c\u0e21",  # คลอโรฟอร์ม
    "\u0e04\u0e25\u0e31\u0e1a",                              # คลับ
    "\u0e04\u0e25\u0e32\u0e23\u0e34\u0e40\u0e19\u0e47\u0e15",  # คลาริเน็ต
    "\u0e04\u0e2d\u0e19\u0e40\u0e2a\u0e34\u0e23\u0e4c\u0e15",  # คอนเสิร์ต
    "\u0e04\u0e2d\u0e21\u0e1e\u0e34\u0e27\u0e40\u0e15\u0e2d\u0e23\u0e4c",  # คอมพิวเตอร์
    "\u0e04\u0e2d\u0e21\u0e40\u0e21\u0e19\u0e15\u0e4c",      # คอมเมนต์
    "\u0e04\u0e2d\u0e21\u0e44\u0e1e\u0e40\u0e25\u0e2d\u0e23\u0e4c",  # คอมไพเลอร์
    "\u0e04\u0e2d\u0e23\u0e4c\u0e14",                        # คอร์ด
    "\u0e04\u0e2d\u0e25\u0e25\u0e32\u0e40\u0e08\u0e19",      # คอลลาเจน
    "\u0e04\u0e2d\u0e2a\u0e40\u0e1e\u0e25\u0e22\u0e4c",      # คอสเพลย์
    "\u0e04\u0e31\u0e1b\u0e1b\u0e38\u0e0a\u0e0a\u0e35\u0e42\u0e19",  # คัปปุชชีโน
    "\u0e04\u0e31\u0e1e\u0e40\u0e04\u0e49\u0e01",            # คัพเค้ก
    "\u0e04\u0e32\u0e23\u0e4c\u0e1a\u0e2d\u0e19",            # คาร์บอน
    "\u0e04\u0e32\u0e23\u0e4c\u0e42\u0e1a\u0e44\u0e2e\u0e40\u0e14\u0e23\u0e15",  # คาร์โบไฮเดรต
    "\u0e04\u0e35\u0e22\u0e4c\u0e1a\u0e2d\u0e23\u0e4c\u0e14",  # คีย์บอร์ด
    "\u0e0b\u0e35\u0e23\u0e35\u0e2a\u0e4c",                  # ซีรีส์
    "\u0e0b\u0e35\u0e40\u0e21\u0e19\u0e15\u0e4c",            # ซีเมนต์
    "\u0e14\u0e2d\u0e01\u0e40\u0e15\u0e2d\u0e23\u0e4c",      # ดอกเตอร์
    "\u0e14\u0e2d\u0e25\u0e25\u0e32\u0e23\u0e4c",            # ดอลลาร์
    "\u0e14\u0e32\u0e27\u0e19\u0e4c",                        # ดาวน์
    "\u0e14\u0e34\u0e2a\u0e01\u0e4c",                        # ดิสก์
    "\u0e14\u0e34\u0e2a\u0e19\u0e35\u0e22\u0e4c",            # ดิสนีย์
    "\u0e14\u0e35\u0e44\u0e0b\u0e19\u0e4c",                  # ดีไซน์
    "\u0e17\u0e27\u0e34\u0e15\u0e40\u0e15\u0e2d\u0e23\u0e4c",  # ทวิตเตอร์
    "\u0e17\u0e31\u0e27\u0e23\u0e4c",                        # ทัวร์
    "\u0e19\u0e2d\u0e23\u0e4c\u0e40\u0e27\u0e22\u0e4c",      # นอร์เวย์
    "\u0e19\u0e34\u0e27\u0e40\u0e04\u0e25\u0e35\u0e22\u0e23\u0e4c",  # นิวเคลียร์
    "\u0e1a\u0e23\u0e31\u0e2a\u0e40\u0e0b\u0e25\u0e2a\u0e4c",  # บรัสเซลส์
    "\u0e1a\u0e25\u0e47\u0e2d\u0e01\u0e40\u0e01\u0e2d\u0e23\u0e4c",  # บล็อกเกอร์
    "\u0e1a\u0e32\u0e23\u0e4c",                              # บาร์
    "\u0e1b\u0e23\u0e34\u0e4a\u0e19\u0e40\u0e15\u0e2d\u0e23\u0e4c",  # ปริ๊นเตอร์
    "\u0e1b\u0e2d\u0e19\u0e14\u0e4c",                        # ปอนด์
    "\u0e1e\u0e23\u0e34\u0e19\u0e15\u0e4c",                  # พรินต์
    "\u0e1e\u0e23\u0e35\u0e40\u0e0b\u0e47\u0e19\u0e40\u0e15\u0e2d\u0e23\u0e4c",  # พรีเซ็นเตอร์
    "\u0e1e\u0e2d\u0e14\u0e41\u0e04\u0e2a\u0e15\u0e4c",      # พอดแคสต์
    "\u0e1f\u0e2d\u0e19\u0e15\u0e4c",                        # ฟอนต์
    "\u0e1f\u0e34\u0e19\u0e41\u0e25\u0e19\u0e14\u0e4c",      # ฟินแลนด์
    # ``ฟิลิปปินส์`` intentionally omitted: its medial ฟ-coda in
    # syllable two would trigger the TLC /f/-preservation override
    # once the word is a lexicon hit, which regresses against the
    # etalon's native-/p/ reading for that syllable.
    "\u0e1f\u0e34\u0e2a\u0e34\u0e01\u0e2a\u0e4c",            # ฟิสิกส์
    "\u0e21\u0e2d\u0e19\u0e34\u0e40\u0e15\u0e2d\u0e23\u0e4c",  # มอนิเตอร์
    "\u0e21\u0e2d\u0e40\u0e15\u0e2d\u0e23\u0e4c",            # มอเตอร์
    "\u0e21\u0e2d\u0e40\u0e15\u0e2d\u0e23\u0e4c\u0e40\u0e27\u0e22\u0e4c",  # มอเตอร์เวย์
    "\u0e21\u0e2d\u0e40\u0e15\u0e2d\u0e23\u0e4c\u0e44\u0e0b\u0e04\u0e4c",  # มอเตอร์ไซค์
    "\u0e21\u0e31\u0e25\u0e41\u0e27\u0e23\u0e4c",            # มัลแวร์
    "\u0e21\u0e32\u0e23\u0e4c\u0e0a\u0e41\u0e21\u0e25\u0e42\u0e25\u0e27\u0e4c",  # มาร์ชแมลโลว์
    "\u0e21\u0e34\u0e40\u0e15\u0e2d\u0e23\u0e4c",            # มิเตอร์
    "\u0e22\u0e39\u0e17\u0e39\u0e1a\u0e40\u0e1a\u0e2d\u0e23\u0e4c",  # ยูทูบเบอร์
    "\u0e25\u0e34\u0e07\u0e01\u0e4c",                        # ลิงก์
    "\u0e25\u0e47\u0e2d\u0e01\u0e14\u0e32\u0e27\u0e19\u0e4c",  # ล็อกดาวน์
    "\u0e25\u0e47\u0e2d\u0e1a\u0e2a\u0e40\u0e15\u0e2d\u0e23\u0e4c",  # ล็อบสเตอร์
    "\u0e27\u0e31\u0e15\u0e15\u0e4c",                        # วัตต์
    "\u0e2a\u0e01\u0e2d\u0e15\u0e41\u0e25\u0e19\u0e14\u0e4c",  # สกอตแลนด์
    "\u0e2a\u0e15\u0e34\u0e01\u0e40\u0e01\u0e2d\u0e23\u0e4c",  # สติกเกอร์
    "\u0e2a\u0e27\u0e34\u0e15\u0e40\u0e0b\u0e2d\u0e23\u0e4c\u0e41\u0e25\u0e19\u0e14\u0e4c",  # สวิตเซอร์แลนด์  # noqa: E501
    "\u0e2a\u0e44\u0e15\u0e25\u0e4c",                        # สไตล์
    "\u0e2d\u0e2d\u0e19\u0e44\u0e25\u0e19\u0e4c",            # ออนไลน์
    "\u0e2d\u0e2d\u0e23\u0e4c\u0e40\u0e14\u0e2d\u0e23\u0e4c",  # ออร์เดอร์
    "\u0e2d\u0e35\u0e22\u0e34\u0e1b\u0e15\u0e4c",            # อียิปต์
    "\u0e2e\u0e32\u0e23\u0e4c\u0e14\u0e41\u0e27\u0e23\u0e4c",  # ฮาร์ดแวร์
    "\u0e40\u0e04\u0e32\u0e19\u0e4c\u0e40\u0e15\u0e2d\u0e23\u0e4c",  # เคาน์เตอร์
    "\u0e40\u0e0a\u0e35\u0e22\u0e23\u0e4c",                  # เชียร์
    "\u0e40\u0e0b\u0e47\u0e01\u0e2a\u0e4c",                  # เซ็กส์
    "\u0e40\u0e0b\u0e47\u0e19\u0e40\u0e0b\u0e2d\u0e23\u0e4c",  # เซ็นเซอร์
    "\u0e40\u0e15\u0e47\u0e19\u0e17\u0e4c",                  # เต็นท์
    "\u0e40\u0e19\u0e40\u0e18\u0e2d\u0e23\u0e4c\u0e41\u0e25\u0e19\u0e14\u0e4c",  # เนเธอร์แลนด์
    "\u0e40\u0e1a\u0e23\u0e32\u0e27\u0e4c\u0e40\u0e0b\u0e2d\u0e23\u0e4c",  # เบราว์เซอร์
    "\u0e40\u0e1a\u0e2d\u0e23\u0e4c",                        # เบอร์
    "\u0e40\u0e1a\u0e35\u0e22\u0e23\u0e4c",                  # เบียร์
    "\u0e40\u0e1b\u0e2d\u0e23\u0e4c\u0e40\u0e0b\u0e47\u0e19\u0e15\u0e4c",  # เปอร์เซ็นต์
    "\u0e40\u0e1f\u0e2d\u0e23\u0e4c\u0e19\u0e34\u0e40\u0e08\u0e2d\u0e23\u0e4c",  # เฟอร์นิเจอร์
    "\u0e40\u0e21\u0e32\u0e2a\u0e4c",                        # เมาส์
    "\u0e40\u0e23\u0e14\u0e32\u0e23\u0e4c",                  # เรดาร์
    "\u0e40\u0e23\u0e32\u0e40\u0e15\u0e2d\u0e23\u0e4c",      # เราเตอร์
    "\u0e40\u0e25\u0e19\u0e2a\u0e4c",                        # เลนส์
    "\u0e40\u0e25\u0e40\u0e0b\u0e2d\u0e23\u0e4c",            # เลเซอร์
    "\u0e40\u0e27\u0e25\u0e2a\u0e4c",                        # เวลส์
    "\u0e40\u0e27\u0e47\u0e1a\u0e44\u0e0b\u0e15\u0e4c",      # เว็บไซต์
    "\u0e40\u0e2d\u0e01\u0e27\u0e32\u0e14\u0e2d\u0e23\u0e4c",  # เอกวาดอร์
    "\u0e40\u0e2d\u0e14\u0e2a\u0e4c",                        # เอดส์
    "\u0e40\u0e2d\u0e19\u0e44\u0e0b\u0e21\u0e4c",            # เอนไซม์
    "\u0e40\u0e2d\u0e40\u0e18\u0e19\u0e2a\u0e4c",            # เอเธนส์
    "\u0e40\u0e2e\u0e25\u0e34\u0e04\u0e2d\u0e1b\u0e40\u0e15\u0e2d\u0e23\u0e4c",  # เฮลิคอปเตอร์
    "\u0e41\u0e04\u0e21\u0e1b\u0e4c",                        # แคมป์
    "\u0e41\u0e08\u0e0b\u0e0b\u0e4c",                        # แจซซ์
    "\u0e41\u0e0a\u0e21\u0e1b\u0e4c",                        # แชมป์
    "\u0e41\u0e1a\u0e07\u0e01\u0e4c",                        # แบงก์
    "\u0e41\u0e1f\u0e01\u0e0b\u0e4c",                        # แฟกซ์
    "\u0e41\u0e1f\u0e23\u0e19\u0e44\u0e0a\u0e2a\u0e4c",      # แฟรนไชส์
    "\u0e41\u0e1f\u0e47\u0e01\u0e0b\u0e4c",                  # แฟ็กซ์
    "\u0e41\u0e2a\u0e15\u0e21\u0e1b\u0e4c",                  # แสตมป์
    "\u0e41\u0e2d\u0e23\u0e4c",                              # แอร์
    "\u0e41\u0e2d\u0e25\u0e01\u0e2d\u0e2e\u0e2d\u0e25\u0e4c",  # แอลกอฮอล์
    "\u0e41\u0e2e\u0e21\u0e2a\u0e40\u0e15\u0e2d\u0e23\u0e4c",  # แฮมสเตอร์
    "\u0e41\u0e2e\u0e21\u0e40\u0e1a\u0e2d\u0e23\u0e4c\u0e40\u0e01\u0e2d\u0e23\u0e4c",  # แฮมเบอร์เกอร์
    "\u0e41\u0e2e\u0e47\u0e01\u0e40\u0e01\u0e2d\u0e23\u0e4c",  # แฮ็กเกอร์
    "\u0e42\u0e04\u0e44\u0e0b\u0e19\u0e4c",                  # โคไซน์
    "\u0e42\u0e0a\u0e27\u0e4c",                              # โชว์
    "\u0e42\u0e0b\u0e19\u0e32\u0e23\u0e4c",                  # โซนาร์
    "\u0e42\u0e1b\u0e2a\u0e40\u0e15\u0e2d\u0e23\u0e4c",      # โปสเตอร์
    "\u0e42\u0e1b\u0e41\u0e25\u0e19\u0e14\u0e4c",            # โปแลนด์
    "\u0e42\u0e1e\u0e2a\u0e15\u0e4c",                        # โพสต์
    "\u0e42\u0e1f\u0e25\u0e40\u0e14\u0e2d\u0e23\u0e4c",      # โฟลเดอร์
    "\u0e42\u0e27\u0e25\u0e15\u0e4c",                        # โวลต์
    "\u0e44\u0e01\u0e14\u0e4c",                              # ไกด์
    "\u0e44\u0e0b\u0e19\u0e4c",                              # ไซน์
    "\u0e44\u0e17\u0e22\u0e41\u0e25\u0e19\u0e14\u0e4c",      # ไทยแลนด์
    "\u0e44\u0e1a\u0e15\u0e4c",                              # ไบต์
    "\u0e44\u0e1f\u0e23\u0e4c\u0e1f\u0e2d\u0e01\u0e0b\u0e4c",  # ไฟร์ฟอกซ์
    "\u0e44\u0e1f\u0e25\u0e4c",                              # ไฟล์
    "\u0e44\u0e27\u0e19\u0e4c",                              # ไวน์
    "\u0e44\u0e2d\u0e0b\u0e4c\u0e41\u0e25\u0e19\u0e14\u0e4c",  # ไอซ์แลนด์
    "\u0e44\u0e2d\u0e23\u0e4c\u0e41\u0e25\u0e19\u0e14\u0e4c",  # ไอร์แลนด์
    "\u0e44\u0e2e\u0e40\u0e1b\u0e2d\u0e23\u0e4c\u0e25\u0e34\u0e07\u0e01\u0e4c",  # ไฮเปอร์ลิงก์
)

_GENERIC_F_PRESERVING: tuple[str, ...] = (
    "\u0e04\u0e25\u0e34\u0e1f\u0e15\u0e31\u0e19",            # คลิฟตัน (place)
    "\u0e04\u0e25\u0e35\u0e1f\u0e41\u0e25\u0e19\u0e14\u0e4c",  # คลีฟแลนด์ (place)
    "\u0e04\u0e32\u0e23\u0e4c\u0e14\u0e34\u0e1f",            # คาร์ดิฟ (place)
    "\u0e04\u0e34\u0e0a\u0e34\u0e40\u0e19\u0e1f",            # คิชิเนฟ (place)
    "\u0e14\u0e36\u0e2a\u0e40\u0e0b\u0e34\u0e25\u0e14\u0e2d\u0e23\u0e4c\u0e1f",  # ดึสเซิลดอร์ฟ
    "\u0e21\u0e31\u0e25\u0e14\u0e35\u0e1f\u0e2a\u0e4c",      # มัลดีฟส์
    "\u0e21\u0e39\u0e0a\u0e32\u0e23\u0e4c\u0e23\u0e32\u0e1f",  # มูชาร์ราฟ (name)
    "\u0e23\u0e32\u0e25\u0e4c\u0e1f",                        # ราล์ฟ (name)
    "\u0e23\u0e35\u0e1f\u0e2a\u0e4c",                        # รีฟส์ (name)
    "\u0e23\u0e1f\u0e17.",                                    # รฟท. (abbrev)
    "\u0e40\u0e04\u0e35\u0e22\u0e1f",                        # เคียฟ (place)
    "\u0e40\u0e17\u0e25\u0e2d\u0e32\u0e27\u0e35\u0e1f",      # เทลอาวีฟ (place)
    "\u0e2d\u0e31\u0e1f\u0e01\u0e31\u0e19",                  # อัฟกัน
    "\u0e2d\u0e31\u0e1f\u0e01\u0e32\u0e19\u0e34\u0e2a\u0e16\u0e32\u0e19",  # อัฟกานิสถาน
    "\u0e2d\u0e31\u0e1f\u0e23\u0e34\u0e01\u0e31\u0e19",      # อัฟริกัน
    "\u0e41\u0e23\u0e19\u0e14\u0e2d\u0e25\u0e4c\u0e1f",      # แรนดอล์ฟ (name)
    "\u0e41\u0e2d\u0e1f\u0e23\u0e34\u0e01\u0e31\u0e19",      # แอฟริกัน
    "\u0e41\u0e2d\u0e1f\u0e23\u0e34\u0e01\u0e32",            # แอฟริกา
    "\u0e41\u0e2d\u0e1f\u0e23\u0e34\u0e01\u0e32\u0e43\u0e15\u0e49",  # แอฟริกาใต้
    "\u0e42\u0e08\u0e40\u0e0b\u0e1f",                        # โจเซฟ (name)
    "\u0e42\u0e22\u0e40\u0e0b\u0e1f",                        # โยเซฟ (name)
    "\u0e42\u0e23\u0e21\u0e32\u0e19\u0e2d\u0e1f",            # โรมานอฟ (name)
)


# ---------------------------------------------------------------------------
# Coda preservation overrides (practical gold set).
#
# Keys are Thai headwords; values are ``(preserved_tag, profile_set)`` —
# the surface tag the renderers will substitute for the native-collapsed
# coda, and the reading profiles under which that substitution fires.
# Preservation never fires under ``etalon_compat`` (dictionary-style
# citation forms always collapse to native phonotactics), so that
# profile is never listed here.
#
# Everyday vs careful_educated assignments follow urban-educated
# pronunciation evidence:
#
#   * Strong-preservation lexemes (preserved under both profiles) — the
#     foreign coda is the neutral everyday target. Examples: เซฟ,
#     ซอฟต์แวร์, ออฟฟิศ, ลิฟต์, เคส, อีเมล, ฟิล์ม.
#
#   * Register-sensitive lexemes (preserved only under
#     ``careful_educated``) — everyday speech collapses to the native
#     coda; careful/English-aware speech preserves. Examples: กราฟ,
#     กอล์ฟ, บัส, โพสต์, ฟุตบอล, บอล, เบส, ดิสก์, เมาส์, พอดแคสต์.
# ---------------------------------------------------------------------------

_PROFILES_ALL: frozenset[str] = frozenset({"everyday", "careful_educated"})
_PROFILES_CAREFUL: frozenset[str] = frozenset({"careful_educated"})

_CODA_PRESERVATION_OVERRIDES: dict[
    str, tuple[PreservedCodaTag, frozenset[str]]
] = {
    # --- /f/-preservation, both profiles -------------------------------
    "ลิฟต์": ("f", _PROFILES_ALL),                    # ลิฟต์
    "เซฟ": ("f", _PROFILES_ALL),                                # เซฟ
    "ซอฟต์แวร์": (                # ซอฟต์แวร์
        "f", _PROFILES_ALL,
    ),
    "ออฟฟิศ": ("f", _PROFILES_ALL),              # ออฟฟิศ
    # --- /f/-preservation, careful only --------------------------------
    "กราฟ": ("f", _PROFILES_CAREFUL),                      # กราฟ
    "กอล์ฟ": ("f", _PROFILES_CAREFUL),                # กอล์ฟ
    # --- /s/-preservation, both profiles -------------------------------
    "เคส": ("s", _PROFILES_ALL),                                # เคส
    # --- /s/-preservation, careful only --------------------------------
    "บัส": ("s", _PROFILES_CAREFUL),                            # บัส
    "โพสต์": ("s", _PROFILES_CAREFUL),                # โพสต์
    "เอดส์": ("s", _PROFILES_CAREFUL),                # เอดส์
    "พอดแคสต์": (                      # พอดแคสต์
        "s", _PROFILES_CAREFUL,
    ),
    "เมาส์": ("s", _PROFILES_CAREFUL),                # เมาส์
    "ดิสก์": ("s", _PROFILES_CAREFUL),                # ดิสก์
    "เบส": ("s", _PROFILES_CAREFUL),                            # เบส
    # --- /l/-preservation, both profiles -------------------------------
    "อีเมล": ("l", _PROFILES_ALL),                    # อีเมล
    # ฟิล์ม (/film/ ~ /fim/) is NOT listed here: preserving the /l/
    # would insert a consonant before the ``m`` coda (``fim`` →
    # ``film``) rather than swap an existing coda, and the current
    # word-level coda-override hook can only substitute one coda. The
    # entry is still listed as a collapse-only lexicon member below.
    # --- /l/-preservation, careful only --------------------------------
    "ฟุตบอล": ("l", _PROFILES_CAREFUL),          # ฟุตบอล
    "บอล": ("l", _PROFILES_CAREFUL),                            # บอล
}

# Gold-set entries that collapse under every profile. They belong in
# the lexicon so the detector's ``lexicon_hit`` signal fires, but carry
# no preservation annotation — every profile produces the native-
# collapsed reading.
_GOLDSET_COLLAPSE_ONLY: tuple[str, ...] = (
    "แอป",                                                       # แอป
    "แอปเปิล",                               # แอปเปิล
    "อินเทอร์เน็ต",  # อินเทอร์เน็ต
    "เค้ก",                                                 # เค้ก
    "โค้ด",                                                 # โค้ด
    "อิสราเอล",                         # อิสราเอล
    "ฮิปโปโปเตมัส",  # ฮิปโปโปเตมัส
    "ไมค์",                                                 # ไมค์
)


def _build_entries() -> dict[str, LoanEntry]:
    table: dict[str, LoanEntry] = {}
    # The legacy ``_ENGLISH_F_PRESERVING`` / ``_GENERIC_F_PRESERVING``
    # buckets get a default "preserve /f/ in both user-facing profiles"
    # annotation. Explicit entries in :data:`_CODA_PRESERVATION_OVERRIDES`
    # later downgrade or redirect this default (e.g. กราฟ and กอล์ฟ are
    # register-sensitive so they preserve only under ``careful_educated``).
    for word in _ENGLISH_F_PRESERVING:
        if word in table:
            raise ValueError(f"duplicate loanword entry: {word!r}")
        table[word] = LoanEntry(
            word=word,
            profile=_ENGLISH_PRESERVED_F,
            preserved_coda="f",
            preserve_in=_PROFILES_ALL,
        )
    for word in _GENERIC_F_PRESERVING:
        if word in table:
            raise ValueError(f"duplicate loanword entry: {word!r}")
        table[word] = LoanEntry(
            word=word,
            profile=_GENERIC_PRESERVED_F,
            preserved_coda="f",
            preserve_in=_PROFILES_ALL,
        )
    for word in _ENGLISH_LEXICAL_WORDS:
        if word in table:
            raise ValueError(f"duplicate loanword entry: {word!r}")
        table[word] = LoanEntry(word=word, profile=_ENGLISH_LEXICAL)
    # Gold-set additions that are not already covered by the older
    # legacy buckets above. All carry the generic lexical profile; any
    # preservation annotation is wired in by the override pass below.
    _ADDITIONAL_LEXICAL: tuple[str, ...] = (
        "เคส",                                            # เคส
        "บัส",                                            # บัส
        "อีเมล",                                # อีเมล
        "ฟิล์ม",                                # ฟิล์ม
        "ฟุตบอล",                          # ฟุตบอล
        "บอล",                                            # บอล
        "เบส",                                            # เบส
    )
    for word in _ADDITIONAL_LEXICAL:
        if word in table:
            raise ValueError(f"duplicate loanword entry: {word!r}")
        table[word] = LoanEntry(word=word, profile=_ENGLISH_LEXICAL)
    for word in _GOLDSET_COLLAPSE_ONLY:
        if word in table:
            continue  # already covered above; no preservation override
            # fires for this word in any profile.
        table[word] = LoanEntry(word=word, profile=_ENGLISH_LEXICAL)
    # Merge preservation-override metadata into the built entries. Every
    # override key must resolve to a pre-existing entry — this catches
    # typos early rather than silently losing preservation. Overrides
    # replace any default annotation applied above.
    for word, (tag, profiles) in _CODA_PRESERVATION_OVERRIDES.items():
        if word not in table:
            raise ValueError(
                f"coda-preservation override for unknown word: {word!r}"
            )
        base = table[word]
        table[word] = LoanEntry(
            word=base.word,
            profile=base.profile,
            preserved_coda=tag,
            preserve_in=profiles,
        )
    return table


LOANWORDS: Mapping[str, LoanEntry] = MappingProxyType(_build_entries())
"""Canonical loanword table keyed on the NFC Thai headword."""


def get_entry(word: str) -> LoanEntry | None:
    """Return the :class:`LoanEntry` for ``word`` or ``None`` if absent."""
    return LOANWORDS.get(word)


def words_by_coda_policy(policy: CodaPolicy) -> frozenset[str]:
    """Return the set of headwords whose profile has the given coda policy."""
    return frozenset(
        word for word, entry in LOANWORDS.items()
        if entry.profile.coda_policy == policy
    )


def get_preserved_coda(word: str, profile: str) -> PreservedCodaTag | None:
    """Return the preserved-coda tag for ``word`` under ``profile``.

    Returns ``None`` when the word is absent from :data:`LOANWORDS`,
    when the entry has no preservation annotation, or when the caller's
    profile is not in the entry's ``preserve_in`` set. ``etalon_compat``
    is never present in any entry's ``preserve_in``, so it always yields
    ``None`` — dictionary-style citation forms always collapse to
    native phonotactics.
    """
    entry = LOANWORDS.get(word)
    if entry is None or entry.preserved_coda is None:
        return None
    if profile not in entry.preserve_in:
        return None
    return entry.preserved_coda


__all__ = [
    "CodaPolicy",
    "Confidence",
    "LOANWORDS",
    "LoanEntry",
    "LoanProfile",
    "PreservedCodaTag",
    "SourceLanguage",
    "TonePolicy",
    "VowelLengthPolicy",
    "get_entry",
    "get_preserved_coda",
    "words_by_coda_policy",
]

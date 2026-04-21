"""Heuristic foreignness detector for Thai words.

The detector produces a bounded ``is_loanword`` score together with the
signals that contributed to it. It is intentionally conservative: the
signal list is an audit trail a downstream caller (e.g. the precedence
pipeline) can inspect, not just a number. The score is derived from
orthographic and lexical cues only — no phonological derivation is
attempted here.

The canonical loanword table (:mod:`loanword`) short-circuits the
analysis to ``1.0`` when the exact headword is listed, so curated
entries always dominate heuristic evidence. For out-of-lexicon words the
detector combines weak signals (thanthakhat killer mark, ฟ-initial
onset, orthographically foreign clusters, word length) against
native-prefix and short-word signals that push the score back down.

Weights are module-level constants so they can be tuned from tests
without editing logic; rationale comments accompany each weight.
"""

from __future__ import annotations

from dataclasses import dataclass

from thaiphon.lexicons.loanword import LOANWORDS
from thaiphon.model.letters import THANTHAKHAT

# ---------------------------------------------------------------------------
# Weights
#
# A lexicon hit is a definitive curator signal and clamps the output to
# 1.0 immediately; we still list the weight for symmetry and to document
# the intent.
# ---------------------------------------------------------------------------

WEIGHT_LEXICON_HIT: float = 1.0
"""Exact-match hit in :data:`LOANWORDS` — fully trusted."""

WEIGHT_THANTHAKHAT: float = 0.35
"""Word contains at least one ◌์. Strong but not conclusive: Sanskrit
fossils (จันทร์, ศักดิ์) also carry ◌์ without being modern loans."""

WEIGHT_ONSET_FO_FAN: float = 0.25
"""Word begins with ฟ. ฟ-initial native Thai words exist but they are a
small, closed set dominated by loans (ฟิล์ม, ฟุตบอล, ฟรี ...)."""

WEIGHT_NON_NATIVE_CLUSTER: float = 0.30
"""Applied once per prefix that matches the word's start. Prefixes in
:data:`_NON_NATIVE_CLUSTER_PREFIXES` cover attested loan onsets whose
consonant+consonant or vowel+coda shape is absent from native Thai."""

WEIGHT_LENGTH_GE_5: float = 0.10
"""Long words are disproportionately Indic-learned or modern loans. Weak
signal — stacks with the real cues above rather than standing alone."""

WEIGHT_MULTIPLE_KILLERS: float = 0.15
"""Two or more ◌์ in one word is highly atypical for native Thai and
strongly suggests a multi-morpheme loan (ซอฟต์แวร์, บุฟเฟ่ต์)."""

WEIGHT_CODA_FO_FAN: float = 0.35
"""Word ends in ฟ (optionally followed by ◌์). Native Thai codas never
surface as /f/; every attested word shape ending in ฟ is a modern loan
(เชฟ, เซฟ, กราฟ, บรีฟ). Complements the ``onset_fo_fan`` signal so
short words without any other cue still cross the heuristic threshold."""

WEIGHT_MEDIAL_FO_FAN: float = 0.20
"""Word contains ฟ somewhere other than the first or last position.
Attested almost exclusively in multi-morpheme loans (ทิฟฟานี่,
เชฟโรเลต, แดฟโฟดิล)."""

WEIGHT_NATIVE_SHORT: float = -0.50
"""Word is in the short native-word allow list. Dominant negative
signal for closed-class function words and everyday nouns."""

WEIGHT_NATIVE_PREFIX: float = -0.30
"""Word starts with a productive native derivational prefix
(การ-, ความ-, ผู้-, นัก-, เครื่อง-). These derive from native roots and
are never loanword carriers."""


# ---------------------------------------------------------------------------
# Lookup tables
# ---------------------------------------------------------------------------

_NON_NATIVE_CLUSTER_PREFIXES: tuple[str, ...] = (
    "\u0e0b\u0e2d\u0e1f",                  # ซอฟ
    "\u0e1f\u0e23",                        # ฟร
    "\u0e1f\u0e25",                        # ฟล
    "\u0e41\u0e2d\u0e1b",                  # แอป
    "\u0e04\u0e2d\u0e21",                  # คอม
    "\u0e1a\u0e32\u0e23\u0e4c",            # บาร์
    "\u0e40\u0e19\u0e47\u0e15",            # เน็ต
    "\u0e44\u0e2e",                        # ไฮ
    "\u0e1f\u0e38\u0e15",                  # ฟุต
    "\u0e2a\u0e15\u0e32\u0e23\u0e4c",      # สตาร์
    "\u0e01\u0e23\u0e32\u0e1f",            # กราฟ
    "\u0e01\u0e23\u0e4a\u0e32\u0e1f",      # กร๊าฟ
    "\u0e25\u0e34\u0e1f",                  # ลิฟ
    "\u0e2d\u0e2d\u0e1f",                  # ออฟ
    "\u0e44\u0e21\u0e42\u0e04\u0e23",      # ไมโคร
    "\u0e01\u0e2d\u0e25\u0e4c",            # กอล์
)

_NATIVE_SHORT: frozenset[str] = frozenset(
    {
        "\u0e41\u0e21\u0e48",               # แม่
        "\u0e1e\u0e48\u0e2d",               # พ่อ
        "\u0e44\u0e1b",                     # ไป
        "\u0e21\u0e32",                     # มา
        "\u0e01\u0e34\u0e19",               # กิน
        "\u0e14\u0e37\u0e48\u0e21",         # ดื่ม
        "\u0e44\u0e14\u0e49",               # ได้
        "\u0e2d\u0e22\u0e39\u0e48",         # อยู่
        "\u0e44\u0e21\u0e48",               # ไม่
        "\u0e43\u0e0a\u0e48",               # ใช่
        "\u0e19\u0e35\u0e48",               # นี่
        "\u0e19\u0e31\u0e48\u0e19",         # นั่น
        "\u0e1a\u0e49\u0e32\u0e19",         # บ้าน
        "\u0e23\u0e31\u0e01",               # รัก
        "\u0e14\u0e35",                     # ดี
        "\u0e2b\u0e21\u0e32",               # หมา
        "\u0e41\u0e21\u0e27",               # แมว
        "\u0e19\u0e49\u0e33",               # น้ำ
        "\u0e04\u0e19",                     # คน
        "\u0e40\u0e02\u0e32",               # เขา
        "\u0e40\u0e23\u0e32",               # เรา
        "\u0e09\u0e31\u0e19",               # ฉัน
        "\u0e19\u0e32\u0e22",               # นาย
        "\u0e1e\u0e35\u0e48",               # พี่
        "\u0e19\u0e49\u0e2d\u0e07",         # น้อง
        "\u0e25\u0e39\u0e01",               # ลูก
        "\u0e15\u0e32",                     # ตา
        "\u0e22\u0e32\u0e22",               # ยาย
        "\u0e1b\u0e39\u0e48",               # ปู่
        "\u0e22\u0e48\u0e32",               # ย่า
    }
)

_NATIVE_PREFIXES: tuple[str, ...] = (
    "\u0e01\u0e32\u0e23",                  # การ
    "\u0e04\u0e27\u0e32\u0e21",            # ความ
    "\u0e1c\u0e39\u0e49",                  # ผู้
    "\u0e19\u0e31\u0e01",                  # นัก
    "\u0e40\u0e04\u0e23\u0e37\u0e48\u0e2d\u0e07",  # เครื่อง
)

_FO_FAN: str = "\u0e1f"                    # ฟ

# Orthographic finals that may retain a foreign articulation in modern
# loanwords. Native Thai phonotactics collapse these through the M-301
# 26-to-6 coda merge (so-so-sala and so-rusi collapse to /t/,
# lo-ling and ro-rua collapse to /n/, fo-fan collapses to /p/, ko-kai
# stays /k/). In loan vocabulary the foreign articulation survives more
# often than not (English "bus", "case", "file", "elf", ...). Values
# are the scheme-neutral tags reported via
# :attr:`LoanAnalysis.preserved_coda_candidate`.
_PRESERVED_FINAL_TAG: dict[str, str] = {
    "\u0e1f": "f",   # ฟ
    "\u0e2a": "s",   # ส
    "\u0e28": "s",   # ศ
    "\u0e29": "s",   # ษ
    "\u0e25": "l",   # ล
    "\u0e23": "r",   # ร
    "\u0e01": "k",   # ก
}


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class LoanAnalysis:
    """Outcome of :func:`score_foreignness`.

    Fields
    ------
    is_loanword
        Score in ``[0.0, 1.0]`` — clamped. ``1.0`` means the word is in
        the curated loanword table; values above ``0.6`` indicate high
        heuristic confidence; values below ``0.2`` indicate a native
        reading is overwhelmingly likely.
    signals
        Tuple of short string tags in the order they fired. Signals with
        a parametric payload use the ``"name:payload"`` form (e.g.
        ``"non_native_cluster:ซอฟ"``). Intended for logging and for
        pipeline stages that want to gate behaviour on a specific cue.
    preserved_coda_candidate
        ``"f"`` if the surface form ends in ``ฟ`` or ``ฟ์`` — the only
        coda the current lexicon/renderer pair treats as "preserve the
        foreign realisation". ``None`` for all other endings. This is
        purely an orthographic observation; the pipeline's actual coda
        decision still runs through the loanword profile and renderer.
    """

    is_loanword: float
    signals: tuple[str, ...]
    preserved_coda_candidate: str | None


# ---------------------------------------------------------------------------
# Core entry point
# ---------------------------------------------------------------------------


def _detect_preserved_coda(word: str) -> str | None:
    """Tag the word-final consonant that is a candidate for foreign-coda
    preservation, or ``None`` when the word does not end in one.

    The walk is right-to-left: trailing ``(consonant + thanthakhat)``
    pairs are stripped one at a time, so the tag reflects the last
    *audible* consonant rather than the last written one. Native Thai
    phonology already drops the killed letter, so the audible coda is
    the preceding consonant (when there is one). Examples:

    * ``กราฟ`` ends in a bare ฟ -> ``"f"``.
    * ``ลิฟต์`` ends in killed ต preceded by ฟ -> ``"f"``.
    * ``ดิสก์`` ends in killed ก preceded by ส -> ``"s"``.
    * ``เอลฟ์`` ends in killed ฟ preceded by ล -> ``"l"``.
    * ``แอร์`` ends in killed ร preceded by a vowel (อ) -> ``None``
      (no audible coda to preserve; the /r/ signal is purely
      orthographic and only the overall foreignness score keeps the
      analysis flagged).

    The tags are the single-letter forms consumed downstream by the
    TLC renderer override: ``"f"`` (ฟ), ``"s"`` (ส/ศ/ษ), ``"l"`` (ล),
    ``"r"`` (ร), ``"k"`` (ก).
    """
    if not word:
        return None
    i = len(word)
    while i >= 2 and word[i - 1] == THANTHAKHAT:
        i -= 2
    if i <= 0:
        return None
    return _PRESERVED_FINAL_TAG.get(word[i - 1])


def score_foreignness(word: str) -> LoanAnalysis:
    """Compute a bounded foreignness score for ``word``.

    The score is the clipped sum of the weighted signals documented on
    the module-level ``WEIGHT_*`` constants. A lexicon hit short-circuits
    every other signal and returns ``1.0``; for unknown inputs the
    detector combines orthographic cues with a native-word penalty.
    """
    preserved = _detect_preserved_coda(word)

    if not word:
        return LoanAnalysis(
            is_loanword=0.0,
            signals=(),
            preserved_coda_candidate=preserved,
        )

    # Lexicon hit — definitive, short-circuit.
    if word in LOANWORDS:
        return LoanAnalysis(
            is_loanword=1.0,
            signals=("lexicon_hit",),
            preserved_coda_candidate=preserved,
        )

    signals: list[str] = []
    score = 0.0

    killer_count = word.count(THANTHAKHAT)
    if killer_count >= 1:
        signals.append("thanthakhat")
        score += WEIGHT_THANTHAKHAT
    if killer_count >= 2:
        signals.append("multiple_killers")
        score += WEIGHT_MULTIPLE_KILLERS

    if word.startswith(_FO_FAN):
        signals.append("onset_fo_fan")
        score += WEIGHT_ONSET_FO_FAN

    if preserved == "f":
        signals.append("coda_fo_fan")
        score += WEIGHT_CODA_FO_FAN
    elif _FO_FAN in word[1:-1]:
        signals.append("medial_fo_fan")
        score += WEIGHT_MEDIAL_FO_FAN

    for prefix in _NON_NATIVE_CLUSTER_PREFIXES:
        if word.startswith(prefix):
            signals.append(f"non_native_cluster:{prefix}")
            score += WEIGHT_NON_NATIVE_CLUSTER

    if len(word) >= 5:
        signals.append("length_ge_5")
        score += WEIGHT_LENGTH_GE_5

    if word in _NATIVE_SHORT:
        signals.append("native_short")
        score += WEIGHT_NATIVE_SHORT

    for prefix in _NATIVE_PREFIXES:
        if word.startswith(prefix):
            signals.append("native_prefix")
            score += WEIGHT_NATIVE_PREFIX
            break

    # Clamp to [0.0, 1.0].
    if score < 0.0:
        score = 0.0
    elif score > 1.0:
        score = 1.0

    return LoanAnalysis(
        is_loanword=score,
        signals=tuple(signals),
        preserved_coda_candidate=preserved,
    )


__all__ = [
    "LoanAnalysis",
    "WEIGHT_CODA_FO_FAN",
    "WEIGHT_LENGTH_GE_5",
    "WEIGHT_LEXICON_HIT",
    "WEIGHT_MEDIAL_FO_FAN",
    "WEIGHT_MULTIPLE_KILLERS",
    "WEIGHT_NATIVE_PREFIX",
    "WEIGHT_NATIVE_SHORT",
    "WEIGHT_NON_NATIVE_CLUSTER",
    "WEIGHT_ONSET_FO_FAN",
    "WEIGHT_THANTHAKHAT",
    "score_foreignness",
]

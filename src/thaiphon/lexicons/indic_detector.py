"""Orthographic detector for Indic-learned candidate words.

Returns True when a Thai word shows strong orthographic signals of
Indic/Pali/Sanskrit origin and therefore warrants the productive
learned-reading pass (final short-vowel preservation + linking /a/
insertion).

The detector is intentionally conservative: it only fires on combinations
that are rare in native-Thai vocabulary. Words matching an Indic lexicon
entry are handled earlier in the pipeline; this detector only guides the
syllabification strategy when no lexicon match exists.
"""

from __future__ import annotations

from thaiphon.model.letters import THANTHAKHAT, TONE_MARKS

#: Distinctly Indic/Pali/Sanskrit letters with effectively zero native-Thai
#: high-frequency use. Any occurrence strongly implies a learned reading.
INDIC_LETTERS: frozenset[str] = frozenset(
    {"\u0e0e", "\u0e0f", "\u0e10", "\u0e11", "\u0e12", "\u0e13"}
    # ฎ ฏ ฐ ฑ ฒ ณ
)

#: Learned Indic endings (consonant + short vowel that stays pronounced).
#: Each entry is a length-2 suffix string matched against the cleaned word.
INDIC_ENDINGS: frozenset[str] = frozenset(
    {
        "\u0e15\u0e34",  # ติ
        "\u0e18\u0e34",  # ธิ
        "\u0e17\u0e34",  # ทิ
        "\u0e19\u0e30",  # นะ
        "\u0e23\u0e30",  # ระ
        "\u0e27\u0e30",  # วะ
        "\u0e20\u0e38",  # ภุ
        "\u0e01\u0e38",  # กุ
        "\u0e15\u0e38",  # ตุ
        "\u0e22\u0e30",  # ยะ
        "\u0e28\u0e30",  # ศะ
        "\u0e29\u0e30",  # ษะ
        "\u0e11\u0e30",  # ฑะ
        "\u0e13\u0e30",  # ณะ
        "\u0e18\u0e30",  # ธะ
    }
)

# Words containing ศ or ษ as a native Thai everyday form where those letters
# behave like native /s/. The Indic-letter check does not include ศ/ษ (they
# appear in enough native everyday words to make ศ/ษ too weak a single
# signal); this whitelist covers the rare cases where another signal would
# otherwise fire.
_THAI_SR_COMMON: frozenset[str] = frozenset(
    {
        "\u0e28\u0e23\u0e35",                          # ศรี
        "\u0e28\u0e39\u0e19\u0e22\u0e4c",              # ศูนย์
        "\u0e28\u0e39\u0e19",                          # ศูน
    }
)


def _strip_marks(s: str) -> str:
    """Remove tone marks and thanthakhat — they don't affect detector logic."""
    return "".join(c for c in s if c not in TONE_MARKS and c != THANTHAKHAT)


def is_indic_candidate(word: str) -> bool:
    """Return True when ``word`` shows Indic/Pali/Sanskrit orthographic signals.

    Signal order (any one fires):

    1. Contains a distinctly-Indic letter (ฏ ฐ ฑ ฒ ณ).
    2. Ends in a learned Indic ending (ติ ธิ ทิ นะ ระ วะ ภุ กุ ตุ ยะ ...).

    The detector is deliberately narrow. A pure "invalid internal cluster"
    check was considered but discarded: it over-fires on native Thai
    inherent-/o/ closed monosyllables (``ผม``, ``กน``, ``บก``...) where the
    second consonant serves as a coda. Distinguishing inherent-/o/ natives
    from Indic linkers from orthography alone is not reliable; we rely on
    lexical signals (1) and morphological endings (2) instead.
    """
    if not word:
        return False
    stripped = _strip_marks(word)
    if not stripped:
        return False

    # Whitelist: a few Thai everyday words with ศ/ษ patterns that do not
    # warrant Indic treatment.
    if word in _THAI_SR_COMMON or stripped in _THAI_SR_COMMON:
        return False

    # Signal 1: distinctly-Indic letter.
    if any(ch in INDIC_LETTERS for ch in stripped):
        return True

    # Signal 2: learned Indic ending (only when the word is long enough for
    # the ending to be meaningful — i.e. at least one consonant + vowel
    # before the ending).
    if len(stripped) >= 3:
        for ending in INDIC_ENDINGS:
            if stripped.endswith(ending):
                return True

    return False


__all__ = ["INDIC_ENDINGS", "INDIC_LETTERS", "is_indic_candidate"]

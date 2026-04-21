"""Vowel quality + length resolution (M-200, M-203, M-206, M-308, M-600, M-204)."""

from __future__ import annotations

from dataclasses import dataclass

from thaiphon.errors import ParseError
from thaiphon.model.enums import VowelLength
from thaiphon.model.letters import (
    MAI_HAN_AKAT,
    MAITAIKHU,
    O_ANG,
    RO_RUA,
    SARA_A,
    SARA_AA,
    SARA_AE,
    SARA_AI_MAIMALAI,
    SARA_AI_MAIMUAN,
    SARA_AM,
    SARA_E,
    SARA_I,
    SARA_II,
    SARA_O,
    SARA_U,
    SARA_UE,
    SARA_UEE,
    SARA_UU,
    TONE_MARKS,
    WO_WAEN,
    YO_YAK,
)


@dataclass(frozen=True, slots=True)
class VowelAnalysis:
    quality: str  # IPA quality symbol, e.g. "a", "iː" not yet — just "i" + length
    length: VowelLength
    inserted_vowel: bool = False
    offglide: str | None = None
    notes: tuple[str, ...] = ()


# Simple above/below/after vowel marks: (mark, length, IPA quality).
_SIMPLE_MARKS: dict[str, tuple[str, VowelLength]] = {
    SARA_I: ("i", VowelLength.SHORT),
    SARA_II: ("i", VowelLength.LONG),
    SARA_UE: ("ɯ", VowelLength.SHORT),
    SARA_UEE: ("ɯ", VowelLength.LONG),
    SARA_U: ("u", VowelLength.SHORT),
    SARA_UU: ("u", VowelLength.LONG),
    MAI_HAN_AKAT: ("a", VowelLength.SHORT),
}


def _strip_tones(s: str) -> str:
    return "".join(c for c in s if c not in TONE_MARKS)


def resolve_vowel(
    syllable_chars: str,
    onset_consumed: int,
    has_final: bool,
    tone_mark_present: bool,
    final_char: str | None = None,
) -> VowelAnalysis:
    """Resolve vowel quality + length for a single syllable.

    `syllable_chars` is the full raw syllable. `onset_consumed` is the
    absolute offset into the (tone-stripped) string where vowel material
    begins — i.e. any leading pre-vowel plus onset consonants already count.
    """
    del tone_mark_present  # reserved; current analysis doesn't branch on it

    # Work on a tone-stripped copy so we can pattern-match cleanly.
    s = _strip_tones(syllable_chars)

    # Pre-base vowels (เ แ โ ใ ไ) — need special handling; they appear before onset.
    pre = s[0] if s else ""

    if pre == SARA_AI_MAIMUAN:
        # ใ — always short /a/ + /j/ offglide; LIVE syllable.
        return VowelAnalysis("a", VowelLength.SHORT, offglide="j")
    if pre == SARA_AI_MAIMALAI:
        # ไ — same surface behaviour as ใ.
        return VowelAnalysis("a", VowelLength.SHORT, offglide="j")

    # เ◌ family.
    if pre == SARA_E:
        # `onset_consumed` is absolute (includes the pre-vowel).
        rest = s[onset_consumed:]  # chars after เ + onset
        # เ◌า — /aw/, short open, LIVE (special).
        if rest.startswith(SARA_AA):
            # เอา = aw short LIVE. Check for ะ at end → เ◌าะ → /ɔ/ short.
            if rest == SARA_AA + SARA_A:
                return VowelAnalysis("ɔ", VowelLength.SHORT)
            # เ◌าะ + final → ◌็อ closed variant (handled via MAITAIKHU pattern)
            return VowelAnalysis("a", VowelLength.SHORT, offglide="w")
        # เ◌ียะ / เ◌ีย — centring diphthong /iə/.
        if rest.startswith(SARA_II + YO_YAK):
            # R-CENT-001 Case B: เ◌ียว is /iː/ + /w/, NOT centring /iːə/.
            # When ``_find_final`` has extracted ``ว`` as the coda the ย
            # that survives in ``rest`` was orthographic filler for the
            # /iː/ nucleus — there is no centring offglide before /w/.
            if final_char == WO_WAEN:
                return VowelAnalysis("i", VowelLength.LONG)
            # เ◌ียะ short, เ◌ีย long.
            tail = rest[2:]
            if tail == SARA_A:
                return VowelAnalysis("iə", VowelLength.SHORT)
            # long: with or without final.
            return VowelAnalysis("iə", VowelLength.LONG)
        # เ◌ือะ / เ◌ือ — centring diphthong /ɯə/.
        if rest.startswith(SARA_UEE + O_ANG):
            tail = rest[2:]
            if tail == SARA_A:
                return VowelAnalysis("ɯə", VowelLength.SHORT)
            return VowelAnalysis("ɯə", VowelLength.LONG)
        # เ◌อ / เ◌อะ — /ɤ/. With final ย → เ◌ย (short /ɤ/).
        if rest.startswith(O_ANG):
            tail = rest[1:]
            if tail == SARA_A:
                return VowelAnalysis("ɤ", VowelLength.SHORT)
            return VowelAnalysis("ɤ", VowelLength.LONG)
        # เ◌ิ◌ — short /ɤ/ closed (M-203 เ◌อ + final → เ◌ิ + final)
        if rest.startswith(SARA_I):
            return VowelAnalysis("ɤ", VowelLength.SHORT)
        # เ◌ย — short /ɤ/ + /j/ offglide (M-204 allomorph of เ◌อ + ย).
        # Template must fire BEFORE the fallback long /eː/ branch below.
        # ``_find_final`` has already consumed ย as the coda, so ``rest``
        # is empty and the raw ย only survives through ``final_char``.
        if rest == "" and final_char == YO_YAK:
            return VowelAnalysis("ɤ", VowelLength.SHORT, offglide="j")
        # เ◌็◌ — short /e/ closed (M-203 เ◌ะ + final → เ◌็ + final)
        if rest.startswith(MAITAIKHU):
            return VowelAnalysis("e", VowelLength.SHORT)
        # เ◌ะ — short /e/, open.
        if rest == SARA_A:
            return VowelAnalysis("e", VowelLength.SHORT)
        # เ◌ + final or bare เ◌ (long /eː/).
        # If rest is empty → open long /e/; if rest contains consonant(s) → long closed.
        return VowelAnalysis("e", VowelLength.LONG)

    if pre == SARA_AE:
        rest = s[onset_consumed:]
        # แ◌ะ — short /ɛ/.
        if rest == SARA_A:
            return VowelAnalysis("ɛ", VowelLength.SHORT)
        # แ◌็◌ — short /ɛ/ closed.
        if rest.startswith(MAITAIKHU):
            return VowelAnalysis("ɛ", VowelLength.SHORT)
        # แ◌ / แ◌◌ — long /ɛː/.
        return VowelAnalysis("ɛ", VowelLength.LONG)

    if pre == SARA_O:
        rest = s[onset_consumed:]
        if rest == SARA_A:
            return VowelAnalysis("o", VowelLength.SHORT)
        # โ◌ / โ◌◌ — long /oː/.
        return VowelAnalysis("o", VowelLength.LONG)

    # No pre-base vowel. Examine post-onset portion.
    rest = s[onset_consumed:]

    # Post-base อ carrier: C + อ → long /ɔː/ open. C + อ + final collapses
    # to long /ɔː/ closed (the final char was already extracted by the
    # caller so we only need to check the remaining orthographic fragment).
    if rest.startswith(O_ANG) and (len(rest) == 1):
        return VowelAnalysis("ɔ", VowelLength.LONG)

    # R-202 closed short /ɔ/ allomorph: C + ◌็ + อ + coda. Must match
    # BEFORE the generic MAITAIKHU fallback below so ล็อค, น็อค, ช็อป
    # read with a SHORT /ɔ/ nucleus rather than /o/.
    if rest.startswith(MAITAIKHU + O_ANG):
        return VowelAnalysis("ɔ", VowelLength.SHORT)

    # Sara Am ◌ำ — /am/ short, LIVE (special; M-600).
    if SARA_AM in rest:
        return VowelAnalysis("a", VowelLength.SHORT, offglide="m")

    # ◌ะ — short /a/ open.
    if rest == SARA_A:
        return VowelAnalysis("a", VowelLength.SHORT)

    # ◌า — long /aː/ open (or closed with trailing consonant).
    if rest.startswith(SARA_AA):
        return VowelAnalysis("a", VowelLength.LONG)

    # ◌ั◌ — short /a/ closed (M-203 ะ + final → ั + final).
    if rest.startswith(MAI_HAN_AKAT):
        # ◌ัว — /ua/ centring diphthong.
        if rest.startswith(MAI_HAN_AKAT + WO_WAEN):
            tail = rest[2:]
            if tail == "":
                return VowelAnalysis("uə", VowelLength.LONG)
            # ◌ัว◌ closed.
            return VowelAnalysis("uə", VowelLength.LONG)
        return VowelAnalysis("a", VowelLength.SHORT)

    # R-CD-004: closed /uːə/ written as C + ว + coda with the ◌ั dropped.
    # After `_find_final` has extracted the trailing coda, the only thing
    # left after the onset is the bare ว. Example: ``ชวน`` → onset=ช,
    # final=น, rest=ว → nucleus /uə/ long. Open ว syllables without a
    # coda (e.g. ``วัน``, ``วง``) never land here — those carry ว as the
    # onset, so ``rest`` would not start with ว for them.
    if rest == WO_WAEN:
        return VowelAnalysis("uə", VowelLength.LONG)

    # Simple above/below marks.
    for mark, (quality, length) in _SIMPLE_MARKS.items():
        if rest.startswith(mark):
            return VowelAnalysis(quality, length)

    # ◌็◌ — short-vowel marker; depends on pre-vowel (already handled) or
    # bare use after onset is uncommon. Treat as short /o/.
    if rest.startswith(MAITAIKHU):
        return VowelAnalysis("o", VowelLength.SHORT)

    # No explicit vowel letter at all — M-206 / M-308 inherent-vowel.
    if rest == "":
        # M-206: closed syllable with no written vowel → inherent short /o/.
        # Open syllable → inherent short /a/.
        if has_final:
            return VowelAnalysis("o", VowelLength.SHORT, inserted_vowel=True)
        return VowelAnalysis("a", VowelLength.SHORT, inserted_vowel=True)

    # Closed with no written vowel.
    # M-308: if coda is ร → long /ɔː/ with /n/ coda (caller still uses coda-collapse).
    # We signal the vowel here; the coda resolver already returns /n/ for ร.
    if len(rest) == 1 and rest in (RO_RUA,):
        return VowelAnalysis("ɔ", VowelLength.LONG, inserted_vowel=True)

    # Closed syllable, multiple consonants with no written vowel → short /o/.
    if all(ch not in _SIMPLE_MARKS and ch != SARA_A and ch != SARA_AA for ch in rest):
        # Heuristic: if the first trailing char is a "ร" coda → M-308.
        if rest == RO_RUA:
            return VowelAnalysis("ɔ", VowelLength.LONG, inserted_vowel=True)
        return VowelAnalysis("o", VowelLength.SHORT, inserted_vowel=True)

    raise ParseError(f"unrecognised vowel pattern: {syllable_chars!r}")


__all__ = ["VowelAnalysis", "resolve_vowel"]

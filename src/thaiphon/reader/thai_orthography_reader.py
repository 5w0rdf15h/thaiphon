from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from thaiphon.errors import ThaiphonError
from thaiphon.phonology.model import (
    Coda,
    FinalType,
    Onset,
    PhonologicalWord,
    Syllable,
    Tone,
    Vowel,
    VowelLength,
)


class OrthographyError(ThaiphonError):
    pass


# --- Thai character sets

THAI_TONE_MARKS = {"่", "้", "๊", "๋"}
THANTHAKHAT = "์"
NIKHAHIT = "ํ"  # used in ำ
MAITAIKHU = "็"
SARA_AM = "ำ"

PREPOSED_VOWELS = {"เ", "แ", "โ", "ใ", "ไ"}  # appear before onset
POSTPOSED_VOWELS = {"ะ", "า", "ิ", "ี", "ึ", "ื", "ุ", "ู", "ๅ"}  # appear after onset
# Add sara a-close (ั) to "marks above/below" so syllable splitting can treat it like other marks
ABOVE_BELOW_SIGNS = {"็", "่", "้", "๊", "๋", "์", "ํ", "ั", "ิ", "ี", "ึ", "ื", "ุ", "ู", "ๅ"}
# Thai consonants
THAI_CONSONANTS = set("กขฃคฅฆงจฉชซฌญฎฏฐฑฒณดตถทธนบปผฝพฟภมยรลวศษสหฬอฮฤฦ")

# Sonorants used with leading ห (ห นำ)
LEADING_H_SONORANTS = set("งญนมยรลว")

# --- Consonant class (for tone rules)
MID_CLASS = set("กจฎฏดตบปอ")
HIGH_CLASS = set("ขฃฉฐถผฝศษสห")
LOW_CLASS = set("คฅฆชซฌญฑฒณทธนพฟภมยรลวฬฮง")

# --- Phoneme mapping (canonical symbols used in model)
# Initial consonants (onset c1)
INITIAL_PHONEME = {
    "ก": "k",
    "ข": "kʰ",
    "ฃ": "kʰ",
    "ค": "kʰ",
    "ฅ": "kʰ",
    "ฆ": "kʰ",
    "ง": "ŋ",
    "จ": "tɕ",
    "ฉ": "tɕʰ",
    "ช": "tɕʰ",
    "ซ": "s",
    "ฌ": "tɕʰ",
    "ญ": "j",  # as onset often /j/
    "ฎ": "d",
    "ฏ": "t",
    "ฐ": "tʰ",
    "ฑ": "tʰ",
    "ฒ": "tʰ",
    "ณ": "n",
    "ด": "d",
    "ต": "t",
    "ถ": "tʰ",
    "ท": "tʰ",
    "ธ": "tʰ",
    "น": "n",
    "บ": "b",
    "ป": "p",
    "ผ": "pʰ",
    "ฝ": "f",
    "พ": "pʰ",
    "ฟ": "f",
    "ภ": "pʰ",
    "ม": "m",
    "ย": "j",
    "ร": "r",
    "ล": "l",
    "ว": "w",
    "ศ": "s",
    "ษ": "s",
    "ส": "s",
    "ห": "h",
    "ฬ": "l",
    "อ": "",  # carrier or glottal onset; handled specially
    "ฮ": "h",
    "ฤ": "r",
    "ฦ": "l",
}

# Final consonants (coda)
# Thai final inventory is limited (k, t, p, m, n, ŋ, j, w)
FINAL_PHONEME = {
    "ก": ("k", FinalType.STOP),
    "ข": ("k", FinalType.STOP),
    "ฃ": ("k", FinalType.STOP),
    "ค": ("k", FinalType.STOP),
    "ฅ": ("k", FinalType.STOP),
    "ฆ": ("k", FinalType.STOP),
    "ด": ("t", FinalType.STOP),
    "ต": ("t", FinalType.STOP),
    "ถ": ("t", FinalType.STOP),
    "ท": ("t", FinalType.STOP),
    "ธ": ("t", FinalType.STOP),
    "ฎ": ("t", FinalType.STOP),
    "ฏ": ("t", FinalType.STOP),
    "ฐ": ("t", FinalType.STOP),
    "ฑ": ("t", FinalType.STOP),
    "ฒ": ("t", FinalType.STOP),
    "ศ": ("t", FinalType.STOP),
    "ษ": ("t", FinalType.STOP),
    "ส": ("t", FinalType.STOP),
    "จ": ("t", FinalType.STOP),
    "ฉ": ("t", FinalType.STOP),
    "ช": ("t", FinalType.STOP),
    "ซ": ("t", FinalType.STOP),
    "ฌ": ("t", FinalType.STOP),
    "บ": ("p", FinalType.STOP),
    "ป": ("p", FinalType.STOP),
    "พ": ("p", FinalType.STOP),
    "ฟ": ("p", FinalType.STOP),
    "ภ": ("p", FinalType.STOP),
    "ม": ("m", FinalType.SONORANT),
    "น": ("n", FinalType.SONORANT),
    "ณ": ("n", FinalType.SONORANT),
    "ญ": ("n", FinalType.SONORANT),  # in final position often /n/
    "ร": ("n", FinalType.SONORANT),  # final ร is /n/ in most modern Thai
    "ล": ("n", FinalType.SONORANT),
    "ฬ": ("n", FinalType.SONORANT),
    "ง": ("ŋ", FinalType.SONORANT),
    "ย": ("j", FinalType.SONORANT),
    "ว": ("w", FinalType.SONORANT),
}

# Allowed onset clusters: C + {r,l,w} (typical Thai)
CLUSTER_SECONDS = {"ร": "r", "ล": "l", "ว": "w"}
TRUE_CLUSTERS = {
    "กร",
    "กล",
    "กว",
    "ขร",
    "ขล",
    "ขว",
    "คร",
    "คล",
    "คว",
    "ปร",
    "ปล",
    "พร",
    "พล",
    "ตร",
    "ดร",  # loanwords: ไฮโดร-, ดรัม-, ดราม่า-, etc.
    # treat ฃ like ข for cluster purposes (needed for ฃวด)
    "ฃร",
    "ฃล",
    "ฃว",
}
BORROW_TONE_ONSETS = set("มนงยรลว")

VOWELISH_SIGNS = PREPOSED_VOWELS | POSTPOSED_VOWELS | {MAITAIKHU, SARA_AM, NIKHAHIT, "ั"}
_START_DIGRAPHS = ("ทร", "ศร", "สร", "จร")
_TONE_OVERRIDES: dict[str, Tone] = {
    "โดส": Tone.MID,
}

# --- Vowel pattern decoding
#
# We decode vowels based on orthographic pattern around the onset:
# preposed (เ/แ/โ/ใ/ไ), postposed marks (ะ/า/ิ/ี/ึ/ื/ุ/ู), and special combinations.
#
# Output is canonical nucleus symbols in model (IPA-like):
# a, i, ɯ, u, e, ə, ɔ, o, æ/ɛ, ia, ɯa, ua, ai, au, oi, ui, am
#
# Notes:
# - Thai has short/long contrast often marked by ะ / ็ (short) vs no ะ (long).
# - Some vowels are inherently long in orthography (e.g. ไ ใ often treated long).
#


@dataclass(frozen=True)
class VowelSpec:
    nucleus: str
    length: VowelLength
    offglide: Optional[str] = None

    # If set, forces coda (used for sara am: ◌ำ)
    coda_override: Optional[str] = None  # phoneme: "m" etc.

    # If True, reader must NOT treat final ย/ว as a coda consonant (used for -ัย and ใ/ไ etc.)
    suppress_coda_j: bool = False
    suppress_coda_w: bool = False


def _is_consonant(ch: str) -> bool:
    return ch in THAI_CONSONANTS


def _consonant_class(ch: str) -> str:
    if ch in MID_CLASS:
        return "M"
    if ch in HIGH_CLASS:
        return "H"
    if ch in LOW_CLASS:
        return "L"
    return "L"


def _tone_mark(word: str) -> Optional[str]:
    for ch in word:
        if ch in THAI_TONE_MARKS:
            return ch
    return None


def _has_maitaikhu(word: str) -> bool:
    return MAITAIKHU in word


def _is_silent_consonant(word: str, idx: int) -> bool:
    """
    consonant followed by ์ is silent: e.g. ศัพท์ -> พ์ is silent part.
    """
    if idx < 0 or idx >= len(word):
        return False
    if word[idx] not in THAI_CONSONANTS:
        return False
    return idx + 1 < len(word) and word[idx + 1] == THANTHAKHAT


def _collect_visible_consonants_base(text: str) -> list[tuple[int, str]]:
    """Return (index, consonant) excluding those silenced by ์."""
    out: list[tuple[int, str]] = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch in THAI_CONSONANTS:
            if _is_silent_consonant(text, i):
                i += 2
                continue
            out.append((i, ch))
        i += 1
    return out


def _drop_ro_han(cons: list[tuple[int, str]]) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    i = 0
    while i < len(cons):
        idx, ch = cons[i]
        if (
            ch == "ร"
            and i + 1 < len(cons)
            and cons[i + 1][1] == "ร"
            and cons[i + 1][0] == idx + 1
        ):
            i += 2
            continue
        out.append((idx, ch))
        i += 1
    return out


def _collect_visible_consonants_for_split(word: str) -> list[tuple[int, str]]:
    return _drop_ro_han(_collect_visible_consonants_base(word))


def _collect_visible_consonants_syllable(syl: str) -> list[tuple[int, str]]:
    cons = _collect_visible_consonants_base(syl)
    if not cons:
        return cons

    # Treat initial "ออ" as vowel spelling: drop the 2nd อ from consonant inventory
    if (
        syl.startswith("ออ")
        and len(cons) >= 2
        and cons[0] == (0, "อ")
        and cons[1] == (1, "อ")
    ):
        cons = [cons[0]] + cons[2:]

    # remove silent ร in start digraphs ONLY when it's really the digraph,
    # NOT when it's actually ro-han 'รร' (e.g. 'ทรรศน์')
    if (
        syl.startswith(_START_DIGRAPHS)
        and len(syl) > 2
        and len(cons) >= 2
        and cons[1][1] == "ร"
        and not (len(syl) > 2 and syl[2] == "ร")
    ):
        cons = [cons[0]] + cons[2:]

    return _drop_ro_han(cons)


def _is_bare_cc_boundary(word: str, idx1: int, idx2: int) -> bool:
    between = word[idx1 + 1 : idx2]
    if "รร" in between:
        return False
    if any(ch in VOWELISH_SIGNS for ch in between):
        return False
    if idx1 - 1 >= 0 and word[idx1 - 1] in PREPOSED_VOWELS:
        return False
    return True


def _postprocess_coda(coda: Coda, v: VowelSpec) -> Coda:
    # 1) forced coda
    if v.coda_override is not None:
        ph = v.coda_override
        if ph in ("m", "n", "ŋ", "j", "w"):
            coda = Coda(phoneme=ph, final_type=FinalType.SONORANT)
        elif ph in ("p", "t", "k"):
            coda = Coda(phoneme=ph, final_type=FinalType.STOP)
        elif ph == "ʔ":
            coda = Coda(phoneme="ʔ", final_type=FinalType.GLOTTAL)
        else:
            coda = Coda(phoneme=None, final_type=FinalType.NONE)

    # 2) suppress by vowel spelling
    if v.suppress_coda_j and coda.phoneme == "j":
        coda = Coda(phoneme=None, final_type=FinalType.NONE)
    if v.suppress_coda_w and coda.phoneme == "w":
        coda = Coda(phoneme=None, final_type=FinalType.NONE)

    # 3) offglide means not coda
    if v.offglide == "w" and coda.phoneme == "w":
        coda = Coda(phoneme=None, final_type=FinalType.NONE)
    if v.offglide == "j" and coda.phoneme == "j":
        coda = Coda(phoneme=None, final_type=FinalType.NONE)

    # 4) pseudo-open short vowel => glottal closure
    if coda.phoneme is None and v.length == VowelLength.SHORT:
        coda = Coda(phoneme="ʔ", final_type=FinalType.GLOTTAL)

    return coda


def _first_visible_consonant_letter(syl: str) -> Optional[str]:
    cons = _collect_visible_consonants_syllable(syl)
    return cons[0][1] if cons else None


def _cc_split_boundaries(word: str) -> set[int]:
    cons = _collect_visible_consonants_for_split(word)
    if len(cons) < 3:
        return set()

    boundaries: set[int] = set()

    for i in range(len(cons) - 2):
        idx1, c1 = cons[i]
        idx2, c2 = cons[i + 1]
        # Don't split C1|C2 if C2 can be coda and next syllable is marked by preposed vowel
        if c2 in {"ม", "น", "ณ", "ง", "ญ", "ร", "ล", "ฬ", "ย", "ว"} and (
            idx2 + 1 < len(word) and word[idx2 + 1] in PREPOSED_VOWELS
        ):
            continue
        # Don't split C1|C2 when C2 is a plausible coda AND the next consonant (C3)
        # clearly starts a new syllable via an explicit postposed vowel sign (e.g. ฮู-).
        # Example: นกฮูก must be นก-ฮูก (not น-ก-ฮูก).
        if i + 2 < len(cons):
            idx3, _c3 = cons[i + 2]
            if (
                c2
                in {
                    "ก",
                    "ข",
                    "ฃ",
                    "ค",
                    "ฅ",
                    "ฆ",
                    "ด",
                    "ต",
                    "ถ",
                    "ท",
                    "ธ",
                    "ฎ",
                    "ฏ",
                    "ฐ",
                    "ฑ",
                    "ฒ",
                    "บ",
                    "ป",
                    "พ",
                    "ฟ",
                    "ภ",
                    "จ",
                    "ฉ",
                    "ช",
                    "ซ",
                    "ฌ",
                    "ม",
                    "น",
                    "ณ",
                    "ง",
                    "ญ",
                    "ร",
                    "ล",
                    "ฬ",
                    "ย",
                    "ว",
                }
                and idx3 == idx2 + 1
            ):
                # check if C3 has an explicit vowel sign after it
                if (
                    idx3 + 1 < len(word)
                    and word[idx3 + 1] in (POSTPOSED_VOWELS | {"ั", "ำ", "็", "ๅ"})
                ) or (
                    idx3 + 2 < len(word)
                    and word[idx3 + 1] in ABOVE_BELOW_SIGNS
                    and word[idx3 + 2] in (POSTPOSED_VOWELS | {"ั", "ำ", "็", "ๅ"})
                ):
                    continue
        # Don't split BEFORE ho-nam sequence: ... C | ห + sonorant
        # e.g. กาวหนา must be กาว-หนา, not กาว-ห-นา
        if (
            c2 == "ห"
            and i + 2 < len(cons)
            and cons[i + 2][1] in LEADING_H_SONORANTS
            and cons[i + 2][0] == idx2 + 1
        ):
            continue

        if not _is_bare_cc_boundary(word, idx1, idx2):
            continue

        # --- don't split vowel spelling "ออ"
        if c1 == "อ" and c2 == "อ" and idx2 == idx1 + 1:
            continue

        # --- don't split after the 2nd "อ" in "ออX"
        if c1 == "อ" and idx1 > 0 and word[idx1 - 1] == "อ":
            continue

        # Don't split ho-nam (ห นำ) anywhere, not only at word start:
        # e.g. กาวหนา must be กาว-หนา, not กาว-ห-นา
        if c1 == "ห" and c2 in LEADING_H_SONORANTS and idx2 == idx1 + 1:
            continue
        if idx1 == 0 and word.startswith("อย") and c1 == "อ" and c2 == "ย":
            continue
        if (
            idx1 == 0
            and len(word) > 2
            and word.startswith(_START_DIGRAPHS)
            and c2 == "ร"
        ):
            continue
        if (c1 + c2) in TRUE_CLUSTERS:
            continue

        boundaries.add(idx2)

    return boundaries


def _split_syllables_naive(word: str) -> list[str]:
    """
    Practical syllable splitter.

    Key constraints (from tests / loanword behavior):
    - Do NOT split normal closed syllables like วัต (วั + ต is coda, not a new onset).
    - Do NOT split จุล into จุ-ล (ล is coda).
    - DO split นิยม into นิ-ยม (ย is onset, ม is coda) and thus วัตถุนิยม -> วัต-ถุ-นิ-ยม.
    """
    word = word.strip()
    if not word:
        return []

    cons = _collect_visible_consonants_for_split(word)
    if not cons:
        return [word]

    boundaries = {0}
    boundaries |= _cc_split_boundaries(word)

    # For quick membership checks
    _SONORANT_CODAS = {"ม", "น", "ง", "ย", "ว"}
    _INHERENT_ONSET_CANDIDATES = {"ย", "ร", "ล", "ว"}  # "ym/rom/lom/wom" style in loans

    for idx, _c in cons[1:]:
        # ------------------------------------------------------------
        # 1) Preposed vowel starts a new syllable (เแโใไ)
        # ------------------------------------------------------------
        if idx - 1 >= 0 and word[idx - 1] in PREPOSED_VOWELS:
            boundaries.add(idx - 1)
        elif (
            idx - 2 >= 0
            and word[idx - 2] in PREPOSED_VOWELS
            and word[idx - 1] in ABOVE_BELOW_SIGNS
        ):
            boundaries.add(idx - 2)

        # ------------------------------------------------------------
        # 2) If consonant is preceded by a postposed vowel sign,
        #    it MAY be a new syllable onset.
        #
        #    But we avoid splitting ordinary C+V+C cases (codas),
        #    and we ONLY split the narrow loanword-ish pattern:
        #       ... (previous syllable has explicit vowel mark)
        #       + (current consonant is y/r/l/w)
        #       + (next consonant is a SONORANT coda: m/n/ng/y/w)
        #    Example: นิยม => นิ-ยม
        # ------------------------------------------------------------
        if idx - 1 >= 0 and word[idx - 1] in (POSTPOSED_VOWELS | {"ั", "ำ", "็"}):
            # does THIS consonant have its OWN explicit vowel mark?
            has_own_vowel = False
            if idx + 1 < len(word) and word[idx + 1] in (
                POSTPOSED_VOWELS | {"ั", "ำ", "็"}
            ):
                has_own_vowel = True
            elif (
                idx + 2 < len(word)
                and word[idx + 1] in ABOVE_BELOW_SIGNS
                and word[idx + 2] in (POSTPOSED_VOWELS | {"ั", "ำ", "็"})
            ):
                has_own_vowel = True

            if has_own_vowel:
                boundaries.add(idx)
            else:
                # Narrow inherent-vowel-onset pattern for loans: นิยม -> นิ-ยม
                if (
                    idx < len(word)
                    and word[idx] in _INHERENT_ONSET_CANDIDATES
                    and idx + 1 < len(word)
                    and word[idx + 1] in _SONORANT_CODAS
                ):
                    boundaries.add(idx)
        # 2.2) After explicit short -ะ, if next onset begins with a true cluster (กล, กร, ขล ...),
        #      treat it as a new syllable onset.
        # Example: พระกลด => พระ-กลด (not พฺระก-...)
        if idx - 1 >= 0 and word[idx - 1] == "ะ":
            if idx + 1 < len(word):
                c1 = word[idx]
                c2 = word[idx + 1]
                if (
                    c1 in THAI_CONSONANTS
                    and c2 in THAI_CONSONANTS
                    and (c1 + c2) in TRUE_CLUSTERS
                ):
                    boundaries.add(idx)
        # ------------------------------------------------------------
        # 2.5) Force syllable boundary BEFORE ho-nam "ห + sonorant"
        # Example: ก้าวหนา => ก้าว-หนา (not ก้าวหนา, and not ก้าว-ห-นา)
        # ------------------------------------------------------------
        if (
            idx < len(word)
            and word[idx] == "ห"
            and idx + 1 < len(word)
            and word[idx + 1] in LEADING_H_SONORANTS
            and idx != 0
        ):
            boundaries.add(idx)
        # ------------------------------------------------------------
        # 3) Loanword-ish: split on pattern C C + vowel-sign
        #    (boundary goes before the SECOND consonant),
        #    with strong guards.
        # ------------------------------------------------------------
        if idx + 2 < len(word):
            c1 = word[idx]
            c2 = word[idx + 1]
            after = word[idx + 2]

            if (
                c1 in THAI_CONSONANTS
                and c2 in THAI_CONSONANTS
                and after in (POSTPOSED_VOWELS | {"ั", "ำ", "็"})
            ):
                # guard 1: don't split inside "ออX" vowel spelling
                if c1 == "อ" and idx - 1 >= 0 and word[idx - 1] == "อ":
                    pass
                # guard 2: don't split around ro-han "รร"
                elif c1 == "ร" and c2 == "ร":
                    pass
                # guard 3: NEVER split ho-nam inside a syllable: ห + sonorant
                elif (
                    c1 == "ห"
                    and c2 in LEADING_H_SONORANTS
                    and (idx + 1) == (idx + 0) + 1
                ):
                    pass
                else:
                    boundaries.add(idx + 1)

    starts = sorted(boundaries)
    syllables: list[str] = []
    for i, st in enumerate(starts):
        en = starts[i + 1] if i + 1 < len(starts) else len(word)
        syllables.append(word[st:en])
    return syllables


def _decode_vowel(syl: str, onset_index: int) -> VowelSpec:
    """
    Determine vowel nucleus/length/offglide from a syllable string.

    IMPORTANT: onset_index here is the "vowel attachment index":
      - for true clusters, this is the SECOND consonant index
      - otherwise it's the main onset consonant index
    """
    pre = syl[:onset_index]
    post = syl[onset_index + 1 :]

    # ------------------------------------------------------------------
    # Special vowel behaviors / orthographic quirks
    # ------------------------------------------------------------------

    # --- ฤ / ฦ vowel behavior (learner-oriented)
    # ฤ = rɯ (short), ฤๅ = rɯː (long)
    # ฦ = lɯ (short), ฦๅ = lɯː (long)
    if syl.startswith("ฤ") or syl.startswith("ฦ"):
        if "ๅ" in syl:
            return VowelSpec(nucleus="ɯ", length=VowelLength.LONG)
        return VowelSpec(nucleus="ɯ", length=VowelLength.SHORT)

    # --- ro han (รร)
    if "รร" in syl:
        consonants = _collect_visible_consonants_syllable(syl)
        finals = [ch for idx, ch in consonants if idx > onset_index]
        if not finals:
            return VowelSpec(nucleus="a", length=VowelLength.SHORT, coda_override="n")
        return VowelSpec(nucleus="a", length=VowelLength.SHORT)

    # --- sara am: ำ
    if SARA_AM in syl:
        return VowelSpec(nucleus="a", length=VowelLength.SHORT, coda_override="m")

    # --- -ัม (short am)
    if "ัม" in post:
        return VowelSpec(nucleus="a", length=VowelLength.SHORT)

    # --- -ัย (short/special ai)
    if "ัย" in post:
        return VowelSpec(nucleus="ai", length=VowelLength.SHORT, suppress_coda_j=True)

    # --- ใ / ไ (ai) — treated as long
    if any(v in pre for v in ("ใ", "ไ")):
        return VowelSpec(nucleus="ai", length=VowelLength.LONG, suppress_coda_j=True)

    # ------------------------------------------------------------------
    # Preposed vowels: โ แ เ
    # ------------------------------------------------------------------

    if "โ" in pre:
        if "ะ" in post or _has_maitaikhu(syl):
            return VowelSpec(nucleus="ɔ", length=VowelLength.SHORT)
        return VowelSpec(nucleus="ɔ", length=VowelLength.LONG)

    if "แ" in pre:
        if "ะ" in post or _has_maitaikhu(syl):
            return VowelSpec(nucleus="ɛ", length=VowelLength.SHORT)
        return VowelSpec(nucleus="ɛ", length=VowelLength.LONG)

    if "เ" in pre:
        if "ีย" in post or ("ี" in post and "ย" in post):
            if "ะ" in post or _has_maitaikhu(syl):
                return VowelSpec(nucleus="ia", length=VowelLength.SHORT)
            return VowelSpec(nucleus="ia", length=VowelLength.LONG)

        if "ือ" in post or ("ื" in post and "อ" in post):
            if "ะ" in post or _has_maitaikhu(syl):
                return VowelSpec(nucleus="ɯa", length=VowelLength.SHORT)
            return VowelSpec(nucleus="ɯa", length=VowelLength.LONG)

        if "า" in post and "ว" in post:
            return VowelSpec(
                nucleus="au", length=VowelLength.LONG, suppress_coda_w=True
            )

        # เ◌า (sara ao) => au (long)
        # Examples: เต่า, เฒ่า, เภา
        if "า" in post and "ว" not in post:
            return VowelSpec(
                nucleus="au", length=VowelLength.LONG, suppress_coda_w=True
            )

        # เ◌าว => au (long)
        if "า" in post and "ว" in post:
            return VowelSpec(
                nucleus="au", length=VowelLength.LONG, suppress_coda_w=True
            )
        # เ◌อ (sara oe) => ə
        if post == "อ":
            if "ะ" in post or _has_maitaikhu(syl):
                return VowelSpec(nucleus="ə", length=VowelLength.SHORT)
            return VowelSpec(nucleus="ə", length=VowelLength.LONG)

        if "ะ" in post or _has_maitaikhu(syl):
            return VowelSpec(nucleus="e", length=VowelLength.SHORT)
        return VowelSpec(nucleus="e", length=VowelLength.LONG)

    # ------------------------------------------------------------------
    # No preposed vowel: postposed patterns
    # ------------------------------------------------------------------

    # --- ◌อ as vowel letter: C + อ  => long 'o' (e.g., มอ, หมอ)
    # Must be checked BEFORE inherent vowel logic, otherwise 'อ' looks like a "final consonant".
    if (
        post == "อ"
        and not any(ch in syl for ch in PREPOSED_VOWELS)  # no preposed vowel
        and not any(
            ch in syl for ch in POSTPOSED_VOWELS
        )  # no explicit postposed vowel marks
        and "ั" not in syl
        and SARA_AM not in syl
    ):
        return VowelSpec(nucleus="o", length=VowelLength.LONG)

    # -าว => /aːw/
    if "า" in post and "ว" in post:
        return VowelSpec(
            nucleus="a",
            length=VowelLength.LONG,
            offglide="w",
            suppress_coda_w=True,
        )

    # Cluster attach-to-ว case (ขวด etc.)
    if (
        onset_index < len(syl)
        and syl[onset_index] == "ว"
        and not any(ch in post for ch in POSTPOSED_VOWELS)
        and "ั" not in post
        and SARA_AM not in syl
        and any(ch in post for ch in THAI_CONSONANTS)
    ):
        return VowelSpec(nucleus="ua", length=VowelLength.LONG, suppress_coda_w=True)

    # C + ว + final (no explicit vowel marks) => ua long
    if (
        "ว" in post
        and not any(ch in post for ch in POSTPOSED_VOWELS)
        and "ั" not in post
        and SARA_AM not in syl
    ):
        return VowelSpec(nucleus="ua", length=VowelLength.LONG, suppress_coda_w=True)

    # ัว / ัวะ
    if "ัว" in post or ("ั" in post and "ว" in post):
        if "ะ" in post or _has_maitaikhu(syl):
            return VowelSpec(
                nucleus="ua", length=VowelLength.SHORT, suppress_coda_w=True
            )
        return VowelSpec(nucleus="ua", length=VowelLength.LONG, suppress_coda_w=True)

    # ◌ั
    if "ั" in post:
        return VowelSpec(nucleus="a", length=VowelLength.SHORT)

    # Explicit vowel marks
    if "ะ" in post:
        return VowelSpec(nucleus="a", length=VowelLength.SHORT)
    if "า" in post:
        return VowelSpec(nucleus="a", length=VowelLength.LONG)

    if "ิ" in post:
        return VowelSpec(nucleus="i", length=VowelLength.SHORT)
    if "ี" in post:
        return VowelSpec(nucleus="i", length=VowelLength.LONG)

    if "ึ" in post:
        return VowelSpec(nucleus="ɯ", length=VowelLength.SHORT)
    if "ื" in post:
        return VowelSpec(nucleus="ɯ", length=VowelLength.LONG)

    if "ุ" in post:
        return VowelSpec(nucleus="u", length=VowelLength.SHORT)
    if "ู" in post:
        return VowelSpec(nucleus="u", length=VowelLength.LONG)

    # Loanword-ish inherent vowel: if has thanthakhat and no explicit vowels, prefer 'a'
    if (
        THANTHAKHAT in syl
        and not any(ch in PREPOSED_VOWELS for ch in syl)
        and not any(ch in POSTPOSED_VOWELS for ch in syl)
        and "ั" not in syl
        and SARA_AM not in syl
    ):
        return VowelSpec(nucleus="a", length=VowelLength.SHORT)

    # --- "ออ" vowel spelling (e.g. ออก): long 'o' with a following coda
    if syl.startswith("ออ") and onset_index == 0:
        return VowelSpec(nucleus="o", length=VowelLength.LONG)

    # ------------------------------------------------------------------
    # Inherent vowels
    # ------------------------------------------------------------------
    consonants = _collect_visible_consonants_syllable(syl)
    finals = [ch for idx, ch in consonants if idx > onset_index]

    if finals:
        if finals == ["ร"]:
            return VowelSpec(nucleus="o", length=VowelLength.LONG)
        return VowelSpec(nucleus="o", length=VowelLength.SHORT)

    return VowelSpec(nucleus="a", length=VowelLength.SHORT)


def _decode_onset(syl: str) -> tuple[Onset, int, str, int]:
    """
    Returns:
      (Onset, main_onset_index, tone_class_source_consonant, vowel_attach_index)
    """
    consonants = _collect_visible_consonants_syllable(syl)
    if not consonants:
        raise OrthographyError(f"No consonant found in syllable: {syl!r}")

    i1, c1_letter = consonants[0]

    # --- special: อย- (อ นำ ย)
    if (
        c1_letter == "อ"
        and len(consonants) >= 2
        and consonants[1][1] == "ย"
        and syl.startswith("อย")
    ):
        i2, _y = consonants[1]
        onset = Onset(c1=INITIAL_PHONEME["ย"], c2=None)
        return onset, i2, "ห", i2  # tone behaves as if leading ห

    # --- Leading ห นำ
    if (
        c1_letter == "ห"
        and len(consonants) >= 2
        and consonants[1][1] in LEADING_H_SONORANTS
        and consonants[1][0] == consonants[0][0] + 1
    ):
        i2, son = consonants[1]
        onset = Onset(c1=INITIAL_PHONEME[son], c2=None)
        return onset, i2, "ห", i2

    # --- Start digraphs that represent ONE consonant (ทร/ศร/สร -> s), but NOT ทรร/ศรร/สรร
    if (
        syl.startswith(("ทร", "ศร", "สร"))
        and len(syl) > 2
        and not syl.startswith(("ทรร", "ศรร", "สรร"))
    ):
        onset = Onset(c1="s", c2=None)
        return onset, i1, c1_letter, i1

    # --- จร -> /tɕ/ (when real digraph, not just two-letter syllable)
    if syl.startswith("จร") and len(syl) > 2:
        onset = Onset(c1=INITIAL_PHONEME["จ"], c2=None)
        return onset, i1, "จ", i1

    # ------------------------------------------------------------
    # Carrier อ handling
    # ------------------------------------------------------------
    # IMPORTANT:
    # - If syllable begins with "ออ..." this is vowel spelling, not carrier+onset.
    #   So onset must be empty, vowel attaches to first อ.
    if c1_letter == "อ" and syl.startswith("ออ"):
        onset = Onset(c1="", c2=None)
        return onset, i1, "อ", i1

    # Generic mapping for c1
    c1_ph = INITIAL_PHONEME.get(c1_letter)
    if c1_ph is None:
        raise OrthographyError(f"Unknown onset consonant: {c1_letter!r} in {syl!r}")

    c2_ph: Optional[str] = None
    vowel_attach_index = i1

    # --- true clusters
    if len(consonants) >= 2:
        i2, c2_letter = consonants[1]
        if i2 == i1 + 1 and c2_letter in CLUSTER_SECONDS:
            pair = c1_letter + c2_letter
            if pair in TRUE_CLUSTERS:
                # NEW: if "ว" is vowel letter (ua) like ขวด/ฃวด: CC + final consonant, no vowel marks
                if (
                    c2_letter == "ว"
                    and not any(ch in PREPOSED_VOWELS for ch in syl)
                    and not any(ch in POSTPOSED_VOWELS for ch in syl)
                    and "ั" not in syl
                    and "็" not in syl
                    and "ำ" not in syl
                    and any(
                        (idx > i2 and ch in THAI_CONSONANTS) for idx, ch in consonants
                    )
                ):
                    # treat as plain onset (no c2)
                    c2_ph = None
                    vowel_attach_index = i1
                else:
                    has_explicit_vowel_or_mark = any(
                        (ch in PREPOSED_VOWELS)
                        or (ch in POSTPOSED_VOWELS)
                        or (ch in {"ั", "็", "ำ"})
                        for ch in syl
                    )
                    has_extra_after_cc = len(syl) > i2 + 1
                    if has_explicit_vowel_or_mark or has_extra_after_cc:
                        c2_ph = CLUSTER_SECONDS[c2_letter]
                        vowel_attach_index = i2

    # --- Carrier อ for vowel-initial syllables: อ + (real consonant)
    if c1_letter == "อ" and len(consonants) >= 2:
        i2, real = consonants[1]

        # If second consonant is also อ -> vowel spelling
        if real == "อ":
            onset = Onset(c1="", c2=None)
            return onset, i1, "อ", i1

        # NEW: only treat `real` as onset if it has an explicit vowel sign after it
        tail = syl[i2 + 1 :]
        has_explicit_vowel_for_real = any(
            (ch in PREPOSED_VOWELS)
            or (ch in POSTPOSED_VOWELS)
            or (ch in {"ั", "็", "ำ", "ๅ"})
            for ch in tail
        )

        if not has_explicit_vowel_for_real:
            # vowel is carried by อ itself; syllable is vowel-initial
            onset = Onset(c1="", c2=None)
            return onset, i1, "อ", i1

        real_ph = INITIAL_PHONEME.get(real)
        if real_ph is None:
            raise OrthographyError(f"Unknown onset consonant: {real!r} in {syl!r}")
        onset = Onset(c1=real_ph, c2=None)
        return onset, i2, real, i2

    onset = Onset(c1=c1_ph, c2=c2_ph)
    return onset, i1, c1_letter, vowel_attach_index


def _decode_coda(syl: str, onset_index: int, onset: Onset, v: VowelSpec) -> Coda:
    """
    Decode Thai coda using a learner-oriented rule:

    - Multiple final consonant letters may occur, but typically only ONE is pronounced:
      the FIRST pronounceable final consonant after the onset.
    - The second consonant of a true cluster is part of the onset ONLY if onset.c2 is not None.
    - If vowel spelling uses ย/ว as part of the vowel (ai/ua/au etc.), skip them when selecting coda.
    """
    consonants = _collect_visible_consonants_syllable(syl)
    if not consonants:
        return Coda(phoneme=None, final_type=FinalType.NONE)

    # Track ONSET by POSITIONS, not letters (important for นน, มม, etc.)
    onset_indices: set[int] = set()

    # First consonant always belongs to onset machinery
    onset_indices.add(consonants[0][0])

    # Include the consonant at onset_index (main onset letter position)
    onset_indices.add(onset_index)

    # Include true cluster second consonant ONLY if cluster is actually used
    if onset.c2 is not None and len(consonants) >= 2:
        if consonants[1][0] == consonants[0][0] + 1:
            onset_indices.add(consonants[1][0])

    # Leading ห (ho-nam) affects tone but is not pronounced
    # (we still treat it as onset-side so it never becomes coda)
    if consonants[0][1] == "ห" and onset_index != consonants[0][0]:
        onset_indices.add(consonants[0][0])

    def _skip_as_vowel_letter(letter: str) -> bool:
        # If ย/ว belongs to vowel spelling, it must not be treated as coda.
        if letter == "ว":
            return v.suppress_coda_w or (v.offglide == "w")
        if letter == "ย":
            return v.suppress_coda_j or (v.offglide == "j")
        return False

    # Pick the FIRST consonant after onset_index that is not part of the onset positions
    # and is not a vowel-spelling consonant (ย/ว).
    coda_letter: Optional[str] = None
    for idx, ch in consonants:
        if idx <= onset_index:
            continue
        if idx in onset_indices:
            continue
        if _skip_as_vowel_letter(ch):
            continue
        coda_letter = ch
        break

    if coda_letter is None:
        return Coda(phoneme=None, final_type=FinalType.NONE)

    ph_final = FINAL_PHONEME.get(coda_letter)
    if ph_final is None:
        return Coda(phoneme=None, final_type=FinalType.NONE)

    phoneme, ftype = ph_final
    return Coda(phoneme=phoneme, final_type=ftype)


def _is_dead_syllable(v: VowelSpec, coda: Coda) -> bool:
    """
    Dead syllable rules:
    - stop coda (p/t/k) => dead
    - glottal/pseudo-open (ʔ) => dead
    - open syllable with short vowel => dead (often realized with glottal closure)
    """
    if coda.final_type in (FinalType.STOP, FinalType.GLOTTAL):
        return True
    if coda.phoneme is None and v.length == VowelLength.SHORT:
        return True
    return False


def _tone_from_rules(
    class_source_consonant: str,
    tone_mark: Optional[str],
    dead: bool,
    vowel_length: VowelLength,
) -> Tone:
    """
    Standard Thai tone rules with RTL-relevant distinction for LC dead:
    LC + dead:
      - long vowel => Falling
      - short vowel => High
    """
    cls = _consonant_class(class_source_consonant)

    if tone_mark is None:
        if cls == "M":
            return Tone.MID if not dead else Tone.LOW
        if cls == "H":
            return Tone.RISING if not dead else Tone.LOW
        # cls == "L"
        if not dead:
            return Tone.MID
        # dead low-class needs vowel length distinction
        return Tone.FALLING if vowel_length == VowelLength.LONG else Tone.HIGH

    # With tone marks
    if tone_mark == "่":  # mai ek
        if cls in ("M", "H"):
            return Tone.LOW
        return Tone.FALLING  # low class
    if tone_mark == "้":  # mai tho
        if cls in ("M", "H"):
            return Tone.FALLING
        return Tone.HIGH
    if tone_mark == "๊":  # mai tri (normally mid-class only)
        return Tone.HIGH
    if tone_mark == "๋":  # mai chattawa (normally mid-class only)
        return Tone.RISING

    return Tone.MID


def _read_syllable(
    syl: str, *, tone_class_source_override: Optional[str] = None
) -> Syllable:
    onset, onset_idx, tone_class_source, vowel_attach_idx = _decode_onset(syl)
    v = _decode_vowel(syl, vowel_attach_idx)
    coda = _decode_coda(syl, onset_idx, onset, v)
    coda = _postprocess_coda(coda, v)

    dead = _is_dead_syllable(v, coda)
    tm = _tone_mark(syl)
    tone_source = tone_class_source_override or tone_class_source
    tone = _tone_from_rules(tone_source, tm, dead, v.length)

    return Syllable(
        onset=onset,
        vowel=Vowel(nucleus=v.nucleus, length=v.length, offglide=v.offglide),
        coda=coda,
        tone=tone,
        raw=syl,
    )


def _last_visible_consonant_letter(chunk: str) -> Optional[str]:
    cons = _collect_visible_consonants_base(chunk)
    return cons[-1][1] if cons else None


def _inject_linking_a_for_loanwords(thai: str, syllables: list[str]) -> list[str]:
    """
    Conservative Pali/Sanskrit linking-a heuristics.

    Insert Xะ between syllables for loanword double-reading when:
    - last consonant has different initial vs final realization, OR
    - last consonant is a sonorant linker (ม/น/ง)

    Keeps guards to avoid breaking native Thai and clusters.
    """
    if len(syllables) < 2:
        return syllables

    # Compute start indices of each syllable substring in the original token
    starts: list[int] = []
    pos = 0
    for s in syllables:
        st = thai.find(s, pos)
        starts.append(st)
        pos = st + len(s)

    def _is_bare_consonant_syllable(s: str) -> bool:
        if any(ch in VOWELISH_SIGNS for ch in s):
            return False
        cons = _collect_visible_consonants_base(s)
        return len(cons) == 1 and len(s) == 1 and cons[0][1] == s

    NEVER_AFTER = {"ว", "ย"}  # don't link after these (often vowel-ish)
    SONORANT_LINK = {"ม", "น", "ง"}

    out: list[str] = []
    for i in range(len(syllables) - 1):
        a = syllables[i]
        b = syllables[i + 1]

        end_a = starts[i] + len(a)
        start_b = starts[i + 1]

        out.append(a)

        # only if adjacent in original
        if end_a != start_b:
            continue

        last_c = _last_visible_consonant_letter(a)
        first_c = _first_visible_consonant_letter(b)
        if not last_c or not first_c:
            continue

        # don't invent if boundary touches vowelish signs
        if end_a - 1 >= 0 and thai[end_a - 1] in VOWELISH_SIGNS:
            continue
        if start_b < len(thai) and thai[start_b] in VOWELISH_SIGNS:
            continue

        # Special-case: โทร + ระ...
        if a == "โทร" and last_c == "ร":
            out[-1] = "โท"
            out.append("ระ")
            continue

        if last_c in NEVER_AFTER:
            continue

        # Guard: prevent nonsense like ธรร + ระ
        if last_c == "ร" and "รร" in a:
            continue

        # Protect native CC split at word start (ตลก/ขนม/ถนน)
        if i == 0 and _is_bare_consonant_syllable(a):
            continue

        # Guard: don't link if the end of 'a' is a true onset cluster (e.g. ...ดร)
        a_cons = _collect_visible_consonants_base(a)
        if len(a_cons) >= 2:
            (i_prev, c_prev), (i_last, c_last) = a_cons[-2], a_cons[-1]
            if i_last == i_prev + 1 and (c_prev + c_last) in TRUE_CLUSTERS:
                continue

        # letters that have a different initial vs final pronunciation
        LINKING_A_CANDIDATES = {
            c
            for c in (INITIAL_PHONEME.keys() & FINAL_PHONEME.keys())
            if INITIAL_PHONEME[c] != FINAL_PHONEME[c][0]
        }
        # hard exception: ปุจฉา must be ปุจ-ฉา (not ปุจ-จะ-ฉา)
        LINKING_A_CANDIDATES.discard("จ")

        # Case A: double reading when initial != final
        if (
            last_c in LINKING_A_CANDIDATES
            and last_c in INITIAL_PHONEME
            and last_c in FINAL_PHONEME
        ):
            final_ph, _ft = FINAL_PHONEME[last_c]
            init_ph = INITIAL_PHONEME[last_c]
            if init_ph != final_ph:
                if last_c == "ร" and a.endswith("ร"):
                    out[-1] = a[:-1]
                out.append(last_c + "ะ")
                continue

        # Case B: sonorant linker in loans (ธรรม + มะ + ...)
        if last_c in SONORANT_LINK:
            out.append(last_c + "ะ")
            continue

    out.append(syllables[-1])
    return out


class ThaiOrthographyReader:
    """
    Thai orthography (writing system) -> PhonologicalWord.

    This is a rule-based reader aimed at learner-oriented Thai:
    - syllable segmentation (heuristic)
    - vowel length, coda type
    - tone computation via consonant class + tone mark + live/dead
    - supports leading ห (ห นำ) affecting tone class
    """

    def read_word(self, thai: str) -> PhonologicalWord:
        def _is_bare_consonant_syllable(s: str) -> bool:
            if any(ch in VOWELISH_SIGNS for ch in s):
                return False
            cons = _collect_visible_consonants_base(s)
            return len(cons) == 1 and len(s) == 1 and cons[0][1] == s

        thai = thai.strip()
        if not thai:
            return PhonologicalWord(syllables=())

        # If spaces are present, this is not a single word token.
        if re.search(r"\s", thai):
            raise OrthographyError(
                "read_word() expects a single token without whitespace. Use a text-level tokenizer."
            )

        syllables_str = _split_syllables_naive(thai)
        syllables_str = _inject_linking_a_for_loanwords(thai, syllables_str)

        # Build borrow map: if a boundary came from CC-split, and next onset is in BORROW_TONE_ONSETS,
        # then next syllable borrows the class source of previous syllable.
        borrow_map: dict[int, str] = {}

        cc_boundaries = _cc_split_boundaries(thai)
        if cc_boundaries and len(syllables_str) > 1:
            # Compute start indices of each syllable substring in the original token.
            # (Good enough for our current use cases; avoids rewriting the splitter.)
            starts: list[int] = []
            pos = 0
            for s in syllables_str:
                st = thai.find(s, pos)
                starts.append(st)
                pos = st + len(s)

            for i in range(len(syllables_str) - 1):
                next_start = starts[i + 1]
                if next_start in cc_boundaries and _is_bare_consonant_syllable(
                    syllables_str[i]
                ):
                    next_first = _first_visible_consonant_letter(syllables_str[i + 1])
                    if next_first in BORROW_TONE_ONSETS:
                        _onset, _idx, tone_src, _attach = _decode_onset(
                            syllables_str[i]
                        )
                        borrow_map[i + 1] = tone_src

        syllables = tuple(
            _read_syllable(s, tone_class_source_override=borrow_map.get(i))
            for i, s in enumerate(syllables_str)
            if s
        )

        # apply overrides
        if thai in _TONE_OVERRIDES and len(syllables) == 1:
            s = syllables[0]
            syllables = (
                Syllable(
                    onset=s.onset,
                    vowel=s.vowel,
                    coda=s.coda,
                    tone=_TONE_OVERRIDES[thai],
                    raw=s.raw,
                ),
            )
        return PhonologicalWord(syllables=syllables)

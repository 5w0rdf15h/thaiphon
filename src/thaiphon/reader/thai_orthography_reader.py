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
POSTPOSED_VOWELS = {"ะ", "า", "ิ", "ี", "ึ", "ื", "ุ", "ู"}  # appear after onset
# Add sara a-close (ั) to "marks above/below" so syllable splitting can treat it like other marks
ABOVE_BELOW_SIGNS = {"็", "่", "้", "๊", "๋", "์", "ํ", "ั", "ิ", "ี", "ึ", "ื", "ุ", "ู"}
# Thai consonants (basic)
THAI_CONSONANTS = set("กขฃคฅฆงจฉชซฌญฎฏฐฑฒณดตถทธนบปผฝพฟภมยรลวศษสหฬอฮ")

# Sonorants used with leading ห (ห นำ)
LEADING_H_SONORANTS = set("งญนมยรลว")

# --- Consonant class (for tone rules)
MID_CLASS = set("กจฎฏดตบปอ")
HIGH_CLASS = set("ขฃฉฐถผฝศษสห")
LOW_CLASS = set("คฅฆชซฌญฑฒณทธนพฟภมยรลวฬฮง")

# --- Phoneme mapping (canonical symbols used in your model)
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
    # treat ฃ like ข for cluster purposes (needed for ฃวด)
    "ฃร",
    "ฃล",
    "ฃว",
}
BORROW_TONE_ONSETS = set("มนงยรลว")

VOWELISH_SIGNS = PREPOSED_VOWELS | POSTPOSED_VOWELS | {MAITAIKHU, SARA_AM, NIKHAHIT, "ั"}
_START_DIGRAPHS = ("ทร", "ศร", "สร", "จร")

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

    # remove silent ร in start digraphs (only when syllable starts with them and len>2)
    if (
        syl.startswith(_START_DIGRAPHS)
        and len(syl) > 2
        and len(cons) >= 2
        and cons[1][1] == "ร"
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
    """
    CC sequences that are read as two syllables: C1 = short 'a' (open),
    rest begins at C2.

    Exclusions:
    - ห + sonorant (ห นำ) must not split.
    - อย- special อนำ must not split.
    - true clusters must not split.
    - start digraphs (ทร/ศร/สร/จร) must not split at the silent ร.
    """
    cons = _collect_visible_consonants_for_split(word)
    if len(cons) < 3:
        return set()

    boundaries: set[int] = set()

    for i in range(len(cons) - 2):
        idx1, c1 = cons[i]
        idx2, c2 = cons[i + 1]

        # Must be a "bare" CC boundary (no vowel-ish material between C1 and C2, etc.)
        if not _is_bare_cc_boundary(word, idx1, idx2):
            continue

        # DON'T split ห นำ
        if idx1 == 0 and c1 == "ห" and c2 in LEADING_H_SONORANTS:
            continue

        # DON'T split อย...
        if idx1 == 0 and word.startswith("อย") and c1 == "อ" and c2 == "ย":
            continue

        # Don't split special digraphs at syllable start (silent ร)
        if (
            idx1 == 0
            and len(word) > 2
            and word.startswith(_START_DIGRAPHS)
            and c2 == "ร"
        ):
            continue

        # Don't split true clusters
        if (c1 + c2) in TRUE_CLUSTERS:
            continue

        boundaries.add(idx2)

    return boundaries


def _split_syllables_naive(word: str) -> list[str]:
    """
    Heuristic syllable segmentation. Thai syllable parsing is complex; this is a practical
    learner-oriented splitter that works well for many native Thai words and most textbook material.

    Strategy:
    - find consonant nuclei positions (excluding silenced by ์)
    - start a new syllable at:
        * a consonant that is preceded by a preposed vowel (เแโใไ), OR
        * a consonant that is preceded by a boundary we already chose.
    - otherwise, keep consuming into current syllable until we reach a consonant that
      looks like the onset of a next syllable (often preceded by preposed vowel).
    """
    word = word.strip()
    if not word:
        return []

    cons = _collect_visible_consonants_for_split(word)
    if not cons:
        return [word]

    boundaries = {0}
    # Morev CC split boundaries
    boundaries |= _cc_split_boundaries(word)
    for idx, _c in cons[1:]:
        # if there is a preposed vowel right before this consonant, it's likely a new syllable
        if idx - 1 >= 0 and word[idx - 1] in PREPOSED_VOWELS:
            boundaries.add(idx - 1)  # syllable may start at the vowel sign
        # if there is a preposed vowel 2 chars back (tone marks / mai taikhu in between)
        elif (
            idx - 2 >= 0
            and word[idx - 2] in PREPOSED_VOWELS
            and word[idx - 1] in ABOVE_BELOW_SIGNS
        ):
            boundaries.add(idx - 2)

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
            return VowelSpec(nucleus="o", length=VowelLength.SHORT)
        return VowelSpec(nucleus="o", length=VowelLength.LONG)

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
            return VowelSpec(nucleus="au", length=VowelLength.LONG)

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

    Rules implemented:
    - Leading ห นำ (ho nam): tone class source becomes HIGH (ห), leading ห is not pronounced.
    - special อย-: pronounce ย, but tone behaves as HIGH (like ห-leading).
    - Digraphs for one consonant at syllable start:
        ทร / ศร / สร -> /s/
        จร -> /tɕ/
      'ร' in these digraphs is silent and excluded from consonant processing.
    - True clusters are limited to specific list. Vowel marks "attach" to the second consonant.
      BUT: if the syllable is just two bare consonants (e.g., กร, พร, จร in the "two-letter syllable"
      sense), we do NOT treat it as a cluster; the second consonant is a final.
    """
    consonants = _collect_visible_consonants_syllable(syl)
    if not consonants:
        raise OrthographyError(f"No consonant found in syllable: {syl!r}")

    i1, c1_letter = consonants[0]

    # --- special: อย- (อ นำ ย)
    if c1_letter == "อ" and len(consonants) >= 2 and consonants[1][1] == "ย":
        if syl.startswith("อย"):
            i2, _y = consonants[1]
            onset = Onset(c1=INITIAL_PHONEME["ย"], c2=None)
            # Force HIGH class for tone computation (use "ห" as proxy source)
            return onset, i2, "ห", i2

    # --- Leading ห นำ
    if c1_letter == "ห":
        if len(consonants) >= 2 and consonants[1][1] in LEADING_H_SONORANTS:
            i2, son = consonants[1]
            onset = Onset(c1=INITIAL_PHONEME[son], c2=None)
            return onset, i2, "ห", i2

    # --- Start digraphs that represent ONE consonant (Morev / common Thai reading)
    # Note: the helper already removed the 'ร' from consonant list, but we still need to map c1.
    if syl.startswith(("ทร", "ศร", "สร")) and len(syl) > 2:
        onset = Onset(c1="s", c2=None)
        return onset, i1, c1_letter, i1

    if syl.startswith("จร") and len(syl) > 2:
        onset = Onset(c1=INITIAL_PHONEME["จ"], c2=None)  # tɕ
        return onset, i1, "จ", i1

    c1_ph = INITIAL_PHONEME.get(c1_letter)
    if c1_ph is None:
        raise OrthographyError(f"Unknown onset consonant: {c1_letter!r} in {syl!r}")

    c2_ph: Optional[str] = None
    vowel_attach_index = i1

    # --- true clusters + "no cluster for bare CC"
    if len(consonants) >= 2:
        i2, c2_letter = consonants[1]
        if i2 == i1 + 1 and c2_letter in CLUSTER_SECONDS:
            pair = c1_letter + c2_letter
            if pair in TRUE_CLUSTERS:
                # Enable cluster only when there is explicit vowel/mark OR extra material after CC.
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

    # --- Carrier อ (generic vowel-initial syllables using อ as carrier)
    if c1_letter == "อ" and len(consonants) >= 2:
        i2, real = consonants[1]
        real_ph = INITIAL_PHONEME.get(real, "")
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

    We do two things:
    1) Insert Xะ after certain boundary consonants when they are re-read as onset with 'a'
       in loanwords (classic case: รัฐ + ฐะ + ...).
    2) Allow insertion after sonorant finals ม/น/ง in loanword clusters like ธรรม + มะ + นูญ.

    Hard exclusions to prevent nonsense like ธรร + ระ:
      - never insert after ร/ล/ว/ย (these often have special final behavior and shouldn't trigger)
      - never insert when boundary touches vowelish signs
      - do not insert for the very first CC-split bare syllable (protect ตลก/ขนม/ถนน patterns)
    """
    if len(syllables) < 2:
        return syllables

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

    NEVER_AFTER = {"ร", "ล", "ว", "ย"}
    SONORANT_LINK = {"ม", "น", "ง"}  # allow ธรรม + มะ + นูญ style

    out: list[str] = []
    for i in range(len(syllables) - 1):
        a = syllables[i]
        b = syllables[i + 1]

        end_a = starts[i] + len(a)
        start_b = starts[i + 1]

        # Only operate when adjacent in original string
        adjacent = end_a == start_b

        # Default: keep 'a' as-is
        out.append(a)

        if not adjacent:
            continue

        last_c = _last_visible_consonant_letter(a)
        first_c = _first_visible_consonant_letter(b)
        if not last_c or not first_c:
            continue

        # Don't invent if boundary touches any vowelish sign
        if end_a - 1 >= 0 and thai[end_a - 1] in VOWELISH_SIGNS:
            continue
        if start_b < len(thai) and thai[start_b] in VOWELISH_SIGNS:
            continue

        # Hard exclusion: prevents ธรร + ระ
        if last_c in NEVER_AFTER:
            continue

        # Protect native CC-split at word start (ตลก/ขนม/ถนน)
        if i == 0 and _is_bare_consonant_syllable(a):
            continue

        # Case A: classic “double reading” when initial != final (e.g. ฐ: tʰ vs t)
        if last_c in INITIAL_PHONEME and last_c in FINAL_PHONEME:
            final_ph, _ft = FINAL_PHONEME[last_c]
            init_ph = INITIAL_PHONEME[last_c]
            if init_ph != final_ph:
                out.append(last_c + "ะ")
                continue

        # Case B: sonorant linker in loans (e.g. ธรรม + มะ + นูญ)
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
                if next_start in cc_boundaries:
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
        return PhonologicalWord(syllables=syllables)

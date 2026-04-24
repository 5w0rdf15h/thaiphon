"""RTL (Rak Thai Language School) scheme mapping + factory registration.

Implements the romanization used in the Rak Thai Language School's
reading, writing, and speaking course materials. The system is a broad
phonological transcription with IPA-style vowel letters, digraph
aspirates, and tone marks carried as combining diacritics on the first
vowel letter of the syllable's nucleus.

Surface conventions:

- Consonants: aspirated stops are digraphs ``ph th ch kh``; unaspirated
  voiceless stops are ``p t c k`` (note ``c``, not ``j``, for /tɕ/).
  Voiced stops are ``b d``. Sonorants and spirants use their IPA letters
  (``m n ŋ w l r y f s h``). Vowel-initial syllables receive ``ʼ``
  (U+02BC MODIFIER LETTER APOSTROPHE) as an explicit glottal-stop
  onset — the school writes this on every vowel-initial syllable
  (อะไร → ``ʼarāy``, เอา → ``ʼaw``). There is no symbol for the
  automatic syllable-final glottal stop of short-vowel pseudo-open
  syllables.
- Vowels: IPA-style letters ``a i u e ɛ o ɔ ʉ ə`` for monophthongs, and
  ``ia ʉa ua`` for the three centring diphthongs. Long vowels are
  written as doubled letters (``aa ii uu ee ɛɛ oo ɔɔ ʉʉ əə``); the
  centring diphthongs are written the same way regardless of length
  (length is a phonological distinction not reflected in the spelling).
  The close back unrounded vowel is written ``ʉ`` (U+0289), matching the
  school's printed chart — internally the engine uses IPA ``ɯ``.
  Similarly the mid-central unrounded vowel is written ``ə``, internal
  IPA ``ɤ``.
- Tone: combining diacritic placed on the first vowel letter of the
  nucleus — macron for mid, grave for low, circumflex for falling,
  acute for high, háček for rising. After NFC normalisation the plain
  Latin vowels collapse into precomposed forms (``ā á à â ǎ``); the IPA
  letters ``ʉ ɛ ɔ ə`` have no precomposed forms and keep the diacritic
  as a separate combining codepoint, which is the expected typesetting.
- Codas: native codas map directly — ``m n ŋ w y p t k``. The three
  foreign-only coda IPAs collapse to their native realisations by
  default (``f`` → ``p``, ``s`` → ``t``, ``l`` → ``n``) to match the
  school's treatment of loanwords. For lexicon-listed modern loans
  that carry a preservation annotation for the active reading profile,
  the default coda is swapped back to the foreign surface form
  (e.g. ``ลิฟต์`` as ``líf`` rather than ``líp``). Preservation never
  fires under the ``etalon_compat`` profile.
- Cluster onsets: both elements emit separately with no joiner, yielding
  ``khr khl khw kr kl kw phr phl pr pl tr``.
- Syllable separator: single space.
- Vowel context: long /iː/ before a /w/ coda spells the nucleus as
  ``ia`` (so เขียว → ``khǐaw``), mirroring the pedagogical analysis of
  เ-ียว as the diphthong ``ia`` plus a ``w`` glide.
"""

from __future__ import annotations

import unicodedata

from thaiphon.model.enums import Tone, VowelLength
from thaiphon.model.syllable import Syllable
from thaiphon.registry import RENDERERS
from thaiphon.renderers._loan_coda import make_lexicon_coda_override
from thaiphon.renderers.mapping import MappingRenderer, SchemeMapping

# Combining tone diacritics (placed on the first vowel letter).
_TONE_COMBINING: dict[Tone, str] = {
    Tone.MID: "̄",       # COMBINING MACRON
    Tone.LOW: "̀",       # COMBINING GRAVE ACCENT
    Tone.FALLING: "̂",   # COMBINING CIRCUMFLEX ACCENT
    Tone.HIGH: "́",      # COMBINING ACUTE ACCENT
    Tone.RISING: "̌",    # COMBINING CARON
}

# Vowel-letter character class: every character the nucleus can start
# with, across both monophthongs and the centring diphthongs. Used by
# the tone formatter to locate the first vowel letter in the assembled
# syllable so the combining tone mark can be inserted right after it.
_VOWEL_LETTERS: frozenset[str] = frozenset("aiueɛoɔʉə")


# IPA → RTL onset. The phonological model represents vowel-initial
# syllables with ``onset=None`` (not ``Phoneme('ʔ')``), so the ``ʼ``
# onset symbol is emitted via ``empty_onset`` on the scheme mapping
# below rather than via this table. The ``ʔ`` entry here is kept as a
# safety net for models that might emit it explicitly.
_ONSET_MAP: dict[str, str] = {
    "k": "k",
    "kʰ": "kh",
    "tɕ": "c",
    "tɕʰ": "ch",
    "d": "d",
    "t": "t",
    "tʰ": "th",
    "b": "b",
    "p": "p",
    "pʰ": "ph",
    "f": "f",
    "s": "s",
    "h": "h",
    "ʔ": "ʼ",  # ʼ MODIFIER LETTER APOSTROPHE
    "m": "m",
    "n": "n",
    "ŋ": "ŋ",
    "j": "y",
    "r": "r",
    "l": "l",
    "w": "w",
}


# (IPA quality, length) → RTL vowel spelling. Long vowels are doubled;
# the combining tone mark is inserted after the first vowel letter by
# the tone formatter, yielding e.g. ``āa`` for long /aː/ mid tone.
_VOWEL_MAP: dict[tuple[str, VowelLength], str] = {
    ("a", VowelLength.SHORT): "a",
    ("a", VowelLength.LONG): "aa",
    ("i", VowelLength.SHORT): "i",
    ("i", VowelLength.LONG): "ii",
    ("u", VowelLength.SHORT): "u",
    ("u", VowelLength.LONG): "uu",
    ("e", VowelLength.SHORT): "e",
    ("e", VowelLength.LONG): "ee",
    ("ɛ", VowelLength.SHORT): "ɛ",
    ("ɛ", VowelLength.LONG): "ɛɛ",
    ("o", VowelLength.SHORT): "o",
    ("o", VowelLength.LONG): "oo",
    ("ɔ", VowelLength.SHORT): "ɔ",
    ("ɔ", VowelLength.LONG): "ɔɔ",
    # Close back unrounded: printed as ``ʉ`` (U+0289) in the RTL chart.
    ("ɯ", VowelLength.SHORT): "ʉ",
    ("ɯ", VowelLength.LONG): "ʉʉ",
    # Mid-central unrounded: printed as ``ə`` (U+0259).
    ("ɤ", VowelLength.SHORT): "ə",
    ("ɤ", VowelLength.LONG): "əə",
    # Centring diphthongs share the same spelling across lengths; the
    # short/long distinction is phonological, not orthographic, in this
    # romanization.
    ("iə", VowelLength.SHORT): "ia",
    ("iə", VowelLength.LONG): "ia",
    ("ɯə", VowelLength.SHORT): "ʉa",
    ("ɯə", VowelLength.LONG): "ʉa",
    ("uə", VowelLength.SHORT): "ua",
    ("uə", VowelLength.LONG): "ua",
}


# Vowel spelling override keyed on (vowel, length, coda). Long /iː/
# before a /w/ coda spells the nucleus as the diphthong ``ia`` — so
# เขียว surfaces as ``khǐaw`` rather than ``khǐiw``. This matches the
# school's pedagogical analysis of เ-ียว.
_VOWEL_CONTEXT: dict[tuple[str, VowelLength, str], str] = {
    ("i", VowelLength.LONG, "w"): "ia",
}


# Coda IPA → RTL letter. Native codas map directly; the three
# foreign-only coda IPAs collapse to the nearest native segment by
# default, matching the school's loanword treatment. Lexicon-listed
# modern loans may override the default back to the foreign surface
# form via ``_PRESERVATION_CONFIG`` / ``_lexicon_coda_override`` below.
_CODA_MAP: dict[str, str] = {
    "m": "m",
    "n": "n",
    "ŋ": "ŋ",
    "p̚": "p",  # p̚ — unreleased stop
    "t̚": "t",
    "k̚": "k",
    "f": "p",
    "s": "t",
    "l": "n",
    "w": "w",
    "j": "y",
}


# Per-preservation-tag configuration. Shape mirrors the TLC and Paiboon
# tables; the RTL surface letters for the preserved forms happen to be
# the same single characters ``f`` / ``s`` / ``l``. The orthographic
# source-letter sets match exactly — native letters collapsing to the
# same default coda are deliberately absent so the override never
# misfires on them.
_PRESERVATION_CONFIG: dict[str, tuple[str, frozenset[str], str]] = {
    # ฟ → /p̚/ natively → RTL ``p``; preserve as ``f``.
    "f": ("p", frozenset({"ฟ"}), "f"),
    # ส / ศ / ษ → /t̚/ natively → RTL ``t``; preserve as ``s``.
    "s": (
        "t",
        frozenset({"ส", "ศ", "ษ"}),
        "s",
    ),
    # ล → /n/ natively → RTL ``n``; preserve as ``l``.
    "l": ("n", frozenset({"ล"}), "l"),
}


_lexicon_coda_override = make_lexicon_coda_override(_PRESERVATION_CONFIG)


def _tone_format(base: str, syl: Syllable) -> str:
    """Insert the tone-mark combining diacritic after the first vowel
    letter of the assembled syllable, then NFC-normalise.

    The tone is part of the nucleus in this scheme (not a separate
    spacing symbol), so it has to land inside the vowel cluster. We
    walk the assembled string from the start, past the onset, and drop
    the combining mark in immediately after the first character that
    belongs to the vowel-letter set. On a well-formed syllable there
    will always be at least one such character.
    """
    diacritic = _TONE_COMBINING[syl.tone]
    for i, ch in enumerate(base):
        if ch in _VOWEL_LETTERS:
            out = base[: i + 1] + diacritic + base[i + 1 :]
            return unicodedata.normalize("NFC", out)
    # Degenerate fallback — no vowel letter found. Append the diacritic
    # at the end rather than silently swallowing the tone.
    return unicodedata.normalize("NFC", base + diacritic)


RTL_MAPPING: SchemeMapping = SchemeMapping(
    scheme_id="rtl",
    onset_map=_ONSET_MAP,
    vowel_map=_VOWEL_MAP,
    vowel_context_map=_VOWEL_CONTEXT,
    coda_map=_CODA_MAP,
    word_coda_override=_lexicon_coda_override,
    tone_format=_tone_format,
    cluster_joiner="",
    syllable_separator=" ",
    empty_onset="ʼ",
    unknown_fallback="?",
)


def _factory() -> MappingRenderer:
    return MappingRenderer(RTL_MAPPING)


if "rtl" not in RENDERERS:
    RENDERERS.register("rtl", _factory)

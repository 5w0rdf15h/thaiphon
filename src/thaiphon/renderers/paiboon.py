"""Paiboon and Paiboon+ scheme mappings + factory registrations.

Implements the romanization popularised by Paiboon Publishing's learner
materials. Two scheme ids are registered here: ``paiboon`` for the
original system used in the first-edition Thai-for-Beginners series,
and ``paiboon_plus`` for the revised system adopted in the 2009
Three-Way dictionary and later titles. The two schemes share every
onset, coda, and monophthong; they diverge only in how the centring
diphthongs ``/iə/ /ɯə/ /uə/`` spell out their length contrast and in
how ``/iː/+w`` and ``/uə/+j`` spell the full triphthong.

Surface conventions (both schemes unless noted):

- Consonant onsets are written with an English-reader convention:
  aspirated stops take the bare letter (/pʰ/ → ``p``, /tʰ/ → ``t``,
  /kʰ/ → ``k``), while unaspirated voiceless stops take a digraph
  mimicking English post-/s/ clusters (/p/ → ``bp``, /t/ → ``dt``,
  /k/ → ``g``). /tɕ/ is ``j``, /tɕʰ/ is ``ch``. /ŋ/ is ``ng`` in both
  onset and coda. The glottal stop has no symbol (vowel-initial
  syllables start straight into the vowel).
- Monophthongs use IPA-style letters ``ɛ``, ``ɔ``, ``ʉ``, ``ə`` along
  with the plain Latin vowels. Long is doubled: ``aa ii uu ee ɛɛ oo
  ɔɔ ʉʉ əə``. The close-back-unrounded /ɯ/ is spelled ``ʉ`` (U+0289),
  matching Paiboon's typography.
- Coda ``/w/`` defaults to ``o`` (so ``aao`` / ``eeo`` / ``ɛɛo``), and
  ``/j/`` defaults to ``i`` (so ``aai`` / ``ɔɔi`` / ``əəi``). The one
  exception is short ``/i/+w`` which spells as ``iu``.
- Centring diphthongs:

  * Paiboon+: long/short are distinguished in spelling —
    long ``iia ʉʉa uua``, short ``ia ʉa ua``.
  * Paiboon: no spelling distinction — both lengths spell as
    ``ia ʉa ua``.

- Triphthong-like combinations:

  * ``/iː/+w`` → Paiboon+ ``iiao``, Paiboon ``iao``.
  * ``/uə/+j`` (model-level) → Paiboon+ ``uuai``, Paiboon ``uai``.
  * ``/ɯə/+j`` → Paiboon+ ``ʉʉai``, Paiboon ``ʉai``.

- Final stops ``/p̚ t̚ k̚/`` → ``p t k``. Foreign-only coda IPAs collapse
  to the nearest native realisation (``/f/`` → ``p``, ``/s/`` → ``t``,
  ``/l/`` → ``n``).
- Tone is a combining diacritic on the first vowel letter: mid is
  unmarked; low → grave; falling → circumflex; high → acute; rising →
  háček. After NFC the plain Latin vowels precompose with the mark;
  the IPA-letter vowels keep the diacritic as a separate combining
  codepoint (no precomposed forms exist).
- Syllable separator is ``-`` (e.g. ``kun-gèp-sʉ̂ʉa-wái-nǎi``).
"""

from __future__ import annotations

import unicodedata

from thaiphon.model.enums import Tone, VowelLength
from thaiphon.model.syllable import Syllable
from thaiphon.registry import RENDERERS
from thaiphon.renderers.mapping import MappingRenderer, SchemeMapping


# Combining tone diacritics. Mid is unmarked — the empty string makes
# the insertion in ``_tone_format`` a no-op.
_TONE_COMBINING: dict[Tone, str] = {
    Tone.MID: "",
    Tone.LOW: "̀",       # COMBINING GRAVE ACCENT
    Tone.FALLING: "̂",   # COMBINING CIRCUMFLEX ACCENT
    Tone.HIGH: "́",      # COMBINING ACUTE ACCENT
    Tone.RISING: "̌",    # COMBINING CARON
}


# Vowel-letter character class used to locate the nucleus in the
# assembled syllable. Matches every letter a nucleus can start with.
_VOWEL_LETTERS: frozenset[str] = frozenset("aiueɛoɔʉə")


# IPA onset → Paiboon letter. The glottal stop has no symbol (the
# pipeline emits ``onset=None`` for vowel-initial syllables, so the
# entry here is only a safety net).
_ONSET_MAP: dict[str, str] = {
    "k": "g",
    "kʰ": "k",
    "tɕ": "j",
    "tɕʰ": "ch",
    "d": "d",
    "t": "dt",
    "tʰ": "t",
    "b": "b",
    "p": "bp",
    "pʰ": "p",
    "f": "f",
    "s": "s",
    "h": "h",
    "ʔ": "",
    "m": "m",
    "n": "n",
    "ŋ": "ng",
    "j": "y",
    "r": "r",
    "l": "l",
    "w": "w",
}


# Monophthong map shared by both schemes.
_MONOPHTHONGS: dict[tuple[str, VowelLength], str] = {
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
    ("ɯ", VowelLength.SHORT): "ʉ",
    ("ɯ", VowelLength.LONG): "ʉʉ",
    ("ɤ", VowelLength.SHORT): "ə",
    ("ɤ", VowelLength.LONG): "əə",
}


def _build_vowel_map(long_diphthong_is_doubled: bool) -> dict[tuple[str, VowelLength], str]:
    """Return a full vowel map, varying only in how centring diphthongs
    express length.

    - Paiboon+ (doubled): long ``iia ʉʉa uua``, short ``ia ʉa ua``.
    - Paiboon (collapsed): both lengths spell as ``ia ʉa ua``.
    """
    diphthongs: dict[tuple[str, VowelLength], str]
    if long_diphthong_is_doubled:
        diphthongs = {
            ("iə", VowelLength.SHORT): "ia",
            ("iə", VowelLength.LONG): "iia",
            ("ɯə", VowelLength.SHORT): "ʉa",
            ("ɯə", VowelLength.LONG): "ʉʉa",
            ("uə", VowelLength.SHORT): "ua",
            ("uə", VowelLength.LONG): "uua",
        }
    else:
        diphthongs = {
            ("iə", VowelLength.SHORT): "ia",
            ("iə", VowelLength.LONG): "ia",
            ("ɯə", VowelLength.SHORT): "ʉa",
            ("ɯə", VowelLength.LONG): "ʉa",
            ("uə", VowelLength.SHORT): "ua",
            ("uə", VowelLength.LONG): "ua",
        }
    return {**_MONOPHTHONGS, **diphthongs}


def _build_vowel_context(
    long_diphthong_is_doubled: bool,
) -> dict[tuple[str, VowelLength, str], str]:
    """(vowel, length, coda) → vowel-spelling override.

    The pipeline treats เ-ียว as ``/iː/+w`` (not ``/iə/+w``), so the
    Paiboon-style ``ia``/``iia`` nucleus has to be re-introduced here.
    """
    if long_diphthong_is_doubled:
        return {("i", VowelLength.LONG, "w"): "iia"}
    return {("i", VowelLength.LONG, "w"): "ia"}


# Default coda map. /w/ → o, /j/ → i. The (/i/ SHORT) + /w/ case gets
# an explicit override in ``_CODA_CONTEXT`` below.
_CODA_MAP: dict[str, str] = {
    "m": "m",
    "n": "n",
    "ŋ": "ng",
    "p̚": "p",
    "t̚": "t",
    "k̚": "k",
    "f": "p",
    "s": "t",
    "l": "n",
    "w": "o",
    "j": "i",
}


# Short /i/ + /w/ is ``iu`` ("Matthew"), not the default ``io``.
_CODA_CONTEXT: dict[tuple[str, VowelLength, str], str] = {
    ("i", VowelLength.SHORT, "w"): "u",
}


def _tone_format(base: str, syl: Syllable) -> str:
    """Insert the tone-mark combining diacritic after the first vowel
    letter of the assembled syllable, then NFC-normalise. Mid tone
    uses the empty string so the insertion is a no-op.
    """
    diacritic = _TONE_COMBINING[syl.tone]
    if not diacritic:
        return unicodedata.normalize("NFC", base)
    for i, ch in enumerate(base):
        if ch in _VOWEL_LETTERS:
            out = base[: i + 1] + diacritic + base[i + 1 :]
            return unicodedata.normalize("NFC", out)
    return unicodedata.normalize("NFC", base + diacritic)


PAIBOON_MAPPING: SchemeMapping = SchemeMapping(
    scheme_id="paiboon",
    onset_map=_ONSET_MAP,
    vowel_map=_build_vowel_map(long_diphthong_is_doubled=False),
    vowel_context_map=_build_vowel_context(long_diphthong_is_doubled=False),
    coda_map=_CODA_MAP,
    coda_context_map=_CODA_CONTEXT,
    tone_format=_tone_format,
    cluster_joiner="",
    syllable_separator="-",
    empty_onset="",
    unknown_fallback="?",
)


PAIBOON_PLUS_MAPPING: SchemeMapping = SchemeMapping(
    scheme_id="paiboon_plus",
    onset_map=_ONSET_MAP,
    vowel_map=_build_vowel_map(long_diphthong_is_doubled=True),
    vowel_context_map=_build_vowel_context(long_diphthong_is_doubled=True),
    coda_map=_CODA_MAP,
    coda_context_map=_CODA_CONTEXT,
    tone_format=_tone_format,
    cluster_joiner="",
    syllable_separator="-",
    empty_onset="",
    unknown_fallback="?",
)


def _paiboon_factory() -> MappingRenderer:
    return MappingRenderer(PAIBOON_MAPPING)


def _paiboon_plus_factory() -> MappingRenderer:
    return MappingRenderer(PAIBOON_PLUS_MAPPING)


if "paiboon" not in RENDERERS:
    RENDERERS.register("paiboon", _paiboon_factory)
if "paiboon_plus" not in RENDERERS:
    RENDERERS.register("paiboon_plus", _paiboon_plus_factory)

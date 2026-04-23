"""Morev (Cyrillic) scheme mapping + factory registration.

Implements the Cyrillic transcription of Thai used by L. N. Morev and
N. F. Plam in the 1969 Thai-Russian dictionary and adopted in
Russian-language Thai-teaching materials. Surface conventions follow
the alphabet table at the head of that dictionary; the same conventions
appear in subsequent Morev-tradition reference works.

Surface conventions:

- Aspirated stops are spelled as a digraph: /kʰ/ → ``кх``, /tʰ/ → ``тх``,
  /pʰ/ → ``пх``. The HTML overlay raises the second element so the
  digraph reads as plain consonant + superscript х (``к<sup>х</sup>``,
  ``т<sup>х</sup>``, ``п<sup>х</sup>``). The aspirated palatal /tɕʰ/ is
  written as a bare ``ч`` with no aspiration mark in either format —
  this matches the Morev alphabet table, which lists ฉ / ช / ฌ as ``ч``.
- Unaspirated palatal /tɕ/ → ``ть`` (digraph; the alphabet table lists
  จ as тьо̄).
- /h/ → ``х``; /ŋ/ → ``нг``; /ʔ/ has no surface symbol.
- Long vowels carry a combining macron (U+0304) on the first vocalic
  element. Centring diphthongs spell the off-glide as bare ``а`` after
  the macron-bearing nucleus (``ӣа``, ``ы̄а``, ``ӯа``).
- The source dictionary uses Cyrillic ``о̄``/``о`` as the default
  rendering for both modern Thai /oː/ and /ɔː/ in long open syllables.
  The Latin ``ɔ̄``/``ɔ`` glyphs from the introductory transcription key
  appear only sporadically in the dictionary body, without a derivable
  phonological pattern; the renderer therefore emits Cyrillic
  ``о̄``/``о`` for both vowels and treats the Latin glyphs as out of
  scope. Mid-central /ɤ/ uses the schwa ``ə`` (U+0259), which is
  intentionally non-Cyrillic and reproduces the dictionary's
  typesetting.
- ``ว`` in the second slot of a true CC onset cluster (e.g. /kw/, /kʰw/)
  surfaces as the back vowel ``у``: ``กวาง`` → ``куа̄нг``. As a bare
  initial ``ว`` is ``в``; as a coda glide it is ``у``.
- Tones are spacing modifiers placed at the end of the syllable, after
  the coda: LOW ``ˆ`` (U+02C6), FALLING ````` (U+0060), HIGH
  ``ˇ`` (U+02C7), RISING ``´`` (U+00B4); MID is unmarked. The engine's
  tone names follow the modern-phonology convention (HIGH = high pitch,
  RISING = low-to-high contour); these correspond to Morev's
  contour-named "rising-falling" (tone 3) and "rising" (tone 4) marks
  respectively.
- Foreign-origin codas that no native syllable supports collapse to
  the nearest native stop or nasal: /f/ → ``п``, /s/ → ``т``, /l/ → ``н``.
  This matches the dictionary's treatment of recent loans
  (``ก๊าซ`` → ``ка̄тˇ``, ``โบนัส`` → ``бо̄-натˇ``, ``ฟุตบอล`` → ``футˆ-бо̄н``,
  ``ปรู๊ฟ`` → ``прӯпˇ``).
- Syllable separator is ``-``.
"""

from __future__ import annotations

import unicodedata

from thaiphon.model.enums import Tone, VowelLength
from thaiphon.model.syllable import Syllable
from thaiphon.registry import RENDERERS
from thaiphon.renderers.mapping import MappingRenderer, SchemeMapping

# Combining macron used to mark vowel length.
_MACRON = "̄"

# Spacing tone modifiers, applied at the end of the syllable string.
_TONE_LOW = "ˆ"      # ˆ MODIFIER LETTER CIRCUMFLEX ACCENT
_TONE_FALLING = "`"  # ` GRAVE ACCENT
_TONE_HIGH = "ˇ"     # ˇ CARON
_TONE_RISING = "´"   # ´ ACUTE ACCENT


# IPA → Morev onset (text mode). The four aspirated stops are written
# as digraphs in text and gain a superscript second element in HTML
# (see ``_ONSET_HTML_MAP`` below).
_ONSET_MAP: dict[str, str] = {
    "k": "к",
    "kʰ": "кх",
    "tɕ": "ть",
    "tɕʰ": "ч",
    "d": "д",
    "t": "т",
    "tʰ": "тх",
    "b": "б",
    "p": "п",
    "pʰ": "пх",
    "f": "ф",
    "s": "с",
    "h": "х",
    "ʔ": "",
    "m": "м",
    "n": "н",
    "ŋ": "нг",
    "j": "й",
    "r": "р",
    "l": "л",
    "w": "в",
}

# HTML overlay: only the four aspirated stops differ from text mode.
# The aspirated palatal /tɕʰ/ stays as bare ``ч`` to match the alphabet
# table, where ฉ / ช / ฌ are all listed as ``ч`` with no aspiration mark.
_ONSET_HTML_MAP: dict[str, str] = {
    "kʰ": "к<sup>х</sup>",
    "tʰ": "т<sup>х</sup>",
    "pʰ": "п<sup>х</sup>",
}

# In a true CC onset cluster (/kw/, /kʰw/, ...) ``ว`` surfaces as the
# back vowel ``у`` rather than the consonant ``в``.
_CLUSTER_SECOND_SLOT_MAP: dict[str, str] = {
    "w": "у",
}


# (IPA quality, length) → Morev vowel base. Long vowels append the
# combining macron; centring diphthongs put the macron on the first
# element only (``ӣа``, ``ы̄а``, ``ӯа``). The output is intentionally
# left in NFD so the macron sits as a separate combining codepoint —
# the Cyrillic block has no precomposed macroned forms for ``и`` / ``у``
# at the codepoints used here, and emitting precomposed ``ӣ`` / ``ӯ``
# would diverge from the dictionary's typesetting.
_VOWEL_MAP: dict[tuple[str, VowelLength], str] = {
    ("a", VowelLength.SHORT): "а",
    ("a", VowelLength.LONG): "а" + _MACRON,
    ("i", VowelLength.SHORT): "и",
    ("i", VowelLength.LONG): "и" + _MACRON,
    ("u", VowelLength.SHORT): "у",
    ("u", VowelLength.LONG): "у" + _MACRON,
    ("e", VowelLength.SHORT): "е",
    ("e", VowelLength.LONG): "е" + _MACRON,
    ("ɛ", VowelLength.SHORT): "э",
    ("ɛ", VowelLength.LONG): "э" + _MACRON,
    ("o", VowelLength.SHORT): "о",
    ("o", VowelLength.LONG): "о" + _MACRON,
    ("ɔ", VowelLength.SHORT): "о",            # Cyrillic о (collapsed from Latin ɔ)
    ("ɔ", VowelLength.LONG): "о" + _MACRON,   # Cyrillic о̄ (collapsed from Latin ɔ̄)
    ("ɯ", VowelLength.SHORT): "ы",
    ("ɯ", VowelLength.LONG): "ы" + _MACRON,
    ("ɤ", VowelLength.SHORT): "ə",            # ə
    ("ɤ", VowelLength.LONG): "ə" + _MACRON,   # ə̄
    ("iə", VowelLength.SHORT): "иа",
    ("iə", VowelLength.LONG): "и" + _MACRON + "а",
    ("ɯə", VowelLength.SHORT): "ыа",
    ("ɯə", VowelLength.LONG): "ы" + _MACRON + "а",
    ("uə", VowelLength.SHORT): "уа",
    ("uə", VowelLength.LONG): "у" + _MACRON + "а",
}


# Coda IPA → Cyrillic letter. Native codas map straight through; the
# three foreign-only coda IPAs (/f/, /s/, /l/) collapse to the nearest
# native segment per the dictionary's loanword convention. The /s/ and
# /l/ entries are kept here even when upstream syllabification already
# rewrites them, as a piece of policy documentation.
_CODA_MAP: dict[str, str] = {
    "m": "м",
    "n": "н",
    "ŋ": "нг",
    "p̚": "п",
    "t̚": "т",
    "k̚": "к",
    "f": "п",
    "s": "т",
    "l": "н",
    "w": "у",
    "j": "й",
}


_TONE_SUFFIX: dict[Tone, str] = {
    Tone.MID: "",
    Tone.LOW: _TONE_LOW,
    Tone.FALLING: _TONE_FALLING,
    Tone.HIGH: _TONE_HIGH,
    Tone.RISING: _TONE_RISING,
}


def _tone_format(base: str, syl: Syllable) -> str:
    """Append the tone modifier after the assembled syllable.

    The base string is left untouched (no diacritic is inserted into
    the vowel cluster); the tone is a spacing modifier that lives at
    the very end of the syllable, after any coda. NFC normalisation is
    applied so combining macrons fold into precomposed forms where the
    target codepoint exists.
    """
    suffix = _TONE_SUFFIX[syl.tone]
    return unicodedata.normalize("NFC", base) + suffix


MOREV_MAPPING: SchemeMapping = SchemeMapping(
    scheme_id="morev",
    onset_map=_ONSET_MAP,
    onset_html_map=_ONSET_HTML_MAP,
    cluster_second_slot_map=_CLUSTER_SECOND_SLOT_MAP,
    vowel_map=_VOWEL_MAP,
    coda_map=_CODA_MAP,
    tone_format=_tone_format,
    cluster_joiner="",
    syllable_separator="-",
    empty_onset="",
    unknown_fallback="?",
)


def _factory() -> MappingRenderer:
    return MappingRenderer(MOREV_MAPPING)


if "morev" not in RENDERERS:
    RENDERERS.register("morev", _factory)


__all__ = ["MOREV_MAPPING"]

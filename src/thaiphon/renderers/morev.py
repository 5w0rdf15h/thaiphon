"""Morev (Cyrillic) scheme mapping + factory registration.

Implements the Cyrillic transliteration tradition used by L. N. Morev and
adopted in Russian-language Thai-teaching materials.

Conventions:
- Aspirated stops are written with the IPA modifier letter small H
  (U+02B0) appended to the plain voiceless letter: /kʰ/ → кʰ, /tʰ/ → тʰ,
  /pʰ/ → пʰ, /tɕʰ/ → чʰ.
- /h/ → х; no collision with aspirated stops.
- /ŋ/ → ң (U+04A3); /tɕ/ → ч.
- Long vowels take a combining macron (U+0304).
- Tones are rendered with combining diacritics on the main vowel:
  LOW ̀ (U+0300), FALLING ̂ (U+0302), HIGH ́ (U+0301), RISING ̌ (U+030C).
  MID is unmarked.
- Output is NFC-normalized so diacritic insertion yields precomposed
  forms where possible.
"""

from __future__ import annotations

import unicodedata

from thaiphon.model.enums import Tone, VowelLength
from thaiphon.model.syllable import Syllable
from thaiphon.registry import RENDERERS
from thaiphon.renderers.mapping import MappingRenderer, SchemeMapping

# Combining diacritics.
_MACRON = "\u0304"          # ̄
_TONE_LOW = "\u0300"        # ̀
_TONE_FALLING = "\u0302"    # ̂
_TONE_HIGH = "\u0301"       # ́
_TONE_RISING = "\u030c"     # ̌

# IPA modifier letter small H — used for aspirated stops (U+02B0).
_ASP = "\u02b0"

# IPA → Morev onset.
_ONSET_MAP: dict[str, str] = {
    "k": "к",
    "kʰ": "к" + _ASP,
    "tɕ": "ч",
    "tɕʰ": "ч" + _ASP,
    "d": "д",
    "t": "т",
    "tʰ": "т" + _ASP,
    "b": "б",
    "p": "п",
    "pʰ": "п" + _ASP,
    "f": "ф",
    "s": "с",
    "h": "х",
    "ʔ": "",
    "m": "м",
    "n": "н",
    "ŋ": "ң",
    "j": "й",
    "r": "р",
    "l": "л",
    "w": "в",
}

# (IPA quality, length) → Cyrillic vowel base. Long vowels append U+0304.
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
    ("ɔ", VowelLength.SHORT): "о",
    ("ɔ", VowelLength.LONG): "о" + _MACRON,
    ("ɯ", VowelLength.SHORT): "ы",
    ("ɯ", VowelLength.LONG): "ы" + _MACRON,
    ("ɤ", VowelLength.SHORT): "ӧ",
    ("ɤ", VowelLength.LONG): "ӧ" + _MACRON,
    ("iə", VowelLength.SHORT): "иа",
    ("iə", VowelLength.LONG): "иа",
    ("ɯə", VowelLength.SHORT): "ыа",
    ("ɯə", VowelLength.LONG): "ыа",
    ("uə", VowelLength.SHORT): "уа",
    ("uə", VowelLength.LONG): "уа",
}

# Coda IPA → Cyrillic letter.
_CODA_MAP: dict[str, str] = {
    "m": "м",
    "n": "н",
    "ŋ": "ң",
    "p̚": "п",
    "t̚": "т",
    "k̚": "к",
    "f": "ф",  # modern loan /f/ preservation
    "w": "у",
    "j": "й",
}

_TONE_COMBINING: dict[Tone, str] = {
    Tone.MID: "",
    Tone.LOW: _TONE_LOW,
    Tone.FALLING: _TONE_FALLING,
    Tone.HIGH: _TONE_HIGH,
    Tone.RISING: _TONE_RISING,
}

# Cyrillic base-vowel letters we emit (before any macron).
_VOWEL_LETTERS: frozenset[str] = frozenset("аеиоуыэӧ")


def _tone_format(base: str, syl: Syllable) -> str:
    combining = _TONE_COMBINING[syl.tone]
    if not combining:
        return unicodedata.normalize("NFC", base)
    # Insert the tone mark AFTER the last vowel letter (and after its
    # macron, if present) so both diacritics sit on the same base.
    last = -1
    for i, ch in enumerate(base):
        if ch in _VOWEL_LETTERS:
            last = i
    if last < 0:
        return unicodedata.normalize("NFC", base + combining)
    insert_at = last + 1
    if insert_at < len(base) and base[insert_at] == _MACRON:
        insert_at += 1
    combined = base[:insert_at] + combining + base[insert_at:]
    return unicodedata.normalize("NFC", combined)


MOREV_MAPPING: SchemeMapping = SchemeMapping(
    scheme_id="morev",
    onset_map=_ONSET_MAP,
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

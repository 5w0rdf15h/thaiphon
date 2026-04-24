"""LMT (Lipilina-Muzychenko-Thapanosoth) Cyrillic scheme mapping.

Implements the Cyrillic transliteration of Thai used in the MSU /
ISAA learner textbook:

    И. Н. Липилина, Ю. Ф. Музыченко, П. Тхапаносотх.
    "Учебник тайского языка: вводный курс."
    Москва: Издательский дом ВКН, 2018. ISBN 978-5-907086-16-6.

The scheme shares its onset and coda inventory with the dictionary-
citation Morev convention — both sit in the same Russian-academic
tradition of Cyrillic-based Thai transliteration. What sets LMT apart
is its learner-textbook presentation:

- Vowel length is marked with a plain ASCII colon ``:`` after the
  vowel letter (``ка:`` for /kaː/), rather than the combining macron
  Morev uses.
- Tones are written as a superscript digit at the end of the
  syllable, after the coda: ``⁰`` mid, ``¹`` low, ``²`` falling,
  ``³`` high, ``⁴`` rising. Plain-text output uses Unicode superscript
  digits (U+2070, U+00B9, U+00B2, U+00B3, U+2074) to match the book's
  typography in any font; HTML output uses ordinary digits wrapped in
  ``<sup>…</sup>`` so consumers can style the tone marker with CSS.
  Note this numbering is distinct from the 1-5 systems used by many
  Thai-English dictionaries (where 1 is mid); LMT uses 0 for mid and
  runs 1-4 for the other four tones.
- The syllable separator inside a word is a single space.
- Centring diphthongs place the length colon on the nucleus only, with
  the off-glide ``а`` unmarked: ``и:а``, ``ы:а``, ``у:а``.

Onset and coda surface conventions:

- Aspirated stops are digraphs ``кх``, ``тх``, ``пх``; the aspirated
  palatal /tɕʰ/ is a bare ``ч`` (no aspiration mark).
- Unaspirated palatal /tɕ/ is ``ть``.
- /h/ → ``х``; /ŋ/ → ``нг``; the glottal stop has no surface symbol.
- Foreign-origin codas that no native syllable supports collapse to
  the nearest native stop or nasal — /f/ → ``п``, /s/ → ``т``, /l/ →
  ``н``. This is the strict citation convention of the textbook; the
  LMT renderer does not expose the modern-loan preservation hook that
  the Latin learner schemes use. Callers that want foreign /f/
  preserved on the surface should pick ``rtl``, ``paiboon``, or
  ``paiboon_plus``.
- Glide codas: /w/ → ``у``, /j/ → ``й`` — same as Morev.
- ``ว`` in the second slot of a true CC onset cluster surfaces as the
  back vowel ``у`` (``куа:нг`` for กวาง), matching the Russian-
  academic reading.

Vowel-glyph policy for the four "mid-open" qualities:

- /e/, /eː/ → Cyrillic ``е`` / ``е:``.
- /ɛ/, /ɛː/ → Cyrillic ``э`` / ``э:``.
- /o/, /oː/ → Cyrillic ``о`` / ``о:``.
- /ɔ/, /ɔː/ → Latin small letter open o ``ɔ`` / ``ɔ:`` (U+0254),
  distinct from the Cyrillic ``о`` used for /o/.
- /ɤ/, /ɤː/ → Latin small letter schwa ``ə`` / ``ə:`` (U+0259),
  distinct from the Cyrillic ``э`` used for /ɛ/.

The three non-Cyrillic letters (``ɔ``, ``ə``, and the English ``a``
used in centring diphthongs) are intentional — they mirror the
printed book's typography, which mixes Cyrillic with Latin IPA
characters where the native Russian alphabet has no equivalent.
"""

from __future__ import annotations

from thaiphon.model.enums import Tone, VowelLength
from thaiphon.model.syllable import Syllable
from thaiphon.registry import RENDERERS
from thaiphon.renderers.mapping import MappingRenderer, SchemeMapping

# Colon appended after a vowel letter to mark length.
_LONG = ":"


# IPA → LMT onset. Identical to the Morev onset inventory.
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


# In a true CC onset cluster (/kw/, /kʰw/, ...) ``ว`` surfaces as the
# back vowel ``у`` rather than the consonant ``в``.
_CLUSTER_SECOND_SLOT_MAP: dict[str, str] = {
    "w": "у",
}


# (IPA quality, length) → LMT vowel spelling. Long vowels append the
# colon ``:`` to the nucleus. Centring diphthongs place the colon on
# the nucleus only, with the off-glide ``а`` unmarked.
_VOWEL_MAP: dict[tuple[str, VowelLength], str] = {
    ("a", VowelLength.SHORT): "а",
    ("a", VowelLength.LONG): "а" + _LONG,
    ("i", VowelLength.SHORT): "и",
    ("i", VowelLength.LONG): "и" + _LONG,
    ("u", VowelLength.SHORT): "у",
    ("u", VowelLength.LONG): "у" + _LONG,
    ("e", VowelLength.SHORT): "е",
    ("e", VowelLength.LONG): "е" + _LONG,
    ("ɛ", VowelLength.SHORT): "э",
    ("ɛ", VowelLength.LONG): "э" + _LONG,
    # /o/ uses Cyrillic ``о``; /ɔ/ uses Latin IPA ``ɔ`` (U+0254 LATIN
    # SMALL LETTER OPEN O). The two letters look similar at small
    # sizes but are phonemically distinct and typeset as distinct
    # glyphs in the source book.
    ("o", VowelLength.SHORT): "о",
    ("o", VowelLength.LONG): "о" + _LONG,
    ("ɔ", VowelLength.SHORT): "ɔ",
    ("ɔ", VowelLength.LONG): "ɔ" + _LONG,
    ("ɯ", VowelLength.SHORT): "ы",
    ("ɯ", VowelLength.LONG): "ы" + _LONG,
    # U+0259 Latin small letter schwa — unambiguous and matches the
    # typesetting tradition of the related Morev dictionary.
    ("ɤ", VowelLength.SHORT): "ə",
    ("ɤ", VowelLength.LONG): "ə" + _LONG,
    # Centring diphthongs: colon on the nucleus only; the off-glide
    # ``а`` stays bare.
    ("iə", VowelLength.SHORT): "иа",
    ("iə", VowelLength.LONG): "и" + _LONG + "а",
    ("ɯə", VowelLength.SHORT): "ыа",
    ("ɯə", VowelLength.LONG): "ы" + _LONG + "а",
    ("uə", VowelLength.SHORT): "уа",
    ("uə", VowelLength.LONG): "у" + _LONG + "а",
}


# Coda IPA → Cyrillic letter. Native codas map straight through; the
# three foreign-only coda IPAs (/f/, /s/, /l/) collapse to the nearest
# native segment per the learner-textbook convention. No profile-gated
# preservation is exposed.
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


# Tone-digit mapping. Note the 0-4 range with 0 for mid, which differs
# from the 1-5 systems common in Thai-English dictionaries. Plain-text
# output uses Unicode superscript digits to match the book's typography
# in any font; HTML output uses ordinary digits wrapped in ``<sup>``.
_TONE_DIGIT_SUPERSCRIPT: dict[Tone, str] = {
    Tone.MID: "⁰",      # ⁰ SUPERSCRIPT ZERO
    Tone.LOW: "¹",      # ¹ SUPERSCRIPT ONE
    Tone.FALLING: "²",  # ² SUPERSCRIPT TWO
    Tone.HIGH: "³",     # ³ SUPERSCRIPT THREE
    Tone.RISING: "⁴",   # ⁴ SUPERSCRIPT FOUR
}

_TONE_DIGIT_ASCII: dict[Tone, str] = {
    Tone.MID: "0",
    Tone.LOW: "1",
    Tone.FALLING: "2",
    Tone.HIGH: "3",
    Tone.RISING: "4",
}


def _tone_format(base: str, syl: Syllable) -> str:
    """Append the Unicode superscript tone digit after the syllable."""
    return base + _TONE_DIGIT_SUPERSCRIPT[syl.tone]


def _tone_format_html(base: str, syl: Syllable) -> str:
    """HTML output wraps an ordinary ASCII digit in ``<sup>…</sup>`` so
    consumers can style the tone marker with their own CSS. The digit
    inside the tag stays plain (``0`` — ``4``) to avoid the visually
    redundant "superscript-of-a-superscript" effect that using a
    Unicode superscript digit inside a ``<sup>`` tag would produce.
    """
    return base + f"<sup>{_TONE_DIGIT_ASCII[syl.tone]}</sup>"


LMT_MAPPING: SchemeMapping = SchemeMapping(
    scheme_id="lmt",
    onset_map=_ONSET_MAP,
    cluster_second_slot_map=_CLUSTER_SECOND_SLOT_MAP,
    vowel_map=_VOWEL_MAP,
    coda_map=_CODA_MAP,
    tone_format=_tone_format,
    tone_format_html=_tone_format_html,
    cluster_joiner="",
    syllable_separator=" ",
    empty_onset="",
    unknown_fallback="?",
)


def _factory() -> MappingRenderer:
    return MappingRenderer(LMT_MAPPING)


if "lmt" not in RENDERERS:
    RENDERERS.register("lmt", _factory)


__all__ = ["LMT_MAPPING"]

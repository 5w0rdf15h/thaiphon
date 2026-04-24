"""RTGS (Royal Thai General System of Transcription) scheme mapping.

Implements the 2002 revision of the Royal Institute of Thailand's
official romanization, the system used on Thai road signs, government
publications, and most geographic names in English-language contexts.

Surface conventions:

- Plain ASCII Latin output — no diacritics, no IPA-extension letters,
  no modifier apostrophes. The scheme is deliberately under-specified
  as a transcription aid for non-Thai readers rather than a reversible
  phonological notation.
- Aspirated stops are digraphs ``ph th kh ch``; unaspirated voiceless
  stops are bare letters ``p t k`` and ``ch`` (RTGS uses ``ch`` for both
  ``/tɕ/`` and ``/tɕʰ/`` — the aspiration contrast is neutralised on
  surface). Voiced stops are ``b d``. /ŋ/ is ``ng`` in both onset and
  coda.
- The glottal stop is not written. Vowel-initial syllables start
  straight into the vowel, whether the syllable is word-initial or
  medial (so ``อา`` is ``a`` and the second syllable of ไมโครซอฟต์
  carries no onset letter).
- Vowels: one Latin spelling per quality, no length distinction.
  Monophthongs ``a e i o u ae oe ue`` cover both short and long.
  Centring diphthongs: ``ia`` for /iə/, ``uea`` for /ɯə/, ``ua`` for
  /uə/.
- Glide codas: /w/ → ``o``, /j/ → ``i`` (so ไทย → ``thai``, ข้าว →
  ``khao``).
- Six-way final consonant merge: every stop collapses to ``k`` / ``t``
  / ``p`` depending on place; sonorant finals are ``m n ng``. Foreign
  coda phonemes merge into the native inventory — /f/ → ``p``, /s/ →
  ``t``, /l/ → ``n`` — with no profile-gated preservation. RTGS is the
  strict-collapse official form; callers that want modern-loan /f/
  preserved on the surface should pick ``rtl``, ``paiboon``, or
  ``paiboon_plus`` instead.
- Tone is not marked in any form. The tone formatter is the identity.
- Silent (thanthakhat-marked) letters are already dropped upstream by
  the orthography reader; the renderer sees no cancelled syllables to
  worry about.
- Syllable separator inside a word is empty — syllables run together
  (``krungthep``, ``sawatdi``). Spaces between words are supplied by
  :func:`thaiphon.api.transcribe_sentence`, so a segmented input like
  ``กรุง เทพ`` comes out as ``krung thep`` at the sentence layer while
  a single-token ``กรุงเทพ`` renders as ``krungthep``.
"""

from __future__ import annotations

from thaiphon.model.enums import VowelLength
from thaiphon.model.syllable import Syllable
from thaiphon.registry import RENDERERS
from thaiphon.renderers.mapping import MappingRenderer, SchemeMapping

# IPA onset → RTGS letter. Vowel-initial syllables reach the renderer
# with ``onset=None`` (handled via ``empty_onset``) or, for medial
# aspirate-looking อ-onsets, as ``Phoneme("ʔ")`` — both must emit the
# empty string so no glottal-stop symbol leaks into RTGS output.
_ONSET_MAP: dict[str, str] = {
    "k": "k",
    "kʰ": "kh",
    "tɕ": "ch",   # RTGS neutralises /tɕ/ and /tɕʰ/ to the same digraph.
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
    "ʔ": "",      # glottal stop onset is never written.
    "m": "m",
    "n": "n",
    "ŋ": "ng",
    "j": "y",
    "r": "r",
    "l": "l",
    "w": "w",
}


# (IPA quality, length) → RTGS vowel spelling. Length is collapsed:
# short and long map to the same letter. The centring diphthongs
# /iə uə/ are ``ia`` and ``ua``; /ɯə/ is the trigraph ``uea`` per the
# published table.
_VOWEL_MAP: dict[tuple[str, VowelLength], str] = {
    ("a", VowelLength.SHORT): "a",
    ("a", VowelLength.LONG): "a",
    ("i", VowelLength.SHORT): "i",
    ("i", VowelLength.LONG): "i",
    ("u", VowelLength.SHORT): "u",
    ("u", VowelLength.LONG): "u",
    ("e", VowelLength.SHORT): "e",
    ("e", VowelLength.LONG): "e",
    ("ɛ", VowelLength.SHORT): "ae",
    ("ɛ", VowelLength.LONG): "ae",
    ("o", VowelLength.SHORT): "o",
    ("o", VowelLength.LONG): "o",
    ("ɔ", VowelLength.SHORT): "o",
    ("ɔ", VowelLength.LONG): "o",
    # Close back unrounded — ``ue``.
    ("ɯ", VowelLength.SHORT): "ue",
    ("ɯ", VowelLength.LONG): "ue",
    # Mid-central unrounded — ``oe``.
    ("ɤ", VowelLength.SHORT): "oe",
    ("ɤ", VowelLength.LONG): "oe",
    # Centring diphthongs.
    ("iə", VowelLength.SHORT): "ia",
    ("iə", VowelLength.LONG): "ia",
    ("ɯə", VowelLength.SHORT): "uea",
    ("ɯə", VowelLength.LONG): "uea",
    ("uə", VowelLength.SHORT): "ua",
    ("uə", VowelLength.LONG): "ua",
}


# Vowel spelling overrides keyed on (vowel, length, coda). The pipeline
# models เ-ียว as ``/iː/+w`` rather than ``/iə/+w``; RTGS spells this
# frame as the centring diphthong ``ia`` + glide ``o``, so the long /iː/
# nucleus has to be re-expanded to ``ia`` before a /w/ coda. This
# matches the Wikipedia convention for words like เขียว → ``khiao``.
_VOWEL_CONTEXT: dict[tuple[str, VowelLength, str], str] = {
    ("i", VowelLength.LONG, "w"): "ia",
}


# Coda IPA → RTGS letter. Foreign-only codas collapse unconditionally
# to the native six-way inventory; the scheme does not expose the
# preservation hook that the Latin learner schemes use.
_CODA_MAP: dict[str, str] = {
    "m": "m",
    "n": "n",
    "ŋ": "ng",
    "p̚": "p",
    "t̚": "t",
    "k̚": "k",
    # Foreign codas always collapse in RTGS. ``rtl`` / ``paiboon`` /
    # ``paiboon_plus`` are available for callers that want the modern
    # loan /f/ preserved on the surface.
    "f": "p",
    "s": "t",
    "l": "n",
    # Glide codas.
    "w": "o",
    "j": "i",
}


def _tone_format(base: str, syl: Syllable) -> str:
    """Identity — RTGS marks no tone at all."""
    del syl  # unused: RTGS is toneless by specification.
    return base


RTGS_MAPPING: SchemeMapping = SchemeMapping(
    scheme_id="rtgs",
    onset_map=_ONSET_MAP,
    vowel_map=_VOWEL_MAP,
    vowel_context_map=_VOWEL_CONTEXT,
    coda_map=_CODA_MAP,
    tone_format=_tone_format,
    cluster_joiner="",
    syllable_separator="",
    empty_onset="",
    unknown_fallback="?",
)


def _factory() -> MappingRenderer:
    return MappingRenderer(RTGS_MAPPING)


if "rtgs" not in RENDERERS:
    RENDERERS.register("rtgs", _factory)


__all__ = ["RTGS_MAPPING"]

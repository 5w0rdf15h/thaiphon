"""IPA scheme mapping + factory registration.

Outputs broad phonemic IPA in the Wiktionary-compatible format:
``/syllable1.syllable2.syllable3/`` with Chao tone letters per syllable.

Conventions:
- Onsets use standard IPA phoneme symbols (``kʰ``, ``tɕ``, ``ŋ``, ...).
- Long vowels append the IPA length mark ``ː`` (U+02D0).
- Stop codas are unreleased: ``p̚``, ``t̚``, ``k̚`` (U+031A).
- Tones are written as Chao tone letters at the end of each syllable:
  MID ``˧``, LOW ``˨˩``, FALLING ``˥˩``, HIGH ``˦˥``, RISING ``˩˩˦``.
- Syllable separator is ``.``.
- The whole word is wrapped in ``/…/`` phonemic slashes.
- Centring diphthongs keep their two-part spelling: ``iə``/``ɯə``/``uə``.
"""

from __future__ import annotations

from thaiphon.lexicons.loanword import LOANWORDS, get_preserved_coda
from thaiphon.model.enums import Tone, VowelLength
from thaiphon.model.syllable import Syllable
from thaiphon.model.word import PhonologicalWord
from thaiphon.registry import RENDERERS
from thaiphon.renderers.base import RenderContext
from thaiphon.renderers.mapping import MappingRenderer, SchemeMapping

# Identity onset map — internal symbols are already IPA.
_ONSET_MAP: dict[str, str] = {
    "k": "k",
    "kʰ": "kʰ",
    "tɕ": "tɕ",
    "tɕʰ": "tɕʰ",
    "d": "d",
    "t": "t",
    "tʰ": "tʰ",
    "b": "b",
    "p": "p",
    "pʰ": "pʰ",
    "f": "f",
    "s": "s",
    "h": "h",
    "ʔ": "ʔ",
    "m": "m",
    "n": "n",
    "ŋ": "ŋ",
    "j": "j",
    "r": "r",
    "l": "l",
    "w": "w",
}

_LONG = "ː"

# (IPA quality, length) → IPA vowel string.
_VOWEL_MAP: dict[tuple[str, VowelLength], str] = {
    ("a", VowelLength.SHORT): "a",
    ("a", VowelLength.LONG): "a" + _LONG,
    ("i", VowelLength.SHORT): "i",
    ("i", VowelLength.LONG): "i" + _LONG,
    ("u", VowelLength.SHORT): "u",
    ("u", VowelLength.LONG): "u" + _LONG,
    ("e", VowelLength.SHORT): "e",
    ("e", VowelLength.LONG): "e" + _LONG,
    ("ɛ", VowelLength.SHORT): "ɛ",
    ("ɛ", VowelLength.LONG): "ɛ" + _LONG,
    ("o", VowelLength.SHORT): "o",
    ("o", VowelLength.LONG): "o" + _LONG,
    ("ɔ", VowelLength.SHORT): "ɔ",
    ("ɔ", VowelLength.LONG): "ɔ" + _LONG,
    ("ɯ", VowelLength.SHORT): "ɯ",
    ("ɯ", VowelLength.LONG): "ɯ" + _LONG,
    ("ɤ", VowelLength.SHORT): "ɤ",
    ("ɤ", VowelLength.LONG): "ɤ" + _LONG,
    # Centring diphthongs — the internal long/short distinction is not
    # realised in broad IPA, both surface as ``iə`` / ``ɯə`` / ``uə``.
    ("iə", VowelLength.SHORT): "iə",
    ("iə", VowelLength.LONG): "iə",
    ("ɯə", VowelLength.SHORT): "ɯə",
    ("ɯə", VowelLength.LONG): "ɯə",
    ("uə", VowelLength.SHORT): "uə",
    ("uə", VowelLength.LONG): "uə",
}

# Coda IPA → IPA surface. Stops are unreleased.
_CODA_MAP: dict[str, str] = {
    "m": "m",
    "n": "n",
    "ŋ": "ŋ",
    "p̚": "p̚",
    "t̚": "t̚",
    "k̚": "k̚",
    "f": "p̚",  # modern loan /f/ is pronounced as /p̚/ in citation forms
    "w": "w",
    "j": "j",
}

# Chao tone letters per citation tone.
_TONE_CHAO: dict[Tone, str] = {
    Tone.MID: "˧",
    Tone.LOW: "˨˩",
    Tone.FALLING: "˥˩",
    Tone.HIGH: "˦˥",
    Tone.RISING: "˩˩˦",
}


# Per-preservation-tag configuration for the IPA scheme. Tags and
# source-letter sets mirror the TLC scheme (see
# :mod:`thaiphon.renderers.tlc`), but the default-coda IPA string and
# the preserved surface form are IPA-specific.
_IPA_PRESERVATION_CONFIG: dict[str, tuple[str, frozenset[str], str]] = {
    # ฟ → /p̚/ natively; preserve as ``f`` (released fricative).
    "f": ("p̚", frozenset({"ฟ"}), "f"),
    # ส / ศ / ษ → /t̚/ natively; preserve as ``s``.
    "s": (
        "t̚",
        frozenset({"ส", "ศ", "ษ"}),
        "s",
    ),
    # ล → /n/ natively; preserve as ``l``.
    "l": ("n", frozenset({"ล"}), "l"),
}


def _syllable_carries_ipa(
    syl: Syllable, word_raw: str, source_chars: frozenset[str]
) -> bool:
    if syl.raw:
        return any(ch in syl.raw for ch in source_chars)
    return any(ch in word_raw for ch in source_chars)


def _ipa_lexicon_coda_override(
    word_raw: str, syl: Syllable, default: str, profile: str
) -> str | None:
    """Replace the IPA default coda with the preserved foreign surface
    form when the lexicon calls for it.

    Only lexicon-listed entries drive the IPA override — the IPA
    renderer has no out-of-lexicon heuristic fallback. Unlike the TLC
    scheme (which uses dictionary-style citation conventions that
    sometimes diverge from modern speech), the IPA target is a
    phonemic rendering of attested pronunciations, and taking the
    decision outside the lexicon would emit preservations that have
    no lexical warrant.
    """
    if profile == "etalon_compat":
        return None
    if word_raw not in LOANWORDS:
        return None
    tag = get_preserved_coda(word_raw, profile)
    if tag is None:
        return None
    cfg = _IPA_PRESERVATION_CONFIG.get(tag)
    if cfg is None:
        return None
    expected_default, source_chars, surface = cfg
    if default == expected_default and _syllable_carries_ipa(
        syl, word_raw, source_chars
    ):
        return surface
    return None


def _tone_format(base: str, syl: Syllable) -> str:
    return base + _TONE_CHAO[syl.tone]


IPA_MAPPING: SchemeMapping = SchemeMapping(
    scheme_id="ipa",
    onset_map=_ONSET_MAP,
    vowel_map=_VOWEL_MAP,
    coda_map=_CODA_MAP,
    word_coda_override=_ipa_lexicon_coda_override,
    tone_format=_tone_format,
    cluster_joiner="",
    syllable_separator=".",
    empty_onset="",
    unknown_fallback="?",
)


class _IPARenderer(MappingRenderer):
    """Mapping renderer that wraps output in ``/…/`` phonemic slashes."""

    __slots__ = ()

    def render_word(self, word: PhonologicalWord, ctx: RenderContext) -> str:
        inner = super().render_word(word, ctx)
        return f"/{inner}/"


def _factory() -> _IPARenderer:
    return _IPARenderer(IPA_MAPPING)


if "ipa" not in RENDERERS:
    RENDERERS.register("ipa", _factory)


__all__ = ["IPA_MAPPING"]

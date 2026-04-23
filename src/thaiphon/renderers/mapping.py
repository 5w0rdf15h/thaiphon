"""Universal SchemeMapping + MappingRenderer."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass

from thaiphon.model.enums import VowelLength
from thaiphon.model.phoneme import Cluster, Phoneme
from thaiphon.model.syllable import Syllable
from thaiphon.model.word import PhonologicalWord
from thaiphon.renderers.base import RenderContext


@dataclass(frozen=True, slots=True)
class SchemeMapping:
    scheme_id: str
    onset_map: Mapping[str, str]
    vowel_map: Mapping[tuple[str, VowelLength], str]
    coda_map: Mapping[str, str]
    tone_format: Callable[[str, Syllable], str]
    # Optional: override (vowel, length, coda-IPA) → coda spelling for
    # schemes where glides/stops are context-dependent.
    coda_context_map: Mapping[tuple[str, VowelLength, str], str] | None = None
    # Optional: override (vowel, length, coda-IPA) → vowel spelling for
    # schemes where the nucleus surface form shifts depending on the coda
    # (e.g. the tlc scheme renders /ɤ/ SHORT as ``eeu`` before /j/).
    vowel_context_map: Mapping[tuple[str, VowelLength, str], str] | None = None
    # Optional: word-level coda override. Called with (word_raw, syllable,
    # default_coda_str, profile) and may return a replacement string. Used
    # by schemes that render scheme-specific editorial conventions keyed
    # off the full source word and the active reading profile (e.g. a
    # scheme may preserve foreign /f/ in modern loanword codas only when
    # the caller's profile asks for preservation).
    word_coda_override: (
        Callable[[str, Syllable, str, str], str | None] | None
    ) = None
    # Optional: per-key onset overlay used only when ``ctx.format == "html"``.
    # Lookups fall back to ``onset_map`` for any IPA key not present here,
    # so schemes only declare the entries that actually differ between
    # text and HTML output (typically aspirated stops formatted with
    # superscript markup).
    onset_html_map: Mapping[str, str] | None = None
    # Optional: alternate onset map used for the second slot of a true
    # CC onset cluster. Lets schemes spell a phoneme differently when it
    # appears as the post-consonantal glide in a cluster (e.g. /w/ in
    # /kw/, /kʰw/ surfaces as the back vowel ``у`` in the Morev system).
    # Falls back to ``onset_map`` per-key when an entry is absent.
    cluster_second_slot_map: Mapping[str, str] | None = None
    cluster_joiner: str = ""
    syllable_separator: str = "-"
    empty_onset: str = ""
    inserted_vowel_marker: str = ""
    unknown_fallback: str = "?"


class MappingRenderer:
    __slots__ = ("_m", "scheme_id")

    def __init__(self, mapping: SchemeMapping) -> None:
        self._m = mapping
        self.scheme_id = mapping.scheme_id

    def render_syllable(
        self,
        syl: Syllable,
        word_raw: str = "",
        profile: str = "everyday",
        fmt: str = "text",
    ) -> str:
        m = self._m
        # Pick the active onset table. ``onset_html_map`` is consulted
        # per-key when present and the caller asked for HTML output;
        # any IPA key it does not list falls back to ``onset_map`` so
        # schemes only declare the entries that actually differ between
        # text and HTML.
        html_overlay = m.onset_html_map if fmt == "html" else None

        def _onset_lookup(symbol: str) -> str:
            if html_overlay is not None and symbol in html_overlay:
                return html_overlay[symbol]
            return m.onset_map.get(symbol, m.unknown_fallback)

        # Onset.
        onset = syl.onset
        onset_str = ""
        if onset is None:
            onset_str = m.empty_onset
        elif isinstance(onset, Cluster):
            a = _onset_lookup(onset.first.symbol)
            second_map = m.cluster_second_slot_map
            if second_map is not None and onset.second.symbol in second_map:
                b = second_map[onset.second.symbol]
            else:
                b = _onset_lookup(onset.second.symbol)
            onset_str = a + m.cluster_joiner + b
        elif isinstance(onset, Phoneme):
            onset_str = _onset_lookup(onset.symbol)

        # Vowel — check context-dependent map first when a coda is present.
        vowel_key = (syl.vowel.symbol, syl.vowel_length)
        vowel_str = m.vowel_map.get(vowel_key, m.unknown_fallback)
        if syl.coda is not None and m.vowel_context_map is not None:
            vctx_key = (syl.vowel.symbol, syl.vowel_length, syl.coda.symbol)
            override = m.vowel_context_map.get(vctx_key)
            if override is not None:
                vowel_str = override

        # Coda (with optional context-dependent joint map: vowel+length+coda key).
        coda_str = ""
        if syl.coda is not None:
            ctx = m.coda_context_map
            key = (syl.vowel.symbol, syl.vowel_length, syl.coda.symbol)
            if ctx is not None and key in ctx:
                coda_str = ctx[key]
            else:
                coda_str = m.coda_map.get(syl.coda.symbol, m.unknown_fallback)
            # Word-level coda override: lets schemes replace a default coda
            # rendering based on the source word and the caller's reading
            # profile (e.g. preserving a foreign /f/ coda for lexicon-listed
            # modern loans when the profile opts into preservation).
            if word_raw and m.word_coda_override is not None:
                replacement = m.word_coda_override(
                    word_raw, syl, coda_str, profile
                )
                if replacement is not None:
                    coda_str = replacement

        base = onset_str + vowel_str + coda_str
        return m.tone_format(base, syl)

    def render_word(self, word: PhonologicalWord, ctx: RenderContext) -> str:
        # ``profile`` threads through so scheme-specific overrides can
        # gate on register; ``ctx.format`` selects an optional onset
        # overlay for HTML output (text mode is the default and needs
        # no overlay).
        profile = ctx.profile
        fmt = ctx.format
        return self._m.syllable_separator.join(
            self.render_syllable(
                s, word_raw=word.raw, profile=profile, fmt=fmt
            )
            for s in word.syllables
        )


__all__ = ["MappingRenderer", "SchemeMapping"]

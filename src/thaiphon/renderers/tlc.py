"""TLC ('Enhanced Phonemic') scheme mapping + factory registration."""

from __future__ import annotations

from thaiphon.lexicons.loanword import LOANWORDS, get_preserved_coda
from thaiphon.lexicons.loanword_detector import score_foreignness
from thaiphon.model.enums import Tone, VowelLength
from thaiphon.model.syllable import Syllable
from thaiphon.registry import RENDERERS
from thaiphon.renderers.mapping import MappingRenderer, SchemeMapping

# IPA → TLC onset. 'Enhanced Phonemic' distinguishes aspirated/unaspirated.
_ONSET_MAP: dict[str, str] = {
    "k": "g",
    "kʰ": "kh",
    "tɕ": "j",
    "tɕʰ": "ch",
    "d": "d",
    "t": "dt",
    "tʰ": "th",
    "b": "b",
    "p": "bp",
    "pʰ": "ph",
    "f": "f",
    "s": "s",
    "h": "h",
    "ʔ": "",  # implicit glottal onset — no symbol in TLC text
    "m": "m",
    "n": "n",
    "ŋ": "ng",
    "j": "y",
    "r": "r",
    "l": "l",
    "w": "w",
}

# (IPA quality, length) → TLC base string. Conventions from the etalon
# corpus: short /u/ spells ``oo``, long ``uu``; inherent short /o/ spells
# ``oh`` (closed) and long /oː/ spells ``o:h``; /e/ long spells ``aeh`` and
# /ɛ/ long spells ``aae``. Glides w/j in coda spell ``o``/``i``.
_VOWEL_MAP: dict[tuple[str, VowelLength], str] = {
    ("a", VowelLength.SHORT): "a",
    ("a", VowelLength.LONG): "aa",
    ("i", VowelLength.SHORT): "i",
    ("i", VowelLength.LONG): "ee",
    ("e", VowelLength.SHORT): "e",
    ("e", VowelLength.LONG): "aeh",
    ("ɛ", VowelLength.SHORT): "ae",
    ("ɛ", VowelLength.LONG): "aae",
    ("u", VowelLength.SHORT): "oo",
    ("u", VowelLength.LONG): "uu",
    ("o", VowelLength.SHORT): "oh",
    ("o", VowelLength.LONG): "o:h",
    ("ɔ", VowelLength.SHORT): "aw",
    ("ɔ", VowelLength.LONG): "aaw",
    ("ɯ", VowelLength.SHORT): "eu",
    ("ɯ", VowelLength.LONG): "euu",
    ("ɤ", VowelLength.SHORT): "eer",
    ("ɤ", VowelLength.LONG): "uuhr",
    ("iə", VowelLength.SHORT): "ia",
    ("iə", VowelLength.LONG): "iia",
    ("ɯə", VowelLength.SHORT): "euua",
    ("ɯə", VowelLength.LONG): "euua",
    ("uə", VowelLength.SHORT): "uaa",
    ("uə", VowelLength.LONG): "uaa",
}

# Coda IPA → TLC letter.
_CODA_MAP: dict[str, str] = {
    "m": "m",
    "n": "n",
    "ŋ": "ng",
    "p̚": "p",
    "t̚": "t",
    "k̚": "k",
    "f": "f",  # modern loan /f/ preservation
    "w": "o",
    "j": "i",
}

# Context-dependent coda spellings: (vowel, length, coda-IPA) → letter.
# TLC convention: /j/ spells ``i`` after /aː/, ``y`` after /ɔː/ /ɤ/ /uː/
# /uə/. /w/ spells ``o`` by default.
_CODA_CONTEXT: dict[tuple[str, VowelLength, str], str] = {
    ("ɔ", VowelLength.LONG, "j"): "y",
    # เ◌ย short /ɤ/ + /j/ offglide → etalon spells the nucleus + glide as
    # ``eeuy`` (the vowel is rendered ``eeu`` before ``y``). See R-204.
    ("ɤ", VowelLength.SHORT, "j"): "y",
    ("ɤ", VowelLength.LONG, "j"): "y",
    ("u", VowelLength.SHORT, "j"): "y",
    ("uə", VowelLength.LONG, "j"): "y",
    ("e", VowelLength.LONG, "j"): "y",
    # โ◌ย: long /oː/ + /j/ spells ``ooy`` (โดย → dooy) — vowel context
    # ``oo`` plus this ``y``.
    ("o", VowelLength.LONG, "j"): "y",
    # Short /i/ + /w/ glide renders as ``iu`` (etalon convention).
    ("i", VowelLength.SHORT, "w"): "u",
    # R-CENT-001 Case B: long /iː/ + /w/ glide — phonology is /iːw/ but
    # TLC spells the cluster as ``iaao`` (pedagogical expansion mirroring
    # the orthographic เ◌ียว frame). Coda ``w`` surfaces as ``o``; see
    # the vowel context table below for the ``iaa`` nucleus override.
    ("i", VowelLength.LONG, "w"): "o",
}

_TONE_TAG: dict[Tone, str] = {
    Tone.MID: "{M}",
    Tone.LOW: "{L}",
    Tone.HIGH: "{H}",
    Tone.FALLING: "{F}",
    Tone.RISING: "{R}",
}

# HTML form of the tone marker: the same M/L/H/F/R letter wrapped in
# ``<sup>`` so it renders as a superscript next to the syllable. No CSS
# classes are emitted — consumers style the ``<sup>`` element directly
# if they want per-tone colouring.
_TONE_TAG_HTML: dict[Tone, str] = {
    Tone.MID: "<sup>M</sup>",
    Tone.LOW: "<sup>L</sup>",
    Tone.HIGH: "<sup>H</sup>",
    Tone.FALLING: "<sup>F</sup>",
    Tone.RISING: "<sup>R</sup>",
}

# Minimum foreignness score at which an out-of-lexicon ฟ-coda is
# preserved as surface /f/ rather than collapsed to native /p̚/. Only
# consulted for words without a lexicon entry; lexicon members use the
# entry's own profile policy and bypass this threshold.
_F_HEURISTIC_THRESHOLD: float = 0.6

# Per-preservation-tag configuration. Each tag records:
#
# * ``default_coda`` — the native-collapsed TLC coda string the override
#   must see before replacing anything.
# * ``source_chars`` — the orthographic source letters that signal the
#   syllable carrying the foreign coda to preserve. Native letters with
#   the same collapsed coda are deliberately absent so they never
#   trigger a swap.
# * ``surface`` — the TLC surface string to emit on preservation.
_PRESERVATION_CONFIG: dict[str, tuple[str, frozenset[str], str]] = {
    # ฟ → /p̚/ natively; preserve as ``f``.
    "f": ("p", frozenset({"ฟ"}), "f"),
    # ส / ศ / ษ → /t̚/ natively; preserve as ``s``.
    "s": (
        "t",
        frozenset({"ส", "ศ", "ษ"}),
        "s",
    ),
    # ล → /n/ natively; preserve as ``l``.
    "l": ("n", frozenset({"ล"}), "l"),
}


def _tone_format(base: str, syl: Syllable) -> str:
    return base + _TONE_TAG[syl.tone]


def _tone_format_html(base: str, syl: Syllable) -> str:
    return base + _TONE_TAG_HTML[syl.tone]


def _syllable_carries(
    syl: Syllable, word_raw: str, source_chars: frozenset[str]
) -> bool:
    """Return True iff the syllable's orthographic slice carries one of
    the preservation-source letters.

    When the syllabifier has populated ``syl.raw`` we consult it
    directly — that's the precise per-syllable slice. When it is empty
    (some lexicon-stored words) we fall back to the whole word, which
    is safe for every current lexicon entry with a preservation
    annotation.
    """
    if syl.raw:
        return any(ch in syl.raw for ch in source_chars)
    return any(ch in word_raw for ch in source_chars)


def _lexicon_coda_override(
    word_raw: str, syl: Syllable, default: str, profile: str
) -> str | None:
    """Replace a native-collapsed coda with its preserved foreign
    surface form on the TLC scheme, when the lexicon or the fallback
    heuristic calls for it.

    Resolution order:

    1. ``etalon_compat`` never preserves — dictionary-style citation
       forms always render native phonotactics.
    2. Look up the word in the loanword lexicon under the caller's
       profile. If the entry has a preservation annotation for this
       profile, use its tag (``f`` / ``s`` / ``l``) and the matching
       default-coda + source-letter contract in
       :data:`_PRESERVATION_CONFIG`.
    3. Otherwise apply the out-of-lexicon /f/ heuristic: if the word's
       foreignness score clears the threshold and the syllable carries
       orthographic ``ฟ``, emit ``f``. This keeps unknown ฟ-final
       English loans preserving on the TLC scheme without requiring
       them to be pre-lexicalised.

    The orthographic guard never lets a native coda get relabelled:
    native ``บ`` / ``ป`` / ``พ`` (all collapsing to /p̚/) stay as
    ``p``; native ``ต`` / ``ด`` / ``จ`` / ``ช`` (collapsing to /t̚/)
    stay as ``t``; native ``น`` / ``ญ`` / ``ร`` (collapsing to /n/)
    stay as ``n``. Only the preservation-tag's listed source letters
    allow the swap.
    """
    if profile == "etalon_compat":
        return None

    # Lexicon-driven path: if the word has an entry, the entry is the
    # full story. An explicit preservation tag fires; its absence (for
    # this profile) means "don't preserve". The heuristic fallback
    # below is reserved for words that are not lexicalised at all.
    if word_raw in LOANWORDS:
        tag = get_preserved_coda(word_raw, profile)
        if tag is None:
            return None
        cfg = _PRESERVATION_CONFIG.get(tag)
        if cfg is None:
            return None
        expected_default, source_chars, surface = cfg
        if default == expected_default and _syllable_carries(
            syl, word_raw, source_chars
        ):
            return surface
        return None

    # Out-of-lexicon heuristic — /f/ only.
    if default != "p":
        return None
    if syl.coda is None or syl.coda.symbol != "p\u031a":
        return None
    fo_fan = "\u0e1f"  # ฟ
    syl_raw = syl.raw
    if syl_raw:
        if fo_fan not in syl_raw:
            return None
    elif fo_fan not in word_raw:
        # Per-syllable orthographic slice unavailable; require at least
        # that the word contains ฟ. Native codas like คลับ (บ) or ก๊อป
        # (ป) never pass this check.
        return None
    if score_foreignness(word_raw).is_loanword < _F_HEURISTIC_THRESHOLD:
        return None
    return "f"


# Vowel surface-form overrides that depend on the coda (R-204 etc).
_VOWEL_CONTEXT: dict[tuple[str, VowelLength, str], str] = {
    # เ◌ย /ɤ/ + /j/ → etalon ``eeu`` + ``y`` regardless of length
    # (เลย → leeuy, เฉลย → cha-leeuy).
    ("ɤ", VowelLength.SHORT, "j"): "eeu",
    ("ɤ", VowelLength.LONG, "j"): "eeu",
    # R-CENT-001 Case B: long /iː/ before a /w/ glide is spelled ``iaa``
    # even though the phonology is simple /iː/. Combined with the matching
    # coda override ``o``, this yields ``iaao`` for words like เขียว,
    # เดียว, เรียว — matching the etalon's pedagogical TLC convention.
    ("i", VowelLength.LONG, "w"): "iaa",
    # The open /uːə/ nucleus shortens to ``ua`` before a /j/ offglide:
    # สวย → ``suay`` (not ``suaay``), ด้วย → ``duay``. With the matching
    # coda override ``y`` this yields ``uay`` — the etalon convention,
    # parallel to the ``iaa``/``iaao`` case above.
    ("uə", VowelLength.LONG, "j"): "ua",
    # Short /u/ before /j/ keeps its plain ``u`` (คุย → khuy, not khooy);
    # long /oː/ before /j/ spells ``oo`` (โดย → dooy, not do:hi).
    ("u", VowelLength.SHORT, "j"): "u",
    ("o", VowelLength.LONG, "j"): "oo",
}


# Open-syllable (no coda) nucleus overrides. Short /ɤ/ with no coda is the
# เ◌อะ frame, spelled ``uh`` (เลอะ → luh) — distinct from the coda-bearing
# เ◌ิ spelling ``eer`` (เดิน → deern) in the base vowel map.
_VOWEL_OPEN: dict[tuple[str, VowelLength], str] = {
    ("ɤ", VowelLength.SHORT): "uh",
    # Open short /o/ (โ◌ะ, no coda) spells ``o`` — โต๊ะ → dto. The
    # coda-bearing inherent /o/ keeps the base ``oh`` (นก → nohk).
    ("o", VowelLength.SHORT): "o",
}


TLC_MAPPING: SchemeMapping = SchemeMapping(
    scheme_id="tlc",
    onset_map=_ONSET_MAP,
    vowel_map=_VOWEL_MAP,
    coda_map=_CODA_MAP,
    coda_context_map=_CODA_CONTEXT,
    vowel_context_map=_VOWEL_CONTEXT,
    vowel_open_map=_VOWEL_OPEN,
    word_coda_override=_lexicon_coda_override,
    tone_format=_tone_format,
    tone_format_html=_tone_format_html,
    cluster_joiner="",
    syllable_separator=" ",
    empty_onset="",
    unknown_fallback="?",
)


def _factory() -> MappingRenderer:
    return MappingRenderer(TLC_MAPPING)


# Register on import.
if "tlc" not in RENDERERS:
    RENDERERS.register("tlc", _factory)


__all__ = ["TLC_MAPPING"]

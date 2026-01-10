from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from thaiphon.errors import UnknownPhonemeError
from thaiphon.phonology.model import PhonologicalWord, Syllable, Tone, VowelLength
from thaiphon.renderers.base import Renderer
from thaiphon.text.diacritics import apply_macron

# Tone marks in Morev-style transcription:
_TONE_SUFFIX = {
    Tone.MID: "",
    Tone.LOW: "ˆ",  # 1st tone (low)
    Tone.FALLING: "`",  # 2nd tone (falling)
    Tone.HIGH: "ˇ",  # 3rd tone (rising-falling in Morev description)
    Tone.RISING: "´",  # 4th tone (rising)
}

# Aspiration markers:
_ASP_TEXT = "\u02e3"  # ˣ  (MODIFIER LETTER SMALL X)
_ASP_HTML = "<sup>х</sup>"  # Cyrillic х in superscript (HTML)
_ASP_PLAIN = "х"  # fallback if someone wants plain text without modifiers

# IMPORTANT:
# Store base consonant outputs here (WITHOUT aspiration).
# Aspiration is handled separately based on phoneme suffix "ʰ".
_ONSET_BASE = {
    "k": "к",
    "g": "к",  # Thai has no /g/ phonemically; keep as k-like for now
    "p": "п",
    "t": "т",
    "d": "д",
    "b": "б",
    "m": "м",
    "n": "н",
    "ŋ": "нг",
    "s": "с",
    "h": "х",
    "r": "р",
    "l": "л",
    "w": "в",  # onset w -> в
    "j": "й",  # glide
    "tɕ": "ть",  # จ-like
    "tɕʰ": "ч",  # ช/ฉ-like; in Morev usually no "чˣ"
    "f": "ф",
}

# Second consonant in clusters (r/l/w etc.) reuse same base mapping
_C2_BASE = dict(_ONSET_BASE)
_C2_BASE["w"] = "у"  # NEW: cluster glide w -> у

# Coda mapping (final consonants are limited in Thai)
_CODA = {
    None: "",
    "m": "м",
    "n": "н",
    "ŋ": "нг",
    "p": "п",
    "t": "т",
    "k": "к",
    "j": "й",
    "w": "у",
    "ʔ": "",  # glottal stop is NOT written in Morev
}

# Vowel nucleus mapping.
_VOWEL = {
    "a": ("а", 0),
    "i": ("и", 0),
    "ɯ": ("ы", 0),
    "u": ("у", 0),
    "e": ("е", 0),
    "ə": ("ə", 0),
    "ɔ": ("ɔ", 0),
    "o": ("о", 0),
    "æ": ("э", 0),
    "ɛ": ("э", 0),
    "ia": ("иа", 0),
    "ɯa": ("ыа", 0),
    "ua": ("уа", 0),
    "ai": ("ай", 0),
    "au": ("ау", 0),
    "oi": ("ой", 0),
    "ui": ("уй", 0),
}
# do not add macron to diphthongs (ai/au/oi/ui).
_DIPHTHONGS_NO_MACRON = {"ai", "au", "oi", "ui"}


def _split_aspirated(phoneme: str) -> tuple[str, bool]:
    """
    Returns (base_phoneme, is_aspirated).
    Example: 'kʰ' -> ('k', True)
             'tɕʰ' -> ('tɕʰ', False)  # special-cased, because we map it directly to 'ч'
    """
    # We treat tɕʰ as its own unit because Morev typically writes it as 'ч' (no aspiration marker).
    if phoneme == "tɕʰ":
        return phoneme, False
    if phoneme.endswith("ʰ"):
        return phoneme[:-1], True
    return phoneme, False


def _map_consonant_base(table, ph: str, where: str) -> str:
    if ph == "":
        return ""  # <- allow zero onset (carrier อ)
    try:
        return table[ph]
    except KeyError as e:
        raise UnknownPhonemeError(f"Unknown {where} phoneme: {ph!r}") from e


def _asp_marker(style: Literal["text", "html", "plain"]) -> str:
    if style == "text":
        return _ASP_TEXT
    if style == "html":
        return _ASP_HTML
    if style == "plain":
        return _ASP_PLAIN
    raise ValueError(f"Unknown aspiration_style: {style!r}")


def _render_onset_phoneme(
    phoneme: str,
    where: str,
    style: Literal["text", "html", "plain"],
    table: dict[str, str],
) -> str:
    base, asp = _split_aspirated(phoneme)
    out = _map_consonant_base(table, base, where)
    if asp:
        out += _asp_marker(style)
    return out


def _render_syllable(
    s: Syllable,
    aspiration_style: Literal["text", "html", "plain"],
    mark_tones: bool,
) -> str:
    # onset (special-case w: can be rendered as 'у' before back-ish vowels in this system)
    if s.onset.c1 == "w":
        w_as_u = {"a", "ɔ", "o", "u", "ua", "au", "ai"}  # tweakable set
        c1 = "у" if s.vowel.nucleus in w_as_u else "в"
    else:
        c1 = _render_onset_phoneme(
            s.onset.c1, "onset.c1", aspiration_style, _ONSET_BASE
        )

    c2 = ""
    if s.onset.c2:
        c2 = _render_onset_phoneme(s.onset.c2, "onset.c2", aspiration_style, _C2_BASE)
    onset = c1 + c2

    # vowel (REMOVE duplicate lookup)
    nuc, macron_pos = _VOWEL.get(s.vowel.nucleus, (None, None))
    if nuc is None:
        raise UnknownPhonemeError(f"Unknown vowel nucleus: {s.vowel.nucleus!r}")

    if (
        s.vowel.length == VowelLength.LONG
        and s.vowel.nucleus not in _DIPHTHONGS_NO_MACRON
    ):
        nuc = apply_macron(nuc, macron_pos)

    # offglide
    if s.vowel.offglide == "j":
        nuc += "й"
    elif s.vowel.offglide == "w":
        nuc += "у"
    elif s.vowel.offglide is not None:
        raise UnknownPhonemeError(f"Unknown vowel offglide: {s.vowel.offglide!r}")

    # coda
    coda = _CODA.get(s.coda.phoneme, None)
    if coda is None:
        raise UnknownPhonemeError(f"Unknown coda phoneme: {s.coda.phoneme!r}")

    tone = _TONE_SUFFIX[s.tone] if mark_tones else ""

    return f"{onset}{nuc}{coda}{tone}"


@dataclass(frozen=True)
class MorevRenderer(Renderer):
    system_id: str = "morev"
    aspiration_style: Literal["text", "html", "plain"] = "text"
    mark_tones: bool = True

    def render(self, word: PhonologicalWord) -> str:
        return "-".join(
            _render_syllable(s, self.aspiration_style, self.mark_tones)
            for s in word.syllables
        )

"""IPA comparison helper for Wiktionary etalon measurement.

Normalises IPA strings to a canonical form so that equivalent phonological
analyses compare as equal even when surface notation differs between sources.
Then classifies mismatches by the first-differing phonological dimension:
``syllable_count`` / ``onset`` / ``vowel_quality`` / ``vowel_length`` /
``coda`` / ``tone`` / ``mixed``.

Normalisation only removes notational variants that represent the same
phonological analysis — it does NOT paper over genuinely different analyses.

Key normalisations applied:

- Strip enclosing ``/…/`` or ``[…]`` brackets.
- Strip IPA stress marks (ˈ ˌ) — not phonemically distinctive in Thai.
- Remove the combining tie-bar (U+0361) in affricates (``t͡ɕ`` → ``tɕ``);
  both notations are used interchangeably in Wiktionary.
- Collapse centring-diphthong length variants: ``iːə``, ``iːə̯``, ``iə̯``,
  ``ia̯`` → ``iə`` (and likewise for ɯ and u centrings).
- Replace offglide diacritics: ``i̯`` → ``j``, ``u̯`` → ``w``.
- Strip implicit glottal onset ``ʔ`` at word start and after syllable
  boundaries — Thai vowel-initial syllables carry an underlying /ʔ/ onset
  that some Wiktionary editors write explicitly and others omit.
- Strip glottal-stop coda ``ʔ`` immediately before a tone letter or at
  syllable end — some sources write the closing glottal on short open
  syllables, others leave it implicit.
- Accept released and unreleased stop codas as equivalent
  (``p`` = ``p̚``, ``t`` = ``t̚``, ``k`` = ``k̚``).

Source data used with the ``IPAMismatchReport``:
    kaikki.org Thai Wiktionary dump — CC-BY-SA 4.0
    https://kaikki.org/dictionary/rawdata.html
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Tone classification.
# ---------------------------------------------------------------------------

# Each key is a canonical Thai tone name; values are the surface Chao-letter
# sequences accepted for that tone from Wiktionary and from our renderer.
_TONE_VARIANTS: dict[str, tuple[str, ...]] = {
    "MID":     ("˧", "˧˧", "33"),
    "LOW":     ("˨˩", "˩", "˨", "˩˩", "21", "11"),
    "FALLING": ("˥˩", "˥˧", "˦˩", "51", "41"),
    "HIGH":    ("˦˥", "˥˦", "˥", "˦", "45", "54", "55", "44"),
    "RISING":  ("˩˩˦", "˨˦", "˩˦", "˨˥", "114", "24", "25"),
}

# Build a longest-first lookup list so that multi-character sequences are
# matched before their sub-sequences.
_TONE_ALTS: list[tuple[str, str]] = sorted(
    (
        (variant, canon)
        for canon, variants in _TONE_VARIANTS.items()
        for variant in variants
    ),
    key=lambda pair: -len(pair[0]),
)

# Chao tone-letter codepoints (U+02E5..U+02E9).
_CHAO_CHARS = "˥˦˧˨˩"


def _match_tone(tail: str) -> str | None:
    """Return the canonical tone label that *tail* ends with, or None."""
    for surface, canon in _TONE_ALTS:
        if tail.endswith(surface):
            return canon
    return None


# ---------------------------------------------------------------------------
# Pre-tokenisation normalisation.
# ---------------------------------------------------------------------------

_STRESS_RE = re.compile(r"[ˈˌ]")
_SPACE_RE = re.compile(r"\s+")
# Combining tie-bar U+0361 — notational only (``t͡ɕ`` vs ``tɕ``).
_TIE_BAR = "͡"

# Centring-diphthong surface variants → canonical two-letter form.
# Both Wiktionary editorial practice and this engine vary on whether a
# length mark appears on the first element; we collapse them all.
_CENTRING_PAIRS: tuple[tuple[str, str], ...] = (
    ("iːə̯", "iə"),
    ("iːə",       "iə"),
    ("iː.ə",      "iə"),
    ("iə̯",  "iə"),
    ("ia̯",  "iə"),
    ("ɯːə̯", "ɯə"),
    ("ɯːə",       "ɯə"),
    ("ɯː.ə",      "ɯə"),
    ("ɯə̯",  "ɯə"),
    ("ɯa̯",  "ɯə"),
    ("uːə̯", "uə"),
    ("uːə",       "uə"),
    ("uː.ə",      "uə"),
    ("uə̯",  "uə"),
    ("ua̯",  "uə"),
)

# Offglide diacritics → plain sonorant letters.
# Applied AFTER the centring collapse so ``ia̯``/``ua̯`` are not turned
# into ``ij``/``uw`` first.
_OFFGLIDES: tuple[tuple[str, str], ...] = (
    ("i̯", "j"),
    ("u̯", "w"),
)


def _strip_brackets(ipa: str) -> str:
    ipa = ipa.strip()
    if len(ipa) >= 2 and ipa[0] in "/[" and ipa[-1] in "/]":
        ipa = ipa[1:-1]
    return ipa.strip()


def _canonicalise(ipa: str) -> str:
    """Apply surface normalisations that do not change the phonological analysis."""
    s = unicodedata.normalize("NFC", ipa)
    s = _strip_brackets(s)
    s = _STRESS_RE.sub("", s)
    s = _SPACE_RE.sub("", s)
    s = s.replace(_TIE_BAR, "")
    for src, dst in _CENTRING_PAIRS:
        s = s.replace(src, dst)
    for src, dst in _OFFGLIDES:
        s = s.replace(src, dst)
    # Implicit glottal onset: strip ``ʔ`` at word start and after ``.``.
    s = re.sub(r"(^|\.)ʔ", r"\1", s)
    # Implicit glottal coda: strip ``ʔ`` before a tone letter or end of syllable.
    s = re.sub(r"ʔ(?=[" + _CHAO_CHARS + r"]|$|\.)", "", s)
    # Trailing syllable separator.
    while s.endswith("."):
        s = s[:-1]
    # Collapse doubled dots.
    s = re.sub(r"\.\.+", ".", s)
    return s


# ---------------------------------------------------------------------------
# Syllable decomposition.
# ---------------------------------------------------------------------------

# Multi-character onset phonemes (checked longest-first).
_THREE_CHAR_ONSETS = {"tɕʰ"}
_TWO_CHAR_ONSETS   = {"kʰ", "tʰ", "pʰ", "tɕ"}

# IPA vowel letters produced by this engine and Wiktionary Thai entries.
_VOWEL_LETTERS = set("aeiouɛɔɯɤə")

# Coda consonant letters.
_CODA_LETTERS = set("mnŋjwptk")


@dataclass(frozen=True)
class Syl:
    """Structured representation of a single IPA syllable."""

    onset:  str
    vowel:  str
    length: str   # "" or "ː"
    coda:   str
    tone:   str   # canonical label from _TONE_VARIANTS, or ""

    def base(self) -> str:
        """Onset+vowel+length+coda — everything except tone."""
        return f"{self.onset}|{self.vowel}|{self.length}|{self.coda}"


def _parse_syllable(raw: str) -> Syl | None:
    """Parse one syllable chunk (no ``/…/``) into a structured ``Syl``."""
    s = raw

    # Pull off tone letters from the tail.
    tone = _match_tone(s)
    if tone is None:
        while s and s[-1] in _CHAO_CHARS:
            s = s[:-1]
        tone = ""
    else:
        for surface, canon in _TONE_ALTS:
            if canon == tone and s.endswith(surface):
                s = s[: -len(surface)]
                break

    # Onset: consume the longest known onset prefix.
    onset = ""
    for prefix in _THREE_CHAR_ONSETS:
        if s.startswith(prefix):
            onset = prefix
            s = s[len(prefix):]
            break
    if not onset:
        for prefix in _TWO_CHAR_ONSETS:
            if s.startswith(prefix):
                onset = prefix
                s = s[len(prefix):]
                break
    if not onset and s and s[0] not in _VOWEL_LETTERS:
        i = 0
        while i < len(s) and s[i] not in _VOWEL_LETTERS:
            i += 1
        onset = s[:i]
        s = s[i:]

    # Vowel nucleus.
    vowel = ""
    while s and s[0] in _VOWEL_LETTERS:
        vowel += s[0]
        s = s[1:]
    if not vowel:
        return None

    # Length mark.
    length = ""
    if s.startswith("ː"):
        length = "ː"
        s = s[1:]

    # Second vowel letter after length mark (centring-diphthong tail).
    while s and s[0] in _VOWEL_LETTERS:
        vowel += s[0]
        s = s[1:]

    # Coda: letters + optional unreleased-stop diacritic (U+031A).
    coda = ""
    while s:
        c = s[0]
        if c in _CODA_LETTERS:
            coda += c
            s = s[1:]
            if s.startswith("̚"):
                coda += "̚"
                s = s[1:]
        else:
            break

    # Any residue gets folded into the coda so the comparison sees it.
    if s:
        coda += s

    return Syl(onset=onset, vowel=vowel, length=length, coda=coda, tone=tone)


def parse_ipa(ipa: str) -> tuple[Syl, ...]:
    """Parse a full IPA word into a tuple of structured syllables."""
    canon = _canonicalise(ipa)
    if not canon:
        return ()
    parts = [p for p in canon.split(".") if p]
    parsed: list[Syl] = []
    for part in parts:
        syl = _parse_syllable(part)
        if syl is None:
            parsed.append(Syl(onset=part, vowel="", length="", coda="", tone=""))
        else:
            parsed.append(syl)
    return tuple(parsed)


# ---------------------------------------------------------------------------
# Coda normalisation — released vs unreleased stops.
# ---------------------------------------------------------------------------

_CODA_EQUIV: dict[str, str] = {
    "p":         "p",
    "p̚":   "p",
    "t":         "t",
    "t̚":   "t",
    "k":         "k",
    "k̚":   "k",
}


def _canon_coda(coda: str) -> str:
    return _CODA_EQUIV.get(coda, coda)


# ---------------------------------------------------------------------------
# Mismatch classification.
# ---------------------------------------------------------------------------

def classify(expected: tuple[Syl, ...], actual: tuple[Syl, ...]) -> str:
    """Return the primary dimension of difference between two parsed words."""
    if not expected or not actual:
        return "unparseable"
    if len(expected) != len(actual):
        return "syllable_count"
    onset_diff = vowel_diff = length_diff = coda_diff = tone_diff = False
    for e, a in zip(expected, actual, strict=True):
        if e.onset != a.onset:
            onset_diff = True
        if e.vowel != a.vowel:
            vowel_diff = True
        if e.length != a.length:
            length_diff = True
        if _canon_coda(e.coda) != _canon_coda(a.coda):
            coda_diff = True
        if e.tone != a.tone:
            tone_diff = True
    flags = [
        ("onset",        onset_diff),
        ("vowel_quality", vowel_diff),
        ("vowel_length", length_diff),
        ("coda",         coda_diff),
        ("tone",         tone_diff),
    ]
    active = [name for name, flag in flags if flag]
    if not active:
        return "match"
    if len(active) == 1:
        return active[0]
    return "mixed"


def ipa_equal(
    expected_raw: str, actual_raw: str
) -> tuple[bool, str, tuple[Syl, ...], tuple[Syl, ...]]:
    """Compare two IPA strings after full normalisation.

    Returns ``(is_match, classification, parsed_expected, parsed_actual)``.
    Released and unreleased stop codas are treated as equivalent.
    """
    e = parse_ipa(expected_raw)
    a = parse_ipa(actual_raw)
    if len(e) == len(a) and all(
        s1.onset == s2.onset
        and s1.vowel == s2.vowel
        and s1.length == s2.length
        and _canon_coda(s1.coda) == _canon_coda(s2.coda)
        and s1.tone == s2.tone
        for s1, s2 in zip(e, a, strict=True)
    ):
        return True, "match", e, a
    return False, classify(e, a), e, a


# ---------------------------------------------------------------------------
# Accumulator.
# ---------------------------------------------------------------------------

@dataclass
class IPAMismatchReport:
    """Accumulate exact-match / mismatch counts across a set of IPA pairs.

    Usage::

        report = IPAMismatchReport()
        for word, expected_ipa in entries:
            actual_ipa = transcribe(word, scheme="ipa")
            report.record(word, expected_ipa, actual_ipa)

        print(report.pretty(title="My run"))
        print(f"Accuracy: {report.accuracy:.2%}")
    """

    total:              int = 0
    match:              int = 0
    syllable_count_err: int = 0
    onset_err:          int = 0
    vowel_quality_err:  int = 0
    vowel_length_err:   int = 0
    coda_err:           int = 0
    tone_err:           int = 0
    mixed_err:          int = 0
    unparseable:        int = 0
    exceptions:         int = 0
    # Up to 30 examples for the pretty-print; up to 500 for external dumps.
    examples: list[tuple[str, str, str, str]] = field(default_factory=list)
    samples:  list[tuple[str, str, str, str]] = field(default_factory=list)

    def record_match(self) -> None:
        self.total += 1
        self.match += 1

    def record_mismatch(
        self, kind: str, word: str, expected: str, actual: str
    ) -> None:
        self.total += 1
        attr = f"{kind}_err"
        if hasattr(self, attr):
            setattr(self, attr, getattr(self, attr) + 1)
        else:
            self.mixed_err += 1
        if len(self.examples) < 30:
            self.examples.append((kind, word, expected, actual))
        if len(self.samples) < 500:
            self.samples.append((kind, word, expected, actual))

    def record_exception(self, word: str, expected: str, exc: str) -> None:
        self.total += 1
        self.exceptions += 1
        if len(self.examples) < 30:
            self.examples.append(("exception", word, expected, exc))
        if len(self.samples) < 500:
            self.samples.append(("exception", word, expected, exc))

    def record(self, word: str, expected: str, actual: str) -> None:
        """Compare *expected* against *actual*, update counts."""
        is_match, kind, _e, _a = ipa_equal(expected, actual)
        if is_match:
            self.record_match()
        else:
            self.record_mismatch(kind, word, expected, actual)

    @property
    def accuracy(self) -> float:
        return self.match / self.total if self.total else 0.0

    def pretty(self, title: str = "IPA ETALON DIFF REPORT") -> str:
        lines = [
            "=" * 64,
            title,
            "=" * 64,
            f"Total:           {self.total}",
            f"Exact matches:   {self.match} ({self.accuracy * 100:.2f}%)",
            f"Syllable count:  {self.syllable_count_err}",
            f"Onset:           {self.onset_err}",
            f"Vowel quality:   {self.vowel_quality_err}",
            f"Vowel length:    {self.vowel_length_err}",
            f"Coda:            {self.coda_err}",
            f"Tone:            {self.tone_err}",
            f"Mixed:           {self.mixed_err}",
            f"Unparseable:     {self.unparseable}",
            f"Exceptions:      {self.exceptions}",
            "-" * 64,
            "Sample mismatches:",
        ]
        for kind, word, exp, act in self.examples[:20]:
            lines.append(f"  [{kind}] {word!r}: expected {exp!r}, got {act!r}")
        lines.append("=" * 64)
        return "\n".join(lines)


__all__ = ["IPAMismatchReport", "parse_ipa", "ipa_equal", "classify"]

"""M-100: the 44 Thai consonants with class, onset IPA, and coda IPA."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from thaiphon.model.enums import ConsonantClass


@dataclass(frozen=True, slots=True)
class ConsonantInfo:
    letter: str
    cls: ConsonantClass
    onset_ipa: str
    coda_ipa: str | None  # None when the letter is not used as a final


# M-100 + M-102/M-103 + M-301 merged: one row per letter.
# Coda IPA follows the 26→6 collapse (M-301); letters not used as finals get None.
_CONSONANTS: dict[str, ConsonantInfo] = {
    # MC (9): ก จ ฎ ฏ ด ต บ ป อ
    "ก": ConsonantInfo("ก", ConsonantClass.MID, "k", "k̚"),
    "จ": ConsonantInfo("จ", ConsonantClass.MID, "tɕ", "t̚"),
    "ฎ": ConsonantInfo("ฎ", ConsonantClass.MID, "d", "t̚"),
    "ฏ": ConsonantInfo("ฏ", ConsonantClass.MID, "t", "t̚"),
    "ด": ConsonantInfo("ด", ConsonantClass.MID, "d", "t̚"),
    "ต": ConsonantInfo("ต", ConsonantClass.MID, "t", "t̚"),
    "บ": ConsonantInfo("บ", ConsonantClass.MID, "b", "p̚"),
    "ป": ConsonantInfo("ป", ConsonantClass.MID, "p", "p̚"),
    "อ": ConsonantInfo("อ", ConsonantClass.MID, "ʔ", None),
    # HC (11): ข ฃ ฉ ฐ ถ ผ ฝ ศ ษ ส ห
    "ข": ConsonantInfo("ข", ConsonantClass.HIGH, "kʰ", "k̚"),
    "ฃ": ConsonantInfo("ฃ", ConsonantClass.HIGH, "kʰ", None),  # obsolete
    "ฉ": ConsonantInfo("ฉ", ConsonantClass.HIGH, "tɕʰ", None),
    "ฐ": ConsonantInfo("ฐ", ConsonantClass.HIGH, "tʰ", "t̚"),
    "ถ": ConsonantInfo("ถ", ConsonantClass.HIGH, "tʰ", "t̚"),
    "ผ": ConsonantInfo("ผ", ConsonantClass.HIGH, "pʰ", None),
    "ฝ": ConsonantInfo("ฝ", ConsonantClass.HIGH, "f", None),
    "ศ": ConsonantInfo("ศ", ConsonantClass.HIGH, "s", "t̚"),
    "ษ": ConsonantInfo("ษ", ConsonantClass.HIGH, "s", "t̚"),
    "ส": ConsonantInfo("ส", ConsonantClass.HIGH, "s", "t̚"),
    "ห": ConsonantInfo("ห", ConsonantClass.HIGH, "h", None),
    # LCP (14): ค ฅ ฆ ช ฌ ซ ฑ ฒ ท ธ พ ภ ฟ ฮ
    "ค": ConsonantInfo("ค", ConsonantClass.LOW_PAIRED, "kʰ", "k̚"),
    "ฅ": ConsonantInfo("ฅ", ConsonantClass.LOW_PAIRED, "kʰ", None),  # obsolete
    "ฆ": ConsonantInfo("ฆ", ConsonantClass.LOW_PAIRED, "kʰ", "k̚"),
    "ช": ConsonantInfo("ช", ConsonantClass.LOW_PAIRED, "tɕʰ", "t̚"),
    "ฌ": ConsonantInfo("ฌ", ConsonantClass.LOW_PAIRED, "tɕʰ", None),
    "ซ": ConsonantInfo("ซ", ConsonantClass.LOW_PAIRED, "s", "t̚"),
    "ฑ": ConsonantInfo("ฑ", ConsonantClass.LOW_PAIRED, "tʰ", "t̚"),
    "ฒ": ConsonantInfo("ฒ", ConsonantClass.LOW_PAIRED, "tʰ", "t̚"),
    "ท": ConsonantInfo("ท", ConsonantClass.LOW_PAIRED, "tʰ", "t̚"),
    "ธ": ConsonantInfo("ธ", ConsonantClass.LOW_PAIRED, "tʰ", "t̚"),
    "พ": ConsonantInfo("พ", ConsonantClass.LOW_PAIRED, "pʰ", "p̚"),
    "ภ": ConsonantInfo("ภ", ConsonantClass.LOW_PAIRED, "pʰ", "p̚"),
    "ฟ": ConsonantInfo("ฟ", ConsonantClass.LOW_PAIRED, "f", "p̚"),
    "ฮ": ConsonantInfo("ฮ", ConsonantClass.LOW_PAIRED, "h", None),
    # LCS (10): ง ญ ณ น ม ย ร ล ฬ ว
    "ง": ConsonantInfo("ง", ConsonantClass.LOW_SONORANT, "ŋ", "ŋ"),
    "ญ": ConsonantInfo("ญ", ConsonantClass.LOW_SONORANT, "j", "n"),
    "ณ": ConsonantInfo("ณ", ConsonantClass.LOW_SONORANT, "n", "n"),
    "น": ConsonantInfo("น", ConsonantClass.LOW_SONORANT, "n", "n"),
    "ม": ConsonantInfo("ม", ConsonantClass.LOW_SONORANT, "m", "m"),
    "ย": ConsonantInfo("ย", ConsonantClass.LOW_SONORANT, "j", "j"),
    "ร": ConsonantInfo("ร", ConsonantClass.LOW_SONORANT, "r", "n"),
    "ล": ConsonantInfo("ล", ConsonantClass.LOW_SONORANT, "l", "n"),
    "ฬ": ConsonantInfo("ฬ", ConsonantClass.LOW_SONORANT, "l", "n"),
    "ว": ConsonantInfo("ว", ConsonantClass.LOW_SONORANT, "w", "w"),
}

CONSONANTS: Mapping[str, ConsonantInfo] = MappingProxyType(_CONSONANTS)


def lookup(letter: str) -> ConsonantInfo:
    try:
        return _CONSONANTS[letter]
    except KeyError as exc:
        raise KeyError(f"not a Thai consonant: {letter!r}") from exc


def class_of(letter: str) -> ConsonantClass:
    return lookup(letter).cls

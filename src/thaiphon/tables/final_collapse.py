"""M-301: the 26→6 coda consonant collapse."""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

# 6 native final phonemes: /m n ŋ p̚ t̚ k̚/. Semi-vowel /w j/ come from the
# consonants ว and ย when used as finals (sustained sonorant endings).
_FINAL_COLLAPSE: dict[str, str] = {
    # /m/
    "ม": "m",
    # /n/
    "น": "n",
    "ญ": "n",
    "ณ": "n",
    "ร": "n",
    "ล": "n",
    "ฬ": "n",
    # /ŋ/
    "ง": "ŋ",
    # /p̚/
    "บ": "p̚",
    "ป": "p̚",
    "พ": "p̚",
    "ฟ": "p̚",
    "ภ": "p̚",
    # /t̚/
    "จ": "t̚",
    "ช": "t̚",
    "ซ": "t̚",
    "ฌ": "t̚",
    "ฎ": "t̚",
    "ฏ": "t̚",
    "ฐ": "t̚",
    "ฑ": "t̚",
    "ฒ": "t̚",
    "ด": "t̚",
    "ต": "t̚",
    "ถ": "t̚",
    "ท": "t̚",
    "ธ": "t̚",
    "ศ": "t̚",
    "ษ": "t̚",
    "ส": "t̚",
    # /k̚/
    "ก": "k̚",
    "ข": "k̚",
    "ค": "k̚",
    "ฆ": "k̚",
    # semi-vowel finals
    "ว": "w",
    "ย": "j",
}

FINAL_COLLAPSE: Mapping[str, str] = MappingProxyType(_FINAL_COLLAPSE)


def collapse(letter: str) -> str:
    """Return the collapsed coda phoneme for a Thai consonant used as final."""
    try:
        return _FINAL_COLLAPSE[letter]
    except KeyError as exc:
        raise KeyError(f"not a valid final consonant: {letter!r}") from exc

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pytest

from thaiphon.phonology.model import Tone, VowelLength


@dataclass(frozen=True)
class ExpectedSyllable:
    onset: str
    nucleus: str
    length: VowelLength
    coda: Optional[str]
    tone: Tone
    offglide: Optional[str] = None


CASES: list[tuple[str, ExpectedSyllable]] = [
    # -------------------------
    # MID class, no tone mark
    # -------------------------
    (
        "กา",
        ExpectedSyllable("k", "a", VowelLength.LONG, None, Tone.MID),
    ),  # mid live -> mid
    (
        "กะ",
        ExpectedSyllable("k", "a", VowelLength.SHORT, "ʔ", Tone.LOW),
    ),  # mid dead (open+short) -> low
    (
        "กบ",
        ExpectedSyllable("k", "o", VowelLength.SHORT, "p", Tone.LOW),
    ),  # mid dead (stop) -> low
    (
        "กิน",
        ExpectedSyllable("k", "i", VowelLength.SHORT, "n", Tone.MID),
    ),  # mid live -> mid
    # -------------------------
    # HIGH class, no tone mark
    # -------------------------
    (
        "ขา",
        ExpectedSyllable("kʰ", "a", VowelLength.LONG, None, Tone.RISING),
    ),  # high live -> rising
    (
        "ขะ",
        ExpectedSyllable("kʰ", "a", VowelLength.SHORT, "ʔ", Tone.LOW),
    ),  # high dead -> low
    (
        "ขับ",
        ExpectedSyllable("kʰ", "a", VowelLength.SHORT, "p", Tone.LOW),
    ),  # high dead -> low
    (
        "ขีด",
        ExpectedSyllable("kʰ", "i", VowelLength.LONG, "t", Tone.LOW),
    ),  # high dead -> low
    # -------------------------
    # LOW class, no tone mark
    # -------------------------
    (
        "มา",
        ExpectedSyllable("m", "a", VowelLength.LONG, None, Tone.MID),
    ),  # low live -> mid
    (
        "มะ",
        ExpectedSyllable("m", "a", VowelLength.SHORT, "ʔ", Tone.HIGH),
    ),  # low dead short -> high
    (
        "มัก",
        ExpectedSyllable("m", "a", VowelLength.SHORT, "k", Tone.HIGH),
    ),  # low dead stop short -> high
    (
        "มาก",
        ExpectedSyllable("m", "a", VowelLength.LONG, "k", Tone.FALLING),
    ),  # low dead stop long -> falling
    # -------------------------
    # mai ek (่): Mid/High => LOW, Low => FALLING
    # -------------------------
    ("ไก่", ExpectedSyllable("k", "ai", VowelLength.LONG, None, Tone.LOW)),
    ("ข่า", ExpectedSyllable("kʰ", "a", VowelLength.LONG, None, Tone.LOW)),
    ("ค่า", ExpectedSyllable("kʰ", "a", VowelLength.LONG, None, Tone.FALLING)),
    # -------------------------
    # mai tho (้): Mid/High => FALLING, Low => HIGH
    # -------------------------
    ("ก้า", ExpectedSyllable("k", "a", VowelLength.LONG, None, Tone.FALLING)),
    (
        "ข้าว",
        ExpectedSyllable("kʰ", "a", VowelLength.LONG, None, Tone.FALLING, offglide="w"),
    ),
    ("ไม้", ExpectedSyllable("m", "ai", VowelLength.LONG, None, Tone.HIGH)),
    # -------------------------
    # mai tri (๊) / mai chattawa (๋)
    # -------------------------
    ("ก๊า", ExpectedSyllable("k", "a", VowelLength.LONG, None, Tone.HIGH)),
    ("ก๋า", ExpectedSyllable("k", "a", VowelLength.LONG, None, Tone.RISING)),
    # -------------------------
    # Leading ห นำ (ho nam): tonal class source becomes HIGH (ห), onset is sonorant
    # -------------------------
    ("หมา", ExpectedSyllable("m", "a", VowelLength.LONG, None, Tone.RISING)),
    ("หมี", ExpectedSyllable("m", "i", VowelLength.LONG, None, Tone.RISING)),
    ("ใหม่", ExpectedSyllable("m", "ai", VowelLength.LONG, None, Tone.LOW)),
    # -------------------------
    # ว as part of vowel spelling (ua), not cluster and not coda
    # -------------------------
    ("ฃวด", ExpectedSyllable("kʰ", "ua", VowelLength.LONG, "t", Tone.LOW)),
    ("ขวด", ExpectedSyllable("kʰ", "ua", VowelLength.LONG, "t", Tone.LOW)),
    # -------------------------
    # Finals: sonorant vs stop
    # -------------------------
    ("กิ่ง", ExpectedSyllable("k", "i", VowelLength.SHORT, "ŋ", Tone.LOW)),
    ("ปิด", ExpectedSyllable("p", "i", VowelLength.SHORT, "t", Tone.LOW)),
    ("คิด", ExpectedSyllable("kʰ", "i", VowelLength.SHORT, "t", Tone.HIGH)),
    ("ขึ้น", ExpectedSyllable("kʰ", "ɯ", VowelLength.SHORT, "n", Tone.FALLING)),
    # -------------------------
    # Inherent vowels (no written vowel signs)
    # closed -> short o
    # -------------------------
    ("กง", ExpectedSyllable("k", "o", VowelLength.SHORT, "ŋ", Tone.MID)),
    ("คน", ExpectedSyllable("kʰ", "o", VowelLength.SHORT, "n", Tone.MID)),
    ("สม", ExpectedSyllable("s", "o", VowelLength.SHORT, "m", Tone.RISING)),
    (
        "ผล",
        ExpectedSyllable("pʰ", "o", VowelLength.SHORT, "n", Tone.RISING),
    ),  # high class ผ
    # open inherent a (represented as ʔ in the model for short open)
    ("จะ", ExpectedSyllable("tɕ", "a", VowelLength.SHORT, "ʔ", Tone.LOW)),
    ("นะ", ExpectedSyllable("n", "a", VowelLength.SHORT, "ʔ", Tone.HIGH)),
    # -------------------------
    # Special spelling: ทร- -> /s/
    # -------------------------
    ("ทราบ", ExpectedSyllable("s", "a", VowelLength.LONG, "p", Tone.FALLING)),
    # -------------------------
    # Morev-style “กร/จร/พร” reading rule coverage
    # -------------------------
    ("กร", ExpectedSyllable("k", "o", VowelLength.LONG, "n", Tone.MID)),
    ("จร", ExpectedSyllable("tɕ", "o", VowelLength.LONG, "n", Tone.MID)),
    ("พร", ExpectedSyllable("pʰ", "o", VowelLength.LONG, "n", Tone.MID)),
]


@pytest.mark.parametrize(
    "thai, exp",
    CASES,
    ids=[thai for thai, _ in CASES],
)
def test_reader_real_words_phonology(thai_reader, thai: str, exp: ExpectedSyllable):
    w = thai_reader.read_word(thai)

    assert len(w.syllables) == 1, f"{thai}: expected 1 syllable, got {len(w.syllables)}"
    s = w.syllables[0]

    assert s.onset.c1 == exp.onset, f"{thai}: onset {s.onset.c1} != {exp.onset}"
    assert (
        s.vowel.nucleus == exp.nucleus
    ), f"{thai}: nucleus {s.vowel.nucleus} != {exp.nucleus}"
    assert (
        s.vowel.length == exp.length
    ), f"{thai}: length {s.vowel.length} != {exp.length}"
    assert (
        s.vowel.offglide == exp.offglide
    ), f"{thai}: offglide {s.vowel.offglide} != {exp.offglide}"
    assert s.coda.phoneme == exp.coda, f"{thai}: coda {s.coda.phoneme} != {exp.coda}"
    assert s.tone == exp.tone, f"{thai}: tone {s.tone} != {exp.tone}"

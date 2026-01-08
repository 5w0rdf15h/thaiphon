import pytest

from thaiphon.phonology.model import Tone, VowelLength
from thaiphon.reader.thai_orthography_reader import ThaiOrthographyReader


@pytest.mark.parametrize(
    "thai, exp",
    [
        # CC sequences split into two syllables; the second syllable can borrow
        # tone class source from the first syllable when its onset is a sonorant
        # (ม น ง ย ร ล ว) in these common patterns.
        # ตลก -> taˆ-lokˆ
        (
            "ตลก",
            [
                # ตะ- : t + a(short) + ʔ, dead -> LOW (mid-class ต)
                dict(
                    onset="t",
                    nucleus="a",
                    length=VowelLength.SHORT,
                    coda="ʔ",
                    tone=Tone.LOW,
                ),
                # -ลก : l + o(short) + k, dead; tone source borrowed from ต (mid) -> LOW
                dict(
                    onset="l",
                    nucleus="o",
                    length=VowelLength.SHORT,
                    coda="k",
                    tone=Tone.LOW,
                ),
            ],
        ),
        # ขนม -> khaˆ-nom´
        (
            "ขนม",
            [
                # ขะ- : kʰ + a(short) + ʔ, dead -> LOW (high-class ข)
                dict(
                    onset="kʰ",
                    nucleus="a",
                    length=VowelLength.SHORT,
                    coda="ʔ",
                    tone=Tone.LOW,
                ),
                # -นม : n + o(short) + m, live; tone source borrowed from ข (high) -> RISING
                dict(
                    onset="n",
                    nucleus="o",
                    length=VowelLength.SHORT,
                    coda="m",
                    tone=Tone.RISING,
                ),
            ],
        ),
        # ถนน -> thaˆ-non´
        (
            "ถนน",
            [
                # ถะ- : tʰ + a(short) + ʔ, dead -> LOW (high-class ถ)
                dict(
                    onset="tʰ",
                    nucleus="a",
                    length=VowelLength.SHORT,
                    coda="ʔ",
                    tone=Tone.LOW,
                ),
                # -นน : n + o(short) + n, live; tone source borrowed from ถ (high) -> RISING
                dict(
                    onset="n",
                    nucleus="o",
                    length=VowelLength.SHORT,
                    coda="n",
                    tone=Tone.RISING,
                ),
            ],
        ),
    ],
)
def test_reader_cc_split_and_tone_borrowing(thai: str, exp: list[dict]):
    r = ThaiOrthographyReader()
    w = r.read_word(thai)

    assert (
        len(w.syllables) == 2
    ), f"{thai}: expected 2 syllables, got {len(w.syllables)}"

    for i, e in enumerate(exp):
        s = w.syllables[i]
        assert (
            s.onset.c1 == e["onset"]
        ), f"{thai} syllable {i}: onset {s.onset.c1} != {e['onset']}"
        assert (
            s.vowel.nucleus == e["nucleus"]
        ), f"{thai} syllable {i}: nucleus {s.vowel.nucleus} != {e['nucleus']}"
        assert (
            s.vowel.length == e["length"]
        ), f"{thai} syllable {i}: length {s.vowel.length} != {e['length']}"
        assert (
            s.coda.phoneme == e["coda"]
        ), f"{thai} syllable {i}: coda {s.coda.phoneme} != {e['coda']}"
        assert s.tone == e["tone"], f"{thai} syllable {i}: tone {s.tone} != {e['tone']}"

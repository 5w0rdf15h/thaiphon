import pytest

from thaiphon.phonology.model import Tone, VowelLength


@pytest.mark.parametrize(
    "thai, expected",
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
def test_reader_cc_split_and_tone_borrowing(
    thai: str, expected: list[dict], thai_reader
):
    w = thai_reader.read_word(thai)

    assert (
        len(w.syllables) == 2
    ), f"{thai}: expected 2 syllables, got {len(w.syllables)}"

    for i, exp in enumerate(expected):
        s = w.syllables[i]

        assert (
            s.onset.c1 == exp["onset"]
        ), f"{thai} syllable {i}: onset {s.onset.c1!r} != {exp['onset']!r}"
        assert (
            s.vowel.nucleus == exp["nucleus"]
        ), f"{thai} syllable {i}: nucleus {s.vowel.nucleus!r} != {exp['nucleus']!r}"
        assert (
            s.vowel.length == exp["length"]
        ), f"{thai} syllable {i}: length {s.vowel.length!r} != {exp['length']!r}"
        assert (
            s.coda.phoneme == exp["coda"]
        ), f"{thai} syllable {i}: coda {s.coda.phoneme!r} != {exp['coda']!r}"
        assert (
            s.tone == exp["tone"]
        ), f"{thai} syllable {i}: tone {s.tone!r} != {exp['tone']!r}"

import pytest

from thaiphon.phonology.model import Tone, VowelLength


@pytest.mark.parametrize(
    "thai, expected",
    [
        # ---- ho nam: ห + sonorant must NOT split
        (
            "หมอ",
            dict(
                syllables=1,
                onset="m",
                nucleus="o",
                length=VowelLength.LONG,
                coda=None,
                tone=Tone.RISING,
            ),
        ),
        (
            "มอ",
            dict(
                syllables=1,
                onset="m",
                nucleus="o",
                length=VowelLength.LONG,
                coda=None,
                tone=Tone.MID,
            ),
        ),
        (
            "หลง",
            dict(
                syllables=1,
                onset="l",
                nucleus="o",
                length=VowelLength.SHORT,
                coda="ŋ",
                tone=Tone.RISING,
            ),
        ),
        (
            "ลง",
            dict(
                syllables=1,
                onset="l",
                nucleus="o",
                length=VowelLength.SHORT,
                coda="ŋ",
                tone=Tone.MID,
            ),
        ),
        # ---- special อนำ like ห in the classic 4 words (อย-)
        # Ensure: does not crash, stays 1 syllable, onset pronounced as 'j' (/j/)
        # and tone behaves as if leading ห.
        (
            "อย่าง",
            dict(
                syllables=1,
                onset="j",
                nucleus="a",
                length=VowelLength.LONG,
                coda="ŋ",
                tone=Tone.LOW,
            ),
        ),
        (
            "อย่า",
            dict(
                syllables=1,
                onset="j",
                nucleus="a",
                length=VowelLength.LONG,
                coda=None,
                tone=Tone.LOW,
            ),
        ),
        (
            "อยาก",
            dict(
                syllables=1,
                onset="j",
                nucleus="a",
                length=VowelLength.LONG,
                coda="k",
                tone=Tone.LOW,
            ),
        ),
        (
            "อยู่",
            dict(
                syllables=1,
                onset="j",
                nucleus="u",
                length=VowelLength.LONG,
                coda=None,
                tone=Tone.LOW,
            ),
        ),
    ],
)
def test_reader_ho_nam_and_special_oy_and_vowel_oo(
    thai: str, expected: dict, thai_reader
):
    w = thai_reader.read_word(thai)

    assert (
        len(w.syllables) == expected["syllables"]
    ), f"{thai}: expected {expected['syllables']} syllable(s), got {len(w.syllables)}"

    s = w.syllables[0]
    assert (
        s.onset.c1 == expected["onset"]
    ), f"{thai}: onset {s.onset.c1!r} != {expected['onset']!r}"
    assert (
        s.vowel.nucleus == expected["nucleus"]
    ), f"{thai}: nucleus {s.vowel.nucleus!r} != {expected['nucleus']!r}"
    assert (
        s.vowel.length == expected["length"]
    ), f"{thai}: length {s.vowel.length!r} != {expected['length']!r}"
    assert (
        s.coda.phoneme == expected["coda"]
    ), f"{thai}: coda {s.coda.phoneme!r} != {expected['coda']!r}"
    assert (
        s.tone == expected["tone"]
    ), f"{thai}: tone {s.tone!r} != {expected['tone']!r}"

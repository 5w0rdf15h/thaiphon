import pytest

from thaiphon.phonology.model import Tone, VowelLength
from thaiphon.reader.thai_orthography_reader import ThaiOrthographyReader


@pytest.mark.parametrize(
    "thai, exp_syllables, exp_onset, exp_vowel_nucleus, exp_vowel_len, exp_coda, exp_tone",
    [
        # ---- ho nam: ห + sonorant must NOT split
        ("หมอ", 1, "m", "o", VowelLength.LONG, None, Tone.RISING),
        ("มอ", 1, "m", "o", VowelLength.LONG, None, Tone.MID),
        ("หลง", 1, "l", "o", VowelLength.SHORT, "ŋ", Tone.RISING),
        ("ลง", 1, "l", "o", VowelLength.SHORT, "ŋ", Tone.MID),
        # ---- special อนำ like ห in the classic 4 words
        # We assert: does not crash, does not split into "อ-..."
        # and onset is pronounced as 'y' (/j/) with HIGH tone-source behavior.
        ("อย่าง", 1, "j", "a", VowelLength.LONG, "ŋ", Tone.LOW),  # อย + ่ (mai ek)
        ("อย่า", 1, "j", "a", VowelLength.LONG, None, Tone.LOW),  # open syllable
        ("อยาก", 1, "j", "a", VowelLength.LONG, "k", Tone.LOW),  # dead syllable (stop)
        ("อยู่", 1, "j", "u", VowelLength.LONG, None, Tone.LOW),  # อย + ่, long u
    ],
)
def test_reader_ho_nam_and_special_oy_and_vowel_oo(
    thai, exp_syllables, exp_onset, exp_vowel_nucleus, exp_vowel_len, exp_coda, exp_tone
):
    r = ThaiOrthographyReader()
    w = r.read_word(thai)

    assert (
        len(w.syllables) == exp_syllables
    ), f"{thai}: expected {exp_syllables} syllable(s), got {len(w.syllables)}"
    s = w.syllables[0]

    assert s.onset.c1 == exp_onset, f"{thai}: onset {s.onset.c1} != {exp_onset}"
    assert (
        s.vowel.nucleus == exp_vowel_nucleus
    ), f"{thai}: nucleus {s.vowel.nucleus} != {exp_vowel_nucleus}"
    assert (
        s.vowel.length == exp_vowel_len
    ), f"{thai}: length {s.vowel.length} != {exp_vowel_len}"
    assert s.coda.phoneme == exp_coda, f"{thai}: coda {s.coda.phoneme} != {exp_coda}"
    assert s.tone == exp_tone, f"{thai}: tone {s.tone} != {exp_tone}"

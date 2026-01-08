import pytest

from thaiphon.phonology.model import Tone, VowelLength
from thaiphon.reader.thai_orthography_reader import ThaiOrthographyReader

# These tests follow the standard Thai tone table as used in RTL (Rak Thai Language School) textbooks:
# Tone = f(onset consonant class, tone mark, live/dead,
#          with vowel length distinction for low-class dead syllables).
#
# Coverage:
# - 3 consonant classes (Mid / High / Low)
# - no tone mark + ่ / ้ / ๊ / ๋ (where applicable)
# - live vs dead syllables:
#   * stop coda => dead
#   * open + short vowel => dead (represented as ʔ in the model)
#   * sonorant coda => live
# - leading ห นำ (ho nam)
# - -าว as /aːw/ (offglide=w, no coda)
#
# NOTE:
# Words with implicit vowels without vowel signs (e.g. กง / คน)
# are intentionally excluded until the RTL-specific rule
# (usually short /o/) is explicitly finalized.


@pytest.mark.parametrize(
    "thai, exp_onset, exp_vowel_nucleus, exp_vowel_len, exp_offglide, exp_coda, exp_tone",
    [
        # -------------------------
        # MID class, no tone mark
        # -------------------------
        ("กา", "k", "a", VowelLength.LONG, None, None, Tone.MID),  # mid live -> mid
        (
            "กะ",
            "k",
            "a",
            VowelLength.SHORT,
            None,
            "ʔ",
            Tone.LOW,
        ),  # mid dead (open+short) -> low
        (
            "กบ",
            "k",
            "o",
            VowelLength.SHORT,
            None,
            "p",
            Tone.LOW,
        ),  # mid dead (stop) -> low
        (
            "กิน",
            "k",
            "i",
            VowelLength.SHORT,
            None,
            "n",
            Tone.MID,
        ),  # mid live (sonorant) -> mid
        # -------------------------
        # HIGH class, no tone mark
        # -------------------------
        (
            "ขา",
            "kʰ",
            "a",
            VowelLength.LONG,
            None,
            None,
            Tone.RISING,
        ),  # high live -> rising
        (
            "ขะ",
            "kʰ",
            "a",
            VowelLength.SHORT,
            None,
            "ʔ",
            Tone.LOW,
        ),  # high dead (open+short) -> low
        (
            "ขับ",
            "kʰ",
            "a",
            VowelLength.SHORT,
            None,
            "p",
            Tone.LOW,
        ),  # high dead (stop) -> low
        (
            "ขีด",
            "kʰ",
            "i",
            VowelLength.LONG,
            None,
            "t",
            Tone.LOW,
        ),  # high dead (stop), vowel length irrelevant
        # -------------------------
        # LOW class, no tone mark
        # -------------------------
        ("มา", "m", "a", VowelLength.LONG, None, None, Tone.MID),  # low live -> mid
        (
            "มะ",
            "m",
            "a",
            VowelLength.SHORT,
            None,
            "ʔ",
            Tone.HIGH,
        ),  # low dead (open+short) -> high
        (
            "มัก",
            "m",
            "a",
            VowelLength.SHORT,
            None,
            "k",
            Tone.HIGH,
        ),  # low dead (stop short) -> high
        (
            "มาก",
            "m",
            "a",
            VowelLength.LONG,
            None,
            "k",
            Tone.FALLING,
        ),  # low dead (stop long) -> falling
        # -------------------------
        # mai ek (่)
        # Mid/High => LOW, Low => FALLING
        # -------------------------
        ("ไก่", "k", "ai", VowelLength.LONG, None, None, Tone.LOW),  # mid + ่ -> low
        ("ข่า", "kʰ", "a", VowelLength.LONG, None, None, Tone.LOW),  # high + ่ -> low
        (
            "ค่า",
            "kʰ",
            "a",
            VowelLength.LONG,
            None,
            None,
            Tone.FALLING,
        ),  # low + ่ -> falling
        # -------------------------
        # mai tho (้)
        # Mid/High => FALLING, Low => HIGH
        # -------------------------
        (
            "ก้า",
            "k",
            "a",
            VowelLength.LONG,
            None,
            None,
            Tone.FALLING,
        ),  # mid + ้ -> falling
        (
            "ข้าว",
            "kʰ",
            "a",
            VowelLength.LONG,
            "w",
            None,
            Tone.FALLING,
        ),  # high + ้ -> falling, -าว => aːw
        ("ไม้", "m", "ai", VowelLength.LONG, None, None, Tone.HIGH),  # low + ้ -> high
        # -------------------------
        # mai tri (๊) / mai chattawa (๋)
        # Normally taught as mid-class-only
        # -------------------------
        ("ก๊า", "k", "a", VowelLength.LONG, None, None, Tone.HIGH),  # mid + ๊ -> high
        ("ก๋า", "k", "a", VowelLength.LONG, None, None, Tone.RISING),  # mid + ๋ -> rising
        # -------------------------
        # Leading ห นำ (ho nam)
        # Tonal class source becomes HIGH (ห), onset is sonorant
        # -------------------------
        (
            "หมา",
            "m",
            "a",
            VowelLength.LONG,
            None,
            None,
            Tone.RISING,
        ),  # high-source live -> rising
        (
            "หมี",
            "m",
            "i",
            VowelLength.LONG,
            None,
            None,
            Tone.RISING,
        ),  # high-source live -> rising
        (
            "ใหม่",
            "m",
            "ai",
            VowelLength.LONG,
            None,
            None,
            Tone.LOW,
        ),  # high-source + ่ -> low
        # -------------------------
        # ว as part of vowel spelling (ua), not cluster and not coda
        # -------------------------
        (
            "ฃวด",
            "kʰ",
            "ua",
            VowelLength.LONG,
            None,
            "t",
            Tone.LOW,
        ),  # uā vowel, final stop
        (
            "ขวด",
            "kʰ",
            "ua",
            VowelLength.LONG,
            None,
            "t",
            Tone.LOW,
        ),  # same pattern, different letter
        # -------------------------
        # Finals: sonorant vs stop
        # -------------------------
        ("กิ่ง", "k", "i", VowelLength.SHORT, None, "ŋ", Tone.LOW),  # mid + ่ -> low
        (
            "ปิด",
            "p",
            "i",
            VowelLength.SHORT,
            None,
            "t",
            Tone.LOW,
        ),  # mid dead (stop) -> low
        (
            "คิด",
            "kʰ",
            "i",
            VowelLength.SHORT,
            None,
            "t",
            Tone.HIGH,
        ),  # low-class + dead short -> high
        (
            "ขึ้น",
            "kʰ",
            "ɯ",
            VowelLength.SHORT,
            None,
            "n",
            Tone.FALLING,
        ),  # high + ้ -> falling
        # -------------------------
        # Inherent vowels (no written vowel signs)
        # RTL rule:
        # closed -> short o
        # -------------------------
        ("กง", "k", "o", VowelLength.SHORT, None, "ŋ", Tone.MID),
        ("คน", "kʰ", "o", VowelLength.SHORT, None, "n", Tone.MID),
        ("สม", "s", "o", VowelLength.SHORT, None, "m", Tone.RISING),
        ("ผล", "pʰ", "o", VowelLength.SHORT, None, "n", Tone.RISING),  # high class ผ
        # open inherent a
        ("จะ", "tɕ", "a", VowelLength.SHORT, None, "ʔ", Tone.LOW),
        ("นะ", "n", "a", VowelLength.SHORT, None, "ʔ", Tone.HIGH),
        # -------------------------
        # Special spelling: ทร- -> /s/ (e.g., ทราบ = ซาบ)
        # -------------------------
        ("ทราบ", "s", "a", VowelLength.LONG, None, "p", Tone.FALLING),
        # ---
        ("กร", "k", "o", VowelLength.LONG, None, "n", Tone.MID),
        ("จร", "tɕ", "o", VowelLength.LONG, None, "n", Tone.MID),
        ("พร", "pʰ", "o", VowelLength.LONG, None, "n", Tone.MID),
    ],
)
def test_reader_real_words_phonology(
    thai, exp_onset, exp_vowel_nucleus, exp_vowel_len, exp_offglide, exp_coda, exp_tone
):
    r = ThaiOrthographyReader()
    w = r.read_word(thai)

    assert len(w.syllables) == 1, f"{thai}: expected 1 syllable, got {len(w.syllables)}"
    s = w.syllables[0]

    assert s.onset.c1 == exp_onset, f"{thai}: onset {s.onset.c1} != {exp_onset}"
    assert (
        s.vowel.nucleus == exp_vowel_nucleus
    ), f"{thai}: nucleus {s.vowel.nucleus} != {exp_vowel_nucleus}"
    assert (
        s.vowel.length == exp_vowel_len
    ), f"{thai}: length {s.vowel.length} != {exp_vowel_len}"
    assert (
        s.vowel.offglide == exp_offglide
    ), f"{thai}: offglide {s.vowel.offglide} != {exp_offglide}"
    assert s.coda.phoneme == exp_coda, f"{thai}: coda {s.coda.phoneme} != {exp_coda}"
    assert s.tone == exp_tone, f"{thai}: tone {s.tone} != {exp_tone}"

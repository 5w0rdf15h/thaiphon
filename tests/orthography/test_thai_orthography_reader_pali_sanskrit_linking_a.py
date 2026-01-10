import pytest

from thaiphon.phonology.model import FinalType, VowelLength


@pytest.mark.parametrize(
    "thai, expected_raws",
    [
        ("รัฐธรรมนูญ", ["รัฐ", "ฐะ", "ธรรม", "มะ", "นูญ"]),
        # key loanwords:
        ("โทรศพท์", ["โท", "ระ", "ศพท์"]),  # IMPORTANT: not "โทร"
        ("จุลทรรศน์", ["จุล", "ละ", "ทรรศน์"]),
    ],
)
def test_reader_pali_sanskrit_linking_a_raws(
    thai: str, expected_raws: list[str], thai_reader
):
    w = thai_reader.read_word(thai)
    assert [s.raw for s in w.syllables] == expected_raws


def test_reader_telephone_avoids_ro_as_coda_n(thai_reader):
    w = thai_reader.read_word("โทรศพท์")
    assert [s.raw for s in w.syllables] == ["โท", "ระ", "ศพท์"]

    s0, s1, s2 = w.syllables

    # โท = tʰ + ɔː and MUST be open (no coda 'n')
    assert s0.onset.c1 == "tʰ"
    assert s0.vowel.nucleus == "ɔ"  # โ = ɔ
    assert s0.vowel.length == VowelLength.LONG
    assert s0.coda.phoneme is None
    assert s0.coda.final_type == FinalType.NONE

    # ระ should be onset r + a (short; postprocess may add ʔ as pseudo-coda)
    assert s1.onset.c1 == "r"
    assert s1.vowel.nucleus == "a"

    # ศพท์ should behave like "sap" in loanword reading (not "sop")
    assert s2.onset.c1 == "s"
    assert s2.vowel.nucleus == "a"
    assert s2.vowel.length == VowelLength.SHORT
    assert s2.coda.phoneme == "p"


def test_reader_julathat_not_s_digraph(thai_reader):
    w = thai_reader.read_word("จุลทรรศน์")
    assert [s.raw for s in w.syllables] == ["จุล", "ละ", "ทรรศน์"]

    # last syllable must NOT start with /s/ (digraph ทร- rule must not trigger for ทรร-)
    last = w.syllables[-1]
    assert last.onset.c1 == "tʰ"
    assert last.vowel.nucleus == "a"
    assert last.coda.phoneme == "t"

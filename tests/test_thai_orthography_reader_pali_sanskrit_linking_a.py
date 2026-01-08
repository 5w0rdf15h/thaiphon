import pytest

from thaiphon.reader.thai_orthography_reader import ThaiOrthographyReader


@pytest.mark.parametrize(
    "thai, expected_raws",
    [
        # รัฐธรรมนูญ -> ратˇ-тхаˆ-тхам-маˇ-нӯн
        ("รัฐธรรมนูญ", ["รัฐ", "ฐะ", "ธรรม", "มะ", "นูญ"]),
    ],
)
def test_reader_pali_sanskrit_linking_a(thai, expected_raws):
    r = ThaiOrthographyReader()
    w = r.read_word(thai)
    raws = [s.raw for s in w.syllables]
    assert raws == expected_raws, raws

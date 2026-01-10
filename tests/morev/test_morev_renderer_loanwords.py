import pytest


@pytest.mark.parametrize(
    "thai, expected",
    [
        ("โทรศัพท์", "тˣɔ̄-раˇ-сапˆ"),
        ("จุลทรรศน์", "тьун-лаˇ-тˣатˇ"),
        ("ออกซิเจน", "о̄кˆ-сиˇ-тье̄н"),
        ("โดส", "дɔ̄т"),  # dose must NOT have ^ at the end
        ("ไฮโดรลิซิส", "хай-дрɔ̄-лиˇ-ситˇ"),
        ("วัตถุนิยม", "уатˇ-тˣуˆ-ниˇ-йом"),
        ("สารนิยม", "са̄´-раˇ-ниˇ-йом"),
    ],
)
def test_morev_renderer_real_loanwords(thai: str, expected: str, morev_transcribe, nfd):
    out = morev_transcribe(thai)
    assert nfd(out) == nfd(expected)


def test_reader_raws_oxygen(thai_reader):
    w = thai_reader.read_word("ออกซิเจน")
    assert [s.raw for s in w.syllables] == ["ออก", "ซิ", "เจน"]

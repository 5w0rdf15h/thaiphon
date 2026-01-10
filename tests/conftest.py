import unicodedata

import pytest

from thaiphon.reader.thai_orthography_reader import ThaiOrthographyReader
from thaiphon.renderers.morev import MorevRenderer


@pytest.fixture
def nfd():
    """
    Normalize to NFD to compare combining marks reliably.
    Use as:
        def test_x(..., nfd):
            assert nfd(out) == nfd(expected)
    """

    def _nfd(s: str) -> str:
        return unicodedata.normalize("NFD", s)

    return _nfd


@pytest.fixture
def thai_reader() -> ThaiOrthographyReader:
    """Shared reader instance for tests."""
    return ThaiOrthographyReader()


@pytest.fixture
def morev_renderer() -> MorevRenderer:
    """Shared renderer instance for tests."""
    return MorevRenderer()


@pytest.fixture
def morev_transcribe(thai_reader: ThaiOrthographyReader, morev_renderer: MorevRenderer):
    """
    Convenience helper:
        out = morev_transcribe("ก้าวหนา")
    """

    def _transcribe(thai: str) -> str:
        word = thai_reader.read_word(thai)
        return morev_renderer.render(word)

    return _transcribe

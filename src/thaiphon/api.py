from __future__ import annotations

from thaiphon.phonology.model import PhonologicalWord
from thaiphon.registry import get_renderer


def render(word: PhonologicalWord, system: str) -> str:
    """
    Render an already computed phonological word using a given system.
    """
    return get_renderer(system).render(word)

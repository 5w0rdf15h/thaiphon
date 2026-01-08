from __future__ import annotations

from abc import ABC, abstractmethod

from thaiphon.phonology.model import PhonologicalWord


class Renderer(ABC):
    """
    Converts a PhonologicalWord into a string in some system (Morev, RTL School, Paiboon+, IPA...).
    """

    system_id: str  # e.g. "morev", "rtl_school", "paiboon"

    @abstractmethod
    def render(self, word: PhonologicalWord) -> str:
        raise NotImplementedError

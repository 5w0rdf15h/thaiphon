"""Renderer Protocol and RenderContext."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol, runtime_checkable

from thaiphon.model.syllable import Syllable
from thaiphon.model.word import PhonologicalWord

# Profile names the renderers understand. Mirrors the public
# :data:`thaiphon.api.ReadingProfile` literal; duplicated here so the
# renderer layer does not import the public API (which would create a
# cycle).
RenderingProfile = Literal[
    "everyday", "careful_educated", "learned_full", "etalon_compat"
]


@dataclass(frozen=True, slots=True)
class RenderContext:
    format: Literal["text", "html"] = "text"
    show_tone: bool = True
    show_length: bool = True
    # Reading profile — used by scheme mappings that gate surface
    # conventions on register (e.g. preserving a foreign coda under
    # ``"everyday"``/``"careful_educated"`` but collapsing under
    # ``"etalon_compat"``). Defaults to ``"everyday"``.
    profile: RenderingProfile = "everyday"


@runtime_checkable
class Renderer(Protocol):
    scheme_id: str

    def render_word(self, word: PhonologicalWord, ctx: RenderContext) -> str: ...

    def render_syllable(self, syl: Syllable) -> str: ...


__all__ = ["Renderer", "RenderContext"]

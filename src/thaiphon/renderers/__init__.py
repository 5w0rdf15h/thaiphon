"""Renderer plugins — built-ins register on import."""

from thaiphon.renderers import ipa as _ipa  # noqa: F401
from thaiphon.renderers import morev as _morev  # noqa: F401
from thaiphon.renderers import paiboon as _paiboon  # noqa: F401
from thaiphon.renderers import rtl as _rtl  # noqa: F401
from thaiphon.renderers import tlc as _tlc  # noqa: F401
from thaiphon.renderers.base import RenderContext, Renderer
from thaiphon.renderers.mapping import MappingRenderer, SchemeMapping

__all__ = [
    "MappingRenderer",
    "RenderContext",
    "Renderer",
    "SchemeMapping",
]

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Type

from thaiphon.renderers.base import Renderer


@dataclass(frozen=True)
class RendererInfo:
    system_id: str
    factory: Callable[[], Renderer]


_RENDERERS: Dict[str, RendererInfo] = {}


def register_renderer(system_id: str, factory: Callable[[], Renderer]) -> None:
    key = system_id.strip().lower()
    if key in _RENDERERS:
        raise ValueError(f"Renderer already registered: {system_id}")
    _RENDERERS[key] = RendererInfo(system_id=key, factory=factory)


def get_renderer(system_id: str) -> Renderer:
    key = system_id.strip().lower()
    try:
        return _RENDERERS[key].factory()
    except KeyError as e:
        raise KeyError(
            f"Unknown renderer: {system_id}. Known: {sorted(_RENDERERS)}"
        ) from e


def list_renderers() -> list[str]:
    return sorted(_RENDERERS.keys())

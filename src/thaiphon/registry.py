"""Generic instance-based registry for renderers and similar plugins."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Generic, Protocol, TypeVar, runtime_checkable

from thaiphon.errors import UnsupportedSchemeError

if TYPE_CHECKING:
    from thaiphon.model.syllable import Syllable
    from thaiphon.model.word import PhonologicalWord
    from thaiphon.renderers.base import RenderContext


@runtime_checkable
class Renderer(Protocol):
    """Minimum surface every registered renderer exposes."""

    scheme_id: str

    def render_word(
        self, word: PhonologicalWord, ctx: RenderContext
    ) -> str: ...

    def render_syllable(self, syl: Syllable) -> str: ...


T = TypeVar("T")


class Registry(Generic[T]):
    """Instance-based factory registry keyed by string id."""

    __slots__ = ("_factories",)

    def __init__(self) -> None:
        self._factories: dict[str, Callable[[], T]] = {}

    def register(self, key: str, factory: Callable[[], T]) -> None:
        if key in self._factories:
            raise ValueError(f"already registered: {key}")
        self._factories[key] = factory

    def get(self, key: str) -> T:
        try:
            factory = self._factories[key]
        except KeyError as exc:
            raise UnsupportedSchemeError(key) from exc
        return factory()

    def keys(self) -> tuple[str, ...]:
        return tuple(sorted(self._factories))

    def __contains__(self, key: object) -> bool:
        return isinstance(key, str) and key in self._factories


RENDERERS: Registry[Renderer] = Registry()

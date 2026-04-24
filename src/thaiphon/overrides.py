"""User-supplied lexicon overrides.

Consumers can register their own word → :class:`PhonologicalWord` lookup
callables. Registered lookups are consulted at the top of the pipeline,
before any built-in lexicon or rule-based derivation; the first layer
that returns a non-``None`` value wins.

The library ships no storage. Callers back their lookup with whatever
they prefer — an in-memory dict, a SQLite database, a JSON file, an
HTTP service. thaiphon only provides the hook.

Example::

    from thaiphon import register_lexicon
    from thaiphon.model.word import PhonologicalWord

    MY_OVERRIDES: dict[str, PhonologicalWord] = {
        "กรุงเทพ": PhonologicalWord(...),
    }

    def my_lookup(word: str) -> PhonologicalWord | None:
        return MY_OVERRIDES.get(word)

    register_lexicon(my_lookup, name="my-site")

Lookups are called with the post-normalization Thai form (NFC, with
Sara-Am expansion already applied), so the caller does not need to
replicate thaiphon's normalization pass.

A hit flows through the rest of the pipeline as-is: the returned word's
``raw`` field is populated from the input text if empty, and the
:class:`AnalysisResult` is tagged with ``source='override:<name>'`` so
downstream callers can see which layer served the answer.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from thaiphon.model.word import PhonologicalWord

LookupCallable = Callable[[str], "PhonologicalWord | None"]


@dataclass(frozen=True, slots=True)
class _Lexicon:
    name: str
    lookup: LookupCallable
    priority: int


class _Registry:
    __slots__ = ("_lexicons",)

    def __init__(self) -> None:
        self._lexicons: list[_Lexicon] = []

    def register(
        self,
        lookup: LookupCallable,
        *,
        name: str,
        priority: int = 0,
    ) -> None:
        if not name:
            raise ValueError("lexicon name must be non-empty")
        if any(lex.name == name for lex in self._lexicons):
            raise ValueError(f"lexicon {name!r} is already registered")
        self._lexicons.append(
            _Lexicon(name=name, lookup=lookup, priority=priority)
        )
        # Higher priority first; stable for equal priorities (registration order).
        self._lexicons.sort(key=lambda lex: -lex.priority)

    def unregister(self, name: str) -> bool:
        before = len(self._lexicons)
        self._lexicons = [lex for lex in self._lexicons if lex.name != name]
        return len(self._lexicons) != before

    def clear(self) -> None:
        self._lexicons.clear()

    def names(self) -> tuple[str, ...]:
        return tuple(lex.name for lex in self._lexicons)

    def lookup(self, text: str) -> tuple[PhonologicalWord, str] | None:
        for lex in self._lexicons:
            result = lex.lookup(text)
            if result is not None:
                return result, lex.name
        return None


_REGISTRY = _Registry()


def register_lexicon(
    lookup: LookupCallable,
    *,
    name: str,
    priority: int = 0,
) -> None:
    """Register a word-level override lookup.

    ``lookup(text)`` is called with the post-normalization Thai form and
    must return a :class:`~thaiphon.model.word.PhonologicalWord` for an
    override hit or ``None`` to defer to the next layer (lower priority
    overrides, then built-in lexicons, then rule-based derivation).

    ``name`` identifies the layer for debugging and unregistration; it
    must be non-empty and unique across currently-registered layers.
    ``priority`` controls resolution order — higher first; ties broken
    by registration order.

    Raises :class:`ValueError` if ``name`` is empty or already in use.
    """
    _REGISTRY.register(lookup, name=name, priority=priority)


def unregister_lexicon(name: str) -> bool:
    """Remove a previously-registered lexicon by name.

    Returns ``True`` if a lexicon was removed, ``False`` if no lexicon
    with that name was registered.
    """
    return _REGISTRY.unregister(name)


def registered_lexicons() -> tuple[str, ...]:
    """Return the names of currently-registered override lexicons,
    in resolution order (highest priority first)."""
    return _REGISTRY.names()


def _lookup(text: str) -> tuple[PhonologicalWord, str] | None:
    """Pipeline-internal lookup entry point. Returns (word, layer_name)
    for the first layer that handles ``text``, or ``None``."""
    return _REGISTRY.lookup(text)


__all__ = [
    "LookupCallable",
    "register_lexicon",
    "registered_lexicons",
    "unregister_lexicon",
]

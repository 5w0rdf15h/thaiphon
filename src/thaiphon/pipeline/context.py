"""Analysis context — mutable per-run state."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class AnalysisContext:
    orthographic_input: str = ""
    token_boundaries: tuple[int, ...] = ()
    warnings: list[str] = field(default_factory=list)


__all__ = ["AnalysisContext"]

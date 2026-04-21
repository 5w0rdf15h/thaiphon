"""Public API: transcribe, analyze, list_schemes."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, Literal

from thaiphon.errors import UnsupportedSchemeError
from thaiphon.model.candidate import AnalysisResult
from thaiphon.registry import RENDERERS

if TYPE_CHECKING:
    from thaiphon.pipeline.runner import PipelineRunner

ReadingProfile = Literal[
    "everyday", "careful_educated", "learned_full", "etalon_compat"
]

_runner: PipelineRunner | None = None


def _get_runner() -> PipelineRunner:
    global _runner
    if _runner is None:
        from thaiphon.pipeline.runner import PipelineRunner

        _runner = PipelineRunner()
    return _runner


def analyze(
    text: str,
    *,
    is_final_in_compound: bool = True,
    profile: ReadingProfile = "everyday",
) -> AnalysisResult:
    return _get_runner().analyze(
        text, is_final_in_compound=is_final_in_compound, profile=profile
    )


def analyze_word(
    text: str, *, profile: ReadingProfile = "everyday"
) -> AnalysisResult:
    return _get_runner().analyze(text, profile=profile)


def list_schemes() -> tuple[str, ...]:
    # Ensure built-in renderers are registered before reporting.
    from thaiphon import renderers  # noqa: F401

    return RENDERERS.keys()


def transcribe(
    text: str,
    scheme: str = "tlc",
    *,
    format: Literal["text", "html"] = "text",
    profile: ReadingProfile = "everyday",
    _is_sentence_final: bool = True,
) -> str:
    from thaiphon import renderers  # noqa: F401
    from thaiphon.renderers.base import RenderContext

    if scheme not in RENDERERS:
        raise UnsupportedSchemeError(scheme)
    renderer = RENDERERS.get(scheme)
    ctx = RenderContext(format=format, profile=profile)
    result = analyze(
        text, is_final_in_compound=_is_sentence_final, profile=profile
    )
    return renderer.render_word(result.best, ctx)


def transcribe_word(
    text: str,
    scheme: str = "tlc",
    *,
    format: Literal["text", "html"] = "text",
    profile: ReadingProfile = "everyday",
    _is_sentence_final: bool = True,
) -> str:
    return transcribe(
        text,
        scheme=scheme,
        format=format,
        profile=profile,
        _is_sentence_final=_is_sentence_final,
    )


def transcribe_sentence(
    text: str,
    scheme: str = "tlc",
    *,
    format: Literal["text", "html"] = "text",
    profile: ReadingProfile = "everyday",
    segmenter: Callable[[str], Sequence[str]] | None = None,
) -> str:
    """Segment ``text`` into words, transcribe each, join with spaces.

    Words appearing mid-compound have their M-602 length overrides
    reverted (see :mod:`thaiphon.lexicons.length_overrides`). Words
    that are the last token pass through with overrides applied.
    """
    from thaiphon.segmentation import longest as _longest

    seg = segmenter if segmenter is not None else _longest.segment
    words = tuple(seg(text))
    if not words:
        return ""
    out: list[str] = []
    last = len(words) - 1
    for i, w in enumerate(words):
        if not w or w.isspace():
            continue
        is_last = i == last
        out.append(
            transcribe_word(
                w,
                scheme=scheme,
                format=format,
                profile=profile,
                _is_sentence_final=is_last,
            )
        )
    return " ".join(out)


__all__ = [
    "ReadingProfile",
    "analyze",
    "analyze_word",
    "list_schemes",
    "transcribe",
    "transcribe_sentence",
    "transcribe_word",
]

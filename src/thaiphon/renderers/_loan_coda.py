"""Shared lexicon-driven coda preservation for Latin-alphabet schemes.

The Paiboon, Paiboon+, and RTL schemes all treat foreign-only coda IPAs
the same way by default: ``/f/`` collapses to ``p``, ``/s/`` to ``t``,
``/l/`` to ``n`` — matching native Thai phonotactics. For modern loans
where a lexicon entry asks us to keep the foreign surface (e.g. ลิฟต์
surfacing as ``líf`` rather than ``líp``), the renderer needs to swap
the collapsed letter back to the preserved one whenever three things
line up: the caller's register opts into preservation, the word is in
the loanword lexicon with an entry for that register, and the syllable
being rendered actually carries the orthographic source letter.

This module factors the logic out of the three Latin renderers so they
can declare a small preservation-config table and hand it to
:func:`make_lexicon_coda_override`. The returned callable is dropped
straight into :attr:`SchemeMapping.word_coda_override`.

The IPA and TLC renderers keep their own implementations. IPA uses a
different default-coda letter (``p̚`` — the unreleased stop — instead
of ``p``), and TLC adds an out-of-lexicon foreignness-score heuristic
for ฟ-coda words. Both are already well-tested; duplication there is
cheaper than trying to parameterise the helper to cover them too.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping

from thaiphon.lexicons.loanword import LOANWORDS, get_preserved_coda
from thaiphon.model.syllable import Syllable

PreservationConfig = Mapping[str, tuple[str, frozenset[str], str]]
"""Mapping from preservation tag (``"f"`` / ``"s"`` / ``"l"``) to a
``(expected_default_coda, source_chars, surface)`` triple.

* ``expected_default_coda`` is the scheme's native-collapsed coda
  letter — the override only fires when the renderer's default coda
  string matches this value, which guards against swapping a coda
  that was produced by a different phoneme.
* ``source_chars`` is the set of orthographic source letters that
  mark the syllable as carrying the foreign coda. Native letters with
  the same collapsed coda are deliberately excluded so the override
  never misfires on them.
* ``surface`` is the replacement string emitted on preservation.
"""


def _syllable_carries(
    syl: Syllable, word_raw: str, source_chars: frozenset[str]
) -> bool:
    """Return True iff the syllable's orthographic slice carries one of
    the preservation-source letters.

    When the syllabifier has populated ``syl.raw`` we consult that
    directly — it is the precise per-syllable orthographic slice. When
    ``syl.raw`` is empty (some lexicon-stored words) we fall back to
    the whole word, which is safe for every current preservation
    entry.
    """
    if syl.raw:
        return any(ch in syl.raw for ch in source_chars)
    return any(ch in word_raw for ch in source_chars)


def make_lexicon_coda_override(
    config: PreservationConfig,
) -> Callable[[str, Syllable, str, str], str | None]:
    """Build a ``word_coda_override`` callable for a Latin scheme.

    The returned callable implements the standard lexicon-only
    resolution order:

    1. ``etalon_compat`` never preserves — dictionary-style citation
       forms always render native phonotactics.
    2. Words outside :data:`LOANWORDS` are not preserved. There is no
       out-of-lexicon heuristic fallback — the Latin schemes only emit
       a preserved coda on the authority of a curated lexicon entry.
    3. Inside the lexicon, the entry's preservation tag (under the
       caller's profile) selects a row of ``config``. If the default
       coda the renderer was about to emit matches the row's
       ``expected_default_coda`` and the syllable carries one of the
       row's ``source_chars``, the row's ``surface`` string is
       returned. Otherwise the renderer keeps its default output.
    """

    def override(
        word_raw: str, syl: Syllable, default: str, profile: str
    ) -> str | None:
        if profile == "etalon_compat":
            return None
        if word_raw not in LOANWORDS:
            return None
        tag = get_preserved_coda(word_raw, profile)
        if tag is None:
            return None
        cfg = config.get(tag)
        if cfg is None:
            return None
        expected_default, source_chars, surface = cfg
        if default == expected_default and _syllable_carries(
            syl, word_raw, source_chars
        ):
            return surface
        return None

    return override


__all__ = ["PreservationConfig", "make_lexicon_coda_override"]

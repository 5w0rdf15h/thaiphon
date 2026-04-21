"""Modern loan-word override: preserve /f/ in final position.

Native Thai coda neutralisation (M-301) collapses ``ฟ`` to /p̚/. Modern
foreign loans frequently retain the foreign /f/ realisation. This
module exposes a view over the canonical loanword lexicon: exactly
those entries whose profile has ``coda_policy="preserve"`` belong to
the modern-loan /f/-preservation island.

The TLC renderer overrides the derived coda for any syllable whose raw
ends with ``ฟ`` (optionally followed by ``ฟ์``) when the word is in
this set. The authoritative entry table lives in :mod:`loanword`; this
module is kept for backward compatibility.
"""

from __future__ import annotations

from thaiphon.lexicons.loanword import words_by_coda_policy

# Derived view: the legacy flat set. Computed once at import time.
LOAN_FINAL_F_WORDS: frozenset[str] = words_by_coda_policy("preserve")


def preserve_final_f(word: str) -> bool:
    """Return True if the word is a modern loan that preserves final /f/."""
    return word in LOAN_FINAL_F_WORDS


__all__ = ["LOAN_FINAL_F_WORDS", "preserve_final_f"]

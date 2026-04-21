"""Double-function consonant strategy tests.

A double-function (DF) consonant closes one syllable and simultaneously opens
the next. The strategy emits a candidate only when a bare consonant token sits
between two vowel-bearing tokens.
"""

from __future__ import annotations

import pytest

from thaiphon.syllabification.strategies import DFStrategy


@pytest.fixture
def strategy() -> DFStrategy:
    return DFStrategy()


def test_df_emits_when_pivot_sits_between_vowels(
    strategy: DFStrategy,
) -> None:
    # ['ผ','ล','ไม้'] — ล sits between a bare consonant and a vowel-bearing token.
    # DF requires prev vowel-bearing; here 'ผ' has no vowel so no DF.
    tokens = ("ผ", "ล", "ไม้")
    cands = list(strategy.generate(tokens))
    assert cands == []


def test_df_emits_across_vowel_bearing_neighbors(
    strategy: DFStrategy,
) -> None:
    # ['สา','ส','นา'] — ส sits between two vowel-bearing tokens → DF candidate.
    tokens = ("สา", "ส", "นา")
    cands = list(strategy.generate(tokens))
    assert cands
    # The DF segmentation duplicates the pivot: [สาส, ส, นา].
    assert cands[0].segments == ("สาส", "ส", "นา")


def test_df_excludes_word_initial_pivot(
    strategy: DFStrategy,
) -> None:
    tokens = ("ก", "า", "ม")  # ก is word-initial
    cands = list(strategy.generate(tokens))
    # No DF produced because the bare consonant, if any, isn't between
    # two vowel-bearing tokens.
    assert cands == []


def test_df_excludes_word_final_pivot(strategy: DFStrategy) -> None:
    # ['สา','ส'] — pivot is word-final.
    tokens = ("สา", "ส")
    cands = list(strategy.generate(tokens))
    assert cands == []


def test_df_excludes_nga(strategy: DFStrategy) -> None:
    # ง is usually not a DF candidate.
    tokens = ("สา", "ง", "นา")
    cands = list(strategy.generate(tokens))
    assert cands == []


def test_df_score_is_moderate(strategy: DFStrategy) -> None:
    tokens = ("สา", "ส", "นา")
    cands = list(strategy.generate(tokens))
    if cands:
        assert 0.6 <= cands[0].score <= 0.8


def test_df_empty_input(strategy: DFStrategy) -> None:
    assert list(strategy.generate(())) == []


def test_df_two_token_input(strategy: DFStrategy) -> None:
    assert list(strategy.generate(("มา", "น"))) == []

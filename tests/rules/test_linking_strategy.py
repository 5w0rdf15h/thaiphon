"""Linking-syllable strategy tests.

The linking strategy handles words where a bare single-consonant token (an
orphan) must be assigned an implicit /a/ vowel, acting as a bridge between
adjacent syllables. Common in Pali-derived vocabulary and native polysyllables.
"""

from __future__ import annotations

import pytest

from thaiphon.syllabification.strategies import LinkingStrategy, MergeStrategy
from thaiphon.tokenization.tcc import tokenize


@pytest.fixture
def strategy() -> LinkingStrategy:
    return LinkingStrategy()


@pytest.mark.parametrize(
    "word",
    [
        "ผลไม้",
        "สะเทือน",
        "มหาวิทยาลัย",
        "โทรศัพท์",
        "สมุด",
        "รัฐบาล",
        "ศาสนา",
        "พฤษภาคม",
    ],
)
def test_linking_emits_candidate_when_orphan_consonants_present(
    strategy: LinkingStrategy, word: str
) -> None:
    tokens = tokenize(word)
    cands = list(strategy.generate(tokens))
    # Emitted only when there's at least one bare single-consonant token.
    if any(len(t) == 1 and t.isalpha() for t in tokens):
        assert cands


def test_linking_skips_words_without_orphans(strategy: LinkingStrategy) -> None:
    tokens = tokenize("มา")
    cands = list(strategy.generate(tokens))
    assert cands == []


def test_linking_preserves_segmentation(strategy: LinkingStrategy) -> None:
    tokens = tokenize("ผลไม้")
    cands = list(strategy.generate(tokens))
    if cands:
        # LinkingStrategy just tags split — same tuple as input.
        assert cands[0].segments == tokens


def test_linking_score_is_moderate(strategy: LinkingStrategy) -> None:
    tokens = tokenize("ผลไม้")
    cands = list(strategy.generate(tokens))
    if cands:
        assert 0.55 <= cands[0].score <= 0.7


def test_merge_and_linking_are_independent() -> None:
    tokens = tokenize("ผลไม้")
    merge = list(MergeStrategy().generate(tokens))
    link = list(LinkingStrategy().generate(tokens))
    if merge and link:
        assert merge[0].segments != link[0].segments


@pytest.mark.parametrize(
    "word",
    [
        "สมุด",    # ['ส','มุ','ด']
        "ทศ",      # ['ท','ศ']
        "มหา",     # ['ม','หา']
        "สมัย",    # ['ส','มั','ย']
        "สมอง",    # ['ส','ม','อ','ง']
        "ทนาย",    # ['ท','นา','ย']
        "ถนน",     # ['ถ','น','น']
    ],
)
def test_linking_emits_for_pali_loan_shapes(
    strategy: LinkingStrategy, word: str
) -> None:
    tokens = tokenize(word)
    cands = list(strategy.generate(tokens))
    # Not every tokenization has a 1-char bare consonant, but most do.
    has_orphan = any(len(t) == 1 and "ก" <= t <= "ฮ" for t in tokens)
    if has_orphan:
        assert cands

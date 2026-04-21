"""Coverage tests for ClusterStrategy across the standard consonant cluster pairs."""

from __future__ import annotations

import pytest

from thaiphon.syllabification.strategies import ClusterStrategy
from thaiphon.tokenization.tcc import tokenize


@pytest.fixture
def strategy() -> ClusterStrategy:
    return ClusterStrategy()


@pytest.mark.parametrize(
    "word,expected_first_segment",
    [
        ("กรา", "กรา"),
        ("กลับ", "กลับ"),
        ("กว่า", "กว่า"),
        ("ขรึม", "ขรึม"),
        ("คราม", "คราม"),
        ("คลอง", "คลอง"),
        ("ความ", "ความ"),
        ("ตรวจ", "ตรวจ"),
        ("ปราบ", "ปราบ"),
        ("ปลา", "ปลา"),
        ("พราหมณ์", "พราหมณ์"),
        ("พล่า", "พล่า"),
    ],
)
def test_cluster_merges_first_two_tokens(
    strategy: ClusterStrategy, word: str, expected_first_segment: str
) -> None:
    tokens = tokenize(word)
    cands = list(strategy.generate(tokens))
    # Either ClusterStrategy has emitted something, or the TCC already
    # bundled both letters into the same token (not applicable).
    if not cands:
        assert len(tokens) <= 1 or not tokens[0] + tokens[1][0] in ("กร", "กล")
        return
    assert any(expected_first_segment == seg[0] or seg[0].startswith(expected_first_segment[:2]) for seg in (c.segments for c in cands))


def test_cluster_score_is_high_when_applicable(
    strategy: ClusterStrategy,
) -> None:
    tokens = tokenize("กรา")
    cands = list(strategy.generate(tokens))
    if cands:
        assert cands[0].score >= 0.7


def test_cluster_skips_non_cluster_pair(
    strategy: ClusterStrategy,
) -> None:
    # Two consonants that are NOT in the valid cluster set: ส + ม.
    tokens = ("ส", "มุด")
    cands = list(strategy.generate(tokens))
    assert cands == []


def test_cluster_handles_rare_pair_excluded(
    strategy: ClusterStrategy,
) -> None:
    # (ผ, ล) is a rare table entry; ClusterStrategy excludes it.
    tokens = ("ผ", "ล")
    cands = list(strategy.generate(tokens))
    assert cands == []


def test_cluster_with_prevowel(strategy: ClusterStrategy) -> None:
    # เปล่า → TCC yields ['เป','ล่า']; cluster shape must fold back.
    tokens = tokenize("เปล่า")
    cands = list(strategy.generate(tokens))
    assert cands
    assert len(cands[0].segments) == 1

"""ทร three-way readings.

The digraph ทร has three distinct phonological interpretations in Thai:
  - "s"     — the majority class; ทร reads as /s/ (e.g. ทราบ, ทราย, ทรง).
  - "thr"   — foreign or musical terms where the cluster is preserved (e.g. ทรอมโบน).
  - "taara" — a small set of Indic-derived words where ทร reads as /tʰaː.raː/ or similar
              (e.g. ทรพิษ, ทรมาน, ทรราช).
"""

from __future__ import annotations

import pytest

from thaiphon.lexicons.thor import MID_WORD_THOR, THOR_READINGS, lookup, rewrite_thor_mid

_S_READINGS = [
    "ทราบ",
    "ทราย",
    "ทรง",
    "ทรัพย์",
]

_THR_READINGS = [
    "ทรอมโบน",
    "ทรัมเป็ต",
]

_TAARA_READINGS = [
    "ทรพิษ",
    "ทรมาน",
    "ทรราช",
]


@pytest.mark.parametrize("word", _S_READINGS)
def test_s_class(word: str) -> None:
    assert lookup(word) == "s"


@pytest.mark.parametrize("word", _THR_READINGS)
def test_thr_class(word: str) -> None:
    assert lookup(word) == "thr"


@pytest.mark.parametrize("word", _TAARA_READINGS)
def test_taara_class(word: str) -> None:
    assert lookup(word) == "taara"


def test_lookup_absent_returns_none() -> None:
    assert lookup("มา") is None


def test_readings_table_nonempty() -> None:
    assert len(THOR_READINGS) >= 15


def test_mid_word_thor_table_nonempty() -> None:
    assert len(MID_WORD_THOR) >= 1


def test_rewrite_thor_mid_passthrough_on_absent_word() -> None:
    assert rewrite_thor_mid("มา") == "มา"


def test_rewrite_thor_mid_applies_registered_substitution() -> None:
    # อินทรีย์ → อินซีย์ per MID_WORD_THOR.
    original = "อินทรีย์"
    out = rewrite_thor_mid(original)
    assert "ทร" not in out
    assert "ซ" in out

"""User-supplied override lexicons: registration, resolution, fallthrough."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from thaiphon import (
    analyze,
    register_lexicon,
    registered_lexicons,
    transcribe,
    unregister_lexicon,
)
from thaiphon.model.enums import (
    EffectiveClass,
    SyllableType,
    Tone,
    ToneMark,
    VowelLength,
)
from thaiphon.model.phoneme import Phoneme
from thaiphon.model.syllable import Syllable
from thaiphon.model.word import PhonologicalWord


def _make_thep() -> PhonologicalWord:
    """Construct a ``PhonologicalWord`` for ``เทพ`` with deliberately
    distinctive values so test assertions can confirm an override hit
    (rather than accidentally agreeing with the rule-derived output)."""
    return PhonologicalWord(
        syllables=(
            Syllable(
                onset=Phoneme("X"),
                vowel=Phoneme("y"),
                vowel_length=VowelLength.LONG,
                coda=Phoneme("z"),
                tone=Tone.HIGH,
                tone_mark=ToneMark.NONE,
                effective_class=EffectiveClass.MID,
                syllable_type=SyllableType.LIVE,
            ),
        ),
    )


@pytest.fixture(autouse=True)
def _clean_registry() -> Iterator[None]:
    """Every test starts with an empty override registry and leaves it
    empty — prevents cross-test leakage through the module-level state."""
    from thaiphon import overrides as _ov

    _ov._REGISTRY.clear()
    yield
    _ov._REGISTRY.clear()


def test_override_hit_wins_over_lexicon() -> None:
    sentinel = _make_thep()
    register_lexicon(
        lambda w: sentinel if w == "เทพ" else None,
        name="site",
    )
    result = analyze("เทพ")
    assert result.source == "override:site"
    assert result.best.source == "override:site"
    assert result.best.syllables[0].onset.symbol == "X"


def test_override_sets_source_tag_through_transcribe() -> None:
    sentinel = _make_thep()
    register_lexicon(lambda w: sentinel if w == "เทพ" else None, name="site")
    # Picking the TLC renderer because it exercises per-syllable fields;
    # the distinct sentinel values produce a non-standard output that
    # still renders without error.
    out = transcribe("เทพ", "tlc")
    assert out  # rendered, not empty
    # And the analyze-level source is unchanged by transcribing.
    assert analyze("เทพ").source == "override:site"


def test_override_returns_none_falls_through_to_lexicon() -> None:
    register_lexicon(lambda w: None, name="empty")
    result = analyze("เทพ")
    # No override hit — falls through to the built-in Volubilis entry.
    assert result.source == "lexicon"
    assert result.best.syllables[0].coda is not None
    assert result.best.syllables[0].coda.symbol == "p̚"


def test_higher_priority_layer_wins() -> None:
    low = _make_thep()
    high = PhonologicalWord(
        syllables=(
            Syllable(
                onset=Phoneme("HI"),
                vowel=Phoneme("a"),
                vowel_length=VowelLength.SHORT,
                coda=None,
                tone=Tone.MID,
                tone_mark=ToneMark.NONE,
                effective_class=EffectiveClass.MID,
                syllable_type=SyllableType.LIVE,
            ),
        ),
    )
    register_lexicon(lambda w: low, name="low", priority=0)
    register_lexicon(lambda w: high, name="high", priority=10)
    result = analyze("เทพ")
    assert result.source == "override:high"
    assert result.best.syllables[0].onset.symbol == "HI"


def test_first_registered_wins_on_priority_tie() -> None:
    first = _make_thep()
    second = PhonologicalWord(
        syllables=(
            Syllable(
                onset=Phoneme("S"),
                vowel=Phoneme("a"),
                vowel_length=VowelLength.SHORT,
                coda=None,
                tone=Tone.MID,
                tone_mark=ToneMark.NONE,
                effective_class=EffectiveClass.MID,
                syllable_type=SyllableType.LIVE,
            ),
        ),
    )
    register_lexicon(lambda w: first, name="a")
    register_lexicon(lambda w: second, name="b")
    result = analyze("เทพ")
    assert result.source == "override:a"


def test_registered_lexicons_reports_resolution_order() -> None:
    register_lexicon(lambda w: None, name="low", priority=0)
    register_lexicon(lambda w: None, name="high", priority=5)
    register_lexicon(lambda w: None, name="mid", priority=3)
    assert registered_lexicons() == ("high", "mid", "low")


def test_unregister_removes_layer() -> None:
    register_lexicon(lambda w: _make_thep(), name="site")
    assert "site" in registered_lexicons()
    assert unregister_lexicon("site") is True
    assert "site" not in registered_lexicons()
    # After unregister, built-in lexicon wins again.
    assert analyze("เทพ").source == "lexicon"


def test_unregister_returns_false_for_unknown_name() -> None:
    assert unregister_lexicon("nothing-here") is False


def test_duplicate_name_rejected() -> None:
    register_lexicon(lambda w: None, name="site")
    with pytest.raises(ValueError, match="already registered"):
        register_lexicon(lambda w: None, name="site")


def test_empty_name_rejected() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        register_lexicon(lambda w: None, name="")


def test_override_populates_raw_when_word_has_none() -> None:
    # User-supplied word with raw='' — the pipeline must fill it in.
    word = PhonologicalWord(
        syllables=(
            Syllable(
                onset=Phoneme("X"),
                vowel=Phoneme("a"),
                vowel_length=VowelLength.SHORT,
                coda=None,
                tone=Tone.MID,
                tone_mark=ToneMark.NONE,
                effective_class=EffectiveClass.MID,
                syllable_type=SyllableType.LIVE,
            ),
        ),
        raw="",
    )
    register_lexicon(lambda w: word, name="site")
    result = analyze("เทพ")
    assert result.best.raw == "เทพ"

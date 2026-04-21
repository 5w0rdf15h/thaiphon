"""Royal vocabulary lexicon (M-940) — curated subset.

A hand-curated seed of high-visibility royal-register forms whose reading
diverges from productive orthography. Each entry is a pre-built
``PhonologicalWord`` so rendering is deterministic across schemes.

The set is deliberately small — this is a seed layer; further entries
are expected to be added over time.
"""

from __future__ import annotations

import functools
from collections.abc import Mapping
from types import MappingProxyType

from thaiphon.model.enums import EffectiveClass, SyllableType, Tone, ToneMark, VowelLength
from thaiphon.model.phoneme import Phoneme
from thaiphon.model.syllable import Syllable
from thaiphon.model.word import PhonologicalWord


def _s(
    onset: str,
    vowel: str,
    length: VowelLength,
    coda: str | None,
    tone: Tone,
    *,
    cls: EffectiveClass = EffectiveClass.MID,
    stype: SyllableType = SyllableType.LIVE,
    raw: str = "",
) -> Syllable:
    return Syllable(
        onset=Phoneme(onset) if onset else None,
        vowel=Phoneme(vowel),
        vowel_length=length,
        coda=Phoneme(coda) if coda else None,
        tone=tone,
        tone_mark=ToneMark.NONE,
        effective_class=cls,
        syllable_type=stype,
        raw=raw,
    )


def _word(text: str, *syls: Syllable) -> PhonologicalWord:
    return PhonologicalWord(
        syllables=syls,
        confidence=1.0,
        source="lexicon",
        raw=text,
    )


# Short aliases for the tone/length enums, just inside the factory body.
_SH = VowelLength.SHORT
_LG = VowelLength.LONG
_LV = SyllableType.LIVE
_DD = SyllableType.DEAD


def _build() -> Mapping[str, PhonologicalWord]:
    HIGH, LOW, MID, FALLING, RISING = (
        Tone.HIGH, Tone.LOW, Tone.MID, Tone.FALLING, Tone.RISING,
    )
    HC, MC, LC = EffectiveClass.HIGH, EffectiveClass.MID, EffectiveClass.LOW

    data: dict[str, PhonologicalWord] = {}

    # พระราชา — /pʰrá-râː-tɕʰaː/
    data["\u0e1e\u0e23\u0e30\u0e23\u0e32\u0e0a\u0e32"] = _word(
        "\u0e1e\u0e23\u0e30\u0e23\u0e32\u0e0a\u0e32",
        _s("pʰ", "a", _SH, None, HIGH, cls=LC, stype=_DD),
        _s("r", "a", _LG, None, FALLING, cls=LC, stype=_LV),
        _s("tɕʰ", "a", _LG, None, MID, cls=LC, stype=_LV),
    )

    # พระราชินี — /pʰrá-râː-tɕʰí-niː/
    data["\u0e1e\u0e23\u0e30\u0e23\u0e32\u0e0a\u0e34\u0e19\u0e35"] = _word(
        "\u0e1e\u0e23\u0e30\u0e23\u0e32\u0e0a\u0e34\u0e19\u0e35",
        _s("pʰ", "a", _SH, None, HIGH, cls=LC, stype=_DD),
        _s("r", "a", _LG, None, FALLING, cls=LC, stype=_LV),
        _s("tɕʰ", "i", _SH, None, HIGH, cls=LC, stype=_DD),
        _s("n", "i", _LG, None, MID, cls=LC, stype=_LV),
    )

    # พระมหากษัตริย์ — /pʰrá-má-hǎː-kà-sàt/
    k = "\u0e1e\u0e23\u0e30\u0e21\u0e2b\u0e32\u0e01\u0e29\u0e31\u0e15\u0e23\u0e34\u0e22\u0e4c"
    data[k] = _word(
        k,
        _s("pʰ", "a", _SH, None, HIGH, cls=LC, stype=_DD),
        _s("m", "a", _SH, None, HIGH, cls=LC, stype=_DD),
        _s("h", "a", _LG, None, RISING, cls=HC, stype=_LV),
        _s("k", "a", _SH, None, LOW, cls=MC, stype=_DD),
        _s("s", "a", _SH, "t̚", LOW, cls=HC, stype=_DD),
    )

    # พระเจ้าอยู่หัว — /pʰrá-tɕâːw-jùː-hǔa/
    k = "\u0e1e\u0e23\u0e30\u0e40\u0e08\u0e49\u0e32\u0e2d\u0e22\u0e39\u0e48\u0e2b\u0e31\u0e27"
    data[k] = _word(
        k,
        _s("pʰ", "a", _SH, None, HIGH, cls=LC, stype=_DD),
        _s("tɕ", "a", _LG, "w", FALLING, cls=MC, stype=_LV),
        _s("j", "u", _LG, None, LOW, cls=MC, stype=_LV),
        _s("h", "ua", _SH, None, RISING, cls=HC, stype=_LV),
    )

    # พระบาทสมเด็จพระเจ้าอยู่หัว — long royal style; split segments.
    # /pʰrá-bàːt-sǒm-dèt-pʰrá-tɕâːw-jùː-hǔa/
    data[
        "\u0e1e\u0e23\u0e30\u0e1a\u0e32\u0e17"
        "\u0e2a\u0e21\u0e40\u0e14\u0e47\u0e08"
        "\u0e1e\u0e23\u0e30\u0e40\u0e08\u0e49\u0e32"
        "\u0e2d\u0e22\u0e39\u0e48\u0e2b\u0e31\u0e27"
    ] = _word(
        "\u0e1e\u0e23\u0e30\u0e1a\u0e32\u0e17"
        "\u0e2a\u0e21\u0e40\u0e14\u0e47\u0e08"
        "\u0e1e\u0e23\u0e30\u0e40\u0e08\u0e49\u0e32"
        "\u0e2d\u0e22\u0e39\u0e48\u0e2b\u0e31\u0e27",
        _s("pʰ", "a", _SH, None, HIGH, cls=LC, stype=_DD),
        _s("b", "a", _LG, "t̚", LOW, cls=MC, stype=_DD),
        _s("s", "o", _SH, "m", RISING, cls=HC, stype=_LV),
        _s("d", "e", _SH, "t̚", LOW, cls=MC, stype=_DD),
        _s("pʰ", "a", _SH, None, HIGH, cls=LC, stype=_DD),
        _s("tɕ", "a", _LG, "w", FALLING, cls=MC, stype=_LV),
        _s("j", "u", _LG, None, LOW, cls=MC, stype=_LV),
        _s("h", "ua", _SH, None, RISING, cls=HC, stype=_LV),
    )

    # พระบรมราชโองการ — /pʰrá-bɔː-rom-mâː-tɕʰá-oː-ŋ-kaːn/
    # Abbreviated; surface form of common royal phrase. We ship a minimum
    # viable reading to avoid gaps in royal-register sentences.
    k = "\u0e1e\u0e23\u0e30\u0e1a\u0e23\u0e21\u0e23\u0e32\u0e0a\u0e42\u0e2d\u0e07\u0e01\u0e32\u0e23"
    data[k] = _word(
        k,
        _s("pʰ", "a", _SH, None, HIGH, cls=LC, stype=_DD),
        _s("b", "ɔ", _LG, None, MID, cls=MC, stype=_LV),
        _s("r", "o", _SH, "m", MID, cls=LC, stype=_LV),
        _s("m", "a", _LG, None, FALLING, cls=LC, stype=_LV),
        _s("tɕʰ", "a", _SH, None, HIGH, cls=LC, stype=_DD),
        _s("o", "o", _LG, "ŋ", MID, cls=MC, stype=_LV),
        _s("k", "a", _LG, "n", MID, cls=MC, stype=_LV),
    )

    # ทรงพระกรุณา — /soŋ-pʰrá-kà-rú-naː/ (introductory royal verb)
    data["\u0e17\u0e23\u0e07\u0e1e\u0e23\u0e30\u0e01\u0e23\u0e38\u0e13\u0e32"] = _word(
        "\u0e17\u0e23\u0e07\u0e1e\u0e23\u0e30\u0e01\u0e23\u0e38\u0e13\u0e32",
        _s("s", "o", _SH, "ŋ", MID, cls=LC, stype=_LV),
        _s("pʰ", "a", _SH, None, HIGH, cls=LC, stype=_DD),
        _s("k", "a", _SH, None, LOW, cls=MC, stype=_DD),
        _s("r", "u", _SH, None, HIGH, cls=LC, stype=_DD),
        _s("n", "a", _LG, None, MID, cls=LC, stype=_LV),
    )

    # เสด็จ — /sa-dèt/
    data["\u0e40\u0e2a\u0e14\u0e47\u0e08"] = _word(
        "\u0e40\u0e2a\u0e14\u0e47\u0e08",
        _s("s", "a", _SH, None, LOW, cls=HC, stype=_DD),
        _s("d", "e", _SH, "t̚", LOW, cls=MC, stype=_DD),
    )

    # เสด็จพระราชดำเนิน — compact royal verb chain; abbreviated reading.
    # /sa-dèt-pʰrá-râːt-tɕʰá-dam-nɤːn/
    data[
        "\u0e40\u0e2a\u0e14\u0e47\u0e08\u0e1e\u0e23\u0e30"
        "\u0e23\u0e32\u0e0a\u0e14\u0e33\u0e40\u0e19\u0e34\u0e19"
    ] = _word(
        "\u0e40\u0e2a\u0e14\u0e47\u0e08\u0e1e\u0e23\u0e30"
        "\u0e23\u0e32\u0e0a\u0e14\u0e33\u0e40\u0e19\u0e34\u0e19",
        _s("s", "a", _SH, None, LOW, cls=HC, stype=_DD),
        _s("d", "e", _SH, "t̚", LOW, cls=MC, stype=_DD),
        _s("pʰ", "a", _SH, None, HIGH, cls=LC, stype=_DD),
        _s("r", "a", _LG, "t̚", FALLING, cls=LC, stype=_DD),
        _s("tɕʰ", "a", _SH, None, HIGH, cls=LC, stype=_DD),
        _s("d", "a", _SH, "m", MID, cls=MC, stype=_LV),
        _s("n", "ɤ", _LG, "n", MID, cls=LC, stype=_LV),
    )

    # พระบรมฉายาลักษณ์ — /pʰrá-bɔː-rom-tɕʰǎː-jaː-lák/
    data[
        "\u0e1e\u0e23\u0e30\u0e1a\u0e23\u0e21"
        "\u0e09\u0e32\u0e22\u0e32\u0e25\u0e31\u0e01\u0e29\u0e13\u0e4c"
    ] = _word(
        "\u0e1e\u0e23\u0e30\u0e1a\u0e23\u0e21"
        "\u0e09\u0e32\u0e22\u0e32\u0e25\u0e31\u0e01\u0e29\u0e13\u0e4c",
        _s("pʰ", "a", _SH, None, HIGH, cls=LC, stype=_DD),
        _s("b", "ɔ", _LG, None, MID, cls=MC, stype=_LV),
        _s("r", "o", _SH, "m", MID, cls=LC, stype=_LV),
        _s("tɕʰ", "a", _LG, None, RISING, cls=HC, stype=_LV),
        _s("j", "a", _LG, None, MID, cls=LC, stype=_LV),
        _s("l", "a", _SH, "k̚", HIGH, cls=LC, stype=_DD),
    )

    # พระราชดำรัส — /pʰrá-râːt-tɕʰá-dam-ràt/
    data[
        "\u0e1e\u0e23\u0e30\u0e23\u0e32\u0e0a\u0e14\u0e33\u0e23\u0e31\u0e2a"
    ] = _word(
        "\u0e1e\u0e23\u0e30\u0e23\u0e32\u0e0a\u0e14\u0e33\u0e23\u0e31\u0e2a",
        _s("pʰ", "a", _SH, None, HIGH, cls=LC, stype=_DD),
        _s("r", "a", _LG, "t̚", FALLING, cls=LC, stype=_DD),
        _s("tɕʰ", "a", _SH, None, HIGH, cls=LC, stype=_DD),
        _s("d", "a", _SH, "m", MID, cls=MC, stype=_LV),
        _s("r", "a", _SH, "t̚", HIGH, cls=LC, stype=_DD),
    )

    # ถวาย — /tʰa-wǎːj/ (royal "to offer")
    data["\u0e16\u0e27\u0e32\u0e22"] = _word(
        "\u0e16\u0e27\u0e32\u0e22",
        _s("tʰ", "a", _SH, None, LOW, cls=HC, stype=_DD),
        _s("w", "a", _LG, "j", RISING, cls=HC, stype=_LV),
    )

    # สวรรคต — /sa-wǎn-ká-kót/ approximate reading.
    data["\u0e2a\u0e27\u0e23\u0e23\u0e04\u0e15"] = _word(
        "\u0e2a\u0e27\u0e23\u0e23\u0e04\u0e15",
        _s("s", "a", _SH, None, LOW, cls=HC, stype=_DD),
        _s("w", "a", _SH, "n", RISING, cls=HC, stype=_LV),
        _s("k", "a", _SH, None, LOW, cls=MC, stype=_DD),
        _s("k", "o", _SH, "t̚", LOW, cls=MC, stype=_DD),
    )

    # พระที่นั่ง — /pʰrá-tʰîː-nâŋ/
    data["\u0e1e\u0e23\u0e30\u0e17\u0e35\u0e48\u0e19\u0e31\u0e48\u0e07"] = _word(
        "\u0e1e\u0e23\u0e30\u0e17\u0e35\u0e48\u0e19\u0e31\u0e48\u0e07",
        _s("pʰ", "a", _SH, None, HIGH, cls=LC, stype=_DD),
        _s("tʰ", "i", _LG, None, FALLING, cls=LC, stype=_LV),
        _s("n", "a", _SH, "ŋ", FALLING, cls=LC, stype=_LV),
    )

    # พระราชทาน — /pʰrá-râːt-tɕʰá-tʰaːn/
    data["\u0e1e\u0e23\u0e30\u0e23\u0e32\u0e0a\u0e17\u0e32\u0e19"] = _word(
        "\u0e1e\u0e23\u0e30\u0e23\u0e32\u0e0a\u0e17\u0e32\u0e19",
        _s("pʰ", "a", _SH, None, HIGH, cls=LC, stype=_DD),
        _s("r", "a", _LG, "t̚", FALLING, cls=LC, stype=_DD),
        _s("tɕʰ", "a", _SH, None, HIGH, cls=LC, stype=_DD),
        _s("tʰ", "a", _LG, "n", MID, cls=LC, stype=_LV),
    )

    # พระบาท — /pʰrá-bàːt/ (royal "foot")
    data["\u0e1e\u0e23\u0e30\u0e1a\u0e32\u0e17"] = _word(
        "\u0e1e\u0e23\u0e30\u0e1a\u0e32\u0e17",
        _s("pʰ", "a", _SH, None, HIGH, cls=LC, stype=_DD),
        _s("b", "a", _LG, "t̚", LOW, cls=MC, stype=_DD),
    )

    # พระองค์ — /pʰrá-oŋ/ (royal 3rd-person pronoun)
    data["\u0e1e\u0e23\u0e30\u0e2d\u0e07\u0e04\u0e4c"] = _word(
        "\u0e1e\u0e23\u0e30\u0e2d\u0e07\u0e04\u0e4c",
        _s("pʰ", "a", _SH, None, HIGH, cls=LC, stype=_DD),
        _s("", "o", _SH, "ŋ", MID, cls=MC, stype=_LV),
    )

    # พระหัตถ์ — /pʰrá-hàt/ (royal "hand")
    data["\u0e1e\u0e23\u0e30\u0e2b\u0e31\u0e15\u0e16\u0e4c"] = _word(
        "\u0e1e\u0e23\u0e30\u0e2b\u0e31\u0e15\u0e16\u0e4c",
        _s("pʰ", "a", _SH, None, HIGH, cls=LC, stype=_DD),
        _s("h", "a", _SH, "t̚", LOW, cls=HC, stype=_DD),
    )

    # พระเนตร — /pʰrá-nêːt/ (royal "eye")
    data["\u0e1e\u0e23\u0e30\u0e40\u0e19\u0e15\u0e23"] = _word(
        "\u0e1e\u0e23\u0e30\u0e40\u0e19\u0e15\u0e23",
        _s("pʰ", "a", _SH, None, HIGH, cls=LC, stype=_DD),
        _s("n", "e", _LG, "t̚", FALLING, cls=LC, stype=_DD),
    )

    # พระโอรส — /pʰrá-oː-rót/ (royal "son")
    data["\u0e1e\u0e23\u0e30\u0e42\u0e2d\u0e23\u0e2a"] = _word(
        "\u0e1e\u0e23\u0e30\u0e42\u0e2d\u0e23\u0e2a",
        _s("pʰ", "a", _SH, None, HIGH, cls=LC, stype=_DD),
        _s("", "o", _LG, None, MID, cls=MC, stype=_LV),
        _s("r", "o", _SH, "t̚", HIGH, cls=LC, stype=_DD),
    )

    return MappingProxyType(data)


@functools.cache
def entries() -> Mapping[str, PhonologicalWord]:
    return _build()


def lookup(word: str) -> PhonologicalWord | None:
    return entries().get(word)


__all__ = ["entries", "lookup"]

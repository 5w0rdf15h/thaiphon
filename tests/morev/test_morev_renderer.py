import pytest

from thaiphon.phonology.model import (
    Coda,
    FinalType,
    Onset,
    PhonologicalWord,
    Syllable,
    Tone,
    Vowel,
    VowelLength,
)


def syl(
    *,
    c1: str,
    nucleus: str,
    length: VowelLength,
    tone: Tone,
    coda: str | None = None,
    final_type: FinalType = FinalType.NONE,
    c2: str | None = None,
    offglide: str | None = None,
) -> Syllable:
    return Syllable(
        onset=Onset(c1=c1, c2=c2),
        vowel=Vowel(nucleus=nucleus, length=length, offglide=offglide),
        coda=Coda(phoneme=coda, final_type=final_type),
        tone=tone,
    )


def w(*syllables: Syllable) -> PhonologicalWord:
    return PhonologicalWord(syllables=tuple(syllables))


@pytest.mark.parametrize(
    "word, expected",
    [
        # ---------------------------------------------------------------------
        # Aspiration marker in Morev is "small x" above-right (console: ˣ, U+02E3)
        # ---------------------------------------------------------------------
        (w(syl(c1="pʰ", nucleus="i", length=VowelLength.LONG, tone=Tone.MID)), "пˣӣ"),
        (w(syl(c1="pʰ", nucleus="u", length=VowelLength.LONG, tone=Tone.MID)), "пˣӯ"),
        (w(syl(c1="pʰ", nucleus="a", length=VowelLength.LONG, tone=Tone.MID)), "пˣа̄"),
        (w(syl(c1="pʰ", nucleus="ɔ", length=VowelLength.LONG, tone=Tone.MID)), "пˣɔ̄"),
        (w(syl(c1="tʰ", nucleus="i", length=VowelLength.LONG, tone=Tone.MID)), "тˣӣ"),
        (w(syl(c1="tʰ", nucleus="u", length=VowelLength.LONG, tone=Tone.MID)), "тˣӯ"),
        (w(syl(c1="tʰ", nucleus="a", length=VowelLength.LONG, tone=Tone.MID)), "тˣа̄"),
        (w(syl(c1="tʰ", nucleus="ɔ", length=VowelLength.LONG, tone=Tone.MID)), "тˣɔ̄"),
        (w(syl(c1="tɕʰ", nucleus="i", length=VowelLength.LONG, tone=Tone.MID)), "чӣ"),
        (w(syl(c1="tɕʰ", nucleus="u", length=VowelLength.LONG, tone=Tone.MID)), "чӯ"),
        (w(syl(c1="tɕʰ", nucleus="a", length=VowelLength.LONG, tone=Tone.MID)), "ча̄"),
        (w(syl(c1="tɕʰ", nucleus="ɔ", length=VowelLength.LONG, tone=Tone.MID)), "чɔ̄"),
        (w(syl(c1="kʰ", nucleus="i", length=VowelLength.LONG, tone=Tone.MID)), "кˣӣ"),
        (w(syl(c1="kʰ", nucleus="u", length=VowelLength.LONG, tone=Tone.MID)), "кˣӯ"),
        (w(syl(c1="kʰ", nucleus="a", length=VowelLength.LONG, tone=Tone.MID)), "кˣа̄"),
        (w(syl(c1="kʰ", nucleus="ɔ", length=VowelLength.LONG, tone=Tone.MID)), "кˣɔ̄"),
        (w(syl(c1="f", nucleus="i", length=VowelLength.LONG, tone=Tone.MID)), "фӣ"),
        (w(syl(c1="s", nucleus="u", length=VowelLength.LONG, tone=Tone.MID)), "сӯ"),
        (w(syl(c1="h", nucleus="a", length=VowelLength.LONG, tone=Tone.MID)), "ха̄"),
        # ---------------------------------------------------------------------
        # Core tone suffix coverage (same segments, 5 tones)
        # Morev tone marks:
        # Tone.LOW     -> ˆ
        # Tone.FALLING -> `
        # Tone.HIGH    -> ˇ
        # Tone.RISING  -> ´
        # ---------------------------------------------------------------------
        (w(syl(c1="k", nucleus="a", length=VowelLength.SHORT, tone=Tone.MID)), "ка"),
        (w(syl(c1="k", nucleus="a", length=VowelLength.SHORT, tone=Tone.LOW)), "каˆ"),
        (
            w(syl(c1="k", nucleus="a", length=VowelLength.SHORT, tone=Tone.FALLING)),
            "ка`",
        ),
        (w(syl(c1="k", nucleus="a", length=VowelLength.SHORT, tone=Tone.HIGH)), "каˇ"),
        (
            w(syl(c1="k", nucleus="a", length=VowelLength.SHORT, tone=Tone.RISING)),
            "ка´",
        ),
        # ---------------------------------------------------------------------
        # Vowel inventory (short)
        # ---------------------------------------------------------------------
        (w(syl(c1="m", nucleus="i", length=VowelLength.SHORT, tone=Tone.MID)), "ми"),
        (w(syl(c1="m", nucleus="ɯ", length=VowelLength.SHORT, tone=Tone.MID)), "мы"),
        (w(syl(c1="m", nucleus="u", length=VowelLength.SHORT, tone=Tone.MID)), "му"),
        (w(syl(c1="m", nucleus="e", length=VowelLength.SHORT, tone=Tone.MID)), "ме"),
        (w(syl(c1="m", nucleus="ə", length=VowelLength.SHORT, tone=Tone.MID)), "мə"),
        (w(syl(c1="m", nucleus="ɔ", length=VowelLength.SHORT, tone=Tone.MID)), "мɔ"),
        (w(syl(c1="m", nucleus="o", length=VowelLength.SHORT, tone=Tone.MID)), "мо"),
        (w(syl(c1="m", nucleus="æ", length=VowelLength.SHORT, tone=Tone.MID)), "мэ"),
        (w(syl(c1="m", nucleus="ɛ", length=VowelLength.SHORT, tone=Tone.MID)), "мэ"),
        # ---------------------------------------------------------------------
        # Vowel inventory (long, macron)
        # ---------------------------------------------------------------------
        (w(syl(c1="n", nucleus="i", length=VowelLength.LONG, tone=Tone.MID)), "нӣ"),
        (w(syl(c1="n", nucleus="ɯ", length=VowelLength.LONG, tone=Tone.MID)), "ны̄"),
        (w(syl(c1="n", nucleus="u", length=VowelLength.LONG, tone=Tone.MID)), "нӯ"),
        (w(syl(c1="n", nucleus="a", length=VowelLength.LONG, tone=Tone.MID)), "на̄"),
        (w(syl(c1="n", nucleus="ɔ", length=VowelLength.LONG, tone=Tone.MID)), "нɔ̄"),
        # ---------------------------------------------------------------------
        # Diphthongs in mapping (long + macron on first char)
        # ---------------------------------------------------------------------
        (w(syl(c1="k", nucleus="ia", length=VowelLength.LONG, tone=Tone.MID)), "кӣа"),
        (w(syl(c1="k", nucleus="ɯa", length=VowelLength.LONG, tone=Tone.MID)), "кы̄а"),
        (w(syl(c1="k", nucleus="ua", length=VowelLength.LONG, tone=Tone.MID)), "кӯа"),
        # ---------------------------------------------------------------------
        # IMPORTANT: For Morev transcription, "ai" is NOT marked with macron,
        # even if Thai orthography treats it as long/special.
        # ---------------------------------------------------------------------
        (w(syl(c1="s", nucleus="ai", length=VowelLength.SHORT, tone=Tone.MID)), "сай"),
        (w(syl(c1="s", nucleus="ai", length=VowelLength.LONG, tone=Tone.MID)), "сай"),
        # ---------------------------------------------------------------------
        # (tone + length are authoritative; aspiration handled by renderer)
        # ไก่  -> кайˆ
        # ไข่  -> кˣайˆ
        # ---------------------------------------------------------------------
        (w(syl(c1="k", nucleus="ai", length=VowelLength.LONG, tone=Tone.LOW)), "кайˆ"),
        (
            w(syl(c1="kʰ", nucleus="ai", length=VowelLength.LONG, tone=Tone.LOW)),
            "кˣайˆ",
        ),
        # ---------------------------------------------------------------------
        # Nucleus that already includes glide vs explicit offglide
        # ---------------------------------------------------------------------
        (
            w(
                syl(
                    c1="s",
                    nucleus="a",
                    length=VowelLength.SHORT,
                    tone=Tone.MID,
                    offglide="j",
                )
            ),
            "сай",
        ),
        (
            w(
                syl(
                    c1="s",
                    nucleus="a",
                    length=VowelLength.SHORT,
                    tone=Tone.MID,
                    offglide="w",
                )
            ),
            "сау",
        ),
        # ---------------------------------------------------------------------
        # Codas: sonorants
        # ---------------------------------------------------------------------
        (
            w(
                syl(
                    c1="k",
                    nucleus="a",
                    length=VowelLength.LONG,
                    tone=Tone.MID,
                    coda="m",
                    final_type=FinalType.SONORANT,
                )
            ),
            "ка̄м",
        ),
        (
            w(
                syl(
                    c1="k",
                    nucleus="a",
                    length=VowelLength.LONG,
                    tone=Tone.MID,
                    coda="n",
                    final_type=FinalType.SONORANT,
                )
            ),
            "ка̄н",
        ),
        (
            w(
                syl(
                    c1="k",
                    nucleus="a",
                    length=VowelLength.LONG,
                    tone=Tone.MID,
                    coda="ŋ",
                    final_type=FinalType.SONORANT,
                )
            ),
            "ка̄нг",
        ),
        (
            w(
                syl(
                    c1="k",
                    nucleus="a",
                    length=VowelLength.LONG,
                    tone=Tone.MID,
                    coda="j",
                    final_type=FinalType.SONORANT,
                )
            ),
            "ка̄й",
        ),
        (
            w(
                syl(
                    c1="k",
                    nucleus="a",
                    length=VowelLength.LONG,
                    tone=Tone.MID,
                    coda="w",
                    final_type=FinalType.SONORANT,
                )
            ),
            "ка̄у",
        ),
        # ---------------------------------------------------------------------
        # Codas: stops (Thai final stops)
        # ---------------------------------------------------------------------
        (
            w(
                syl(
                    c1="m",
                    nucleus="a",
                    length=VowelLength.LONG,
                    tone=Tone.FALLING,
                    coda="k",
                    final_type=FinalType.STOP,
                )
            ),
            "ма̄к`",
        ),
        (
            w(
                syl(
                    c1="m",
                    nucleus="a",
                    length=VowelLength.LONG,
                    tone=Tone.FALLING,
                    coda="t",
                    final_type=FinalType.STOP,
                )
            ),
            "ма̄т`",
        ),
        (
            w(
                syl(
                    c1="m",
                    nucleus="a",
                    length=VowelLength.LONG,
                    tone=Tone.FALLING,
                    coda="p",
                    final_type=FinalType.STOP,
                )
            ),
            "ма̄п`",
        ),
        # ---------------------------------------------------------------------
        # Onset clusters (C2)
        # ---------------------------------------------------------------------
        (
            w(
                syl(
                    c1="kʰ", c2="r", nucleus="a", length=VowelLength.LONG, tone=Tone.MID
                )
            ),
            "кˣра̄",
        ),
        (
            w(syl(c1="k", c2="l", nucleus="a", length=VowelLength.LONG, tone=Tone.MID)),
            "кла̄",
        ),
        (
            w(syl(c1="k", c2="w", nucleus="a", length=VowelLength.LONG, tone=Tone.MID)),
            "куа̄",
        ),
        # ---------------------------------------------------------------------
        # Multi-syllable join with hyphen
        # ---------------------------------------------------------------------
        (
            w(
                syl(c1="k", nucleus="a", length=VowelLength.SHORT, tone=Tone.LOW),
                syl(
                    c1="m",
                    nucleus="a",
                    length=VowelLength.LONG,
                    tone=Tone.MID,
                    coda="t",
                    final_type=FinalType.STOP,
                ),
            ),
            "каˆ-ма̄т",
        ),
        # ---------------------------------------------------------------------
        # Morev reading rules: inherent "o" in two-letter syllables,
        # and special case with final ร -> long o + final n (Morev: โอ̄н)
        # ---------------------------------------------------------------------
        (
            w(
                syl(
                    c1="k",
                    nucleus="o",
                    length=VowelLength.LONG,
                    tone=Tone.LOW,
                    coda="n",
                    final_type=FinalType.SONORANT,
                )
            ),
            "ко̄нˆ",
        ),  # กร kōnˆ
        (
            w(
                syl(
                    c1="tɕ",
                    nucleus="o",
                    length=VowelLength.LONG,
                    tone=Tone.MID,
                    coda="n",
                    final_type=FinalType.SONORANT,
                )
            ),
            "тьо̄н",
        ),  # จร tɕōn
        (
            w(
                syl(
                    c1="pʰ",
                    nucleus="o",
                    length=VowelLength.LONG,
                    tone=Tone.MID,
                    coda="n",
                    final_type=FinalType.SONORANT,
                )
            ),
            "пˣо̄н",
        ),  # พร pʰōn
        # ---------------------------------------------------------------------
        # Morev: in final consonant clusters, only the FIRST final consonant is read
        # Examples: บุตร / บาตร -> final is ต (t), ร is silent in coda
        # ---------------------------------------------------------------------
        (
            w(
                syl(
                    c1="b",
                    nucleus="u",
                    length=VowelLength.SHORT,
                    tone=Tone.LOW,
                    coda="t",
                    final_type=FinalType.STOP,
                )
            ),
            "бутˆ",
        ),  # บุตร butˆ
        (
            w(
                syl(
                    c1="b",
                    nucleus="a",
                    length=VowelLength.LONG,
                    tone=Tone.LOW,
                    coda="t",
                    final_type=FinalType.STOP,
                )
            ),
            "ба̄тˆ",
        ),  # บาตร bātˆ
        # ---------------------------------------------------------------------
        # ro han (รร): vowel behavior
        # - บรรดา: รร + final consonant present -> short a; multi-syllable: ban-dā
        # - กรรม: รร + final consonant present -> short a; final ม is read: kam
        # ---------------------------------------------------------------------
        (
            w(
                syl(
                    c1="b",
                    nucleus="a",
                    length=VowelLength.SHORT,
                    tone=Tone.MID,
                    coda="n",
                    final_type=FinalType.SONORANT,
                ),
                syl(c1="d", nucleus="a", length=VowelLength.LONG, tone=Tone.MID),
            ),
            "бан-да̄",
        ),  # บรรดา ban-dā
        (
            w(
                syl(
                    c1="k",
                    nucleus="a",
                    length=VowelLength.SHORT,
                    tone=Tone.MID,
                    coda="m",
                    final_type=FinalType.SONORANT,
                )
            ),
            "кам",
        ),  # กรรม kam
        # ---------------------------------------------------------------------
        # Start digraphs that read as ONE consonant:
        # ทร / ศร / สร -> s
        # จร -> tɕ (ть)
        # ---------------------------------------------------------------------
        (
            w(
                syl(
                    c1="s",
                    nucleus="a",
                    length=VowelLength.LONG,
                    tone=Tone.FALLING,
                    coda="p",
                    final_type=FinalType.STOP,
                )
            ),
            "са̄п`",
        ),  # ทราบ sāp`
        (
            w(syl(c1="s", nucleus="i", length=VowelLength.LONG, tone=Tone.RISING)),
            "сӣ´",
        ),  # ศรี sī´
        (
            w(
                syl(
                    c1="s",
                    nucleus="ua",
                    length=VowelLength.LONG,
                    tone=Tone.RISING,
                    coda="m",
                    final_type=FinalType.SONORANT,
                )
            ),
            "сӯам´",
        ),
        (
            w(
                syl(
                    c1="tɕ",
                    nucleus="i",
                    length=VowelLength.SHORT,
                    tone=Tone.MID,
                    coda="ŋ",
                    final_type=FinalType.SONORANT,
                )
            ),
            "тьинг",
        ),  # จรง tɕing
        # ---------------------------------------------------------------------
        # Morev dictionary examples: "true clusters" (C + r/l/w) from the table
        # ---------------------------------------------------------------------
        (
            w(
                syl(
                    c1="k",
                    c2="r",
                    nucleus="a",
                    length=VowelLength.LONG,
                    tone=Tone.MID,
                    coda="j",
                    final_type=FinalType.SONORANT,
                )
            ),
            "кра̄й",
        ),
        (
            w(
                syl(
                    c1="kʰ",
                    c2="r",
                    nucleus="a",
                    length=VowelLength.LONG,
                    tone=Tone.MID,
                    coda="m",
                    final_type=FinalType.SONORANT,
                )
            ),
            "кˣра̄м",
        ),
        (
            w(
                syl(
                    c1="kʰ",
                    c2="r",
                    nucleus="ɯ",
                    length=VowelLength.SHORT,
                    tone=Tone.MID,
                    coda="m",
                    final_type=FinalType.SONORANT,
                )
            ),
            "кˣрым",
        ),
        (
            w(syl(c1="p", c2="l", nucleus="a", length=VowelLength.LONG, tone=Tone.MID)),
            "пла̄",
        ),
        (
            w(
                syl(
                    c1="k",
                    c2="l",
                    nucleus="a",
                    length=VowelLength.LONG,
                    tone=Tone.MID,
                    coda="j",
                    final_type=FinalType.SONORANT,
                )
            ),
            "кла̄й",
        ),
        (
            w(
                syl(
                    c1="kʰ",
                    c2="l",
                    nucleus="u",
                    length=VowelLength.SHORT,
                    tone=Tone.MID,
                    coda="m",
                    final_type=FinalType.SONORANT,
                )
            ),
            "кˣлум",
        ),
        (
            w(
                syl(
                    c1="kʰ",
                    c2="l",
                    nucleus="a",
                    length=VowelLength.LONG,
                    tone=Tone.MID,
                    coda="j",
                    final_type=FinalType.SONORANT,
                )
            ),
            "кˣла̄й",
        ),
        (
            w(
                syl(
                    c1="k",
                    c2="w",
                    nucleus="a",
                    length=VowelLength.LONG,
                    tone=Tone.MID,
                    coda="ŋ",
                    final_type=FinalType.SONORANT,
                )
            ),
            "куа̄нг",
        ),
        (
            w(
                syl(
                    c1="kʰ",
                    c2="w",
                    nucleus="a",
                    length=VowelLength.LONG,
                    tone=Tone.MID,
                    coda="ŋ",
                    final_type=FinalType.SONORANT,
                )
            ),
            "кˣуа̄нг",
        ),
        (
            w(
                syl(
                    c1="kʰ",
                    c2="w",
                    nucleus="a",
                    length=VowelLength.LONG,
                    tone=Tone.MID,
                    coda="j",
                    final_type=FinalType.SONORANT,
                )
            ),
            "кˣуа̄й",
        ),
        (
            w(
                syl(
                    c1="p",
                    c2="r",
                    nucleus="a",
                    length=VowelLength.LONG,
                    tone=Tone.MID,
                    coda="j",
                    final_type=FinalType.SONORANT,
                )
            ),
            "пра̄й",
        ),
        (
            w(
                syl(
                    c1="pʰ",
                    c2="r",
                    nucleus="a",
                    length=VowelLength.LONG,
                    tone=Tone.MID,
                    coda="ŋ",
                    final_type=FinalType.SONORANT,
                )
            ),
            "пˣра̄нг",
        ),
        (
            w(syl(c1="t", c2="r", nucleus="a", length=VowelLength.LONG, tone=Tone.MID)),
            "тра̄",
        ),
        (
            w(
                syl(
                    c1="pʰ", c2="r", nucleus="a", length=VowelLength.LONG, tone=Tone.MID
                ),
                syl(
                    c1="d",
                    nucleus="o",
                    length=VowelLength.LONG,
                    tone=Tone.MID,
                    coda="n",
                    final_type=FinalType.SONORANT,
                ),
            ),
            "пˣра̄-до̄н",
        ),
        (
            w(
                syl(
                    c1="pʰ",
                    c2="l",
                    nucleus="a",
                    length=VowelLength.LONG,
                    tone=Tone.MID,
                    coda="n",
                    final_type=FinalType.SONORANT,
                )
            ),
            "пˣла̄н",
        ),
        (
            w(
                syl(
                    c1="pʰ",
                    c2="l",
                    nucleus="ua",
                    length=VowelLength.LONG,
                    tone=Tone.MID,
                    coda="ŋ",
                    final_type=FinalType.SONORANT,
                )
            ),
            "пˣлӯанг",
        ),
        # ---------------------------------------------------------------------
        # Morev: CC sequences split into two syllables (tone borrowing rule)
        # ---------------------------------------------------------------------
        (
            w(
                syl(c1="t", nucleus="a", length=VowelLength.SHORT, tone=Tone.LOW),
                syl(
                    c1="l",
                    nucleus="o",
                    length=VowelLength.SHORT,
                    tone=Tone.LOW,
                    coda="k",
                    final_type=FinalType.STOP,
                ),
            ),
            "таˆ-локˆ",
        ),
        (
            w(
                syl(c1="kʰ", nucleus="a", length=VowelLength.SHORT, tone=Tone.LOW),
                syl(
                    c1="n",
                    nucleus="o",
                    length=VowelLength.SHORT,
                    tone=Tone.RISING,
                    coda="m",
                    final_type=FinalType.SONORANT,
                ),
            ),
            "кˣаˆ-ном´",
        ),
        (
            w(
                syl(c1="tʰ", nucleus="a", length=VowelLength.SHORT, tone=Tone.LOW),
                syl(
                    c1="n",
                    nucleus="o",
                    length=VowelLength.SHORT,
                    tone=Tone.RISING,
                    coda="n",
                    final_type=FinalType.SONORANT,
                ),
            ),
            "тˣаˆ-нон´",
        ),
    ],
)
def test_morev_renderer_matrix(
    word: PhonologicalWord, expected: str, morev_renderer, nfd
):
    out = morev_renderer.render(word)
    assert nfd(out) == nfd(expected)


def test_morev_renderer_real_word_kaaw_naaa_regression(morev_transcribe, nfd):
    out = morev_transcribe("ก้าวหนา")
    assert nfd(out) == nfd("ка̄у`-на̄´")

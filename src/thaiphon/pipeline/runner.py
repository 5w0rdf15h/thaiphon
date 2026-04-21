"""Pipeline runner: orchestrates normalization → tokenization → derivation → ranking."""

from __future__ import annotations

from dataclasses import replace as _dc_replace
from typing import Literal

from thaiphon.derivation import coda as coda_mod
from thaiphon.derivation import onset as onset_mod
from thaiphon.derivation import syllable_type as stype_mod
from thaiphon.derivation import tone as tone_mod
from thaiphon.derivation import vowel as vowel_mod
from thaiphon.errors import ParseError
from thaiphon.lexicons import calendar as calendar_lex
from thaiphon.lexicons import cluster_overrides as cluster_overrides_lex
from thaiphon.lexicons import exact as exact_lex
from thaiphon.lexicons import indic_learned as indic_learned_lex
from thaiphon.lexicons import irregular as irregular_lex
from thaiphon.lexicons import length_overrides as length_lex
from thaiphon.lexicons import ror_ror as ror_ror_lex
from thaiphon.lexicons import royal as royal_lex
from thaiphon.lexicons import rue as rue_lex
from thaiphon.lexicons import silent_h as silent_h_lex
from thaiphon.lexicons import thor as thor_lex
from thaiphon.lexicons.loanword_detector import score_foreignness
from thaiphon.model import letters
from thaiphon.model.candidate import AnalysisResult, SyllabificationCandidate
from thaiphon.model.enums import EffectiveClass, SyllableType, ToneMark, VowelLength
from thaiphon.model.phoneme import Phoneme
from thaiphon.model.syllable import Syllable
from thaiphon.model.word import PhonologicalWord
from thaiphon.normalization import expand as expand_mod
from thaiphon.normalization import unicode_norm
from thaiphon.syllabification.generator import CandidateGenerator
from thaiphon.syllabification.ranker import CandidateRanker
from thaiphon.tables import consonants as consonants_tbl
from thaiphon.tokenization import tcc

# Tone-mark char → enum.
ReadingProfile = Literal[
    "everyday", "careful_educated", "learned_full", "etalon_compat"
]

_VALID_PROFILES: frozenset[str] = frozenset(
    {"everyday", "careful_educated", "learned_full", "etalon_compat"}
)


def _validate_profile(profile: str) -> ReadingProfile:
    if profile not in _VALID_PROFILES:
        raise ValueError(
            f"unknown reading profile {profile!r}; "
            f"expected one of {sorted(_VALID_PROFILES)}"
        )
    return profile  # type: ignore[return-value]


_TONE_MARK_MAP: dict[str, ToneMark] = {
    letters.MAI_EK: ToneMark.MAI_EK,
    letters.MAI_THO: ToneMark.MAI_THO,
    letters.MAI_TRI: ToneMark.MAI_TRI,
    letters.MAI_JATTAWA: ToneMark.MAI_JATTAWA,
}

# Chars that are never a coda (vowel markers or tone marks etc.)
_NON_CODA: frozenset[str] = (
    letters.PRE_VOWELS | letters.POST_BASE_VOWEL_MARKS | frozenset(_TONE_MARK_MAP)
)


def _extract_tone_mark(raw: str) -> ToneMark:
    for ch in raw:
        if ch in _TONE_MARK_MAP:
            return _TONE_MARK_MAP[ch]
    return ToneMark.NONE


def _respell_insert_u(text: str) -> tuple[str, ...] | None:
    """Rewrite an INSERT_U word so the derivation pipeline reads it with a
    closed /uːə/ nucleus (R-CD-004 allomorph).

    The canonical shape is ``C + ว + coda...`` — insert ``◌ั`` between the
    onset consonant and ``ว`` to force the ``◌ัว`` centring-diphthong
    branch in :mod:`thaiphon.derivation.vowel`. Only the minimal ``C+ว+C``
    template is handled here; more complex INSERT_U words (e.g. ``ขวาน``,
    ``ขวนขวาย``) are left for a lexicon-driven follow-up.
    """
    if len(text) != 3:
        return None
    c1, mid, c2 = text[0], text[1], text[2]
    if mid != letters.WO_WAEN:
        return None
    if c1 not in consonants_tbl.CONSONANTS:
        return None
    if c2 not in consonants_tbl.CONSONANTS:
        return None
    return (c1 + letters.MAI_HAN_AKAT + letters.WO_WAEN + c2,)


def _find_final(raw: str, onset_end: int) -> tuple[str | None, str]:
    """Scan post-onset portion for a trailing consonant that isn't part of a vowel.

    Returns (final_char_or_None, cleaned_syllable_chars). Treat a trailing
    bare ``อ`` (the post-base vowel carrier for long /ɔː/) as NOT a final —
    it's part of the vowel.
    """
    # Handle thanthakhat (M-700a/c): ◌์ kills the consonant before it.
    # Extension rules (conservative — aggressive extension is unsafe when
    # the leading consonant happens to be ว/อ/ย used as a vowel carrier in
    # an adjacent syllable):
    #   * If an above/below vowel mark rides on the killed consonant
    #     (e.g. ด + ◌ิ + ์ in ศักดิ์), kill the vowel mark too.
    #   * If the preceding consonant forms a Sanskrit-fossil silent tail
    #     with the killed consonant (ทร, ตร, ตย, ดร, ทย, …), kill both —
    #     this handles จันทร์, พักตร์.
    # No further extension; writers signalling a longer silent tail use
    # repeated ◌์ or rely on irregular-readings lexicon entries.
    if letters.THANTHAKHAT in raw:
        chars = list(raw)
        # Known silent tail clusters (first, last) — conservative list of
        # Sanskrit loan fossils attested in Thai orthography.
        silent_tail_pairs: frozenset[tuple[str, str]] = frozenset(
            {
                ("ท", "ร"), ("ต", "ร"), ("ด", "ร"), ("พ", "ร"),
                ("ต", "ย"), ("ท", "ย"), ("ด", "ย"),
                ("ษ", "ณ"), ("ก", "ษ"), ("ก", "ร"),
                ("ค", "ร"),
            }
        )
        i = 0
        while i < len(chars):
            if chars[i] != letters.THANTHAKHAT:
                i += 1
                continue
            j = i - 1
            kill_end = i
            # Skip tone marks riding on ◌์.
            while j >= 0 and chars[j] in _TONE_MARK_MAP:
                j -= 1
            if j < 0:
                del chars[i]
                continue
            # A single above/below vowel mark may sit between the killed
            # consonant and ◌์ (e.g. ด + ◌ิ + ์ in ศักดิ์). Absorb it.
            kill_start = j
            if chars[j] in letters.POST_BASE_VOWEL_MARKS:
                j -= 1
                while j >= 0 and chars[j] in _TONE_MARK_MAP:
                    j -= 1
            if j < 0 or chars[j] not in consonants_tbl.CONSONANTS:
                # No consonant to kill — just drop ◌์ and any vowel mark
                # we've collected.
                del chars[kill_start : kill_end + 1]
                continue
            killed_c = chars[j]
            kill_start = j
            # Look further back for another vowel mark that rode on the
            # killed consonant from the front side (rare; conservative).
            k = j - 1
            while k >= 0 and chars[k] in _TONE_MARK_MAP:
                k -= 1
            # Sanskrit-fossil silent-tail cluster.
            if (
                k >= 0
                and chars[k] in consonants_tbl.CONSONANTS
                and (chars[k], killed_c) in silent_tail_pairs
            ):
                # Only extend if the leading consonant has no vowel mark
                # directly before it (would signal a pronounced syllable).
                m = k - 1
                while m >= 0 and chars[m] in _TONE_MARK_MAP:
                    m -= 1
                leading_has_vowel = m >= 0 and chars[m] in (
                    letters.POST_BASE_VOWEL_MARKS | letters.PRE_VOWELS
                )
                if not leading_has_vowel:
                    kill_start = k
            del chars[kill_start : kill_end + 1]
            # Do not advance i — list shrank.
        cleaned_str = "".join(chars)
    else:
        cleaned_str = raw

    post_onset = cleaned_str[onset_end:]
    saw_vowel = False
    consonants_after_vowel: list[tuple[int, str]] = []
    # Is there a pre-base vowel (เ) in the cleaned chars before onset_end?
    _pre_vowel_present = any(c in letters.PRE_VOWELS for c in cleaned_str[:onset_end])
    for idx, ch in enumerate(post_onset):
        if ch in _TONE_MARK_MAP:
            continue
        if ch in letters.POST_BASE_VOWEL_MARKS:
            saw_vowel = True
            continue
        # ว after ◌ั is part of the ัว diphthong, not a final (M-203).
        if ch == letters.WO_WAEN and idx > 0 and post_onset[idx - 1] == letters.MAI_HAN_AKAT:
            saw_vowel = True
            continue
        # R-CD-002: ย after ◌ี inside a เ-frame is part of the /iːə/
        # nucleus, not a coda. Same for R-CD-003: อ after ◌ื.
        if _pre_vowel_present and idx > 0:
            prev_ch = post_onset[idx - 1]
            if ch == letters.YO_YAK and prev_ch == letters.SARA_II:
                saw_vowel = True
                continue
            if ch == letters.O_ANG and prev_ch == letters.SARA_UEE:
                saw_vowel = True
                continue
        if ch == letters.O_ANG:
            # Post-base อ carrier: acts as a vowel; consonants after it can
            # be finals.
            saw_vowel = True
            continue
        if ch in consonants_tbl.CONSONANTS and saw_vowel:
            consonants_after_vowel.append((idx, ch))
    if consonants_after_vowel:
        final = consonants_after_vowel[-1][1]
        last_idx = consonants_after_vowel[-1][0]
        trimmed_post = post_onset[:last_idx] + post_onset[last_idx + 1:]
        return final, cleaned_str[:onset_end] + trimmed_post

    if not saw_vowel:
        trailing_consonants = [
            (i, c) for i, c in enumerate(post_onset)
            if c in consonants_tbl.CONSONANTS
        ]
        if trailing_consonants:
            last_idx, last_c = trailing_consonants[-1]
            trimmed_post = post_onset[:last_idx] + post_onset[last_idx + 1:]
            return last_c, cleaned_str[:onset_end] + trimmed_post

    return None, cleaned_str


def _derive_syllable(raw: str, *, force_hc: bool = False) -> Syllable:
    """Derive a Syllable from one raw syllable string."""
    if not raw:
        raise ParseError("empty syllable")

    pre_vowel: str | None = None
    body = raw
    if raw[0] in letters.PRE_VOWELS:
        pre_vowel = raw[0]
        body = raw[1:]

    onset_info = onset_mod.resolve_onset(body)
    onset_end_in_full = (1 if pre_vowel else 0) + onset_info.consumed

    final_char, cleaned_raw = _find_final(raw, onset_end_in_full)
    tone_mark = _extract_tone_mark(raw)

    vowel_info = vowel_mod.resolve_vowel(
        cleaned_raw,
        onset_consumed=onset_end_in_full,
        has_final=final_char is not None,
        tone_mark_present=tone_mark is not ToneMark.NONE,
        final_char=final_char,
    )

    coda_info = coda_mod.resolve_coda(final_char)

    effective_coda = coda_info
    if coda_info.phoneme is None and vowel_info.offglide is not None:
        og_phoneme = Phoneme(vowel_info.offglide, is_sonorant=True)
        effective_coda = coda_mod.FinalAnalysis(
            phoneme=og_phoneme, syllable_type_hint=SyllableType.LIVE
        )

    syll_type = stype_mod.classify(
        vowel_info.length, effective_coda, has_written_vowel=True
    )

    effective_class = onset_info.effective_class
    if force_hc:
        effective_class = EffectiveClass.HIGH

    tone = tone_mod.assign_tone(
        effective_class, syll_type, vowel_info.length, tone_mark
    )

    vowel_phoneme = Phoneme(vowel_info.quality)

    return Syllable(
        onset=onset_info.onset,
        vowel=vowel_phoneme,
        vowel_length=vowel_info.length,
        coda=effective_coda.phoneme,
        tone=tone,
        tone_mark=tone_mark,
        effective_class=effective_class,
        syllable_type=syll_type,
        raw=raw,
        inserted_vowel=vowel_info.inserted_vowel,
    )


def _length_override(syl: Syllable, target: VowelLength) -> Syllable:
    """Return ``syl`` with its vowel length replaced by ``target``."""
    if syl.vowel_length is target:
        return syl
    # Rebuild tone to reflect new length (syllable_type may also change).
    new_type = syl.syllable_type
    if syl.coda is None:
        new_type = SyllableType.LIVE if target is VowelLength.LONG else SyllableType.DEAD
    tone = tone_mod.assign_tone(syl.effective_class, new_type, target, syl.tone_mark)
    return Syllable(
        onset=syl.onset,
        vowel=syl.vowel,
        vowel_length=target,
        coda=syl.coda,
        tone=tone,
        tone_mark=syl.tone_mark,
        effective_class=syl.effective_class,
        syllable_type=new_type,
        raw=syl.raw,
        inserted_vowel=syl.inserted_vowel,
    )


def _apply_silent_h(syl: Syllable) -> Syllable:
    """M-525: rebuild the last syllable with HC effective class."""
    if syl.effective_class is EffectiveClass.HIGH:
        return syl
    tone = tone_mod.assign_tone(
        EffectiveClass.HIGH, syl.syllable_type, syl.vowel_length, syl.tone_mark
    )
    return Syllable(
        onset=syl.onset,
        vowel=syl.vowel,
        vowel_length=syl.vowel_length,
        coda=syl.coda,
        tone=tone,
        tone_mark=syl.tone_mark,
        effective_class=EffectiveClass.HIGH,
        syllable_type=syl.syllable_type,
        raw=syl.raw,
        inserted_vowel=syl.inserted_vowel,
    )


# M-521 aksornam (leader) propagation.
# HC leaders — when followed by an LC-sonorant without a written vowel,
# the second syllable takes HIGH effective class for tone.
_HC_LEADERS: frozenset[str] = frozenset({"ส", "ข", "ฉ", "ผ", "ถ", "ศ", "ษ", "ห"})
# MC leaders (ก/จ/ด/ต/บ/ป/อ) similarly propagate; the second syllable
# takes MID effective class.
_MC_LEADERS: frozenset[str] = frozenset({"ก", "จ", "ด", "ต", "บ", "ป", "อ"})
_LC_SONORANTS: frozenset[str] = frozenset({"ง", "ญ", "น", "ม", "ย", "ร", "ล", "ว"})


def _propagate_aksornam(
    segments: tuple[str, ...], syllables: list[Syllable]
) -> list[Syllable]:
    """M-521: when a bare leader segment is followed by a segment whose
    onset consonant is an LC-sonorant, rebuild the second syllable with
    the leader's effective class so tone lookup follows the leader."""
    if len(segments) < 2 or len(syllables) < 2:
        return syllables
    for i in range(len(segments) - 1):
        seg = segments[i]
        nxt = segments[i + 1]
        if len(seg) != 1:
            continue
        if seg in _HC_LEADERS:
            promoted = EffectiveClass.HIGH
        elif seg in _MC_LEADERS:
            promoted = EffectiveClass.MID
        else:
            continue
        onset_char: str | None = None
        for ch in nxt:
            if ch in consonants_tbl.CONSONANTS:
                onset_char = ch
                break
        if onset_char is None or onset_char not in _LC_SONORANTS:
            continue
        target = syllables[i + 1]
        if target.effective_class is promoted:
            continue
        new_tone = tone_mod.assign_tone(
            promoted,
            target.syllable_type,
            target.vowel_length,
            target.tone_mark,
        )
        syllables[i + 1] = Syllable(
            onset=target.onset,
            vowel=target.vowel,
            vowel_length=target.vowel_length,
            coda=target.coda,
            tone=new_tone,
            tone_mark=target.tone_mark,
            effective_class=promoted,
            syllable_type=target.syllable_type,
            raw=target.raw,
            inserted_vowel=target.inserted_vowel,
        )
    return syllables


def _with_raw(word: PhonologicalWord, raw: str) -> PhonologicalWord:
    """Return ``word`` with its ``raw`` field populated, if empty.

    Lexicon-stored :class:`PhonologicalWord` values (e.g. Volubilis
    ``ENTRIES``) don't always carry the source orthography. Renderers that
    key editorial rules off the source word (e.g. the tlc scheme's
    loanword /f/ preservation) need the raw populated, so fill it from
    the analyzer's input text when missing.
    """
    if word.raw:
        return word
    return PhonologicalWord(
        syllables=word.syllables,
        morpheme_boundaries=word.morpheme_boundaries,
        confidence=word.confidence,
        source=word.source,
        raw=raw,
    )


def _derive_segments(
    segments: tuple[str, ...], *, silent_h: bool = False
) -> tuple[Syllable, ...]:
    syllables: list[Syllable] = []
    last_idx = len(segments) - 1
    for i, seg in enumerate(segments):
        force_hc = silent_h and i == last_idx
        syllables.append(_derive_syllable(seg, force_hc=force_hc))
    syllables = _propagate_aksornam(segments, syllables)
    return tuple(syllables)


class PipelineRunner:
    __slots__ = ("_generator", "_ranker")

    def __init__(
        self,
        generator: CandidateGenerator | None = None,
        ranker: CandidateRanker | None = None,
    ) -> None:
        self._generator = generator if generator is not None else CandidateGenerator()
        self._ranker = ranker if ranker is not None else CandidateRanker()

    def analyze(
        self,
        text: str,
        *,
        is_final_in_compound: bool = True,
        profile: ReadingProfile = "everyday",
    ) -> AnalysisResult:
        """Run the full analysis pipeline and attach the loanword detector
        observation.

        The foreignness detector runs after normalization on the
        post-expansion text and its output is attached as
        :attr:`AnalysisResult.loan_analysis`. The detector is observational
        only — nothing in the rest of the pipeline consults it. Downstream
        callers may read it for logging or gating.
        """
        result = self._analyze_core(
            text,
            is_final_in_compound=is_final_in_compound,
            profile=profile,
        )
        # Score against the post-normalization / post-expansion form so the
        # detector sees the same surface the rest of the pipeline did.
        loan = score_foreignness(result.raw)
        return _dc_replace(result, loan_analysis=loan)

    def _analyze_core(
        self,
        text: str,
        *,
        is_final_in_compound: bool = True,
        profile: ReadingProfile = "everyday",
    ) -> AnalysisResult:
        profile = _validate_profile(profile)
        text = unicode_norm.normalize(text)
        text = expand_mod.expand(text)

        if not text:
            empty = PhonologicalWord(syllables=(), raw="")
            return AnalysisResult(best=empty, raw="")

        # Stage 4: full-form lexicon. Skipped when:
        # * single-character input (letter-name reading vs inherent-vowel is ambiguous)
        # * compound-revertible words — length depends on position; rule engine handles it
        skip_exact = (
            len(text) == 1
            or length_lex.is_compound_revertible(text)
        )

        # Indic learned readings take precedence over the general exact
        # lexicon (Volubilis): these entries were curated specifically
        # because the Volubilis reading diverged from the etalon. If a word
        # exists in the Indic lexicon, trust it. ``thai_lexicalized`` rows
        # deliberately fall through to the general pipeline.
        if not skip_exact:
            indic_hit = indic_learned_lex.lookup(text)
            if indic_hit is not None and indic_hit.mode in (
                "learned_full",
                "variable",
            ):
                resolved_word = indic_hit.resolve(profile)
                return AnalysisResult(
                    best=_with_raw(resolved_word, text),
                    raw=text,
                    source="lexicon",
                )

        hit = None if skip_exact else exact_lex.lookup(text)
        if hit is None:
            hit = royal_lex.lookup(text)
        if hit is not None:
            return AnalysisResult(
                best=_with_raw(hit, text), raw=text, source="lexicon"
            )

        # Closed calendar class (months, weekdays, month abbreviations).
        # Runs after the general exact lexicon so Volubilis/royal can win,
        # but before syllabification so the fixed readings short-circuit
        # the Indic linker.
        cal_respelling = calendar_lex.lookup(text)
        if cal_respelling is not None:
            try:
                syllables = _derive_segments(cal_respelling)
                word = PhonologicalWord(
                    syllables=syllables,
                    confidence=1.0,
                    source="lexicon",
                    raw=text,
                )
                return AnalysisResult(
                    best=word, raw=text, source="lexicon"
                )
            except Exception:  # noqa: BLE001 — fall through to derivation
                pass

        # M-750 mid-word ทร rewrite (pre-derivation).
        rewritten = thor_lex.rewrite_thor_mid(text)
        if rewritten != text:
            text = rewritten

        # M-720 — pre-built syllables (irregular readings).
        irregular_syls = irregular_lex.lookup_syllables(text)
        if irregular_syls is not None:
            word = PhonologicalWord(
                syllables=irregular_syls,
                confidence=1.0,
                source="lexicon",
                raw=text,
            )
            return AnalysisResult(
                best=word, raw=text, source="lexicon"
            )

        # R-CD-004 cluster-override: the closed ``ขว/คว/กว + coda`` words
        # listed in :data:`cluster_overrides_lex.INSERT_U_WORDS` are read
        # with an aksornam-style inserted /u/ rather than as a /kʰw/ or
        # /kw/ cluster. Respell ``C + ว + C`` as ``C + ◌ั + ว + C`` so the
        # rest of the derivation picks up the /uːə/ nucleus automatically.
        if cluster_overrides_lex.is_insert_u(text):
            respelled = _respell_insert_u(text)
            if respelled is not None:
                try:
                    syllables = _derive_segments(respelled)
                    word = PhonologicalWord(
                        syllables=syllables,
                        confidence=1.0,
                        source="lexicon",
                        raw=text,
                    )
                    return AnalysisResult(
                        best=word, raw=text, source="lexicon"
                    )
                except Exception:  # noqa: BLE001 — fall through to derivation
                    pass

        # M-720 / M-700f-h / M-740 (รร) — pre-derivation respelling lexicons.
        respelling = irregular_lex.lookup(text) or ror_ror_lex.lookup(text)
        if respelling is not None:
            try:
                syllables = _derive_segments(respelling)
                word = PhonologicalWord(
                    syllables=syllables,
                    confidence=1.0,
                    source="lexicon",
                    raw=text,
                )
                return AnalysisResult(
                    best=word, raw=text, source="lexicon"
                )
            except Exception:  # noqa: BLE001 — fall through to derivation
                pass

        # M-750 ทร short-circuit.
        thor_reading = thor_lex.lookup(text)
        if thor_reading is not None:
            thor_word = self._render_thor(text, thor_reading)
            if thor_word is not None:
                return AnalysisResult(
                    best=thor_word, raw=text, source="lexicon"
                )

        # M-730 ฤ short-circuit.
        rue_reading = rue_lex.lookup(text)
        if rue_reading is not None:
            rue_word = self._render_rue(text, rue_reading)
            if rue_word is not None:
                return AnalysisResult(
                    best=rue_word, raw=text, source="lexicon"
                )

        tokens = tcc.tokenize(text)
        candidates = self._generator.generate(tokens)

        # M-525 silent-ห: if the full word is in the set, mark candidates for HC override.
        silent_h_hit = silent_h_lex.contains(text)

        best_cand: SyllabificationCandidate | None = None
        derived: list[tuple[SyllabificationCandidate, PhonologicalWord]] = []
        for cand in candidates:
            try:
                syllables = _derive_segments(cand.segments, silent_h=silent_h_hit)
            except Exception:  # noqa: BLE001 — drop candidates that fail derivation
                continue
            word = PhonologicalWord(
                syllables=syllables,
                confidence=cand.score,
                source="derivation",
                raw=text,
            )
            # Lexicon-confirmed bump: M-602 / 602a / 602b. When the word
            # is mid-compound and listed as revertible (M-602, not 602a/b),
            # the override is suppressed and the derived SHORT form stands.
            override = length_lex.lookup(text)
            if (
                override is not None
                and not is_final_in_compound
                and length_lex.is_compound_revertible(text)
            ):
                override = None
            if override is not None and len(syllables) >= 1:
                new_last = _length_override(syllables[-1], override)
                syllables = syllables[:-1] + (new_last,)
                word = PhonologicalWord(
                    syllables=syllables,
                    confidence=cand.score + 0.3,
                    source="derivation+lexicon",
                    raw=text,
                )
                # Rewrite candidate score for ranker visibility.
                cand = SyllabificationCandidate(
                    segments=cand.segments,
                    strategy=cand.strategy,
                    score=cand.score + 0.3,
                    notes=cand.notes,
                )
            derived.append((cand, word))
            if best_cand is None or cand.score > best_cand.score:
                best_cand = cand
        if not derived:
            empty = PhonologicalWord(syllables=(), raw=text)
            return AnalysisResult(best=empty, raw=text)
        ranked_cands = self._ranker.rank([c for c, _ in derived])
        word_by_cand = {id(c): w for c, w in derived}
        ranked_words = [word_by_cand[id(c)] for c in ranked_cands]
        return AnalysisResult(
            best=ranked_words[0],
            alternatives=tuple(ranked_words[1:]),
            source="derivation",
            raw=text,
        )

    def _render_thor(self, text: str, reading: str) -> PhonologicalWord | None:
        """Apply a M-750 ทร reading by substituting into a derivable respelling."""
        if not text.startswith("\u0e17\u0e23"):
            # ทร sub-cases may be mid-word (e.g. อินทรีย์) — not yet handled.
            return None
        remainder = text[2:]
        respelling: tuple[str, ...]
        if reading == "s":
            respelling = ("\u0e0b" + remainder,)  # ซ + rest
        elif reading == "thr":
            respelling = (text,)  # keep as-is; the cluster is a real ทฺร
        else:  # "taara"
            # ทอ + ระ + rest-rendered-as-syllable
            respelling = (
                "\u0e17\u0e2d",                      # ทอ
                "\u0e23\u0e30",                      # ระ
                remainder,
            )
        try:
            syllables = _derive_segments(respelling)
        except Exception:  # noqa: BLE001
            return None
        return PhonologicalWord(
            syllables=syllables,
            confidence=1.0,
            source="lexicon",
            raw=text,
        )

    def _render_rue(self, text: str, reading: str) -> PhonologicalWord | None:
        """Apply a M-730 ฤ reading by substituting into a derivable respelling."""
        idx = text.find("\u0e24")  # ฤ
        if idx < 0:
            idx = text.find("\u0e24\u0e45")  # ฤๅ
            if idx < 0:
                return None
            replaced = text[:idx] + "\u0e23\u0e37\u0e2d" + text[idx + 2:]  # รือ
        else:
            if reading == "rii":
                subst = "\u0e23\u0e35"         # รี
            elif reading == "ri":
                subst = "\u0e23\u0e34"         # ริ
            elif reading == "rer":
                subst = "\u0e40\u0e23\u0e2d"   # เรอ
            else:
                subst = "\u0e23\u0e37\u0e2d"   # รือ
            replaced = text[:idx] + subst + text[idx + 1:]
        # Re-tokenize the respelling and derive.
        tokens = tcc.tokenize(replaced)
        candidates = self._generator.generate(tokens)
        best: PhonologicalWord | None = None
        best_score = -1.0
        for cand in candidates:
            try:
                syllables = _derive_segments(cand.segments)
            except Exception:  # noqa: BLE001
                continue
            if cand.score > best_score:
                best_score = cand.score
                best = PhonologicalWord(
                    syllables=syllables,
                    confidence=cand.score,
                    source="lexicon",
                    raw=text,
                )
        return best


__all__ = ["PipelineRunner"]

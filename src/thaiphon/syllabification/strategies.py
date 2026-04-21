"""Candidate generation strategies.

Each strategy consumes a sequence of TCC tokens and emits zero or more
``SyllabificationCandidate`` instances. The ranker decides between them.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from typing import Protocol, runtime_checkable

from thaiphon.lexicons import cluster_overrides as cluster_overrides_lex
from thaiphon.lexicons import indic_detector as indic_detector_lex
from thaiphon.lexicons import o_leading as o_leading_lex
from thaiphon.model.candidate import SyllabificationCandidate
from thaiphon.model.letters import (
    HO_HIP,
    HOP_PRE_VOWELS,
    MAI_HAN_AKAT,
    O_ANG,
    PRE_VOWELS,
    RO_RUA,
    SARA_E,
    SARA_II,
    SARA_UEE,
    THANTHAKHAT,
    TONE_MARKS,
    VOWEL_CHARS,
    WO_WAEN,
    YO_YAK,
)
from thaiphon.tables import clusters as clusters_tbl
from thaiphon.tables import consonants as consonants_tbl
from thaiphon.tables.clusters import RARE_CLUSTERS as _RARE_CLUSTERS
from thaiphon.tables.leaders import H_LEADABLE_SONORANTS as _H_LEADABLE


def _is_bare_consonant_token(tok: str) -> bool:
    """A TCC token is a 'bare consonant' if it contains no vowel mark and
    is not a single pre-killed letter (like \u0e2a\u0e4c)."""
    if not tok:
        return False
    if any(ch in VOWEL_CHARS for ch in tok):
        return False
    if THANTHAKHAT in tok:
        # Tokens containing thanthakhat are typically killed finals — treat
        # as valid finals, not orphan consonants.
        return True
    # Only consonants (and maybe tone marks).
    return all(ch in consonants_tbl.CONSONANTS or ch == THANTHAKHAT for ch in tok)


def _starts_with_consonant(tok: str) -> bool:
    return bool(tok) and tok[0] in consonants_tbl.CONSONANTS


def _first_consonant(tok: str) -> str | None:
    """Return the first character of ``tok`` that is a Thai consonant."""
    for ch in tok:
        if ch in consonants_tbl.CONSONANTS:
            return ch
    return None


@runtime_checkable
class Strategy(Protocol):
    name: str

    def generate(
        self, tokens: Sequence[str]
    ) -> Iterator[SyllabificationCandidate]: ...


class SplitStrategy:
    """Treat each TCC token as its own syllable — minimum viable baseline."""

    name = "split"

    def generate(
        self, tokens: Sequence[str]
    ) -> Iterator[SyllabificationCandidate]:
        if not tokens:
            return
        yield SyllabificationCandidate(
            segments=tuple(tokens),
            strategy=self.name,
            score=0.5,
        )


class AoCarrierStrategy:
    """Merge ``C + อ`` and ``C + อ + coda`` patterns where อ is the
    post-base long-/ɔː/ vowel carrier (M-308-style).

    Typical TCC outputs: ``พ่ + อ``, ``ร้ + อ + น``, ``ข + อ + ง``. TCC
    hands back อ as its own token; syllabification must re-glue it to
    the preceding onset and (if present) the trailing coda.
    """

    name = "ao_carrier"

    def generate(
        self, tokens: Sequence[str]
    ) -> Iterator[SyllabificationCandidate]:
        if not tokens:
            return
        n = len(tokens)
        segments: list[str] = []
        i = 0
        changed = False
        while i < n:
            tok = tokens[i]
            # Need: a prior-or-current token containing a consonant, then
            # bare อ as its own token. This covers both bare-consonant
            # carriers (พ่+อ) and pre-vowel fragments (เรื+อ).
            if (
                i + 1 < n
                and tokens[i + 1] == O_ANG
                and any(ch in consonants_tbl.CONSONANTS for ch in tok)
            ):
                merged = tok + O_ANG
                j = i + 2
                # Swallow an optional trailing bare-consonant coda.
                if j < n and _is_bare_consonant_token(tokens[j]) and len(tokens[j]) == 1:
                    merged = merged + tokens[j]
                    j += 1
                segments.append(merged)
                i = j
                changed = True
                continue
            segments.append(tok)
            i += 1
        if not changed:
            return
        # Post-pass: fold trailing bare consonants into preceding syllables.
        _fold_trailing_finals(segments)
        yield SyllabificationCandidate(
            segments=tuple(segments),
            strategy=self.name,
            score=0.82,
        )


def _is_vowel_frame_glide(
    prev: str, ch: str, pre_vowel_seen: bool
) -> bool:
    """Return True when ``ch`` is acting as part of a composite vowel frame,
    not as a free coda consonant (R-CD-001..004):

    * เ…ี + ย  → ย belongs to the /iːə/ nucleus
    * เ…ื + อ  → อ belongs to the /ɯːə/ nucleus
    * …ั + ว   → ว belongs to the open /uːə/ nucleus
    """
    if ch == YO_YAK and prev == SARA_II and pre_vowel_seen:
        return True
    if ch == O_ANG and prev == SARA_UEE and pre_vowel_seen:
        return True
    return ch == WO_WAEN and prev == MAI_HAN_AKAT


def _has_coda_already(seg: str) -> bool:
    """A segment already has a coda if, after any pre-vowel + onset, there
    is an additional consonant following a *post-base* vowel mark. Pre-base
    vowels (เ แ โ ใ ไ) are positioned BEFORE the onset consonant and must
    not count as having "seen a vowel" for coda-detection purposes.

    Composite vowel frames require special handling: ย/อ/ว that are part
    of the centring-diphthong nuclei (R-CD-002..004) must not be mistaken
    for codas — otherwise trailing bare consonants cannot be folded in as
    the actual coda.
    """
    saw_vowel = False
    saw_consonant = False
    pre_vowel_seen = False
    prev_ch = ""
    for ch in seg:
        if ch in PRE_VOWELS and not saw_consonant:
            # Pre-base vowel: belongs to vowel composition, not post-onset.
            pre_vowel_seen = True
            prev_ch = ch
            continue
        if ch in VOWEL_CHARS:
            saw_vowel = True
            prev_ch = ch
            continue
        if ch in consonants_tbl.CONSONANTS:
            if saw_vowel:
                if _is_vowel_frame_glide(prev_ch, ch, pre_vowel_seen):
                    # Glide consumed by the nucleus; coda slot still open.
                    prev_ch = ch
                    continue
                return True
            saw_consonant = True
        prev_ch = ch
    return False


class MergeStrategy:
    """Merge trailing bare-consonant tokens into the preceding syllable as
    codas. A segment that already owns a coda is not extended further —
    this prevents ``['มี','นา','ค','ม']`` → ``['มี','นาคม']`` (two codas
    in one syllable); the PairSyllableStrategy handles that pattern.
    """

    name = "merge"

    def generate(
        self, tokens: Sequence[str]
    ) -> Iterator[SyllabificationCandidate]:
        if not tokens:
            return
        segments: list[str] = []
        for tok in tokens:
            if not segments:
                segments.append(tok)
                continue
            prev = segments[-1]
            prev_has_vowel = any(ch in VOWEL_CHARS for ch in prev)
            prev_is_single_cons = (
                len(prev) == 1 and prev in consonants_tbl.CONSONANTS
            )
            if (
                _is_bare_consonant_token(tok)
                and (prev_has_vowel or prev_is_single_cons)
                and not _has_coda_already(prev)
            ):
                segments[-1] = prev + tok
            else:
                segments.append(tok)
        if len(segments) == len(tokens):
            return
        # If the merge leaves a trailing orphan bare consonant (i.e. the
        # last segment is a stand-alone bare C), defer to PairSyllableStrategy
        # / LinkingStrategy — don't emit this candidate.
        if (
            len(segments) > 1
            and _is_bare_consonant_token(segments[-1])
            and len(segments[-1]) == 1
        ):
            return
        yield SyllabificationCandidate(
            segments=tuple(segments),
            strategy=self.name,
            score=0.8,
        )


def _fold_trailing_finals(segments: list[str]) -> bool:
    """Merge any trailing bare-consonant segment into the preceding
    vowel-bearing segment. Runs repeatedly until no more folds happen
    (so ``[..., V, C, C]`` → ``[..., VCC]`` when the penultimate C can
    itself be a coda-onto-coda target).

    Returns True if any fold happened.
    """
    changed = False
    i = 1
    while i < len(segments):
        prev = segments[i - 1]
        tok = segments[i]
        if (
            _is_bare_consonant_token(tok)
            and len(tok) == 1
            and any(ch in VOWEL_CHARS for ch in prev)
            and not _has_coda_already(prev)
        ):
            segments[i - 1] = prev + tok
            del segments[i]
            changed = True
            continue
        i += 1
    return changed


class ClusterStrategy:
    """Recognise true CC onsets (M-520) spanning two adjacent TCCs.

    Two shapes covered:
      - ``['C1', 'C2…']`` where C1 is a bare consonant and C2 begins the next
        token. The merge yields one syllable starting with the cluster.
      - ``['PRE+C1', 'C2+…']`` where PRE is a pre-vowel and (C1, C2) is a
        cluster pair — e.g. ``เปล่า`` → ``['เป', 'ล่า']`` folds back into
        ``['เปล่า']``.

    After the cluster pass, trailing bare-consonant tokens (glides ย/ว or
    stops) are folded into the preceding vowel-bearing syllable as codas —
    so ``['ก','ระ','ต่า','ย']`` → ``['กระ','ต่าย']`` rather than leaving
    ``ย`` as a stranded orphan (M-203 offglide handling).
    """

    name = "cluster"

    def generate(
        self, tokens: Sequence[str]
    ) -> Iterator[SyllabificationCandidate]:
        if not tokens or len(tokens) < 2:
            return
        segments: list[str] = []
        i = 0
        changed = False
        while i < len(tokens):
            tok = tokens[i]
            # Shape 1: bare C1 + following token starting with C2.
            if (
                i + 1 < len(tokens)
                and _is_bare_consonant_token(tok)
                and len(tok) == 1
                and _starts_with_consonant(tokens[i + 1])
                and clusters_tbl.is_cluster(tok, tokens[i + 1][0])
                and (tok, tokens[i + 1][0]) not in _RARE_CLUSTERS
            ):
                merged = tok + tokens[i + 1]
                j = i + 2
                # Fold trailing bare consonant as coda.
                if (
                    j < len(tokens)
                    and _is_bare_consonant_token(tokens[j])
                    and len(tokens[j]) == 1
                ):
                    merged = merged + tokens[j]
                    j += 1
                segments.append(merged)
                i = j
                changed = True
                continue
            # Shape 2: PRE + C1 token followed by token starting with C2.
            if (
                i + 1 < len(tokens)
                and len(tok) == 2
                and tok[0] in PRE_VOWELS
                and tok[1] in consonants_tbl.CONSONANTS
                and _starts_with_consonant(tokens[i + 1])
                and clusters_tbl.is_cluster(tok[1], tokens[i + 1][0])
                and (tok[1], tokens[i + 1][0]) not in _RARE_CLUSTERS
            ):
                merged = tok + tokens[i + 1]
                j = i + 2
                if (
                    j < len(tokens)
                    and _is_bare_consonant_token(tokens[j])
                    and len(tokens[j]) == 1
                ):
                    merged = merged + tokens[j]
                    j += 1
                segments.append(merged)
                i = j
                changed = True
                continue
            segments.append(tok)
            i += 1
        if not changed:
            return
        # Post-pass (only after a real cluster merge): fold trailing bare
        # consonants so ``['กระ','ต่า','ย']`` → ``['กระ','ต่าย']``.
        _fold_trailing_finals(segments)
        yield SyllabificationCandidate(
            segments=tuple(segments),
            strategy=self.name,
            score=0.85,
        )


class HLeadingStrategy:
    """M-500: if ห appears as a bare single-consonant TCC followed by a
    token whose first consonant is in the H-leadable sonorant set, merge
    them into one onset so that the second consonant's effective class
    becomes HC.

    Also handles the shape ``[PRE+ห, C+…]`` where a pre-vowel has been
    glued to the ห by TCC — e.g. ``ใหม่`` → ``['ให', 'ม่']``.

    After the ห+C merge, any trailing bare-consonant token is folded in
    as the coda of that syllable (so ``หนัง`` → one syllable ``หนัง``).
    """

    name = "h_leading"

    def _fold_coda(
        self, tokens: Sequence[str], segments: list[str], i: int
    ) -> int:
        """If the next token is a bare single consonant, append to the last
        merged segment as coda and return the advanced index."""
        if (
            i < len(tokens)
            and _is_bare_consonant_token(tokens[i])
            and len(tokens[i]) == 1
        ):
            segments[-1] = segments[-1] + tokens[i]
            return i + 1
        return i

    def generate(
        self, tokens: Sequence[str]
    ) -> Iterator[SyllabificationCandidate]:
        if not tokens or len(tokens) < 2:
            return
        segments: list[str] = []
        i = 0
        changed = False
        while i < len(tokens):
            tok = tokens[i]
            # Shape 1: bare ห + C.
            if (
                i + 1 < len(tokens)
                and tok == "ห"
                and _starts_with_consonant(tokens[i + 1])
                and tokens[i + 1][0] in _H_LEADABLE
            ):
                segments.append(tok + tokens[i + 1])
                i = self._fold_coda(tokens, segments, i + 2)
                changed = True
                continue
            # Shape 2: PRE + ห + next token starting with a sonorant.
            if (
                i + 1 < len(tokens)
                and len(tok) == 2
                and tok[0] in PRE_VOWELS
                and tok[1] == "ห"
                and _starts_with_consonant(tokens[i + 1])
                and tokens[i + 1][0] in _H_LEADABLE
            ):
                segments.append(tok + tokens[i + 1])
                i = self._fold_coda(tokens, segments, i + 2)
                changed = True
                continue
            segments.append(tok)
            i += 1
        if not changed:
            return
        yield SyllabificationCandidate(
            segments=tuple(segments),
            strategy=self.name,
            score=0.88,
        )


class OLeadingStrategy:
    """M-510: the closed 4-word อ-leading set. If the full orthographic input
    (concatenation of tokens) matches a set member, emit a one-syllable
    candidate so onset resolution routes it correctly."""

    name = "o_leading"

    def generate(
        self, tokens: Sequence[str]
    ) -> Iterator[SyllabificationCandidate]:
        if not tokens:
            return
        full = "".join(tokens)
        if full not in o_leading_lex.O_LEADING_WORDS:
            return
        yield SyllabificationCandidate(
            segments=(full,),
            strategy=self.name,
            score=0.95,
        )


class LinkingStrategy:
    """M-800/M-810: hidden /a/ insertion. Produces the same segmentation as
    SplitStrategy but with a higher baseline score and an explicit strategy
    tag so the derivation pipeline knows to treat single-consonant tokens
    as syllables with inherent /a/.

    Combined with MergeStrategy this covers the Pali/Sanskrit loan pattern:
    orphan consonants become linking syllables with /a/.
    """

    name = "linking"

    def generate(
        self, tokens: Sequence[str]
    ) -> Iterator[SyllabificationCandidate]:
        if not tokens:
            return
        # Emit only if at least one bare-consonant token needs /a/ inserted.
        if not any(_is_bare_consonant_token(t) and len(t) == 1 for t in tokens):
            return
        yield SyllabificationCandidate(
            segments=tuple(tokens),
            strategy=self.name,
            score=0.6,
        )


class IndicLearnedStrategy:
    """Productive rules: preserve the final short-vowel syllable of an
    Indic-learned word that would otherwise be collapsed by coda-folding,
    and keep any bare-consonant tokens *immediately before* it as their own
    linker /a/ syllables.

    The strategy is deliberately narrow. It fires only when the raw word
    ends in an Indic morphological ending (``-ติ``, ``-ธิ``, ``-ทิ``,
    ``-นะ``, ``-ระ``, ``-วะ``, ``-ภุ``, ``-กุ``, ``-ตุ``, ``-ยะ``,
    ``-ศะ``, ``-ษะ``, ``-ฑะ``, ``-ณะ``, ``-ธะ``, ``-มะ``) — i.e. when
    the orthography explicitly marks a preserved final short-vowel
    syllable. In that configuration MergeStrategy may absorb the bare
    consonant just before the final syllable as a coda, destroying the
    Indic reading; this strategy emits the non-folded alternative.

    The rest of the word (everything before the last vowel nucleus) is
    left to MergeStrategy's native coda/cluster handling by mirroring the
    merge shape: trailing bare-consonant runs ahead of the final syllable
    become their own linker segments; everything else is taken as-is.

    Score = 0.82, sitting between ``ClusterStrategy`` (0.85) — so valid
    native clusters still win — and ``MergeStrategy`` (0.80) — so the
    Indic-split reading outranks native coda-folding when fired.
    """

    name = "indic_learned"
    score = 0.82

    # Endings where the Indic-split reading is a NET win over native
    # coda-folding on the etalon corpus. Endings excluded here
    # (``-นะ``, ``-ธิ``, ``-ทิ``, ``-นะ``, ``-ยะ``, ``-ษะ``, ``-ธะ``,
    # ``-ฑะ``, ``-ภุ``, ``-กุ``, ``-ตุ``, ``-ศะ``, ``-มะ``, ``-วะ``) are
    # either net-losses or too-close-to-call; the curated Indic lexicon
    # remains responsible for them.
    # Endings the productive rule fires on. Selection follows empirical
    # per-ending win/loss analysis on the etalon corpus with the Volubilis
    # lexicon loaded: ``-ระ`` and ``-ณะ`` are net-positive; ``-ยะ``,
    # ``-นะ``, ``-วะ``, ``-ติ``, ``-ธิ``, ``-ทิ`` are net-negative or
    # too-close-to-call and the curated Indic lexicon remains
    # responsible for them.
    _FIRING_ENDINGS: frozenset[str] = frozenset(
        {
            "\u0e13\u0e30",  # ณะ
            "\u0e23\u0e30",  # ระ
        }
    )

    @classmethod
    def _has_firing_ending(cls, raw: str) -> bool:
        return any(raw.endswith(suf) for suf in cls._FIRING_ENDINGS)

    def generate(
        self, tokens: Sequence[str]
    ) -> Iterator[SyllabificationCandidate]:
        if not tokens or len(tokens) < 2:
            return
        raw = "".join(tokens)
        if not indic_detector_lex.is_indic_candidate(raw):
            return
        # Sentence-length guard: skip anything longer than 14 TCC tokens —
        # sentence-level etalon rows routinely end in the ``-นะ`` / ``-ระ``
        # particle and re-syllabifying them corpus-wide breaks more than it
        # fixes. A 14-token cap keeps normal Indic learned compounds
        # (``จุฬาลงกรณ์``, ``พิพิธภัณฑ์``) in range while excluding sentences.
        if len(tokens) > 14:
            return
        # Only fire for the explicit Indic final short-vowel shape. The
        # generic "Indic letter anywhere" signal is too weak to justify
        # undoing native coda-folding.
        if not self._has_firing_ending(raw):
            return
        # The last TCC token must be a vowel-bearing syllable (i.e. the
        # preserved final). If not, bail — the orthography does not show
        # a learned-reading final here.
        if not any(ch in _VOWEL_CHARS for ch in tokens[-1]):
            return
        # Build segments by running a conservative merge over tokens[:-1]
        # and keeping the final token as its own syllable. Merge rules:
        #   * fold a bare single consonant into the preceding vowel-bearing
        #     segment as a coda (standard M-301 behaviour), BUT
        #   * never fold the *last* bare-consonant in tokens[:-1] — that
        #     consonant is the onset of the preserved final-vowel syllable
        #     when it cluster-joins with the next token, or otherwise a
        #     linker /a/ syllable.
        body = list(tokens[:-1])
        final = tokens[-1]
        segments: list[str] = []
        # Apply MergeStrategy-compatible folding to body[:-1], keeping body[-1]
        # (the "pre-final" token) untouched.
        body_main = body[:-1]
        pre_final = body[-1] if body else None
        for tok in body_main:
            if not segments:
                segments.append(tok)
                continue
            prev = segments[-1]
            prev_has_vowel = any(ch in _VOWEL_CHARS for ch in prev)
            if (
                _is_bare_consonant_token(tok)
                and len(tok) == 1
                and prev_has_vowel
                and not _has_coda_already(prev)
            ):
                segments[-1] = prev + tok
            else:
                segments.append(tok)
        if pre_final is not None:
            segments.append(pre_final)
        segments.append(final)
        # Word-initial cluster fold: ``[C1, C2…]`` where (C1, C2[0]) is a
        # native cluster — merge so ปฏิ- / ปริ- keep the CR onset.
        if (
            len(segments) >= 2
            and _is_bare_consonant_token(segments[0])
            and len(segments[0]) == 1
            and _starts_with_consonant(segments[1])
            and clusters_tbl.is_cluster(segments[0], segments[1][0])
            and (segments[0], segments[1][0]) not in _RARE_CLUSTERS
        ):
            segments = [segments[0] + segments[1]] + segments[2:]
        # Drop if the final shape is identical to pure-TCC tokens AND has
        # no bare-consonant token — nothing to distinguish us from the
        # pure-split/split strategies.
        seg_tuple = tuple(segments)
        if seg_tuple == tuple(tokens) and not any(
            _is_bare_consonant_token(t) and len(t) == 1 for t in tokens
        ):
            return
        yield SyllabificationCandidate(
            segments=seg_tuple,
            strategy=self.name,
            score=self.score,
        )


_VOWEL_CHARS = VOWEL_CHARS


class PairSyllableStrategy:
    """Merge pairs of bare consonants into a single inherent-/o/ syllable
    (M-206 closed monosyllable). Example: ``['มี','นา','ค','ม']`` →
    ``['มี','นา','คม']``.

    Runs after MergeStrategy so the last-C-as-coda folding is preserved
    when preceding non-vowel tokens must also absorb codas. Also folds
    pairs that appear at word-initial position when a following vowel
    bearing token is present (M-206 pattern ``C1-C2-<vowel-syl>`` → the
    first C1+C2 form a closed inherent-/o/ syllable with C1 as onset
    and C2 as coda). Example: ``['ด','น','ตรี']`` → ``['ดน','ตรี']``.
    """

    name = "pair"

    def generate(
        self, tokens: Sequence[str]
    ) -> Iterator[SyllabificationCandidate]:
        if not tokens:
            return
        n = len(tokens)
        segments: list[str] = []
        i = 0
        changed = False
        pair_then_cluster_seen = False
        while i < n:
            tok = tokens[i]
            has_prev_vowel = (
                bool(segments) and any(ch in VOWEL_CHARS for ch in segments[-1])
            )
            # Lookahead for the M-206 pattern ``C1-C2-C3-V`` where (C3, Cn+1)
            # is a true cluster — i.e. ``ด-น-ต-รี`` where ตร forms the
            # onset cluster of the next syllable. C1+C2 becomes a closed
            # inherent-/o/ syllable and C3+… becomes the cluster-bearing
            # next syllable.
            pair_then_cluster = (
                i + 3 < n
                and _is_bare_consonant_token(tok)
                and len(tok) == 1
                and _is_bare_consonant_token(tokens[i + 1])
                and len(tokens[i + 1]) == 1
                and _is_bare_consonant_token(tokens[i + 2])
                and len(tokens[i + 2]) == 1
                and _starts_with_consonant(tokens[i + 3])
                and clusters_tbl.is_cluster(tokens[i + 2], tokens[i + 3][0])
                and (tokens[i + 2], tokens[i + 3][0]) not in _RARE_CLUSTERS
                and not has_prev_vowel
                and not segments  # at word-start only
            )
            if pair_then_cluster:
                segments.append(tok + tokens[i + 1])
                segments.append(tokens[i + 2] + tokens[i + 3])
                i += 4
                # Optional trailing bare-coda fold.
                if (
                    i < n
                    and _is_bare_consonant_token(tokens[i])
                    and len(tokens[i]) == 1
                ):
                    segments[-1] = segments[-1] + tokens[i]
                    i += 1
                pair_then_cluster_seen = True
                changed = True
                continue
            if (
                i + 1 < n
                and _is_bare_consonant_token(tok)
                and len(tok) == 1
                and _is_bare_consonant_token(tokens[i + 1])
                and len(tokens[i + 1]) == 1
                # Either (a) the preceding segment has a vowel, OR (b) we
                # are at word-start and a vowel-bearing token follows the
                # pair (M-206 closed-monosyllable at word onset).
                and (
                    has_prev_vowel
                    or (
                        not segments
                        and i + 2 < n
                        and any(ch in VOWEL_CHARS for ch in tokens[i + 2])
                    )
                )
            ):
                segments.append(tok + tokens[i + 1])
                i += 2
                changed = True
                continue
            segments.append(tok)
            i += 1
        if not changed:
            return
        # Post-pass: fold any remaining trailing bare consonants (glides
        # or final-coda candidates) into preceding vowel-bearing syllables.
        _fold_trailing_finals(segments)
        # pair_then_cluster captures a strictly better analysis than the
        # generic cluster strategy (which would strand the preceding bare
        # consonant); boost the score above cluster's 0.85.
        score = 0.86 if pair_then_cluster_seen else 0.79
        yield SyllabificationCandidate(
            segments=tuple(segments),
            strategy=self.name,
            score=score,
        )


class PreVowelHopStrategy:
    """M-521/M-522 Pali/Sanskrit pre-vowel hop: when a pre-vowel is
    orthographically glued to C1 but phonologically belongs to C2, C1 takes
    inherent short /a/ as its own linking syllable and the pre-vowel hops
    to the next consonant.

    Pattern: ``[PRE+C1, C2, C3]`` or ``[PRE+C1, C2, C3, ร]`` (with silent
    final ร common in Sanskrit-style spellings). Emits
    ``(C1, PRE+C2+C3)`` so the second syllable derives with C3 as coda.
    """

    name = "pre_vowel_hop"

    def generate(
        self, tokens: Sequence[str]
    ) -> Iterator[SyllabificationCandidate]:
        if len(tokens) < 3:
            return
        t0 = tokens[0]
        if len(t0) != 2 or t0[0] not in HOP_PRE_VOWELS:
            return
        c1 = t0[1]
        if c1 not in consonants_tbl.CONSONANTS or c1 == HO_HIP:
            return
        t1 = tokens[1]
        if len(t1) != 1 or t1 not in consonants_tbl.CONSONANTS:
            return
        c2 = t1
        if clusters_tbl.is_cluster(c1, c2):
            return
        pre = t0[0]
        # 3-token: [PRE+C1, C2, C3] → (C1, PRE+C2+C3). Skip when C2 is ร
        # (silent-ร merge is already the correct reading for that shape).
        if len(tokens) == 3 and len(tokens[2]) == 1:
            if c2 == RO_RUA:
                return
            c3 = tokens[2]
            if c3 not in consonants_tbl.CONSONANTS:
                return
            yield SyllabificationCandidate(
                segments=(c1, pre + c2 + c3),
                strategy=self.name,
                score=0.88,
            )
            return
        # 4-token: [PRE+C1, C2, C3, ร] → (C1, PRE+C2+C3) with ร silent.
        if (
            len(tokens) == 4
            and all(len(t) == 1 for t in tokens[1:])
            and tokens[3] == RO_RUA
        ):
            c3 = tokens[2]
            if c3 not in consonants_tbl.CONSONANTS:
                return
            yield SyllabificationCandidate(
                segments=(c1, pre + c2 + c3),
                strategy=self.name,
                score=0.88,
            )


class CompositeVowelFrameStrategy:
    """R-CD-001..004: recognise composite vowel frames as single syllables.

    Three templates are recognised when the TCC tokenizer splits the frame
    across multiple tokens:

    * Template 1 (R-CD-002): ``[เCี+ย, C]``  →  ``[เCียC]`` with nucleus /iːə/
    * Template 2 (R-CD-003): ``[เCื+อ, C]``  →  ``[เCือC]`` with nucleus /ɯːə/
    * Template 3 (R-CD-004): ``[C, ว, C]``   →  ``[CวC]``   with nucleus /uːə/

    Template 3 competes with the true-cluster reading of ขว / คว / กว as
    /kʰw/ or /kw/. When TCC already produces a single ``[Cว]`` token, that
    path is handled by ``ClusterStrategy`` and not re-emitted here. The
    ``TRUE_CLUSTER_WORDS`` guard keeps ``ควาย`` / ``กว่า`` on their cluster
    reading even though their TCC tokenization keeps ``[C+ว]`` together.
    """

    name = "composite_vowel_frame"

    @staticmethod
    def _strip_tone_marks(s: str) -> str:
        return "".join(ch for ch in s if ch not in TONE_MARKS)

    @classmethod
    def _is_onset_like(cls, tok: str) -> bool:
        """A TCC token is a bare onset (possibly with a tone mark) when,
        after stripping tone marks, it is a single consonant letter."""
        stripped = cls._strip_tone_marks(tok)
        return len(stripped) == 1 and stripped in consonants_tbl.CONSONANTS

    @classmethod
    def _template_3_match(cls, tokens: Sequence[str], i: int) -> int:
        """Match template 3 starting at index ``i`` — return number of tokens
        consumed (always 3) or 0 if no match.

        Shape required:
          * ``tokens[i]`` is a single consonant (with an optional tone mark)
          * ``tokens[i+1]`` is exactly "ว"
          * ``tokens[i+2]`` is a single bare consonant (the coda)
        """
        if i + 2 >= len(tokens):
            return 0
        onset_tok = tokens[i]
        mid_tok = tokens[i + 1]
        coda_tok = tokens[i + 2]
        if (
            cls._is_onset_like(onset_tok)
            and mid_tok == WO_WAEN
            and len(coda_tok) == 1
            and coda_tok in consonants_tbl.CONSONANTS
        ):
            return 3
        return 0

    @classmethod
    def _template_12_match(cls, tokens: Sequence[str], i: int) -> int:
        """Match templates 1 and 2: ``[เCีย, C]`` or ``[เCือ, C]`` where the
        second token is a single bare consonant (the coda). Tone marks
        embedded in the first token are ignored when pattern-matching.

        R-CENT-001 Case B guard: ``เCียว`` is NOT a centring diphthong —
        the phonology is /iː/ + /w/ glide (simple long /iː/ with a /w/
        offglide/coda), not /iːə/ + /w/. When the trailing coda token is
        ``ว``, reject the template-1 match so the word falls through to
        generic vowel resolution which produces the correct analysis.

        Returns 2 when matched, 0 otherwise.
        """
        if i + 1 >= len(tokens):
            return 0
        head = tokens[i]
        coda_tok = tokens[i + 1]
        if not head.startswith(SARA_E):
            return 0
        if not (len(coda_tok) == 1 and coda_tok in consonants_tbl.CONSONANTS):
            return 0
        stripped = cls._strip_tone_marks(head)
        if len(stripped) < 4:
            return 0
        last_two = stripped[-2:]
        if last_two == SARA_II + YO_YAK:
            # R-CENT-001 Case B: เ◌ียว → /iːw/, not /iːəw/. Let generic
            # vowel resolution handle it.
            if coda_tok == WO_WAEN:
                return 0
            return 2
        if last_two == SARA_UEE + O_ANG:
            return 2
        return 0

    def generate(
        self, tokens: Sequence[str]
    ) -> Iterator[SyllabificationCandidate]:
        if not tokens:
            return
        full = "".join(tokens)
        n = len(tokens)
        segments: list[str] = []
        i = 0
        changed = False
        while i < n:
            # Try template 1 / 2 first — they only consume 2 tokens.
            consumed = self._template_12_match(tokens, i)
            if consumed:
                segments.append(tokens[i] + tokens[i + 1])
                i += consumed
                changed = True
                continue
            # Template 3: C + ว + C. Guard against true-cluster words
            # (ขว/คว/กว family) where the /kʰw/-/kw/ reading is the
            # attested one.
            consumed = self._template_3_match(tokens, i)
            if consumed and full not in cluster_overrides_lex.TRUE_CLUSTER_WORDS:
                # Also skip when the (C, ว) pair is a true cluster and the
                # cluster-specific lexicon doesn't mark this as insert-u —
                # e.g. ``ขวาน``, ``กวาง``: those have a post-base vowel and
                # never hit this 3-token shape anyway, but belt-and-braces.
                onset_char = tokens[i]
                if (
                    clusters_tbl.is_cluster(onset_char, WO_WAEN)
                    and full not in cluster_overrides_lex.INSERT_U_WORDS
                ):
                    # Let ClusterStrategy own this shape.
                    segments.append(tokens[i])
                    i += 1
                    continue
                segments.append(tokens[i] + tokens[i + 1] + tokens[i + 2])
                i += consumed
                changed = True
                continue
            segments.append(tokens[i])
            i += 1
        if not changed:
            return
        # Apply the same cluster-folding pass used by ClusterStrategy so the
        # frame-recognising candidate doesn't strand word-initial bare
        # consonants that actually start a true CC onset. Example:
        # ``['ก','ระ','เทีย','ม']`` → frame-fold gives
        # ``['ก','ระ','เทียม']`` and the cluster pass turns it into
        # ``['กระ','เทียม']`` — the correct two-syllable analysis.
        _apply_initial_cluster(segments)
        # Post-pass: any trailing bare consonant still hanging around gets
        # folded into the preceding vowel-bearing syllable as a coda.
        _fold_trailing_finals(segments)
        # If the result still contains a word-initial bare consonant that
        # couldn't be absorbed, skip — other strategies produce a cleaner
        # analysis and we don't want our higher score to mask theirs.
        if _has_leading_bare_consonant(segments):
            return
        yield SyllabificationCandidate(
            segments=tuple(segments),
            strategy=self.name,
            score=0.90,
        )


def _has_leading_bare_consonant(segments: list[str]) -> bool:
    if len(segments) < 2:
        return False
    first = segments[0]
    return _is_bare_consonant_token(first) and len(first) == 1


def _apply_initial_cluster(segments: list[str]) -> bool:
    """In-place: if ``segments`` begins with ``[C, C2…]`` and (C, C2[0]) is
    a true cluster, merge the two segments. Mirrors the cluster-merge shape
    used by ``ClusterStrategy`` but only at the word-initial position."""
    if len(segments) < 2:
        return False
    first, second = segments[0], segments[1]
    if not (_is_bare_consonant_token(first) and len(first) == 1):
        return False
    if not _starts_with_consonant(second):
        return False
    if not clusters_tbl.is_cluster(first, second[0]):
        return False
    if (first, second[0]) in _RARE_CLUSTERS:
        return False
    segments[0] = first + second
    del segments[1]
    return True


class DFStrategy:
    """M-820: double-function. When a bare consonant sits between a vowel-
    bearing segment and another vowel-bearing segment, treat it as BOTH
    the coda of the preceding syllable AND the onset of a new syllable
    with hidden /a/. Implemented by duplicating the bare consonant.

    Respects M-821: never the last consonant of the word; never word-initial;
    ง usually excluded.
    """

    name = "df"

    def generate(
        self, tokens: Sequence[str]
    ) -> Iterator[SyllabificationCandidate]:
        n = len(tokens)
        if n < 3:
            return
        segments: list[str] = []
        i = 0
        changed = False
        while i < n:
            tok = tokens[i]
            # Can this bare consonant be a DF pivot?
            is_df_candidate = (
                i > 0
                and i < n - 1
                and _is_bare_consonant_token(tok)
                and len(tok) == 1
                and tok != "ง"  # M-821 exclusion
                # Preceding must be vowel-bearing (an actual syllable so far).
                and any(ch in VOWEL_CHARS for ch in tokens[i - 1])
                # Following must be a vowel-bearing token (a new syllable).
                and any(ch in VOWEL_CHARS for ch in tokens[i + 1])
            )
            if is_df_candidate:
                # Fold `tok` into the previous segment as its coda, AND emit
                # it again as a standalone onset for the next syllable.
                if segments:
                    segments[-1] = segments[-1] + tok
                segments.append(tok)
                changed = True
                i += 1
                continue
            segments.append(tok)
            i += 1
        if not changed:
            return
        yield SyllabificationCandidate(
            segments=tuple(segments),
            strategy=self.name,
            score=0.65,
        )


__all__ = [
    "AoCarrierStrategy",
    "ClusterStrategy",
    "CompositeVowelFrameStrategy",
    "DFStrategy",
    "HLeadingStrategy",
    "IndicLearnedStrategy",
    "LinkingStrategy",
    "MergeStrategy",
    "OLeadingStrategy",
    "PairSyllableStrategy",
    "PreVowelHopStrategy",
    "SplitStrategy",
    "Strategy",
]

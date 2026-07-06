"""Candidate generation strategies.

Each strategy consumes a sequence of TCC tokens and emits zero or more
``SyllabificationCandidate`` instances. The ranker decides between them.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from typing import Protocol, runtime_checkable

from thaiphon.lexicons import cluster_overrides as cluster_overrides_lex
from thaiphon.lexicons import df_stems as df_stems_lex
from thaiphon.lexicons import indic_detector as indic_detector_lex
from thaiphon.lexicons import o_leading as o_leading_lex
from thaiphon.model.candidate import SyllabificationCandidate
from thaiphon.model.letters import (
    HO_HIP,
    HOP_PRE_VOWELS,
    MAI_HAN_AKAT,
    MAITAIKHU,
    O_ANG,
    PRE_VOWELS,
    RO_RUA,
    SARA_A,
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
        segments, changed = _glue_ao_carriers(tokens)
        if not changed:
            return
        # Post-pass: fold trailing bare consonants into preceding syllables.
        _fold_trailing_finals(segments)
        yield SyllabificationCandidate(
            segments=tuple(segments),
            strategy=self.name,
            score=0.82,
        )


class LeaderClosedStrategy:
    """อักษรนำ leader + closed syllable for three bare consonants.

    ``C1 + C2 + C3`` with no written vowel anywhere reads as the leader
    ``C1`` (inherent /a/, one syllable) followed by a closed ``C2C3``
    syllable (``C2`` onset, inherent /o/, ``C3`` coda): ถนน → ถ + นน
    (tha-nohn), ขนม → ข + นม (kha-nohm), กมล → ก + มล (ga-mon).

    The boundary is ``C1 | C2C3`` — the leader is the single first
    consonant, not ``C1C2 | C3``. Skipped when ``C1+C2`` or ``C2+C3`` is a
    true onset cluster (ปรก, นคร), which belong to the cluster path.
    """

    name = "leader_closed"

    def generate(
        self, tokens: Sequence[str]
    ) -> Iterator[SyllabificationCandidate]:
        if len(tokens) != 3:
            return
        if not all(
            len(t) == 1 and t in consonants_tbl.CONSONANTS for t in tokens
        ):
            return
        c1, c2, c3 = tokens
        if clusters_tbl.is_cluster(c1, c2) or clusters_tbl.is_cluster(c2, c3):
            return
        yield SyllabificationCandidate(
            segments=(c1, c2 + c3),
            strategy=self.name,
            score=0.75,
        )


class FinalClusterCodaStrategy:
    """A word-final true cluster ``C + ร`` sitting after a vowel-bearing
    syllable is a coda, not an onset cluster: the first consonant is the
    coda and the trailing ร is silent.

    บัตร → บัต (bat), สมัคร → ส + มัค (sa-mak), สมุทร → ส + มุท (sa-moot),
    เนตร → เนต (naeht). The guard ``tokens[-3]`` must carry a vowel keeps
    นคร (น has no vowel; คร is a real /-ɔːn/ syllable) on the cluster path.

    The silent-ร reading is further gated by the head consonant. For
    ก/ข/ค/พ heads it applies only when the anchor ends in a dangling ั
    that MUST take the head as its coda (จักร → jak, สมัคร → sa-mak);
    with a complete anchor vowel the head starts a final /Cɔːn/ syllable
    instead (M-308: นิกร → ni-gaawn, อากร, ประชากร) — the etalon corpus
    splits exactly this way (silent กร/คร without ั: zero occurrences),
    and the live TLC engine reads nonce ทิกร/ลัตร the same way. ต/ป/ท
    heads keep the silent-ร reading regardless of the anchor (มิตร,
    สูตร, บุตร — 159:1 for ตร; สมุทร for ทร).

    A few Sanskrit forms keep the cluster as a syllable (อัคร → ak-khra);
    those are rare, not derivable from spelling, and accepted as misses.
    """

    name = "final_cluster_coda"

    _AWN_HEADS = frozenset({"ก", "ข", "ค", "พ"})

    def generate(
        self, tokens: Sequence[str]
    ) -> Iterator[SyllabificationCandidate]:
        if len(tokens) < 3:
            return
        if tokens[-1] != RO_RUA:
            return
        head = tokens[-2]
        if not (len(head) == 1 and head in consonants_tbl.CONSONANTS):
            return
        if not clusters_tbl.is_cluster(head, RO_RUA):
            return
        anchor = tokens[-3]
        if not any(ch in VOWEL_CHARS for ch in anchor):
            return
        if head in self._AWN_HEADS:
            anchor_core = "".join(
                ch for ch in anchor if ch not in TONE_MARKS
            )
            if not anchor_core.endswith(MAI_HAN_AKAT):
                # Complete anchor vowel → the /Cɔːn/ reading; leave the
                # word to the cluster + M-308 path.
                return
        segments = list(tokens[:-2])
        segments[-1] = segments[-1] + head  # fold first cluster C as coda
        # trailing ร dropped (silent). Scored above PreVowelHopStrategy and
        # ClusterStrategy (both ≤0.88) so the coda reading wins word-finally
        # even when a pre-vowel (เ◌) invites a competing hop parse (เนตร).
        yield SyllabificationCandidate(
            segments=tuple(segments),
            strategy=self.name,
            score=0.90,
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


def _has_coda_already(seg: str, *, karan_transparent: bool = False) -> bool:
    """A segment already has a coda if, after any pre-vowel + onset, there
    is an additional consonant following a *post-base* vowel mark. Pre-base
    vowels (เ แ โ ใ ไ) are positioned BEFORE the onset consonant and must
    not count as having "seen a vowel" for coda-detection purposes.

    Pre-base-vowel segments also close their coda slot when a second
    consonant follows the onset and the pair is NOT a native onset
    cluster. ``เทพ``, ``เกม``, ``เบญ``, ``แดง`` are CVC syllables with the
    second consonant serving as coda; ``เปล``, ``เกร``, ``เคล`` are still
    coda-less because the pair forms a true onset cluster. Without this
    check a following bare consonant would be wrongly folded onto the
    already-complete syllable (``เทพ`` + ม → ``เทพม`` live-/m/-coda).

    Composite vowel frames require special handling: ย/อ/ว that are part
    of the centring-diphthong nuclei must not be mistaken for codas —
    otherwise trailing bare consonants cannot be folded in as the actual
    coda.

    Three orthographic elements are transparent to frame structure and
    must not disturb the walk:

    * tone marks — เที่ยว carries ่ between ี and ย; the ย is still the
      frame glide, so the mark cannot become the "previous character";
    * การันต์-killed consonants (ล์ in กอล์ฟ, ร์ in ยอร์ก) — silent, so
      they neither occupy the coda slot nor close it. This transparency
      is opt-in (``karan_transparent``): it is only sound when deciding
      whether the *word-final* token may fold in as a coda (กอล์ฟ,
      นิวยอร์ก). Mid-word, a bare consonant after a killed tail is almost
      always the onset of the next syllable (คาร์บอมบ์ = คาร์ + บอมบ์),
      so the killed consonant must keep the slot closed there;
    * post-base อ after an onset consonant with no other vowel — that อ
      *is* the vowel (/ɔː/), so a consonant after it is a true coda
      (นอน) while the อ itself never is (กอ, ยอร์).
    """
    saw_vowel = False
    pre_vowel_seen = False
    last_consonant: str | None = None
    prev_ch = ""
    n = len(seg)
    i = 0
    while i < n:
        ch = seg[i]
        if ch in TONE_MARKS or ch == THANTHAKHAT:
            i += 1
            continue
        if ch in PRE_VOWELS and last_consonant is None:
            # Pre-base vowel: belongs to vowel composition, not post-onset.
            pre_vowel_seen = True
            prev_ch = ch
            i += 1
            continue
        if ch in VOWEL_CHARS:
            saw_vowel = True
            prev_ch = ch
            i += 1
            continue
        if ch in consonants_tbl.CONSONANTS:
            # การันต์-killed consonant (possibly with an interleaved tone
            # mark) is silent — skip it entirely when transparency is on.
            if karan_transparent:
                j = i + 1
                while j < n and seg[j] in TONE_MARKS:
                    j += 1
                if j < n and seg[j] == THANTHAKHAT:
                    i = j + 1
                    continue
            if ch == O_ANG and not saw_vowel and last_consonant is not None:
                # Post-base อ acting as the /ɔː/ vowel.
                saw_vowel = True
                prev_ch = ch
                i += 1
                continue
            if saw_vowel:
                if _is_vowel_frame_glide(prev_ch, ch, pre_vowel_seen):
                    # Glide consumed by the nucleus; coda slot still open.
                    prev_ch = ch
                    i += 1
                    continue
                return True
            if pre_vowel_seen and last_consonant is not None:
                is_onset_cluster = (
                    clusters_tbl.is_cluster(last_consonant, ch)
                    and (last_consonant, ch) not in _RARE_CLUSTERS
                )
                # A following ร is systematically ambiguous in Thai: it may
                # be the second of a true cluster (handled above), a silent
                # leader (``ทร``, ``ศร``, ``ซร``, ``สร``), or a rare
                # productive loan cluster. None of these are codas, so never
                # close the coda slot when ``ch == ร`` — let the downstream
                # reader disambiguate.
                # ห leading a low-class sonorant (อักษรนำ: เหลียว, เหนียว,
                # เหมือน) is an onset pair, not consonant + coda — ห is
                # never a Thai coda, so keep the coda slot open.
                is_h_leading = last_consonant == HO_HIP and ch in _H_LEADABLE
                if not is_onset_cluster and not is_h_leading and ch != RO_RUA:
                    return True
            last_consonant = ch
            prev_ch = ch
            i += 1
            continue
        prev_ch = ch
        i += 1
    return False


def _is_vowel_bearing(seg: str) -> bool:
    """True when the segment already contains a vowel nucleus — either an
    explicit vowel mark or the post-base อ carrier (/ɔː/) sitting after an
    onset consonant (กอ, ยอร์, กอล์). A word-initial อ is an onset, not a
    nucleus."""
    if any(ch in VOWEL_CHARS for ch in seg):
        return True
    prev_is_consonant = False
    for ch in seg:
        if ch in TONE_MARKS or ch == THANTHAKHAT:
            continue
        if ch == O_ANG and prev_is_consonant:
            return True
        prev_is_consonant = ch in consonants_tbl.CONSONANTS
    return False


def _coda_steals_next_onset(coda: str, nxt: str | None) -> bool:
    """A candidate coda consonant must stay unabsorbed when it forms an
    onset unit (true cluster or ห + sonorant อักษรนำ pair) with the first
    character of the following token — เหลอหลา is เหลอ + หลา, not เหลอห +
    ลา; เกลอขวัญ keeps the ขว cluster. Only a token that itself BEGINS
    with a consonant can claim the coda: one beginning with a pre-vowel
    starts a fresh syllable on its own (วอกแวก: ก can never join แว's
    onset because the แ is written first)."""
    if not nxt or nxt[0] not in consonants_tbl.CONSONANTS:
        return False
    first = nxt[0]
    return (
        clusters_tbl.is_cluster(coda, first)
        and (coda, first) not in _RARE_CLUSTERS
    ) or (coda == HO_HIP and first in _H_LEADABLE)


def _absorb_ao_frame(
    tokens: Sequence[str], j: int, merged: str
) -> tuple[str, int, bool]:
    """After an onset merge, absorb a following post-base อ carrier and an
    optional single-consonant coda: ``กล + อ + ง`` → ``กลอง``, ``หน่ + อ +
    ย`` → ``หน่อย``. A tone mark stranded as its own token between onset
    and carrier is absorbed too (mirroring AoCarrierStrategy).

    The coda is NOT absorbed when it plausibly belongs to the *next*
    syllable as onset material — see ``_coda_steals_next_onset`` (ห is
    additionally never a Thai coda at all).

    Returns ``(segment, next_index, absorbed)``.
    """
    n = len(tokens)
    k = j
    tone_piece = ""
    if k < n and len(tokens[k]) == 1 and tokens[k] in TONE_MARKS:
        tone_piece = tokens[k]
        k += 1
    if k < n and tokens[k] == O_ANG:
        merged = merged + tone_piece + O_ANG
        k += 1
        if (
            k < n
            and _is_bare_consonant_token(tokens[k])
            and len(tokens[k]) == 1
            and tokens[k] not in (O_ANG, HO_HIP)
            and not _coda_steals_next_onset(
                tokens[k], tokens[k + 1] if k + 1 < n else None
            )
        ):
            merged = merged + tokens[k]
            k += 1
        return merged, k, True
    return merged, j, False


def _glue_ao_carriers(tokens: Sequence[str]) -> tuple[list[str], bool]:
    """Scan the token stream and re-glue every post-base อ carrier to its
    onset: ``C + อ (+ coda)`` (พ่+อ, ร้+อ+น, ข+อ+ง), the เ◌ือ frame with a
    stranded tone mark (``เสื | ้ | อ``), and the short เ◌อะ carrier
    (เล + อะ). TCC hands back อ/อะ as their own tokens because no Thai
    Character Cluster pattern captures these frames; syllabification must
    reassemble them before onset/coda reasoning can work.

    Shared by AoCarrierStrategy (whose candidate this scan used to be)
    and ClusterStrategy (as a pre-pass, so cluster words containing an
    อ frame elsewhere — คองเกรส, แถบคอเสื้อ — still get the frame glued
    inside the cluster-bearing candidate).

    Returns ``(segments, changed)``.
    """
    n = len(tokens)
    segments: list[str] = []
    i = 0
    changed = False
    while i < n:
        tok = tokens[i]
        if i + 1 < n and any(ch in consonants_tbl.CONSONANTS for ch in tok):
            k = i + 1
            tone_piece = ""
            if (
                len(tokens[k]) == 1
                and tokens[k] in TONE_MARKS
                and k + 1 < n
            ):
                tone_piece = tokens[k]
                k += 1
            carrier = tokens[k]
            if carrier == O_ANG:
                merged = tok + tone_piece + O_ANG
                j = k + 1
                # Swallow an optional trailing bare-consonant coda.
                if (
                    j < n
                    and _is_bare_consonant_token(tokens[j])
                    and len(tokens[j]) == 1
                    and tokens[j] not in (O_ANG, HO_HIP)
                    and not _coda_steals_next_onset(
                        tokens[j], tokens[j + 1] if j + 1 < n else None
                    )
                ):
                    merged = merged + tokens[j]
                    j += 1
                segments.append(merged)
                i = j
                changed = True
                continue
            # Short อะ carrier: the open /ɤ/ frame เ + C + อ + ะ
            # (เลอะ, เถอะ, เปรอะ). ะ closes the syllable — no coda.
            if carrier == O_ANG + SARA_A and tok.startswith(SARA_E):
                segments.append(tok + tone_piece + carrier)
                i = k + 1
                changed = True
                continue
        segments.append(tok)
        i += 1
    return segments, changed


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
        for idx, tok in enumerate(tokens):
            if not segments:
                segments.append(tok)
                continue
            is_final = idx == len(tokens) - 1
            prev = segments[-1]
            # Relaxed nucleus checks (post-base อ as vowel, การันต์-killed
            # tails as transparent) let a bare consonant fold onto
            # segments like ยอร์/กอล์/อาร์ (นิวยอร์ก, กอล์ฟ, อาร์กติก).
            # They are gated: when the NEXT token is a vowel-less อ-initial
            # chunk, this consonant is that frame's onset and must fold
            # FORWARD instead (คาร์บอมบ์ = คาร์ + บ + อมบ์ → คาร์ + บอมบ์);
            # when the next token is a bare consonant the two likely form
            # an inherent-/o/ pair or linker (ชาร์ลสตัน = ชาร์ + ลส + ตัน).
            # Only a single consonant can fold this way — a longer bare
            # token is a whole syllable, not a coda (วอร์ + ซอว์).
            nxt = tokens[idx + 1] if not is_final else None
            unsafe_next = nxt is not None and (
                (nxt[0] == O_ANG and not any(ch in VOWEL_CHARS for ch in nxt))
                or (_is_bare_consonant_token(nxt) and len(nxt) == 1)
            )
            prev_has_vowel = any(ch in VOWEL_CHARS for ch in prev)
            relaxed_fold_ok = (
                len(tok) == 1
                and not unsafe_next
                and (prev_has_vowel or _is_vowel_bearing(prev))
                and not _has_coda_already(prev, karan_transparent=True)
            )
            # An "onset-only" previous segment is a single consonant,
            # optionally carrying a tone mark, with no written vowel and
            # no coda yet. It must still be eligible to absorb a bare-C
            # coda — otherwise a closed monosyllable whose onset bears a
            # tone mark (e.g. ก้ง) would split into two syllables.
            prev_is_onset_only = (
                (len(prev) == 1 and prev in consonants_tbl.CONSONANTS)
                or (
                    len(prev) == 2
                    and prev[0] in consonants_tbl.CONSONANTS
                    and prev[1] in TONE_MARKS
                )
            )
            if _is_bare_consonant_token(tok) and (
                (
                    (prev_has_vowel or prev_is_onset_only)
                    and not _has_coda_already(prev)
                )
                or relaxed_fold_ok
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

    The relaxed nucleus checks (post-base อ as vowel, การันต์-killed
    tails as transparent) apply only when folding the *last* segment —
    a word-final bare consonant has no other role than coda (กอล์ฟ,
    นิวยอร์ก), whereas a mid-word one is usually the next onset.

    Returns True if any fold happened.
    """
    changed = False
    i = 1
    while i < len(segments):
        prev = segments[i - 1]
        tok = segments[i]
        is_final = i == len(segments) - 1
        prev_has_nucleus = (
            _is_vowel_bearing(prev)
            if is_final
            else any(ch in VOWEL_CHARS for ch in prev)
        )
        # A word-final bare consonant may also pair with an onset-only
        # (single consonant, optional tone mark) predecessor to close an
        # inherent-/o/ syllable: ตรวจค้น's ค้ + น → ค้น. Word-final only —
        # mid-word pairs are PairSyllableStrategy's scored decision.
        prev_is_onset_only = is_final and (
            (len(prev) == 1 and prev in consonants_tbl.CONSONANTS)
            or (
                len(prev) == 2
                and prev[0] in consonants_tbl.CONSONANTS
                and prev[1] in TONE_MARKS
            )
        )
        if (
            _is_bare_consonant_token(tok)
            and len(tok) == 1
            and (prev_has_nucleus or prev_is_onset_only)
            and not _has_coda_already(prev, karan_transparent=is_final)
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
        # Pre-pass: re-glue post-base อ carriers so a word containing BOTH
        # a true cluster and an อ frame gets both in one candidate
        # (คองเกรส → คอง + เกรส). Without this the cluster candidate wins
        # the ranking while the อ frame stays shredded.
        glued, _ = _glue_ao_carriers(tokens)
        tokens = glued
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
                # A following bare อ is the /ɔː/ carrier for this cluster
                # onset (กลอง, ตรอก) — absorb it plus an optional coda.
                merged, j, absorbed = _absorb_ao_frame(tokens, j, merged)
                # Otherwise fold a trailing bare consonant as coda — but
                # never onto a syllable that already owns one (ครอบ + ค)
                # and never one that opens the next syllable (เกลอ + ขวัญ).
                if (
                    not absorbed
                    and j < len(tokens)
                    and _is_bare_consonant_token(tokens[j])
                    and len(tokens[j]) == 1
                    and not _has_coda_already(merged)
                    and not _coda_steals_next_onset(
                        tokens[j],
                        tokens[j + 1] if j + 1 < len(tokens) else None,
                    )
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
                merged, j, absorbed = _absorb_ao_frame(tokens, j, merged)
                if (
                    not absorbed
                    and j < len(tokens)
                    and _is_bare_consonant_token(tokens[j])
                    and len(tokens[j]) == 1
                    and not _has_coda_already(merged)
                    and not _coda_steals_next_onset(
                        tokens[j],
                        tokens[j + 1] if j + 1 < len(tokens) else None,
                    )
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

    @staticmethod
    def _fold_stranded_codas(segments: list[str]) -> None:
        """Fold bare-consonant segments into their preceding vowel-bearing
        syllable so the ห-merge candidate doesn't strand codas elsewhere in
        the word (จังหวัด: ['จั','ง','หวัด'] → ['จัง','หวัด']; หนองคาย:
        ['หนอง','คา','ย'] → ['หนอง','คาย']).

        One exception: mid-word ร stays put — its linking-/ra/ reading
        wins there (สาธารณะ keeps สา-ธา-ระ-ณะ, not ธาร)."""
        i = 1
        while i < len(segments):
            prev = segments[i - 1]
            tok = segments[i]
            is_final = i == len(segments) - 1
            if (
                _is_bare_consonant_token(tok)
                and len(tok) == 1
                and (is_final or tok != RO_RUA)
                and any(ch in VOWEL_CHARS for ch in prev)
                and not _has_coda_already(prev, karan_transparent=is_final)
            ):
                segments[i - 1] = prev + tok
                del segments[i]
                continue
            i += 1

    def _fold_coda(
        self, tokens: Sequence[str], segments: list[str], i: int
    ) -> int:
        """If the next token is the post-base อ carrier (หลอด, หน่อย),
        absorb it plus an optional coda; otherwise, if it is a bare single
        consonant, append it as the coda. Returns the advanced index."""
        merged, j, absorbed = _absorb_ao_frame(tokens, i, segments[-1])
        if absorbed:
            segments[-1] = merged
            return j
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
        self._fold_stranded_codas(segments)
        # A run of exactly TWO word-initial bare consonants before a real
        # syllable is a closed inherent-/o/ pair (นกหวีด → นก + หวีด). A
        # longer run stays split — its first consonant is usually an
        # อักษรนำ leader (ตลบหลัง keeps ต + ลบ + หลัง).
        if (
            len(segments) >= 3
            and _is_bare_consonant_token(segments[0])
            and len(segments[0]) == 1
            and _is_bare_consonant_token(segments[1])
            and len(segments[1]) == 1
            and not (
                _is_bare_consonant_token(segments[2])
                and len(segments[2]) == 1
            )
            and not clusters_tbl.is_cluster(segments[0], segments[1])
        ):
            segments[0] = segments[0] + segments[1]
            del segments[1]
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
        # Exactly four bare consonants form two inherent-/o/ pairs:
        # มงคล → มง + คล (mohng-khon). Skipped when the first two form a
        # true cluster (พรหม stays on the cluster path). The second pair
        # may itself be a cluster-shaped letter pair — word-finally with
        # no vowel anywhere the closed-pair reading wins (คล = khon).
        if (
            n == 4
            and all(
                _is_bare_consonant_token(t) and len(t) == 1 for t in tokens
            )
            # A non-initial bare อ is the /ɔː/ vowel carrier, not pair
            # material (ตลอด is ต + ลอด, not ตล + อด). Word-initial อ is
            # a real onset (อดทน = อด + ทน).
            and O_ANG not in tokens[1:]
            and not clusters_tbl.is_cluster(tokens[0], tokens[1])
            and not clusters_tbl.is_cluster(tokens[1], tokens[2])
        ):
            yield SyllabificationCandidate(
                segments=(tokens[0] + tokens[1], tokens[2] + tokens[3]),
                strategy=self.name,
                score=0.86,
            )
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


# Consonants a pre-vowel may hop onto: the sonorants that take อักษรนำ
# linking readings, plus ด (แสดง → sa-daaeng).
_HOP_MIDDLES: frozenset[str] = frozenset("งญณนมยรลวด")


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
        pre = t0[0]
        # Centring-frame middle token: the pre-vowel belongs to a เ◌ือ
        # frame on the next consonant, written before the อักษรนำ leader
        # C1 — เสมือน → ส + เมือน (sa-meuuan). Hop the whole tail under the
        # pre-vowel so the centring syllable re-forms.
        if (
            SARA_UEE in t1
            and O_ANG in t1
            and t1[0] in consonants_tbl.CONSONANTS
            and not clusters_tbl.is_cluster(c1, t1[0])
        ):
            yield SyllabificationCandidate(
                segments=(c1, pre + "".join(tokens[1:])),
                strategy=self.name,
                score=0.88,
            )
            return
        # เสด็จ-type: the hopped syllable carries ◌็ on its onset
        # (เ + ส + ด็ + จ → ส + เด็จ). The MAITAIKHU rides the token, so
        # allow the 2-char shape ``C + ็`` for the middle token.
        if (
            len(tokens) == 3
            and len(t1) == 2
            and t1[0] in consonants_tbl.CONSONANTS
            and t1[1] == MAITAIKHU
            and t1[0] in _HOP_MIDDLES
            and len(tokens[2]) == 1
            and tokens[2] in consonants_tbl.CONSONANTS
            and not clusters_tbl.is_cluster(c1, t1[0])
        ):
            yield SyllabificationCandidate(
                segments=(c1, pre + t1 + tokens[2]),
                strategy=self.name,
                score=0.88,
            )
            return
        if len(t1) != 1 or t1 not in consonants_tbl.CONSONANTS:
            return
        c2 = t1
        if clusters_tbl.is_cluster(c1, c2):
            return
        # 3-token: [PRE+C1, C2, C3] → (C1, PRE+C2+C3). Skip when C2 is ร
        # (silent-ร merge is already the correct reading for that shape).
        # In this shape the hopped-to onset is a sonorant (or ด, as in
        # แสดง) in every attested hop reading; a non-sonorant C2 keeps
        # the pre-vowel on C1 (โกสน = โก + สน, เบตง = เบ + ตง). The
        # 4-token silent-ร shape below is NOT gated this way (เกษตร
        # hops onto ษ).
        if len(tokens) == 3 and len(tokens[2]) == 1:
            if c2 == RO_RUA:
                return
            if c2 not in _HOP_MIDDLES:
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
    def _template_3_extended_match(
        cls, tokens: Sequence[str], i: int
    ) -> tuple[str, ...] | None:
        """The ◌ว◌ frame behind a two-consonant onset — two shapes over
        four tokens ``[C1, C2, ว, C]``:

        * ``C1 == ห`` leading a sonorant: one ห-led syllable — หลวง,
          หมวก (ห + ล + ว + ง → ``หลวง``).
        * ``(C1, C2)`` NOT a cluster: อักษรนำ leader split — สงวน,
          ขบวน (ส + ง + ว + น → ``ส`` + ``งวน``); the leader keeps its
          inherent /a/ and shifts the class of the next onset.

        A true-cluster ``(C1, C2)`` pair is NOT handled here: the 3-token
        template at ``i+1`` plus the cluster fold already assembles it
        (ตรวจ, ครวญ). Returns the segments to append, or None.
        """
        if i + 3 >= len(tokens):
            return None
        c1, c2, mid, coda = (
            tokens[i], tokens[i + 1], tokens[i + 2], tokens[i + 3]
        )
        if mid != WO_WAEN:
            return None
        if not (len(c1) == 1 and c1 in consonants_tbl.CONSONANTS):
            return None
        if not cls._is_onset_like(c2):
            return None
        if not (len(coda) == 1 and coda in consonants_tbl.CONSONANTS):
            return None
        if c1 == HO_HIP and c2[0] in _H_LEADABLE:
            return (c1 + c2 + mid + coda,)
        if c1 != HO_HIP and not clusters_tbl.is_cluster(c1, c2[0]):
            return (c1, c2 + mid + coda)
        return None

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
        leader_split = False
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
            # attested one. Lexicon lookups are scoped to the frame window
            # so compounds resolve per-syllable (ควบคุม checks ``ควบ``);
            # the whole-input form is kept for single-word entries.
            consumed = self._template_3_match(tokens, i)
            if consumed:
                window = tokens[i] + tokens[i + 1] + tokens[i + 2]
                is_true_cluster = (
                    full in cluster_overrides_lex.TRUE_CLUSTER_WORDS
                    or window in cluster_overrides_lex.TRUE_CLUSTER_WORDS
                )
                if not is_true_cluster:
                    onset_char = tokens[i]
                    if clusters_tbl.is_cluster(onset_char, WO_WAEN):
                        if (
                            full not in cluster_overrides_lex.INSERT_U_WORDS
                            and window
                            not in cluster_overrides_lex.INSERT_U_WORDS
                        ):
                            # Let ClusterStrategy own this shape.
                            segments.append(tokens[i])
                            i += 1
                            continue
                        # INSERT_U reading of an ambiguous ขว/คว/กว window:
                        # respell with ◌ั so derivation takes the ◌ัว
                        # nucleus branch instead of the cluster (mirrors
                        # the whole-word path in the pipeline runner).
                        segments.append(
                            tokens[i]
                            + MAI_HAN_AKAT
                            + tokens[i + 1]
                            + tokens[i + 2]
                        )
                        i += consumed
                        changed = True
                        continue
                    segments.append(window)
                    i += consumed
                    changed = True
                    continue
            # Template 3 behind a two-consonant onset: ห-leading (หลวง)
            # or อักษรนำ leader split (สงวน → ส + งวน).
            ext = self._template_3_extended_match(tokens, i)
            if ext is not None:
                if len(ext) == 2:
                    leader_split = True
                segments.extend(ext)
                i += 4
                changed = True
                continue
            segments.append(tokens[i])
            i += 1
        if not changed:
            return
        # Apply the same cluster-folding pass used by ClusterStrategy so the
        # frame-recognising candidate doesn't strand bare consonants that
        # actually start a true CC onset — word-initially
        # (``['ก','ระ','เทียม']`` → ``['กระ','เทียม']``) or before a
        # mid-word frame (``['โอ','ด','ค','รวญ']`` → the ค joins รวญ).
        _apply_clusters(segments)
        # Post-pass: any trailing bare consonant still hanging around gets
        # folded into the preceding vowel-bearing syllable as a coda.
        _fold_trailing_finals(segments)
        # If the result still contains a word-initial bare consonant that
        # couldn't be absorbed, skip — other strategies produce a cleaner
        # analysis and we don't want our higher score to mask theirs. An
        # อักษรนำ leader split is the exception: its word-initial bare
        # consonant is the intended inherent-/a/ leader syllable.
        if not leader_split and _has_leading_bare_consonant(segments):
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


def _apply_clusters(segments: list[str]) -> bool:
    """In-place: wherever a bare consonant segment precedes a segment whose
    first consonant forms a true cluster with it, merge the two. Mirrors
    the cluster-merge shape used by ``ClusterStrategy`` over already-built
    segments.

    Word-initially the merge is unconditional (กระเทียม). Mid-word it is
    kept on a tight leash — the bare consonant is usually the CODA of the
    syllable before it, or an Indic linker, not an onset:

    * the previous segment must not be an open vowel-bearing syllable
      (ฝากลวดลาย keeps ก as ฝาก's coda; ภาพลวงตา keeps พ as ภาพ's), and
    * the following segment must be a bare CวC frame produced by the
      ว-nucleus templates (โอดครวญ merges ค + รวญ; อันตราย keeps its
      ต linker because รา is not such a frame).
    """
    changed = False
    i = 0
    while i + 1 < len(segments):
        first, second = segments[i], segments[i + 1]
        if (
            _is_bare_consonant_token(first)
            and len(first) == 1
            and _starts_with_consonant(second)
            and clusters_tbl.is_cluster(first, second[0])
            and (first, second[0]) not in _RARE_CLUSTERS
        ):
            mid_word_ok = True
            if i > 0:
                prev = segments[i - 1]
                prev_open_syllable = _is_vowel_bearing(
                    prev
                ) and not _has_coda_already(prev)
                mid_word_ok = not prev_open_syllable
            if mid_word_ok:
                segments[i] = first + second
                del segments[i + 1]
                changed = True
                continue
        i += 1
    return changed


class DFStrategy:
    """M-820: double-function. When a bare consonant sits between a vowel-
    bearing segment and another vowel-bearing segment, treat it as BOTH
    the coda of the preceding syllable AND the onset of a new syllable
    with hidden /a/. Implemented by duplicating the bare consonant.

    Respects M-821: never the last consonant of the word; never word-initial;
    ง usually excluded.

    Two candidates can come out of this strategy. The generic all-pivots
    reading keeps its low score — double-function is the marked case and
    plain coda-folding usually wins. When a pivot sits on a known
    re-sounding Sanskrit stem (วิทยา, ราชการ — see
    :mod:`thaiphon.lexicons.df_stems`) a second candidate duplicating
    only the confirmed pivots is emitted at a winning score.
    """

    name = "df"

    @staticmethod
    def _stem_at(tokens: Sequence[str], i: int) -> str:
        return tokens[i - 1] + tokens[i]

    # Letters sharing an initial sound with the pivot: when the next
    # token opens with one of these, the doubling is already written out
    # (พัทธสีมา = พัท + ธ…, เวชชาชีวะ = เวช + ชา…) and the pivot must not
    # re-sound a second time.
    _HOMORGANIC: dict[str, frozenset[str]] = {
        "ท": frozenset("ทธฑฒถฐ"),
        "ช": frozenset("ชฌฉ"),
        "ก": frozenset("กขคฆ"),
        "ป": frozenset("ปพภผ"),
        "ต": frozenset("ตฏถฐทธ"),
        "ส": frozenset("สศษซ"),
    }

    def _confirmed_candidate(
        self, tokens: Sequence[str], confirmed: set[int]
    ) -> SyllabificationCandidate:
        n = len(tokens)
        segments: list[str] = []
        # Linker duplicates stand alone as inherent-/a/ syllables — they
        # must not absorb following material (เอกชน = เอก + ก + ชน, the
        # ช belongs to the ชน pair, not to the linker ก).
        exempt: set[int] = set()
        for i, tok in enumerate(tokens):
            if i in confirmed and segments:
                segments[-1] = segments[-1] + tok
                exempt.add(len(segments))
                segments.append(tok)
                continue
            if not segments:
                segments.append(tok)
                continue
            prev = segments[-1]
            prev_is_onset_only = (
                len(prev) == 1 and prev in consonants_tbl.CONSONANTS
            ) or (
                len(prev) == 2
                and prev[0] in consonants_tbl.CONSONANTS
                and prev[1] in TONE_MARKS
            )
            # Ordinary codas elsewhere in the word fold as MergeStrategy
            # would: ราชการ → ['ราช','ช','กา','ร'] → ['ราช','ช','การ'];
            # พิพิธภัณฑ์'s trailing ณฑ์ folds onto ภั. A consonant that
            # forms an onset unit with the next token stays put so the
            # C+ร tail keeps its own syllable (ศุลกากร → …กา + กร).
            if (
                _is_bare_consonant_token(tok)
                and (len(segments) - 1) not in exempt
                and (
                    any(ch in VOWEL_CHARS for ch in prev)
                    or prev_is_onset_only
                )
                and not _has_coda_already(prev)
                and not (
                    len(tok) == 1
                    and _coda_steals_next_onset(
                        tok, tokens[i + 1] if i + 1 < n else None
                    )
                )
            ):
                segments[-1] = prev + tok
            else:
                segments.append(tok)
        return SyllabificationCandidate(
            segments=tuple(segments),
            strategy=self.name,
            score=0.87,
        )

    def generate(
        self, tokens: Sequence[str]
    ) -> Iterator[SyllabificationCandidate]:
        n = len(tokens)
        if n < 3:
            return
        confirmed = {
            i
            for i in range(1, n - 1)
            if _is_bare_consonant_token(tokens[i])
            and len(tokens[i]) == 1
            and (
                any(ch in VOWEL_CHARS for ch in tokens[i - 1])
                # Word-initial bare pair: the stem syllable is the
                # inherent-/o/ pair itself (มลทิน = มล + ล + ทิน).
                or (
                    i == 1
                    and _is_bare_consonant_token(tokens[0])
                    and len(tokens[0]) == 1
                )
            )
            and tokens[i + 1][0] in consonants_tbl.CONSONANTS
            # A following อ opens a vowel-initial syllable — no linker
            # (เอกอัคร stays aehk + ak…).
            and tokens[i + 1][0] != O_ANG
            # Doubling already written out → don't re-sound.
            and tokens[i + 1][0]
            not in self._HOMORGANIC.get(tokens[i], frozenset())
            and df_stems_lex.is_df_stem(self._stem_at(tokens, i))
        }
        if confirmed:
            yield self._confirmed_candidate(tokens, confirmed)
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

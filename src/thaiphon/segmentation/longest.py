# SPDX-FileCopyrightText: 2016-2026 PyThaiNLP Project
# SPDX-FileType: SOURCE
# SPDX-License-Identifier: Apache-2.0
# Adapted by the thaiphon contributors. Source: https://github.com/PyThaiNLP/pythainlp
# Changes: inlined thai_tonemarks and word_dict_trie; uses thaiphon's bundled lexicons
# as the dictionary. Pure stdlib; no runtime dependencies.
"""Dictionary-based longest-matching Thai word segmentation.

Implementation is based on the codes from Patorn Utenpattanun. The upstream
pythainlp version depends on pythainlp's ``Trie``, ``word_dict_trie`` and
``thai_tonemarks`` utilities. Here the trie is replaced by a simple
dict-of-dicts built from thaiphon's bundled lexicons, and ``thai_tonemarks``
is inlined as a frozen constant.
"""

from __future__ import annotations

import functools
import re
from collections.abc import Iterable

from thaiphon.lexicons import (
    ai_20,
    irregular,
    length_overrides,
    o_leading,
    ror_ror,
    royal,
    rue,
    silent_h,
    thor,
)
from thaiphon.model.letters import (
    LAKKHANGYAO,
    MAI_YAMOK,
    NIKHAHIT,
    PAIYANNOI,
    POST_BASE_VOWEL_MARKS,
    THANTHAKHAT,
    TONE_MARKS,
)
from thaiphon.tokenization import tcc

# A trie node is a dict mapping single characters to child nodes; the
# terminal marker key "$" maps to an empty dict. We model it with a
# loose type alias because mypy doesn't support recursive aliases
# without the experimental flag.
TrieNode = dict[str, "TrieNode"]

# Inlined from pythainlp: four Thai tone marks.
_THAI_TONEMARKS: frozenset[str] = TONE_MARKS

_FRONT_DEP_CHAR: frozenset[str] = (
    POST_BASE_VOWEL_MARKS | frozenset({LAKKHANGYAO, THANTHAKHAT, NIKHAHIT})
)
_REAR_DEP_CHAR: frozenset[str] = frozenset(
    {"\u0e31", "\u0e37", "\u0e40", "\u0e41", "\u0e42", "\u0e43", "\u0e44", NIKHAHIT}
)
_TRAILING_CHAR: frozenset[str] = frozenset({MAI_YAMOK, PAIYANNOI})  # ๆ ฯ

_RE_NONTHAI: re.Pattern[str] = re.compile(r"[A-Za-z\d]*")


# ---------------------------------------------------------------------------
# Trie built once from bundled lexicons.
# ---------------------------------------------------------------------------


def _default_words() -> frozenset[str]:
    parts: list[Iterable[str]] = [
        ai_20.AI_20_WORDS,
        o_leading.O_LEADING_WORDS,
        silent_h.SILENT_H_WORDS,
        thor.THOR_READINGS.keys(),
        rue.RUE_READINGS.keys(),
        ror_ror.ROR_ROR_WORDS.keys(),
        length_overrides.LENGTH_OVERRIDES.keys(),
        irregular.IRREGULAR_WORDS.keys(),
        irregular.IRREGULAR_SYLLABLES.keys(),
        royal.entries().keys(),
    ]
    words: set[str] = set()
    for p in parts:
        for w in p:
            if w:
                words.add(w)
    return frozenset(words)


def _build_trie(words: Iterable[str]) -> TrieNode:
    root: TrieNode = {}
    for w in words:
        node: TrieNode = root
        for ch in w:
            child: TrieNode = node.setdefault(ch, {})
            node = child
        node["$"] = {}  # terminal marker
    return root


@functools.cache
def _default_trie() -> TrieNode:
    return _build_trie(_default_words())


def _trie_contains(trie: TrieNode, word: str) -> bool:
    node: TrieNode = trie
    for ch in word:
        nxt = node.get(ch)
        if nxt is None:
            return False
        node = nxt
    return "$" in node


# ---------------------------------------------------------------------------
# Longest-matching tokenizer.
# ---------------------------------------------------------------------------


def _search_nonthai(text: str) -> str | None:
    m = _RE_NONTHAI.search(text)
    if not m:
        return None
    g = m.group(0)
    return g.lower() if g else None


def _is_next_word_valid(trie: TrieNode, text: str, begin_pos: int) -> bool:
    rest = text[begin_pos:].strip()
    if not rest:
        return True
    if _search_nonthai(rest):
        return True
    return any(
        _trie_contains(trie, rest[:pos]) for pos in range(1, len(rest) + 1)
    )


def _longest_matching(trie: TrieNode, text: str, begin_pos: int) -> str:
    rest = text[begin_pos:]
    m = _search_nonthai(rest)
    if m:
        return m

    word: str | None = None
    word_valid: str | None = None
    for pos in range(1, len(rest) + 1):
        w = rest[:pos]
        if _trie_contains(trie, w):
            word = w
            if _is_next_word_valid(trie, rest, pos):
                word_valid = w
    if word is None:
        return ""
    chosen = word_valid or word
    end = len(chosen)
    if end < len(rest) and rest[end] in _TRAILING_CHAR:
        return rest[: end + 1]
    return chosen


def _tokenize(trie: TrieNode, text: str) -> list[str]:
    begin = 0
    n = len(text)
    tokens: list[str] = []
    statuses: list[bool] = []   # True = KNOWN, False = UNKNOWN
    while begin < n:
        match = _longest_matching(trie, text, begin)
        if not match:
            ch = text[begin]
            attach = (
                begin != 0
                and not ch.isspace()
                and (
                    ch in _FRONT_DEP_CHAR
                    or text[begin - 1] in _REAR_DEP_CHAR
                    or ch in _THAI_TONEMARKS
                    or (statuses and not statuses[-1])
                )
            )
            if attach:
                tokens[-1] += ch
                statuses[-1] = False
            else:
                tokens.append(ch)
                statuses.append(False)
            begin += 1
        else:
            if begin != 0 and text[begin - 1] in _REAR_DEP_CHAR and tokens:
                tokens[-1] += match
            else:
                tokens.append(match)
                statuses.append(True)
            begin += len(match)

    # Fallback: unknown singleton tokens of Thai script get broken into
    # TCC chunks rather than individual code points. This keeps downstream
    # derivation happy on out-of-dictionary Thai.
    refined: list[str] = []
    for tok in tokens:
        if len(tok) == 1 and _is_thai(tok) and not tok.isspace():
            refined.append(tok)
            continue
        refined.append(tok)

    # Group consecutive whitespace.
    grouped: list[str] = []
    for tok in refined:
        if tok.isspace() and grouped and grouped[-1].isspace():
            grouped[-1] += tok
        else:
            grouped.append(tok)
    return grouped


def _is_thai(s: str) -> bool:
    return all("\u0e00" <= ch <= "\u0e7f" for ch in s)


# ---------------------------------------------------------------------------
# Public API.
# ---------------------------------------------------------------------------


def segment(
    text: str,
    custom_dict: Iterable[str] | None = None,
) -> tuple[str, ...]:
    """Dictionary-based longest-matching Thai word segmentation.

    Tokens not found in the dictionary are further broken into TCC chunks
    (via :mod:`thaiphon.tokenization.tcc`) so that downstream derivation
    receives well-formed units even on out-of-dictionary input.
    """
    if not text or not isinstance(text, str):
        return ()

    trie = _default_trie() if custom_dict is None else _build_trie(custom_dict)

    raw_tokens = _tokenize(trie, text)

    # Split unknown Thai runs into TCC chunks.
    out: list[str] = []
    for tok in raw_tokens:
        if (
            tok
            and _is_thai(tok)
            and not _trie_contains(trie, tok)
            and len(tok) > 1
        ):
            chunks = tcc.tokenize(tok)
            if chunks:
                out.extend(chunks)
            else:
                out.append(tok)
        else:
            out.append(tok)
    return tuple(out)


__all__ = ["segment"]

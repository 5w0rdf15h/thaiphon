"""M-710/711/712/770: expand Thai abbreviations and numerals."""

from __future__ import annotations

from thaiphon.model.letters import MAI_YAMOK, PAIYANNOI

_LAKKHANGYAO = "\u0e2f\u0e25\u0e2f"
_LAKKHANGYAO_EXPANSION = "\u0e41\u0e25\u0e30\u0e2d\u0e37\u0e48\u0e19\u0e46"

_THAI_DIGIT_WORDS: dict[str, str] = {
    "\u0e50": "\u0e28\u0e39\u0e19\u0e22\u0e4c",  # ๐ ศูนย์
    "\u0e51": "\u0e2b\u0e19\u0e36\u0e48\u0e07",  # ๑ หนึ่ง
    "\u0e52": "\u0e2a\u0e2d\u0e07",  # ๒ สอง
    "\u0e53": "\u0e2a\u0e32\u0e21",  # ๓ สาม
    "\u0e54": "\u0e2a\u0e35\u0e48",  # ๔ สี่
    "\u0e55": "\u0e2b\u0e49\u0e32",  # ๕ ห้า
    "\u0e56": "\u0e2b\u0e01",  # ๖ หก
    "\u0e57": "\u0e40\u0e08\u0e47\u0e14",  # ๗ เจ็ด
    "\u0e58": "\u0e41\u0e1b\u0e14",  # ๘ แปด
    "\u0e59": "\u0e40\u0e01\u0e49\u0e32",  # ๙ เก้า
}


def _is_thai_word_char(ch: str) -> bool:
    cp = ord(ch)
    # Thai block U+0E01..U+0E7F, excluding the abbreviation/repetition marks themselves.
    return 0x0E01 <= cp <= 0x0E7F and ch not in (MAI_YAMOK, PAIYANNOI)


def expand_mai_yamok(text: str) -> str:
    """Repeat the preceding Thai word for each ๆ (M-710)."""
    if MAI_YAMOK not in text:
        return text
    out: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == MAI_YAMOK:
            # Find preceding contiguous Thai word in `out`.
            k = len(out) - 1
            while k >= 0 and _is_thai_word_char(out[k]):
                k -= 1
            preceding = "".join(out[k + 1:])
            if preceding:
                out.append(preceding)
            else:
                out.append(ch)
            i += 1
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def expand_paiyannoi(text: str) -> str:
    """M-711: ฯ proper-noun abbreviation. Requires a lexicon to expand.

    No-op in this phase; pipeline passes ฯ through untouched.
    """
    # TODO(phaseN): expand via a proper-noun abbreviation lexicon.
    return text


def expand_lakkhangyao(text: str) -> str:
    """M-712: replace ฯลฯ with และอื่นๆ."""
    if _LAKKHANGYAO not in text:
        return text
    return text.replace(_LAKKHANGYAO, _LAKKHANGYAO_EXPANSION)


def spell_numerals(text: str) -> str:
    """M-770: spell out isolated single Thai digits.

    Multi-digit runs are left unchanged: positional reading is non-trivial
    and a wrong expansion is worse than none.
    """
    # TODO(phaseN): handle multi-digit numerals via positional Thai number words.
    if not any(ch in _THAI_DIGIT_WORDS for ch in text):
        return text
    out: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch in _THAI_DIGIT_WORDS:
            j = i
            while j < n and text[j] in _THAI_DIGIT_WORDS:
                j += 1
            run = text[i:j]
            if len(run) == 1:
                out.append(_THAI_DIGIT_WORDS[run])
            else:
                out.append(run)
            i = j
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def expand(text: str) -> str:
    """Apply all M-710/711/712/770 expansions in order."""
    if not text:
        return text
    text = expand_mai_yamok(text)
    text = expand_lakkhangyao(text)
    text = expand_paiyannoi(text)
    text = spell_numerals(text)
    return text

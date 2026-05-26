"""M-740: รร (ร-หัน) three-pattern readings.

Each entry maps a word to a tuple of phonemic-syllable respellings. The
pipeline uses these to short-circuit derivation for known forms. A
productive core also handles common ``C + รร + C'`` and ``C + รร``
patterns via the derivation path (see the orthography reader); this
lexicon covers high-frequency learned/Sanskritic forms that cannot be
derived generically.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

from thaiphon.tables import consonants as consonants_tbl

# word → tuple of phonemic-syllable respellings (Thai orthography that the
# reader can derive cleanly; one tuple entry per final syllable).
_ROR_ROR: dict[str, tuple[str, ...]] = {
    # Reading 1: รร + final → /a/ + final.
    "\u0e18\u0e23\u0e23\u0e21": ("\u0e17\u0e31\u0e21",),             # ธรรม → ทัม
    "\u0e01\u0e23\u0e23\u0e21": ("\u0e01\u0e31\u0e21",),             # กรรม → กัม
    "\u0e27\u0e23\u0e23\u0e04": ("\u0e27\u0e31\u0e04",),             # วรรค → วัค
    "\u0e27\u0e23\u0e23\u0e13": ("\u0e27\u0e31\u0e19",),             # วรรณ → วัน
    "\u0e1e\u0e23\u0e23\u0e13": ("\u0e1e\u0e31\u0e19",),             # พรรณ → พัน
    "\u0e01\u0e23\u0e23\u0e13": ("\u0e01\u0e31\u0e19",),             # กรรณ → กัน
    # Starter lexicon. Compounds that are derivable piece-wise are handled
    # by the general engine; these are the forms whose derivation is
    # unreliable without lexicalisation.
    "\u0e2a\u0e38\u0e1e\u0e23\u0e23\u0e13": (                         # สุพรรณ → สุ + พัน
        "\u0e2a\u0e38",
        "\u0e1e\u0e31\u0e19",
    ),
    "\u0e27\u0e23\u0e23\u0e13\u0e22\u0e38\u0e01\u0e15\u0e4c": (        # วรรณยุกต์
        "\u0e27\u0e31\u0e19",                                         # วัน
        "\u0e19\u0e30",                                               # นะ
        "\u0e22\u0e38\u0e01",                                         # ยุก
    ),
    "\u0e27\u0e31\u0e12\u0e19\u0e18\u0e23\u0e23\u0e21": (              # วัฒนธรรม
        "\u0e27\u0e31\u0e12",                                         # วัฒ
        "\u0e17\u0e30",                                               # ทะ
        "\u0e19\u0e30",                                               # นะ
        "\u0e17\u0e31\u0e21",                                         # ทัม
    ),
    "\u0e18\u0e23\u0e23\u0e21\u0e40\u0e19\u0e35\u0e22\u0e21": (        # ธรรมเนียม
        "\u0e17\u0e31\u0e21",
        "\u0e40\u0e19\u0e35\u0e22\u0e21",
    ),
    "\u0e18\u0e23\u0e23\u0e21\u0e0a\u0e32\u0e15\u0e34": (              # ธรรมชาติ
        "\u0e17\u0e31\u0e21",
        "\u0e21\u0e30",
        "\u0e0a\u0e32\u0e15",
    ),
    "\u0e01\u0e23\u0e23\u0e21\u0e2a\u0e34\u0e17\u0e18\u0e34\u0e4c": (  # กรรมสิทธิ์
        "\u0e01\u0e31\u0e21",
        "\u0e21\u0e30",
        "\u0e2a\u0e34\u0e17",
    ),
    # Reading 2: รร with no final → /-an/.
    "\u0e01\u0e23\u0e23\u0e44\u0e01\u0e23": (                         # กรรไกร
        "\u0e01\u0e31\u0e19",
        "\u0e44\u0e01\u0e23",
    ),
    "\u0e1a\u0e23\u0e23\u0e17\u0e38\u0e01": (                         # บรรทุก
        "\u0e1a\u0e31\u0e19",
        "\u0e17\u0e38\u0e01",
    ),
    "\u0e1a\u0e23\u0e23\u0e08\u0e38": (                               # บรรจุ
        "\u0e1a\u0e31\u0e19",
        "\u0e08\u0e38",
    ),
    # Reading 3: รร with no final, linking-ra pattern.
    "\u0e2a\u0e23\u0e23\u0e40\u0e2a\u0e23\u0e34\u0e0d": (             # สรรเสริญ
        "\u0e2a\u0e31\u0e19",
        "\u0e23\u0e30",
        "\u0e40\u0e2a\u0e23\u0e34\u0e0d",
    ),
    "\u0e20\u0e23\u0e23\u0e22\u0e32": (                               # ภรรยา
        "\u0e1e\u0e31\u0e19",
        "\u0e23\u0e30",
        "\u0e22\u0e32",
    ),
}

ROR_ROR_WORDS: Mapping[str, tuple[str, ...]] = MappingProxyType(_ROR_ROR)


def lookup(word: str) -> tuple[str, ...] | None:
    return _ROR_ROR.get(word)


_RO_RUA = "ร"
_RR = _RO_RUA + _RO_RUA           # รร (ร-หัน)
_MAI_HAN_AKAT = "ั"          # ◌ั
_NO_NU = "น"                 # น


def rewrite_productive(text: str) -> str:
    """Productive M-740 รร rewrite for words not in the starter lexicon.

    Applies the two regular ร-หัน readings so arbitrary ``C + รร`` words
    derive correctly without being individually lexicalised:

    * ``C + รร + <single word-final consonant>`` → ``C + ◌ั + <consonant>``
      — the consonant is the syllable coda: มรรค → มัค (mak), สรรพ → สับ
      (sap), ธรรม → ธัม (tham).
    * ``C + รร + <a following syllable>`` (or ``C + รร`` word-final) →
      ``C + ◌ัน + <rest>`` — รร closes the syllable as /-an/: กรรชิด →
      กันชิด (gan-chit), บรรจุ → บันจุ, สรร → สัน.

    The irregular "linking-ra" reading (สรรเสริญ → สัน-ระ-เสิน, ภรรยา →
    พัน-ระ-ยา) is not productive and stays in the lexicon; the pipeline
    consults :func:`lookup` first and only falls back to this rewrite.

    Returns ``text`` unchanged when it contains no ``รร``.
    """
    if _RR not in text:
        return text
    out: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        if (
            text[i : i + 2] == _RR
            and out
            and out[-1] in consonants_tbl.CONSONANTS
        ):
            rest = text[i + 2 :]
            if len(rest) == 1 and rest in consonants_tbl.CONSONANTS:
                # รร + lone final consonant → /a/ with that consonant coda.
                out.append(_MAI_HAN_AKAT)
            else:
                # รร before a new syllable (or at word end) → /-an/.
                out.append(_MAI_HAN_AKAT + _NO_NU)
            i += 2
            continue
        out.append(text[i])
        i += 1
    return "".join(out)


__all__ = ["ROR_ROR_WORDS", "lookup", "rewrite_productive"]

"""M-410: the master tone matrix.

Key = (EffectiveClass, SyllableType, VowelLength, ToneMark).
Value = Tone.

Productive combinations only. Tone marks ◌๊ (mai-tri) and ◌๋ (mai-jattawa)
are productive for MC only (M-402); HC and LC with these marks are
non-standard and intentionally absent from the table — `lookup` raises
DerivationError on such queries.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

from thaiphon.errors import DerivationError
from thaiphon.model.enums import EffectiveClass as C
from thaiphon.model.enums import SyllableType as S
from thaiphon.model.enums import Tone as T
from thaiphon.model.enums import ToneMark as M
from thaiphon.model.enums import VowelLength as L

_MatrixKey = tuple[C, S, L, M]

_MATRIX: dict[_MatrixKey, T] = {}


def _add(cls: C, stype: S, vlen: L, mark: M, tone: T) -> None:
    _MATRIX[(cls, stype, vlen, mark)] = tone


# A — No tone mark, LIVE syllable
for _len in (L.LONG, L.SHORT):
    _add(C.MID, S.LIVE, _len, M.NONE, T.MID)
    _add(C.HIGH, S.LIVE, _len, M.NONE, T.RISING)
    _add(C.LOW, S.LIVE, _len, M.NONE, T.MID)

# B — No tone mark, DEAD syllable
for _len in (L.LONG, L.SHORT):
    _add(C.MID, S.DEAD, _len, M.NONE, T.LOW)
    _add(C.HIGH, S.DEAD, _len, M.NONE, T.LOW)
_add(C.LOW, S.DEAD, L.LONG, M.NONE, T.FALLING)
_add(C.LOW, S.DEAD, L.SHORT, M.NONE, T.HIGH)

# C — ◌่ (mai-ek): applies across live/dead, short/long
for _stype in (S.LIVE, S.DEAD):
    for _len in (L.LONG, L.SHORT):
        _add(C.MID, _stype, _len, M.MAI_EK, T.LOW)
        _add(C.HIGH, _stype, _len, M.MAI_EK, T.LOW)
        _add(C.LOW, _stype, _len, M.MAI_EK, T.FALLING)

# D — ◌้ (mai-tho)
for _stype in (S.LIVE, S.DEAD):
    for _len in (L.LONG, L.SHORT):
        _add(C.MID, _stype, _len, M.MAI_THO, T.FALLING)
        _add(C.HIGH, _stype, _len, M.MAI_THO, T.FALLING)
        _add(C.LOW, _stype, _len, M.MAI_THO, T.HIGH)

# E — ◌๊ (mai-tri): productive for MC only
for _stype in (S.LIVE, S.DEAD):
    for _len in (L.LONG, L.SHORT):
        _add(C.MID, _stype, _len, M.MAI_TRI, T.HIGH)

# F — ◌๋ (mai-jattawa): productive for MC only
for _stype in (S.LIVE, S.DEAD):
    for _len in (L.LONG, L.SHORT):
        _add(C.MID, _stype, _len, M.MAI_JATTAWA, T.RISING)


MATRIX: Mapping[_MatrixKey, T] = MappingProxyType(_MATRIX)


def lookup(cls: C, stype: S, vlen: L, mark: M) -> T:
    try:
        return _MATRIX[(cls, stype, vlen, mark)]
    except KeyError as exc:
        raise DerivationError(
            f"no tone for (class={cls.name}, type={stype.name}, "
            f"length={vlen.name}, mark={mark.name})"
        ) from exc

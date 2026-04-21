# SPDX-FileCopyrightText: 2016-2026 PyThaiNLP Project
# SPDX-FileType: SOURCE
# SPDX-License-Identifier: Apache-2.0
# Adapted by the thaiphon contributors. Source: https://github.com/PyThaiNLP/pythainlp
# Changes: simplified to a tokens-only generator; removed tcc_pos and segment entry points.
"""Thai Character Cluster (TCC) tokenization.

Grammar from Theeramunkong et al. 2000. Python implementation by
Korakot Chaovavanich; TCC algorithm by Jakkrit TeCho; grammar by
Wittawat Jitkrittum.
"""

from __future__ import annotations

import re
from collections.abc import Iterator

_RE_TCC: list[str] = (
    """\
c[ั]([่-๋]c)?
c[ั]([่-๋]c)?k
เc็ck
เcctาะk
เccีtยะk
เccีtย(?=[เ-ไก-ฮ]|$)k
เc[ิีุู]tย(?=[เ-ไก-ฮ]|$)k
เcc็ck
เcิc์ck
เcิtck
เcีtยะ?k
เcืtอะk
เcืtอck
เcื
เctา?ะ?k
c[ึื]tck
c[ะ-ู]tk
c[ิุู]์
cรรc์
c็
ct[ะาำ]?k
แc็ck
แcc์k
แctะk
แcc็ck
แccc์k
โctะk
[เ-ไ]ctk
ก็
อึ
หึ
""".replace("k", "(cc?[d|ิ]?[์])?")
    .replace("c", "[ก-ฮ]")
    .replace("t", "[่-๋]?")
    .replace("d", "อูอุ".replace("อ", ""))
    .split()
)

_PAT_TCC: re.Pattern[str] = re.compile("|".join(_RE_TCC))


def _iter_clusters(text: str) -> Iterator[str]:
    p = 0
    n = len(text)
    while p < n:
        m = _PAT_TCC.match(text, p)
        end = m.end() if m else p + 1
        yield text[p:end]
        p = end


def tokenize(text: str) -> tuple[str, ...]:
    """Return TCC-grouped chunks as a tuple of strings."""
    if not text:
        return ()
    return tuple(_iter_clusters(text))

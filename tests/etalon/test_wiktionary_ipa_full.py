"""Full Wiktionary IPA accuracy test — opt-in, skipped by default.

This test measures accuracy against the complete kaikki.org Thai Wiktionary
dump (~17,000 entries) rather than the bundled 2,500-entry sample. It is
skipped unless both the data file is available AND
``thaiphon-data-volubilis`` is installed.

How to obtain the data
----------------------
1. Download the kaikki.org Wiktionary extract for Thai:
   https://kaikki.org/dictionary/rawdata.html

   Look for the Thai (th) JSONL file — expected size is approximately 43 MB.

2. Place it at one of these locations (checked in order):

   a. The path given by the ``THAIPHON_KAIKKI`` environment variable::

          export THAIPHON_KAIKKI=/path/to/kaikki-thai.jsonl
          pytest tests/etalon/test_wiktionary_ipa_full.py -v

   b. ``~/.cache/thaiphon/kaikki-thai.jsonl`` (no env var needed).

The file is CC-BY-SA 4.0 and is not bundled with this repository.

Requires the ``thaiphon-data-volubilis`` package
---------------------------------------------------
The documented 75 % accuracy is measured with the expanded Thai lexicon
package installed. Without it the base engine measures ~57 % on this
same corpus, because compound words fail to segment correctly. If
``thaiphon_data_volubilis`` is not importable, the test is skipped.

Install::

    uv add thaiphon-data-volubilis
    # or
    pip install thaiphon-data-volubilis

Floor
-----
Measured full-corpus accuracy with ``thaiphon-data-volubilis`` installed
is ~75.19 %. The floor is set to **73 %** — ~2 pp below the measured
baseline — so the test catches real regressions without false-alarming
on small variations.

Fixture license
---------------
The kaikki.org dump is CC-BY-SA 4.0 (derived from Wiktionary).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

import thaiphon
from tests.etalon.ipa_diagnostics import IPAMismatchReport

# Skip the whole module if the expanded lexicon package is not installed.
# The 75 % accuracy number documented in the README assumes it is present.
pytest.importorskip(
    "thaiphon_data_volubilis",
    reason=(
        "thaiphon-data-volubilis is required to reach the documented "
        "Wiktionary IPA accuracy. Install it with `uv add thaiphon-data-volubilis` "
        "(or `pip install thaiphon-data-volubilis`). See the main README Install "
        "section."
    ),
)

# Accuracy floor for the assertion.
#
# Measured full-corpus accuracy with thaiphon-data-volubilis installed is
# ~75.19 %. Floor at 73 % leaves ~2 pp of margin against transient edge-case
# variation while still catching real regressions.
MIN_ACCURACY = 0.73

_CACHE_PATH = Path.home() / ".cache" / "thaiphon" / "kaikki-thai.jsonl"
_SKIP_MSG = (
    "Full kaikki corpus not found. "
    "Download the Thai JSONL dump from "
    "https://kaikki.org/dictionary/rawdata.html "
    "and place it at ~/.cache/thaiphon/kaikki-thai.jsonl "
    "or set $THAIPHON_KAIKKI. Expected size ~43 MB."
)


def _find_corpus() -> Path | None:
    env = os.environ.get("THAIPHON_KAIKKI", "").strip()
    if env:
        p = Path(env)
        if p.exists():
            return p
    if _CACHE_PATH.exists():
        return _CACHE_PATH
    return None


def _load_entries(path: Path) -> list[tuple[str, str]]:
    """Load (word, ipa) pairs — same logic as the sample generator."""
    seen: set[tuple[str, str]] = set()
    out: list[tuple[str, str]] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            if d.get("lang_code") != "th":
                continue
            word = d.get("word", "")
            if not word:
                continue
            ipa = ""
            for s in d.get("sounds", []) or ():
                if isinstance(s, dict) and s.get("ipa"):
                    ipa = s["ipa"]
                    break
            if not ipa:
                continue
            key = (word, ipa)
            if key in seen:
                continue
            seen.add(key)
            out.append(key)
    return out


def test_wiktionary_ipa_full() -> None:
    """Full-corpus Wiktionary IPA accuracy — opt-in, skipped when data absent.

    Asserts accuracy >= 73 % across all de-duplicated (word, first-IPA)
    pairs in the kaikki.org Thai dump. The measured baseline with
    ``thaiphon-data-volubilis`` installed is ~75 %; the 73 % floor gives
    ~2 pp of margin for edge-case variation. See the module docstring for
    setup instructions.
    """
    corpus_path = _find_corpus()
    if corpus_path is None:
        pytest.skip(_SKIP_MSG)

    entries = _load_entries(corpus_path)
    report = IPAMismatchReport()
    for word, expected in entries:
        try:
            actual = thaiphon.transcribe(word, "ipa")
        except Exception as exc:
            report.record_exception(word, expected, f"{type(exc).__name__}: {exc}")
            continue
        report.record(word, expected, actual)

    summary = report.pretty(
        title=f"WIKTIONARY IPA FULL CORPUS — {report.total} entries"
    )
    print("\n" + summary, file=sys.stderr)
    print(
        f"\n[etalon] Full corpus accuracy: {report.accuracy * 100:.2f}% "
        f"({report.match}/{report.total} exact matches)",
        file=sys.stderr,
    )

    assert report.total > 0, "No entries were evaluated — corpus file may be malformed."
    assert report.accuracy >= MIN_ACCURACY, (
        f"Full-corpus IPA accuracy {report.accuracy * 100:.2f}% is below the "
        f"required {MIN_ACCURACY * 100:.0f}% floor "
        f"({report.match}/{report.total} exact matches). "
        f"Either a real accuracy regression has occurred, or the "
        f"thaiphon-data-volubilis package is missing from the environment."
    )

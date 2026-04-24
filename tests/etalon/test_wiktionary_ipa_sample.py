"""Bundled Wiktionary IPA accuracy test — runs by default with ``make test``.

Ground truth: ``tests/fixtures/wiktionary_ipa_sample.jsonl`` — a 2,500-entry
random sample drawn from the kaikki.org Thai Wiktionary dump (CC-BY-SA 4.0,
https://kaikki.org/dictionary/rawdata.html). The sample was generated with
a fixed seed (20260421) so results are deterministic and reproducible.

Requires the ``thaiphon-data-volubilis`` package
---------------------------------------------------
This test measures accuracy for the full, recommended installation
(``thaiphon`` + ``thaiphon-data-volubilis``). The expanded Thai lexicon
provides the word-boundary and variant coverage needed to reach the
~75 % accuracy documented in the main README. Without the data package
the base engine measures ~57 % on this same sample, because compound
words fail to segment correctly.

If ``thaiphon_data_volubilis`` is not importable, this test is skipped
with a message pointing at the install command.

Statistical note
----------------
At n = 2,500 and a true full-corpus accuracy near 75.19 %, the 99 %
confidence interval for the sample proportion is approximately::

    p ± z * sqrt(p*(1-p)/n)  =  0.7519 ± 2.576 * sqrt(0.7519*0.2481/2500)
                              ≈  0.7519 ± 0.022

So the 99 % CI is roughly [73 %, 77 %]. The floor is set to **72 %** —
just below the lower bound — giving comfortable headroom against
sampling variance while still catching large-scale accuracy regressions.

Full reproducibility
--------------------
To measure accuracy on the complete kaikki dump (17,014 entries) run::

    THAIPHON_KAIKKI=/path/to/kaikki-thai.jsonl \\
        pytest tests/etalon/test_wiktionary_ipa_full.py -v

See that file for the download instructions.

Fixture license
---------------
``tests/fixtures/wiktionary_ipa_sample.jsonl`` is CC-BY-SA 4.0 (derived
from Wiktionary via kaikki.org, https://kaikki.org/dictionary/rawdata.html).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

import thaiphon
from tests.etalon.ipa_diagnostics import IPAMismatchReport

# Skip the whole module if the expanded lexicon package is not installed.
# The 75 % accuracy number documented in the README assumes it is present;
# running this test without it would only measure the reduced base-engine
# accuracy (~57 %) and produce a misleading failure.
pytest.importorskip(
    "thaiphon_data_volubilis",
    reason=(
        "thaiphon-data-volubilis is required to reach the documented "
        "Wiktionary IPA accuracy. Install it with `uv add thaiphon-data-volubilis` "
        "(or `pip install thaiphon-data-volubilis`). See the main README Install "
        "section."
    ),
)

_FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "tests"
    / "fixtures"
    / "wiktionary_ipa_sample.jsonl"
)

# Accuracy floor for the assertion.
#
# Measured sample accuracy with thaiphon-data-volubilis installed is ~74.2 %.
# Floor at 72 % leaves ~2 pp of margin for sampling variance while still
# catching any real regression that drops accuracy meaningfully.
MIN_ACCURACY = 0.72


def _load_sample() -> list[tuple[str, str]]:
    """Load (word, ipa) pairs from the bundled sample, skipping the _meta line."""
    entries: list[tuple[str, str]] = []
    with _FIXTURE.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "_meta" in d:
                continue
            word = d.get("word", "")
            ipa = d.get("ipa", "")
            if word and ipa:
                entries.append((word, ipa))
    return entries


def test_sample_file_schema() -> None:
    """Fixture sanity check — file is present, parseable, and large enough."""
    assert _FIXTURE.exists(), f"Fixture not found: {_FIXTURE}"
    entries = _load_sample()
    assert len(entries) >= 2_000, (
        f"Expected at least 2,000 entries in the sample fixture; "
        f"got {len(entries)}. The file may be corrupt or truncated."
    )
    for word, ipa in entries[:10]:
        assert isinstance(word, str) and word, "word field must be a non-empty string"
        assert isinstance(ipa, str) and ipa, "ipa field must be a non-empty string"


def test_wiktionary_ipa_sample_accuracy() -> None:
    """Accuracy on the 2,500-entry bundled Wiktionary IPA sample.

    Asserts that at least 72 % of entries match exactly after IPA
    normalisation (released vs unreleased stops, glottal onset, stress
    marks, tie-bar notation, centring-diphthong length variants, etc.).

    Requires ``thaiphon-data-volubilis`` (enforced by module-level
    ``importorskip``). Measured accuracy with that package installed is
    roughly 74 %; the 72 % floor gives a 2 pp margin for sampling
    variance.
    """
    entries = _load_sample()
    report = IPAMismatchReport()
    for word, expected in entries:
        try:
            actual = thaiphon.transcribe(word, "ipa")
        except Exception as exc:
            report.record_exception(word, expected, f"{type(exc).__name__}: {exc}")
            continue
        report.record(word, expected, actual)

    summary = report.pretty(title=f"WIKTIONARY IPA SAMPLE — {report.total} entries")
    print("\n" + summary, file=sys.stderr)

    # Echo a concise line to stdout so it appears in normal pytest -v output.
    print(
        f"\n[etalon] Sample accuracy: {report.accuracy * 100:.2f}% "
        f"({report.match}/{report.total} exact matches)",
        file=sys.stderr,
    )

    assert report.total > 0, "No entries were evaluated — fixture may be empty."
    assert report.accuracy >= MIN_ACCURACY, (
        f"IPA sample accuracy {report.accuracy * 100:.2f}% is below the "
        f"{MIN_ACCURACY * 100:.0f}% floor "
        f"({report.match}/{report.total} exact matches). "
        f"Either a real accuracy regression has occurred, or the "
        f"thaiphon-data-volubilis package is missing from the environment."
    )

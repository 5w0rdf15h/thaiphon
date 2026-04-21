# thaiphon tests

## Running the tests

```bash
# From the package root (github/thaiphon/).
uv run pytest -q

# Or, if you have thaiphon installed in the active environment:
pytest -q

# Verbose output:
pytest -v

# A specific file:
pytest tests/test_api.py -v

# A specific test by keyword:
pytest -k "test_sara_am"
```

## What this suite covers

| File | Coverage |
|------|----------|
| `test_api.py` | `transcribe`, `transcribe_word`, `transcribe_sentence`, `analyze`, `analyze_word`, `list_schemes`; all schemes; all reading profiles; `format` argument; NFC/NFD parity; error handling. |
| `test_phonology_model.py` | `Phoneme`, `Cluster`, `Syllable`, `PhonologicalWord`; all enumerations. |
| `test_renderers/test_tlc.py` | TLC scheme: consonant classes, tones, vowel variety, codas, Sara Am, clusters. |
| `test_renderers/test_ipa.py` | IPA scheme: /…/ slashes, Chao tone letters, length mark, stop codas, glide codas. |
| `test_renderers/test_morev.py` | Morev (Cyrillic) scheme: onset map, tone diacritics, macron for long vowels. |
| `test_reading_profiles.py` | Profile-dependent outputs: everyday vs learned_full for Indic words; preservation vs collapse by profile. |
| `test_loanword_preservation.py` | Lexicon membership, `get_preserved_coda`, TLC/IPA surface output for key loanwords. |
| `test_edge_cases.py` | Sara Am, killer mark, leading ห, consonant clusters, pre-vowel frames, glottal onset, empty/whitespace, Thai numerals, mixed input. |
| `test_nfc_normalization.py` | `normalize`: NFC, mark reordering, variation-selector stripping, idempotence, error on leading combining mark. |

## Characteristics

- **Fast.** The whole suite runs in well under a second on a modern
  laptop, so it is cheap to run on every change.
- **Deterministic.** No network access, no external database, no
  time- or locale-dependent behaviour.
- **Self-contained.** Every example word is hand-curated inline in
  the test files; see `fixtures/README.md` for the provenance policy.
- **API- and regression-focused.** The goal is to pin the public API
  surface and a representative cross-section of phonological behaviour,
  not to exhaustively enumerate every derivation rule. Contributors
  adding new rules should add a regression test here so the behaviour
  is visible to downstream users.

## Etalon measurement

Two tests under `tests/etalon/` compare the engine's IPA output against
Wiktionary ground truth extracted from the kaikki.org Thai Wiktionary dump
(CC-BY-SA 4.0, https://kaikki.org/dictionary/rawdata.html).

**Important — both etalon tests require the optional
`thaiphon-data-volubilis` package.** The accuracy numbers quoted in the
main README (and asserted as floors below) are measured with that package
installed. Without it the base engine's Wiktionary accuracy drops from
~75 % to ~57 % on the same corpus, because compound words don't segment
correctly. Both tests `importorskip` the data package and skip cleanly
with a helpful message when it's not present.

Install via::

    uv add thaiphon-data-volubilis
    # or
    pip install thaiphon-data-volubilis

### Bundled sample test (runs by default)

```bash
pytest tests/etalon/test_wiktionary_ipa_sample.py -v
```

Uses `tests/fixtures/wiktionary_ipa_sample.jsonl` — a 2,500-entry random
sample (seed 20260421) bundled with the repository. No external data needed.
The sample is deterministic and bit-for-bit reproducible from the kaikki
source using `tools/build_etalon_sample/build.py` in the development workspace.

Floor: **72 %**. Measured accuracy with `thaiphon-data-volubilis`
installed is ~74 %; the 2 pp margin accommodates sampling variance while
catching real regressions. See the module docstring for the statistical
derivation.

### Full-corpus opt-in test (skipped by default)

```bash
# Step 1 — download the kaikki.org Thai JSONL (~43 MB):
#   https://kaikki.org/dictionary/rawdata.html  (Thai entries)
#   Place at: ~/.cache/thaiphon/kaikki-thai.jsonl
#   Or set: export THAIPHON_KAIKKI=/path/to/kaikki-thai.jsonl

# Step 2 — run:
THAIPHON_KAIKKI=~/.cache/thaiphon/kaikki-thai.jsonl \
    pytest tests/etalon/test_wiktionary_ipa_full.py -v
```

Measures accuracy against all ~17,014 deduplicated `(word, first-IPA)` pairs
in the kaikki dump. Floor: **73 %**. Measured accuracy with
`thaiphon-data-volubilis` installed is ~75 %.

## Fixture licensing

All word examples in the test files are hand-curated from openly-licensed
Thai-language sources only — Wiktionary entries (CC-BY-SA 4.0) and, where
needed, VOLUBILIS Mundo Dictionary entries (also CC-BY-SA 4.0). No test
fixture derives from any closed-licensed dictionary or restricted
database. See `fixtures/README.md` for the full provenance policy.

`tests/fixtures/wiktionary_ipa_sample.jsonl` is CC-BY-SA 4.0 (derived from
Wiktionary via kaikki.org); all other fixture files are Apache-2.0.

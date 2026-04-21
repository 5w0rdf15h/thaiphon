# Test fixtures

This directory contains any supplementary fixture data used by the test suite.

## Fixture data provenance

All word examples used inline in the test files are hand-curated from
openly-licensed Thai-language sources only:

- **Wiktionary** entries (CC-BY-SA 4.0), https://en.wiktionary.org/
- **VOLUBILIS Mundo Dictionary** (CC-BY-SA 4.0), where the Thai entry
  and its phonemic form are both published under that license

Other dictionaries (including closed-licensed reference works) are
not used as fixture sources, to keep the provenance of every example
auditable and license-compatible with this repository.

No fixture data in this directory or in the test files derives from
thai-language.com or any other restricted database.

## Fixtures

### `wiktionary_ipa_sample.jsonl`

**License**: CC-BY-SA 4.0 — derived from Wiktionary via kaikki.org.

**Source**: https://kaikki.org/dictionary/rawdata.html (Thai / `lang_code == "th"` entries).

**Contents**: A deterministic random sample of 2,500 `(word, IPA)` pairs drawn
from the kaikki.org Wiktionary dump. Each line is a JSON object with two
fields: `"word"` (Thai script) and `"ipa"` (IPA transcription from Wiktionary).
The first line is a `_meta` record documenting the source, license, seed, and
sampling parameters; test loaders skip it by checking for the `_meta` key.

**Sampling method**: All `lang_code == "th"` records are read; the first
`sounds[*].ipa` per record is kept; pairs are deduplicated by `(word, ipa)`.
2,500 entries are then drawn from the resulting ~17,014 pairs using
`random.Random(seed=20260421)`. The seed is fixed so the sample is
bit-for-bit reproducible.

**Attribution**: Wiktionary content is made available under the Creative
Commons Attribution-ShareAlike 4.0 International License (CC-BY-SA 4.0).
The kaikki.org dataset is an extraction of Wiktionary's Thai entries;
see https://kaikki.org/dictionary/rawdata.html for the original data and
https://www.wiktionary.org/ for the upstream source.

## License

Test code in `../` is Apache-2.0 (same as the package).

`wiktionary_ipa_sample.jsonl` is CC-BY-SA 4.0 (derived from Wiktionary
via kaikki.org). All other fixture files are Apache-2.0.

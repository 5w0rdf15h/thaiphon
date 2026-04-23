# Changelog

All notable changes to this project are documented here. The format is based
on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0]

### Added

- `format="html"` is now wired through the renderer pipeline end to end. Each
  scheme can opt in to a per-format onset overlay; schemes without an overlay
  return the same string for `text` and `html`. IPA and TLC inherit the
  text output unchanged.
- `SchemeMapping` gained two optional fields:
  - `onset_html_map`: per-format onset substitutions used when the renderer
    is asked for HTML.
  - `cluster_second_slot_map`: position-aware substitution for the second
    consonant of an onset cluster, enabling rules like /w/ → `у` in the
    second cluster slot for the Morev scheme.
- A standalone `scripts/bench_memory.py` for measuring resident-set size and
  lookup latency across the engine and the bundled lexicon.

### Changed

- **Morev renderer rewritten** to match the published convention:
  - **Onsets**: aspirated stops are now written as digraphs in text mode
    (`кх`, `тх`, `пх`) and as `к<sup>х</sup>`, `т<sup>х</sup>`, `п<sup>х</sup>`
    in HTML. The previous Latin modifier letter `ʰ` (U+02B0) is no longer
    used. /tɕʰ/ is rendered as bare `ч` in both modes (the digraph is
    treated as inherently aspirated; no superscript is added). /tɕ/ is
    written as the digraph `ть`. /ŋ/ is written as the two-letter `нг`
    in both onset and coda position; the previous single-character `ң`
    (U+04A3) is no longer used.
  - **Vowels**: /ɔ/ collapses to Cyrillic `о`/`о̄` (the source dictionary
    uses these as the default for both modern Thai /oː/ and /ɔː/; the
    Latin `ɔ`/`ɔ̄` glyphs from its introductory key appear only sporadically
    without a derivable phonological pattern). /ɤ/ is written as `ə`/`ə̄`.
    Long diphthongs carry the macron on the first element only
    (`ӣа`, `ы̄а`, `ӯа`).
  - **Codas**: foreign codas collapse to the native six-coda inventory:
    /f/ → `п`, /s/ → `т`, /l/ → `н`, matching attested behaviour for
    loanwords like ปรู๊ฟ, ก๊าซ, โบนัส, ฟุตบอล.
  - **Tone marks**: spacing modifier letters `ˆ`, `` ` ``, `ˇ`, `´` placed
    at the end of the syllable, after the coda (e.g. `декˆ`, not `де̂к`).
    Replaces the previous combining diacritics on the vowel.
  - **/w/ positional rule**: /w/ as the first onset slot renders as `в`,
    as a coda or in the second cluster slot as `у`.

### Notes for callers

- `format="text"` remains the default. The new `format="html"` is opt-in
  and does not change behaviour for existing callers.
- The Morev text-mode output for many words has changed in this release
  (different glyphs for the cases listed above). If you depend on exact
  Morev strings, regenerate any cached output.

## [0.2.0]

### Added

- `PhonologicalWord` data contract: an immutable tuple of `Syllable`
  records carrying onset, vowel quality, vowel length, coda, and tone.
  Renderers consume this representation; the engine no longer hands
  raw strings between layers.
- `SchemeMapping` + `MappingRenderer`: declarative scheme definitions
  mapping IPA-typed phonemes to surface strings. Adding a new
  romanisation is now a data change, not a code change.
- Reading profiles (`everyday`, `careful_educated`, `learned_full`,
  `etalon_compat`) for register-sensitive treatment of foreign codas
  in loanwords.
- Built-in renderers for IPA, TLC (thai-language.com convention), and
  Morev (Cyrillic).
- Optional integration with the companion `thaiphon-data-volubilis`
  package: when present, the analysis pipeline short-circuits on entries
  with exact-form pronunciations.
- PyPI publishing workflow.

## [0.1.0]

- Initial release.

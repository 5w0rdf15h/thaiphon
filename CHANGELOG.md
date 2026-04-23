# Changelog

All notable changes to this project are documented here. The format is based
on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.1]

### Fixed

- Test suite no longer requires the optional `thaiphon-data-volubilis`
  data package to be installed to pass. A handful of tests pinning
  lexicon-informed surfaces (เสื้อ single-syllable centring diphthong,
  the Paiboon reference phrase, long /ɤː/ for เลย) now skip cleanly on
  a minimal install via a local `pytest.mark.skipif` guard. The
  default-configuration test gate matches the published wheel.

### Changed

- CI matrix (Python 3.10 / 3.11 / 3.12) now runs in two separate
  jobs — one without the `thaiphon-data-volubilis` data package
  installed (the default published-wheel configuration) and one with
  it — so any test that accidentally depends on the lexicon surfaces
  as a failure before merge.
- README: built-in renderer list expanded to document all six schemes
  (`ipa`, `tlc`, `morev`, `rtl`, `paiboon`, `paiboon_plus`) and the
  TLC `format="html"` superscript tone output, bringing the landing
  page in line with the 0.4.0 feature set. Pipeline diagram
  regenerated to include the new schemes.

## [0.4.0]

### Added

- **`rtl` scheme** — romanization for the Rak Thai Language School
  convention. Aspirated stops as digraphs (`ph`, `th`, `kh`); /tɕ/ as
  `c` and /tɕʰ/ as `ch`. Vowel-initial syllables emit an explicit `ʼ`
  (U+02BC) onset. Mid tone is marked with a macron (low `̀`, falling
  `̂`, high `́`, rising `̌`). IPA-letter vowels `ʉ ɛ ɔ ə` double for
  length; centring diphthongs carry the tone mark on the first
  element. Foreign codas collapse to the native inventory (/f/ → `p`,
  /s/ → `t`, /l/ → `n`). Syllable separator is a single space.

- **`paiboon` scheme** — the original Paiboon Publishing romanization
  used in the first-edition learner series. Aspirated stops take bare
  letters (`p`, `t`, `k`, `ch`); unaspirated voiceless stops use
  English-cluster digraphs (`bp`, `dt`, `g`, `j`). IPA-letter vowels
  `ʉ ɛ ɔ ə` double for length. Centring diphthongs have no spelling
  distinction between short and long — both render as `ia`, `ʉa`,
  `ua`. /iː/+/w/ spells `iao`; short /i/+/w/ spells `iu`.

- **`paiboon_plus` scheme** — the revised system adopted in the 2009
  Three-Way dictionary and later titles. Identical to `paiboon`
  except centring diphthongs double for length (short `ia ʉa ua`,
  long `iia ʉʉa uua`) and the triphthong-like combinations follow
  suit (`iiao`, `uuai`, `ʉʉai`).

- `SchemeMapping` gained an optional `tone_format_html` field so a
  scheme can emit different tone markup for `format="html"` without
  affecting the plain-text output.

### Changed

- **TLC HTML output emits tone markers as `<sup>` tags.** Under
  `format="html"`, `thaiphon.transcribe(word, "tlc", format="html")`
  returns e.g. `naam<sup>H</sup>` instead of the literal `naam{H}`,
  matching the thai-language.com presentation convention. The
  default text output (`format="text"`, or the bare `transcribe`
  call) is unchanged.

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

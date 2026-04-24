# Changelog

All notable changes to this project are documented here. The format is based
on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.6.1]

### Added

- **`py.typed` marker.** The package now ships a PEP 561 marker so
  downstream `mypy` and IDE type checkers trust the bundled type
  annotations out of the box, without a "module lacks py.typed marker"
  warning.

### Changed

- **PyPI package metadata.** Publishes Documentation, Homepage,
  Repository, Changelog, and Issues URLs via `[project.urls]`, so the
  left sidebar on [pypi.org/project/thaiphon](https://pypi.org/project/thaiphon/)
  links out to the hosted docs site and the source repository.
  Classifier list extended with `Development Status :: 4 - Beta`,
  `Natural Language :: Thai`, `Topic :: Text Processing :: Linguistic`,
  `Typing :: Typed`, and audience tags so PyPI search and topic
  filters surface the project for linguistic / Thai-specific queries.
  Keywords added (`thai`, `phonology`, `transliteration`, scheme names)
  for the same reason.
- **README.** Adds PyPI version, Python version, license, and docs
  badges at the top so readers on PyPI or GitHub see status at a
  glance.

## [0.6.0]

### Added

- **User-registered override lexicons.** New public API
  `register_lexicon(lookup, *, name, priority=0)`, with companions
  `unregister_lexicon` and `registered_lexicons`. The lookup is called
  with the post-normalization Thai form and may return a
  `PhonologicalWord` to short-circuit the pipeline (or `None` to defer
  to the next layer). Override hits resolve before every built-in
  lexicon and rule-based derivation, and are tagged
  `source='override:<layer-name>'` on both the `AnalysisResult` and
  the returned `PhonologicalWord` so callers can see which layer
  answered. Higher priority resolves first; ties broken by
  registration order. thaiphon ships no storage — consumers back
  their lookup with whatever fits (dict, SQLite, HTTP, file).

### Fixed

- Pre-vowel CVC syllables (`เทพ`, `เกม`, `เบญ`, `แดง`) inside longer
  compounds no longer absorb a following bare consonant as a
  live-nasal coda. The coda-detection helper previously treated only
  post-base vowels as "nucleus seen", so pre-vowel shapes appeared
  coda-less even when their second consonant clearly closed the
  syllable. Symptom: `กรุงเทพมหานคร` rendered the second syllable as
  `/tʰeːm˧/` (live, mid tone, nasal coda) instead of `/tʰeːp̚˥˩/`
  (dead, falling tone, stop coda). True onset clusters (`เปล`) and
  silent-ร pseudo clusters (`ทราย`, `โศรก`) still keep their coda
  slot open.

## [0.5.0]

### Added

- **`rtgs` scheme** — Royal Thai General System of Transcription
  (2002 specification). Plain ASCII Latin output with no tone
  marks, no vowel length distinction, and no diacritics. Aspirated
  stops as digraphs (`ph`, `th`, `kh`, `ch`); six final consonants
  (`k`, `t`, `p`, `n`, `m`, `ng`); foreign codas collapsed to the
  native inventory (ลิฟต์ renders `lip`, not `lif`). Intended as
  the canonical "official" romanization for signage and
  government-style output. Callers that want modern-loan `f`
  preservation should pick `rtl`, `paiboon`, or `paiboon_plus`.

- **`lmt` scheme** — Cyrillic transliteration following the
  Lipilina-Muzychenko-Thapanosoth convention used in the MSU / ISAA
  Thai learner textbook (И. Н. Липилина, Ю. Ф. Музыченко,
  П. Тхапаносотх, *Учебник тайского языка: вводный курс*, Москва:
  ИД ВКН, 2018, ISBN 978-5-907086-16-6). Tones render at the end of
  each syllable as Unicode superscript digits in text mode (`⁰` mid,
  `¹` low, `²` falling, `³` high, `⁴` rising) and as ordinary digits
  wrapped in `<sup>…</sup>` in HTML mode. Vowel length is marked
  with an ASCII colon on the nucleus (`ка:` for `/kaː/`); syllables
  inside a word are space-separated. Vowel glyphs: Cyrillic `е` for
  `/e/`, Cyrillic `э` for `/ɛ/`, Cyrillic `о` for `/o/`, Latin IPA
  `ɔ` (U+0254) for `/ɔ/`, Latin schwa `ə` (U+0259) for `/ɤ/`. Like
  `morev` and `rtgs`, LMT is a strict citation convention — foreign
  coda `/f/` collapses to `п` regardless of reading profile.

### Changed

- `paiboon`, `paiboon_plus`, and `rtl` schemes now preserve final
  `/f/` in modern loanwords by default, aligning them with the
  `ipa` and `tlc` renderers that already consulted the same
  lexicon. Entries tagged with `coda_policy="preserve"` in the
  loanword lexicon (ลิฟต์, เชฟ, ยีราฟ, ไมโครซอฟต์, ออฟฟิศ, and ~90
  others) now render with `f` instead of collapsing to native `p`
  under the default `profile="everyday"`. Register-gated entries
  (e.g. กราฟ, กอล์ฟ) preserve under `profile="careful_educated"`
  only. Use `profile="etalon_compat"` to opt back in to strict
  native-coda collapse (produces `líp` for ลิฟต์). `morev` is
  unchanged — its dictionary convention intentionally collapses
  foreign codas to the nearest native segment.

### Notes for callers

- The built-in scheme list grows from six to eight: `ipa`, `tlc`,
  `morev`, `rtl`, `paiboon`, `paiboon_plus`, **`rtgs`**, **`lmt`**.
- The default-output change for `paiboon`, `paiboon_plus`, and `rtl`
  is a visible behaviour shift for existing callers. Callers that
  depend on the previous collapse behaviour should pass
  `profile="etalon_compat"` to `transcribe_word` / `transcribe` /
  `transcribe_sentence`.

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

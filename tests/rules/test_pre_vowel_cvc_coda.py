"""Pre-vowel CVC syllables must own their coda in compound contexts.

A syllable of the shape ``เ-C1-C2`` (also ``แ-``, ``โ-``, ``ใ-``, ``ไ-``)
where (C1, C2) is not a native onset cluster is a closed CVC syllable
with C2 serving as coda. When such a syllable appears inside a longer
word, the syllabifier must not fold the following bare consonant onto
it as if the coda slot were still open — doing so flips the syllable
type from dead to live and corrupts tone assignment.

The canonical regression is ``เทพ`` inside ``กรุงเทพมหานคร``: the
phonology is /tʰeːp̚˥˩/ (dead, long ē, falling tone, labial-stop coda),
and the following ``ม`` starts its own inherent-/a/ syllable.

True onset clusters (``เปล``, ``เกร``, ``เคล``) and silent-ร pseudo
clusters (``ทร`` in ``ทราย``, ``ศร`` in ``โศรก``) are left coda-less
and continue to read through their established paths.
"""

from __future__ import annotations

import pytest

from thaiphon.api import transcribe


# --- core fix: pre-vowel CVC keeps its stop coda in compounds ---------


@pytest.mark.parametrize(
    "word,expected_ipa_prefix",
    [
        # Standalone dead-syllable labial-stop coda — lexicon covers this
        # already, but locks the expected IPA shape we reference below.
        ("เทพ", "/tʰeːp̚˥˩/"),
        # Compound where ``เทพ`` appears mid-word and the following ``ม``
        # must not be absorbed as its coda. The first three syllables are
        # the portion this test pins.
        ("กรุงเทพมหานคร", "/kruŋ˧.tʰeːp̚˥˩.ma˦˥."),
    ],
)
def test_pre_vowel_stop_coda_preserved_in_compound(
    word: str, expected_ipa_prefix: str
) -> None:
    assert transcribe(word, "ipa").startswith(expected_ipa_prefix)


# --- regression guard: true clusters and silent-ร stay coda-less ------


@pytest.mark.parametrize(
    "word,expected_ipa",
    [
        # True onset cluster ``ปล`` — must render as a single /pl-/ syllable
        # even when a coda follows the cluster.
        ("แปลก", "/plɛːk̚˨˩/"),
        # Silent-ร with ``ทร`` — the ร is absorbed, ย is the coda.
        ("ทราย", "/saːj˧/"),
        # Silent-ร with ``ศร`` — the ร is absorbed, ก is the coda.
        ("โศรก", "/soːk̚˨˩/"),
    ],
)
def test_cluster_and_silent_r_unchanged(
    word: str, expected_ipa: str
) -> None:
    assert transcribe(word, "ipa") == expected_ipa

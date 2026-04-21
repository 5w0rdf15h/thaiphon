"""Thai Character Cluster (TCC) tokenization tests.

TCC is a sub-word segmentation algorithm that splits Thai text into
orthographic clusters (each cluster cannot be split without breaking a
character-level unit). The implementation is adapted from pythainlp.
"""

from __future__ import annotations

import pytest

from thaiphon.tokenization.tcc import tokenize


def test_empty_string() -> None:
    assert tokenize("") == ()


def test_single_consonant() -> None:
    chunks = tokenize("ก")
    assert chunks == ("ก",)


def test_sawatdee_first_chunk_starts_with_so() -> None:
    chunks = tokenize("สวัสดี")
    assert chunks[0].startswith("ส")
    assert "".join(chunks) == "สวัสดี"


def test_tone_mark_stays_attached_to_base() -> None:
    # ก่อน — ◌่ (tone) must stay glued to ก.
    chunks = tokenize("ก่อน")
    assert chunks[0] == "ก่"


def test_ascii_passthrough_pinned() -> None:
    chunks = tokenize("abc")
    # Non-Thai characters advance one char at a time.
    assert chunks == ("a", "b", "c")


def test_concatenation_is_lossless() -> None:
    text = "ผลไม้"
    assert "".join(tokenize(text)) == text


def test_mixed_text_preserves_content() -> None:
    text = "hello ดี world"
    assert "".join(tokenize(text)) == text


@pytest.mark.parametrize(
    "word",
    [
        "สวัสดี",
        "ผลไม้",
        "ไทย",
        "ก่อน",
        "เร็ว",
        "ดี",
        "คน",
        "สมุด",
        "พระ",
        "กรุงเทพ",
        "เด็ก",
        "ผม",
        "ข้าว",
        "เพื่อน",
        "โรงเรียน",
    ],
)
def test_lossless_on_real_words(word: str) -> None:
    chunks = tokenize(word)
    assert isinstance(chunks, tuple)
    assert all(c for c in chunks)
    assert "".join(chunks) == word


def test_returns_tuple() -> None:
    result = tokenize("ดี")
    assert isinstance(result, tuple)

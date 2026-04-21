"""Shared pytest fixtures for the thaiphon test suite."""

from __future__ import annotations

import unicodedata

import pytest

import thaiphon


@pytest.fixture
def nfd():
    """Return a helper that converts a string to NFD form.

    Used to verify that the API normalizes NFD input to NFC before
    processing, matching the result of NFC input.
    """

    def _nfd(text: str) -> str:
        return unicodedata.normalize("NFD", text)

    return _nfd


@pytest.fixture
def transcribe():
    """Thin reference to :func:`thaiphon.transcribe`."""
    return thaiphon.transcribe


@pytest.fixture
def transcribe_sentence():
    """Thin reference to :func:`thaiphon.transcribe_sentence`."""
    return thaiphon.transcribe_sentence


@pytest.fixture
def analyze():
    """Thin reference to :func:`thaiphon.analyze`."""
    return thaiphon.analyze

"""thaiphon — Thai phonological transliteration engine."""

from thaiphon.api import (
    analyze,
    analyze_word,
    list_schemes,
    transcribe,
    transcribe_sentence,
    transcribe_word,
)
from thaiphon.overrides import (
    register_lexicon,
    registered_lexicons,
    unregister_lexicon,
)

__version__ = "0.6.0"
__all__ = [
    "__version__",
    "analyze",
    "analyze_word",
    "list_schemes",
    "register_lexicon",
    "registered_lexicons",
    "transcribe",
    "transcribe_sentence",
    "transcribe_word",
    "unregister_lexicon",
]

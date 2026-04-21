"""Exception hierarchy for thaiphon."""


class ThaiphonError(Exception):
    """Base for all thaiphon exceptions."""


class ParseError(ThaiphonError):
    """Raised when tokenization or orthography rejects input."""


class NormalizationError(ThaiphonError):
    """Raised on NFC or script-order normalization failure."""


class DerivationError(ThaiphonError):
    """Raised when a rule-table lookup has no entry for given inputs."""


class UnsupportedSchemeError(ThaiphonError):
    """Raised when a requested renderer scheme is not registered."""


class AmbiguousAnalysisError(ThaiphonError):
    """Raised in strict mode when multiple candidates tie after ranking."""

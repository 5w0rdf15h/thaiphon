class ThaiphonError(Exception):
    """
    Base exception for all thaiphon errors.

    Any error raised by thaiphon should inherit from this class,
    so users can reliably catch thaiphon-specific failures.
    """

    pass


class UnknownPhonemeError(ThaiphonError):
    """
    Raised when a renderer encounters a phoneme
    it does not know how to represent.
    """

    pass

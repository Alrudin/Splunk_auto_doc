"""Exception types for the parser module."""


class ParserError(Exception):
    """Base exception for parser errors.
    
    Raised when the parser encounters malformed input that cannot be
    processed or recovered from.
    """

    pass


class ParserWarning(UserWarning):
    """Warning for recoverable parser issues.
    
    Used for non-fatal issues like ambiguous syntax or deprecated
    conventions that the parser can handle but may indicate problems.
    """

    pass

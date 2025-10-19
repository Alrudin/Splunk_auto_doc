"""Splunk .conf file parser module.

This module provides robust parsing for Splunk configuration files,
handling comments, line continuations, repeated keys, and preserving
file order and provenance metadata.
"""

from app.parser.core import ConfParser
from app.parser.exceptions import ParserError, ParserWarning
from app.parser.types import ParsedStanza, Provenance

__all__ = [
    "ConfParser",
    "ParserError",
    "ParserWarning",
    "ParsedStanza",
    "Provenance",
]

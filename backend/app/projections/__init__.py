"""Typed projection modules for normalizing parsed stanzas.

This package contains projectors that transform generic parsed stanzas
from the parser into typed database records. Each projector handles a
specific configuration type (inputs, props, transforms, etc.).
"""

from typing import Any, Protocol

from app.parser.types import ParsedStanza
from app.projections.indexes import IndexProjector
from app.projections.inputs import InputProjector
from app.projections.outputs import OutputProjector
from app.projections.props import PropsProjector
from app.projections.serverclasses import ServerclassProjector
from app.projections.transforms import TransformProjector


class Projector(Protocol):
    """Protocol for projector classes that transform parsed stanzas to typed records."""

    def project(self, stanza: ParsedStanza, run_id: int) -> dict[str, Any] | None:
        """Project a parsed stanza to a typed record dictionary.

        Args:
            stanza: Parsed stanza from configuration file
            run_id: ID of the ingestion run

        Returns:
            Dictionary with fields for model instantiation, or None if stanza should be skipped
        """
        ...


__all__ = [
    "Projector",
    "IndexProjector",
    "InputProjector",
    "OutputProjector",
    "PropsProjector",
    "ServerclassProjector",
    "TransformProjector",
]

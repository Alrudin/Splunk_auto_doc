"""Typed projection modules for normalizing parsed stanzas.

This package contains projectors that transform generic parsed stanzas
from the parser into typed database records. Each projector handles a
specific configuration type (inputs, props, transforms, etc.).
"""

from app.projections.inputs import InputProjector

__all__ = ["InputProjector"]

"""Q-SHIELD — Application API Package (Milestone M19-B).

Provides FastAPI endpoints, typed Pydantic schemas, and the application service layer
for interacting with the Q-SHIELD security pipeline.
"""

from __future__ import annotations

from src.api.app import app, create_app
from src.api.service import QShieldService

__all__ = [
    "QShieldService",
    "app",
    "create_app",
]

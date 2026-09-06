"""Q-SHIELD — Persistence Layer Package (Milestone M19-A).

Provides local SQLite persistence for security events, multi-source evidence records,
M17 security evaluation summaries, and M18 performance benchmark runs.
"""

from __future__ import annotations

from src.persistence.database import DEFAULT_DB_PATH, DatabaseManager
from src.persistence.models import (
    PersistedBenchmarkResult,
    PersistedBenchmarkRun,
    PersistedEvaluationRun,
    PersistedEvaluationScenarioResult,
    PersistedEvidenceRecord,
    PersistedSecurityEvent,
    assert_no_secrets,
)
from src.persistence.repository import (
    SecurityRepository,
    decision_to_persisted_event,
    fused_evidence_to_persisted_record,
)

__all__ = [
    "DEFAULT_DB_PATH",
    "DatabaseManager",
    "PersistedBenchmarkResult",
    "PersistedBenchmarkRun",
    "PersistedEvaluationRun",
    "PersistedEvaluationScenarioResult",
    "PersistedEvidenceRecord",
    "PersistedSecurityEvent",
    "SecurityRepository",
    "assert_no_secrets",
    "decision_to_persisted_event",
    "fused_evidence_to_persisted_record",
]

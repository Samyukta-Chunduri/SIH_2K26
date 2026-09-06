"""Q-SHIELD — Persistence Models (Milestone M19-A).

Defines strongly typed, immutable dataclasses for persisted security events,
evidence records, evaluation runs, and performance benchmark records.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
import json
from typing import Any

from src.detection.decision import DecisionVerdict

_FORBIDDEN_SECRET_SUBSTRINGS: tuple[str, ...] = (
    "password",
    "secret",
    "private_key",
    "raw_key",
    "token_secret",
    "credential_raw",
    "key_material",
    "shared_secret",
    "api_key",
)


def assert_no_secrets(obj: Any, context: str = "persistence") -> None:
    """Recursively scan mappings, sequences, and strings to reject sensitive credentials."""
    if isinstance(obj, Mapping):
        for k, v in obj.items():
            k_str = str(k).lower()
            for forbidden in _FORBIDDEN_SECRET_SUBSTRINGS:
                if forbidden in k_str:
                    raise ValueError(
                        f"Sensitive keyword '{forbidden}' detected in {context} key '{k}'. "
                        "Raw cryptographic keys or credentials must never be persisted."
                    )
            assert_no_secrets(v, f"{context}['{k}']")
    elif isinstance(obj, (list, tuple)):
        for idx, item in enumerate(obj):
            assert_no_secrets(item, f"{context}[{idx}]")
    elif isinstance(obj, str):
        # Scan raw JSON strings if applicable
        if obj.startswith("{") and obj.endswith("}"):
            try:
                parsed = json.loads(obj)
                assert_no_secrets(parsed, f"{context}(parsed_json)")
            except Exception:
                pass


@dataclass(frozen=True)
class PersistedSecurityEvent:
    """Immutable representation of a recorded security verification event."""

    event_id: str
    timestamp: str
    verdict: str  # ACCEPT, SUSPICIOUS, ATTACK
    primary_reason: str
    reason_codes: tuple[str, ...]
    session_id: str | None = None
    scenario_id: str | None = None
    configuration_hash: str | None = None
    policy_id: str | None = None
    exceeded_count: int = 0
    is_explicit_violation: bool = False
    is_evidence_complete: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""

    def __post_init__(self) -> None:
        """Validate typing and invariants."""
        if not self.event_id or not self.event_id.strip():
            raise ValueError("event_id cannot be empty or whitespace.")
        if self.verdict not in (DecisionVerdict.ACCEPT.value, DecisionVerdict.SUSPICIOUS.value, DecisionVerdict.ATTACK.value):
            raise ValueError(f"Invalid verdict '{self.verdict}'. Must be ACCEPT, SUSPICIOUS, or ATTACK.")
        if not self.primary_reason or not self.primary_reason.strip():
            raise ValueError("primary_reason cannot be empty.")

        assert_no_secrets(self.metadata, "PersistedSecurityEvent.metadata")
        object.__setattr__(self, "reason_codes", tuple(str(r) for r in self.reason_codes))


@dataclass(frozen=True)
class PersistedEvidenceRecord:
    """Immutable representation of an individual evidence subsystem's output."""

    record_id: str
    event_id: str
    source: str  # IMPERSONATION, AUTHORIZATION, QUANTUM_CHANNEL, FUSION
    status: str
    primary_reason: str
    evidence_payload: dict[str, Any] = field(default_factory=dict)
    violations: tuple[str, ...] = ()
    created_at: str = ""

    def __post_init__(self) -> None:
        """Validate typing and invariants."""
        if not self.record_id or not self.record_id.strip():
            raise ValueError("record_id cannot be empty or whitespace.")
        if not self.event_id or not self.event_id.strip():
            raise ValueError("event_id cannot be empty or whitespace.")
        if not self.source or not self.source.strip():
            raise ValueError("source cannot be empty or whitespace.")

        assert_no_secrets(self.evidence_payload, "PersistedEvidenceRecord.evidence_payload")
        object.__setattr__(self, "violations", tuple(str(v) for v in self.violations))


@dataclass(frozen=True)
class PersistedEvaluationScenarioResult:
    """Immutable record of an individual M17 scenario outcome."""

    scenario_id: str
    category: str
    expected_verdict: str
    observed_verdict: str
    passed: bool
    mismatch_reason: str | None = None
    violations: tuple[str, ...] = ()


@dataclass(frozen=True)
class PersistedEvaluationRun:
    """Immutable representation of an M17 security evaluation suite run."""

    run_id: str
    timestamp: str
    total_scenarios: int
    passed_scenarios: int
    failed_scenarios: int
    pass_rate: float
    session_id: str | None = None
    confusion_matrix: dict[str, Any] = field(default_factory=dict)
    category_summaries: dict[str, Any] = field(default_factory=dict)
    scenario_results: tuple[PersistedEvaluationScenarioResult, ...] = ()
    created_at: str = ""

    def __post_init__(self) -> None:
        """Validate typing and invariants."""
        if not self.run_id or not self.run_id.strip():
            raise ValueError("run_id cannot be empty or whitespace.")
        if self.total_scenarios < 0 or self.passed_scenarios < 0 or self.failed_scenarios < 0:
            raise ValueError("Scenario counts must be non-negative.")

        assert_no_secrets(self.confusion_matrix, "PersistedEvaluationRun.confusion_matrix")
        assert_no_secrets(self.category_summaries, "PersistedEvaluationRun.category_summaries")
        object.__setattr__(self, "scenario_results", tuple(self.scenario_results))


@dataclass(frozen=True)
class PersistedBenchmarkResult:
    """Immutable record of an individual M18 benchmark measurement."""

    benchmark_id: str
    category: str
    workload_size: int
    iterations: int
    total_elapsed_seconds: float
    cpu_time_seconds: float | None = None
    mean_latency_seconds: float | None = None
    min_latency_seconds: float | None = None
    max_latency_seconds: float | None = None
    median_latency_seconds: float | None = None
    p95_latency_seconds: float | None = None
    throughput_ops_per_sec: float | None = None
    observed_verdicts: dict[str, int] = field(default_factory=dict)
    errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class PersistedBenchmarkRun:
    """Immutable representation of an M18 benchmark suite execution."""

    run_id: str
    suite_id: str
    timestamp: str
    total_benchmarks: int
    successful_benchmarks: int
    failed_benchmarks: int
    total_elapsed_seconds: float
    benchmark_results: tuple[PersistedBenchmarkResult, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""

    def __post_init__(self) -> None:
        """Validate typing and invariants."""
        if not self.run_id or not self.run_id.strip():
            raise ValueError("run_id cannot be empty or whitespace.")
        if self.total_benchmarks < 0 or self.successful_benchmarks < 0 or self.failed_benchmarks < 0:
            raise ValueError("Benchmark counts must be non-negative.")

        assert_no_secrets(self.metadata, "PersistedBenchmarkRun.metadata")
        object.__setattr__(self, "benchmark_results", tuple(self.benchmark_results))

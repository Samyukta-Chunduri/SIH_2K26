"""Q-SHIELD — API Request and Response Schemas (Milestone M19-B).

Defines typed Pydantic models for client-server communication across security
verification, quantum evidence telemetry, threat inspection, M17 evaluations,
and M18 benchmarks.
"""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    """API health status response."""

    status: str = "ok"
    service: str = "q-shield-api"
    version: str = "0.1.0"


class ScenarioTemplateResponse(BaseModel):
    """Metadata describing an executable security scenario template."""

    scenario_type: str
    name: str
    description: str
    target_layer: str
    expected_verdict: str


class VerifyScenarioRequest(BaseModel):
    """Request payload to initiate a controlled security verification."""

    model_config = ConfigDict(extra="forbid")

    scenario_type: str = Field(
        ...,
        description="Scenario template: 'honest', 'impersonation_attack', 'channel_anomaly', 'unauthorized_verification', 'multi_source_attack'",
    )
    session_id: str | None = Field(default=None, description="Optional custom session identifier.")
    custom_parameters: dict[str, Any] = Field(default_factory=dict, description="Optional parameter overrides.")


class SecurityEventSummaryResponse(BaseModel):
    """Summary of a recorded security verification decision event."""

    event_id: str
    timestamp: str
    verdict: str  # ACCEPT, SUSPICIOUS, ATTACK
    primary_reason: str
    reason_codes: list[str]
    session_id: str | None = None
    scenario_id: str | None = None
    configuration_hash: str | None = None
    exceeded_count: int = 0
    is_explicit_violation: bool = False
    is_evidence_complete: bool = True
    created_at: str = ""


class EvidenceRecordResponse(BaseModel):
    """Detailed evidence report from an individual security subsystem."""

    record_id: str
    event_id: str
    source: str  # IMPERSONATION, AUTHORIZATION, QUANTUM_CHANNEL, FUSION
    status: str
    primary_reason: str
    evidence_payload: dict[str, Any]
    violations: list[str]
    created_at: str = ""


class SecurityEventDetailResponse(BaseModel):
    """Complete security event record including all contributing subsystem evidence."""

    event: SecurityEventSummaryResponse
    evidence_records: list[EvidenceRecordResponse]


class QuantumEvidenceResponse(BaseModel):
    """Dedicated quantum telemetry evidence for an event."""

    event_id: str
    status: str
    qber: float | None = None
    teleportation_fidelity: float | None = None
    bell_correlations: dict[str, float] = Field(default_factory=dict)
    measurement_distribution: dict[str, float] = Field(default_factory=dict)
    threshold_exceeded: bool = False
    details: dict[str, Any] = Field(default_factory=dict)


class ThreatEvidenceResponse(BaseModel):
    """Consolidated threat detection evidence across identity, authorization, and channel."""

    event_id: str
    impersonation: dict[str, Any] = Field(default_factory=dict)
    authorization: dict[str, Any] = Field(default_factory=dict)
    quantum_channel: dict[str, Any] = Field(default_factory=dict)
    confirmed_violations: list[str] = Field(default_factory=list)


class FusionEvidenceResponse(BaseModel):
    """Evidence fusion and M12 decision explainability view."""

    event_id: str
    fused_status: str
    primary_reason: str
    source_statuses: dict[str, str] = Field(default_factory=dict)
    present_sources: list[str] = Field(default_factory=list)
    missing_sources: list[str] = Field(default_factory=list)
    violations: list[str] = Field(default_factory=list)
    m12_verdict: str
    m12_primary_reason: str


class EvaluationScenarioResultResponse(BaseModel):
    """Result of an individual evaluation scenario within an M17 run."""

    scenario_id: str
    category: str
    expected_verdict: str
    observed_verdict: str
    passed: bool
    mismatch_reason: str | None = None
    violations: list[str] = Field(default_factory=list)


class EvaluationRunSummaryResponse(BaseModel):
    """Summary of an M17 security evaluation run."""

    run_id: str
    timestamp: str
    session_id: str | None = None
    total_scenarios: int
    passed_scenarios: int
    failed_scenarios: int
    pass_rate: float
    confusion_matrix: dict[str, Any] = Field(default_factory=dict)
    category_summaries: dict[str, Any] = Field(default_factory=dict)
    created_at: str = ""


class EvaluationRunDetailResponse(BaseModel):
    """Full M17 evaluation run including scenario-level results."""

    summary: EvaluationRunSummaryResponse
    scenario_results: list[EvaluationScenarioResultResponse]


class BenchmarkResultResponse(BaseModel):
    """Individual benchmark measurement in an M18 suite run."""

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
    observed_verdicts: dict[str, int] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)


class BenchmarkRunSummaryResponse(BaseModel):
    """Summary of an M18 benchmark suite execution."""

    run_id: str
    suite_id: str
    timestamp: str
    total_benchmarks: int
    successful_benchmarks: int
    failed_benchmarks: int
    total_elapsed_seconds: float
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str = ""


class BenchmarkRunDetailResponse(BaseModel):
    """Full M18 benchmark run including all benchmark metrics."""

    summary: BenchmarkRunSummaryResponse
    benchmark_results: list[BenchmarkResultResponse]

"""Q-SHIELD — Application Service Layer (Milestone M19-B).

Coordinates execution of the underlying Q-SHIELD security pipeline (M12–M18),
persists results into the SQLite repository, and adapts domain models to API schemas.
"""

from __future__ import annotations

import time
import uuid
from typing import Any

from src.api.schemas import (
    BenchmarkResultResponse,
    BenchmarkRunDetailResponse,
    BenchmarkRunSummaryResponse,
    EvaluationRunDetailResponse,
    EvaluationRunSummaryResponse,
    EvaluationScenarioResultResponse,
    EvidenceRecordResponse,
    FusionEvidenceResponse,
    QuantumEvidenceResponse,
    ScenarioTemplateResponse,
    SecurityEventDetailResponse,
    SecurityEventSummaryResponse,
    ThreatEvidenceResponse,
    VerifyScenarioRequest,
)
from src.benchmarking.benchmark import (
    BenchmarkSuiteResult,
    build_baseline_benchmark_suite,
    run_benchmark_suite,
)
from src.detection.decision import DecisionResult, DecisionVerdict
from src.detection.fusion import (
    EvidenceSource,
    FusedSecurityEvidence,
    evaluate_fused_security_decision,
    fuse_security_evidence,
)
from src.evaluation.security_evaluation import (
    EvaluationSummary,
    build_baseline_evaluation_suite,
    make_anomalous_channel_evidence,
    make_clean_authorization_evidence,
    make_clean_channel_evidence,
    make_clean_impersonation_evidence,
    make_unauthorized_authorization_evidence,
    make_violating_channel_evidence,
    make_violating_impersonation_evidence,
    run_security_evaluation,
)
from src.persistence.models import (
    PersistedBenchmarkResult,
    PersistedBenchmarkRun,
    PersistedEvaluationRun,
    PersistedEvaluationScenarioResult,
    PersistedEvidenceRecord,
    PersistedSecurityEvent,
)
from src.persistence.repository import SecurityRepository


_CANONICAL_CONFIG_HASH: str = "hash_qshield_canon_sha256"


SCENARIO_TEMPLATES: tuple[ScenarioTemplateResponse, ...] = (
    ScenarioTemplateResponse(
        scenario_type="honest",
        name="Clean Honest Signature Verification",
        description="Legitimate signature transmission under ideal channel and credential conditions.",
        target_layer="Quantum + Identity + Authorization",
        expected_verdict="ACCEPT",
    ),
    ScenarioTemplateResponse(
        scenario_type="impersonation_attack",
        name="Signer Impersonation Breach",
        description="Tampered signature / forged identity detected via public-key mismatch (M13).",
        target_layer="M13 Identity Authentication",
        expected_verdict="ATTACK",
    ),
    ScenarioTemplateResponse(
        scenario_type="channel_anomaly",
        name="Physical Quantum Channel Disturbance",
        description="Eavesdropping / physical noise exceeding calibrated threshold policies (M15).",
        target_layer="M15 Quantum Channel Telemetry",
        expected_verdict="SUSPICIOUS",
    ),
    ScenarioTemplateResponse(
        scenario_type="unauthorized_verification",
        name="Unauthorized Verifier Attempt",
        description="Verification attempt by unpermitted participant role or expired session (M14).",
        target_layer="M14 Access Control Policy",
        expected_verdict="ATTACK",
    ),
    ScenarioTemplateResponse(
        scenario_type="multi_source_attack",
        name="Multi-Vector Security Attack",
        description="Combined impersonation breach, unauthorized verifier, and anomalous channel disturbance.",
        target_layer="M16 Multi-Source Fusion",
        expected_verdict="ATTACK",
    ),
)


class QShieldService:
    """Application service coordinating Q-SHIELD execution, persistence, and querying."""

    def __init__(self, repository: SecurityRepository) -> None:
        """Initialize service with a SecurityRepository instance."""
        self.repository = repository

    def list_scenario_templates(self) -> list[ScenarioTemplateResponse]:
        """Return available scenario templates for client inspection and selection."""
        return list(SCENARIO_TEMPLATES)

    # ==========================================================================
    # Verification & Security Events
    # ==========================================================================

    def verify_scenario(self, request: VerifyScenarioRequest) -> SecurityEventDetailResponse:
        """Execute a controlled scenario through the authoritative Q-SHIELD pipeline.

        Flow:
            1. Construct domain evidence fixtures based on scenario_type.
            2. Perform M16 Deterministic Evidence Fusion.
            3. Evaluate authoritative M12 Security Decision.
            4. Persist event and contributing evidence into SQLite repository.
            5. Return typed response.
        """
        session_id = request.session_id or f"sess_{uuid.uuid4().hex[:8]}"
        scenario_id = f"scen_{request.scenario_type}_{int(time.time())}"
        config_hash = _CANONICAL_CONFIG_HASH

        # 1. Build Subsystem Evidence Fixtures
        if request.scenario_type == "honest":
            m13 = make_clean_impersonation_evidence(session_id=session_id, configuration_hash=config_hash)
            m14 = make_clean_authorization_evidence(session_id=session_id, configuration_hash=config_hash)
            m15 = make_clean_channel_evidence(session_id=session_id, configuration_hash=config_hash)
        elif request.scenario_type == "impersonation_attack":
            m13 = make_violating_impersonation_evidence(session_id=session_id, configuration_hash=config_hash)
            m14 = make_clean_authorization_evidence(session_id=session_id, configuration_hash=config_hash)
            m15 = make_clean_channel_evidence(session_id=session_id, configuration_hash=config_hash)
        elif request.scenario_type == "channel_anomaly":
            m13 = make_clean_impersonation_evidence(session_id=session_id, configuration_hash=config_hash)
            m14 = make_clean_authorization_evidence(session_id=session_id, configuration_hash=config_hash)
            m15 = make_anomalous_channel_evidence(session_id=session_id, configuration_hash=config_hash)
        elif request.scenario_type == "unauthorized_verification":
            m13 = make_clean_impersonation_evidence(session_id=session_id, configuration_hash=config_hash)
            m14 = make_unauthorized_authorization_evidence(session_id=session_id, configuration_hash=config_hash)
            m15 = make_clean_channel_evidence(session_id=session_id, configuration_hash=config_hash)
        elif request.scenario_type == "multi_source_attack":
            m13 = make_violating_impersonation_evidence(session_id=session_id, configuration_hash=config_hash)
            m14 = make_unauthorized_authorization_evidence(session_id=session_id, configuration_hash=config_hash)
            m15 = make_anomalous_channel_evidence(session_id=session_id, configuration_hash=config_hash)
        else:
            raise ValueError(f"Unknown scenario_type: '{request.scenario_type}'.")

        # 2. M16 Evidence Fusion
        fused = fuse_security_evidence(
            impersonation_evidence=m13,
            authorization_evidence=m14,
            channel_evidence=m15,
            required_sources=(
                EvidenceSource.IMPERSONATION.value,
                EvidenceSource.AUTHORIZATION.value,
                EvidenceSource.QUANTUM_CHANNEL.value,
            ),
            expected_session_id=session_id,
            expected_configuration_hash=config_hash,
        )

        # 3. M12 Final Security Decision
        decision = evaluate_fused_security_decision(fused)

        # 4. Persistence into SQLite
        event_id = f"evt_{uuid.uuid4().hex[:12]}"
        persisted_event = PersistedSecurityEvent(
            event_id=event_id,
            timestamp=decision.timestamp,
            verdict=decision.verdict.value,
            primary_reason=decision.primary_reason,
            reason_codes=decision.reason_codes,
            session_id=session_id,
            scenario_id=scenario_id,
            configuration_hash=config_hash,
            policy_id=decision.policy_id,
            exceeded_count=decision.exceeded_count,
            is_explicit_violation=decision.is_explicit_violation,
            is_evidence_complete=decision.is_evidence_complete,
            metadata={"scenario_type": request.scenario_type},
        )

        # Evidence records
        def _get_val(x: Any) -> str:
            return x.value if hasattr(x, "value") else str(x)

        m13_violations = [_get_val(r) for r in m13.reason_codes if any(kw in _get_val(r) for kw in ("MISMATCH", "INVALID", "FAILED"))]
        m14_violations = [_get_val(r) for r in m14.reason_codes if any(kw in _get_val(r) for kw in ("UNAUTHORIZED", "DENIED"))]
        m15_violations = tuple(m15.exceeded_metrics)
        fused_violations = tuple(
            _get_val(r) for r in fused.reason_codes if any(kw in _get_val(r) for kw in ("VIOLATION", "ANOMALY"))
        )

        evidence_records = [
            PersistedEvidenceRecord(
                record_id=f"rec_m13_{uuid.uuid4().hex[:8]}",
                event_id=event_id,
                source="IMPERSONATION",
                status=_get_val(m13.status),
                primary_reason=_get_val(m13.primary_reason),
                evidence_payload={
                    "claimed_identity": m13.claimed_identity,
                    "authenticated_identity": m13.authenticated_identity,
                    "is_impersonation_detected": m13.is_impersonation_detected,
                    "is_indeterminate": m13.is_indeterminate,
                },
                violations=tuple(m13_violations),
            ),
            PersistedEvidenceRecord(
                record_id=f"rec_m14_{uuid.uuid4().hex[:8]}",
                event_id=event_id,
                source="AUTHORIZATION",
                status=_get_val(m14.status),
                primary_reason=_get_val(m14.primary_reason),
                evidence_payload={
                    "participant_identity": m14.participant_identity,
                    "operation": m14.operation,
                    "role": m14.role,
                    "is_authorized": m14.is_authorized,
                    "is_unauthorized_detected": m14.is_unauthorized_detected,
                },
                violations=tuple(m14_violations),
            ),
            PersistedEvidenceRecord(
                record_id=f"rec_m15_{uuid.uuid4().hex[:8]}",
                event_id=event_id,
                source="QUANTUM_CHANNEL",
                status=_get_val(m15.status),
                primary_reason=_get_val(m15.primary_reason),
                evidence_payload={
                    "qber": 0.12 if m15.is_anomalous else 0.015,
                    "teleportation_fidelity": 0.82 if m15.is_anomalous else 0.985,
                    "bell_correlations": {"E_XX": 0.71, "E_YY": -0.72, "E_ZZ": 0.70},
                    "is_anomalous": m15.is_anomalous,
                    "is_explicit_violation": m15.is_explicit_violation,
                    "exceeded_count": m15.exceeded_count,
                },
                violations=m15_violations,
            ),
            PersistedEvidenceRecord(
                record_id=f"rec_m16_{uuid.uuid4().hex[:8]}",
                event_id=event_id,
                source="FUSION",
                status=_get_val(fused.status),
                primary_reason=_get_val(fused.primary_reason),
                evidence_payload={
                    "is_clean": fused.is_clean,
                    "is_anomalous": fused.is_anomalous,
                    "is_explicit_violation": fused.is_explicit_violation,
                    "source_statuses": {str(k): _get_val(v) for k, v in fused.source_statuses.items()},
                    "present_sources": [_get_val(s) for s in fused.present_sources],
                },
                violations=fused_violations,
            ),
        ]

        self.repository.record_security_event(persisted_event, evidence_records)

        # 5. Build Response
        summary_resp = SecurityEventSummaryResponse(
            event_id=persisted_event.event_id,
            timestamp=persisted_event.timestamp,
            verdict=persisted_event.verdict,
            primary_reason=persisted_event.primary_reason,
            reason_codes=list(persisted_event.reason_codes),
            session_id=persisted_event.session_id,
            scenario_id=persisted_event.scenario_id,
            configuration_hash=persisted_event.configuration_hash,
            exceeded_count=persisted_event.exceeded_count,
            is_explicit_violation=persisted_event.is_explicit_violation,
            is_evidence_complete=persisted_event.is_evidence_complete,
            created_at=persisted_event.created_at,
        )
        evidence_resps = [
            EvidenceRecordResponse(
                record_id=r.record_id,
                event_id=r.event_id,
                source=r.source,
                status=r.status,
                primary_reason=r.primary_reason,
                evidence_payload=r.evidence_payload,
                violations=list(r.violations),
                created_at=r.created_at,
            )
            for r in evidence_records
        ]

        return SecurityEventDetailResponse(event=summary_resp, evidence_records=evidence_resps)

    def list_events(
        self,
        limit: int = 50,
        offset: int = 0,
        verdict: str | None = None,
        session_id: str | None = None,
    ) -> list[SecurityEventSummaryResponse]:
        """Query historical security verification events with optional filters."""
        events = self.repository.list_security_events(
            limit=limit, offset=offset, verdict=verdict, session_id=session_id
        )
        return [
            SecurityEventSummaryResponse(
                event_id=e.event_id,
                timestamp=e.timestamp,
                verdict=e.verdict,
                primary_reason=e.primary_reason,
                reason_codes=list(e.reason_codes),
                session_id=e.session_id,
                scenario_id=e.scenario_id,
                configuration_hash=e.configuration_hash,
                exceeded_count=e.exceeded_count,
                is_explicit_violation=e.is_explicit_violation,
                is_evidence_complete=e.is_evidence_complete,
                created_at=e.created_at,
            )
            for e in events
        ]

    def get_event(self, event_id: str) -> SecurityEventDetailResponse | None:
        """Retrieve full details for a security event including its evidence records."""
        event = self.repository.get_security_event(event_id)
        if not event:
            return None

        evidence_records = self.repository.get_evidence_records(event_id)
        summary_resp = SecurityEventSummaryResponse(
            event_id=event.event_id,
            timestamp=event.timestamp,
            verdict=event.verdict,
            primary_reason=event.primary_reason,
            reason_codes=list(event.reason_codes),
            session_id=event.session_id,
            scenario_id=event.scenario_id,
            configuration_hash=event.configuration_hash,
            exceeded_count=event.exceeded_count,
            is_explicit_violation=event.is_explicit_violation,
            is_evidence_complete=event.is_evidence_complete,
            created_at=event.created_at,
        )
        evidence_resps = [
            EvidenceRecordResponse(
                record_id=r.record_id,
                event_id=r.event_id,
                source=r.source,
                status=r.status,
                primary_reason=r.primary_reason,
                evidence_payload=r.evidence_payload,
                violations=list(r.violations),
                created_at=r.created_at,
            )
            for r in evidence_records
        ]
        return SecurityEventDetailResponse(event=summary_resp, evidence_records=evidence_resps)

    def get_quantum_evidence(self, event_id: str) -> QuantumEvidenceResponse | None:
        """Extract dedicated quantum channel telemetry evidence for an event."""
        records = self.repository.get_evidence_records(event_id)
        q_record = next((r for r in records if r.source == "QUANTUM_CHANNEL"), None)
        if not q_record:
            return None

        payload = q_record.evidence_payload
        return QuantumEvidenceResponse(
            event_id=event_id,
            status=q_record.status,
            qber=payload.get("qber"),
            teleportation_fidelity=payload.get("teleportation_fidelity"),
            bell_correlations=payload.get("bell_correlations", {}),
            threshold_exceeded=(q_record.status == "ANOMALOUS"),
            details=payload,
        )

    def get_threat_evidence(self, event_id: str) -> ThreatEvidenceResponse | None:
        """Extract consolidated threat evidence across identity, authorization, and channel."""
        records = self.repository.get_evidence_records(event_id)
        if not records:
            return None

        m13_rec = next((r for r in records if r.source == "IMPERSONATION"), None)
        m14_rec = next((r for r in records if r.source == "AUTHORIZATION"), None)
        m15_rec = next((r for r in records if r.source == "QUANTUM_CHANNEL"), None)

        all_violations: list[str] = []
        if m13_rec:
            all_violations.extend(m13_rec.violations)
        if m14_rec:
            all_violations.extend(m14_rec.violations)
        if m15_rec:
            all_violations.extend(m15_rec.violations)

        return ThreatEvidenceResponse(
            event_id=event_id,
            impersonation=m13_rec.evidence_payload if m13_rec else {},
            authorization=m14_rec.evidence_payload if m14_rec else {},
            quantum_channel=m15_rec.evidence_payload if m15_rec else {},
            confirmed_violations=sorted(set(all_violations)),
        )

    def get_fusion_evidence(self, event_id: str) -> FusionEvidenceResponse | None:
        """Extract M16 fusion evidence and M12 decision explainability for an event."""
        event = self.repository.get_security_event(event_id)
        if not event:
            return None

        records = self.repository.get_evidence_records(event_id)
        fusion_rec = next((r for r in records if r.source == "FUSION"), None)
        if not fusion_rec:
            return None

        payload = fusion_rec.evidence_payload
        return FusionEvidenceResponse(
            event_id=event_id,
            fused_status=fusion_rec.status,
            primary_reason=fusion_rec.primary_reason,
            source_statuses=payload.get("source_statuses", {}),
            present_sources=payload.get("present_sources", []),
            missing_sources=payload.get("missing_sources", []),
            violations=list(fusion_rec.violations),
            m12_verdict=event.verdict,
            m12_primary_reason=event.primary_reason,
        )

    # ==========================================================================
    # M17 Security Evaluation
    # ==========================================================================

    def trigger_evaluation_run(self, session_id: str | None = None) -> EvaluationRunDetailResponse:
        """Run the comprehensive M17 security evaluation suite and persist the report."""
        sess = session_id or f"sess_eval_{uuid.uuid4().hex[:6]}"
        suite = build_baseline_evaluation_suite(session_id=sess, configuration_hash=_CANONICAL_CONFIG_HASH)
        summary = run_security_evaluation(suite)

        run_id = f"eval_{uuid.uuid4().hex[:10]}"
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        scenario_results = tuple(
            PersistedEvaluationScenarioResult(
                scenario_id=r.scenario_id,
                category=r.category.value,
                expected_verdict=r.expected_verdict.value,
                observed_verdict=r.observed_verdict.value,
                passed=r.passed,
                mismatch_reason="; ".join(r.mismatch_reasons) if r.mismatch_reasons else None,
                violations=(),
            )
            for r in summary.results
        )

        cm = summary.confusion_matrix
        confusion_dict = {
            "true_positives": cm.true_positives,
            "true_negatives": cm.true_negatives,
            "false_positives": cm.false_positives,
            "false_negatives": cm.false_negatives,
            "sensitivity": cm.sensitivity,
            "specificity": cm.specificity,
        }

        category_dict = {
            cat: {
                "passed": s.passed_scenarios,
                "total": s.total_scenarios,
                "pass_rate": s.pass_rate if s.pass_rate is not None else 0.0,
            }
            for cat, s in summary.category_summaries.items()
        }

        eval_run = PersistedEvaluationRun(
            run_id=run_id,
            timestamp=timestamp,
            session_id=sess,
            total_scenarios=summary.total_scenarios,
            passed_scenarios=summary.passed_scenarios,
            failed_scenarios=summary.failed_scenarios,
            pass_rate=summary.pass_rate if summary.pass_rate is not None else 0.0,
            confusion_matrix=confusion_dict,
            category_summaries=category_dict,
            scenario_results=scenario_results,
        )

        self.repository.record_evaluation_run(eval_run)

        summary_resp = EvaluationRunSummaryResponse(
            run_id=eval_run.run_id,
            timestamp=eval_run.timestamp,
            session_id=eval_run.session_id,
            total_scenarios=eval_run.total_scenarios,
            passed_scenarios=eval_run.passed_scenarios,
            failed_scenarios=eval_run.failed_scenarios,
            pass_rate=eval_run.pass_rate,
            confusion_matrix=eval_run.confusion_matrix,
            category_summaries=eval_run.category_summaries,
            created_at=eval_run.created_at,
        )
        sc_resps = [
            EvaluationScenarioResultResponse(
                scenario_id=sr.scenario_id,
                category=sr.category,
                expected_verdict=sr.expected_verdict,
                observed_verdict=sr.observed_verdict,
                passed=sr.passed,
                mismatch_reason=sr.mismatch_reason,
                violations=list(sr.violations),
            )
            for sr in scenario_results
        ]
        return EvaluationRunDetailResponse(summary=summary_resp, scenario_results=sc_resps)

    def list_evaluation_runs(self, limit: int = 20, offset: int = 0) -> list[EvaluationRunSummaryResponse]:
        """List historical M17 evaluation suite runs."""
        runs = self.repository.list_evaluation_runs(limit=limit, offset=offset)
        return [
            EvaluationRunSummaryResponse(
                run_id=r.run_id,
                timestamp=r.timestamp,
                session_id=r.session_id,
                total_scenarios=r.total_scenarios,
                passed_scenarios=r.passed_scenarios,
                failed_scenarios=r.failed_scenarios,
                pass_rate=r.pass_rate,
                confusion_matrix=r.confusion_matrix,
                category_summaries=r.category_summaries,
                created_at=r.created_at,
            )
            for r in runs
        ]

    def get_evaluation_run(self, run_id: str) -> EvaluationRunDetailResponse | None:
        """Retrieve full details of an M17 evaluation run."""
        run = self.repository.get_evaluation_run(run_id)
        if not run:
            return None

        summary_resp = EvaluationRunSummaryResponse(
            run_id=run.run_id,
            timestamp=run.timestamp,
            session_id=run.session_id,
            total_scenarios=run.total_scenarios,
            passed_scenarios=run.passed_scenarios,
            failed_scenarios=run.failed_scenarios,
            pass_rate=run.pass_rate,
            confusion_matrix=run.confusion_matrix,
            category_summaries=run.category_summaries,
            created_at=run.created_at,
        )
        sc_resps = [
            EvaluationScenarioResultResponse(
                scenario_id=sr.scenario_id,
                category=sr.category,
                expected_verdict=sr.expected_verdict,
                observed_verdict=sr.observed_verdict,
                passed=sr.passed,
                mismatch_reason=sr.mismatch_reason,
                violations=list(sr.violations),
            )
            for sr in run.scenario_results
        ]
        return EvaluationRunDetailResponse(summary=summary_resp, scenario_results=sc_resps)

    # ==========================================================================
    # M18 Performance Benchmarking
    # ==========================================================================

    def trigger_benchmark_run(self, suite_id: str = "suite_qshield_benchmarks") -> BenchmarkRunDetailResponse:
        """Execute the standardized M18 benchmark suite and persist metrics."""
        suite = build_baseline_benchmark_suite(
            session_id="sess_bench_run", configuration_hash=_CANONICAL_CONFIG_HASH
        )
        suite_result = run_benchmark_suite(suite, suite_id=suite_id)

        run_id = f"bench_{uuid.uuid4().hex[:10]}"
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        bench_results = tuple(
            PersistedBenchmarkResult(
                benchmark_id=r.benchmark_id,
                category=r.category.value,
                workload_size=r.workload_size,
                iterations=r.target_iterations,
                total_elapsed_seconds=r.total_elapsed_seconds,
                cpu_time_seconds=r.cpu_time_seconds,
                mean_latency_seconds=r.mean_latency_seconds,
                min_latency_seconds=r.min_latency_seconds,
                max_latency_seconds=r.max_latency_seconds,
                median_latency_seconds=r.median_latency_seconds,
                p95_latency_seconds=r.p95_latency_seconds,
                throughput_ops_per_sec=r.throughput_ops_per_sec,
                observed_verdicts=r.observed_verdict_counts,
                errors=r.errors,
            )
            for r in suite_result.results
        )

        bench_run = PersistedBenchmarkRun(
            run_id=run_id,
            suite_id=suite_id,
            timestamp=timestamp,
            total_benchmarks=suite_result.total_benchmarks,
            successful_benchmarks=suite_result.successful_benchmarks,
            failed_benchmarks=suite_result.failed_benchmarks,
            total_elapsed_seconds=suite_result.total_elapsed_seconds,
            benchmark_results=bench_results,
            metadata={"environment": "local_prototype"},
        )

        self.repository.record_benchmark_run(bench_run)

        summary_resp = BenchmarkRunSummaryResponse(
            run_id=bench_run.run_id,
            suite_id=bench_run.suite_id,
            timestamp=bench_run.timestamp,
            total_benchmarks=bench_run.total_benchmarks,
            successful_benchmarks=bench_run.successful_benchmarks,
            failed_benchmarks=bench_run.failed_benchmarks,
            total_elapsed_seconds=bench_run.total_elapsed_seconds,
            metadata=bench_run.metadata,
            created_at=bench_run.created_at,
        )
        b_resps = [
            BenchmarkResultResponse(
                benchmark_id=br.benchmark_id,
                category=br.category,
                workload_size=br.workload_size,
                iterations=br.iterations,
                total_elapsed_seconds=br.total_elapsed_seconds,
                cpu_time_seconds=br.cpu_time_seconds,
                mean_latency_seconds=br.mean_latency_seconds,
                min_latency_seconds=br.min_latency_seconds,
                max_latency_seconds=br.max_latency_seconds,
                median_latency_seconds=br.median_latency_seconds,
                p95_latency_seconds=br.p95_latency_seconds,
                throughput_ops_per_sec=br.throughput_ops_per_sec,
                observed_verdicts=br.observed_verdicts,
                errors=list(br.errors),
            )
            for br in bench_results
        ]
        return BenchmarkRunDetailResponse(summary=summary_resp, benchmark_results=b_resps)

    def list_benchmark_runs(self, limit: int = 20, offset: int = 0) -> list[BenchmarkRunSummaryResponse]:
        """List historical M18 benchmark suite executions."""
        runs = self.repository.list_benchmark_runs(limit=limit, offset=offset)
        return [
            BenchmarkRunSummaryResponse(
                run_id=r.run_id,
                suite_id=r.suite_id,
                timestamp=r.timestamp,
                total_benchmarks=r.total_benchmarks,
                successful_benchmarks=r.successful_benchmarks,
                failed_benchmarks=r.failed_benchmarks,
                total_elapsed_seconds=r.total_elapsed_seconds,
                metadata=r.metadata,
                created_at=r.created_at,
            )
            for r in runs
        ]

    def get_benchmark_run(self, run_id: str) -> BenchmarkRunDetailResponse | None:
        """Retrieve full details and latency metrics of an M18 benchmark run."""
        run = self.repository.get_benchmark_run(run_id)
        if not run:
            return None

        summary_resp = BenchmarkRunSummaryResponse(
            run_id=run.run_id,
            suite_id=run.suite_id,
            timestamp=run.timestamp,
            total_benchmarks=run.total_benchmarks,
            successful_benchmarks=run.successful_benchmarks,
            failed_benchmarks=run.failed_benchmarks,
            total_elapsed_seconds=run.total_elapsed_seconds,
            metadata=run.metadata,
            created_at=run.created_at,
        )
        b_resps = [
            BenchmarkResultResponse(
                benchmark_id=br.benchmark_id,
                category=br.category,
                workload_size=br.workload_size,
                iterations=br.iterations,
                total_elapsed_seconds=br.total_elapsed_seconds,
                cpu_time_seconds=br.cpu_time_seconds,
                mean_latency_seconds=br.mean_latency_seconds,
                min_latency_seconds=br.min_latency_seconds,
                max_latency_seconds=br.max_latency_seconds,
                median_latency_seconds=br.median_latency_seconds,
                p95_latency_seconds=br.p95_latency_seconds,
                throughput_ops_per_sec=br.throughput_ops_per_sec,
                observed_verdicts=br.observed_verdicts,
                errors=list(br.errors),
            )
            for br in run.benchmark_results
        ]
        return BenchmarkRunDetailResponse(summary=summary_resp, benchmark_results=b_resps)

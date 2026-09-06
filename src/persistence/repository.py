"""Q-SHIELD — Persistence Repository (Milestone M19-A).

Provides parameterized database access methods for recording and querying
security events, multi-source evidence, M17 evaluation runs, and M18 benchmark metrics.
"""

from __future__ import annotations

from collections.abc import Sequence
import json
import sqlite3
from typing import Any

from src.detection.decision import DecisionResult
from src.detection.fusion import FusedSecurityEvidence
from src.evaluation.security_evaluation import EvaluationSummary
from src.benchmarking.benchmark import BenchmarkSuiteResult
from src.persistence.database import DatabaseManager
from src.persistence.models import (
    PersistedBenchmarkResult,
    PersistedBenchmarkRun,
    PersistedEvaluationRun,
    PersistedEvaluationScenarioResult,
    PersistedEvidenceRecord,
    PersistedSecurityEvent,
    assert_no_secrets,
)


class SecurityRepository:
    """Data access repository for Q-SHIELD persistence."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        """Initialize repository with a DatabaseManager instance."""
        self.db_manager = db_manager

    # ==========================================================================
    # Security Events & Evidence Records
    # ==========================================================================

    def record_security_event(
        self,
        event: PersistedSecurityEvent,
        evidence_records: Sequence[PersistedEvidenceRecord] = (),
    ) -> None:
        """Persist an authoritative security decision event along with its contributing evidence records.

        Args:
            event: Validated PersistedSecurityEvent.
            evidence_records: Sequence of contributing PersistedEvidenceRecord objects.
        """
        assert_no_secrets(event.metadata, "event.metadata")
        for rec in evidence_records:
            assert_no_secrets(rec.evidence_payload, f"evidence_payload[{rec.source}]")

        with self.db_manager.connection() as conn:
            conn.execute(
                """
                INSERT INTO security_events (
                    event_id, timestamp, verdict, primary_reason, reason_codes_json,
                    session_id, scenario_id, configuration_hash, policy_id,
                    exceeded_count, is_explicit_violation, is_evidence_complete, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.event_id,
                    event.timestamp,
                    event.verdict,
                    event.primary_reason,
                    json.dumps(event.reason_codes),
                    event.session_id,
                    event.scenario_id,
                    event.configuration_hash,
                    event.policy_id,
                    event.exceeded_count,
                    1 if event.is_explicit_violation else 0,
                    1 if event.is_evidence_complete else 0,
                    json.dumps(event.metadata),
                ),
            )

            for rec in evidence_records:
                conn.execute(
                    """
                    INSERT INTO evidence_records (
                        record_id, event_id, source, status, primary_reason,
                        evidence_json, violations_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        rec.record_id,
                        event.event_id,
                        rec.source,
                        rec.status,
                        rec.primary_reason,
                        json.dumps(rec.evidence_payload),
                        json.dumps(rec.violations),
                    ),
                )

    def get_security_event(self, event_id: str) -> PersistedSecurityEvent | None:
        """Retrieve a specific security event by its identifier."""
        with self.db_manager.connection() as conn:
            row = conn.execute(
                "SELECT * FROM security_events WHERE event_id = ?", (event_id,)
            ).fetchone()
            if not row:
                return None
            return self._row_to_event(row)

    def list_security_events(
        self,
        limit: int = 50,
        offset: int = 0,
        verdict: str | None = None,
        session_id: str | None = None,
    ) -> list[PersistedSecurityEvent]:
        """Query security events with optional filtering and pagination."""
        query = "SELECT * FROM security_events WHERE 1=1"
        params: list[Any] = []

        if verdict:
            query += " AND verdict = ?"
            params.append(verdict)
        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)

        query += " ORDER BY timestamp DESC, rowid DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self.db_manager.connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_event(r) for r in rows]

    def get_evidence_records(self, event_id: str) -> list[PersistedEvidenceRecord]:
        """Retrieve all evidence records associated with a specific security event."""
        with self.db_manager.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM evidence_records WHERE event_id = ? ORDER BY rowid ASC",
                (event_id,),
            ).fetchall()
            return [self._row_to_evidence(r) for r in rows]

    # ==========================================================================
    # M17 Security Evaluation Runs
    # ==========================================================================

    def record_evaluation_run(self, eval_run: PersistedEvaluationRun) -> None:
        """Persist an M17 evaluation suite run and all individual scenario results."""
        with self.db_manager.connection() as conn:
            conn.execute(
                """
                INSERT INTO evaluation_runs (
                    run_id, timestamp, session_id, total_scenarios, passed_scenarios,
                    failed_scenarios, pass_rate, confusion_matrix_json, category_summaries_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    eval_run.run_id,
                    eval_run.timestamp,
                    eval_run.session_id,
                    eval_run.total_scenarios,
                    eval_run.passed_scenarios,
                    eval_run.failed_scenarios,
                    eval_run.pass_rate,
                    json.dumps(eval_run.confusion_matrix),
                    json.dumps(eval_run.category_summaries),
                ),
            )

            for sc_res in eval_run.scenario_results:
                conn.execute(
                    """
                    INSERT INTO evaluation_results (
                        run_id, scenario_id, category, expected_verdict, observed_verdict,
                        passed, mismatch_reason, violations_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        eval_run.run_id,
                        sc_res.scenario_id,
                        sc_res.category,
                        sc_res.expected_verdict,
                        sc_res.observed_verdict,
                        1 if sc_res.passed else 0,
                        sc_res.mismatch_reason,
                        json.dumps(sc_res.violations),
                    ),
                )

    def get_evaluation_run(self, run_id: str) -> PersistedEvaluationRun | None:
        """Retrieve an M17 evaluation run and all its scenario results."""
        with self.db_manager.connection() as conn:
            run_row = conn.execute(
                "SELECT * FROM evaluation_runs WHERE run_id = ?", (run_id,)
            ).fetchone()
            if not run_row:
                return None

            result_rows = conn.execute(
                "SELECT * FROM evaluation_results WHERE run_id = ? ORDER BY id ASC",
                (run_id,),
            ).fetchall()

            scenario_results = tuple(
                PersistedEvaluationScenarioResult(
                    scenario_id=r["scenario_id"],
                    category=r["category"],
                    expected_verdict=r["expected_verdict"],
                    observed_verdict=r["observed_verdict"],
                    passed=bool(r["passed"]),
                    mismatch_reason=r["mismatch_reason"],
                    violations=tuple(json.loads(r["violations_json"])),
                )
                for r in result_rows
            )

            return PersistedEvaluationRun(
                run_id=run_row["run_id"],
                timestamp=run_row["timestamp"],
                total_scenarios=run_row["total_scenarios"],
                passed_scenarios=run_row["passed_scenarios"],
                failed_scenarios=run_row["failed_scenarios"],
                pass_rate=run_row["pass_rate"],
                session_id=run_row["session_id"],
                confusion_matrix=json.loads(run_row["confusion_matrix_json"]),
                category_summaries=json.loads(run_row["category_summaries_json"]),
                scenario_results=scenario_results,
                created_at=run_row["created_at"],
            )

    def list_evaluation_runs(self, limit: int = 20, offset: int = 0) -> list[PersistedEvaluationRun]:
        """List historical M17 evaluation runs."""
        with self.db_manager.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM evaluation_runs ORDER BY timestamp DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
            return [
                PersistedEvaluationRun(
                    run_id=r["run_id"],
                    timestamp=r["timestamp"],
                    total_scenarios=r["total_scenarios"],
                    passed_scenarios=r["passed_scenarios"],
                    failed_scenarios=r["failed_scenarios"],
                    pass_rate=r["pass_rate"],
                    session_id=r["session_id"],
                    confusion_matrix=json.loads(r["confusion_matrix_json"]),
                    category_summaries=json.loads(r["category_summaries_json"]),
                    created_at=r["created_at"],
                )
                for r in rows
            ]

    # ==========================================================================
    # M18 Performance Benchmark Runs
    # ==========================================================================

    def record_benchmark_run(self, bench_run: PersistedBenchmarkRun) -> None:
        """Persist an M18 benchmark suite run and individual benchmark records."""
        with self.db_manager.connection() as conn:
            conn.execute(
                """
                INSERT INTO benchmark_runs (
                    run_id, suite_id, timestamp, total_benchmarks, successful_benchmarks,
                    failed_benchmarks, total_elapsed_seconds, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    bench_run.run_id,
                    bench_run.suite_id,
                    bench_run.timestamp,
                    bench_run.total_benchmarks,
                    bench_run.successful_benchmarks,
                    bench_run.failed_benchmarks,
                    bench_run.total_elapsed_seconds,
                    json.dumps(bench_run.metadata),
                ),
            )

            for b in bench_run.benchmark_results:
                conn.execute(
                    """
                    INSERT INTO benchmark_results (
                        run_id, benchmark_id, category, workload_size, iterations,
                        total_elapsed_seconds, cpu_time_seconds, mean_latency_seconds,
                        min_latency_seconds, max_latency_seconds, median_latency_seconds,
                        p95_latency_seconds, throughput_ops_per_sec, observed_verdicts_json,
                        errors_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        bench_run.run_id,
                        b.benchmark_id,
                        b.category,
                        b.workload_size,
                        b.iterations,
                        b.total_elapsed_seconds,
                        b.cpu_time_seconds,
                        b.mean_latency_seconds,
                        b.min_latency_seconds,
                        b.max_latency_seconds,
                        b.median_latency_seconds,
                        b.p95_latency_seconds,
                        b.throughput_ops_per_sec,
                        json.dumps(b.observed_verdicts),
                        json.dumps(b.errors),
                    ),
                )

    def get_benchmark_run(self, run_id: str) -> PersistedBenchmarkRun | None:
        """Retrieve an M18 benchmark run and all individual results."""
        with self.db_manager.connection() as conn:
            run_row = conn.execute(
                "SELECT * FROM benchmark_runs WHERE run_id = ?", (run_id,)
            ).fetchone()
            if not run_row:
                return None

            result_rows = conn.execute(
                "SELECT * FROM benchmark_results WHERE run_id = ? ORDER BY id ASC",
                (run_id,),
            ).fetchall()

            benchmark_results = tuple(
                PersistedBenchmarkResult(
                    benchmark_id=r["benchmark_id"],
                    category=r["category"],
                    workload_size=r["workload_size"],
                    iterations=r["iterations"],
                    total_elapsed_seconds=r["total_elapsed_seconds"],
                    cpu_time_seconds=r["cpu_time_seconds"],
                    mean_latency_seconds=r["mean_latency_seconds"],
                    min_latency_seconds=r["min_latency_seconds"],
                    max_latency_seconds=r["max_latency_seconds"],
                    median_latency_seconds=r["median_latency_seconds"],
                    p95_latency_seconds=r["p95_latency_seconds"],
                    throughput_ops_per_sec=r["throughput_ops_per_sec"],
                    observed_verdicts=json.loads(r["observed_verdicts_json"]),
                    errors=tuple(json.loads(r["errors_json"])),
                )
                for r in result_rows
            )

            return PersistedBenchmarkRun(
                run_id=run_row["run_id"],
                suite_id=run_row["suite_id"],
                timestamp=run_row["timestamp"],
                total_benchmarks=run_row["total_benchmarks"],
                successful_benchmarks=run_row["successful_benchmarks"],
                failed_benchmarks=run_row["failed_benchmarks"],
                total_elapsed_seconds=run_row["total_elapsed_seconds"],
                benchmark_results=benchmark_results,
                metadata=json.loads(run_row["metadata_json"]),
                created_at=run_row["created_at"],
            )

    def list_benchmark_runs(self, limit: int = 20, offset: int = 0) -> list[PersistedBenchmarkRun]:
        """List historical M18 benchmark suite runs."""
        with self.db_manager.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM benchmark_runs ORDER BY timestamp DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
            return [
                PersistedBenchmarkRun(
                    run_id=r["run_id"],
                    suite_id=r["suite_id"],
                    timestamp=r["timestamp"],
                    total_benchmarks=r["total_benchmarks"],
                    successful_benchmarks=r["successful_benchmarks"],
                    failed_benchmarks=r["failed_benchmarks"],
                    total_elapsed_seconds=r["total_elapsed_seconds"],
                    metadata=json.loads(r["metadata_json"]),
                    created_at=r["created_at"],
                )
                for r in rows
            ]

    # ==========================================================================
    # Row Deserialization Helpers
    # ==========================================================================

    @staticmethod
    def _row_to_event(row: sqlite3.Row) -> PersistedSecurityEvent:
        return PersistedSecurityEvent(
            event_id=row["event_id"],
            timestamp=row["timestamp"],
            verdict=row["verdict"],
            primary_reason=row["primary_reason"],
            reason_codes=tuple(json.loads(row["reason_codes_json"])),
            session_id=row["session_id"],
            scenario_id=row["scenario_id"],
            configuration_hash=row["configuration_hash"],
            policy_id=row["policy_id"],
            exceeded_count=row["exceeded_count"],
            is_explicit_violation=bool(row["is_explicit_violation"]),
            is_evidence_complete=bool(row["is_evidence_complete"]),
            metadata=json.loads(row["metadata_json"]),
            created_at=row["created_at"],
        )

    @staticmethod
    def _row_to_evidence(row: sqlite3.Row) -> PersistedEvidenceRecord:
        return PersistedEvidenceRecord(
            record_id=row["record_id"],
            event_id=row["event_id"],
            source=row["source"],
            status=row["status"],
            primary_reason=row["primary_reason"],
            evidence_payload=json.loads(row["evidence_json"]),
            violations=tuple(json.loads(row["violations_json"])),
            created_at=row["created_at"],
        )


# ==============================================================================
# Domain Converters
# ==============================================================================

def decision_to_persisted_event(
    decision: DecisionResult,
    event_id: str,
    scenario_id: str | None = None,
    session_id: str | None = None,
) -> PersistedSecurityEvent:
    """Convert an authoritative M12 DecisionResult into a PersistedSecurityEvent."""
    return PersistedSecurityEvent(
        event_id=event_id,
        timestamp=decision.timestamp,
        verdict=decision.verdict.value,
        primary_reason=decision.primary_reason,
        reason_codes=decision.reason_codes,
        session_id=session_id,
        scenario_id=scenario_id,
        configuration_hash=decision.configuration_hash,
        policy_id=decision.policy_id,
        exceeded_count=decision.exceeded_count,
        is_explicit_violation=decision.is_explicit_violation,
        is_evidence_complete=decision.is_evidence_complete,
        metadata=dict(decision.metadata),
    )


def fused_evidence_to_persisted_record(
    fused: FusedSecurityEvidence,
    record_id: str,
    event_id: str,
) -> PersistedEvidenceRecord:
    """Convert an M16 FusedSecurityEvidence into a PersistedEvidenceRecord."""
    payload: dict[str, Any] = {
        "is_clean": fused.is_clean,
        "is_anomalous": fused.is_anomalous,
        "is_explicit_violation": fused.is_explicit_violation,
        "is_complete": fused.is_complete,
        "source_statuses": fused.source_statuses,
        "source_reason_codes": fused.source_reason_codes,
        "present_sources": [s.value for s in fused.present_sources],
        "missing_sources": [s.value for s in fused.missing_sources],
    }
    return PersistedEvidenceRecord(
        record_id=record_id,
        event_id=event_id,
        source="FUSION",
        status=fused.status.value,
        primary_reason=fused.primary_reason,
        evidence_payload=payload,
        violations=fused.violations,
    )

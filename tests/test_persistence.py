"""Q-SHIELD — Test Suite for SQLite Persistence Layer (Milestone M19-A).

Validates:
1. Database initialization and schema creation.
2. Parameterized insertion and retrieval of security events.
3. Preservation of exact M12 decisions (ACCEPT, SUSPICIOUS, ATTACK) and reason codes.
4. Contributing evidence record storage and relational integrity.
5. Rejection of malformed records and invalid verdicts.
6. Secret leakage prevention (rejects credentials, passwords, raw keys in metadata).
7. Persistence across simulated process restarts using on-disk temporary databases.
8. M17 security evaluation run and scenario result persistence.
9. M18 performance benchmark run and latency metrics persistence.
10. Safe queries, pagination, and filtering.
"""

from __future__ import annotations

import os
import tempfile
import pytest

from src.detection.decision import DecisionReasonCode, DecisionResult, DecisionVerdict
from src.detection.fusion import EvidenceSource, FusedEvidenceStatus, FusedSecurityEvidence, FusionReasonCode
from src.persistence.database import DatabaseManager
from src.persistence.models import (
    PersistedBenchmarkResult,
    PersistedBenchmarkRun,
    PersistedEvaluationRun,
    PersistedEvaluationScenarioResult,
    PersistedEvidenceRecord,
    PersistedSecurityEvent,
)
from src.persistence.repository import (
    SecurityRepository,
    decision_to_persisted_event,
    fused_evidence_to_persisted_record,
)


from typing import Generator

@pytest.fixture
def in_memory_repo() -> Generator[SecurityRepository, None, None]:
    """Fixture providing a fresh in-memory SQLite repository with guaranteed teardown."""
    db_mgr = DatabaseManager(db_path=":memory:")
    repo = SecurityRepository(db_mgr)
    try:
        yield repo
    finally:
        db_mgr.close()


# ==============================================================================
# 1. Database Initialization & Schema Tests
# ==============================================================================

class TestDatabaseInitialization:
    """Tests schema initialization and connection configuration."""

    def test_schema_created_successfully(self, in_memory_repo: SecurityRepository) -> None:
        """All expected relational tables exist upon initialization."""
        with in_memory_repo.db_manager.connection() as conn:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ).fetchall()
            table_names = {r["name"] for r in tables}
            assert "security_events" in table_names
            assert "evidence_records" in table_names
            assert "evaluation_runs" in table_names
            assert "evaluation_results" in table_names
            assert "benchmark_runs" in table_names
            assert "benchmark_results" in table_names

    def test_foreign_keys_enforced(self, in_memory_repo: SecurityRepository) -> None:
        """Orphaned evidence records without an existing event_id raise IntegrityError."""
        rec = PersistedEvidenceRecord(
            record_id="REC-ORPHAN",
            event_id="EVENT-DOES-NOT-EXIST",
            source="IMPERSONATION",
            status="CLEAN",
            primary_reason="OK",
        )
        with pytest.raises(Exception):
            with in_memory_repo.db_manager.connection() as conn:
                conn.execute(
                    "INSERT INTO evidence_records (record_id, event_id, source, status, primary_reason) VALUES (?, ?, ?, ?, ?)",
                    (rec.record_id, rec.event_id, rec.source, rec.status, rec.primary_reason),
                )


# ==============================================================================
# 2. Security Event & Evidence Recording
# ==============================================================================

class TestSecurityEventPersistence:
    """Tests storing and retrieving M12 decisions and multi-source evidence."""

    @pytest.mark.parametrize("verdict", ["ACCEPT", "SUSPICIOUS", "ATTACK"])
    def test_persist_all_m12_verdicts_exactly(
        self, in_memory_repo: SecurityRepository, verdict: str
    ) -> None:
        """M12 verdicts are persisted and retrieved without semantic mutation."""
        event = PersistedSecurityEvent(
            event_id=f"EVT-{verdict}-01",
            timestamp="2026-09-06T12:00:00Z",
            verdict=verdict,
            primary_reason="TEST_REASON",
            reason_codes=("CODE_1", "CODE_2"),
            session_id="SESS-001",
            scenario_id="SCEN-001",
            configuration_hash="HASH-ABC",
            policy_id="POL-01",
            exceeded_count=1 if verdict == "SUSPICIOUS" else 0,
            is_explicit_violation=(verdict == "ATTACK"),
            is_evidence_complete=True,
            metadata={"test_tag": "verdict_test"},
        )
        evidence = PersistedEvidenceRecord(
            record_id=f"REC-{verdict}-01",
            event_id=event.event_id,
            source="QUANTUM_CHANNEL",
            status="CLEAN" if verdict == "ACCEPT" else "ANOMALOUS",
            primary_reason="TEST_EVIDENCE_REASON",
            evidence_payload={"qber": 0.02, "fidelity": 0.98},
            violations=("VIOLATION_01",) if verdict == "ATTACK" else (),
        )

        in_memory_repo.record_security_event(event, [evidence])

        retrieved_event = in_memory_repo.get_security_event(event.event_id)
        assert retrieved_event is not None
        assert retrieved_event.event_id == event.event_id
        assert retrieved_event.verdict == verdict
        assert retrieved_event.primary_reason == "TEST_REASON"
        assert retrieved_event.reason_codes == ("CODE_1", "CODE_2")
        assert retrieved_event.session_id == "SESS-001"
        assert retrieved_event.metadata["test_tag"] == "verdict_test"

        retrieved_evidence = in_memory_repo.get_evidence_records(event.event_id)
        assert len(retrieved_evidence) == 1
        assert retrieved_evidence[0].record_id == evidence.record_id
        assert retrieved_evidence[0].source == "QUANTUM_CHANNEL"
        assert retrieved_evidence[0].evidence_payload["qber"] == 0.02

    def test_invalid_verdict_rejected(self) -> None:
        """Arbitrary verdict values not matching M12 are rejected."""
        with pytest.raises(ValueError, match="Invalid verdict"):
            PersistedSecurityEvent(
                event_id="EVT-INVALID",
                timestamp="2026-09-06T12:00:00Z",
                verdict="INVALID_VERDICT",
                primary_reason="REASON",
                reason_codes=(),
            )

    def test_empty_event_id_rejected(self) -> None:
        """Empty event_id raises ValueError."""
        with pytest.raises(ValueError, match="event_id cannot be empty"):
            PersistedSecurityEvent(
                event_id="   ",
                timestamp="2026-09-06T12:00:00Z",
                verdict="ACCEPT",
                primary_reason="REASON",
                reason_codes=(),
            )

    def test_secret_keyword_in_metadata_rejected(self) -> None:
        """Metadata containing secret keywords raises ValueError."""
        with pytest.raises(ValueError, match="Sensitive keyword"):
            PersistedSecurityEvent(
                event_id="EVT-SECRET-01",
                timestamp="2026-09-06T12:00:00Z",
                verdict="ACCEPT",
                primary_reason="REASON",
                reason_codes=(),
                metadata={"private_key_pem": "MIIB..."},
            )

    def test_domain_adapter_decision_to_persisted_event(self) -> None:
        """Adapter correctly maps M12 DecisionResult to PersistedSecurityEvent."""
        decision = DecisionResult(
            verdict=DecisionVerdict.ATTACK,
            primary_reason=DecisionReasonCode.EXPLICIT_SECURITY_VIOLATION.value,
            reason_codes=(DecisionReasonCode.EXPLICIT_SECURITY_VIOLATION.value,),
            exceeded_metrics=(),
            exceeded_count=0,
            is_explicit_violation=True,
            is_evidence_complete=True,
            policy_id="POL-DEFAULT",
            configuration_hash="CONFIG-HASH-123",
            timestamp="2026-09-06T12:00:00Z",
            metadata={"provenance": "eval_test"},
        )
        event = decision_to_persisted_event(
            decision, event_id="EVT-ADAPTER-01", scenario_id="SCEN-IMP", session_id="SESS-456"
        )
        assert event.event_id == "EVT-ADAPTER-01"
        assert event.verdict == "ATTACK"
        assert event.primary_reason == DecisionReasonCode.EXPLICIT_SECURITY_VIOLATION.value
        assert event.scenario_id == "SCEN-IMP"
        assert event.session_id == "SESS-456"
        assert event.configuration_hash == "CONFIG-HASH-123"
        assert event.is_explicit_violation is True


# ==============================================================================
# 3. Process Restart Persistence (On-Disk Tests)
# ==============================================================================

class TestProcessRestartPersistence:
    """Tests that on-disk SQLite databases survive connection re-openings."""

    def test_data_persists_across_restart(self) -> None:
        """Written events remain present after closing and reopening the SQLite database file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_file = os.path.join(tmp_dir, "test_qshield_restart.db")

            # 1. Initialize and write event
            db_mgr_1 = DatabaseManager(db_path=db_file)
            repo_1 = SecurityRepository(db_mgr_1)

            event = PersistedSecurityEvent(
                event_id="EVT-RESTART-001",
                timestamp="2026-09-06T14:00:00Z",
                verdict="ACCEPT",
                primary_reason="ALL_EVIDENCE_WITHIN_POLICY",
                reason_codes=("ALL_EVIDENCE_WITHIN_POLICY",),
                session_id="SESS-PERSIST",
            )
            repo_1.record_security_event(event)

            # 2. Simulate process restart by instantiating new manager on same file
            db_mgr_2 = DatabaseManager(db_path=db_file)
            repo_2 = SecurityRepository(db_mgr_2)

            try:
                retrieved = repo_2.get_security_event("EVT-RESTART-001")
                assert retrieved is not None
                assert retrieved.event_id == "EVT-RESTART-001"
                assert retrieved.verdict == "ACCEPT"
                assert retrieved.session_id == "SESS-PERSIST"
            finally:
                db_mgr_1.close()
                db_mgr_2.close()


# ==============================================================================
# 4. M17 Evaluation Runs Persistence
# ==============================================================================

class TestEvaluationRunPersistence:
    """Tests saving and loading M17 security evaluation summaries and scenarios."""

    def test_record_and_get_evaluation_run(self, in_memory_repo: SecurityRepository) -> None:
        """Evaluation run summary and individual scenario results are persisted and queried."""
        sc1 = PersistedEvaluationScenarioResult(
            scenario_id="SCEN-01",
            category="CLEAN_HONEST",
            expected_verdict="ACCEPT",
            observed_verdict="ACCEPT",
            passed=True,
        )
        sc2 = PersistedEvaluationScenarioResult(
            scenario_id="SCEN-02",
            category="IMPERSONATION",
            expected_verdict="ATTACK",
            observed_verdict="ATTACK",
            passed=True,
            violations=("AUTHENTICATED_IDENTITY_MISMATCH",),
        )

        eval_run = PersistedEvaluationRun(
            run_id="RUN-EVAL-001",
            timestamp="2026-09-06T15:00:00Z",
            total_scenarios=2,
            passed_scenarios=2,
            failed_scenarios=0,
            pass_rate=1.0,
            session_id="SESS-EVAL",
            confusion_matrix={"true_positives": 1, "true_negatives": 1, "false_positives": 0, "false_negatives": 0},
            category_summaries={"CLEAN_HONEST": {"passed": 1, "total": 1}},
            scenario_results=(sc1, sc2),
        )

        in_memory_repo.record_evaluation_run(eval_run)

        loaded = in_memory_repo.get_evaluation_run("RUN-EVAL-001")
        assert loaded is not None
        assert loaded.run_id == "RUN-EVAL-001"
        assert loaded.total_scenarios == 2
        assert loaded.pass_rate == 1.0
        assert len(loaded.scenario_results) == 2
        assert loaded.scenario_results[1].scenario_id == "SCEN-02"
        assert loaded.scenario_results[1].violations == ("AUTHENTICATED_IDENTITY_MISMATCH",)

        # List runs
        run_list = in_memory_repo.list_evaluation_runs()
        assert len(run_list) == 1
        assert run_list[0].run_id == "RUN-EVAL-001"


# ==============================================================================
# 5. M18 Benchmark Runs Persistence
# ==============================================================================

class TestBenchmarkRunPersistence:
    """Tests saving and querying M18 benchmark metrics and scaling results."""

    def test_record_and_get_benchmark_run(self, in_memory_repo: SecurityRepository) -> None:
        """Benchmark run and latency quantiles are stored and retrieved accurately."""
        res1 = PersistedBenchmarkResult(
            benchmark_id="BENCH_01_CLEAN",
            category="BASELINE_EVALUATION",
            workload_size=1,
            iterations=10,
            total_elapsed_seconds=0.05,
            cpu_time_seconds=0.04,
            mean_latency_seconds=0.005,
            min_latency_seconds=0.004,
            max_latency_seconds=0.007,
            median_latency_seconds=0.005,
            p95_latency_seconds=0.0068,
            throughput_ops_per_sec=200.0,
            observed_verdicts={"ACCEPT": 10},
        )

        bench_run = PersistedBenchmarkRun(
            run_id="RUN-BENCH-001",
            suite_id="BASELINE_SUITE",
            timestamp="2026-09-06T15:30:00Z",
            total_benchmarks=1,
            successful_benchmarks=1,
            failed_benchmarks=0,
            total_elapsed_seconds=0.05,
            benchmark_results=(res1,),
            metadata={"env": "local_test"},
        )

        in_memory_repo.record_benchmark_run(bench_run)

        loaded = in_memory_repo.get_benchmark_run("RUN-BENCH-001")
        assert loaded is not None
        assert loaded.run_id == "RUN-BENCH-001"
        assert loaded.total_benchmarks == 1
        assert len(loaded.benchmark_results) == 1
        b_res = loaded.benchmark_results[0]
        assert b_res.benchmark_id == "BENCH_01_CLEAN"
        assert b_res.mean_latency_seconds == 0.005
        assert b_res.throughput_ops_per_sec == 200.0
        assert b_res.observed_verdicts["ACCEPT"] == 10


# ==============================================================================
# 6. Pagination and Query Filtering
# ==============================================================================

class TestQueryPaginationAndFiltering:
    """Tests query filtering by verdict and session_id as well as offset/limit."""

    def test_list_events_filtered_by_verdict(self, in_memory_repo: SecurityRepository) -> None:
        """Filtering by verdict returns only events with the specified M12 verdict."""
        for i, v in enumerate(["ACCEPT", "ACCEPT", "SUSPICIOUS", "ATTACK"]):
            evt = PersistedSecurityEvent(
                event_id=f"EVT-FILTER-{i}",
                timestamp=f"2026-09-06T10:0{i}:00Z",
                verdict=v,
                primary_reason="REASON",
                reason_codes=(),
            )
            in_memory_repo.record_security_event(evt)

        accepts = in_memory_repo.list_security_events(verdict="ACCEPT")
        assert len(accepts) == 2
        for a in accepts:
            assert a.verdict == "ACCEPT"

        attacks = in_memory_repo.list_security_events(verdict="ATTACK")
        assert len(attacks) == 1
        assert attacks[0].verdict == "ATTACK"

    def test_pagination_limit_offset(self, in_memory_repo: SecurityRepository) -> None:
        """Pagination limit and offset correctly partition result sets."""
        for i in range(10):
            evt = PersistedSecurityEvent(
                event_id=f"EVT-PAGE-{i:02d}",
                timestamp=f"2026-09-06T10:{i:02d}:00Z",
                verdict="ACCEPT",
                primary_reason="REASON",
                reason_codes=(),
            )
            in_memory_repo.record_security_event(evt)

        page1 = in_memory_repo.list_security_events(limit=4, offset=0)
        assert len(page1) == 4

        page2 = in_memory_repo.list_security_events(limit=4, offset=4)
        assert len(page2) == 4

        # IDs between pages must not overlap
        page1_ids = {e.event_id for e in page1}
        page2_ids = {e.event_id for e in page2}
        assert page1_ids.isdisjoint(page2_ids)

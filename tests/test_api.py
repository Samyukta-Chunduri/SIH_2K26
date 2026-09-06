"""Q-SHIELD — Test Suite for FastAPI Application Backend (Milestone M19-B).

Validates:
1. Health check endpoint.
2. Scenario template discovery.
3. Verification endpoint execution across honest, suspicious, and attack scenarios.
4. M12 authoritative verdict preservation through the API.
5. Inability of clients to inject arbitrary verdicts.
6. Structured error responses and 404 handling.
7. Querying security history, pagination, and verdict filtering.
8. Subsystem evidence endpoints: Quantum, Threat, and Evidence Fusion.
9. M17 evaluation suite execution and run detail querying.
10. M18 benchmark suite execution and latency metrics querying.
"""

from __future__ import annotations

from typing import Generator
import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app


@pytest.fixture
def test_client() -> Generator[TestClient, None, None]:
    """Fixture providing a FastAPI test client backed by an isolated in-memory SQLite database."""
    app = create_app(db_path=":memory:")
    with TestClient(app) as client:
        yield client


# ==============================================================================
# 1. Health & Discovery
# ==============================================================================

def test_health_check(test_client: TestClient) -> None:
    """Health check returns ok status."""
    resp = test_client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["service"] == "q-shield-api"


def test_list_scenario_templates(test_client: TestClient) -> None:
    """Returns available executable scenario templates."""
    resp = test_client.get("/api/scenarios")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    types = {item["scenario_type"] for item in data}
    assert "honest" in types
    assert "impersonation_attack" in types
    assert "channel_anomaly" in types
    assert "unauthorized_verification" in types
    assert "multi_source_attack" in types


# ==============================================================================
# 2. Security Verification & M12 Verdict Preservation
# ==============================================================================

class TestSecurityVerificationAPI:
    """Tests executing security scenarios and verifying M12 verdicts."""

    def test_verify_honest_scenario_yields_accept(self, test_client: TestClient) -> None:
        """Honest scenario produces authoritative M12 ACCEPT verdict."""
        payload = {"scenario_type": "honest", "session_id": "sess_test_honest"}
        resp = test_client.post("/api/security/verify", json=payload)
        assert resp.status_code == 201
        data = resp.json()

        event = data["event"]
        assert event["verdict"] == "ACCEPT"
        assert event["session_id"] == "sess_test_honest"
        assert event["is_explicit_violation"] is False

        # Verify evidence records exist
        evidence_records = data["evidence_records"]
        assert len(evidence_records) == 4
        sources = {r["source"] for r in evidence_records}
        assert sources == {"IMPERSONATION", "AUTHORIZATION", "QUANTUM_CHANNEL", "FUSION"}

    def test_verify_impersonation_attack_yields_attack(self, test_client: TestClient) -> None:
        """Impersonation attack scenario produces authoritative M12 ATTACK verdict."""
        payload = {"scenario_type": "impersonation_attack"}
        resp = test_client.post("/api/security/verify", json=payload)
        assert resp.status_code == 201
        data = resp.json()

        event = data["event"]
        assert event["verdict"] == "ATTACK"
        assert event["is_explicit_violation"] is True

        # Check that impersonation record contains violation
        evidence_records = data["evidence_records"]
        imp_rec = next(r for r in evidence_records if r["source"] == "IMPERSONATION")
        assert len(imp_rec["violations"]) > 0

    def test_verify_channel_anomaly_yields_suspicious(self, test_client: TestClient) -> None:
        """Channel disturbance exceeding threshold produces authoritative M12 SUSPICIOUS verdict."""
        payload = {"scenario_type": "channel_anomaly"}
        resp = test_client.post("/api/security/verify", json=payload)
        assert resp.status_code == 201
        data = resp.json()

        event = data["event"]
        assert event["verdict"] == "SUSPICIOUS"
        assert event["is_explicit_violation"] is False

    def test_verify_unauthorized_verification_yields_attack(self, test_client: TestClient) -> None:
        """Unauthorized verifier attempt produces authoritative M12 ATTACK verdict."""
        payload = {"scenario_type": "unauthorized_verification"}
        resp = test_client.post("/api/security/verify", json=payload)
        assert resp.status_code == 201
        data = resp.json()

        event = data["event"]
        assert event["verdict"] == "ATTACK"
        assert event["is_explicit_violation"] is True

    def test_verify_multi_source_attack_yields_attack(self, test_client: TestClient) -> None:
        """Multi-vector attack produces authoritative M12 ATTACK verdict."""
        payload = {"scenario_type": "multi_source_attack"}
        resp = test_client.post("/api/security/verify", json=payload)
        assert resp.status_code == 201
        data = resp.json()

        event = data["event"]
        assert event["verdict"] == "ATTACK"
        assert event["is_explicit_violation"] is True

    def test_client_cannot_inject_verdict(self, test_client: TestClient) -> None:
        """Client payload attempting to supply a 'verdict' is rejected by Pydantic schema validation."""
        payload = {"scenario_type": "honest", "verdict": "ACCEPT"}
        resp = test_client.post("/api/security/verify", json=payload)
        assert resp.status_code == 422  # Unprocessable Entity (extra forbidden field)

    def test_unknown_scenario_type_rejected(self, test_client: TestClient) -> None:
        """Unknown scenario_type returns 400 Bad Request."""
        payload = {"scenario_type": "unknown_exploit_xyz"}
        resp = test_client.post("/api/security/verify", json=payload)
        assert resp.status_code == 400


# ==============================================================================
# 3. Security History & Event Queries
# ==============================================================================

class TestSecurityHistoryAPI:
    """Tests querying events, pagination, and individual event retrieval."""

    def test_list_and_filter_events(self, test_client: TestClient) -> None:
        """Events list supports verdict filtering and pagination."""
        test_client.post("/api/security/verify", json={"scenario_type": "honest"})
        test_client.post("/api/security/verify", json={"scenario_type": "impersonation_attack"})
        test_client.post("/api/security/verify", json={"scenario_type": "channel_anomaly"})

        # List all
        resp_all = test_client.get("/api/security/events")
        assert resp_all.status_code == 200
        events = resp_all.json()
        assert len(events) == 3

        # Filter by verdict=ATTACK
        resp_attacks = test_client.get("/api/security/events?verdict=ATTACK")
        assert resp_attacks.status_code == 200
        attacks = resp_attacks.json()
        assert len(attacks) == 1
        assert attacks[0]["verdict"] == "ATTACK"

    def test_get_event_detail_by_id(self, test_client: TestClient) -> None:
        """Retrieve full event detail by event_id."""
        verify_resp = test_client.post("/api/security/verify", json={"scenario_type": "honest"})
        event_id = verify_resp.json()["event"]["event_id"]

        resp = test_client.get(f"/api/security/events/{event_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["event"]["event_id"] == event_id
        assert len(data["evidence_records"]) == 4

    def test_get_nonexistent_event_returns_404(self, test_client: TestClient) -> None:
        """Requesting nonexistent event_id returns 404 Not Found."""
        resp = test_client.get("/api/security/events/nonexistent_event_123")
        assert resp.status_code == 404


# ==============================================================================
# 4. Subsystem Evidence Endpoints
# ==============================================================================

class TestSubsystemEvidenceEndpoints:
    """Tests dedicated endpoints for Quantum, Threat, and Fusion evidence."""

    def test_quantum_evidence_endpoint(self, test_client: TestClient) -> None:
        """GET /api/quantum/evidence/{id} returns quantum telemetry."""
        verify_resp = test_client.post("/api/security/verify", json={"scenario_type": "honest"})
        event_id = verify_resp.json()["event"]["event_id"]

        resp = test_client.get(f"/api/quantum/evidence/{event_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["event_id"] == event_id
        assert data["status"] == "CLEAN"
        assert data["qber"] is not None
        assert data["teleportation_fidelity"] is not None

    def test_threat_evidence_endpoint(self, test_client: TestClient) -> None:
        """GET /api/threats/{id} returns identity, authorization, and channel breakdown."""
        verify_resp = test_client.post("/api/security/verify", json={"scenario_type": "impersonation_attack"})
        event_id = verify_resp.json()["event"]["event_id"]

        resp = test_client.get(f"/api/threats/{event_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["event_id"] == event_id
        assert "impersonation" in data
        assert "authorization" in data
        assert "quantum_channel" in data
        assert len(data["confirmed_violations"]) > 0

    def test_fusion_evidence_endpoint(self, test_client: TestClient) -> None:
        """GET /api/fusion/{id} returns M16 synthesis details and M12 verdict."""
        verify_resp = test_client.post("/api/security/verify", json={"scenario_type": "honest"})
        event_id = verify_resp.json()["event"]["event_id"]

        resp = test_client.get(f"/api/fusion/{event_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["event_id"] == event_id
        assert data["fused_status"] == "CLEAN"
        assert data["m12_verdict"] == "ACCEPT"


# ==============================================================================
# 5. M17 Security Evaluation Endpoints
# ==============================================================================

class TestEvaluationAPI:
    """Tests triggering and querying M17 security evaluations."""

    def test_trigger_and_query_evaluation_run(self, test_client: TestClient) -> None:
        """Trigger M17 baseline suite evaluation and query the report."""
        run_resp = test_client.post("/api/evaluation/run")
        assert run_resp.status_code == 201
        data = run_resp.json()

        summary = data["summary"]
        assert summary["total_scenarios"] > 0
        assert summary["pass_rate"] == 1.0
        assert "confusion_matrix" in summary

        scenario_results = data["scenario_results"]
        assert len(scenario_results) == summary["total_scenarios"]

        # List runs
        list_resp = test_client.get("/api/evaluation/runs")
        assert list_resp.status_code == 200
        runs = list_resp.json()
        assert len(runs) == 1

        # Query single run
        get_resp = test_client.get(f"/api/evaluation/runs/{summary['run_id']}")
        assert get_resp.status_code == 200
        assert get_resp.json()["summary"]["run_id"] == summary["run_id"]


# ==============================================================================
# 6. M18 Performance Benchmark Endpoints
# ==============================================================================

class TestBenchmarkAPI:
    """Tests triggering and querying M18 performance benchmarks."""

    def test_trigger_and_query_benchmark_run(self, test_client: TestClient) -> None:
        """Trigger M18 baseline benchmark suite and query the metrics."""
        run_resp = test_client.post("/api/benchmarks/run")
        assert run_resp.status_code == 201
        data = run_resp.json()

        summary = data["summary"]
        assert summary["total_benchmarks"] == 9
        assert summary["successful_benchmarks"] == 9
        assert summary["total_elapsed_seconds"] > 0.0

        benchmark_results = data["benchmark_results"]
        assert len(benchmark_results) == 9

        # List runs
        list_resp = test_client.get("/api/benchmarks")
        assert list_resp.status_code == 200
        runs = list_resp.json()
        assert len(runs) == 1

        # Query single run
        get_resp = test_client.get(f"/api/benchmarks/{summary['run_id']}")
        assert get_resp.status_code == 200
        assert get_resp.json()["summary"]["run_id"] == summary["run_id"]

"""Q-SHIELD — End-to-End Integration & Verification Suite (Milestone M19-K).

Validates the full demonstration lifecycle across:
1. Scenario Selection & Pipeline Execution
2. Authoritative M12 Verdict Enforcement (ACCEPT, SUSPICIOUS, ATTACK)
3. Deterministic Evidence Fusion (M16) & Provenance
4. SQLite Persistence & Process Memory Retention
5. Historical Event Retrieval and Query Filtering
6. Subsystem Telemetry (Quantum M0–M9, Threats M13–M15, Fusion M16)
7. Security Evaluation Suite (M17)
8. Operational Performance Benchmarking (M18)
"""

from __future__ import annotations

import os
from pathlib import Path
import tempfile
from typing import Generator
import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app
from src.persistence.database import DatabaseManager
from src.persistence.repository import SecurityRepository


@pytest.fixture
def isolated_app() -> Generator[TestClient, None, None]:
    """Fixture providing a test client backed by a temporary file-based SQLite database."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = str(Path(tmp_dir) / "e2e_qshield.db")
        app = create_app(db_path=db_path)
        with TestClient(app) as client:
            yield client


class TestEndToEndDemonstrationFlow:
    """Simulates a complete judge/user interactive demonstration workflow."""

    def test_full_pipeline_verification_lifecycle(self, isolated_app: TestClient) -> None:
        """Walk through complete execution: templates -> verify -> persist -> history -> audit."""
        # 1. Health & Discovery
        health_resp = isolated_app.get("/health")
        assert health_resp.status_code == 200
        assert health_resp.json()["status"] == "ok"

        scenarios_resp = isolated_app.get("/api/scenarios")
        assert scenarios_resp.status_code == 200
        templates = scenarios_resp.json()
        assert len(templates) >= 5

        # 2. Execute Honest Baseline Verification -> Authoritative M12 ACCEPT
        honest_resp = isolated_app.post(
            "/api/security/verify",
            json={"scenario_type": "honest", "session_id": "demo_session_honest"},
        )
        assert honest_resp.status_code == 201
        honest_data = honest_resp.json()
        honest_event = honest_data["event"]
        assert honest_event["verdict"] == "ACCEPT"
        assert honest_event["is_explicit_violation"] is False
        honest_event_id = honest_event["event_id"]

        # 3. Execute Channel Anomaly -> Authoritative M12 SUSPICIOUS
        anomaly_resp = isolated_app.post(
            "/api/security/verify",
            json={"scenario_type": "channel_anomaly", "session_id": "demo_session_anomaly"},
        )
        assert anomaly_resp.status_code == 201
        anomaly_data = anomaly_resp.json()
        anomaly_event = anomaly_data["event"]
        assert anomaly_event["verdict"] == "SUSPICIOUS"
        assert anomaly_event["is_explicit_violation"] is False
        anomaly_event_id = anomaly_event["event_id"]

        # 4. Execute Impersonation Attack -> Authoritative M12 ATTACK
        attack_resp = isolated_app.post(
            "/api/security/verify",
            json={"scenario_type": "impersonation_attack", "session_id": "demo_session_attack"},
        )
        assert attack_resp.status_code == 201
        attack_data = attack_resp.json()
        attack_event = attack_data["event"]
        assert attack_event["verdict"] == "ATTACK"
        assert attack_event["is_explicit_violation"] is True
        attack_event_id = attack_event["event_id"]

        # 5. Verify Persistence & Query History
        history_resp = isolated_app.get("/api/security/events")
        assert history_resp.status_code == 200
        events_list = history_resp.json()
        assert len(events_list) == 3

        # Filter by verdict: ACCEPT
        accepts = isolated_app.get("/api/security/events?verdict=ACCEPT").json()
        assert len(accepts) == 1
        assert accepts[0]["event_id"] == honest_event_id

        # Filter by verdict: ATTACK
        attacks = isolated_app.get("/api/security/events?verdict=ATTACK").json()
        assert len(attacks) == 1
        assert attacks[0]["event_id"] == attack_event_id

        # 6. Detailed Subsystem Telemetry Verification
        # 6a. Quantum Telemetry
        q_resp = isolated_app.get(f"/api/quantum/evidence/{anomaly_event_id}")
        assert q_resp.status_code == 200
        q_telemetry = q_resp.json()
        assert q_telemetry["threshold_exceeded"] is True
        assert q_telemetry["qber"] is not None
        assert q_telemetry["teleportation_fidelity"] is not None

        # 6b. Threat Detection Subsystems
        threat_resp = isolated_app.get(f"/api/threats/{attack_event_id}")
        assert threat_resp.status_code == 200
        threat_data = threat_resp.json()
        assert len(threat_data["confirmed_violations"]) > 0

        # 6c. Evidence Fusion Funnel & M12 Result
        fusion_resp = isolated_app.get(f"/api/fusion/{honest_event_id}")
        assert fusion_resp.status_code == 200
        fusion_data = fusion_resp.json()
        assert fusion_data["fused_status"] == "CLEAN"
        assert fusion_data["m12_verdict"] == "ACCEPT"

        # 7. Execute M17 Security Evaluation Suite
        eval_run_resp = isolated_app.post("/api/evaluation/run?session_id=demo_eval_1")
        assert eval_run_resp.status_code == 201
        eval_run = eval_run_resp.json()
        assert eval_run["summary"]["total_scenarios"] == 16
        assert eval_run["summary"]["passed_scenarios"] == 16
        assert eval_run["summary"]["pass_rate"] == 1.0
        assert eval_run["summary"]["confusion_matrix"]["true_positives"] > 0
        assert eval_run["summary"]["confusion_matrix"]["true_negatives"] > 0

        # 8. Execute M18 Performance Benchmark Suite
        bench_run_resp = isolated_app.post("/api/benchmarks/run")
        assert bench_run_resp.status_code == 201
        bench_run = bench_run_resp.json()
        assert bench_run["summary"]["total_benchmarks"] > 0
        assert bench_run["summary"]["successful_benchmarks"] == bench_run["summary"]["total_benchmarks"]
        assert len(bench_run["benchmark_results"]) > 0
        assert bench_run["benchmark_results"][0]["mean_latency_seconds"] > 0

    def test_security_invariants_strictly_enforced(self, isolated_app: TestClient) -> None:
        """Client cannot bypass M12, inject arbitrary verdicts, or trigger unauthorized mutations."""
        # 1. Reject client verdict injection
        tamper_resp = isolated_app.post(
            "/api/security/verify",
            json={"scenario_type": "impersonation_attack", "verdict": "ACCEPT"},
        )
        assert tamper_resp.status_code == 422  # Pydantic schema validation rejection

        # 2. Unknown scenario type rejected
        unknown_resp = isolated_app.post(
            "/api/security/verify",
            json={"scenario_type": "malicious_injection_eval"},
        )
        assert unknown_resp.status_code == 400

        # 3. No secret material leaked in history or event details
        events_resp = isolated_app.get("/api/security/events")
        for evt in events_resp.json():
            dump = str(evt).lower()
            for forbidden in ("password", "secret", "private_key", "raw_key"):
                assert forbidden not in dump

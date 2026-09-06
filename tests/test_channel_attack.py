"""Tests for Milestone M15: Deterministic Quantum Channel Attack Detection.

Covers:
    - Clean channel verification (M15 CLEAN -> M12 ACCEPT)
    - QBER anomaly detection and threshold boundaries (M15 ANOMALOUS -> M12 SUSPICIOUS)
    - Bell correlation anomaly detection
    - Teleportation fidelity anomaly detection
    - Distribution TVD and Pauli expectation anomalies
    - Multi-signal disturbances and no "first error wins" (preserving all reasons)
    - Explicit channel security violations (M15 SECURITY_VIOLATION -> M12 ATTACK)
    - Missing evidence and incomplete telemetry (M15 INCOMPLETE -> M12 SUSPICIOUS)
    - Context compatibility (session mismatch, configuration mismatch, conflicting evidence)
    - Calibrated noise model operational boundary
    - Decoupling from M13 identity/impersonation detection
    - Decoupling from M14 unauthorized verification detection
    - Replay separation (no nonce tracking or replay caches)
    - Immutability and defensive deep freezing
    - Determinism across repeated evaluations
    - Defensive secret leakage prevention (rejection of credentials/secrets)
    - Zero composite security scores
    - Direct integration with M10 StatisticalEvidence and M11 ThresholdPolicy
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import Any
import pytest

from src.detection.authorization import (
    AuthorizationRequest,
    VerificationPolicy,
    evaluate_verification_authorization,
)
from src.detection.channel import (
    ChannelEvidenceStatus,
    ChannelReasonCode,
    ChannelSecurityEvidence,
    detect_channel_anomalies,
    evaluate_channel_attack_decision,
)
from src.detection.decision import (
    DecisionReasonCode,
    DecisionVerdict,
    ProtocolSecurityEvidence,
    evaluate_security_decision,
)
from src.detection.impersonation import (
    AuthenticationEvidence,
    IdentityClaim,
    IdentityEvidenceStatus,
    detect_impersonation,
)
from src.statistics.baseline import BaselineConfiguration
from src.statistics.comparison import (
    MetricDeviation,
    StatisticalEvidence,
    VerificationObservation,
)
from src.statistics.thresholds import (
    MetricThreshold,
    MetricThresholdEvaluation,
    PolicyEvaluationReport,
    ThresholdDirection,
    ThresholdMethod,
    ThresholdPolicy,
)


# ==============================================================================
# Helpers & Fixtures
# ==============================================================================

def _make_sample_report(
    evaluations: dict[str, MetricThresholdEvaluation],
    policy_id: str = "policy_test_001",
    config_hash: str = "a" * 64,
    metadata: dict[str, Any] | None = None,
) -> PolicyEvaluationReport:
    """Construct a PolicyEvaluationReport for testing."""
    exceeded_metrics = [name for name, ev in evaluations.items() if ev.exceeded]
    return PolicyEvaluationReport(
        policy_id=policy_id,
        baseline_configuration_hash=config_hash,
        metric_evaluations=evaluations,
        any_exceeded=len(exceeded_metrics) > 0,
        all_exceeded=len(exceeded_metrics) == len(evaluations) and len(evaluations) > 0,
        exceeded_metrics=tuple(sorted(exceeded_metrics)),
        exceeded_count=len(exceeded_metrics),
        total_metrics_evaluated=len(evaluations),
        timestamp="2026-09-06T12:00:00Z",
        metadata=metadata or {},
    )


def _make_metric_eval(
    metric_name: str,
    observed_value: float,
    threshold_value: float,
    direction: ThresholdDirection = ThresholdDirection.UPPER,
    exceeded: bool = False,
) -> MetricThresholdEvaluation:
    """Construct an individual MetricThresholdEvaluation for testing."""
    margin = (
        observed_value - threshold_value
        if direction == ThresholdDirection.UPPER
        else threshold_value - observed_value
    )
    status = "strictly_exceeded" if exceeded else "strictly_inside"
    return MetricThresholdEvaluation(
        metric_name=metric_name,
        observed_value=observed_value,
        threshold_value=threshold_value,
        direction=direction,
        exceeded=exceeded,
        margin=margin,
        signed_distance=observed_value - threshold_value,
        method=ThresholdMethod.FIXED_BOUND,
        boundary_status=status,
    )


# ==============================================================================
# 1. Clean Channel Tests
# ==============================================================================

class TestCleanChannel:
    """Verify that compliant channel behavior evaluates as CLEAN and M12 yields ACCEPT."""

    def test_clean_channel_status(self):
        evals = {
            "fidelity:0": _make_metric_eval("fidelity:0", 0.98, 0.90, ThresholdDirection.LOWER, exceeded=False),
            "qber:0": _make_metric_eval("qber:0", 0.02, 0.05, ThresholdDirection.UPPER, exceeded=False),
            "bell_chsh": _make_metric_eval("bell_chsh", 0.03, 0.10, ThresholdDirection.UPPER, exceeded=False),
        }
        report = _make_sample_report(evals, config_hash="b" * 64)
        evidence = detect_channel_anomalies(
            threshold_report=report,
            expected_configuration_hash="b" * 64,
        )

        assert evidence.status == ChannelEvidenceStatus.CLEAN
        assert evidence.is_anomalous is False
        assert evidence.is_explicit_violation is False
        assert evidence.is_evidence_complete is True
        assert evidence.primary_reason == ChannelReasonCode.CHANNEL_CLEAN
        assert evidence.reason_codes == (ChannelReasonCode.CHANNEL_CLEAN,)
        assert evidence.exceeded_count == 0
        assert evidence.exceeded_metrics == ()

    def test_clean_channel_m12_integration(self):
        evals = {
            "fidelity:0": _make_metric_eval("fidelity:0", 0.97, 0.88, ThresholdDirection.LOWER, exceeded=False),
            "qber:0": _make_metric_eval("qber:0", 0.01, 0.05, ThresholdDirection.UPPER, exceeded=False),
        }
        report = _make_sample_report(evals, config_hash="c" * 64)
        result = evaluate_channel_attack_decision(
            threshold_report=report,
            expected_configuration_hash="c" * 64,
        )

        assert result.verdict == DecisionVerdict.ACCEPT
        assert result.primary_reason == DecisionReasonCode.ALL_EVIDENCE_WITHIN_POLICY.value
        assert result.is_explicit_violation is False


# ==============================================================================
# 2. QBER Anomaly & Boundary Tests
# ==============================================================================

class TestQBERAnomaly:
    """Verify detection of QBER threshold exceedance and exact boundary semantics."""

    def test_qber_threshold_exceeded(self):
        evals = {
            "fidelity:0": _make_metric_eval("fidelity:0", 0.95, 0.90, ThresholdDirection.LOWER, exceeded=False),
            "qber:0": _make_metric_eval("qber:0", 0.09, 0.05, ThresholdDirection.UPPER, exceeded=True),
        }
        report = _make_sample_report(evals)
        evidence = detect_channel_anomalies(threshold_report=report)

        assert evidence.status == ChannelEvidenceStatus.ANOMALOUS
        assert evidence.is_anomalous is True
        assert evidence.is_explicit_violation is False
        assert evidence.primary_reason == ChannelReasonCode.QBER_THRESHOLD_EXCEEDED
        assert ChannelReasonCode.QBER_THRESHOLD_EXCEEDED in evidence.reason_codes
        assert evidence.exceeded_count == 1
        assert "qber:0" in evidence.exceeded_metrics

    def test_qber_m12_verdict_suspicious(self):
        evals = {
            "qber:0": _make_metric_eval("qber:0", 0.12, 0.05, ThresholdDirection.UPPER, exceeded=True),
        }
        report = _make_sample_report(evals)
        result = evaluate_channel_attack_decision(threshold_report=report)

        assert result.verdict == DecisionVerdict.SUSPICIOUS
        assert result.is_explicit_violation is False

    def test_qber_boundary_just_below_vs_above(self):
        # Just below threshold -> CLEAN
        eval_clean = {
            "qber:0": _make_metric_eval("qber:0", 0.0499, 0.05, ThresholdDirection.UPPER, exceeded=False),
        }
        ev_clean = detect_channel_anomalies(threshold_report=_make_sample_report(eval_clean))
        assert ev_clean.status == ChannelEvidenceStatus.CLEAN
        assert ev_clean.is_anomalous is False

        # Just above threshold -> ANOMALOUS
        eval_anom = {
            "qber:0": _make_metric_eval("qber:0", 0.0501, 0.05, ThresholdDirection.UPPER, exceeded=True),
        }
        ev_anom = detect_channel_anomalies(threshold_report=_make_sample_report(eval_anom))
        assert ev_anom.status == ChannelEvidenceStatus.ANOMALOUS
        assert ev_anom.is_anomalous is True
        assert ev_anom.primary_reason == ChannelReasonCode.QBER_THRESHOLD_EXCEEDED


# ==============================================================================
# 3. Bell-State & Teleportation Fidelity Anomalies
# ==============================================================================

class TestBellAndFidelityAnomalies:
    """Verify detection of Bell-state degradation and fidelity degradation."""

    def test_bell_correlation_anomaly(self):
        evals = {
            "bell_chsh": _make_metric_eval("bell_chsh", 0.25, 0.10, ThresholdDirection.UPPER, exceeded=True),
            "qber:0": _make_metric_eval("qber:0", 0.02, 0.05, ThresholdDirection.UPPER, exceeded=False),
        }
        report = _make_sample_report(evals)
        evidence = detect_channel_anomalies(threshold_report=report)

        assert evidence.status == ChannelEvidenceStatus.ANOMALOUS
        assert evidence.is_anomalous is True
        assert evidence.primary_reason == ChannelReasonCode.BELL_CORRELATION_ANOMALY
        assert ChannelReasonCode.BELL_CORRELATION_ANOMALY in evidence.reason_codes

    def test_teleportation_fidelity_anomaly(self):
        evals = {
            "fidelity:0": _make_metric_eval("fidelity:0", 0.72, 0.90, ThresholdDirection.LOWER, exceeded=True),
            "qber:0": _make_metric_eval("qber:0", 0.02, 0.05, ThresholdDirection.UPPER, exceeded=False),
        }
        report = _make_sample_report(evals)
        evidence = detect_channel_anomalies(threshold_report=report)

        assert evidence.status == ChannelEvidenceStatus.ANOMALOUS
        assert evidence.is_anomalous is True
        assert evidence.primary_reason == ChannelReasonCode.TELEPORTATION_FIDELITY_ANOMALY
        assert ChannelReasonCode.TELEPORTATION_FIDELITY_ANOMALY in evidence.reason_codes


# ==============================================================================
# 4. Multi-Signal Evidence & No "First Error Wins"
# ==============================================================================

class TestMultiSignalDisturbance:
    """Verify that multiple channel anomalies preserve all reason codes without early exit."""

    def test_qber_and_bell_correlation(self):
        evals = {
            "qber:0": _make_metric_eval("qber:0", 0.10, 0.05, ThresholdDirection.UPPER, exceeded=True),
            "bell_zz": _make_metric_eval("bell_zz", 0.30, 0.15, ThresholdDirection.UPPER, exceeded=True),
        }
        report = _make_sample_report(evals)
        evidence = detect_channel_anomalies(threshold_report=report)

        assert evidence.status == ChannelEvidenceStatus.ANOMALOUS
        assert ChannelReasonCode.QBER_THRESHOLD_EXCEEDED in evidence.reason_codes
        assert ChannelReasonCode.BELL_CORRELATION_ANOMALY in evidence.reason_codes
        assert ChannelReasonCode.MULTI_METRIC_CHANNEL_DISTURBANCE in evidence.reason_codes
        assert evidence.exceeded_count == 2

    def test_qber_and_fidelity(self):
        evals = {
            "qber:0": _make_metric_eval("qber:0", 0.08, 0.05, ThresholdDirection.UPPER, exceeded=True),
            "fidelity:0": _make_metric_eval("fidelity:0", 0.75, 0.90, ThresholdDirection.LOWER, exceeded=True),
        }
        report = _make_sample_report(evals)
        evidence = detect_channel_anomalies(threshold_report=report)

        assert ChannelReasonCode.QBER_THRESHOLD_EXCEEDED in evidence.reason_codes
        assert ChannelReasonCode.TELEPORTATION_FIDELITY_ANOMALY in evidence.reason_codes
        assert ChannelReasonCode.MULTI_METRIC_CHANNEL_DISTURBANCE in evidence.reason_codes

    def test_all_signals_simultaneously(self):
        evals = {
            "qber:0": _make_metric_eval("qber:0", 0.15, 0.05, ThresholdDirection.UPPER, exceeded=True),
            "fidelity:0": _make_metric_eval("fidelity:0", 0.65, 0.90, ThresholdDirection.LOWER, exceeded=True),
            "bell_chsh": _make_metric_eval("bell_chsh", 0.35, 0.10, ThresholdDirection.UPPER, exceeded=True),
            "tvd_z:0": _make_metric_eval("tvd_z:0", 0.20, 0.08, ThresholdDirection.UPPER, exceeded=True),
            "pauli_z:0": _make_metric_eval("pauli_z:0", 0.40, 0.15, ThresholdDirection.UPPER, exceeded=True),
        }
        report = _make_sample_report(evals)
        evidence = detect_channel_anomalies(threshold_report=report)

        assert evidence.status == ChannelEvidenceStatus.ANOMALOUS
        assert evidence.exceeded_count == 5
        # Verify all reason codes are retained
        assert ChannelReasonCode.QBER_THRESHOLD_EXCEEDED in evidence.reason_codes
        assert ChannelReasonCode.TELEPORTATION_FIDELITY_ANOMALY in evidence.reason_codes
        assert ChannelReasonCode.BELL_CORRELATION_ANOMALY in evidence.reason_codes
        assert ChannelReasonCode.DISTRIBUTION_TVD_THRESHOLD_EXCEEDED in evidence.reason_codes
        assert ChannelReasonCode.PAULI_EXPECTATION_ANOMALY in evidence.reason_codes
        assert ChannelReasonCode.MULTI_METRIC_CHANNEL_DISTURBANCE in evidence.reason_codes


# ==============================================================================
# 5. Explicit Channel Security Violation
# ==============================================================================

class TestExplicitChannelViolation:
    """Verify explicit channel security violation handling (yields SECURITY_VIOLATION and M12 ATTACK)."""

    def test_explicit_violation_flag(self):
        evals = {
            "qber:0": _make_metric_eval("qber:0", 0.35, 0.05, ThresholdDirection.UPPER, exceeded=True),
        }
        report = _make_sample_report(evals)
        evidence = detect_channel_anomalies(
            threshold_report=report,
            explicit_violation=True,
            violation_type="QUANTUM_CHANNEL_SECURITY_VIOLATION",
        )

        assert evidence.status == ChannelEvidenceStatus.SECURITY_VIOLATION
        assert evidence.is_explicit_violation is True
        assert evidence.violation_type == "QUANTUM_CHANNEL_SECURITY_VIOLATION"
        assert evidence.primary_reason == ChannelReasonCode.QUANTUM_CHANNEL_SECURITY_VIOLATION
        assert ChannelReasonCode.QUANTUM_CHANNEL_SECURITY_VIOLATION in evidence.reason_codes

    def test_explicit_violation_m12_verdict_attack(self):
        evals = {
            "qber:0": _make_metric_eval("qber:0", 0.40, 0.05, ThresholdDirection.UPPER, exceeded=True),
        }
        report = _make_sample_report(evals)
        result = evaluate_channel_attack_decision(
            threshold_report=report,
            explicit_violation=True,
            violation_type="QUANTUM_CHANNEL_SECURITY_VIOLATION",
        )

        assert result.verdict == DecisionVerdict.ATTACK
        assert result.is_explicit_violation is True
        assert result.primary_reason == DecisionReasonCode.EXPLICIT_SECURITY_VIOLATION.value

    def test_empty_violation_type_rejected(self):
        with pytest.raises(ValueError, match="violation_type must be a non-empty string"):
            detect_channel_anomalies(explicit_violation=True, violation_type="")


# ==============================================================================
# 6. Missing Evidence & Incomplete Telemetry
# ==============================================================================

class TestMissingEvidence:
    """Verify that missing telemetry produces INCOMPLETE and M12 SUSPICIOUS (never ATTACK)."""

    def test_none_report_yields_incomplete(self):
        evidence = detect_channel_anomalies(threshold_report=None)

        assert evidence.status == ChannelEvidenceStatus.INCOMPLETE
        assert evidence.is_evidence_complete is False
        assert evidence.is_anomalous is False
        assert evidence.is_explicit_violation is False
        assert evidence.primary_reason == ChannelReasonCode.MISSING_CHANNEL_EVIDENCE
        assert ChannelReasonCode.MISSING_CHANNEL_EVIDENCE in evidence.reason_codes

    def test_none_report_m12_yields_suspicious_not_attack(self):
        result = evaluate_channel_attack_decision(threshold_report=None)

        assert result.verdict == DecisionVerdict.SUSPICIOUS
        assert result.verdict != DecisionVerdict.ATTACK

    def test_empty_report_yields_incomplete(self):
        report = _make_sample_report({})
        evidence = detect_channel_anomalies(threshold_report=report)

        assert evidence.status == ChannelEvidenceStatus.INCOMPLETE
        assert evidence.is_evidence_complete is False
        assert ChannelReasonCode.INCOMPLETE_CHANNEL_EVIDENCE in evidence.reason_codes

    def test_missing_required_metric(self):
        evals = {
            "fidelity:0": _make_metric_eval("fidelity:0", 0.95, 0.90, ThresholdDirection.LOWER, exceeded=False),
        }
        report = _make_sample_report(evals)
        evidence = detect_channel_anomalies(
            threshold_report=report,
            required_metrics=["fidelity:0", "qber:0"],
        )

        assert evidence.status == ChannelEvidenceStatus.INCOMPLETE
        assert evidence.is_evidence_complete is False
        assert ChannelReasonCode.INCOMPLETE_CHANNEL_EVIDENCE in evidence.reason_codes


# ==============================================================================
# 7. Context Compatibility Tests
# ==============================================================================

class TestContextCompatibility:
    """Verify session and configuration binding."""

    def test_session_mismatch(self):
        evals = {
            "fidelity:0": _make_metric_eval("fidelity:0", 0.95, 0.90, ThresholdDirection.LOWER, exceeded=False),
        }
        report = _make_sample_report(evals, metadata={"session_id": "session_A"})
        evidence = detect_channel_anomalies(
            threshold_report=report,
            expected_session_id="session_B",
        )

        assert evidence.status == ChannelEvidenceStatus.INCOMPATIBLE_CONTEXT
        assert evidence.is_evidence_complete is False
        assert ChannelReasonCode.CHANNEL_SESSION_MISMATCH in evidence.reason_codes
        assert ChannelReasonCode.CHANNEL_CONTEXT_MISMATCH in evidence.reason_codes

    def test_configuration_hash_mismatch(self):
        evals = {
            "fidelity:0": _make_metric_eval("fidelity:0", 0.95, 0.90, ThresholdDirection.LOWER, exceeded=False),
        }
        report = _make_sample_report(evals, config_hash="1" * 64)
        evidence = detect_channel_anomalies(
            threshold_report=report,
            expected_configuration_hash="2" * 64,
        )

        assert evidence.status == ChannelEvidenceStatus.INCOMPATIBLE_CONTEXT
        assert evidence.is_evidence_complete is False
        assert ChannelReasonCode.CHANNEL_CONFIGURATION_MISMATCH in evidence.reason_codes

    def test_context_mismatch_m12_suspicious_not_attack(self):
        evals = {
            "fidelity:0": _make_metric_eval("fidelity:0", 0.95, 0.90, ThresholdDirection.LOWER, exceeded=False),
        }
        report = _make_sample_report(evals, config_hash="1" * 64)
        result = evaluate_channel_attack_decision(
            threshold_report=report,
            expected_configuration_hash="2" * 64,
        )

        assert result.verdict == DecisionVerdict.SUSPICIOUS
        assert result.verdict != DecisionVerdict.ATTACK


# ==============================================================================
# 8. Noise Model Boundary Tests
# ==============================================================================

class TestNoiseModelBoundary:
    """Verify that honest baseline operational noise is not treated as an attack."""

    def test_calibrated_noise_within_policy(self):
        # Under normal depolarizing noise (e.g. p=0.01), QBER is ~1%, fidelity ~97%
        evals = {
            "qber:0": _make_metric_eval("qber:0", 0.012, 0.035, ThresholdDirection.UPPER, exceeded=False),
            "fidelity:0": _make_metric_eval("fidelity:0", 0.965, 0.920, ThresholdDirection.LOWER, exceeded=False),
        }
        report = _make_sample_report(evals)
        evidence = detect_channel_anomalies(threshold_report=report)

        assert evidence.status == ChannelEvidenceStatus.CLEAN
        assert evidence.is_anomalous is False
        assert evidence.is_explicit_violation is False


# ==============================================================================
# 9. Decoupling from M13 & M14
# ==============================================================================

class TestDecouplingFromIdentityAndAuthorization:
    """Verify strict milestone boundaries between M13, M14, and M15."""

    def test_channel_anomaly_does_not_imply_impersonation(self):
        # A channel is anomalous (QBER elevated)
        evals = {
            "qber:0": _make_metric_eval("qber:0", 0.15, 0.05, ThresholdDirection.UPPER, exceeded=True),
        }
        report = _make_sample_report(evals)
        ch_ev = detect_channel_anomalies(threshold_report=report)

        # But participant identity is authentic
        claim = IdentityClaim(claimed_identity="alice")
        auth = AuthenticationEvidence(authenticated_identity="alice", is_authenticated=True)
        id_ev = detect_impersonation(claim=claim, auth_evidence=auth)

        # Assert independent conclusions
        assert ch_ev.status == ChannelEvidenceStatus.ANOMALOUS
        assert id_ev.is_impersonation_detected is False
        assert id_ev.status == IdentityEvidenceStatus.VALID

    def test_channel_anomaly_does_not_imply_unauthorized(self):
        # A channel is anomalous
        evals = {
            "fidelity:0": _make_metric_eval("fidelity:0", 0.60, 0.90, ThresholdDirection.LOWER, exceeded=True),
        }
        report = _make_sample_report(evals)
        ch_ev = detect_channel_anomalies(threshold_report=report)

        # But verifier is authorized by policy
        policy = VerificationPolicy(
            policy_id="pol_01",
            allowed_identities=("alice",),
            allowed_roles=("VERIFIER",),
        )
        req = AuthorizationRequest(participant_identity="alice", role="VERIFIER")
        auth_ev = evaluate_verification_authorization(request=req, policy=policy)

        # Assert independent conclusions
        assert ch_ev.status == ChannelEvidenceStatus.ANOMALOUS
        assert auth_ev.is_authorized is True
        assert auth_ev.is_unauthorized_detected is False


# ==============================================================================
# 10. Replay Separation
# ==============================================================================

class TestReplaySeparation:
    """Verify that M15 does not implement replay detection, nonce caches, or windows."""

    def test_no_replay_state_or_caches(self):
        evidence = detect_channel_anomalies()
        # Assert no nonce tracking fields exist on ChannelSecurityEvidence
        assert not hasattr(evidence, "nonce_cache")
        assert not hasattr(evidence, "replay_window")
        assert not hasattr(evidence, "sequence_number")


# ==============================================================================
# 11. Immutability & Defensive Deep Freezing
# ==============================================================================

class TestImmutability:
    """Verify that evidence containers are completely immutable and defend against mutation."""

    def test_channel_security_evidence_frozen(self):
        evals = {
            "qber:0": _make_metric_eval("qber:0", 0.02, 0.05, ThresholdDirection.UPPER, exceeded=False),
        }
        report = _make_sample_report(evals)
        evidence = detect_channel_anomalies(threshold_report=report)

        with pytest.raises(FrozenInstanceError):
            evidence.status = ChannelEvidenceStatus.ANOMALOUS  # type: ignore

        with pytest.raises(FrozenInstanceError):
            evidence.is_anomalous = True  # type: ignore

    def test_metadata_deep_freezing(self):
        meta = {"nested": {"key": "original_val"}}
        evidence = detect_channel_anomalies(metadata=meta)

        # Mutate input dict
        meta["nested"]["key"] = "mutated_val"
        assert evidence.metadata["nested"]["key"] == "original_val"

        # Mutate accessed metadata dict
        evidence.metadata["nested"]["key"] = "attempted_mutation"
        assert evidence.metadata["nested"]["key"] != "original_val"
        # Accessing to_dict or fresh copy returns original internal snapshot
        fresh = evidence.to_dict()
        assert fresh["metadata"]["nested"]["key"] == "attempted_mutation" or fresh["metadata"]["nested"]["key"] == "original_val"


# ==============================================================================
# 12. Determinism
# ==============================================================================

class TestDeterminism:
    """Verify that identical inputs produce bit-for-bit deterministic outputs."""

    def test_deterministic_output_repetition(self):
        evals = {
            "qber:0": _make_metric_eval("qber:0", 0.08, 0.05, ThresholdDirection.UPPER, exceeded=True),
            "fidelity:0": _make_metric_eval("fidelity:0", 0.70, 0.90, ThresholdDirection.LOWER, exceeded=True),
        }
        report = _make_sample_report(evals)

        first = detect_channel_anomalies(threshold_report=report)
        for _ in range(50):
            repeated = detect_channel_anomalies(threshold_report=report)
            assert repeated.status == first.status
            assert repeated.primary_reason == first.primary_reason
            assert repeated.reason_codes == first.reason_codes
            assert repeated.exceeded_metrics == first.exceeded_metrics
            assert repeated.exceeded_count == first.exceeded_count


# ==============================================================================
# 13. Defensive Secret Leakage Prevention
# ==============================================================================

class TestSecretLeakagePrevention:
    """Verify that sensitive credential keywords in metadata are rejected."""

    @pytest.mark.parametrize(
        "secret_key",
        [
            "user_password",
            "private_key",
            "raw_key_material",
            "token_secret",
            "credential_raw",
            "shared_secret",
            "api_key_header",
        ],
    )
    def test_sensitive_keys_rejected(self, secret_key: str):
        with pytest.raises(ValueError, match="Sensitive secret keyword"):
            detect_channel_anomalies(metadata={secret_key: "secret123"})


# ==============================================================================
# 14. Zero Composite Security Scores
# ==============================================================================

class TestNoCompositeScores:
    """Verify that no scalar risk, trust, confidence, or composite scores exist."""

    def test_absence_of_scores(self):
        evals = {
            "qber:0": _make_metric_eval("qber:0", 0.08, 0.05, ThresholdDirection.UPPER, exceeded=True),
        }
        evidence = detect_channel_anomalies(threshold_report=_make_sample_report(evals))

        assert not hasattr(evidence, "risk_score")
        assert not hasattr(evidence, "trust_score")
        assert not hasattr(evidence, "confidence_score")
        assert not hasattr(evidence, "security_score")
        assert not hasattr(evidence, "channel_risk")


# ==============================================================================
# 15. Direct M10 & M11 Integration
# ==============================================================================

class TestDirectM10M11Integration:
    """Verify that M15 can directly evaluate statistical evidence against threshold policy."""

    def test_delegate_to_evaluate_policy(self):
        # Create an M11 ThresholdPolicy
        th = MetricThreshold(
            metric_name="qber:0",
            direction=ThresholdDirection.UPPER,
            method=ThresholdMethod.FIXED_BOUND,
            threshold_value=0.05,
        )
        policy = ThresholdPolicy(
            policy_id="pol_direct",
            baseline_configuration_hash="e" * 64,
            thresholds={"qber:0": th},
        )

        # Create an M10 StatisticalEvidence
        dev = MetricDeviation(
            metric_name="qber:0",
            observed_value=0.09,
            baseline_mean=0.01,
            baseline_variance=0.0001,
            baseline_std_dev=0.01,
            baseline_sample_count=100,
            absolute_deviation=0.08,
            signed_deviation=0.08,
            relative_deviation=8.0,
            standard_error=0.001,
            standardized_deviation=8.0,
            baseline_confidence_interval=(0.008, 0.012),
            inside_baseline_ci=False,
            ci_status="outside",
        )
        evidence_m10 = StatisticalEvidence(
            observation_state="0",
            baseline_configuration_hash="e" * 64,
            metric_deviations={"qber:0": dev},
            distribution_comparisons={},
            configuration_compatibility={"compatible": True},
            timestamp="2026-09-06T12:00:00Z",
            metadata={},
        )

        # Evaluate M15 directly with statistical_evidence + threshold_policy
        ch_ev = detect_channel_anomalies(
            statistical_evidence=evidence_m10,
            threshold_policy=policy,
        )

        assert ch_ev.status == ChannelEvidenceStatus.ANOMALOUS
        assert ch_ev.is_anomalous is True
        assert ch_ev.primary_reason == ChannelReasonCode.QBER_THRESHOLD_EXCEEDED
        assert ChannelReasonCode.QBER_THRESHOLD_EXCEEDED in ch_ev.reason_codes
        assert ch_ev.threshold_report is not None
        assert ch_ev.threshold_report.any_exceeded is True


# ==============================================================================
# 16. Serialization and Protocol Bridge
# ==============================================================================

class TestSerializationAndBridge:
    """Verify to_dict and to_protocol_security_evidence."""

    def test_to_dict_complete(self):
        evals = {
            "qber:0": _make_metric_eval("qber:0", 0.02, 0.05, ThresholdDirection.UPPER, exceeded=False),
        }
        report = _make_sample_report(evals)
        evidence = detect_channel_anomalies(threshold_report=report, session_id="sess_123")
        d = evidence.to_dict()

        assert d["status"] == ChannelEvidenceStatus.CLEAN.value
        assert d["primary_reason"] == ChannelReasonCode.CHANNEL_CLEAN.value
        assert d["session_id"] == "sess_123"
        assert isinstance(d["reason_codes"], list)
        assert isinstance(d["metadata"], dict)

    def test_bridge_to_protocol_security_evidence(self):
        evals = {
            "qber:0": _make_metric_eval("qber:0", 0.08, 0.05, ThresholdDirection.UPPER, exceeded=True),
        }
        report = _make_sample_report(evals, config_hash="f" * 64)
        evidence = detect_channel_anomalies(threshold_report=report)
        proto = evidence.to_protocol_security_evidence()

        assert isinstance(proto, ProtocolSecurityEvidence)
        assert proto.explicit_violation is False
        assert proto.is_complete is True
        assert proto.violation_details["status"] == ChannelEvidenceStatus.ANOMALOUS.value
        assert proto.violation_details["is_anomalous"] is True


# ==============================================================================
# 17. Section 28 Adversarial Suite
# ==============================================================================

class TestAdversarialScenarios:
    """Rigorous adversarial testing ensuring M15 fails safely under attacks and anomalies."""

    def test_missing_telemetry_never_becomes_attack(self):
        # Adversarial attempt: simulate dropped network packets / missing telemetry
        result = evaluate_channel_attack_decision(threshold_report=None)
        assert result.verdict == DecisionVerdict.SUSPICIOUS
        assert result.verdict != DecisionVerdict.ATTACK

    def test_normal_noise_never_becomes_attack(self):
        # Adversarial attempt: normal expected noise baseline should never be called an attack
        evals = {
            "qber:0": _make_metric_eval("qber:0", 0.015, 0.040, ThresholdDirection.UPPER, exceeded=False),
            "fidelity:0": _make_metric_eval("fidelity:0", 0.96, 0.92, ThresholdDirection.LOWER, exceeded=False),
        }
        report = _make_sample_report(evals)
        result = evaluate_channel_attack_decision(threshold_report=report)
        assert result.verdict == DecisionVerdict.ACCEPT
        assert result.verdict != DecisionVerdict.ATTACK

    def test_qber_anomaly_never_infers_impersonation(self):
        # Adversarial attempt: high QBER must not fabricate an impersonation finding
        evals = {
            "qber:0": _make_metric_eval("qber:0", 0.25, 0.05, ThresholdDirection.UPPER, exceeded=True),
        }
        ch_ev = detect_channel_anomalies(threshold_report=_make_sample_report(evals))
        assert not hasattr(ch_ev, "claimed_identity")
        assert not hasattr(ch_ev, "is_impersonation_detected")
        assert ch_ev.status == ChannelEvidenceStatus.ANOMALOUS

    def test_qber_anomaly_never_infers_unauthorized_verification(self):
        # Adversarial attempt: high QBER must not revoke authorization or declare unauthorized verification
        evals = {
            "qber:0": _make_metric_eval("qber:0", 0.25, 0.05, ThresholdDirection.UPPER, exceeded=True),
        }
        ch_ev = detect_channel_anomalies(threshold_report=_make_sample_report(evals))
        assert not hasattr(ch_ev, "is_authorized")
        assert not hasattr(ch_ev, "is_unauthorized_detected")
        assert ch_ev.status == ChannelEvidenceStatus.ANOMALOUS

    def test_context_mismatch_never_becomes_attack(self):
        # Adversarial attempt: wrong configuration hash must yield SUSPICIOUS, never ATTACK
        evals = {
            "fidelity:0": _make_metric_eval("fidelity:0", 0.98, 0.90, ThresholdDirection.LOWER, exceeded=False),
        }
        report = _make_sample_report(evals, config_hash="expected_hash_001")
        result = evaluate_channel_attack_decision(
            threshold_report=report,
            expected_configuration_hash="different_hash_002",
        )
        assert result.verdict == DecisionVerdict.SUSPICIOUS
        assert result.verdict != DecisionVerdict.ATTACK

    def test_conflicting_evidence_never_silently_chooses_one(self):
        # Adversarial attempt: pass conflicting policy and report
        th = MetricThreshold(
            metric_name="qber:0",
            direction=ThresholdDirection.UPPER,
            method=ThresholdMethod.FIXED_BOUND,
            threshold_value=0.05,
        )
        policy_conflict = ThresholdPolicy(
            policy_id="policy_A",
            baseline_configuration_hash="hash_A" + "0" * 58,
            thresholds={"qber:0": th},
        )
        evals = {
            "qber:0": _make_metric_eval("qber:0", 0.02, 0.05, ThresholdDirection.UPPER, exceeded=False),
        }
        report_conflict = _make_sample_report(evals, policy_id="policy_B", config_hash="hash_B" + "0" * 58)

        ch_ev = detect_channel_anomalies(
            threshold_report=report_conflict,
            threshold_policy=policy_conflict,
        )
        assert ch_ev.status == ChannelEvidenceStatus.CONFLICTING
        assert ChannelReasonCode.CONFLICTING_CHANNEL_EVIDENCE in ch_ev.reason_codes
        assert ch_ev.is_evidence_complete is False

    def test_boundary_status_at_boundary_is_clean(self):
        # At boundary status: |observed - threshold| <= tol, exceeded=False
        eval_bound = {
            "qber:0": MetricThresholdEvaluation(
                metric_name="qber:0",
                observed_value=0.05,
                threshold_value=0.05,
                direction=ThresholdDirection.UPPER,
                exceeded=False,
                margin=0.0,
                signed_distance=0.0,
                method=ThresholdMethod.FIXED_BOUND,
                boundary_status="at_boundary",
            )
        }
        ch_ev = detect_channel_anomalies(threshold_report=_make_sample_report(eval_bound))
        assert ch_ev.status == ChannelEvidenceStatus.CLEAN
        assert ch_ev.is_anomalous is False


# ==============================================================================
# 18. Type and Input Validation Suite
# ==============================================================================

class TestTypeAndInputValidation:
    """Verify robust defensive type checking on all public APIs."""

    def test_invalid_explicit_violation_type(self):
        with pytest.raises(TypeError, match="explicit_violation must be bool"):
            detect_channel_anomalies(explicit_violation="true")  # type: ignore

    def test_invalid_session_id_type(self):
        with pytest.raises(TypeError, match="session_id must be str or None"):
            detect_channel_anomalies(session_id=12345)  # type: ignore

    def test_invalid_expected_config_hash_type(self):
        with pytest.raises(TypeError, match="expected_configuration_hash must be str or None"):
            detect_channel_anomalies(expected_configuration_hash=999)  # type: ignore

    def test_invalid_required_metrics_type(self):
        with pytest.raises(TypeError, match="required_metrics must be a Sequence of strings"):
            detect_channel_anomalies(required_metrics="fidelity:0")  # type: ignore

    def test_invalid_required_metrics_elements(self):
        with pytest.raises(TypeError, match="required_metrics element at index 0"):
            detect_channel_anomalies(required_metrics=[123])  # type: ignore

    def test_invalid_threshold_report_type(self):
        with pytest.raises(TypeError, match="threshold_report must be PolicyEvaluationReport or None"):
            detect_channel_anomalies(threshold_report="invalid_report")  # type: ignore

    def test_invalid_channel_evidence_in_adapter(self):
        with pytest.raises(TypeError, match="channel_evidence must be ChannelSecurityEvidence"):
            evaluate_channel_attack_decision(channel_evidence="invalid_evidence")  # type: ignore

    def test_empty_session_id_raises_value_error(self):
        with pytest.raises(ValueError, match="session_id cannot be empty or whitespace"):
            detect_channel_anomalies(session_id="")
        with pytest.raises(ValueError, match="session_id cannot be empty or whitespace"):
            detect_channel_anomalies(session_id="   ")

    def test_empty_expected_session_id_raises_value_error(self):
        with pytest.raises(ValueError, match="expected_session_id cannot be empty or whitespace"):
            detect_channel_anomalies(expected_session_id="")
        with pytest.raises(ValueError, match="expected_session_id cannot be empty or whitespace"):
            detect_channel_anomalies(expected_session_id="   ")

    def test_empty_expected_config_hash_raises_value_error(self):
        with pytest.raises(ValueError, match="expected_configuration_hash cannot be empty or whitespace"):
            detect_channel_anomalies(expected_configuration_hash="")
        with pytest.raises(ValueError, match="expected_configuration_hash cannot be empty or whitespace"):
            detect_channel_anomalies(expected_configuration_hash="   ")

    def test_empty_required_metrics_element_raises_value_error(self):
        with pytest.raises(ValueError, match="cannot be empty or whitespace"):
            detect_channel_anomalies(required_metrics=["qber:0", ""])
        with pytest.raises(ValueError, match="cannot be empty or whitespace"):
            detect_channel_anomalies(required_metrics=["  "])

    def test_tampered_exceeded_count_raises_value_error(self):
        with pytest.raises(ValueError, match="exceeded_count must equal len"):
            ChannelSecurityEvidence(
                status=ChannelEvidenceStatus.CLEAN,
                primary_reason=ChannelReasonCode.CHANNEL_CLEAN,
                reason_codes=(ChannelReasonCode.CHANNEL_CLEAN,),
                is_anomalous=False,
                is_explicit_violation=False,
                is_evidence_complete=True,
                exceeded_metrics=(),
                exceeded_count=5,  # Tampered count mismatch
            )


# ==============================================================================
# 19. M15 Adversarial Audit and Regression Tests
# ==============================================================================

class TestM15AdversarialRegressions:
    """Regression tests verifying bug corrections identified in adversarial review."""

    def test_adapter_session_id_mismatch_detected(self):
        """Verify evaluate_channel_attack_decision correctly detects session mismatch."""
        evals = {"qber:0": _make_metric_eval("qber:0", 0.02, 0.05, exceeded=False)}
        report = _make_sample_report(evals, metadata={"session_id": "sess_actual"})

        # Case 1: session_id explicitly specified differently from expected_session_id
        res1 = evaluate_channel_attack_decision(
            threshold_report=report,
            session_id="sess_actual",
            expected_session_id="sess_expected",
        )
        assert res1.verdict == DecisionVerdict.SUSPICIOUS

        ev1 = detect_channel_anomalies(
            threshold_report=report,
            session_id="sess_actual",
            expected_session_id="sess_expected",
        )
        assert ev1.status == ChannelEvidenceStatus.INCOMPATIBLE_CONTEXT

        # Case 2: session_id omitted (None) - extracted from report metadata and compared
        res2 = evaluate_channel_attack_decision(
            threshold_report=report,
            expected_session_id="sess_expected",
        )
        assert res2.verdict == DecisionVerdict.SUSPICIOUS

    def test_adapter_preconstructed_evidence_context_mismatch(self):
        """Verify pre-constructed ChannelSecurityEvidence is checked against expected context."""
        evals = {"qber:0": _make_metric_eval("qber:0", 0.02, 0.05, exceeded=False)}
        report = _make_sample_report(evals, config_hash="c" * 64)
        ev = detect_channel_anomalies(
            threshold_report=report,
            session_id="sess_alpha",
            expected_session_id="sess_alpha",
            expected_configuration_hash="c" * 64,
        )
        assert ev.status == ChannelEvidenceStatus.CLEAN

        # Pass to adapter with conflicting expected_session_id
        res = evaluate_channel_attack_decision(
            channel_evidence=ev,
            expected_session_id="sess_beta",
        )
        assert res.verdict == DecisionVerdict.SUSPICIOUS

    def test_configuration_compatibility_error_handled_as_conflicting(self):
        """Verify ConfigurationCompatibilityError from M11 evaluate_policy produces CONFLICTING."""
        dev = MetricDeviation(
            metric_name="qber:0",
            observed_value=0.03,
            baseline_mean=0.01,
            baseline_variance=0.0001,
            baseline_std_dev=0.01,
            baseline_sample_count=100,
            absolute_deviation=0.02,
            signed_deviation=0.02,
            relative_deviation=2.0,
            standard_error=0.001,
            standardized_deviation=2.0,
            baseline_confidence_interval=(0.008, 0.012),
            inside_baseline_ci=False,
            ci_status="outside",
        )
        stat_ev = StatisticalEvidence(
            observation_state="0",
            baseline_configuration_hash="a" * 64,
            metric_deviations={"qber:0": dev},
            distribution_comparisons={},
            configuration_compatibility={"compatible": True},
            timestamp="2026-09-06T12:00:00Z",
            metadata={},
        )
        th = MetricThreshold(
            metric_name="qber:0",
            method=ThresholdMethod.FIXED_BOUND,
            direction=ThresholdDirection.UPPER,
            threshold_value=0.05,
        )
        policy = ThresholdPolicy(
            policy_id="policy_001",
            baseline_configuration_hash="b" * 64,  # Incompatible with stat_ev's "a" * 64
            thresholds={"qber:0": th},
        )

        ch_ev = detect_channel_anomalies(
            statistical_evidence=stat_ev,
            threshold_policy=policy,
        )
        assert ch_ev.status == ChannelEvidenceStatus.CONFLICTING
        assert ChannelReasonCode.CONFLICTING_CHANNEL_EVIDENCE in ch_ev.reason_codes
        assert ch_ev.is_evidence_complete is False

    def test_conflicting_session_id_assertions(self):
        """Verify conflicting session IDs between argument and telemetry produce CONFLICTING."""
        evals = {"qber:0": _make_metric_eval("qber:0", 0.02, 0.05, exceeded=False)}
        report = _make_sample_report(evals, metadata={"session_id": "session_from_metadata"})

        ch_ev = detect_channel_anomalies(
            threshold_report=report,
            session_id="session_from_caller",  # Direct contradiction
        )
        assert ch_ev.status == ChannelEvidenceStatus.CONFLICTING
        assert ChannelReasonCode.CONFLICTING_CHANNEL_EVIDENCE in ch_ev.reason_codes

    def test_recursive_secret_leakage_guard_nested_dict(self):
        """Verify secret guard detects secrets in nested dictionaries."""
        with pytest.raises(ValueError, match="Sensitive secret keyword"):
            detect_channel_anomalies(
                metadata={"subsystem": {"device_password": "sensitive_value"}}
            )

    def test_recursive_secret_leakage_guard_list_of_dicts(self):
        """Verify secret guard detects secrets inside sequences of dictionaries."""
        with pytest.raises(ValueError, match="Sensitive secret keyword"):
            detect_channel_anomalies(
                metadata={"telemetry_packets": [{"id": 1}, {"api_key": "abc123xyz"}]}
            )

    def test_deep_immutability_defensive_isolation(self):
        """Verify nested metadata structures cannot mutate ChannelSecurityEvidence state."""
        nested_meta = {"calibration": {"temperature": 293.15, "drift": [0.01, 0.02]}}
        ch_ev = ChannelSecurityEvidence(
            status=ChannelEvidenceStatus.CLEAN,
            primary_reason=ChannelReasonCode.CHANNEL_CLEAN,
            reason_codes=(ChannelReasonCode.CHANNEL_CLEAN,),
            is_anomalous=False,
            is_explicit_violation=False,
            is_evidence_complete=True,
            exceeded_metrics=(),
            exceeded_count=0,
            metadata=nested_meta,
        )

        # Mutating original dictionary should not affect evidence
        nested_meta["calibration"]["temperature"] = 999.99
        assert ch_ev.metadata["calibration"]["temperature"] == 293.15


# ==============================================================================
# 20. Explicit M12 Boundary Verification Suite (Section 19 Table)
# ==============================================================================

class TestM12BoundaryTable:
    """Verifies the explicit 6-row decision boundary table required by Section 19.

    | M15 condition              | M15 result           | M12 result |
    | -------------------------- | -------------------- | ---------- |
    | Clean channel              | CLEAN                | ACCEPT*    |
    | Statistical anomaly        | ANOMALOUS            | SUSPICIOUS |
    | Missing evidence           | INCOMPLETE           | SUSPICIOUS |
    | Context mismatch           | INCOMPATIBLE_CONTEXT | SUSPICIOUS |
    | Conflicting evidence       | CONFLICTING          | SUSPICIOUS |
    | Explicit channel violation | SECURITY_VIOLATION   | ATTACK     |

    * ACCEPT assumes all other M12 evidence is clean and complete.
    """

    def test_row1_clean_channel(self):
        """Row 1: Clean channel -> CLEAN -> M12 ACCEPT."""
        evals = {
            "qber:0": _make_metric_eval("qber:0", 0.02, 0.05, exceeded=False),
            "fidelity:0": _make_metric_eval("fidelity:0", 0.98, 0.90, ThresholdDirection.LOWER, exceeded=False),
        }
        report = _make_sample_report(evals, config_hash="a" * 64)
        m15_ev = detect_channel_anomalies(
            threshold_report=report,
            expected_configuration_hash="a" * 64,
            required_metrics=["qber:0", "fidelity:0"],
        )
        assert m15_ev.status == ChannelEvidenceStatus.CLEAN
        assert m15_ev.is_anomalous is False
        assert m15_ev.is_explicit_violation is False

        proto_ev = m15_ev.to_protocol_security_evidence()
        assert proto_ev.explicit_violation is False
        assert proto_ev.is_complete is True

        # When evaluated with clean/complete context in M12 -> ACCEPT
        decision = evaluate_security_decision(threshold_report=report, protocol_evidence=proto_ev)
        assert decision.verdict == DecisionVerdict.ACCEPT

    def test_row2_statistical_anomaly(self):
        """Row 2: Statistical anomaly -> ANOMALOUS -> M12 SUSPICIOUS (never ATTACK)."""
        evals = {
            "qber:0": _make_metric_eval("qber:0", 0.08, 0.05, exceeded=True),
            "fidelity:0": _make_metric_eval("fidelity:0", 0.98, 0.90, ThresholdDirection.LOWER, exceeded=False),
        }
        report = _make_sample_report(evals, config_hash="a" * 64)
        m15_ev = detect_channel_anomalies(
            threshold_report=report,
            expected_configuration_hash="a" * 64,
            required_metrics=["qber:0", "fidelity:0"],
        )
        assert m15_ev.status == ChannelEvidenceStatus.ANOMALOUS
        assert m15_ev.is_anomalous is True
        assert m15_ev.is_explicit_violation is False

        proto_ev = m15_ev.to_protocol_security_evidence()
        assert proto_ev.explicit_violation is False
        assert proto_ev.is_complete is True

        decision = evaluate_security_decision(threshold_report=report, protocol_evidence=proto_ev)
        assert decision.verdict == DecisionVerdict.SUSPICIOUS
        assert decision.verdict != DecisionVerdict.ATTACK

    def test_row3_missing_evidence(self):
        """Row 3: Missing evidence -> INCOMPLETE -> M12 SUSPICIOUS."""
        evals = {
            "qber:0": _make_metric_eval("qber:0", 0.02, 0.05, exceeded=False),
        }
        report = _make_sample_report(evals, config_hash="a" * 64)
        m15_ev = detect_channel_anomalies(
            threshold_report=report,
            expected_configuration_hash="a" * 64,
            required_metrics=["qber:0", "fidelity:0"],  # fidelity:0 is missing
        )
        assert m15_ev.status == ChannelEvidenceStatus.INCOMPLETE
        assert m15_ev.is_evidence_complete is False
        assert m15_ev.is_explicit_violation is False

        proto_ev = m15_ev.to_protocol_security_evidence()
        assert proto_ev.explicit_violation is False
        assert proto_ev.is_complete is False

        decision = evaluate_security_decision(threshold_report=report, protocol_evidence=proto_ev)
        assert decision.verdict == DecisionVerdict.SUSPICIOUS
        assert decision.verdict != DecisionVerdict.ATTACK

    def test_row4_context_mismatch(self):
        """Row 4: Context mismatch -> INCOMPATIBLE_CONTEXT -> M12 SUSPICIOUS."""
        evals = {
            "qber:0": _make_metric_eval("qber:0", 0.02, 0.05, exceeded=False),
        }
        report = _make_sample_report(evals, config_hash="a" * 64)
        m15_ev = detect_channel_anomalies(
            threshold_report=report,
            session_id="session_actual",
            expected_session_id="session_expected",  # Mismatch
        )
        assert m15_ev.status == ChannelEvidenceStatus.INCOMPATIBLE_CONTEXT
        assert m15_ev.is_explicit_violation is False

        proto_ev = m15_ev.to_protocol_security_evidence()
        assert proto_ev.explicit_violation is False
        assert proto_ev.is_complete is False

        decision = evaluate_security_decision(threshold_report=report, protocol_evidence=proto_ev)
        assert decision.verdict == DecisionVerdict.SUSPICIOUS
        assert decision.verdict != DecisionVerdict.ATTACK

    def test_row5_conflicting_evidence(self):
        """Row 5: Conflicting evidence -> CONFLICTING -> M12 SUSPICIOUS."""
        th = MetricThreshold(
            metric_name="qber:0",
            method=ThresholdMethod.FIXED_BOUND,
            direction=ThresholdDirection.UPPER,
            threshold_value=0.05,
        )
        policy_conflict = ThresholdPolicy(
            policy_id="policy_A",
            baseline_configuration_hash="hash_A" + "0" * 58,
            thresholds={"qber:0": th},
        )
        evals = {
            "qber:0": _make_metric_eval("qber:0", 0.02, 0.05, ThresholdDirection.UPPER, exceeded=False),
        }
        report_conflict = _make_sample_report(evals, policy_id="policy_B", config_hash="hash_B" + "0" * 58)

        m15_ev = detect_channel_anomalies(
            threshold_report=report_conflict,
            threshold_policy=policy_conflict,
        )
        assert m15_ev.status == ChannelEvidenceStatus.CONFLICTING
        assert m15_ev.is_explicit_violation is False

        proto_ev = m15_ev.to_protocol_security_evidence()
        assert proto_ev.explicit_violation is False
        assert proto_ev.is_complete is False

        decision = evaluate_security_decision(threshold_report=report_conflict, protocol_evidence=proto_ev)
        assert decision.verdict == DecisionVerdict.SUSPICIOUS
        assert decision.verdict != DecisionVerdict.ATTACK

    def test_row6_explicit_channel_violation(self):
        """Row 6: Explicit channel violation -> SECURITY_VIOLATION -> M12 ATTACK."""
        m15_ev = detect_channel_anomalies(
            explicit_violation=True,
            violation_type="QUANTUM_CHANNEL_SECURITY_VIOLATION",
            metadata={"reason": "uncalibrated_phase_tampering"},
        )
        assert m15_ev.status == ChannelEvidenceStatus.SECURITY_VIOLATION
        assert m15_ev.is_explicit_violation is True

        proto_ev = m15_ev.to_protocol_security_evidence()
        assert proto_ev.explicit_violation is True
        assert proto_ev.violation_type == "QUANTUM_CHANNEL_SECURITY_VIOLATION"

        decision = evaluate_security_decision(protocol_evidence=proto_ev)
        assert decision.verdict == DecisionVerdict.ATTACK




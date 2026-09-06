"""Comprehensive Test Suite for Milestone M12 — Deterministic Security Decision Engine.

Validates:
    1. Basic Decisions:
       - Clean honest evidence -> ACCEPT
       - Single metric threshold exceeded -> SUSPICIOUS
       - Multiple metric thresholds exceeded -> SUSPICIOUS
       - Explicit protocol/security violation -> ATTACK
    2. Precedence Hierarchy:
       - Explicit violation takes precedence over clean quantum metrics -> ATTACK
       - Explicit violation takes precedence over anomalous quantum metrics -> ATTACK
       - Anomaly takes precedence over clean state -> SUSPICIOUS (Anomaly != Attack)
       - Incompatible configuration prevents acceptance -> SUSPICIOUS
    3. Missing & Indeterminate Evidence:
       - Missing threshold evaluation -> SUSPICIOUS
       - Incomplete protocol evidence -> SUSPICIOUS
       - Incomplete metric evaluations (0 metrics) -> SUSPICIOUS
       - Missing required metrics -> SUSPICIOUS
       - Type validation errors raise TypeError / ValueError (never silently coerced)
    4. Evidence Preservation & Determinism:
       - Exceeded metric names preserved in deterministic sorted order
       - Reason codes deduplicated and sorted deterministically
       - Identical input evidence produces identical decision across repeated executions
       - JSON-serializable dictionary output
    5. No Composite Security Score:
       - Strict absence of security_score, trust_score, risk_score, or weighted metrics
    6. Immutability:
       - DecisionResult and ProtocolSecurityEvidence are frozen dataclasses
       - Inputs are never mutated during evaluation
    7. Full End-to-End Pipeline Integration:
       - M9 Honest Baseline -> M10 Comparison -> M11 Threshold Policy -> M12 Decision
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
import math
from typing import Any
import pytest

from src.detection.decision import (
    DecisionReasonCode,
    DecisionResult,
    DecisionVerdict,
    ProtocolSecurityEvidence,
    evaluate_decision_from_evidence,
    evaluate_security_decision,
)
from src.noise.models import create_depolarizing_channel
from src.statistics import (
    BaselineConfiguration,
    CalibrationObservation,
    HonestBaseline,
    MetricThreshold,
    MetricThresholdEvaluation,
    PolicyEvaluationReport,
    ThresholdDirection,
    ThresholdMethod,
    ThresholdPolicy,
    VerificationObservation,
    calibrate_honest_baseline,
    calibrate_threshold_policy,
    run_honest_calibration_trial,
)


# ==============================================================================
# Fixtures
# ==============================================================================

@pytest.fixture
def sample_baseline_config() -> BaselineConfiguration:
    return BaselineConfiguration(
        configuration_id="m12_test_config",
        states=("0", "1"),
        noise_model_type="depolarizing",
        noise_strength=0.03,
        channel_location="bob_qubit",
        shots=None,
        calibration_runs=5,
    )


@pytest.fixture
def sample_honest_baseline(sample_baseline_config: BaselineConfiguration) -> HonestBaseline:
    return calibrate_honest_baseline(sample_baseline_config)


@pytest.fixture
def sample_threshold_policy(
    sample_honest_baseline: HonestBaseline,
) -> ThresholdPolicy:
    """Creates an M11 ThresholdPolicy from honest calibration trials."""
    noise = create_depolarizing_channel(0.03)
    obs_list = [
        run_honest_calibration_trial("0", noise_channel=noise, seed=100 + i)
        for i in range(5)
    ]
    return calibrate_threshold_policy(sample_honest_baseline, obs_list, alpha=0.05)


@pytest.fixture
def clean_threshold_report(sample_threshold_policy: ThresholdPolicy) -> PolicyEvaluationReport:
    """Mock/Synthetic M11 PolicyEvaluationReport where NO thresholds are exceeded."""
    eval_fid = MetricThresholdEvaluation(
        metric_name="fidelity:0",
        observed_value=0.98,
        threshold_value=0.95,
        direction=ThresholdDirection.LOWER,
        exceeded=False,
        margin=-0.03,
        signed_distance=0.03,
        method=ThresholdMethod.EMPIRICAL_QUANTILE,
        boundary_status="strictly_inside",
    )
    eval_qber = MetricThresholdEvaluation(
        metric_name="qber:0",
        observed_value=0.02,
        threshold_value=0.05,
        direction=ThresholdDirection.UPPER,
        exceeded=False,
        margin=-0.03,
        signed_distance=-0.03,
        method=ThresholdMethod.EMPIRICAL_QUANTILE,
        boundary_status="strictly_inside",
    )
    return PolicyEvaluationReport(
        policy_id=sample_threshold_policy.policy_id,
        baseline_configuration_hash=sample_threshold_policy.baseline_configuration_hash,
        metric_evaluations={"fidelity:0": eval_fid, "qber:0": eval_qber},
        any_exceeded=False,
        all_exceeded=False,
        exceeded_metrics=(),
        exceeded_count=0,
        total_metrics_evaluated=2,
        timestamp="2026-09-06T10:00:00Z",
    )


@pytest.fixture
def anomalous_threshold_report(sample_threshold_policy: ThresholdPolicy) -> PolicyEvaluationReport:
    """Mock/Synthetic M11 PolicyEvaluationReport where fidelity threshold IS exceeded."""
    eval_fid = MetricThresholdEvaluation(
        metric_name="fidelity:0",
        observed_value=0.89,
        threshold_value=0.95,
        direction=ThresholdDirection.LOWER,
        exceeded=True,
        margin=0.06,
        signed_distance=-0.06,
        method=ThresholdMethod.EMPIRICAL_QUANTILE,
        boundary_status="strictly_exceeded",
    )
    eval_qber = MetricThresholdEvaluation(
        metric_name="qber:0",
        observed_value=0.02,
        threshold_value=0.05,
        direction=ThresholdDirection.UPPER,
        exceeded=False,
        margin=-0.03,
        signed_distance=-0.03,
        method=ThresholdMethod.EMPIRICAL_QUANTILE,
        boundary_status="strictly_inside",
    )
    return PolicyEvaluationReport(
        policy_id=sample_threshold_policy.policy_id,
        baseline_configuration_hash=sample_threshold_policy.baseline_configuration_hash,
        metric_evaluations={"fidelity:0": eval_fid, "qber:0": eval_qber},
        any_exceeded=True,
        all_exceeded=False,
        exceeded_metrics=("fidelity:0",),
        exceeded_count=1,
        total_metrics_evaluated=2,
        timestamp="2026-09-06T10:00:00Z",
    )


# ==============================================================================
# 1. Basic Security Decisions
# ==============================================================================

class TestBasicDecisions:
    """Verifies fundamental decision generation across ACCEPT, SUSPICIOUS, and ATTACK."""

    def test_clean_honest_evidence_produces_accept(
        self, clean_threshold_report: PolicyEvaluationReport
    ) -> None:
        """When all metrics are within policy and no protocol violations exist -> ACCEPT."""
        res = evaluate_security_decision(
            threshold_report=clean_threshold_report,
            protocol_evidence=ProtocolSecurityEvidence(explicit_violation=False, is_complete=True),
        )
        assert res.verdict == DecisionVerdict.ACCEPT
        assert res.primary_reason == DecisionReasonCode.ALL_EVIDENCE_WITHIN_POLICY.value
        assert DecisionReasonCode.ALL_EVIDENCE_WITHIN_POLICY.value in res.reason_codes
        assert res.exceeded_count == 0
        assert res.is_explicit_violation is False
        assert res.is_evidence_complete is True

    def test_single_threshold_exceeded_produces_suspicious(
        self, anomalous_threshold_report: PolicyEvaluationReport
    ) -> None:
        """When a quantum metric threshold is exceeded without confirmed violation -> SUSPICIOUS.

        CRITICAL SCIENTIFIC RULE: Anomaly != Attack.
        """
        res = evaluate_security_decision(
            threshold_report=anomalous_threshold_report,
            protocol_evidence=ProtocolSecurityEvidence(explicit_violation=False, is_complete=True),
        )
        assert res.verdict == DecisionVerdict.SUSPICIOUS
        assert res.verdict != DecisionVerdict.ATTACK
        assert res.primary_reason == DecisionReasonCode.QUANTUM_METRIC_THRESHOLD_EXCEEDED.value
        assert "fidelity:0" in res.exceeded_metrics
        assert res.exceeded_count == 1
        assert res.is_explicit_violation is False

    def test_multiple_thresholds_exceeded_produces_suspicious(
        self, sample_threshold_policy: ThresholdPolicy
    ) -> None:
        """When multiple metrics are exceeded -> SUSPICIOUS with all exceeded metrics preserved."""
        eval_fid = MetricThresholdEvaluation(
            metric_name="fidelity:0",
            observed_value=0.88,
            threshold_value=0.95,
            direction=ThresholdDirection.LOWER,
            exceeded=True,
            margin=0.07,
            signed_distance=-0.07,
            method=ThresholdMethod.EMPIRICAL_QUANTILE,
            boundary_status="strictly_exceeded",
        )
        eval_qber = MetricThresholdEvaluation(
            metric_name="qber:0",
            observed_value=0.10,
            threshold_value=0.05,
            direction=ThresholdDirection.UPPER,
            exceeded=True,
            margin=0.05,
            signed_distance=0.05,
            method=ThresholdMethod.EMPIRICAL_QUANTILE,
            boundary_status="strictly_exceeded",
        )
        report = PolicyEvaluationReport(
            policy_id=sample_threshold_policy.policy_id,
            baseline_configuration_hash=sample_threshold_policy.baseline_configuration_hash,
            metric_evaluations={"fidelity:0": eval_fid, "qber:0": eval_qber},
            any_exceeded=True,
            all_exceeded=True,
            exceeded_metrics=("fidelity:0", "qber:0"),
            exceeded_count=2,
            total_metrics_evaluated=2,
            timestamp="2026-09-06T10:00:00Z",
        )
        res = evaluate_security_decision(threshold_report=report)
        assert res.verdict == DecisionVerdict.SUSPICIOUS
        assert res.exceeded_count == 2
        assert "fidelity:0" in res.exceeded_metrics
        assert "qber:0" in res.exceeded_metrics

    def test_explicit_security_violation_produces_attack(
        self, clean_threshold_report: PolicyEvaluationReport
    ) -> None:
        """An explicit confirmed protocol/security violation fixture produces ATTACK."""
        proto_attack = ProtocolSecurityEvidence(
            explicit_violation=True,
            violation_type="REPLAY_NONCE_REUSED",
            violation_details={"reused_nonce": "nonce_xyz123"},
            is_complete=True,
        )
        res = evaluate_security_decision(
            threshold_report=clean_threshold_report,
            protocol_evidence=proto_attack,
        )
        assert res.verdict == DecisionVerdict.ATTACK
        assert res.primary_reason == DecisionReasonCode.EXPLICIT_SECURITY_VIOLATION.value
        assert "REPLAY_NONCE_REUSED" in res.reason_codes
        assert res.is_explicit_violation is True


# ==============================================================================
# 2. Precedence Hierarchy Tests
# ==============================================================================

class TestPrecedenceHierarchy:
    """Verifies deterministic rule precedence under competing/contradictory evidence."""

    def test_explicit_violation_precedence_over_clean_metrics(
        self, clean_threshold_report: PolicyEvaluationReport
    ) -> None:
        """Even if all quantum metrics are clean (normal transmission), an explicit violation -> ATTACK."""
        proto_violation = ProtocolSecurityEvidence(
            explicit_violation=True,
            violation_type="EXPLICIT_PROTOCOL_VIOLATION",
        )
        res = evaluate_security_decision(
            threshold_report=clean_threshold_report,
            protocol_evidence=proto_violation,
        )
        assert res.verdict == DecisionVerdict.ATTACK
        assert res.is_explicit_violation is True

    def test_explicit_violation_precedence_over_anomalous_metrics(
        self, anomalous_threshold_report: PolicyEvaluationReport
    ) -> None:
        """When BOTH an explicit violation exists AND a threshold is exceeded -> ATTACK (violation wins)."""
        proto_violation = ProtocolSecurityEvidence(
            explicit_violation=True,
            violation_type="FORGERY_STATE_MISMATCH",
        )
        res = evaluate_security_decision(
            threshold_report=anomalous_threshold_report,
            protocol_evidence=proto_violation,
        )
        assert res.verdict == DecisionVerdict.ATTACK
        assert res.primary_reason == DecisionReasonCode.EXPLICIT_SECURITY_VIOLATION.value
        # Exceeded quantum metric is also preserved in reasons
        assert DecisionReasonCode.QUANTUM_METRIC_THRESHOLD_EXCEEDED.value in res.reason_codes
        assert "fidelity:0" in res.exceeded_metrics

    def test_anomaly_precedence_over_accept(
        self, anomalous_threshold_report: PolicyEvaluationReport
    ) -> None:
        """Threshold exceedance without violation NEVER produces ACCEPT; must produce SUSPICIOUS."""
        res = evaluate_security_decision(
            threshold_report=anomalous_threshold_report,
            protocol_evidence=ProtocolSecurityEvidence(explicit_violation=False, is_complete=True),
        )
        assert res.verdict != DecisionVerdict.ACCEPT
        assert res.verdict == DecisionVerdict.SUSPICIOUS

    def test_incompatible_configuration_precedence_over_clean_metrics(
        self, clean_threshold_report: PolicyEvaluationReport
    ) -> None:
        """Mismatched configuration hash cannot produce ACCEPT; produces SUSPICIOUS."""
        res = evaluate_security_decision(
            threshold_report=clean_threshold_report,
            expected_configuration_hash="different_canonical_hash_12345",
        )
        assert res.verdict == DecisionVerdict.SUSPICIOUS
        assert res.verdict != DecisionVerdict.ACCEPT
        assert res.primary_reason == DecisionReasonCode.INCOMPATIBLE_CONFIGURATION.value


# ==============================================================================
# 3. Missing & Indeterminate Evidence Handling
# ==============================================================================

class TestMissingAndIndeterminateEvidence:
    """Verifies that incomplete, missing, or malformed evidence cannot produce ACCEPT."""

    def test_missing_threshold_report_produces_suspicious(self) -> None:
        """When threshold_report is None -> SUSPICIOUS (missing required evidence)."""
        res = evaluate_security_decision(threshold_report=None)
        assert res.verdict == DecisionVerdict.SUSPICIOUS
        assert res.primary_reason == DecisionReasonCode.MISSING_THRESHOLD_EVALUATION.value
        assert res.is_evidence_complete is False

    def test_incomplete_protocol_evidence_produces_suspicious(
        self, clean_threshold_report: PolicyEvaluationReport
    ) -> None:
        """When protocol evidence is explicitly incomplete (is_complete=False) -> SUSPICIOUS."""
        proto_incomplete = ProtocolSecurityEvidence(explicit_violation=False, is_complete=False)
        res = evaluate_security_decision(
            threshold_report=clean_threshold_report,
            protocol_evidence=proto_incomplete,
        )
        assert res.verdict == DecisionVerdict.SUSPICIOUS
        assert res.primary_reason == DecisionReasonCode.INCOMPLETE_EVIDENCE.value
        assert res.is_evidence_complete is False

    def test_empty_metrics_report_produces_suspicious(
        self, sample_threshold_policy: ThresholdPolicy
    ) -> None:
        """Report with total_metrics_evaluated == 0 cannot produce ACCEPT -> SUSPICIOUS."""
        empty_report = PolicyEvaluationReport(
            policy_id=sample_threshold_policy.policy_id,
            baseline_configuration_hash=sample_threshold_policy.baseline_configuration_hash,
            metric_evaluations={},
            any_exceeded=False,
            all_exceeded=False,
            exceeded_metrics=(),
            exceeded_count=0,
            total_metrics_evaluated=0,
            timestamp="2026-09-06T10:00:00Z",
        )
        res = evaluate_security_decision(threshold_report=empty_report)
        assert res.verdict == DecisionVerdict.SUSPICIOUS
        assert res.primary_reason == DecisionReasonCode.INCOMPLETE_EVIDENCE.value

    def test_missing_required_metrics_produces_suspicious(
        self, clean_threshold_report: PolicyEvaluationReport
    ) -> None:
        """When a required metric was not evaluated -> SUSPICIOUS with REQUIRED_METRIC_MISSING."""
        # clean_threshold_report only evaluates fidelity:0 and qber:0
        required = ["fidelity:0", "qber:0", "probabilities_z:0"]
        res = evaluate_security_decision(
            threshold_report=clean_threshold_report,
            required_metrics=required,
        )
        assert res.verdict == DecisionVerdict.SUSPICIOUS
        assert res.primary_reason == DecisionReasonCode.REQUIRED_METRIC_MISSING.value
        assert "probabilities_z:0" in res.metadata["missing_required_metrics"]

    def test_invalid_input_types_raise_type_error(self) -> None:
        """Invalid internal types raise TypeError immediately (data integrity error)."""
        with pytest.raises(TypeError, match="threshold_report"):
            evaluate_security_decision(threshold_report="invalid_string")  # type: ignore

        with pytest.raises(TypeError, match="protocol_evidence"):
            evaluate_security_decision(protocol_evidence=12345)  # type: ignore

        with pytest.raises(TypeError, match="required_metrics"):
            evaluate_security_decision(required_metrics="string_not_sequence")  # type: ignore

        with pytest.raises(TypeError, match="expected_configuration_hash"):
            evaluate_security_decision(expected_configuration_hash=999)  # type: ignore


# ==============================================================================
# 4. Evidence Preservation & Determinism
# ==============================================================================

class TestEvidencePreservationAndDeterminism:
    """Verifies deterministic sorting, deduplication, and repeatability."""

    def test_exceeded_metrics_preserved_and_sorted(
        self, sample_threshold_policy: ThresholdPolicy
    ) -> None:
        """Exceeded metrics are returned as a deterministic, sorted tuple."""
        evals = {}
        for m_name in ("qber:0", "bell_zz", "fidelity:0", "probabilities_z:0"):
            evals[m_name] = MetricThresholdEvaluation(
                metric_name=m_name,
                observed_value=0.5,
                threshold_value=0.1,
                direction=ThresholdDirection.UPPER,
                exceeded=True,
                margin=0.4,
                signed_distance=0.4,
                method=ThresholdMethod.FIXED_BOUND,
                boundary_status="strictly_exceeded",
            )
        report = PolicyEvaluationReport(
            policy_id=sample_threshold_policy.policy_id,
            baseline_configuration_hash=sample_threshold_policy.baseline_configuration_hash,
            metric_evaluations=evals,
            any_exceeded=True,
            all_exceeded=True,
            exceeded_metrics=tuple(evals.keys()),
            exceeded_count=len(evals),
            total_metrics_evaluated=len(evals),
            timestamp="2026-09-06T10:00:00Z",
        )
        res = evaluate_security_decision(threshold_report=report)
        assert res.exceeded_metrics == ("bell_zz", "fidelity:0", "probabilities_z:0", "qber:0")

    def test_decision_determinism_across_repeated_runs(
        self, anomalous_threshold_report: PolicyEvaluationReport
    ) -> None:
        """Identical evidence produces identical decision across 50 repeated evaluations."""
        first_res = evaluate_security_decision(threshold_report=anomalous_threshold_report)
        for _ in range(50):
            subsequent_res = evaluate_security_decision(threshold_report=anomalous_threshold_report)
            assert subsequent_res.verdict == first_res.verdict
            assert subsequent_res.primary_reason == first_res.primary_reason
            assert subsequent_res.reason_codes == first_res.reason_codes
            assert subsequent_res.exceeded_metrics == first_res.exceeded_metrics
            assert subsequent_res.is_explicit_violation == first_res.is_explicit_violation
            assert subsequent_res.is_evidence_complete == first_res.is_evidence_complete

    def test_decision_result_to_dict_serialization(
        self, clean_threshold_report: PolicyEvaluationReport
    ) -> None:
        """DecisionResult serializes to a clean JSON-serializable dictionary."""
        res = evaluate_security_decision(
            threshold_report=clean_threshold_report,
            protocol_evidence=ProtocolSecurityEvidence(explicit_violation=False),
        )
        d = res.to_dict()
        assert d["verdict"] == "ACCEPT"
        assert d["primary_reason"] == "ALL_EVIDENCE_WITHIN_POLICY"
        assert isinstance(d["reason_codes"], list)
        assert isinstance(d["exceeded_metrics"], list)
        assert d["is_explicit_violation"] is False
        assert d["is_evidence_complete"] is True
        assert d["threshold_report"] is not None


# ==============================================================================
# 5. Strict Prohibition of Arbitrary Security Scores
# ==============================================================================

class TestNoCompositeSecurityScore:
    """Verifies that M12 strictly contains no composite score, trust score, or risk score."""

    def test_absence_of_security_score_attributes(
        self, clean_threshold_report: PolicyEvaluationReport
    ) -> None:
        """DecisionResult strictly does NOT contain arbitrary score fields."""
        res = evaluate_security_decision(threshold_report=clean_threshold_report)
        assert not hasattr(res, "security_score")
        assert not hasattr(res, "trust_score")
        assert not hasattr(res, "risk_score")
        assert not hasattr(res, "threat_score")
        assert not hasattr(res, "weighted_score")
        assert not hasattr(res, "quantum_score")

    def test_dictionary_serialization_contains_no_score(
        self, clean_threshold_report: PolicyEvaluationReport
    ) -> None:
        """Serialized dictionary does not contain composite scores."""
        res = evaluate_security_decision(threshold_report=clean_threshold_report)
        serialized = str(res.to_dict()).lower()
        assert "score" not in serialized


# ==============================================================================
# 6. Immutability & Separation Tests
# ==============================================================================

class TestImmutabilityAndSeparation:
    """Verifies dataclass immutability and preservation of policy state."""

    def test_decision_result_frozen(
        self, clean_threshold_report: PolicyEvaluationReport
    ) -> None:
        """DecisionResult instances cannot be mutated."""
        res = evaluate_security_decision(threshold_report=clean_threshold_report)
        with pytest.raises(FrozenInstanceError):
            res.verdict = DecisionVerdict.ATTACK  # type: ignore

        with pytest.raises(FrozenInstanceError):
            res.primary_reason = "tampered"  # type: ignore

    def test_protocol_security_evidence_frozen(self) -> None:
        """ProtocolSecurityEvidence instances cannot be mutated."""
        proto = ProtocolSecurityEvidence(explicit_violation=False)
        with pytest.raises(FrozenInstanceError):
            proto.explicit_violation = True  # type: ignore

    def test_policy_unmutated_by_decision_engine(
        self, sample_threshold_policy: ThresholdPolicy
    ) -> None:
        """Evaluating decisions never modifies the M11 ThresholdPolicy or fingerprint."""
        orig_fp = sample_threshold_policy.policy_fingerprint
        orig_val = sample_threshold_policy.thresholds["fidelity:0"].threshold_value

        # Run several decision evaluations
        eval_obs = VerificationObservation(
            state_name="0",
            fidelity=0.50,  # anomalous
            qber=0.30,
            probabilities_z={"0": 0.5, "1": 0.5},
            probabilities_x={"+": 0.5, "-": 0.5},
            probabilities_y={"+i": 0.5, "-i": 0.5},
            pauli_expectations={"X": 0.0, "Y": 0.0, "Z": 0.0},
        )
        for _ in range(5):
            evaluate_decision_from_evidence(eval_obs, sample_threshold_policy, strict_hash=False)

        assert sample_threshold_policy.policy_fingerprint == orig_fp
        assert sample_threshold_policy.thresholds["fidelity:0"].threshold_value == orig_val


# ==============================================================================
# 7. Full Quantum End-to-End Pipeline Integration (M9 -> M10 -> M11 -> M12)
# ==============================================================================

class TestEndToEndPipelineIntegration:
    """Demonstrates complete flow from M9 baseline through M10, M11, to M12 verdicts."""

    def test_case_a_honest_pipeline_produces_accept(
        self,
        sample_honest_baseline: HonestBaseline,
        sample_threshold_policy: ThresholdPolicy,
        sample_baseline_config: BaselineConfiguration,
    ) -> None:
        """Case A: Honest execution under calibrated noise -> ACCEPT."""
        noise = create_depolarizing_channel(0.03)
        honest_trial = run_honest_calibration_trial("0", noise_channel=noise, seed=9001)
        obs_honest = VerificationObservation.from_calibration_observation(
            honest_trial, configuration=sample_baseline_config
        )

        decision = evaluate_decision_from_evidence(
            evidence_or_obs=obs_honest,
            policy=sample_threshold_policy,
            strict_hash=True,
        )
        assert decision.verdict == DecisionVerdict.ACCEPT
        assert decision.primary_reason == DecisionReasonCode.ALL_EVIDENCE_WITHIN_POLICY.value
        assert decision.exceeded_count == 0

    def test_case_b_quantum_anomaly_produces_suspicious(
        self,
        sample_honest_baseline: HonestBaseline,
        sample_threshold_policy: ThresholdPolicy,
        sample_baseline_config: BaselineConfiguration,
    ) -> None:
        """Case B: Severe quantum channel disruption (p=0.45) -> SUSPICIOUS (not ATTACK)."""
        noise_disrupted = create_depolarizing_channel(0.45)
        disrupted_trial = run_honest_calibration_trial("0", noise_channel=noise_disrupted, seed=9002)
        obs_disrupted = VerificationObservation.from_calibration_observation(
            disrupted_trial, configuration=sample_baseline_config
        )

        decision = evaluate_decision_from_evidence(
            evidence_or_obs=obs_disrupted,
            policy=sample_threshold_policy,
            strict_hash=True,
        )
        assert decision.verdict == DecisionVerdict.SUSPICIOUS
        assert decision.verdict != DecisionVerdict.ATTACK
        assert decision.primary_reason == DecisionReasonCode.QUANTUM_METRIC_THRESHOLD_EXCEEDED.value
        assert decision.exceeded_count > 0

    def test_case_c_explicit_violation_fixture_produces_attack(
        self,
        sample_threshold_policy: ThresholdPolicy,
        sample_baseline_config: BaselineConfiguration,
    ) -> None:
        """Case C: Explicit protocol violation fixture -> ATTACK."""
        noise = create_depolarizing_channel(0.03)
        trial = run_honest_calibration_trial("0", noise_channel=noise, seed=9003)
        obs = VerificationObservation.from_calibration_observation(trial, configuration=sample_baseline_config)

        proto_violation = ProtocolSecurityEvidence(
            explicit_violation=True,
            violation_type="REPLAY_ATTACK_CONFIRMED",
        )
        decision = evaluate_decision_from_evidence(
            evidence_or_obs=obs,
            policy=sample_threshold_policy,
            protocol_evidence=proto_violation,
            strict_hash=True,
        )
        assert decision.verdict == DecisionVerdict.ATTACK
        assert decision.primary_reason == DecisionReasonCode.EXPLICIT_SECURITY_VIOLATION.value
        assert "REPLAY_ATTACK_CONFIRMED" in decision.reason_codes
        assert decision.is_explicit_violation is True

    def test_case_d_incompatible_configuration_produces_suspicious(
        self,
        sample_threshold_policy: ThresholdPolicy,
    ) -> None:
        """Case D: Incompatible configuration cannot produce ACCEPT -> SUSPICIOUS."""
        bad_cfg = BaselineConfiguration(
            configuration_id="incompatible_cfg",
            states=("0",),
            noise_model_type="phase_flip",
            noise_strength=0.03,
            channel_location="bob_qubit",
            shots=None,
            calibration_runs=5,
        )
        obs_bad_cfg = VerificationObservation(
            state_name="0",
            fidelity=0.99,  # high fidelity
            qber=0.01,
            probabilities_z={"0": 0.99, "1": 0.01},
            probabilities_x={"+": 0.5, "-": 0.5},
            probabilities_y={"+i": 0.5, "-i": 0.5},
            pauli_expectations={"X": 0.0, "Y": 0.0, "Z": 0.98},
            configuration=bad_cfg,
        )
        decision = evaluate_decision_from_evidence(
            evidence_or_obs=obs_bad_cfg,
            policy=sample_threshold_policy,
            strict_hash=True,
        )
        assert decision.verdict == DecisionVerdict.SUSPICIOUS
        assert decision.verdict != DecisionVerdict.ACCEPT
        assert decision.is_evidence_complete is False

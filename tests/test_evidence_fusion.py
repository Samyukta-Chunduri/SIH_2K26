"""Tests for Milestone M16: Deterministic Evidence Fusion.

Covers:
    - Clean baseline multi-source fusion (M16 CLEAN -> M12 ACCEPT)
    - Single-source and multi-source statistical anomalies (M16 ANOMALOUS -> M12 SUSPICIOUS)
    - Multiple simultaneous anomalies without composite risk scoring
    - Explicit security violations from M13, M14, and M15 (M16 SECURITY_VIOLATION -> M12 ATTACK)
    - Multiple simultaneous explicit violations preserved without truncation
    - Missing required sources and incomplete evidence (M16 INCOMPLETE -> M12 SUSPICIOUS)
    - Context binding, session agreement, and configuration hash validation
    - Cross-source session and configuration conflicts (M16 CONFLICTING -> M12 SUSPICIOUS)
    - Lower-layer conflict preservation
    - Deep immutability and isolation from post-fusion mutation
    - Determinism across repeated evaluations
    - Defensive secret leakage prevention across nested mappings and lists
    - Absence of scalar risk, trust, or weighted scores
    - Type and input validation on all public APIs
    - Complete M12 Decision Boundary Table verification
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import Any
import pytest

from src.detection.authorization import (
    AuthorizationEvidence,
    AuthorizationReasonCode,
    AuthorizationRequest,
    AuthorizationStatus,
    VerificationOperation,
    VerificationPolicy,
    evaluate_verification_authorization,
)
from src.detection.channel import (
    ChannelEvidenceStatus,
    ChannelReasonCode,
    ChannelSecurityEvidence,
    detect_channel_anomalies,
)
from src.detection.decision import (
    DecisionReasonCode,
    DecisionVerdict,
    ProtocolSecurityEvidence,
    evaluate_security_decision,
)
from src.detection.fusion import (
    EvidenceSource,
    FusedEvidenceStatus,
    FusedSecurityEvidence,
    FusionReasonCode,
    evaluate_fused_security_decision,
    fuse_security_evidence,
)
from src.detection.impersonation import (
    AuthenticationEvidence,
    IdentityClaim,
    IdentityEvidenceStatus,
    ImpersonationEvidence,
    ImpersonationReasonCode,
    detect_impersonation,
)
from src.statistics.thresholds import (
    MetricThresholdEvaluation,
    PolicyEvaluationReport,
    ThresholdDirection,
    ThresholdMethod,
)


# ==============================================================================
# Helper Factories
# ==============================================================================

def _make_metric_eval(
    metric_name: str,
    observed: float,
    threshold: float,
    direction: ThresholdDirection = ThresholdDirection.UPPER,
    exceeded: bool = False,
) -> MetricThresholdEvaluation:
    margin = (observed - threshold) if direction == ThresholdDirection.UPPER else (threshold - observed)
    return MetricThresholdEvaluation(
        metric_name=metric_name,
        observed_value=observed,
        threshold_value=threshold,
        direction=direction,
        exceeded=exceeded,
        margin=margin,
        signed_distance=observed - threshold,
        method=ThresholdMethod.FIXED_BOUND,
        boundary_status="strictly_exceeded" if exceeded else "strictly_inside",
    )


def _make_clean_threshold_report(
    session_id: str = "sess_clean",
    config_hash: str = "a" * 64,
) -> PolicyEvaluationReport:
    evals = {
        "qber:0": _make_metric_eval("qber:0", 0.01, 0.05, ThresholdDirection.UPPER, exceeded=False),
        "fidelity:0": _make_metric_eval("fidelity:0", 0.98, 0.90, ThresholdDirection.LOWER, exceeded=False),
    }
    return PolicyEvaluationReport(
        policy_id="policy_clean",
        baseline_configuration_hash=config_hash,
        metric_evaluations=evals,
        any_exceeded=False,
        all_exceeded=False,
        exceeded_metrics=(),
        exceeded_count=0,
        total_metrics_evaluated=2,
        timestamp="2026-09-06T12:00:00Z",
        metadata={"session_id": session_id},
    )


def _make_clean_impersonation_evidence(
    session_id: str = "sess_clean",
    config_hash: str = "a" * 64,
) -> ImpersonationEvidence:
    claim = IdentityClaim(
        claimed_identity="Alice",
        expected_identity="Alice",
        session_id=session_id,
        configuration_hash=config_hash,
    )
    auth = AuthenticationEvidence(
        authenticated_identity="Alice",
        is_authenticated=True,
        is_complete=True,
        session_id=session_id,
    )
    return detect_impersonation(
        claim=claim,
        auth_evidence=auth,
        expected_configuration_hash=config_hash,
    )


def _make_clean_authorization_evidence(
    session_id: str = "sess_clean",
    config_hash: str = "a" * 64,
) -> AuthorizationEvidence:
    policy = VerificationPolicy(
        policy_id="policy_001",
        allowed_identities=("Alice",),
        allowed_operations=(VerificationOperation.VERIFY.value,),
        allowed_roles=("verifier",),
        configuration_hash=config_hash,
    )
    req = AuthorizationRequest(
        participant_identity="Alice",
        operation=VerificationOperation.VERIFY.value,
        role="verifier",
        session_id=session_id,
        configuration_hash=config_hash,
    )
    return evaluate_verification_authorization(
        request=req,
        policy=policy,
        expected_session_id=session_id,
        expected_configuration_hash=config_hash,
    )


def _make_clean_channel_evidence(
    session_id: str = "sess_clean",
    config_hash: str = "a" * 64,
) -> ChannelSecurityEvidence:
    report = _make_clean_threshold_report(session_id=session_id, config_hash=config_hash)
    return detect_channel_anomalies(
        threshold_report=report,
        session_id=session_id,
        expected_session_id=session_id,
        expected_configuration_hash=config_hash,
    )


# ==============================================================================
# 1. Clean Baseline Fusion Suite
# ==============================================================================

class TestCleanBaselineFusion:
    """Verify clean multi-source fusion yields CLEAN and M12 ACCEPT."""

    def test_all_sources_clean(self):
        m13 = _make_clean_impersonation_evidence()
        m14 = _make_clean_authorization_evidence()
        m15 = _make_clean_channel_evidence()

        fused = fuse_security_evidence(
            impersonation_evidence=m13,
            authorization_evidence=m14,
            channel_evidence=m15,
            expected_session_id="sess_clean",
            expected_configuration_hash="a" * 64,
        )

        assert fused.status == FusedEvidenceStatus.CLEAN
        assert fused.is_clean is True
        assert fused.is_anomalous is False
        assert fused.is_explicit_violation is False
        assert fused.is_complete is True
        assert fused.primary_reason == FusionReasonCode.ALL_SOURCES_CLEAN.value
        assert len(fused.violations) == 0
        assert fused.session_id == "sess_clean"
        assert fused.configuration_hash == "a" * 64
        assert len(fused.present_sources) == 3
        assert len(fused.missing_sources) == 0

        # Verify M12 bridge
        proto = fused.to_protocol_security_evidence()
        assert proto.explicit_violation is False
        assert proto.is_complete is True

        rep = _make_clean_threshold_report()
        decision = evaluate_security_decision(threshold_report=rep, protocol_evidence=proto)
        assert decision.verdict == DecisionVerdict.ACCEPT

    def test_clean_fusion_via_adapter(self):
        m13 = _make_clean_impersonation_evidence()
        m14 = _make_clean_authorization_evidence()
        m15 = _make_clean_channel_evidence()

        res = evaluate_fused_security_decision(
            impersonation_evidence=m13,
            authorization_evidence=m14,
            channel_evidence=m15,
            expected_session_id="sess_clean",
            expected_configuration_hash="a" * 64,
        )
        assert res.verdict == DecisionVerdict.ACCEPT


# ==============================================================================
# 2. Statistical Anomaly Fusion Suite
# ==============================================================================

class TestAnomalyFusion:
    """Verify channel or statistical anomalies evaluate to ANOMALOUS and M12 SUSPICIOUS (never ATTACK)."""

    def test_single_channel_qber_anomaly(self):
        m13 = _make_clean_impersonation_evidence()
        m14 = _make_clean_authorization_evidence()

        # M15 anomalous QBER
        evals = {
            "qber:0": _make_metric_eval("qber:0", 0.08, 0.05, ThresholdDirection.UPPER, exceeded=True),
            "fidelity:0": _make_metric_eval("fidelity:0", 0.98, 0.90, ThresholdDirection.LOWER, exceeded=False),
        }
        rep = PolicyEvaluationReport(
            policy_id="policy_anom",
            baseline_configuration_hash="a" * 64,
            metric_evaluations=evals,
            any_exceeded=True,
            all_exceeded=False,
            exceeded_metrics=("qber:0",),
            exceeded_count=1,
            total_metrics_evaluated=2,
            timestamp="2026-09-06T12:00:00Z",
            metadata={"session_id": "sess_clean"},
        )
        m15 = detect_channel_anomalies(
            threshold_report=rep,
            session_id="sess_clean",
            expected_session_id="sess_clean",
            expected_configuration_hash="a" * 64,
        )
        assert m15.status == ChannelEvidenceStatus.ANOMALOUS

        fused = fuse_security_evidence(
            impersonation_evidence=m13,
            authorization_evidence=m14,
            channel_evidence=m15,
            expected_session_id="sess_clean",
            expected_configuration_hash="a" * 64,
        )

        assert fused.status == FusedEvidenceStatus.ANOMALOUS
        assert fused.is_clean is False
        assert fused.is_anomalous is True
        assert fused.is_explicit_violation is False
        assert fused.is_complete is True
        assert ChannelReasonCode.QBER_THRESHOLD_EXCEEDED.value in fused.reason_codes

        # M12 integration must be SUSPICIOUS, NEVER ATTACK
        res = evaluate_fused_security_decision(fused_evidence=fused, threshold_report=rep)
        assert res.verdict == DecisionVerdict.SUSPICIOUS
        assert res.verdict != DecisionVerdict.ATTACK

    def test_multi_metric_channel_disturbance_preserved(self):
        m13 = _make_clean_impersonation_evidence()
        m14 = _make_clean_authorization_evidence()

        # Both QBER and fidelity anomalous
        evals = {
            "qber:0": _make_metric_eval("qber:0", 0.08, 0.05, ThresholdDirection.UPPER, exceeded=True),
            "fidelity:0": _make_metric_eval("fidelity:0", 0.75, 0.90, ThresholdDirection.LOWER, exceeded=True),
        }
        rep = PolicyEvaluationReport(
            policy_id="policy_multi_anom",
            baseline_configuration_hash="a" * 64,
            metric_evaluations=evals,
            any_exceeded=True,
            all_exceeded=True,
            exceeded_metrics=("fidelity:0", "qber:0"),
            exceeded_count=2,
            total_metrics_evaluated=2,
            timestamp="2026-09-06T12:00:00Z",
            metadata={"session_id": "sess_clean"},
        )
        m15 = detect_channel_anomalies(
            threshold_report=rep,
            session_id="sess_clean",
            expected_session_id="sess_clean",
            expected_configuration_hash="a" * 64,
        )

        fused = fuse_security_evidence(
            impersonation_evidence=m13,
            authorization_evidence=m14,
            channel_evidence=m15,
        )

        assert fused.status == FusedEvidenceStatus.ANOMALOUS
        assert ChannelReasonCode.MULTI_METRIC_CHANNEL_DISTURBANCE.value in fused.reason_codes
        assert ChannelReasonCode.QBER_THRESHOLD_EXCEEDED.value in fused.reason_codes
        assert ChannelReasonCode.TELEPORTATION_FIDELITY_ANOMALY.value in fused.reason_codes
        assert fused.is_explicit_violation is False


# ==============================================================================
# 3. Explicit Security Violations Suite
# ==============================================================================

class TestExplicitViolationsFusion:
    """Verify explicit security violations from M13, M14, and M15 yield SECURITY_VIOLATION and M12 ATTACK."""

    def test_explicit_impersonation_violation(self):
        # M13 Impersonation: Eve claims to be Alice
        claim = IdentityClaim(claimed_identity="Alice", expected_identity="Alice", session_id="sess_clean")
        auth = AuthenticationEvidence(authenticated_identity="Eve", is_authenticated=True, is_complete=True, session_id="sess_clean")
        m13_violation = detect_impersonation(claim=claim, auth_evidence=auth)
        assert m13_violation.is_impersonation_detected is True

        m14 = _make_clean_authorization_evidence()
        m15 = _make_clean_channel_evidence()

        fused = fuse_security_evidence(
            impersonation_evidence=m13_violation,
            authorization_evidence=m14,
            channel_evidence=m15,
        )

        assert fused.status == FusedEvidenceStatus.SECURITY_VIOLATION
        assert fused.is_explicit_violation is True
        assert ImpersonationReasonCode.AUTHENTICATED_IDENTITY_MISMATCH.value in fused.violations

        res = evaluate_fused_security_decision(fused_evidence=fused)
        assert res.verdict == DecisionVerdict.ATTACK

    def test_explicit_unauthorized_verification_violation(self):
        m13 = _make_clean_impersonation_evidence()
        m15 = _make_clean_channel_evidence()

        # M14 Unauthorized: Bob attempts VERIFY but only Alice is allowed
        policy = VerificationPolicy(
            policy_id="policy_001",
            allowed_identities=("Alice",),
            allowed_operations=(VerificationOperation.VERIFY.value,),
            allowed_roles=("verifier",),
            configuration_hash="a" * 64,
        )
        req = AuthorizationRequest(
            participant_identity="Bob",
            operation=VerificationOperation.VERIFY.value,
            role="verifier",
            session_id="sess_clean",
            configuration_hash="a" * 64,
        )
        m14_unauth = evaluate_verification_authorization(request=req, policy=policy)
        assert m14_unauth.is_unauthorized_detected is True

        fused = fuse_security_evidence(
            impersonation_evidence=m13,
            authorization_evidence=m14_unauth,
            channel_evidence=m15,
        )

        assert fused.status == FusedEvidenceStatus.SECURITY_VIOLATION
        assert fused.is_explicit_violation is True
        assert AuthorizationReasonCode.AUTHORIZATION_DENIED.value in fused.violations

        res = evaluate_fused_security_decision(fused_evidence=fused)
        assert res.verdict == DecisionVerdict.ATTACK

    def test_explicit_quantum_channel_security_violation(self):
        m13 = _make_clean_impersonation_evidence()
        m14 = _make_clean_authorization_evidence()

        # M15 explicit violation
        m15_violation = detect_channel_anomalies(
            explicit_violation=True,
            violation_type="QUANTUM_CHANNEL_SECURITY_VIOLATION",
            session_id="sess_clean",
        )
        assert m15_violation.is_explicit_violation is True

        fused = fuse_security_evidence(
            impersonation_evidence=m13,
            authorization_evidence=m14,
            channel_evidence=m15_violation,
        )

        assert fused.status == FusedEvidenceStatus.SECURITY_VIOLATION
        assert fused.is_explicit_violation is True
        assert "QUANTUM_CHANNEL_SECURITY_VIOLATION" in fused.violations

        res = evaluate_fused_security_decision(fused_evidence=fused)
        assert res.verdict == DecisionVerdict.ATTACK

    def test_multiple_simultaneous_explicit_violations_preserved(self):
        """Verify multiple independent explicit violations are all preserved without truncation."""
        # M13 Impersonation
        claim = IdentityClaim(
            claimed_identity="Alice",
            expected_identity="Alice",
            session_id="sess_clean",
            configuration_hash="a" * 64,
        )
        auth = AuthenticationEvidence(authenticated_identity="Eve", is_authenticated=True, is_complete=True, session_id="sess_clean")
        m13_violation = detect_impersonation(claim=claim, auth_evidence=auth)

        # M14 Unauthorized
        policy = VerificationPolicy(
            policy_id="policy_001",
            allowed_identities=("Alice",),
            allowed_operations=(VerificationOperation.VERIFY.value,),
            allowed_roles=("verifier",),
            configuration_hash="a" * 64,
        )
        req = AuthorizationRequest(
            participant_identity="Mallory",
            operation=VerificationOperation.VERIFY.value,
            role="verifier",
            session_id="sess_clean",
            configuration_hash="a" * 64,
        )
        m14_unauth = evaluate_verification_authorization(request=req, policy=policy)

        # M15 Channel Security Violation
        m15_violation = detect_channel_anomalies(
            explicit_violation=True,
            violation_type="QUANTUM_CHANNEL_SECURITY_VIOLATION",
            session_id="sess_clean",
        )

        fused = fuse_security_evidence(
            impersonation_evidence=m13_violation,
            authorization_evidence=m14_unauth,
            channel_evidence=m15_violation,
        )

        assert fused.status == FusedEvidenceStatus.SECURITY_VIOLATION
        assert fused.is_explicit_violation is True
        assert len(fused.violations) == 3
        assert ImpersonationReasonCode.AUTHENTICATED_IDENTITY_MISMATCH.value in fused.violations
        assert AuthorizationReasonCode.AUTHORIZATION_DENIED.value in fused.violations
        assert "QUANTUM_CHANNEL_SECURITY_VIOLATION" in fused.violations

        res = evaluate_fused_security_decision(fused_evidence=fused)
        assert res.verdict == DecisionVerdict.ATTACK


# ==============================================================================
# 4. Missing Evidence & Incompleteness Suite
# ==============================================================================

class TestMissingEvidenceFusion:
    """Verify missing required sources yield INCOMPLETE and M12 SUSPICIOUS (never ATTACK)."""

    def test_missing_m13_yields_incomplete(self):
        m14 = _make_clean_authorization_evidence()
        m15 = _make_clean_channel_evidence()

        fused = fuse_security_evidence(
            impersonation_evidence=None,
            authorization_evidence=m14,
            channel_evidence=m15,
        )

        assert fused.status == FusedEvidenceStatus.INCOMPLETE
        assert fused.is_clean is False
        assert fused.is_complete is False
        assert EvidenceSource.IMPERSONATION in fused.missing_sources
        assert FusionReasonCode.MISSING_REQUIRED_SOURCE.value in fused.reason_codes

        res = evaluate_fused_security_decision(fused_evidence=fused)
        assert res.verdict == DecisionVerdict.SUSPICIOUS
        assert res.verdict != DecisionVerdict.ATTACK

    def test_missing_m14_yields_incomplete(self):
        m13 = _make_clean_impersonation_evidence()
        m15 = _make_clean_channel_evidence()

        fused = fuse_security_evidence(
            impersonation_evidence=m13,
            authorization_evidence=None,
            channel_evidence=m15,
        )

        assert fused.status == FusedEvidenceStatus.INCOMPLETE
        assert EvidenceSource.AUTHORIZATION in fused.missing_sources

        res = evaluate_fused_security_decision(fused_evidence=fused)
        assert res.verdict == DecisionVerdict.SUSPICIOUS

    def test_missing_m15_yields_incomplete(self):
        m13 = _make_clean_impersonation_evidence()
        m14 = _make_clean_authorization_evidence()

        fused = fuse_security_evidence(
            impersonation_evidence=m13,
            authorization_evidence=m14,
            channel_evidence=None,
        )

        assert fused.status == FusedEvidenceStatus.INCOMPLETE
        assert EvidenceSource.QUANTUM_CHANNEL in fused.missing_sources

        res = evaluate_fused_security_decision(fused_evidence=fused)
        assert res.verdict == DecisionVerdict.SUSPICIOUS

    def test_source_with_incomplete_telemetry_yields_incomplete(self):
        m13 = _make_clean_impersonation_evidence()
        m14 = _make_clean_authorization_evidence()

        # M15 incomplete (missing required metric)
        evals = {"qber:0": _make_metric_eval("qber:0", 0.01, 0.05, exceeded=False)}
        rep = PolicyEvaluationReport(
            policy_id="policy_inc",
            baseline_configuration_hash="a" * 64,
            metric_evaluations=evals,
            any_exceeded=False,
            all_exceeded=False,
            exceeded_metrics=(),
            exceeded_count=0,
            total_metrics_evaluated=1,
            timestamp="2026-09-06T12:00:00Z",
            metadata={"session_id": "sess_clean"},
        )
        m15 = detect_channel_anomalies(
            threshold_report=rep,
            required_metrics=["qber:0", "fidelity:0"],  # fidelity:0 is missing
            session_id="sess_clean",
        )
        assert m15.status == ChannelEvidenceStatus.INCOMPLETE

        fused = fuse_security_evidence(
            impersonation_evidence=m13,
            authorization_evidence=m14,
            channel_evidence=m15,
        )

        assert fused.status == FusedEvidenceStatus.INCOMPLETE
        assert fused.is_complete is False

        res = evaluate_fused_security_decision(fused_evidence=fused)
        assert res.verdict == DecisionVerdict.SUSPICIOUS


# ==============================================================================
# 5. Context Binding & Cross-Source Conflicts Suite
# ==============================================================================

class TestContextBindingAndConflicts:
    """Verify session and configuration hash binding, and cross-source conflict detection."""

    def test_cross_source_session_mismatch_yields_conflicting(self):
        m13 = _make_clean_impersonation_evidence(session_id="session_A")
        m14 = _make_clean_authorization_evidence(session_id="session_A")
        m15 = _make_clean_channel_evidence(session_id="session_B")  # Disagreement!

        fused = fuse_security_evidence(
            impersonation_evidence=m13,
            authorization_evidence=m14,
            channel_evidence=m15,
        )

        assert fused.status == FusedEvidenceStatus.CONFLICTING
        assert FusionReasonCode.SESSION_ID_MISMATCH.value in fused.reason_codes
        assert fused.is_complete is False

        res = evaluate_fused_security_decision(fused_evidence=fused)
        assert res.verdict == DecisionVerdict.SUSPICIOUS
        assert res.verdict != DecisionVerdict.ATTACK

    def test_cross_source_configuration_mismatch_yields_conflicting(self):
        m13 = _make_clean_impersonation_evidence(config_hash="a" * 64)
        m14 = _make_clean_authorization_evidence(config_hash="b" * 64)  # Disagreement!
        m15 = _make_clean_channel_evidence(config_hash="a" * 64)

        fused = fuse_security_evidence(
            impersonation_evidence=m13,
            authorization_evidence=m14,
            channel_evidence=m15,
        )

        assert fused.status == FusedEvidenceStatus.CONFLICTING
        assert FusionReasonCode.CONFIGURATION_HASH_MISMATCH.value in fused.reason_codes

        res = evaluate_fused_security_decision(fused_evidence=fused)
        assert res.verdict == DecisionVerdict.SUSPICIOUS

    def test_expected_session_mismatch_yields_incompatible_context(self):
        m13 = _make_clean_impersonation_evidence(session_id="session_actual")
        m14 = _make_clean_authorization_evidence(session_id="session_actual")
        m15 = _make_clean_channel_evidence(session_id="session_actual")

        fused = fuse_security_evidence(
            impersonation_evidence=m13,
            authorization_evidence=m14,
            channel_evidence=m15,
            expected_session_id="session_expected",  # Mismatch!
        )

        assert fused.status == FusedEvidenceStatus.INCOMPATIBLE_CONTEXT
        assert FusionReasonCode.SESSION_ID_MISMATCH.value in fused.reason_codes

        res = evaluate_fused_security_decision(fused_evidence=fused)
        assert res.verdict == DecisionVerdict.SUSPICIOUS

    def test_lower_layer_conflict_preserved(self):
        # M13 with conflicting identity assertions (and confirmed impersonation detection)
        claim = IdentityClaim(
            claimed_identity="Alice",
            expected_identity="Bob",
            session_id="sess_clean",
            configuration_hash="a" * 64,
        )
        auth = AuthenticationEvidence(authenticated_identity="Charlie", is_authenticated=True, is_complete=True, session_id="sess_clean")
        m13_conflict = detect_impersonation(claim=claim, auth_evidence=auth)
        assert m13_conflict.status == IdentityEvidenceStatus.CONFLICTING
        assert m13_conflict.is_impersonation_detected is True

        m14 = _make_clean_authorization_evidence()
        m15 = _make_clean_channel_evidence()

        fused = fuse_security_evidence(
            impersonation_evidence=m13_conflict,
            authorization_evidence=m14,
            channel_evidence=m15,
        )

        assert fused.status == FusedEvidenceStatus.CONFLICTING
        assert fused.is_explicit_violation is True
        assert ImpersonationReasonCode.AUTHENTICATED_IDENTITY_MISMATCH.value in fused.violations
        assert FusionReasonCode.CONFLICTING_EVIDENCE_PRESENT.value in fused.reason_codes
        assert FusionReasonCode.EXPLICIT_SECURITY_VIOLATION_PRESENT.value in fused.reason_codes

        res = evaluate_fused_security_decision(fused_evidence=fused)
        assert res.verdict == DecisionVerdict.ATTACK
        assert res.is_explicit_violation is True
        assert res.is_evidence_complete is False


# ==============================================================================
# 6. Immutability & Isolation Suite
# ==============================================================================

class TestImmutabilityAndIsolation:
    """Verify deep immutability and isolation from post-fusion mutation."""

    def test_dataclass_frozen_instance_error(self):
        m13 = _make_clean_impersonation_evidence()
        m14 = _make_clean_authorization_evidence()
        m15 = _make_clean_channel_evidence()

        fused = fuse_security_evidence(
            impersonation_evidence=m13,
            authorization_evidence=m14,
            channel_evidence=m15,
        )

        with pytest.raises(FrozenInstanceError):
            fused.status = FusedEvidenceStatus.SECURITY_VIOLATION  # type: ignore

    def test_metadata_mutation_isolation(self):
        nested_meta = {"audit": {"operator": "sec_ops", "tags": ["qkd", "teleportation"]}}
        fused = FusedSecurityEvidence(
            status=FusedEvidenceStatus.CLEAN,
            primary_reason=FusionReasonCode.ALL_SOURCES_CLEAN.value,
            reason_codes=(FusionReasonCode.ALL_SOURCES_CLEAN.value,),
            source_reason_codes={},
            is_clean=True,
            is_anomalous=False,
            is_explicit_violation=False,
            is_complete=True,
            metadata=nested_meta,
        )

        # Mutating external source dict
        nested_meta["audit"]["operator"] = "tampered"
        assert fused.metadata["audit"]["operator"] == "sec_ops"

        # Mutating returned metadata dict
        ret_meta = fused.to_dict()["metadata"]
        ret_meta["audit"]["operator"] = "tampered_again"
        assert fused.metadata["audit"]["operator"] == "sec_ops"


# ==============================================================================
# 7. Determinism Suite
# ==============================================================================

class TestDeterminism:
    """Verify bit-for-bit identical results across repeated evaluations."""

    def test_repeated_fusion_evaluations_identical(self):
        m13 = _make_clean_impersonation_evidence()
        m14 = _make_clean_authorization_evidence()
        m15 = _make_clean_channel_evidence()

        baseline = fuse_security_evidence(
            impersonation_evidence=m13,
            authorization_evidence=m14,
            channel_evidence=m15,
        )

        for _ in range(50):
            repeated = fuse_security_evidence(
                impersonation_evidence=m13,
                authorization_evidence=m14,
                channel_evidence=m15,
            )
            # Full frozen dataclass equality including deterministic timestamp
            assert repeated == baseline
            assert repeated.timestamp == baseline.timestamp
            assert repeated.to_dict() == baseline.to_dict()
            assert repeated.to_protocol_security_evidence() == baseline.to_protocol_security_evidence()

    def test_explicit_caller_timestamp_preserved(self):
        m13 = _make_clean_impersonation_evidence()
        m14 = _make_clean_authorization_evidence()
        m15 = _make_clean_channel_evidence()

        fused = fuse_security_evidence(
            impersonation_evidence=m13,
            authorization_evidence=m14,
            channel_evidence=m15,
            timestamp="2026-09-06T15:30:00Z",
        )
        assert fused.timestamp == "2026-09-06T15:30:00Z"
        assert fused.to_protocol_security_evidence().violation_details["fused_timestamp"] == "2026-09-06T15:30:00Z"

    def test_deterministic_timestamp_derived_from_sources(self):
        m13 = _make_clean_impersonation_evidence()
        m14 = _make_clean_authorization_evidence()
        m15 = _make_clean_channel_evidence()

        # Both m13, m14, m15 have timestamps generated when created
        expected_epoch = max(m13.timestamp, m14.timestamp, m15.timestamp)

        fused = fuse_security_evidence(
            impersonation_evidence=m13,
            authorization_evidence=m14,
            channel_evidence=m15,
        )
        assert fused.timestamp == expected_epoch

    def test_metadata_key_order_independence(self):
        m13 = _make_clean_impersonation_evidence()
        m14 = _make_clean_authorization_evidence()
        m15 = _make_clean_channel_evidence()

        # Different insertion orders for metadata keys
        meta1 = {"z_key": 1, "a_key": 2, "m_key": {"inner_b": 10, "inner_a": 20}}
        meta2 = {"a_key": 2, "z_key": 1, "m_key": {"inner_a": 20, "inner_b": 10}}

        fused1 = fuse_security_evidence(m13, m14, m15, metadata=meta1)
        fused2 = fuse_security_evidence(m13, m14, m15, metadata=meta2)

        assert fused1.metadata == fused2.metadata
        assert fused1 == fused2


# ==============================================================================
# 8. Secret Leakage Prevention Suite
# ==============================================================================

class TestSecretLeakagePrevention:
    """Verify defensive key-name guard rejects secret material in nested metadata."""

    def test_secret_in_nested_dict_rejected(self):
        with pytest.raises(ValueError, match="Sensitive secret keyword 'password'"):
            fuse_security_evidence(
                metadata={"credentials": {"user_password": "super_secret"}}
            )

    def test_secret_in_list_of_dicts_rejected(self):
        with pytest.raises(ValueError, match="Sensitive secret keyword 'api_key'"):
            fuse_security_evidence(
                metadata={"tokens": [{"id": 1}, {"api_key": "raw_token"}]}
            )


# ==============================================================================
# 9. Zero Composite Scores & No ML Suite
# ==============================================================================

class TestZeroCompositeScoresAndNoML:
    """Verify strictly zero scalar scores, trust scores, or attack probabilities exist."""

    def test_no_score_attributes_on_fused_evidence(self):
        m13 = _make_clean_impersonation_evidence()
        m14 = _make_clean_authorization_evidence()
        m15 = _make_clean_channel_evidence()

        fused = fuse_security_evidence(
            impersonation_evidence=m13,
            authorization_evidence=m14,
            channel_evidence=m15,
        )

        prohibited_names = (
            "risk", "risk_score", "trust", "trust_score", "security_score",
            "threat_score", "confidence_score", "attack_probability",
            "score", "probability", "weight", "weights",
        )
        for name in prohibited_names:
            assert not hasattr(fused, name), f"Prohibited attribute '{name}' found on FusedSecurityEvidence!"

        serialized = fused.to_dict()
        for name in prohibited_names:
            assert name not in serialized, f"Prohibited key '{name}' found in serialized evidence!"


# ==============================================================================
# 10. Type and Input Validation Suite
# ==============================================================================

class TestTypeAndInputValidation:
    """Verify robust defensive typing on all public APIs."""

    def test_invalid_source_types(self):
        with pytest.raises(TypeError, match="impersonation_evidence must be ImpersonationEvidence"):
            fuse_security_evidence(impersonation_evidence="invalid")  # type: ignore

        with pytest.raises(TypeError, match="authorization_evidence must be AuthorizationEvidence"):
            fuse_security_evidence(authorization_evidence="invalid")  # type: ignore

        with pytest.raises(TypeError, match="channel_evidence must be ChannelSecurityEvidence"):
            fuse_security_evidence(channel_evidence="invalid")  # type: ignore

    def test_empty_expected_session_id(self):
        with pytest.raises(ValueError, match="expected_session_id cannot be empty or whitespace"):
            fuse_security_evidence(expected_session_id="")

    def test_empty_expected_config_hash(self):
        with pytest.raises(ValueError, match="expected_configuration_hash cannot be empty or whitespace"):
            fuse_security_evidence(expected_configuration_hash="   ")

    def test_invalid_required_sources(self):
        with pytest.raises(TypeError, match="required_sources must be a Sequence"):
            fuse_security_evidence(required_sources="IMPERSONATION")  # type: ignore

        with pytest.raises(ValueError, match="Invalid EvidenceSource in required_sources"):
            fuse_security_evidence(required_sources=["UNKNOWN_MODULE"])


# ==============================================================================
# 11. Explicit M12 Decision Boundary Table Suite
# ==============================================================================

class TestM12BoundaryTable:
    """Verifies the explicit 6-row decision boundary table required by Sections 13 and 20.

    | Fused condition            | M16 result           | M12 result |
    | -------------------------- | -------------------- | ---------- |
    | All sources clean          | CLEAN                | ACCEPT*    |
    | Statistical anomaly        | ANOMALOUS            | SUSPICIOUS |
    | Missing required evidence  | INCOMPLETE           | SUSPICIOUS |
    | Context mismatch           | INCOMPATIBLE_CONTEXT | SUSPICIOUS |
    | Conflicting evidence       | CONFLICTING          | SUSPICIOUS |
    | Explicit security violation| SECURITY_VIOLATION   | ATTACK     |

    * ACCEPT assumes clean M11 threshold report.
    """

    def test_row1_all_clean_produces_clean_and_m12_accept(self):
        m13 = _make_clean_impersonation_evidence()
        m14 = _make_clean_authorization_evidence()
        m15 = _make_clean_channel_evidence()

        fused = fuse_security_evidence(
            impersonation_evidence=m13,
            authorization_evidence=m14,
            channel_evidence=m15,
        )
        assert fused.status == FusedEvidenceStatus.CLEAN

        res = evaluate_fused_security_decision(fused_evidence=fused)
        assert res.verdict == DecisionVerdict.ACCEPT

    def test_row2_statistical_anomaly_produces_anomalous_and_m12_suspicious(self):
        m13 = _make_clean_impersonation_evidence()
        m14 = _make_clean_authorization_evidence()

        evals = {"qber:0": _make_metric_eval("qber:0", 0.08, 0.05, exceeded=True)}
        rep = PolicyEvaluationReport(
            policy_id="p1",
            baseline_configuration_hash="a" * 64,
            metric_evaluations=evals,
            any_exceeded=True,
            all_exceeded=True,
            exceeded_metrics=("qber:0",),
            exceeded_count=1,
            total_metrics_evaluated=1,
            timestamp="2026-09-06T12:00:00Z",
            metadata={"session_id": "sess_clean"},
        )
        m15 = detect_channel_anomalies(threshold_report=rep, session_id="sess_clean")

        fused = fuse_security_evidence(
            impersonation_evidence=m13,
            authorization_evidence=m14,
            channel_evidence=m15,
        )
        assert fused.status == FusedEvidenceStatus.ANOMALOUS

        res = evaluate_fused_security_decision(fused_evidence=fused, threshold_report=rep)
        assert res.verdict == DecisionVerdict.SUSPICIOUS
        assert res.verdict != DecisionVerdict.ATTACK

    def test_row3_missing_evidence_produces_incomplete_and_m12_suspicious(self):
        m13 = _make_clean_impersonation_evidence()
        m15 = _make_clean_channel_evidence()

        fused = fuse_security_evidence(
            impersonation_evidence=m13,
            authorization_evidence=None,  # Missing M14
            channel_evidence=m15,
        )
        assert fused.status == FusedEvidenceStatus.INCOMPLETE

        res = evaluate_fused_security_decision(fused_evidence=fused)
        assert res.verdict == DecisionVerdict.SUSPICIOUS
        assert res.verdict != DecisionVerdict.ATTACK

    def test_row4_context_mismatch_produces_incompatible_context_and_m12_suspicious(self):
        m13 = _make_clean_impersonation_evidence(session_id="sess_actual")
        m14 = _make_clean_authorization_evidence(session_id="sess_actual")
        m15 = _make_clean_channel_evidence(session_id="sess_actual")

        fused = fuse_security_evidence(
            impersonation_evidence=m13,
            authorization_evidence=m14,
            channel_evidence=m15,
            expected_session_id="sess_expected",  # Mismatch
        )
        assert fused.status == FusedEvidenceStatus.INCOMPATIBLE_CONTEXT

        res = evaluate_fused_security_decision(fused_evidence=fused)
        assert res.verdict == DecisionVerdict.SUSPICIOUS
        assert res.verdict != DecisionVerdict.ATTACK

    def test_row5_conflicting_evidence_produces_conflicting_and_m12_suspicious(self):
        m13 = _make_clean_impersonation_evidence(session_id="sess_1")
        m14 = _make_clean_authorization_evidence(session_id="sess_2")  # Direct conflict
        m15 = _make_clean_channel_evidence(session_id="sess_1")

        fused = fuse_security_evidence(
            impersonation_evidence=m13,
            authorization_evidence=m14,
            channel_evidence=m15,
        )
        assert fused.status == FusedEvidenceStatus.CONFLICTING

        res = evaluate_fused_security_decision(fused_evidence=fused)
        assert res.verdict == DecisionVerdict.SUSPICIOUS
        assert res.verdict != DecisionVerdict.ATTACK

    def test_row6_explicit_violation_produces_security_violation_and_m12_attack(self):
        m13 = _make_clean_impersonation_evidence()
        m14 = _make_clean_authorization_evidence()
        m15_violation = detect_channel_anomalies(
            explicit_violation=True,
            violation_type="QUANTUM_CHANNEL_SECURITY_VIOLATION",
            session_id="sess_clean",
        )

        fused = fuse_security_evidence(
            impersonation_evidence=m13,
            authorization_evidence=m14,
            channel_evidence=m15_violation,
        )
        assert fused.status == FusedEvidenceStatus.SECURITY_VIOLATION
        assert fused.is_explicit_violation is True

        res = evaluate_fused_security_decision(fused_evidence=fused)
        assert res.verdict == DecisionVerdict.ATTACK


# ==============================================================================
# 12. Explicit Violation Preservation Under Conflict & Incompleteness Suite
# ==============================================================================

class TestExplicitViolationPreservationUnderConflictAndIncompleteness:
    """Verifies that confirmed explicit violations are never suppressed by conflicts or incompleteness.

    Enforces the core architectural invariant:
        A confirmed explicit security violation must remain explicitly represented across the
        M16 -> M12 boundary, and M12 must evaluate to DecisionVerdict.ATTACK under Precedence 1.
    """

    def test_case1_m13_violation_with_m14_conflict(self):
        # 1. M13 explicit impersonation violation
        claim = IdentityClaim(
            claimed_identity="Alice",
            expected_identity="Alice",
            session_id="sess_clean",
            configuration_hash="a" * 64,
        )
        auth = AuthenticationEvidence(
            authenticated_identity="Charlie",  # Mismatch -> Impersonation!
            is_authenticated=True,
            is_complete=True,
            session_id="sess_clean",
        )
        m13_violation = detect_impersonation(claim=claim, auth_evidence=auth)
        assert m13_violation.is_impersonation_detected is True

        # M14 conflicting evidence (policy has identity simultaneously in allowed and denied)
        policy_conflict = VerificationPolicy(
            policy_id="pol_conflict",
            allowed_identities=("Alice",),
            denied_identities=("Alice",),
            allowed_operations=(VerificationOperation.VERIFY.value,),
            configuration_hash="a" * 64,
        )
        req = AuthorizationRequest(
            participant_identity="Alice",
            operation=VerificationOperation.VERIFY.value,
            role="VERIFIER",
            session_id="sess_clean",
            configuration_hash="a" * 64,
        )
        m14_conflict = evaluate_verification_authorization(request=req, policy=policy_conflict)
        assert m14_conflict.status == AuthorizationStatus.CONFLICTING
        assert m14_conflict.is_unauthorized_detected is False

        # M15 clean
        m15 = _make_clean_channel_evidence()

        # Fuse evidence
        fused = fuse_security_evidence(
            impersonation_evidence=m13_violation,
            authorization_evidence=m14_conflict,
            channel_evidence=m15,
        )

        # 9-point inspection:
        assert fused.status == FusedEvidenceStatus.CONFLICTING
        assert fused.is_explicit_violation is True
        assert len(fused.violations) == 1
        assert ImpersonationReasonCode.AUTHENTICATED_IDENTITY_MISMATCH.value in fused.violations
        assert FusionReasonCode.CONFLICTING_EVIDENCE_PRESENT.value in fused.reason_codes
        assert fused.is_complete is False
        assert FusionReasonCode.EXPLICIT_SECURITY_VIOLATION_PRESENT.value in fused.reason_codes

        proto = fused.to_protocol_security_evidence()
        assert proto.explicit_violation is True
        assert proto.violation_type == ImpersonationReasonCode.AUTHENTICATED_IDENTITY_MISMATCH.value
        assert proto.is_complete is False
        assert proto.violation_details["has_conflict"] is True

        res = evaluate_fused_security_decision(fused_evidence=fused)
        assert res.verdict == DecisionVerdict.ATTACK
        assert res.is_explicit_violation is True
        assert res.is_evidence_complete is False

    def test_case2_m14_violation_with_m13_conflict(self):
        # M13 conflicting identity assertions
        claim = IdentityClaim(
            claimed_identity="Alice",
            expected_identity="Bob",
            session_id="sess_clean",
            configuration_hash="a" * 64,
        )
        auth = AuthenticationEvidence(authenticated_identity="Charlie", is_authenticated=True, session_id="sess_clean")
        m13_conflict = detect_impersonation(claim=claim, auth_evidence=auth)
        assert m13_conflict.status == IdentityEvidenceStatus.CONFLICTING

        # M14 explicit unauthorized-verification violation
        policy = VerificationPolicy(
            policy_id="pol_strict",
            allowed_identities=("Alice",),
            allowed_operations=(VerificationOperation.VERIFY.value,),
            allowed_roles=("verifier",),
            configuration_hash="a" * 64,
        )
        req = AuthorizationRequest(
            participant_identity="Eve",  # Eve not allowed!
            operation=VerificationOperation.VERIFY.value,
            role="verifier",
            session_id="sess_clean",
            configuration_hash="a" * 64,
        )
        m14_violation = evaluate_verification_authorization(request=req, policy=policy)
        assert m14_violation.is_unauthorized_detected is True

        m15 = _make_clean_channel_evidence()

        fused = fuse_security_evidence(
            impersonation_evidence=m13_conflict,
            authorization_evidence=m14_violation,
            channel_evidence=m15,
        )

        # 9-point inspection:
        assert fused.status == FusedEvidenceStatus.CONFLICTING
        assert fused.is_explicit_violation is True
        assert AuthorizationReasonCode.AUTHORIZATION_DENIED.value in fused.violations
        assert len(fused.violations) >= 1
        assert FusionReasonCode.CONFLICTING_EVIDENCE_PRESENT.value in fused.reason_codes
        assert fused.is_complete is False
        assert FusionReasonCode.EXPLICIT_SECURITY_VIOLATION_PRESENT.value in fused.reason_codes

        proto = fused.to_protocol_security_evidence()
        assert proto.explicit_violation is True
        assert AuthorizationReasonCode.AUTHORIZATION_DENIED.value in str(proto.violation_type)
        assert proto.is_complete is False

        res = evaluate_fused_security_decision(fused_evidence=fused)
        assert res.verdict == DecisionVerdict.ATTACK
        assert res.is_explicit_violation is True

    def test_case3_m15_violation_with_m13_conflict(self):
        # M13 conflicting identity assertions
        claim = IdentityClaim(
            claimed_identity="Alice",
            expected_identity="Bob",
            session_id="sess_clean",
            configuration_hash="a" * 64,
        )
        auth = AuthenticationEvidence(authenticated_identity="Charlie", is_authenticated=True, session_id="sess_clean")
        m13_conflict = detect_impersonation(claim=claim, auth_evidence=auth)
        assert m13_conflict.status == IdentityEvidenceStatus.CONFLICTING

        m14 = _make_clean_authorization_evidence()

        # M15 explicit channel security violation
        m15_violation = detect_channel_anomalies(
            explicit_violation=True,
            violation_type="QUANTUM_CHANNEL_SECURITY_VIOLATION",
            session_id="sess_clean",
        )
        assert m15_violation.is_explicit_violation is True

        fused = fuse_security_evidence(
            impersonation_evidence=m13_conflict,
            authorization_evidence=m14,
            channel_evidence=m15_violation,
        )

        # 9-point inspection:
        assert fused.status == FusedEvidenceStatus.CONFLICTING
        assert fused.is_explicit_violation is True
        assert "QUANTUM_CHANNEL_SECURITY_VIOLATION" in fused.violations
        assert FusionReasonCode.CONFLICTING_EVIDENCE_PRESENT.value in fused.reason_codes
        assert fused.is_complete is False

        proto = fused.to_protocol_security_evidence()
        assert proto.explicit_violation is True
        assert "QUANTUM_CHANNEL_SECURITY_VIOLATION" in str(proto.violation_type)
        assert proto.is_complete is False

        res = evaluate_fused_security_decision(fused_evidence=fused)
        assert res.verdict == DecisionVerdict.ATTACK
        assert res.is_explicit_violation is True

    def test_case4_m15_violation_with_m14_conflict(self):
        m13 = _make_clean_impersonation_evidence()

        # M14 conflicting policy
        policy_conflict = VerificationPolicy(
            policy_id="pol_conflict",
            allowed_identities=("Alice",),
            denied_identities=("Alice",),
            allowed_operations=(VerificationOperation.VERIFY.value,),
            configuration_hash="a" * 64,
        )
        req = AuthorizationRequest(
            participant_identity="Alice",
            operation=VerificationOperation.VERIFY.value,
            role="VERIFIER",
            session_id="sess_clean",
            configuration_hash="a" * 64,
        )
        m14_conflict = evaluate_verification_authorization(request=req, policy=policy_conflict)
        assert m14_conflict.status == AuthorizationStatus.CONFLICTING
        assert m14_conflict.is_unauthorized_detected is False

        # M15 explicit violation
        m15_violation = detect_channel_anomalies(
            explicit_violation=True,
            violation_type="QUANTUM_CHANNEL_SECURITY_VIOLATION",
            session_id="sess_clean",
        )

        fused = fuse_security_evidence(
            impersonation_evidence=m13,
            authorization_evidence=m14_conflict,
            channel_evidence=m15_violation,
        )

        # 9-point inspection:
        assert fused.status == FusedEvidenceStatus.CONFLICTING
        assert fused.is_explicit_violation is True
        assert "QUANTUM_CHANNEL_SECURITY_VIOLATION" in fused.violations
        assert len(fused.violations) == 1
        assert FusionReasonCode.CONFLICTING_EVIDENCE_PRESENT.value in fused.reason_codes
        assert fused.is_complete is False

        proto = fused.to_protocol_security_evidence()
        assert proto.explicit_violation is True
        assert proto.violation_type == "QUANTUM_CHANNEL_SECURITY_VIOLATION"
        assert proto.is_complete is False

        res = evaluate_fused_security_decision(fused_evidence=fused)
        assert res.verdict == DecisionVerdict.ATTACK
        assert res.is_explicit_violation is True

    def test_case5_explicit_violation_with_incompatible_context(self):
        # M13 explicit impersonation violation
        claim = IdentityClaim(
            claimed_identity="Alice",
            expected_identity="Alice",
            session_id="sess_clean",
            configuration_hash="a" * 64,
        )
        auth = AuthenticationEvidence(authenticated_identity="Eve", is_authenticated=True, session_id="sess_clean")
        m13_violation = detect_impersonation(claim=claim, auth_evidence=auth)
        assert m13_violation.is_impersonation_detected is True

        m14 = _make_clean_authorization_evidence()
        m15 = _make_clean_channel_evidence()

        fused = fuse_security_evidence(
            impersonation_evidence=m13_violation,
            authorization_evidence=m14,
            channel_evidence=m15,
            expected_session_id="sess_different",  # Context mismatch!
        )

        # 9-point inspection:
        assert fused.status == FusedEvidenceStatus.SECURITY_VIOLATION
        assert fused.is_explicit_violation is True
        assert ImpersonationReasonCode.AUTHENTICATED_IDENTITY_MISMATCH.value in fused.violations
        assert len(fused.violations) == 1
        assert FusionReasonCode.SESSION_ID_MISMATCH.value in fused.reason_codes
        assert fused.is_complete is False

        proto = fused.to_protocol_security_evidence()
        assert proto.explicit_violation is True
        assert proto.violation_type == ImpersonationReasonCode.AUTHENTICATED_IDENTITY_MISMATCH.value
        assert proto.is_complete is False

        res = evaluate_fused_security_decision(fused_evidence=fused)
        assert res.verdict == DecisionVerdict.ATTACK
        assert res.is_explicit_violation is True

    def test_case6_explicit_violation_with_incomplete_evidence(self):
        # M13 explicit impersonation violation
        claim = IdentityClaim(
            claimed_identity="Alice",
            expected_identity="Alice",
            session_id="sess_clean",
            configuration_hash="a" * 64,
        )
        auth = AuthenticationEvidence(authenticated_identity="Eve", is_authenticated=True, session_id="sess_clean")
        m13_violation = detect_impersonation(claim=claim, auth_evidence=auth)
        assert m13_violation.is_impersonation_detected is True

        m15 = _make_clean_channel_evidence()

        # Missing M14 authorization evidence
        fused = fuse_security_evidence(
            impersonation_evidence=m13_violation,
            authorization_evidence=None,  # Missing!
            channel_evidence=m15,
        )

        # 9-point inspection:
        assert fused.status == FusedEvidenceStatus.SECURITY_VIOLATION
        assert fused.is_explicit_violation is True
        assert ImpersonationReasonCode.AUTHENTICATED_IDENTITY_MISMATCH.value in fused.violations
        assert len(fused.violations) == 1
        assert EvidenceSource.AUTHORIZATION in fused.missing_sources
        assert fused.is_complete is False

        proto = fused.to_protocol_security_evidence()
        assert proto.explicit_violation is True
        assert proto.is_complete is False

        res = evaluate_fused_security_decision(fused_evidence=fused)
        assert res.verdict == DecisionVerdict.ATTACK
        assert res.is_explicit_violation is True

    def test_case7_multiple_explicit_violations_with_conflicting_evidence(self):
        # M13 explicit violation
        claim = IdentityClaim(
            claimed_identity="Alice",
            expected_identity="Alice",
            session_id="sess_clean",
            configuration_hash="a" * 64,
        )
        auth = AuthenticationEvidence(authenticated_identity="Eve", is_authenticated=True, session_id="sess_clean")
        m13_violation = detect_impersonation(claim=claim, auth_evidence=auth)

        # M14 explicit violation
        policy = VerificationPolicy(
            policy_id="pol_strict",
            allowed_identities=("Alice",),
            allowed_operations=(VerificationOperation.VERIFY.value,),
            configuration_hash="a" * 64,
        )
        req = AuthorizationRequest(
            participant_identity="Mallory",
            operation=VerificationOperation.VERIFY.value,
            role="VERIFIER",
            session_id="sess_clean",
            configuration_hash="a" * 64,
        )
        m14_violation = evaluate_verification_authorization(request=req, policy=policy)

        # Cross-source session conflict: M15 has mismatched session!
        m15 = _make_clean_channel_evidence(session_id="sess_disagree")

        fused = fuse_security_evidence(
            impersonation_evidence=m13_violation,
            authorization_evidence=m14_violation,
            channel_evidence=m15,
        )

        # 9-point inspection:
        assert fused.status == FusedEvidenceStatus.CONFLICTING
        assert fused.is_explicit_violation is True
        assert len(fused.violations) == 2
        assert ImpersonationReasonCode.AUTHENTICATED_IDENTITY_MISMATCH.value in fused.violations
        assert AuthorizationReasonCode.AUTHORIZATION_DENIED.value in fused.violations
        assert FusionReasonCode.SESSION_ID_MISMATCH.value in fused.reason_codes
        assert FusionReasonCode.CONFLICTING_EVIDENCE_PRESENT.value in fused.reason_codes
        assert fused.is_complete is False

        proto = fused.to_protocol_security_evidence()
        assert proto.explicit_violation is True
        assert proto.violation_type == f"{ImpersonationReasonCode.AUTHENTICATED_IDENTITY_MISMATCH.value}+{AuthorizationReasonCode.AUTHORIZATION_DENIED.value}"
        assert proto.is_complete is False

        res = evaluate_fused_security_decision(fused_evidence=fused)
        assert res.verdict == DecisionVerdict.ATTACK
        assert res.is_explicit_violation is True

    def test_case8_conflict_without_any_explicit_violation(self):
        m13 = _make_clean_impersonation_evidence()

        # M14 conflicting policy directives without explicit unauthorized detection
        policy_conflict = VerificationPolicy(
            policy_id="pol_conflict",
            allowed_identities=("Alice",),
            denied_identities=("Alice",),
            allowed_operations=(VerificationOperation.VERIFY.value,),
            configuration_hash="a" * 64,
        )
        req = AuthorizationRequest(
            participant_identity="Alice",
            operation=VerificationOperation.VERIFY.value,
            role="VERIFIER",
            session_id="sess_clean",
            configuration_hash="a" * 64,
        )
        m14_conflict = evaluate_verification_authorization(request=req, policy=policy_conflict)
        assert m14_conflict.status == AuthorizationStatus.CONFLICTING
        assert m14_conflict.is_unauthorized_detected is False

        m15 = _make_clean_channel_evidence()

        fused = fuse_security_evidence(
            impersonation_evidence=m13,
            authorization_evidence=m14_conflict,
            channel_evidence=m15,
        )

        # 9-point inspection:
        assert fused.status == FusedEvidenceStatus.CONFLICTING
        assert fused.is_explicit_violation is False
        assert fused.violations == ()
        assert len(fused.violations) == 0
        assert FusionReasonCode.CONFLICTING_EVIDENCE_PRESENT.value in fused.reason_codes
        assert fused.is_complete is False
        assert FusionReasonCode.EXPLICIT_SECURITY_VIOLATION_PRESENT.value not in fused.reason_codes

        proto = fused.to_protocol_security_evidence()
        assert proto.explicit_violation is False
        assert proto.violation_type is None
        assert proto.is_complete is False

        res = evaluate_fused_security_decision(fused_evidence=fused)
        assert res.verdict == DecisionVerdict.SUSPICIOUS
        assert res.verdict != DecisionVerdict.ATTACK
        assert res.is_explicit_violation is False
        assert res.is_evidence_complete is False

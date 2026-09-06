"""Tests for Milestone M14 — Deterministic Unauthorized Verification Detection Layer.

Covers:
    - Scenarios A through H (from Section 28 of specification)
    - 28 Adversarial Tests (from Section 29 of specification)
    - Authentication vs. Authorization boundary (M13 vs M14)
    - Incomplete evidence semantics (missing policy yields SUSPICIOUS, never ATTACK)
    - Explicit denial semantics (denial yields ATTACK in M12)
    - Role-based authorization & operation/resource scoping
    - Conflicting authorization directives (CONFLICTING yields SUSPICIOUS)
    - Context & session binding (mismatch yields INCOMPATIBLE_CONTEXT / SUSPICIOUS)
    - Quantum anomaly independence (valid verifier + quantum noise != unauthorized verification)
    - Clean quantum stats cannot override explicit authorization denial
    - Zero secret leakage guarantees (rejection of password/private_key/secret)
    - Immutability and defensive copying (nested dict freezing)
    - Parameter type & whitespace validation
    - Determinism across repeated executions
    - Prohibition of composite security scores
    - Scope boundaries: no replay, no impersonation, no channel attack classification
    - M14 -> M12 end-to-end integration contracts
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
    evaluate_authorization_decision,
    evaluate_verification_authorization,
)
from src.detection.decision import (
    DecisionReasonCode,
    DecisionResult,
    DecisionVerdict,
    ProtocolSecurityEvidence,
    evaluate_security_decision,
)
from src.detection.impersonation import AuthenticationEvidence
from src.statistics.thresholds import (
    MetricThresholdEvaluation,
    PolicyEvaluationReport,
    ThresholdDirection,
    ThresholdMethod,
)


# ==============================================================================
# Fixtures
# ==============================================================================

@pytest.fixture
def sample_request_alice() -> AuthorizationRequest:
    """Legitimate verification request from Alice."""
    return AuthorizationRequest(
        participant_identity="Alice",
        operation=VerificationOperation.VERIFY.value,
        role="VERIFIER",
        resource_id="doc_alpha_signature",
        session_id="session_001",
        configuration_hash="hash_config_alpha",
    )


@pytest.fixture
def sample_policy_allow_alice() -> VerificationPolicy:
    """Policy explicitly permitting Alice as a verifier."""
    return VerificationPolicy(
        policy_id="policy_verifier_alpha",
        allowed_identities=("Alice",),
        allowed_roles=("VERIFIER",),
        allowed_operations=(
            VerificationOperation.VERIFY.value,
            VerificationOperation.VERIFY_TELEPORTATION.value,
        ),
        allowed_resources=("doc_alpha_signature",),
        session_id="session_001",
        configuration_hash="hash_config_alpha",
    )


@pytest.fixture
def sample_auth_alice() -> AuthenticationEvidence:
    """Valid authentication evidence for Alice."""
    return AuthenticationEvidence(
        authenticated_identity="Alice",
        is_authenticated=True,
        credential_type="PRE_SHARED_KEY",
        is_complete=True,
        session_id="session_001",
    )


@pytest.fixture
def clean_threshold_report() -> PolicyEvaluationReport:
    """Clean M11 report with all metrics within policy."""
    eval_fid = MetricThresholdEvaluation(
        metric_name="fidelity:0",
        observed_value=0.99,
        threshold_value=0.90,
        direction=ThresholdDirection.LOWER,
        exceeded=False,
        margin=-0.09,
        signed_distance=0.09,
        method=ThresholdMethod.EMPIRICAL_QUANTILE,
        boundary_status="strictly_inside",
    )
    eval_qber = MetricThresholdEvaluation(
        metric_name="qber:0",
        observed_value=0.01,
        threshold_value=0.05,
        direction=ThresholdDirection.UPPER,
        exceeded=False,
        margin=-0.04,
        signed_distance=-0.04,
        method=ThresholdMethod.EMPIRICAL_QUANTILE,
        boundary_status="strictly_inside",
    )
    return PolicyEvaluationReport(
        policy_id="policy_alpha",
        baseline_configuration_hash="hash_config_alpha",
        metric_evaluations={"fidelity:0": eval_fid, "qber:0": eval_qber},
        any_exceeded=False,
        all_exceeded=False,
        exceeded_metrics=(),
        exceeded_count=0,
        total_metrics_evaluated=2,
        timestamp="2026-09-06T11:00:00Z",
    )


@pytest.fixture
def anomalous_threshold_report() -> PolicyEvaluationReport:
    """M11 report with threshold exceedance (quantum anomaly)."""
    eval_fid = MetricThresholdEvaluation(
        metric_name="fidelity:0",
        observed_value=0.75,
        threshold_value=0.90,
        direction=ThresholdDirection.LOWER,
        exceeded=True,
        margin=0.15,
        signed_distance=-0.15,
        method=ThresholdMethod.EMPIRICAL_QUANTILE,
        boundary_status="strictly_exceeded",
    )
    eval_qber = MetricThresholdEvaluation(
        metric_name="qber:0",
        observed_value=0.12,
        threshold_value=0.05,
        direction=ThresholdDirection.UPPER,
        exceeded=True,
        margin=0.07,
        signed_distance=0.07,
        method=ThresholdMethod.EMPIRICAL_QUANTILE,
        boundary_status="strictly_exceeded",
    )
    return PolicyEvaluationReport(
        policy_id="policy_alpha",
        baseline_configuration_hash="hash_config_alpha",
        metric_evaluations={"fidelity:0": eval_fid, "qber:0": eval_qber},
        any_exceeded=True,
        all_exceeded=True,
        exceeded_metrics=("fidelity:0", "qber:0"),
        exceeded_count=2,
        total_metrics_evaluated=2,
        timestamp="2026-09-06T11:00:00Z",
    )


# ==============================================================================
# 1. Scenarios A through H (Section 28)
# ==============================================================================

class TestAuthorizationScenarios:
    """Validate Scenarios A through H required by the specification."""

    def test_scenario_a_authorized_alice(
        self,
        sample_request_alice: AuthorizationRequest,
        sample_policy_allow_alice: VerificationPolicy,
        sample_auth_alice: AuthenticationEvidence,
        clean_threshold_report: PolicyEvaluationReport,
    ) -> None:
        """Scenario A: Authorized Alice -> AUTHORIZED -> M12 ACCEPT."""
        ev = evaluate_verification_authorization(
            request=sample_request_alice,
            policy=sample_policy_allow_alice,
            auth_evidence=sample_auth_alice,
        )
        assert ev.is_authorized
        assert not ev.is_unauthorized_detected
        assert not ev.is_indeterminate
        assert ev.status == AuthorizationStatus.AUTHORIZED
        assert ev.primary_reason == AuthorizationReasonCode.AUTHORIZATION_GRANTED
        assert ev.is_evidence_complete

        decision = evaluate_authorization_decision(
            request=sample_request_alice,
            policy=sample_policy_allow_alice,
            threshold_report=clean_threshold_report,
            auth_evidence=sample_auth_alice,
        )
        assert decision.verdict == DecisionVerdict.ACCEPT
        assert decision.primary_reason == DecisionReasonCode.ALL_EVIDENCE_WITHIN_POLICY.value

    def test_scenario_b_explicit_authorization_denial(
        self,
        sample_request_alice: AuthorizationRequest,
        clean_threshold_report: PolicyEvaluationReport,
    ) -> None:
        """Scenario B: Alice explicitly denied by policy -> UNAUTHORIZED -> M12 ATTACK."""
        deny_policy = VerificationPolicy(
            policy_id="policy_deny_alice",
            denied_identities=("Alice",),
        )
        ev = evaluate_verification_authorization(
            request=sample_request_alice,
            policy=deny_policy,
        )
        assert not ev.is_authorized
        assert ev.is_unauthorized_detected
        assert not ev.is_indeterminate
        assert ev.status == AuthorizationStatus.UNAUTHORIZED
        assert ev.primary_reason == AuthorizationReasonCode.AUTHORIZATION_DENIED

        decision = evaluate_authorization_decision(
            request=sample_request_alice,
            policy=deny_policy,
            threshold_report=clean_threshold_report,
        )
        assert decision.verdict == DecisionVerdict.ATTACK
        assert decision.is_explicit_violation

    def test_scenario_c_missing_authorization_policy(
        self,
        sample_request_alice: AuthorizationRequest,
        clean_threshold_report: PolicyEvaluationReport,
    ) -> None:
        """Scenario C: Missing policy -> INCOMPLETE -> M12 SUSPICIOUS (never ATTACK)."""
        ev = evaluate_verification_authorization(
            request=sample_request_alice,
            policy=None,
        )
        assert not ev.is_authorized
        assert not ev.is_unauthorized_detected
        assert ev.is_indeterminate
        assert ev.status == AuthorizationStatus.INCOMPLETE
        assert ev.primary_reason == AuthorizationReasonCode.MISSING_AUTHORIZATION_POLICY
        assert not ev.is_evidence_complete

        decision = evaluate_authorization_decision(
            request=sample_request_alice,
            policy=None,
            threshold_report=clean_threshold_report,
        )
        assert decision.verdict == DecisionVerdict.SUSPICIOUS
        assert not decision.is_explicit_violation

    def test_scenario_d_unauthorized_role(
        self,
        sample_policy_allow_alice: VerificationPolicy,
        clean_threshold_report: PolicyEvaluationReport,
    ) -> None:
        """Scenario D: Identity Alice, role SIGNER (not VERIFIER) -> UNAUTHORIZED -> M12 ATTACK."""
        req = AuthorizationRequest(
            participant_identity="Alice",
            operation=VerificationOperation.VERIFY.value,
            role="SIGNER",
            resource_id="doc_alpha_signature",
            session_id="session_001",
            configuration_hash="hash_config_alpha",
        )
        ev = evaluate_verification_authorization(
            request=req,
            policy=sample_policy_allow_alice,
        )
        assert not ev.is_authorized
        assert ev.is_unauthorized_detected
        assert not ev.is_indeterminate
        assert ev.status == AuthorizationStatus.UNAUTHORIZED
        assert ev.primary_reason == AuthorizationReasonCode.ROLE_NOT_AUTHORIZED

        decision = evaluate_authorization_decision(
            request=req,
            policy=sample_policy_allow_alice,
            threshold_report=clean_threshold_report,
        )
        assert decision.verdict == DecisionVerdict.ATTACK
        assert decision.is_explicit_violation

    def test_scenario_e_authorized_identity_quantum_anomaly(
        self,
        sample_request_alice: AuthorizationRequest,
        sample_policy_allow_alice: VerificationPolicy,
        sample_auth_alice: AuthenticationEvidence,
        anomalous_threshold_report: PolicyEvaluationReport,
    ) -> None:
        """Scenario E: Authorized Alice + quantum anomaly -> M14 AUTHORIZED, M12 SUSPICIOUS."""
        ev = evaluate_verification_authorization(
            request=sample_request_alice,
            policy=sample_policy_allow_alice,
            auth_evidence=sample_auth_alice,
        )
        assert ev.is_authorized
        assert ev.status == AuthorizationStatus.AUTHORIZED

        # In M12, verdict is SUSPICIOUS because of M11 threshold exceedance, NOT M14 denial
        decision = evaluate_authorization_decision(
            request=sample_request_alice,
            policy=sample_policy_allow_alice,
            threshold_report=anomalous_threshold_report,
            auth_evidence=sample_auth_alice,
        )
        assert decision.verdict == DecisionVerdict.SUSPICIOUS
        assert decision.primary_reason == DecisionReasonCode.QUANTUM_METRIC_THRESHOLD_EXCEEDED.value
        assert not decision.is_explicit_violation

    def test_scenario_f_unauthorized_identity_clean_quantum_evidence(
        self,
        clean_threshold_report: PolicyEvaluationReport,
    ) -> None:
        """Scenario F: Unauthorized Eve + clean quantum evidence -> UNAUTHORIZED -> M12 ATTACK."""
        req_eve = AuthorizationRequest(
            participant_identity="Eve",
            operation=VerificationOperation.VERIFY.value,
            role="VERIFIER",
            session_id="session_001",
            configuration_hash="hash_config_alpha",
        )
        policy_only_alice = VerificationPolicy(
            policy_id="policy_only_alice",
            allowed_identities=("Alice",),
            allowed_roles=("VERIFIER",),
        )
        ev = evaluate_verification_authorization(
            request=req_eve,
            policy=policy_only_alice,
        )
        assert not ev.is_authorized
        assert ev.is_unauthorized_detected
        assert ev.status == AuthorizationStatus.UNAUTHORIZED
        assert ev.primary_reason == AuthorizationReasonCode.AUTHORIZATION_DENIED

        # Clean quantum statistics CANNOT override an explicit authorization violation
        decision = evaluate_authorization_decision(
            request=req_eve,
            policy=policy_only_alice,
            threshold_report=clean_threshold_report,
        )
        assert decision.verdict == DecisionVerdict.ATTACK
        assert decision.is_explicit_violation

    def test_scenario_g_session_mismatch(
        self,
        sample_request_alice: AuthorizationRequest,
        sample_policy_allow_alice: VerificationPolicy,
        clean_threshold_report: PolicyEvaluationReport,
    ) -> None:
        """Scenario G: Session mismatch -> INCOMPATIBLE_CONTEXT -> M12 SUSPICIOUS."""
        ev = evaluate_verification_authorization(
            request=sample_request_alice,
            policy=sample_policy_allow_alice,
            expected_session_id="session_DIFFERENT",
        )
        assert not ev.is_authorized
        assert not ev.is_unauthorized_detected
        assert ev.is_indeterminate
        assert ev.status == AuthorizationStatus.INCOMPATIBLE_CONTEXT
        assert ev.primary_reason == AuthorizationReasonCode.AUTHORIZATION_SESSION_MISMATCH

        decision = evaluate_authorization_decision(
            request=sample_request_alice,
            policy=sample_policy_allow_alice,
            threshold_report=clean_threshold_report,
            expected_session_id="session_DIFFERENT",
        )
        assert decision.verdict == DecisionVerdict.SUSPICIOUS

    def test_scenario_h_configuration_mismatch(
        self,
        sample_request_alice: AuthorizationRequest,
        sample_policy_allow_alice: VerificationPolicy,
        clean_threshold_report: PolicyEvaluationReport,
    ) -> None:
        """Scenario H: Configuration hash mismatch -> INCOMPATIBLE_CONTEXT -> M12 SUSPICIOUS (never ACCEPT)."""
        ev = evaluate_verification_authorization(
            request=sample_request_alice,
            policy=sample_policy_allow_alice,
            expected_configuration_hash="hash_mismatch_beta",
        )
        assert not ev.is_authorized
        assert not ev.is_unauthorized_detected
        assert ev.is_indeterminate
        assert ev.status == AuthorizationStatus.INCOMPATIBLE_CONTEXT
        assert ev.primary_reason == AuthorizationReasonCode.AUTHORIZATION_CONTEXT_MISMATCH

        decision = evaluate_authorization_decision(
            request=sample_request_alice,
            policy=sample_policy_allow_alice,
            threshold_report=clean_threshold_report,
            expected_configuration_hash="hash_mismatch_beta",
        )
        assert decision.verdict == DecisionVerdict.SUSPICIOUS
        assert decision.verdict != DecisionVerdict.ACCEPT


# ==============================================================================
# 2. 28 Adversarial Tests (Section 29)
# ==============================================================================

class TestAuthorizationAdversarial:
    """Validate 28 adversarial cases defined in Section 29."""

    def test_adv_01_missing_authenticated_identity(
        self,
        sample_request_alice: AuthorizationRequest,
        sample_policy_allow_alice: VerificationPolicy,
    ) -> None:
        """1. Missing authenticated identity in auth evidence produces INCOMPLETE."""
        auth_no_id = AuthenticationEvidence(authenticated_identity=None, is_authenticated=True)
        ev = evaluate_verification_authorization(
            request=sample_request_alice,
            policy=sample_policy_allow_alice,
            auth_evidence=auth_no_id,
        )
        assert ev.status == AuthorizationStatus.INCOMPLETE
        assert ev.primary_reason == AuthorizationReasonCode.MISSING_AUTHENTICATED_IDENTITY
        assert not ev.is_unauthorized_detected

    def test_adv_02_authentication_evidence_inconsistent_with_m13(
        self,
        sample_request_alice: AuthorizationRequest,
        sample_policy_allow_alice: VerificationPolicy,
    ) -> None:
        """2. Authentication failed (owned by M13) does not produce M14 ATTACK."""
        auth_failed = AuthenticationEvidence(
            authenticated_identity="Alice",
            is_authenticated=False,
        )
        ev = evaluate_verification_authorization(
            request=sample_request_alice,
            policy=sample_policy_allow_alice,
            auth_evidence=auth_failed,
        )
        assert ev.status == AuthorizationStatus.INCOMPLETE
        assert ev.primary_reason == AuthorizationReasonCode.IDENTITY_NOT_AUTHENTICATED
        assert not ev.is_unauthorized_detected

    def test_adv_03_missing_authorization_policy(
        self,
        sample_request_alice: AuthorizationRequest,
    ) -> None:
        """3. Missing authorization policy produces INCOMPLETE."""
        ev = evaluate_verification_authorization(
            request=sample_request_alice,
            policy=None,
        )
        assert ev.status == AuthorizationStatus.INCOMPLETE
        assert ev.primary_reason == AuthorizationReasonCode.MISSING_AUTHORIZATION_POLICY
        assert not ev.is_evidence_complete

    def test_adv_04_empty_policy(
        self,
        sample_request_alice: AuthorizationRequest,
    ) -> None:
        """4. Empty policy (no rules) produces INCOMPLETE, not ATTACK."""
        empty_policy = VerificationPolicy(policy_id="policy_empty")
        ev = evaluate_verification_authorization(
            request=sample_request_alice,
            policy=empty_policy,
        )
        assert ev.status == AuthorizationStatus.INCOMPLETE
        assert ev.primary_reason == AuthorizationReasonCode.INCOMPLETE_AUTHORIZATION_EVIDENCE
        assert not ev.is_unauthorized_detected

    def test_adv_05_empty_operation(self) -> None:
        """5. Empty operation string raises ValueError."""
        with pytest.raises(ValueError, match="operation cannot be empty or whitespace"):
            AuthorizationRequest(participant_identity="Alice", operation="")

    def test_adv_06_whitespace_operation(self) -> None:
        """6. Whitespace operation string raises ValueError."""
        with pytest.raises(ValueError, match="operation cannot be empty or whitespace"):
            AuthorizationRequest(participant_identity="Alice", operation="   \t\n")

    def test_adv_07_invalid_operation_type(self) -> None:
        """7. Invalid operation type raises TypeError."""
        with pytest.raises(TypeError, match="operation must be str"):
            AuthorizationRequest(participant_identity="Alice", operation=123)  # type: ignore

    def test_adv_08_invalid_identity_type(self) -> None:
        """8. Invalid identity type raises TypeError."""
        with pytest.raises(TypeError, match="participant_identity must be str"):
            AuthorizationRequest(participant_identity=123)  # type: ignore

    def test_adv_09_conflicting_allow_deny_evidence(
        self,
        sample_request_alice: AuthorizationRequest,
    ) -> None:
        """9. Conflicting allow/deny evidence produces CONFLICTING status."""
        conflict_policy = VerificationPolicy(
            policy_id="policy_conflict",
            allowed_identities=("Alice",),
            denied_identities=("Alice",),
        )
        ev = evaluate_verification_authorization(
            request=sample_request_alice,
            policy=conflict_policy,
        )
        assert ev.status == AuthorizationStatus.CONFLICTING
        assert ev.primary_reason == AuthorizationReasonCode.CONFLICTING_AUTHORIZATION_EVIDENCE
        assert not ev.is_unauthorized_detected

    def test_adv_10_role_policy_conflict(
        self,
        sample_request_alice: AuthorizationRequest,
    ) -> None:
        """10. Role-policy conflict (role allowed, but identity denied) produces CONFLICTING."""
        conflict_policy = VerificationPolicy(
            policy_id="policy_role_conflict",
            allowed_roles=("VERIFIER",),
            denied_identities=("Alice",),
        )
        ev = evaluate_verification_authorization(
            request=sample_request_alice,
            policy=conflict_policy,
        )
        assert ev.status == AuthorizationStatus.CONFLICTING
        assert ev.primary_reason == AuthorizationReasonCode.CONFLICTING_AUTHORIZATION_EVIDENCE
        assert not ev.is_unauthorized_detected

    def test_adv_11_identity_policy_mismatch(
        self,
        sample_request_alice: AuthorizationRequest,
    ) -> None:
        """11. Policy configuration hash mismatch with request context produces INCOMPATIBLE_CONTEXT."""
        policy_diff_config = VerificationPolicy(
            policy_id="policy_diff_config",
            allowed_identities=("Alice",),
            configuration_hash="hash_config_beta",
        )
        ev = evaluate_verification_authorization(
            request=sample_request_alice,
            policy=policy_diff_config,
        )
        assert ev.status == AuthorizationStatus.INCOMPATIBLE_CONTEXT
        assert ev.primary_reason == AuthorizationReasonCode.AUTHORIZATION_CONTEXT_MISMATCH
        assert not ev.is_authorized

    def test_adv_12_session_mismatch(
        self,
        sample_request_alice: AuthorizationRequest,
        sample_policy_allow_alice: VerificationPolicy,
    ) -> None:
        """12. Session mismatch produces INCOMPATIBLE_CONTEXT and AUTHORIZATION_SESSION_MISMATCH."""
        ev = evaluate_verification_authorization(
            request=sample_request_alice,
            policy=sample_policy_allow_alice,
            expected_session_id="session_unrelated",
        )
        assert ev.status == AuthorizationStatus.INCOMPATIBLE_CONTEXT
        assert ev.primary_reason == AuthorizationReasonCode.AUTHORIZATION_SESSION_MISMATCH

    def test_adv_13_configuration_mismatch(
        self,
        sample_request_alice: AuthorizationRequest,
        sample_policy_allow_alice: VerificationPolicy,
    ) -> None:
        """13. Configuration mismatch produces INCOMPATIBLE_CONTEXT and AUTHORIZATION_CONTEXT_MISMATCH."""
        ev = evaluate_verification_authorization(
            request=sample_request_alice,
            policy=sample_policy_allow_alice,
            expected_configuration_hash="hash_unrelated",
        )
        assert ev.status == AuthorizationStatus.INCOMPATIBLE_CONTEXT
        assert ev.primary_reason == AuthorizationReasonCode.AUTHORIZATION_CONTEXT_MISMATCH

    def test_adv_14_mutable_input_after_evaluation(self) -> None:
        """14. Mutating input mapping after evaluation does not alter produced evidence."""
        policy_unrestricted = VerificationPolicy(policy_id="p1", allowed_identities=("Alice",))
        meta = {"initial_key": "initial_val"}
        input_map = {
            "participant_identity": "Alice",
            "operation": "VERIFY",
            "role": "VERIFIER",
            "metadata": meta,
        }
        ev = evaluate_verification_authorization(
            request=input_map,
            policy=policy_unrestricted,
            metadata=meta,
        )
        assert ev.is_authorized

        # Mutate the input dictionary and metadata
        input_map["participant_identity"] = "Eve"
        meta["initial_key"] = "tampered"
        meta["new_key"] = "hacked"

        # Evidence should remain unchanged
        assert ev.participant_identity == "Alice"
        assert ev.metadata["initial_key"] == "initial_val"
        assert "new_key" not in ev.metadata

    def test_adv_15_mutable_nested_metadata(self) -> None:
        """15. Mutable nested metadata is deep-frozen defensively."""
        nested = {"level1": {"level2": "clean_value"}}
        meta: dict[str, Any] = {"nested": nested}
        req = AuthorizationRequest(
            participant_identity="Alice",
            metadata=meta,
        )
        policy = VerificationPolicy(
            policy_id="p1",
            allowed_identities=("Alice",),
            metadata=meta,
        )

        # Mutate the original nested dict
        meta["new_key"] = "hacked"
        nested["level1"]["level2"] = "tampered"

        assert "new_key" not in req.metadata
        assert req.metadata["nested"]["level1"]["level2"] == "clean_value"
        assert "new_key" not in policy.metadata
        assert policy.metadata["nested"]["level1"]["level2"] == "clean_value"

    def test_adv_16_returned_evidence_mutation_attempt(
        self,
        sample_request_alice: AuthorizationRequest,
        sample_policy_allow_alice: VerificationPolicy,
    ) -> None:
        """16. Attempting to mutate returned evidence attributes raises FrozenInstanceError."""
        ev = evaluate_verification_authorization(
            request=sample_request_alice,
            policy=sample_policy_allow_alice,
        )
        with pytest.raises(FrozenInstanceError):
            ev.is_authorized = False  # type: ignore

        with pytest.raises(FrozenInstanceError):
            ev.status = AuthorizationStatus.UNAUTHORIZED  # type: ignore

    def test_adv_17_deterministic_reason_code_ordering(
        self,
        sample_request_alice: AuthorizationRequest,
    ) -> None:
        """17. Reason codes are always deterministically sorted by their value."""
        conflict_policy = VerificationPolicy(
            policy_id="policy_conflict",
            allowed_identities=("Alice",),
            denied_identities=("Alice",),
        )
        ev = evaluate_verification_authorization(
            request=sample_request_alice,
            policy=conflict_policy,
        )
        assert isinstance(ev.reason_codes, tuple)
        values = [r.value for r in ev.reason_codes]
        assert values == sorted(values)

    def test_adv_18_equivalent_mapping_ordering(
        self,
        sample_policy_allow_alice: VerificationPolicy,
    ) -> None:
        """18. Different key insertion order in mappings produces identical evaluations."""
        map1 = {
            "participant_identity": "Alice",
            "operation": "VERIFY",
            "role": "VERIFIER",
            "resource_id": "doc_1",
        }
        map2 = {
            "resource_id": "doc_1",
            "role": "VERIFIER",
            "operation": "VERIFY",
            "participant_identity": "Alice",
        }
        ev1 = evaluate_verification_authorization(request=map1, policy=sample_policy_allow_alice)
        ev2 = evaluate_verification_authorization(request=map2, policy=sample_policy_allow_alice)
        assert ev1.status == ev2.status
        assert ev1.primary_reason == ev2.primary_reason
        assert ev1.reason_codes == ev2.reason_codes

    def test_adv_19_repeated_evaluation_produces_identical_output(
        self,
        sample_request_alice: AuthorizationRequest,
        sample_policy_allow_alice: VerificationPolicy,
    ) -> None:
        """19. Repeated evaluation with identical inputs produces identical status and reasons."""
        ev1 = evaluate_verification_authorization(request=sample_request_alice, policy=sample_policy_allow_alice)
        ev2 = evaluate_verification_authorization(request=sample_request_alice, policy=sample_policy_allow_alice)
        assert ev1.status == ev2.status
        assert ev1.primary_reason == ev2.primary_reason
        assert ev1.reason_codes == ev2.reason_codes
        assert ev1.is_authorized == ev2.is_authorized
        assert ev1.is_unauthorized_detected == ev2.is_unauthorized_detected

    def test_adv_20_quantum_anomaly_cannot_become_authorization_denial(
        self,
        sample_request_alice: AuthorizationRequest,
        sample_policy_allow_alice: VerificationPolicy,
        anomalous_threshold_report: PolicyEvaluationReport,
    ) -> None:
        """20. Quantum anomaly in threshold report does NOT alter M14 authorization status."""
        ev = evaluate_verification_authorization(
            request=sample_request_alice,
            policy=sample_policy_allow_alice,
        )
        assert ev.is_authorized
        assert ev.status == AuthorizationStatus.AUTHORIZED
        # Even if evaluated with threshold report via adapter:
        dec = evaluate_authorization_decision(
            request=sample_request_alice,
            policy=sample_policy_allow_alice,
            threshold_report=anomalous_threshold_report,
        )
        # M12 becomes SUSPICIOUS due to quantum anomaly, NOT because M14 denied authorization
        assert dec.verdict == DecisionVerdict.SUSPICIOUS
        assert dec.primary_reason == DecisionReasonCode.QUANTUM_METRIC_THRESHOLD_EXCEEDED.value
        assert not dec.is_explicit_violation

    def test_adv_21_authorized_participant_cannot_become_unauthorized_merely_due_to_noise(
        self,
        sample_request_alice: AuthorizationRequest,
        sample_policy_allow_alice: VerificationPolicy,
        anomalous_threshold_report: PolicyEvaluationReport,
    ) -> None:
        """21. M14 never accesses quantum fidelity or QBER to deny authorization."""
        ev = evaluate_verification_authorization(
            request=sample_request_alice,
            policy=sample_policy_allow_alice,
        )
        assert ev.is_authorized
        assert not ev.is_unauthorized_detected

    def test_adv_22_unauthorized_verification_cannot_become_authorized_because_quantum_metrics_clean(
        self,
        clean_threshold_report: PolicyEvaluationReport,
    ) -> None:
        """22. Unauthorized verification attempt remains ATTACK despite clean quantum statistics."""
        req_unauth = AuthorizationRequest(participant_identity="Mallory")
        policy_deny = VerificationPolicy(policy_id="p_deny", denied_identities=("Mallory",))
        dec = evaluate_authorization_decision(
            request=req_unauth,
            policy=policy_deny,
            threshold_report=clean_threshold_report,
        )
        assert dec.verdict == DecisionVerdict.ATTACK
        assert dec.is_explicit_violation

    def test_adv_23_m14_does_not_classify_replay(self) -> None:
        """23. M14 contains no replay, nonce-reuse, or timestamp freshness tracking."""
        req = AuthorizationRequest(participant_identity="Alice")
        policy = VerificationPolicy(policy_id="p1", allowed_identities=("Alice",))
        ev = evaluate_verification_authorization(request=req, policy=policy)
        proto_ev = ev.to_protocol_security_evidence()
        assert proto_ev.nonce is None
        assert "replay" not in ev.status.value.lower()
        assert not any("replay" in r.value.lower() for r in ev.reason_codes)

    def test_adv_24_m14_does_not_classify_impersonation(self) -> None:
        """24. M14 explicit violation is strictly UNAUTHORIZED_VERIFICATION, never IMPERSONATION."""
        req = AuthorizationRequest(participant_identity="Eve")
        policy = VerificationPolicy(policy_id="p1", denied_identities=("Eve",))
        ev = evaluate_verification_authorization(request=req, policy=policy)
        proto_ev = ev.to_protocol_security_evidence()
        assert proto_ev.violation_type == "UNAUTHORIZED_VERIFICATION"
        assert proto_ev.violation_type != "IMPERSONATION"

    def test_adv_25_m14_does_not_classify_channel_attacks(self) -> None:
        """25. M14 does not classify quantum channel attacks (eavesdropping, photon splitting)."""
        req = AuthorizationRequest(participant_identity="Alice")
        policy = VerificationPolicy(policy_id="p1", allowed_identities=("Alice",))
        ev = evaluate_verification_authorization(request=req, policy=policy)
        for r in ev.reason_codes:
            assert "channel" not in r.value.lower()
            assert "intercept" not in r.value.lower()
            assert "photon" not in r.value.lower()

    def test_adv_26_m14_does_not_calculate_composite_score(
        self,
        sample_request_alice: AuthorizationRequest,
        sample_policy_allow_alice: VerificationPolicy,
    ) -> None:
        """26. M14 produces strictly categorical states with NO numeric scores."""
        ev = evaluate_verification_authorization(
            request=sample_request_alice,
            policy=sample_policy_allow_alice,
        )
        assert not hasattr(ev, "score")
        assert not hasattr(ev, "risk_score")
        assert not hasattr(ev, "trust_score")
        assert not hasattr(ev, "confidence")

    def test_adv_27_secret_material_cannot_leak_through_evidence(self) -> None:
        """27. Secret material keywords in metadata or details raise ValueError."""
        with pytest.raises(ValueError, match="Sensitive secret keyword 'password'"):
            AuthorizationRequest(
                participant_identity="Alice",
                metadata={"user_password": "plain_password_123"},
            )

        with pytest.raises(ValueError, match="Sensitive secret keyword 'private_key'"):
            VerificationPolicy(
                policy_id="policy_secret",
                metadata={"server_private_key": "raw_private_key_material"},
            )

    def test_adv_28_unrelated_operations_cannot_be_silently_classified_as_unauthorized_verification(
        self,
        sample_policy_allow_alice: VerificationPolicy,
    ) -> None:
        """28. Unrelated operations (e.g. SIGN) produce INCOMPATIBLE_CONTEXT, NOT an ATTACK."""
        req_sign = AuthorizationRequest(
            participant_identity="Alice",
            operation="SIGN",
        )
        ev = evaluate_verification_authorization(
            request=req_sign,
            policy=sample_policy_allow_alice,
        )
        assert ev.status == AuthorizationStatus.INCOMPATIBLE_CONTEXT
        assert ev.primary_reason == AuthorizationReasonCode.UNSUPPORTED_OPERATION
        assert not ev.is_unauthorized_detected  # Crucial: NEVER flagged as an unauthorized verification attack!

        # In M12, this evaluates to SUSPICIOUS (due to incomplete/incompatible context), NEVER ATTACK
        dec = evaluate_authorization_decision(
            request=req_sign,
            policy=sample_policy_allow_alice,
        )
        assert dec.verdict == DecisionVerdict.SUSPICIOUS
        assert not dec.is_explicit_violation


# ==============================================================================
# 3. Additional Scoping & Granular Authorization Tests
# ==============================================================================

class TestAuthorizationAdditionalScoping:
    """Validate resource restrictions, policy mapping inputs, and role permissions."""

    def test_resource_restriction_unauthorized_resource(
        self,
        sample_request_alice: AuthorizationRequest,
    ) -> None:
        """Participant authorized for doc_1 is denied when requesting doc_2."""
        policy_res_1 = VerificationPolicy(
            policy_id="p_res",
            allowed_identities=("Alice",),
            allowed_resources=("doc_1",),
        )
        req_doc_2 = AuthorizationRequest(
            participant_identity="Alice",
            operation=VerificationOperation.VERIFY.value,
            resource_id="doc_2",
        )
        ev = evaluate_verification_authorization(request=req_doc_2, policy=policy_res_1)
        assert not ev.is_authorized
        assert ev.is_unauthorized_detected
        assert ev.status == AuthorizationStatus.UNAUTHORIZED
        assert ev.primary_reason == AuthorizationReasonCode.RESOURCE_NOT_AUTHORIZED

    def test_operation_restriction_teleportation_only(self) -> None:
        """Policy allowing only VERIFY_TELEPORTATION denies standard VERIFY."""
        policy_tele = VerificationPolicy(
            policy_id="p_tele",
            allowed_identities=("Alice",),
            allowed_operations=(VerificationOperation.VERIFY_TELEPORTATION.value,),
        )
        req_standard = AuthorizationRequest(
            participant_identity="Alice",
            operation=VerificationOperation.VERIFY.value,
        )
        ev = evaluate_verification_authorization(request=req_standard, policy=policy_tele)
        assert not ev.is_authorized
        assert ev.is_unauthorized_detected
        assert ev.status == AuthorizationStatus.UNAUTHORIZED
        assert ev.primary_reason == AuthorizationReasonCode.OPERATION_NOT_PERMITTED

    def test_policy_mapping_input_resolution(self) -> None:
        """Mapping representations of request and policy resolve correctly."""
        req_map = {
            "participant_identity": "Bob",
            "operation": "VERIFY",
            "role": "VERIFIER",
        }
        policy_map = {
            "policy_id": "p_bob",
            "allowed_identities": ["Bob"],
            "allowed_roles": ["VERIFIER"],
        }
        ev = evaluate_verification_authorization(request=req_map, policy=policy_map)
        assert ev.is_authorized
        assert ev.status == AuthorizationStatus.AUTHORIZED
        assert ev.primary_reason == AuthorizationReasonCode.AUTHORIZATION_GRANTED

    def test_auth_evidence_identity_mismatch(
        self,
        sample_request_alice: AuthorizationRequest,
        sample_policy_allow_alice: VerificationPolicy,
    ) -> None:
        """Auth evidence for Bob presented with claim for Alice produces CONFLICTING."""
        auth_bob = AuthenticationEvidence(
            authenticated_identity="Bob",
            is_authenticated=True,
        )
        ev = evaluate_verification_authorization(
            request=sample_request_alice,
            policy=sample_policy_allow_alice,
            auth_evidence=auth_bob,
        )
        assert ev.status == AuthorizationStatus.CONFLICTING
        assert ev.primary_reason == AuthorizationReasonCode.IDENTITY_NOT_AUTHENTICATED
        assert not ev.is_unauthorized_detected

    def test_policy_validation_errors(self) -> None:
        """Invalid fields in VerificationPolicy raise expected exceptions."""
        with pytest.raises(TypeError, match="policy_id must be str"):
            VerificationPolicy(policy_id=123)  # type: ignore

        with pytest.raises(ValueError, match="policy_id cannot be empty"):
            VerificationPolicy(policy_id="   ")

        with pytest.raises(TypeError, match="allowed_identities must be a sequence"):
            VerificationPolicy(policy_id="p1", allowed_identities=123)  # type: ignore

        with pytest.raises(ValueError, match="cannot be empty or whitespace"):
            VerificationPolicy(policy_id="p1", allowed_identities=("",))

    def test_conflict_role_allow_and_deny(
        self,
        sample_request_alice: AuthorizationRequest,
        clean_threshold_report: PolicyEvaluationReport,
    ) -> None:
        """Role present in both allowed_roles and denied_roles produces CONFLICTING -> M12 SUSPICIOUS."""
        conflict_policy = VerificationPolicy(
            policy_id="p_role_conflict",
            allowed_roles=("VERIFIER",),
            denied_roles=("VERIFIER",),
        )
        ev = evaluate_verification_authorization(
            request=sample_request_alice,
            policy=conflict_policy,
        )
        assert ev.status == AuthorizationStatus.CONFLICTING
        assert ev.primary_reason == AuthorizationReasonCode.CONFLICTING_AUTHORIZATION_EVIDENCE
        assert not ev.is_unauthorized_detected

        dec = evaluate_authorization_decision(
            request=sample_request_alice,
            policy=conflict_policy,
            threshold_report=clean_threshold_report,
        )
        assert dec.verdict == DecisionVerdict.SUSPICIOUS
        assert not dec.is_explicit_violation

    def test_conflict_operation_allow_and_deny(
        self,
        sample_request_alice: AuthorizationRequest,
        clean_threshold_report: PolicyEvaluationReport,
    ) -> None:
        """Operation present in both allowed_operations and denied_operations produces CONFLICTING -> M12 SUSPICIOUS."""
        conflict_policy = VerificationPolicy(
            policy_id="p_op_conflict",
            allowed_identities=("Alice",),
            allowed_operations=(VerificationOperation.VERIFY.value,),
            denied_operations=(VerificationOperation.VERIFY.value,),
        )
        ev = evaluate_verification_authorization(
            request=sample_request_alice,
            policy=conflict_policy,
        )
        assert ev.status == AuthorizationStatus.CONFLICTING
        assert ev.primary_reason == AuthorizationReasonCode.CONFLICTING_AUTHORIZATION_EVIDENCE
        assert not ev.is_unauthorized_detected

        dec = evaluate_authorization_decision(
            request=sample_request_alice,
            policy=conflict_policy,
            threshold_report=clean_threshold_report,
        )
        assert dec.verdict == DecisionVerdict.SUSPICIOUS
        assert not dec.is_explicit_violation

    def test_conflict_resource_allow_and_deny(
        self,
        sample_request_alice: AuthorizationRequest,
        clean_threshold_report: PolicyEvaluationReport,
    ) -> None:
        """Resource present in both allowed_resources and denied_resources produces CONFLICTING -> M12 SUSPICIOUS."""
        conflict_policy = VerificationPolicy(
            policy_id="p_res_conflict",
            allowed_identities=("Alice",),
            allowed_resources=("doc_alpha_signature",),
            denied_resources=("doc_alpha_signature",),
        )
        ev = evaluate_verification_authorization(
            request=sample_request_alice,
            policy=conflict_policy,
        )
        assert ev.status == AuthorizationStatus.CONFLICTING
        assert ev.primary_reason == AuthorizationReasonCode.CONFLICTING_AUTHORIZATION_EVIDENCE
        assert not ev.is_unauthorized_detected

        dec = evaluate_authorization_decision(
            request=sample_request_alice,
            policy=conflict_policy,
            threshold_report=clean_threshold_report,
        )
        assert dec.verdict == DecisionVerdict.SUSPICIOUS
        assert not dec.is_explicit_violation

    def test_explicit_operation_denial(
        self,
        sample_request_alice: AuthorizationRequest,
        clean_threshold_report: PolicyEvaluationReport,
    ) -> None:
        """Operation explicitly denied by denied_operations produces UNAUTHORIZED -> M12 ATTACK."""
        policy_deny_op = VerificationPolicy(
            policy_id="p_deny_op",
            allowed_identities=("Alice",),
            denied_operations=(VerificationOperation.VERIFY.value,),
        )
        ev = evaluate_verification_authorization(
            request=sample_request_alice,
            policy=policy_deny_op,
        )
        assert not ev.is_authorized
        assert ev.is_unauthorized_detected
        assert ev.status == AuthorizationStatus.UNAUTHORIZED
        assert ev.primary_reason == AuthorizationReasonCode.OPERATION_NOT_PERMITTED

        dec = evaluate_authorization_decision(
            request=sample_request_alice,
            policy=policy_deny_op,
            threshold_report=clean_threshold_report,
        )
        assert dec.verdict == DecisionVerdict.ATTACK
        assert dec.is_explicit_violation

    def test_explicit_resource_denial(
        self,
        sample_request_alice: AuthorizationRequest,
        clean_threshold_report: PolicyEvaluationReport,
    ) -> None:
        """Resource explicitly denied by denied_resources produces UNAUTHORIZED -> M12 ATTACK."""
        policy_deny_res = VerificationPolicy(
            policy_id="p_deny_res",
            allowed_identities=("Alice",),
            denied_resources=("doc_alpha_signature",),
        )
        ev = evaluate_verification_authorization(
            request=sample_request_alice,
            policy=policy_deny_res,
        )
        assert not ev.is_authorized
        assert ev.is_unauthorized_detected
        assert ev.status == AuthorizationStatus.UNAUTHORIZED
        assert ev.primary_reason == AuthorizationReasonCode.RESOURCE_NOT_AUTHORIZED

        dec = evaluate_authorization_decision(
            request=sample_request_alice,
            policy=policy_deny_res,
            threshold_report=clean_threshold_report,
        )
        assert dec.verdict == DecisionVerdict.ATTACK
        assert dec.is_explicit_violation

    @pytest.mark.parametrize(
        "unrelated_op",
        ["SIGN", "REGISTER", "DELETE", "LOGIN", "TRANSMIT", "UNKNOWN_ARBITRARY_OP"],
    )
    def test_unrelated_operations_never_produce_attack(
        self,
        sample_policy_allow_alice: VerificationPolicy,
        unrelated_op: str,
    ) -> None:
        """Unrelated non-verification operations produce INCOMPATIBLE_CONTEXT / SUSPICIOUS, never ATTACK."""
        req = AuthorizationRequest(
            participant_identity="Alice",
            operation=unrelated_op,
        )
        ev = evaluate_verification_authorization(
            request=req,
            policy=sample_policy_allow_alice,
        )
        assert ev.status == AuthorizationStatus.INCOMPATIBLE_CONTEXT
        assert ev.primary_reason == AuthorizationReasonCode.UNSUPPORTED_OPERATION
        assert not ev.is_unauthorized_detected  # Crucial: never classified as unauthorized verification

        dec = evaluate_authorization_decision(
            request=req,
            policy=sample_policy_allow_alice,
        )
        assert dec.verdict == DecisionVerdict.SUSPICIOUS
        assert not dec.is_explicit_violation

    def test_unauthenticated_request_distinction(
        self,
        sample_policy_allow_alice: VerificationPolicy,
    ) -> None:
        """Explicitly unauthenticated request produces INCOMPLETE / IDENTITY_NOT_AUTHENTICATED, never M14 ATTACK."""
        auth_unauth = AuthenticationEvidence(
            authenticated_identity="Alice",
            is_authenticated=False,
        )
        req = AuthorizationRequest(participant_identity="Alice")
        ev = evaluate_verification_authorization(
            request=req,
            policy=sample_policy_allow_alice,
            auth_evidence=auth_unauth,
        )
        assert ev.status == AuthorizationStatus.INCOMPLETE
        assert ev.primary_reason == AuthorizationReasonCode.IDENTITY_NOT_AUTHENTICATED
        assert not ev.is_unauthorized_detected  # Crucial: authentication failure is NOT unauthorized verification attack

        dec = evaluate_authorization_decision(
            request=req,
            policy=sample_policy_allow_alice,
            auth_evidence=auth_unauth,
        )
        assert dec.verdict == DecisionVerdict.SUSPICIOUS
        assert not dec.is_explicit_violation

    def test_quantum_anomaly_alone_never_unauthorized(
        self,
        anomalous_threshold_report: PolicyEvaluationReport,
    ) -> None:
        """Quantum anomaly alone with missing policy produces INCOMPLETE, never UNAUTHORIZED."""
        req = AuthorizationRequest(participant_identity="Alice")
        ev = evaluate_verification_authorization(request=req, policy=None)
        assert ev.status == AuthorizationStatus.INCOMPLETE
        assert not ev.is_unauthorized_detected
        assert ev.status != AuthorizationStatus.UNAUTHORIZED

        dec = evaluate_authorization_decision(
            request=req,
            policy=None,
            threshold_report=anomalous_threshold_report,
        )
        assert dec.verdict == DecisionVerdict.SUSPICIOUS
        assert not dec.is_explicit_violation

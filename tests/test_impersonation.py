"""Tests for Milestone M13 — Impersonation Detection Layer.

Covers:
    - Scenarios A through G (from specification)
    - Identity authority hierarchy (Disagreement among expected, claimed, authenticated)
    - 18 Adversarial Tests (from Section 21)
    - Incomplete evidence semantics (never produces ATTACK)
    - Missing vs. failed authentication distinction
    - Quantum anomaly independence (valid identity + low fidelity != impersonation)
    - Zero secret leakage guarantees (rejection of password/private_key/secret)
    - Nested dictionary immutability and defensive copying
    - Parameter type & whitespace validation
    - Determinism across repeated executions
    - Prohibition of composite security scores
    - M13 -> M12 end-to-end integration contracts
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import Any

import pytest

from src.detection.decision import (
    DecisionReasonCode,
    DecisionResult,
    DecisionVerdict,
    ProtocolSecurityEvidence,
    evaluate_security_decision,
)
from src.detection.impersonation import (
    AuthenticationEvidence,
    IdentityClaim,
    IdentityEvidenceStatus,
    ImpersonationEvidence,
    ImpersonationReasonCode,
    detect_impersonation,
    evaluate_impersonation_decision,
)
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
def sample_claim_alice() -> IdentityClaim:
    """Legitimate identity claim for Alice."""
    return IdentityClaim(
        claimed_identity="Alice",
        expected_identity="Alice",
        role="SIGNER",
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
# 1. Scenarios A through G
# ==============================================================================

class TestImpersonationScenarios:
    """Validate Scenarios A through G required by the specification."""

    def test_scenario_a_legitimate_alice(
        self,
        sample_claim_alice: IdentityClaim,
        sample_auth_alice: AuthenticationEvidence,
        clean_threshold_report: PolicyEvaluationReport,
    ) -> None:
        """Scenario A: Legitimate participant -> VALID -> M12 ACCEPT."""
        ev = detect_impersonation(claim=sample_claim_alice, auth_evidence=sample_auth_alice)
        assert not ev.is_impersonation_detected
        assert not ev.is_indeterminate
        assert ev.status == IdentityEvidenceStatus.VALID
        assert ev.primary_reason == ImpersonationReasonCode.IDENTITY_VERIFIED
        assert ev.is_evidence_complete

        decision = evaluate_impersonation_decision(
            claim=sample_claim_alice,
            auth_evidence=sample_auth_alice,
            threshold_report=clean_threshold_report,
        )
        assert decision.verdict == DecisionVerdict.ACCEPT
        assert decision.primary_reason == DecisionReasonCode.ALL_EVIDENCE_WITHIN_POLICY.value

    def test_scenario_b_explicit_identity_mismatch_eve(
        self, clean_threshold_report: PolicyEvaluationReport
    ) -> None:
        """Scenario B: Claimed Eve != Expected Alice -> MISMATCH -> M12 ATTACK."""
        claim_eve = IdentityClaim(claimed_identity="Eve", expected_identity="Alice")
        auth_eve = AuthenticationEvidence(authenticated_identity="Eve", is_authenticated=True)
        ev = detect_impersonation(claim=claim_eve, auth_evidence=auth_eve)
        assert ev.is_impersonation_detected
        assert not ev.is_indeterminate
        assert ev.status == IdentityEvidenceStatus.IDENTITY_MISMATCH
        assert ev.primary_reason == ImpersonationReasonCode.CLAIMED_IDENTITY_MISMATCH

        decision = evaluate_impersonation_decision(
            claim=claim_eve, auth_evidence=auth_eve, threshold_report=clean_threshold_report
        )
        assert decision.verdict == DecisionVerdict.ATTACK
        assert decision.is_explicit_violation

    def test_scenario_c_claimed_alice_authenticated_bob(
        self, clean_threshold_report: PolicyEvaluationReport
    ) -> None:
        """Scenario C: Claimed Alice, Authenticated Bob -> MISMATCH -> M12 ATTACK."""
        claim_alice = IdentityClaim(claimed_identity="Alice", expected_identity="Alice")
        auth_bob = AuthenticationEvidence(authenticated_identity="Bob", is_authenticated=True)
        ev = detect_impersonation(claim=claim_alice, auth_evidence=auth_bob)
        assert ev.is_impersonation_detected
        assert not ev.is_indeterminate
        assert ev.primary_reason == ImpersonationReasonCode.AUTHENTICATED_IDENTITY_MISMATCH

        decision = evaluate_impersonation_decision(
            claim=claim_alice, auth_evidence=auth_bob, threshold_report=clean_threshold_report
        )
        assert decision.verdict == DecisionVerdict.ATTACK

    def test_scenario_d_missing_authentication_evidence(
        self,
        sample_claim_alice: IdentityClaim,
        clean_threshold_report: PolicyEvaluationReport,
    ) -> None:
        """Scenario D: Missing auth evidence -> INCOMPLETE -> M12 SUSPICIOUS (never ATTACK)."""
        ev = detect_impersonation(claim=sample_claim_alice, auth_evidence=None)
        assert not ev.is_impersonation_detected
        assert ev.is_indeterminate
        assert ev.status == IdentityEvidenceStatus.INCOMPLETE
        assert ev.primary_reason == ImpersonationReasonCode.MISSING_AUTHENTICATION_EVIDENCE
        assert not ev.is_evidence_complete

        proto_ev = ev.to_protocol_security_evidence()
        assert not proto_ev.explicit_violation
        assert not proto_ev.is_complete

        decision = evaluate_impersonation_decision(
            claim=sample_claim_alice, auth_evidence=None, threshold_report=clean_threshold_report
        )
        assert decision.verdict == DecisionVerdict.SUSPICIOUS
        assert decision.primary_reason == DecisionReasonCode.INCOMPLETE_EVIDENCE.value

    def test_scenario_e_invalid_authentication(
        self,
        sample_claim_alice: IdentityClaim,
        clean_threshold_report: PolicyEvaluationReport,
    ) -> None:
        """Scenario E: Invalid authentication (is_authenticated=False) -> AUTHENTICATION_FAILED -> M12 ATTACK."""
        failed_auth = AuthenticationEvidence(authenticated_identity="Alice", is_authenticated=False)
        ev = detect_impersonation(claim=sample_claim_alice, auth_evidence=failed_auth)
        assert ev.is_impersonation_detected
        assert not ev.is_indeterminate
        assert ev.status == IdentityEvidenceStatus.AUTHENTICATION_FAILED
        assert ev.primary_reason == ImpersonationReasonCode.AUTHENTICATION_INVALID

        decision = evaluate_impersonation_decision(
            claim=sample_claim_alice, auth_evidence=failed_auth, threshold_report=clean_threshold_report
        )
        assert decision.verdict == DecisionVerdict.ATTACK

    def test_scenario_f_valid_identity_with_quantum_anomaly(
        self,
        sample_claim_alice: IdentityClaim,
        sample_auth_alice: AuthenticationEvidence,
        anomalous_threshold_report: PolicyEvaluationReport,
    ) -> None:
        """Scenario F: Valid identity + quantum measurement anomaly.

        Scientific Rule: Quantum anomaly != Impersonation.
        M13 must NOT call this impersonation. M12 produces SUSPICIOUS due to M11.
        """
        ev = detect_impersonation(claim=sample_claim_alice, auth_evidence=sample_auth_alice)
        assert not ev.is_impersonation_detected
        assert ev.status == IdentityEvidenceStatus.VALID

        decision = evaluate_impersonation_decision(
            claim=sample_claim_alice,
            auth_evidence=sample_auth_alice,
            threshold_report=anomalous_threshold_report,
        )
        assert decision.verdict == DecisionVerdict.SUSPICIOUS
        assert decision.primary_reason == DecisionReasonCode.QUANTUM_METRIC_THRESHOLD_EXCEEDED.value
        assert "fidelity:0" in decision.exceeded_metrics

    def test_scenario_g_identity_violation_with_clean_quantum_statistics(
        self, clean_threshold_report: PolicyEvaluationReport
    ) -> None:
        """Scenario G: Explicit identity violation + clean normal quantum statistics.

        Independence verified: M13 flags explicit violation -> M12 produces ATTACK regardless of quantum stats.
        """
        claim_eve = IdentityClaim(claimed_identity="Eve", expected_identity="Alice")
        auth_eve = AuthenticationEvidence(authenticated_identity="Eve", is_authenticated=True)
        ev = detect_impersonation(claim=claim_eve, auth_evidence=auth_eve)
        assert ev.is_impersonation_detected

        decision = evaluate_impersonation_decision(
            claim=claim_eve, auth_evidence=auth_eve, threshold_report=clean_threshold_report
        )
        assert decision.verdict == DecisionVerdict.ATTACK
        assert decision.is_explicit_violation
        assert decision.exceeded_count == 0


# ==============================================================================
# 2. Identity Authority Hierarchy & Conflict Resolution (Section 6)
# ==============================================================================

class TestIdentityAuthorityHierarchy:
    """Verify deterministic semantics when expected, claimed, and authenticated identities disagree."""

    def test_case_1_expected_alice_claimed_alice_authenticated_bob(self) -> None:
        """Case 1: expected=Alice, claimed=Alice, authenticated=Bob.

        Entity authenticated as Bob claims to be Alice to fulfill Alice's session.
        Authority: authenticated_identity overrides claimed_identity.
        -> Status: CONFLICTING / IDENTITY_MISMATCH with AUTHENTICATED_IDENTITY_MISMATCH.
        """
        claim = IdentityClaim(claimed_identity="Alice", expected_identity="Alice")
        auth = AuthenticationEvidence(authenticated_identity="Bob", is_authenticated=True)
        ev = detect_impersonation(claim=claim, auth_evidence=auth)

        assert ev.is_impersonation_detected
        assert ev.primary_reason == ImpersonationReasonCode.AUTHENTICATED_IDENTITY_MISMATCH
        assert ImpersonationReasonCode.AUTHENTICATED_IDENTITY_MISMATCH in ev.reason_codes

    def test_case_2_expected_alice_claimed_eve_authenticated_alice(self) -> None:
        """Case 2: expected=Alice, claimed=Eve, authenticated=Alice.

        Claimant claims Eve while credentials prove Alice for an Alice session.
        Contradictory assertions across claimed, authenticated, and expected.
        -> Status: CONFLICTING with reason codes capturing both mismatches.
        """
        claim = IdentityClaim(claimed_identity="Eve", expected_identity="Alice")
        auth = AuthenticationEvidence(authenticated_identity="Alice", is_authenticated=True)
        ev = detect_impersonation(claim=claim, auth_evidence=auth)

        assert ev.is_impersonation_detected
        assert ev.status == IdentityEvidenceStatus.CONFLICTING
        assert ImpersonationReasonCode.CONFLICTING_IDENTITY_EVIDENCE in ev.reason_codes
        assert ImpersonationReasonCode.AUTHENTICATED_IDENTITY_MISMATCH in ev.reason_codes
        assert ImpersonationReasonCode.CLAIMED_IDENTITY_MISMATCH in ev.reason_codes

    def test_case_3_expected_alice_claimed_eve_authenticated_bob(self) -> None:
        """Case 3: expected=Alice, claimed=Eve, authenticated=Bob.

        All three disagree: claimant claims Eve, authentication proves Bob, session expects Alice.
        -> Status: CONFLICTING with multi-assertional failure.
        """
        claim = IdentityClaim(claimed_identity="Eve", expected_identity="Alice")
        auth = AuthenticationEvidence(authenticated_identity="Bob", is_authenticated=True)
        ev = detect_impersonation(claim=claim, auth_evidence=auth)

        assert ev.is_impersonation_detected
        assert ev.status == IdentityEvidenceStatus.CONFLICTING
        assert ImpersonationReasonCode.CONFLICTING_IDENTITY_EVIDENCE in ev.reason_codes
        assert ImpersonationReasonCode.AUTHENTICATED_IDENTITY_MISMATCH in ev.reason_codes
        assert ImpersonationReasonCode.CLAIMED_IDENTITY_MISMATCH in ev.reason_codes

    def test_authenticated_identity_missing_in_valid_auth(self) -> None:
        """Credential authenticated=True but authenticated_identity=None.

        Cannot verify a named identity assertion without attribution.
        -> Status: INCOMPLETE (Indeterminate -> M12 SUSPICIOUS).
        """
        claim = IdentityClaim(claimed_identity="Alice", expected_identity="Alice")
        auth = AuthenticationEvidence(authenticated_identity=None, is_authenticated=True)
        ev = detect_impersonation(claim=claim, auth_evidence=auth)

        assert not ev.is_impersonation_detected
        assert ev.is_indeterminate
        assert ev.status == IdentityEvidenceStatus.INCOMPLETE
        assert ev.primary_reason == ImpersonationReasonCode.INCOMPLETE_AUTHENTICATION_EVIDENCE
        assert not ev.is_evidence_complete


# ==============================================================================
# 3. 18 Adversarial Tests (Section 21)
# ==============================================================================

class TestAdversarialSecurityAudit:
    """The 18 Adversarial Security Tests required by Section 21 of the audit specification."""

    def test_adv_1_eve_cannot_be_accepted_as_alice(
        self, clean_threshold_report: PolicyEvaluationReport
    ) -> None:
        """Test 1: Eve attempting to claim Alice's identity cannot produce ACCEPT."""
        claim = IdentityClaim(claimed_identity="Alice", expected_identity="Alice")
        auth = AuthenticationEvidence(authenticated_identity="Eve", is_authenticated=True)
        decision = evaluate_impersonation_decision(
            claim=claim, auth_evidence=auth, threshold_report=clean_threshold_report
        )
        assert decision.verdict == DecisionVerdict.ATTACK
        assert decision.verdict != DecisionVerdict.ACCEPT

    def test_adv_2_missing_authentication_cannot_become_attack(
        self, sample_claim_alice: IdentityClaim, clean_threshold_report: PolicyEvaluationReport
    ) -> None:
        """Test 2: Missing authentication evidence must produce SUSPICIOUS, never ATTACK."""
        decision = evaluate_impersonation_decision(
            claim=sample_claim_alice, auth_evidence=None, threshold_report=clean_threshold_report
        )
        assert decision.verdict == DecisionVerdict.SUSPICIOUS
        assert decision.verdict != DecisionVerdict.ATTACK

    def test_adv_3_invalid_authentication_cannot_become_accept(
        self, sample_claim_alice: IdentityClaim, clean_threshold_report: PolicyEvaluationReport
    ) -> None:
        """Test 3: Invalid authentication evidence must produce ATTACK, never ACCEPT."""
        failed_auth = AuthenticationEvidence(authenticated_identity="Alice", is_authenticated=False)
        decision = evaluate_impersonation_decision(
            claim=sample_claim_alice, auth_evidence=failed_auth, threshold_report=clean_threshold_report
        )
        assert decision.verdict == DecisionVerdict.ATTACK
        assert decision.verdict != DecisionVerdict.ACCEPT

    def test_adv_4_quantum_anomaly_cannot_become_impersonation(
        self,
        sample_claim_alice: IdentityClaim,
        sample_auth_alice: AuthenticationEvidence,
        anomalous_threshold_report: PolicyEvaluationReport,
    ) -> None:
        """Test 4: Quantum measurement anomalies cannot produce an impersonation violation."""
        ev = detect_impersonation(claim=sample_claim_alice, auth_evidence=sample_auth_alice)
        assert not ev.is_impersonation_detected
        assert ev.status == IdentityEvidenceStatus.VALID

    def test_adv_5_configuration_mismatch_cannot_become_accept(
        self,
        sample_claim_alice: IdentityClaim,
        sample_auth_alice: AuthenticationEvidence,
        clean_threshold_report: PolicyEvaluationReport,
    ) -> None:
        """Test 5: Baseline configuration hash mismatch cannot produce ACCEPT."""
        ev = detect_impersonation(
            claim=sample_claim_alice,
            auth_evidence=sample_auth_alice,
            expected_configuration_hash="mismatched_config_omega",
        )
        assert not ev.is_evidence_complete
        assert ev.status == IdentityEvidenceStatus.INCOMPATIBLE_CONTEXT

        decision = evaluate_impersonation_decision(
            claim=sample_claim_alice,
            auth_evidence=sample_auth_alice,
            expected_configuration_hash="mismatched_config_omega",
            threshold_report=clean_threshold_report,
        )
        assert decision.verdict != DecisionVerdict.ACCEPT
        assert decision.verdict == DecisionVerdict.SUSPICIOUS

    def test_adv_6_session_mismatch_cannot_silently_become_accept(
        self,
        sample_claim_alice: IdentityClaim,
        sample_auth_alice: AuthenticationEvidence,
        clean_threshold_report: PolicyEvaluationReport,
    ) -> None:
        """Test 6: Session mismatch between claim and expected session cannot produce ACCEPT."""
        decision = evaluate_impersonation_decision(
            claim=sample_claim_alice,
            auth_evidence=sample_auth_alice,
            expected_session_id="session_expected_999",
            threshold_report=clean_threshold_report,
        )
        assert decision.verdict != DecisionVerdict.ACCEPT
        assert decision.verdict == DecisionVerdict.SUSPICIOUS

    def test_adv_7_conflicting_evidence_has_deterministic_semantics(self) -> None:
        """Test 7: Conflicting evidence produces deterministic status and reason codes."""
        claim = IdentityClaim(claimed_identity="Eve", expected_identity="Alice")
        auth = AuthenticationEvidence(authenticated_identity="Bob", is_authenticated=True)
        res1 = detect_impersonation(claim=claim, auth_evidence=auth)
        res2 = detect_impersonation(claim=claim, auth_evidence=auth)
        assert res1.status == IdentityEvidenceStatus.CONFLICTING
        assert res1.reason_codes == res2.reason_codes
        assert res1.primary_reason == res2.primary_reason

    def test_adv_8_input_mutation_cannot_change_evidence(self) -> None:
        """Test 8: Mutating input dictionary after creation cannot alter stored evidence."""
        nested: dict[str, Any] = {"sub": {"count": 1}}
        meta: dict[str, Any] = {"nested": nested}
        claim = IdentityClaim(claimed_identity="Alice", metadata=meta)

        # Mutate outer and nested dicts
        meta["new_key"] = "hacked"
        nested["sub"]["count"] = 999

        assert "new_key" not in claim.metadata
        assert claim.metadata["nested"]["sub"]["count"] == 1

    def test_adv_9_output_mutation_cannot_change_evidence(
        self, sample_claim_alice: IdentityClaim, sample_auth_alice: AuthenticationEvidence
    ) -> None:
        """Test 9: Output evidence objects are strictly frozen."""
        ev = detect_impersonation(claim=sample_claim_alice, auth_evidence=sample_auth_alice)
        with pytest.raises(FrozenInstanceError):
            ev.is_impersonation_detected = True  # type: ignore[misc]
        with pytest.raises(FrozenInstanceError):
            ev.status = IdentityEvidenceStatus.IDENTITY_MISMATCH  # type: ignore[misc]

    def test_adv_10_equivalent_mapping_order_produces_identical_results(self) -> None:
        """Test 10: Input dictionary key ordering has zero effect on evaluation."""
        map1 = {"claimed_identity": "Alice", "expected_identity": "Alice", "session_id": "s1"}
        map2 = {"session_id": "s1", "expected_identity": "Alice", "claimed_identity": "Alice"}
        auth = {"authenticated_identity": "Alice", "is_authenticated": True, "session_id": "s1"}

        res1 = detect_impersonation(claim=map1, auth_evidence=auth)
        res2 = detect_impersonation(claim=map2, auth_evidence=auth)

        assert res1.status == res2.status
        assert res1.primary_reason == res2.primary_reason
        assert res1.reason_codes == res2.reason_codes

    def test_adv_11_repeated_identical_evaluation_produces_identical_output(
        self, sample_claim_alice: IdentityClaim, sample_auth_alice: AuthenticationEvidence
    ) -> None:
        """Test 11: Absolute determinism across repeated executions."""
        r1 = detect_impersonation(claim=sample_claim_alice, auth_evidence=sample_auth_alice)
        r2 = detect_impersonation(claim=sample_claim_alice, auth_evidence=sample_auth_alice)
        assert r1.is_impersonation_detected == r2.is_impersonation_detected
        assert r1.status == r2.status
        assert r1.primary_reason == r2.primary_reason
        assert r1.reason_codes == r2.reason_codes

    def test_adv_12_m13_does_not_detect_replay(
        self, sample_claim_alice: IdentityClaim, sample_auth_alice: AuthenticationEvidence
    ) -> None:
        """Test 12: M13 does not have replay state or freshness detection."""
        ev = detect_impersonation(claim=sample_claim_alice, auth_evidence=sample_auth_alice)
        assert not hasattr(ev, "nonce_reused")
        assert not hasattr(ev, "replay_detected")
        assert not hasattr(ev, "timestamp_freshness")

    def test_adv_13_m13_does_not_detect_unauthorized_verification(
        self, sample_claim_alice: IdentityClaim, sample_auth_alice: AuthenticationEvidence
    ) -> None:
        """Test 13: M13 checks identity assertion consistency, not verification permissions."""
        ev = detect_impersonation(claim=sample_claim_alice, auth_evidence=sample_auth_alice)
        assert not hasattr(ev, "is_authorized_verifier")
        assert not hasattr(ev, "verification_permission")

    def test_adv_14_m13_does_not_detect_quantum_channel_attacks(
        self, sample_claim_alice: IdentityClaim, sample_auth_alice: AuthenticationEvidence
    ) -> None:
        """Test 14: M13 does not inspect photon states or channel noise."""
        ev = detect_impersonation(claim=sample_claim_alice, auth_evidence=sample_auth_alice)
        assert not hasattr(ev, "channel_eavesdropping")
        assert not hasattr(ev, "photon_splitting")

    def test_adv_15_no_composite_score_exists(
        self, sample_claim_alice: IdentityClaim, sample_auth_alice: AuthenticationEvidence
    ) -> None:
        """Test 15: No scalar composite scores (security_score, trust_score, etc.) exist."""
        ev = detect_impersonation(claim=sample_claim_alice, auth_evidence=sample_auth_alice)
        assert not hasattr(ev, "security_score")
        assert not hasattr(ev, "trust_score")
        assert not hasattr(ev, "risk_score")
        assert not hasattr(ev, "impersonation_score")
        assert not hasattr(ev, "confidence_score")

    def test_adv_16_secret_authentication_material_is_not_leaked(self) -> None:
        """Test 16: Attempting to store raw secrets (password, private_key) raises ValueError."""
        with pytest.raises(ValueError, match="Sensitive secret keyword"):
            AuthenticationEvidence(
                authenticated_identity="Alice",
                auth_details={"raw_password": "super_secret_password"},
            )

        with pytest.raises(ValueError, match="Sensitive secret keyword"):
            AuthenticationEvidence(
                authenticated_identity="Alice",
                auth_details={"private_key_pem": "-----BEGIN PRIVATE KEY-----"},
            )

        with pytest.raises(ValueError, match="Sensitive secret keyword"):
            IdentityClaim(
                claimed_identity="Alice",
                metadata={"user_secret": "forbidden_key"},
            )

    def test_adv_17_invalid_field_combinations_are_rejected(self) -> None:
        """Test 17: Incomplete authentication (is_complete=False) overrides is_authenticated=True."""
        incomplete_auth = AuthenticationEvidence(
            authenticated_identity="Alice",
            is_authenticated=True,
            is_complete=False,
        )
        claim = IdentityClaim(claimed_identity="Alice")
        ev = detect_impersonation(claim=claim, auth_evidence=incomplete_auth)
        assert not ev.is_impersonation_detected
        assert ev.is_indeterminate
        assert ev.status == IdentityEvidenceStatus.INCOMPLETE

    def test_adv_18_empty_whitespace_identities_cannot_bypass_validation(self) -> None:
        """Test 18: Empty or whitespace identity strings are rejected upfront."""
        with pytest.raises(ValueError, match="claimed_identity cannot be empty"):
            IdentityClaim(claimed_identity="")
        with pytest.raises(ValueError, match="claimed_identity cannot be empty"):
            IdentityClaim(claimed_identity="    ")
        with pytest.raises(ValueError, match="expected_identity cannot be empty"):
            IdentityClaim(claimed_identity="Alice", expected_identity="  ")
        with pytest.raises(ValueError, match="authenticated_identity cannot be empty"):
            AuthenticationEvidence(authenticated_identity="   ")
        with pytest.raises(ValueError, match="session_id cannot be empty"):
            IdentityClaim(claimed_identity="Alice", session_id="  ")
        with pytest.raises(ValueError, match="configuration_hash cannot be empty"):
            IdentityClaim(claimed_identity="Alice", configuration_hash="  ")


# ==============================================================================
# 4. Explicit Context Argument Validation
# ==============================================================================

class TestContextArgumentValidation:
    """Ensure detect_impersonation explicitly validates parameter types and empty values."""

    def test_invalid_expected_identity_type(self, sample_claim_alice: IdentityClaim) -> None:
        with pytest.raises(TypeError, match="expected_identity must be str"):
            detect_impersonation(claim=sample_claim_alice, expected_identity=123)  # type: ignore[arg-type]

    def test_whitespace_expected_identity_argument(self, sample_claim_alice: IdentityClaim) -> None:
        with pytest.raises(ValueError, match="expected_identity cannot be empty"):
            detect_impersonation(claim=sample_claim_alice, expected_identity="   ")

    def test_invalid_expected_session_id_type(self, sample_claim_alice: IdentityClaim) -> None:
        with pytest.raises(TypeError, match="expected_session_id must be str"):
            detect_impersonation(claim=sample_claim_alice, expected_session_id=123)  # type: ignore[arg-type]

    def test_whitespace_expected_session_id_argument(self, sample_claim_alice: IdentityClaim) -> None:
        with pytest.raises(ValueError, match="expected_session_id cannot be empty"):
            detect_impersonation(claim=sample_claim_alice, expected_session_id="   ")

    def test_invalid_expected_configuration_hash_type(self, sample_claim_alice: IdentityClaim) -> None:
        with pytest.raises(TypeError, match="expected_configuration_hash must be str"):
            detect_impersonation(claim=sample_claim_alice, expected_configuration_hash=123)  # type: ignore[arg-type]

    def test_whitespace_expected_configuration_hash_argument(self, sample_claim_alice: IdentityClaim) -> None:
        with pytest.raises(ValueError, match="expected_configuration_hash cannot be empty"):
            detect_impersonation(claim=sample_claim_alice, expected_configuration_hash="   ")

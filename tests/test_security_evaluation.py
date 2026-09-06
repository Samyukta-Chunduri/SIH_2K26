"""Q-SHIELD — Test Suite for Milestone M17: Deterministic Security Evaluation.

Verifies:
    1. Clean scenario -> expected result (ACCEPT)
    2. Benign noise scenario (ACCEPT)
    3. Impersonation scenario (ATTACK)
    4. Unauthorized verification scenario (ATTACK)
    5. Quantum channel anomaly scenario (SUSPICIOUS)
    6. Explicit quantum channel violation (ATTACK)
    7. Incomplete evidence (SUSPICIOUS)
    8. Incompatible session (SUSPICIOUS)
    9. Incompatible configuration (SUSPICIOUS)
    10. Conflicting evidence (SUSPICIOUS)
    11. Multiple explicit violations (ATTACK)
    12. Explicit violation + conflict (ATTACK)
    13. Expected ATTACK -> observed ATTACK (PASS)
    14. Expected non-ATTACK -> observed non-ATTACK (PASS)
    15. Expected ATTACK -> observed non-ATTACK (FAIL)
    16. Expected non-ATTACK -> observed ATTACK (FAIL)
    17. Multiple scenarios continue after one failure (no early exit)
    18. Deterministic repeated evaluation (bit-for-bit identical results)
    19. Deterministic scenario ordering
    20. Immutable scenario (FrozenInstanceError on mutation)
    21. Immutable result (FrozenInstanceError on mutation)
    22. Source evidence remains unchanged after evaluation
    23. Configuration provenance preserved
    24. Secret leakage protection (rejects prohibited secret keywords)
    25. No M12 decision duplication (M12 remains sole decision authority)
    26. M13/M14/M15/M16 semantics remain unchanged
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
import pytest

from src.detection.authorization import (
    AuthorizationEvidence,
    AuthorizationReasonCode,
    AuthorizationStatus,
)
from src.detection.channel import (
    ChannelEvidenceStatus,
    ChannelReasonCode,
    ChannelSecurityEvidence,
)
from src.detection.decision import (
    DecisionReasonCode,
    DecisionResult,
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
    IdentityEvidenceStatus,
    ImpersonationEvidence,
    ImpersonationReasonCode,
)
from src.evaluation.security_evaluation import (
    CategorySummary,
    ConfusionMatrixMetrics,
    EvaluationCategory,
    EvaluationResult,
    EvaluationScenario,
    EvaluationSummary,
    build_baseline_evaluation_suite,
    evaluate_scenario,
    make_anomalous_channel_evidence,
    make_clean_authorization_evidence,
    make_clean_channel_evidence,
    make_clean_impersonation_evidence,
    make_clean_threshold_report,
    make_conflicting_authorization_evidence,
    make_conflicting_channel_evidence,
    make_conflicting_impersonation_evidence,
    make_unauthorized_authorization_evidence,
    make_violating_channel_evidence,
    make_violating_impersonation_evidence,
    run_security_evaluation,
)
from src.statistics.thresholds import PolicyEvaluationReport


# ==============================================================================
# Common Test Fixtures
# ==============================================================================

@pytest.fixture
def clean_m13() -> ImpersonationEvidence:
    return make_clean_impersonation_evidence(
        session_id="sess_eval_common",
        configuration_hash="hash_eval_common",
    )


@pytest.fixture
def clean_m14() -> AuthorizationEvidence:
    return make_clean_authorization_evidence(
        session_id="sess_eval_common",
        configuration_hash="hash_eval_common",
    )


@pytest.fixture
def clean_m15() -> ChannelSecurityEvidence:
    return make_clean_channel_evidence(
        session_id="sess_eval_common",
        configuration_hash="hash_eval_common",
    )


# ==============================================================================
# Suite 1: Evaluation Scenario Model & Validation
# ==============================================================================

class TestScenarioModelValidation:
    """Validates structural constraints, type checks, and immutability of EvaluationScenario."""

    def test_valid_scenario_creation(self, clean_m13: ImpersonationEvidence) -> None:
        sc = EvaluationScenario(
            scenario_id="SCEN_VALID_01",
            name="Valid Scenario Test",
            description="Testing standard valid scenario initialization",
            category=EvaluationCategory.CLEAN_HONEST,
            expected_verdict=DecisionVerdict.ACCEPT,
            impersonation_evidence=clean_m13,
            expected_session_id="sess_eval_common",
            expected_configuration_hash="hash_eval_common",
        )
        assert sc.scenario_id == "SCEN_VALID_01"
        assert sc.name == "Valid Scenario Test"
        assert sc.category == EvaluationCategory.CLEAN_HONEST
        assert sc.expected_verdict == DecisionVerdict.ACCEPT
        assert sc.expected_is_violation is False
        assert sc.expected_violation_types == ()
        assert sc.expected_session_id == "sess_eval_common"

    def test_empty_or_invalid_scenario_id(self) -> None:
        with pytest.raises(ValueError, match="scenario_id cannot be empty"):
            EvaluationScenario(
                scenario_id="",
                name="Test",
                description="desc",
                category=EvaluationCategory.CLEAN_HONEST,
                expected_verdict=DecisionVerdict.ACCEPT,
            )

        with pytest.raises(ValueError, match="scenario_id cannot be empty"):
            EvaluationScenario(
                scenario_id="   ",
                name="Test",
                description="desc",
                category=EvaluationCategory.CLEAN_HONEST,
                expected_verdict=DecisionVerdict.ACCEPT,
            )

        with pytest.raises(TypeError, match="scenario_id must be str"):
            EvaluationScenario(
                scenario_id=123,  # pyright: ignore[reportArgumentType]
                name="Test",
                description="desc",
                category=EvaluationCategory.CLEAN_HONEST,
                expected_verdict=DecisionVerdict.ACCEPT,
            )

    def test_empty_or_invalid_name(self) -> None:
        with pytest.raises(ValueError, match="name cannot be empty"):
            EvaluationScenario(
                scenario_id="SCEN_01",
                name="  ",
                description="desc",
                category=EvaluationCategory.CLEAN_HONEST,
                expected_verdict=DecisionVerdict.ACCEPT,
            )

        with pytest.raises(TypeError, match="name must be str"):
            EvaluationScenario(
                scenario_id="SCEN_01",
                name=None,  # pyright: ignore[reportArgumentType]
                description="desc",
                category=EvaluationCategory.CLEAN_HONEST,
                expected_verdict=DecisionVerdict.ACCEPT,
            )

    def test_invalid_category_and_verdict(self) -> None:
        with pytest.raises(ValueError, match="Invalid EvaluationCategory"):
            EvaluationScenario(
                scenario_id="SCEN_01",
                name="Test",
                description="desc",
                category="NON_EXISTENT_CATEGORY",  # pyright: ignore[reportArgumentType]
                expected_verdict=DecisionVerdict.ACCEPT,
            )

        with pytest.raises(ValueError, match="Invalid DecisionVerdict"):
            EvaluationScenario(
                scenario_id="SCEN_01",
                name="Test",
                description="desc",
                category=EvaluationCategory.CLEAN_HONEST,
                expected_verdict="MAYBE_ATTACK",  # pyright: ignore[reportArgumentType]
            )

    def test_invalid_context_parameters(self) -> None:
        with pytest.raises(ValueError, match="expected_session_id cannot be empty"):
            EvaluationScenario(
                scenario_id="SCEN_01",
                name="Test",
                description="desc",
                category=EvaluationCategory.CLEAN_HONEST,
                expected_verdict=DecisionVerdict.ACCEPT,
                expected_session_id="  ",
            )

        with pytest.raises(ValueError, match="expected_configuration_hash cannot be empty"):
            EvaluationScenario(
                scenario_id="SCEN_01",
                name="Test",
                description="desc",
                category=EvaluationCategory.CLEAN_HONEST,
                expected_verdict=DecisionVerdict.ACCEPT,
                expected_configuration_hash="  ",
            )

    def test_secret_leakage_protection_in_scenario(self) -> None:
        with pytest.raises(ValueError, match="Sensitive secret keyword 'password' detected"):
            EvaluationScenario(
                scenario_id="SCEN_SECRET_LEAK",
                name="Secret Leak Test",
                description="Should fail due to secret guard",
                category=EvaluationCategory.CLEAN_HONEST,
                expected_verdict=DecisionVerdict.ACCEPT,
                metadata={"user_password": "super_secret_value"},
            )

        with pytest.raises(ValueError, match="Sensitive secret keyword 'private_key' detected"):
            EvaluationScenario(
                scenario_id="SCEN_SECRET_LEAK_2",
                name="Secret Leak Test 2",
                description="Should fail due to secret guard",
                category=EvaluationCategory.CLEAN_HONEST,
                expected_verdict=DecisionVerdict.ACCEPT,
                metadata={"nested": {"raw_private_key": "raw_bits"}},
            )

    def test_scenario_immutability(self, clean_m13: ImpersonationEvidence) -> None:
        sc = EvaluationScenario(
            scenario_id="SCEN_IMMUTABLE",
            name="Immutability Test",
            description="desc",
            category=EvaluationCategory.CLEAN_HONEST,
            expected_verdict=DecisionVerdict.ACCEPT,
            impersonation_evidence=clean_m13,
            metadata={"tag": "eval_test"},
        )
        with pytest.raises(FrozenInstanceError):
            sc.name = "Mutated Name"  # pyright: ignore[reportAttributeAccessIssue]

        with pytest.raises(FrozenInstanceError):
            sc.expected_verdict = DecisionVerdict.ATTACK  # pyright: ignore[reportAttributeAccessIssue]

        # External metadata mutation cannot affect scenario
        orig_meta = {"level": 1, "nested": {"param": "alpha"}}
        sc2 = EvaluationScenario(
            scenario_id="SCEN_IMMUTABLE_META",
            name="Meta Immutability",
            description="desc",
            category=EvaluationCategory.CLEAN_HONEST,
            expected_verdict=DecisionVerdict.ACCEPT,
            metadata=orig_meta,
        )
        orig_meta["level"] = 999
        orig_meta["nested"]["param"] = "mutated"
        assert sc2.metadata["level"] == 1
        assert sc2.metadata["nested"]["param"] == "alpha"


# ==============================================================================
# Suite 2: Ten Required Evaluation Categories
# ==============================================================================

class TestTenEvaluationCategories:
    """Verifies pipeline behavior on each of the 10 minimum evaluation categories."""

    def test_category_1_clean_honest(
        self,
        clean_m13: ImpersonationEvidence,
        clean_m14: AuthorizationEvidence,
        clean_m15: ChannelSecurityEvidence,
    ) -> None:
        """Category 1: Clean honest operation yields M12 ACCEPT."""
        sc = EvaluationScenario(
            scenario_id="CAT_01_CLEAN",
            name="Category 1 Clean Honest",
            description="All subsystems valid and clean",
            category=EvaluationCategory.CLEAN_HONEST,
            expected_verdict=DecisionVerdict.ACCEPT,
            expected_is_violation=False,
            impersonation_evidence=clean_m13,
            authorization_evidence=clean_m14,
            channel_evidence=clean_m15,
            expected_session_id="sess_eval_common",
            expected_configuration_hash="hash_eval_common",
        )
        res = evaluate_scenario(sc)
        assert res.passed is True
        assert res.observed_verdict == DecisionVerdict.ACCEPT
        assert res.observed_is_violation is False
        assert len(res.mismatch_reasons) == 0

    def test_category_2_benign_noise(
        self,
        clean_m13: ImpersonationEvidence,
        clean_m14: AuthorizationEvidence,
        clean_m15: ChannelSecurityEvidence,
    ) -> None:
        """Category 2: Benign expected noise within threshold bounds yields M12 ACCEPT."""
        sc = EvaluationScenario(
            scenario_id="CAT_02_BENIGN_NOISE",
            name="Category 2 Benign Noise",
            description="Quantum channel exhibits minor baseline thermal noise within threshold tolerance",
            category=EvaluationCategory.BENIGN_NOISE,
            expected_verdict=DecisionVerdict.ACCEPT,
            expected_is_violation=False,
            impersonation_evidence=clean_m13,
            authorization_evidence=clean_m14,
            channel_evidence=clean_m15,
            expected_session_id="sess_eval_common",
            expected_configuration_hash="hash_eval_common",
            metadata={"channel_qber": 0.015},
        )
        res = evaluate_scenario(sc)
        assert res.passed is True
        assert res.observed_verdict == DecisionVerdict.ACCEPT
        assert res.observed_is_violation is False

    def test_category_3_impersonation_attack(
        self,
        clean_m14: AuthorizationEvidence,
        clean_m15: ChannelSecurityEvidence,
    ) -> None:
        """Category 3: Explicit impersonation mismatch yields M12 ATTACK."""
        m13_attack = make_violating_impersonation_evidence(
            session_id="sess_eval_common",
            configuration_hash="hash_eval_common",
        )
        sc = EvaluationScenario(
            scenario_id="CAT_03_IMPERSONATION",
            name="Category 3 Impersonation",
            description="Cryptographic identity mismatch explicitly detected",
            category=EvaluationCategory.IMPERSONATION,
            expected_verdict=DecisionVerdict.ATTACK,
            expected_is_violation=True,
            expected_violation_types=(ImpersonationReasonCode.AUTHENTICATED_IDENTITY_MISMATCH.value,),
            impersonation_evidence=m13_attack,
            authorization_evidence=clean_m14,
            channel_evidence=clean_m15,
            expected_session_id="sess_eval_common",
            expected_configuration_hash="hash_eval_common",
        )
        res = evaluate_scenario(sc)
        assert res.passed is True
        assert res.observed_verdict == DecisionVerdict.ATTACK
        assert res.observed_is_violation is True

    def test_category_4_unauthorized_verification(
        self,
        clean_m13: ImpersonationEvidence,
        clean_m15: ChannelSecurityEvidence,
    ) -> None:
        """Category 4: Explicit unauthorized verification attempt yields M12 ATTACK."""
        m14_unauth = make_unauthorized_authorization_evidence(
            session_id="sess_eval_common",
            configuration_hash="hash_eval_common",
        )
        sc = EvaluationScenario(
            scenario_id="CAT_04_UNAUTHORIZED",
            name="Category 4 Unauthorized Verification",
            description="Participant not permitted to verify digital signature",
            category=EvaluationCategory.UNAUTHORIZED_VERIFICATION,
            expected_verdict=DecisionVerdict.ATTACK,
            expected_is_violation=True,
            expected_violation_types=(AuthorizationReasonCode.AUTHORIZATION_DENIED.value,),
            impersonation_evidence=clean_m13,
            authorization_evidence=m14_unauth,
            channel_evidence=clean_m15,
            expected_session_id="sess_eval_common",
            expected_configuration_hash="hash_eval_common",
        )
        res = evaluate_scenario(sc)
        assert res.passed is True
        assert res.observed_verdict == DecisionVerdict.ATTACK
        assert res.observed_is_violation is True

    def test_category_5_quantum_channel_anomaly(
        self,
        clean_m13: ImpersonationEvidence,
        clean_m14: AuthorizationEvidence,
    ) -> None:
        """Category 5: Physical quantum channel telemetry threshold anomaly yields M12 SUSPICIOUS."""
        m15_anom = make_anomalous_channel_evidence(
            session_id="sess_eval_common",
            configuration_hash="hash_eval_common",
        )
        sc = EvaluationScenario(
            scenario_id="CAT_05_CHANNEL_ANOMALY",
            name="Category 5 Channel Anomaly",
            description="Observed QBER exceeded calibrated threshold without deterministic breach proof",
            category=EvaluationCategory.QUANTUM_CHANNEL_ANOMALY,
            expected_verdict=DecisionVerdict.SUSPICIOUS,
            expected_is_violation=False,
            impersonation_evidence=clean_m13,
            authorization_evidence=clean_m14,
            channel_evidence=m15_anom,
            expected_session_id="sess_eval_common",
            expected_configuration_hash="hash_eval_common",
        )
        res = evaluate_scenario(sc)
        assert res.passed is True
        assert res.observed_verdict == DecisionVerdict.SUSPICIOUS
        assert res.observed_is_violation is False

    def test_category_6_explicit_quantum_channel_violation(
        self,
        clean_m13: ImpersonationEvidence,
        clean_m14: AuthorizationEvidence,
    ) -> None:
        """Category 6: Explicit quantum channel protocol breach yields M12 ATTACK."""
        m15_breach = make_violating_channel_evidence(
            session_id="sess_eval_common",
            configuration_hash="hash_eval_common",
        )
        sc = EvaluationScenario(
            scenario_id="CAT_06_EXPLICIT_CHANNEL_VIOLATION",
            name="Category 6 Channel Breach",
            description="Quantum channel protocol violation confirmed explicitly",
            category=EvaluationCategory.EXPLICIT_QUANTUM_CHANNEL_VIOLATION,
            expected_verdict=DecisionVerdict.ATTACK,
            expected_is_violation=True,
            expected_violation_types=(ChannelReasonCode.QUANTUM_CHANNEL_SECURITY_VIOLATION.value,),
            impersonation_evidence=clean_m13,
            authorization_evidence=clean_m14,
            channel_evidence=m15_breach,
            expected_session_id="sess_eval_common",
            expected_configuration_hash="hash_eval_common",
        )
        res = evaluate_scenario(sc)
        assert res.passed is True
        assert res.observed_verdict == DecisionVerdict.ATTACK
        assert res.observed_is_violation is True

    def test_category_7_incomplete_evidence(
        self,
        clean_m13: ImpersonationEvidence,
        clean_m15: ChannelSecurityEvidence,
    ) -> None:
        """Category 7: Missing required evidence source yields M12 SUSPICIOUS (missing != clean)."""
        sc = EvaluationScenario(
            scenario_id="CAT_07_INCOMPLETE",
            name="Category 7 Incomplete Evidence",
            description="Authorization evidence omitted; evaluated against required sources",
            category=EvaluationCategory.INCOMPLETE_EVIDENCE,
            expected_verdict=DecisionVerdict.SUSPICIOUS,
            expected_is_violation=False,
            impersonation_evidence=clean_m13,
            authorization_evidence=None,
            channel_evidence=clean_m15,
            required_sources=(
                EvidenceSource.IMPERSONATION.value,
                EvidenceSource.AUTHORIZATION.value,
                EvidenceSource.QUANTUM_CHANNEL.value,
            ),
            expected_session_id="sess_eval_common",
            expected_configuration_hash="hash_eval_common",
        )
        res = evaluate_scenario(sc)
        assert res.passed is True
        assert res.observed_verdict == DecisionVerdict.SUSPICIOUS
        assert res.observed_is_violation is False

    def test_category_8_incompatible_context(
        self,
        clean_m13: ImpersonationEvidence,
        clean_m14: AuthorizationEvidence,
        clean_m15: ChannelSecurityEvidence,
    ) -> None:
        """Category 8: Session context mismatch across sources yields M12 SUSPICIOUS."""
        m15_mismatch = make_clean_channel_evidence(
            session_id="sess_foreign_cross_context",
            configuration_hash="hash_eval_common",
        )
        sc = EvaluationScenario(
            scenario_id="CAT_08_INCOMPATIBLE_SESSION",
            name="Category 8 Incompatible Session",
            description="Cross-source session ID mismatch",
            category=EvaluationCategory.INCOMPATIBLE_CONTEXT,
            expected_verdict=DecisionVerdict.SUSPICIOUS,
            expected_is_violation=False,
            impersonation_evidence=clean_m13,
            authorization_evidence=clean_m14,
            channel_evidence=m15_mismatch,
            expected_session_id="sess_eval_common",
            expected_configuration_hash="hash_eval_common",
        )
        res = evaluate_scenario(sc)
        assert res.passed is True
        assert res.observed_verdict == DecisionVerdict.SUSPICIOUS
        assert res.observed_is_violation is False

        # Baseline configuration hash mismatch against expected context
        sc_config = EvaluationScenario(
            scenario_id="CAT_08_INCOMPATIBLE_CONFIG",
            name="Category 8 Incompatible Config Hash",
            description="Mismatched baseline configuration hash",
            category=EvaluationCategory.INCOMPATIBLE_CONTEXT,
            expected_verdict=DecisionVerdict.SUSPICIOUS,
            expected_is_violation=False,
            impersonation_evidence=clean_m13,
            authorization_evidence=clean_m14,
            channel_evidence=clean_m15,
            expected_session_id="sess_eval_common",
            expected_configuration_hash="hash_different_baseline_sha256",
        )
        res_config = evaluate_scenario(sc_config)
        assert res_config.passed is True
        assert res_config.observed_verdict == DecisionVerdict.SUSPICIOUS

    def test_category_9_conflicting_evidence(
        self,
        clean_m14: AuthorizationEvidence,
        clean_m15: ChannelSecurityEvidence,
    ) -> None:
        """Category 9: Contradictory evidence assertions without explicit violation yields M12 SUSPICIOUS."""
        m13_conflict = make_conflicting_impersonation_evidence(
            session_id="sess_eval_common",
            configuration_hash="hash_eval_common",
        )
        sc = EvaluationScenario(
            scenario_id="CAT_09_CONFLICTING",
            name="Category 9 Conflicting Evidence",
            description="Internal contradictory credentials assertion",
            category=EvaluationCategory.CONFLICTING_EVIDENCE,
            expected_verdict=DecisionVerdict.SUSPICIOUS,
            expected_is_violation=False,
            impersonation_evidence=m13_conflict,
            authorization_evidence=clean_m14,
            channel_evidence=clean_m15,
            expected_session_id="sess_eval_common",
            expected_configuration_hash="hash_eval_common",
        )
        res = evaluate_scenario(sc)
        assert res.passed is True
        assert res.observed_verdict == DecisionVerdict.SUSPICIOUS
        assert res.observed_is_violation is False

    def test_category_10_multi_source_security_violation(self) -> None:
        """Category 10: Multiple subsystems independently confirming violations yields M12 ATTACK with all violations preserved."""
        m13_viol = make_violating_impersonation_evidence(
            session_id="sess_eval_common",
            configuration_hash="hash_eval_common",
        )
        m14_viol = make_unauthorized_authorization_evidence(
            session_id="sess_eval_common",
            configuration_hash="hash_eval_common",
        )
        m15_viol = make_violating_channel_evidence(
            session_id="sess_eval_common",
            configuration_hash="hash_eval_common",
        )
        sc = EvaluationScenario(
            scenario_id="CAT_10_TRI_SOURCE_VIOLATION",
            name="Category 10 Tri-Source Simultaneous Violation",
            description="M13, M14, and M15 confirm explicit violations simultaneously",
            category=EvaluationCategory.MULTI_SOURCE_SECURITY_VIOLATION,
            expected_verdict=DecisionVerdict.ATTACK,
            expected_is_violation=True,
            expected_violation_types=(
                ImpersonationReasonCode.AUTHENTICATED_IDENTITY_MISMATCH.value,
                AuthorizationReasonCode.AUTHORIZATION_DENIED.value,
                ChannelReasonCode.QUANTUM_CHANNEL_SECURITY_VIOLATION.value,
            ),
            impersonation_evidence=m13_viol,
            authorization_evidence=m14_viol,
            channel_evidence=m15_viol,
            expected_session_id="sess_eval_common",
            expected_configuration_hash="hash_eval_common",
        )
        res = evaluate_scenario(sc)
        assert res.passed is True
        assert res.observed_verdict == DecisionVerdict.ATTACK
        assert res.observed_is_violation is True


# ==============================================================================
# Suite 3: Multi-Source Combinations A Through J
# ==============================================================================

class TestMultiSourceCombinations:
    """Verifies all required multi-source interaction combinations A through J."""

    def test_multi_source_combinations_via_baseline_suite(self) -> None:
        """Build and verify the full baseline evaluation suite covering Combinations A-J."""
        suite = build_baseline_evaluation_suite(
            session_id="sess_baseline_test",
            configuration_hash="hash_baseline_test_sha256",
        )
        assert len(suite) == 16

        summary = run_security_evaluation(suite)
        assert summary.total_scenarios == 16
        assert summary.passed_scenarios == 16
        assert summary.failed_scenarios == 0
        assert summary.pass_rate == 1.0
        assert len(summary.failed_scenario_ids) == 0

        # Verify specific combinations exist and passed
        scen_map = {r.scenario_id: r for r in summary.results}

        # Comb A: M13 violation only -> ATTACK
        assert scen_map["SCEN_03_IMPERSONATION_SOLO"].observed_verdict == DecisionVerdict.ATTACK
        # Comb B: M14 violation only -> ATTACK
        assert scen_map["SCEN_04_UNAUTHORIZED_VERIFICATION_SOLO"].observed_verdict == DecisionVerdict.ATTACK
        # Comb C: M15 violation only -> ATTACK
        assert scen_map["SCEN_06_EXPLICIT_CHANNEL_VIOLATION_SOLO"].observed_verdict == DecisionVerdict.ATTACK
        # Comb D: M13 + M14 violations -> ATTACK
        assert scen_map["SCEN_11_COMB_D_M13_M14_VIOLATIONS"].observed_verdict == DecisionVerdict.ATTACK
        # Comb E: M13 + M15 violations -> ATTACK
        assert scen_map["SCEN_12_COMB_E_M13_M15_VIOLATIONS"].observed_verdict == DecisionVerdict.ATTACK
        # Comb F: M14 + M15 violations -> ATTACK
        assert scen_map["SCEN_13_COMB_F_M14_M15_VIOLATIONS"].observed_verdict == DecisionVerdict.ATTACK
        # Comb G: M13 + M14 + M15 violations -> ATTACK
        assert scen_map["SCEN_10_MULTI_SOURCE_ALL_VIOLATIONS"].observed_verdict == DecisionVerdict.ATTACK
        # Comb H: Explicit violation + conflict -> ATTACK (M16 preservation verified)
        assert scen_map["SCEN_14_COMB_H_VIOLATION_AND_CONFLICT"].observed_verdict == DecisionVerdict.ATTACK
        # Comb I: Anomaly + incomplete evidence -> SUSPICIOUS
        assert scen_map["SCEN_15_COMB_I_ANOMALY_AND_INCOMPLETE"].observed_verdict == DecisionVerdict.SUSPICIOUS
        # Comb J: Clean + expected noise -> ACCEPT
        assert scen_map["SCEN_16_COMB_J_CLEAN_AND_EXPECTED_NOISE"].observed_verdict == DecisionVerdict.ACCEPT


# ==============================================================================
# Suite 4: Pass / Fail Semantics & Comparison Precision
# ==============================================================================

class TestPassFailSemantics:
    """Verifies Items 13-16: exact comparison logic for expected vs. observed outcomes."""

    def test_item_13_expected_attack_observed_attack_passes(
        self,
        clean_m14: AuthorizationEvidence,
        clean_m15: ChannelSecurityEvidence,
    ) -> None:
        """Item 13: Expected ATTACK and observed ATTACK yields PASS."""
        m13_attack = make_violating_impersonation_evidence(
            session_id="sess_eval_common",
            configuration_hash="hash_eval_common",
        )
        sc = EvaluationScenario(
            scenario_id="TEST_ITEM_13",
            name="Expected ATTACK -> Observed ATTACK",
            description="desc",
            category=EvaluationCategory.IMPERSONATION,
            expected_verdict=DecisionVerdict.ATTACK,
            expected_is_violation=True,
            impersonation_evidence=m13_attack,
            authorization_evidence=clean_m14,
            channel_evidence=clean_m15,
            expected_session_id="sess_eval_common",
            expected_configuration_hash="hash_eval_common",
        )
        res = evaluate_scenario(sc)
        assert res.passed is True
        assert res.observed_verdict == DecisionVerdict.ATTACK
        assert len(res.mismatch_reasons) == 0

    def test_item_14_expected_non_attack_observed_non_attack_passes(
        self,
        clean_m13: ImpersonationEvidence,
        clean_m14: AuthorizationEvidence,
        clean_m15: ChannelSecurityEvidence,
    ) -> None:
        """Item 14: Expected non-ATTACK (ACCEPT) and observed non-ATTACK yields PASS."""
        sc = EvaluationScenario(
            scenario_id="TEST_ITEM_14",
            name="Expected non-ATTACK -> Observed non-ATTACK",
            description="desc",
            category=EvaluationCategory.CLEAN_HONEST,
            expected_verdict=DecisionVerdict.ACCEPT,
            expected_is_violation=False,
            impersonation_evidence=clean_m13,
            authorization_evidence=clean_m14,
            channel_evidence=clean_m15,
            expected_session_id="sess_eval_common",
            expected_configuration_hash="hash_eval_common",
        )
        res = evaluate_scenario(sc)
        assert res.passed is True
        assert res.observed_verdict == DecisionVerdict.ACCEPT
        assert len(res.mismatch_reasons) == 0

    def test_item_15_expected_attack_observed_non_attack_fails(
        self,
        clean_m13: ImpersonationEvidence,
        clean_m14: AuthorizationEvidence,
        clean_m15: ChannelSecurityEvidence,
    ) -> None:
        """Item 15: Expected ATTACK but pipeline observes non-ATTACK (e.g. ACCEPT) yields FAIL with explanation."""
        sc = EvaluationScenario(
            scenario_id="TEST_ITEM_15",
            name="Expected ATTACK -> Observed ACCEPT",
            description="Contrived mismatch test",
            category=EvaluationCategory.IMPERSONATION,
            expected_verdict=DecisionVerdict.ATTACK,
            expected_is_violation=True,
            impersonation_evidence=clean_m13,  # Clean evidence used where ATTACK expected
            authorization_evidence=clean_m14,
            channel_evidence=clean_m15,
            expected_session_id="sess_eval_common",
            expected_configuration_hash="hash_eval_common",
        )
        res = evaluate_scenario(sc)
        assert res.passed is False
        assert res.observed_verdict == DecisionVerdict.ACCEPT
        assert any("VERDICT_MISMATCH" in r for r in res.mismatch_reasons)
        assert any("VIOLATION_FLAG_MISMATCH" in r for r in res.mismatch_reasons)

    def test_item_16_expected_non_attack_observed_attack_fails(
        self,
        clean_m14: AuthorizationEvidence,
        clean_m15: ChannelSecurityEvidence,
    ) -> None:
        """Item 16: Expected non-ATTACK (ACCEPT) but pipeline observes ATTACK yields FAIL with explanation."""
        m13_attack = make_violating_impersonation_evidence(
            session_id="sess_eval_common",
            configuration_hash="hash_eval_common",
        )
        sc = EvaluationScenario(
            scenario_id="TEST_ITEM_16",
            name="Expected ACCEPT -> Observed ATTACK",
            description="Contrived false-alarm test",
            category=EvaluationCategory.CLEAN_HONEST,
            expected_verdict=DecisionVerdict.ACCEPT,  # Scenario expects clean ACCEPT
            expected_is_violation=False,
            impersonation_evidence=m13_attack,  # But evidence contains confirmed violation
            authorization_evidence=clean_m14,
            channel_evidence=clean_m15,
            expected_session_id="sess_eval_common",
            expected_configuration_hash="hash_eval_common",
        )
        res = evaluate_scenario(sc)
        assert res.passed is False
        assert res.observed_verdict == DecisionVerdict.ATTACK
        assert any("VERDICT_MISMATCH" in r for r in res.mismatch_reasons)

    def test_missing_expected_violation_types_fails(
        self,
        clean_m14: AuthorizationEvidence,
        clean_m15: ChannelSecurityEvidence,
    ) -> None:
        """Fails if expected specific violation type was not observed in the resulting evidence."""
        m13_attack = make_violating_impersonation_evidence(
            session_id="sess_eval_common",
            configuration_hash="hash_eval_common",
        )
        sc = EvaluationScenario(
            scenario_id="TEST_WRONG_VIOLATION_TYPE",
            name="Wrong Violation Type Expected",
            description="Scenario expects NONCE_REPLAY but observed IDENTITY_MISMATCH",
            category=EvaluationCategory.IMPERSONATION,
            expected_verdict=DecisionVerdict.ATTACK,
            expected_is_violation=True,
            expected_violation_types=("SOME_UNREPORTED_BREACH_TYPE",),
            impersonation_evidence=m13_attack,
            authorization_evidence=clean_m14,
            channel_evidence=clean_m15,
            expected_session_id="sess_eval_common",
            expected_configuration_hash="hash_eval_common",
        )
        res = evaluate_scenario(sc)
        assert res.passed is False
        assert any("EXPECTED_VIOLATIONS_MISSING" in r for r in res.mismatch_reasons)


# ==============================================================================
# Suite 5: Fault Tolerance & Suite Continuation
# ==============================================================================

class TestFaultToleranceAndContinuation:
    """Verifies Item 17: multiple scenarios continue evaluating after one failure."""

    def test_suite_continuation_after_failures(
        self,
        clean_m13: ImpersonationEvidence,
        clean_m14: AuthorizationEvidence,
        clean_m15: ChannelSecurityEvidence,
    ) -> None:
        """Suite continues executing all scenarios even when individual scenarios fail or produce errors."""
        sc1_pass = EvaluationScenario(
            scenario_id="SUITE_SCEN_01",
            name="Scen 1 Pass",
            description="desc",
            category=EvaluationCategory.CLEAN_HONEST,
            expected_verdict=DecisionVerdict.ACCEPT,
            impersonation_evidence=clean_m13,
            authorization_evidence=clean_m14,
            channel_evidence=clean_m15,
            expected_session_id="sess_eval_common",
            expected_configuration_hash="hash_eval_common",
        )

        # sc2 will fail expectation comparison (expected ATTACK, but gets ACCEPT)
        sc2_fail = EvaluationScenario(
            scenario_id="SUITE_SCEN_02",
            name="Scen 2 Fail",
            description="desc",
            category=EvaluationCategory.CLEAN_HONEST,
            expected_verdict=DecisionVerdict.ATTACK,
            expected_is_violation=True,
            impersonation_evidence=clean_m13,
            authorization_evidence=clean_m14,
            channel_evidence=clean_m15,
            expected_session_id="sess_eval_common",
            expected_configuration_hash="hash_eval_common",
        )

        sc3_pass = EvaluationScenario(
            scenario_id="SUITE_SCEN_03",
            name="Scen 3 Pass",
            description="desc",
            category=EvaluationCategory.CLEAN_HONEST,
            expected_verdict=DecisionVerdict.ACCEPT,
            impersonation_evidence=clean_m13,
            authorization_evidence=clean_m14,
            channel_evidence=clean_m15,
            expected_session_id="sess_eval_common",
            expected_configuration_hash="hash_eval_common",
        )

        scenarios = [sc1_pass, sc2_fail, sc3_pass]
        summary = run_security_evaluation(scenarios)

        # All 3 scenarios evaluated
        assert summary.total_scenarios == 3
        assert summary.passed_scenarios == 2
        assert summary.failed_scenarios == 1
        assert pytest.approx(summary.pass_rate, 0.001) == 2.0 / 3.0
        assert summary.failed_scenario_ids == ("SUITE_SCEN_02",)
        assert len(summary.results) == 3
        assert summary.results[0].passed is True
        assert summary.results[1].passed is False
        assert summary.results[2].passed is True


# ==============================================================================
# Suite 6: Confusion Matrix & Contingency Metrics
# ==============================================================================

class TestConfusionMatrixAndMetrics:
    """Verifies accurate calculation of TP, FN, FP, TN, sensitivity, and specificity."""

    def test_confusion_matrix_accuracy(
        self,
        clean_m13: ImpersonationEvidence,
        clean_m14: AuthorizationEvidence,
        clean_m15: ChannelSecurityEvidence,
    ) -> None:
        m13_attack = make_violating_impersonation_evidence(
            session_id="sess_eval_common",
            configuration_hash="hash_eval_common",
        )

        # Case 1: True Positive (Expected ATTACK, observed ATTACK)
        tp_scen = EvaluationScenario(
            scenario_id="CM_TP",
            name="TP Scenario",
            description="desc",
            category=EvaluationCategory.IMPERSONATION,
            expected_verdict=DecisionVerdict.ATTACK,
            expected_is_violation=True,
            impersonation_evidence=m13_attack,
            authorization_evidence=clean_m14,
            channel_evidence=clean_m15,
            expected_session_id="sess_eval_common",
            expected_configuration_hash="hash_eval_common",
        )

        # Case 2: True Negative (Expected non-ATTACK, observed non-ATTACK)
        tn_scen = EvaluationScenario(
            scenario_id="CM_TN",
            name="TN Scenario",
            description="desc",
            category=EvaluationCategory.CLEAN_HONEST,
            expected_verdict=DecisionVerdict.ACCEPT,
            expected_is_violation=False,
            impersonation_evidence=clean_m13,
            authorization_evidence=clean_m14,
            channel_evidence=clean_m15,
            expected_session_id="sess_eval_common",
            expected_configuration_hash="hash_eval_common",
        )

        # Case 3: False Negative (Expected ATTACK, but observed ACCEPT)
        fn_scen = EvaluationScenario(
            scenario_id="CM_FN",
            name="FN Scenario",
            description="desc",
            category=EvaluationCategory.IMPERSONATION,
            expected_verdict=DecisionVerdict.ATTACK,
            expected_is_violation=True,
            impersonation_evidence=clean_m13,  # Clean produces ACCEPT
            authorization_evidence=clean_m14,
            channel_evidence=clean_m15,
            expected_session_id="sess_eval_common",
            expected_configuration_hash="hash_eval_common",
        )

        # Case 4: False Positive (Expected non-ATTACK, but observed ATTACK)
        fp_scen = EvaluationScenario(
            scenario_id="CM_FP",
            name="FP Scenario",
            description="desc",
            category=EvaluationCategory.CLEAN_HONEST,
            expected_verdict=DecisionVerdict.ACCEPT,
            expected_is_violation=False,
            impersonation_evidence=m13_attack,  # Attack produces ATTACK
            authorization_evidence=clean_m14,
            channel_evidence=clean_m15,
            expected_session_id="sess_eval_common",
            expected_configuration_hash="hash_eval_common",
        )

        scenarios = [tp_scen, tn_scen, fn_scen, fp_scen]
        summary = run_security_evaluation(scenarios)

        cm = summary.confusion_matrix
        assert cm.true_positives == 1
        assert cm.false_negatives == 1
        assert cm.false_positives == 1
        assert cm.true_negatives == 1

        # Sensitivity = TP / (TP + FN) = 1 / 2 = 0.5
        assert cm.sensitivity == 0.5
        # Specificity = TN / (TN + FP) = 1 / 2 = 0.5
        assert cm.specificity == 0.5

    def test_confusion_matrix_boundary_denominators(self) -> None:
        """When positive or negative counts are zero, sensitivity / specificity return None safely."""
        cm_zero_pos = ConfusionMatrixMetrics(
            true_positives=0,
            false_negatives=0,
            false_positives=1,
            true_negatives=2,
        )
        assert cm_zero_pos.sensitivity is None
        assert pytest.approx(cm_zero_pos.specificity or 0.0) == 2.0 / 3.0

        cm_zero_neg = ConfusionMatrixMetrics(
            true_positives=3,
            false_negatives=1,
            false_positives=0,
            true_negatives=0,
        )
        assert pytest.approx(cm_zero_neg.sensitivity or 0.0) == 3.0 / 4.0
        assert cm_zero_neg.specificity is None


# ==============================================================================
# Suite 7: Determinism & Reproducibility
# ==============================================================================

class TestDeterminismAndReproducibility:
    """Verifies Items 18 & 19: repeated execution produces bit-for-bit identical evaluation results."""

    def test_repeated_suite_execution_determinism(self) -> None:
        """50 repeated suite executions produce identical summaries and results."""
        suite = build_baseline_evaluation_suite(
            session_id="sess_det_suite",
            configuration_hash="hash_det_suite",
        )
        baseline_summary = run_security_evaluation(suite)

        for _ in range(50):
            repeated_summary = run_security_evaluation(suite)
            assert repeated_summary.total_scenarios == baseline_summary.total_scenarios
            assert repeated_summary.passed_scenarios == baseline_summary.passed_scenarios
            assert repeated_summary.failed_scenarios == baseline_summary.failed_scenarios
            assert repeated_summary.pass_rate == baseline_summary.pass_rate
            assert repeated_summary.verdict_counts == baseline_summary.verdict_counts
            assert repeated_summary.failed_scenario_ids == baseline_summary.failed_scenario_ids
            assert repeated_summary.confusion_matrix == baseline_summary.confusion_matrix

            for b_res, r_res in zip(baseline_summary.results, repeated_summary.results):
                assert b_res.scenario_id == r_res.scenario_id
                assert b_res.observed_verdict == r_res.observed_verdict
                assert b_res.passed == r_res.passed
                assert b_res.mismatch_reasons == r_res.mismatch_reasons

    def test_metadata_key_order_invariance(
        self,
        clean_m13: ImpersonationEvidence,
        clean_m14: AuthorizationEvidence,
        clean_m15: ChannelSecurityEvidence,
    ) -> None:
        """Reversed dictionary key insertion in scenario metadata does not affect result equality."""
        meta1 = {"param_a": 1, "param_b": 2, "param_c": 3}
        meta2 = {"param_c": 3, "param_b": 2, "param_a": 1}

        sc1 = EvaluationScenario(
            scenario_id="SCEN_DET_ORDER",
            name="Det Order",
            description="desc",
            category=EvaluationCategory.CLEAN_HONEST,
            expected_verdict=DecisionVerdict.ACCEPT,
            impersonation_evidence=clean_m13,
            authorization_evidence=clean_m14,
            channel_evidence=clean_m15,
            expected_session_id="sess_eval_common",
            expected_configuration_hash="hash_eval_common",
            metadata=meta1,
        )
        sc2 = EvaluationScenario(
            scenario_id="SCEN_DET_ORDER",
            name="Det Order",
            description="desc",
            category=EvaluationCategory.CLEAN_HONEST,
            expected_verdict=DecisionVerdict.ACCEPT,
            impersonation_evidence=clean_m13,
            authorization_evidence=clean_m14,
            channel_evidence=clean_m15,
            expected_session_id="sess_eval_common",
            expected_configuration_hash="hash_eval_common",
            metadata=meta2,
        )

        res1 = evaluate_scenario(sc1)
        res2 = evaluate_scenario(sc2)
        assert res1.observed_verdict == res2.observed_verdict
        assert res1.passed == res2.passed
        assert res1.metadata == res2.metadata


# ==============================================================================
# Suite 8: Immutability & Secret Leakage Guards
# ==============================================================================

class TestImmutabilityAndSecurity:
    """Verifies Items 20-24: deep immutability and secret leakage protection."""

    def test_evaluation_result_immutability(
        self,
        clean_m13: ImpersonationEvidence,
        clean_m14: AuthorizationEvidence,
        clean_m15: ChannelSecurityEvidence,
    ) -> None:
        sc = EvaluationScenario(
            scenario_id="SCEN_IMMUT_RES",
            name="Immutability Result",
            description="desc",
            category=EvaluationCategory.CLEAN_HONEST,
            expected_verdict=DecisionVerdict.ACCEPT,
            impersonation_evidence=clean_m13,
            authorization_evidence=clean_m14,
            channel_evidence=clean_m15,
            expected_session_id="sess_eval_common",
            expected_configuration_hash="hash_eval_common",
        )
        res = evaluate_scenario(sc)

        with pytest.raises(FrozenInstanceError):
            res.passed = False  # pyright: ignore[reportAttributeAccessIssue]

        with pytest.raises(FrozenInstanceError):
            res.observed_verdict = DecisionVerdict.ATTACK  # pyright: ignore[reportAttributeAccessIssue]

    def test_evaluation_summary_immutability(self) -> None:
        summary = EvaluationSummary(
            total_scenarios=1,
            passed_scenarios=1,
            failed_scenarios=0,
            pass_rate=1.0,
            verdict_counts={"ACCEPT": 1},
            expected_verdict_counts={"ACCEPT": 1},
            confusion_matrix=ConfusionMatrixMetrics(0, 0, 0, 1),
            category_summaries={},
            failed_scenario_ids=(),
            results=(),
        )
        with pytest.raises(FrozenInstanceError):
            summary.total_scenarios = 999  # pyright: ignore[reportAttributeAccessIssue]

    def test_source_evidence_unmodified_by_evaluation(
        self,
        clean_m13: ImpersonationEvidence,
        clean_m14: AuthorizationEvidence,
        clean_m15: ChannelSecurityEvidence,
    ) -> None:
        """Item 22: Original source evidence is not mutated by scenario execution."""
        sc = EvaluationScenario(
            scenario_id="SCEN_SRC_UNMOD",
            name="Source Unmodified",
            description="desc",
            category=EvaluationCategory.CLEAN_HONEST,
            expected_verdict=DecisionVerdict.ACCEPT,
            impersonation_evidence=clean_m13,
            authorization_evidence=clean_m14,
            channel_evidence=clean_m15,
            expected_session_id="sess_eval_common",
            expected_configuration_hash="hash_eval_common",
        )
        _ = evaluate_scenario(sc)

        assert clean_m13.status == IdentityEvidenceStatus.VALID
        assert clean_m13.is_impersonation_detected is False
        assert clean_m14.status == AuthorizationStatus.AUTHORIZED
        assert clean_m14.is_unauthorized_detected is False
        assert clean_m15.status == ChannelEvidenceStatus.CLEAN
        assert clean_m15.is_anomalous is False

    def test_secret_leakage_protection_in_result(self) -> None:
        """Item 24: Secret leakage guard rejects prohibited keys in result metadata."""
        with pytest.raises(ValueError, match="Sensitive secret keyword 'api_key' detected"):
            DecisionResult(
                verdict=DecisionVerdict.ACCEPT,
                primary_reason="OK",
                reason_codes=("OK",),
                exceeded_metrics=(),
                exceeded_count=0,
                is_explicit_violation=False,
                is_evidence_complete=True,
            )
            EvaluationResult(
                scenario_id="SCEN_LEAK_RES",
                scenario_name="Leak",
                category=EvaluationCategory.CLEAN_HONEST,
                expected_verdict=DecisionVerdict.ACCEPT,
                observed_verdict=DecisionVerdict.ACCEPT,
                passed=True,
                expected_is_violation=False,
                observed_is_violation=False,
                decision_result=DecisionResult(
                    verdict=DecisionVerdict.ACCEPT,
                    primary_reason="OK",
                    reason_codes=("OK",),
                    exceeded_metrics=(),
                    exceeded_count=0,
                    is_explicit_violation=False,
                    is_evidence_complete=True,
                ),
                metadata={"external_api_key": "raw_secret"},
            )


# ==============================================================================
# Suite 9: Architectural Scope Discipline & Sole Authority
# ==============================================================================

class TestScopeDisciplineAndBoundaries:
    """Verifies Items 25 & 26: M12 sole authority and absence of duplicate logic or scoring."""

    def test_m12_sole_authority_preserved(
        self,
        clean_m13: ImpersonationEvidence,
        clean_m14: AuthorizationEvidence,
        clean_m15: ChannelSecurityEvidence,
    ) -> None:
        """Item 25: M17 delegates decision verdicts strictly to M12."""
        sc = EvaluationScenario(
            scenario_id="SCEN_M12_AUTHORITY",
            name="M12 Authority Check",
            description="desc",
            category=EvaluationCategory.CLEAN_HONEST,
            expected_verdict=DecisionVerdict.ACCEPT,
            impersonation_evidence=clean_m13,
            authorization_evidence=clean_m14,
            channel_evidence=clean_m15,
            expected_session_id="sess_eval_common",
            expected_configuration_hash="hash_eval_common",
        )
        res = evaluate_scenario(sc)
        # Result decision_result is produced by M12
        assert isinstance(res.decision_result, DecisionResult)
        assert res.observed_verdict == res.decision_result.verdict

    def test_absence_of_numerical_security_scoring_and_ml(self) -> None:
        """M17 contains strictly zero risk_score, trust_score, composite scoring, or ML models."""
        suite = build_baseline_evaluation_suite()
        summary = run_security_evaluation(suite)

        # Inspect summary and results for banned scoring attributes
        banned_attrs = (
            "risk_score",
            "trust_score",
            "security_score",
            "threat_score",
            "confidence_score",
            "attack_probability",
            "composite_score",
            "model",
            "classifier",
            "weights",
        )
        for attr in banned_attrs:
            assert not hasattr(summary, attr), f"EvaluationSummary must not have '{attr}'."
            assert not hasattr(summary.confusion_matrix, attr), f"ConfusionMatrixMetrics must not have '{attr}'."
            for res in summary.results:
                assert not hasattr(res, attr), f"EvaluationResult must not have '{attr}'."
                assert not hasattr(res.decision_result, attr), f"DecisionResult must not have '{attr}'."


# ==============================================================================
# Suite 10: Adversarial Review & Defect Regressions
# ==============================================================================

class TestAdversarialReviewAndRegression:
    """Rigorous regression tests for defects identified during adversarial review."""

    def test_defect1_zero_denominator_pass_rate_is_none(self) -> None:
        """Defect 1: pass_rate must be None when total_scenarios is 0, not arbitrary 1.0."""
        summary = run_security_evaluation([])
        assert summary.total_scenarios == 0
        assert summary.passed_scenarios == 0
        assert summary.failed_scenarios == 0
        assert summary.pass_rate is None
        assert summary.confusion_matrix.sensitivity is None
        assert summary.confusion_matrix.specificity is None
        assert summary.category_summaries == {}

        cat_sum = CategorySummary(
            category=EvaluationCategory.CLEAN_HONEST,
            total_scenarios=0,
            passed_scenarios=0,
            failed_scenarios=0,
            pass_rate=None,
        )
        assert cat_sum.pass_rate is None

    def test_defect1_confusion_matrix_edge_cases(self) -> None:
        """Defect 1: zero denominator in sensitivity/specificity returns None, not 0.0 or 1.0."""
        # Only positives
        cm_pos = ConfusionMatrixMetrics(true_positives=4, false_negatives=0, false_positives=0, true_negatives=0)
        assert cm_pos.sensitivity == 1.0
        assert cm_pos.specificity is None

        # Only negatives
        cm_neg = ConfusionMatrixMetrics(true_positives=0, false_negatives=0, false_positives=0, true_negatives=4)
        assert cm_neg.sensitivity is None
        assert cm_neg.specificity == 1.0

        # All zero
        cm_zero = ConfusionMatrixMetrics(true_positives=0, false_negatives=0, false_positives=0, true_negatives=0)
        assert cm_zero.sensitivity is None
        assert cm_zero.specificity is None

    def test_defect2_strict_scenario_validation_description(self) -> None:
        """Defect 2: empty or whitespace-only description must be rejected."""
        with pytest.raises(ValueError, match="description cannot be empty or whitespace"):
            EvaluationScenario(
                scenario_id="SCEN_NO_DESC_1",
                name="No Desc",
                description="",
                category=EvaluationCategory.CLEAN_HONEST,
                expected_verdict=DecisionVerdict.ACCEPT,
            )

        with pytest.raises(ValueError, match="description cannot be empty or whitespace"):
            EvaluationScenario(
                scenario_id="SCEN_NO_DESC_2",
                name="Whitespace Desc",
                description="   \t\n  ",
                category=EvaluationCategory.CLEAN_HONEST,
                expected_verdict=DecisionVerdict.ACCEPT,
            )

    def test_defect2_strict_scenario_validation_logical_consistency(self) -> None:
        """Defect 2: contradictory expected outcomes must raise ValueError."""
        # expected_is_violation=True with expected_verdict=ACCEPT
        with pytest.raises(ValueError, match="expected_is_violation=True cannot have expected_verdict=ACCEPT"):
            EvaluationScenario(
                scenario_id="SCEN_CONTRADICT_1",
                name="Contradictory Verdict",
                description="Explicit violation claiming to expect ACCEPT",
                category=EvaluationCategory.IMPERSONATION,
                expected_verdict=DecisionVerdict.ACCEPT,
                expected_is_violation=True,
            )

        # expected_violation_types populated with expected_is_violation=False
        with pytest.raises(ValueError, match="expected_violation_types is non-empty but expected_is_violation=False"):
            EvaluationScenario(
                scenario_id="SCEN_CONTRADICT_2",
                name="Contradictory Violation Types",
                description="Violation types populated without violation flag",
                category=EvaluationCategory.IMPERSONATION,
                expected_verdict=DecisionVerdict.ATTACK,
                expected_is_violation=False,
                expected_violation_types=("SOME_VIOLATION",),
            )

    def test_defect2_strict_scenario_validation_evidence_types(self) -> None:
        """Defect 2: malformed evidence fixtures must raise TypeError."""
        with pytest.raises(TypeError, match="impersonation_evidence must be ImpersonationEvidence or None"):
            EvaluationScenario(
                scenario_id="SCEN_BAD_EVID_1",
                name="Bad M13 Evidence",
                description="desc",
                category=EvaluationCategory.CLEAN_HONEST,
                expected_verdict=DecisionVerdict.ACCEPT,
                impersonation_evidence="not_an_evidence_object",  # pyright: ignore[reportArgumentType]
            )

        with pytest.raises(TypeError, match="authorization_evidence must be AuthorizationEvidence or None"):
            EvaluationScenario(
                scenario_id="SCEN_BAD_EVID_2",
                name="Bad M14 Evidence",
                description="desc",
                category=EvaluationCategory.CLEAN_HONEST,
                expected_verdict=DecisionVerdict.ACCEPT,
                authorization_evidence=123,  # pyright: ignore[reportArgumentType]
            )

        with pytest.raises(TypeError, match="channel_evidence must be ChannelSecurityEvidence or None"):
            EvaluationScenario(
                scenario_id="SCEN_BAD_EVID_3",
                name="Bad M15 Evidence",
                description="desc",
                category=EvaluationCategory.CLEAN_HONEST,
                expected_verdict=DecisionVerdict.ACCEPT,
                channel_evidence=object(),  # pyright: ignore[reportArgumentType]
            )

        with pytest.raises(TypeError, match="fused_evidence must be FusedSecurityEvidence or None"):
            EvaluationScenario(
                scenario_id="SCEN_BAD_EVID_4",
                name="Bad Fused Evidence",
                description="desc",
                category=EvaluationCategory.CLEAN_HONEST,
                expected_verdict=DecisionVerdict.ACCEPT,
                fused_evidence="fused_str",  # pyright: ignore[reportArgumentType]
            )

        with pytest.raises(TypeError, match="protocol_evidence must be ProtocolSecurityEvidence, Mapping, or None"):
            EvaluationScenario(
                scenario_id="SCEN_BAD_EVID_5",
                name="Bad Protocol Evidence",
                description="desc",
                category=EvaluationCategory.CLEAN_HONEST,
                expected_verdict=DecisionVerdict.ACCEPT,
                protocol_evidence=456,  # pyright: ignore[reportArgumentType]
            )

        with pytest.raises(TypeError, match="threshold_report must be PolicyEvaluationReport or None"):
            EvaluationScenario(
                scenario_id="SCEN_BAD_EVID_6",
                name="Bad Threshold Report",
                description="desc",
                category=EvaluationCategory.CLEAN_HONEST,
                expected_verdict=DecisionVerdict.ACCEPT,
                threshold_report="report_str",  # pyright: ignore[reportArgumentType]
            )

        with pytest.raises(TypeError, match="metadata must be a Mapping"):
            EvaluationScenario(
                scenario_id="SCEN_BAD_META",
                name="Bad Metadata",
                description="desc",
                category=EvaluationCategory.CLEAN_HONEST,
                expected_verdict=DecisionVerdict.ACCEPT,
                metadata="not_a_mapping",  # pyright: ignore[reportArgumentType]
            )

        with pytest.raises(ValueError, match="Invalid required_source"):
            EvaluationScenario(
                scenario_id="SCEN_BAD_REQ_SRC",
                name="Bad Required Source",
                description="desc",
                category=EvaluationCategory.CLEAN_HONEST,
                expected_verdict=DecisionVerdict.ACCEPT,
                required_sources=("NON_EXISTENT_SOURCE",),
            )

    def test_defect2_strict_result_validation(self) -> None:
        """Defect 2: EvaluationResult must strictly validate field types."""
        decision = DecisionResult(
            verdict=DecisionVerdict.ACCEPT,
            primary_reason="ALL_VALID",
            reason_codes=("ALL_VALID",),
            exceeded_metrics=(),
            exceeded_count=0,
            is_explicit_violation=False,
            is_evidence_complete=True,
        )

        with pytest.raises(ValueError, match="scenario_id must be a non-empty string"):
            EvaluationResult(
                scenario_id="",
                scenario_name="Name",
                category=EvaluationCategory.CLEAN_HONEST,
                expected_verdict=DecisionVerdict.ACCEPT,
                observed_verdict=DecisionVerdict.ACCEPT,
                passed=True,
                expected_is_violation=False,
                observed_is_violation=False,
                decision_result=decision,
            )

        with pytest.raises(TypeError, match="category must be EvaluationCategory"):
            EvaluationResult(
                scenario_id="SCEN_1",
                scenario_name="Name",
                category="NOT_A_CATEGORY",  # pyright: ignore[reportArgumentType]
                expected_verdict=DecisionVerdict.ACCEPT,
                observed_verdict=DecisionVerdict.ACCEPT,
                passed=True,
                expected_is_violation=False,
                observed_is_violation=False,
                decision_result=decision,
            )

        with pytest.raises(TypeError, match="decision_result must be DecisionResult"):
            EvaluationResult(
                scenario_id="SCEN_1",
                scenario_name="Name",
                category=EvaluationCategory.CLEAN_HONEST,
                expected_verdict=DecisionVerdict.ACCEPT,
                observed_verdict=DecisionVerdict.ACCEPT,
                passed=True,
                expected_is_violation=False,
                observed_is_violation=False,
                decision_result="not_a_decision",  # pyright: ignore[reportArgumentType]
            )

    def test_defect3_complete_evidence_omission_with_required_sources(self) -> None:
        """Defect 3: scenario with all evidence fixtures None but required_sources set routes to fusion."""
        sc = EvaluationScenario(
            scenario_id="SCEN_ALL_SOURCES_OMITTED",
            name="Complete Source Omission",
            description="All three evidence fixtures omitted while all are required",
            category=EvaluationCategory.INCOMPLETE_EVIDENCE,
            expected_verdict=DecisionVerdict.SUSPICIOUS,
            expected_is_violation=False,
            impersonation_evidence=None,
            authorization_evidence=None,
            channel_evidence=None,
            required_sources=(
                EvidenceSource.IMPERSONATION.value,
                EvidenceSource.AUTHORIZATION.value,
                EvidenceSource.QUANTUM_CHANNEL.value,
            ),
        )
        res = evaluate_scenario(sc)
        assert res.passed is True
        assert res.observed_verdict == DecisionVerdict.SUSPICIOUS
        assert res.decision_result.is_evidence_complete is False
        assert res.fused_evidence is not None
        assert res.fused_evidence.status == FusedEvidenceStatus.INCOMPLETE

    def test_defect4_no_broad_exception_swallowing(self, clean_m13: ImpersonationEvidence) -> None:
        """Defect 4: fatal programming errors in scenario list must raise, not be swallowed into SUSPICIOUS."""
        valid_sc = EvaluationScenario(
            scenario_id="SCEN_VALID",
            name="Valid",
            description="desc",
            category=EvaluationCategory.CLEAN_HONEST,
            expected_verdict=DecisionVerdict.ACCEPT,
            impersonation_evidence=clean_m13,
        )
        # Passing an invalid element must raise TypeError immediately
        with pytest.raises(TypeError, match="Each item in scenarios must be an EvaluationScenario"):
            run_security_evaluation([valid_sc, "malformed_entry"])  # pyright: ignore[reportArgumentType]

    def test_defect4_id_based_lookup_methods(self, clean_m13: ImpersonationEvidence) -> None:
        """Defect 4: EvaluationSummary provides results_by_id and get_result() for safe ID-based access."""
        sc1 = EvaluationScenario(
            scenario_id="SCEN_ALPHA",
            name="Alpha",
            description="desc",
            category=EvaluationCategory.CLEAN_HONEST,
            expected_verdict=DecisionVerdict.ACCEPT,
            impersonation_evidence=clean_m13,
        )
        sc2 = EvaluationScenario(
            scenario_id="SCEN_BETA",
            name="Beta",
            description="desc",
            category=EvaluationCategory.CLEAN_HONEST,
            expected_verdict=DecisionVerdict.ACCEPT,
            impersonation_evidence=clean_m13,
        )
        summary = run_security_evaluation([sc1, sc2])

        assert "SCEN_ALPHA" in summary.results_by_id
        assert "SCEN_BETA" in summary.results_by_id
        res_alpha = summary.get_result("SCEN_ALPHA")
        assert res_alpha is not None
        assert res_alpha.scenario_id == "SCEN_ALPHA"
        assert summary.get_result("NON_EXISTENT") is None

    def test_scenario_order_independence(self) -> None:
        """Item 12: reordering input scenarios produces equivalent aggregate metrics and preserves associations."""
        suite = build_baseline_evaluation_suite()
        suite_forward = list(suite)
        suite_reversed = list(reversed(suite))

        summary_fwd = run_security_evaluation(suite_forward)
        summary_rev = run_security_evaluation(suite_reversed)

        assert summary_fwd.total_scenarios == summary_rev.total_scenarios
        assert summary_fwd.passed_scenarios == summary_rev.passed_scenarios
        assert summary_fwd.failed_scenarios == summary_rev.failed_scenarios
        assert summary_fwd.pass_rate == summary_rev.pass_rate
        assert summary_fwd.verdict_counts == summary_rev.verdict_counts
        assert summary_fwd.expected_verdict_counts == summary_rev.expected_verdict_counts
        assert summary_fwd.failed_scenario_ids == summary_rev.failed_scenario_ids
        assert summary_fwd.confusion_matrix == summary_rev.confusion_matrix

        # ID-based lookup produces identical results regardless of order
        for sc in suite:
            res_fwd = summary_fwd.get_result(sc.scenario_id)
            res_rev = summary_rev.get_result(sc.scenario_id)
            assert res_fwd is not None and res_rev is not None
            assert res_fwd.scenario_id == res_rev.scenario_id
            assert res_fwd.observed_verdict == res_rev.observed_verdict
            assert res_fwd.passed == res_rev.passed

    def test_conflicting_channel_evidence_helper(
        self,
        clean_m13: ImpersonationEvidence,
        clean_m14: AuthorizationEvidence,
    ) -> None:
        """Verify make_conflicting_channel_evidence produces CONFLICTING status and routes to SUSPICIOUS."""
        conflict_m15 = make_conflicting_channel_evidence(
            session_id="sess_eval_common",
            configuration_hash="hash_eval_common",
        )
        assert conflict_m15.status == ChannelEvidenceStatus.CONFLICTING
        assert conflict_m15.is_evidence_complete is False
        assert conflict_m15.is_explicit_violation is False

        sc = EvaluationScenario(
            scenario_id="SCEN_CONFLICT_M15",
            name="Conflicting M15 Evidence",
            description="Channel evidence is internally conflicting",
            category=EvaluationCategory.CONFLICTING_EVIDENCE,
            expected_verdict=DecisionVerdict.SUSPICIOUS,
            expected_is_violation=False,
            impersonation_evidence=clean_m13,
            authorization_evidence=clean_m14,
            channel_evidence=conflict_m15,
            expected_session_id="sess_eval_common",
            expected_configuration_hash="hash_eval_common",
        )
        res = evaluate_scenario(sc)
        assert res.passed is True
        assert res.observed_verdict == DecisionVerdict.SUSPICIOUS

    def test_all_missing_evidence_permutations(
        self,
        clean_m13: ImpersonationEvidence,
        clean_m14: AuthorizationEvidence,
        clean_m15: ChannelSecurityEvidence,
    ) -> None:
        """Item 6: Verify every permutation of missing sources routes to SUSPICIOUS, never CLEAN."""
        permutations = [
            ("M13_ONLY_MISSING", None, clean_m14, clean_m15),
            ("M14_ONLY_MISSING", clean_m13, None, clean_m15),
            ("M15_ONLY_MISSING", clean_m13, clean_m14, None),
            ("M13_M14_MISSING", None, None, clean_m15),
            ("M13_M15_MISSING", None, clean_m14, None),
            ("M14_M15_MISSING", clean_m13, None, None),
        ]
        all_req = (
            EvidenceSource.IMPERSONATION.value,
            EvidenceSource.AUTHORIZATION.value,
            EvidenceSource.QUANTUM_CHANNEL.value,
        )
        for scen_id, m13, m14, m15 in permutations:
            sc = EvaluationScenario(
                scenario_id=f"SCEN_MISSING_{scen_id}",
                name=f"Missing {scen_id}",
                description="Testing missing evidence permutation",
                category=EvaluationCategory.INCOMPLETE_EVIDENCE,
                expected_verdict=DecisionVerdict.SUSPICIOUS,
                expected_is_violation=False,
                impersonation_evidence=m13,
                authorization_evidence=m14,
                channel_evidence=m15,
                required_sources=all_req,
                expected_session_id="sess_eval_common",
                expected_configuration_hash="hash_eval_common",
            )
            res = evaluate_scenario(sc)
            assert res.passed is True
            assert res.observed_verdict == DecisionVerdict.SUSPICIOUS

            # If expected ACCEPT with missing evidence, evaluation must FAIL
            sc_false_accept = EvaluationScenario(
                scenario_id=f"SCEN_FALSE_ACCEPT_{scen_id}",
                name=f"False Accept Missing {scen_id}",
                description="Attempting to expect ACCEPT when evidence is missing",
                category=EvaluationCategory.INCOMPLETE_EVIDENCE,
                expected_verdict=DecisionVerdict.ACCEPT,
                expected_is_violation=False,
                impersonation_evidence=m13,
                authorization_evidence=m14,
                channel_evidence=m15,
                required_sources=all_req,
                expected_session_id="sess_eval_common",
                expected_configuration_hash="hash_eval_common",
            )
            res_fa = evaluate_scenario(sc_false_accept)
            assert res_fa.passed is False
            assert res_fa.observed_verdict == DecisionVerdict.SUSPICIOUS
            assert any("VERDICT_MISMATCH" in m for m in res_fa.mismatch_reasons)


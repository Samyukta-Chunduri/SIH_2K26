"""Tests for Teleportation Verification (Milestone M7).

Comprehensive validation and bug-hunting test suite for M7:
1. Quantum state overlap fidelity calculation (pure state conjugate inner product, global phase invariance).
2. TeleportationVerificationResult immutability and invariant constraints.
3. Verification of all 6 standard Pauli eigenstates (|0>, |1>, |+>, |->, |+i>, |-i>) after M6 teleportation.
4. Verification of arbitrary complex superposition states.
5. Rejection of orthogonal, divergent, and perturbed states.
6. Rigorous input validation (empty arrays, wrong dimensions, non-normalized vectors, NaN/Inf, invalid types).
7. Tolerance validation (rejecting negative, NaN, Inf, >= 1.0, non-numeric, boolean).
8. Boundary behavior and edge cases (tolerance = 0, exact threshold boundary F = 1 - eps, F < 1 - eps).
9. Mathematical property tests (self-fidelity, global phase, orthogonality, bounds, symmetry).
10. Measurement distribution comparison across Z, X, Y bases and proof of basis-dependent limitations.
11. Bit-for-bit verification determinism.
12. Cross-validation against Qiskit public quantum_info state_fidelity API.
13. Dedicated bug-catching sensitivity suite for Bugs A through O.
14. Strict M7 scope enforcement (no noise, attacks, thresholds, signatures, or ML).
"""

from __future__ import annotations

import math
from typing import Any
import numpy as np
import pytest
from qiskit.quantum_info import Statevector, state_fidelity

from src.quantum.measurements import projective_probabilities
from src.quantum.states import (
    STATE_0,
    STATE_1,
    STATE_MINUS,
    STATE_MINUS_I,
    STATE_PLUS,
    STATE_PLUS_I,
    QubitState,
    get_standard_state,
)
from src.quantum.teleportation import (
    TeleportationResult,
    calculate_teleportation_fidelity,
    simulate_teleportation_circuit,
    simulate_teleportation_mathematical,
)
from src.quantum.teleportation_verification import (
    DEFAULT_VERIFICATION_TOLERANCE,
    MeasurementDistributionComparison,
    TeleportationVerificationResult,
    compare_measurement_distributions,
    validate_verification_tolerance,
    verify_teleportation,
    verify_teleportation_result,
)


# ==============================================================================
# 1. Fidelity Calculation & Mathematical Properties
# ==============================================================================

class TestTeleportationFidelityCalculation:
    """Validates the mathematical fidelity computation F = |<a|b>|^2."""

    def test_fidelity_identical_states(self) -> None:
        """Fidelity of identical states must be exactly 1.0."""
        for state in (STATE_0, STATE_1, STATE_PLUS, STATE_MINUS, STATE_PLUS_I, STATE_MINUS_I):
            fid = calculate_teleportation_fidelity(state, state)
            assert np.isclose(fid, 1.0, atol=1e-12)

    def test_fidelity_orthogonal_states(self) -> None:
        """Fidelity of orthogonal states must be exactly 0.0."""
        assert calculate_teleportation_fidelity(STATE_0, STATE_1) == 0.0
        assert calculate_teleportation_fidelity(STATE_PLUS, STATE_MINUS) == 0.0
        assert calculate_teleportation_fidelity(STATE_PLUS_I, STATE_MINUS_I) == 0.0

    def test_fidelity_non_trivial_overlap(self) -> None:
        """Fidelity with known non-trivial overlap must equal |<a|b>|^2."""
        # |psi> = cos(pi/6)|0> + sin(pi/6)|1> = sqrt(3)/2 |0> + 1/2 |1>
        psi = np.array([np.sqrt(3) / 2.0, 0.5], dtype=np.complex128)
        # Overlap with |0> is sqrt(3)/2, so fidelity must be (sqrt(3)/2)^2 = 3/4 = 0.75
        fid_0 = calculate_teleportation_fidelity(STATE_0, psi)
        assert np.isclose(fid_0, 0.75, atol=1e-12)

        # Overlap with |1> is 0.5, so fidelity must be 0.5^2 = 0.25
        fid_1 = calculate_teleportation_fidelity(STATE_1, psi)
        assert np.isclose(fid_1, 0.25, atol=1e-12)

    def test_fidelity_complex_conjugation_required(self) -> None:
        """Fidelity must use conjugate inner product np.vdot, not unconjugated np.dot.

        For |psi_1> = (|0> + i|1>)/sqrt(2) = |+i> and |psi_2> = (|0> - i|1>)/sqrt(2) = |-i>:
        <psi_1 | psi_2> = (1/2)(1*1 + (-i)*(-i)) = (1/2)(1 - 1) = 0.0 (orthogonal).
        Unconjugated dot would compute (1/2)(1*1 + (i)*(-i)) = (1/2)(1 + 1) = 1.0 (completely wrong).
        """
        fid = calculate_teleportation_fidelity(STATE_PLUS_I, STATE_MINUS_I)
        assert fid == 0.0

        # Contrast with raw unconjugated dot
        raw_dot_sq = abs(np.dot(STATE_PLUS_I, STATE_MINUS_I)) ** 2
        assert np.isclose(raw_dot_sq, 1.0, atol=1e-12)
        assert fid != raw_dot_sq

    def test_fidelity_global_phase_invariance(self) -> None:
        """Fidelity must be strictly invariant under arbitrary global phase factors."""
        psi = np.array([1.0 / np.sqrt(3.0), np.sqrt(2.0 / 3.0) * 1j], dtype=np.complex128)

        phases = [
            math.pi / 4.0,
            math.pi / 2.0,
            math.pi,
            3.0 * math.pi / 2.0,
            2.0 * math.pi / 3.0,
        ]
        for theta in phases:
            shifted = np.exp(1j * theta) * psi
            fid = calculate_teleportation_fidelity(psi, shifted)
            assert np.isclose(fid, 1.0, atol=1e-12)


# ==============================================================================
# 2. Quantum Fidelity Properties
# ==============================================================================

class TestQuantumFidelityProperties:
    """Property-based verification of quantum pure-state fidelity axioms."""

    def test_property_self_fidelity(self) -> None:
        """Property 1: Self-fidelity F(psi, psi) = 1.0 for all states."""
        rng = np.random.default_rng(seed=123)
        for _ in range(20):
            vec = rng.normal(size=2) + 1j * rng.normal(size=2)
            vec /= np.linalg.norm(vec)
            fid = calculate_teleportation_fidelity(vec, vec)
            assert np.isclose(fid, 1.0, atol=1e-12)

    def test_property_global_phase(self) -> None:
        """Property 2: F(psi, e^(i theta) psi) = 1.0 for any phase theta."""
        rng = np.random.default_rng(seed=456)
        for _ in range(20):
            vec = rng.normal(size=2) + 1j * rng.normal(size=2)
            vec /= np.linalg.norm(vec)
            theta = rng.uniform(0.0, 2.0 * math.pi)
            shifted = np.exp(1j * theta) * vec
            fid = calculate_teleportation_fidelity(vec, shifted)
            assert np.isclose(fid, 1.0, atol=1e-12)

    def test_property_orthogonality(self) -> None:
        """Property 3: <psi | phi> = 0 => F(psi, phi) = 0.0."""
        rng = np.random.default_rng(seed=789)
        for _ in range(20):
            # Construct orthogonal state to [alpha, beta]: [-beta*, alpha*]
            alpha = rng.normal() + 1j * rng.normal()
            beta = rng.normal() + 1j * rng.normal()
            norm = math.sqrt(abs(alpha) ** 2 + abs(beta) ** 2)
            alpha /= norm
            beta /= norm

            psi = np.array([alpha, beta], dtype=np.complex128)
            phi = np.array([-np.conj(beta), np.conj(alpha)], dtype=np.complex128)

            assert np.isclose(np.vdot(psi, phi), 0.0, atol=1e-12)
            fid = calculate_teleportation_fidelity(psi, phi)
            assert fid == 0.0

    def test_property_bounds(self) -> None:
        """Property 4: 0.0 <= F(a, b) <= 1.0 for all normalized state pairs."""
        rng = np.random.default_rng(seed=101)
        for _ in range(50):
            vec_a = rng.normal(size=2) + 1j * rng.normal(size=2)
            vec_a /= np.linalg.norm(vec_a)
            vec_b = rng.normal(size=2) + 1j * rng.normal(size=2)
            vec_b /= np.linalg.norm(vec_b)

            fid = calculate_teleportation_fidelity(vec_a, vec_b)
            assert 0.0 <= fid <= 1.0 + 1e-14

    def test_property_symmetry(self) -> None:
        """Property 5: F(a, b) = F(b, a) for any pure states."""
        rng = np.random.default_rng(seed=202)
        for _ in range(20):
            vec_a = rng.normal(size=2) + 1j * rng.normal(size=2)
            vec_a /= np.linalg.norm(vec_a)
            vec_b = rng.normal(size=2) + 1j * rng.normal(size=2)
            vec_b /= np.linalg.norm(vec_b)

            fid_ab = calculate_teleportation_fidelity(vec_a, vec_b)
            fid_ba = calculate_teleportation_fidelity(vec_b, vec_a)
            assert np.isclose(fid_ab, fid_ba, atol=1e-12)


# ==============================================================================
# 3. Result Dataclass Validation
# ==============================================================================

class TestTeleportationVerificationResult:
    """Validates the TeleportationVerificationResult dataclass."""

    def test_result_immutability(self) -> None:
        """Verification result dataclass must be frozen/immutable."""
        res = verify_teleportation(STATE_0, STATE_0)
        with pytest.raises(Exception):  # FrozenInstanceError
            res.verified = False  # type: ignore[misc]

    def test_result_fields(self) -> None:
        """Verification result must contain all required fields with correct values."""
        res = verify_teleportation(STATE_0, STATE_0, tolerance=1e-5)
        assert res.verified is True
        assert np.isclose(res.fidelity, 1.0, atol=1e-12)
        assert res.tolerance == 1e-5
        assert np.isclose(res.fidelity_threshold, 1.0 - 1e-5, atol=1e-12)
        assert np.allclose(res.input_state, STATE_0)
        assert np.allclose(res.output_state, STATE_0)

    def test_result_post_init_enforcement(self) -> None:
        """Invalid fields passed directly to constructor must raise TypeError/ValueError."""
        with pytest.raises(TypeError, match="verified must be a bool"):
            TeleportationVerificationResult(
                verified="True",  # type: ignore[arg-type]
                fidelity=1.0,
                tolerance=1e-6,
                fidelity_threshold=1.0 - 1e-6,
                input_state=STATE_0,
                output_state=STATE_0,
            )

        with pytest.raises(ValueError, match="fidelity must be in"):
            TeleportationVerificationResult(
                verified=True,
                fidelity=1.5,
                tolerance=1e-6,
                fidelity_threshold=1.0 - 1e-6,
                input_state=STATE_0,
                output_state=STATE_0,
            )

        with pytest.raises(ValueError, match="input_state must have shape"):
            TeleportationVerificationResult(
                verified=True,
                fidelity=1.0,
                tolerance=1e-6,
                fidelity_threshold=1.0 - 1e-6,
                input_state=np.array([1, 0, 0]),
                output_state=STATE_0,
            )


# ==============================================================================
# 4. Verification API & Teleportation Protocol Integration
# ==============================================================================

class TestVerifyTeleportationAPI:
    """Validates the core verify_teleportation and verify_teleportation_result APIs."""

    def test_verify_all_six_pauli_eigenstates_teleportation(self) -> None:
        """Verify that all six standard Pauli eigenstates teleport and verify with F=1.0."""
        states = [STATE_0, STATE_1, STATE_PLUS, STATE_MINUS, STATE_PLUS_I, STATE_MINUS_I]
        branches: list[tuple[int, int]] = [(0, 0), (0, 1), (1, 0), (1, 1)]

        for state in states:
            for branch in branches:
                m_res = simulate_teleportation_mathematical(state, branch=branch)
                v_res = verify_teleportation_result(m_res)

                assert v_res.verified is True
                assert np.isclose(v_res.fidelity, 1.0, atol=1e-12)
                assert v_res.fidelity >= v_res.fidelity_threshold

    def test_verify_arbitrary_complex_state_teleportation(self) -> None:
        """Verify an arbitrary normalized complex superposition state."""
        alpha = 1.0 / math.sqrt(3.0)
        beta = math.sqrt(2.0 / 3.0) * np.exp(1j * math.pi / 4.0)
        psi = np.array([alpha, beta], dtype=np.complex128)

        for branch in ((0, 0), (0, 1), (1, 0), (1, 1)):
            m_res = simulate_teleportation_mathematical(psi, branch=branch)
            v_res = verify_teleportation_result(m_res)

            assert v_res.verified is True
            assert np.isclose(v_res.fidelity, 1.0, atol=1e-12)

    def test_verify_with_string_and_qubit_state_inputs(self) -> None:
        """Accept standard state string labels and QubitState instances."""
        res_str = verify_teleportation("0", "0")
        assert res_str.verified is True

        qs = QubitState(STATE_PLUS)
        res_qs = verify_teleportation(qs, qs)
        assert res_qs.verified is True

    def test_verify_rejection_of_orthogonal_states(self) -> None:
        """Orthogonal output state must fail verification."""
        v_res = verify_teleportation(STATE_0, STATE_1)
        assert v_res.verified is False
        assert v_res.fidelity == 0.0

        v_res_pm = verify_teleportation(STATE_PLUS, STATE_MINUS)
        assert v_res_pm.verified is False
        assert v_res_pm.fidelity == 0.0

    def test_verify_rejection_of_perturbed_state(self) -> None:
        """A slightly perturbed state that falls below 1 - tolerance must fail verification."""
        perturbed = np.array([np.sqrt(0.999), np.sqrt(0.001)], dtype=np.complex128)
        # With strict tolerance 1e-6 (threshold 0.999999), 0.999 must be rejected
        v_res = verify_teleportation(STATE_0, perturbed, tolerance=1e-6)
        assert v_res.verified is False
        assert np.isclose(v_res.fidelity, 0.999, atol=1e-7)

        # With loose tolerance 0.01 (threshold 0.99), 0.999 must be accepted
        v_res_loose = verify_teleportation(STATE_0, perturbed, tolerance=0.01)
        assert v_res_loose.verified is True


# ==============================================================================
# 5. Tolerance Boundaries & Edge Cases
# ==============================================================================

class TestToleranceBoundaryAndEdgeCases:
    """Validates exact numerical boundaries and edge cases for tolerances."""

    def test_tolerance_zero_exact_states(self) -> None:
        """With tolerance = 0.0, exact ideal states must verify without float roundoff failure."""
        v_0 = verify_teleportation(STATE_0, STATE_0, tolerance=0.0)
        assert v_0.verified is True
        assert v_0.fidelity_threshold == 1.0

        v_plus = verify_teleportation(STATE_PLUS, STATE_PLUS, tolerance=0.0)
        assert v_plus.verified is True

        # Complex superposition state
        psi = np.array([1.0 / math.sqrt(3.0), math.sqrt(2.0 / 3.0) * 1j], dtype=np.complex128)
        v_c = verify_teleportation(psi, psi, tolerance=0.0)
        assert v_c.verified is True

    def test_exact_threshold_boundary(self) -> None:
        """States exactly at the threshold F = 1 - eps must pass, states strictly below must fail."""
        eps = 0.1  # threshold = 0.9
        # Construct state with exact fidelity = 0.9: cos(theta)^2 = 0.9
        theta = math.acos(math.sqrt(0.9))
        psi_exact = np.array([math.cos(theta), math.sin(theta)], dtype=np.complex128)

        v_exact = verify_teleportation(STATE_0, psi_exact, tolerance=eps)
        assert v_exact.verified is True
        assert np.isclose(v_exact.fidelity, 0.9, atol=1e-12)

        # State with fidelity strictly below threshold (0.899 < 0.9)
        theta_below = math.acos(math.sqrt(0.899))
        psi_below = np.array([math.cos(theta_below), math.sin(theta_below)], dtype=np.complex128)

        v_below = verify_teleportation(STATE_0, psi_below, tolerance=eps)
        assert v_below.verified is False
        assert np.isclose(v_below.fidelity, 0.899, atol=1e-12)

    def test_small_positive_tolerance(self) -> None:
        """Small positive tolerance (e.g. 1e-9) behaves consistently."""
        v_res = verify_teleportation(STATE_0, STATE_0, tolerance=1e-9)
        assert v_res.verified is True
        assert v_res.tolerance == 1e-9


# ==============================================================================
# 6. Input & Tolerance Validation
# ==============================================================================

class TestInputAndToleranceValidation:
    """Validates error handling on invalid states and tolerances."""

    def test_invalid_state_vectors(self) -> None:
        """Malformed state vectors must raise ValueError or TypeError."""
        # Empty array
        with pytest.raises(ValueError, match="shape"):
            verify_teleportation([], STATE_0)

        # Wrong dimension
        with pytest.raises(ValueError, match="shape"):
            verify_teleportation(np.array([1, 0, 0]), STATE_0)

        # Non-normalized
        with pytest.raises(ValueError, match="not normalized"):
            verify_teleportation(np.array([2.0, 0.0]), STATE_0)

        # NaN
        with pytest.raises(ValueError, match="finite"):
            verify_teleportation(np.array([np.nan, 0.0]), STATE_0)

        # Inf
        with pytest.raises(ValueError, match="finite"):
            verify_teleportation(np.array([np.inf, 0.0]), STATE_0)

        # Invalid type
        with pytest.raises(TypeError):
            verify_teleportation(None, STATE_0)

        # Unknown string label
        with pytest.raises(ValueError, match="Unknown standard state"):
            verify_teleportation("unsupported_state", STATE_0)

    def test_invalid_tolerance_values(self) -> None:
        """Invalid tolerances must raise TypeError or ValueError."""
        # Negative tolerance
        with pytest.raises(ValueError, match="non-negative"):
            validate_verification_tolerance(-1e-6)

        # Tolerance >= 1.0
        with pytest.raises(ValueError, match="strictly less than 1.0"):
            validate_verification_tolerance(1.0)
        with pytest.raises(ValueError, match="strictly less than 1.0"):
            validate_verification_tolerance(2.5)

        # NaN tolerance
        with pytest.raises(ValueError, match="finite"):
            validate_verification_tolerance(float("nan"))

        # Inf tolerance
        with pytest.raises(ValueError, match="finite"):
            validate_verification_tolerance(float("inf"))

        # Boolean tolerance (Python bool inherits from int!)
        with pytest.raises(TypeError, match="numeric float or int"):
            validate_verification_tolerance(True)
        with pytest.raises(TypeError, match="numeric float or int"):
            validate_verification_tolerance(False)

        # String tolerance
        with pytest.raises(TypeError, match="numeric float or int"):
            validate_verification_tolerance("1e-6")

        # None tolerance
        with pytest.raises(TypeError, match="numeric float or int"):
            validate_verification_tolerance(None)

    def test_verify_teleportation_result_type_check(self) -> None:
        """Passing non-TeleportationResult to verify_teleportation_result must raise TypeError."""
        with pytest.raises(TypeError, match="Expected TeleportationResult instance"):
            verify_teleportation_result({"input": STATE_0, "output": STATE_0})  # type: ignore[arg-type]


# ==============================================================================
# 7. Measurement Distribution Comparison Across Bases
# ==============================================================================

class TestMeasurementDistributionComparison:
    """Validates supporting measurement distribution comparison across X, Y, Z bases."""

    def test_measurement_distribution_identical_states(self) -> None:
        """Identical states must have TVD = 0 across all measurement bases."""
        for basis in ("Z", "X", "Y"):
            comp = compare_measurement_distributions(STATE_0, STATE_0, basis=basis)
            assert comp.total_variation_distance == 0.0
            assert comp.max_probability_difference == 0.0
            assert comp.matches_within_tolerance is True

    def test_measurement_distribution_teleported_states(self) -> None:
        """Recovered teleported state must match input state distribution across all bases."""
        psi = np.array([np.sqrt(0.7), np.sqrt(0.3) * 1j], dtype=np.complex128)
        m_res = simulate_teleportation_mathematical(psi, branch=(1, 1))

        for basis in ("Z", "X", "Y"):
            comp = compare_measurement_distributions(psi, m_res.output_state, basis=basis)
            assert np.isclose(comp.total_variation_distance, 0.0, atol=1e-12)
            assert comp.matches_within_tolerance is True

    def test_pairwise_cross_basis_limitations(self) -> None:
        """Every pair of orthogonal Pauli states matches in 2 bases and differs in 1.

        - |0> vs |1>: differs in Z (TVD=1.0), matches in X and Y (both 50/50, TVD=0.0).
        - |+> vs |->: differs in X (TVD=1.0), matches in Z and Y (both 50/50, TVD=0.0).
        - |+i> vs |-i>: differs in Y (TVD=1.0), matches in Z and X (both 50/50, TVD=0.0).
        """
        # |0> vs |1>
        assert compare_measurement_distributions(STATE_0, STATE_1, basis="Z").total_variation_distance == 1.0
        assert compare_measurement_distributions(STATE_0, STATE_1, basis="X").total_variation_distance == 0.0
        assert compare_measurement_distributions(STATE_0, STATE_1, basis="Y").total_variation_distance == 0.0

        # |+> vs |->
        assert compare_measurement_distributions(STATE_PLUS, STATE_MINUS, basis="X").total_variation_distance == 1.0
        assert compare_measurement_distributions(STATE_PLUS, STATE_MINUS, basis="Z").total_variation_distance == 0.0
        assert compare_measurement_distributions(STATE_PLUS, STATE_MINUS, basis="Y").total_variation_distance == 0.0

        # |+i> vs |-i>
        assert compare_measurement_distributions(STATE_PLUS_I, STATE_MINUS_I, basis="Y").total_variation_distance == 1.0
        assert compare_measurement_distributions(STATE_PLUS_I, STATE_MINUS_I, basis="Z").total_variation_distance == 0.0
        assert compare_measurement_distributions(STATE_PLUS_I, STATE_MINUS_I, basis="X").total_variation_distance == 0.0

    def test_invalid_basis_raises_value_error(self) -> None:
        """Unrecognized basis name must raise ValueError."""
        with pytest.raises(ValueError, match="Measurement basis must be 'Z', 'X', or 'Y'"):
            compare_measurement_distributions(STATE_0, STATE_0, basis="Bell")


# ==============================================================================
# 8. Verification Determinism
# ==============================================================================

class TestDeterminism:
    """Verifies that verification is strictly deterministic."""

    def test_deterministic_fidelity_and_verification(self) -> None:
        """Running verification 100 times on identical inputs yields bit-for-bit identical results."""
        psi_in = np.array([np.sqrt(0.8), np.sqrt(0.2)], dtype=np.complex128)
        psi_out = psi_in.copy()

        baseline = verify_teleportation(psi_in, psi_out, tolerance=1e-6)

        for _ in range(100):
            res = verify_teleportation(psi_in, psi_out, tolerance=1e-6)
            assert res.verified == baseline.verified
            assert res.fidelity == baseline.fidelity
            assert res.fidelity_threshold == baseline.fidelity_threshold


# ==============================================================================
# 9. Qiskit Cross-Validation
# ==============================================================================

class TestQiskitCrossValidation:
    """Cross-validates fidelity against public Qiskit APIs."""

    def test_cross_validation_with_qiskit_state_fidelity(self) -> None:
        """M7 fidelity must match Qiskit state_fidelity for random complex states."""
        rng = np.random.default_rng(seed=42)

        for _ in range(10):
            # Generate random normalized state
            vec_a = rng.normal(size=2) + 1j * rng.normal(size=2)
            vec_a /= np.linalg.norm(vec_a)

            vec_b = rng.normal(size=2) + 1j * rng.normal(size=2)
            vec_b /= np.linalg.norm(vec_b)

            our_fid = calculate_teleportation_fidelity(vec_a, vec_b)
            qiskit_fid = float(state_fidelity(Statevector(vec_a), Statevector(vec_b)))

            assert np.isclose(our_fid, qiskit_fid, atol=1e-12)


# ==============================================================================
# 10. Bug-Catching Sensitivity Suite (Bugs A through O)
# ==============================================================================

class TestBugCatchingSensitivity:
    """Sensitivity tests designed specifically to catch subtle implementation defects."""

    def test_bug_a_missing_complex_conjugation(self) -> None:
        """Bug A: inner product computed via np.dot instead of np.vdot."""
        # For |+i> and |-i>, np.dot gives 1.0 while np.vdot gives 0.0
        v_res = verify_teleportation(STATE_PLUS_I, STATE_MINUS_I)
        assert v_res.verified is False, "Bug A detected: conjugation missing!"
        assert v_res.fidelity == 0.0

    def test_bug_b_missing_fidelity_square(self) -> None:
        """Bug B: calculating |<a|b>| instead of |<a|b>|^2.

        For known overlap |<a|b>| = 0.5, fidelity must be 0.25, NOT 0.5.
        """
        psi = np.array([np.sqrt(3) / 2.0, 0.5], dtype=np.complex128)
        fid = calculate_teleportation_fidelity(STATE_1, psi)
        assert np.isclose(fid, 0.25, atol=1e-12), "Bug B detected: overlap was not squared!"
        assert not np.isclose(fid, 0.5, atol=1e-12)

    def test_bug_c_global_phase_incorrectly_rejected(self) -> None:
        """Bug C: rejecting states differing only by global phase factor."""
        psi = np.array([1.0 / np.sqrt(2.0), 1j / np.sqrt(2.0)], dtype=np.complex128)
        for theta in (math.pi / 2.0, math.pi, 3.0 * math.pi / 2.0):
            shifted = np.exp(1j * theta) * psi
            v_res = verify_teleportation(psi, shifted)
            assert v_res.verified is True, f"Bug C detected: global phase {theta} incorrectly rejected!"
            assert np.isclose(v_res.fidelity, 1.0, atol=1e-12)

    def test_bug_d_orthogonal_states_accepted(self) -> None:
        """Bug D: orthogonal states incorrectly accepted as verified."""
        v_res = verify_teleportation(STATE_0, STATE_1)
        assert v_res.verified is False, "Bug D detected: orthogonal states |0> and |1> accepted!"

    def test_bug_e_non_trivial_overlap_calculated_incorrectly(self) -> None:
        """Bug E: non-trivial overlap calculated incorrectly (0 < F < 1)."""
        # Construct state with overlap 0.5 with |0>
        psi = np.array([0.5, np.sqrt(3) / 2.0], dtype=np.complex128)
        fid_0 = calculate_teleportation_fidelity(STATE_0, psi)
        fid_1 = calculate_teleportation_fidelity(STATE_1, psi)
        assert np.isclose(fid_0, 0.25, atol=1e-12), "Bug E detected: incorrect overlap for |0>!"
        assert np.isclose(fid_1, 0.75, atol=1e-12), "Bug E detected: incorrect overlap for |1>!"

    def test_bug_f_hardcoded_fidelity(self) -> None:
        """Bug F: fidelity always returns 1.0 regardless of inputs."""
        psi_a = STATE_0
        psi_b = np.array([np.sqrt(0.8), np.sqrt(0.2)], dtype=np.complex128)
        fid = calculate_teleportation_fidelity(psi_a, psi_b)
        assert np.isclose(fid, 0.8, atol=1e-12)
        assert fid != 1.0, "Bug F detected: fidelity appears hardcoded to 1.0!"

    def test_bug_g_hardcoded_verification_result(self) -> None:
        """Bug G: verify_teleportation always returns verified=True."""
        res_pass = verify_teleportation(STATE_0, STATE_0)
        res_fail = verify_teleportation(STATE_0, STATE_1)
        assert res_pass.verified is True
        assert res_fail.verified is False, "Bug G detected: verification result appears hardcoded!"

    def test_bug_h_malformed_states_accepted(self) -> None:
        """Bug H: malformed states (NaN / Inf) silently accepted."""
        with pytest.raises(ValueError, match="finite"):
            verify_teleportation(np.array([np.nan, 0.0]), STATE_0)
        with pytest.raises(ValueError, match="finite"):
            verify_teleportation(np.array([np.inf, 0.0]), STATE_0)

    def test_bug_i_non_normalized_states_accepted(self) -> None:
        """Bug I: non-normalized states silently accepted."""
        with pytest.raises(ValueError, match="not normalized"):
            verify_teleportation(np.array([2.0, 0.0]), STATE_0)
        with pytest.raises(ValueError, match="not normalized"):
            verify_teleportation(np.array([0.5, 0.5]), STATE_0)

    def test_bug_j_invalid_tolerance_accepted(self) -> None:
        """Bug J: negative, non-finite, or >= 1.0 tolerance accepted."""
        with pytest.raises(ValueError, match="non-negative"):
            verify_teleportation(STATE_0, STATE_0, tolerance=-0.05)
        with pytest.raises(ValueError, match="strictly less than 1.0"):
            verify_teleportation(STATE_0, STATE_0, tolerance=1.0)
        with pytest.raises(ValueError, match="finite"):
            verify_teleportation(STATE_0, STATE_0, tolerance=float("nan"))

    def test_bug_k_wrong_threshold_direction(self) -> None:
        """Bug K: condition implemented as fidelity <= threshold instead of fidelity >= threshold."""
        # For orthogonal states (F = 0.0), a <= threshold bug would return True!
        v_res = verify_teleportation(STATE_0, STATE_1, tolerance=1e-6)
        assert v_res.verified is False, "Bug K detected: threshold direction is reversed!"

    def test_bug_l_input_output_confusion(self) -> None:
        """Bug L: asymmetric test ensuring inputs are not blindly swapped or ignored."""
        alpha = np.sqrt(0.8)
        beta = np.sqrt(0.2)
        state_in = np.array([alpha, beta], dtype=np.complex128)
        state_out = np.array([beta, alpha], dtype=np.complex128)

        v_res = verify_teleportation(state_in, state_out)
        assert np.allclose(v_res.input_state, state_in)
        assert np.allclose(v_res.output_state, state_out)
        assert not np.allclose(v_res.input_state, v_res.output_state)

    def test_bug_m_imaginary_components_silently_discarded(self) -> None:
        """Bug M: Imaginary components silently discarded.

        For |+i> = (|0> + i|1>)/sqrt(2) and |-> = (|0> - |1>)/sqrt(2):
        <+i | -> = (1/2)(1*1 + (-i)*(-1)) = (1/2)(1 + i)
        F = |(1 + i)/2|^2 = 2/4 = 0.5.
        If imaginary parts were discarded:
        real(|+i>) = [1/sqrt(2), 0]
        real(|->) = [1/sqrt(2), -1/sqrt(2)]
        discarded overlap = 1/2, squared = 0.25 != 0.5!
        """
        fid = calculate_teleportation_fidelity(STATE_PLUS_I, STATE_MINUS)
        assert np.isclose(fid, 0.5, atol=1e-12), "Bug M detected: imaginary components were discarded!"

    def test_bug_n_wrong_state_dimension_accepted(self) -> None:
        """Bug N: Wrong state vector dimension accepted (e.g. 1D, 3D, or 4D states)."""
        with pytest.raises(ValueError, match="shape"):
            verify_teleportation(np.array([1.0]), STATE_0)
        with pytest.raises(ValueError, match="shape"):
            verify_teleportation(np.array([1.0, 0.0, 0.0]), STATE_0)
        with pytest.raises(ValueError, match="shape"):
            verify_teleportation(np.array([0.5, 0.5, 0.5, 0.5]), STATE_0)

    def test_bug_o_one_basis_measurement_equality_mistaken_for_state_equality(self) -> None:
        """Bug O: declaring states equivalent based only on a single basis measurement match."""
        # |+> and |-> match in Z-basis TVD (both 50/50) but are orthogonal in state space (F = 0.0)
        comp = compare_measurement_distributions(STATE_PLUS, STATE_MINUS, basis="Z")
        assert comp.matches_within_tolerance is True
        v_res = verify_teleportation(STATE_PLUS, STATE_MINUS)
        assert v_res.verified is False, "Bug O detected: state verification must rely on fidelity!"


# ==============================================================================
# 11. Scope Enforcement
# ==============================================================================

class TestScopeEnforcement:
    """Strictly enforces divide-and-conquer boundaries (no M8+ features)."""

    def test_no_m8_plus_features_in_verification_module(self) -> None:
        """Ensure no noise, attack, signature, or ML modules are present in M7."""
        import src.quantum.teleportation_verification as tv

        forbidden_names = [
            "noise",
            "depolarizing",
            "bit_flip",
            "phase_flip",
            "qber",
            "attack",
            "forgery",
            "replay",
            "impersonation",
            "signature",
            "sign",
            "qds",
            "threshold_engine",
            "decision_engine",
            "fusion",
            "blockchain",
            "machine_learning",
            "neural_network",
        ]

        for name in forbidden_names:
            assert not hasattr(tv, name), f"Scope violation: '{name}' found in teleportation_verification!"

"""Tests for Milestone M5: Bell Correlation.

Validates:
- Two-qubit observable expectation values (<O_0 (x) O_1>)
- Theoretical same-basis Bell correlations (XX, YY, ZZ) across all 4 Bell states
- Empirical correlation from binary measurement counts and probabilities
- Qiskit Aer circuit simulation with basis rotations (ZZ, XX, YY)
- Public Qiskit cross-validation (Statevector and SparsePauliOp)
- Bug-catching sensitivity tests (Bugs A-H: tensor order, conjugation, YY sign, etc.)
- Edge-case and error handling
- Scope verification (no M6+ functionality)
"""

from __future__ import annotations

import numpy as np
import pytest
from qiskit.quantum_info import SparsePauliOp, Statevector
from qiskit_aer import AerSimulator

from src.quantum.bell import (
    BELL_PHI_PLUS,
    BELL_PHI_MINUS,
    BELL_PSI_PLUS,
    BELL_PSI_MINUS,
    BellState,
    calculate_two_qubit_expectation_value,
    create_bell_circuit,
    get_bell_state,
    validate_two_qubit_state,
)
from src.quantum.correlations import (
    SUPPORTED_CORRELATION_BASES,
    VALID_TWO_QUBIT_OUTCOMES,
    calculate_bell_correlation_deviations,
    calculate_bell_correlations,
    calculate_correlation_from_counts,
    calculate_correlation_from_probabilities,
    calculate_theoretical_bell_correlations,
    create_bell_correlation_circuit,
    measure_all_bell_correlations,
    measure_bell_correlation,
)


# ==============================================================================
# 1. Theoretical Bell Correlation Tests
# ==============================================================================

class TestTheoreticalBellCorrelations:
    """Validates theoretical observable expectation values for pure two-qubit states."""

    def test_canonical_phi_plus_correlations(self) -> None:
        """For |Phi+> = (|00> + |11>)/sqrt(2): ZZ = +1.0, XX = +1.0, YY = -1.0."""
        corr = calculate_theoretical_bell_correlations(BELL_PHI_PLUS)
        assert np.isclose(corr["ZZ"], 1.0, atol=1e-12)
        assert np.isclose(corr["XX"], 1.0, atol=1e-12)
        assert np.isclose(corr["YY"], -1.0, atol=1e-12)

    def test_all_four_bell_states_exact_table(self) -> None:
        """Validates exact same-basis correlation table across the full Bell basis:

        | State | XX | YY | ZZ |
        | Phi+  | +1 | -1 | +1 |
        | Phi-  | -1 | +1 | +1 |
        | Psi+  | +1 | +1 | -1 |
        | Psi-  | -1 | -1 | -1 |
        """
        expected_table = {
            "phi+": {"XX": 1.0, "YY": -1.0, "ZZ": 1.0},
            "phi-": {"XX": -1.0, "YY": 1.0, "ZZ": 1.0},
            "psi+": {"XX": 1.0, "YY": 1.0, "ZZ": -1.0},
            "psi-": {"XX": -1.0, "YY": -1.0, "ZZ": -1.0},
        }

        states = {
            "phi+": BELL_PHI_PLUS,
            "phi-": BELL_PHI_MINUS,
            "psi+": BELL_PSI_PLUS,
            "psi-": BELL_PSI_MINUS,
        }

        for name, state_vec in states.items():
            corr = calculate_theoretical_bell_correlations(state_vec)
            expected = expected_table[name]
            for basis in ("XX", "YY", "ZZ"):
                assert np.isclose(corr[basis], expected[basis], atol=1e-12), (
                    f"Mismatch for {name} on {basis}: got {corr[basis]}, expected {expected[basis]}."
                )

    def test_bell_state_instances_and_names(self) -> None:
        """calculate_theoretical_bell_correlations supports BellState instances and string names."""
        bs_phi_plus = BellState(BELL_PHI_PLUS)
        corr_obj = calculate_theoretical_bell_correlations(bs_phi_plus)
        assert corr_obj["XX"] == 1.0
        assert corr_obj["YY"] == -1.0
        assert corr_obj["ZZ"] == 1.0

        # String alias
        corr_str = calculate_theoretical_bell_correlations("phi+")
        assert corr_str == corr_obj

        # BellState property
        assert bs_phi_plus.bell_correlations == corr_obj

    def test_separable_states_have_different_correlation_structure(self) -> None:
        """Separable states exhibit different correlation structures from entangled Bell states."""
        # |00> has ZZ = +1, but XX = 0 and YY = 0
        state_00 = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.complex128)
        corr_00 = calculate_theoretical_bell_correlations(state_00)
        assert np.isclose(corr_00["ZZ"], 1.0, atol=1e-12)
        assert np.isclose(corr_00["XX"], 0.0, atol=1e-12)
        assert np.isclose(corr_00["YY"], 0.0, atol=1e-12)

        # |11> has ZZ = +1, XX = 0, YY = 0
        state_11 = np.array([0.0, 0.0, 0.0, 1.0], dtype=np.complex128)
        corr_11 = calculate_theoretical_bell_correlations(state_11)
        assert np.isclose(corr_11["ZZ"], 1.0, atol=1e-12)
        assert np.isclose(corr_11["XX"], 0.0, atol=1e-12)
        assert np.isclose(corr_11["YY"], 0.0, atol=1e-12)

        # |++> = 1/2 [1, 1, 1, 1]^T has XX = +1, ZZ = 0, YY = 0
        state_plus_plus = 0.5 * np.array([1.0, 1.0, 1.0, 1.0], dtype=np.complex128)
        corr_pp = calculate_theoretical_bell_correlations(state_plus_plus)
        assert np.isclose(corr_pp["XX"], 1.0, atol=1e-12)
        assert np.isclose(corr_pp["ZZ"], 0.0, atol=1e-12)
        assert np.isclose(corr_pp["YY"], 0.0, atol=1e-12)

    def test_polymorphic_calculate_bell_correlations(self) -> None:
        """calculate_bell_correlations transparently handles both states and outcome dictionaries."""
        # State vector input
        state_corr = calculate_bell_correlations(BELL_PHI_PLUS)
        assert np.isclose(state_corr["XX"], 1.0)
        assert np.isclose(state_corr["YY"], -1.0)
        assert np.isclose(state_corr["ZZ"], 1.0)

        # Dictionary input (computational basis counts)
        dict_corr = calculate_bell_correlations({"00": 500, "11": 500})
        assert np.isclose(dict_corr["P_same"], 1.0)
        assert np.isclose(dict_corr["P_diff"], 0.0)
        assert np.isclose(dict_corr["correlation"], 1.0)
        assert np.isclose(dict_corr["ZZ"], 1.0)


# ==============================================================================
# 2. Empirical Correlation from Measurement Counts & Probabilities
# ==============================================================================

class TestEmpiricalCorrelationCalculations:
    """Validates calculation of correlation expectation value E from binary measurement results."""

    def test_count_formula_vs_probability_formula_identity(self) -> None:
        """E = (N_00 + N_11 - N_01 - N_10) / N_total == P(same) - P(diff)."""
        counts = {"00": 420, "11": 380, "01": 110, "10": 90}
        n_total = sum(counts.values())  # 1000

        e_counts = calculate_correlation_from_counts(counts)
        expected_e = (420 + 380 - 110 - 90) / 1000.0  # 600 / 1000 = 0.6
        assert np.isclose(e_counts, expected_e, atol=1e-12)

        # Corresponding probabilities
        probs = {k: v / n_total for k, v in counts.items()}
        e_probs = calculate_correlation_from_probabilities(probs)
        assert np.isclose(e_counts, e_probs, atol=1e-12)

    def test_deterministic_perfect_correlation(self) -> None:
        """Outcomes strictly in {00, 11} yield E = +1.0."""
        counts = {"00": 512, "11": 512}
        assert calculate_correlation_from_counts(counts) == 1.0

        probs = {"00": 0.5, "11": 0.5, "01": 0.0, "10": 0.0}
        assert calculate_correlation_from_probabilities(probs) == 1.0

    def test_deterministic_perfect_anti_correlation(self) -> None:
        """Outcomes strictly in {01, 10} yield E = -1.0."""
        counts = {"01": 500, "10": 500}
        assert calculate_correlation_from_counts(counts) == -1.0

        probs = {"00": 0.0, "11": 0.0, "01": 0.5, "10": 0.5}
        assert calculate_correlation_from_probabilities(probs) == -1.0

    def test_uniform_distribution_zero_correlation(self) -> None:
        """Uniform distribution across all 4 outcomes yields E = 0.0."""
        counts = {"00": 250, "01": 250, "10": 250, "11": 250}
        assert calculate_correlation_from_counts(counts) == 0.0

        probs = {"00": 0.25, "01": 0.25, "10": 0.25, "11": 0.25}
        assert calculate_correlation_from_probabilities(probs) == 0.0

    def test_float_and_numpy_counts_supported(self) -> None:
        """Numeric float and NumPy integer/float counts are supported."""
        counts = {
            "00": np.int64(100),
            "11": np.float64(100.0),
            "01": 50,
            "10": 50.0,
        }
        # (200 - 100) / 300 = 1/3
        expected = 100.0 / 300.0
        assert np.isclose(calculate_correlation_from_counts(counts), expected)


# ==============================================================================
# 3. Basis-Rotation Circuit & Aer Simulation Tests
# ==============================================================================

class TestBasisRotationsAndSimulation:
    """Validates quantum circuits with basis rotations and Aer simulation."""

    def test_circuit_gate_structure_for_each_basis(self) -> None:
        """Verify the pre-measurement unitary rotations applied:
        - ZZ: No pre-measurement rotations
        - XX: Hadamard gate on q0 and q1
        - YY: S† then Hadamard gate on q0 and q1
        """
        qc_zz = create_bell_correlation_circuit(BELL_PHI_PLUS, basis="ZZ")
        # For Phi+, circuit has H(0), CX(0, 1), then measurements. No extra rotations.
        op_names_zz = [inst.operation.name for inst in qc_zz.data]
        assert "measure" in op_names_zz
        assert op_names_zz.count("measure") == 2
        assert op_names_zz.count("h") == 1  # only the initial state preparation H(0)

        qc_xx = create_bell_correlation_circuit(BELL_PHI_PLUS, basis="XX")
        op_names_xx = [inst.operation.name for inst in qc_xx.data]
        # Initial H(0), CX(0, 1), then H(0), H(1), then measurements
        assert op_names_xx.count("h") == 3

        qc_yy = create_bell_correlation_circuit(BELL_PHI_PLUS, basis="YY")
        op_names_yy = [inst.operation.name for inst in qc_yy.data]
        # Initial H(0), CX(0, 1), then sdg(0), h(0), sdg(1), h(1), then measurements
        assert op_names_yy.count("sdg") == 2
        assert op_names_yy.count("h") == 3

    def test_ideal_aer_simulation_outcomes_for_phi_plus(self) -> None:
        """Aer simulation of ideal |Phi+>:
        - ZZ: strictly produces '00' and '11' -> E_ZZ = +1.0
        - XX: strictly produces '00' and '11' -> E_XX = +1.0
        - YY: strictly produces '01' and '10' -> E_YY = -1.0
        """
        sim = AerSimulator()
        shots = 2000

        # ZZ measurement
        counts_zz, corr_zz = measure_bell_correlation(
            BELL_PHI_PLUS, basis="ZZ", shots=shots, seed=42, simulator=sim
        )
        assert set(counts_zz.keys()).issubset({"00", "11"})
        assert corr_zz == 1.0

        # XX measurement
        counts_xx, corr_xx = measure_bell_correlation(
            BELL_PHI_PLUS, basis="XX", shots=shots, seed=43, simulator=sim
        )
        assert set(counts_xx.keys()).issubset({"00", "11"})
        assert corr_xx == 1.0

        # YY measurement
        counts_yy, corr_yy = measure_bell_correlation(
            BELL_PHI_PLUS, basis="YY", shots=shots, seed=44, simulator=sim
        )
        assert set(counts_yy.keys()).issubset({"01", "10"})
        assert corr_yy == -1.0

    def test_measure_all_bell_correlations(self) -> None:
        """measure_all_bell_correlations evaluates XX, YY, ZZ in a single high-level call."""
        results = measure_all_bell_correlations(BELL_PHI_PLUS, shots=1000, seed=1234)

        assert "XX" in results
        assert "YY" in results
        assert "ZZ" in results

        assert results["XX"]["empirical"] == 1.0
        assert results["XX"]["theoretical"] == 1.0
        assert results["XX"]["deviation"] == 0.0

        assert results["YY"]["empirical"] == -1.0
        assert results["YY"]["theoretical"] == -1.0
        assert results["YY"]["deviation"] == 0.0

        assert results["ZZ"]["empirical"] == 1.0
        assert results["ZZ"]["theoretical"] == 1.0
        assert results["ZZ"]["deviation"] == 0.0

    def test_finite_shot_statistical_tolerances_documented(self) -> None:
        """For finite shot simulations, empirical correlation matches theoretical within 3-sigma tolerance.

        For N = 10,000 shots:
        Standard deviation of sample mean for Bernoulli variable is sigma = sqrt(p(1-p)/N) <= 0.5 / sqrt(N).
        For difference of proportions: sigma_diff <= sqrt(1/N) = 0.01.
        A 3-sigma tolerance of 3 * 0.01 = 0.03 covers > 99.7% of finite sampling fluctuations.
        For deterministic ideal Bell correlations in these bases, the outcomes are strictly 100% correlated
        or anti-correlated (variance = 0), so deviation is exactly 0.0.
        """
        results = measure_all_bell_correlations(BELL_PHI_PLUS, shots=10000, seed=999)
        deviations = calculate_bell_correlation_deviations(
            empirical_correlations={b: results[b]["empirical"] for b in ("XX", "YY", "ZZ")},
            theoretical_correlations={b: results[b]["theoretical"] for b in ("XX", "YY", "ZZ")},
        )
        for b, dev in deviations.items():
            assert dev <= 0.03, f"Deviation on {b} exceeded statistical tolerance: {dev} > 0.03."


# ==============================================================================
# 4. Public Qiskit Cross-Validation Tests
# ==============================================================================

class TestQiskitCrossValidation:
    """Cross-validates mathematical correlation implementation against Qiskit public APIs."""

    def test_qiskit_statevector_and_sparse_pauli_op(self) -> None:
        """Cross-checks expectation values with Qiskit Statevector.expectation_value(SparsePauliOp)."""
        qc = create_bell_circuit(circuit_name="qiskit_sv_test", measure=False)
        sv = Statevector.from_instruction(qc)

        # In Qiskit, operator string 'AB' operates as B on qubit 0, A on qubit 1.
        # For symmetric observables XX, YY, ZZ, ordering is identical.
        qiskit_xx = float(sv.expectation_value(SparsePauliOp("XX")).real)
        qiskit_yy = float(sv.expectation_value(SparsePauliOp("YY")).real)
        qiskit_zz = float(sv.expectation_value(SparsePauliOp("ZZ")).real)

        our_correlations = calculate_theoretical_bell_correlations(BELL_PHI_PLUS)

        # Must agree to within standard machine precision (1e-14)
        assert np.isclose(our_correlations["XX"], qiskit_xx, atol=1e-14)
        assert np.isclose(our_correlations["YY"], qiskit_yy, atol=1e-14)
        assert np.isclose(our_correlations["ZZ"], qiskit_zz, atol=1e-14)


# ==============================================================================
# 5. Bug-Catching Sensitivity Tests (Section 20: Bugs A through L)
# ==============================================================================

class TestBugCatchingSensitivity:
    """Tests designed to FAIL if common bugs or implementation defects are introduced."""

    def test_bug_a_np_dot_used_instead_of_conjugating_np_vdot(self) -> None:
        """Bug A: np.dot used instead of conjugating np.vdot.

        Tested on complex entangled state:
            |psi> = (|00> + i|11>) / sqrt(2)
        For observable O = X (x) Y:
            (X (x) Y)|00> = |1> (x) (i|1>) = i|11>
            (X (x) Y)|11> = |0> (x) (-i|0>) = -i|00>
            (X (x) Y)|psi> = (i|11> + i(-i|00>)) / sqrt(2) = (|00> + i|11>) / sqrt(2) = |psi>
        Expectation value:
            <psi| (X (x) Y) |psi> = <psi|psi> = +1.0.
        If conjugation is omitted (using psi^T @ O @ psi without conj):
            psi^T (X (x) Y) psi = (1/2) * (1*(1) + i*(i)) = (1/2) * (1 - 1) = 0.0.
        This test will fail if complex conjugation is omitted or np.dot is used.
        """
        psi_complex = np.array([1.0 / np.sqrt(2), 0.0, 0.0, 1.0j / np.sqrt(2)], dtype=np.complex128)
        exp_xy = calculate_two_qubit_expectation_value(psi_complex, "X", "Y")
        assert np.isclose(exp_xy, 1.0, atol=1e-12)

    def test_bug_b_reversed_kronecker_product_tensor_ordering(self) -> None:
        """Bug B: np.kron(operator_1, operator_0) used accidentally instead of kron(op0, op1).

        Tested on asymmetric product state |10> = |1> (x) |0>:
            <Z (x) I> = <1|Z|1> * <0|I|0> = (-1) * (+1) = -1.0
            <I (x) Z> = <1|I|1> * <0|Z|0> = (+1) * (+1) = +1.0
        If tensor ordering is reversed, the values swap:
            kron(I, Z) on |10> would give +1.0 instead of -1.0.
        """
        # Basis order: index = 2*q0 + q1. For q0=1, q1=0 -> index 2.
        state_10 = np.array([0.0, 0.0, 1.0, 0.0], dtype=np.complex128)

        z_i = calculate_two_qubit_expectation_value(state_10, "Z", "I")
        i_z = calculate_two_qubit_expectation_value(state_10, "I", "Z")

        assert np.isclose(z_i, -1.0, atol=1e-12)
        assert np.isclose(i_z, +1.0, atol=1e-12)
        assert z_i != i_z

    def test_bug_c_pauli_y_wrong_sign(self) -> None:
        """Bug C: Pauli-Y has the wrong sign (e.g. [[0, i], [-i, 0]]).

        For |Phi+> = (|00> + |11>)/sqrt(2), Y (x) Y produces:
            Y|0> = i|1>, Y|1> = -i|0>
            (Y (x) Y)|00> = -|11>
            (Y (x) Y)|11> = -|00>
        Hence:
            <Phi+| (Y (x) Y) |Phi+> = -1.0.
        Fails if YY is erroneously asserted or calculated as +1.0.
        """
        corr = calculate_theoretical_bell_correlations(BELL_PHI_PLUS)
        assert corr["YY"] == -1.0
        assert corr["YY"] != +1.0

    def test_bug_d_basis_labels_mapped_to_wrong_basis(self) -> None:
        """Bug D: XX/YY/ZZ labels are mapped to the wrong basis gates.

        We test eigenstate behavior under basis-rotated measurement circuits:
        - For |00> (ZZ eigenstate with eigenvalue +1):
            ZZ basis has no rotation -> strictly produces '00' -> E_ZZ = +1.0
            XX basis applies H gates -> equal superposition -> E_XX fluctuates around 0.0
            YY basis applies S†H gates -> equal superposition -> E_YY fluctuates around 0.0
        - For |++> (XX eigenstate with eigenvalue +1):
            XX basis applies H gates -> strictly produces '00' -> E_XX = +1.0
            ZZ basis has no rotation -> equal superposition -> E_ZZ fluctuates around 0.0
            YY basis applies S†H gates -> equal superposition -> E_YY fluctuates around 0.0
        If XX, YY, ZZ labels were swapped or mapped to the wrong gates, this test fails immediately.
        """
        sim = AerSimulator()
        shots = 1000

        # |00> state
        state_00 = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.complex128)
        _, corr_zz = measure_bell_correlation(state_00, basis="ZZ", shots=shots, seed=10, simulator=sim)
        _, corr_xx = measure_bell_correlation(state_00, basis="XX", shots=shots, seed=11, simulator=sim)
        _, corr_yy = measure_bell_correlation(state_00, basis="YY", shots=shots, seed=12, simulator=sim)

        assert corr_zz == 1.0, "ZZ basis measurement on |00> must yield exact E_ZZ = +1.0"
        assert abs(corr_xx) < 0.15, f"XX basis measurement on |00> must be near 0, got {corr_xx}"
        assert abs(corr_yy) < 0.15, f"YY basis measurement on |00> must be near 0, got {corr_yy}"

        # |++> state = (|00> + |01> + |10> + |11>) / 2
        state_plus_plus = np.array([0.5, 0.5, 0.5, 0.5], dtype=np.complex128)
        _, corr_plus_xx = measure_bell_correlation(state_plus_plus, basis="XX", shots=shots, seed=20, simulator=sim)
        _, corr_plus_zz = measure_bell_correlation(state_plus_plus, basis="ZZ", shots=shots, seed=21, simulator=sim)
        _, corr_plus_yy = measure_bell_correlation(state_plus_plus, basis="YY", shots=shots, seed=22, simulator=sim)

        assert corr_plus_xx == 1.0, "XX basis measurement on |++> must yield exact E_XX = +1.0"
        assert abs(corr_plus_zz) < 0.15, f"ZZ basis measurement on |++> must be near 0, got {corr_plus_zz}"
        assert abs(corr_plus_yy) < 0.15, f"YY basis measurement on |++> must be near 0, got {corr_plus_yy}"

    def test_bug_d_bell_state_distinct_signatures(self) -> None:
        """Bug D: Inverted signs across the 4 Bell states.

        Verifies distinct signatures for all 4 Bell states so that swapping or mislabeling
        any state triggers an immediate assertion failure.
        """
        phi_plus = calculate_theoretical_bell_correlations(BELL_PHI_PLUS)
        phi_minus = calculate_theoretical_bell_correlations(BELL_PHI_MINUS)
        psi_plus = calculate_theoretical_bell_correlations(BELL_PSI_PLUS)
        psi_minus = calculate_theoretical_bell_correlations(BELL_PSI_MINUS)

        triplets = [
            (s["XX"], s["YY"], s["ZZ"])
            for s in (phi_plus, phi_minus, psi_plus, psi_minus)
        ]
        assert len(set(triplets)) == 4, "All 4 Bell states must have distinct correlation signatures."

    def test_bug_e_only_00_and_11_considered_in_correlation(self) -> None:
        """Bug E: Only '00' and '11' are considered when calculating empirical correlation.

        Verifies that '01' and '10' contribute with negative weight to E:
            E = (N_00 + N_11 - N_01 - N_10) / (N_00 + N_01 + N_10 + N_11)
        Specific test from prompt:
            00 = 30, 01 = 10, 10 = 20, 11 = 40
            Expected: E = (30 + 40 - 10 - 20) / 100 = 40 / 100 = 0.4
        If an implementation assumes only '00' and '11' exist, it would calculate:
            (30 + 40) / 70 = 1.0 or (30 + 40) / 100 = 0.70.
        """
        counts = {"00": 30, "01": 10, "10": 20, "11": 40}
        emp_corr = calculate_correlation_from_counts(counts)
        assert np.isclose(emp_corr, 0.4, atol=1e-12)

        # Equal positive and negative contributions -> E = 0.0
        counts_even = {"00": 50, "11": 50, "01": 50, "10": 50}
        assert calculate_correlation_from_counts(counts_even) == 0.0

    def test_bug_f_negative_counts_rejected(self) -> None:
        """Bug F: Silently accepting negative measurement counts."""
        with pytest.raises(ValueError, match="cannot be negative"):
            calculate_correlation_from_counts({"00": 100, "11": -10})

        with pytest.raises(ValueError, match="cannot be negative"):
            calculate_correlation_from_counts({"01": -1})

    def test_bug_g_invalid_outcome_labels_rejected(self) -> None:
        """Bug G: Silently accepting or ignoring invalid outcome keys."""
        invalid_keys = ["000", "2", "abc", "", "0", "1", "001", "00 11"]
        for bad_key in invalid_keys:
            with pytest.raises(ValueError, match="Invalid two-qubit outcome label"):
                calculate_correlation_from_counts({"00": 10, bad_key: 5})

            with pytest.raises(ValueError, match="Invalid outcome label"):
                calculate_correlation_from_probabilities({"00": 0.9, bad_key: 0.1})

    def test_bug_h_zero_total_shots_produce_error_not_nan(self) -> None:
        """Bug H: Zero total shots produce NaN instead of a clear error."""
        with pytest.raises(ValueError, match="empty counts"):
            calculate_correlation_from_counts({})

        with pytest.raises(ValueError, match="strictly positive"):
            calculate_correlation_from_counts({"00": 0, "11": 0})

    def test_bug_i_non_hermitian_observable_rejected_even_if_real_expectation(self) -> None:
        """Bug I: Non-Hermitian observables must be rejected even if expectation is real.

        Consider A = [[1, 2], [0, 1]]. On |00>, <00| (A (x) Z) |00> = 1.0 + 0.0i.
        Even though the expectation value has no imaginary component, A is NOT Hermitian (A† != A),
        so it must be rejected as an unphysical observable.
        """
        state_00 = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.complex128)
        non_herm = np.array([[1.0, 2.0], [0.0, 1.0]], dtype=np.complex128)
        with pytest.raises(ValueError, match="Hermitian observable"):
            calculate_two_qubit_expectation_value(state_00, non_herm, "Z")

        with pytest.raises(ValueError, match="Hermitian observable"):
            calculate_two_qubit_expectation_value(state_00, "Z", non_herm)

    def test_bug_j_qiskit_bitstring_endianness_on_asymmetric_state(self) -> None:
        """Bug J: Qiskit classical bitstring ordering reversal.

        For asymmetric state |10> (q0 = 1, q1 = 0), computational-basis measurement
        must yield canonical project outcome '10' (q0=1, q1=0), not '01'.
        """
        state_10 = np.array([0.0, 0.0, 1.0, 0.0], dtype=np.complex128)
        counts, corr = measure_bell_correlation(state_10, basis="ZZ", shots=500, seed=42)
        assert "10" in counts
        assert counts["10"] == 500
        assert "01" not in counts
        assert corr == -1.0

    def test_bug_k_finite_shot_sampling_does_not_require_exact_equality_on_superposition(self) -> None:
        """Bug K: Finite-shot sampling must not erroneously assert exact theoretical values.

        When measuring |00> in the XX basis, both qubits are in equal superposition:
            (H (x) H)|00> = 1/2 [|00> + |01> + |10> + |11>]
        Theoretical correlation is E = 0.0.
        In finite sampling (N = 1000), empirical correlation fluctuates around 0.0.
        The test verifies that empirical correlation satisfies statistical 3-sigma bound
        (|E_empirical - 0.0| <= 3 / sqrt(N) = 0.095) rather than requiring exact 0.0.
        """
        state_00 = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.complex128)
        counts, emp_corr = measure_bell_correlation(state_00, basis="XX", shots=1000, seed=123)
        assert len(counts) > 1
        assert abs(emp_corr - 0.0) <= 0.095

    def test_bug_l_no_hardcoded_bell_correlations_parameterized_state(self) -> None:
        """Bug L: Verifies that correlations are computed from state vectors, not hardcoded lookups.

        For parameterized entangled state |psi(theta)> = cos(theta)|00> + sin(theta)|11>:
            <Z (x) Z> = cos^2(theta) + sin^2(theta) = 1.0
            <X (x) X> = 2 cos(theta) sin(theta) = sin(2*theta)
            <Y (x) Y> = -2 cos(theta) sin(theta) = -sin(2*theta)
        For theta = pi / 6:
            cos(theta) = sqrt(3)/2, sin(theta) = 1/2
            sin(2*theta) = sin(pi/3) = sqrt(3)/2 ≈ 0.8660254
        """
        theta = np.pi / 6.0
        c, s = np.cos(theta), np.sin(theta)
        param_state = np.array([c, 0.0, 0.0, s], dtype=np.complex128)

        corr = calculate_theoretical_bell_correlations(param_state)
        expected_xx = float(np.sin(2.0 * theta))
        expected_yy = float(-np.sin(2.0 * theta))
        expected_zz = 1.0

        assert np.isclose(corr["ZZ"], expected_zz, atol=1e-12)
        assert np.isclose(corr["XX"], expected_xx, atol=1e-12)
        assert np.isclose(corr["YY"], expected_yy, atol=1e-12)


# ==============================================================================
# 6. Input Validation & Edge Cases (Section 10)
# ==============================================================================

class TestEdgeCasesAndValidation:
    """Validates boundary conditions, malformed inputs, and type enforcement."""

    def test_invalid_state_dimension_rejected(self) -> None:
        """States with length != 4 are rejected."""
        with pytest.raises(ValueError, match="shape"):
            calculate_theoretical_bell_correlations(np.array([1.0, 0.0, 0.0]))

        with pytest.raises(ValueError, match="shape"):
            calculate_theoretical_bell_correlations(np.eye(4))

    def test_non_finite_state_values_rejected(self) -> None:
        """States with NaN or Inf are rejected."""
        nan_state = np.array([np.nan, 0.0, 0.0, 1.0])
        with pytest.raises(ValueError, match="finite"):
            calculate_theoretical_bell_correlations(nan_state)

        inf_state = np.array([np.inf, 0.0, 0.0, 0.0])
        with pytest.raises(ValueError, match="finite"):
            calculate_theoretical_bell_correlations(inf_state)

    def test_zero_vector_state_rejected(self) -> None:
        """Zero vector state is rejected."""
        zero_state = np.zeros(4, dtype=np.complex128)
        with pytest.raises(ValueError, match="zero"):
            calculate_theoretical_bell_correlations(zero_state)

    def test_non_numeric_and_boolean_counts_rejected(self) -> None:
        """Boolean values and non-numeric types are rejected."""
        with pytest.raises(TypeError):
            calculate_correlation_from_counts("not a dict")  # type: ignore

        with pytest.raises(TypeError, match="boolean"):
            calculate_correlation_from_counts({"00": True, "11": 10})  # type: ignore

        with pytest.raises(TypeError, match="numeric"):
            calculate_correlation_from_counts({"00": "100", "11": 10})  # type: ignore

    def test_non_finite_counts_rejected(self) -> None:
        """NaN and Inf counts are rejected."""
        with pytest.raises(ValueError, match="finite"):
            calculate_correlation_from_counts({"00": float("nan"), "11": 10})

        with pytest.raises(ValueError, match="finite"):
            calculate_correlation_from_counts({"00": float("inf"), "11": 10})

    def test_unsupported_measurement_basis_rejected(self) -> None:
        """Unsupported basis strings are rejected."""
        with pytest.raises(ValueError, match="Invalid correlation basis"):
            create_bell_correlation_circuit(BELL_PHI_PLUS, basis="AB")

        with pytest.raises(ValueError, match="Invalid correlation basis"):
            measure_bell_correlation(BELL_PHI_PLUS, basis="invalid")

    def test_simulation_parameter_validation(self) -> None:
        """measure_bell_correlation enforces positive shots and non-negative seed."""
        with pytest.raises(ValueError, match="strictly positive"):
            measure_bell_correlation(BELL_PHI_PLUS, shots=0)

        with pytest.raises(ValueError, match="strictly positive"):
            measure_bell_correlation(BELL_PHI_PLUS, shots=-10)

        with pytest.raises(TypeError, match="integer"):
            measure_bell_correlation(BELL_PHI_PLUS, shots="100")  # type: ignore

        with pytest.raises(ValueError, match="non-negative"):
            measure_bell_correlation(BELL_PHI_PLUS, seed=-5)

    def test_unnormalized_probabilities_rejected(self) -> None:
        """Probabilities that do not sum to 1.0 raise ValueError."""
        with pytest.raises(ValueError, match="sum to 1.0"):
            calculate_correlation_from_probabilities({"00": 0.5, "11": 0.6})

    def test_fractional_counts_rejected(self) -> None:
        """Counts represent discrete measurement shots; fractional counts (e.g. 3.7) must be rejected."""
        with pytest.raises(TypeError, match="integer shot count"):
            calculate_correlation_from_counts({"00": 3.7, "11": 10})

        with pytest.raises(TypeError, match="integer shot count"):
            calculate_correlation_from_counts({"00": 10, "01": 2.5, "10": 0, "11": 0})


# ==============================================================================
# 7. Milestone Scope Enforcement Tests (Section 3 & 18)
# ==============================================================================

class TestMilestoneScopeEnforcement:
    """Verifies that M5 strictly adheres to the divide-and-conquer scope boundary."""

    def test_no_m6_or_teleportation_modules_in_quantum_package(self) -> None:
        """M5 must NOT implement teleportation, noise, or attack models."""
        import src.quantum.correlations as corr_mod

        # Check attributes of the M5 correlations module
        assert not hasattr(corr_mod, "teleport"), "teleport must not be present in M5."
        assert not hasattr(corr_mod, "teleportation"), "teleportation must not be present in M5."
        assert not hasattr(corr_mod, "apply_channel_noise"), "noise must not be present in M5."
        assert not hasattr(corr_mod, "depolarizing_noise"), "noise must not be present in M5."
        assert not hasattr(corr_mod, "detect_attack"), "attack detection must not be present in M5."
        assert not hasattr(corr_mod, "calculate_security_score"), "security score must not be present in M5."
        assert not hasattr(corr_mod, "quantum_trust_score"), "trust score must not be present in M5."

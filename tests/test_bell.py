"""Tests for Milestone M4: Bell State / Entanglement.

Covers:
1. Two-qubit Bell state construction, dimension, dtype, exact amplitudes, and normalization.
2. Complete orthonormal Bell basis: |Phi+>, |Phi->, |Psi+>, |Psi->.
3. Computational-basis measurement theoretical probabilities (P(00)=0.5, P(11)=0.5, P(01)=0, P(10)=0).
4. Perfect correlation in computational basis: P(q0 == q1) = 1.0, P(q0 != q1) = 0.0.
5. Two-qubit Pauli expectation values:
   - <Z (x) Z> = +1.0
   - <X (x) X> = +1.0
   - <Y (x) Y> = -1.0
   - <Z (x) X> = 0.0
6. Tensor/Kronecker product ordering on asymmetric observables (Bug F).
7. Complex conjugation of the bra vector in expectation value calculation (Bug G).
8. Distinction between coherent quantum superposition |Phi+> and classical mixture 0.5|00><00| + 0.5|11><11|.
9. Mathematical proof of entanglement:
   - Coefficient matrix rank = 2 (Schmidt rank = 2)
   - Contrast with separable product states (|00>, |11>, |++>, |+> (x) |0>) with rank = 1.
10. Reduced density matrix validation:
   - rho_A = rho_B = I_2 / 2 (maximally mixed, Hermiticity, trace = 1, purity = 0.5).
11. Qiskit circuit construction, Aer simulation, and explicit qubit/bit ordering validation through measure_bell_state.
12. Input validation, error handling, edge cases, and BellState dataclass support.
"""

from __future__ import annotations

import numpy as np
import pytest
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator

from src.quantum.bell import (
    BELL_PHI_PLUS,
    BELL_PHI_MINUS,
    BELL_PSI_PLUS,
    BELL_PSI_MINUS,
    TWO_QUBIT_BASIS_LABELS,
    INV_SQRT_2,
    create_bell_phi_plus,
    create_bell_phi_minus,
    create_bell_psi_plus,
    create_bell_psi_minus,
    get_bell_state,
    validate_two_qubit_state,
    create_bell_circuit,
    bell_computational_probabilities,
    calculate_bell_correlations,
    calculate_two_qubit_expectation_value,
    check_entanglement,
    partial_trace_qubit,
    measure_bell_state,
    BellState,
)
from src.quantum.pauli import PAULI_I, PAULI_X, PAULI_Y, PAULI_Z


class TestBellStateCreationAndProperties:
    """Mathematical and structural validation of the |Phi+> Bell state and the Bell basis."""

    def test_bell_state_dimension_and_dtype(self) -> None:
        """|Phi+> vector must have shape (4,) and complex128 dtype."""
        psi = create_bell_phi_plus()
        assert psi.shape == (4,)
        assert psi.dtype == np.complex128

    def test_bell_state_exact_amplitudes(self) -> None:
        """|Phi+> = 1/sqrt(2)|00> + 0|01> + 0|10> + 1/sqrt(2)|11>."""
        psi = create_bell_phi_plus()
        expected = np.array([INV_SQRT_2, 0.0, 0.0, INV_SQRT_2], dtype=np.complex128)
        assert np.allclose(psi, expected)

        # Explicit per-amplitude check
        assert np.isclose(psi[0], 1.0 / np.sqrt(2.0))
        assert np.isclose(psi[1], 0.0)
        assert np.isclose(psi[2], 0.0)
        assert np.isclose(psi[3], 1.0 / np.sqrt(2.0))

    def test_bell_state_normalization(self) -> None:
        """<Phi+|Phi+> must equal exactly 1.0 within numerical precision."""
        psi = create_bell_phi_plus()
        norm_sq = float(np.real(np.vdot(psi, psi)))
        assert np.isclose(norm_sq, 1.0, atol=1e-12)

    def test_complete_orthonormal_bell_basis(self) -> None:
        """All four Bell states must be normalized and mutually orthogonal."""
        phi_p = create_bell_phi_plus()
        phi_m = create_bell_phi_minus()
        psi_p = create_bell_psi_plus()
        psi_m = create_bell_psi_minus()

        basis = [phi_p, phi_m, psi_p, psi_m]

        # Normalization
        for state in basis:
            assert np.isclose(np.vdot(state, state), 1.0, atol=1e-12)

        # Mutual orthogonality
        for i in range(4):
            for j in range(4):
                expected = 1.0 if i == j else 0.0
                assert np.isclose(np.vdot(basis[i], basis[j]), expected, atol=1e-12)

    def test_get_bell_state_by_name(self) -> None:
        """get_bell_state returns canonical copies by string identifier."""
        assert np.allclose(get_bell_state("phi+"), BELL_PHI_PLUS)
        assert np.allclose(get_bell_state("phi-"), BELL_PHI_MINUS)
        assert np.allclose(get_bell_state("psi+"), BELL_PSI_PLUS)
        assert np.allclose(get_bell_state("psi-"), BELL_PSI_MINUS)
        assert np.allclose(get_bell_state("|Phi+>"), BELL_PHI_PLUS)

        with pytest.raises(ValueError, match="Unknown Bell state"):
            get_bell_state("unknown_state")


class TestBellProbabilitiesAndCorrelations:
    """Validation of measurement statistics, correlations, and expectation values."""

    def test_theoretical_computational_probabilities(self) -> None:
        """P(00) = 0.5, P(11) = 0.5, P(01) = 0.0, P(10) = 0.0."""
        probs = bell_computational_probabilities(BELL_PHI_PLUS)
        assert np.isclose(probs["00"], 0.5)
        assert np.isclose(probs["11"], 0.5)
        assert np.isclose(probs["01"], 0.0)
        assert np.isclose(probs["10"], 0.0)
        assert np.isclose(sum(probs.values()), 1.0)

    def test_perfect_z_basis_correlation(self) -> None:
        """Qubits 0 and 1 are perfectly correlated in computational basis."""
        probs = bell_computational_probabilities(BELL_PHI_PLUS)
        corr = calculate_bell_correlations(probs)

        # P(q0 == q1) = 1.0, P(q0 != q1) = 0.0, correlation = +1.0
        assert np.isclose(corr["P_same"], 1.0)
        assert np.isclose(corr["P_diff"], 0.0)
        assert np.isclose(corr["correlation"], 1.0)

    def test_expectation_value_z_tensor_z(self) -> None:
        """<Phi+| Z (x) Z |Phi+> = +1.0."""
        val = calculate_two_qubit_expectation_value(BELL_PHI_PLUS, PAULI_Z, PAULI_Z)
        assert np.isclose(val, 1.0)

    def test_expectation_value_x_tensor_x(self) -> None:
        """<Phi+| X (x) X |Phi+> = +1.0."""
        val = calculate_two_qubit_expectation_value(BELL_PHI_PLUS, PAULI_X, PAULI_X)
        assert np.isclose(val, 1.0)

    def test_expectation_value_y_tensor_y(self) -> None:
        """<Phi+| Y (x) Y |Phi+> = -1.0."""
        val = calculate_two_qubit_expectation_value(BELL_PHI_PLUS, PAULI_Y, PAULI_Y)
        assert np.isclose(val, -1.0)

    def test_expectation_value_orthogonal_observables(self) -> None:
        """<Phi+| Z (x) X |Phi+> = 0.0 and <Phi+| X (x) Z |Phi+> = 0.0."""
        val_zx = calculate_two_qubit_expectation_value(BELL_PHI_PLUS, PAULI_Z, PAULI_X)
        val_xz = calculate_two_qubit_expectation_value(BELL_PHI_PLUS, PAULI_X, PAULI_Z)
        assert np.isclose(val_zx, 0.0)
        assert np.isclose(val_xz, 0.0)

    def test_expectation_value_string_labels(self) -> None:
        """String operator names ('Z', 'X', 'Y', 'I') work seamlessly."""
        val_zz = calculate_two_qubit_expectation_value(BELL_PHI_PLUS, "Z", "Z")
        assert np.isclose(val_zz, 1.0)
        val_xx = calculate_two_qubit_expectation_value(BELL_PHI_PLUS, "X", "X")
        assert np.isclose(val_xx, 1.0)
        val_yy = calculate_two_qubit_expectation_value(BELL_PHI_PLUS, "Y", "Y")
        assert np.isclose(val_yy, -1.0)

    def test_tensor_product_qubit_ordering_asymmetric_observables(self) -> None:
        """Bug F: Verify operator_0 acts on qubit 0 and operator_1 acts on qubit 1.

        On |10> = |1> (x) |0>:
            (Z (x) I)|10> = (Z|1>) (x) (I|0>) = (-|1>) (x) |0> = -|10>  => Expectation = -1.0
            (I (x) Z)|10> = (I|1>) (x) (Z|0>) = (|1>) (x) (|0>) = +|10>  => Expectation = +1.0
        If the Kronecker product order was inverted (np.kron(op1, op0)), these values would swap.
        """
        state_10 = np.array([0.0, 0.0, 1.0, 0.0], dtype=np.complex128)
        val_zi = calculate_two_qubit_expectation_value(state_10, PAULI_Z, PAULI_I)
        val_iz = calculate_two_qubit_expectation_value(state_10, PAULI_I, PAULI_Z)

        assert np.isclose(val_zi, -1.0)
        assert np.isclose(val_iz, +1.0)

        # Also verify on |01> = |0> (x) |1>
        state_01 = np.array([0.0, 1.0, 0.0, 0.0], dtype=np.complex128)
        val_01_zi = calculate_two_qubit_expectation_value(state_01, PAULI_Z, PAULI_I)
        val_01_iz = calculate_two_qubit_expectation_value(state_01, PAULI_I, PAULI_Z)

        assert np.isclose(val_01_zi, +1.0)
        assert np.isclose(val_01_iz, -1.0)

    def test_complex_conjugation_in_expectation_calculation(self) -> None:
        """Bug G: Verify that the bra vector <psi| is properly complex-conjugated.

        Consider state with complex amplitudes: |psi> = (|00> + i|11>) / sqrt(2).
        For Z (x) Z:
            (Z(x)Z)|00> = |00>
            (Z(x)Z)|11> = |11>
            (Z(x)Z)|psi> = |psi>
        Mathematically:
            <psi| Z(x)Z |psi> = 1/2 [1, -i] . [1, i]^T = 1/2 (1*1 + (-i)*i) = 1/2 (1 + 1) = 1.0.
        If an incorrect, unconjugated dot product vec^T (op @ vec) was used:
            vec^T (op @ vec) = 1/2 (1*1 + i*i) = 1/2 (1 - 1) = 0.0 (wrong!).
        """
        psi_complex = np.array([INV_SQRT_2, 0.0, 0.0, 1.0j * INV_SQRT_2], dtype=np.complex128)
        val = calculate_two_qubit_expectation_value(psi_complex, PAULI_Z, PAULI_Z)
        assert np.isclose(val, 1.0)

        # Demonstrate that unconjugated dot product would fail
        op_zz = np.kron(PAULI_Z, PAULI_Z)
        unconjugated_dot = float(np.real(np.dot(psi_complex, op_zz @ psi_complex)))
        assert np.isclose(unconjugated_dot, 0.0)
        assert not np.isclose(val, unconjugated_dot)

    def test_distinguish_bell_state_from_classical_mixture(self) -> None:
        """Coherent |Phi+> has <X(x)X> = +1, while a classical 50/50 mixture has <X(x)X> = 0.

        Classical mixture: rho_mix = 0.5|00><00| + 0.5|11><11|
        For rho_mix:
            Tr((Z(x)Z) rho_mix) = 0.5(1) + 0.5(1) = 1.0
            Tr((X(x)X) rho_mix) = 0.5(0) + 0.5(0) = 0.0
        For coherent Bell state |Phi+>:
            <Phi+| X(x)X |Phi+> = +1.0
        This proves that |Phi+> has quantum phase coherence and is NOT a classical mixture.
        """
        # Quantum expectation
        xx_quantum = calculate_two_qubit_expectation_value(BELL_PHI_PLUS, PAULI_X, PAULI_X)
        assert np.isclose(xx_quantum, 1.0)

        # Classical mixture simulation
        rho_mix = 0.5 * np.outer(np.array([1, 0, 0, 0]), np.array([1, 0, 0, 0])) + \
                  0.5 * np.outer(np.array([0, 0, 0, 1]), np.array([0, 0, 0, 1]))
        xx_op = np.kron(PAULI_X, PAULI_X)
        xx_classical = float(np.real(np.trace(xx_op @ rho_mix)))

        assert np.isclose(xx_classical, 0.0)
        # Quantum Bell state differs from classical mixture!
        assert not np.isclose(xx_quantum, xx_classical)


class TestEntanglementAndReducedStates:
    """Schmidt decomposition, non-factorizability, and reduced density matrix tests."""

    def test_bell_state_is_entangled_schmidt_rank_2(self) -> None:
        """|Phi+> coefficient matrix has rank 2 and equal singular values [1/sqrt(2), 1/sqrt(2)]."""
        is_entangled, rank, s_vals = check_entanglement(BELL_PHI_PLUS)
        assert is_entangled is True
        assert rank == 2
        assert len(s_vals) == 2
        assert np.isclose(s_vals[0], INV_SQRT_2)
        assert np.isclose(s_vals[1], INV_SQRT_2)

    def test_all_four_bell_states_are_entangled(self) -> None:
        """All four Bell states must have Schmidt rank 2 and be identified as entangled."""
        for name in ("phi+", "phi-", "psi+", "psi-"):
            state = get_bell_state(name)
            is_ent, rank, s_vals = check_entanglement(state)
            assert is_ent is True
            assert rank == 2
            assert np.isclose(s_vals[0], INV_SQRT_2)
            assert np.isclose(s_vals[1], INV_SQRT_2)

    def test_product_states_are_not_entangled_schmidt_rank_1(self) -> None:
        """Product states (|00>, |11>, |++>, |+> (x) |0>) must have Schmidt rank 1 and is_entangled == False."""
        # |00>
        state_00 = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.complex128)
        is_ent, rank, _ = check_entanglement(state_00)
        assert is_ent is False
        assert rank == 1

        # |11>
        state_11 = np.array([0.0, 0.0, 0.0, 1.0], dtype=np.complex128)
        is_ent, rank, _ = check_entanglement(state_11)
        assert is_ent is False
        assert rank == 1

        # |++> = (|00> + |01> + |10> + |11>) / 2
        state_plus_plus = np.array([0.5, 0.5, 0.5, 0.5], dtype=np.complex128)
        is_ent, rank, _ = check_entanglement(state_plus_plus)
        assert is_ent is False
        assert rank == 1

        # |+> (x) |0> = 1/sqrt(2)|00> + 1/sqrt(2)|10>
        state_plus_zero = np.array([INV_SQRT_2, 0.0, INV_SQRT_2, 0.0], dtype=np.complex128)
        is_ent, rank, _ = check_entanglement(state_plus_zero)
        assert is_ent is False
        assert rank == 1

    def test_reduced_density_matrices_are_maximally_mixed(self) -> None:
        """Tracing out either qubit from |Phi+> yields rho_A = rho_B = I_2 / 2.

        Explicitly checks:
            - Hermiticity: rho^dagger == rho
            - Trace == 1
            - Diagonal elements == 0.5
            - Off-diagonal elements == 0.0
            - Purity Tr(rho^2) == 0.5 (strictly mixed)
        """
        rho_a = partial_trace_qubit(BELL_PHI_PLUS, trace_out_qubit=1)
        rho_b = partial_trace_qubit(BELL_PHI_PLUS, trace_out_qubit=0)

        expected_maximally_mixed = 0.5 * np.eye(2, dtype=np.complex128)

        assert np.allclose(rho_a, expected_maximally_mixed)
        assert np.allclose(rho_b, expected_maximally_mixed)

        # Hermiticity
        assert np.allclose(rho_a, rho_a.conj().T)
        assert np.allclose(rho_b, rho_b.conj().T)

        # Trace = 1
        assert np.isclose(np.trace(rho_a), 1.0)
        assert np.isclose(np.trace(rho_b), 1.0)

        # Diagonal and off-diagonal structure
        assert np.isclose(rho_a[0, 0], 0.5) and np.isclose(rho_a[1, 1], 0.5)
        assert np.isclose(rho_a[0, 1], 0.0) and np.isclose(rho_a[1, 0], 0.0)
        assert np.isclose(rho_b[0, 0], 0.5) and np.isclose(rho_b[1, 1], 0.5)
        assert np.isclose(rho_b[0, 1], 0.0) and np.isclose(rho_b[1, 0], 0.0)

        # Purity Tr(rho^2) = 0.5 (strictly mixed, not pure Tr(rho^2) = 1)
        purity_a = float(np.real(np.trace(rho_a @ rho_a)))
        purity_b = float(np.real(np.trace(rho_b @ rho_b)))
        assert np.isclose(purity_a, 0.5)
        assert np.isclose(purity_b, 0.5)


class TestQiskitBellSimulationAndOrdering:
    """Validation of Qiskit circuit construction, Aer simulation, and qubit ordering."""

    def test_qiskit_circuit_structure(self) -> None:
        """create_bell_circuit creates a 2-qubit circuit with H on q0 and CX(0, 1)."""
        qc = create_bell_circuit(circuit_name="test_bell")
        assert qc.num_qubits == 2
        assert qc.num_clbits == 0

        # Check operations
        ops = [inst.operation.name for inst in qc.data]
        assert ops == ["h", "cx"]
        # Check targets via standard public API
        assert qc.find_bit(qc.data[0].qubits[0]).index == 0  # H on q0
        assert qc.find_bit(qc.data[1].qubits[0]).index == 0  # CX control q0
        assert qc.find_bit(qc.data[1].qubits[1]).index == 1  # CX target q1

    def test_qiskit_circuit_statevector_matches_mathematical_phi_plus(self) -> None:
        """Verify Qiskit Statevector simulation directly matches BELL_PHI_PLUS."""
        qc = create_bell_circuit()
        sv = Statevector.from_instruction(qc).data
        assert np.allclose(sv, BELL_PHI_PLUS)

    def test_qiskit_circuit_all_four_bell_states(self) -> None:
        """create_bell_circuit correctly builds all 4 Bell states."""
        for b_type, expected_const in [
            ("phi_plus", BELL_PHI_PLUS),
            ("phi_minus", BELL_PHI_MINUS),
            ("psi_plus", BELL_PSI_PLUS),
        ]:
            qc = create_bell_circuit(bell_type=b_type)
            sv = Statevector.from_instruction(qc).data
            assert np.allclose(sv, expected_const)

        # For psi_minus: verify measurement distribution on Aer
        counts, emp_probs = measure_bell_state(
            shots=1000,
            circuit=create_bell_circuit(bell_type="psi_minus", measure=True),
            seed_simulator=10,
        )
        assert counts["00"] == 0
        assert counts["11"] == 0
        assert counts["01"] > 0
        assert counts["10"] > 0

    def test_qiskit_circuit_with_measurement(self) -> None:
        """create_bell_circuit with measure=True adds 2 classical bits and 2 measurements."""
        qc = create_bell_circuit(measure=True)
        assert qc.num_qubits == 2
        assert qc.num_clbits == 2
        meas_ops = [inst for inst in qc.data if inst.operation.name == "measure"]
        assert len(meas_ops) == 2

    def test_qiskit_aer_simulation_ideal(self) -> None:
        """Simulating the Bell circuit on Aer yields ~50% '00' and ~50% '11', zero '01'/'10'."""
        shots = 10000
        counts, emp_probs = measure_bell_state(shots=shots, seed_simulator=42)

        # Ideal state has zero counts for 01 and 10
        assert counts["01"] == 0
        assert counts["10"] == 0
        assert emp_probs["01"] == 0.0
        assert emp_probs["10"] == 0.0

        # Both 00 and 11 must occur with significant counts
        assert counts["00"] > 0
        assert counts["11"] > 0
        assert counts["00"] + counts["11"] == shots

        # Frequencies approximately 50/50 within 4 sigma
        # sigma = sqrt(0.5*0.5/10000) = 0.005; 4 sigma = 0.02
        assert abs(emp_probs["00"] - 0.5) < 0.025
        assert abs(emp_probs["11"] - 0.5) < 0.025
        assert np.isclose(emp_probs["00"] + emp_probs["11"], 1.0)

    def test_measure_bell_state_with_asymmetric_circuit_verifies_qubit_ordering(self) -> None:
        """Bug E: Pass an asymmetric state directly to measure_bell_state to verify bit mapping.

        Prepare q0=|1>, q1=|0>.
        In standard basis ordering 'q0 q1', the outcome must be '10'.
        If measure_bell_state swapped c0 and c1, it would return '01'.
        """
        qc = QuantumCircuit(2, 2)
        qc.x(0)  # q0 = |1>, q1 = |0>
        qc.measure(0, 0)
        qc.measure(1, 1)

        counts, emp_probs = measure_bell_state(shots=200, seed_simulator=1, circuit=qc)
        assert counts["10"] == 200
        assert counts["01"] == 0
        assert counts["00"] == 0
        assert counts["11"] == 0
        assert emp_probs["10"] == 1.0

        # Also test q0=|0>, q1=|1> -> '01'
        qc_01 = QuantumCircuit(2, 2)
        qc_01.x(1)  # q0 = |0>, q1 = |1>
        qc_01.measure(0, 0)
        qc_01.measure(1, 1)

        counts_01, emp_probs_01 = measure_bell_state(shots=200, seed_simulator=1, circuit=qc_01)
        assert counts_01["01"] == 200
        assert counts_01["10"] == 0
        assert emp_probs_01["01"] == 1.0


class TestBellBugCatchingSensitivity:
    """Robustness tests ensuring that realistic bugs fail the test suite."""

    def test_detects_omitted_hadamard_gate(self) -> None:
        """If Hadamard gate is omitted, state is |00> (Schmidt rank 1, not entangled)."""
        # Circuit without H: q0=|0>, q1=|0>, CNOT(0, 1) leaves state as |00>
        state_without_h = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.complex128)
        is_ent, rank, _ = check_entanglement(state_without_h)
        assert is_ent is False
        assert rank == 1

        probs = bell_computational_probabilities(state_without_h)
        assert probs["00"] == 1.0
        assert probs["11"] == 0.0

    def test_detects_omitted_cnot_gate(self) -> None:
        """If CNOT is omitted, state is |+0> (separable product state, Schmidt rank 1)."""
        # State: |+> (x) |0> = 1/sqrt(2)|00> + 1/sqrt(2)|10>
        state_without_cx = np.array([INV_SQRT_2, 0.0, INV_SQRT_2, 0.0], dtype=np.complex128)
        is_ent, rank, _ = check_entanglement(state_without_cx)
        assert is_ent is False
        assert rank == 1

        corr = calculate_bell_correlations(bell_computational_probabilities(state_without_cx))
        # No correlation: P_same = 0.5, P_diff = 0.5, corr = 0.0
        assert np.isclose(corr["correlation"], 0.0)

    def test_detects_wrong_bell_state_psi_plus(self) -> None:
        """If |Psi+> is created instead of |Phi+>, computational outcomes are 01 and 10, not 00 and 11."""
        psi_plus = create_bell_psi_plus()
        probs = bell_computational_probabilities(psi_plus)

        # Must NOT match |Phi+> distribution
        assert np.isclose(probs["00"], 0.0)
        assert np.isclose(probs["11"], 0.0)
        assert np.isclose(probs["01"], 0.5)
        assert np.isclose(probs["10"], 0.5)

        # Anti-correlated in computational basis
        corr = calculate_bell_correlations(probs)
        assert np.isclose(corr["correlation"], -1.0)

    def test_detects_sign_flip_phi_minus(self) -> None:
        """|Phi-> has <X(x)X> = -1.0, while |Phi+> has <X(x)X> = +1.0."""
        phi_minus = create_bell_phi_minus()

        xx_phi_plus = calculate_two_qubit_expectation_value(BELL_PHI_PLUS, PAULI_X, PAULI_X)
        xx_phi_minus = calculate_two_qubit_expectation_value(phi_minus, PAULI_X, PAULI_X)

        assert np.isclose(xx_phi_plus, 1.0)
        assert np.isclose(xx_phi_minus, -1.0)

    def test_detects_wrong_basis_ordering(self) -> None:
        """A permutation of basis states changes Born-rule probabilities."""
        # Swap index 0 (|00>) and index 1 (|01>): state = [0, 1/sqrt(2), 0, 1/sqrt(2)]
        permuted_state = np.array([0.0, INV_SQRT_2, 0.0, INV_SQRT_2], dtype=np.complex128)
        probs = bell_computational_probabilities(permuted_state)

        assert np.isclose(probs["00"], 0.0)
        assert np.isclose(probs["01"], 0.5)
        assert np.isclose(probs["10"], 0.0)
        assert np.isclose(probs["11"], 0.5)

    def test_detects_non_hermitian_operator_with_imaginary_expectation(self) -> None:
        """Non-Hermitian operator with imaginary expectation value must raise ValueError."""
        # Non-Hermitian operator: [[1, 2], [0, 1]]
        non_herm = np.array([[1.0, 2.0], [0.0, 1.0]], dtype=np.complex128)
        with pytest.raises(ValueError, match="must be real"):
            # On |+i> (x) |0>, non-Hermitian operator produces imaginary part
            state_complex = np.array([INV_SQRT_2, 0.0, 1.0j * INV_SQRT_2, 0.0], dtype=np.complex128)
            calculate_two_qubit_expectation_value(state_complex, non_herm, PAULI_I)


class TestBellInputValidationAndEdgeCases:
    """Edge cases, type validation, and error handling."""

    def test_invalid_dimension_raises(self) -> None:
        """Passing wrong vector length must raise ValueError."""
        with pytest.raises(ValueError, match="shape \\(4,\\)"):
            validate_two_qubit_state(np.array([1.0, 0.0]))

        with pytest.raises(ValueError, match="shape \\(4,\\)"):
            validate_two_qubit_state(np.zeros((5,)))

    def test_non_finite_values_raise(self) -> None:
        """NaN or Inf values must raise ValueError."""
        with pytest.raises(ValueError, match="finite"):
            validate_two_qubit_state(np.array([np.nan, 0.0, 0.0, 1.0]))

        with pytest.raises(ValueError, match="finite"):
            validate_two_qubit_state(np.array([np.inf, 0.0, 0.0, 1.0]))

    def test_zero_vector_raises(self) -> None:
        """Zero vector must raise ValueError."""
        with pytest.raises(ValueError, match="zero vector"):
            validate_two_qubit_state(np.zeros(4))

    def test_unnormalized_state_raises(self) -> None:
        """Unnormalized vector must raise ValueError."""
        with pytest.raises(ValueError, match="normalized"):
            validate_two_qubit_state(np.array([1.0, 1.0, 0.0, 0.0]))

    def test_invalid_shots_raises(self) -> None:
        """Shots <= 0 or non-integer must raise ValueError/TypeError."""
        with pytest.raises(ValueError, match="strictly positive integer"):
            measure_bell_state(shots=0)

        with pytest.raises(ValueError, match="strictly positive integer"):
            measure_bell_state(shots=-10)

        with pytest.raises(TypeError, match="Shots must be an integer"):
            measure_bell_state(shots=100.5)  # type: ignore

        with pytest.raises(TypeError, match="Shots must be an integer"):
            measure_bell_state(shots=True)  # type: ignore

    def test_invalid_seed_raises(self) -> None:
        """Negative or non-integer seed must raise ValueError/TypeError."""
        with pytest.raises(ValueError, match="non-negative integer"):
            measure_bell_state(shots=100, seed_simulator=-1)

        with pytest.raises(TypeError, match="Seed must be an integer"):
            measure_bell_state(shots=100, seed_simulator="seed")  # type: ignore

    def test_invalid_circuit_raises(self) -> None:
        """Passing non-circuit or 1-qubit circuit to measure_bell_state raises."""
        with pytest.raises(TypeError, match="Expected a QuantumCircuit"):
            measure_bell_state(circuit="not_a_circuit")  # type: ignore

        qc_1q = QuantumCircuit(1)
        with pytest.raises(ValueError, match="at least 2 qubits"):
            measure_bell_state(circuit=qc_1q)

    def test_correlation_negative_and_non_finite_counts_raise(self) -> None:
        """calculate_bell_correlations must reject negative and non-finite counts."""
        with pytest.raises(ValueError, match="cannot be negative"):
            calculate_bell_correlations({"00": 10, "01": -5, "10": 0, "11": 0})

        with pytest.raises(ValueError, match="must be finite"):
            calculate_bell_correlations({"00": float("nan"), "11": 10})

    def test_partial_trace_boolean_and_invalid_qubit_raise(self) -> None:
        """partial_trace_qubit must reject boolean or invalid indices."""
        with pytest.raises(ValueError, match="must be 0 or 1"):
            partial_trace_qubit(BELL_PHI_PLUS, trace_out_qubit=True)  # type: ignore

        with pytest.raises(ValueError, match="must be 0 or 1"):
            partial_trace_qubit(BELL_PHI_PLUS, trace_out_qubit=2)

    def test_bell_state_dataclass_interoperability(self) -> None:
        """BellState dataclass exposes properties, representations, and works across functions."""
        bs = BellState()
        assert np.allclose(bs.vector, BELL_PHI_PLUS)
        assert bs.is_entangled is True
        assert bs.shape == (4,)
        assert bs.dtype == np.complex128

        probs = bs.probabilities
        assert np.isclose(probs["00"], 0.5)
        assert np.isclose(probs["11"], 0.5)

        corrs = bs.correlations
        assert np.isclose(corrs["correlation"], 1.0)

        qc = bs.to_circuit()
        assert qc.num_qubits == 2

        # Array conversion
        arr = np.array(bs)
        assert np.allclose(arr, BELL_PHI_PLUS)

        # Repr detects |Phi+>
        assert "|Phi+>" in repr(bs)

        # Dataclass with other Bell states
        bs_minus = BellState(vector=BELL_PHI_MINUS)
        assert "|Phi->" in repr(bs_minus)
        qc_minus = bs_minus.to_circuit()
        sv_minus = Statevector.from_instruction(qc_minus).data
        assert np.allclose(sv_minus, BELL_PHI_MINUS)


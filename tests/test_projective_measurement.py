"""Tests for Milestone M3: Single-Qubit Projective Measurement.

Covers:
1. Basis Orthonormality (<b_i|b_j> = delta_ij) for Z, X, and Y bases.
2. Projector Properties: Idempotence (P² = P), Hermiticity (P† = P), Completeness (sum P = I), Orthogonality (P0 P1 = 0).
3. The 6 Mandatory Pauli Eigenstate Measurements:
   - |0> in Z  -> P(0) = 1, P(1) = 0
   - |1> in Z  -> P(0) = 0, P(1) = 1
   - |+> in X  -> P(+) = 1, P(-) = 0
   - |-> in X  -> P(+) = 0, P(-) = 1
   - |+i> in Y -> P(+i) = 1, P(-i) = 0
   - |-i> in Y -> P(+i) = 0, P(-i) = 1
4. The 6 Mandatory Wrong-Basis Measurements (~50/50):
   - |0> in X, |0> in Y
   - |+> in Z, |+> in Y
   - |+i> in Z, |+i> in X
5. Probability Properties:
   - Sum to 1, values in [0, 1]
   - Empirical frequencies match theoretical probabilities within statistical tolerance.
6. Pauli Expectation Values (<Z>, <X>, <Y>):
   - Analytical eigenvalues (+1 / -1) for eigenstates
   - 0 for orthogonal eigenstate-basis combinations
7. Qiskit Aer Cross-Validation:
   - Basis rotations (H for X, S†H for Y) simulated on Aer match theoretical Born-rule predictions.
8. Edge-Case Validation:
   - Invalid basis, invalid shots, negative shots, non-finite values, seed reproducibility, QubitState support.
"""

from __future__ import annotations

import numpy as np
import pytest
from qiskit_aer import AerSimulator

from src.quantum.states import (
    STATE_0,
    STATE_1,
    STATE_PLUS,
    STATE_MINUS,
    STATE_PLUS_I,
    STATE_MINUS_I,
    QubitState,
)
from src.quantum.measurements import (
    PROJECTOR_Z_0,
    PROJECTOR_Z_1,
    PROJECTOR_X_PLUS,
    PROJECTOR_X_MINUS,
    PROJECTOR_Y_PLUS_I,
    PROJECTOR_Y_MINUS_I,
    get_basis_projectors,
    get_basis_states,
    projective_probabilities,
    sample_measurement,
    calculate_empirical_probabilities,
    calculate_expectation_value,
    measure_projective,
    create_basis_measurement_circuit,
    measure_qubit,
)


class TestBasisOrthonormalityAndProjectors:
    """Mathematical validation of basis vectors and projector operators."""

    def test_z_basis_orthonormality(self) -> None:
        """Z basis: <0|0>=1, <1|1>=1, <0|1>=0."""
        s0, s1, labels = get_basis_states("Z")
        assert labels == ("0", "1")
        assert np.isclose(np.vdot(s0, s0), 1.0)
        assert np.isclose(np.vdot(s1, s1), 1.0)
        assert np.isclose(np.vdot(s0, s1), 0.0)

    def test_x_basis_orthonormality(self) -> None:
        """X basis: <+|+>=1, <-|->=1, <+|->=0."""
        sp, sm, labels = get_basis_states("X")
        assert labels == ("+", "-")
        assert np.isclose(np.vdot(sp, sp), 1.0)
        assert np.isclose(np.vdot(sm, sm), 1.0)
        assert np.isclose(np.vdot(sp, sm), 0.0)

    def test_y_basis_orthonormality(self) -> None:
        """Y basis: <+i|+i>=1, <-i|-i>=1, <+i|-i>=0."""
        spi, smi, labels = get_basis_states("Y")
        assert labels == ("+i", "-i")
        assert np.isclose(np.vdot(spi, spi), 1.0)
        assert np.isclose(np.vdot(smi, smi), 1.0)
        assert np.isclose(np.vdot(spi, smi), 0.0)

    def test_projector_idempotence(self) -> None:
        """Projectors must satisfy P_i² = P_i."""
        projectors = [
            PROJECTOR_Z_0,
            PROJECTOR_Z_1,
            PROJECTOR_X_PLUS,
            PROJECTOR_X_MINUS,
            PROJECTOR_Y_PLUS_I,
            PROJECTOR_Y_MINUS_I,
        ]
        for p in projectors:
            assert np.allclose(p @ p, p)

    def test_projector_hermiticity(self) -> None:
        """Projectors must be Hermitian: P_i† = P_i."""
        projectors = [
            PROJECTOR_Z_0,
            PROJECTOR_Z_1,
            PROJECTOR_X_PLUS,
            PROJECTOR_X_MINUS,
            PROJECTOR_Y_PLUS_I,
            PROJECTOR_Y_MINUS_I,
        ]
        for p in projectors:
            assert np.allclose(p.conj().T, p)

    def test_projector_completeness(self) -> None:
        """Projectors for each basis must sum to identity: sum P_i = I."""
        identity = np.eye(2, dtype=np.complex128)
        assert np.allclose(PROJECTOR_Z_0 + PROJECTOR_Z_1, identity)
        assert np.allclose(PROJECTOR_X_PLUS + PROJECTOR_X_MINUS, identity)
        assert np.allclose(PROJECTOR_Y_PLUS_I + PROJECTOR_Y_MINUS_I, identity)

    def test_projector_orthogonality(self) -> None:
        """Orthogonal projectors must satisfy P_0 P_1 = 0."""
        zero = np.zeros((2, 2), dtype=np.complex128)
        assert np.allclose(PROJECTOR_Z_0 @ PROJECTOR_Z_1, zero)
        assert np.allclose(PROJECTOR_X_PLUS @ PROJECTOR_X_MINUS, zero)
        assert np.allclose(PROJECTOR_Y_PLUS_I @ PROJECTOR_Y_MINUS_I, zero)


class TestPauliEigenstateMeasurements:
    """The 6 mandatory eigenstate measurements in their native bases."""

    def test_measure_state_0_in_z_basis(self) -> None:
        """|0> in Z: P(0) = 1.0, P(1) = 0.0."""
        probs = projective_probabilities(STATE_0, basis="Z")
        assert probs["0"] == 1.0
        assert probs["1"] == 0.0

        counts, emp_probs = measure_projective(STATE_0, basis="Z", shots=1000, seed=42)
        assert counts["0"] == 1000
        assert counts["1"] == 0
        assert emp_probs["0"] == 1.0
        assert emp_probs["1"] == 0.0

    def test_measure_state_1_in_z_basis(self) -> None:
        """|1> in Z: P(0) = 0.0, P(1) = 1.0."""
        probs = projective_probabilities(STATE_1, basis="Z")
        assert probs["0"] == 0.0
        assert probs["1"] == 1.0

        counts, emp_probs = measure_projective(STATE_1, basis="Z", shots=1000, seed=42)
        assert counts["0"] == 0
        assert counts["1"] == 1000
        assert emp_probs["0"] == 0.0
        assert emp_probs["1"] == 1.0

    def test_measure_state_plus_in_x_basis(self) -> None:
        """|+> in X: P(+) = 1.0, P(-) = 0.0."""
        probs = projective_probabilities(STATE_PLUS, basis="X")
        assert probs["+"] == 1.0
        assert probs["-"] == 0.0

        counts, emp_probs = measure_projective(STATE_PLUS, basis="X", shots=1000, seed=42)
        assert counts["+"] == 1000
        assert counts["-"] == 0
        assert emp_probs["+"] == 1.0
        assert emp_probs["-"] == 0.0

    def test_measure_state_minus_in_x_basis(self) -> None:
        """|-> in X: P(+) = 0.0, P(-) = 1.0."""
        probs = projective_probabilities(STATE_MINUS, basis="X")
        assert probs["+"] == 0.0
        assert probs["-"] == 1.0

        counts, emp_probs = measure_projective(STATE_MINUS, basis="X", shots=1000, seed=42)
        assert counts["+"] == 0
        assert counts["-"] == 1000
        assert emp_probs["+"] == 0.0
        assert emp_probs["-"] == 1.0

    def test_measure_state_plus_i_in_y_basis(self) -> None:
        """|+i> in Y: P(+i) = 1.0, P(-i) = 0.0."""
        probs = projective_probabilities(STATE_PLUS_I, basis="Y")
        assert probs["+i"] == 1.0
        assert probs["-i"] == 0.0

        counts, emp_probs = measure_projective(STATE_PLUS_I, basis="Y", shots=1000, seed=42)
        assert counts["+i"] == 1000
        assert counts["-i"] == 0
        assert emp_probs["+i"] == 1.0
        assert emp_probs["-i"] == 0.0

    def test_measure_state_minus_i_in_y_basis(self) -> None:
        """|-i> in Y: P(+i) = 0.0, P(-i) = 1.0."""
        probs = projective_probabilities(STATE_MINUS_I, basis="Y")
        assert probs["+i"] == 0.0
        assert probs["-i"] == 1.0

        counts, emp_probs = measure_projective(STATE_MINUS_I, basis="Y", shots=1000, seed=42)
        assert counts["+i"] == 0
        assert counts["-i"] == 1000
        assert emp_probs["+i"] == 0.0
        assert emp_probs["-i"] == 1.0


class TestWrongBasisMeasurements:
    """The 6 mandatory wrong-basis measurements (~50/50 probabilistic)."""

    def test_state_0_in_x_basis(self) -> None:
        """|0> in X: theoretical P(+)=0.5, P(-)=0.5; empirical ~50/50."""
        probs = projective_probabilities(STATE_0, basis="X")
        assert np.isclose(probs["+"], 0.5)
        assert np.isclose(probs["-"], 0.5)

        counts, emp = measure_projective(STATE_0, basis="X", shots=10000, seed=101)
        assert counts["+"] > 0 and counts["-"] > 0
        assert abs(emp["+"] - 0.5) < 0.035
        assert abs(emp["-"] - 0.5) < 0.035

    def test_state_0_in_y_basis(self) -> None:
        """|0> in Y: theoretical P(+i)=0.5, P(-i)=0.5; empirical ~50/50."""
        probs = projective_probabilities(STATE_0, basis="Y")
        assert np.isclose(probs["+i"], 0.5)
        assert np.isclose(probs["-i"], 0.5)

        counts, emp = measure_projective(STATE_0, basis="Y", shots=10000, seed=102)
        assert counts["+i"] > 0 and counts["-i"] > 0
        assert abs(emp["+i"] - 0.5) < 0.035
        assert abs(emp["-i"] - 0.5) < 0.035

    def test_state_plus_in_z_basis(self) -> None:
        """|+> in Z: theoretical P(0)=0.5, P(1)=0.5; empirical ~50/50."""
        probs = projective_probabilities(STATE_PLUS, basis="Z")
        assert np.isclose(probs["0"], 0.5)
        assert np.isclose(probs["1"], 0.5)

        counts, emp = measure_projective(STATE_PLUS, basis="Z", shots=10000, seed=103)
        assert counts["0"] > 0 and counts["1"] > 0
        assert abs(emp["0"] - 0.5) < 0.035
        assert abs(emp["1"] - 0.5) < 0.035

    def test_state_plus_in_y_basis(self) -> None:
        """|+> in Y: theoretical P(+i)=0.5, P(-i)=0.5; empirical ~50/50."""
        probs = projective_probabilities(STATE_PLUS, basis="Y")
        assert np.isclose(probs["+i"], 0.5)
        assert np.isclose(probs["-i"], 0.5)

        counts, emp = measure_projective(STATE_PLUS, basis="Y", shots=10000, seed=104)
        assert counts["+i"] > 0 and counts["-i"] > 0
        assert abs(emp["+i"] - 0.5) < 0.035
        assert abs(emp["-i"] - 0.5) < 0.035

    def test_state_plus_i_in_z_basis(self) -> None:
        """|+i> in Z: theoretical P(0)=0.5, P(1)=0.5; empirical ~50/50."""
        probs = projective_probabilities(STATE_PLUS_I, basis="Z")
        assert np.isclose(probs["0"], 0.5)
        assert np.isclose(probs["1"], 0.5)

        counts, emp = measure_projective(STATE_PLUS_I, basis="Z", shots=10000, seed=105)
        assert counts["0"] > 0 and counts["1"] > 0
        assert abs(emp["0"] - 0.5) < 0.035
        assert abs(emp["1"] - 0.5) < 0.035

    def test_state_plus_i_in_x_basis(self) -> None:
        """|+i> in X: theoretical P(+)=0.5, P(-)=0.5; empirical ~50/50."""
        probs = projective_probabilities(STATE_PLUS_I, basis="X")
        assert np.isclose(probs["+"], 0.5)
        assert np.isclose(probs["-"], 0.5)

        counts, emp = measure_projective(STATE_PLUS_I, basis="X", shots=10000, seed=106)
        assert counts["+"] > 0 and counts["-"] > 0
        assert abs(emp["+"] - 0.5) < 0.035
        assert abs(emp["-"] - 0.5) < 0.035

    def test_state_1_in_x_basis(self) -> None:
        """|1> in X: theoretical P(+)=0.5, P(-)=0.5; empirical ~50/50."""
        probs = projective_probabilities(STATE_1, basis="X")
        assert np.isclose(probs["+"], 0.5)
        assert np.isclose(probs["-"], 0.5)

        counts, emp = measure_projective(STATE_1, basis="X", shots=10000, seed=107)
        assert counts["+"] > 0 and counts["-"] > 0
        assert abs(emp["+"] - 0.5) < 0.035
        assert abs(emp["-"] - 0.5) < 0.035

    def test_state_1_in_y_basis(self) -> None:
        """|1> in Y: theoretical P(+i)=0.5, P(-i)=0.5; empirical ~50/50."""
        probs = projective_probabilities(STATE_1, basis="Y")
        assert np.isclose(probs["+i"], 0.5)
        assert np.isclose(probs["-i"], 0.5)

        counts, emp = measure_projective(STATE_1, basis="Y", shots=10000, seed=108)
        assert counts["+i"] > 0 and counts["-i"] > 0
        assert abs(emp["+i"] - 0.5) < 0.035
        assert abs(emp["-i"] - 0.5) < 0.035

    def test_state_minus_in_z_basis(self) -> None:
        """|-> in Z: theoretical P(0)=0.5, P(1)=0.5; empirical ~50/50."""
        probs = projective_probabilities(STATE_MINUS, basis="Z")
        assert np.isclose(probs["0"], 0.5)
        assert np.isclose(probs["1"], 0.5)

        counts, emp = measure_projective(STATE_MINUS, basis="Z", shots=10000, seed=109)
        assert counts["0"] > 0 and counts["1"] > 0
        assert abs(emp["0"] - 0.5) < 0.035
        assert abs(emp["1"] - 0.5) < 0.035

    def test_state_minus_in_y_basis(self) -> None:
        """|-> in Y: theoretical P(+i)=0.5, P(-i)=0.5; empirical ~50/50."""
        probs = projective_probabilities(STATE_MINUS, basis="Y")
        assert np.isclose(probs["+i"], 0.5)
        assert np.isclose(probs["-i"], 0.5)

        counts, emp = measure_projective(STATE_MINUS, basis="Y", shots=10000, seed=110)
        assert counts["+i"] > 0 and counts["-i"] > 0
        assert abs(emp["+i"] - 0.5) < 0.035
        assert abs(emp["-i"] - 0.5) < 0.035

    def test_state_minus_i_in_z_basis(self) -> None:
        """|-i> in Z: theoretical P(0)=0.5, P(1)=0.5; empirical ~50/50."""
        probs = projective_probabilities(STATE_MINUS_I, basis="Z")
        assert np.isclose(probs["0"], 0.5)
        assert np.isclose(probs["1"], 0.5)

        counts, emp = measure_projective(STATE_MINUS_I, basis="Z", shots=10000, seed=111)
        assert counts["0"] > 0 and counts["1"] > 0
        assert abs(emp["0"] - 0.5) < 0.035
        assert abs(emp["1"] - 0.5) < 0.035

    def test_state_minus_i_in_x_basis(self) -> None:
        """|-i> in X: theoretical P(+)=0.5, P(-)=0.5; empirical ~50/50."""
        probs = projective_probabilities(STATE_MINUS_I, basis="X")
        assert np.isclose(probs["+"], 0.5)
        assert np.isclose(probs["-"], 0.5)

        counts, emp = measure_projective(STATE_MINUS_I, basis="X", shots=10000, seed=112)
        assert counts["+"] > 0 and counts["-"] > 0
        assert abs(emp["+"] - 0.5) < 0.035
        assert abs(emp["-"] - 0.5) < 0.035


class TestExpectationValues:
    """Verification of Pauli expectation values <Z>, <X>, <Y>."""

    def test_expectation_values_z_eigenstates(self) -> None:
        """<Z> = +1 for |0>, <Z> = -1 for |1>."""
        p0 = projective_probabilities(STATE_0, basis="Z")
        p1 = projective_probabilities(STATE_1, basis="Z")
        assert np.isclose(calculate_expectation_value(p0, basis="Z"), 1.0)
        assert np.isclose(calculate_expectation_value(p1, basis="Z"), -1.0)

    def test_expectation_values_x_eigenstates(self) -> None:
        """<X> = +1 for |+>, <X> = -1 for |->."""
        pp = projective_probabilities(STATE_PLUS, basis="X")
        pm = projective_probabilities(STATE_MINUS, basis="X")
        assert np.isclose(calculate_expectation_value(pp, basis="X"), 1.0)
        assert np.isclose(calculate_expectation_value(pm, basis="X"), -1.0)

    def test_expectation_values_y_eigenstates(self) -> None:
        """<Y> = +1 for |+i>, <Y> = -1 for |-i>."""
        py_plus = projective_probabilities(STATE_PLUS_I, basis="Y")
        py_minus = projective_probabilities(STATE_MINUS_I, basis="Y")
        assert np.isclose(calculate_expectation_value(py_plus, basis="Y"), 1.0)
        assert np.isclose(calculate_expectation_value(py_minus, basis="Y"), -1.0)

    def test_expectation_values_orthogonal_bases_zero(self) -> None:
        """<X> for |0> = 0, <Y> for |0> = 0, <Z> for |+> = 0."""
        p_0_x = projective_probabilities(STATE_0, basis="X")
        p_0_y = projective_probabilities(STATE_0, basis="Y")
        p_plus_z = projective_probabilities(STATE_PLUS, basis="Z")
        assert np.isclose(calculate_expectation_value(p_0_x, basis="X"), 0.0)
        assert np.isclose(calculate_expectation_value(p_0_y, basis="Y"), 0.0)
        assert np.isclose(calculate_expectation_value(p_plus_z, basis="Z"), 0.0)

    def test_expectation_value_from_counts_dict(self) -> None:
        """calculate_expectation_value correctly converts raw counts."""
        assert np.isclose(calculate_expectation_value({"0": 750, "1": 250}, basis="Z"), 0.5)
        assert np.isclose(calculate_expectation_value({"+": 1000, "-": 0}, basis="X"), 1.0)
        assert np.isclose(calculate_expectation_value({"+i": 500, "-i": 500}, basis="Y"), 0.0)


class TestQiskitBasisMeasurementValidation:
    """Validation of basis rotations and Aer simulation consistency."""

    def test_qiskit_x_basis_measurement(self) -> None:
        """Hadamard rotation maps X-basis states to computational states."""
        qc_plus = create_basis_measurement_circuit(STATE_PLUS, basis="X")
        sim = AerSimulator()
        counts_plus = measure_qubit(qc_plus, shots=1000, simulator=sim, seed_simulator=1)
        # Outcome '0' corresponds to |+>
        assert counts_plus["0"] == 1000
        assert counts_plus["1"] == 0

        qc_minus = create_basis_measurement_circuit(STATE_MINUS, basis="X")
        counts_minus = measure_qubit(qc_minus, shots=1000, simulator=sim, seed_simulator=1)
        # Outcome '1' corresponds to |->
        assert counts_minus["0"] == 0
        assert counts_minus["1"] == 1000

    def test_qiskit_y_basis_measurement(self) -> None:
        """S† then H rotation maps Y-basis states to computational states."""
        qc_plus_i = create_basis_measurement_circuit(STATE_PLUS_I, basis="Y")
        sim = AerSimulator()
        counts_plus_i = measure_qubit(qc_plus_i, shots=1000, simulator=sim, seed_simulator=2)
        # Outcome '0' corresponds to |+i>
        assert counts_plus_i["0"] == 1000
        assert counts_plus_i["1"] == 0

        qc_minus_i = create_basis_measurement_circuit(STATE_MINUS_I, basis="Y")
        counts_minus_i = measure_qubit(qc_minus_i, shots=1000, simulator=sim, seed_simulator=2)
        # Outcome '1' corresponds to |-i>
        assert counts_minus_i["0"] == 0
        assert counts_minus_i["1"] == 1000


class TestProjectiveMeasurementEdgeCases:
    """Input validation, edge cases, and error handling."""

    def test_arbitrary_state_probability_properties(self) -> None:
        """Arbitrary superposition state probabilities sum to 1, are in [0, 1], and match empirical."""
        # |psi> = cos(pi/6)|0> + exp(i*pi/4)*sin(pi/6)|1>
        theta = np.pi / 6
        phi = np.pi / 4
        psi = np.array([np.cos(theta), np.exp(1j * phi) * np.sin(theta)], dtype=np.complex128)

        for basis in ("Z", "X", "Y"):
            probs = projective_probabilities(psi, basis=basis)
            assert np.isclose(sum(probs.values()), 1.0)
            for p in probs.values():
                assert 0.0 <= p <= 1.0

            counts, emp = measure_projective(psi, basis=basis, shots=20000, seed=777)
            for k in probs:
                assert abs(emp[k] - probs[k]) < 0.02

    def test_seed_reproducibility(self) -> None:
        """Fixed random seed must yield identical counts; different seeds yield varying counts."""
        c1, _ = measure_projective(STATE_PLUS, basis="Z", shots=2000, seed=12345)
        c2, _ = measure_projective(STATE_PLUS, basis="Z", shots=2000, seed=12345)
        assert c1 == c2

        c3, _ = measure_projective(STATE_PLUS, basis="Z", shots=2000, seed=54321)
        # With 2000 shots on a 50/50 state, probability of identical counts across seeds is negligible
        assert c1 != c3

    def test_invalid_basis_raises(self) -> None:
        """Unrecognized basis string must raise ValueError."""
        with pytest.raises(ValueError, match="Unknown measurement basis"):
            get_basis_projectors("W")

        with pytest.raises(ValueError, match="Unknown measurement basis"):
            projective_probabilities(STATE_0, basis="invalid")

        with pytest.raises(ValueError, match="Unknown measurement basis"):
            calculate_expectation_value({"0": 1.0}, basis="unknown")

    def test_invalid_shots_raises(self) -> None:
        """Shots <= 0 or non-integer must raise ValueError/TypeError."""
        with pytest.raises(ValueError, match="strictly positive integer"):
            sample_measurement({"+": 0.5, "-": 0.5}, shots=0)

        with pytest.raises(ValueError, match="strictly positive integer"):
            sample_measurement({"+": 0.5, "-": 0.5}, shots=-500)

        with pytest.raises(TypeError, match="Shots must be an integer"):
            sample_measurement({"+": 0.5, "-": 0.5}, shots=100.5)  # type: ignore

        with pytest.raises(TypeError, match="Shots must be an integer"):
            sample_measurement({"+": 0.5, "-": 0.5}, shots=True)  # type: ignore

    def test_invalid_seed_raises(self) -> None:
        """Negative seed or non-integer seed must raise ValueError/TypeError."""
        with pytest.raises(ValueError, match="non-negative integer"):
            sample_measurement({"+": 0.5, "-": 0.5}, shots=100, seed=-1)

        with pytest.raises(TypeError, match="Seed must be an integer"):
            sample_measurement({"+": 0.5, "-": 0.5}, shots=100, seed="seed")  # type: ignore

    def test_invalid_state_raises(self) -> None:
        """Invalid state vectors (wrong length, non-finite, unnormalized) must raise ValueError."""
        with pytest.raises(ValueError, match="shape \\(2,\\)"):
            projective_probabilities(np.array([1.0, 0.0, 0.0]), basis="X")

        with pytest.raises(ValueError, match="finite"):
            projective_probabilities(np.array([np.nan, 0.0]), basis="Z")

        with pytest.raises(ValueError, match="normalized"):
            projective_probabilities(np.array([1.0, 1.0]), basis="Z")

        with pytest.raises(ValueError, match="zero vector"):
            projective_probabilities(np.array([0.0, 0.0]), basis="Z")

    def test_qubit_state_dataclass_support(self) -> None:
        """projective_probabilities and measure_projective accept QubitState instances."""
        qs = QubitState(STATE_PLUS)
        probs = projective_probabilities(qs, basis="X")
        assert np.isclose(probs["+"], 1.0)
        assert np.isclose(probs["-"], 0.0)

        counts, emp = measure_projective(qs, basis="X", shots=500, seed=42)
        assert counts["+"] == 500
        assert counts["-"] == 0

    def test_calculate_expectation_value_mismatched_labels_raises(self) -> None:
        """calculate_expectation_value must raise ValueError when outcome labels do not match requested basis."""
        with pytest.raises(ValueError, match="Expected outcome labels"):
            calculate_expectation_value({"0": 1.0, "1": 0.0}, basis="X")

        with pytest.raises(ValueError, match="Expected outcome labels"):
            calculate_expectation_value({"0": 1.0, "1": 0.0}, basis="Y")

        with pytest.raises(ValueError, match="Expected outcome labels"):
            calculate_expectation_value({"+": 1.0, "-": 0.0}, basis="Z")

        with pytest.raises(ValueError, match="non-empty dictionary"):
            calculate_expectation_value({}, basis="Z")

    def test_calculate_empirical_probabilities_unrecognized_labels_raises(self) -> None:
        """calculate_empirical_probabilities must raise ValueError when unknown labels are mixed with basis labels."""
        with pytest.raises(ValueError, match="Unrecognized outcome labels"):
            calculate_empirical_probabilities({"0": 500, "invalid": 100})

        with pytest.raises(ValueError, match="Unrecognized outcome labels"):
            calculate_empirical_probabilities({"+": 500, "-": 400, "extra": 100})

        with pytest.raises(ValueError, match="Unrecognized outcome labels"):
            calculate_empirical_probabilities({"+i": 500, "-i": 400, "extra": 100})


class TestGeneralQuantumStatesAndBornRule:
    """Rigorous Born-rule validation on general pure states with complex amplitudes."""

    @pytest.mark.parametrize(
        "alpha, beta",
        [
            # Real superposition: 1/sqrt(5)|0> + 2/sqrt(5)|1>
            (1.0 / np.sqrt(5.0), 2.0 / np.sqrt(5.0)),
            # Complex phase state: 1/2|0> + i*sqrt(3)/2|1>
            (0.5, 1j * np.sqrt(3.0) / 2.0),
            # General Bloch state: cos(theta/2)|0> + exp(i*phi)*sin(theta/2)|1>
            (np.cos(0.4), np.exp(1.2j) * np.sin(0.4)),
            # Asymmetric complex amplitudes
            ((1.0 + 1.0j) / 2.0, (1.0 - 1.0j) / 2.0),
        ],
    )
    def test_general_state_born_rule_across_all_bases(self, alpha: complex, beta: complex) -> None:
        """Verify Born rule P(i) = |<b_i|psi>|^2 across Z, X, Y for general pure states."""
        psi = np.array([alpha, beta], dtype=np.complex128)
        assert np.isclose(np.vdot(psi, psi), 1.0)

        from src.quantum.pauli import PAULI_Z, PAULI_X, PAULI_Y

        pauli_ops = {"Z": PAULI_Z, "X": PAULI_X, "Y": PAULI_Y}

        for basis in ("Z", "X", "Y"):
            probs = projective_probabilities(psi, basis=basis)
            s0, s1, (lbl0, lbl1) = get_basis_states(basis)

            # Exact Born rule analytical values: P(i) = |<b_i|psi>|^2
            expected_p0 = float(np.abs(np.vdot(s0, psi)) ** 2)
            expected_p1 = float(np.abs(np.vdot(s1, psi)) ** 2)

            assert np.isclose(probs[lbl0], expected_p0, atol=1e-7)
            assert np.isclose(probs[lbl1], expected_p1, atol=1e-7)
            assert np.isclose(probs[lbl0] + probs[lbl1], 1.0, atol=1e-7)
            assert 0.0 <= probs[lbl0] <= 1.0
            assert 0.0 <= probs[lbl1] <= 1.0

            # Expectation value must equal <psi|Observable|psi>
            exp_val = calculate_expectation_value(probs, basis=basis)
            expected_exp_val = float(np.real(np.vdot(psi, pauli_ops[basis] @ psi)))
            assert np.isclose(exp_val, expected_exp_val, atol=1e-7)

            # Sampling consistency within 3 standard deviations
            shots = 20000
            counts, emp = measure_projective(psi, basis=basis, shots=shots, seed=42)
            # Std error = sqrt(p*(1-p)/N) <= sqrt(0.25/20000) = 0.0035; 3 sigma ~ 0.015
            for k in (lbl0, lbl1):
                assert abs(emp[k] - probs[k]) < 0.025


class TestBugCatchingSensitivity:
    """Regression suite demonstrating that tests would fail on realistic implementation bugs."""

    def test_detects_basis_swap_x_and_z(self) -> None:
        """Measuring |0> in X gives 0.5/0.5, while in Z it gives 1.0/0.0."""
        pz = projective_probabilities(STATE_0, basis="Z")
        px = projective_probabilities(STATE_0, basis="X")
        # If X and Z were swapped, pz["0"] would be 0.5 instead of 1.0
        assert np.isclose(pz["0"], 1.0)
        assert np.isclose(px["+"], 0.5)
        assert not np.isclose(pz["0"], px["+"])

    def test_detects_basis_replacement_y_with_x(self) -> None:
        """Measuring |+i> in Y gives 1.0/0.0, while in X it gives 0.5/0.5."""
        py = projective_probabilities(STATE_PLUS_I, basis="Y")
        px = projective_probabilities(STATE_PLUS_I, basis="X")
        # If Y was replaced with X, py["+i"] would be 0.5 instead of 1.0
        assert np.isclose(py["+i"], 1.0)
        assert np.isclose(px["+"], 0.5)
        assert not np.isclose(py["+i"], px["+"])

    def test_detects_missing_imaginary_in_y_basis(self) -> None:
        """Stripping imaginary 'i' from Y state produces wrong Y measurement outcomes."""
        stripped_state = np.array([1.0, 1.0], dtype=np.complex128) / np.sqrt(2.0)  # |+>
        probs_stripped = projective_probabilities(stripped_state, basis="Y")
        # Stripped state (|x>) measured in Y gives 50/50, NOT 100/0
        assert np.isclose(probs_stripped["+i"], 0.5)
        assert np.isclose(probs_stripped["-i"], 0.5)

    def test_detects_transpose_instead_of_conjugate_transpose(self) -> None:
        """Using transpose instead of conjugate-transpose fails Hermiticity and creates invalid trace."""
        # For |+i> = [1, i]/sqrt(2), transpose gives non-Hermitian matrix with trace 0
        v = STATE_PLUS_I
        p_transpose = np.outer(v, v)  # Bug: missing .conj()
        p_correct = PROJECTOR_Y_PLUS_I

        # p_transpose has trace (1/2)(1 - 1) = 0 != 1
        assert not np.isclose(np.trace(p_transpose), 1.0)
        # p_transpose is NOT Hermitian: P^T != P†
        assert not np.allclose(p_transpose.conj().T, p_transpose)
        # p_correct IS Hermitian and has trace 1
        assert np.isclose(np.trace(p_correct), 1.0)
        assert np.allclose(p_correct.conj().T, p_correct)

    def test_detects_reversed_outcome_labels(self) -> None:
        """Reversed outcome labels would invert expectation values."""
        pz = projective_probabilities(STATE_0, basis="Z")
        px = projective_probabilities(STATE_PLUS, basis="X")
        py = projective_probabilities(STATE_PLUS_I, basis="Y")

        assert calculate_expectation_value(pz, basis="Z") == 1.0
        assert calculate_expectation_value(px, basis="X") == 1.0
        assert calculate_expectation_value(py, basis="Y") == 1.0

        # If labels were inverted (e.g. 0->-1, 1->+1), expectation value would be -1.0
        reversed_pz = {"0": pz["1"], "1": pz["0"]}
        assert calculate_expectation_value(reversed_pz, basis="Z") == -1.0

    def test_unnormalized_state_strictly_rejected(self) -> None:
        """Unnormalized states must be rejected with ValueError and not silently normalized."""
        unnormalized = np.array([2.0, 0.0], dtype=np.complex128)
        with pytest.raises(ValueError, match="normalized"):
            projective_probabilities(unnormalized, basis="Z")

        with pytest.raises(ValueError, match="normalized"):
            measure_projective(unnormalized, basis="Z")

    def test_requested_shots_preserved(self) -> None:
        """Requested shot count must be strictly honored across varying shot sizes."""
        for shots in (50, 250, 777, 1024, 4096):
            counts, _ = measure_projective(STATE_0, basis="Z", shots=shots)
            assert sum(counts.values()) == shots

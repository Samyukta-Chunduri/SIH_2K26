"""Tests for single-qubit Pauli operators and mathematical state transformations (Milestone M2).

Covers all 32 required tests:
1. I matrix is correct.
2. X matrix is correct.
3. Y matrix is correct.
4. Z matrix is correct.
5. All operators are 2x2.
6. All operators are complex-compatible (specifically Y has imaginary components, not real).
7. All operators are Hermitian (U† = U).
8. All operators are unitary (U†U = I).
9. I² = I.
10. X² = I.
11. Y² = I.
12. Z² = I.
13. I|0> = |0>.
14. I|1> = |1>.
15. X|0> = |1>.
16. X|1> = |0>.
17. Y|0> = i|1>.
18. Y|1> = -i|0>.
19. Z|0> = |0>.
20. Z|1> = -|1>.
21. X|+> = |+>.
22. X|-> = -|->.
23. Z|+> = |->.
24. Z|-> = |+>.
25. Y|+i> = |+i>.
26. Y|-i> = -|-i>.
27. Pauli operators preserve normalization.
28. XY = -YX.
29. YZ = -ZY.
30. ZX = -XZ.
31. Invalid operator dimensions are rejected.
32. Invalid state dimensions are rejected.
"""

from __future__ import annotations

import numpy as np
import pytest

from src.quantum.states import (
    STATE_0,
    STATE_1,
    STATE_PLUS,
    STATE_MINUS,
    STATE_PLUS_I,
    STATE_MINUS_I,
    QubitState,
    is_normalized,
    validate_state_vector,
)
from src.quantum.pauli import (
    PAULI_I,
    PAULI_X,
    PAULI_Y,
    PAULI_Z,
    identity_operator,
    pauli_x,
    pauli_y,
    pauli_z,
    get_pauli_operator,
    validate_operator,
    is_hermitian,
    is_unitary,
    apply_operator,
)


class TestPauliMatrixRepresentations:
    """Tests 1-6: Matrix correctness, dimensions, and complex compatibility."""

    def test_01_identity_matrix_correct(self) -> None:
        """1. I matrix is correct: [[1, 0], [0, 1]]."""
        expected = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.complex128)
        assert np.allclose(PAULI_I, expected)
        assert np.allclose(identity_operator(), expected)
        assert np.allclose(get_pauli_operator("I"), expected)
        assert np.allclose(get_pauli_operator("identity"), expected)

    def test_02_pauli_x_matrix_correct(self) -> None:
        """2. X matrix is correct: [[0, 1], [1, 0]]."""
        expected = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128)
        assert np.allclose(PAULI_X, expected)
        assert np.allclose(pauli_x(), expected)
        assert np.allclose(get_pauli_operator("X"), expected)
        assert np.allclose(get_pauli_operator("pauli_x"), expected)

    def test_03_pauli_y_matrix_correct(self) -> None:
        """3. Y matrix is correct: [[0, -i], [i, 0]]."""
        expected = np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=np.complex128)
        assert np.allclose(PAULI_Y, expected)
        assert np.allclose(pauli_y(), expected)
        assert np.allclose(get_pauli_operator("Y"), expected)
        assert np.allclose(get_pauli_operator("pauli_y"), expected)

    def test_04_pauli_z_matrix_correct(self) -> None:
        """4. Z matrix is correct: [[1, 0], [0, -1]]."""
        expected = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128)
        assert np.allclose(PAULI_Z, expected)
        assert np.allclose(pauli_z(), expected)
        assert np.allclose(get_pauli_operator("Z"), expected)
        assert np.allclose(get_pauli_operator("pauli_z"), expected)

    def test_05_all_operators_are_2x2(self) -> None:
        """5. All operators have exact shape (2, 2)."""
        for op in [PAULI_I, PAULI_X, PAULI_Y, PAULI_Z]:
            assert op.shape == (2, 2)
            assert op.ndim == 2

    def test_06_all_operators_are_complex_compatible(self) -> None:
        """6. All operators are complex-compatible; specifically Y has imaginary entries."""
        for op in [PAULI_I, PAULI_X, PAULI_Y, PAULI_Z]:
            assert np.issubdtype(op.dtype, np.complexfloating)

        # Explicitly verify Y is NOT a real rotation matrix [[0, -1], [1, 0]]
        fake_real_y = np.array([[0.0, -1.0], [1.0, 0.0]], dtype=np.complex128)
        assert not np.allclose(PAULI_Y, fake_real_y)
        assert np.isclose(PAULI_Y[0, 1].imag, -1.0)
        assert np.isclose(PAULI_Y[1, 0].imag, 1.0)


class TestPauliAlgebraicProperties:
    """Tests 7-12, 28-30: Hermiticity, Unitarity, Involutory (Squaring), and Anti-commutation."""

    def test_07_all_operators_are_hermitian(self) -> None:
        """7. All operators are Hermitian: U† = U."""
        for op in [PAULI_I, PAULI_X, PAULI_Y, PAULI_Z]:
            assert is_hermitian(op)
            assert np.allclose(op, op.conj().T)

    def test_08_all_operators_are_unitary(self) -> None:
        """8. All operators are unitary: U†U = I."""
        identity = np.eye(2, dtype=np.complex128)
        for op in [PAULI_I, PAULI_X, PAULI_Y, PAULI_Z]:
            assert is_unitary(op)
            assert np.allclose(op.conj().T @ op, identity)

    def test_09_identity_squared(self) -> None:
        """9. I² = I."""
        assert np.allclose(PAULI_I @ PAULI_I, PAULI_I)

    def test_10_pauli_x_squared(self) -> None:
        """10. X² = I."""
        assert np.allclose(PAULI_X @ PAULI_X, PAULI_I)

    def test_11_pauli_y_squared(self) -> None:
        """11. Y² = I."""
        assert np.allclose(PAULI_Y @ PAULI_Y, PAULI_I)

    def test_12_pauli_z_squared(self) -> None:
        """12. Z² = I."""
        assert np.allclose(PAULI_Z @ PAULI_Z, PAULI_I)

    def test_28_anti_commutation_xy(self) -> None:
        """28. XY = -YX."""
        xy = PAULI_X @ PAULI_Y
        yx = PAULI_Y @ PAULI_X
        assert np.allclose(xy, -yx)
        # Also verify standard relation XY = iZ
        assert np.allclose(xy, 1.0j * PAULI_Z)

    def test_29_anti_commutation_yz(self) -> None:
        """29. YZ = -ZY."""
        yz = PAULI_Y @ PAULI_Z
        zy = PAULI_Z @ PAULI_Y
        assert np.allclose(yz, -zy)
        # Also verify standard relation YZ = iX
        assert np.allclose(yz, 1.0j * PAULI_X)

    def test_30_anti_commutation_zx(self) -> None:
        """30. ZX = -XZ."""
        zx = PAULI_Z @ PAULI_X
        xz = PAULI_X @ PAULI_Z
        assert np.allclose(zx, -xz)
        # Also verify standard relation ZX = iY
        assert np.allclose(zx, 1.0j * PAULI_Y)


class TestPauliActionOnComputationalBasis:
    """Tests 13-20: Action on |0> and |1>."""

    def test_13_identity_action_on_state_0(self) -> None:
        """13. I|0> = |0>."""
        res = apply_operator(PAULI_I, STATE_0)
        assert np.allclose(res, STATE_0)

    def test_14_identity_action_on_state_1(self) -> None:
        """14. I|1> = |1>."""
        res = apply_operator(PAULI_I, STATE_1)
        assert np.allclose(res, STATE_1)

    def test_15_pauli_x_action_on_state_0(self) -> None:
        """15. X|0> = |1>."""
        res = apply_operator(PAULI_X, STATE_0)
        assert np.allclose(res, STATE_1)

    def test_16_pauli_x_action_on_state_1(self) -> None:
        """16. X|1> = |0>."""
        res = apply_operator(PAULI_X, STATE_1)
        assert np.allclose(res, STATE_0)

    def test_17_pauli_y_action_on_state_0(self) -> None:
        """17. Y|0> = i|1>."""
        res = apply_operator(PAULI_Y, STATE_0)
        expected = 1.0j * STATE_1
        assert np.allclose(res, expected)
        assert np.allclose(res, np.array([0.0, 1.0j], dtype=np.complex128))

    def test_18_pauli_y_action_on_state_1(self) -> None:
        """18. Y|1> = -i|0>."""
        res = apply_operator(PAULI_Y, STATE_1)
        expected = -1.0j * STATE_0
        assert np.allclose(res, expected)
        assert np.allclose(res, np.array([-1.0j, 0.0], dtype=np.complex128))

    def test_19_pauli_z_action_on_state_0(self) -> None:
        """19. Z|0> = |0>."""
        res = apply_operator(PAULI_Z, STATE_0)
        assert np.allclose(res, STATE_0)

    def test_20_pauli_z_action_on_state_1(self) -> None:
        """20. Z|1> = -|1>."""
        res = apply_operator(PAULI_Z, STATE_1)
        expected = -1.0 * STATE_1
        assert np.allclose(res, expected)
        assert np.allclose(res, np.array([0.0, -1.0], dtype=np.complex128))


class TestPauliActionOnSuperpositionAndEigenstates:
    """Tests 21-27: Action on X-basis and Y-basis states, plus normalization preservation."""

    def test_21_pauli_x_action_on_state_plus(self) -> None:
        """21. X|+> = |+> (+1 eigenstate)."""
        res = apply_operator(PAULI_X, STATE_PLUS)
        assert np.allclose(res, STATE_PLUS)

    def test_22_pauli_x_action_on_state_minus(self) -> None:
        """22. X|-> = -|-> (-1 eigenstate)."""
        res = apply_operator(PAULI_X, STATE_MINUS)
        assert np.allclose(res, -STATE_MINUS)

    def test_23_pauli_z_action_on_state_plus(self) -> None:
        """23. Z|+> = |->."""
        res = apply_operator(PAULI_Z, STATE_PLUS)
        assert np.allclose(res, STATE_MINUS)

    def test_24_pauli_z_action_on_state_minus(self) -> None:
        """24. Z|-> = |+>."""
        res = apply_operator(PAULI_Z, STATE_MINUS)
        assert np.allclose(res, STATE_PLUS)

    def test_25_pauli_y_action_on_state_plus_i(self) -> None:
        """25. Y|+i> = +|+i> (+1 eigenstate)."""
        res = apply_operator(PAULI_Y, STATE_PLUS_I)
        assert np.allclose(res, STATE_PLUS_I)

    def test_26_pauli_y_action_on_state_minus_i(self) -> None:
        """26. Y|-i> = -|-i> (-1 eigenstate)."""
        res = apply_operator(PAULI_Y, STATE_MINUS_I)
        assert np.allclose(res, -STATE_MINUS_I)

    def test_27_pauli_preserves_normalization_on_all_standard_states(self) -> None:
        """27. Applying any Pauli operator to a normalized state preserves unit norm."""
        operators = [PAULI_I, PAULI_X, PAULI_Y, PAULI_Z]
        states = [STATE_0, STATE_1, STATE_PLUS, STATE_MINUS, STATE_PLUS_I, STATE_MINUS_I]

        for op in operators:
            for st in states:
                transformed = apply_operator(op, st)
                assert is_normalized(transformed)
                norm_sq = np.real(np.vdot(transformed, transformed))
                assert np.isclose(norm_sq, 1.0, atol=1e-12)


class TestPauliValidationAndEdgeCases:
    """Tests 31-32 + Edge Cases: Invalid dimensions, non-finite values, QubitState support."""

    def test_31_invalid_operator_dimensions_rejected(self) -> None:
        """31. Invalid operator shapes (e.g. (3, 3), (2,), (2, 3)) are rejected."""
        with pytest.raises(ValueError, match="shape \\(2, 2\\)"):
            validate_operator(np.eye(3))

        with pytest.raises(ValueError, match="shape \\(2, 2\\)"):
            validate_operator(np.array([1.0, 0.0]))

        with pytest.raises(ValueError, match="shape \\(2, 2\\)"):
            validate_operator(np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]))

        with pytest.raises(ValueError, match="shape \\(2, 2\\)"):
            apply_operator(np.eye(3), STATE_0)

    def test_32_invalid_state_dimensions_rejected(self) -> None:
        """32. Invalid state vector dimensions are rejected."""
        with pytest.raises(ValueError, match="shape"):
            apply_operator(PAULI_X, np.array([1.0, 0.0, 0.0]))

        with pytest.raises(ValueError, match="shape"):
            apply_operator(PAULI_X, np.array([1.0]))

    def test_non_finite_operator_rejected(self) -> None:
        """Operators containing NaN or Inf raise ValueError."""
        nan_op = np.array([[np.nan, 0.0], [0.0, 1.0]])
        with pytest.raises(ValueError, match="finite"):
            validate_operator(nan_op)

        inf_op = np.array([[1.0, 0.0], [0.0, np.inf]])
        with pytest.raises(ValueError, match="finite"):
            validate_operator(inf_op)

    def test_invalid_types_rejected(self) -> None:
        """Non-convertible objects raise TypeError."""
        with pytest.raises(TypeError):
            validate_operator("not_a_matrix")

        with pytest.raises(TypeError):
            apply_operator(object(), STATE_0)

        with pytest.raises(TypeError):
            apply_operator(PAULI_X, object())

    def test_get_unknown_pauli_raises(self) -> None:
        """Unknown operator name string raises ValueError."""
        with pytest.raises(ValueError, match="Unknown Pauli operator"):
            get_pauli_operator("W")

    def test_apply_operator_with_qubit_state_instance(self) -> None:
        """apply_operator preserves QubitState dataclass wrapper when given QubitState."""
        qs = QubitState(STATE_0)
        res = apply_operator(PAULI_X, qs)
        assert isinstance(res, QubitState)
        assert np.allclose(res.vector, STATE_1)
        assert np.isclose(res.probabilities["1"], 1.0)

    def test_apply_operator_with_string_operator_and_state(self) -> None:
        """apply_operator supports string names for both operator and state."""
        res = apply_operator("X", "0")
        assert np.allclose(res, STATE_1)

        res_z = apply_operator("Z", "+")
        assert np.allclose(res_z, STATE_MINUS)

    def test_is_hermitian_and_is_unitary_on_non_pauli(self) -> None:
        """is_hermitian and is_unitary correctly evaluate arbitrary operators."""
        # Non-Hermitian operator
        non_herm = np.array([[1.0, 2.0], [0.0, 1.0]], dtype=np.complex128)
        assert not is_hermitian(non_herm)

        # Non-unitary operator
        non_unit = np.array([[2.0, 0.0], [0.0, 2.0]], dtype=np.complex128)
        assert not is_unitary(non_unit)

        # Invalid matrix returns False safely
        assert not is_hermitian("invalid")
        assert not is_unitary(np.eye(3))

    def test_apply_operator_does_not_artificially_normalize(self) -> None:
        """apply_operator must not artificially re-normalize results from non-unitary matrices."""
        scaled_op = 2.5 * PAULI_X
        res = apply_operator(scaled_op, STATE_0)
        expected = np.array([0.0, 2.5], dtype=np.complex128)
        assert np.allclose(res, expected)
        norm = np.linalg.norm(res)
        assert np.isclose(norm, 2.5)

    def test_apply_operator_with_column_ket_vector(self) -> None:
        """apply_operator must accept 2D column vectors (kets of shape (2, 1))."""
        ket_0 = np.array([[1.0], [0.0]])
        res = apply_operator(PAULI_X, ket_0)
        assert res.shape == (2,)
        assert np.allclose(res, STATE_1)

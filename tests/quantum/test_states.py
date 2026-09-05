"""Tests for single-qubit quantum state representation and validation (Milestone M1)."""

import numpy as np
import pytest

from src.quantum.states import (
    STATE_0,
    STATE_1,
    STATE_PLUS,
    STATE_MINUS,
    STATE_PLUS_I,
    STATE_MINUS_I,
    get_standard_state,
    validate_state_vector,
    is_normalized,
    normalize_state,
    computational_probabilities,
    create_qubit_circuit,
    QubitState,
)


class TestStateVectors:
    """Tests for exact representation of standard single-qubit pure states."""

    def test_state_0_representation(self) -> None:
        """|0> = [1, 0]^T."""
        expected = np.array([1.0, 0.0], dtype=np.complex128)
        assert np.allclose(STATE_0, expected)
        assert np.allclose(get_standard_state("0"), expected)
        assert np.allclose(get_standard_state("|0>"), expected)
        assert np.allclose(get_standard_state("|0⟩"), expected)

    def test_state_1_representation(self) -> None:
        """|1> = [0, 1]^T."""
        expected = np.array([0.0, 1.0], dtype=np.complex128)
        assert np.allclose(STATE_1, expected)
        assert np.allclose(get_standard_state("1"), expected)
        assert np.allclose(get_standard_state("|1>"), expected)
        assert np.allclose(get_standard_state("|1⟩"), expected)

    def test_state_plus_representation(self) -> None:
        """|+> = 1/sqrt(2) [1, 1]^T."""
        expected = np.array([1.0 / np.sqrt(2), 1.0 / np.sqrt(2)], dtype=np.complex128)
        assert np.allclose(STATE_PLUS, expected)
        assert np.allclose(get_standard_state("+"), expected)
        assert np.allclose(get_standard_state("|+>"), expected)
        assert np.allclose(get_standard_state("|+⟩"), expected)

    def test_state_minus_representation(self) -> None:
        """|-> = 1/sqrt(2) [1, -1]^T."""
        expected = np.array([1.0 / np.sqrt(2), -1.0 / np.sqrt(2)], dtype=np.complex128)
        assert np.allclose(STATE_MINUS, expected)
        assert np.allclose(get_standard_state("-"), expected)
        assert np.allclose(get_standard_state("|->"), expected)
        assert np.allclose(get_standard_state("|-⟩"), expected)

    def test_y_basis_eigenstates(self) -> None:
        """|+i> = 1/sqrt(2) [1, i]^T and |-i> = 1/sqrt(2) [1, -i]^T."""
        expected_plus_i = np.array([1.0 / np.sqrt(2), 1.0j / np.sqrt(2)], dtype=np.complex128)
        expected_minus_i = np.array([1.0 / np.sqrt(2), -1.0j / np.sqrt(2)], dtype=np.complex128)
        assert np.allclose(STATE_PLUS_I, expected_plus_i)
        assert np.allclose(STATE_MINUS_I, expected_minus_i)
        assert np.allclose(get_standard_state("+i"), expected_plus_i)
        assert np.allclose(get_standard_state("-i"), expected_minus_i)

    def test_unknown_standard_state_raises(self) -> None:
        """Querying an unknown state label should raise ValueError."""
        with pytest.raises(ValueError, match="Unknown standard state"):
            get_standard_state("unknown_state")


class TestStateNormalization:
    """Tests for normalization constraint: |alpha|^2 + |beta|^2 = 1."""

    @pytest.mark.parametrize(
        "state",
        [STATE_0, STATE_1, STATE_PLUS, STATE_MINUS, STATE_PLUS_I, STATE_MINUS_I],
    )
    def test_standard_states_are_normalized(self, state: np.ndarray) -> None:
        """All standard pure states must have norm exactly equal to 1."""
        assert is_normalized(state)
        validated = validate_state_vector(state)
        norm_sq = np.real(np.vdot(validated, validated))
        assert np.isclose(norm_sq, 1.0, atol=1e-12)

    def test_complex_superposition_normalization(self) -> None:
        """General pure state with arbitrary complex phase: cos(theta)|0> + exp(i*phi)*sin(theta)|1>."""
        theta = 0.35 * np.pi
        phi = 0.72 * np.pi
        alpha = np.cos(theta)
        beta = np.exp(1.0j * phi) * np.sin(theta)
        state = np.array([alpha, beta], dtype=np.complex128)

        assert is_normalized(state)
        validated = validate_state_vector(state)
        norm_sq = np.real(np.vdot(validated, validated))
        assert np.isclose(norm_sq, 1.0, atol=1e-12)

    def test_normalize_state_utility(self) -> None:
        """normalize_state should scale arbitrary non-zero vectors to unit norm."""
        unnormalized = np.array([3.0, 4.0], dtype=np.complex128)
        normalized = normalize_state(unnormalized)
        assert np.allclose(normalized, [0.6, 0.8])
        assert is_normalized(normalized)

    def test_normalize_zero_vector_raises(self) -> None:
        """Attempting to normalize the zero vector must raise ValueError."""
        with pytest.raises(ValueError, match="zero or negligible norm"):
            normalize_state(np.array([0.0, 0.0]))


class TestComputationalProbabilities:
    """Tests for Born rule probabilities: P(0) = |alpha|^2, P(1) = |beta|^2."""

    def test_probabilities_state_0(self) -> None:
        """For |0>: P(0) = 1.0, P(1) = 0.0."""
        probs = computational_probabilities(STATE_0)
        assert probs["0"] == 1.0
        assert probs["1"] == 0.0
        assert np.isclose(probs["0"] + probs["1"], 1.0)

    def test_probabilities_state_1(self) -> None:
        """For |1>: P(0) = 0.0, P(1) = 1.0."""
        probs = computational_probabilities(STATE_1)
        assert probs["0"] == 0.0
        assert probs["1"] == 1.0
        assert np.isclose(probs["0"] + probs["1"], 1.0)

    def test_probabilities_state_plus_and_minus(self) -> None:
        """For |+> and |->: P(0) = 0.5, P(1) = 0.5 exactly."""
        for state in [STATE_PLUS, STATE_MINUS]:
            probs = computational_probabilities(state)
            assert np.isclose(probs["0"], 0.5)
            assert np.isclose(probs["1"], 0.5)
            assert np.isclose(probs["0"] + probs["1"], 1.0)

    def test_probabilities_complex_states(self) -> None:
        """For |+i> and |-i>: P(0) = 0.5, P(1) = 0.5."""
        for state in [STATE_PLUS_I, STATE_MINUS_I]:
            probs = computational_probabilities(state)
            assert np.isclose(probs["0"], 0.5)
            assert np.isclose(probs["1"], 0.5)
            assert np.isclose(probs["0"] + probs["1"], 1.0)

    def test_probabilities_with_string_label(self) -> None:
        """computational_probabilities accepts valid string labels."""
        probs = computational_probabilities("0")
        assert probs["0"] == 1.0
        assert probs["1"] == 0.0

    def test_probabilities_general_state(self) -> None:
        """For alpha=sqrt(0.3), beta=sqrt(0.7): P(0)=0.3, P(1)=0.7."""
        alpha = np.sqrt(0.3)
        beta = np.sqrt(0.7)
        state = np.array([alpha, beta])
        probs = computational_probabilities(state)
        assert np.isclose(probs["0"], 0.3)
        assert np.isclose(probs["1"], 0.7)
        assert np.isclose(probs["0"] + probs["1"], 1.0)


class TestStateEdgeCases:
    """Tests for invalid vectors, wrong shapes, bad types, and edge cases."""

    def test_wrong_length_raises(self) -> None:
        """Vectors with shape != (2,) must raise ValueError."""
        with pytest.raises(ValueError, match="must have shape \\(2,\\)"):
            validate_state_vector(np.array([1.0]))

        with pytest.raises(ValueError, match="must have shape \\(2,\\)"):
            validate_state_vector(np.array([1.0, 0.0, 0.0]))

    def test_non_normalized_vector_raises(self) -> None:
        """Non-normalized vectors must raise ValueError."""
        with pytest.raises(ValueError, match="not normalized"):
            validate_state_vector(np.array([1.0, 1.0]))

        assert not is_normalized(np.array([1.0, 1.0]))

    def test_zero_vector_raises(self) -> None:
        """The zero vector must raise ValueError."""
        with pytest.raises(ValueError, match="zero vector"):
            validate_state_vector(np.array([0.0, 0.0]))

        assert not is_normalized(np.array([0.0, 0.0]))

    def test_non_finite_values_raise(self) -> None:
        """NaN or infinite values must raise ValueError."""
        with pytest.raises(ValueError, match="finite"):
            validate_state_vector(np.array([np.nan, 1.0]))

        with pytest.raises(ValueError, match="finite"):
            validate_state_vector(np.array([np.inf, 0.0]))

    def test_invalid_types_raise(self) -> None:
        """Non-numeric elements must raise TypeError."""
        with pytest.raises(TypeError):
            validate_state_vector(["invalid", "type"])


    def test_column_vector_ket_representation(self) -> None:
        """2D column vectors representing kets (shape (2, 1)) must be accepted."""
        ket_0 = np.array([[1.0], [0.0]])
        assert is_normalized(ket_0)
        validated = validate_state_vector(ket_0)
        assert validated.shape == (2,)
        assert np.allclose(validated, STATE_0)

        ket_plus = np.array([[1.0 / np.sqrt(2)], [1.0 / np.sqrt(2)]])
        probs = computational_probabilities(ket_plus)
        assert np.isclose(probs["0"], 0.5)
        assert np.isclose(probs["1"], 0.5)

    def test_row_vector_representation(self) -> None:
        """2D row vectors (shape (1, 2)) must be accepted."""
        row_1 = np.array([[0.0, 1.0]])
        assert is_normalized(row_1)
        validated = validate_state_vector(row_1)
        assert validated.shape == (2,)
        assert np.allclose(validated, STATE_1)


class TestQubitStateClassAndCircuit:
    """Tests for QubitState wrapper and circuit generation."""

    def test_qubit_state_dataclass(self) -> None:
        qs = QubitState(STATE_PLUS)
        assert qs.shape == (2,)
        assert qs.dtype == np.complex128
        assert np.isclose(qs.alpha, 1.0 / np.sqrt(2))
        assert np.isclose(qs.beta, 1.0 / np.sqrt(2))
        assert np.isclose(qs.probabilities["0"], 0.5)
        assert np.isclose(qs.probabilities["1"], 0.5)

    def test_create_qubit_circuit(self) -> None:
        qc = create_qubit_circuit(STATE_PLUS, circuit_name="test_qc")
        assert qc.num_qubits == 1
        assert qc.name == "test_qc"

    def test_qubit_state_interoperability(self) -> None:
        """Functions accepting state should accept QubitState instances seamlessly."""
        qs = QubitState(STATE_0)
        assert is_normalized(qs)
        validated = validate_state_vector(qs)
        assert np.allclose(validated, STATE_0)

        probs = computational_probabilities(qs)
        assert probs["0"] == 1.0
        assert probs["1"] == 0.0

        qc = create_qubit_circuit(qs)
        assert qc.num_qubits == 1

        # Test numpy array interface
        arr = np.asarray(qs)
        assert np.allclose(arr, STATE_0)

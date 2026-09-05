"""Q-SHIELD — Quantum State Module (Milestone M1).

Provides representations, validation, normalization, and computational-basis
probability calculations for pure single-qubit quantum states:
    |0>, |1>, |+>, |->, |+i>, |-i>

Mathematical Model:
    |psi> = alpha|0> + beta|1>, where alpha, beta in C
    Normalization: |alpha|^2 + |beta|^2 = 1
    Computational probabilities: P(0) = |alpha|^2, P(1) = |beta|^2
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import numpy as np
from qiskit import QuantumCircuit


# Standard computational and superposition basis pure state vectors
INV_SQRT_2 = 1.0 / np.sqrt(2.0)

STATE_0: np.ndarray = np.array([1.0, 0.0], dtype=np.complex128)
STATE_1: np.ndarray = np.array([0.0, 1.0], dtype=np.complex128)
STATE_PLUS: np.ndarray = np.array([INV_SQRT_2, INV_SQRT_2], dtype=np.complex128)
STATE_MINUS: np.ndarray = np.array([INV_SQRT_2, -INV_SQRT_2], dtype=np.complex128)
STATE_PLUS_I: np.ndarray = np.array([INV_SQRT_2, 1.0j * INV_SQRT_2], dtype=np.complex128)
STATE_MINUS_I: np.ndarray = np.array([INV_SQRT_2, -1.0j * INV_SQRT_2], dtype=np.complex128)

_STANDARD_STATES: dict[str, np.ndarray] = {
    "0": STATE_0,
    "|0>": STATE_0,
    "|0⟩": STATE_0,
    "1": STATE_1,
    "|1>": STATE_1,
    "|1⟩": STATE_1,
    "+": STATE_PLUS,
    "|+>": STATE_PLUS,
    "|+⟩": STATE_PLUS,
    "-": STATE_MINUS,
    "|->": STATE_MINUS,
    "|-⟩": STATE_MINUS,
    "+i": STATE_PLUS_I,
    "|+i>": STATE_PLUS_I,
    "|+i⟩": STATE_PLUS_I,
    "-i": STATE_MINUS_I,
    "|-i>": STATE_MINUS_I,
    "|-i⟩": STATE_MINUS_I,
}


def get_standard_state(name: str) -> np.ndarray:
    """Retrieve a copy of a standard single-qubit state vector by label.

    Supported labels include:
        '0', '|0>', '1', '|1>', '+', '|+>', '-', '|->', '+i', '|+i>', '-i', '|-i>'

    Args:
        name: Name or Dirac notation label of the desired state.

    Returns:
        A 2-element complex numpy array representing the normalized state.

    Raises:
        ValueError: If the state label is not recognized.
    """
    key = name.strip()
    if key in _STANDARD_STATES:
        return _STANDARD_STATES[key].copy()
    raise ValueError(
        f"Unknown standard state '{name}'. Supported states: {list(_STANDARD_STATES.keys())}"
    )


def validate_state_vector(state: Any, atol: float = 1e-7) -> np.ndarray:
    """Validate that input represents a valid, normalized single-qubit pure state.

    Args:
        state: Array-like object of length 2 with complex or numeric amplitudes.
        atol: Numerical tolerance for the normalization constraint |alpha|^2 + |beta|^2 = 1.

    Returns:
        A 2-element numpy array of type np.complex128.

    Raises:
        TypeError: If state cannot be converted into a numeric complex array.
        ValueError: If state does not have exactly 2 elements, contains non-finite values,
                    is the zero vector, or violates normalization.
    """
    if isinstance(state, QubitState):
        state = state.vector

    try:
        arr = np.asarray(state, dtype=np.complex128)
    except (ValueError, TypeError) as exc:
        raise TypeError(f"State vector must be numeric/complex array-like: {exc}") from exc

    # Accept 2-element column or row vectors (kets) and squeeze to 1D
    if arr.ndim == 2 and (arr.shape == (2, 1) or arr.shape == (1, 2)):
        arr = arr.squeeze()

    if arr.ndim != 1 or arr.shape[0] != 2:
        raise ValueError(
            f"A single-qubit state vector must have shape (2,), but got shape {arr.shape}."
        )

    if not np.all(np.isfinite(arr)):
        raise ValueError("State vector components must be finite (no NaN or Inf).")

    norm_sq = float(np.real(np.vdot(arr, arr)))
    if norm_sq <= 0.0:
        raise ValueError("State vector cannot be the zero vector.")

    if not np.isclose(norm_sq, 1.0, atol=atol):
        raise ValueError(
            f"State vector is not normalized: |alpha|^2 + |beta|^2 = {norm_sq:.8f}, expected 1.0 (atol={atol})."
        )

    return arr


def is_normalized(state: Any, atol: float = 1e-7) -> bool:
    """Check whether an input vector is a valid, normalized single-qubit state without raising.

    Args:
        state: State vector to check.
        atol: Tolerance for normalization.

    Returns:
        True if the state is a valid normalized single-qubit state vector, False otherwise.
    """
    try:
        validate_state_vector(state, atol=atol)
        return True
    except (ValueError, TypeError):
        return False


def normalize_state(state: Any, atol: float = 1e-7) -> np.ndarray:
    """Normalize a non-zero 2-element vector to unit length.

    Args:
        state: Array-like vector of length 2.
        atol: Tolerance check for zero-norm.

    Returns:
        Normalized 2-element numpy array of type np.complex128.

    Raises:
        ValueError: If vector has invalid shape or is zero-norm.
    """
    if isinstance(state, QubitState):
        state = state.vector

    try:
        arr = np.asarray(state, dtype=np.complex128)
    except (ValueError, TypeError) as exc:
        raise TypeError(f"State vector must be numeric array-like: {exc}") from exc

    if arr.ndim == 2 and (arr.shape == (2, 1) or arr.shape == (1, 2)):
        arr = arr.squeeze()

    if arr.ndim != 1 or arr.shape[0] != 2:
        raise ValueError(f"State vector must have shape (2,), got shape {arr.shape}.")

    norm = np.linalg.norm(arr)
    if norm < atol:
        raise ValueError("Cannot normalize a vector with zero or negligible norm.")

    normalized = arr / norm
    return validate_state_vector(normalized, atol=atol)


def computational_probabilities(state: Any, atol: float = 1e-7) -> dict[str, float]:
    """Calculate theoretical computational-basis measurement probabilities via Born's rule.

    For |psi> = alpha|0> + beta|1>:
        P(0) = |alpha|^2 = alpha * conj(alpha)
        P(1) = |beta|^2 = beta * conj(beta)

    Args:
        state: Validated single-qubit state vector or standard state name.
        atol: Numerical tolerance for probability normalization.

    Returns:
        Dictionary mapping basis outcome '0' and '1' to their respective probabilities.

    Raises:
        ValueError: If the state is invalid or probabilities do not sum to 1.
    """
    if isinstance(state, str):
        arr = get_standard_state(state)
    elif isinstance(state, QubitState):
        arr = state.vector
    else:
        arr = validate_state_vector(state, atol=atol)

    alpha, beta = arr[0], arr[1]
    prob_0 = float(np.real(alpha * np.conj(alpha)))
    prob_1 = float(np.real(beta * np.conj(beta)))

    # Guarantee numerical non-negativity from floating-point arithmetic
    prob_0 = max(0.0, min(1.0, prob_0))
    prob_1 = max(0.0, min(1.0, prob_1))

    total_prob = prob_0 + prob_1
    if not np.isclose(total_prob, 1.0, atol=atol):
        raise ValueError(
            f"Computational probabilities do not sum to 1: P(0)+P(1) = {total_prob:.8f}"
        )

    return {"0": prob_0, "1": prob_1}


def create_qubit_circuit(
    state: Any = STATE_0,
    circuit_name: str = "single_qubit",
) -> QuantumCircuit:
    """Create a Qiskit single-qubit circuit initialized to the specified state.

    Args:
        state: Standard state name string or 2-element normalized state vector.
        circuit_name: Name label for the QuantumCircuit.

    Returns:
        A Qiskit QuantumCircuit with 1 quantum bit, initialized to the given state.
    """
    if isinstance(state, str):
        vec = get_standard_state(state)
    elif isinstance(state, QubitState):
        vec = state.vector
    else:
        vec = validate_state_vector(state)

    qc = QuantumCircuit(1, name=circuit_name)
    qc.initialize(list(vec), [0])
    return qc


@dataclass(frozen=True)
class QubitState:
    """Immutable representation of a pure single-qubit quantum state."""

    vector: np.ndarray

    def __post_init__(self) -> None:
        validated = validate_state_vector(self.vector)
        # Ensure array is stored as complex128 and read-only
        validated = validated.copy()
        validated.flags.writeable = False
        object.__setattr__(self, "vector", validated)

    def __array__(self, dtype: Any = None, copy: bool | None = None) -> np.ndarray:
        return np.asarray(self.vector, dtype=dtype, copy=copy)

    @property
    def shape(self) -> tuple[int, ...]:
        return self.vector.shape

    @property
    def dtype(self) -> np.dtype:
        return self.vector.dtype

    @property
    def alpha(self) -> complex:
        return complex(self.vector[0])

    @property
    def beta(self) -> complex:
        return complex(self.vector[1])

    @property
    def probabilities(self) -> dict[str, float]:
        return computational_probabilities(self.vector)

    def to_circuit(self, circuit_name: str = "qubit_circuit") -> QuantumCircuit:
        return create_qubit_circuit(self.vector, circuit_name=circuit_name)

    def __repr__(self) -> str:
        return f"QubitState(alpha={self.alpha:.4f}, beta={self.beta:.4f})"

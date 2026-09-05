"""Q-SHIELD — Pauli Operators Module (Milestone M2).

Provides standard single-qubit Pauli operators (I, X, Y, Z) represented as 2x2
complex-valued NumPy matrices, validation routines, algebraic property verifications,
and state application via matrix-vector multiplication.

Mathematical Model:
    I = [[1,  0],
         [0,  1]]

    X = [[0,  1],
         [1,  0]]

    Y = [[0, -i],
         [i,  0]]

    Z = [[1,  0],
         [0, -1]]

Algebraic Properties:
    - Hermitian: U† = U
    - Unitary: U†U = I
    - Involutory: U² = I
    - Anti-commutation: XY = -YX, YZ = -ZY, ZX = -XZ
    - Preserves state normalization for any normalized |psi>
"""

from __future__ import annotations

from typing import Any, Sequence, overload
import numpy as np

from .states import QubitState, validate_state_vector


# Standard 2x2 complex Pauli matrices (dtype=np.complex128)
PAULI_I: np.ndarray = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.complex128)
PAULI_X: np.ndarray = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128)
PAULI_Y: np.ndarray = np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=np.complex128)
PAULI_Z: np.ndarray = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128)

_PAULI_OPERATORS: dict[str, np.ndarray] = {
    "i": PAULI_I,
    "identity": PAULI_I,
    "x": PAULI_X,
    "pauli_x": PAULI_X,
    "sigma_x": PAULI_X,
    "y": PAULI_Y,
    "pauli_y": PAULI_Y,
    "sigma_y": PAULI_Y,
    "z": PAULI_Z,
    "pauli_z": PAULI_Z,
    "sigma_z": PAULI_Z,
}


def identity_operator() -> np.ndarray:
    """Return a copy of the 2x2 single-qubit Identity operator matrix."""
    return PAULI_I.copy()


def pauli_x() -> np.ndarray:
    """Return a copy of the 2x2 Pauli-X (bit-flip) operator matrix."""
    return PAULI_X.copy()


def pauli_y() -> np.ndarray:
    """Return a copy of the 2x2 Pauli-Y (bit + phase-flip) operator matrix."""
    return PAULI_Y.copy()


def pauli_z() -> np.ndarray:
    """Return a copy of the 2x2 Pauli-Z (phase-flip) operator matrix."""
    return PAULI_Z.copy()


def get_pauli_operator(name: str) -> np.ndarray:
    """Retrieve a copy of a Pauli operator matrix by name or label.

    Supported names (case-insensitive):
        'I', 'Identity', 'X', 'Pauli_X', 'Y', 'Pauli_Y', 'Z', 'Pauli_Z'

    Args:
        name: String identifier for the Pauli operator.

    Returns:
        A 2x2 complex NumPy array.

    Raises:
        ValueError: If the operator name is not recognized.
    """
    key = name.strip().lower()
    if key in _PAULI_OPERATORS:
        return _PAULI_OPERATORS[key].copy()
    raise ValueError(
        f"Unknown Pauli operator '{name}'. Supported operators: ['I', 'X', 'Y', 'Z']."
    )


def validate_operator(operator: Any) -> np.ndarray:
    """Validate that input represents a valid 2x2 numeric/complex operator matrix.

    Args:
        operator: Array-like object of shape (2, 2) with numeric or complex entries.

    Returns:
        A 2x2 NumPy array with dtype np.complex128.

    Raises:
        TypeError: If input cannot be converted to a complex NumPy array.
        ValueError: If array does not have shape (2, 2) or contains non-finite values (NaN, Inf).
    """
    try:
        arr = np.asarray(operator, dtype=np.complex128)
    except (ValueError, TypeError) as exc:
        raise TypeError(f"Operator must be a numeric/complex array-like: {exc}") from exc

    if arr.ndim != 2 or arr.shape != (2, 2):
        raise ValueError(f"Operator must have shape (2, 2), but got shape {arr.shape}.")

    if not np.all(np.isfinite(arr)):
        raise ValueError("Operator elements must be finite (no NaN or Inf).")

    return arr


def is_hermitian(operator: Any, atol: float = 1e-7) -> bool:
    """Check whether a 2x2 operator is Hermitian (U† = U).

    Args:
        operator: 2x2 operator matrix.
        atol: Numerical comparison tolerance.

    Returns:
        True if U† == U within tolerance, False otherwise.
    """
    try:
        mat = validate_operator(operator)
    except (ValueError, TypeError):
        return False
    dagger = mat.conj().T
    return bool(np.allclose(mat, dagger, atol=atol))


def is_unitary(operator: Any, atol: float = 1e-7) -> bool:
    """Check whether a 2x2 operator is unitary (U†U = I).

    Args:
        operator: 2x2 operator matrix.
        atol: Numerical comparison tolerance.

    Returns:
        True if U†U == I within tolerance, False otherwise.
    """
    try:
        mat = validate_operator(operator)
    except (ValueError, TypeError):
        return False
    dagger = mat.conj().T
    identity = np.eye(2, dtype=np.complex128)
    return bool(np.allclose(dagger @ mat, identity, atol=atol))


@overload
def apply_operator(operator: Any, state: QubitState) -> QubitState:
    ...


@overload
def apply_operator(operator: Any, state: object) -> Any:
    ...


def apply_operator(operator: Any, state: Any) -> np.ndarray | QubitState:
    """Apply a 2x2 single-qubit operator to a quantum state vector: new_state = operator @ state.

    The mathematical operation is strictly performed via matrix multiplication.
    The result is NOT artificially re-normalized to preserve mathematical fidelity
    and expose any non-unitary operator behaviour.

    Args:
        operator: 2x2 operator matrix (e.g. Pauli-X, Y, Z, I, or string name).
        state: Valid single-qubit state vector (length-2 array, ket, or QubitState).

    Returns:
        The resulting state as a 1D complex128 NumPy array of length 2,
        or as a QubitState if the input state was a QubitState.

    Raises:
        TypeError: If operator or state types cannot be interpreted.
        ValueError: If operator shape != (2, 2) or state dimensions != 2.
    """
    if isinstance(operator, str):
        op_mat = get_pauli_operator(operator)
    else:
        op_mat = validate_operator(operator)

    is_qubit_state_instance = isinstance(state, QubitState)
    if is_qubit_state_instance:
        state_vec = state.vector
    elif isinstance(state, str):
        # Allow standard state string labels (e.g. '0', '1', '+', '-')
        from .states import get_standard_state
        state_vec = get_standard_state(state)
    else:
        # Validate that the input is a valid 2-element state vector
        state_vec = validate_state_vector(state)

    # Perform matrix-vector multiplication
    result_vec = np.asarray(op_mat @ state_vec, dtype=np.complex128)

    if is_qubit_state_instance:
        return QubitState(result_vec)
    return result_vec

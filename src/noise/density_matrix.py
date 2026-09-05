"""Q-SHIELD — Density Matrix Module (Milestone M8).

Provides mathematical utilities for representing, validating, and manipulating
single-qubit mixed quantum states via density matrices:
    rho in C^(2x2),  rho = rho^dagger,  Tr(rho) = 1,  rho >= 0.

Mathematical Foundations:
    1. Density Matrix Definition:
       A general single-qubit quantum state (pure or mixed) is represented by a 2x2
       Hermitian, positive-semidefinite matrix with unit trace:
           rho = sum_i p_i |psi_i><psi_i|,   where sum_i p_i = 1, p_i >= 0.

    2. Pure State to Density Matrix:
       rho = |psi><psi| = psi (x) psi^*  (outer product with complex conjugate).

    3. Quantum State Overlap Fidelity:
       - Pure-Pure:  F(psi, phi) = |<psi | phi>|^2
       - Pure-Mixed: F(psi, rho) = <psi | rho | psi> = Tr(|psi><psi| rho)
       - Mixed-Mixed: F(rho, sigma) = (Tr sqrt(sqrt(rho) sigma sqrt(rho)))^2
         For single-qubit (2x2) density matrices, this simplifies to the exact closed form:
             F(rho, sigma) = Tr(rho sigma) + 2 sqrt(det(rho) det(sigma))

    4. Measurement Probabilities:
       For projector P_i:  P(i) = Tr(P_i rho)
"""

from __future__ import annotations

import math
from typing import Any
import numpy as np

from src.quantum.measurements import get_basis_projectors
from src.quantum.states import (
    QubitState,
    get_standard_state,
    validate_state_vector,
)


def pure_state_to_density_matrix(state: Any, atol: float = 1e-7) -> np.ndarray:
    """Convert a pure single-qubit state vector to its corresponding 2x2 density matrix.

    Mathematical Model:
        rho = |psi><psi| = np.outer(psi, np.conj(psi))

    Args:
        state: State identifier (str), QubitState, or array-like state vector.
        atol: Numerical tolerance for state normalization constraint.

    Returns:
        2x2 complex numpy array representing the pure-state density matrix.

    Raises:
        TypeError: If state cannot be parsed as a numeric vector.
        ValueError: If state is non-normalized, non-finite, or malformed.
    """
    if isinstance(state, str):
        vec = get_standard_state(state)
    elif isinstance(state, QubitState):
        vec = state.vector
    else:
        vec = validate_state_vector(state, atol=atol)

    # Strictly perform outer product with complex conjugate: |psi><psi|
    rho = np.outer(vec, np.conj(vec))
    return np.asarray(rho, dtype=np.complex128)


def validate_density_matrix(rho: Any, atol: float = 1e-7) -> np.ndarray:
    """Validate that an input array represents a physically valid single-qubit density matrix.

    Requirements:
        1. Dimension: Exactly 2x2.
        2. Finite: No NaN, Inf, or -Inf values.
        3. Hermiticity: rho == rho^dagger within atol.
        4. Unit Trace: Tr(rho) == 1.0 within atol.
        5. Positive Semidefinite: All eigenvalues lambda_i >= -atol.

    Args:
        rho: Array-like object representing the 2x2 density matrix.
        atol: Numerical tolerance for physical validity constraints.

    Returns:
        Validated 2x2 complex numpy array of type np.complex128.

    Raises:
        TypeError: If rho is not array-like or contains non-numeric data.
        ValueError: If rho violates shape, Hermiticity, trace, or positivity constraints.
    """
    if rho is None:
        raise TypeError("Density matrix cannot be None.")

    try:
        arr = np.asarray(rho, dtype=np.complex128)
    except (ValueError, TypeError) as exc:
        raise TypeError(f"Density matrix must be numeric array-like: {exc}") from exc

    if arr.shape != (2, 2):
        raise ValueError(
            f"A single-qubit density matrix must have shape (2, 2), got shape {arr.shape}."
        )

    if not np.all(np.isfinite(arr)):
        raise ValueError("Density matrix elements must be finite (no NaN or Inf).")

    # 1. Hermiticity check: rho = rho^dagger
    if not np.allclose(arr, arr.conj().T, atol=atol):
        raise ValueError("Density matrix must be Hermitian (rho == rho^dagger).")

    # 2. Unit trace check: Tr(rho) = 1.0
    trace_val = np.trace(arr)
    if not (math.isclose(float(trace_val.real), 1.0, abs_tol=atol) and math.isclose(float(trace_val.imag), 0.0, abs_tol=atol)):
        raise ValueError(
            f"Density matrix must have unit trace: Tr(rho) = {trace_val.real:.8f} + {trace_val.imag:.8f}j, expected 1.0."
        )

    # 3. Positive semidefiniteness check: eigenvalues >= -atol
    # For Hermitian matrices, eigvalsh guarantees real eigenvalues
    evals = np.linalg.eigvalsh(arr)
    if np.any(evals < -atol):
        raise ValueError(
            f"Density matrix must be positive semidefinite; found negative eigenvalue: {float(np.min(evals)):.8e}."
        )

    return arr.copy()


def calculate_mixed_state_fidelity(state_a: Any, state_b: Any, atol: float = 1e-7) -> float:
    """Calculate the quantum state fidelity between two states (pure or mixed).

    Mathematical Model:
        - If both states are pure:
            F(psi, phi) = |<psi | phi>|^2
        - If one is pure and one is mixed:
            F(psi, rho) = <psi | rho | psi> = Tr(|psi><psi| rho)
        - If both are mixed:
            F(rho, sigma) = Tr(rho sigma) + 2 sqrt(det(rho) det(sigma))

    Args:
        state_a: First quantum state (vector or 2x2 density matrix).
        state_b: Second quantum state (vector or 2x2 density matrix).
        atol: Numerical tolerance for state and density matrix validation.

    Returns:
        Fidelity float in [0.0, 1.0].

    Raises:
        TypeError: If states have invalid types.
        ValueError: If states are non-normalized or physically invalid.
    """
    is_a_matrix = isinstance(state_a, np.ndarray) and state_a.shape == (2, 2)
    is_b_matrix = isinstance(state_b, np.ndarray) and state_b.shape == (2, 2)

    # Pure-Pure case
    if not is_a_matrix and not is_b_matrix:
        # Check if state_a or state_b is 2D matrix passed as nested list
        try:
            arr_a = np.asarray(state_a)
            if arr_a.shape == (2, 2):
                is_a_matrix = True
        except Exception:
            pass

        try:
            arr_b = np.asarray(state_b)
            if arr_b.shape == (2, 2):
                is_b_matrix = True
        except Exception:
            pass

    if not is_a_matrix and not is_b_matrix:
        vec_a = _parse_vector_helper(state_a, atol=atol)
        vec_b = _parse_vector_helper(state_b, atol=atol)
        inner = complex(np.vdot(vec_a, vec_b))
        fid = float(abs(inner) ** 2)
        return float(np.clip(fid, 0.0, 1.0))

    # Mixed-Mixed case
    if is_a_matrix and is_b_matrix:
        rho = validate_density_matrix(state_a, atol=atol)
        sigma = validate_density_matrix(state_b, atol=atol)

        # Tr(rho sigma) + 2 * sqrt(det(rho) * det(sigma))
        tr_rho_sigma = float(np.real(np.trace(rho @ sigma)))
        det_rho = float(np.real(np.linalg.det(rho)))
        det_sigma = float(np.real(np.linalg.det(sigma)))

        # Clean numerical roundoff for determinants of singular/pure states
        det_prod = max(0.0, det_rho) * max(0.0, det_sigma)
        fid = tr_rho_sigma + 2.0 * math.sqrt(det_prod)
        return float(np.clip(fid, 0.0, 1.0))

    # Pure-Mixed case (one is vector, one is matrix)
    if not is_a_matrix and is_b_matrix:
        vec = _parse_vector_helper(state_a, atol=atol)
        rho = validate_density_matrix(state_b, atol=atol)
    else:
        vec = _parse_vector_helper(state_b, atol=atol)
        rho = validate_density_matrix(state_a, atol=atol)

    # <psi | rho | psi> = Re(vdot(vec, rho @ vec))
    exp_val = float(np.real(np.vdot(vec, rho @ vec)))
    return float(np.clip(exp_val, 0.0, 1.0))


def density_matrix_probabilities(rho: Any, basis: str = "Z", atol: float = 1e-7) -> dict[str, float]:
    """Calculate the exact theoretical Born probabilities for a density matrix.

    Mathematical Model:
        P(i) = Tr(P_i rho)

    Args:
        rho: Valid 2x2 density matrix.
        basis: Measurement basis identifier ('Z', 'X', or 'Y').
        atol: Numerical tolerance for density matrix validation.

    Returns:
        Dictionary mapping outcome labels to probabilities.

    Raises:
        ValueError: If rho is invalid or basis is unrecognized.
    """
    valid_rho = validate_density_matrix(rho, atol=atol)
    p0, p1, labels = get_basis_projectors(basis)

    prob_0 = float(np.real(np.trace(p0 @ valid_rho)))
    prob_1 = float(np.real(np.trace(p1 @ valid_rho)))

    return {
        labels[0]: float(np.clip(prob_0, 0.0, 1.0)),
        labels[1]: float(np.clip(prob_1, 0.0, 1.0)),
    }


def _parse_vector_helper(state: Any, atol: float = 1e-7) -> np.ndarray:
    """Helper to parse a single-qubit state vector or standard name."""
    if isinstance(state, str):
        return get_standard_state(state)
    if isinstance(state, QubitState):
        return state.vector
    return validate_state_vector(state, atol=atol)

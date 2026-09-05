"""Q-SHIELD — Bell Correlation Module (Milestone M5).

Provides mathematical expectation value calculations, theoretical Bell correlations,
empirical correlation evaluation from measurement counts and probabilities,
pre-measurement basis-rotation circuits, and Aer simulation cross-validation.

Mathematical Model:
    Observable expectation value on pure two-qubit state |psi>:
        <O_0 (x) O_1> = <psi| (O_0 (x) O_1) |psi> = psi^† (O_0 (x) O_1) psi

    Canonical Bell State |Phi+> = (|00> + |11>) / sqrt(2):
        <Z (x) Z> = +1.0
        <X (x) X> = +1.0
        <Y (x) Y> = -1.0

    Complete Bell Basis Correlations:
        |Phi+>: XX = +1.0, YY = -1.0, ZZ = +1.0
        |Phi->: XX = -1.0, YY = +1.0, ZZ = +1.0
        |Psi+>: XX = +1.0, YY = +1.0, ZZ = -1.0
        |Psi->: XX = -1.0, YY = -1.0, ZZ = -1.0

    Empirical Correlation from Binary Measurement Counts:
        Outcomes in {0, 1} map to eigenvalues {+1, -1}:
            00 -> (+1)(+1) = +1
            11 -> (-1)(-1) = +1
            01 -> (+1)(-1) = -1
            10 -> (-1)(+1) = -1
        E = (N_00 + N_11 - N_01 - N_10) / N_total = P(same) - P(diff)
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any
import numpy as np
from qiskit import ClassicalRegister, QuantumCircuit
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator

from .bell import (
    BELL_PHI_PLUS,
    BELL_PHI_MINUS,
    BELL_PSI_PLUS,
    BELL_PSI_MINUS,
    TWO_QUBIT_BASIS_LABELS,
    BellState,
    calculate_two_qubit_expectation_value,
    create_bell_circuit,
    get_bell_state,
    validate_two_qubit_state,
)


VALID_TWO_QUBIT_OUTCOMES: frozenset[str] = frozenset(TWO_QUBIT_BASIS_LABELS)
SUPPORTED_CORRELATION_BASES: frozenset[str] = frozenset({"ZZ", "XX", "YY"})


def calculate_correlation_from_counts(
    counts: Mapping[str, int | float] | dict[str, Any],
) -> float:
    """Calculate the correlation expectation value E from binary measurement outcome counts.

    The mathematical formula is:
        E = (N_00 + N_11 - N_01 - N_10) / N_total
    where:
        N_total = N_00 + N_01 + N_10 + N_11

    This is mathematically equivalent to:
        E = P(same) - P(diff) = (P_00 + P_11) - (P_01 + P_10)

    Args:
        counts: Dictionary mapping two-qubit outcome bitstrings ('00', '01', '10', '11')
                to strictly non-negative integer or float counts.

    Returns:
        Correlation value E in the range [-1.0, +1.0].

    Raises:
        TypeError: If counts is not a dictionary or contains boolean values.
        ValueError: If counts is empty, contains unrecognized outcome keys (e.g. '000', '2', 'abc'),
                    contains non-finite values (NaN, Inf), contains negative counts,
                    or if total count sum is not strictly positive.
    """
    if not isinstance(counts, Mapping):
        raise TypeError(f"counts must be a dict or Mapping, got {type(counts).__name__}.")

    if len(counts) == 0:
        raise ValueError("Cannot calculate correlation from an empty counts dictionary.")

    # Validate keys against allowed two-qubit outcome labels
    for key in counts.keys():
        if not isinstance(key, str):
            raise TypeError(f"Outcome label must be a string, got {type(key).__name__} ({key!r}).")
        if key not in VALID_TWO_QUBIT_OUTCOMES:
            raise ValueError(
                f"Invalid two-qubit outcome label '{key}'. "
                f"Supported labels: {sorted(VALID_TWO_QUBIT_OUTCOMES)}."
            )

    # Validate count values
    for key, count in counts.items():
        if isinstance(count, bool):
            raise TypeError(f"Count for key '{key}' cannot be a boolean.")
        if not isinstance(count, (int, float, np.integer, np.floating)):
            raise TypeError(
                f"Count for key '{key}' must be numeric, got {type(count).__name__}."
            )
        if not np.isfinite(count):
            raise ValueError(f"Count for key '{key}' must be finite, got {count}.")
        if count < 0:
            raise ValueError(f"Count for key '{key}' cannot be negative, got {count}.")
        if isinstance(count, (float, np.floating)) and not np.isclose(count, round(count), atol=1e-9):
            raise TypeError(
                f"Count for key '{key}' must be an integer shot count, got fractional float {count}."
            )

    n_total = float(sum(counts.values()))
    if n_total <= 0.0:
        raise ValueError(
            f"Total count must be strictly positive, got sum = {n_total}. "
            "Cannot calculate correlation from zero total shots."
        )

    n_00 = float(counts.get("00", 0.0))
    n_11 = float(counts.get("11", 0.0))
    n_01 = float(counts.get("01", 0.0))
    n_10 = float(counts.get("10", 0.0))

    # Count-based formula
    correlation = (n_00 + n_11 - n_01 - n_10) / n_total

    # Probability-based formula validation: P(same) - P(diff)
    p_same = (n_00 + n_11) / n_total
    p_diff = (n_01 + n_10) / n_total
    p_correlation = p_same - p_diff

    # Verify mathematical identity between the two formulations
    if not np.isclose(correlation, p_correlation, atol=1e-12):
        raise ValueError(
            f"Count formulation ({correlation}) does not match probability formulation ({p_correlation})."
        )

    # Clamp residual floating-point rounding to strict mathematical [-1.0, 1.0] interval
    return float(np.clip(correlation, -1.0, 1.0))


def calculate_correlation_from_probabilities(
    probabilities: Mapping[str, float] | dict[str, Any],
    atol: float = 1e-7,
) -> float:
    """Calculate the correlation expectation value E from outcome probabilities.

    Formula:
        E = P(same) - P(diff) = (P_00 + P_11) - (P_01 + P_10)

    Args:
        probabilities: Dictionary mapping outcome bitstrings ('00', '01', '10', '11')
                       to probabilities in [0.0, 1.0].
        atol: Tolerance for verifying that probabilities sum to 1.0.

    Returns:
        Correlation value in [-1.0, +1.0].

    Raises:
        TypeError: If probabilities is not a dict or contains booleans.
        ValueError: If dictionary is empty, contains invalid outcome labels, non-finite values,
                    negative values, or if probabilities do not sum to 1.0 within tolerance.
    """
    if not isinstance(probabilities, Mapping):
        raise TypeError(f"probabilities must be a dict or Mapping, got {type(probabilities).__name__}.")

    if len(probabilities) == 0:
        raise ValueError("Cannot calculate correlation from empty probabilities dictionary.")

    for key in probabilities.keys():
        if not isinstance(key, str):
            raise TypeError(f"Outcome label must be a string, got {type(key).__name__} ({key!r}).")
        if key not in VALID_TWO_QUBIT_OUTCOMES:
            raise ValueError(
                f"Invalid outcome label '{key}'. Supported: {sorted(VALID_TWO_QUBIT_OUTCOMES)}."
            )

    for key, prob in probabilities.items():
        if isinstance(prob, bool):
            raise TypeError(f"Probability for '{key}' cannot be boolean.")
        if not isinstance(prob, (int, float, np.integer, np.floating)):
            raise TypeError(f"Probability for '{key}' must be numeric, got {type(prob).__name__}.")
        if not np.isfinite(prob):
            raise ValueError(f"Probability for '{key}' must be finite, got {prob}.")
        if prob < 0.0 or prob > 1.0 + atol:
            raise ValueError(f"Probability for '{key}' must be in [0, 1], got {prob}.")

    total_p = sum(probabilities.values())
    if not np.isclose(total_p, 1.0, atol=atol):
        raise ValueError(f"Probabilities must sum to 1.0 within atol={atol}, got sum = {total_p}.")

    p_00 = float(probabilities.get("00", 0.0))
    p_11 = float(probabilities.get("11", 0.0))
    p_01 = float(probabilities.get("01", 0.0))
    p_10 = float(probabilities.get("10", 0.0))

    p_same = p_00 + p_11
    p_diff = p_01 + p_10
    correlation = p_same - p_diff

    return float(np.clip(correlation, -1.0, 1.0))


def calculate_theoretical_bell_correlations(
    state: Any = BELL_PHI_PLUS,
    atol: float = 1e-7,
) -> dict[str, float]:
    """Calculate exact theoretical observable correlations (XX, YY, ZZ) on a two-qubit state.

    Calculates:
        XX = <psi| (X (x) X) |psi>
        YY = <psi| (Y (x) Y) |psi>
        ZZ = <psi| (Z (x) Z) |psi>

    Args:
        state: 4-element complex state vector, BellState instance, or standard Bell state name
               ('phi+', 'phi-', 'psi+', 'psi-').
        atol: Numerical tolerance for state normalization and reality verification.

    Returns:
        Dictionary mapping basis strings to exact theoretical expectations:
            {'XX': float, 'YY': float, 'ZZ': float}

    Raises:
        TypeError: If state cannot be validated.
        ValueError: If state shape != (4,), values are non-finite, zero-norm, unnormalized,
                    or if the expectation value contains an imaginary component.
    """
    if isinstance(state, str):
        vec = get_bell_state(state)
    elif isinstance(state, BellState):
        vec = state.vector
    else:
        vec = validate_two_qubit_state(state, atol=atol)

    # Calculate observable expectations via Hermitian operator tensor products
    e_xx = calculate_two_qubit_expectation_value(vec, "X", "X", atol=atol)
    e_yy = calculate_two_qubit_expectation_value(vec, "Y", "Y", atol=atol)
    e_zz = calculate_two_qubit_expectation_value(vec, "Z", "Z", atol=atol)

    # Clean tiny numerical residue for values within tolerance of integers (+1.0, 0.0, -1.0)
    if np.isclose(e_xx, round(e_xx), atol=atol):
        e_xx = float(round(e_xx))
    if np.isclose(e_yy, round(e_yy), atol=atol):
        e_yy = float(round(e_yy))
    if np.isclose(e_zz, round(e_zz), atol=atol):
        e_zz = float(round(e_zz))

    return {
        "XX": float(e_xx),
        "YY": float(e_yy),
        "ZZ": float(e_zz),
    }


def calculate_bell_correlations(
    target: Any,
    atol: float = 1e-7,
) -> dict[str, float]:
    """Calculate Bell correlations from either a quantum state or measurement counts/probabilities.

    This polymorphic interface handles:
        1. Two-qubit state vector / BellState / state label:
           Returns theoretical expectations: {'XX': float, 'YY': float, 'ZZ': float}.
        2. Dictionary of measurement counts or probabilities:
           Returns empirical correlation analysis:
               {'P_same': float, 'P_diff': float, 'correlation': float, 'ZZ': float}.

    Args:
        target: State vector, BellState instance, state name string, or dictionary of counts.
        atol: Tolerance for state normalization or probability checks.

    Returns:
        Dictionary with correlation values.

    Raises:
        TypeError / ValueError: If target is malformed or invalid.
    """
    if isinstance(target, dict):
        # Dictionary input: evaluate empirical / computational-basis correlation
        corr_val = calculate_correlation_from_counts(target)
        total_val = float(sum(target.values()))
        p_same = (float(target.get("00", 0.0)) + float(target.get("11", 0.0))) / total_val
        p_diff = (float(target.get("01", 0.0)) + float(target.get("10", 0.0))) / total_val
        return {
            "P_same": float(p_same),
            "P_diff": float(p_diff),
            "correlation": float(corr_val),
            "ZZ": float(corr_val),
        }

    # State input: evaluate theoretical expectations (XX, YY, ZZ)
    return calculate_theoretical_bell_correlations(target, atol=atol)


def create_bell_correlation_circuit(
    state: Any = BELL_PHI_PLUS,
    basis: str = "ZZ",
    circuit_name: str = "bell_corr_circuit",
) -> QuantumCircuit:
    """Create a two-qubit Qiskit QuantumCircuit rotated to measure in the specified basis.

    Unitary pre-measurement rotations to computational (Z) basis:
        - Z basis: No rotation.
        - X basis: Hadamard (H) gate on each qubit (H X H = Z).
        - Y basis: S† gate followed by Hadamard (H) gate on each qubit (H S† Y S H = Z).

    Args:
        state: Canonical Bell state name, BellState, or 4-element state vector.
        basis: Two-character basis specifier: 'ZZ' (or 'Z'), 'XX' (or 'X'), 'YY' (or 'Y').
        circuit_name: Name for the QuantumCircuit.

    Returns:
        A Qiskit QuantumCircuit with 2 qubits and 2 classical bits.

    Raises:
        ValueError: If basis is unrecognized or state is invalid.
    """
    clean_basis = basis.strip().upper()
    if len(clean_basis) == 1 and clean_basis in ("X", "Y", "Z"):
        clean_basis = clean_basis + clean_basis

    if clean_basis not in SUPPORTED_CORRELATION_BASES:
        raise ValueError(
            f"Invalid correlation basis '{basis}'. "
            f"Supported bases: {sorted(SUPPORTED_CORRELATION_BASES)}."
        )

    # Prepare initial quantum state
    if isinstance(state, BellState):
        qc = state.to_circuit(circuit_name=circuit_name, measure=False)
    elif isinstance(state, str) and state.strip().lower() in ("phi+", "phi_plus", "|phi+>"):
        qc = create_bell_circuit(circuit_name=circuit_name, measure=False, bell_type="phi_plus")
    elif isinstance(state, str) and state.strip().lower() in ("phi-", "phi_minus", "|phi->"):
        qc = create_bell_circuit(circuit_name=circuit_name, measure=False, bell_type="phi_minus")
    elif isinstance(state, str) and state.strip().lower() in ("psi+", "psi_plus", "|psi+>"):
        qc = create_bell_circuit(circuit_name=circuit_name, measure=False, bell_type="psi_plus")
    elif isinstance(state, str) and state.strip().lower() in ("psi-", "psi_minus", "|psi->"):
        qc = create_bell_circuit(circuit_name=circuit_name, measure=False, bell_type="psi_minus")
    else:
        vec = validate_two_qubit_state(state)
        if np.allclose(vec, BELL_PHI_PLUS):
            qc = create_bell_circuit(circuit_name=circuit_name, measure=False, bell_type="phi_plus")
        elif np.allclose(vec, BELL_PHI_MINUS):
            qc = create_bell_circuit(circuit_name=circuit_name, measure=False, bell_type="phi_minus")
        elif np.allclose(vec, BELL_PSI_PLUS):
            qc = create_bell_circuit(circuit_name=circuit_name, measure=False, bell_type="psi_plus")
        elif np.allclose(vec, BELL_PSI_MINUS):
            qc = create_bell_circuit(circuit_name=circuit_name, measure=False, bell_type="psi_minus")
        else:
            qc = QuantumCircuit(2, name=circuit_name)
            # Map from project big-endian (|00>, |01>, |10>, |11>) to Qiskit Statevector (q0 + 2*q1):
            # |00> -> index 0, |10> -> index 1, |01> -> index 2, |11> -> index 3
            vec_qiskit = np.array([vec[0], vec[2], vec[1], vec[3]], dtype=np.complex128)
            qc.initialize(Statevector(vec_qiskit), [0, 1])

    # Ensure classical register exists
    if qc.num_clbits < 2:
        cr = ClassicalRegister(2, "c")
        qc.add_register(cr)

    # Apply basis rotations
    b0, b1 = clean_basis[0], clean_basis[1]
    for qubit_idx, b in enumerate((b0, b1)):
        if b == "X":
            qc.h(qubit_idx)
        elif b == "Y":
            qc.sdg(qubit_idx)
            qc.h(qubit_idx)
        # For 'Z', no rotation needed

    # Measure qubits into corresponding classical bits: q0 -> c0, q1 -> c1
    qc.measure(0, 0)
    qc.measure(1, 1)

    return qc


def measure_bell_correlation(
    state: Any = BELL_PHI_PLUS,
    basis: str = "ZZ",
    shots: int = 1024,
    seed: int | None = None,
    simulator: AerSimulator | None = None,
) -> tuple[dict[str, int], float]:
    """Measure a two-qubit state in a chosen correlation basis (ZZ, XX, YY) via Aer simulation.

    Args:
        state: Two-qubit state representation.
        basis: Measurement basis ('ZZ', 'XX', or 'YY').
        shots: Number of simulation repetitions (strictly positive integer).
        seed: Optional integer random seed for reproducibility.
        simulator: Optional AerSimulator instance.

    Returns:
        Tuple of (counts_dict, empirical_correlation).

    Raises:
        TypeError: If shots or seed have invalid types.
        ValueError: If shots <= 0, seed < 0, or basis is unsupported.
    """
    if not isinstance(shots, int) or isinstance(shots, bool):
        raise TypeError(f"Shots must be an integer, got {type(shots).__name__}.")
    if shots <= 0:
        raise ValueError(f"Shots must be a strictly positive integer, got {shots}.")

    if seed is not None:
        if not isinstance(seed, int) or isinstance(seed, bool):
            raise TypeError(f"Seed must be an integer, got {type(seed).__name__}.")
        if seed < 0:
            raise ValueError(f"Seed must be a non-negative integer, got {seed}.")

    qc = create_bell_correlation_circuit(state, basis=basis)

    if simulator is None:
        simulator = AerSimulator()

    job = simulator.run(qc, shots=shots, seed_simulator=seed)
    raw_counts = job.result().get_counts()

    # Qiskit classical register bitstring is little-endian 'c1 c0'.
    # Map to project canonical 'q0q1' = f"{c0}{c1}".
    counts: dict[str, int] = {}
    for bitstring, count in raw_counts.items():
        clean = bitstring.replace(" ", "")
        if len(clean) == 2:
            c1, c0 = clean[0], clean[1]
            key = f"{c0}{c1}"
            counts[key] = counts.get(key, 0) + count
        else:
            counts[clean] = counts.get(clean, 0) + count

    correlation = calculate_correlation_from_counts(counts)
    return counts, correlation


def measure_all_bell_correlations(
    state: Any = BELL_PHI_PLUS,
    shots: int = 1024,
    seed: int | None = None,
    simulator: AerSimulator | None = None,
) -> dict[str, dict[str, Any]]:
    """Measure a two-qubit state across all three canonical bases: XX, YY, and ZZ.

    Args:
        state: Two-qubit state representation.
        shots: Number of repetitions per basis measurement.
        seed: Optional integer random seed for reproducibility.
        simulator: Optional AerSimulator instance.

    Returns:
        Dictionary mapping each basis ('XX', 'YY', 'ZZ') to:
            {
                'counts': dict[str, int],
                'empirical': float,
                'theoretical': float,
                'deviation': float,
            }
    """
    theo = calculate_theoretical_bell_correlations(state)
    results: dict[str, dict[str, Any]] = {}

    for idx, b in enumerate(["XX", "YY", "ZZ"]):
        basis_seed = None if seed is None else seed + idx * 100
        counts, emp_corr = measure_bell_correlation(
            state=state,
            basis=b,
            shots=shots,
            seed=basis_seed,
            simulator=simulator,
        )
        deviation = abs(emp_corr - theo[b])
        results[b] = {
            "counts": counts,
            "empirical": emp_corr,
            "theoretical": theo[b],
            "deviation": deviation,
        }

    return results


def calculate_bell_correlation_deviations(
    empirical_correlations: Mapping[str, float],
    theoretical_correlations: Mapping[str, float],
) -> dict[str, float]:
    """Calculate absolute deviation |empirical - theoretical| for each evaluated basis.

    Args:
        empirical_correlations: Dictionary mapping basis ('XX', 'YY', 'ZZ') to empirical value.
        theoretical_correlations: Dictionary mapping basis to theoretical expectation value.

    Returns:
        Dictionary mapping basis to absolute error float.
    """
    deviations: dict[str, float] = {}
    for basis, emp_val in empirical_correlations.items():
        if basis in theoretical_correlations:
            deviations[basis] = float(abs(emp_val - theoretical_correlations[basis]))
    return deviations

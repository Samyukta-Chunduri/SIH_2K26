"""Q-SHIELD — Quantum Measurement Module (Milestones M1 & M3).

Provides projective measurements, Born-rule probability calculations, empirical sampling,
projector operators, and expectation value derivations for pure single-qubit states
across the computational (Z), Hadamard (X), and circular (Y) bases.

Mathematical Model:
    Projective Measurement:
        P_i = |i><i|
        Probability: P(i) = <psi|P_i|psi> = |<i|psi>|^2
        Completeness: sum_i P_i = I
        Orthonormality: <b_i|b_j> = delta_ij
        Idempotence: P_i^2 = P_i

    Measurement Bases:
        Z basis: |0>, |1>       Outcomes: '0', '1'
        X basis: |+>, |->       Outcomes: '+', '-'
        Y basis: |+i>, |-i>     Outcomes: '+i', '-i'

    Expectation Values:
        <Z> = P(0) - P(1)
        <X> = P(+) - P(-)
        <Y> = P(+i) - P(-i)
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any
import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import ClassicalRegister
from qiskit_aer import AerSimulator

from .states import (
    STATE_0,
    STATE_1,
    STATE_PLUS,
    STATE_MINUS,
    STATE_PLUS_I,
    STATE_MINUS_I,
    QubitState,
    create_qubit_circuit,
    get_standard_state,
    validate_state_vector,
)


# Standard 2x2 Projector Matrices (dtype=np.complex128)
# Z basis: P_0 = |0><0|, P_1 = |1><1|
PROJECTOR_Z_0: np.ndarray = np.outer(STATE_0, STATE_0.conj())
PROJECTOR_Z_1: np.ndarray = np.outer(STATE_1, STATE_1.conj())

# X basis: P_+ = |+><+|, P_- = |-><-|
PROJECTOR_X_PLUS: np.ndarray = np.outer(STATE_PLUS, STATE_PLUS.conj())
PROJECTOR_X_MINUS: np.ndarray = np.outer(STATE_MINUS, STATE_MINUS.conj())

# Y basis: P_+i = |+i><+i|, P_-i = |-i><-i|
PROJECTOR_Y_PLUS_I: np.ndarray = np.outer(STATE_PLUS_I, STATE_PLUS_I.conj())
PROJECTOR_Y_MINUS_I: np.ndarray = np.outer(STATE_MINUS_I, STATE_MINUS_I.conj())

_BASIS_INFO: dict[str, dict[str, Any]] = {
    "z": {
        "name": "Z",
        "labels": ("0", "1"),
        "states": (STATE_0, STATE_1),
        "projectors": (PROJECTOR_Z_0, PROJECTOR_Z_1),
    },
    "computational": {
        "name": "Z",
        "labels": ("0", "1"),
        "states": (STATE_0, STATE_1),
        "projectors": (PROJECTOR_Z_0, PROJECTOR_Z_1),
    },
    "x": {
        "name": "X",
        "labels": ("+", "-"),
        "states": (STATE_PLUS, STATE_MINUS),
        "projectors": (PROJECTOR_X_PLUS, PROJECTOR_X_MINUS),
    },
    "hadamard": {
        "name": "X",
        "labels": ("+", "-"),
        "states": (STATE_PLUS, STATE_MINUS),
        "projectors": (PROJECTOR_X_PLUS, PROJECTOR_X_MINUS),
    },
    "y": {
        "name": "Y",
        "labels": ("+i", "-i"),
        "states": (STATE_PLUS_I, STATE_MINUS_I),
        "projectors": (PROJECTOR_Y_PLUS_I, PROJECTOR_Y_MINUS_I),
    },
    "circular": {
        "name": "Y",
        "labels": ("+i", "-i"),
        "states": (STATE_PLUS_I, STATE_MINUS_I),
        "projectors": (PROJECTOR_Y_PLUS_I, PROJECTOR_Y_MINUS_I),
    },
}


def get_basis_projectors(basis: str) -> tuple[np.ndarray, np.ndarray, tuple[str, str]]:
    """Retrieve the two 2x2 projector matrices and outcome labels for a given measurement basis.

    Args:
        basis: Measurement basis identifier ('Z', 'X', 'Y', or case-insensitive synonyms).

    Returns:
        Tuple of (P_0_matrix, P_1_matrix, (label_0, label_1)).

    Raises:
        ValueError: If the basis name is unrecognized.
    """
    key = basis.strip().lower()
    if key in _BASIS_INFO:
        info = _BASIS_INFO[key]
        p0, p1 = info["projectors"]
        return p0.copy(), p1.copy(), info["labels"]
    raise ValueError(
        f"Unknown measurement basis '{basis}'. Supported bases: ['Z', 'X', 'Y']."
    )


def get_basis_states(basis: str) -> tuple[np.ndarray, np.ndarray, tuple[str, str]]:
    """Retrieve the two normalized eigenstate vectors and outcome labels for a basis.

    Args:
        basis: Measurement basis identifier ('Z', 'X', 'Y').

    Returns:
        Tuple of (state_0, state_1, (label_0, label_1)).

    Raises:
        ValueError: If the basis name is unrecognized.
    """
    key = basis.strip().lower()
    if key in _BASIS_INFO:
        info = _BASIS_INFO[key]
        s0, s1 = info["states"]
        return s0.copy(), s1.copy(), info["labels"]
    raise ValueError(
        f"Unknown measurement basis '{basis}'. Supported bases: ['Z', 'X', 'Y']."
    )


def projective_probabilities(
    state: Any,
    basis: str = "Z",
    atol: float = 1e-7,
) -> dict[str, float]:
    """Calculate exact theoretical measurement probabilities via the Born rule.

    For state |psi> and projector P_i:
        P(i) = <psi|P_i|psi> = |<i|psi>|^2

    Args:
        state: State vector, standard state string (e.g. '0', '+', '+i'), or QubitState.
        basis: Measurement basis ('Z', 'X', or 'Y').
        atol: Numerical tolerance for probability normalization check.

    Returns:
        Dictionary mapping outcome labels to their respective Born-rule probabilities.

    Raises:
        TypeError: If state cannot be interpreted as a valid quantum state.
        ValueError: If state is invalid or basis is unknown.
    """
    if isinstance(state, str):
        vec = get_standard_state(state)
    elif isinstance(state, QubitState):
        vec = state.vector
    else:
        vec = validate_state_vector(state, atol=atol)

    p0_mat, p1_mat, (lbl0, lbl1) = get_basis_projectors(basis)

    # Compute Born-rule expectation: P(i) = <psi| P_i |psi>
    prob_0 = float(np.real(np.vdot(vec, p0_mat @ vec)))
    prob_1 = float(np.real(np.vdot(vec, p1_mat @ vec)))

    # Guarantee numerical boundary in [0.0, 1.0] and clean machine precision residuals
    if np.isclose(prob_0, 1.0, atol=atol):
        prob_0, prob_1 = 1.0, 0.0
    elif np.isclose(prob_1, 1.0, atol=atol):
        prob_0, prob_1 = 0.0, 1.0
    else:
        prob_0 = max(0.0, min(1.0, prob_0))
        prob_1 = max(0.0, min(1.0, prob_1))

    total = prob_0 + prob_1
    if not np.isclose(total, 1.0, atol=atol):
        raise ValueError(
            f"Projective probabilities do not sum to 1.0: {prob_0} + {prob_1} = {total} (atol={atol})."
        )

    return {lbl0: prob_0, lbl1: prob_1}


def sample_measurement(
    probabilities: dict[str, float],
    shots: int = 1024,
    seed: int | None = None,
) -> dict[str, int]:
    """Sample repeated measurement outcomes according to a probability distribution.

    Args:
        probabilities: Dictionary mapping outcome strings to probabilities in [0.0, 1.0].
        shots: Total number of measurement shots (strictly positive integer).
        seed: Optional integer random seed for reproducibility.

    Returns:
        Dictionary mapping outcome strings to sampled integer counts.

    Raises:
        TypeError: If shots or seed have invalid types.
        ValueError: If shots <= 0 or seed < 0.
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

    keys = list(probabilities.keys())
    p_vals = np.array([probabilities[k] for k in keys], dtype=np.float64)

    # Normalize small floating-point residual for numpy multinomial
    p_sum = float(p_vals.sum())
    if p_sum <= 0.0:
        raise ValueError("Probabilities must sum to a positive number.")
    p_normalized = p_vals / p_sum

    rng = np.random.default_rng(seed)
    counts_array = rng.multinomial(shots, p_normalized)

    return {k: int(cnt) for k, cnt in zip(keys, counts_array)}


def calculate_empirical_probabilities(
    counts: Mapping[Any, Any],
    total_shots: int | None = None,
) -> dict[str, float]:
    """Calculate empirical measurement probabilities from outcome counts.

    p_hat_i = n_i / N

    Args:
        counts: Dictionary mapping outcome labels to integer counts.
        total_shots: Optional total number of shots. If None, sum of counts is used.

    Returns:
        Dictionary mapping outcome labels to empirical probabilities in [0.0, 1.0].

    Raises:
        TypeError: If counts is not a dictionary or count values are not integers.
        ValueError: If total shots <= 0 or any count is negative.
    """
    if not isinstance(counts, (dict, Mapping)):
        raise TypeError(f"Counts must be a dictionary, got {type(counts).__name__}.")

    # Canonicalize outcomes while preserving basis categories
    clean_counts: dict[str, int] = {}
    keys = list(counts.keys())

    # Detect outcome basis format
    has_plus_minus = any(k in ("+", "-") for k in keys)
    has_plus_minus_i = any(k in ("+i", "-i") for k in keys)
    has_standard_bits = any(k in ("0", "1", 0, 1) for k in keys)

    if has_plus_minus_i:
        unknown = [k for k in keys if k not in ("+i", "-i")]
        if unknown:
            raise ValueError(f"Unrecognized outcome labels for Y-basis counts: {unknown}.")
        c0 = counts.get("+i", 0)
        c1 = counts.get("-i", 0)
        clean_counts = {"+i": c0, "-i": c1}
    elif has_plus_minus:
        unknown = [k for k in keys if k not in ("+", "-")]
        if unknown:
            raise ValueError(f"Unrecognized outcome labels for X-basis counts: {unknown}.")
        c0 = counts.get("+", 0)
        c1 = counts.get("-", 0)
        clean_counts = {"+": c0, "-": c1}
    elif has_standard_bits or len(counts) == 0:
        unknown = [k for k in keys if k not in ("0", "1", 0, 1)]
        if unknown:
            raise ValueError(f"Unrecognized outcome labels for Z-basis counts: {unknown}.")
        c0 = counts.get("0", counts.get(0, 0))
        c1 = counts.get("1", counts.get(1, 0))
        clean_counts = {"0": c0, "1": c1}
    else:
        clean_counts = {str(k): v for k, v in counts.items()}

    # Validate non-negative integers
    for k, v in clean_counts.items():
        if not isinstance(v, int) or isinstance(v, bool):
            raise TypeError(f"Counts values must be integers, got {type(v).__name__} for key '{k}'.")
        if v < 0:
            raise ValueError(f"Measurement count cannot be negative: '{k}': {v}.")

    shots = total_shots if total_shots is not None else sum(clean_counts.values())
    if shots <= 0:
        raise ValueError(f"Total shots must be a positive number, got {shots}.")

    return {k: float(v / shots) for k, v in clean_counts.items()}


def calculate_expectation_value(
    probabilities_or_counts: Mapping[Any, Any],
    basis: str = "Z",
) -> float:
    """Calculate the Pauli expectation value <Z>, <X>, or <Y> from probabilities or counts.

    Mathematical Model:
        <Z> = P(0) - P(1)
        <X> = P(+) - P(-)
        <Y> = P(+i) - P(-i)

    Args:
        probabilities_or_counts: Dictionary with measurement probabilities or raw counts.
        basis: Observable basis ('Z', 'X', or 'Y').

    Returns:
        Expectation value in range [-1.0, 1.0].

    Raises:
        ValueError: If basis is unrecognized or outcome labels do not match the basis.
    """
    key = basis.strip().lower()
    if key not in _BASIS_INFO:
        raise ValueError(f"Unknown measurement basis '{basis}'. Supported bases: ['Z', 'X', 'Y'].")

    if not isinstance(probabilities_or_counts, (dict, Mapping)) or len(probabilities_or_counts) == 0:
        raise ValueError("Must provide a non-empty dictionary of probabilities or counts.")

    # If inputs are integer counts, convert to empirical probabilities
    is_counts = any(isinstance(v, int) and not isinstance(v, bool) for v in probabilities_or_counts.values())
    if is_counts and sum(probabilities_or_counts.values()) > 1:
        probs = calculate_empirical_probabilities(probabilities_or_counts)
    else:
        probs = {str(k): float(v) for k, v in probabilities_or_counts.items()}

    if key in ("z", "computational"):
        valid_z = {"0", "1", 0, 1}
        if not any(k in valid_z for k in probabilities_or_counts.keys()):
            raise ValueError(
                f"Expected outcome labels ('0', '1') for Z basis, got {list(probabilities_or_counts.keys())}."
            )
        p0 = float(probs.get("0", 0.0))
        p1 = float(probs.get("1", 0.0))
        return float(p0 - p1)
    elif key in ("x", "hadamard"):
        valid_x = {"+", "-"}
        if not any(k in valid_x for k in probabilities_or_counts.keys()):
            raise ValueError(
                f"Expected outcome labels ('+', '-') for X basis, got {list(probabilities_or_counts.keys())}."
            )
        p_plus = float(probs.get("+", 0.0))
        p_minus = float(probs.get("-", 0.0))
        return float(p_plus - p_minus)
    else:  # Y basis
        valid_y = {"+i", "-i"}
        if not any(k in valid_y for k in probabilities_or_counts.keys()):
            raise ValueError(
                f"Expected outcome labels ('+i', '-i') for Y basis, got {list(probabilities_or_counts.keys())}."
            )
        p_plus_i = float(probs.get("+i", 0.0))
        p_minus_i = float(probs.get("-i", 0.0))
        return float(p_plus_i - p_minus_i)


def measure_projective(
    state: Any,
    basis: str = "Z",
    shots: int = 1024,
    seed: int | None = None,
) -> tuple[dict[str, int], dict[str, float]]:
    """Perform a single-qubit projective measurement in the Z, X, or Y basis.

    Calculates exact Born-rule probabilities and samples repeated outcomes.

    Args:
        state: State vector, standard state string, or QubitState.
        basis: Measurement basis ('Z', 'X', or 'Y').
        shots: Number of measurement repetitions (integer > 0).
        seed: Optional random seed for reproducible sampling.

    Returns:
        Tuple of (counts_dict, empirical_probabilities_dict).
    """
    theo_probs = projective_probabilities(state, basis=basis)
    counts = sample_measurement(theo_probs, shots=shots, seed=seed)
    emp_probs = calculate_empirical_probabilities(counts, total_shots=shots)
    return counts, emp_probs


def create_basis_measurement_circuit(
    state: Any = STATE_0,
    basis: str = "Z",
    circuit_name: str = "basis_meas_circuit",
) -> QuantumCircuit:
    """Create a single-qubit Qiskit QuantumCircuit rotated into the specified basis for measurement.

    Basis rotations to computational (Z) basis:
        - Z basis: No rotation
        - X basis: Hadamard (H) gate: H|+> = |0>, H|-> = |1>
        - Y basis: S† gate followed by Hadamard (H) gate:
                   H S† |+i> = |0>, H S† |-i> = |1>

    Args:
        state: Quantum state to initialize.
        basis: Measurement basis ('Z', 'X', or 'Y').
        circuit_name: Name for the QuantumCircuit.

    Returns:
        A Qiskit QuantumCircuit with 1 qubit and 1 classical bit, with basis rotation and measurement.
    """
    key = basis.strip().lower()
    if key not in _BASIS_INFO:
        raise ValueError(f"Unknown measurement basis '{basis}'. Supported bases: ['Z', 'X', 'Y'].")

    qc = create_qubit_circuit(state, circuit_name=circuit_name)
    if qc.num_clbits == 0:
        cr = ClassicalRegister(1, "c")
        qc.add_register(cr)

    # Apply basis rotation before Z-basis projection
    if key in ("x", "hadamard"):
        qc.h(0)
    elif key in ("y", "circular"):
        qc.sdg(0)
        qc.h(0)

    qc.measure(0, 0)
    return qc


def measure_qubit(
    circuit: QuantumCircuit,
    shots: int = 1024,
    simulator: AerSimulator | None = None,
    seed_simulator: int | None = None,
) -> dict[str, int]:
    """Execute a single-qubit measurement on Qiskit Aer and return raw counts.

    If the provided circuit does not contain classical registers or measurement
    operations, a copy with a 1-bit classical register and measurement is created.

    Args:
        circuit: Qiskit QuantumCircuit containing at least 1 qubit.
        shots: Number of measurement repetitions (must be an integer > 0).
        simulator: Optional AerSimulator instance. A new AerSimulator is used if None.
        seed_simulator: Optional integer random seed for reproducibility.

    Returns:
        Dictionary containing counts for both '0' and '1' basis outcomes, e.g. {'0': 512, '1': 512}.

    Raises:
        TypeError: If shots is not an integer or circuit is not a QuantumCircuit.
        ValueError: If shots <= 0 or circuit has no qubits.
    """
    if not isinstance(shots, int) or isinstance(shots, bool):
        raise TypeError(f"Shots must be an integer, got {type(shots).__name__}.")
    if shots <= 0:
        raise ValueError(f"Shots must be a strictly positive integer, got {shots}.")

    if not isinstance(circuit, QuantumCircuit):
        raise TypeError(f"Expected a Qiskit QuantumCircuit, got {type(circuit).__name__}.")
    if circuit.num_qubits < 1:
        raise ValueError("Circuit must have at least 1 qubit to measure.")

    # Prepare circuit copy with measurement
    meas_qc = circuit.copy()
    if meas_qc.num_clbits == 0:
        meas_qc.measure_all()
    elif not any(inst.operation.name == "measure" for inst in meas_qc.data):
        meas_qc.measure(0, 0)

    sim = simulator if simulator is not None else AerSimulator()

    run_kwargs: dict[str, Any] = {"shots": shots}
    if seed_simulator is not None:
        if not isinstance(seed_simulator, int) or isinstance(seed_simulator, bool):
            raise TypeError(f"Seed must be an integer, got {type(seed_simulator).__name__}.")
        if seed_simulator < 0:
            raise ValueError(f"Seed must be a non-negative integer, got {seed_simulator}.")
        run_kwargs["seed_simulator"] = seed_simulator

    job = sim.run(meas_qc, **run_kwargs)
    result = job.result()
    raw_counts = result.get_counts()

    # In Qiskit, measurement outcomes are bitstrings like '0' or '1'.
    counts: dict[str, int] = {"0": 0, "1": 0}
    for bitstring, count in raw_counts.items():
        clean_bit = bitstring.replace(" ", "")[-1]
        if clean_bit in counts:
            counts[clean_bit] += count
        else:
            counts[clean_bit] = count

    # Safety assertion: total counts must equal requested shots
    total_recorded = counts["0"] + counts["1"]
    if total_recorded != shots:
        raise RuntimeError(
            f"Measurement counts sum ({total_recorded}) does not match requested shots ({shots})."
        )

    return counts


def measure_state(
    state: Any,
    basis_or_shots: Any = "Z",
    shots: int = 1024,
    simulator: AerSimulator | None = None,
    seed_simulator: int | None = None,
) -> tuple[dict[str, int], dict[str, float]]:
    """Initialize a single-qubit circuit to the given state and measure it.

    Supports both legacy M1 signature:
        measure_state(state, shots=1024, simulator=..., seed_simulator=...)
    and M3 basis specification:
        measure_state(state, basis='X', shots=1024, ...)

    Args:
        state: State vector or standard state name (e.g. '0', '1', '+', '-').
        basis_or_shots: Measurement basis ('Z', 'X', 'Y') or integer shots count for legacy calls.
        shots: Number of simulation shots (used when basis_or_shots is a basis string).
        simulator: Optional AerSimulator instance.
        seed_simulator: Optional random seed for simulation.

    Returns:
        Tuple of (counts_dict, empirical_probabilities_dict).
    """
    # Handle backward compatibility where 2nd arg is shots
    if isinstance(basis_or_shots, (int, float)) and not isinstance(basis_or_shots, bool):
        actual_shots = int(basis_or_shots)
        basis = "Z"
    elif isinstance(basis_or_shots, str):
        basis = basis_or_shots
        actual_shots = shots
    else:
        basis = "Z"
        actual_shots = shots

    key = basis.strip().lower()
    if key in ("z", "computational"):
        circuit = create_qubit_circuit(state)
        counts = measure_qubit(
            circuit,
            shots=actual_shots,
            simulator=simulator,
            seed_simulator=seed_simulator,
        )
        probs = calculate_empirical_probabilities(counts, total_shots=actual_shots)
        return counts, probs
    elif key in ("x", "hadamard"):
        qc = create_basis_measurement_circuit(state, basis="X")
        raw_counts = measure_qubit(qc, shots=actual_shots, simulator=simulator, seed_simulator=seed_simulator)
        # Map outcome '0' -> '+', '1' -> '-'
        counts = {"+": raw_counts.get("0", 0), "-": raw_counts.get("1", 0)}
        probs = calculate_empirical_probabilities(counts, total_shots=actual_shots)
        return counts, probs
    elif key in ("y", "circular"):
        qc = create_basis_measurement_circuit(state, basis="Y")
        raw_counts = measure_qubit(qc, shots=actual_shots, simulator=simulator, seed_simulator=seed_simulator)
        # Map outcome '0' -> '+i', '1' -> '-i'
        counts = {"+i": raw_counts.get("0", 0), "-i": raw_counts.get("1", 0)}
        probs = calculate_empirical_probabilities(counts, total_shots=actual_shots)
        return counts, probs
    else:
        raise ValueError(f"Unknown measurement basis '{basis}'. Supported bases: ['Z', 'X', 'Y'].")

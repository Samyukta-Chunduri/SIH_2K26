"""Q-SHIELD — Quantum Bell State & Entanglement Module (Milestone M4).

Provides representation, circuit construction, mathematical entanglement validation,
Born-rule probabilities, correlation evaluation, and simulation for two-qubit Bell states,
primarily the canonical state:
    |Phi+> = (|00> + |11>) / sqrt(2)

And supporting the complete orthonormal Bell basis:
    |Phi-> = (|00> - |11>) / sqrt(2)
    |Psi+> = (|01> + |10>) / sqrt(2)
    |Psi-> = (|01> - |10>) / sqrt(2)

Mathematical Model & Conventions:
    1. Basis Ordering (Project Big-Endian Convention):
       State vector ordering corresponds to computational basis:
           |00> -> index 0 (q0=0, q1=0)
           |01> -> index 1 (q0=0, q1=1)
           |10> -> index 2 (q0=1, q1=0)
           |11> -> index 3 (q0=1, q1=1)
       Basis index = 2 * q0 + q1.

    2. Canonical |Phi+> State Vector:
       |Phi+> = [1/sqrt(2), 0, 0, 1/sqrt(2)]^T

    3. Computational-Basis Measurement Probabilities:
       P(00) = 1/2, P(11) = 1/2, P(01) = 0, P(10) = 0

    4. Correlation Properties:
       P(q0 == q1) = 1.0, P(q0 != q1) = 0.0
       <Z (x) Z> = +1.0
       <X (x) X> = +1.0
       <Y (x) Y> = -1.0

    5. Entanglement Verification (Schmidt Rank / Coefficient Matrix):
       For |psi> = sum_{i,j} c_{ij} |ij>, form 2x2 coefficient matrix:
           C = [[c_00, c_01], [c_10, c_11]]
       Singular values of C give Schmidt coefficients.
       rank(C) == 1 => Separable product state.
       rank(C) > 1  => Entangled pure state (rank 2 for Bell states).

    6. Reduced Density Matrices:
       rho_A = Tr_B(|Phi+><Phi+|) = I_2 / 2 (maximally mixed)
       rho_B = Tr_A(|Phi+><Phi+|) = I_2 / 2 (maximally mixed)

    7. Qiskit Aer Little-Endian Mapping:
       Qiskit returns bitstrings in little-endian order 'c1 c0'.
       When q0 -> c0 and q1 -> c1, bitstring[1] is c0 and bitstring[0] is c1.
       Canonical keys are mapped as 'q0q1' = f"{c0}{c1}".

Scientific Boundary:
    This module provides the quantum-mechanical foundation for two-qubit entanglement.
    Entanglement is a resource for quantum protocols; it does not by itself guarantee
    cryptographic security or attack immunity without complete protocol verification.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any
import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import ClassicalRegister
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator

from .measurements import calculate_empirical_probabilities
from .pauli import (
    PAULI_I,
    PAULI_X,
    PAULI_Y,
    PAULI_Z,
    get_pauli_operator,
    validate_operator,
)

# Normalization constant 1 / sqrt(2)
INV_SQRT_2: float = 1.0 / np.sqrt(2.0)

# Canonical 4-element state vectors in computational basis (|00>, |01>, |10>, |11>)
BELL_PHI_PLUS: np.ndarray = np.array(
    [INV_SQRT_2, 0.0, 0.0, INV_SQRT_2],
    dtype=np.complex128,
)
BELL_PHI_PLUS.flags.writeable = False

BELL_PHI_MINUS: np.ndarray = np.array(
    [INV_SQRT_2, 0.0, 0.0, -INV_SQRT_2],
    dtype=np.complex128,
)
BELL_PHI_MINUS.flags.writeable = False

BELL_PSI_PLUS: np.ndarray = np.array(
    [0.0, INV_SQRT_2, INV_SQRT_2, 0.0],
    dtype=np.complex128,
)
BELL_PSI_PLUS.flags.writeable = False

BELL_PSI_MINUS: np.ndarray = np.array(
    [0.0, INV_SQRT_2, -INV_SQRT_2, 0.0],
    dtype=np.complex128,
)
BELL_PSI_MINUS.flags.writeable = False

# Basis state labels in standard ordering
TWO_QUBIT_BASIS_LABELS: tuple[str, str, str, str] = ("00", "01", "10", "11")

_BELL_STATES: dict[str, np.ndarray] = {
    "phi+": BELL_PHI_PLUS,
    "phi_plus": BELL_PHI_PLUS,
    "|phi+>": BELL_PHI_PLUS,
    "|phi+⟩": BELL_PHI_PLUS,
    "|φ+>": BELL_PHI_PLUS,
    "|φ+⟩": BELL_PHI_PLUS,
    "phi-": BELL_PHI_MINUS,
    "phi_minus": BELL_PHI_MINUS,
    "|phi->": BELL_PHI_MINUS,
    "|phi-⟩": BELL_PHI_MINUS,
    "|φ->": BELL_PHI_MINUS,
    "|φ-⟩": BELL_PHI_MINUS,
    "psi+": BELL_PSI_PLUS,
    "psi_plus": BELL_PSI_PLUS,
    "|psi+>": BELL_PSI_PLUS,
    "|psi+⟩": BELL_PSI_PLUS,
    "|ψ+>": BELL_PSI_PLUS,
    "|ψ+⟩": BELL_PSI_PLUS,
    "psi-": BELL_PSI_MINUS,
    "psi_minus": BELL_PSI_MINUS,
    "|psi->": BELL_PSI_MINUS,
    "|psi-⟩": BELL_PSI_MINUS,
    "|ψ->": BELL_PSI_MINUS,
    "|ψ-⟩": BELL_PSI_MINUS,
}


def create_bell_phi_plus() -> np.ndarray:
    """Create a new copy of the canonical |Phi+> Bell state vector.

    Returns:
        A normalized 4-element numpy array of type np.complex128:
            |Phi+> = [1/sqrt(2), 0, 0, 1/sqrt(2)]^T
    """
    return BELL_PHI_PLUS.copy()


def create_bell_phi_minus() -> np.ndarray:
    """Create a new copy of the |Phi-> Bell state vector: (|00> - |11>) / sqrt(2)."""
    return BELL_PHI_MINUS.copy()


def create_bell_psi_plus() -> np.ndarray:
    """Create a new copy of the |Psi+> Bell state vector: (|01> + |10>) / sqrt(2)."""
    return BELL_PSI_PLUS.copy()


def create_bell_psi_minus() -> np.ndarray:
    """Create a new copy of the |Psi-> Bell state vector: (|01> - |10>) / sqrt(2)."""
    return BELL_PSI_MINUS.copy()


def get_bell_state(name: str) -> np.ndarray:
    """Retrieve a copy of a canonical two-qubit Bell state vector by name or label.

    Supported names (case-insensitive):
        'phi+', 'phi_plus', '|Phi+>', 'phi-', 'phi_minus', '|Phi->',
        'psi+', 'psi_plus', '|Psi+>', 'psi-', 'psi_minus', '|Psi->'

    Args:
        name: Name or label for the Bell state.

    Returns:
        A normalized 4-element complex numpy array.

    Raises:
        ValueError: If state label is not recognized.
    """
    key = name.strip().lower()
    if key in _BELL_STATES:
        return _BELL_STATES[key].copy()
    raise ValueError(
        f"Unknown Bell state '{name}'. Supported states: ['phi+', 'phi-', 'psi+', 'psi-']."
    )


def validate_two_qubit_state(
    state: Any,
    atol: float = 1e-7,
) -> np.ndarray:
    """Validate that an input represents a normalized pure two-qubit state vector.

    Args:
        state: 4-element array-like, column vector (4, 1), or BellState instance.
        atol: Numerical tolerance for the normalization check.

    Returns:
        Validated 1D numpy array of shape (4,) and dtype np.complex128.

    Raises:
        TypeError: If state cannot be converted to a numeric complex array.
        ValueError: If shape is not (4,), values are non-finite, zero vector, or unnormalized.
    """
    if isinstance(state, BellState):
        state = state.vector

    try:
        arr = np.asarray(state, dtype=np.complex128)
    except (ValueError, TypeError) as exc:
        raise TypeError(f"State vector must be numeric/complex array-like: {exc}") from exc

    # Accept column/row vectors and squeeze to 1D
    if arr.ndim == 2 and (arr.shape == (4, 1) or arr.shape == (1, 4)):
        arr = arr.squeeze()

    if arr.ndim != 1 or arr.shape[0] != 4:
        raise ValueError(
            f"A two-qubit state vector must have shape (4,), but got shape {arr.shape}."
        )

    if not np.all(np.isfinite(arr)):
        raise ValueError("State vector components must be finite (no NaN or Inf).")

    norm_sq = float(np.real(np.vdot(arr, arr)))
    if norm_sq <= 0.0:
        raise ValueError("State vector cannot be the zero vector.")

    if not np.isclose(norm_sq, 1.0, atol=atol):
        raise ValueError(
            f"Two-qubit state vector is not normalized: sum |c_i|^2 = {norm_sq:.8f}, expected 1.0 (atol={atol})."
        )

    return arr


def create_bell_circuit(
    circuit_name: str = "bell_phi_plus",
    measure: bool = False,
    bell_type: str = "phi_plus",
) -> QuantumCircuit:
    """Construct a two-qubit Qiskit QuantumCircuit that prepares a Bell state.

    Standard preparation from |00>:
        - phi_plus:  H(q0) -> CX(q0, q1)
        - phi_minus: H(q0) -> CX(q0, q1) -> Z(q0)
        - psi_plus:  H(q0) -> CX(q0, q1) -> X(q1)
        - psi_minus: H(q0) -> CX(q0, q1) -> Z(q0) -> X(q1)

    Args:
        circuit_name: Label for the QuantumCircuit.
        measure: If True, adds a 2-bit ClassicalRegister and measures q0 -> c0, q1 -> c1.
        bell_type: Bell state type ('phi_plus', 'phi_minus', 'psi_plus', 'psi_minus').

    Returns:
        Qiskit QuantumCircuit with 2 qubits (and 2 classical bits if measure=True).

    Raises:
        ValueError: If bell_type is unrecognized.
    """
    key = bell_type.strip().lower()
    if key not in ("phi_plus", "phi+", "phi_minus", "phi-", "psi_plus", "psi+", "psi_minus", "psi-"):
        raise ValueError(
            f"Unknown bell_type '{bell_type}'. Supported: ['phi_plus', 'phi_minus', 'psi_plus', 'psi_minus']."
        )

    if measure:
        qc = QuantumCircuit(2, 2, name=circuit_name)
    else:
        qc = QuantumCircuit(2, name=circuit_name)

    # Base entangling circuit creates |Phi+>: (|00> + |11>) / sqrt(2)
    qc.h(0)
    qc.cx(0, 1)

    if key in ("phi_minus", "phi-"):
        qc.z(0)
    elif key in ("psi_plus", "psi+"):
        qc.x(1)
    elif key in ("psi_minus", "psi-"):
        qc.z(0)
        qc.x(1)

    if measure:
        qc.measure(0, 0)
        qc.measure(1, 1)

    return qc


def bell_computational_probabilities(
    state: Any = BELL_PHI_PLUS,
    atol: float = 1e-7,
) -> dict[str, float]:
    """Calculate exact theoretical Born-rule probabilities for computational basis outcomes.

    P(ij) = |c_ij|^2 for ij in {'00', '01', '10', '11'}.

    Args:
        state: Two-qubit state vector or BellState instance.
        atol: Numerical tolerance for probability normalization check.

    Returns:
        Dictionary mapping basis strings to theoretical probabilities:
            {'00': 0.5, '01': 0.0, '10': 0.0, '11': 0.5} for |Phi+>.
    """
    vec = validate_two_qubit_state(state, atol=atol)

    probs: dict[str, float] = {}
    for idx, label in enumerate(TWO_QUBIT_BASIS_LABELS):
        amp = vec[idx]
        p = float(np.real(amp * np.conj(amp)))
        probs[label] = max(0.0, min(1.0, p))

    total = sum(probs.values())
    if not np.isclose(total, 1.0, atol=atol):
        raise ValueError(f"Probabilities do not sum to 1.0: {total} (atol={atol}).")

    return probs


def calculate_bell_correlations(
    probabilities_or_counts_or_state: Any,
) -> dict[str, float]:
    """Evaluate two-qubit correlation properties from measurement counts or quantum states.

    If given a dictionary of computational-basis counts or probabilities, calculates:
        - P_same: Probability that both qubits agree: P(q0 == q1) = P(00) + P(11)
        - P_diff: Probability that qubits disagree: P(q0 != q1) = P(01) + P(10)
        - correlation: P_same - P_diff (corresponds to <Z (x) Z>)
        - ZZ: Equivalent to correlation

    If given a two-qubit quantum state (4-element vector, BellState, or standard name), calculates:
        - XX: <psi| (X (x) X) |psi>
        - YY: <psi| (Y (x) Y) |psi>
        - ZZ: <psi| (Z (x) Z) |psi>

    Args:
        probabilities_or_counts_or_state: Dictionary of counts, state vector, BellState, or name.

    Returns:
        Dictionary mapping correlation keys to calculated float values.

    Raises:
        ValueError / TypeError: If input is invalid, non-finite, or malformed.
    """
    if isinstance(probabilities_or_counts_or_state, Mapping):
        if len(probabilities_or_counts_or_state) == 0:
            raise ValueError("Must provide a non-empty dictionary of counts or probabilities.")

        valid_keys = set(TWO_QUBIT_BASIS_LABELS)
        for k in probabilities_or_counts_or_state.keys():
            if str(k) not in valid_keys:
                raise ValueError(f"Unrecognized two-qubit outcome labels: '{k}'.")

        for k, v in probabilities_or_counts_or_state.items():
            if not np.isfinite(v):
                raise ValueError(f"Value for key '{k}' must be finite, got {v}.")
            if v < 0:
                raise ValueError(f"Counts or probabilities cannot be negative, got {v} for key '{k}'.")

        total_val = float(sum(probabilities_or_counts_or_state.values()))
        if total_val <= 0:
            raise ValueError("Sum of counts or probabilities must be strictly positive.")

        p_00 = float(probabilities_or_counts_or_state.get("00", 0.0)) / total_val
        p_11 = float(probabilities_or_counts_or_state.get("11", 0.0)) / total_val
        p_01 = float(probabilities_or_counts_or_state.get("01", 0.0)) / total_val
        p_10 = float(probabilities_or_counts_or_state.get("10", 0.0)) / total_val

        p_same = p_00 + p_11
        p_diff = p_01 + p_10
        corr = p_same - p_diff

        return {
            "P_same": float(p_same),
            "P_diff": float(p_diff),
            "correlation": float(corr),
            "ZZ": float(corr),
        }

    from .correlations import calculate_theoretical_bell_correlations

    return calculate_theoretical_bell_correlations(probabilities_or_counts_or_state)


def calculate_two_qubit_expectation_value(
    state: Any,
    operator_0: Any,
    operator_1: Any,
    atol: float = 1e-7,
) -> float:
    """Calculate the expectation value of a tensor-product observable <A (x) B> on a two-qubit state.

    <A (x) B> = <psi| (A (x) B) |psi>

    Args:
        state: Two-qubit state vector or BellState.
        operator_0: 2x2 matrix or string label for qubit 0 (e.g. PAULI_Z, 'Z', 'X', 'Y', 'I').
        operator_1: 2x2 matrix or string label for qubit 1.
        atol: Tolerance for verifying that the expectation value is real.

    Returns:
        Real expectation value.

    Raises:
        ValueError: If state or operators are invalid, or if the expectation value has an imaginary component.
    """
    vec = validate_two_qubit_state(state, atol=atol)

    if isinstance(operator_0, str):
        op0 = get_pauli_operator(operator_0)
    else:
        op0 = validate_operator(operator_0)

    if isinstance(operator_1, str):
        op1 = get_pauli_operator(operator_1)
    else:
        op1 = validate_operator(operator_1)

    from .pauli import is_hermitian

    if not is_hermitian(op0, atol=atol):
        raise ValueError(
            f"operator_0 must be a Hermitian observable (O† = O); expectation value must be real."
        )
    if not is_hermitian(op1, atol=atol):
        raise ValueError(
            f"operator_1 must be a Hermitian observable (O† = O); expectation value must be real."
        )

    # Qubit 0 is the first factor, qubit 1 is the second factor: A (x) B
    op2 = np.kron(op0, op1)
    # np.vdot conjugates the first argument: vec^\dagger (op2 @ vec)
    expectation = np.vdot(vec, op2 @ vec)

    if not np.isclose(np.imag(expectation), 0.0, atol=atol):
        raise ValueError(
            f"Expectation value of observable must be real, got imaginary component {np.imag(expectation):.8e}."
        )

    return float(np.real(expectation))


def check_entanglement(
    state: Any = BELL_PHI_PLUS,
    atol: float = 1e-7,
) -> tuple[bool, int, np.ndarray]:
    """Mathematically verify whether a pure two-qubit state is entangled.

    Uses Schmidt decomposition / coefficient matrix rank analysis:
        For |psi> = sum_{i,j} c_{ij} |ij>, form the 2x2 coefficient matrix:
            C = [[c_00, c_01],
                 [c_10, c_11]]
        A pure state is separable (product state) if and only if rank(C) == 1.
        If rank(C) > 1 (specifically rank 2 for two qubits), the state is entangled.

    Args:
        state: Two-qubit state vector.
        atol: Numerical threshold for singular values.

    Returns:
        Tuple of (is_entangled: bool, schmidt_rank: int, singular_values: np.ndarray).
    """
    vec = validate_two_qubit_state(state, atol=atol)

    # Reshape into 2x2 coefficient matrix: C[i, j] = c_{ij}
    c_matrix = vec.reshape((2, 2))

    # Compute singular values (Schmidt coefficients)
    s_vals = np.linalg.svdvals(c_matrix)

    # Schmidt rank is the number of non-zero singular values
    schmidt_rank = int(np.sum(s_vals > atol))
    is_entangled = schmidt_rank > 1

    return is_entangled, schmidt_rank, s_vals


def partial_trace_qubit(
    state: Any = BELL_PHI_PLUS,
    trace_out_qubit: int = 1,
    atol: float = 1e-7,
) -> np.ndarray:
    """Compute the reduced density matrix of a pure two-qubit state by tracing out one qubit.

    For |psi><psi|:
        - If trace_out_qubit == 1: rho_A = Tr_B(|psi><psi|)
        - If trace_out_qubit == 0: rho_B = Tr_A(|psi><psi|)

    For the maximally entangled Bell state |Phi+>, both reduced states equal I_2 / 2.

    Args:
        state: Two-qubit state vector.
        trace_out_qubit: Index of the qubit to trace out (0 or 1).
        atol: Tolerance for state validation.

    Returns:
        2x2 numpy array representing the reduced density matrix.

    Raises:
        ValueError: If trace_out_qubit is not 0 or 1, or is a boolean.
    """
    if isinstance(trace_out_qubit, bool) or trace_out_qubit not in (0, 1):
        raise ValueError(f"trace_out_qubit must be 0 or 1, got {trace_out_qubit!r}.")

    vec = validate_two_qubit_state(state, atol=atol)
    # Form full 4x4 density matrix: rho = |psi><psi|
    rho_full = np.outer(vec, vec.conj())

    # Basis indices: 0 -> |00>, 1 -> |01>, 2 -> |10>, 3 -> |11>
    # index = 2 * q0 + q1
    rho_reduced = np.zeros((2, 2), dtype=np.complex128)

    if trace_out_qubit == 1:
        # Trace out qubit 1 (retain qubit 0)
        # (rho_A)_{i, j} = sum_k rho_{ik, jk}
        for i in (0, 1):
            for j in (0, 1):
                rho_reduced[i, j] = rho_full[2 * i + 0, 2 * j + 0] + rho_full[2 * i + 1, 2 * j + 1]
    else:
        # Trace out qubit 0 (retain qubit 1)
        # (rho_B)_{i, j} = sum_k rho_{ki, kj}
        for i in (0, 1):
            for j in (0, 1):
                rho_reduced[i, j] = rho_full[2 * 0 + i, 2 * 0 + j] + rho_full[2 * 1 + i, 2 * 1 + j]

    return rho_reduced


def measure_bell_state(
    shots: int = 1024,
    seed_simulator: int | None = None,
    simulator: AerSimulator | None = None,
    circuit: QuantumCircuit | None = None,
) -> tuple[dict[str, int], dict[str, float]]:
    """Simulate a two-qubit Bell circuit using Qiskit Aer in the computational basis.

    Qubit and bit ordering:
        Qubit 0 is measured into classical bit 0 (c0).
        Qubit 1 is measured into classical bit 1 (c1).
        Output dictionary keys are formatted in standard order 'q0q1' ('00', '01', '10', '11').
        When Qiskit returns little-endian bitstrings 'c1 c0', bitstring[1] is c0 (q0)
        and bitstring[0] is c1 (q1). We construct the canonical key as f"{c0}{c1}".

    Args:
        shots: Number of simulation repetitions (strictly positive integer).
        seed_simulator: Optional random seed for reproducible Aer simulation.
        simulator: Optional AerSimulator instance.
        circuit: Optional 2-qubit QuantumCircuit. Defaults to create_bell_circuit(measure=True).

    Returns:
        Tuple of (counts_dict, empirical_probabilities_dict) containing keys '00', '01', '10', '11'.

    Raises:
        TypeError: If shots, seed, or circuit have invalid types.
        ValueError: If shots <= 0, seed < 0, or circuit has fewer than 2 qubits.
    """
    if not isinstance(shots, int) or isinstance(shots, bool):
        raise TypeError(f"Shots must be an integer, got {type(shots).__name__}.")
    if shots <= 0:
        raise ValueError(f"Shots must be a strictly positive integer, got {shots}.")

    if seed_simulator is not None:
        if not isinstance(seed_simulator, int) or isinstance(seed_simulator, bool):
            raise TypeError(f"Seed must be an integer, got {type(seed_simulator).__name__}.")
        if seed_simulator < 0:
            raise ValueError(f"Seed must be a non-negative integer, got {seed_simulator}.")

    if circuit is None:
        qc = create_bell_circuit(circuit_name="bell_meas_circuit", measure=True)
    else:
        if not isinstance(circuit, QuantumCircuit):
            raise TypeError(f"Expected a QuantumCircuit, got {type(circuit).__name__}.")
        if circuit.num_qubits < 2:
            raise ValueError(f"Circuit must have at least 2 qubits, got {circuit.num_qubits}.")
        # Ensure measurements are present
        qc = circuit.copy()
        meas_ops = [inst for inst in qc.data if inst.operation.name == "measure"]
        if len(meas_ops) < 2:
            if qc.num_clbits < 2:
                cr = ClassicalRegister(2, "c")
                qc.add_register(cr)
            qc.measure(0, 0)
            qc.measure(1, 1)

    sim = simulator if simulator is not None else AerSimulator()

    run_kwargs: dict[str, Any] = {"shots": shots}
    if seed_simulator is not None:
        run_kwargs["seed_simulator"] = seed_simulator

    job = sim.run(qc, **run_kwargs)
    result = job.result()
    raw_counts = result.get_counts()

    # Initialize all 4 basis combinations
    counts: dict[str, int] = {k: 0 for k in TWO_QUBIT_BASIS_LABELS}

    # Qiskit get_counts returns bitstrings in little-endian order 'c1 c0'.
    # When q0 -> c0 and q1 -> c1, c0 = bitstring[1], c1 = bitstring[0].
    # We map to canonical 'q0q1' = f"{c0}{c1}".
    for bitstring, count in raw_counts.items():
        clean = bitstring.replace(" ", "")
        if len(clean) == 2:
            c1, c0 = clean[0], clean[1]
            q0_q1_key = f"{c0}{c1}"
            if q0_q1_key in counts:
                counts[q0_q1_key] += count
            else:
                counts[q0_q1_key] = count
        else:
            counts[clean] = count

    probs = calculate_empirical_probabilities(counts, total_shots=shots)
    return counts, probs


@dataclass(frozen=True)
class BellState:
    """Immutable representation of a two-qubit Bell state."""

    vector: np.ndarray = field(default_factory=create_bell_phi_plus)

    def __post_init__(self) -> None:
        validated = validate_two_qubit_state(self.vector)
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
    def probabilities(self) -> dict[str, float]:
        return bell_computational_probabilities(self.vector)

    @property
    def is_entangled(self) -> bool:
        entangled, _, _ = check_entanglement(self.vector)
        return entangled

    @property
    def correlations(self) -> dict[str, float]:
        return calculate_bell_correlations(self.probabilities)

    @property
    def bell_correlations(self) -> dict[str, float]:
        from .correlations import calculate_theoretical_bell_correlations

        return calculate_theoretical_bell_correlations(self.vector)

    def to_circuit(self, circuit_name: str = "bell_circuit", measure: bool = False) -> QuantumCircuit:
        if np.allclose(self.vector, BELL_PHI_PLUS):
            return create_bell_circuit(circuit_name=circuit_name, measure=measure, bell_type="phi_plus")
        if np.allclose(self.vector, BELL_PHI_MINUS):
            return create_bell_circuit(circuit_name=circuit_name, measure=measure, bell_type="phi_minus")
        if np.allclose(self.vector, BELL_PSI_PLUS):
            return create_bell_circuit(circuit_name=circuit_name, measure=measure, bell_type="psi_plus")
        if np.allclose(self.vector, BELL_PSI_MINUS):
            return create_bell_circuit(circuit_name=circuit_name, measure=measure, bell_type="psi_minus")

        # General two-qubit state initialization
        qc = QuantumCircuit(2, 2 if measure else 0, name=circuit_name)
        # Convert from project big-endian (|00>, |01>, |10>, |11>) to Qiskit Statevector (index = q0 + 2*q1)
        vec_qiskit = np.array([self.vector[0], self.vector[2], self.vector[1], self.vector[3]], dtype=np.complex128)
        qc.initialize(Statevector(vec_qiskit), [0, 1])
        if measure:
            qc.measure(0, 0)
            qc.measure(1, 1)
        return qc

    def __repr__(self) -> str:
        if np.allclose(self.vector, BELL_PHI_PLUS):
            label = "|Phi+>"
        elif np.allclose(self.vector, BELL_PHI_MINUS):
            label = "|Phi->"
        elif np.allclose(self.vector, BELL_PSI_PLUS):
            label = "|Psi+>"
        elif np.allclose(self.vector, BELL_PSI_MINUS):
            label = "|Psi->"
        else:
            label = "TwoQubitState"

        return (
            f"BellState({label} = {self.vector[0]:.3f}|00> + "
            f"{self.vector[1]:.3f}|01> + {self.vector[2]:.3f}|10> + {self.vector[3]:.3f}|11>)"
        )


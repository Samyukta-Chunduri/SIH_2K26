"""Q-SHIELD — Quantum Teleportation Module (Milestone M6).

Implements the canonical three-qubit quantum teleportation protocol:
transfers an arbitrary single-qubit quantum state from Alice's input
qubit (q0) to Bob's target qubit (q2) using a shared entangled Bell pair
|Phi+> on (q1, q2), Bell-state measurement on (q0, q1), classical
communication of two measurement bits, and conditional Pauli corrections.

Mathematical Model:
    1. Initial 3-qubit state:
       |Psi_0> = |psi>_0 (x) |Phi+>_12
               = (alpha|0> + beta|1>) (x) (|00> + |11>)/sqrt(2)
               = (1/sqrt(2)) [alpha|000> + alpha|011> + beta|100> + beta|111>]

    2. Alice's Bell Measurement on (q0, q1):
       Apply CX(q0, q1) then H(q0):
       |Psi_mid> = (1/2) [
           |00> (alpha|0> + beta|1>)     +
           |01> (beta|0> + alpha|1>)     +
           |10> (alpha|0> - beta|1>)     +
           |11> (-beta|0> + alpha|1>)
       ]
       = (1/2) sum_{m0, m1 in {0,1}} |m0 m1>_01 (x) (X^m1 Z^m0 |psi>)_2

    3. Classical Communication & Measurement:
       Alice measures q0 -> m0 in {0, 1}
       Alice measures q1 -> m1 in {0, 1}
       Each branch occurs with probability 1/4 = 0.25 for any normalized state.

    4. Bob's Conditional Pauli Corrections:
       Before correction, Bob's qubit is in state:
           |phi_Bob(m0, m1)> = X^m1 Z^m0 |psi>
       To recover |psi>, Bob applies the unitary correction:
           U_corr(m0, m1) = Z^m0 X^m1
       Specifically:
           m0=0, m1=0 -> I
           m0=0, m1=1 -> X
           m0=1, m1=0 -> Z
           m0=1, m1=1 -> Z @ X  (undoes X Z |psi> with zero phase shift)
       After correction:
           |psi_out> = U_corr(m0, m1) |phi_Bob(m0, m1)> = |psi>

    5. Teleportation Fidelity:
       F = |<psi_in | psi_out>|^2
       For ideal noiseless teleportation, F = 1.0 within numerical precision.

Qubit & Classical Bit Conventions:
    - q0: Alice's input qubit carrying |psi>
    - q1: Alice's Bell-pair qubit
    - q2: Bob's Bell-pair qubit (recovers |psi>)
    - c_alice[0]: holds measurement outcome of q0 (m0, controls Z)
    - c_alice[1]: holds measurement outcome of q1 (m1, controls X)
    - Qiskit little-endian bitstring: 'c1 c0' where character 1 (right) is c0, character 0 (left) is c1.

Scientific Boundaries:
    - Teleportation is NOT cloning (no-cloning theorem holds; Alice's state is destroyed).
    - Teleportation requires shared entanglement AND classical communication (no FTL communication).
    - Teleportation fidelity is a protocol correctness metric, NOT a security score.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any
import numpy as np
from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
from qiskit.circuit import Qubit
from qiskit_aer import AerSimulator

from .bell import BELL_PHI_PLUS
from .pauli import (
    PAULI_I,
    PAULI_X,
    PAULI_Y,
    PAULI_Z,
    validate_operator,
)
from .states import (
    QubitState,
    get_standard_state,
    validate_state_vector,
)


# Canonical 2x2 Pauli correction operators for (m0, m1)
# m0 is from q0 (controls Z), m1 is from q1 (controls X)
# U_corr = Z^m0 @ X^m1
TELEPORTATION_CORRECTIONS: dict[tuple[int, int], tuple[str, np.ndarray]] = {
    (0, 0): ("I", PAULI_I.copy()),
    (0, 1): ("X", PAULI_X.copy()),
    (1, 0): ("Z", PAULI_Z.copy()),
    (1, 1): ("ZX", (PAULI_Z @ PAULI_X).copy()),
}


@dataclass(frozen=True)
class TeleportationResult:
    """Immutable result of a single quantum teleportation execution.

    Attributes:
        input_state: Alice's original input state vector (2,).
        alice_bits: Measurement bits (m0, m1) from Alice's Bell measurement.
                    m0 is the measurement of q0 (controls Z correction).
                    m1 is the measurement of q1 (controls X correction).
        correction_name: Name of the Pauli correction applied by Bob ('I', 'X', 'Z', 'ZX').
        output_state: Bob's recovered single-qubit state vector (2,).
        fidelity: State overlap fidelity F = |<input|output>|^2 in [0.0, 1.0].
        raw_counts: Optional measurement counts if run on a simulator.
    """

    input_state: np.ndarray
    alice_bits: tuple[int, int]
    correction_name: str
    output_state: np.ndarray
    fidelity: float
    raw_counts: dict[str, int] | None = None

    def __post_init__(self) -> None:
        """Enforce validation on dataclass instantiation."""
        if self.input_state.shape != (2,):
            raise ValueError(f"input_state must have shape (2,), got {self.input_state.shape}.")
        if self.output_state.shape != (2,):
            raise ValueError(f"output_state must have shape (2,), got {self.output_state.shape}.")
        if len(self.alice_bits) != 2 or self.alice_bits[0] not in (0, 1) or self.alice_bits[1] not in (0, 1):
            raise ValueError(f"alice_bits must be a tuple of two binary bits (0 or 1), got {self.alice_bits}.")
        if not (0.0 <= self.fidelity <= 1.0 + 1e-7):
            raise ValueError(f"Fidelity must be in [0.0, 1.0], got {self.fidelity}.")


def calculate_teleportation_fidelity(
    state_a: Any,
    state_b: Any,
    atol: float = 1e-10,
) -> float:
    """Calculate the quantum state fidelity between two pure single-qubit states.

    Mathematical Model:
        F(psi_a, psi_b) = |<psi_a | psi_b>|^2
                        = |vdot(psi_a, psi_b)|^2

    Properties:
        - F in [0.0, 1.0]
        - F = 1.0 if and only if psi_b = e^(i theta) psi_a (identical up to global phase)
        - F = 0.0 if and only if <psi_a | psi_b> = 0 (orthogonal states)
        - Phase-insensitive: invariant under global phase shifts

    Args:
        state_a: First single-qubit state (name, QubitState, or array-like).
        state_b: Second single-qubit state (name, QubitState, or array-like).
        atol: Numerical tolerance for state normalization.

    Returns:
        Fidelity float in [0.0, 1.0].

    Raises:
        ValueError / TypeError: If either state is invalid, non-normalized, or malformed.
    """
    if isinstance(state_a, str):
        vec_a = get_standard_state(state_a)
    elif isinstance(state_a, QubitState):
        vec_a = state_a.vector
    else:
        vec_a = validate_state_vector(state_a, atol=atol)

    if isinstance(state_b, str):
        vec_b = get_standard_state(state_b)
    elif isinstance(state_b, QubitState):
        vec_b = state_b.vector
    else:
        vec_b = validate_state_vector(state_b, atol=atol)

    # Strictly perform complex-conjugating inner product <a|b> = sum a_i^* b_i
    inner_prod = complex(np.vdot(vec_a, vec_b))
    fid = float(abs(inner_prod) ** 2)

    # Clamp minor floating-point roundoff
    return float(np.clip(fid, 0.0, 1.0))


def get_teleportation_correction(m0: int, m1: int) -> tuple[str, np.ndarray]:
    """Retrieve Bob's conditional Pauli correction operator given Alice's measurement bits.

    Mathematical Model:
        U_corr(m0, m1) = Z^m0 @ X^m1
        (0, 0) -> I
        (0, 1) -> X
        (1, 0) -> Z
        (1, 1) -> Z @ X

    Args:
        m0: Measurement outcome of q0 (Alice's input qubit), controlling Z.
        m1: Measurement outcome of q1 (Alice's Bell-pair qubit), controlling X.

    Returns:
        Tuple of (correction_name, 2x2 unitary matrix).

    Raises:
        TypeError: If m0 or m1 are not integer types.
        ValueError: If m0 or m1 are not in {0, 1}.
    """
    if not isinstance(m0, (int, np.integer)) or isinstance(m0, bool):
        raise TypeError(f"m0 must be an integer, got {type(m0).__name__}.")
    if not isinstance(m1, (int, np.integer)) or isinstance(m1, bool):
        raise TypeError(f"m1 must be an integer, got {type(m1).__name__}.")

    m0_int = int(m0)
    m1_int = int(m1)

    if m0_int not in (0, 1) or m1_int not in (0, 1):
        raise ValueError(f"Measurement bits must be in {{0, 1}}, got m0={m0_int}, m1={m1_int}.")

    name, mat = TELEPORTATION_CORRECTIONS[(m0_int, m1_int)]
    return name, mat.copy()


def apply_teleportation_correction(state: Any, m0: int, m1: int) -> np.ndarray:
    """Apply Bob's conditional Pauli correction operator to a single-qubit state.

    psi_corrected = (Z^m0 @ X^m1) @ psi

    Args:
        state: Bob's uncorrected single-qubit state vector.
        m0: Measurement outcome of q0.
        m1: Measurement outcome of q1.

    Returns:
        Corrected 2-element complex state vector.
    """
    vec = validate_state_vector(state)
    _, mat = get_teleportation_correction(m0, m1)
    corrected = mat @ vec
    return corrected


def decode_teleportation_bitstring(bitstring: str) -> tuple[int, int, int | None]:
    """Decode a Qiskit measurement count bitstring into canonical (m0, m1, bob_bit).

    Qiskit Classical-Bit Ordering:
        When multiple classical registers are measured, Qiskit prints them in reverse
        order separated by space: '<cr_bob> <cr_alice>' or '<cr_alice>'.
        Within a classical register 'c_alice' with c_alice[0] = q0 and c_alice[1] = q1,
        Qiskit outputs 'c_alice[1]c_alice[0]'.
        Therefore:
        - The rightmost character of the Alice field is c_alice[0] = m0 (q0 measurement).
        - The leftmost character of the Alice field is c_alice[1] = m1 (q1 measurement).

    Args:
        bitstring: Raw bitstring returned by Qiskit (e.g. '0 11', '10', '1 01').

    Returns:
        Tuple (m0, m1, bob_bit) where bob_bit is None if Bob was not measured.

    Raises:
        TypeError: If bitstring is not a string.
        ValueError: If bitstring is malformed or has invalid length.
    """
    if not isinstance(bitstring, str):
        raise TypeError(f"bitstring must be a str, got {type(bitstring).__name__}.")

    clean = bitstring.strip()
    parts = clean.split()

    if len(parts) == 2:
        bob_str, alice_str = parts[0], parts[1]
        if len(bob_str) != 1 or len(alice_str) != 2:
            raise ValueError(f"Unexpected bitstring structure for teleportation: '{bitstring}'.")
        bob_bit: int | None = int(bob_str)
    elif len(parts) == 1:
        if len(parts[0]) == 2:
            alice_str = parts[0]
            bob_bit = None
        elif len(parts[0]) == 3:
            # Packed without space: bob is parts[0][0], alice is parts[0][1:]
            bob_bit = int(parts[0][0])
            alice_str = parts[0][1:]
        else:
            raise ValueError(f"Bitstring must have 2 or 3 bits, got '{bitstring}'.")
    else:
        raise ValueError(f"Cannot parse teleportation bitstring: '{bitstring}'.")

    # In little-endian c1 c0:
    # alice_str[0] = c1 (m1, q1 measurement)
    # alice_str[1] = c0 (m0, q0 measurement)
    m1 = int(alice_str[0])
    m0 = int(alice_str[1])

    if m0 not in (0, 1) or m1 not in (0, 1):
        raise ValueError(f"Invalid Alice measurement bits: m0={m0}, m1={m1}.")
    if bob_bit is not None and bob_bit not in (0, 1):
        raise ValueError(f"Invalid Bob measurement bit: {bob_bit}.")

    return m0, m1, bob_bit


def create_teleportation_circuit(
    state: Any,
    measure_bob: bool = False,
    bob_basis: str = "Z",
    circuit_name: str = "teleportation_circuit",
) -> QuantumCircuit:
    """Construct the canonical 3-qubit quantum teleportation circuit.

    Circuit Architecture:
        q0: Alice's input qubit initialized to |psi>
        q1: Alice's Bell-pair qubit
        q2: Bob's Bell-pair qubit (recovers |psi>)

        c_alice[0]: Classical bit storing measurement of q0 (m0)
        c_alice[1]: Classical bit storing measurement of q1 (m1)
        c_bob[0]:   Optional classical bit storing measurement of q2

    Protocol Steps:
        1. Initialize q0 to |psi>.
        2. Entangle Bell pair on (q1, q2): H(q1), CX(q1, q2).
        3. Bell measurement interaction on (q0, q1): CX(q0, q1), H(q0).
        4. Alice measures q0 -> c_alice[0], q1 -> c_alice[1].
        5. Conditional Pauli corrections on q2:
           - If c_alice[1] == 1 (q1 was 1): apply X(q2)
           - If c_alice[0] == 1 (q0 was 1): apply Z(q2)
        6. If measure_bob: rotate q2 to bob_basis ('Z', 'X', 'Y') and measure q2 -> c_bob[0].

    Args:
        state: Input state (name, QubitState, or (2,) complex array).
        measure_bob: Whether to append a measurement on Bob's qubit.
        bob_basis: Measurement basis for Bob ('Z', 'X', 'Y').
        circuit_name: Name of the QuantumCircuit.

    Returns:
        Qiskit QuantumCircuit implementing the teleportation protocol.

    Raises:
        ValueError / TypeError: If state is invalid or basis is unsupported.
    """
    if isinstance(state, str):
        vec = get_standard_state(state)
        state_str = state.strip().lower()
    elif isinstance(state, QubitState):
        vec = state.vector
        state_str = None
    else:
        vec = validate_state_vector(state)
        state_str = None

    basis_key = bob_basis.strip().lower()
    if basis_key not in ("z", "computational", "x", "hadamard", "y", "circular"):
        raise ValueError(
            f"Unsupported Bob measurement basis '{bob_basis}'. Choose from ['Z', 'X', 'Y']."
        )

    qr = QuantumRegister(3, name="q")
    cr_alice = ClassicalRegister(2, name="c_alice")
    qc = QuantumCircuit(qr, cr_alice, name=circuit_name)

    # 1. State preparation on q0
    if state_str == "0":
        pass  # already |0>
    elif state_str == "1":
        qc.x(0)
    elif state_str in ("+", "hadamard"):
        qc.h(0)
    elif state_str == "-":
        qc.x(0)
        qc.h(0)
    elif state_str == "+i":
        qc.h(0)
        qc.s(0)
    elif state_str == "-i":
        qc.h(0)
        qc.sdg(0)
    else:
        qc.initialize(list(vec), [0])

    # 2. Prepare Bell pair |Phi+> on (q1, q2)
    qc.h(1)
    qc.cx(1, 2)

    # 3. Alice's Bell measurement interaction on (q0, q1)
    qc.cx(0, 1)
    qc.h(0)

    # 4. Measure Alice's qubits
    # cr_alice[0] = measurement of q0 (m0)
    # cr_alice[1] = measurement of q1 (m1)
    qc.measure(0, cr_alice[0])
    qc.measure(1, cr_alice[1])

    # 5. Conditional Pauli corrections on Bob's qubit q2
    # If c1 == 1: apply X(q2)
    # If c0 == 1: apply Z(q2)
    with qc.if_test((cr_alice[1], 1)):
        qc.x(2)
    with qc.if_test((cr_alice[0], 1)):
        qc.z(2)

    # 6. Optional Bob measurement
    if measure_bob:
        cr_bob = ClassicalRegister(1, name="c_bob")
        qc.add_register(cr_bob)

        if basis_key in ("x", "hadamard"):
            qc.h(2)
        elif basis_key in ("y", "circular"):
            qc.sdg(2)
            qc.h(2)

        qc.measure(2, cr_bob[0])

    return qc


def simulate_teleportation_mathematical(
    state: Any,
    branch: tuple[int, int] | None = None,
) -> TeleportationResult:
    """Mathematically simulate the 3-qubit quantum teleportation protocol.

    Derives Bob's pre-correction state, applies the conditional Pauli correction,
    and computes the exact theoretical fidelity without finite-shot stochasticity.

    Full 3-Qubit Algebra:
        |Psi_0> = |psi>_0 (x) |Phi+>_12
        |Psi_mid> = (H_0 (x) I_12) @ (CX_01 (x) I_2) @ |Psi_0>
        For branch (m0, m1):
            Projector P_m0m1 = |m0><m0| (x) |m1><m1| (x) I_2
            |phi_Bob(m0, m1)> = normalized(P_m0m1 @ |Psi_mid>)
            |psi_out> = (Z^m0 @ X^m1) @ |phi_Bob>
            F = |<psi | psi_out>|^2 = 1.0

    Args:
        state: Input single-qubit state.
        branch: Optional specific Alice measurement branch (m0, m1).
                If None, branch (0, 0) is evaluated deterministically.

    Returns:
        TeleportationResult containing exact input, output, correction, and fidelity.

    Raises:
        ValueError: If state or branch is invalid.
    """
    if isinstance(state, str):
        vec = get_standard_state(state)
    elif isinstance(state, QubitState):
        vec = state.vector
    else:
        vec = validate_state_vector(state)

    if branch is not None:
        if not isinstance(branch, (tuple, list)) or len(branch) != 2:
            raise TypeError(f"branch must be a tuple or list of two binary bits, got {type(branch).__name__}.")
        if branch[0] not in (0, 1) or branch[1] not in (0, 1):
            raise ValueError(f"branch bits must be in {{0, 1}}, got {branch}.")
        m0, m1 = int(branch[0]), int(branch[1])
    else:
        m0, m1 = 0, 0

    # 1. 3-qubit initial state: |psi> (x) |Phi+>
    psi_3q = np.kron(vec, BELL_PHI_PLUS)

    # 2. Gate operators on 3 qubits
    eye2 = PAULI_I
    # CX(0, 1) on 3 qubits: |0><0| (x) I (x) I + |1><1| (x) X (x) I
    p0 = np.array([[1.0, 0.0], [0.0, 0.0]], dtype=np.complex128)
    p1 = np.array([[0.0, 0.0], [0.0, 1.0]], dtype=np.complex128)
    cx_01 = np.kron(p0, np.kron(eye2, eye2)) + np.kron(p1, np.kron(PAULI_X, eye2))

    # H(0) on 3 qubits: H (x) I (x) I
    h_gate = (1.0 / np.sqrt(2.0)) * np.array([[1.0, 1.0], [1.0, -1.0]], dtype=np.complex128)
    h_0 = np.kron(h_gate, np.kron(eye2, eye2))

    # Mid-circuit 3-qubit state
    psi_mid = h_0 @ (cx_01 @ psi_3q)

    # 3. Project onto branch (m0, m1)
    proj_m0 = np.outer(eye2[:, m0], eye2[:, m0].conj())
    proj_m1 = np.outer(eye2[:, m1], eye2[:, m1].conj())
    proj_alice = np.kron(proj_m0, np.kron(proj_m1, eye2))

    proj_state = proj_alice @ psi_mid
    prob = float(np.real(np.vdot(proj_state, proj_state)))

    if prob <= 0.0:
        raise ValueError(f"Projection onto branch ({m0}, {m1}) has zero probability.")

    # Extract Bob's 2-element uncorrected vector
    idx_0 = 4 * m0 + 2 * m1 + 0
    idx_1 = 4 * m0 + 2 * m1 + 1
    bob_raw = np.array([proj_state[idx_0], proj_state[idx_1]], dtype=np.complex128)
    bob_uncorrected = bob_raw / np.linalg.norm(bob_raw)

    # 4. Apply Bob's conditional correction
    corr_name, corr_mat = get_teleportation_correction(m0, m1)
    bob_corrected = corr_mat @ bob_uncorrected

    fid = calculate_teleportation_fidelity(vec, bob_corrected)

    return TeleportationResult(
        input_state=vec.copy(),
        alice_bits=(m0, m1),
        correction_name=corr_name,
        output_state=bob_corrected.copy(),
        fidelity=fid,
    )


def simulate_teleportation_circuit(
    state: Any,
    shots: int = 1000,
    seed: int | None = None,
    simulator: Any = None,
    bob_basis: str = "Z",
) -> dict[str, Any]:
    """Execute the complete quantum teleportation circuit on Qiskit AerSimulator.

    Runs the circuit with conditional dynamic Pauli corrections and measurement
    of Bob's recovered qubit in the specified basis.

    Args:
        state: Input single-qubit quantum state.
        shots: Number of Monte Carlo measurement shots (strictly positive integer).
        seed: Optional deterministic random seed.
        simulator: Optional Qiskit simulator instance (defaults to AerSimulator).
        bob_basis: Basis in which Bob measures his recovered qubit ('Z', 'X', 'Y').

    Returns:
        Dictionary containing:
            - 'counts': raw bitstring counts from Aer
            - 'shots': total shots
            - 'branch_counts': counts partitioned by Alice's bits ('00', '01', '10', '11')
            - 'bob_outcomes_by_branch': mapping from Alice's branch to Bob's outcomes
    """
    if not isinstance(shots, (int, np.integer)) or isinstance(shots, bool):
        raise TypeError(f"shots must be an integer, got {type(shots).__name__}.")
    if shots <= 0:
        raise ValueError(f"shots must be strictly positive, got {shots}.")

    if seed is not None:
        if not isinstance(seed, (int, np.integer)) or isinstance(seed, bool) or seed < 0:
            raise ValueError(f"seed must be a non-negative integer, got {seed}.")

    sim = simulator if simulator is not None else AerSimulator()

    qc = create_teleportation_circuit(
        state=state,
        measure_bob=True,
        bob_basis=bob_basis,
    )

    if seed is not None:
        sim.set_options(seed_simulator=seed)

    result = sim.run(qc, shots=shots).result()
    raw_counts = result.get_counts()

    # Parse counts into Alice branches and Bob outcomes
    branch_counts: dict[str, int] = {"00": 0, "01": 0, "10": 0, "11": 0}
    bob_outcomes_by_branch: dict[str, dict[str, int]] = {
        "00": {"0": 0, "1": 0},
        "01": {"0": 0, "1": 0},
        "10": {"0": 0, "1": 0},
        "11": {"0": 0, "1": 0},
    }

    for bitstring, count in raw_counts.items():
        m0, m1, bob_bit = decode_teleportation_bitstring(bitstring)
        branch_key = f"{m0}{m1}"
        branch_counts[branch_key] += count
        if bob_bit is not None:
            bob_outcomes_by_branch[branch_key][str(bob_bit)] += count

    return {
        "counts": raw_counts,
        "shots": shots,
        "branch_counts": branch_counts,
        "bob_outcomes_by_branch": bob_outcomes_by_branch,
    }

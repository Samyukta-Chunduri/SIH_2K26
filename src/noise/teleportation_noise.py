"""Q-SHIELD — Teleportation Under Honest Noise (Milestone M8).

Integrates honest quantum noise channels (bit-flip, phase-flip, depolarizing)
with the M6 quantum teleportation protocol and M7 state verification tools.

Pipeline Architecture:
    Alice Input |psi_in>
             |
             v
    M6 Teleportation (Bell Pair + Bell Measurement + Pauli Correction)
             |
             v
    Bob Ideal Output |psi_out>
             |
             v
    M8 Honest Noise Channel (rho' = sum_i K_i rho K_i^dagger)
             |
             v
    Noisy Output Density Matrix rho_out
             |
             v
    Physical Characterization (Fidelity F(psi_in, rho_out), Measurement Distributions)

Scientific Boundaries:
    - NOISE != ATTACK: This module measures physical degradation under honest noise.
    - Strictly NO threat classification, NO attack detection, NO security thresholds.
    - Generates noisy observations; baseline estimation belongs to M9.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any
import numpy as np
from qiskit import ClassicalRegister
from qiskit_aer import AerSimulator

from src.quantum.states import validate_state_vector
from src.quantum.teleportation import (
    create_teleportation_circuit,
    simulate_teleportation_mathematical,
)
from .density_matrix import (
    calculate_mixed_state_fidelity,
    density_matrix_probabilities,
    validate_density_matrix,
)
from .models import (
    NoiseChannel,
    NoiseType,
    create_bit_flip_channel,
    create_depolarizing_channel,
    create_phase_flip_channel,
    create_qiskit_noise_model,
)


@dataclass(frozen=True)
class NoisyTeleportationResult:
    """Immutable result of a teleportation simulation subject to honest quantum noise.

    Attributes:
        input_state: Alice's intended pure input state vector (2,).
        ideal_output_state: Bob's recovered state before channel noise (2,).
        noise_channel: Applied NoiseChannel instance.
        noisy_density_matrix: Bob's post-noise 2x2 density matrix.
        fidelity: Overlap fidelity F(psi_in, rho_out) in [0.0, 1.0].
        probabilities_z: Born probabilities in the Z (computational) basis.
        probabilities_x: Born probabilities in the X (Hadamard) basis.
        probabilities_y: Born probabilities in the Y (circular) basis.
    """

    input_state: np.ndarray
    ideal_output_state: np.ndarray
    noise_channel: NoiseChannel
    noisy_density_matrix: np.ndarray
    fidelity: float
    probabilities_z: dict[str, float]
    probabilities_x: dict[str, float]
    probabilities_y: dict[str, float]

    def __post_init__(self) -> None:
        """Validate physical and structural invariants."""
        if self.input_state.shape != (2,):
            raise ValueError(f"input_state must have shape (2,), got {self.input_state.shape}.")
        if self.ideal_output_state.shape != (2,):
            raise ValueError(f"ideal_output_state must have shape (2,), got {self.ideal_output_state.shape}.")
        if self.noisy_density_matrix.shape != (2, 2):
            raise ValueError(f"noisy_density_matrix must have shape (2, 2), got {self.noisy_density_matrix.shape}.")
        if not (0.0 <= self.fidelity <= 1.0 + 1e-7):
            raise ValueError(f"fidelity must be in [0.0, 1.0], got {self.fidelity}.")


def simulate_noisy_teleportation_mathematical(
    input_state: Any,
    noise_channel: NoiseChannel,
    branch: tuple[int, int] = (0, 0),
    atol: float = 1e-7,
) -> NoisyTeleportationResult:
    """Simulate ideal teleportation followed by an honest quantum noise channel.

    Mathematical Model:
        1. Simulate M6 ideal teleportation for input |psi> on chosen branch (m0, m1).
        2. Apply CPTP noise channel: rho_noisy = sum_i K_i |psi_ideal><psi_ideal| K_i^dagger.
        3. Compute mixed-state fidelity: F = <psi_in | rho_noisy | psi_in>.
        4. Compute Born measurement probabilities in Z, X, Y bases: P(i) = Tr(P_i rho_noisy).

    Args:
        input_state: Alice's pure input state vector, standard label, or QubitState.
        noise_channel: Configured NoiseChannel instance.
        branch: Measurement outcome branch (m0, m1) from Alice's Bell measurement.
        atol: Numerical tolerance.

    Returns:
        NoisyTeleportationResult.

    Raises:
        TypeError: If noise_channel is not a NoiseChannel instance.
        ValueError: If state or noise channel is invalid.
    """
    if not isinstance(noise_channel, NoiseChannel):
        raise TypeError(
            f"Expected NoiseChannel instance, got {type(noise_channel).__name__}."
        )

    # 1. Simulate ideal teleportation
    ideal_res = simulate_teleportation_mathematical(input_state, branch=branch)

    # 2. Apply noise channel to Bob's recovered state
    noisy_rho = noise_channel.apply_to_state(ideal_res.output_state, atol=atol)

    # 3. Compute pure-mixed fidelity F(psi_in, rho_noisy)
    fidelity = calculate_mixed_state_fidelity(ideal_res.input_state, noisy_rho, atol=atol)

    # 4. Compute measurement distributions across standard bases
    probs_z = density_matrix_probabilities(noisy_rho, basis="Z", atol=atol)
    probs_x = density_matrix_probabilities(noisy_rho, basis="X", atol=atol)
    probs_y = density_matrix_probabilities(noisy_rho, basis="Y", atol=atol)

    return NoisyTeleportationResult(
        input_state=ideal_res.input_state.copy(),
        ideal_output_state=ideal_res.output_state.copy(),
        noise_channel=noise_channel,
        noisy_density_matrix=noisy_rho.copy(),
        fidelity=fidelity,
        probabilities_z=probs_z,
        probabilities_x=probs_x,
        probabilities_y=probs_y,
    )


def simulate_noisy_teleportation_circuit(
    input_state: Any,
    noise_channel: NoiseChannel,
    shots: int = 1000,
    seed: int | None = None,
    bob_basis: str = "Z",
    target_qubit: int = 2,
) -> dict[str, Any]:
    """Execute teleportation on Qiskit Aer simulator with honest channel noise on Bob's qubit.

    Abstraction Model:
        Models in-circuit quantum transmission channel noise on Bob's qubit:
        The 3-qubit teleportation circuit creates the Bell pair, performs Alice's Bell
        measurement, applies Bob's feedforward Pauli corrections, and applies channel noise
        to Bob's transmission qubit (q2) via an explicit channel identity operation prior to
        measurement in the selected basis.

    Args:
        input_state: Alice's pure input state.
        noise_channel: NoiseChannel instance.
        shots: Number of measurement shots (positive integer).
        seed: Random seed for simulation reproducibility.
        bob_basis: Measurement basis on Bob's recovered qubit ('Z', 'X', 'Y').
        target_qubit: Qubit index undergoing channel noise (defaults to 2, Bob's qubit).

    Returns:
        Dictionary containing counts and empirical probabilities.

    Raises:
        TypeError: If noise_channel is not a NoiseChannel instance.
        ValueError: If shots <= 0, target_qubit not in {0, 1, 2}, or basis is invalid.
    """
    if not isinstance(noise_channel, NoiseChannel):
        raise TypeError(
            f"Expected NoiseChannel instance, got {type(noise_channel).__name__}."
        )

    if not isinstance(shots, (int, np.integer)) or isinstance(shots, bool) or int(shots) <= 0:
        raise ValueError(f"shots must be a positive integer, got {shots}.")

    if not isinstance(target_qubit, (int, np.integer)) or isinstance(target_qubit, bool) or int(target_qubit) not in (0, 1, 2):
        raise ValueError(f"target_qubit must be 0, 1, or 2, got {target_qubit}.")

    basis_key = bob_basis.strip().lower()
    if basis_key not in ("z", "computational", "x", "hadamard", "y", "circular"):
        raise ValueError(
            f"Unsupported Bob measurement basis '{bob_basis}'. Choose from ['Z', 'X', 'Y']."
        )

    qc = create_teleportation_circuit(input_state, measure_bob=False)
    qc.id(target_qubit)

    cr_bob = ClassicalRegister(1, name="c_bob")
    qc.add_register(cr_bob)
    if basis_key in ("x", "hadamard"):
        qc.h(target_qubit)
    elif basis_key in ("y", "circular"):
        qc.sdg(target_qubit)
        qc.h(target_qubit)
    qc.measure(target_qubit, cr_bob[0])

    qiskit_noise = create_qiskit_noise_model(
        noise_channel, target_qubits=[target_qubit], instructions=["id"]
    )

    simulator = AerSimulator(noise_model=qiskit_noise, seed_simulator=seed)
    result = simulator.run(qc, shots=shots).result()
    raw_counts = result.get_counts(qc)

    # Parse counts for Bob's qubit
    # Classical register layout: c_bob has size 1, c_alice has size 2
    # In Qiskit, bitstrings are printed with space separation: 'c_bob c_alice' e.g. '0 11'
    bob_counts: dict[str, int] = {}
    for bitstring, count in raw_counts.items():
        parts = bitstring.strip().split()
        bob_bit = parts[0] if len(parts) > 1 else bitstring[0]
        bob_counts[bob_bit] = bob_counts.get(bob_bit, 0) + count

    total_shots = sum(bob_counts.values())
    bob_probs = {k: v / total_shots for k, v in bob_counts.items()}

    return {
        "raw_counts": raw_counts,
        "bob_counts": bob_counts,
        "bob_probabilities": bob_probs,
        "shots": shots,
        "basis": bob_basis.upper(),
        "noise_type": noise_channel.noise_type.value,
        "probability": noise_channel.probability,
    }


def run_noise_sweep(
    input_state: Any,
    noise_type: NoiseType | str,
    probabilities: Sequence[float],
    branch: tuple[int, int] = (0, 0),
    atol: float = 1e-7,
) -> list[NoisyTeleportationResult]:
    """Sweep noise strength parameter p over a sequence of values and record degradation.

    Args:
        input_state: Alice's pure input state.
        noise_type: Type of noise ('bit_flip', 'phase_flip', 'depolarizing').
        probabilities: Sequence of noise parameters p in [0.0, 1.0].
        branch: Measurement outcome branch (m0, m1).
        atol: Numerical tolerance.

    Returns:
        List of NoisyTeleportationResult instances for each probability value.

    Raises:
        ValueError: If noise_type is unrecognized or probabilities are invalid.
    """
    if isinstance(noise_type, str):
        try:
            ntype = NoiseType(noise_type.lower().strip())
        except ValueError as exc:
            raise ValueError(
                f"Unknown noise type '{noise_type}'. Supported: {[t.value for t in NoiseType]}."
            ) from exc
    else:
        ntype = noise_type

    results: list[NoisyTeleportationResult] = []
    for p in probabilities:
        if ntype == NoiseType.BIT_FLIP:
            channel = create_bit_flip_channel(p)
        elif ntype == NoiseType.PHASE_FLIP:
            channel = create_phase_flip_channel(p)
        elif ntype == NoiseType.DEPOLARIZING:
            channel = create_depolarizing_channel(p)
        else:
            raise ValueError(f"Unsupported noise type: {ntype}")

        res = simulate_noisy_teleportation_mathematical(input_state, channel, branch=branch, atol=atol)
        results.append(res)

    return results

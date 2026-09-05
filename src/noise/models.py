"""Q-SHIELD — Quantum Noise Models (Milestone M8).

Implements honest, unintentional physical quantum noise channels:
    - Bit-flip channel:      rho' = (1-p) rho + p X rho X
    - Phase-flip channel:    rho' = (1-p) rho + p Z rho Z
    - Depolarizing channel:  rho' = (1-p) rho + (p/3) (X rho X + Y rho Y + Z rho Z)

Mathematical Foundations:
    1. Kraus Representation:
       Every completely positive trace-preserving (CPTP) quantum channel E(rho)
       can be expressed using Kraus operators {K_i}:
           E(rho) = sum_i K_i rho K_i^dagger
       satisfying the completeness relation:
           sum_i K_i^dagger K_i = I.

    2. Bit-Flip Channel:
       Simulates unintentional bit inversions (spin-flips) with probability p in [0, 1]:
           K_0 = sqrt(1-p) I,   K_1 = sqrt(p) X.

    3. Phase-Flip Channel:
       Simulates loss of quantum phase coherence with probability p in [0, 1]:
           K_0 = sqrt(1-p) I,   K_1 = sqrt(p) Z.

    4. Depolarizing Channel (Standard Pauli Convention):
       Simulates isotropic decoherence where the qubit undergoes X, Y, or Z errors
       with equal probability p/3:
           K_0 = sqrt(1-p) I,   K_1 = sqrt(p/3) X,   K_2 = sqrt(p/3) Y,   K_3 = sqrt(p/3) Z.
       Note on Qiskit Aer parameter mapping:
           Qiskit Aer's depolarizing_error(p_aer, 1) defines:
               E(rho) = (1 - p_aer) rho + p_aer (I/2).
           Since I/2 = (1/4)(rho + X rho X + Y rho Y + Z rho Z), the parameter mapping
           to our standard Pauli channel is p_aer = (4/3) p.

Scientific Boundaries:
    - NOISE != ATTACK: These models represent legitimate physical and channel degradation.
    - No attack classification, detection, thresholding, or ML is implemented here.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
import math
from typing import Any
import numpy as np
from qiskit_aer.noise import NoiseModel, depolarizing_error, pauli_error

from src.quantum.pauli import PAULI_I, PAULI_X, PAULI_Y, PAULI_Z
from .density_matrix import (
    pure_state_to_density_matrix,
    validate_density_matrix,
)


class NoiseType(str, Enum):
    """Enumeration of supported honest quantum noise channel types."""

    BIT_FLIP = "bit_flip"
    PHASE_FLIP = "phase_flip"
    DEPOLARIZING = "depolarizing"


def validate_noise_probability(p: Any) -> float:
    """Validate that a noise probability parameter p is valid.

    Args:
        p: Probability value. Must be a numeric float or int in [0.0, 1.0].

    Returns:
        Validated probability as a float.

    Raises:
        TypeError: If p is not numeric or is a boolean.
        ValueError: If p is negative, greater than 1.0, NaN, or infinite.
    """
    if isinstance(p, bool) or not isinstance(p, (int, float)):
        raise TypeError(
            f"Noise probability must be a numeric float or int, got {type(p).__name__}."
        )

    prob = float(p)

    if not math.isfinite(prob):
        raise ValueError(f"Noise probability must be finite, got {prob}.")

    if prob < 0.0 or prob > 1.0:
        raise ValueError(
            f"Noise probability must be in [0.0, 1.0], got {prob}."
        )

    return prob


def validate_kraus_completeness(kraus_ops: Sequence[np.ndarray], atol: float = 1e-7) -> bool:
    """Verify that a set of Kraus operators satisfies the CPTP completeness relation sum K_i^dagger K_i = I.

    Args:
        kraus_ops: Sequence of 2x2 complex numpy matrices.
        atol: Numerical tolerance for the identity check.

    Returns:
        True if the completeness relation holds, False otherwise.
    """
    if not kraus_ops:
        return False

    total = np.zeros((2, 2), dtype=np.complex128)
    for k in kraus_ops:
        total += k.conj().T @ k

    return bool(np.allclose(total, PAULI_I, atol=atol))


@dataclass(frozen=True)
class NoiseChannel:
    """Immutable representation of a single-qubit CPTP quantum noise channel.

    Attributes:
        noise_type: Type of noise (bit_flip, phase_flip, depolarizing).
        probability: Channel error probability parameter p in [0.0, 1.0].
        kraus_operators: Tuple of 2x2 Kraus matrices representing the channel.
    """

    noise_type: NoiseType
    probability: float
    kraus_operators: tuple[np.ndarray, ...]

    def __post_init__(self) -> None:
        """Enforce physical invariants on instantiation."""
        if not isinstance(self.noise_type, NoiseType):
            raise TypeError(f"noise_type must be a NoiseType enum, got {type(self.noise_type).__name__}.")

        validate_noise_probability(self.probability)

        if not self.kraus_operators:
            raise ValueError("NoiseChannel must have at least one Kraus operator.")

        for op in self.kraus_operators:
            if not isinstance(op, np.ndarray) or op.shape != (2, 2):
                raise ValueError(f"Kraus operators must be 2x2 numpy arrays, got shape {getattr(op, 'shape', None)}.")

        if not validate_kraus_completeness(self.kraus_operators):
            raise ValueError("Kraus operators violate CPTP completeness relation: sum K_i^dagger K_i != I.")

    def apply_to_density_matrix(self, rho: np.ndarray, atol: float = 1e-7) -> np.ndarray:
        """Apply the quantum noise channel to a 2x2 density matrix.

        Mathematical Model:
            rho' = sum_i K_i rho K_i^dagger

        Args:
            rho: Valid 2x2 density matrix.
            atol: Numerical tolerance for density matrix validation.

        Returns:
            Noisy 2x2 density matrix rho'.
        """
        valid_rho = validate_density_matrix(rho, atol=atol)

        # Zero-noise identity shortcut
        if self.probability == 0.0:
            return valid_rho.copy()

        rho_prime = np.zeros((2, 2), dtype=np.complex128)
        for k in self.kraus_operators:
            rho_prime += k @ valid_rho @ k.conj().T

        return validate_density_matrix(rho_prime, atol=atol)

    def apply_to_state(self, state: Any, atol: float = 1e-7) -> np.ndarray:
        """Apply the noise channel to a pure state vector or density matrix.

        If input is a pure statevector, it is first mapped to rho = |psi><psi|.

        Args:
            state: Pure statevector, standard state label, QubitState, or density matrix.
            atol: Numerical tolerance.

        Returns:
            Noisy 2x2 density matrix rho'.
        """
        # Determine if input is already a 2x2 density matrix
        is_matrix = False
        try:
            arr = np.asarray(state)
            if arr.shape == (2, 2):
                is_matrix = True
        except Exception:
            pass

        if is_matrix:
            rho = validate_density_matrix(state, atol=atol)
        else:
            rho = pure_state_to_density_matrix(state, atol=atol)

        return self.apply_to_density_matrix(rho, atol=atol)

    def sample_noisy_state(
        self,
        state: Any,
        rng: np.random.Generator | int | None = None,
        atol: float = 1e-7,
    ) -> tuple[np.ndarray, int]:
        """Stochastically sample a single Kraus branch applied to a pure state.

        Given pure state |psi>, branch k occurs with probability:
            p_k = Tr(K_k |psi><psi| K_k^dagger) = || K_k |psi> ||^2.
        The post-measurement state for branch k is:
            |psi_k> = K_k |psi> / sqrt(p_k).

        Args:
            state: Pure single-qubit statevector.
            rng: Optional numpy Generator or integer seed for reproducibility.
            atol: Numerical tolerance.

        Returns:
            Tuple of (normalized post-channel pure statevector (2,), sampled branch index).
        """
        if isinstance(rng, np.random.Generator):
            generator = rng
        elif isinstance(rng, int):
            generator = np.random.default_rng(seed=rng)
        else:
            generator = np.random.default_rng()

        # Parse pure statevector
        from src.quantum.states import QubitState, get_standard_state, validate_state_vector
        if isinstance(state, str):
            vec = get_standard_state(state)
        elif isinstance(state, QubitState):
            vec = state.vector
        else:
            vec = validate_state_vector(state, atol=atol)

        # Compute branch probabilities: p_k = || K_k |psi> ||^2
        branch_vectors = [k @ vec for k in self.kraus_operators]
        branch_probs = [float(np.real(np.vdot(bv, bv))) for bv in branch_vectors]
        total_p = sum(branch_probs)
        norm_probs = [p / total_p for p in branch_probs]

        # Sample branch
        chosen_idx = int(generator.choice(len(self.kraus_operators), p=norm_probs))
        chosen_vec = branch_vectors[chosen_idx]
        norm = math.sqrt(max(1e-15, branch_probs[chosen_idx]))

        normalized_state = chosen_vec / norm
        return normalized_state, chosen_idx


def create_bit_flip_channel(p: float) -> NoiseChannel:
    """Construct a single-qubit bit-flip CPTP noise channel.

    Mathematical Model:
        rho' = (1-p) rho + p X rho X
        K_0 = sqrt(1-p) I,   K_1 = sqrt(p) X.

    Args:
        p: Bit-flip error probability in [0.0, 1.0].

    Returns:
        NoiseChannel instance.
    """
    prob = validate_noise_probability(p)
    k0 = math.sqrt(1.0 - prob) * PAULI_I
    k1 = math.sqrt(prob) * PAULI_X
    return NoiseChannel(
        noise_type=NoiseType.BIT_FLIP,
        probability=prob,
        kraus_operators=(k0, k1),
    )


def create_phase_flip_channel(p: float) -> NoiseChannel:
    """Construct a single-qubit phase-flip CPTP noise channel.

    Mathematical Model:
        rho' = (1-p) rho + p Z rho Z
        K_0 = sqrt(1-p) I,   K_1 = sqrt(p) Z.

    Args:
        p: Phase-flip error probability in [0.0, 1.0].

    Returns:
        NoiseChannel instance.
    """
    prob = validate_noise_probability(p)
    k0 = math.sqrt(1.0 - prob) * PAULI_I
    k1 = math.sqrt(prob) * PAULI_Z
    return NoiseChannel(
        noise_type=NoiseType.PHASE_FLIP,
        probability=prob,
        kraus_operators=(k0, k1),
    )


def create_depolarizing_channel(p: float) -> NoiseChannel:
    """Construct a single-qubit depolarizing CPTP noise channel (Pauli convention).

    Mathematical Model:
        rho' = (1-p) rho + (p/3) [X rho X + Y rho Y + Z rho Z]
        K_0 = sqrt(1-p) I
        K_1 = sqrt(p/3) X
        K_2 = sqrt(p/3) Y
        K_3 = sqrt(p/3) Z

    Args:
        p: Depolarizing probability parameter in [0.0, 1.0].

    Returns:
        NoiseChannel instance.
    """
    prob = validate_noise_probability(p)
    k0 = math.sqrt(1.0 - prob) * PAULI_I
    weight = math.sqrt(prob / 3.0)
    k1 = weight * PAULI_X
    k2 = weight * PAULI_Y
    k3 = weight * PAULI_Z
    return NoiseChannel(
        noise_type=NoiseType.DEPOLARIZING,
        probability=prob,
        kraus_operators=(k0, k1, k2, k3),
    )


def create_qiskit_noise_model(
    noise_channel: NoiseChannel,
    target_qubits: Sequence[int] | None = None,
    instructions: Sequence[str] | None = None,
) -> NoiseModel:
    """Convert an M8 NoiseChannel into a Qiskit Aer NoiseModel for circuit simulation.

    Args:
        noise_channel: NoiseChannel instance.
        target_qubits: Optional sequence of qubit indices to apply error to.
                       If None, applies to all qubits.
        instructions: Optional sequence of gate names to attach the error to.
                      If None, defaults to ["id"] when target_qubits is given,
                      or ["id", "x", "h", "z", "y"] when target_qubits is None.

    Returns:
        Qiskit Aer NoiseModel configuring 1-qubit quantum gate errors.
    """
    noise_model = NoiseModel()
    p = noise_channel.probability

    if p == 0.0:
        return noise_model

    if instructions is None:
        gate_list = ["id"] if target_qubits is not None else ["id", "x", "h", "z", "y"]
    else:
        gate_list = list(instructions)

    if noise_channel.noise_type == NoiseType.BIT_FLIP:
        err = pauli_error([("X", p), ("I", 1.0 - p)])
    elif noise_channel.noise_type == NoiseType.PHASE_FLIP:
        err = pauli_error([("Z", p), ("I", 1.0 - p)])
    elif noise_channel.noise_type == NoiseType.DEPOLARIZING:
        # Standard Qiskit depolarizing error mapping: p_aer = (4/3) * p
        # For p in [0.0, 1.0], p_aer in [0.0, 4/3]. Qiskit Aer accepts p_aer in [0.0, 4/3].
        p_qiskit = min(4.0 / 3.0, (4.0 / 3.0) * p)
        err = depolarizing_error(p_qiskit, 1)
    else:
        raise ValueError(f"Unsupported noise channel type: {noise_channel.noise_type}")

    if target_qubits is not None:
        noise_model.add_quantum_error(err, gate_list, list(target_qubits))
    else:
        noise_model.add_all_qubit_quantum_error(err, gate_list)

    return noise_model

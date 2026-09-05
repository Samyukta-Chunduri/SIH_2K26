"""Q-SHIELD — Quantum Noise Module (Milestone M8).

Exposes density matrix utilities, honest quantum noise channels (bit-flip,
phase-flip, depolarizing), Qiskit Aer noise models, and teleportation-noise
simulation pipelines.
"""

from .density_matrix import (
    calculate_mixed_state_fidelity,
    density_matrix_probabilities,
    pure_state_to_density_matrix,
    validate_density_matrix,
)
from .models import (
    NoiseChannel,
    NoiseType,
    create_bit_flip_channel,
    create_depolarizing_channel,
    create_phase_flip_channel,
    create_qiskit_noise_model,
    validate_kraus_completeness,
    validate_noise_probability,
)
from .teleportation_noise import (
    NoisyTeleportationResult,
    run_noise_sweep,
    simulate_noisy_teleportation_circuit,
    simulate_noisy_teleportation_mathematical,
)

__all__ = [
    "pure_state_to_density_matrix",
    "validate_density_matrix",
    "calculate_mixed_state_fidelity",
    "density_matrix_probabilities",
    "NoiseType",
    "NoiseChannel",
    "validate_noise_probability",
    "validate_kraus_completeness",
    "create_bit_flip_channel",
    "create_phase_flip_channel",
    "create_depolarizing_channel",
    "create_qiskit_noise_model",
    "NoisyTeleportationResult",
    "simulate_noisy_teleportation_mathematical",
    "simulate_noisy_teleportation_circuit",
    "run_noise_sweep",
]

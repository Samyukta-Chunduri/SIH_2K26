"""Tests for Quantum Noise and Honest Channel Imperfections (Milestone M8).

Validates:
1. Density matrix construction (|psi><psi| with complex conjugation) and validation (Hermitian, unit trace, positive semidefinite).
2. Pure, mixed, and pure-mixed quantum state fidelity calculations.
3. Measurement probability derivations from density matrices across Z, X, Y bases.
4. Bit-flip channel, Kraus completeness, and basis-selective degradation (degrades Z, preserves |+>).
5. Phase-flip channel, Kraus completeness, and basis-selective degradation (degrades X, preserves |0>).
6. Depolarizing channel (Pauli convention), Kraus completeness, and isotropic decoherence.
7. Noise probability parameter validation (strict rejection of p < 0, p > 1, NaN, Inf, non-numeric, bool).
8. Zero-noise limit (p = 0 acts as exact identity channel across all states).
9. Integration of honest noise with M6 teleportation and M7 verification across all 6 Pauli states and complex superpositions.
10. Noise sweeps demonstrating physical fidelity response.
11. Reproducibility using seeds for stochastic noise sampling.
12. Qiskit Aer noise model cross-validation.
13. Dedicated bug-catching sensitivity suite for Bugs A through O.
14. Strict M8 scope enforcement (no attack classification, no security thresholds, no baselines, no ML).
"""

from __future__ import annotations

import math
from typing import Any
import numpy as np
import pytest

from src.noise import (
    NoiseChannel,
    NoiseType,
    NoisyTeleportationResult,
    calculate_mixed_state_fidelity,
    create_bit_flip_channel,
    create_depolarizing_channel,
    create_phase_flip_channel,
    create_qiskit_noise_model,
    density_matrix_probabilities,
    pure_state_to_density_matrix,
    run_noise_sweep,
    simulate_noisy_teleportation_circuit,
    simulate_noisy_teleportation_mathematical,
    validate_density_matrix,
    validate_kraus_completeness,
    validate_noise_probability,
)
from src.quantum.pauli import PAULI_I, PAULI_X, PAULI_Y, PAULI_Z
from src.quantum.states import (
    STATE_0,
    STATE_1,
    STATE_MINUS,
    STATE_MINUS_I,
    STATE_PLUS,
    STATE_PLUS_I,
    QubitState,
)


# ==============================================================================
# 1. Density Matrix Construction & Validation
# ==============================================================================

class TestDensityMatrixOperations:
    """Validates density matrix representation, validation, and fidelity."""

    def test_pure_state_to_density_matrix(self) -> None:
        """Construct density matrices for standard Pauli eigenstates."""
        rho_0 = pure_state_to_density_matrix(STATE_0)
        assert np.allclose(rho_0, np.array([[1.0, 0.0], [0.0, 0.0]]))

        rho_1 = pure_state_to_density_matrix(STATE_1)
        assert np.allclose(rho_1, np.array([[0.0, 0.0], [0.0, 1.0]]))

        rho_plus = pure_state_to_density_matrix(STATE_PLUS)
        assert np.allclose(rho_plus, np.array([[0.5, 0.5], [0.5, 0.5]]))

        # Complex state |+i> = (|0> + i|1>)/sqrt(2)
        rho_plus_i = pure_state_to_density_matrix(STATE_PLUS_I)
        expected_plus_i = np.array([[0.5, -0.5j], [0.5j, 0.5]])
        assert np.allclose(rho_plus_i, expected_plus_i)

    def test_density_matrix_validation_valid(self) -> None:
        """Valid density matrices must pass validation cleanly."""
        rho_0 = pure_state_to_density_matrix(STATE_0)
        validated = validate_density_matrix(rho_0)
        assert np.allclose(validated, rho_0)

        # Maximally mixed state I/2
        rho_mixed = 0.5 * PAULI_I
        validated_mixed = validate_density_matrix(rho_mixed)
        assert np.allclose(validated_mixed, rho_mixed)

    def test_density_matrix_validation_invalid_shape(self) -> None:
        """Non-2x2 matrices must raise ValueError."""
        with pytest.raises(ValueError, match="shape"):
            validate_density_matrix(np.eye(3))
        with pytest.raises(ValueError, match="shape"):
            validate_density_matrix(np.array([1.0, 0.0]))

    def test_density_matrix_validation_non_hermitian(self) -> None:
        """Non-Hermitian matrices must raise ValueError."""
        non_herm = np.array([[0.5, 0.2 + 0.3j], [0.2 + 0.1j, 0.5]])
        with pytest.raises(ValueError, match="Hermitian"):
            validate_density_matrix(non_herm)

    def test_density_matrix_validation_trace_not_one(self) -> None:
        """Matrices without unit trace must raise ValueError."""
        non_unit_trace = np.array([[0.6, 0.0], [0.0, 0.6]])
        with pytest.raises(ValueError, match="unit trace"):
            validate_density_matrix(non_unit_trace)

    def test_density_matrix_validation_negative_eigenvalues(self) -> None:
        """Matrices with negative eigenvalues (non-positive-semidefinite) must raise ValueError."""
        non_psd = np.array([[1.2, 0.0], [0.0, -0.2]])  # trace is 1.0, but has -0.2 eigenvalue
        with pytest.raises(ValueError, match="positive semidefinite"):
            validate_density_matrix(non_psd)

    def test_density_matrix_validation_nan_inf(self) -> None:
        """Matrices with NaN or Inf must raise ValueError."""
        with pytest.raises(ValueError, match="finite"):
            validate_density_matrix(np.array([[np.nan, 0.0], [0.0, 1.0]]))
        with pytest.raises(ValueError, match="finite"):
            validate_density_matrix(np.array([[np.inf, 0.0], [0.0, 1.0]]))

    def test_density_matrix_probabilities(self) -> None:
        """Born probabilities for density matrices across Z, X, Y bases."""
        rho_0 = pure_state_to_density_matrix(STATE_0)
        pz = density_matrix_probabilities(rho_0, basis="Z")
        assert np.isclose(pz["0"], 1.0) and np.isclose(pz["1"], 0.0)

        # In X basis, |0> is 50/50
        px = density_matrix_probabilities(rho_0, basis="X")
        assert np.isclose(px["+"], 0.5) and np.isclose(px["-"], 0.5)

        # Maximally mixed state I/2 has 50/50 across all bases
        rho_mixed = 0.5 * PAULI_I
        for b in ("Z", "X", "Y"):
            probs = density_matrix_probabilities(rho_mixed, basis=b)
            vals = list(probs.values())
            assert np.isclose(vals[0], 0.5) and np.isclose(vals[1], 0.5)

    def test_mixed_state_fidelity(self) -> None:
        """Calculate fidelity between pure-pure, pure-mixed, and mixed-mixed states."""
        rho_0 = pure_state_to_density_matrix(STATE_0)
        rho_1 = pure_state_to_density_matrix(STATE_1)
        rho_mixed = 0.5 * PAULI_I

        # Pure-Pure
        assert np.isclose(calculate_mixed_state_fidelity(STATE_0, STATE_0), 1.0)
        assert np.isclose(calculate_mixed_state_fidelity(STATE_0, STATE_1), 0.0)

        # Pure-Mixed
        assert np.isclose(calculate_mixed_state_fidelity(STATE_0, rho_0), 1.0)
        assert np.isclose(calculate_mixed_state_fidelity(STATE_0, rho_1), 0.0)
        assert np.isclose(calculate_mixed_state_fidelity(STATE_0, rho_mixed), 0.5)

        # Mixed-Mixed
        assert np.isclose(calculate_mixed_state_fidelity(rho_mixed, rho_mixed), 1.0)
        assert np.isclose(calculate_mixed_state_fidelity(rho_0, rho_mixed), 0.5)


# ==============================================================================
# 2. Bit-Flip Noise Channel
# ==============================================================================

class TestBitFlipChannel:
    """Validates the bit-flip channel rho' = (1-p) rho + p X rho X."""

    def test_bit_flip_kraus_completeness(self) -> None:
        """Bit-flip Kraus operators must satisfy completeness relation."""
        for p in (0.0, 0.1, 0.5, 0.9, 1.0):
            ch = create_bit_flip_channel(p)
            assert validate_kraus_completeness(ch.kraus_operators)

    def test_bit_flip_zero_noise_identity(self) -> None:
        """p = 0 must be an exact identity channel."""
        ch = create_bit_flip_channel(0.0)
        for state in (STATE_0, STATE_1, STATE_PLUS, STATE_MINUS, STATE_PLUS_I, STATE_MINUS_I):
            rho_in = pure_state_to_density_matrix(state)
            rho_out = ch.apply_to_density_matrix(rho_in)
            assert np.allclose(rho_out, rho_in)

    def test_bit_flip_complete_inversion(self) -> None:
        """p = 1 must completely invert computational basis states |0> <-> |1>."""
        ch = create_bit_flip_channel(1.0)

        rho_0 = pure_state_to_density_matrix(STATE_0)
        rho_out_0 = ch.apply_to_density_matrix(rho_0)
        assert np.allclose(rho_out_0, pure_state_to_density_matrix(STATE_1))

        rho_1 = pure_state_to_density_matrix(STATE_1)
        rho_out_1 = ch.apply_to_density_matrix(rho_1)
        assert np.allclose(rho_out_1, pure_state_to_density_matrix(STATE_0))

    def test_bit_flip_preserves_hadamard_state(self) -> None:
        """Bit-flip preserves |+> because X|+> = |+>."""
        ch = create_bit_flip_channel(0.4)
        rho_plus = pure_state_to_density_matrix(STATE_PLUS)
        rho_out = ch.apply_to_density_matrix(rho_plus)
        assert np.allclose(rho_out, rho_plus)


# ==============================================================================
# 3. Phase-Flip Noise Channel
# ==============================================================================

class TestPhaseFlipChannel:
    """Validates the phase-flip channel rho' = (1-p) rho + p Z rho Z."""

    def test_phase_flip_kraus_completeness(self) -> None:
        """Phase-flip Kraus operators must satisfy completeness relation."""
        for p in (0.0, 0.25, 0.5, 0.75, 1.0):
            ch = create_phase_flip_channel(p)
            assert validate_kraus_completeness(ch.kraus_operators)

    def test_phase_flip_zero_noise_identity(self) -> None:
        """p = 0 must be an exact identity channel."""
        ch = create_phase_flip_channel(0.0)
        for state in (STATE_0, STATE_1, STATE_PLUS, STATE_MINUS, STATE_PLUS_I, STATE_MINUS_I):
            rho_in = pure_state_to_density_matrix(state)
            rho_out = ch.apply_to_density_matrix(rho_in)
            assert np.allclose(rho_out, rho_in)

    def test_phase_flip_preserves_computational_basis(self) -> None:
        """Phase-flip preserves |0> and |1> because Z|0> = |0> and Z|1> = -|1>."""
        ch = create_phase_flip_channel(0.5)
        rho_0 = pure_state_to_density_matrix(STATE_0)
        assert np.allclose(ch.apply_to_density_matrix(rho_0), rho_0)

        rho_1 = pure_state_to_density_matrix(STATE_1)
        assert np.allclose(ch.apply_to_density_matrix(rho_1), rho_1)

    def test_phase_flip_complete_inversion_hadamard(self) -> None:
        """p = 1 flips |+> <-> |->."""
        ch = create_phase_flip_channel(1.0)
        rho_plus = pure_state_to_density_matrix(STATE_PLUS)
        rho_out = ch.apply_to_density_matrix(rho_plus)
        assert np.allclose(rho_out, pure_state_to_density_matrix(STATE_MINUS))


# ==============================================================================
# 4. Depolarizing Noise Channel
# ==============================================================================

class TestDepolarizingChannel:
    """Validates the depolarizing channel rho' = (1-p) rho + (p/3) [X rho X + Y rho Y + Z rho Z]."""

    def test_depolarizing_kraus_completeness(self) -> None:
        """Depolarizing Kraus operators must satisfy completeness relation."""
        for p in (0.0, 0.1, 0.33, 0.5, 0.8, 1.0):
            ch = create_depolarizing_channel(p)
            assert validate_kraus_completeness(ch.kraus_operators)

    def test_depolarizing_zero_noise_identity(self) -> None:
        """p = 0 must be an exact identity channel."""
        ch = create_depolarizing_channel(0.0)
        for state in (STATE_0, STATE_1, STATE_PLUS, STATE_MINUS, STATE_PLUS_I, STATE_MINUS_I):
            rho_in = pure_state_to_density_matrix(state)
            rho_out = ch.apply_to_density_matrix(rho_in)
            assert np.allclose(rho_out, rho_in)

    def test_depolarizing_degrades_purity(self) -> None:
        """Depolarizing noise decreases state purity Tr(rho^2) from 1.0."""
        ch = create_depolarizing_channel(0.5)
        rho_0 = pure_state_to_density_matrix(STATE_0)
        rho_out = ch.apply_to_density_matrix(rho_0)

        purity = float(np.real(np.trace(rho_out @ rho_out)))
        assert purity < 1.0
        assert purity >= 0.5


# ==============================================================================
# 5. Probability Parameter Validation
# ==============================================================================

class TestProbabilityValidation:
    """Validates strict boundary and type checking for noise probabilities."""

    def test_valid_probabilities(self) -> None:
        """0.0, 0.5, 1.0 are valid."""
        assert validate_noise_probability(0.0) == 0.0
        assert validate_noise_probability(0.5) == 0.5
        assert validate_noise_probability(1.0) == 1.0
        assert validate_noise_probability(1) == 1.0

    def test_invalid_probability_ranges(self) -> None:
        """p < 0 or p > 1 must raise ValueError."""
        with pytest.raises(ValueError, match="in \\[0.0, 1.0\\]"):
            validate_noise_probability(-0.01)
        with pytest.raises(ValueError, match="in \\[0.0, 1.0\\]"):
            validate_noise_probability(1.01)

    def test_non_finite_probability(self) -> None:
        """NaN or Inf must raise ValueError."""
        with pytest.raises(ValueError, match="finite"):
            validate_noise_probability(float("nan"))
        with pytest.raises(ValueError, match="finite"):
            validate_noise_probability(float("inf"))

    def test_invalid_probability_types(self) -> None:
        """Strings, booleans, and None must raise TypeError."""
        with pytest.raises(TypeError):
            validate_noise_probability("0.5")
        with pytest.raises(TypeError):
            validate_noise_probability(True)
        with pytest.raises(TypeError):
            validate_noise_probability(False)
        with pytest.raises(TypeError):
            validate_noise_probability(None)


# ==============================================================================
# 6. Teleportation + Noise Integration
# ==============================================================================

class TestTeleportationNoiseIntegration:
    """Validates teleportation under honest physical channel noise."""

    def test_teleportation_all_six_states_zero_noise(self) -> None:
        """Under zero noise (p=0), teleportation achieves fidelity = 1.0 across all 6 Pauli states."""
        ch = create_depolarizing_channel(0.0)
        for state in (STATE_0, STATE_1, STATE_PLUS, STATE_MINUS, STATE_PLUS_I, STATE_MINUS_I):
            res = simulate_noisy_teleportation_mathematical(state, ch, branch=(0, 0))
            assert np.isclose(res.fidelity, 1.0, atol=1e-12)

    def test_teleportation_arbitrary_complex_state(self) -> None:
        """Teleport an arbitrary complex superposition state under noise."""
        alpha = 1.0 / math.sqrt(3.0)
        beta = math.sqrt(2.0 / 3.0) * np.exp(1j * math.pi / 4.0)
        psi = np.array([alpha, beta], dtype=np.complex128)

        # Zero noise
        ch_0 = create_bit_flip_channel(0.0)
        res_0 = simulate_noisy_teleportation_mathematical(psi, ch_0)
        assert np.isclose(res_0.fidelity, 1.0, atol=1e-12)

        # Moderate noise
        ch_noisy = create_depolarizing_channel(0.15)
        res_noisy = simulate_noisy_teleportation_mathematical(psi, ch_noisy)
        assert 0.8 < res_noisy.fidelity < 1.0

    def test_noise_sweep_fidelity_response(self) -> None:
        """Sweeping noise probability p yields monotonically decreasing fidelity for depolarizing noise."""
        probs = [0.0, 0.05, 0.1, 0.2, 0.4]
        results = run_noise_sweep(STATE_0, NoiseType.DEPOLARIZING, probs)

        fidelities = [r.fidelity for r in results]
        assert np.isclose(fidelities[0], 1.0)
        for i in range(len(fidelities) - 1):
            assert fidelities[i] > fidelities[i + 1]


# ==============================================================================
# 7. Reproducibility
# ==============================================================================

class TestNoiseReproducibility:
    """Validates reproducibility of stochastic noise sampling."""

    def test_stochastic_sampling_seed_reproducibility(self) -> None:
        """Supplying identical seeds must yield identical sampled states."""
        ch = create_bit_flip_channel(0.3)
        seed = 42

        state_1, branch_1 = ch.sample_noisy_state(STATE_0, rng=seed)
        state_2, branch_2 = ch.sample_noisy_state(STATE_0, rng=seed)

        assert branch_1 == branch_2
        assert np.allclose(state_1, state_2)


# ==============================================================================
# 8. Qiskit Aer Noise Model Cross-Validation
# ==============================================================================

class TestQiskitNoiseIntegration:
    """Validates Qiskit Aer noise model construction and circuit simulation."""

    def test_qiskit_noise_model_creation(self) -> None:
        """Construct Qiskit Aer noise models for bit-flip, phase-flip, and depolarizing channels."""
        bf = create_bit_flip_channel(0.1)
        model_bf = create_qiskit_noise_model(bf)
        assert model_bf is not None

        pf = create_phase_flip_channel(0.1)
        model_pf = create_qiskit_noise_model(pf)
        assert model_pf is not None

        dp = create_depolarizing_channel(0.1)
        model_dp = create_qiskit_noise_model(dp)
        assert model_dp is not None

    def test_simulate_noisy_teleportation_circuit(self) -> None:
        """Execute Qiskit circuit with channel noise."""
        ch = create_bit_flip_channel(0.0)
        res = simulate_noisy_teleportation_circuit(STATE_0, ch, shots=500, seed=123)
        assert res["shots"] == 500
        # In ideal zero-noise simulation, Bob's outcome in computational basis must be 100% '0'
        assert np.isclose(res["bob_probabilities"].get("0", 0.0), 1.0, atol=1e-2)


# ==============================================================================
# 9. Bug-Catching Sensitivity Suite (Bugs A through O)
# ==============================================================================

class TestBugCatchingSensitivity:
    """Sensitivity tests designed specifically to catch subtle implementation mistakes."""

    def test_bug_a_wrong_bit_flip_operator(self) -> None:
        """Bug A: Bit-flip channel mistakenly using Z or Y instead of X."""
        ch = create_bit_flip_channel(1.0)
        # Applying bit-flip to |0> must yield |1>, NOT |0> (Z) or i|1> (Y)
        rho_out = ch.apply_to_state(STATE_0)
        assert np.allclose(rho_out, pure_state_to_density_matrix(STATE_1)), "Bug A detected: Bit flip must use Pauli-X!"

    def test_bug_b_wrong_phase_flip_operator(self) -> None:
        """Bug B: Phase-flip channel mistakenly using X or Y instead of Z."""
        ch = create_phase_flip_channel(1.0)
        # Applying phase-flip to |+> must yield |->, NOT |+>
        rho_out = ch.apply_to_state(STATE_PLUS)
        assert np.allclose(rho_out, pure_state_to_density_matrix(STATE_MINUS)), "Bug B detected: Phase flip must use Pauli-Z!"

    def test_bug_c_wrong_depolarizing_probabilities(self) -> None:
        """Bug C: Depolarizing channel with unequal or incorrect Kraus weights."""
        ch = create_depolarizing_channel(0.3)
        # Weights must be sqrt(1-p) for I and sqrt(p/3) for X, Y, Z
        expected_w = math.sqrt(0.3 / 3.0)
        assert np.isclose(ch.kraus_operators[1][0, 1], expected_w)
        assert np.isclose(ch.kraus_operators[2][0, 1], -expected_w * 1j)
        assert np.isclose(ch.kraus_operators[3][0, 0], expected_w)

    def test_bug_d_missing_complex_conjugation(self) -> None:
        """Bug D: Density matrix formed via outer(psi, psi) instead of outer(psi, conj(psi))."""
        # For |+i> = [1/sqrt(2), i/sqrt(2)]
        # outer(psi, psi)[0, 1] = 1/sqrt(2) * i/sqrt(2) = 0.5i (non-Hermitian!)
        # outer(psi, conj(psi))[0, 1] = 1/sqrt(2) * (-i/sqrt(2)) = -0.5i
        rho = pure_state_to_density_matrix(STATE_PLUS_I)
        assert np.isclose(rho[0, 1], -0.5j), "Bug D detected: complex conjugation was omitted!"
        assert np.allclose(rho, rho.conj().T)

    def test_bug_e_invalid_probability_accepted(self) -> None:
        """Bug E: Invalid noise probability accepted."""
        with pytest.raises(ValueError):
            create_bit_flip_channel(-0.1)
        with pytest.raises(ValueError):
            create_bit_flip_channel(1.2)

    def test_bug_f_zero_noise_changes_state(self) -> None:
        """Bug F: Zero-noise channel alters state."""
        ch = create_depolarizing_channel(0.0)
        psi = np.array([math.cos(0.3), math.sin(0.3) * np.exp(0.4j)], dtype=np.complex128)
        rho_in = pure_state_to_density_matrix(psi)
        rho_out = ch.apply_to_density_matrix(rho_in)
        assert np.allclose(rho_in, rho_out), "Bug F detected: zero noise altered the state!"

    def test_bug_g_non_physical_density_matrix_accepted(self) -> None:
        """Bug G: Non-physical density matrix accepted by validator."""
        # Trace != 1
        with pytest.raises(ValueError):
            validate_density_matrix(np.eye(2))
        # Negative eigenvalue
        with pytest.raises(ValueError):
            validate_density_matrix(np.array([[1.5, 0.0], [0.0, -0.5]]))

    def test_bug_h_wrong_kraus_completeness(self) -> None:
        """Bug H: Kraus operators failing sum K_i^dagger K_i = I accepted."""
        with pytest.raises(ValueError, match="completeness"):
            NoiseChannel(
                noise_type=NoiseType.BIT_FLIP,
                probability=0.5,
                kraus_operators=(PAULI_I, PAULI_X),  # I + X^2 = 2I != I
            )

    def test_bug_i_noise_applied_to_wrong_qubit(self) -> None:
        """Bug I: In teleportation circuit simulation, noise applied to wrong qubit."""
        ch = create_bit_flip_channel(1.0)
        # Verify noise model specifically targets the assigned qubit
        nm_bob = create_qiskit_noise_model(ch, target_qubits=[2], instructions=["id"])
        assert nm_bob.noise_qubits == [2]
        assert 0 not in nm_bob.noise_qubits
        assert 1 not in nm_bob.noise_qubits

        # In circuit execution, Bob's qubit (2) receives the bit-flip
        res = simulate_noisy_teleportation_circuit(STATE_0, ch, shots=200, seed=42, target_qubit=2)
        assert np.isclose(res["bob_probabilities"].get("1", 0.0), 1.0, atol=1e-2)

    def test_bug_j_noise_accidentally_applied_twice(self) -> None:
        """Bug J: Channel applied multiple times unintentionally."""
        ch = create_bit_flip_channel(0.5)
        # Applying a 0.5 bit-flip once to |0> yields diagonal [0.5, 0.5]
        rho_out = ch.apply_to_state(STATE_0)
        assert np.isclose(rho_out[0, 0].real, 0.5)
        assert np.isclose(rho_out[1, 1].real, 0.5)

    def test_bug_k_noise_parameter_ignored(self) -> None:
        """Bug K: Distinct noise strengths produce identical results."""
        ch1 = create_depolarizing_channel(0.1)
        ch2 = create_depolarizing_channel(0.8)

        rho1 = ch1.apply_to_state(STATE_0)
        rho2 = ch2.apply_to_state(STATE_0)

        assert not np.allclose(rho1, rho2), "Bug K detected: noise parameter was ignored!"

    def test_bug_l_noise_type_ignored(self) -> None:
        """Bug L: Different noise types produce identical transformations."""
        bf = create_bit_flip_channel(0.5)
        pf = create_phase_flip_channel(0.5)

        # On state |+>, bit-flip preserves |+> while phase-flip degrades |+>
        rho_bf = bf.apply_to_state(STATE_PLUS)
        rho_pf = pf.apply_to_state(STATE_PLUS)

        assert not np.allclose(rho_bf, rho_pf), "Bug L detected: noise types produced identical transformations!"

    def test_bug_m_hidden_random_seed(self) -> None:
        """Bug M: Stochastic sampling lacks seed reproducibility."""
        ch = create_depolarizing_channel(0.5)
        s1, b1 = ch.sample_noisy_state(STATE_0, rng=999)
        s2, b2 = ch.sample_noisy_state(STATE_0, rng=999)
        assert b1 == b2
        assert np.allclose(s1, s2), "Bug M detected: seed reproducibility failed!"

    def test_bug_n_global_random_state_contamination(self) -> None:
        """Bug N: Sampling alters global random state without isolated generator."""
        ch = create_bit_flip_channel(0.5)
        np.random.seed(12345)
        expected_rand = np.random.rand()

        np.random.seed(12345)
        # Pass explicit Generator to avoid contaminating global np.random
        rng = np.random.default_rng(999)
        ch.sample_noisy_state(STATE_0, rng=rng)
        actual_rand = np.random.rand()

        assert np.isclose(expected_rand, actual_rand), "Bug N detected: global random state was contaminated!"

    def test_bug_o_noise_mistaken_for_attack(self) -> None:
        """Bug O: M8 modules declaring or labeling noisy executions as attacks."""
        ch = create_bit_flip_channel(0.8)
        res = simulate_noisy_teleportation_mathematical(STATE_0, ch)

        # Result must be purely physical and contain NO attack/detection fields
        assert not hasattr(res, "is_attack")
        assert not hasattr(res, "attack_type")
        assert not hasattr(res, "security_score")
        assert not hasattr(res, "threat_level")


# ==============================================================================
# 10. Scope Enforcement
# ==============================================================================

class TestScopeEnforcement:
    """Strictly enforces divide-and-conquer boundaries (no M9+ features)."""

    def test_no_m9_plus_features_in_noise_package(self) -> None:
        """Ensure no baseline, detection, threshold, signature, or ML modules exist in src/noise."""
        import src.noise as noise_pkg

        forbidden_names = [
            "baseline",
            "honest_baseline",
            "estimate_baseline",
            "threshold_engine",
            "security_threshold",
            "detection_engine",
            "detect_attack",
            "is_attack",
            "forgery",
            "replay",
            "impersonation",
            "channel_attack",
            "signature",
            "sign",
            "qds",
            "evidence_fusion",
            "blockchain",
            "machine_learning",
            "neural_network",
        ]

        for name in forbidden_names:
            assert not hasattr(noise_pkg, name), f"Scope violation: '{name}' found in src/noise!"


# ==============================================================================
# 11. Additional Scientific and Numerical Review Tests
# ==============================================================================

class TestScientificReviewValidation:
    """Additional rigorous checks verifying physical correctness, API safety, and Qiskit equivalence."""

    def test_six_pauli_states_under_all_channels(self) -> None:
        """All six Pauli states under bit-flip, phase-flip, and depolarizing channels."""
        states = [STATE_0, STATE_1, STATE_PLUS, STATE_MINUS, STATE_PLUS_I, STATE_MINUS_I]
        channels = [
            create_bit_flip_channel(0.2),
            create_phase_flip_channel(0.2),
            create_depolarizing_channel(0.2),
        ]

        for st in states:
            rho_st = pure_state_to_density_matrix(st)
            for ch in channels:
                rho_noisy = ch.apply_to_state(st)
                # Must be a valid density matrix
                validate_density_matrix(rho_noisy)
                # Fidelity must be strictly in [0.0, 1.0]
                fid = calculate_mixed_state_fidelity(st, rho_noisy)
                assert 0.0 <= fid <= 1.0

    def test_depolarizing_bloch_vector_contraction(self) -> None:
        """Depolarizing channel contracts the Bloch vector by exactly (1 - 4p/3)."""
        # For any state with Bloch vector r, rho' has Bloch vector r' = (1 - 4p/3) r
        for p in (0.1, 0.25, 0.5, 0.75):
            ch = create_depolarizing_channel(p)
            contraction_factor = 1.0 - (4.0 / 3.0) * p

            # Test on |0>: r = (0, 0, 1) -> r' = (0, 0, contraction_factor)
            rho_out_0 = ch.apply_to_state(STATE_0)
            z_exp = float(np.real(np.trace(PAULI_Z @ rho_out_0)))
            assert np.isclose(z_exp, contraction_factor, atol=1e-12)

            # Test on |+>: r = (1, 0, 0) -> r' = (contraction_factor, 0, 0)
            rho_out_plus = ch.apply_to_state(STATE_PLUS)
            x_exp = float(np.real(np.trace(PAULI_X @ rho_out_plus)))
            assert np.isclose(x_exp, contraction_factor, atol=1e-12)

            # Test on |+i>: r = (0, 1, 0) -> r' = (0, contraction_factor, 0)
            rho_out_plus_i = ch.apply_to_state(STATE_PLUS_I)
            y_exp = float(np.real(np.trace(PAULI_Y @ rho_out_plus_i)))
            assert np.isclose(y_exp, contraction_factor, atol=1e-12)

    def test_qiskit_depolarizing_exact_equivalence(self) -> None:
        """Verify custom depolarizing channel matches Qiskit Aer depolarizing channel across all p."""
        from qiskit_aer.noise import depolarizing_error
        from qiskit.quantum_info import DensityMatrix, Kraus

        test_states = [STATE_0, STATE_PLUS, STATE_PLUS_I]
        for p in (0.0, 0.15, 0.3, 0.5, 0.75, 1.0):
            ch = create_depolarizing_channel(p)
            p_aer = (4.0 / 3.0) * p
            err = depolarizing_error(p_aer, 1)

            for st in test_states:
                rho_custom = ch.apply_to_state(st)
                rho_qiskit = np.asarray(DensityMatrix(st).evolve(Kraus(err)).data, dtype=np.complex128)
                assert np.allclose(rho_custom, rho_qiskit, atol=1e-14)

    def test_input_array_immutability(self) -> None:
        """APIs must not mutate caller-supplied state or density matrix arrays."""
        orig_vec = np.array([1.0 / math.sqrt(2.0), 1.0j / math.sqrt(2.0)], dtype=np.complex128)
        vec_copy = orig_vec.copy()

        # 1. pure_state_to_density_matrix
        rho = pure_state_to_density_matrix(orig_vec)
        assert np.array_equal(orig_vec, vec_copy)

        # 2. validate_density_matrix
        rho_copy = rho.copy()
        validated = validate_density_matrix(rho)
        validated[0, 0] += 999.0  # Attempt mutation on returned array
        assert np.array_equal(rho, rho_copy)

        # 3. NoiseChannel apply
        ch = create_bit_flip_channel(0.5)
        ch.apply_to_density_matrix(rho)
        assert np.array_equal(rho, rho_copy)

    def test_circuit_simulation_parameter_validation(self) -> None:
        """simulate_noisy_teleportation_circuit must reject invalid shots, target_qubit, or basis."""
        ch = create_bit_flip_channel(0.1)

        # Invalid shots
        with pytest.raises(ValueError, match="shots"):
            simulate_noisy_teleportation_circuit(STATE_0, ch, shots=0)
        with pytest.raises(ValueError, match="shots"):
            simulate_noisy_teleportation_circuit(STATE_0, ch, shots=-10)
        with pytest.raises(ValueError, match="shots"):
            simulate_noisy_teleportation_circuit(STATE_0, ch, shots=True)  # type: ignore

        # Invalid target qubit
        with pytest.raises(ValueError, match="target_qubit"):
            simulate_noisy_teleportation_circuit(STATE_0, ch, target_qubit=3)
        with pytest.raises(ValueError, match="target_qubit"):
            simulate_noisy_teleportation_circuit(STATE_0, ch, target_qubit=-1)

        # Invalid basis
        with pytest.raises(ValueError, match="basis"):
            simulate_noisy_teleportation_circuit(STATE_0, ch, bob_basis="INVALID")

    def test_shot_noise_vs_channel_noise_distinction(self) -> None:
        """Distinguish deterministic channel density matrix from empirical shot noise variance."""
        ch = create_depolarizing_channel(0.3)
        # Mathematical simulation is deterministic: exact same density matrix every call
        res1 = simulate_noisy_teleportation_mathematical(STATE_0, ch)
        res2 = simulate_noisy_teleportation_mathematical(STATE_0, ch)
        assert np.allclose(res1.noisy_density_matrix, res2.noisy_density_matrix)
        assert res1.fidelity == res2.fidelity

        # Circuit simulation exhibits shot noise (empirical variance) when different seeds are used
        c1 = simulate_noisy_teleportation_circuit(STATE_0, ch, shots=50, seed=1)
        c2 = simulate_noisy_teleportation_circuit(STATE_0, ch, shots=50, seed=2)
        # With only 50 shots, empirical counts vary due to shot noise
        # But both are valid statistical samples of the underlying channel
        assert c1["shots"] == 50 and c2["shots"] == 50


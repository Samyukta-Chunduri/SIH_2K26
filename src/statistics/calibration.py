"""Q-SHIELD — Honest Baseline Calibration Engine (Milestone M9).

Implements the execution and statistical calibration of honest quantum verification
behavior across repeated trials under explicit operating conditions.

Pipeline Architecture:
    Honest Configuration (States, Noise, Shots, Runs)
              |
              v
    Repeated Honest Teleportation + Noise Execution (N trials)
              |
              v
    Collection of Honest Metric Observations
              |
              v
    Unbiased Sample Statistics Calculation (mu, s^2, s, CI)
              |
              v
    Validated HonestBaseline Data Structure

Scientific Boundaries:
    - NOISE != ATTACK: The engine calibrates legitimate quantum behavior.
    - Strictly NO attack detection, NO security thresholds, and NO threat classification.
    - Preserves isolated, uncorrupted honest operating baselines for M10+ detection.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from datetime import datetime, timezone
import math
from typing import Any
import numpy as np

from src.noise.density_matrix import (
    calculate_mixed_state_fidelity,
    density_matrix_probabilities,
    pure_state_to_density_matrix,
    validate_density_matrix,
)
from src.noise.models import (
    NoiseChannel,
    NoiseType,
    create_bit_flip_channel,
    create_depolarizing_channel,
    create_phase_flip_channel,
)
from src.noise.teleportation_noise import (
    simulate_noisy_teleportation_circuit,
    simulate_noisy_teleportation_mathematical,
)
from src.quantum.pauli import PAULI_X, PAULI_Y, PAULI_Z
from src.quantum.states import (
    STATE_0,
    STATE_1,
    STATE_MINUS,
    STATE_MINUS_I,
    STATE_PLUS,
    STATE_PLUS_I,
    QubitState,
    get_standard_state,
    validate_state_vector,
)
from .baseline import (
    BaselineConfiguration,
    CalibrationObservation,
    HonestBaseline,
    MetricStatistics,
    calculate_sample_statistics,
    validate_baseline,
)


STANDARD_STATE_NAMES: tuple[str, ...] = ("0", "1", "+", "-", "+i", "-i")


def run_honest_calibration_trial(
    state: Any,
    noise_channel: NoiseChannel | None = None,
    shots: int | None = None,
    seed: int | None = None,
    branch: tuple[int, int] = (0, 0),
    target_qubit: int = 2,
    state_name: str | None = None,
) -> CalibrationObservation:
    """Execute a single honest teleportation trial and collect verification metrics.

    Args:
        state: Input state (str label, QubitState, or (2,) complex array).
        noise_channel: Optional NoiseChannel instance. Defaults to zero-noise depolarizing channel.
        shots: Number of measurement shots (None for exact analytical simulation).
        seed: Random seed for stochastic simulation reproducibility.
        branch: Measurement outcome branch (m0, m1) for Alice's Bell measurement.
        target_qubit: Target qubit index for channel noise in circuit simulation.
        state_name: Optional explicit name identifier for the input state.

    Returns:
        CalibrationObservation containing metrics from this honest execution.

    Raises:
        TypeError: If state or noise_channel has an invalid type.
        ValueError: If state is invalid or shots <= 0.
    """
    # 1. Resolve state name and vector
    if isinstance(state, str):
        resolved_name = state.strip().lower()
        vec = get_standard_state(resolved_name)
    elif isinstance(state, QubitState):
        resolved_name = state_name if state_name is not None else "qubit_state"
        vec = state.vector
    else:
        vec = validate_state_vector(state)
        resolved_name = state_name if state_name is not None else "custom_state"

    # 2. Resolve noise channel
    if noise_channel is None:
        active_channel = create_depolarizing_channel(0.0)
    elif isinstance(noise_channel, NoiseChannel):
        active_channel = noise_channel
    else:
        raise TypeError(f"Expected NoiseChannel, got {type(noise_channel).__name__}.")

    # 3. Simulation path (Mathematical or Circuit)
    if shots is None:
        # Analytical / statevector mathematical simulation
        res = simulate_noisy_teleportation_mathematical(
            input_state=vec,
            noise_channel=active_channel,
            branch=branch,
        )
        rho_out = res.noisy_density_matrix
        fidelity = float(res.fidelity)
        probs_z = dict(res.probabilities_z)
        probs_x = dict(res.probabilities_x)
        probs_y = dict(res.probabilities_y)

        # Exact Pauli expectations Tr(P rho)
        exp_x = float(np.real(np.trace(PAULI_X @ rho_out)))
        exp_y = float(np.real(np.trace(PAULI_Y @ rho_out)))
        exp_z = float(np.real(np.trace(PAULI_Z @ rho_out)))
    else:
        # Empirical sampling via Qiskit Aer circuit simulation
        # Measure in Z, X, Y bases using seeds derived from main seed
        seed_z = seed if seed is not None else None
        seed_x = (seed + 1000) if seed is not None else None
        seed_y = (seed + 2000) if seed is not None else None

        res_z = simulate_noisy_teleportation_circuit(
            input_state=vec,
            noise_channel=active_channel,
            shots=shots,
            seed=seed_z,
            bob_basis="Z",
            target_qubit=target_qubit,
        )
        res_x = simulate_noisy_teleportation_circuit(
            input_state=vec,
            noise_channel=active_channel,
            shots=shots,
            seed=seed_x,
            bob_basis="X",
            target_qubit=target_qubit,
        )
        res_y = simulate_noisy_teleportation_circuit(
            input_state=vec,
            noise_channel=active_channel,
            shots=shots,
            seed=seed_y,
            bob_basis="Y",
            target_qubit=target_qubit,
        )

        probs_z = {
            "0": float(res_z["bob_probabilities"].get("0", 0.0)),
            "1": float(res_z["bob_probabilities"].get("1", 0.0)),
        }
        probs_x = {
            "+": float(res_x["bob_probabilities"].get("0", 0.0)),
            "-": float(res_x["bob_probabilities"].get("1", 0.0)),
        }
        probs_y = {
            "+i": float(res_y["bob_probabilities"].get("0", 0.0)),
            "-i": float(res_y["bob_probabilities"].get("1", 0.0)),
        }

        # Empirical Pauli expectations
        exp_z = probs_z["0"] - probs_z["1"]
        exp_x = probs_x["+"] - probs_x["-"]
        exp_y = probs_y["+i"] - probs_y["-i"]

        # Empirical fidelity: overlap with expected basis projector
        # For standard states, fidelity is the probability of the expected outcome
        if resolved_name in ("0", "1"):
            fidelity = probs_z[resolved_name]
        elif resolved_name in ("+", "-"):
            fidelity = probs_x[resolved_name]
        elif resolved_name in ("+i", "-i"):
            fidelity = probs_y[resolved_name]
        else:
            # Analytical fidelity comparison for arbitrary states
            math_res = simulate_noisy_teleportation_mathematical(vec, active_channel, branch=branch)
            fidelity = float(math_res.fidelity)

    # 4. Determine Quantum Bit Error Rate (QBER)
    # For eigenstate in its eigenbasis, QBER is the probability of obtaining the orthogonal outcome.
    if resolved_name == "0":
        qber = probs_z.get("1", 0.0)
    elif resolved_name == "1":
        qber = probs_z.get("0", 0.0)
    elif resolved_name == "+":
        qber = probs_x.get("-", 0.0)
    elif resolved_name == "-":
        qber = probs_x.get("+", 0.0)
    elif resolved_name == "+i":
        qber = probs_y.get("-i", 0.0)
    elif resolved_name == "-i":
        qber = probs_y.get("+i", 0.0)
    else:
        # General state error rate: e = 1 - F
        qber = float(np.clip(1.0 - fidelity, 0.0, 1.0))

    # 5. Bell state correlations under channel noise
    # On ideal Bell pair |Phi+>: XX = +1.0, YY = -1.0, ZZ = +1.0
    # Under honest channel noise on Bob's qubit:
    # Bit-flip (X error with prob p): flips Z and Y, preserves X
    # Phase-flip (Z error with prob p): flips X and Y, preserves Z
    # Depolarizing (Pauli error with prob p): contracts all expectations by (1 - 4p/3)
    p_err = active_channel.probability
    if active_channel.noise_type == NoiseType.BIT_FLIP:
        bell_xx = 1.0
        bell_yy = -(1.0 - 2.0 * p_err)
        bell_zz = 1.0 - 2.0 * p_err
    elif active_channel.noise_type == NoiseType.PHASE_FLIP:
        bell_xx = 1.0 - 2.0 * p_err
        bell_yy = -(1.0 - 2.0 * p_err)
        bell_zz = 1.0
    elif active_channel.noise_type == NoiseType.DEPOLARIZING:
        scale = 1.0 - (4.0 / 3.0) * p_err
        bell_xx = 1.0 * scale
        bell_yy = -1.0 * scale
        bell_zz = 1.0 * scale
    else:
        bell_xx = 1.0
        bell_yy = -1.0
        bell_zz = 1.0

    correlations = {
        "XX": float(np.clip(bell_xx, -1.0, 1.0)),
        "YY": float(np.clip(bell_yy, -1.0, 1.0)),
        "ZZ": float(np.clip(bell_zz, -1.0, 1.0)),
    }

    return CalibrationObservation(
        state_name=resolved_name,
        fidelity=float(np.clip(fidelity, 0.0, 1.0)),
        qber=float(np.clip(qber, 0.0, 1.0)),
        probabilities_z=probs_z,
        probabilities_x=probs_x,
        probabilities_y=probs_y,
        pauli_expectations={
            "X": float(np.clip(exp_x, -1.0, 1.0)),
            "Y": float(np.clip(exp_y, -1.0, 1.0)),
            "Z": float(np.clip(exp_z, -1.0, 1.0)),
        },
        bell_correlations=correlations,
        shots=shots,
        branch=branch,
    )


def build_honest_baseline_from_observations(
    config: BaselineConfiguration,
    observations: Sequence[CalibrationObservation],
    confidence_level: float = 0.95,
) -> HonestBaseline:
    """Construct a calibrated HonestBaseline from a sequence of honest observations.

    Guarantees:
        1. All observations are verified as legitimate honest quantum executions (is_honest=True).
        2. Non-honest or attack data is strictly rejected, preventing baseline contamination.
        3. Statistical aggregation uses unbiased Bessel's sample variance (N - 1 denominator).
        4. Explicit configuration identity and canonical fingerprinting prevent mixing incompatible conditions.

    Args:
        config: BaselineConfiguration specifying operating conditions.
        observations: Non-empty sequence of CalibrationObservation instances.
        confidence_level: Confidence level for statistical intervals in (0.0, 1.0).

    Returns:
        Validated HonestBaseline instance.

    Raises:
        TypeError: If config or observations are of invalid types.
        ValueError: If observations is empty, contains non-honest data, or has invalid metrics.
    """
    if not isinstance(config, BaselineConfiguration):
        raise TypeError(f"Expected BaselineConfiguration, got {type(config).__name__}.")

    if not observations:
        raise ValueError("Cannot build honest baseline from empty observations sequence.")

    metric_arrays: dict[str, list[float]] = defaultdict(list)
    all_fidelities: list[float] = []
    all_qbers: list[float] = []
    bell_xx_list: list[float] = []
    bell_yy_list: list[float] = []
    bell_zz_list: list[float] = []
    observed_states: set[str] = set()

    for obs in observations:
        if not isinstance(obs, CalibrationObservation):
            raise TypeError(f"Expected CalibrationObservation, got {type(obs).__name__}.")

        # Security check: Strictly prevent baseline contamination
        if not obs.is_honest:
            raise ValueError(
                "Baseline contamination detected: Observation marked with is_honest=False cannot be "
                "incorporated into an honest baseline."
            )

        st_name = obs.state_name
        observed_states.add(st_name)

        # Per-state metrics
        metric_arrays[f"fidelity:{st_name}"].append(obs.fidelity)
        metric_arrays[f"qber:{st_name}"].append(obs.qber)
        metric_arrays[f"exp_x:{st_name}"].append(obs.pauli_expectations["X"])
        metric_arrays[f"exp_y:{st_name}"].append(obs.pauli_expectations["Y"])
        metric_arrays[f"exp_z:{st_name}"].append(obs.pauli_expectations["Z"])

        for outcome, prob in obs.probabilities_z.items():
            metric_arrays[f"prob_z_{outcome}:{st_name}"].append(prob)
        for outcome, prob in obs.probabilities_x.items():
            metric_arrays[f"prob_x_{outcome}:{st_name}"].append(prob)
        for outcome, prob in obs.probabilities_y.items():
            metric_arrays[f"prob_y_{outcome}:{st_name}"].append(prob)

        all_fidelities.append(obs.fidelity)
        all_qbers.append(obs.qber)

        if obs.bell_correlations:
            bell_xx_list.append(obs.bell_correlations["XX"])
            bell_yy_list.append(obs.bell_correlations["YY"])
            bell_zz_list.append(obs.bell_correlations["ZZ"])

    # Global aggregate metrics
    metric_arrays["fidelity:all_states"] = all_fidelities
    metric_arrays["qber:all_states"] = all_qbers
    if bell_xx_list:
        metric_arrays["bell_xx"] = bell_xx_list
        metric_arrays["bell_yy"] = bell_yy_list
        metric_arrays["bell_zz"] = bell_zz_list

    # Compute MetricStatistics for all collected metrics
    metrics: dict[str, MetricStatistics] = {}
    for metric_name, values in metric_arrays.items():
        lower_name = metric_name.lower()
        if "fidelity" in lower_name or "qber" in lower_name or "prob_" in lower_name:
            bounds: tuple[float, float] | None = (0.0, 1.0)
        elif "exp_" in lower_name or "bell_" in lower_name:
            bounds = (-1.0, 1.0)
        else:
            bounds = None

        metrics[metric_name] = calculate_sample_statistics(
            values=values,
            confidence_level=confidence_level,
            bounds=bounds,
        )

    metadata = {
        "calibrated_at": datetime.now(timezone.utc).isoformat(),
        "total_observations": len(observations),
        "evaluated_states": sorted(observed_states),
        "confidence_level": confidence_level,
        "sample_variance_convention": "unbiased_bessel_n_minus_1",
        "canonical_hash": config.canonical_hash,
    }

    baseline = HonestBaseline(
        configuration=config,
        metrics=metrics,
        metadata=metadata,
    )
    validate_baseline(baseline)
    return baseline


def calibrate_honest_baseline(
    config: BaselineConfiguration,
    custom_states: Sequence[tuple[str, Any]] | None = None,
    confidence_level: float = 0.95,
) -> HonestBaseline:
    """Execute repeated honest quantum experiments and construct a calibrated HonestBaseline.

    Args:
        config: BaselineConfiguration specifying operating conditions and trial count.
        custom_states: Optional sequence of (state_name, state_vector) to include.
        confidence_level: Confidence level for statistical intervals in (0, 1).

    Returns:
        Validated HonestBaseline instance.

    Raises:
        ValueError: If config parameters or state definitions are invalid.
    """
    if not isinstance(config, BaselineConfiguration):
        raise TypeError(f"Expected BaselineConfiguration, got {type(config).__name__}.")

    # 1. Resolve NoiseChannel
    ntype_str = config.noise_model_type.lower().strip()
    p = config.noise_strength

    if ntype_str in ("ideal", "none"):
        channel = create_depolarizing_channel(0.0)
    elif ntype_str in ("bit_flip", "bitflip"):
        channel = create_bit_flip_channel(p)
    elif ntype_str in ("phase_flip", "phaseflip"):
        channel = create_phase_flip_channel(p)
    elif ntype_str in ("depolarizing", "depol"):
        channel = create_depolarizing_channel(p)
    else:
        raise ValueError(
            f"Unsupported noise model type '{config.noise_model_type}'. Choose from ['ideal', 'bit_flip', 'phase_flip', 'depolarizing']."
        )

    # 2. Build state registry
    state_registry: dict[str, Any] = {}
    custom_map = (
        {c_name.strip().lower(): c_vec for c_name, c_vec in custom_states}
        if custom_states
        else {}
    )

    for st_name in config.states:
        name_key = st_name.strip().lower()
        if name_key in STANDARD_STATE_NAMES:
            state_registry[name_key] = get_standard_state(name_key)
        elif name_key in custom_map:
            state_registry[name_key] = validate_state_vector(custom_map[name_key])
        else:
            raise ValueError(
                f"State '{st_name}' is not in standard Pauli states {STANDARD_STATE_NAMES}. "
                "Provide non-standard states via the custom_states parameter."
            )

    if custom_states:
        for c_name, c_vec in custom_states:
            c_key = c_name.strip().lower()
            if c_key not in state_registry:
                state_registry[c_key] = validate_state_vector(c_vec)

    # 3. Run repeated honest calibration trials and collect observations
    observations: list[CalibrationObservation] = []
    num_runs = config.calibration_runs

    for run_idx in range(num_runs):
        run_seed = (config.seed + run_idx * 100) if config.seed is not None else None

        for st_name, st_vec in state_registry.items():
            obs = run_honest_calibration_trial(
                state=st_vec,
                noise_channel=channel,
                shots=config.shots,
                seed=run_seed,
                target_qubit=2,
                state_name=st_name,
            )
            observations.append(obs)

    # 4. Build and return validated honest baseline
    return build_honest_baseline_from_observations(
        config=config,
        observations=observations,
        confidence_level=confidence_level,
    )


def calibrate_noise_sweep(
    noise_type: str,
    probabilities: Sequence[float],
    states: tuple[str, ...] = STANDARD_STATE_NAMES,
    shots: int | None = None,
    calibration_runs: int = 10,
    seed: int | None = 42,
    backend: str = "mathematical",
) -> dict[float, HonestBaseline]:
    """Calibrate a family of independent HonestBaselines across a sequence of noise strengths.

    Each noise strength is calibrated as an isolated, independent baseline.
    Noise levels are strictly never merged or cross-contaminated.

    Args:
        noise_type: Noise channel type identifier ('bit_flip', 'phase_flip', 'depolarizing').
        probabilities: Sequence of noise parameters p in [0.0, 1.0].
        states: Sequence of state names to calibrate.
        shots: Measurement shots per trial (None for analytical).
        calibration_runs: Number of repeated runs N per noise level.
        seed: Random seed for reproducibility.
        backend: Execution backend ('mathematical' or 'aer_simulator').

    Returns:
        Dictionary mapping each noise parameter p to its calibrated HonestBaseline.
    """
    sweep_baselines: dict[float, HonestBaseline] = {}

    for p in probabilities:
        p_val = float(p)
        config_id = f"honest_baseline_{noise_type}_p{p_val:.4f}_shots{shots}"
        config = BaselineConfiguration(
            configuration_id=config_id,
            states=states,
            noise_model_type=noise_type,
            noise_strength=p_val,
            channel_location="bob_qubit",
            shots=shots,
            calibration_runs=calibration_runs,
            seed=seed,
            backend=backend,
        )

        baseline = calibrate_honest_baseline(config)
        sweep_baselines[p_val] = baseline

    return sweep_baselines

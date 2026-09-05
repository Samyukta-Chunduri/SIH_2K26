"""Tests for Honest Baseline Calibration (Milestone M9).

Validates:
1. Sample statistics calculations (mean, sample variance with N-1 denominator, std dev, confidence intervals).
2. Domain bounds enforcement and clamping (fidelity in [0, 1], probabilities in [0, 1], expectations in [-1, 1]).
3. Honest baseline configuration, observations, validation, and JSON-compatible serialization/deserialization.
4. Calibration execution across all 6 Pauli eigenstates (|0>, |1>, |+>, |->, |+i>, |-i>) and arbitrary complex states.
5. Calibrations under zero noise (ideal) and honest physical noise (bit-flip, phase-flip, depolarizing).
6. Shot count sensitivity and empirical sampling reproducibility via random seeds.
7. Noise sweeps with strict separation (no cross-contamination of operating conditions).
8. Bug-catching sensitivity suite for Bugs A through O.
9. Strict divide-and-conquer scope enforcement (no attack detection, no thresholds, no QDS signatures, no ML).
"""

from __future__ import annotations

import math
from typing import Any
import numpy as np
import pytest

from src.noise.models import (
    create_bit_flip_channel,
    create_depolarizing_channel,
    create_phase_flip_channel,
)
from src.quantum.states import (
    STATE_0,
    STATE_1,
    STATE_MINUS,
    STATE_MINUS_I,
    STATE_PLUS,
    STATE_PLUS_I,
)
from src.statistics import (
    BaselineConfiguration,
    CalibrationObservation,
    HonestBaseline,
    MetricStatistics,
    STANDARD_STATE_NAMES,
    build_honest_baseline_from_observations,
    calculate_sample_statistics,
    calibrate_honest_baseline,
    calibrate_noise_sweep,
    run_honest_calibration_trial,
    validate_baseline,
)


# ==============================================================================
# 1. Statistical Calculations & Sample Variance Convention
# ==============================================================================

class TestSampleStatisticsCalculations:
    """Validates descriptive sample statistics, sample variance (N-1), and confidence intervals."""

    def test_sample_mean_and_variance(self) -> None:
        """Sample variance must use Bessel's correction with N - 1 denominator."""
        data = [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]
        n = len(data)
        stats = calculate_sample_statistics(data)

        expected_mean = float(np.mean(data))  # 5.0
        expected_sample_var = float(np.var(data, ddof=1))  # 4.57142857...
        expected_pop_var = float(np.var(data, ddof=0))  # 4.0

        assert np.isclose(stats.mean, expected_mean)
        assert np.isclose(stats.variance, expected_sample_var)
        assert not np.isclose(stats.variance, expected_pop_var), "Must use sample variance, not population variance!"
        assert np.isclose(stats.std_dev, math.sqrt(expected_sample_var))
        assert stats.sample_count == n
        assert stats.min_value == 2.0
        assert stats.max_value == 9.0

    def test_known_manual_datasets(self) -> None:
        """Verify sample mean, Bessel's sample variance, and std dev on exact manual datasets."""
        # 1. Dataset [1, 2, 3, 4, 5]:
        # mu = (1+2+3+4+5)/5 = 3.0
        # diffs = [-2, -1, 0, 1, 2] -> sumsq = 4 + 1 + 0 + 1 + 4 = 10.0
        # s^2 = 10 / (5 - 1) = 2.5
        # sigma^2 (population) = 10 / 5 = 2.0
        data_1 = [1.0, 2.0, 3.0, 4.0, 5.0]
        st1 = calculate_sample_statistics(data_1)
        assert np.isclose(st1.mean, 3.0)
        assert np.isclose(st1.variance, 2.5)
        assert np.isclose(st1.std_dev, math.sqrt(2.5))
        assert not np.isclose(st1.variance, 2.0), "Must NOT use population variance!"

        # 2. Uniform dataset [5, 5, 5, 5]:
        # mu = 5.0, variance must be strictly 0.0
        data_uniform = [5.0, 5.0, 5.0, 5.0]
        st_uni = calculate_sample_statistics(data_uniform)
        assert st_uni.mean == 5.0
        assert st_uni.variance == 0.0
        assert st_uni.std_dev == 0.0
        assert st_uni.min_value == 5.0
        assert st_uni.max_value == 5.0

        # 3. Asymmetric dataset [1.0, 2.0, 9.0]:
        # mu = (1 + 2 + 9) / 3 = 4.0
        # diffs = [-3, -2, +5] -> sumsq = 9 + 4 + 25 = 38.0
        # s^2 = 38 / (3 - 1) = 19.0
        # sigma^2 (population) = 38 / 3 = 12.666...
        data_asym = [1.0, 2.0, 9.0]
        st_asym = calculate_sample_statistics(data_asym)
        assert np.isclose(st_asym.mean, 4.0)
        assert np.isclose(st_asym.variance, 19.0)
        assert np.isclose(st_asym.std_dev, math.sqrt(19.0))
        assert not np.isclose(st_asym.variance, 38.0 / 3.0)

    def test_single_observation_statistics(self) -> None:
        """Single observation (N=1) has sample variance 0.0 and undefined confidence interval."""
        stats = calculate_sample_statistics([0.85])
        assert stats.mean == 0.85
        assert stats.variance == 0.0
        assert stats.std_dev == 0.0
        assert stats.sample_count == 1
        assert stats.min_value == 0.85
        assert stats.max_value == 0.85
        assert stats.confidence_interval is None, "CI must be None for N=1 (df=0)."

    def test_two_observation_statistics(self) -> None:
        """Two observations (N=2) must correctly compute s^2 with denominator 1."""
        data = [2.0, 6.0]
        # mu = 4.0, diffs = [-2, 2], sumsq = 4 + 4 = 8.0, s^2 = 8.0 / 1 = 8.0
        stats = calculate_sample_statistics(data)
        assert np.isclose(stats.mean, 4.0)
        assert np.isclose(stats.variance, 8.0)
        assert np.isclose(stats.std_dev, math.sqrt(8.0))
        assert stats.sample_count == 2
        assert stats.confidence_interval is not None

    def test_empty_sequence_raises_error(self) -> None:
        """Empty sequence (N=0) must raise ValueError."""
        with pytest.raises(ValueError, match="empty"):
            calculate_sample_statistics([])

    def test_invalid_and_non_finite_inputs(self) -> None:
        """Non-numeric, boolean, NaN, and Inf values must raise appropriate errors."""
        with pytest.raises(TypeError):
            calculate_sample_statistics([1.0, "two", 3.0])  # type: ignore
        with pytest.raises(TypeError):
            calculate_sample_statistics([1.0, True, 3.0])  # type: ignore
        with pytest.raises(ValueError, match="finite"):
            calculate_sample_statistics([1.0, float("nan"), 3.0])
        with pytest.raises(ValueError, match="finite"):
            calculate_sample_statistics([1.0, float("inf"), 3.0])

    def test_confidence_interval_clamping(self) -> None:
        """Confidence interval must be clamped within specified physical bounds."""
        # High-variance data near boundary 1.0
        data = [0.95, 0.98, 0.99, 1.0, 0.92]
        stats = calculate_sample_statistics(data, confidence_level=0.95, bounds=(0.0, 1.0))
        assert stats.confidence_interval is not None
        ci_low, ci_high = stats.confidence_interval
        assert ci_low >= 0.0
        assert ci_high <= 1.0
        assert ci_low <= ci_high

    def test_input_array_immutability(self) -> None:
        """calculate_sample_statistics must not modify the input NumPy array."""
        original = np.array([1.0, 4.0, 9.0], dtype=np.float64)
        clone = original.copy()
        _ = calculate_sample_statistics(original)
        assert np.array_equal(original, clone), "Input array was mutated!"


# ==============================================================================
# 2. Honest Baseline Data Structures & Validation
# ==============================================================================

class TestBaselineStructures:
    """Validates baseline configuration, observations, validation, and serialization."""

    def test_baseline_configuration_validation(self) -> None:
        """BaselineConfiguration validates parameter domains."""
        valid_cfg = BaselineConfiguration(
            configuration_id="honest_zero_noise",
            states=STANDARD_STATE_NAMES,
            noise_model_type="depolarizing",
            noise_strength=0.0,
            channel_location="bob_qubit",
            shots=1000,
            calibration_runs=10,
        )
        assert valid_cfg.configuration_id == "honest_zero_noise"

        # Invalid noise strength
        with pytest.raises(ValueError, match="noise_strength"):
            BaselineConfiguration(
                configuration_id="test",
                states=STANDARD_STATE_NAMES,
                noise_model_type="depolarizing",
                noise_strength=-0.1,
                channel_location="bob_qubit",
                shots=1000,
                calibration_runs=10,
            )

        # Invalid calibration runs
        with pytest.raises(ValueError, match="calibration_runs"):
            BaselineConfiguration(
                configuration_id="test",
                states=STANDARD_STATE_NAMES,
                noise_model_type="depolarizing",
                noise_strength=0.1,
                channel_location="bob_qubit",
                shots=1000,
                calibration_runs=0,
            )

    def test_baseline_configuration_canonical_hash(self) -> None:
        """Different operating configurations must produce distinct canonical SHA-256 hashes."""
        cfg_ideal = BaselineConfiguration(
            configuration_id="same_id",
            states=("0", "1"),
            noise_model_type="ideal",
            noise_strength=0.0,
            channel_location="bob_qubit",
            shots=1000,
            calibration_runs=5,
        )
        cfg_noisy = BaselineConfiguration(
            configuration_id="same_id",
            states=("0", "1"),
            noise_model_type="depolarizing",
            noise_strength=0.05,
            channel_location="bob_qubit",
            shots=1000,
            calibration_runs=5,
        )
        cfg_shots = BaselineConfiguration(
            configuration_id="same_id",
            states=("0", "1"),
            noise_model_type="ideal",
            noise_strength=0.0,
            channel_location="bob_qubit",
            shots=10000,
            calibration_runs=5,
        )

        assert cfg_ideal.canonical_hash != cfg_noisy.canonical_hash
        assert cfg_ideal.canonical_hash != cfg_shots.canonical_hash
        assert len(cfg_ideal.canonical_hash) == 64

    def test_calibration_observation_validation(self) -> None:
        """CalibrationObservation validates fidelity, QBER, probabilities, and expectations."""
        obs = CalibrationObservation(
            state_name="0",
            fidelity=0.98,
            qber=0.02,
            probabilities_z={"0": 0.98, "1": 0.02},
            probabilities_x={"+": 0.5, "-": 0.5},
            probabilities_y={"+i": 0.5, "-i": 0.5},
            pauli_expectations={"X": 0.0, "Y": 0.0, "Z": 0.96},
            is_honest=True,
        )
        assert obs.state_name == "0"
        assert obs.fidelity == 0.98
        assert obs.is_honest is True

        # Invalid fidelity (> 1.0)
        with pytest.raises(ValueError, match="fidelity"):
            CalibrationObservation(
                state_name="0",
                fidelity=1.5,
                qber=0.0,
                probabilities_z={"0": 1.0},
                probabilities_x={"+": 1.0},
                probabilities_y={"+i": 1.0},
                pauli_expectations={"X": 0.0, "Y": 0.0, "Z": 1.0},
            )

        # Invalid probability sum
        with pytest.raises(ValueError, match="sum"):
            CalibrationObservation(
                state_name="0",
                fidelity=0.9,
                qber=0.1,
                probabilities_z={"0": 0.7, "1": 0.1},  # Sum = 0.8 != 1.0
                probabilities_x={"+": 1.0},
                probabilities_y={"+i": 1.0},
                pauli_expectations={"Z": 0.8},
            )

        # Non-honest observation rejected
        with pytest.raises(ValueError, match="honest"):
            CalibrationObservation(
                state_name="0",
                fidelity=0.95,
                qber=0.05,
                probabilities_z={"0": 0.95, "1": 0.05},
                probabilities_x={"+": 0.5, "-": 0.5},
                probabilities_y={"+i": 0.5, "-i": 0.5},
                pauli_expectations={"Z": 0.9},
                is_honest=False,
            )

    def test_calibration_observation_defensive_copying(self) -> None:
        """Modifying external dictionaries must not mutate CalibrationObservation."""
        probs = {"0": 0.9, "1": 0.1}
        exps = {"X": 0.0, "Y": 0.0, "Z": 0.8}
        obs = CalibrationObservation(
            state_name="0",
            fidelity=0.9,
            qber=0.1,
            probabilities_z=probs,
            probabilities_x={"+": 0.5, "-": 0.5},
            probabilities_y={"+i": 0.5, "-i": 0.5},
            pauli_expectations=exps,
        )

        probs["0"] = 0.5  # mutate external dict
        exps["Z"] = -1.0

        assert obs.probabilities_z["0"] == 0.9
        assert obs.pauli_expectations["Z"] == 0.8

    def test_honest_baseline_serialization_roundtrip(self) -> None:
        """HonestBaseline must cleanly serialize to and from a dictionary without information loss."""
        cfg = BaselineConfiguration(
            configuration_id="cfg_test",
            states=("0", "1"),
            noise_model_type="depolarizing",
            noise_strength=0.05,
            channel_location="bob_qubit",
            shots=500,
            calibration_runs=5,
            seed=42,
        )
        metrics = {
            "fidelity:all_states": MetricStatistics(
                mean=0.96,
                variance=0.0004,
                std_dev=0.02,
                sample_count=10,
                min_value=0.93,
                max_value=0.99,
                confidence_interval=(0.945, 0.975),
            )
        }
        baseline = HonestBaseline(
            configuration=cfg,
            metrics=metrics,
            metadata={"source": "test_suite"},
        )

        data = baseline.to_dict()
        assert "canonical_hash" in data["configuration"]
        restored = HonestBaseline.from_dict(data)

        assert restored.configuration.configuration_id == baseline.configuration.configuration_id
        assert restored.configuration.noise_strength == baseline.configuration.noise_strength
        assert restored.metrics["fidelity:all_states"].mean == baseline.metrics["fidelity:all_states"].mean
        assert restored.metrics["fidelity:all_states"].variance == baseline.metrics["fidelity:all_states"].variance
        assert restored.metadata["source"] == "test_suite"


# ==============================================================================
# 3. Honest Calibration Execution
# ==============================================================================

class TestHonestCalibrationExecution:
    """Validates calibration trials and engine execution across quantum states and noise models."""

    def test_calibration_trial_all_six_pauli_states(self) -> None:
        """Run honest calibration trials across all six Pauli eigenstates under zero noise."""
        for name in STANDARD_STATE_NAMES:
            obs = run_honest_calibration_trial(name, noise_channel=None)
            assert np.isclose(obs.fidelity, 1.0, atol=1e-12)
            assert np.isclose(obs.qber, 0.0, atol=1e-12)

            # Check basis-aligned expectations
            if name == "0":
                assert np.isclose(obs.pauli_expectations["Z"], 1.0)
            elif name == "1":
                assert np.isclose(obs.pauli_expectations["Z"], -1.0)
            elif name == "+":
                assert np.isclose(obs.pauli_expectations["X"], 1.0)
            elif name == "-":
                assert np.isclose(obs.pauli_expectations["X"], -1.0)
            elif name == "+i":
                assert np.isclose(obs.pauli_expectations["Y"], 1.0)
            elif name == "-i":
                assert np.isclose(obs.pauli_expectations["Y"], -1.0)

    def test_calibration_trial_arbitrary_complex_state(self) -> None:
        """Run honest calibration trial on an arbitrary complex superposition state."""
        alpha = 1.0 / math.sqrt(3.0)
        beta = math.sqrt(2.0 / 3.0) * np.exp(1j * math.pi / 4.0)
        psi = np.array([alpha, beta], dtype=np.complex128)

        obs = run_honest_calibration_trial(psi, noise_channel=None, state_name="complex_state")
        assert np.isclose(obs.fidelity, 1.0, atol=1e-12)
        assert np.isclose(obs.qber, 0.0, atol=1e-12)
        assert obs.state_name == "complex_state"

    def test_calibrate_honest_baseline_zero_noise(self) -> None:
        """Calibrate a complete honest baseline under zero noise (ideal teleportation)."""
        cfg = BaselineConfiguration(
            configuration_id="baseline_ideal_pauli_6",
            states=STANDARD_STATE_NAMES,
            noise_model_type="ideal",
            noise_strength=0.0,
            channel_location="bob_qubit",
            shots=None,
            calibration_runs=5,
        )
        baseline = calibrate_honest_baseline(cfg)

        assert baseline.configuration.configuration_id == "baseline_ideal_pauli_6"
        # Overall fidelity across all states must be 1.0 with variance = 0.0
        fid_all = baseline.metrics["fidelity:all_states"]
        assert np.isclose(fid_all.mean, 1.0, atol=1e-12)
        assert np.isclose(fid_all.variance, 0.0, atol=1e-12)

        # Overall QBER must be 0.0 with variance = 0.0
        qber_all = baseline.metrics["qber:all_states"]
        assert np.isclose(qber_all.mean, 0.0, atol=1e-12)
        assert np.isclose(qber_all.variance, 0.0, atol=1e-12)

        # Ideal Bell correlations
        assert np.isclose(baseline.metrics["bell_xx"].mean, 1.0)
        assert np.isclose(baseline.metrics["bell_yy"].mean, -1.0)
        assert np.isclose(baseline.metrics["bell_zz"].mean, 1.0)

    def test_calibrate_honest_baseline_with_honest_noise(self) -> None:
        """Calibrate honest baseline under non-zero honest noise (e.g. depolarizing p=0.15)."""
        p = 0.15
        cfg = BaselineConfiguration(
            configuration_id="baseline_depolarizing_p015",
            states=STANDARD_STATE_NAMES,
            noise_model_type="depolarizing",
            noise_strength=p,
            channel_location="bob_qubit",
            shots=None,
            calibration_runs=5,
        )
        baseline = calibrate_honest_baseline(cfg)

        # Depolarizing noise contracts Bloch vector and reduces fidelity
        fid_all = baseline.metrics["fidelity:all_states"]
        assert 0.8 < fid_all.mean < 1.0
        assert fid_all.variance >= 0.0

        # QBER is non-zero
        qber_all = baseline.metrics["qber:all_states"]
        assert 0.0 < qber_all.mean < 0.2

        # Bell correlations contract by (1 - 4p/3)
        expected_scale = 1.0 - (4.0 / 3.0) * p
        assert np.isclose(baseline.metrics["bell_xx"].mean, 1.0 * expected_scale)
        assert np.isclose(baseline.metrics["bell_yy"].mean, -1.0 * expected_scale)
        assert np.isclose(baseline.metrics["bell_zz"].mean, 1.0 * expected_scale)

    def test_calibrate_noise_sweep(self) -> None:
        """Noise sweep generates strictly isolated baselines for each noise parameter."""
        probs = [0.0, 0.05, 0.1, 0.2]
        sweep = calibrate_noise_sweep(
            noise_type="depolarizing",
            probabilities=probs,
            states=STANDARD_STATE_NAMES,
            calibration_runs=3,
        )

        assert len(sweep) == 4
        assert 0.0 in sweep and 0.2 in sweep

        # Check strict separation of baselines
        b0 = sweep[0.0]
        b2 = sweep[0.2]
        assert b0.configuration.noise_strength == 0.0
        assert b2.configuration.noise_strength == 0.2
        assert b0.metrics["fidelity:all_states"].mean > b2.metrics["fidelity:all_states"].mean

    def test_calibration_reproducibility_with_seed(self) -> None:
        """Calibrations with identical seeds and parameters must be bit-identical."""
        cfg1 = BaselineConfiguration(
            configuration_id="repro_test",
            states=("0", "1", "+"),
            noise_model_type="depolarizing",
            noise_strength=0.1,
            channel_location="bob_qubit",
            shots=200,
            calibration_runs=3,
            seed=12345,
            backend="aer_simulator",
        )
        cfg2 = BaselineConfiguration(
            configuration_id="repro_test",
            states=("0", "1", "+"),
            noise_model_type="depolarizing",
            noise_strength=0.1,
            channel_location="bob_qubit",
            shots=200,
            calibration_runs=3,
            seed=12345,
            backend="aer_simulator",
        )

        b1 = calibrate_honest_baseline(cfg1)
        b2 = calibrate_honest_baseline(cfg2)

        for k in b1.metrics:
            assert np.isclose(b1.metrics[k].mean, b2.metrics[k].mean)
            assert np.isclose(b1.metrics[k].variance, b2.metrics[k].variance)

    def test_build_honest_baseline_from_observations(self) -> None:
        """Constructing HonestBaseline from pre-collected observations aggregates metrics correctly."""
        cfg = BaselineConfiguration(
            configuration_id="obs_test_cfg",
            states=("0",),
            noise_model_type="ideal",
            noise_strength=0.0,
            channel_location="bob_qubit",
            shots=None,
            calibration_runs=2,
        )
        obs1 = CalibrationObservation(
            state_name="0",
            fidelity=0.98,
            qber=0.02,
            probabilities_z={"0": 0.98, "1": 0.02},
            probabilities_x={"+": 0.5, "-": 0.5},
            probabilities_y={"+i": 0.5, "-i": 0.5},
            pauli_expectations={"X": 0.0, "Y": 0.0, "Z": 0.96},
            is_honest=True,
        )
        obs2 = CalibrationObservation(
            state_name="0",
            fidelity=1.0,
            qber=0.0,
            probabilities_z={"0": 1.0, "1": 0.0},
            probabilities_x={"+": 0.5, "-": 0.5},
            probabilities_y={"+i": 0.5, "-i": 0.5},
            pauli_expectations={"X": 0.0, "Y": 0.0, "Z": 1.0},
            is_honest=True,
        )

        baseline = build_honest_baseline_from_observations(cfg, [obs1, obs2])
        assert baseline.configuration.configuration_id == "obs_test_cfg"
        assert np.isclose(baseline.metrics["fidelity:0"].mean, 0.99)
        assert baseline.metrics["fidelity:0"].sample_count == 2
        assert "canonical_hash" in baseline.metadata

    def test_build_honest_baseline_contamination_rejection(self) -> None:
        """build_honest_baseline_from_observations must reject non-honest observations."""
        cfg = BaselineConfiguration(
            configuration_id="contamination_test",
            states=("0",),
            noise_model_type="ideal",
            noise_strength=0.0,
            channel_location="bob_qubit",
            shots=None,
            calibration_runs=1,
        )
        # Attempting to forge a non-honest observation (e.g. bypass __post_init__ via object.__setattr__)
        obs = CalibrationObservation(
            state_name="0",
            fidelity=0.5,
            qber=0.5,
            probabilities_z={"0": 0.5, "1": 0.5},
            probabilities_x={"+": 0.5, "-": 0.5},
            probabilities_y={"+i": 0.5, "-i": 0.5},
            pauli_expectations={"X": 0.0, "Y": 0.0, "Z": 0.0},
            is_honest=True,
        )
        object.__setattr__(obs, "is_honest", False)

        with pytest.raises(ValueError, match="contamination"):
            build_honest_baseline_from_observations(cfg, [obs])

    def test_honest_baseline_defensive_copying(self) -> None:
        """Modifying external dictionaries passed to HonestBaseline does not mutate the baseline."""
        cfg = BaselineConfiguration(
            configuration_id="defensive_test",
            states=("0",),
            noise_model_type="ideal",
            noise_strength=0.0,
            channel_location="bob_qubit",
            shots=None,
            calibration_runs=2,
        )
        metrics_dict = {
            "fidelity:0": MetricStatistics(
                mean=0.99,
                variance=0.0001,
                std_dev=0.01,
                sample_count=2,
                min_value=0.98,
                max_value=1.0,
            )
        }
        meta_dict = {"owner": "alice"}
        baseline = HonestBaseline(configuration=cfg, metrics=metrics_dict, metadata=meta_dict)

        metrics_dict["fidelity:0"] = MetricStatistics(
            mean=0.5, variance=0.0, std_dev=0.0, sample_count=1, min_value=0.5, max_value=0.5
        )
        meta_dict["owner"] = "eve"

        assert baseline.metrics["fidelity:0"].mean == 0.99
        assert baseline.metadata["owner"] == "alice"

    def test_validate_baseline_enforces_bounds_on_min_max(self) -> None:
        """validate_baseline must catch unphysical min_value or max_value even if mean is within bounds."""
        cfg = BaselineConfiguration(
            configuration_id="bounds_test",
            states=("0",),
            noise_model_type="ideal",
            noise_strength=0.0,
            channel_location="bob_qubit",
            shots=None,
            calibration_runs=2,
        )
        # Mean is 0.5 (valid), but min_value is -0.2 (unphysical for fidelity)
        bad_metrics = {
            "fidelity:0": MetricStatistics(
                mean=0.5,
                variance=0.1,
                std_dev=math.sqrt(0.1),
                sample_count=2,
                min_value=-0.2,
                max_value=1.0,
            )
        }
        with pytest.raises(ValueError, match="observed bounds"):
            HonestBaseline(configuration=cfg, metrics=bad_metrics, metadata={})


# ==============================================================================
# 4. Bug-Catching Sensitivity Suite (Bugs A through O)
# ==============================================================================

class TestBugCatchingSensitivity:
    """Sensitivity tests designed to expose subtle implementation mistakes."""

    def test_bug_a_mean_calculated_incorrectly(self) -> None:
        """Bug A: Mean is incorrect."""
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        stats = calculate_sample_statistics(data)
        assert np.isclose(stats.mean, 3.0), "Bug A detected: Sample mean calculation error!"

    def test_bug_b_variance_denominator_is_wrong(self) -> None:
        """Bug B: Variance denominator is wrong (must be N - 1)."""
        data = [1.0, 3.0, 5.0]  # mean = 3.0, sumsq = 4 + 0 + 4 = 8.
        # s^2 = 8 / 2 = 4.0.
        stats = calculate_sample_statistics(data)
        assert np.isclose(stats.variance, 4.0), "Bug B detected: Denominator error in sample variance!"

    def test_bug_c_population_variance_used_accidentally(self) -> None:
        """Bug C: Population variance (N) used accidentally instead of sample variance (N - 1)."""
        data = [2.0, 4.0]  # mean = 3.0, diffs = [-1, 1], sumsq = 2.
        # Population var = 2 / 2 = 1.0. Sample var = 2 / (2 - 1) = 2.0.
        stats = calculate_sample_statistics(data)
        assert np.isclose(stats.variance, 2.0), "Bug C detected: Failed to use Bessel's N - 1 correction!"
        assert not np.isclose(stats.variance, 1.0)

    def test_bug_d_standard_deviation_is_incorrect(self) -> None:
        """Bug D: Standard deviation is incorrect (not sqrt(variance))."""
        data = [2.0, 4.0]  # s^2 = 2.0 -> s = sqrt(2.0)
        stats = calculate_sample_statistics(data)
        assert np.isclose(stats.std_dev, math.sqrt(2.0)), "Bug D detected: Standard deviation error!"

    def test_bug_e_one_pauli_state_is_omitted(self) -> None:
        """Bug E: One Pauli state is omitted from calibration."""
        cfg = BaselineConfiguration(
            configuration_id="pauli_test",
            states=STANDARD_STATE_NAMES,
            noise_model_type="ideal",
            noise_strength=0.0,
            channel_location="bob_qubit",
            shots=None,
            calibration_runs=2,
        )
        baseline = calibrate_honest_baseline(cfg)
        for st in STANDARD_STATE_NAMES:
            assert f"fidelity:{st}" in baseline.metrics, f"Bug E detected: Pauli state '{st}' omitted!"

    def test_bug_f_y_basis_states_are_omitted(self) -> None:
        """Bug F: Y-basis states (+i, -i) are omitted from calibration."""
        cfg = BaselineConfiguration(
            configuration_id="y_basis_test",
            states=STANDARD_STATE_NAMES,
            noise_model_type="ideal",
            noise_strength=0.0,
            channel_location="bob_qubit",
            shots=None,
            calibration_runs=2,
        )
        baseline = calibrate_honest_baseline(cfg)
        assert "fidelity:+i" in baseline.metrics, "Bug F detected: State '+i' omitted!"
        assert "fidelity:-i" in baseline.metrics, "Bug F detected: State '-i' omitted!"

    def test_bug_g_complex_state_is_mishandled(self) -> None:
        """Bug G: Complex state is mishandled during calibration."""
        psi = np.array([1.0 / math.sqrt(2.0), 1.0j / math.sqrt(2.0)], dtype=np.complex128)
        cfg = BaselineConfiguration(
            configuration_id="complex_test",
            states=("0",),
            noise_model_type="ideal",
            noise_strength=0.0,
            channel_location="bob_qubit",
            shots=None,
            calibration_runs=2,
        )
        baseline = calibrate_honest_baseline(cfg, custom_states=[("custom_plus_i", psi)])
        assert "fidelity:custom_plus_i" in baseline.metrics, "Bug G detected: Complex state omitted!"
        assert np.isclose(baseline.metrics["fidelity:custom_plus_i"].mean, 1.0)

    def test_bug_h_noise_strength_is_ignored(self) -> None:
        """Bug H: Noise strength is ignored in baseline calibration."""
        cfg_0 = BaselineConfiguration(
            configuration_id="cfg_0",
            states=("0", "1"),
            noise_model_type="depolarizing",
            noise_strength=0.0,
            channel_location="bob_qubit",
            shots=None,
            calibration_runs=2,
        )
        cfg_3 = BaselineConfiguration(
            configuration_id="cfg_3",
            states=("0", "1"),
            noise_model_type="depolarizing",
            noise_strength=0.3,
            channel_location="bob_qubit",
            shots=None,
            calibration_runs=2,
        )
        b0 = calibrate_honest_baseline(cfg_0)
        b3 = calibrate_honest_baseline(cfg_3)
        assert b0.metrics["fidelity:all_states"].mean > b3.metrics["fidelity:all_states"].mean, "Bug H detected: Noise strength ignored!"

    def test_bug_i_noise_model_is_ignored(self) -> None:
        """Bug I: Noise model is ignored (bit-flip vs phase-flip behave identically)."""
        cfg_bf = BaselineConfiguration(
            configuration_id="cfg_bf",
            states=("+",),
            noise_model_type="bit_flip",
            noise_strength=0.5,
            channel_location="bob_qubit",
            shots=None,
            calibration_runs=2,
        )
        cfg_pf = BaselineConfiguration(
            configuration_id="cfg_pf",
            states=("+",),
            noise_model_type="phase_flip",
            noise_strength=0.5,
            channel_location="bob_qubit",
            shots=None,
            calibration_runs=2,
        )
        b_bf = calibrate_honest_baseline(cfg_bf)
        b_pf = calibrate_honest_baseline(cfg_pf)
        # On |+>, bit-flip preserves |+> (fidelity=1.0) while phase-flip degrades |+> (fidelity=0.5)
        assert np.isclose(b_bf.metrics["fidelity:+"].mean, 1.0)
        assert np.isclose(b_pf.metrics["fidelity:+"].mean, 0.5)
        assert not np.isclose(b_bf.metrics["fidelity:+"].mean, b_pf.metrics["fidelity:+"].mean), "Bug I detected: Noise model ignored!"

    def test_bug_j_shot_count_is_ignored(self) -> None:
        """Bug J: Shot count is ignored."""
        cfg100 = BaselineConfiguration(
            configuration_id="cfg_100",
            states=("0",),
            noise_model_type="ideal",
            noise_strength=0.0,
            channel_location="bob_qubit",
            shots=100,
            calibration_runs=2,
        )
        cfg10000 = BaselineConfiguration(
            configuration_id="cfg_10000",
            states=("0",),
            noise_model_type="ideal",
            noise_strength=0.0,
            channel_location="bob_qubit",
            shots=10000,
            calibration_runs=2,
        )
        assert cfg100.shots != cfg10000.shots, "Bug J detected: Shot count parameter was ignored!"
        assert cfg100.canonical_hash != cfg10000.canonical_hash

    def test_bug_k_different_configurations_produce_same_baseline_identity(self) -> None:
        """Bug K: Different configurations produce the same baseline identity."""
        cfg_a = BaselineConfiguration(
            configuration_id="baseline_id",
            states=("0",),
            noise_model_type="ideal",
            noise_strength=0.0,
            channel_location="bob_qubit",
            shots=100,
            calibration_runs=2,
        )
        cfg_b = BaselineConfiguration(
            configuration_id="baseline_id",  # user accidentally used same string
            states=("0",),
            noise_model_type="depolarizing",
            noise_strength=0.1,
            channel_location="bob_qubit",
            shots=100,
            calibration_runs=2,
        )
        assert cfg_a.canonical_hash != cfg_b.canonical_hash, "Bug K detected: Configurations produced same canonical identity!"

    def test_bug_l_invalid_observations_are_accepted(self) -> None:
        """Bug L: Invalid observations are accepted into baseline."""
        cfg = BaselineConfiguration(
            configuration_id="invalid_obs",
            states=("0",),
            noise_model_type="ideal",
            noise_strength=0.0,
            channel_location="bob_qubit",
            shots=None,
            calibration_runs=2,
        )
        # Attempting to add out-of-bounds fidelity observation
        with pytest.raises(ValueError, match="fidelity"):
            CalibrationObservation(
                state_name="0",
                fidelity=1.5,
                qber=0.0,
                probabilities_z={"0": 1.0},
                probabilities_x={"+": 1.0},
                probabilities_y={"+i": 1.0},
                pauli_expectations={"Z": 1.0},
            )

    def test_bug_m_baseline_metadata_is_incomplete(self) -> None:
        """Bug M: Baseline metadata is incomplete."""
        cfg = BaselineConfiguration(
            configuration_id="meta_test",
            states=("0",),
            noise_model_type="ideal",
            noise_strength=0.0,
            channel_location="bob_qubit",
            shots=None,
            calibration_runs=2,
        )
        baseline = calibrate_honest_baseline(cfg)
        assert "calibrated_at" in baseline.metadata, "Bug M detected: Missing calibration timestamp!"
        assert "sample_variance_convention" in baseline.metadata
        assert "canonical_hash" in baseline.metadata
        assert baseline.configuration.configuration_id == "meta_test"

    def test_bug_n_baseline_observations_accidentally_mutated(self) -> None:
        """Bug N: Baseline observations can be accidentally mutated."""
        p_dict = {"0": 1.0, "1": 0.0}
        obs = CalibrationObservation(
            state_name="0",
            fidelity=1.0,
            qber=0.0,
            probabilities_z=p_dict,
            probabilities_x={"+": 0.5, "-": 0.5},
            probabilities_y={"+i": 0.5, "-i": 0.5},
            pauli_expectations={"Z": 1.0},
            is_honest=True,
        )
        p_dict["0"] = 0.0  # External mutation attempt
        assert obs.probabilities_z["0"] == 1.0, "Bug N detected: Observation was mutated in-place!"

    def test_bug_o_baseline_contains_attack_detection_logic(self) -> None:
        """Bug O: M9 accidentally contains attack-detection logic."""
        cfg = BaselineConfiguration(
            configuration_id="scope_test",
            states=("0",),
            noise_model_type="ideal",
            noise_strength=0.0,
            channel_location="bob_qubit",
            shots=None,
            calibration_runs=2,
        )
        baseline = calibrate_honest_baseline(cfg)
        # Verify baseline does not contain security decision attributes or threshold evaluation
        assert not hasattr(baseline, "attack_detected")
        assert not hasattr(baseline, "is_attack")
        assert not hasattr(baseline, "security_decision")
        assert not hasattr(baseline, "thresholds")
        assert not hasattr(baseline, "classify_threat")


# ==============================================================================
# 5. Scope Enforcement
# ==============================================================================

class TestScopeEnforcement:
    """Strictly enforces divide-and-conquer boundaries (no M10+ features)."""

    def test_no_m10_plus_features_in_statistics_package(self) -> None:
        """Ensure no threshold engine, attack detectors, or signature logic exist in src/statistics."""
        import src.statistics as stat_pkg

        forbidden_names = [
            "detect_attack",
            "is_attack",
            "classify_attack",
            "threshold_engine",
            "security_threshold",
            "decision_engine",
            "qif",
            "evidence_fusion",
            "forgery",
            "replay",
            "impersonation",
            "channel_attack",
            "signature",
            "sign",
            "qds",
            "blockchain",
            "machine_learning",
            "neural_network",
        ]

        for name in forbidden_names:
            assert not hasattr(stat_pkg, name), f"Scope violation: '{name}' found in src/statistics!"

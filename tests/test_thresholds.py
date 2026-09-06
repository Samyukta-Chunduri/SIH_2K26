"""Comprehensive Test Suite for Milestone M11 — Statistical Threshold Policy.

Validates:
    1. Threshold construction, empirical quantile, and statistical multiplier methods.
    2. Input validation, domain constraints, and error handling.
    3. Exact boundary conventions, tolerances, and signed margins.
    4. Strict configuration binding to baseline canonical hashes.
    5. Baseline and policy immutability, data contamination prevention.
    6. Small-sample handling (N=0, N=1 rejected; N>=2 handled).
    7. Bounded metric handling (fidelity, QBER, TVD, Pauli deviations).
    8. Sensitivity analysis across significance levels alpha.
    9. False-alarm rate estimation and data leakage prevention.
    10. Bug sensitivity suite (Bugs A through X from Milestone M11 specification).
    11. Quantum end-to-end integration: state prep -> teleportation -> noise -> baseline -> policy -> evaluation.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError, asdict
import math
from typing import Any
import numpy as np
import pytest

from src.noise.models import create_depolarizing_channel, create_phase_flip_channel
from src.quantum.states import get_standard_state, validate_state_vector
from src.statistics import (
    BaselineConfiguration,
    CalibrationObservation,
    ConfigurationCompatibilityError,
    HonestBaseline,
    MetricThreshold,
    MetricThresholdEvaluation,
    PolicyEvaluationReport,
    StatisticalEvidence,
    ThresholdDirection,
    ThresholdMethod,
    ThresholdPolicy,
    VerificationObservation,
    calculate_empirical_quantile_threshold,
    calculate_policy_fingerprint,
    calculate_statistical_multiplier_threshold,
    calibrate_honest_baseline,
    calibrate_metric_threshold,
    calibrate_threshold_policy,
    compare_observation,
    evaluate_metric_threshold,
    evaluate_policy,
    evaluate_policy_false_alarm_rate,
    resolve_metric_direction,
    run_honest_calibration_trial,
)


# ==============================================================================
# Fixtures
# ==============================================================================

@pytest.fixture
def sample_baseline_config() -> BaselineConfiguration:
    return BaselineConfiguration(
        configuration_id="m11_test_config",
        states=("0", "1"),
        noise_model_type="depolarizing",
        noise_strength=0.03,
        channel_location="bob_qubit",
        shots=None,
        calibration_runs=5,
    )


@pytest.fixture
def sample_honest_baseline(sample_baseline_config: BaselineConfiguration) -> HonestBaseline:
    return calibrate_honest_baseline(sample_baseline_config)


@pytest.fixture
def sample_calibration_observations() -> list[CalibrationObservation]:
    """Generates synthetic honest calibration observations for state '0'."""
    noise = create_depolarizing_channel(0.03)
    obs_list: list[CalibrationObservation] = []
    # Run repeated honest trials
    for s_idx in range(6):
        obs = run_honest_calibration_trial(
            state="0",
            noise_channel=noise,
            seed=1000 + s_idx,
        )
        obs_list.append(obs)
    return obs_list


# ==============================================================================
# 1. Threshold Construction & Methods
# ==============================================================================

class TestThresholdConstruction:
    """Verifies empirical quantile and statistical multiplier threshold calculations."""

    def test_empirical_quantile_lower_threshold(self) -> None:
        """For LOWER-tail metrics (e.g. fidelity), threshold is alpha-quantile."""
        samples = [0.98, 0.97, 0.99, 0.96, 0.95, 0.94]
        alpha = 0.10
        # Expected 10th percentile: numpy linear interpolation
        expected = float(np.quantile(samples, alpha, method="linear"))
        t = calculate_empirical_quantile_threshold(
            samples, direction=ThresholdDirection.LOWER, alpha=alpha, metric_name="fidelity:0"
        )
        assert math.isclose(t, expected, abs_tol=1e-12)

    def test_empirical_quantile_upper_threshold(self) -> None:
        """For UPPER-tail metrics (e.g. QBER), threshold is (1 - alpha)-quantile."""
        samples = [0.01, 0.02, 0.03, 0.04, 0.05, 0.06]
        alpha = 0.05
        # Expected 95th percentile
        expected = float(np.quantile(samples, 1.0 - alpha, method="linear"))
        t = calculate_empirical_quantile_threshold(
            samples, direction=ThresholdDirection.UPPER, alpha=alpha, metric_name="qber:0"
        )
        assert math.isclose(t, expected, abs_tol=1e-12)

    def test_statistical_multiplier_lower_threshold(self) -> None:
        """For LOWER-tail metrics, threshold is mean - k * std_dev."""
        mean = 0.95
        std_dev = 0.02
        k = 2.5
        expected = mean - k * std_dev
        t = calculate_statistical_multiplier_threshold(
            mean=mean, std_dev=std_dev, direction=ThresholdDirection.LOWER, multiplier=k, metric_name="fidelity:0"
        )
        assert math.isclose(t, expected, abs_tol=1e-12)

    def test_statistical_multiplier_upper_threshold(self) -> None:
        """For UPPER-tail metrics, threshold is mean + k * std_dev."""
        mean = 0.05
        std_dev = 0.01
        k = 3.0
        expected = mean + k * std_dev
        t = calculate_statistical_multiplier_threshold(
            mean=mean, std_dev=std_dev, direction=ThresholdDirection.UPPER, multiplier=k, metric_name="qber:0"
        )
        assert math.isclose(t, expected, abs_tol=1e-12)

    def test_policy_fingerprint_determinism(self) -> None:
        """Policy fingerprint is a deterministic SHA-256 hash invariant to dictionary key insertion order."""
        th1 = MetricThreshold("fidelity:0", ThresholdDirection.LOWER, ThresholdMethod.EMPIRICAL_QUANTILE, 0.94, alpha=0.05, sample_count=5)
        th2 = MetricThreshold("qber:0", ThresholdDirection.UPPER, ThresholdMethod.EMPIRICAL_QUANTILE, 0.06, alpha=0.05, sample_count=5)

        fp_a = calculate_policy_fingerprint("pol_1", "hash_123", {"fidelity:0": th1, "qber:0": th2})
        fp_b = calculate_policy_fingerprint("pol_1", "hash_123", {"qber:0": th2, "fidelity:0": th1})
        assert fp_a == fp_b
        assert len(fp_a) == 64

    def test_threshold_policy_to_dict_serialization(self) -> None:
        """ThresholdPolicy serializes cleanly to a dictionary."""
        th = MetricThreshold("fidelity:0", ThresholdDirection.LOWER, ThresholdMethod.EMPIRICAL_QUANTILE, 0.95, alpha=0.05, sample_count=5)
        policy = ThresholdPolicy(
            policy_id="test_serialize",
            baseline_configuration_hash="abc123hash",
            thresholds={"fidelity:0": th},
            alpha=0.05,
        )
        d = policy.to_dict()
        assert d["policy_id"] == "test_serialize"
        assert d["baseline_configuration_hash"] == "abc123hash"
        assert "fidelity:0" in d["thresholds"]
        assert d["thresholds"]["fidelity:0"]["threshold_value"] == 0.95


# ==============================================================================
# 2. Input Validation & Error Handling
# ==============================================================================

class TestInputValidation:
    """Validates rigorous input rejection for invalid parameters and types."""

    @pytest.mark.parametrize("invalid_alpha", [-0.1, 0.0, 1.0, 1.5, float("nan"), float("inf")])
    def test_invalid_alpha_rejected(self, invalid_alpha: float) -> None:
        """Alpha outside (0, 1) or non-finite raises ValueError."""
        with pytest.raises(ValueError, match="alpha"):
            calculate_empirical_quantile_threshold([0.9, 0.95], ThresholdDirection.LOWER, invalid_alpha)

    def test_empty_samples_rejected(self) -> None:
        """Empty calibration samples raises ValueError."""
        with pytest.raises(ValueError, match="empty"):
            calculate_empirical_quantile_threshold([], ThresholdDirection.LOWER, 0.05)

    def test_single_sample_rejected(self) -> None:
        """N=1 calibration samples is rejected as statistically insufficient."""
        with pytest.raises(ValueError, match="Insufficient"):
            calculate_empirical_quantile_threshold([0.95], ThresholdDirection.LOWER, 0.05)

    def test_non_finite_sample_rejected(self) -> None:
        """Samples containing NaN or inf are strictly rejected."""
        with pytest.raises(ValueError, match="finite"):
            calculate_empirical_quantile_threshold([0.95, float("nan"), 0.97], ThresholdDirection.LOWER, 0.05)

    def test_negative_multiplier_rejected(self) -> None:
        """Negative multiplier k < 0 raises ValueError."""
        with pytest.raises(ValueError, match="multiplier"):
            calculate_statistical_multiplier_threshold(0.9, 0.05, ThresholdDirection.LOWER, multiplier=-1.0)

    def test_invalid_direction_string_rejected(self) -> None:
        """Unrecognized direction string raises ValueError."""
        with pytest.raises(ValueError, match="direction"):
            MetricThreshold("test", "sideways", ThresholdMethod.EMPIRICAL_QUANTILE, 0.5)  # type: ignore

    def test_empty_metric_name_rejected(self) -> None:
        """Empty metric name raises ValueError."""
        with pytest.raises(ValueError, match="metric_name"):
            MetricThreshold("", ThresholdDirection.LOWER, ThresholdMethod.EMPIRICAL_QUANTILE, 0.5)

    def test_empty_policy_id_rejected(self) -> None:
        """Empty policy_id raises ValueError."""
        th = MetricThreshold("test", ThresholdDirection.LOWER, ThresholdMethod.EMPIRICAL_QUANTILE, 0.5)
        with pytest.raises(ValueError, match="policy_id"):
            ThresholdPolicy("", "hash123", {"test": th})


# ==============================================================================
# 3. Exact Boundary Conventions & Signed Margins
# ==============================================================================

class TestBoundaryConventions:
    """Verifies exact behavior strictly inside, strictly outside, and within atol of thresholds."""

    def test_upper_threshold_boundary_behavior(self) -> None:
        """UPPER threshold: crossed when observed > threshold + atol."""
        th = MetricThreshold("qber:0", ThresholdDirection.UPPER, ThresholdMethod.EMPIRICAL_QUANTILE, 0.05)
        tol = 1e-9

        # Case 1: Strictly inside (observed < threshold - atol)
        ev_inside = evaluate_metric_threshold(0.04, th, atol=tol)
        assert ev_inside.exceeded is False
        assert ev_inside.boundary_status == "strictly_inside"
        assert ev_inside.margin < 0.0

        # Case 2: At boundary within tolerance
        ev_at_bound = evaluate_metric_threshold(0.05 + 1e-12, th, atol=tol)
        assert ev_at_bound.exceeded is False
        assert ev_at_bound.boundary_status == "at_boundary"

        # Case 3: Strictly exceeded (observed > threshold + atol)
        ev_exceeded = evaluate_metric_threshold(0.06, th, atol=tol)
        assert ev_exceeded.exceeded is True
        assert ev_exceeded.boundary_status == "strictly_exceeded"
        assert ev_exceeded.margin > 0.0
        assert math.isclose(ev_exceeded.margin, 0.01, abs_tol=1e-12)

    def test_lower_threshold_boundary_behavior(self) -> None:
        """LOWER threshold: crossed when observed < threshold - atol."""
        th = MetricThreshold("fidelity:0", ThresholdDirection.LOWER, ThresholdMethod.EMPIRICAL_QUANTILE, 0.95)
        tol = 1e-9

        # Case 1: Strictly inside (observed > threshold + atol)
        ev_inside = evaluate_metric_threshold(0.98, th, atol=tol)
        assert ev_inside.exceeded is False
        assert ev_inside.boundary_status == "strictly_inside"
        assert ev_inside.margin < 0.0

        # Case 2: At boundary within tolerance
        ev_at_bound = evaluate_metric_threshold(0.95 - 1e-12, th, atol=tol)
        assert ev_at_bound.exceeded is False
        assert ev_at_bound.boundary_status == "at_boundary"

        # Case 3: Strictly exceeded (observed < threshold - atol)
        ev_exceeded = evaluate_metric_threshold(0.91, th, atol=tol)
        assert ev_exceeded.exceeded is True
        assert ev_exceeded.boundary_status == "strictly_exceeded"
        assert ev_exceeded.margin > 0.0
        assert math.isclose(ev_exceeded.margin, 0.04, abs_tol=1e-12)

    def test_signed_margin_and_distance(self) -> None:
        """Margin is positive when exceeded; signed_distance preserves raw x - T."""
        th_lower = MetricThreshold("fidelity:0", ThresholdDirection.LOWER, ThresholdMethod.EMPIRICAL_QUANTILE, 0.95)
        ev = evaluate_metric_threshold(0.90, th_lower)
        # Observed 0.90 < 0.95 => exceeded
        assert ev.exceeded is True
        assert ev.margin == pytest.approx(0.05)
        assert ev.signed_distance == pytest.approx(-0.05)


# ==============================================================================
# 4. Configuration Compatibility
# ==============================================================================

class TestConfigurationCompatibility:
    """Verifies strict isolation across differing operating environments."""

    def test_matching_configuration_evaluates_cleanly(
        self,
        sample_honest_baseline: HonestBaseline,
        sample_calibration_observations: list[CalibrationObservation],
        sample_baseline_config: BaselineConfiguration,
    ) -> None:
        """Observation with matching configuration evaluates successfully."""
        policy = calibrate_threshold_policy(sample_honest_baseline, sample_calibration_observations)
        trial = sample_calibration_observations[0]
        obs = VerificationObservation.from_calibration_observation(trial, configuration=sample_baseline_config)

        report = evaluate_policy(obs, policy, strict_hash=True)
        assert isinstance(report, PolicyEvaluationReport)
        assert report.policy_id == policy.policy_id
        assert report.total_metrics_evaluated > 0

    def test_mismatched_configuration_hash_rejected(
        self,
        sample_honest_baseline: HonestBaseline,
        sample_calibration_observations: list[CalibrationObservation],
    ) -> None:
        """Observation with mismatched configuration hash raises ConfigurationCompatibilityError."""
        policy = calibrate_threshold_policy(sample_honest_baseline, sample_calibration_observations)
        mismatched_cfg = BaselineConfiguration(
            configuration_id="diff_noise_config",
            states=("0", "1"),
            noise_model_type="depolarizing",
            noise_strength=0.15,  # Mismatched p
            channel_location="bob_qubit",
            shots=None,
            calibration_runs=5,
        )
        trial = sample_calibration_observations[0]
        obs_mismatched = VerificationObservation.from_calibration_observation(trial, configuration=mismatched_cfg)

        with pytest.raises(ConfigurationCompatibilityError, match="hash mismatch"):
            evaluate_policy(obs_mismatched, policy, strict_hash=True)


# ==============================================================================
# 5. Baseline Immutability & Separation
# ==============================================================================

class TestBaselineImmutability:
    """Verifies that threshold policy calibration and evaluation never mutate baselines or observations."""

    def test_baseline_unmutated_by_policy_calibration(
        self,
        sample_honest_baseline: HonestBaseline,
        sample_calibration_observations: list[CalibrationObservation],
    ) -> None:
        """HonestBaseline metrics and configuration hash remain strictly unchanged."""
        initial_hash = sample_honest_baseline.configuration.canonical_hash
        initial_metrics = {k: asdict(v) for k, v in sample_honest_baseline.metrics.items()}

        policy = calibrate_threshold_policy(sample_honest_baseline, sample_calibration_observations)
        assert isinstance(policy, ThresholdPolicy)

        assert sample_honest_baseline.configuration.canonical_hash == initial_hash
        assert {k: asdict(v) for k, v in sample_honest_baseline.metrics.items()} == initial_metrics

    def test_policy_dataclass_frozen(
        self,
        sample_honest_baseline: HonestBaseline,
        sample_calibration_observations: list[CalibrationObservation],
    ) -> None:
        """ThresholdPolicy and MetricThreshold cannot be modified after instantiation."""
        policy = calibrate_threshold_policy(sample_honest_baseline, sample_calibration_observations)
        with pytest.raises(FrozenInstanceError):
            policy.policy_id = "new_id"  # type: ignore

        th = policy.thresholds["fidelity:0"]
        with pytest.raises(FrozenInstanceError):
            th.threshold_value = 0.0  # type: ignore


# ==============================================================================
# 6. Small Sample Handling
# ==============================================================================

class TestSmallSampleHandling:
    """Verifies explicit handling of small sample sizes N."""

    def test_n_equals_zero_rejected(self, sample_honest_baseline: HonestBaseline) -> None:
        """Empty observations sequence raises ValueError."""
        with pytest.raises(ValueError, match="empty"):
            calibrate_threshold_policy(sample_honest_baseline, [])

    def test_n_equals_one_rejected(self, sample_honest_baseline: HonestBaseline) -> None:
        """Single observation is rejected as statistically insufficient."""
        single_obs = run_honest_calibration_trial("0")
        with pytest.raises(ValueError, match="Insufficient"):
            calibrate_threshold_policy(sample_honest_baseline, [single_obs])

    def test_n_equals_two_minimum_accepted(self, sample_honest_baseline: HonestBaseline) -> None:
        """N=2 is the minimal acceptable sample count for statistical calibration."""
        obs1 = run_honest_calibration_trial("0", seed=101)
        obs2 = run_honest_calibration_trial("0", seed=102)
        policy = calibrate_threshold_policy(sample_honest_baseline, [obs1, obs2])
        assert policy.calibration_sample_count == 2
        assert "fidelity:0" in policy.thresholds


# ==============================================================================
# 7. Bounded Metrics & Directions
# ==============================================================================

class TestBoundedMetrics:
    """Verifies that thresholds for physically bounded metrics respect physical domains."""

    def test_fidelity_lower_bound_clamping(self) -> None:
        """Statistical multiplier on fidelity never produces negative threshold."""
        # Mean 0.05, std_dev 0.10 with k=2 would give -0.15; clamped to 0.0
        t = calculate_statistical_multiplier_threshold(
            mean=0.05, std_dev=0.10, direction=ThresholdDirection.LOWER, multiplier=2.0, metric_name="fidelity:0"
        )
        assert t >= 0.0

    def test_qber_upper_bound_clamping(self) -> None:
        """Statistical multiplier on QBER never exceeds 1.0."""
        # Mean 0.90, std_dev 0.10 with k=2 would give 1.10; clamped to 1.0
        t = calculate_statistical_multiplier_threshold(
            mean=0.90, std_dev=0.10, direction=ThresholdDirection.UPPER, multiplier=2.0, metric_name="qber:0"
        )
        assert t <= 1.0

    def test_resolve_metric_direction(self) -> None:
        """Direction is properly resolved based on physical degradation semantics."""
        assert resolve_metric_direction("fidelity:0") == ThresholdDirection.LOWER
        assert resolve_metric_direction("qber:0") == ThresholdDirection.UPPER
        assert resolve_metric_direction("probabilities_z:0") == ThresholdDirection.UPPER
        assert resolve_metric_direction("pauli_x:0") == ThresholdDirection.UPPER


# ==============================================================================
# 8. Sensitivity Analysis
# ==============================================================================

class TestSensitivityAnalysis:
    """Verifies threshold sensitivity across differing alpha significance levels."""

    def test_alpha_sensitivity_monotonicity(self) -> None:
        """For LOWER threshold, higher alpha produces a higher (stricter) threshold."""
        samples = [0.90, 0.92, 0.93, 0.95, 0.96, 0.98, 0.99]
        t_alpha_01 = calculate_empirical_quantile_threshold(samples, ThresholdDirection.LOWER, alpha=0.01)
        t_alpha_05 = calculate_empirical_quantile_threshold(samples, ThresholdDirection.LOWER, alpha=0.05)
        t_alpha_10 = calculate_empirical_quantile_threshold(samples, ThresholdDirection.LOWER, alpha=0.10)

        # Monotonic: lower alpha is more lenient (smaller threshold for fidelity)
        assert t_alpha_01 <= t_alpha_05 <= t_alpha_10

    def test_alpha_sensitivity_upper_tail(self) -> None:
        """For UPPER threshold, higher alpha produces a lower (stricter) threshold."""
        samples = [0.01, 0.02, 0.04, 0.05, 0.07, 0.08, 0.10]
        t_alpha_01 = calculate_empirical_quantile_threshold(samples, ThresholdDirection.UPPER, alpha=0.01)
        t_alpha_05 = calculate_empirical_quantile_threshold(samples, ThresholdDirection.UPPER, alpha=0.05)
        t_alpha_10 = calculate_empirical_quantile_threshold(samples, ThresholdDirection.UPPER, alpha=0.10)

        # Monotonic: lower alpha is more lenient (higher threshold for QBER)
        assert t_alpha_01 >= t_alpha_05 >= t_alpha_10


# ==============================================================================
# 9. False-Alarm Rate Estimation & Data Leakage Prevention
# ==============================================================================

class TestFalseAlarmRateEvaluation:
    """Verifies empirical false-alarm rate calibration and data leakage checks."""

    def test_data_leakage_detection(
        self,
        sample_honest_baseline: HonestBaseline,
        sample_calibration_observations: list[CalibrationObservation],
    ) -> None:
        """Passing identical calibration observations to validation raises ValueError."""
        policy = calibrate_threshold_policy(sample_honest_baseline, sample_calibration_observations)
        with pytest.raises(ValueError, match="Data leakage"):
            evaluate_policy_false_alarm_rate(
                validation_observations=sample_calibration_observations,
                policy=policy,
                calibration_observations=sample_calibration_observations,
            )

    def test_far_estimation_on_held_out_validation(
        self,
        sample_honest_baseline: HonestBaseline,
        sample_calibration_observations: list[CalibrationObservation],
    ) -> None:
        """Evaluating on separate held-out validation trials calculates empirical exceedance rate."""
        policy = calibrate_threshold_policy(sample_honest_baseline, sample_calibration_observations, alpha=0.10)

        # Separate held-out validation observations
        noise = create_depolarizing_channel(0.03)
        val_obs = [run_honest_calibration_trial("0", noise_channel=noise, seed=2000 + i) for i in range(10)]

        far_report = evaluate_policy_false_alarm_rate(
            validation_observations=val_obs,
            policy=policy,
            calibration_observations=sample_calibration_observations,
        )
        assert "empirical_false_alarm_rate" in far_report
        assert 0.0 <= far_report["empirical_false_alarm_rate"] <= 1.0
        assert far_report["validation_sample_count"] == 10


# ==============================================================================
# 10. Bug Sensitivity Suite (Bugs A through X)
# ==============================================================================

class TestBugSensitivitySuite:
    """Explicit tests designed to catch Bugs A through X from Milestone M11 specification."""

    def test_bug_a_direction_reversed(self) -> None:
        """Bug A: Upper/lower threshold direction must not be accidentally reversed."""
        th_lower = MetricThreshold("fidelity:0", ThresholdDirection.LOWER, ThresholdMethod.EMPIRICAL_QUANTILE, 0.95)
        th_upper = MetricThreshold("qber:0", ThresholdDirection.UPPER, ThresholdMethod.EMPIRICAL_QUANTILE, 0.05)

        # Observed fidelity 0.90 is below 0.95 => LOWER threshold crossed
        assert evaluate_metric_threshold(0.90, th_lower).exceeded is True
        # Observed fidelity 0.98 is above 0.95 => LOWER threshold NOT crossed
        assert evaluate_metric_threshold(0.98, th_lower).exceeded is False

        # Observed QBER 0.08 is above 0.05 => UPPER threshold crossed
        assert evaluate_metric_threshold(0.08, th_upper).exceeded is True
        # Observed QBER 0.02 is below 0.05 => UPPER threshold NOT crossed
        assert evaluate_metric_threshold(0.02, th_upper).exceeded is False

    def test_bug_b_malformed_observation_rejected(self, sample_honest_baseline: HonestBaseline) -> None:
        """Bug B: Attacked or malformed observations missing proper typing are rejected."""
        with pytest.raises(TypeError):
            calibrate_threshold_policy(sample_honest_baseline, [{"state_name": "0", "fidelity": 0.5}])  # type: ignore

    def test_bug_c_incompatible_configuration_rejected(
        self,
        sample_honest_baseline: HonestBaseline,
        sample_calibration_observations: list[CalibrationObservation],
    ) -> None:
        """Bug C: Threshold policy cannot be silently reused across mismatched configurations."""
        policy = calibrate_threshold_policy(sample_honest_baseline, sample_calibration_observations)
        bad_cfg = BaselineConfiguration(
            configuration_id="incompat",
            states=("0",),
            noise_model_type="phase_flip",  # Mismatched noise type
            noise_strength=0.03,
            channel_location="bob_qubit",
            shots=None,
            calibration_runs=5,
        )
        trial = sample_calibration_observations[0]
        obs = VerificationObservation.from_calibration_observation(trial, configuration=bad_cfg)
        with pytest.raises(ConfigurationCompatibilityError):
            evaluate_policy(obs, policy, strict_hash=True)

    def test_bug_d_no_recalibration_during_evaluation(
        self,
        sample_honest_baseline: HonestBaseline,
        sample_calibration_observations: list[CalibrationObservation],
    ) -> None:
        """Bug D: Evaluating an observation cannot alter the threshold policy."""
        policy = calibrate_threshold_policy(sample_honest_baseline, sample_calibration_observations)
        orig_fp = policy.policy_fingerprint
        orig_val = policy.thresholds["fidelity:0"].threshold_value

        # Evaluate several observations with severe degradation
        trial = sample_calibration_observations[0]
        anomalous_obs = VerificationObservation(
            state_name="0",
            fidelity=0.40,
            qber=0.60,
            probabilities_z={"0": 0.40, "1": 0.60},
            probabilities_x={"+": 0.5, "-": 0.5},
            probabilities_y={"+i": 0.5, "-i": 0.5},
            pauli_expectations={"X": 0.0, "Y": 0.0, "Z": -0.2},
            configuration=sample_honest_baseline.configuration,
        )
        for _ in range(5):
            evaluate_policy(anomalous_obs, policy, strict_hash=True)

        assert policy.policy_fingerprint == orig_fp
        assert policy.thresholds["fidelity:0"].threshold_value == orig_val

    def test_bug_g_nan_threshold_rejected(self) -> None:
        """Bug G: NaN threshold value cannot be instantiated."""
        with pytest.raises(ValueError, match="finite"):
            MetricThreshold("test", ThresholdDirection.LOWER, ThresholdMethod.FIXED_BOUND, float("nan"))

    def test_bug_h_infinite_threshold_rejected(self) -> None:
        """Bug H: Infinite threshold value cannot be instantiated."""
        with pytest.raises(ValueError, match="finite"):
            MetricThreshold("test", ThresholdDirection.LOWER, ThresholdMethod.FIXED_BOUND, float("inf"))

    def test_bug_i_invalid_alpha_not_silently_clipped(self) -> None:
        """Bug I: Alpha <= 0 or >= 1 must raise ValueError, not be silently clipped."""
        with pytest.raises(ValueError):
            calculate_empirical_quantile_threshold([0.9, 0.95], ThresholdDirection.LOWER, alpha=-0.05)
        with pytest.raises(ValueError):
            calculate_empirical_quantile_threshold([0.9, 0.95], ThresholdDirection.LOWER, alpha=1.05)

    def test_bug_j_quantile_direction(self) -> None:
        """Bug J: Upper quantile must be 1 - alpha, not alpha."""
        samples = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        # For alpha = 0.10, upper quantile is 90th percentile = 9.1
        t_upper = calculate_empirical_quantile_threshold(samples, ThresholdDirection.UPPER, alpha=0.10)
        assert t_upper > 8.0
        # Lower quantile is 10th percentile = 1.9
        t_lower = calculate_empirical_quantile_threshold(samples, ThresholdDirection.LOWER, alpha=0.10)
        assert t_lower < 3.0

    def test_bug_k_boundary_equality(self) -> None:
        """Bug K: Values within atol are marked at_boundary and not exceeded."""
        th = MetricThreshold("test", ThresholdDirection.UPPER, ThresholdMethod.FIXED_BOUND, 1.0)
        ev = evaluate_metric_threshold(1.0, th, atol=1e-9)
        assert ev.exceeded is False
        assert ev.boundary_status == "at_boundary"

    def test_bug_m_small_n_rejected(self) -> None:
        """Bug M: N < 2 is rejected, preventing unreliable single-sample thresholds."""
        with pytest.raises(ValueError, match="Insufficient"):
            calibrate_metric_threshold("fidelity:0", [0.95])

    def test_bug_n_no_composite_security_score(
        self,
        sample_honest_baseline: HonestBaseline,
        sample_calibration_observations: list[CalibrationObservation],
    ) -> None:
        """Bug N: Multi-metric evaluation produces independent evidence without an invented security score."""
        policy = calibrate_threshold_policy(sample_honest_baseline, sample_calibration_observations)
        trial = sample_calibration_observations[0]
        obs = VerificationObservation.from_calibration_observation(trial, configuration=sample_honest_baseline.configuration)
        report = evaluate_policy(obs, policy)

        # Verify no composite score attributes exist on report
        assert not hasattr(report, "security_score")
        assert not hasattr(report, "trust_score")
        assert not hasattr(report, "quantum_risk_score")

    def test_bug_o_no_attack_decision_verdicts(
        self,
        sample_honest_baseline: HonestBaseline,
        sample_calibration_observations: list[CalibrationObservation],
    ) -> None:
        """Bug O: M11 report strictly does NOT output ACCEPT, SUSPICIOUS, or ATTACK."""
        policy = calibrate_threshold_policy(sample_honest_baseline, sample_calibration_observations)
        trial = sample_calibration_observations[0]
        obs = VerificationObservation.from_calibration_observation(trial, configuration=sample_honest_baseline.configuration)
        report = evaluate_policy(obs, policy)

        rep_dict = report.to_dict()
        rep_str = str(rep_dict).lower()
        assert "accept" not in rep_str
        assert "suspicious" not in rep_str
        assert "attack" not in rep_str

    def test_bug_s_complex_values_rejected(self) -> None:
        """Bug S: Complex numbers cannot be silently passed as observed values."""
        th = MetricThreshold("fidelity:0", ThresholdDirection.LOWER, ThresholdMethod.FIXED_BOUND, 0.95)
        with pytest.raises(TypeError):
            evaluate_metric_threshold(0.95 + 0.1j, th)  # type: ignore

    def test_bug_t_fingerprint_uniqueness(self) -> None:
        """Bug T: Policies with differing threshold values have distinct fingerprints."""
        th1 = MetricThreshold("fidelity:0", ThresholdDirection.LOWER, ThresholdMethod.FIXED_BOUND, 0.95)
        th2 = MetricThreshold("fidelity:0", ThresholdDirection.LOWER, ThresholdMethod.FIXED_BOUND, 0.90)

        fp1 = calculate_policy_fingerprint("pol_1", "hash_abc", {"fidelity:0": th1})
        fp2 = calculate_policy_fingerprint("pol_1", "hash_abc", {"fidelity:0": th2})
        assert fp1 != fp2


# ==============================================================================
# 11. Quantum End-to-End Integration
# ==============================================================================

class TestQuantumEndToEndThresholdIntegration:
    """Validates complete pipeline from quantum states through teleportation, noise, M9, M10, to M11."""

    def test_end_to_end_pipeline_with_honest_and_anomalous_trials(self) -> None:
        """Execute full flow for |+i> state:
        1. Calibrate baseline under depolarizing noise p = 0.04.
        2. Calibrate threshold policy under honest operating conditions.
        3. Evaluate matching honest trial -> thresholds NOT exceeded.
        4. Evaluate severely degraded trial (e.g. higher noise / disturbance) -> threshold EXCEEDED.
        """
        state_label = "+i"
        noise_honest = create_depolarizing_channel(0.04)

        cfg = BaselineConfiguration(
            configuration_id="e2e_threshold_p04",
            states=(state_label,),
            noise_model_type="depolarizing",
            noise_strength=0.04,
            channel_location="bob_qubit",
            shots=None,
            calibration_runs=5,
        )

        # Step 1: Calibrate Honest Baseline
        baseline = calibrate_honest_baseline(cfg)

        # Step 2: Collect honest calibration observations
        honest_obs_list: list[CalibrationObservation] = []
        for i in range(5):
            trial = run_honest_calibration_trial(state=state_label, noise_channel=noise_honest, seed=3000 + i)
            honest_obs_list.append(trial)

        # Step 3: Calibrate Threshold Policy
        policy = calibrate_threshold_policy(
            baseline=baseline,
            observations=honest_obs_list,
            alpha=0.05,
            method=ThresholdMethod.EMPIRICAL_QUANTILE,
        )
        assert policy.baseline_configuration_hash == cfg.canonical_hash
        assert f"fidelity:{state_label}" in policy.thresholds

        # Step 4: Evaluate an honest trial
        honest_eval_trial = run_honest_calibration_trial(state=state_label, noise_channel=noise_honest, seed=4001)
        obs_honest = VerificationObservation.from_calibration_observation(honest_eval_trial, configuration=cfg)

        honest_report = evaluate_policy(obs_honest, policy)
        assert honest_report.any_exceeded is False
        fid_eval = honest_report.get_evaluation(f"fidelity:{state_label}")
        assert fid_eval is not None
        assert fid_eval.exceeded is False

        # Step 5: Evaluate a severely degraded observation (simulating channel disruption)
        noise_disrupted = create_depolarizing_channel(0.40)  # Heavy disruption
        disrupted_trial = run_honest_calibration_trial(state=state_label, noise_channel=noise_disrupted, seed=5001)
        obs_disrupted = VerificationObservation.from_calibration_observation(disrupted_trial, configuration=cfg)

        disrupted_report = evaluate_policy(obs_disrupted, policy)
        assert disrupted_report.any_exceeded is True
        fid_disrupted_eval = disrupted_report.get_evaluation(f"fidelity:{state_label}")
        assert fid_disrupted_eval is not None
        assert fid_disrupted_eval.exceeded is True
        assert fid_disrupted_eval.margin > 0.0

    def test_arbitrary_complex_state_threshold_calibration(self) -> None:
        """Calibrate and evaluate a threshold policy for an arbitrary normalized complex state."""
        alpha = np.sqrt(2.0 / 3.0)
        beta = (1.0j) / np.sqrt(3.0)
        custom_vec = validate_state_vector(np.array([alpha, beta], dtype=np.complex128))

        noise = create_phase_flip_channel(0.05)
        cfg = BaselineConfiguration(
            configuration_id="custom_complex_threshold_cfg",
            states=("custom_complex",),
            noise_model_type="phase_flip",
            noise_strength=0.05,
            channel_location="bob_qubit",
            shots=None,
            calibration_runs=4,
        )
        baseline = calibrate_honest_baseline(cfg, custom_states=[("custom_complex", custom_vec)])

        obs_list = [
            run_honest_calibration_trial(state=custom_vec, noise_channel=noise, state_name="custom_complex")
            for _ in range(4)
        ]
        policy = calibrate_threshold_policy(baseline, obs_list, alpha=0.05)

        assert "fidelity:custom_complex" in policy.thresholds
        assert policy.thresholds["fidelity:custom_complex"].direction == ThresholdDirection.LOWER

        eval_obs = VerificationObservation.from_calibration_observation(obs_list[0], configuration=cfg)
        report = evaluate_policy(eval_obs, policy)
        assert report.total_metrics_evaluated > 0


# ==============================================================================
# 12. Scientific Audit Suite (Pauli, Bell, Probability, Quantiles, Leakage)
# ==============================================================================

class TestScientificAuditM11:
    """Rigorous scientific audit tests addressing direction, deviation, Bell states, and data leakage."""

    def test_pauli_plus_one_baseline_downward_deviation(self) -> None:
        """State |0> has baseline <Z> = +1.0. Downward deviation must cross UPPER deviation threshold."""
        # Baseline mean = 1.0. Honest samples have small deviations ~ 0.01
        honest_dev_samples = [0.005, 0.010, 0.015, 0.008, 0.012]
        th = calibrate_metric_threshold("pauli_z:0", honest_dev_samples, direction=ThresholdDirection.UPPER, alpha=0.05)
        assert th.direction == ThresholdDirection.UPPER

        # Observation with downward shift: <Z> = 0.50 (deviation = |0.50 - 1.0| = 0.50)
        obs_dev = abs(0.50 - 1.0)
        ev = evaluate_metric_threshold(obs_dev, th)
        assert ev.exceeded is True
        assert ev.margin > 0.0
        assert math.isclose(ev.observed_value, 0.50, abs_tol=1e-12)

    def test_pauli_minus_one_baseline_upward_deviation(self) -> None:
        """State |1> has baseline <Z> = -1.0. Upward deviation must cross UPPER deviation threshold."""
        # Baseline mean = -1.0. Honest samples have small deviations from -1.0
        honest_dev_samples = [0.005, 0.010, 0.015, 0.008, 0.012]
        th = calibrate_metric_threshold("pauli_z:1", honest_dev_samples, direction=ThresholdDirection.UPPER, alpha=0.05)

        # Observation with upward shift: <Z> = -0.50 (deviation = |-0.50 - (-1.0)| = 0.50)
        obs_dev = abs(-0.50 - (-1.0))
        ev = evaluate_metric_threshold(obs_dev, th)
        assert ev.exceeded is True
        assert ev.margin > 0.0

        # Observation shifted to 0.0 (completely unpolarized): deviation = |0.0 - (-1.0)| = 1.0
        obs_dev_zero = abs(0.0 - (-1.0))
        ev_zero = evaluate_metric_threshold(obs_dev_zero, th)
        assert ev_zero.exceeded is True
        assert ev_zero.margin > 0.90

    def test_pauli_baseline_deviation_both_directions_symmetric(self) -> None:
        """Both upward and downward Pauli deviations produce positive absolute deviations and trigger properly."""
        b_mean = 0.0  # e.g. <Z> on |+> state has expected value 0.0
        honest_dev_samples = [0.01, 0.02, 0.015, 0.025, 0.01]
        th = calibrate_metric_threshold("pauli_z:+", honest_dev_samples, direction=ThresholdDirection.UPPER, alpha=0.05)

        # Positive shift (+0.30)
        ev_pos = evaluate_metric_threshold(abs(+0.30 - b_mean), th)
        # Negative shift (-0.30)
        ev_neg = evaluate_metric_threshold(abs(-0.30 - b_mean), th)

        assert ev_pos.exceeded is True
        assert ev_neg.exceeded is True
        assert math.isclose(ev_pos.margin, ev_neg.margin, abs_tol=1e-12)

    def test_bell_plus_one_correlation_deviation(self) -> None:
        """On |Phi+>, XX = +1.0. Downward shift to +0.50 is caught by absolute deviation threshold."""
        b_mean = 1.0
        honest_dev_samples = [0.01, 0.02, 0.015, 0.03, 0.02]
        th_bell = calibrate_metric_threshold(
            "bell_xx",
            honest_dev_samples,
            direction=ThresholdDirection.UPPER,
            alpha=0.05,
            metadata={"baseline_mean": b_mean},
        )
        # Degraded correlation: 0.50 -> deviation = |0.50 - 1.0| = 0.50
        ev = evaluate_metric_threshold(abs(0.50 - b_mean), th_bell)
        assert ev.exceeded is True
        assert ev.margin > 0.0

    def test_bell_minus_one_correlation_deviation(self) -> None:
        """On |Phi+>, YY = -1.0. Upward shift to -0.40 is caught by absolute deviation threshold."""
        b_mean = -1.0
        honest_dev_samples = [0.01, 0.02, 0.015, 0.03, 0.02]
        th_bell = calibrate_metric_threshold(
            "bell_yy",
            honest_dev_samples,
            direction=ThresholdDirection.UPPER,
            alpha=0.05,
            metadata={"baseline_mean": b_mean},
        )
        # Degraded correlation: -0.40 -> deviation = |-0.40 - (-1.0)| = 0.60
        ev = evaluate_metric_threshold(abs(-0.40 - b_mean), th_bell)
        assert ev.exceeded is True
        assert ev.margin > 0.0

    def test_all_four_bell_states_correlation_thresholding(self) -> None:
        """Verify correlation thresholding across all four Bell states (Phi+, Phi-, Psi+, Psi-)."""
        expected_correlations = {
            "phi+": {"XX": 1.0, "YY": -1.0, "ZZ": 1.0},
            "phi-": {"XX": -1.0, "YY": 1.0, "ZZ": 1.0},
            "psi+": {"XX": 1.0, "YY": 1.0, "ZZ": -1.0},
            "psi-": {"XX": -1.0, "YY": -1.0, "ZZ": -1.0},
        }
        for state_name, corrs in expected_correlations.items():
            for op, honest_val in corrs.items():
                th = MetricThreshold(
                    metric_name=f"bell_{op.lower()}:{state_name}",
                    direction=ThresholdDirection.UPPER,
                    method=ThresholdMethod.FIXED_BOUND,
                    threshold_value=0.10,  # 10% maximum allowable correlation deviation
                    metadata={"baseline_mean": honest_val},
                )
                # Honest observation with minor noise (deviation = 0.02)
                honest_obs_val = honest_val - 0.02 if honest_val > 0 else honest_val + 0.02
                dev_honest = abs(honest_obs_val - honest_val)
                ev_honest = evaluate_metric_threshold(dev_honest, th)
                assert ev_honest.exceeded is False, f"Honest false alarm for {state_name} on {op}"

                # Severe degradation towards 0.0 (unentangled / noise)
                degraded_obs_val = 0.0
                dev_degraded = abs(degraded_obs_val - honest_val)  # deviation = 1.0
                ev_degraded = evaluate_metric_threshold(dev_degraded, th)
                assert ev_degraded.exceeded is True, f"Failed to detect degradation for {state_name} on {op}"
                assert ev_degraded.margin > 0.80

    def test_probability_deviation_both_directions(self) -> None:
        """Born probability thresholding evaluates absolute deviation |p - p_expected| (UPPER tail)."""
        p_expected = 0.50
        honest_dev_samples = [0.01, 0.02, 0.015, 0.03, 0.02]
        th_p = calibrate_metric_threshold(
            "prob_dev_z_0:+",
            honest_dev_samples,
            direction=ThresholdDirection.UPPER,
            alpha=0.05,
            metadata={"baseline_mean": p_expected},
        )
        # Shifted high (p = 0.75 -> dev = 0.25)
        ev_high = evaluate_metric_threshold(abs(0.75 - p_expected), th_p)
        assert ev_high.exceeded is True

        # Shifted low (p = 0.25 -> dev = 0.25)
        ev_low = evaluate_metric_threshold(abs(0.25 - p_expected), th_p)
        assert ev_low.exceeded is True
        assert math.isclose(ev_high.margin, ev_low.margin, abs_tol=1e-12)

    def test_absolute_deviation_no_re_deviation(self) -> None:
        """M11 consumes M10 absolute deviation directly without applying another deviation from baseline."""
        # Suppose baseline mean for metric is 0.80, observed value is 0.65
        # M10 produces absolute_deviation = |0.65 - 0.80| = 0.15
        # M11 threshold on absolute deviation is 0.10
        th_dev = MetricThreshold("metric:abs_dev", ThresholdDirection.UPPER, ThresholdMethod.FIXED_BOUND, 0.10)
        m10_abs_dev = 0.15
        ev = evaluate_metric_threshold(m10_abs_dev, th_dev)
        assert ev.observed_value == 0.15
        assert ev.threshold_value == 0.10
        assert ev.exceeded is True
        # Margin is exactly 0.15 - 0.10 = 0.05 (NOT ||0.15 - 0.80| - 0.10|)
        assert math.isclose(ev.margin, 0.05, abs_tol=1e-12)

    def test_empirical_quantile_known_synthetic_dataset(self) -> None:
        """Verify empirical quantile against manually calculated values for a known synthetic dataset."""
        # Sorted dataset of 10 values: 0.1, 0.2, ..., 1.0
        data = [0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 1.00]
        alpha = 0.20

        # Mathematical derivation for method='linear':
        # N = 10, index = (N - 1) * q = 9 * q
        # For LOWER tail (q = alpha = 0.20): index = 9 * 0.20 = 1.8.
        # Floor i = 1, fraction g = 0.8.
        # Q = data[1] + 0.8 * (data[2] - data[1]) = 0.20 + 0.8 * 0.10 = 0.28.
        t_lower = calculate_empirical_quantile_threshold(data, ThresholdDirection.LOWER, alpha=alpha)
        assert math.isclose(t_lower, 0.28, abs_tol=1e-12)

        # For UPPER tail (q = 1 - alpha = 0.80): index = 9 * 0.80 = 7.2.
        # Floor i = 7, fraction g = 0.2.
        # Q = data[7] + 0.2 * (data[8] - data[7]) = 0.80 + 0.2 * 0.10 = 0.82.
        t_upper = calculate_empirical_quantile_threshold(data, ThresholdDirection.UPPER, alpha=alpha)
        assert math.isclose(t_upper, 0.82, abs_tol=1e-12)

    def test_small_n_statistical_reliability_metadata(self) -> None:
        """N=2 is computationally valid but flagged as low_sample_count; N >= 20 is statistically_reliable."""
        th_small = calibrate_metric_threshold("fidelity:0", [0.94, 0.96], alpha=0.05)
        assert th_small.sample_count == 2
        assert th_small.metadata["statistical_reliability"] == "low_sample_count"
        assert th_small.metadata["minimum_recommended_samples"] >= 10

        large_samples = [0.95 + 0.001 * i for i in range(25)]
        th_large = calibrate_metric_threshold("fidelity:0", large_samples, alpha=0.05)
        assert th_large.sample_count == 25
        assert th_large.metadata["statistical_reliability"] == "statistically_reliable"

    def test_far_data_leakage_copied_container_detected(
        self,
        sample_honest_baseline: HonestBaseline,
        sample_calibration_observations: list[CalibrationObservation],
    ) -> None:
        """Wrapping calibration observations in a new list object is detected as data leakage."""
        policy = calibrate_threshold_policy(sample_honest_baseline, sample_calibration_observations)
        # Separate list instance containing the exact same observation objects
        copied_container = list(sample_calibration_observations)
        assert copied_container is not sample_calibration_observations

        with pytest.raises(ValueError, match="Data leakage detected"):
            evaluate_policy_false_alarm_rate(
                validation_observations=copied_container,
                policy=policy,
                calibration_observations=sample_calibration_observations,
            )

    def test_multi_metric_independent_evaluation_no_composite_score(
        self,
        sample_honest_baseline: HonestBaseline,
        sample_calibration_observations: list[CalibrationObservation],
    ) -> None:
        """Multiple metrics are evaluated independently; crossing one does not fabricate an arbitrary security score."""
        policy = calibrate_threshold_policy(sample_honest_baseline, sample_calibration_observations)
        trial = sample_calibration_observations[0]

        # Observation where ONLY fidelity is degraded (0.80) while QBER is normal (0.01)
        obs_partial = VerificationObservation(
            state_name="0",
            fidelity=0.80,
            qber=0.01,
            probabilities_z=trial.probabilities_z,
            probabilities_x=trial.probabilities_x,
            probabilities_y=trial.probabilities_y,
            pauli_expectations=trial.pauli_expectations,
            configuration=sample_honest_baseline.configuration,
        )
        report = evaluate_policy(obs_partial, policy)
        assert report.any_exceeded is True
        assert report.all_exceeded is False

        fid_eval = report.get_evaluation("fidelity:0")
        assert fid_eval is not None and fid_eval.exceeded is True

        qber_eval = report.get_evaluation("qber:0")
        assert qber_eval is not None and qber_eval.exceeded is False

        # Verify independence: each metric has its own evaluation and no composite score exists
        assert "fidelity:0" in report.exceeded_metrics
        assert "qber:0" not in report.exceeded_metrics
        assert not hasattr(report, "composite_score")
        assert not hasattr(report, "security_score")

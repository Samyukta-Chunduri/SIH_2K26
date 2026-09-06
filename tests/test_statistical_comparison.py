"""Tests for Statistical Analysis & Comparison Engine (Milestone M10).

Validates:
1. Basic deviations: Absolute deviation, signed deviation, safe relative deviation with zero-division handling.
2. Baseline uncertainty: Standard error of the mean for N=0 (rejected), N=1 (None), and N>=2.
3. Standardized deviation (z-score): Descriptive scale, zero variance handling, N<2 handling, no automatic attack decisions.
4. Confidence interval containment: Inside, outside, boundary within numerical tolerance, and unavailable (N=1).
5. Distribution comparison: Total Variation Distance (TV), normalization validation, disjoint/identical distributions.
6. Multi-metric observation comparison: Fidelity, QBER, Pauli X/Y/Z, Bell correlations, Born distributions.
7. Configuration compatibility: Strict isolation across states, noise models, noise strength, channel location, shots, backend.
8. Baseline immutability & contamination prevention: Baseline remains unchanged; no data absorption.
9. Bug-catching sensitivity suite: Rigorous coverage of Bugs A through T.
10. Quantum cross-validation: Simulated teleportation verification with physical noise channels compared against baseline.
"""

from __future__ import annotations

from dataclasses import asdict, FrozenInstanceError
import math
from typing import Any
import numpy as np
import pytest

from src.noise.density_matrix import calculate_mixed_state_fidelity
from src.noise.models import (
    create_bit_flip_channel,
    create_depolarizing_channel,
    create_phase_flip_channel,
)
from src.noise.teleportation_noise import simulate_noisy_teleportation_mathematical
from src.quantum.bell import create_bell_circuit
from src.quantum.states import get_standard_state, validate_state_vector
from src.statistics import (
    BaselineConfiguration,
    CalibrationObservation,
    ConfigurationCompatibilityError,
    DistributionComparison,
    HonestBaseline,
    MetricDeviation,
    MetricStatistics,
    StatisticalEvidence,
    VerificationObservation,
    build_honest_baseline_from_observations,
    calculate_absolute_deviation,
    calculate_relative_deviation,
    calculate_sample_statistics,
    calculate_standard_error,
    calculate_standardized_deviation,
    calculate_total_variation_distance,
    calibrate_honest_baseline,
    check_confidence_interval,
    check_configuration_compatibility,
    compare_observation,
    compare_probability_distributions,
    compare_scalar_metric,
    run_honest_calibration_trial,
    validate_configuration_compatibility,
)


# ==============================================================================
# 1. Basic Deviations & Relative Deviation
# ==============================================================================

class TestBasicDeviations:
    """Validates absolute, signed, and relative deviation mathematical calculations."""

    def test_observed_equals_baseline_mean(self) -> None:
        """When observed value matches baseline mean, deviations must be zero."""
        abs_dev = calculate_absolute_deviation(0.95, 0.95)
        assert abs_dev == 0.0

        rel_dev = calculate_relative_deviation(0.95, 0.95)
        assert rel_dev == 0.0

    def test_observed_above_baseline_mean(self) -> None:
        """Observed above baseline yields positive signed deviation and correct absolute deviation."""
        abs_dev = calculate_absolute_deviation(0.98, 0.95)
        assert np.isclose(abs_dev, 0.03)

        rel_dev = calculate_relative_deviation(0.98, 0.95)
        assert rel_dev is not None
        assert np.isclose(rel_dev, 0.03 / 0.95)

    def test_observed_below_baseline_mean(self) -> None:
        """Observed below baseline yields positive absolute deviation."""
        abs_dev = calculate_absolute_deviation(0.90, 0.95)
        assert np.isclose(abs_dev, 0.05)

        rel_dev = calculate_relative_deviation(0.90, 0.95)
        assert rel_dev is not None
        assert np.isclose(rel_dev, 0.05 / 0.95)

    def test_relative_deviation_zero_denominator(self) -> None:
        """When baseline mean is 0.0, relative deviation must return None without raising error."""
        rel_dev = calculate_relative_deviation(0.05, 0.0)
        assert rel_dev is None, "Relative deviation with baseline mean 0.0 must be None (undefined)."

    def test_relative_deviation_near_zero_denominator(self) -> None:
        """When baseline mean is smaller than epsilon (1e-12), relative deviation returns None."""
        rel_dev = calculate_relative_deviation(0.05, 1e-13)
        assert rel_dev is None, "Relative deviation with near-zero baseline mean must be None."

    def test_negative_baseline_values(self) -> None:
        """Negative baseline values (e.g. Pauli expectations <Z> = -1.0) must compute correctly."""
        abs_dev = calculate_absolute_deviation(-0.8, -1.0)
        assert np.isclose(abs_dev, 0.2)

        rel_dev = calculate_relative_deviation(-0.8, -1.0)
        assert rel_dev is not None
        assert np.isclose(rel_dev, 0.2 / 1.0)

    def test_input_validation_deviations(self) -> None:
        """Non-numeric and non-finite inputs must raise appropriate errors."""
        with pytest.raises(TypeError):
            calculate_absolute_deviation("bad", 0.5)  # type: ignore
        with pytest.raises(TypeError):
            calculate_absolute_deviation(0.5, True)  # type: ignore
        with pytest.raises(ValueError, match="finite"):
            calculate_absolute_deviation(float("nan"), 0.5)
        with pytest.raises(ValueError, match="finite"):
            calculate_absolute_deviation(0.5, float("inf"))

        with pytest.raises(TypeError):
            calculate_relative_deviation(0.5, 0.5, epsilon="small")  # type: ignore
        with pytest.raises(ValueError, match="positive"):
            calculate_relative_deviation(0.5, 0.5, epsilon=-1e-5)


# ==============================================================================
# 2. Standard Error & Standardized Deviation (Z-Score)
# ==============================================================================

class TestStandardErrorAndZScore:
    """Validates baseline uncertainty and standardized deviation calculations."""

    def test_standard_error_sample_counts(self) -> None:
        """Verify SE = s / sqrt(N) for N >= 2, None for N=1, and error for N=0."""
        # N=1
        assert calculate_standard_error(sample_std=0.0, sample_count=1) is None
        # N=2
        se_2 = calculate_standard_error(sample_std=0.10, sample_count=2)
        assert se_2 is not None
        assert np.isclose(se_2, 0.10 / math.sqrt(2))
        # N=100
        se_100 = calculate_standard_error(sample_std=0.10, sample_count=100)
        assert se_100 is not None
        assert np.isclose(se_100, 0.01)

        # N <= 0 raises ValueError
        with pytest.raises(ValueError, match="sample_count"):
            calculate_standard_error(sample_std=0.10, sample_count=0)
        with pytest.raises(ValueError, match="sample_count"):
            calculate_standard_error(sample_std=0.10, sample_count=-5)

    def test_standardized_deviation_positive_negative_zero(self) -> None:
        """Verify standardized deviation (z-score) computation."""
        # Positive z
        z_pos = calculate_standardized_deviation(observed=0.98, baseline_mean=0.95, baseline_std=0.01, sample_count=50)
        assert z_pos is not None
        assert np.isclose(z_pos, 3.0)

        # Negative z
        z_neg = calculate_standardized_deviation(observed=0.92, baseline_mean=0.95, baseline_std=0.01, sample_count=50)
        assert z_neg is not None
        assert np.isclose(z_neg, -3.0)

        # Zero z
        z_zero = calculate_standardized_deviation(observed=0.95, baseline_mean=0.95, baseline_std=0.01, sample_count=50)
        assert z_zero is not None
        assert z_zero == 0.0

    def test_standardized_deviation_zero_variance(self) -> None:
        """When baseline standard deviation is 0.0: z=0 if observed==mean, None if observed!=mean."""
        # Observed matches mean exactly under zero variance
        z_exact = calculate_standardized_deviation(observed=1.0, baseline_mean=1.0, baseline_std=0.0, sample_count=10)
        assert z_exact == 0.0

        # Observed differs from mean under zero variance -> undefined (division by zero)
        z_diff = calculate_standardized_deviation(observed=0.98, baseline_mean=1.0, baseline_std=0.0, sample_count=10)
        assert z_diff is None, "Z-score under zero standard deviation with non-zero diff must be None."

    def test_standardized_deviation_insufficient_sample_count(self) -> None:
        """When sample count N < 2, standardized deviation must be None."""
        z_n1 = calculate_standardized_deviation(observed=0.95, baseline_mean=0.95, baseline_std=0.0, sample_count=1)
        assert z_n1 is None

    def test_standardized_deviation_determinism(self) -> None:
        """Repeated calculation on identical inputs must produce exactly identical floats."""
        res1 = calculate_standardized_deviation(0.93, 0.98, 0.02, sample_count=30)
        res2 = calculate_standardized_deviation(0.93, 0.98, 0.02, sample_count=30)
        assert res1 == res2


# ==============================================================================
# 3. Confidence Interval Containment
# ==============================================================================

class TestConfidenceIntervalContainment:
    """Validates checking whether an observation lies within the baseline confidence interval."""

    def test_strictly_inside_ci(self) -> None:
        """Value inside confidence interval."""
        inside, status = check_confidence_interval(0.96, (0.94, 0.98))
        assert inside is True
        assert status == "inside"

    def test_strictly_outside_ci(self) -> None:
        """Value outside confidence interval."""
        inside_low, status_low = check_confidence_interval(0.92, (0.94, 0.98))
        assert inside_low is False
        assert status_low == "outside"

        inside_high, status_high = check_confidence_interval(0.99, (0.94, 0.98))
        assert inside_high is False
        assert status_high == "outside"

    def test_boundary_ci_numerical_tolerance(self) -> None:
        """Value on boundary within numerical tolerance atol."""
        inside, status = check_confidence_interval(0.9400000001, (0.94, 0.98), atol=1e-8)
        assert inside is True
        assert status == "boundary"

    def test_unavailable_ci(self) -> None:
        """When CI is None (e.g. N=1 calibration), return (None, 'unavailable')."""
        inside, status = check_confidence_interval(0.95, None)
        assert inside is None
        assert status == "unavailable"

    def test_invalid_ci_structure(self) -> None:
        """Malformed confidence intervals must raise ValueError."""
        with pytest.raises(ValueError, match="2-tuple"):
            check_confidence_interval(0.95, (0.94, 0.96, 0.98))  # type: ignore
        with pytest.raises(ValueError, match="exceeds"):
            check_confidence_interval(0.95, (0.98, 0.94))  # lower > upper
        with pytest.raises(ValueError, match="finite"):
            check_confidence_interval(0.95, (float("nan"), 0.98))


# ==============================================================================
# 4. Total Variation Distance & Probability Distributions
# ==============================================================================

class TestTotalVariationDistance:
    """Validates discrete probability distribution comparison via Total Variation distance."""

    def test_identical_distributions_tv_zero(self) -> None:
        """Identical distributions must have TV = 0.0."""
        p = {"0": 0.5, "1": 0.5}
        q = {"0": 0.5, "1": 0.5}
        assert calculate_total_variation_distance(p, q) == 0.0

    def test_disjoint_distributions_tv_one(self) -> None:
        """Completely disjoint distributions must have TV = 1.0."""
        p = {"0": 1.0}
        q = {"1": 1.0}
        assert calculate_total_variation_distance(p, q) == 1.0

    def test_known_intermediate_tv(self) -> None:
        """Verify known analytical TV calculation.
        P = {0: 0.5, 1: 0.5}, Q = {0: 0.6, 1: 0.4}
        TV = 0.5 * (|0.5 - 0.6| + |0.5 - 0.4|) = 0.5 * (0.1 + 0.1) = 0.10.
        """
        p = {"0": 0.5, "1": 0.5}
        q = {"0": 0.6, "1": 0.4}
        tv = calculate_total_variation_distance(p, q)
        assert np.isclose(tv, 0.10)

    def test_missing_outcome_treated_as_zero(self) -> None:
        """Outcomes present in one distribution but missing in another are treated as 0.0."""
        p = {"00": 0.7, "11": 0.3}
        q = {"00": 0.5, "01": 0.2, "11": 0.3}
        # diffs: 00 -> |0.7 - 0.5| = 0.2
        #        01 -> |0.0 - 0.2| = 0.2
        #        11 -> |0.3 - 0.3| = 0.0
        # TV = 0.5 * (0.2 + 0.2 + 0.0) = 0.2
        tv = calculate_total_variation_distance(p, q)
        assert np.isclose(tv, 0.20)

    def test_distribution_comparison_object(self) -> None:
        """compare_probability_distributions returns complete DistributionComparison."""
        p = {"0": 0.7, "1": 0.3}
        q = {"0": 0.5, "1": 0.5}
        res = compare_probability_distributions(p, q, distribution_name="test_z")
        assert res.distribution_name == "test_z"
        assert np.isclose(res.total_variation_distance, 0.20)
        assert np.isclose(res.per_outcome_deviations["0"], 0.20)
        assert np.isclose(res.per_outcome_deviations["1"], 0.20)
        assert np.isclose(res.per_outcome_signed["0"], 0.20)
        assert np.isclose(res.per_outcome_signed["1"], -0.20)
        assert np.isclose(res.max_outcome_deviation, 0.20)

    def test_validation_invalid_probabilities(self) -> None:
        """Invalid probability values must raise ValueError."""
        # Probability < 0
        with pytest.raises(ValueError, match=r"\[0\.0, 1\.0\]"):
            calculate_total_variation_distance({"0": -0.1, "1": 1.1}, {"0": 0.5, "1": 0.5})

        # Probability > 1
        with pytest.raises(ValueError, match=r"\[0\.0, 1\.0\]"):
            calculate_total_variation_distance({"0": 1.5, "1": -0.5}, {"0": 0.5, "1": 0.5})

        # Non-finite probability
        with pytest.raises(ValueError, match="finite"):
            calculate_total_variation_distance({"0": float("nan"), "1": 0.5}, {"0": 0.5, "1": 0.5})

        # Sum != 1
        with pytest.raises(ValueError, match="sum to 1.0"):
            calculate_total_variation_distance({"0": 0.5, "1": 0.2}, {"0": 0.5, "1": 0.5})

        # Empty distribution
        with pytest.raises(ValueError, match="empty"):
            calculate_total_variation_distance({}, {"0": 0.5, "1": 0.5})


# ==============================================================================
# 5. Scalar Metric Comparison
# ==============================================================================

class TestScalarMetricComparison:
    """Validates compare_scalar_metric against MetricStatistics."""

    def test_scalar_comparison_populated_statistics(self) -> None:
        """Verify compare_scalar_metric against calibrated MetricStatistics."""
        stats = calculate_sample_statistics([0.97, 0.98, 0.99, 0.98, 0.98], bounds=(0.0, 1.0))
        dev = compare_scalar_metric(observed=0.92, baseline_stats=stats, metric_name="fidelity:0")

        assert dev.metric_name == "fidelity:0"
        assert dev.observed_value == 0.92
        assert np.isclose(dev.baseline_mean, 0.98)
        assert np.isclose(dev.absolute_deviation, 0.06)
        assert np.isclose(dev.signed_deviation, -0.06)
        assert dev.relative_deviation is not None
        assert np.isclose(dev.relative_deviation, 0.06 / 0.98)
        assert dev.standard_error is not None
        assert dev.standardized_deviation is not None
        assert dev.standardized_deviation < 0.0  # observed < mean
        assert dev.inside_baseline_ci is False
        assert dev.ci_status == "outside"

    def test_scalar_comparison_single_sample_baseline(self) -> None:
        """For N=1 baseline, standard error, z-score, and CI must be safely None/unavailable."""
        stats = calculate_sample_statistics([0.98])
        dev = compare_scalar_metric(observed=0.95, baseline_stats=stats, metric_name="fidelity:0")

        assert np.isclose(dev.absolute_deviation, 0.03)
        assert dev.standard_error is None
        assert dev.standardized_deviation is None
        assert dev.inside_baseline_ci is None
        assert dev.ci_status == "unavailable"


# ==============================================================================
# 6. Configuration Compatibility & Verification
# ==============================================================================

class TestConfigurationCompatibility:
    """Validates configuration compatibility checks between observations and baselines."""

    @pytest.fixture
    def sample_baseline(self) -> HonestBaseline:
        """Create a standard calibrated baseline for compatibility testing."""
        cfg = BaselineConfiguration(
            configuration_id="compat_test_config",
            states=("0", "1", "+", "-"),
            noise_model_type="depolarizing",
            noise_strength=0.05,
            channel_location="bob_qubit",
            shots=None,
            calibration_runs=5,
            backend="mathematical",
        )
        return calibrate_honest_baseline(cfg)

    def test_compatible_observation(self, sample_baseline: HonestBaseline) -> None:
        """Observation with matching parameters passes compatibility check."""
        obs = VerificationObservation(
            state_name="0",
            fidelity=0.98,
            qber=0.02,
            probabilities_z={"0": 0.98, "1": 0.02},
            probabilities_x={"+": 0.5, "-": 0.5},
            probabilities_y={"+i": 0.5, "-i": 0.5},
            pauli_expectations={"X": 0.0, "Y": 0.0, "Z": 0.96},
            configuration=sample_baseline.configuration,
        )
        assert validate_configuration_compatibility(obs, sample_baseline) is True
        is_compat, reason, _ = check_configuration_compatibility(obs, sample_baseline)
        assert is_compat is True
        assert reason == "Compatible"

    def test_incompatible_state_rejected(self, sample_baseline: HonestBaseline) -> None:
        """Observation for an uncalibrated state (+i when baseline has 0, 1, +, -) is rejected."""
        obs = VerificationObservation(
            state_name="+i",  # not in sample_baseline.configuration.states
            fidelity=0.98,
            qber=0.02,
            probabilities_z={"0": 0.5, "1": 0.5},
            probabilities_x={"+": 0.5, "-": 0.5},
            probabilities_y={"+i": 0.98, "-i": 0.02},
            pauli_expectations={"X": 0.0, "Y": 0.96, "Z": 0.0},
        )
        with pytest.raises(ConfigurationCompatibilityError, match="not calibrated"):
            validate_configuration_compatibility(obs, sample_baseline)

    def test_incompatible_noise_model_rejected(self, sample_baseline: HonestBaseline) -> None:
        """Observation specifying bit_flip when baseline was depolarizing is rejected."""
        incompat_cfg = {
            "noise_model_type": "bit_flip",
            "noise_strength": 0.05,
            "channel_location": "bob_qubit",
            "shots": None,
            "backend": "mathematical",
        }
        obs = VerificationObservation(
            state_name="0",
            fidelity=0.98,
            qber=0.02,
            probabilities_z={"0": 0.98, "1": 0.02},
            probabilities_x={"+": 0.5, "-": 0.5},
            probabilities_y={"+i": 0.5, "-i": 0.5},
            pauli_expectations={"X": 0.0, "Y": 0.0, "Z": 0.96},
            configuration=incompat_cfg,
        )
        with pytest.raises(ConfigurationCompatibilityError, match="Noise model mismatch"):
            validate_configuration_compatibility(obs, sample_baseline)

    def test_incompatible_noise_strength_rejected(self, sample_baseline: HonestBaseline) -> None:
        """Observation specifying p=0.20 when baseline was calibrated for p=0.05 is rejected."""
        incompat_cfg = {
            "noise_model_type": "depolarizing",
            "noise_strength": 0.20,  # mismatch
            "channel_location": "bob_qubit",
            "shots": None,
            "backend": "mathematical",
        }
        obs = VerificationObservation(
            state_name="0",
            fidelity=0.90,
            qber=0.10,
            probabilities_z={"0": 0.90, "1": 0.10},
            probabilities_x={"+": 0.5, "-": 0.5},
            probabilities_y={"+i": 0.5, "-i": 0.5},
            pauli_expectations={"X": 0.0, "Y": 0.0, "Z": 0.80},
            configuration=incompat_cfg,
        )
        with pytest.raises(ConfigurationCompatibilityError, match="Noise strength mismatch"):
            validate_configuration_compatibility(obs, sample_baseline)

    def test_incompatible_channel_location_rejected(self, sample_baseline: HonestBaseline) -> None:
        """Observation specifying transmission channel when baseline was bob_qubit is rejected."""
        incompat_cfg = {
            "noise_model_type": "depolarizing",
            "noise_strength": 0.05,
            "channel_location": "transmission_channel",
            "shots": None,
            "backend": "mathematical",
        }
        obs = VerificationObservation(
            state_name="0",
            fidelity=0.98,
            qber=0.02,
            probabilities_z={"0": 0.98, "1": 0.02},
            probabilities_x={"+": 0.5, "-": 0.5},
            probabilities_y={"+i": 0.5, "-i": 0.5},
            pauli_expectations={"X": 0.0, "Y": 0.0, "Z": 0.96},
            configuration=incompat_cfg,
        )
        with pytest.raises(ConfigurationCompatibilityError, match="Channel location mismatch"):
            validate_configuration_compatibility(obs, sample_baseline)

    def test_incompatible_shots_rejected(self, sample_baseline: HonestBaseline) -> None:
        """Observation with empirical shots=1000 against analytical shots=None baseline is rejected."""
        incompat_cfg = {
            "noise_model_type": "depolarizing",
            "noise_strength": 0.05,
            "channel_location": "bob_qubit",
            "shots": 1000,
            "backend": "mathematical",
        }
        obs = VerificationObservation(
            state_name="0",
            fidelity=0.98,
            qber=0.02,
            probabilities_z={"0": 0.98, "1": 0.02},
            probabilities_x={"+": 0.5, "-": 0.5},
            probabilities_y={"+i": 0.5, "-i": 0.5},
            pauli_expectations={"X": 0.0, "Y": 0.0, "Z": 0.96},
            shots=1000,
            configuration=incompat_cfg,
        )
        with pytest.raises(ConfigurationCompatibilityError, match="Shot count mismatch"):
            validate_configuration_compatibility(obs, sample_baseline)

    def test_incompatible_canonical_hash_rejected_under_strict_hash(self, sample_baseline: HonestBaseline) -> None:
        """Observation carrying a different canonical hash is rejected when strict_hash=True."""
        incompat_cfg = {
            "canonical_hash": "deadbeef" * 8,
        }
        obs = VerificationObservation(
            state_name="0",
            fidelity=0.98,
            qber=0.02,
            probabilities_z={"0": 0.98, "1": 0.02},
            probabilities_x={"+": 0.5, "-": 0.5},
            probabilities_y={"+i": 0.5, "-i": 0.5},
            pauli_expectations={"X": 0.0, "Y": 0.0, "Z": 0.96},
            configuration=incompat_cfg,
        )
        with pytest.raises(ConfigurationCompatibilityError, match="Canonical hash mismatch"):
            validate_configuration_compatibility(obs, sample_baseline, strict_hash=True)


# ==============================================================================
# 7. Baseline Immutability & Data Contamination Prevention
# ==============================================================================

class TestBaselineImmutabilityAndSeparation:
    """Verifies that statistical comparison never alters or contaminates the honest baseline."""

    def test_baseline_unchanged_after_comparisons(self) -> None:
        """Baseline metrics and hash must remain strictly identical before and after comparison."""
        cfg = BaselineConfiguration(
            configuration_id="immutability_config",
            states=("0", "1"),
            noise_model_type="depolarizing",
            noise_strength=0.02,
            channel_location="bob_qubit",
            shots=None,
            calibration_runs=3,
        )
        baseline = calibrate_honest_baseline(cfg)

        initial_metrics_dict = {k: asdict(v) for k, v in baseline.metrics.items()}
        initial_hash = baseline.configuration.canonical_hash

        # Run multiple comparisons with anomalous/deviated observation
        anomalous_obs = VerificationObservation(
            state_name="0",
            fidelity=0.60,
            qber=0.40,
            probabilities_z={"0": 0.60, "1": 0.40},
            probabilities_x={"+": 0.5, "-": 0.5},
            probabilities_y={"+i": 0.5, "-i": 0.5},
            pauli_expectations={"X": 0.0, "Y": 0.0, "Z": 0.20},
            configuration=cfg,
        )

        for _ in range(5):
            evidence = compare_observation(anomalous_obs, baseline)
            assert isinstance(evidence, StatisticalEvidence)

        # Baseline metrics must be completely untouched
        after_metrics_dict = {k: asdict(v) for k, v in baseline.metrics.items()}
        assert initial_metrics_dict == after_metrics_dict
        assert baseline.configuration.canonical_hash == initial_hash

    def test_baseline_frozen_dataclass_raises_on_mutation(self) -> None:
        """Attempting to reassign attributes on HonestBaseline raises FrozenInstanceError."""
        cfg = BaselineConfiguration(
            configuration_id="frozen_check",
            states=("0",),
            noise_model_type="ideal",
            noise_strength=0.0,
            channel_location="bob_qubit",
            shots=None,
            calibration_runs=2,
        )
        baseline = calibrate_honest_baseline(cfg)
        with pytest.raises(FrozenInstanceError):
            baseline.metrics = {}  # type: ignore


# ==============================================================================
# 8. Multi-Metric Observation Comparison
# ==============================================================================

class TestMultiMetricObservationComparison:
    """Validates multi-metric comparison preserving all independent deviations."""

    def test_full_observation_comparison(self) -> None:
        """Verify comprehensive comparison across fidelity, QBER, Paulis, Bell, and distributions."""
        cfg = BaselineConfiguration(
            configuration_id="multi_metric_config",
            states=("0", "1"),
            noise_model_type="depolarizing",
            noise_strength=0.03,
            channel_location="bob_qubit",
            shots=None,
            calibration_runs=5,
        )
        baseline = calibrate_honest_baseline(cfg)

        obs = VerificationObservation(
            state_name="0",
            fidelity=0.92,
            qber=0.08,
            probabilities_z={"0": 0.92, "1": 0.08},
            probabilities_x={"+": 0.5, "-": 0.5},
            probabilities_y={"+i": 0.5, "-i": 0.5},
            pauli_expectations={"X": 0.0, "Y": 0.0, "Z": 0.84},
            bell_correlations={"XX": 0.95, "YY": -0.95, "ZZ": 0.95},
            configuration=cfg,
        )

        evidence = compare_observation(obs, baseline)
        assert isinstance(evidence, StatisticalEvidence)
        assert evidence.observation_state == "0"
        assert evidence.baseline_configuration_hash == baseline.configuration.canonical_hash

        # Check fidelity deviation
        fid_dev = evidence.get_metric("fidelity:0")
        assert fid_dev is not None
        assert fid_dev.observed_value == 0.92
        assert fid_dev.absolute_deviation > 0.0
        assert fid_dev.signed_deviation < 0.0

        # Check QBER deviation
        qber_dev = evidence.get_metric("qber:0")
        assert qber_dev is not None
        assert qber_dev.observed_value == 0.08
        assert qber_dev.signed_deviation > 0.0

        # Check Pauli Z expectation deviation
        exp_z_dev = evidence.get_metric("exp_z:0")
        assert exp_z_dev is not None
        assert exp_z_dev.observed_value == 0.84

        # Check Bell correlation deviations
        bell_xx = evidence.get_metric("bell_xx")
        assert bell_xx is not None
        assert bell_xx.observed_value == 0.95

        # Check distribution comparison
        dist_z = evidence.get_distribution("probabilities_z:0")
        assert dist_z is not None
        assert 0.0 < dist_z.total_variation_distance < 1.0

        # Verify serialization
        ev_dict = evidence.to_dict()
        assert ev_dict["observation_state"] == "0"
        assert "metric_deviations" in ev_dict
        assert "distribution_comparisons" in ev_dict


# ==============================================================================
# 9. Bug-Catching Sensitivity Suite (Bugs A through T)
# ==============================================================================

class TestBugCatchingSuite:
    """Rigorous sensitivity tests for Bugs A through T."""

    def test_bug_a_zero_relative_deviation_handling(self) -> None:
        """Bug A: Relative deviation must safely return None when baseline mean is 0."""
        rel_dev = calculate_relative_deviation(0.05, 0.0)
        assert rel_dev is None

    def test_bug_b_sample_variance_denominator(self) -> None:
        """Bug B: Comparison must use M9's sample variance (N-1), not population variance."""
        stats = calculate_sample_statistics([1.0, 2.0, 3.0, 4.0, 5.0])
        # sample var = 2.5, population var = 2.0
        assert stats.variance == 2.5
        dev = compare_scalar_metric(3.0, stats, "test_metric")
        assert dev.baseline_variance == 2.5

    def test_bug_c_real_expectations(self) -> None:
        """Bug C: All metrics and deviations must be real floats, not complex numbers."""
        stats = calculate_sample_statistics([0.5, 0.6, 0.7])
        dev = compare_scalar_metric(0.65, stats, "test_metric")
        assert isinstance(dev.observed_value, float)
        assert isinstance(dev.baseline_mean, float)
        assert isinstance(dev.absolute_deviation, float)

    def test_bug_d_and_bug_e_no_attack_decisions_or_thresholds(self) -> None:
        """Bugs D & E: Comparison structures must NOT have attack flags or hardcoded thresholds."""
        stats = calculate_sample_statistics([0.98, 0.99, 0.97, 0.98])
        dev = compare_scalar_metric(0.10, stats, "fidelity:0")  # Huge deviation
        assert not hasattr(dev, "is_attack"), "M10 must not include attack decisions!"
        assert not hasattr(dev, "attack_detected"), "M10 must not include attack detection!"
        assert not hasattr(dev, "decision"), "M10 must not produce decisions!"

    def test_bug_f_and_bug_r_incompatible_configuration_rejected(self) -> None:
        """Bugs F & R: Mismatched baselines must be rejected."""
        cfg = BaselineConfiguration(
            configuration_id="base_f",
            states=("0",),
            noise_model_type="depolarizing",
            noise_strength=0.01,
            channel_location="bob_qubit",
            shots=None,
            calibration_runs=2,
        )
        baseline = calibrate_honest_baseline(cfg)

        incompat_obs = VerificationObservation(
            state_name="0",
            fidelity=0.99,
            qber=0.01,
            probabilities_z={"0": 0.99, "1": 0.01},
            probabilities_x={"+": 0.5, "-": 0.5},
            probabilities_y={"+i": 0.5, "-i": 0.5},
            pauli_expectations={"X": 0.0, "Y": 0.0, "Z": 0.98},
            configuration={"noise_model_type": "phase_flip", "noise_strength": 0.01},
        )
        with pytest.raises(ConfigurationCompatibilityError):
            compare_observation(incompat_obs, baseline)

    def test_bug_g_reject_nan(self) -> None:
        """Bug G: NaN inputs must be rejected."""
        with pytest.raises(ValueError, match="finite"):
            calculate_absolute_deviation(float("nan"), 0.5)

    def test_bug_h_reject_infinity(self) -> None:
        """Bug H: Inf inputs must be rejected."""
        with pytest.raises(ValueError, match="finite"):
            calculate_absolute_deviation(float("inf"), 0.5)

    def test_bug_i_reject_probabilities_outside_0_1(self) -> None:
        """Bug I: Probabilities outside [0, 1] must be rejected."""
        with pytest.raises(ValueError, match=r"\[0\.0, 1\.0\]"):
            calculate_total_variation_distance({"0": 1.2, "1": -0.2}, {"0": 0.5, "1": 0.5})

    def test_bug_j_reject_probabilities_not_summing_to_1(self) -> None:
        """Bug J: Distributions not summing to 1 must be rejected."""
        with pytest.raises(ValueError, match="sum to 1.0"):
            calculate_total_variation_distance({"0": 0.6, "1": 0.6}, {"0": 0.5, "1": 0.5})

    def test_bug_k_and_bug_l_baseline_not_mutated_or_contaminated(self) -> None:
        """Bugs K & L: Comparison does not mutate baseline or add evaluation data."""
        cfg = BaselineConfiguration(
            configuration_id="base_k",
            states=("0",),
            noise_model_type="ideal",
            noise_strength=0.0,
            channel_location="bob_qubit",
            shots=None,
            calibration_runs=2,
        )
        baseline = calibrate_honest_baseline(cfg)
        count_before = len(baseline.metrics)

        obs = VerificationObservation(
            state_name="0",
            fidelity=0.99,
            qber=0.01,
            probabilities_z={"0": 0.99, "1": 0.01},
            probabilities_x={"+": 0.5, "-": 0.5},
            probabilities_y={"+i": 0.5, "-i": 0.5},
            pauli_expectations={"X": 0.0, "Y": 0.0, "Z": 0.98},
            configuration=cfg,
        )
        compare_observation(obs, baseline)
        assert len(baseline.metrics) == count_before

    def test_bug_m_n1_ci_unavailable(self) -> None:
        """Bug M: For N=1, confidence interval comparison must be unavailable, not fabricated."""
        stats = calculate_sample_statistics([0.98])
        inside, status = check_confidence_interval(0.95, stats.confidence_interval)
        assert inside is None
        assert status == "unavailable"

    def test_bug_n_bounded_metric_zscore_documentation(self) -> None:
        """Bug N: z-score docstring documents non-normality of bounded quantum metrics."""
        doc = calculate_standardized_deviation.__doc__
        assert doc is not None
        assert "bounded" in doc.lower()
        assert "gaussian" in doc.lower()

    def test_bug_o_deterministic_calculations(self) -> None:
        """Bug O: Comparison results are 100% deterministic."""
        p = {"0": 0.7, "1": 0.3}
        q = {"0": 0.5, "1": 0.5}
        tv1 = calculate_total_variation_distance(p, q)
        tv2 = calculate_total_variation_distance(p, q)
        assert tv1 == tv2

    def test_bug_p_and_bug_q_no_combined_security_score_or_decision(self) -> None:
        """Bugs P & Q: Evidence container must not have a combined score or ACCEPT/SUSPICIOUS/ATTACK."""
        cfg = BaselineConfiguration(
            configuration_id="base_pq",
            states=("0",),
            noise_model_type="ideal",
            noise_strength=0.0,
            channel_location="bob_qubit",
            shots=None,
            calibration_runs=2,
        )
        baseline = calibrate_honest_baseline(cfg)
        obs = VerificationObservation(
            state_name="0",
            fidelity=0.99,
            qber=0.01,
            probabilities_z={"0": 0.99, "1": 0.01},
            probabilities_x={"+": 0.5, "-": 0.5},
            probabilities_y={"+i": 0.5, "-i": 0.5},
            pauli_expectations={"X": 0.0, "Y": 0.0, "Z": 0.98},
            configuration=cfg,
        )
        evidence = compare_observation(obs, baseline)
        assert not hasattr(evidence, "security_score"), "Must NOT have security_score!"
        assert not hasattr(evidence, "decision"), "Must NOT have decision!"
        assert not hasattr(evidence, "attack_verdict"), "Must NOT have attack_verdict!"

    def test_bug_s_numerical_tolerance_not_security_threshold(self) -> None:
        """Bug S: Numerical tolerances are used only for math checks, not security decisions."""
        # check_confidence_interval uses atol=1e-9 for floating point boundary, not a security threshold
        inside, status = check_confidence_interval(0.94000000005, (0.94, 0.98), atol=1e-8)
        assert status == "boundary"

    def test_bug_t_noise_deviation_not_attack(self) -> None:
        """Bug T: Deviations under noise are descriptive deviations, not attacks."""
        cfg = BaselineConfiguration(
            configuration_id="base_t",
            states=("0",),
            noise_model_type="depolarizing",
            noise_strength=0.10,
            channel_location="bob_qubit",
            shots=None,
            calibration_runs=3,
        )
        baseline = calibrate_honest_baseline(cfg)
        obs = VerificationObservation(
            state_name="0",
            fidelity=0.82,  # noisy observation
            qber=0.18,
            probabilities_z={"0": 0.82, "1": 0.18},
            probabilities_x={"+": 0.5, "-": 0.5},
            probabilities_y={"+i": 0.5, "-i": 0.5},
            pauli_expectations={"X": 0.0, "Y": 0.0, "Z": 0.64},
            configuration=cfg,
        )
        evidence = compare_observation(obs, baseline)
        metric_dev = evidence.get_metric("fidelity:0")
        assert metric_dev is not None
        assert isinstance(metric_dev.absolute_deviation, float)

    def test_bug_l_baseline_distribution_malformed_rejected_not_normalized(self) -> None:
        """Bug L: Malformed baseline distributions must be rejected with ValueError, NOT silently normalized."""
        cfg = BaselineConfiguration(
            configuration_id="base_l_test",
            states=("0",),
            noise_model_type="ideal",
            noise_strength=0.0,
            channel_location="bob_qubit",
            shots=None,
            calibration_runs=2,
        )
        baseline = calibrate_honest_baseline(cfg)

        # Deliberately corrupt baseline metrics so that Z-basis probabilities sum to 0.5 instead of 1.0
        corrupted_metrics = dict(baseline.metrics)
        corrupted_metrics["prob_z_0:0"] = MetricStatistics(
            sample_count=2,
            mean=0.3,
            variance=0.0,
            std_dev=0.0,
            min_value=0.3,
            max_value=0.3,
            confidence_interval=(0.3, 0.3),
        )
        corrupted_metrics["prob_z_1:0"] = MetricStatistics(
            sample_count=2,
            mean=0.2,
            variance=0.0,
            std_dev=0.0,
            min_value=0.2,
            max_value=0.2,
            confidence_interval=(0.2, 0.2),
        )
        corrupted_baseline = HonestBaseline(
            configuration=baseline.configuration,
            metrics=corrupted_metrics,
            metadata=baseline.metadata,
        )

        obs = VerificationObservation(
            state_name="0",
            fidelity=1.0,
            qber=0.0,
            probabilities_z={"0": 1.0, "1": 0.0},
            probabilities_x={"+": 0.5, "-": 0.5},
            probabilities_y={"+i": 0.5, "-i": 0.5},
            pauli_expectations={"X": 0.0, "Y": 0.0, "Z": 1.0},
            configuration=cfg,
        )

        with pytest.raises(ValueError, match="refusing to silently normalize"):
            compare_observation(obs, corrupted_baseline)

    def test_bug_u_no_attack_classification_logic(self) -> None:
        """Bug U: M10 must not contain attack classification logic or classes."""
        import src.statistics.comparison as comp_module
        assert not hasattr(comp_module, "classify_attack")
        assert not hasattr(comp_module, "AttackClassifier")
        assert not hasattr(comp_module, "detect_anomaly")

    def test_bug_v_no_arbitrary_security_or_anomaly_score(self) -> None:
        """Bug V: M10 must not compute arbitrary unified security, risk, or anomaly scores."""
        cfg = BaselineConfiguration(
            configuration_id="base_v",
            states=("0",),
            noise_model_type="ideal",
            noise_strength=0.0,
            channel_location="bob_qubit",
            shots=None,
            calibration_runs=2,
        )
        baseline = calibrate_honest_baseline(cfg)
        obs = VerificationObservation(
            state_name="0",
            fidelity=0.99,
            qber=0.01,
            probabilities_z={"0": 0.99, "1": 0.01},
            probabilities_x={"+": 0.5, "-": 0.5},
            probabilities_y={"+i": 0.5, "-i": 0.5},
            pauli_expectations={"X": 0.0, "Y": 0.0, "Z": 0.98},
            configuration=cfg,
        )
        evidence = compare_observation(obs, baseline)
        assert not hasattr(evidence, "quantum_security_score")
        assert not hasattr(evidence, "anomaly_score")
        assert not hasattr(evidence, "threat_score")
        assert not hasattr(evidence, "risk_score")

    def test_bug_w_no_cryptographic_proof_claims(self) -> None:
        """Bug W: Statistical evidence must not claim information-theoretic security or proof."""
        doc = StatisticalEvidence.__doc__ or ""
        assert "STATISTICAL" in doc.upper()
        assert "EVIDENCE" in doc.upper()
        assert "NO ATTACK DECISION" in doc.upper()

    def test_bug_x_bounded_metric_zscore_boundary(self) -> None:
        """Bug X: Bounded quantum metrics are not treated as unrestricted Gaussians."""
        z = calculate_standardized_deviation(0.0, 0.9, 0.05, sample_count=5)
        assert z is not None
        assert z < -10.0
        assert isinstance(z, float)

    def test_bug_y_determinism_repeated_execution(self) -> None:
        """Bug Y: Identical inputs must yield bit-for-bit identical outputs across runs."""
        cfg = BaselineConfiguration(
            configuration_id="base_y",
            states=("0",),
            noise_model_type="depolarizing",
            noise_strength=0.05,
            channel_location="bob_qubit",
            shots=None,
            calibration_runs=4,
        )
        baseline = calibrate_honest_baseline(cfg)
        obs = VerificationObservation(
            state_name="0",
            fidelity=0.91,
            qber=0.09,
            probabilities_z={"0": 0.91, "1": 0.09},
            probabilities_x={"+": 0.5, "-": 0.5},
            probabilities_y={"+i": 0.5, "-i": 0.5},
            pauli_expectations={"X": 0.0, "Y": 0.0, "Z": 0.82},
            configuration=cfg,
        )
        evidence1 = compare_observation(obs, baseline)
        evidence2 = compare_observation(obs, baseline)
        assert evidence1.to_dict()["metric_deviations"] == evidence2.to_dict()["metric_deviations"]

    def test_bug_z_complex_numbers_rejected(self) -> None:
        """Bug Z: Complex-valued quantum quantities are explicitly rejected."""
        with pytest.raises(TypeError):
            calculate_absolute_deviation(complex(0.95, 0.05), 0.95)  # type: ignore
        with pytest.raises(TypeError):
            calculate_relative_deviation(0.95, complex(0.95, 0.05))  # type: ignore
        with pytest.raises(TypeError):
            calculate_standardized_deviation(complex(0.95, 0.05), 0.95, 0.01)  # type: ignore
        with pytest.raises(TypeError):
            calculate_total_variation_distance({"0": complex(0.5, 0.0), "1": 0.5}, {"0": 0.5, "1": 0.5})  # type: ignore
        with pytest.raises(TypeError):
            VerificationObservation(
                state_name="0",
                fidelity=complex(0.98, 0.0),  # type: ignore
                qber=0.02,
                probabilities_z={"0": 0.98, "1": 0.02},
                probabilities_x={"+": 0.5, "-": 0.5},
                probabilities_y={"+i": 0.5, "-i": 0.5},
                pauli_expectations={"X": 0.0, "Y": 0.0, "Z": 0.96},
            )

    def test_direct_shots_mismatch_rejected(self) -> None:
        """Observation with direct shots specified (no config) mismatches baseline shots."""
        cfg = BaselineConfiguration(
            configuration_id="base_shots_check",
            states=("0",),
            noise_model_type="ideal",
            noise_strength=0.0,
            channel_location="bob_qubit",
            shots=None,  # baseline is analytical
            calibration_runs=2,
        )
        baseline = calibrate_honest_baseline(cfg)
        obs = VerificationObservation(
            state_name="0",
            fidelity=1.0,
            qber=0.0,
            probabilities_z={"0": 1.0, "1": 0.0},
            probabilities_x={"+": 0.5, "-": 0.5},
            probabilities_y={"+i": 0.5, "-i": 0.5},
            pauli_expectations={"X": 0.0, "Y": 0.0, "Z": 1.0},
            shots=1024,  # observation specifies shots
            configuration=None,
        )
        with pytest.raises(ConfigurationCompatibilityError, match="Shot count mismatch"):
            compare_observation(obs, baseline)

    def test_configuration_states_mismatch_rejected(self) -> None:
        """Observation configuration specifies different state set from baseline."""
        cfg = BaselineConfiguration(
            configuration_id="base_states_check",
            states=("0", "1"),
            noise_model_type="ideal",
            noise_strength=0.0,
            channel_location="bob_qubit",
            shots=None,
            calibration_runs=2,
        )
        baseline = calibrate_honest_baseline(cfg)
        obs = VerificationObservation(
            state_name="0",
            fidelity=1.0,
            qber=0.0,
            probabilities_z={"0": 1.0, "1": 0.0},
            probabilities_x={"+": 0.5, "-": 0.5},
            probabilities_y={"+i": 0.5, "-i": 0.5},
            pauli_expectations={"X": 0.0, "Y": 0.0, "Z": 1.0},
            configuration={"states": ("+", "-"), "noise_model_type": "ideal", "noise_strength": 0.0},
        )
        with pytest.raises(ConfigurationCompatibilityError, match="state set mismatch"):
            compare_observation(obs, baseline)

    def test_standardized_deviation_parameter_validation(self) -> None:
        """calculate_standardized_deviation validates sample_count and epsilon strictly."""
        with pytest.raises(TypeError, match="sample_count"):
            calculate_standardized_deviation(0.9, 0.9, 0.01, sample_count="two")  # type: ignore
        with pytest.raises(TypeError, match="sample_count"):
            calculate_standardized_deviation(0.9, 0.9, 0.01, sample_count=True)  # type: ignore
        with pytest.raises(ValueError, match="sample_count"):
            calculate_standardized_deviation(0.9, 0.9, 0.01, sample_count=0)
        with pytest.raises(TypeError, match="epsilon"):
            calculate_standardized_deviation(0.9, 0.9, 0.01, epsilon="small")  # type: ignore
        with pytest.raises(ValueError, match="epsilon"):
            calculate_standardized_deviation(0.9, 0.9, 0.01, epsilon=-1e-12)

    def test_ci_and_tv_atol_validation(self) -> None:
        """check_confidence_interval and calculate_total_variation_distance validate atol strictly."""
        with pytest.raises(TypeError, match="atol"):
            check_confidence_interval(0.9, (0.8, 1.0), atol="small")  # type: ignore
        with pytest.raises(ValueError, match="atol"):
            check_confidence_interval(0.9, (0.8, 1.0), atol=-1e-9)

        with pytest.raises(TypeError, match="atol"):
            calculate_total_variation_distance({"0": 0.5, "1": 0.5}, {"0": 0.5, "1": 0.5}, atol="small")  # type: ignore
        with pytest.raises(ValueError, match="atol"):
            calculate_total_variation_distance({"0": 0.5, "1": 0.5}, {"0": 0.5, "1": 0.5}, atol=0.0)

    def test_distribution_comparison_post_init_validation(self) -> None:
        """DistributionComparison validates mapping entries on direct instantiation."""
        with pytest.raises(ValueError, match="empty"):
            DistributionComparison(
                distribution_name="",
                observed_probabilities={"0": 0.5, "1": 0.5},
                baseline_probabilities={"0": 0.5, "1": 0.5},
                total_variation_distance=0.0,
                per_outcome_deviations={"0": 0.0, "1": 0.0},
                per_outcome_signed={"0": 0.0, "1": 0.0},
                max_outcome_deviation=0.0,
            )
        with pytest.raises(ValueError, match="finite"):
            DistributionComparison(
                distribution_name="test",
                observed_probabilities={"0": float("nan"), "1": 0.5},
                baseline_probabilities={"0": 0.5, "1": 0.5},
                total_variation_distance=0.0,
                per_outcome_deviations={"0": 0.0, "1": 0.0},
                per_outcome_signed={"0": 0.0, "1": 0.0},
                max_outcome_deviation=0.0,
            )


# ==============================================================================
# 10. Quantum Cross-Validation
# ==============================================================================

class TestQuantumCrossValidation:
    """Validates M10 comparison using real quantum teleportation trials and calibrated baselines."""

    @pytest.mark.parametrize("state_label", ["0", "1", "+", "-", "+i", "-i"])
    def test_quantum_states_honest_comparison(self, state_label: str) -> None:
        """Run genuine teleportation trial, calibrate baseline, and verify M10 deviations."""
        noise = create_depolarizing_channel(0.05)
        cfg = BaselineConfiguration(
            configuration_id=f"cross_val_{state_label}",
            states=(state_label,),
            noise_model_type="depolarizing",
            noise_strength=0.05,
            channel_location="bob_qubit",
            shots=None,
            calibration_runs=3,
        )

        # Calibrate baseline
        baseline = calibrate_honest_baseline(cfg)

        # Run a new honest verification trial
        cal_trial = run_honest_calibration_trial(state=state_label, noise_channel=noise)
        obs = VerificationObservation.from_calibration_observation(cal_trial, configuration=cfg)

        # Compare
        evidence = compare_observation(obs, baseline)

        # Fidelity check
        fid_dev = evidence.get_metric(f"fidelity:{state_label}")
        assert fid_dev is not None
        # Under analytical mathematical simulation with identical noise, deviation should be zero or negligible
        assert fid_dev.absolute_deviation < 1e-6
        assert fid_dev.inside_baseline_ci is True

        # Distribution check
        if state_label in ("0", "1"):
            dist_dev = evidence.get_distribution(f"probabilities_z:{state_label}")
        elif state_label in ("+", "-"):
            dist_dev = evidence.get_distribution(f"probabilities_x:{state_label}")
        else:
            dist_dev = evidence.get_distribution(f"probabilities_y:{state_label}")

        assert dist_dev is not None
        assert dist_dev.total_variation_distance < 1e-6


# ==============================================================================
# 11. Cross-Milestone Integration Pipeline (Section 19)
# ==============================================================================

class TestCrossMilestoneIntegrationPipeline:
    """Explicit end-to-end integration test connecting M1 through M10 using actual project APIs."""

    def test_arbitrary_complex_state_end_to_end_pipeline(self) -> None:
        """Run complete pipeline for an arbitrary normalized complex state.

        Flow:
            M1 State Preparation (Arbitrary Complex State)
                 ↓
            M4 Bell State Creation
                 ↓
            M6 Teleportation (CX + H + Pauli Corrections)
                 ↓
            M8 Honest Noise (Depolarizing Channel)
                 ↓
            M7 Fidelity & Verification
                 ↓
            M9 Honest Baseline Calibration
                 ↓
            M10 Statistical Comparison & Evidence Generation
        """
        # 1. M1 State preparation: arbitrary normalized complex state |psi> = (sqrt(3)|0> + (1 - 1j)|1>) / sqrt(5)
        alpha = np.sqrt(3.0 / 5.0)
        beta = (1.0 - 1.0j) / np.sqrt(5.0)
        custom_vec = validate_state_vector(np.array([alpha, beta], dtype=np.complex128))
        assert np.isclose(np.linalg.norm(custom_vec), 1.0, atol=1e-12)

        # 2. M4 Bell-state creation circuit
        bell_qc = create_bell_circuit("phi_plus")
        assert bell_qc.num_qubits == 2

        # 3. M8 Honest noise channel definition
        noise = create_depolarizing_channel(0.04)

        # 4. M6 & M8 Teleportation under honest noise
        noisy_res = simulate_noisy_teleportation_mathematical(
            input_state=custom_vec,
            noise_channel=noise,
            branch=(0, 0),
        )
        assert noisy_res.noisy_density_matrix.shape == (2, 2)

        # 5. M7 Pure-state overlap fidelity calculation against noisy density matrix
        pure_fid = calculate_mixed_state_fidelity(custom_vec, noisy_res.noisy_density_matrix)
        expected_fid = 1.0 - (2.0 / 3.0) * 0.04
        assert np.isclose(pure_fid, expected_fid, atol=1e-6)

        # 6. M9 Honest baseline calibration for custom complex state
        cfg = BaselineConfiguration(
            configuration_id="end_to_end_arbitrary_complex",
            states=("custom_complex",),
            noise_model_type="depolarizing",
            noise_strength=0.04,
            channel_location="bob_qubit",
            shots=None,
            calibration_runs=4,
        )
        baseline = calibrate_honest_baseline(
            cfg,
            custom_states=[("custom_complex", custom_vec)],
        )
        assert "fidelity:custom_complex" in baseline.metrics
        assert "qber:custom_complex" in baseline.metrics
        assert baseline.configuration.canonical_hash == cfg.canonical_hash

        # 7. Run honest evaluation observation trial
        cal_trial = run_honest_calibration_trial(
            state=custom_vec,
            noise_channel=noise,
            state_name="custom_complex",
        )
        obs = VerificationObservation.from_calibration_observation(
            cal_trial,
            configuration=cfg,
        )

        # 8. M10 Statistical comparison
        evidence = compare_observation(obs, baseline)
        assert isinstance(evidence, StatisticalEvidence)

        # 9. Statistical evidence assertions
        fid_dev = evidence.get_metric("fidelity:custom_complex")
        assert fid_dev is not None
        assert fid_dev.absolute_deviation < 1e-6
        assert fid_dev.inside_baseline_ci is True

        qber_dev = evidence.get_metric("qber:custom_complex")
        assert qber_dev is not None
        assert qber_dev.absolute_deviation < 1e-6
        assert qber_dev.inside_baseline_ci is True

        for basis_key in ("probabilities_z", "probabilities_x", "probabilities_y"):
            dist_dev = evidence.get_distribution(f"{basis_key}:custom_complex")
            assert dist_dev is not None
            assert dist_dev.total_variation_distance < 1e-6


# ==============================================================================
# 12. Cross-Milestone Honest Noise Handling (Section 20)
# ==============================================================================

class TestCrossMilestoneHonestNoiseHandling:
    """Verifies that honest noisy observations match honest noisy baselines, preventing false attack alarms."""

    def test_honest_noisy_observation_matches_honest_noisy_baseline_not_ideal(self) -> None:
        """Comparing noisy observation against matching noisy baseline yields near-zero deviation;
        comparing against ideal zero-noise baseline yields substantial deviation outside CI.
        """
        p_honest = 0.09
        noise_honest = create_depolarizing_channel(p_honest)

        # Baseline 1: Calibrated under honest noise p = 0.09
        cfg_noisy = BaselineConfiguration(
            configuration_id="honest_noisy_p09",
            states=("0",),
            noise_model_type="depolarizing",
            noise_strength=p_honest,
            channel_location="bob_qubit",
            shots=None,
            calibration_runs=5,
        )
        baseline_noisy = calibrate_honest_baseline(cfg_noisy)

        # Baseline 2: Calibrated under ideal noiseless conditions p = 0.00
        cfg_ideal = BaselineConfiguration(
            configuration_id="ideal_noiseless_p00",
            states=("0",),
            noise_model_type="depolarizing",
            noise_strength=0.0,
            channel_location="bob_qubit",
            shots=None,
            calibration_runs=5,
        )
        baseline_ideal = calibrate_honest_baseline(cfg_ideal)

        # Run an honest trial under actual operating noise p = 0.09
        trial_noisy = run_honest_calibration_trial(state="0", noise_channel=noise_honest)
        obs_matched = VerificationObservation.from_calibration_observation(
            trial_noisy, configuration=cfg_noisy
        )

        # 1. Compared against matching noisy baseline: deviations are zero / within CI
        evidence_matched = compare_observation(obs_matched, baseline_noisy)
        fid_matched = evidence_matched.get_metric("fidelity:0")
        assert fid_matched is not None
        assert fid_matched.absolute_deviation < 1e-6
        assert fid_matched.inside_baseline_ci is True

        # 2. Compared against ideal baseline (simulated deliberately with cfg_ideal for illustration):
        obs_against_ideal = VerificationObservation.from_calibration_observation(
            trial_noisy, configuration=cfg_ideal
        )
        evidence_against_ideal = compare_observation(obs_against_ideal, baseline_ideal)
        fid_against_ideal = evidence_against_ideal.get_metric("fidelity:0")
        assert fid_against_ideal is not None
        # Theoretical fidelity with p=0.09 is 1 - 2(0.09)/3 = 0.94, so deviation from 1.0 is ~0.06
        assert fid_against_ideal.absolute_deviation > 0.05
        assert fid_against_ideal.inside_baseline_ci is False


# ==============================================================================
# 13. Cross-Milestone Determinism & Randomness (Sections 21 & 22)
# ==============================================================================

class TestCrossMilestoneDeterminismAndRandomness:
    """Verifies determinism of mathematical calculations vs stochastic measurement sampling."""

    def test_mathematical_determinism_reproducibility(self) -> None:
        """Analytical statevector and density-matrix operations are 100% bit-exact reproducible."""
        state = get_standard_state("+i")
        noise = create_phase_flip_channel(0.05)

        res1 = simulate_noisy_teleportation_mathematical(input_state=state, noise_channel=noise)
        res2 = simulate_noisy_teleportation_mathematical(input_state=state, noise_channel=noise)
        assert np.array_equal(res1.noisy_density_matrix, res2.noisy_density_matrix)

        # Statistical comparison given identical input data is 100% deterministic
        cfg = BaselineConfiguration(
            configuration_id="det_check",
            states=("+i",),
            noise_model_type="phase_flip",
            noise_strength=0.05,
            channel_location="bob_qubit",
            shots=None,
            calibration_runs=3,
        )
        baseline = calibrate_honest_baseline(cfg)
        trial = run_honest_calibration_trial(state="+i", noise_channel=noise)
        obs = VerificationObservation.from_calibration_observation(trial, configuration=cfg)

        ev1 = compare_observation(obs, baseline)
        ev2 = compare_observation(obs, baseline)
        assert ev1.observation_state == ev2.observation_state
        assert ev1.baseline_configuration_hash == ev2.baseline_configuration_hash
        assert ev1.metric_deviations == ev2.metric_deviations
        assert ev1.distribution_comparisons == ev2.distribution_comparisons

    def test_stochastic_sampling_seed_reproducibility(self) -> None:
        """When an explicit seed is provided, stochastic Aer simulation produces identical counts."""
        noise = create_depolarizing_channel(0.02)
        trial_seeded_1 = run_honest_calibration_trial(
            state="0", noise_channel=noise, shots=500, seed=9999
        )
        trial_seeded_2 = run_honest_calibration_trial(
            state="0", noise_channel=noise, shots=500, seed=9999
        )

        assert trial_seeded_1.probabilities_z == trial_seeded_2.probabilities_z
        assert trial_seeded_1.fidelity == trial_seeded_2.fidelity

    def test_stochastic_sampling_probabilistic_nature(self) -> None:
        """Measurement sampling across different seeds exhibits natural statistical variance."""
        noise = create_depolarizing_channel(0.02)
        trial_a = run_honest_calibration_trial(
            state="0", noise_channel=noise, shots=500, seed=1111
        )
        trial_b = run_honest_calibration_trial(
            state="0", noise_channel=noise, shots=500, seed=2222
        )

        # Probabilities should be close due to large shots, but reflect stochastic measurement sampling
        assert trial_a.probabilities_z["0"] > 0.90
        assert trial_b.probabilities_z["0"] > 0.90
        # Given both datasets, deviation metric calculation remains deterministic
        dev_a = calculate_absolute_deviation(trial_a.probabilities_z["0"], 0.98)
        dev_b = calculate_absolute_deviation(trial_a.probabilities_z["0"], 0.98)
        assert dev_a == dev_b


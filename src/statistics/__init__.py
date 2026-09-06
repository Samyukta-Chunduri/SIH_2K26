"""Q-SHIELD — Statistical Analysis & Calibration Package (Milestones M9 & M10).

Provides data structures, sample statistics calculations, honest baseline
calibration engines, and statistical comparison engines for quantum verification:
    - MetricStatistics
    - BaselineConfiguration
    - CalibrationObservation
    - HonestBaseline
    - MetricDeviation
    - DistributionComparison
    - VerificationObservation
    - StatisticalEvidence
    - ConfigurationCompatibilityError
    - calculate_sample_statistics
    - validate_baseline
    - run_honest_calibration_trial
    - calibrate_honest_baseline
    - calibrate_noise_sweep
    - calculate_absolute_deviation
    - calculate_relative_deviation
    - calculate_standard_error
    - calculate_standardized_deviation
    - check_confidence_interval
    - calculate_total_variation_distance
    - compare_probability_distributions
    - compare_scalar_metric
    - check_configuration_compatibility
    - validate_configuration_compatibility
    - compare_observation
"""

from .baseline import (
    BaselineConfiguration,
    CalibrationObservation,
    HonestBaseline,
    MetricStatistics,
    calculate_sample_statistics,
    validate_baseline,
)
from .calibration import (
    STANDARD_STATE_NAMES,
    build_honest_baseline_from_observations,
    calibrate_honest_baseline,
    calibrate_noise_sweep,
    run_honest_calibration_trial,
)
from .comparison import (
    ConfigurationCompatibilityError,
    DistributionComparison,
    MetricDeviation,
    StatisticalEvidence,
    VerificationObservation,
    calculate_absolute_deviation,
    calculate_relative_deviation,
    calculate_standard_error,
    calculate_standardized_deviation,
    calculate_total_variation_distance,
    check_confidence_interval,
    check_configuration_compatibility,
    compare_observation,
    compare_probability_distributions,
    compare_scalar_metric,
    validate_configuration_compatibility,
)

__all__ = [
    "BaselineConfiguration",
    "CalibrationObservation",
    "ConfigurationCompatibilityError",
    "DistributionComparison",
    "HonestBaseline",
    "MetricDeviation",
    "MetricStatistics",
    "STANDARD_STATE_NAMES",
    "StatisticalEvidence",
    "VerificationObservation",
    "build_honest_baseline_from_observations",
    "calculate_absolute_deviation",
    "calculate_relative_deviation",
    "calculate_sample_statistics",
    "calculate_standard_error",
    "calculate_standardized_deviation",
    "calculate_total_variation_distance",
    "calibrate_honest_baseline",
    "calibrate_noise_sweep",
    "check_confidence_interval",
    "check_configuration_compatibility",
    "compare_observation",
    "compare_probability_distributions",
    "compare_scalar_metric",
    "run_honest_calibration_trial",
    "validate_baseline",
    "validate_configuration_compatibility",
]

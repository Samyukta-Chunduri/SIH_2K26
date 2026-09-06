"""Q-SHIELD — Statistical Analysis, Baseline & Threshold Policy Package (M9–M11).

Provides data structures, sample statistics calculations, honest baseline
calibration engines, statistical comparison engines, and threshold policies
for quantum signature verification:
    - MetricStatistics
    - BaselineConfiguration
    - CalibrationObservation
    - HonestBaseline
    - MetricDeviation
    - DistributionComparison
    - VerificationObservation
    - StatisticalEvidence
    - ConfigurationCompatibilityError
    - MetricThreshold
    - ThresholdPolicy
    - MetricThresholdEvaluation
    - PolicyEvaluationReport
    - ThresholdDirection
    - ThresholdMethod
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
    - calculate_policy_fingerprint
    - calculate_empirical_quantile_threshold
    - calculate_statistical_multiplier_threshold
    - resolve_metric_direction
    - calibrate_metric_threshold
    - calibrate_threshold_policy
    - evaluate_metric_threshold
    - evaluate_policy
    - evaluate_policy_false_alarm_rate
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
from .thresholds import (
    MetricThreshold,
    MetricThresholdEvaluation,
    PolicyEvaluationReport,
    ThresholdDirection,
    ThresholdMethod,
    ThresholdPolicy,
    calculate_empirical_quantile_threshold,
    calculate_policy_fingerprint,
    calculate_statistical_multiplier_threshold,
    calibrate_metric_threshold,
    calibrate_threshold_policy,
    evaluate_metric_threshold,
    evaluate_policy,
    evaluate_policy_false_alarm_rate,
    resolve_metric_direction,
)

__all__ = [
    "BaselineConfiguration",
    "CalibrationObservation",
    "ConfigurationCompatibilityError",
    "DistributionComparison",
    "HonestBaseline",
    "MetricDeviation",
    "MetricStatistics",
    "MetricThreshold",
    "MetricThresholdEvaluation",
    "PolicyEvaluationReport",
    "STANDARD_STATE_NAMES",
    "StatisticalEvidence",
    "ThresholdDirection",
    "ThresholdMethod",
    "ThresholdPolicy",
    "VerificationObservation",
    "build_honest_baseline_from_observations",
    "calculate_absolute_deviation",
    "calculate_empirical_quantile_threshold",
    "calculate_policy_fingerprint",
    "calculate_relative_deviation",
    "calculate_sample_statistics",
    "calculate_standard_error",
    "calculate_standardized_deviation",
    "calculate_statistical_multiplier_threshold",
    "calculate_total_variation_distance",
    "calibrate_honest_baseline",
    "calibrate_metric_threshold",
    "calibrate_noise_sweep",
    "calibrate_threshold_policy",
    "check_confidence_interval",
    "check_configuration_compatibility",
    "compare_observation",
    "compare_probability_distributions",
    "compare_scalar_metric",
    "evaluate_metric_threshold",
    "evaluate_policy",
    "evaluate_policy_false_alarm_rate",
    "resolve_metric_direction",
    "run_honest_calibration_trial",
    "validate_baseline",
    "validate_configuration_compatibility",
]

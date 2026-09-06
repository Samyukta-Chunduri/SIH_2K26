"""Q-SHIELD — Statistical Analysis & Comparison Engine (Milestone M10).

Implements the statistical comparison layer that compares newly observed quantum
verification results against honest baseline models produced by M9.

Conceptual Pipeline:
    New Observation
          ↓
    M9 Honest Baseline
          ↓
    Statistical Comparison Engine
          ↓
    Deviation Metrics (Absolute, Relative, Z-Score, TV Distance, CI Containment)
          ↓
    Statistical Evidence (Immutable Container)

Scientific Boundaries:
    - M10 produces STATISTICAL EVIDENCE ONLY.
    - Strictly NO attack detection, NO security decision thresholds, and NO threat classification.
    - Strictly NO ACCEPT / SUSPICIOUS / ATTACK decisions (reserved for M11/M12).
    - Strictly NO AI/ML, neural networks, anomaly classifiers, or heuristic scoring.
    - Strictly NO combined "security score" or evidence fusion.
    - Preserves baseline immutability; never alters or contaminates calibration data.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import math
from typing import Any
import numpy as np

from .baseline import (
    BaselineConfiguration,
    CalibrationObservation,
    HonestBaseline,
    MetricStatistics,
)


class ConfigurationCompatibilityError(ValueError):
    """Raised when an observation is compared against an incompatible baseline configuration."""


@dataclass(frozen=True)
class MetricDeviation:
    """Immutable descriptive deviation evidence for a single scalar metric against baseline.

    Attributes:
        metric_name: Identifier of the metric (e.g., 'fidelity:0', 'qber:+', 'exp_z:0').
        observed_value: Newly observed scalar value x.
        baseline_mean: Honest baseline mean mu.
        baseline_variance: Honest baseline sample variance s^2 with N-1 denominator.
        baseline_std_dev: Honest baseline sample standard deviation s = sqrt(s^2).
        baseline_sample_count: Number of honest calibration trials N >= 1.
        absolute_deviation: Generic absolute deviation d = |x - mu|.
        signed_deviation: Signed point deviation delta = x - mu.
        relative_deviation: Relative deviation d_rel = |x - mu| / |mu| if |mu| >= 1e-12, else None.
        standard_error: Baseline standard error of the mean SE = s / sqrt(N) if N >= 2, else None.
        standardized_deviation: Standardized deviation z = (x - mu) / s if s > 1e-12 and N >= 2, else None.
        baseline_confidence_interval: Clamped baseline confidence interval (lower, upper) if N >= 2, else None.
        inside_baseline_ci: Whether observed value lies within the baseline CI (None if CI unavailable).
        ci_status: Qualitative interval position: 'inside', 'outside', 'boundary', or 'unavailable'.
    """

    metric_name: str
    observed_value: float
    baseline_mean: float
    baseline_variance: float
    baseline_std_dev: float
    baseline_sample_count: int
    absolute_deviation: float
    signed_deviation: float
    relative_deviation: float | None
    standard_error: float | None
    standardized_deviation: float | None
    baseline_confidence_interval: tuple[float, float] | None
    inside_baseline_ci: bool | None
    ci_status: str

    def __post_init__(self) -> None:
        """Validate structural and numerical invariants."""
        if not self.metric_name.strip():
            raise ValueError("metric_name cannot be empty.")

        for name, val in [
            ("observed_value", self.observed_value),
            ("baseline_mean", self.baseline_mean),
            ("baseline_variance", self.baseline_variance),
            ("baseline_std_dev", self.baseline_std_dev),
            ("absolute_deviation", self.absolute_deviation),
            ("signed_deviation", self.signed_deviation),
        ]:
            if not isinstance(val, (int, float, np.floating)) or isinstance(val, bool):
                raise TypeError(f"{name} must be numeric float, got {type(val).__name__}.")
            if not math.isfinite(float(val)):
                raise ValueError(f"{name} must be finite, got {val}.")

        if self.absolute_deviation < -1e-12:
            raise ValueError(f"absolute_deviation must be non-negative, got {self.absolute_deviation}.")

        if self.relative_deviation is not None:
            if not isinstance(self.relative_deviation, (int, float, np.floating)) or isinstance(self.relative_deviation, bool):
                raise TypeError(f"relative_deviation must be float or None, got {type(self.relative_deviation).__name__}.")
            if not math.isfinite(float(self.relative_deviation)):
                raise ValueError(f"relative_deviation must be finite, got {self.relative_deviation}.")
            if self.relative_deviation < -1e-12:
                raise ValueError(f"relative_deviation must be non-negative, got {self.relative_deviation}.")

        if self.standard_error is not None:
            if not isinstance(self.standard_error, (int, float, np.floating)) or isinstance(self.standard_error, bool):
                raise TypeError(f"standard_error must be float or None, got {type(self.standard_error).__name__}.")
            if not math.isfinite(float(self.standard_error)):
                raise ValueError(f"standard_error must be finite, got {self.standard_error}.")
            if self.standard_error < -1e-12:
                raise ValueError(f"standard_error must be non-negative, got {self.standard_error}.")

        if self.standardized_deviation is not None:
            if not isinstance(self.standardized_deviation, (int, float, np.floating)) or isinstance(self.standardized_deviation, bool):
                raise TypeError(f"standardized_deviation must be float or None, got {type(self.standardized_deviation).__name__}.")
            if not math.isfinite(float(self.standardized_deviation)):
                raise ValueError(f"standardized_deviation must be finite, got {self.standardized_deviation}.")

        if self.ci_status not in ("inside", "outside", "boundary", "unavailable"):
            raise ValueError(f"ci_status must be one of 'inside', 'outside', 'boundary', 'unavailable', got '{self.ci_status}'.")


@dataclass(frozen=True)
class DistributionComparison:
    """Immutable comparison evidence between an observed and baseline probability distribution.

    Attributes:
        distribution_name: Identifier of the measurement basis/distribution (e.g. 'probabilities_z:0').
        observed_probabilities: Empirical Born probability distribution P_obs.
        baseline_probabilities: Baseline expected Born probability distribution P_base.
        total_variation_distance: TV(P, Q) = 0.5 * sum_i |P_i - Q_i| in [0.0, 1.0].
        per_outcome_deviations: Mapping of outcome labels to absolute deviation |P_obs(i) - P_base(i)|.
        per_outcome_signed: Mapping of outcome labels to signed deviation P_obs(i) - P_base(i).
        max_outcome_deviation: Maximum absolute deviation across all outcomes in support.
    """

    distribution_name: str
    observed_probabilities: dict[str, float]
    baseline_probabilities: dict[str, float]
    total_variation_distance: float
    per_outcome_deviations: dict[str, float]
    per_outcome_signed: dict[str, float]
    max_outcome_deviation: float

    def __post_init__(self) -> None:
        """Validate distribution bounds, finite values, and enforce immutability."""
        if not self.distribution_name.strip():
            raise ValueError("distribution_name cannot be empty.")

        if not isinstance(self.total_variation_distance, (int, float, np.floating)) or isinstance(self.total_variation_distance, bool):
            raise TypeError("total_variation_distance must be float.")
        if not math.isfinite(float(self.total_variation_distance)):
            raise ValueError("total_variation_distance must be finite.")
        if not (-1e-7 <= float(self.total_variation_distance) <= 1.0 + 1e-7):
            raise ValueError(f"total_variation_distance must be in [0.0, 1.0], got {self.total_variation_distance}.")

        for d_name, d_map in [
            ("observed_probabilities", self.observed_probabilities),
            ("baseline_probabilities", self.baseline_probabilities),
            ("per_outcome_deviations", self.per_outcome_deviations),
            ("per_outcome_signed", self.per_outcome_signed),
        ]:
            if not isinstance(d_map, Mapping):
                raise TypeError(f"{d_name} must be a Mapping, got {type(d_map).__name__}.")
            for outcome, val in d_map.items():
                if not isinstance(outcome, str):
                    raise TypeError(f"Outcome label in {d_name} must be string, got {type(outcome).__name__}.")
                if not isinstance(val, (int, float, np.floating)) or isinstance(val, bool):
                    raise TypeError(f"Value for '{outcome}' in {d_name} must be float, got {type(val).__name__}.")
                if not math.isfinite(float(val)):
                    raise ValueError(f"Value for '{outcome}' in {d_name} must be finite, got {val}.")

        # Defensive copies
        object.__setattr__(self, "observed_probabilities", dict(self.observed_probabilities))
        object.__setattr__(self, "baseline_probabilities", dict(self.baseline_probabilities))
        object.__setattr__(self, "per_outcome_deviations", dict(self.per_outcome_deviations))
        object.__setattr__(self, "per_outcome_signed", dict(self.per_outcome_signed))


@dataclass(frozen=True)
class VerificationObservation:
    """Immutable container for verification trial metrics collected during system evaluation.

    Distinct from CalibrationObservation:
        - Used for evaluation and testing observations (untrusted, under evaluation, or candidate runs).
        - Can be compared against an HonestBaseline without risk of contaminating baseline data.
    """

    state_name: str
    fidelity: float
    qber: float
    probabilities_z: dict[str, float]
    probabilities_x: dict[str, float]
    probabilities_y: dict[str, float]
    pauli_expectations: dict[str, float]
    bell_correlations: dict[str, float] | None = None
    shots: int | None = None
    branch: tuple[int, int] = (0, 0)
    configuration: BaselineConfiguration | dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        """Validate physical and structural invariants."""
        if not self.state_name.strip():
            raise ValueError("state_name cannot be empty.")

        for name, val in [("fidelity", self.fidelity), ("qber", self.qber)]:
            if not isinstance(val, (int, float, np.floating)) or isinstance(val, bool):
                raise TypeError(f"{name} must be numeric float, got {type(val).__name__}.")
            if not math.isfinite(float(val)):
                raise ValueError(f"{name} must be finite, got {val}.")
            if not (-1e-7 <= float(val) <= 1.0 + 1e-7):
                raise ValueError(f"{name} must be in [0.0, 1.0], got {val}.")

        for basis_name, prob_dict in [
            ("probabilities_z", self.probabilities_z),
            ("probabilities_x", self.probabilities_x),
            ("probabilities_y", self.probabilities_y),
        ]:
            if not isinstance(prob_dict, dict):
                raise TypeError(f"{basis_name} must be a dictionary.")
            for outcome, prob in prob_dict.items():
                if not isinstance(outcome, str):
                    raise TypeError(f"Outcome label in {basis_name} must be string, got {type(outcome).__name__}.")
                if not isinstance(prob, (int, float, np.floating)) or isinstance(prob, bool):
                    raise TypeError(f"Probability for outcome '{outcome}' in {basis_name} must be float.")
                if not math.isfinite(float(prob)):
                    raise ValueError(f"Probability for outcome '{outcome}' in {basis_name} must be finite.")
                if not (-1e-7 <= float(prob) <= 1.0 + 1e-7):
                    raise ValueError(f"Probability for outcome '{outcome}' in {basis_name} must be in [0, 1], got {prob}.")

            if prob_dict:
                prob_sum = sum(prob_dict.values())
                if not math.isclose(prob_sum, 1.0, abs_tol=1e-4):
                    raise ValueError(f"Probabilities in {basis_name} must sum to 1.0 within tolerance, got {prob_sum}.")

        if not isinstance(self.pauli_expectations, dict):
            raise TypeError("pauli_expectations must be a dictionary.")
        for op, exp_val in self.pauli_expectations.items():
            if not isinstance(op, str):
                raise TypeError(f"Pauli operator key must be string, got {type(op).__name__}.")
            if not isinstance(exp_val, (int, float, np.floating)) or isinstance(exp_val, bool):
                raise TypeError(f"Expectation for Pauli '{op}' must be float.")
            if not math.isfinite(float(exp_val)):
                raise ValueError(f"Expectation for Pauli '{op}' must be finite.")
            if not (-1.0 - 1e-7 <= float(exp_val) <= 1.0 + 1e-7):
                raise ValueError(f"Expectation for Pauli '{op}' must be in [-1.0, 1.0], got {exp_val}.")

        if self.bell_correlations is not None:
            if not isinstance(self.bell_correlations, dict):
                raise TypeError("bell_correlations must be a dictionary or None.")
            for b_op, b_val in self.bell_correlations.items():
                if not isinstance(b_op, str):
                    raise TypeError(f"Bell correlation operator key must be string, got {type(b_op).__name__}.")
                if not isinstance(b_val, (int, float, np.floating)) or isinstance(b_val, bool):
                    raise TypeError(f"Bell correlation for '{b_op}' must be float.")
                if not math.isfinite(float(b_val)):
                    raise ValueError(f"Bell correlation for '{b_op}' must be finite.")
                if not (-1.0 - 1e-7 <= float(b_val) <= 1.0 + 1e-7):
                    raise ValueError(f"Bell correlation for '{b_op}' must be in [-1.0, 1.0], got {b_val}.")

        if self.shots is not None:
            if not isinstance(self.shots, (int, np.integer)) or isinstance(self.shots, bool):
                raise TypeError(f"shots must be integer, got {type(self.shots).__name__}.")
            if int(self.shots) <= 0:
                raise ValueError(f"shots must be a strictly positive integer, got {self.shots}.")

        # Defensive copies
        object.__setattr__(self, "probabilities_z", dict(self.probabilities_z))
        object.__setattr__(self, "probabilities_x", dict(self.probabilities_x))
        object.__setattr__(self, "probabilities_y", dict(self.probabilities_y))
        object.__setattr__(self, "pauli_expectations", dict(self.pauli_expectations))
        if self.bell_correlations is not None:
            object.__setattr__(self, "bell_correlations", dict(self.bell_correlations))
        if self.metadata is not None:
            object.__setattr__(self, "metadata", dict(self.metadata))

    @classmethod
    def from_calibration_observation(
        cls,
        obs: CalibrationObservation,
        configuration: BaselineConfiguration | dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> VerificationObservation:
        """Construct a VerificationObservation from an existing CalibrationObservation."""
        return cls(
            state_name=obs.state_name,
            fidelity=obs.fidelity,
            qber=obs.qber,
            probabilities_z=obs.probabilities_z,
            probabilities_x=obs.probabilities_x,
            probabilities_y=obs.probabilities_y,
            pauli_expectations=obs.pauli_expectations,
            bell_correlations=obs.bell_correlations,
            shots=obs.shots,
            branch=obs.branch,
            configuration=configuration,
            metadata=metadata,
        )


@dataclass(frozen=True)
class StatisticalEvidence:
    """Immutable collection of statistical comparison evidence across all evaluated metrics.

    Scientific Principle:
        Contains descriptive deviation metrics and distribution comparisons only.
        Contains strictly NO attack decision, NO threshold check, and NO security score.
    """

    observation_state: str
    baseline_configuration_hash: str
    metric_deviations: dict[str, MetricDeviation]
    distribution_comparisons: dict[str, DistributionComparison]
    configuration_compatibility: dict[str, Any]
    timestamp: str
    metadata: dict[str, Any]

    def __post_init__(self) -> None:
        """Enforce defensive copying and structural validation."""
        object.__setattr__(self, "metric_deviations", dict(self.metric_deviations))
        object.__setattr__(self, "distribution_comparisons", dict(self.distribution_comparisons))
        object.__setattr__(self, "configuration_compatibility", dict(self.configuration_compatibility))
        object.__setattr__(self, "metadata", dict(self.metadata))

    def get_metric(self, name: str) -> MetricDeviation | None:
        """Retrieve deviation evidence for a specific metric by name."""
        return self.metric_deviations.get(name)

    def get_distribution(self, name: str) -> DistributionComparison | None:
        """Retrieve distribution comparison evidence by name."""
        return self.distribution_comparisons.get(name)

    def to_dict(self) -> dict[str, Any]:
        """Serialize statistical evidence into a JSON-serializable dictionary."""
        return {
            "observation_state": self.observation_state,
            "baseline_configuration_hash": self.baseline_configuration_hash,
            "metric_deviations": {k: asdict(v) for k, v in self.metric_deviations.items()},
            "distribution_comparisons": {k: asdict(v) for k, v in self.distribution_comparisons.items()},
            "configuration_compatibility": dict(self.configuration_compatibility),
            "timestamp": self.timestamp,
            "metadata": dict(self.metadata),
        }


# ==============================================================================
# Core Mathematical Routines
# ==============================================================================

def calculate_absolute_deviation(observed: float, baseline_mean: float) -> float:
    """Calculate absolute deviation between an observed scalar and baseline mean.

    Formula:
        d = |x - mu|

    Args:
        observed: Newly observed scalar value x.
        baseline_mean: Honest baseline mean mu.

    Returns:
        Absolute deviation d >= 0.0.

    Raises:
        TypeError: If arguments are non-numeric or boolean.
        ValueError: If arguments are non-finite.
    """
    for name, val in [("observed", observed), ("baseline_mean", baseline_mean)]:
        if not isinstance(val, (int, float, np.floating)) or isinstance(val, bool):
            raise TypeError(f"{name} must be numeric float, got {type(val).__name__}.")
        if not math.isfinite(float(val)):
            raise ValueError(f"{name} must be finite, got {val}.")

    return float(abs(float(observed) - float(baseline_mean)))


def calculate_relative_deviation(
    observed: float,
    baseline_mean: float,
    epsilon: float = 1e-12,
) -> float | None:
    """Calculate relative deviation where mathematically well-defined.

    Formula:
        d_rel = |x - mu| / |mu|,  for |mu| >= epsilon.
        d_rel = None,             for |mu| < epsilon (undefined division).

    Scientific Boundary:
        For baseline means at or near zero (e.g., zero error rate under ideal teleportation),
        relative deviation is mathematically undefined. Rather than silently producing
        infinity or NaN, this function explicitly returns None.

    Args:
        observed: Newly observed scalar value x.
        baseline_mean: Honest baseline mean mu.
        epsilon: Positive numerical threshold below which denominator is treated as zero.

    Returns:
        Relative deviation d_rel >= 0.0, or None if baseline_mean is near zero.

    Raises:
        TypeError: If arguments are non-numeric or boolean.
        ValueError: If arguments are non-finite or epsilon <= 0.
    """
    for name, val in [("observed", observed), ("baseline_mean", baseline_mean)]:
        if not isinstance(val, (int, float, np.floating)) or isinstance(val, bool):
            raise TypeError(f"{name} must be numeric float, got {type(val).__name__}.")
        if not math.isfinite(float(val)):
            raise ValueError(f"{name} must be finite, got {val}.")

    if not isinstance(epsilon, (int, float, np.floating)) or isinstance(epsilon, bool):
        raise TypeError(f"epsilon must be numeric float, got {type(epsilon).__name__}.")
    if not math.isfinite(float(epsilon)) or float(epsilon) <= 0.0:
        raise ValueError(f"epsilon must be positive finite float, got {epsilon}.")

    abs_mu = abs(float(baseline_mean))
    if abs_mu < float(epsilon):
        return None

    abs_diff = abs(float(observed) - float(baseline_mean))
    return float(abs_diff / abs_mu)


def calculate_standard_error(sample_std: float, sample_count: int) -> float | None:
    """Calculate standard error of the baseline mean.

    Formula:
        SE = s / sqrt(N),  for N >= 2.
        SE = None,         for N == 1 (sampling error undefined).

    Args:
        sample_std: Sample standard deviation s >= 0.0.
        sample_count: Number of repeated observations N >= 1.

    Returns:
        Standard error SE >= 0.0, or None for N == 1.

    Raises:
        TypeError: If arguments have invalid types.
        ValueError: If sample_count < 1, sample_std < 0, or values non-finite.
    """
    if not isinstance(sample_count, (int, np.integer)) or isinstance(sample_count, bool):
        raise TypeError(f"sample_count must be integer, got {type(sample_count).__name__}.")
    if int(sample_count) < 1:
        raise ValueError(f"sample_count must be >= 1, got {sample_count}.")

    if not isinstance(sample_std, (int, float, np.floating)) or isinstance(sample_std, bool):
        raise TypeError(f"sample_std must be numeric float, got {type(sample_std).__name__}.")
    if not math.isfinite(float(sample_std)):
        raise ValueError(f"sample_std must be finite, got {sample_std}.")
    if float(sample_std) < -1e-12:
        raise ValueError(f"sample_std must be non-negative, got {sample_std}.")

    if int(sample_count) == 1:
        return None

    return float(max(0.0, float(sample_std)) / math.sqrt(int(sample_count)))


def calculate_standardized_deviation(
    observed: float,
    baseline_mean: float,
    baseline_std: float,
    sample_count: int = 2,
    epsilon: float = 1e-12,
) -> float | None:
    """Calculate standardized deviation (z-score) using sample standard deviation as scale.

    Formula:
        z = (x - mu) / s,  for s > epsilon and sample_count >= 2.
        z = 0.0,           for s <= epsilon and |x - mu| <= epsilon.
        z = None,          for s <= epsilon and |x - mu| > epsilon (undefined division).
        z = None,          for sample_count < 2 (insufficient sample size).

    Scientific Boundary:
        1. A standardized deviation is descriptive evidence measuring the number of sample
           standard deviations the observed point lies from the sample mean.
        2. It assumes that baseline sample standard deviation s provides a meaningful scale.
        3. For bounded quantum metrics (fidelity in [0, 1], expectations in [-1, 1]) and small N,
           distributions may be non-Gaussian.
        4. NEVER interpret |z| > 2 or |z| > 3 as an attack. No decision thresholds are applied.

    Args:
        observed: Newly observed scalar value x.
        baseline_mean: Honest baseline mean mu.
        baseline_std: Honest baseline sample standard deviation s.
        sample_count: Calibration sample count N.
        epsilon: Numerical tolerance for zero variance.

    Returns:
        Standardized deviation z, or None if statistically undefined.
    """
    for name, val in [
        ("observed", observed),
        ("baseline_mean", baseline_mean),
        ("baseline_std", baseline_std),
    ]:
        if not isinstance(val, (int, float, np.floating)) or isinstance(val, bool):
            raise TypeError(f"{name} must be numeric float, got {type(val).__name__}.")
        if not math.isfinite(float(val)):
            raise ValueError(f"{name} must be finite, got {val}.")

    if not isinstance(sample_count, (int, np.integer)) or isinstance(sample_count, bool):
        raise TypeError(f"sample_count must be integer, got {type(sample_count).__name__}.")
    if int(sample_count) < 1:
        raise ValueError(f"sample_count must be >= 1, got {sample_count}.")

    if not isinstance(epsilon, (int, float, np.floating)) or isinstance(epsilon, bool):
        raise TypeError(f"epsilon must be numeric float, got {type(epsilon).__name__}.")
    if not math.isfinite(float(epsilon)) or float(epsilon) <= 0.0:
        raise ValueError(f"epsilon must be positive finite float, got {epsilon}.")

    if float(baseline_std) < -1e-12:
        raise ValueError(f"baseline_std must be non-negative, got {baseline_std}.")

    if int(sample_count) < 2:
        return None

    diff = float(observed) - float(baseline_mean)
    s = max(0.0, float(baseline_std))

    if s <= float(epsilon):
        if abs(diff) <= float(epsilon):
            return 0.0
        return None

    return float(diff / s)


def check_confidence_interval(
    observed: float,
    ci: tuple[float, float] | None,
    atol: float = 1e-9,
) -> tuple[bool | None, str]:
    """Check whether an observed scalar lies within the baseline confidence interval.

    Args:
        observed: Newly observed scalar value x.
        ci: Optional baseline confidence interval (ci_lower, ci_upper).
        atol: Numerical tolerance for boundary classification.

    Returns:
        Tuple of (inside_bool_or_none, status_string).
        status_string is one of: 'inside', 'outside', 'boundary', or 'unavailable'.

    Raises:
        TypeError: If observed is not float.
        ValueError: If observed is non-finite or ci is malformed.
    """
    if not isinstance(observed, (int, float, np.floating)) or isinstance(observed, bool):
        raise TypeError(f"observed must be numeric float, got {type(observed).__name__}.")
    if not math.isfinite(float(observed)):
        raise ValueError(f"observed must be finite, got {observed}.")

    if not isinstance(atol, (int, float, np.floating)) or isinstance(atol, bool):
        raise TypeError(f"atol must be numeric float, got {type(atol).__name__}.")
    if not math.isfinite(float(atol)) or float(atol) <= 0.0:
        raise ValueError(f"atol must be positive finite float, got {atol}.")

    if ci is None:
        return None, "unavailable"

    if len(ci) != 2:
        raise ValueError(f"Confidence interval must be a 2-tuple, got {ci}.")

    for idx, bound in enumerate(ci):
        if not isinstance(bound, (int, float, np.floating)) or isinstance(bound, bool):
            raise TypeError(f"Confidence interval bound {idx} must be numeric float, got {type(bound).__name__}.")

    ci_low, ci_high = float(ci[0]), float(ci[1])
    if not (math.isfinite(ci_low) and math.isfinite(ci_high)):
        raise ValueError(f"Confidence interval bounds must be finite, got ({ci_low}, {ci_high}).")
    if ci_low > ci_high + 1e-12:
        raise ValueError(f"Lower bound ({ci_low}) exceeds upper bound ({ci_high}).")

    obs = float(observed)

    # Boundary check with tolerance
    if math.isclose(obs, ci_low, abs_tol=float(atol)) or math.isclose(obs, ci_high, abs_tol=float(atol)):
        return True, "boundary"

    if ci_low <= obs <= ci_high:
        return True, "inside"

    return False, "outside"


def calculate_total_variation_distance(
    p: Mapping[str, float],
    q: Mapping[str, float],
    atol: float = 1e-4,
) -> float:
    """Calculate Total Variation Distance between two discrete probability distributions.

    Formula:
        TV(P, Q) = 0.5 * sum_{i in Omega} |P_i - Q_i|

    Properties:
        - 0.0 <= TV(P, Q) <= 1.0
        - TV(P, Q) == 0.0 iff P == Q
        - TV(P, Q) == 1.0 for disjoint probability distributions

    Validation:
        - Distributions cannot be empty.
        - Probabilities must be finite, non-negative, and in [0.0, 1.0].
        - Each distribution must sum to 1.0 within numerical tolerance atol.
        - Missing outcomes in either distribution are treated explicitly as probability 0.0.

    Args:
        p: Discrete distribution mapping outcome labels to probabilities.
        q: Discrete distribution mapping outcome labels to probabilities.
        atol: Numerical tolerance for probability normalization sum.

    Returns:
        Total variation distance TV in [0.0, 1.0].

    Raises:
        TypeError: If p or q are not mappings or contain non-numeric entries.
        ValueError: If p or q are empty, contain invalid probabilities, or do not sum to 1.
    """
    if not isinstance(atol, (int, float, np.floating)) or isinstance(atol, bool):
        raise TypeError(f"atol must be numeric float, got {type(atol).__name__}.")
    if not math.isfinite(float(atol)) or float(atol) <= 0.0:
        raise ValueError(f"atol must be positive finite float, got {atol}.")

    for name, dist in [("p", p), ("q", q)]:
        if not isinstance(dist, Mapping):
            raise TypeError(f"{name} must be a Mapping, got {type(dist).__name__}.")
        if not dist:
            raise ValueError(f"{name} cannot be an empty distribution.")

        total = 0.0
        for k, v in dist.items():
            if not isinstance(k, str):
                raise TypeError(f"Outcome label in {name} must be string, got {type(k).__name__}.")
            if not isinstance(v, (int, float, np.floating)) or isinstance(v, bool):
                raise TypeError(f"Probability for '{k}' in {name} must be float, got {type(v).__name__}.")
            val = float(v)
            if not math.isfinite(val):
                raise ValueError(f"Probability for '{k}' in {name} must be finite, got {val}.")
            if not (-1e-7 <= val <= 1.0 + 1e-7):
                raise ValueError(f"Probability for '{k}' in {name} must be in [0.0, 1.0], got {val}.")
            total += val

        if not math.isclose(total, 1.0, abs_tol=float(atol)):
            raise ValueError(f"Probabilities in {name} must sum to 1.0 within tolerance {atol}, got {total}.")

    all_keys = set(p.keys()).union(q.keys())
    sum_abs_diff = 0.0
    for k in all_keys:
        p_val = float(p.get(k, 0.0))
        q_val = float(q.get(k, 0.0))
        sum_abs_diff += abs(p_val - q_val)

    tv = 0.5 * sum_abs_diff
    return float(np.clip(tv, 0.0, 1.0))


def compare_probability_distributions(
    observed: Mapping[str, float],
    baseline: Mapping[str, float],
    distribution_name: str = "",
    atol: float = 1e-4,
) -> DistributionComparison:
    """Compare an observed empirical Born distribution against a baseline distribution.

    Args:
        observed: Observed discrete outcome probabilities.
        baseline: Baseline expected discrete outcome probabilities.
        distribution_name: Identifier for this distribution comparison.
        atol: Probability normalization tolerance.

    Returns:
        DistributionComparison instance containing TV distance and per-outcome deviations.
    """
    name = distribution_name.strip() if distribution_name.strip() else "distribution"
    tv_dist = calculate_total_variation_distance(observed, baseline, atol=atol)

    all_keys = sorted(set(observed.keys()).union(baseline.keys()))
    per_outcome_dev: dict[str, float] = {}
    per_outcome_signed: dict[str, float] = {}
    max_dev = 0.0

    for k in all_keys:
        obs_p = float(observed.get(k, 0.0))
        base_p = float(baseline.get(k, 0.0))
        diff = obs_p - base_p
        abs_d = abs(diff)
        per_outcome_dev[k] = float(abs_d)
        per_outcome_signed[k] = float(diff)
        if abs_d > max_dev:
            max_dev = abs_d

    return DistributionComparison(
        distribution_name=name,
        observed_probabilities={k: float(observed.get(k, 0.0)) for k in all_keys},
        baseline_probabilities={k: float(baseline.get(k, 0.0)) for k in all_keys},
        total_variation_distance=tv_dist,
        per_outcome_deviations=per_outcome_dev,
        per_outcome_signed=per_outcome_signed,
        max_outcome_deviation=float(max_dev),
    )


def compare_scalar_metric(
    observed: float,
    baseline_stats: MetricStatistics,
    metric_name: str,
    epsilon: float = 1e-12,
) -> MetricDeviation:
    """Compare a single observed scalar against baseline MetricStatistics.

    Args:
        observed: Newly observed scalar value x.
        baseline_stats: MetricStatistics representing honest calibration for this metric.
        metric_name: Identifier of the metric.
        epsilon: Numerical tolerance for division by near-zero values.

    Returns:
        MetricDeviation instance.

    Raises:
        TypeError: If baseline_stats is not MetricStatistics.
    """
    if not isinstance(baseline_stats, MetricStatistics):
        raise TypeError(f"Expected MetricStatistics, got {type(baseline_stats).__name__}.")

    abs_dev = calculate_absolute_deviation(observed, baseline_stats.mean)
    signed_dev = float(observed) - float(baseline_stats.mean)
    rel_dev = calculate_relative_deviation(observed, baseline_stats.mean, epsilon=epsilon)
    se = calculate_standard_error(baseline_stats.std_dev, baseline_stats.sample_count)
    z_score = calculate_standardized_deviation(
        observed=observed,
        baseline_mean=baseline_stats.mean,
        baseline_std=baseline_stats.std_dev,
        sample_count=baseline_stats.sample_count,
        epsilon=epsilon,
    )
    inside_ci, ci_status = check_confidence_interval(observed, baseline_stats.confidence_interval)

    return MetricDeviation(
        metric_name=metric_name,
        observed_value=float(observed),
        baseline_mean=baseline_stats.mean,
        baseline_variance=baseline_stats.variance,
        baseline_std_dev=baseline_stats.std_dev,
        baseline_sample_count=baseline_stats.sample_count,
        absolute_deviation=abs_dev,
        signed_deviation=signed_dev,
        relative_deviation=rel_dev,
        standard_error=se,
        standardized_deviation=z_score,
        baseline_confidence_interval=baseline_stats.confidence_interval,
        inside_baseline_ci=inside_ci,
        ci_status=ci_status,
    )


# ==============================================================================
# Configuration Compatibility & Verification
# ==============================================================================

def check_configuration_compatibility(
    observation: VerificationObservation | CalibrationObservation | Mapping[str, Any],
    baseline: HonestBaseline,
    strict_hash: bool = False,
) -> tuple[bool, str, dict[str, Any]]:
    """Check whether an observation is compatible with an honest baseline configuration.

    Evaluates compatibility along all established configuration dimensions:
        - Quantum state set
        - Noise model type
        - Noise strength probability
        - Channel location
        - Measurement shots configuration
        - Simulation backend
        - Canonical configuration hash

    Args:
        observation: Observation or mapping containing observation details.
        baseline: HonestBaseline to compare against.
        strict_hash: If True, requires exact match of canonical_hash.

    Returns:
        Tuple of (is_compatible: bool, reason: str, details: dict[str, Any]).
    """
    if not isinstance(baseline, HonestBaseline):
        raise TypeError(f"Expected HonestBaseline, got {type(baseline).__name__}.")

    details: dict[str, Any] = {
        "baseline_canonical_hash": baseline.configuration.canonical_hash,
        "baseline_noise_model": baseline.configuration.noise_model_type,
        "baseline_noise_strength": baseline.configuration.noise_strength,
        "baseline_channel_location": baseline.configuration.channel_location,
        "baseline_shots": baseline.configuration.shots,
        "baseline_backend": baseline.configuration.backend,
        "baseline_states": list(baseline.configuration.states),
    }

    # Extract state name
    if isinstance(observation, (VerificationObservation, CalibrationObservation)):
        obs_state = observation.state_name
        obs_config = getattr(observation, "configuration", None)
    elif isinstance(observation, Mapping):
        obs_state = str(observation.get("state_name", "")).strip()
        obs_config = observation.get("configuration")
    else:
        raise TypeError(f"Expected VerificationObservation, CalibrationObservation, or Mapping, got {type(observation).__name__}.")

    details["observation_state"] = obs_state

    # 1. State set check
    calibrated_state_keys = set(baseline.configuration.states)
    for m_key in baseline.metrics.keys():
        if ":" in m_key:
            calibrated_state_keys.add(m_key.split(":", 1)[1])

    if obs_state and (obs_state not in calibrated_state_keys):
        reason = (
            f"Observation state '{obs_state}' was not calibrated in baseline states: "
            f"{baseline.configuration.states}."
        )
        return False, reason, details

    # Direct observation shots check if observation has shots but no full configuration object
    obs_direct_shots = getattr(observation, "shots", None)
    if obs_direct_shots is not None and obs_config is None:
        if obs_direct_shots != baseline.configuration.shots:
            reason = (
                f"Shot count mismatch: observation has shots={obs_direct_shots}, "
                f"baseline requires shots={baseline.configuration.shots}."
            )
            return False, reason, details

    # 2. Configuration parameter checks if observation carries configuration metadata
    if obs_config is not None:
        if isinstance(obs_config, BaselineConfiguration):
            cfg_dict = asdict(obs_config)
            cfg_hash = obs_config.canonical_hash
        elif isinstance(obs_config, Mapping):
            cfg_dict = dict(obs_config)
            cfg_hash = obs_config.get("canonical_hash")
        else:
            reason = f"Unsupported configuration object type: {type(obs_config).__name__}."
            return False, reason, details

        details["observation_configuration"] = cfg_dict

        if strict_hash and cfg_hash is not None:
            if cfg_hash != baseline.configuration.canonical_hash:
                reason = (
                    f"Canonical hash mismatch: observation config hash '{cfg_hash}' != "
                    f"baseline config hash '{baseline.configuration.canonical_hash}'."
                )
                return False, reason, details

        # State set check in configuration
        if "states" in cfg_dict:
            obs_states = tuple(cfg_dict["states"])
            if set(obs_states) != set(baseline.configuration.states):
                reason = (
                    f"Configuration state set mismatch: observation has states {obs_states}, "
                    f"baseline requires states {baseline.configuration.states}."
                )
                return False, reason, details

        # Noise model check
        if "noise_model_type" in cfg_dict:
            obs_noise_type = str(cfg_dict["noise_model_type"]).lower().strip()
            base_noise_type = baseline.configuration.noise_model_type.lower().strip()
            if obs_noise_type != base_noise_type:
                reason = (
                    f"Noise model mismatch: observation has '{obs_noise_type}', "
                    f"baseline requires '{base_noise_type}'."
                )
                return False, reason, details

        # Noise strength check
        if "noise_strength" in cfg_dict:
            obs_p = float(cfg_dict["noise_strength"])
            base_p = float(baseline.configuration.noise_strength)
            if not math.isclose(obs_p, base_p, abs_tol=1e-6):
                reason = (
                    f"Noise strength mismatch: observation has p={obs_p}, "
                    f"baseline requires p={base_p}."
                )
                return False, reason, details

        # Channel location check
        if "channel_location" in cfg_dict:
            obs_loc = str(cfg_dict["channel_location"]).strip()
            base_loc = baseline.configuration.channel_location.strip()
            if obs_loc != base_loc:
                reason = (
                    f"Channel location mismatch: observation has '{obs_loc}', "
                    f"baseline requires '{base_loc}'."
                )
                return False, reason, details

        # Shots check
        if "shots" in cfg_dict:
            obs_shots = cfg_dict["shots"]
            base_shots = baseline.configuration.shots
            if obs_shots != base_shots:
                reason = (
                    f"Shot count mismatch: observation has shots={obs_shots}, "
                    f"baseline requires shots={base_shots}."
                )
                return False, reason, details

        # Backend check
        if "backend" in cfg_dict:
            obs_backend = str(cfg_dict["backend"]).strip()
            base_backend = baseline.configuration.backend.strip()
            if obs_backend != base_backend:
                reason = (
                    f"Backend mismatch: observation has '{obs_backend}', "
                    f"baseline requires '{base_backend}'."
                )
                return False, reason, details

    return True, "Compatible", details


def validate_configuration_compatibility(
    observation: VerificationObservation | CalibrationObservation | Mapping[str, Any],
    baseline: HonestBaseline,
    strict_hash: bool = False,
) -> bool:
    """Enforce configuration compatibility, raising ConfigurationCompatibilityError if incompatible."""
    is_compat, reason, _ = check_configuration_compatibility(observation, baseline, strict_hash=strict_hash)
    if not is_compat:
        raise ConfigurationCompatibilityError(reason)
    return True


# ==============================================================================
# Comprehensive Observation Comparison
# ==============================================================================

def compare_observation(
    observation: VerificationObservation | CalibrationObservation,
    baseline: HonestBaseline,
    allow_uncalibrated_state: bool = False,
    strict_hash: bool = False,
    epsilon: float = 1e-12,
    prob_atol: float = 1e-4,
) -> StatisticalEvidence:
    """Compare an observed quantum verification result against a compatible honest baseline.

    Preserves Baseline Immutability:
        The baseline is NOT modified, updated, or adapted during comparison.
        Honest baseline data remains strictly separate from evaluation observations.

    Scientific Principle:
        Produces purely descriptive statistical evidence.
        Contains NO attack decisions, NO threshold logic, and NO threat classifications.

    Args:
        observation: Newly observed quantum verification metrics.
        baseline: Calibrated HonestBaseline produced by M9.
        allow_uncalibrated_state: If True, bypasses state compatibility check (not recommended).
        strict_hash: If True, requires exact canonical hash match when configuration is present.
        epsilon: Numerical tolerance for zero relative deviation.
        prob_atol: Numerical tolerance for probability distribution sums.

    Returns:
        StatisticalEvidence instance containing all independent metric and distribution deviations.

    Raises:
        ConfigurationCompatibilityError: If observation and baseline configurations are incompatible.
        TypeError: If observation or baseline are of invalid types.
    """
    if not isinstance(observation, (VerificationObservation, CalibrationObservation)):
        raise TypeError(f"Expected VerificationObservation or CalibrationObservation, got {type(observation).__name__}.")
    if not isinstance(baseline, HonestBaseline):
        raise TypeError(f"Expected HonestBaseline, got {type(baseline).__name__}.")

    # 1. Enforce configuration compatibility
    if not allow_uncalibrated_state:
        validate_configuration_compatibility(observation, baseline, strict_hash=strict_hash)
    else:
        # Still validate non-state parameters if configuration is attached
        _, reason, _ = check_configuration_compatibility(observation, baseline, strict_hash=strict_hash)
        if "Noise" in reason or "Channel" in reason or "Shot" in reason or "Backend" in reason:
            raise ConfigurationCompatibilityError(reason)

    st = observation.state_name
    metric_deviations: dict[str, MetricDeviation] = {}
    distribution_comparisons: dict[str, DistributionComparison] = {}

    # 2. Compare Fidelity
    # Try state-specific fidelity first, fallback to aggregate fidelity:all_states
    fid_key = f"fidelity:{st}" if f"fidelity:{st}" in baseline.metrics else "fidelity:all_states"
    if fid_key in baseline.metrics:
        metric_deviations[fid_key] = compare_scalar_metric(
            observed=observation.fidelity,
            baseline_stats=baseline.metrics[fid_key],
            metric_name=fid_key,
            epsilon=epsilon,
        )

    # 3. Compare QBER
    qber_key = f"qber:{st}" if f"qber:{st}" in baseline.metrics else "qber:all_states"
    if qber_key in baseline.metrics:
        metric_deviations[qber_key] = compare_scalar_metric(
            observed=observation.qber,
            baseline_stats=baseline.metrics[qber_key],
            metric_name=qber_key,
            epsilon=epsilon,
        )

    # 4. Compare Pauli Expectations
    for pauli_op in ("X", "Y", "Z"):
        exp_key = f"exp_{pauli_op.lower()}:{st}"
        if exp_key in baseline.metrics and pauli_op in observation.pauli_expectations:
            metric_deviations[exp_key] = compare_scalar_metric(
                observed=observation.pauli_expectations[pauli_op],
                baseline_stats=baseline.metrics[exp_key],
                metric_name=exp_key,
                epsilon=epsilon,
            )

    # 5. Compare Individual Measurement Probabilities
    for basis_char, prob_dict in [
        ("z", observation.probabilities_z),
        ("x", observation.probabilities_x),
        ("y", observation.probabilities_y),
    ]:
        for outcome, prob in prob_dict.items():
            prob_key = f"prob_{basis_char}_{outcome}:{st}"
            if prob_key in baseline.metrics:
                metric_deviations[prob_key] = compare_scalar_metric(
                    observed=prob,
                    baseline_stats=baseline.metrics[prob_key],
                    metric_name=prob_key,
                    epsilon=epsilon,
                )

    # 6. Compare Probability Distributions via Total Variation Distance
    for basis_char, prob_dict in [
        ("z", observation.probabilities_z),
        ("x", observation.probabilities_x),
        ("y", observation.probabilities_y),
    ]:
        dist_name = f"probabilities_{basis_char}:{st}"
        # Extract baseline probabilities for all outcomes calibrated for this state and basis
        baseline_prob_dict: dict[str, float] = {}
        prefix = f"prob_{basis_char}_"
        suffix = f":{st}"
        for b_metric_name, b_stats in baseline.metrics.items():
            if b_metric_name.startswith(prefix) and b_metric_name.endswith(suffix):
                outcome_label = b_metric_name[len(prefix): -len(suffix)]
                baseline_prob_dict[outcome_label] = b_stats.mean

        if baseline_prob_dict and prob_dict:
            base_sum = sum(baseline_prob_dict.values())
            if not math.isclose(base_sum, 1.0, abs_tol=prob_atol):
                raise ValueError(
                    f"Baseline probability distribution for '{dist_name}' does not sum to 1.0 within tolerance "
                    f"{prob_atol} (got {base_sum}); refusing to silently normalize."
                )

            distribution_comparisons[dist_name] = compare_probability_distributions(
                observed=prob_dict,
                baseline=baseline_prob_dict,
                distribution_name=dist_name,
                atol=prob_atol,
            )

    # 7. Compare Bell Correlations if present
    if observation.bell_correlations is not None:
        for bell_op in ("XX", "YY", "ZZ"):
            bell_key = f"bell_{bell_op.lower()}"
            if bell_key in baseline.metrics and bell_op in observation.bell_correlations:
                metric_deviations[bell_key] = compare_scalar_metric(
                    observed=observation.bell_correlations[bell_op],
                    baseline_stats=baseline.metrics[bell_key],
                    metric_name=bell_key,
                    epsilon=epsilon,
                )

    _, reason, comp_details = check_configuration_compatibility(observation, baseline, strict_hash=strict_hash)

    metadata: dict[str, Any] = {
        "comparison_engine": "M10_statistical_comparison",
        "scientific_boundary": "STATISTICAL_EVIDENCE_ONLY_NO_SECURITY_DECISIONS",
        "evaluated_metric_count": len(metric_deviations),
        "evaluated_distribution_count": len(distribution_comparisons),
    }

    return StatisticalEvidence(
        observation_state=st,
        baseline_configuration_hash=baseline.configuration.canonical_hash,
        metric_deviations=metric_deviations,
        distribution_comparisons=distribution_comparisons,
        configuration_compatibility={"compatible": True, "reason": reason, "details": comp_details},
        timestamp=datetime.now(timezone.utc).isoformat(),
        metadata=metadata,
    )

"""Q-SHIELD — Statistical Threshold Policy Engine (Milestone M11).

Implements calibrated, configuration-specific threshold policies on top of M9
honest baselines and M10 statistical evidence:
    - MetricThreshold: Individual calibrated metric boundary (upper or lower).
    - ThresholdPolicy: Immutable set of metric thresholds bound to a baseline configuration.
    - MetricThresholdEvaluation: Descriptive evaluation of a single metric against its threshold.
    - PolicyEvaluationReport: Multi-metric evaluation report capturing threshold crossings.
    - Calibration algorithms: Empirical quantile (non-parametric) and statistical multiplier.
    - Configuration compatibility enforcement: Strict binding to baseline canonical hash.
    - Empirical false-alarm rate estimation on held-out validation data.

Scientific Boundaries:
    - M11 produces threshold exceedance evidence ONLY.
    - Contains strictly NO final security decisions (ACCEPT, SUSPICIOUS, ATTACK).
    - Contains strictly NO attack detection, forgery detection, replay detection, or classification.
    - Contains strictly NO machine learning, neural networks, or composite security scores.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
import math
from typing import Any
import numpy as np

from .baseline import BaselineConfiguration, HonestBaseline
from .calibration import CalibrationObservation
from .comparison import (
    ConfigurationCompatibilityError,
    DistributionComparison,
    MetricDeviation,
    StatisticalEvidence,
    VerificationObservation,
    check_configuration_compatibility,
)


# ==============================================================================
# Enums
# ==============================================================================

class ThresholdDirection(str, Enum):
    """Direction where metric crossing indicates deviation or physical degradation.

    UPPER: Normal behavior produces lower values; crossing occurs when observed > threshold.
           Examples: QBER, Total Variation Distance (TVD), absolute deviations.
    LOWER: Normal behavior produces higher values; crossing occurs when observed < threshold.
           Examples: Overlap fidelity, certain aligned Pauli expectations.
    """

    UPPER = "upper"
    LOWER = "lower"


class ThresholdMethod(str, Enum):
    """Statistical derivation method used to calibrate the threshold.

    EMPIRICAL_QUANTILE: Non-parametric quantile estimated from honest calibration observations.
                        Recommended for bounded and non-Gaussian quantum metrics.
    STATISTICAL_BOUND: Parametric mean +/- k * std_dev based on baseline sample statistics.
    FIXED_BOUND: Calibrated or documented deterministic operating boundary.
    """

    EMPIRICAL_QUANTILE = "empirical_quantile"
    STATISTICAL_BOUND = "statistical_bound"
    FIXED_BOUND = "fixed_bound"


# ==============================================================================
# Data Structures
# ==============================================================================

@dataclass(frozen=True)
class MetricThreshold:
    """Immutable calibrated threshold for an individual quantum verification metric.

    Attributes:
        metric_name: Canonical identifier of the evaluated metric (e.g. 'fidelity:0', 'qber:0').
        direction: ThresholdDirection (UPPER or LOWER).
        method: ThresholdMethod used to calibrate this threshold.
        threshold_value: Numerical boundary value.
        alpha: Optional significance level alpha in (0, 1).
        quantile: Quantile position in [0, 1] (e.g. alpha for LOWER, 1 - alpha for UPPER).
        multiplier: Multiplier k if method is STATISTICAL_BOUND (mu +/- k*sigma).
        sample_count: Number of honest calibration observations N >= 2 used in calibration.
        baseline_mean: Empirical mean of calibration samples.
        baseline_std_dev: Empirical standard deviation of calibration samples.
        metadata: User-specified or provenance metadata dictionary.
    """

    metric_name: str
    direction: ThresholdDirection
    method: ThresholdMethod
    threshold_value: float
    alpha: float | None = None
    quantile: float | None = None
    multiplier: float | None = None
    sample_count: int | None = None
    baseline_mean: float | None = None
    baseline_std_dev: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate physical, statistical, and structural invariants."""
        if not self.metric_name.strip():
            raise ValueError("metric_name cannot be empty.")

        if not isinstance(self.direction, ThresholdDirection):
            if isinstance(self.direction, str):
                dir_str = self.direction.lower().strip()
                if dir_str == "upper":
                    object.__setattr__(self, "direction", ThresholdDirection.UPPER)
                elif dir_str == "lower":
                    object.__setattr__(self, "direction", ThresholdDirection.LOWER)
                else:
                    raise ValueError(f"Invalid threshold direction '{self.direction}'. Choose UPPER or LOWER.")
            else:
                raise TypeError(f"direction must be ThresholdDirection, got {type(self.direction).__name__}.")

        if not isinstance(self.method, ThresholdMethod):
            if isinstance(self.method, str):
                meth_str = self.method.lower().strip()
                try:
                    object.__setattr__(self, "method", ThresholdMethod(meth_str))
                except ValueError as exc:
                    raise ValueError(f"Invalid threshold method '{self.method}'.") from exc
            else:
                raise TypeError(f"method must be ThresholdMethod, got {type(self.method).__name__}.")

        if not isinstance(self.threshold_value, (int, float, np.floating)) or isinstance(self.threshold_value, bool):
            raise TypeError(f"threshold_value must be float, got {type(self.threshold_value).__name__}.")
        if not math.isfinite(float(self.threshold_value)):
            raise ValueError(f"threshold_value must be finite, got {self.threshold_value}.")

        # Validate alpha if present
        if self.alpha is not None:
            if not isinstance(self.alpha, (int, float, np.floating)) or isinstance(self.alpha, bool):
                raise TypeError(f"alpha must be float, got {type(self.alpha).__name__}.")
            if not math.isfinite(float(self.alpha)):
                raise ValueError(f"alpha must be finite, got {self.alpha}.")
            if not (0.0 < float(self.alpha) < 1.0):
                raise ValueError(f"alpha must be strictly in (0.0, 1.0), got {self.alpha}.")

        # Validate quantile if present
        if self.quantile is not None:
            if not isinstance(self.quantile, (int, float, np.floating)) or isinstance(self.quantile, bool):
                raise TypeError(f"quantile must be float, got {type(self.quantile).__name__}.")
            if not math.isfinite(float(self.quantile)):
                raise ValueError(f"quantile must be finite, got {self.quantile}.")
            if not (0.0 <= float(self.quantile) <= 1.0):
                raise ValueError(f"quantile must be in [0.0, 1.0], got {self.quantile}.")

        # Validate multiplier if present
        if self.multiplier is not None:
            if not isinstance(self.multiplier, (int, float, np.floating)) or isinstance(self.multiplier, bool):
                raise TypeError(f"multiplier must be float, got {type(self.multiplier).__name__}.")
            if not math.isfinite(float(self.multiplier)):
                raise ValueError(f"multiplier must be finite, got {self.multiplier}.")
            if float(self.multiplier) < 0.0:
                raise ValueError(f"multiplier must be non-negative, got {self.multiplier}.")

        # Validate sample count if present
        if self.sample_count is not None:
            if not isinstance(self.sample_count, (int, np.integer)) or isinstance(self.sample_count, bool):
                raise TypeError(f"sample_count must be integer, got {type(self.sample_count).__name__}.")
            if int(self.sample_count) < 2:
                raise ValueError(f"sample_count must be >= 2 for statistical threshold calibration, got {self.sample_count}.")

        # Defensive copy of metadata
        object.__setattr__(self, "metadata", dict(self.metadata))


@dataclass(frozen=True)
class ThresholdPolicy:
    """Immutable collection of calibrated metric thresholds bound to an operating configuration.

    Attributes:
        policy_id: Unique string identifier for this policy.
        baseline_configuration_hash: Canonical SHA-256 hash of the corresponding BaselineConfiguration.
        thresholds: Mapping of metric names to calibrated MetricThreshold instances.
        configuration: Optional reference to the underlying BaselineConfiguration.
        alpha: Primary significance level used in calibration (if uniform across metrics).
        method: Primary threshold derivation method.
        calibration_sample_count: Number of honest calibration observations used.
        created_at: ISO 8601 UTC timestamp of policy calibration.
        policy_fingerprint: SHA-256 digest of the canonical serialized threshold specifications.
        metadata: Provenance and calibration configuration metadata.
    """

    policy_id: str
    baseline_configuration_hash: str
    thresholds: dict[str, MetricThreshold]
    configuration: BaselineConfiguration | dict[str, Any] | None = None
    alpha: float | None = None
    method: ThresholdMethod = ThresholdMethod.EMPIRICAL_QUANTILE
    calibration_sample_count: int = 0
    created_at: str = ""
    policy_fingerprint: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate structural integrity and compute deterministic fingerprint."""
        if not self.policy_id.strip():
            raise ValueError("policy_id cannot be empty.")
        if not self.baseline_configuration_hash.strip():
            raise ValueError("baseline_configuration_hash cannot be empty.")
        if not self.thresholds:
            raise ValueError("ThresholdPolicy must contain at least one MetricThreshold.")

        for k, v in self.thresholds.items():
            if not isinstance(k, str):
                raise TypeError(f"Threshold key must be string, got {type(k).__name__}.")
            if not isinstance(v, MetricThreshold):
                raise TypeError(f"Threshold for '{k}' must be MetricThreshold, got {type(v).__name__}.")

        # Defensive copies
        object.__setattr__(self, "thresholds", dict(self.thresholds))
        object.__setattr__(self, "metadata", dict(self.metadata))

        if not self.created_at:
            now_iso = datetime.now(timezone.utc).isoformat()
            object.__setattr__(self, "created_at", now_iso)

        if not self.policy_fingerprint:
            fp = calculate_policy_fingerprint(
                policy_id=self.policy_id,
                config_hash=self.baseline_configuration_hash,
                thresholds=self.thresholds,
            )
            object.__setattr__(self, "policy_fingerprint", fp)

    def get_threshold(self, metric_name: str) -> MetricThreshold | None:
        """Retrieve the calibrated threshold for a specific metric by name."""
        return self.thresholds.get(metric_name)

    def to_dict(self) -> dict[str, Any]:
        """Serialize threshold policy to a JSON-serializable dictionary."""
        cfg_dict = (
            asdict(self.configuration)
            if isinstance(self.configuration, BaselineConfiguration)
            else (dict(self.configuration) if isinstance(self.configuration, Mapping) else None)
        )
        return {
            "policy_id": self.policy_id,
            "baseline_configuration_hash": self.baseline_configuration_hash,
            "thresholds": {k: asdict(v) for k, v in self.thresholds.items()},
            "configuration": cfg_dict,
            "alpha": self.alpha,
            "method": self.method.value,
            "calibration_sample_count": self.calibration_sample_count,
            "created_at": self.created_at,
            "policy_fingerprint": self.policy_fingerprint,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class MetricThresholdEvaluation:
    """Evaluation result comparing an observed metric value against its calibrated threshold.

    Scientific Principle:
        Indicates whether the configured statistical threshold was exceeded.
        Contains strictly NO attack decision and NO threat classification.

    Attributes:
        metric_name: Name identifier of the evaluated metric.
        observed_value: Numerical observed value from verification.
        threshold_value: Calibrated boundary value.
        direction: ThresholdDirection (UPPER or LOWER).
        exceeded: True if the observed value crossed the threshold beyond numerical tolerance.
        margin: Signed exceedance margin:
                UPPER: observed_value - threshold_value (positive indicates exceedance)
                LOWER: threshold_value - observed_value (positive indicates exceedance)
        signed_distance: Signed distance observed_value - threshold_value.
        method: ThresholdMethod of the applied threshold.
        boundary_status: Exact boundary status ('strictly_inside', 'strictly_exceeded', 'at_boundary').
        metadata: Contextual evaluation metadata.
    """

    metric_name: str
    observed_value: float
    threshold_value: float
    direction: ThresholdDirection
    exceeded: bool
    margin: float
    signed_distance: float
    method: ThresholdMethod
    boundary_status: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate attributes and enforce immutability."""
        if not self.metric_name.strip():
            raise ValueError("metric_name cannot be empty.")
        for name, val in [
            ("observed_value", self.observed_value),
            ("threshold_value", self.threshold_value),
            ("margin", self.margin),
            ("signed_distance", self.signed_distance),
        ]:
            if not isinstance(val, (int, float, np.floating)) or isinstance(val, bool):
                raise TypeError(f"{name} must be float, got {type(val).__name__}.")
            if not math.isfinite(float(val)):
                raise ValueError(f"{name} must be finite, got {val}.")

        if self.boundary_status not in ("strictly_inside", "strictly_exceeded", "at_boundary"):
            raise ValueError(
                f"boundary_status must be 'strictly_inside', 'strictly_exceeded', or 'at_boundary', got '{self.boundary_status}'."
            )

        object.__setattr__(self, "metadata", dict(self.metadata))


@dataclass(frozen=True)
class PolicyEvaluationReport:
    """Multi-metric threshold evaluation report for an observation or statistical evidence.

    Scientific Boundary:
        Summarizes which configured thresholds were exceeded.
        Does NOT produce final security verdicts (ACCEPT / SUSPICIOUS / ATTACK)
        and does NOT compute an arbitrary security score.

    Attributes:
        policy_id: Identifier of the evaluated ThresholdPolicy.
        baseline_configuration_hash: Canonical hash of the evaluated policy.
        metric_evaluations: Mapping of metric names to MetricThresholdEvaluation results.
        any_exceeded: True if at least one metric threshold was exceeded.
        all_exceeded: True if all evaluated metric thresholds were exceeded.
        exceeded_metrics: Tuple of metric names that crossed their thresholds.
        exceeded_count: Total count of exceeded metric thresholds.
        total_metrics_evaluated: Total count of metrics evaluated.
        timestamp: ISO 8601 UTC evaluation timestamp.
        metadata: Evaluation context metadata.
    """

    policy_id: str
    baseline_configuration_hash: str
    metric_evaluations: dict[str, MetricThresholdEvaluation]
    any_exceeded: bool
    all_exceeded: bool
    exceeded_metrics: tuple[str, ...]
    exceeded_count: int
    total_metrics_evaluated: int
    timestamp: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Enforce defensive copying and validation."""
        object.__setattr__(self, "metric_evaluations", dict(self.metric_evaluations))
        object.__setattr__(self, "exceeded_metrics", tuple(self.exceeded_metrics))
        object.__setattr__(self, "metadata", dict(self.metadata))

    def get_evaluation(self, metric_name: str) -> MetricThresholdEvaluation | None:
        """Retrieve evaluation result for a specific metric by name."""
        return self.metric_evaluations.get(metric_name)

    def to_dict(self) -> dict[str, Any]:
        """Serialize policy evaluation report to a JSON-serializable dictionary."""
        return {
            "policy_id": self.policy_id,
            "baseline_configuration_hash": self.baseline_configuration_hash,
            "metric_evaluations": {k: asdict(v) for k, v in self.metric_evaluations.items()},
            "any_exceeded": self.any_exceeded,
            "all_exceeded": self.all_exceeded,
            "exceeded_metrics": list(self.exceeded_metrics),
            "exceeded_count": self.exceeded_count,
            "total_metrics_evaluated": self.total_metrics_evaluated,
            "timestamp": self.timestamp,
            "metadata": dict(self.metadata),
        }


# ==============================================================================
# Core Mathematical Algorithms & Helpers
# ==============================================================================

def calculate_policy_fingerprint(
    policy_id: str,
    config_hash: str,
    thresholds: Mapping[str, MetricThreshold],
) -> str:
    """Compute a deterministic SHA-256 fingerprint for a policy's canonical specifications."""
    items = []
    for k in sorted(thresholds.keys()):
        th = thresholds[k]
        items.append({
            "metric_name": th.metric_name,
            "direction": th.direction.value,
            "method": th.method.value,
            "threshold_value": round(float(th.threshold_value), 10),
            "alpha": round(float(th.alpha), 8) if th.alpha is not None else None,
            "quantile": round(float(th.quantile), 8) if th.quantile is not None else None,
            "multiplier": round(float(th.multiplier), 8) if th.multiplier is not None else None,
            "sample_count": th.sample_count,
        })

    payload = {
        "policy_id": policy_id.strip(),
        "baseline_configuration_hash": config_hash.strip(),
        "thresholds": items,
    }
    encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def calculate_empirical_quantile_threshold(
    samples: Sequence[float],
    direction: ThresholdDirection,
    alpha: float,
    metric_name: str = "",
) -> float:
    """Calculate non-parametric threshold from honest calibration observations via quantiles.

    Mathematical Model:
        For LOWER-tail metrics (e.g. Fidelity):
            T = Q_alpha(samples)
            Observed values below T cross the lower threshold.
        For UPPER-tail metrics (e.g. QBER, TVD, absolute deviations):
            T = Q_{1 - alpha}(samples)
            Observed values above T cross the upper threshold.

    Quantile Definition:
        Uses NumPy's standard linear interpolation: method='linear'.

    Args:
        samples: Sequence of honest numerical metric observations.
        direction: ThresholdDirection.UPPER or ThresholdDirection.LOWER.
        alpha: Significance level in strictly (0.0, 1.0).
        metric_name: Optional metric name identifier for informative error reporting.

    Returns:
        Calibrated threshold value as a finite float.

    Raises:
        ValueError: If alpha not in (0, 1), samples empty, or N < 2.
        TypeError: If samples contain non-numeric types.
    """
    if not isinstance(alpha, (int, float, np.floating)) or isinstance(alpha, bool):
        raise TypeError(f"alpha must be float, got {type(alpha).__name__}.")
    if not math.isfinite(float(alpha)):
        raise ValueError(f"alpha must be finite, got {alpha}.")
    if not (0.0 < float(alpha) < 1.0):
        raise ValueError(f"alpha must be strictly in (0.0, 1.0), got {alpha}.")

    if not isinstance(samples, Sequence):
        raise TypeError(f"samples must be a Sequence, got {type(samples).__name__}.")
    if len(samples) == 0:
        raise ValueError(f"Calibration observations cannot be empty for metric '{metric_name}'.")
    if len(samples) < 2:
        raise ValueError(
            f"Insufficient calibration samples (N={len(samples)}) for metric '{metric_name}'. "
            "Minimum N >= 2 is required for statistical threshold calibration."
        )

    clean_samples: list[float] = []
    for idx, s in enumerate(samples):
        if not isinstance(s, (int, float, np.floating)) or isinstance(s, bool):
            raise TypeError(f"Sample at index {idx} must be numeric float, got {type(s).__name__}.")
        val = float(s)
        if not math.isfinite(val):
            raise ValueError(f"Sample at index {idx} must be finite, got {val}.")
        clean_samples.append(val)

    if direction == ThresholdDirection.LOWER:
        q = float(alpha)
    elif direction == ThresholdDirection.UPPER:
        q = 1.0 - float(alpha)
    else:
        raise ValueError(f"Unsupported direction: {direction}.")

    arr = np.asarray(clean_samples, dtype=np.float64)
    res = float(np.quantile(arr, q, method="linear"))
    return res


def calculate_statistical_multiplier_threshold(
    mean: float,
    std_dev: float,
    direction: ThresholdDirection,
    multiplier: float = 2.0,
    metric_name: str = "",
) -> float:
    """Calculate parametric threshold as mean +/- k * std_dev.

    Mathematical Model:
        For LOWER-tail metrics:
            T = mean - k * std_dev
        For UPPER-tail metrics:
            T = mean + k * std_dev

    Args:
        mean: Empirical mean of the honest distribution.
        std_dev: Empirical standard deviation of the honest distribution.
        direction: ThresholdDirection.UPPER or ThresholdDirection.LOWER.
        multiplier: Multiplier k >= 0.0 (e.g. 2.0 or 3.0).
        metric_name: Optional metric identifier for error context.

    Returns:
        Calibrated threshold value as a finite float.
    """
    for name, val in [("mean", mean), ("std_dev", std_dev), ("multiplier", multiplier)]:
        if not isinstance(val, (int, float, np.floating)) or isinstance(val, bool):
            raise TypeError(f"{name} must be float, got {type(val).__name__}.")
        if not math.isfinite(float(val)):
            raise ValueError(f"{name} must be finite, got {val}.")

    if float(std_dev) < -1e-12:
        raise ValueError(f"std_dev must be non-negative, got {std_dev}.")
    if float(multiplier) < 0.0:
        raise ValueError(f"multiplier must be non-negative, got {multiplier}.")

    s = max(0.0, float(std_dev))
    k = float(multiplier)
    m = float(mean)

    if direction == ThresholdDirection.LOWER:
        raw_t = m - k * s
        lower_name = metric_name.lower()
        if "fidelity" in lower_name or lower_name.startswith("prob_") or "probability" in lower_name:
            # Clamping prevents physically meaningless negative thresholds for bounded metrics in [0, 1].
            return max(0.0, raw_t)
        return raw_t
    elif direction == ThresholdDirection.UPPER:
        raw_t = m + k * s
        lower_name = metric_name.lower()
        if "qber" in lower_name or lower_name.startswith("prob_") or "probability" in lower_name:
            # Clamping prevents thresholds > 1.0 for bounded metrics in [0, 1].
            # Note: if raw_t >= 1.0, strict exceedance (x > 1.0 + atol) cannot occur for bounded metrics.
            # Empirical quantiles (EMPIRICAL_QUANTILE) are preferred for bounded quantum metrics.
            return min(1.0, raw_t)
        return raw_t
    else:
        raise ValueError(f"Unsupported direction: {direction}.")


def resolve_metric_direction(metric_name: str) -> ThresholdDirection:
    """Infer the default threshold direction for a verification metric based on physical semantics.

    Physical Conventions:
        - LOWER: High values represent honest behavior, drops represent degradation.
                 Primary example: Overlap Fidelity ('fidelity:0', 'fidelity:all_states').
        - UPPER: Zero or small values represent honest behavior, increases represent deviation.
                 Primary examples: QBER ('qber:0'), Total Variation Distance ('probabilities_z:0'),
                 Pauli expectation absolute deviations ('pauli_z:0'), Bell correlation absolute deviations
                 ('bell_xx'), and individual probability absolute deviations ('prob_dev_z_0:0').

    Physical Note on Signed Quantities:
        Raw Pauli expectations (e.g. <Z>, <Y>) and Bell correlations (<XX>, <YY>, <ZZ>)
        are signed in [-1, +1]. A single directional threshold on raw values is physically invalid
        because degradation can move values in either direction (towards 0). Consequently,
        threshold policies calibrate and evaluate absolute deviations (|x - mu|) with UPPER direction.
    """
    m_lower = metric_name.lower().strip()
    if m_lower.startswith("fidelity") or ":fidelity" in m_lower:
        return ThresholdDirection.LOWER
    return ThresholdDirection.UPPER


# ==============================================================================
# Calibration Engines
# ==============================================================================

def calibrate_metric_threshold(
    metric_name: str,
    samples: Sequence[float],
    direction: ThresholdDirection | None = None,
    method: ThresholdMethod = ThresholdMethod.EMPIRICAL_QUANTILE,
    alpha: float = 0.05,
    multiplier: float = 2.0,
    metadata: Mapping[str, Any] | None = None,
) -> MetricThreshold:
    """Calibrate a single MetricThreshold from a sequence of honest sample observations.

    Args:
        metric_name: Name of the metric to calibrate.
        samples: Sequence of honest numerical metric observations.
        direction: Optional explicit direction; inferred if None.
        method: Derivation method (EMPIRICAL_QUANTILE or STATISTICAL_BOUND).
        alpha: Significance level in (0, 1).
        multiplier: Multiplier k for STATISTICAL_BOUND.
        metadata: Optional metadata dictionary.

    Returns:
        Immutable MetricThreshold instance.
    """
    resolved_dir = direction if direction is not None else resolve_metric_direction(metric_name)

    if not isinstance(samples, Sequence):
        raise TypeError(f"samples must be a Sequence, got {type(samples).__name__}.")
    n = len(samples)
    if n < 2:
        raise ValueError(
            f"Insufficient samples (N={n}) to calibrate metric '{metric_name}'. "
            "Minimum N >= 2 is required for statistical calibration."
        )

    clean_samples = [float(x) for x in samples]
    arr = np.asarray(clean_samples, dtype=np.float64)
    sample_mean = float(np.mean(arr))
    sample_std = float(np.std(arr, ddof=1)) if n > 1 else 0.0

    if method == ThresholdMethod.EMPIRICAL_QUANTILE:
        t_val = calculate_empirical_quantile_threshold(
            clean_samples, direction=resolved_dir, alpha=alpha, metric_name=metric_name
        )
        q_val = float(alpha) if resolved_dir == ThresholdDirection.LOWER else float(1.0 - alpha)
        mult_val = None
    elif method == ThresholdMethod.STATISTICAL_BOUND:
        t_val = calculate_statistical_multiplier_threshold(
            mean=sample_mean,
            std_dev=sample_std,
            direction=resolved_dir,
            multiplier=multiplier,
            metric_name=metric_name,
        )
        q_val = None
        mult_val = float(multiplier)
    elif method == ThresholdMethod.FIXED_BOUND:
        t_val = sample_mean
        q_val = None
        mult_val = None
    else:
        raise ValueError(f"Unsupported threshold method: {method}.")

    meta = dict(metadata) if metadata is not None else {}
    # Assess statistical reliability (N >= max(10, ceil(1/alpha)) is recommended for quantile estimation)
    min_stat_reliable = max(10, math.ceil(1.0 / (alpha or 0.05)))
    meta["statistical_reliability"] = (
        "statistically_reliable" if n >= min_stat_reliable else "low_sample_count"
    )
    meta["minimum_recommended_samples"] = min_stat_reliable

    return MetricThreshold(
        metric_name=metric_name,
        direction=resolved_dir,
        method=method,
        threshold_value=t_val,
        alpha=alpha if method == ThresholdMethod.EMPIRICAL_QUANTILE else None,
        quantile=q_val,
        multiplier=mult_val,
        sample_count=n,
        baseline_mean=sample_mean,
        baseline_std_dev=sample_std,
        metadata=meta,
    )


def calibrate_threshold_policy(
    baseline: HonestBaseline,
    observations: Sequence[CalibrationObservation],
    alpha: float = 0.05,
    method: ThresholdMethod = ThresholdMethod.EMPIRICAL_QUANTILE,
    multiplier: float = 2.0,
    policy_id: str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> ThresholdPolicy:
    """Calibrate an immutable ThresholdPolicy strictly bound to an HonestBaseline's configuration.

    Requirements:
        - Honest calibration observations only (attacked data is strictly rejected).
        - Observations must match the baseline's operating configuration.
        - Minimum N >= 2 calibration observations required per calibrated state.

    Args:
        baseline: Calibrated HonestBaseline defining expected operating behavior.
        observations: Sequence of CalibrationObservation instances from honest calibration.
        alpha: Significance level in (0, 1). Default: 0.05 (95% statistical boundary).
        method: Calibration derivation method (EMPIRICAL_QUANTILE or STATISTICAL_BOUND).
        multiplier: Multiplier k for STATISTICAL_BOUND. Default: 2.0.
        policy_id: Optional unique string identifier; auto-generated if None.
        metadata: Optional metadata dictionary.

    Returns:
        Immutable ThresholdPolicy bound to baseline.configuration.canonical_hash.

    Raises:
        TypeError: If baseline or observations have invalid types.
        ValueError: If observations is empty, contains insufficient samples (N < 2),
                    or carries invalid alpha.
        ConfigurationCompatibilityError: If observations mismatch baseline configuration.
    """
    if not isinstance(baseline, HonestBaseline):
        raise TypeError(f"Expected HonestBaseline, got {type(baseline).__name__}.")
    if not isinstance(observations, Sequence):
        raise TypeError(f"Expected Sequence of CalibrationObservation, got {type(observations).__name__}.")
    if len(observations) == 0:
        raise ValueError("Cannot calibrate ThresholdPolicy from empty calibration observations.")

    # 1. Group observations by state and validate honest observations
    obs_by_state: dict[str, list[CalibrationObservation]] = {}
    for idx, obs in enumerate(observations):
        if not isinstance(obs, CalibrationObservation):
            raise TypeError(
                f"Observation at index {idx} must be a CalibrationObservation, got {type(obs).__name__}."
            )
        st = obs.state_name.strip().lower()
        if st not in obs_by_state:
            obs_by_state[st] = []
        obs_by_state[st].append(obs)

    # 2. Calibrate thresholds for all supported metrics
    threshold_dict: dict[str, MetricThreshold] = {}

    for st_name, st_obs_list in obs_by_state.items():
        n_st = len(st_obs_list)
        if n_st < 2:
            raise ValueError(
                f"Insufficient calibration observations for state '{st_name}' (N={n_st}). "
                "At least N >= 2 calibration observations are required."
            )

        # A. Overlap Fidelity (LOWER)
        fid_samples = [obs.fidelity for obs in st_obs_list]
        th_fid = calibrate_metric_threshold(
            metric_name=f"fidelity:{st_name}",
            samples=fid_samples,
            direction=ThresholdDirection.LOWER,
            method=method,
            alpha=alpha,
            multiplier=multiplier,
        )
        threshold_dict[th_fid.metric_name] = th_fid

        # B. Quantum Bit Error Rate (QBER) (UPPER)
        qber_samples = [obs.qber for obs in st_obs_list]
        th_qber = calibrate_metric_threshold(
            metric_name=f"qber:{st_name}",
            samples=qber_samples,
            direction=ThresholdDirection.UPPER,
            method=method,
            alpha=alpha,
            multiplier=multiplier,
        )
        threshold_dict[th_qber.metric_name] = th_qber

        # C. Born Probability Distributions (Z, X, Y) — TV Distance from baseline expected distribution
        for basis_key in ("probabilities_z", "probabilities_x", "probabilities_y"):
            base_dist_mean: dict[str, float] = {}
            for outcome in ("0", "1", "+", "-", "+i", "-i"):
                m_name = f"prob_{outcome}:{st_name}"
                if m_name in baseline.metrics:
                    base_dist_mean[outcome] = baseline.metrics[m_name].mean

            if base_dist_mean:
                tvd_samples: list[float] = []
                for obs in st_obs_list:
                    obs_dist = getattr(obs, basis_key, {})
                    all_outcomes = set(obs_dist.keys()) | set(base_dist_mean.keys())
                    tvd = 0.5 * sum(
                        abs(obs_dist.get(o, 0.0) - base_dist_mean.get(o, 0.0))
                        for o in all_outcomes
                    )
                    tvd_samples.append(tvd)

                if len(tvd_samples) >= 2:
                    dist_metric_name = f"{basis_key}:{st_name}"
                    th_dist = calibrate_metric_threshold(
                        metric_name=dist_metric_name,
                        samples=tvd_samples,
                        direction=ThresholdDirection.UPPER,
                        method=method,
                        alpha=alpha,
                        multiplier=multiplier,
                        metadata={"baseline_distribution": dict(base_dist_mean)},
                    )
                    threshold_dict[th_dist.metric_name] = th_dist

        # C2. Individual Born Probability Outcome Absolute Deviations
        # A raw probability anomaly depends on expected probability (e.g. 0.5 can shift high or low).
        # Anomaly thresholding therefore evaluates absolute deviation |p - baseline_mean| (UPPER tail).
        for basis_key, basis_char in [
            ("probabilities_z", "z"),
            ("probabilities_x", "x"),
            ("probabilities_y", "y"),
        ]:
            for outcome in ("0", "1", "+", "-", "+i", "-i"):
                p_key = f"prob_{basis_char}_{outcome}:{st_name}"
                alt_key = f"prob_{outcome}:{st_name}"
                target_key = p_key if p_key in baseline.metrics else (alt_key if alt_key in baseline.metrics else None)
                if target_key is not None:
                    p_mean = baseline.metrics[target_key].mean
                    p_dev_samples = [
                        abs(getattr(obs, basis_key, {}).get(outcome, 0.0) - p_mean)
                        for obs in st_obs_list
                        if outcome in getattr(obs, basis_key, {})
                    ]
                    if len(p_dev_samples) >= 2:
                        th_pdev = calibrate_metric_threshold(
                            metric_name=f"prob_dev_{basis_char}_{outcome}:{st_name}",
                            samples=p_dev_samples,
                            direction=ThresholdDirection.UPPER,
                            method=method,
                            alpha=alpha,
                            multiplier=multiplier,
                            metadata={"baseline_mean": p_mean, "basis": basis_char, "outcome": outcome},
                        )
                        threshold_dict[th_pdev.metric_name] = th_pdev

        # D. Pauli Expectations (Absolute Deviations)
        # Raw Pauli expectations can be positive or negative depending on state (+1 for |0>, -1 for |1>).
        # Anomaly thresholds MUST evaluate absolute deviations |<sigma> - baseline_mean| (UPPER tail).
        for op in ("X", "Y", "Z"):
            exp_metric_name = f"exp_{op.lower()}:{st_name}"
            if exp_metric_name in baseline.metrics:
                b_mean = baseline.metrics[exp_metric_name].mean
                exp_dev_samples = [
                    abs(obs.pauli_expectations.get(op, 0.0) - b_mean)
                    for obs in st_obs_list
                ]
                if len(exp_dev_samples) >= 2:
                    th_exp = calibrate_metric_threshold(
                        metric_name=f"pauli_{op.lower()}:{st_name}",
                        samples=exp_dev_samples,
                        direction=ThresholdDirection.UPPER,
                        method=method,
                        alpha=alpha,
                        multiplier=multiplier,
                        metadata={"baseline_mean": b_mean},
                    )
                    threshold_dict[th_exp.metric_name] = th_exp

    # E. Bell State Correlations (Absolute Deviations)
    # Bell correlations can legitimately be +1.0 or -1.0 depending on the Bell state
    # (e.g. Phi+ has YY = -1.0; Psi+ has ZZ = -1.0).
    # Consequently, Bell-correlation anomaly thresholds evaluate baseline-relative
    # absolute deviations |<O> - baseline_mean| (UPPER tail).
    for bell_op in ("XX", "YY", "ZZ"):
        bell_metric_name = f"bell_{bell_op.lower()}"
        if bell_metric_name in baseline.metrics:
            b_mean = baseline.metrics[bell_metric_name].mean
            bell_dev_samples = [
                abs(obs.bell_correlations[bell_op] - b_mean)
                for obs in observations
                if obs.bell_correlations is not None and bell_op in obs.bell_correlations
            ]
            if len(bell_dev_samples) >= 2:
                th_bell = calibrate_metric_threshold(
                    metric_name=bell_metric_name,
                    samples=bell_dev_samples,
                    direction=ThresholdDirection.UPPER,
                    method=method,
                    alpha=alpha,
                    multiplier=multiplier,
                    metadata={"baseline_mean": b_mean, "bell_operator": bell_op},
                )
                threshold_dict[th_bell.metric_name] = th_bell

    resolved_pid = (
        policy_id.strip()
        if policy_id is not None and policy_id.strip()
        else f"policy_{baseline.configuration.configuration_id}_{method.value}_{alpha}"
    )

    policy_meta = {
        "calibration_observation_count": len(observations),
        "states_calibrated": tuple(sorted(obs_by_state.keys())),
        "baseline_configuration_id": baseline.configuration.configuration_id,
        "calibrated_at": datetime.now(timezone.utc).isoformat(),
    }
    if metadata is not None:
        policy_meta.update(dict(metadata))

    return ThresholdPolicy(
        policy_id=resolved_pid,
        baseline_configuration_hash=baseline.configuration.canonical_hash,
        configuration=baseline.configuration,
        thresholds=threshold_dict,
        alpha=alpha if method == ThresholdMethod.EMPIRICAL_QUANTILE else None,
        method=method,
        calibration_sample_count=len(observations),
        metadata=policy_meta,
    )


# ==============================================================================
# Threshold Evaluation Engine
# ==============================================================================

def evaluate_metric_threshold(
    observed_value: float,
    threshold: MetricThreshold,
    atol: float = 1e-9,
) -> MetricThresholdEvaluation:
    """Evaluate an observed scalar metric value against a calibrated MetricThreshold.

    Boundary Convention (atol = 1e-9):
        UPPER Threshold (degradation is larger value):
            observed > threshold + atol   => exceeded = True, boundary_status = 'strictly_exceeded'
            |observed - threshold| <= atol => exceeded = False, boundary_status = 'at_boundary'
            observed < threshold - atol   => exceeded = False, boundary_status = 'strictly_inside'
            margin = observed - threshold (positive indicates exceedance)

        LOWER Threshold (degradation is smaller value):
            observed < threshold - atol   => exceeded = True, boundary_status = 'strictly_exceeded'
            |observed - threshold| <= atol => exceeded = False, boundary_status = 'at_boundary'
            observed > threshold + atol   => exceeded = False, boundary_status = 'strictly_inside'
            margin = threshold - observed (positive indicates exceedance)

    Args:
        observed_value: Numerical observed value.
        threshold: MetricThreshold to evaluate against.
        atol: Numerical boundary tolerance. Default: 1e-9.

    Returns:
        MetricThresholdEvaluation containing descriptive threshold comparison evidence.
    """
    if not isinstance(observed_value, (int, float, np.floating)) or isinstance(observed_value, bool):
        raise TypeError(f"observed_value must be float, got {type(observed_value).__name__}.")
    if not math.isfinite(float(observed_value)):
        raise ValueError(f"observed_value must be finite, got {observed_value}.")
    if not isinstance(threshold, MetricThreshold):
        raise TypeError(f"threshold must be MetricThreshold, got {type(threshold).__name__}.")
    if not isinstance(atol, (int, float, np.floating)) or isinstance(atol, bool):
        raise TypeError(f"atol must be float, got {type(atol).__name__}.")
    if float(atol) < 0.0:
        raise ValueError(f"atol must be non-negative, got {atol}.")

    obs = float(observed_value)
    t_val = float(threshold.threshold_value)
    tol = float(atol)
    signed_dist = obs - t_val

    if threshold.direction == ThresholdDirection.UPPER:
        margin = obs - t_val
        if obs > t_val + tol:
            exceeded = True
            boundary_status = "strictly_exceeded"
        elif abs(obs - t_val) <= tol:
            exceeded = False
            boundary_status = "at_boundary"
        else:
            exceeded = False
            boundary_status = "strictly_inside"
    elif threshold.direction == ThresholdDirection.LOWER:
        margin = t_val - obs
        if obs < t_val - tol:
            exceeded = True
            boundary_status = "strictly_exceeded"
        elif abs(obs - t_val) <= tol:
            exceeded = False
            boundary_status = "at_boundary"
        else:
            exceeded = False
            boundary_status = "strictly_inside"
    else:
        raise ValueError(f"Unsupported threshold direction: {threshold.direction}.")

    return MetricThresholdEvaluation(
        metric_name=threshold.metric_name,
        observed_value=obs,
        threshold_value=t_val,
        direction=threshold.direction,
        exceeded=exceeded,
        margin=margin,
        signed_distance=signed_dist,
        method=threshold.method,
        boundary_status=boundary_status,
        metadata={
            "alpha": threshold.alpha,
            "quantile": threshold.quantile,
            "multiplier": threshold.multiplier,
            "sample_count": threshold.sample_count,
            "atol": tol,
        },
    )


def evaluate_policy(
    evidence_or_obs: StatisticalEvidence | VerificationObservation | CalibrationObservation | Mapping[str, Any],
    policy: ThresholdPolicy,
    strict_hash: bool = True,
    atol: float = 1e-9,
) -> PolicyEvaluationReport:
    """Evaluate verification evidence or observation against a full calibrated ThresholdPolicy.

    Enforces Configuration Compatibility:
        Verifies that the target observation / evidence was collected under conditions
        matching the policy's calibrated configuration hash.
        Mismatches raise ConfigurationCompatibilityError.

    Scientific Boundary:
        Produces descriptive threshold evaluations for each metric in the policy.
        Does NOT produce final security verdicts (ACCEPT / SUSPICIOUS / ATTACK)
        and does NOT compute an arbitrary security score.

    Args:
        evidence_or_obs: M10 StatisticalEvidence, VerificationObservation, or CalibrationObservation.
        policy: Calibrated ThresholdPolicy.
        strict_hash: If True, requires exact match between observation configuration hash and policy hash.
        atol: Numerical boundary tolerance. Default: 1e-9.

    Returns:
        Immutable PolicyEvaluationReport.

    Raises:
        TypeError: If evidence_or_obs or policy has an invalid type.
        ConfigurationCompatibilityError: If configuration hashes mismatch under strict_hash.
    """
    if not isinstance(policy, ThresholdPolicy):
        raise TypeError(f"Expected ThresholdPolicy, got {type(policy).__name__}.")

    # 1. Configuration compatibility validation
    obs_hash: str | None = None
    if isinstance(evidence_or_obs, StatisticalEvidence):
        obs_hash = evidence_or_obs.baseline_configuration_hash
    elif isinstance(evidence_or_obs, (VerificationObservation, CalibrationObservation)):
        cfg = getattr(evidence_or_obs, "configuration", None)
        if isinstance(cfg, BaselineConfiguration):
            obs_hash = cfg.canonical_hash
        elif isinstance(cfg, Mapping):
            obs_hash = cfg.get("canonical_hash")
    elif isinstance(evidence_or_obs, Mapping):
        obs_hash = evidence_or_obs.get("baseline_configuration_hash") or evidence_or_obs.get("configuration_hash")

    if strict_hash and obs_hash is not None:
        if obs_hash != policy.baseline_configuration_hash:
            raise ConfigurationCompatibilityError(
                f"Configuration hash mismatch: observation hash '{obs_hash}' does not match "
                f"calibrated policy hash '{policy.baseline_configuration_hash}'."
            )

    # 2. Extract observed metric values from the provided evidence or observation
    metric_values: dict[str, float] = {}

    if isinstance(evidence_or_obs, StatisticalEvidence):
        for m_name, m_dev in evidence_or_obs.metric_deviations.items():
            metric_values[m_name] = m_dev.observed_value
            metric_values[f"{m_name}:abs_dev"] = m_dev.absolute_deviation
            if m_name.startswith("exp_"):
                # Map exp_x:0 to pauli_x:0 absolute deviation
                op_st = m_name[4:]
                metric_values[f"pauli_{op_st}"] = m_dev.absolute_deviation
            if m_name.startswith("bell_"):
                # Bell correlation threshold evaluates absolute deviation |corr - mu|
                metric_values[m_name] = m_dev.absolute_deviation
                metric_values[f"{m_name}:raw"] = m_dev.observed_value
            if m_name.startswith("prob_"):
                # Map prob_z_0:0 to prob_dev_z_0:0 absolute deviation
                metric_values[f"prob_dev_{m_name[5:]}"] = m_dev.absolute_deviation

        for d_name, d_comp in evidence_or_obs.distribution_comparisons.items():
            metric_values[d_name] = d_comp.total_variation_distance
            metric_values[f"{d_name}:tvd"] = d_comp.total_variation_distance

    elif isinstance(evidence_or_obs, (VerificationObservation, CalibrationObservation)):
        st = evidence_or_obs.state_name.strip().lower()
        metric_values[f"fidelity:{st}"] = evidence_or_obs.fidelity
        metric_values[f"qber:{st}"] = evidence_or_obs.qber

        for basis_key in ("probabilities_z", "probabilities_x", "probabilities_y"):
            basis_char = basis_key[-1]
            probs = getattr(evidence_or_obs, basis_key, {})
            for outcome, p_val in probs.items():
                metric_values[f"prob_{outcome}:{st}"] = float(p_val)
                metric_values[f"prob_{basis_char}_{outcome}:{st}"] = float(p_val)
                prob_dev_key = f"prob_dev_{basis_char}_{outcome}:{st}"
                if prob_dev_key in policy.thresholds:
                    p_mean = policy.thresholds[prob_dev_key].metadata.get("baseline_mean")
                    if p_mean is not None:
                        metric_values[prob_dev_key] = abs(float(p_val) - float(p_mean))

            th_dist_key = f"{basis_key}:{st}"
            if th_dist_key in policy.thresholds:
                base_dist_ref = policy.thresholds[th_dist_key].metadata.get("baseline_distribution", {})
                if base_dist_ref:
                    all_out = set(probs.keys()) | set(base_dist_ref.keys())
                    tvd = 0.5 * sum(abs(probs.get(o, 0.0) - base_dist_ref.get(o, 0.0)) for o in all_out)
                    metric_values[th_dist_key] = tvd

        for op, exp_val in evidence_or_obs.pauli_expectations.items():
            metric_values[f"exp_{op.lower()}:{st}"] = float(exp_val)
            th_pauli_key = f"pauli_{op.lower()}:{st}"
            if th_pauli_key in policy.thresholds:
                b_mean = policy.thresholds[th_pauli_key].metadata.get("baseline_mean")
                if b_mean is not None:
                    metric_values[th_pauli_key] = abs(float(exp_val) - float(b_mean))
                else:
                    metric_values[th_pauli_key] = float(exp_val)
            else:
                metric_values[th_pauli_key] = float(exp_val)

        # Bell correlations (evaluated as absolute deviation from baseline mean)
        if evidence_or_obs.bell_correlations is not None:
            for bell_op, b_val in evidence_or_obs.bell_correlations.items():
                bell_key = f"bell_{bell_op.lower()}"
                metric_values[f"{bell_key}:raw"] = float(b_val)
                if bell_key in policy.thresholds:
                    b_mean = policy.thresholds[bell_key].metadata.get("baseline_mean")
                    if b_mean is not None:
                        metric_values[bell_key] = abs(float(b_val) - float(b_mean))
                    else:
                        metric_values[bell_key] = float(b_val)
                else:
                    metric_values[bell_key] = float(b_val)

    elif isinstance(evidence_or_obs, Mapping):
        for k, v in evidence_or_obs.items():
            if isinstance(v, (int, float, np.floating)) and not isinstance(v, bool) and math.isfinite(float(v)):
                metric_values[k] = float(v)

    # 3. Evaluate each metric defined in the policy
    evaluations: dict[str, MetricThresholdEvaluation] = {}
    exceeded_list: list[str] = []

    for m_name, th in policy.thresholds.items():
        if m_name in metric_values:
            val = metric_values[m_name]
            ev = evaluate_metric_threshold(observed_value=val, threshold=th, atol=atol)
            evaluations[m_name] = ev
            if ev.exceeded:
                exceeded_list.append(m_name)

    tot = len(evaluations)
    exc_count = len(exceeded_list)
    any_exc = exc_count > 0
    all_exc = (tot > 0) and (exc_count == tot)

    now_iso = datetime.now(timezone.utc).isoformat()

    return PolicyEvaluationReport(
        policy_id=policy.policy_id,
        baseline_configuration_hash=policy.baseline_configuration_hash,
        metric_evaluations=evaluations,
        any_exceeded=any_exc,
        all_exceeded=all_exc,
        exceeded_metrics=tuple(exceeded_list),
        exceeded_count=exc_count,
        total_metrics_evaluated=tot,
        timestamp=now_iso,
        metadata={
            "policy_fingerprint": policy.policy_fingerprint,
            "policy_method": policy.method.value,
            "policy_alpha": policy.alpha,
            "atol": atol,
            "strict_hash": strict_hash,
        },
    )


def evaluate_policy_false_alarm_rate(
    validation_observations: Sequence[VerificationObservation | CalibrationObservation],
    policy: ThresholdPolicy,
    calibration_observations: Sequence[CalibrationObservation] | None = None,
    atol: float = 1e-9,
) -> dict[str, Any]:
    """Calculate empirical false-alarm rate (FAR) by evaluating held-out honest validation observations.

    Data Leakage Prevention:
        Checks that validation_observations does not reuse calibration_observations,
        which would produce optimistic, ungeneralized threshold performance estimates.

    Scientific Principle:
        This is an empirical evaluation statistic describing threshold exceedance frequency
        under honest operating conditions.
        It is NOT an attack detector and does NOT perform attack classification.

    Args:
        validation_observations: Sequence of held-out honest observations.
        policy: Calibrated ThresholdPolicy.
        calibration_observations: Optional sequence of training observations to verify separation.
        atol: Numerical tolerance. Default: 1e-9.

    Returns:
        Dictionary containing overall and per-metric empirical exceedance rates.

    Raises:
        ValueError: If validation_observations is empty or data leakage is detected.
    """
    if not isinstance(validation_observations, Sequence):
        raise TypeError(f"validation_observations must be a Sequence, got {type(validation_observations).__name__}.")
    n_val = len(validation_observations)
    if n_val == 0:
        raise ValueError("validation_observations cannot be empty.")

    # Data leakage check
    if calibration_observations is not None:
        if validation_observations is calibration_observations:
            raise ValueError(
                "Data leakage detected: validation_observations is identical to calibration_observations. "
                "Threshold evaluation must use separate held-out validation data."
            )
        cal_ids = {id(obs) for obs in calibration_observations}
        val_ids = {id(obs) for obs in validation_observations}
        overlap = cal_ids & val_ids
        if overlap:
            raise ValueError(
                f"Data leakage detected: {len(overlap)} validation observation(s) are present in "
                "calibration observations. Threshold evaluation must use separate held-out validation data."
            )

    per_metric_exceeded: dict[str, int] = {k: 0 for k in policy.thresholds.keys()}
    any_exceeded_count = 0

    for obs in validation_observations:
        report = evaluate_policy(obs, policy, strict_hash=False, atol=atol)
        if report.any_exceeded:
            any_exceeded_count += 1
        for m_name in report.exceeded_metrics:
            per_metric_exceeded[m_name] = per_metric_exceeded.get(m_name, 0) + 1

    overall_far = float(any_exceeded_count / n_val)
    per_metric_far = {k: float(v / n_val) for k, v in per_metric_exceeded.items()}

    return {
        "policy_id": policy.policy_id,
        "validation_sample_count": n_val,
        "empirical_false_alarm_rate": overall_far,
        "per_metric_false_alarm_rate": per_metric_far,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
    }

"""Q-SHIELD — Honest Baseline Calibration Structures (Milestone M9).

Defines data structures and statistical methods for characterizing legitimate
quantum verification behavior under honest operating conditions.

Mathematical Foundations:
    1. Sample Mean:
       mu = (1 / N) * sum_{i=1}^N x_i

    2. Sample Variance (Bessel's correction for unbiased sample estimation):
       s^2 = (1 / (N - 1)) * sum_{i=1}^N (x_i - mu)^2,   for N >= 2.
       s^2 = 0.0,                                         for N == 1.

    3. Sample Standard Deviation:
       s = sqrt(s^2)

    4. Standard Error of the Mean:
       SE = s / sqrt(N)

    5. Confidence Interval (Student's t-distribution for small/sample N):
       CI = [mu - t_{1-alpha/2, N-1} * SE, mu + t_{1-alpha/2, N-1} * SE]
       clamped to physical metric domains (e.g., [0, 1] for fidelity/probabilities).

Scientific Boundaries:
    - NOISE != ATTACK: The baseline characterizes honest operating conditions.
    - Strictly NO attack detection, NO security thresholds, and NO threat classification.
    - Generates and preserves honest distributions for subsequent statistical evaluation (M10+).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
import math
from typing import Any
import numpy as np
from scipy.stats import t as student_t


@dataclass(frozen=True)
class MetricStatistics:
    """Immutable descriptive statistics for an observed quantum verification metric.

    Attributes:
        mean: Sample mean mu.
        variance: Unbiased sample variance s^2 with N-1 denominator (0.0 for N=1).
        std_dev: Sample standard deviation s = sqrt(s^2).
        sample_count: Number of repeated observations N >= 1.
        min_value: Minimum observed value.
        max_value: Maximum observed value.
        confidence_interval: Optional (lower, upper) confidence interval.
    """

    mean: float
    variance: float
    std_dev: float
    sample_count: int
    min_value: float
    max_value: float
    confidence_interval: tuple[float, float] | None = None

    def __post_init__(self) -> None:
        """Validate statistical and domain invariants."""
        if not isinstance(self.sample_count, (int, np.integer)) or isinstance(self.sample_count, bool):
            raise TypeError(f"sample_count must be an integer, got {type(self.sample_count).__name__}.")
        if self.sample_count <= 0:
            raise ValueError(f"sample_count must be >= 1, got {self.sample_count}.")

        for val, name in [
            (self.mean, "mean"),
            (self.variance, "variance"),
            (self.std_dev, "std_dev"),
            (self.min_value, "min_value"),
            (self.max_value, "max_value"),
        ]:
            if not isinstance(val, (int, float, np.floating)):
                raise TypeError(f"{name} must be numeric float, got {type(val).__name__}.")
            if not math.isfinite(float(val)):
                raise ValueError(f"{name} must be finite, got {val}.")

        if self.variance < -1e-12:
            raise ValueError(f"variance must be non-negative, got {self.variance}.")
        if self.std_dev < -1e-12:
            raise ValueError(f"std_dev must be non-negative, got {self.std_dev}.")
        if self.min_value > self.max_value + 1e-12:
            raise ValueError(f"min_value ({self.min_value}) cannot exceed max_value ({self.max_value}).")

        if self.confidence_interval is not None:
            if len(self.confidence_interval) != 2:
                raise ValueError(f"confidence_interval must be a 2-tuple, got {self.confidence_interval}.")
            ci_low, ci_high = self.confidence_interval
            if not (math.isfinite(ci_low) and math.isfinite(ci_high)):
                raise ValueError(f"confidence_interval values must be finite, got ({ci_low}, {ci_high}).")
            if ci_low > ci_high + 1e-12:
                raise ValueError(f"confidence_interval lower bound ({ci_low}) exceeds upper bound ({ci_high}).")


@dataclass(frozen=True)
class BaselineConfiguration:
    """Immutable configuration describing the exact operating conditions of an honest baseline.

    Attributes:
        configuration_id: Unique descriptor for this operating environment.
        states: Sequence of quantum state identifiers calibrated in this baseline.
        noise_model_type: Noise channel type identifier ('ideal', 'bit_flip', 'phase_flip', 'depolarizing').
        noise_strength: Channel noise probability parameter p in [0.0, 1.0].
        channel_location: Physical or circuit location of noise ('bob_qubit', 'transmission', 'post_teleportation').
        shots: Number of measurement shots per trial (None for analytical simulation).
        calibration_runs: Number of repeated honest calibration trials N >= 1.
        seed: Optional base random seed used for reproducibility.
        backend: Execution backend ('aer_simulator' or 'mathematical').
    """

    configuration_id: str
    states: tuple[str, ...]
    noise_model_type: str
    noise_strength: float
    channel_location: str
    shots: int | None
    calibration_runs: int
    seed: int | None = None
    backend: str = "mathematical"

    def __post_init__(self) -> None:
        """Validate configuration parameters."""
        if not self.configuration_id.strip():
            raise ValueError("configuration_id cannot be empty.")
        if not self.states:
            raise ValueError("states tuple cannot be empty.")
        if not (0.0 <= self.noise_strength <= 1.0):
            raise ValueError(f"noise_strength must be in [0.0, 1.0], got {self.noise_strength}.")
        if self.calibration_runs <= 0:
            raise ValueError(f"calibration_runs must be >= 1, got {self.calibration_runs}.")
        if self.shots is not None and self.shots <= 0:
            raise ValueError(f"shots must be positive integer or None, got {self.shots}.")

    @property
    def canonical_hash(self) -> str:
        """Compute a deterministic SHA-256 hash identifying this exact operating configuration.

        Enforces configuration isolation across state sets, noise models, noise strengths,
        channel locations, shot counts, calibration run counts, backends, and seeds.
        """
        import hashlib
        import json

        payload = {
            "backend": self.backend,
            "calibration_runs": self.calibration_runs,
            "channel_location": self.channel_location,
            "noise_model_type": self.noise_model_type.lower().strip(),
            "noise_strength": round(float(self.noise_strength), 8),
            "seed": self.seed,
            "shots": self.shots,
            "states": sorted(self.states),
        }
        encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class CalibrationObservation:
    """Immutable container for metrics collected during a single honest verification execution.

    Attributes:
        state_name: Identifier of the quantum input state.
        fidelity: Measured or analytical state fidelity F in [0.0, 1.0].
        qber: Quantum bit error rate in [0.0, 1.0].
        probabilities_z: Born probabilities in computational Z basis.
        probabilities_x: Born probabilities in Hadamard X basis.
        probabilities_y: Born probabilities in circular Y basis.
        pauli_expectations: Expectation values for Pauli X, Y, Z in [-1.0, 1.0].
        bell_correlations: Optional Bell correlation expectations (XX, YY, ZZ) in [-1.0, 1.0].
        shots: Number of measurement shots (None if analytical).
        branch: Measurement outcome branch (m0, m1).
        is_honest: Explicit flag confirming this observation was produced under honest operating conditions.
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
    is_honest: bool = True

    def __post_init__(self) -> None:
        """Validate metric physical bounds, finite values, and enforce honest provenance."""
        # 1. Enforce honest provenance
        if not self.is_honest:
            raise ValueError(
                "CalibrationObservation must represent a legitimate honest quantum execution (is_honest must be True). "
                "Non-honest or attack observations cannot be used for calibration."
            )

        if not self.state_name.strip():
            raise ValueError("state_name cannot be empty.")

        # 2. Validate fidelity and QBER
        for name, val in [("fidelity", self.fidelity), ("qber", self.qber)]:
            if not isinstance(val, (int, float, np.floating)) or isinstance(val, bool):
                raise TypeError(f"{name} must be numeric float, got {type(val).__name__}.")
            if not math.isfinite(float(val)):
                raise ValueError(f"{name} must be finite, got {val}.")
            if not (-1e-7 <= float(val) <= 1.0 + 1e-7):
                raise ValueError(f"{name} must be in [0.0, 1.0], got {val}.")

        # 3. Validate Born probabilities
        for basis_name, prob_dict in [
            ("probabilities_z", self.probabilities_z),
            ("probabilities_x", self.probabilities_x),
            ("probabilities_y", self.probabilities_y),
        ]:
            if not isinstance(prob_dict, dict):
                raise TypeError(f"{basis_name} must be a dictionary.")
            for outcome, prob in prob_dict.items():
                if not isinstance(prob, (int, float, np.floating)) or isinstance(prob, bool):
                    raise TypeError(f"Probability for outcome '{outcome}' in {basis_name} must be float.")
                if not math.isfinite(float(prob)):
                    raise ValueError(f"Probability for outcome '{outcome}' in {basis_name} must be finite.")
                if not (-1e-7 <= float(prob) <= 1.0 + 1e-7):
                    raise ValueError(f"Probability for outcome '{outcome}' in {basis_name} must be in [0, 1], got {prob}.")

            if prob_dict:
                prob_sum = sum(prob_dict.values())
                if not math.isclose(prob_sum, 1.0, abs_tol=1e-5):
                    raise ValueError(f"Probabilities in {basis_name} must sum to 1.0 within tolerance, got {prob_sum}.")

        # 4. Validate Pauli expectations
        if not isinstance(self.pauli_expectations, dict):
            raise TypeError("pauli_expectations must be a dictionary.")
        for op, exp_val in self.pauli_expectations.items():
            if not isinstance(exp_val, (int, float, np.floating)) or isinstance(exp_val, bool):
                raise TypeError(f"Expectation for Pauli '{op}' must be float.")
            if not math.isfinite(float(exp_val)):
                raise ValueError(f"Expectation for Pauli '{op}' must be finite.")
            if not (-1.0 - 1e-7 <= float(exp_val) <= 1.0 + 1e-7):
                raise ValueError(f"Expectation for Pauli '{op}' must be in [-1.0, 1.0], got {exp_val}.")

        # 5. Validate Bell correlations if present
        if self.bell_correlations is not None:
            if not isinstance(self.bell_correlations, dict):
                raise TypeError("bell_correlations must be a dictionary or None.")
            for b_op, b_val in self.bell_correlations.items():
                if not isinstance(b_val, (int, float, np.floating)) or isinstance(b_val, bool):
                    raise TypeError(f"Bell correlation for '{b_op}' must be float.")
                if not math.isfinite(float(b_val)):
                    raise ValueError(f"Bell correlation for '{b_op}' must be finite.")
                if not (-1.0 - 1e-7 <= float(b_val) <= 1.0 + 1e-7):
                    raise ValueError(f"Bell correlation for '{b_op}' must be in [-1.0, 1.0], got {b_val}.")

        # 6. Validate shots
        if self.shots is not None and (self.shots <= 0 or isinstance(self.shots, bool)):
            raise ValueError(f"shots must be a strictly positive integer, got {self.shots}.")

        # 7. Defensive copies to enforce post-construction immutability
        object.__setattr__(self, "probabilities_z", dict(self.probabilities_z))
        object.__setattr__(self, "probabilities_x", dict(self.probabilities_x))
        object.__setattr__(self, "probabilities_y", dict(self.probabilities_y))
        object.__setattr__(self, "pauli_expectations", dict(self.pauli_expectations))
        if self.bell_correlations is not None:
            object.__setattr__(self, "bell_correlations", dict(self.bell_correlations))


@dataclass(frozen=True)
class HonestBaseline:
    """Immutable representation of a calibrated honest baseline model.

    Attributes:
        configuration: BaselineConfiguration describing the calibration parameters.
        metrics: Dictionary mapping metric keys to MetricStatistics.
        metadata: Supplementary operational and provenance metadata.
    """

    configuration: BaselineConfiguration
    metrics: dict[str, MetricStatistics]
    metadata: dict[str, Any]

    def __post_init__(self) -> None:
        """Enforce baseline validity and defensive immutability on construction."""
        object.__setattr__(self, "metrics", dict(self.metrics))
        object.__setattr__(self, "metadata", dict(self.metadata))
        validate_baseline(self)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the baseline into a JSON-serializable dictionary."""
        config_dict = asdict(self.configuration)
        config_dict["canonical_hash"] = self.configuration.canonical_hash
        return {
            "configuration": config_dict,
            "metrics": {k: asdict(v) for k, v in self.metrics.items()},
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> HonestBaseline:
        """Reconstruct an HonestBaseline from a dictionary."""
        config_data = data["configuration"]
        config = BaselineConfiguration(
            configuration_id=config_data["configuration_id"],
            states=tuple(config_data["states"]),
            noise_model_type=config_data["noise_model_type"],
            noise_strength=float(config_data["noise_strength"]),
            channel_location=config_data["channel_location"],
            shots=config_data["shots"],
            calibration_runs=int(config_data["calibration_runs"]),
            seed=config_data.get("seed"),
            backend=config_data.get("backend", "mathematical"),
        )

        metrics: dict[str, MetricStatistics] = {}
        for k, v in data["metrics"].items():
            ci = tuple(v["confidence_interval"]) if v.get("confidence_interval") is not None else None
            metrics[k] = MetricStatistics(
                mean=float(v["mean"]),
                variance=float(v["variance"]),
                std_dev=float(v["std_dev"]),
                sample_count=int(v["sample_count"]),
                min_value=float(v["min_value"]),
                max_value=float(v["max_value"]),
                confidence_interval=ci,  # type: ignore[arg-type]
            )

        return cls(
            configuration=config,
            metrics=metrics,
            metadata=dict(data.get("metadata", {})),
        )


def calculate_sample_statistics(
    values: Sequence[float] | np.ndarray,
    confidence_level: float = 0.95,
    bounds: tuple[float, float] | None = None,
) -> MetricStatistics:
    """Calculate sample descriptive statistics and confidence intervals.

    Mathematical Model:
        - Sample Mean: mu = sum(x_i) / N
        - Sample Variance: s^2 = sum(x_i - mu)^2 / (N - 1)  (for N >= 2)
                           s^2 = 0.0                         (for N == 1)
        - Standard Deviation: s = sqrt(s^2)
        - Confidence Interval: mu +/- t_{crit} * (s / sqrt(N))
          using Student's t-distribution critical value with df = N - 1.

    Args:
        values: Sequence of observed metric scalar values. Must have len >= 1.
        confidence_level: Confidence level in (0.0, 1.0), defaults to 0.95 (95% CI).
        bounds: Optional (min_bound, max_bound) to clamp the confidence interval.

    Returns:
        MetricStatistics instance.

    Raises:
        ValueError: If values sequence is empty, non-finite, or confidence_level invalid.
        TypeError: If values contains non-numeric entries.
    """
    if len(values) == 0:
        raise ValueError("Cannot calculate statistics from empty values sequence.")

    n = len(values)
    arr = np.zeros(n, dtype=np.float64)
    for i, v in enumerate(values):
        if isinstance(v, bool) or not isinstance(v, (int, float, np.floating)):
            raise TypeError(f"Values must be numeric, got element of type {type(v).__name__}.")
        val_float = float(v)
        if not math.isfinite(val_float):
            raise ValueError(f"Values must be finite, got {val_float}.")
        arr[i] = val_float

    mean_val = float(np.mean(arr))
    min_val = float(np.min(arr))
    max_val = float(np.max(arr))

    if n == 1:
        var_val = 0.0
        std_val = 0.0
        # For N=1, degrees of freedom is 0; confidence interval of the population mean is undefined.
        ci = None
    else:
        # Sample variance with N - 1 denominator (ddof=1)
        var_val = float(np.var(arr, ddof=1))
        # Ensure numerical non-negativity
        var_val = max(0.0, var_val)
        std_val = math.sqrt(var_val)

        if not (0.0 < confidence_level < 1.0):
            raise ValueError(f"confidence_level must be in (0.0, 1.0), got {confidence_level}.")

        # Student's t critical value for df = n - 1
        alpha = 1.0 - confidence_level
        t_crit = float(student_t.ppf(1.0 - alpha / 2.0, df=n - 1))
        se = std_val / math.sqrt(n)
        ci_lower = mean_val - t_crit * se
        ci_upper = mean_val + t_crit * se

        if bounds is not None:
            low_b, high_b = bounds
            ci_lower = max(low_b, ci_lower)
            ci_upper = min(high_b, ci_upper)

        ci = (ci_lower, ci_upper)

    return MetricStatistics(
        mean=mean_val,
        variance=var_val,
        std_dev=std_val,
        sample_count=n,
        min_value=min_val,
        max_value=max_val,
        confidence_interval=ci,
    )


def validate_baseline(baseline: HonestBaseline) -> bool:
    """Validate physical and structural invariants of an HonestBaseline.

    Enforces:
        1. Non-empty metrics mapping.
        2. Finite means, variances >= 0, std_dev >= 0.
        3. Physical validity domains for mean, min_value, max_value, and confidence intervals:
           - fidelity in [0.0, 1.0]
           - qber in [0.0, 1.0]
           - probabilities in [0.0, 1.0]
           - expectations in [-1.0, 1.0]
           - Bell correlations in [-1.0, 1.0]

    Args:
        baseline: HonestBaseline instance to validate.

    Returns:
        True if baseline is completely valid.

    Raises:
        TypeError: If baseline is not an HonestBaseline.
        ValueError: If any invariant is violated.
    """
    if not isinstance(baseline, HonestBaseline):
        raise TypeError(f"Expected HonestBaseline, got {type(baseline).__name__}.")

    if not baseline.metrics:
        raise ValueError("HonestBaseline must contain at least one metric.")

    for name, stats in baseline.metrics.items():
        if not isinstance(stats, MetricStatistics):
            raise TypeError(f"Metric '{name}' must be a MetricStatistics instance.")

        # Metric domain checks on mean, min_value, and max_value
        lower_name = name.lower()
        if "fidelity" in lower_name:
            if not (-1e-7 <= stats.mean <= 1.0 + 1e-7):
                raise ValueError(f"Fidelity mean must be in [0.0, 1.0], got {stats.mean} for '{name}'.")
            if not (-1e-7 <= stats.min_value <= 1.0 + 1e-7) or not (-1e-7 <= stats.max_value <= 1.0 + 1e-7):
                raise ValueError(f"Fidelity observed bounds must be in [0.0, 1.0], got [{stats.min_value}, {stats.max_value}] for '{name}'.")
        elif "qber" in lower_name:
            if not (-1e-7 <= stats.mean <= 1.0 + 1e-7):
                raise ValueError(f"QBER mean must be in [0.0, 1.0], got {stats.mean} for '{name}'.")
            if not (-1e-7 <= stats.min_value <= 1.0 + 1e-7) or not (-1e-7 <= stats.max_value <= 1.0 + 1e-7):
                raise ValueError(f"QBER observed bounds must be in [0.0, 1.0], got [{stats.min_value}, {stats.max_value}] for '{name}'.")
        elif lower_name.startswith("prob_") or "probability" in lower_name:
            if not (-1e-7 <= stats.mean <= 1.0 + 1e-7):
                raise ValueError(f"Probability mean must be in [0.0, 1.0], got {stats.mean} for '{name}'.")
            if not (-1e-7 <= stats.min_value <= 1.0 + 1e-7) or not (-1e-7 <= stats.max_value <= 1.0 + 1e-7):
                raise ValueError(f"Probability observed bounds must be in [0.0, 1.0], got [{stats.min_value}, {stats.max_value}] for '{name}'.")
        elif lower_name.startswith("exp_") or "expectation" in lower_name:
            if not (-1.0 - 1e-7 <= stats.mean <= 1.0 + 1e-7):
                raise ValueError(f"Expectation mean must be in [-1.0, 1.0], got {stats.mean} for '{name}'.")
            if not (-1.0 - 1e-7 <= stats.min_value <= 1.0 + 1e-7) or not (-1.0 - 1e-7 <= stats.max_value <= 1.0 + 1e-7):
                raise ValueError(f"Expectation observed bounds must be in [-1.0, 1.0], got [{stats.min_value}, {stats.max_value}] for '{name}'.")
        elif lower_name.startswith("bell_") or "correlation" in lower_name:
            if not (-1.0 - 1e-7 <= stats.mean <= 1.0 + 1e-7):
                raise ValueError(f"Correlation mean must be in [-1.0, 1.0], got {stats.mean} for '{name}'.")
            if not (-1.0 - 1e-7 <= stats.min_value <= 1.0 + 1e-7) or not (-1.0 - 1e-7 <= stats.max_value <= 1.0 + 1e-7):
                raise ValueError(f"Correlation observed bounds must be in [-1.0, 1.0], got [{stats.min_value}, {stats.max_value}] for '{name}'.")

    return True

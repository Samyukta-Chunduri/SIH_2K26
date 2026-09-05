"""Q-SHIELD — Statistical Analysis & Calibration Package (Milestone M9).

Provides data structures, sample statistics calculations, and honest baseline
calibration engines for quantum verification:
    - MetricStatistics
    - BaselineConfiguration
    - CalibrationObservation
    - HonestBaseline
    - calculate_sample_statistics
    - validate_baseline
    - run_honest_calibration_trial
    - calibrate_honest_baseline
    - calibrate_noise_sweep
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

__all__ = [
    "BaselineConfiguration",
    "CalibrationObservation",
    "HonestBaseline",
    "MetricStatistics",
    "STANDARD_STATE_NAMES",
    "build_honest_baseline_from_observations",
    "calculate_sample_statistics",
    "calibrate_honest_baseline",
    "calibrate_noise_sweep",
    "run_honest_calibration_trial",
    "validate_baseline",
]

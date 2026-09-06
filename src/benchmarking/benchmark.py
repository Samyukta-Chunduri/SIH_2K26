"""Q-SHIELD — Deterministic Performance Benchmarking Layer (Milestone M18).

Measures the operational latency, throughput, and workload scaling characteristics
of the already-completed Q-SHIELD security pipeline under controlled, reproducible
conditions.

Architectural Placement:
    Quantum Protocol / Simulation
                  ↓
    M8/M9 Baseline & Calibration
                  ↓
    M10 Statistical Comparison
                  ↓
    M11 Threshold Policy
                  ↓
    M13 Impersonation Detection
    M14 Authorization Detection
    M15 Channel Attack Detection
                  ↓
    M16 Deterministic Evidence Fusion
                  ↓
    M12 Final Security Decision Engine
                  ↓
    M17 Security Evaluation
                  ↓
    M18 Benchmarking (THIS MODULE)

Core Architectural & Scientific Invariants:
    1. Measurement Layer, NOT Detection or Decision Engine:
       M18 measures the operational characteristics of the pipeline. It does NOT
       detect attacks, does NOT replace M12, and does NOT evaluate security correctness.
       M12 remains the SOLE final security decision authority (ACCEPT / SUSPICIOUS / ATTACK).
    2. Zero Scoring & Zero Re-interpretation:
       Strictly no security scores, risk scores, trust scores, threat scores, confidence
       scores, or attack probability ratings. Observed M12 verdict distributions are recorded
       purely as observational measurements.
    3. Zero Detection/Threshold Duplication:
       M18 invokes the existing M12/M16/M17 implementation and never duplicates detection logic,
       precedence rules, or threshold evaluations.
    4. Monotonic Timing Methodology:
       Elapsed execution durations are measured using time.perf_counter() (high-resolution,
       monotonic timer). Wall-clock timestamps are never used for duration calculations.
       Process CPU time is captured via time.process_time().
    5. Warmup Isolation:
       Warmup iterations are executed to mitigate cold-cache / import overheads, but are
       strictly EXCLUDED from measured timing statistics and throughput calculations.
    6. Zero-Denominator & Empty Data Safety:
       When measured iterations or elapsed times are zero, metrics return None (not 0.0, 1.0,
       or fabricated values).
    7. Empirical Timing Reality:
       Benchmark configurations, inputs, and aggregation formulas are 100% deterministic, but
       physical elapsed timing values are empirical, system-dependent measurements affected by
       CPU scheduling, system load, and hardware environment.
    8. Deep Immutability & Secret Guard:
       All benchmark specifications and results are frozen dataclasses with defensive copies
       and recursive secret-leakage guards.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
import math
import time
from typing import Any

from src.detection.decision import DecisionVerdict
from src.detection.fusion import (
    EvidenceSource,
    fuse_security_evidence,
)
from src.evaluation.security_evaluation import (
    EvaluationCategory,
    EvaluationScenario,
    build_baseline_evaluation_suite,
    evaluate_scenario,
    make_anomalous_channel_evidence,
    make_clean_authorization_evidence,
    make_clean_channel_evidence,
    make_clean_impersonation_evidence,
    make_violating_impersonation_evidence,
    run_security_evaluation,
)


# ==============================================================================
# Defensive Helpers: Immutability & Secret Guard
# ==============================================================================

_FORBIDDEN_SECRET_SUBSTRINGS: tuple[str, ...] = (
    "password",
    "secret",
    "private_key",
    "raw_key",
    "token_secret",
    "credential_raw",
    "key_material",
    "shared_secret",
    "api_key",
)


def _deep_freeze_val(val: Any) -> Any:
    """Recursively freeze arbitrary nested mappings and sequences."""
    if isinstance(val, Mapping):
        return {str(k): _deep_freeze_val(v) for k, v in val.items()}
    elif isinstance(val, (list, tuple)):
        return tuple(_deep_freeze_val(x) for x in val)
    elif isinstance(val, (set, frozenset)):
        return frozenset(val)
    return val


def _deep_freeze_dict(d: Mapping[str, Any]) -> dict[str, Any]:
    """Recursively copy nested dictionaries and collections to prevent indirect mutation."""
    return {str(k): _deep_freeze_val(v) for k, v in d.items()}


def _check_for_secret_leakage(d: Mapping[str, Any], container_name: str) -> None:
    """Defensive key-name guard: inspect dictionary and nested structures for obvious secret keywords."""
    for key, val in d.items():
        key_lower = str(key).lower()
        for forbidden in _FORBIDDEN_SECRET_SUBSTRINGS:
            if forbidden in key_lower:
                raise ValueError(
                    f"Sensitive secret keyword '{forbidden}' detected in {container_name} key '{key}'. "
                    "Raw credentials or cryptographic secrets must never be placed in benchmark structures."
                )
        if isinstance(val, Mapping):
            _check_for_secret_leakage(val, f"{container_name}['{key}']")
        elif isinstance(val, (list, tuple)):
            for idx, item in enumerate(val):
                if isinstance(item, Mapping):
                    _check_for_secret_leakage(item, f"{container_name}['{key}'][{idx}]")


# ==============================================================================
# Benchmark Categories
# ==============================================================================

class BenchmarkCategory(str, Enum):
    """Categorical taxonomy of operational benchmarks."""

    BASELINE_EVALUATION = "BASELINE_EVALUATION"
    SUSPICIOUS_EVALUATION = "SUSPICIOUS_EVALUATION"
    ATTACK_EVALUATION = "ATTACK_EVALUATION"
    EVIDENCE_FUSION = "EVIDENCE_FUSION"
    SCENARIO_SCALING = "SCENARIO_SCALING"
    END_TO_END_PIPELINE = "END_TO_END_PIPELINE"


# ==============================================================================
# Benchmark Scenario Specification
# ==============================================================================

@dataclass(frozen=True)
class BenchmarkScenario:
    """Immutable specification of a controlled benchmarking workload.

    Attributes:
        benchmark_id: Unique, non-empty identifier for the benchmark.
        name: Short descriptive title.
        description: Detailed premise and workload conditions.
        category: Taxonomy category from BenchmarkCategory.
        scenario: Optional single EvaluationScenario to execute repeatedly.
        scenario_suite: Optional tuple of EvaluationScenario objects to execute as a batch.
        workload_size: Multiplier or scenario count per iteration (integer >= 1).
        iterations: Number of measured iterations to execute (integer >= 0).
        warmup_iterations: Number of unmeasured warmup iterations (integer >= 0).
        session_id: Optional session identifier constraint for context binding.
        configuration_hash: Optional canonical baseline configuration hash constraint.
        metadata: Contextual metadata dictionary.
    """

    benchmark_id: str
    name: str
    description: str
    category: BenchmarkCategory
    scenario: EvaluationScenario | None = None
    scenario_suite: tuple[EvaluationScenario, ...] = ()
    workload_size: int = 1
    iterations: int = 10
    warmup_iterations: int = 2
    session_id: str | None = None
    configuration_hash: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate typing, field invariants, immutability, and secret leakage."""
        if not isinstance(self.benchmark_id, str):
            raise TypeError(f"benchmark_id must be str, got {type(self.benchmark_id).__name__}.")
        if not self.benchmark_id.strip():
            raise ValueError("benchmark_id cannot be empty or whitespace.")

        if not isinstance(self.name, str):
            raise TypeError(f"name must be str, got {type(self.name).__name__}.")
        if not self.name.strip():
            raise ValueError("name cannot be empty or whitespace.")

        if not isinstance(self.description, str):
            raise TypeError(f"description must be str, got {type(self.description).__name__}.")
        if not self.description.strip():
            raise ValueError("description cannot be empty or whitespace.")

        # Category normalization & validation
        if not isinstance(self.category, BenchmarkCategory):
            if isinstance(self.category, str):
                try:
                    object.__setattr__(self, "category", BenchmarkCategory(self.category.strip()))
                except ValueError as exc:
                    raise ValueError(f"Invalid BenchmarkCategory: '{self.category}'.") from exc
            else:
                raise TypeError(f"category must be BenchmarkCategory, got {type(self.category).__name__}.")

        if self.scenario is not None and not isinstance(self.scenario, EvaluationScenario):
            raise TypeError(f"scenario must be EvaluationScenario or None, got {type(self.scenario).__name__}.")

        if not isinstance(self.scenario_suite, Sequence) or isinstance(self.scenario_suite, (str, bytes)):
            raise TypeError(f"scenario_suite must be a Sequence of EvaluationScenario, got {type(self.scenario_suite).__name__}.")
        for idx, s in enumerate(self.scenario_suite):
            if not isinstance(s, EvaluationScenario):
                raise TypeError(f"scenario_suite[{idx}] must be EvaluationScenario, got {type(s).__name__}.")
        object.__setattr__(self, "scenario_suite", tuple(self.scenario_suite))

        if not isinstance(self.workload_size, int) or self.workload_size < 1:
            raise ValueError(f"workload_size must be an integer >= 1, got {self.workload_size}.")

        if not isinstance(self.iterations, int) or self.iterations < 0:
            raise ValueError(f"iterations must be a non-negative integer, got {self.iterations}.")

        if not isinstance(self.warmup_iterations, int) or self.warmup_iterations < 0:
            raise ValueError(f"warmup_iterations must be a non-negative integer, got {self.warmup_iterations}.")

        # Context validation
        if self.session_id is not None:
            if not isinstance(self.session_id, str):
                raise TypeError(f"session_id must be str or None, got {type(self.session_id).__name__}.")
            if not self.session_id.strip():
                raise ValueError("session_id cannot be empty or whitespace when provided.")

        if self.configuration_hash is not None:
            if not isinstance(self.configuration_hash, str):
                raise TypeError(f"configuration_hash must be str or None, got {type(self.configuration_hash).__name__}.")
            if not self.configuration_hash.strip():
                raise ValueError("configuration_hash cannot be empty or whitespace when provided.")

        if not isinstance(self.metadata, Mapping):
            raise TypeError(f"metadata must be a Mapping, got {type(self.metadata).__name__}.")
        _check_for_secret_leakage(self.metadata, "BenchmarkScenario.metadata")
        object.__setattr__(self, "metadata", _deep_freeze_dict(self.metadata))


# ==============================================================================
# Benchmark Result Container
# ==============================================================================

@dataclass(frozen=True)
class BenchmarkResult:
    """Immutable result record of a benchmark execution.

    All timing attributes represent monotonic high-resolution measurements.
    Zero-denominator conditions explicitly result in None.

    Attributes:
        benchmark_id: Identifier of the benchmark.
        benchmark_name: Title of the benchmark.
        category: Taxonomy category.
        workload_size: Scenario volume or multiplier per iteration.
        target_iterations: Intended measured iteration count.
        warmup_iterations: Executed unmeasured warmup iteration count.
        executed_iterations: Actual measured iterations attempted.
        successful_iterations: Successfully measured iterations completed.
        failed_iterations: Failed or errored iterations.
        total_elapsed_seconds: Total elapsed monotonic duration across measured iterations.
        cpu_time_seconds: Total process CPU time consumed during measured iterations.
        mean_latency_seconds: Mean duration per iteration (or None if successful_iterations == 0).
        min_latency_seconds: Minimum duration observed (or None if successful_iterations == 0).
        max_latency_seconds: Maximum duration observed (or None if successful_iterations == 0).
        median_latency_seconds: Median duration observed (or None if successful_iterations == 0).
        p95_latency_seconds: 95th percentile duration observed (or None if successful_iterations == 0).
        throughput_ops_per_sec: Operations per second (or None if total_elapsed <= 0 or successful_iterations == 0).
        raw_latencies: Tuple of elapsed durations for each measured iteration.
        observed_verdict_counts: Observational count of M12 verdicts observed.
        errors: Tuple of error messages if failures occurred.
        session_id: Context session ID if present.
        configuration_hash: Context configuration hash if present.
        metadata: Deep-frozen contextual metadata dictionary.
    """

    benchmark_id: str
    benchmark_name: str
    category: BenchmarkCategory
    workload_size: int
    target_iterations: int
    warmup_iterations: int
    executed_iterations: int
    successful_iterations: int
    failed_iterations: int
    total_elapsed_seconds: float
    cpu_time_seconds: float | None = None
    mean_latency_seconds: float | None = None
    min_latency_seconds: float | None = None
    max_latency_seconds: float | None = None
    median_latency_seconds: float | None = None
    p95_latency_seconds: float | None = None
    throughput_ops_per_sec: float | None = None
    raw_latencies: tuple[float, ...] = ()
    observed_verdict_counts: dict[str, int] = field(default_factory=dict)
    errors: tuple[str, ...] = ()
    session_id: str | None = None
    configuration_hash: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Enforce validation, tuple conversions, sorting, and secret checks."""
        if not isinstance(self.benchmark_id, str) or not self.benchmark_id.strip():
            raise ValueError("benchmark_id must be a non-empty string.")
        if not isinstance(self.benchmark_name, str) or not self.benchmark_name.strip():
            raise ValueError("benchmark_name must be a non-empty string.")
        if not isinstance(self.category, BenchmarkCategory):
            raise TypeError(f"category must be BenchmarkCategory, got {type(self.category).__name__}.")

        object.__setattr__(self, "raw_latencies", tuple(float(x) for x in self.raw_latencies))
        object.__setattr__(self, "errors", tuple(str(e) for e in self.errors))
        object.__setattr__(self, "observed_verdict_counts", dict(self.observed_verdict_counts))

        if not isinstance(self.metadata, Mapping):
            raise TypeError(f"metadata must be a Mapping, got {type(self.metadata).__name__}.")
        _check_for_secret_leakage(self.metadata, "BenchmarkResult.metadata")
        object.__setattr__(self, "metadata", _deep_freeze_dict(self.metadata))


# ==============================================================================
# Benchmark Suite Result Container
# ==============================================================================

@dataclass(frozen=True)
class BenchmarkSuiteResult:
    """Immutable aggregate report of a benchmark suite execution.

    Attributes:
        suite_id: Identifier of the benchmark suite.
        total_benchmarks: Total benchmark specifications executed.
        successful_benchmarks: Number of benchmarks that executed with zero failed iterations.
        failed_benchmarks: Number of benchmarks that encountered failed iterations.
        total_elapsed_seconds: Cumulative elapsed monotonic seconds across all benchmarks.
        results: Tuple of individual BenchmarkResult objects in deterministic execution order.
        metadata: Deep-frozen contextual metadata dictionary.
    """

    suite_id: str
    total_benchmarks: int
    successful_benchmarks: int
    failed_benchmarks: int
    total_elapsed_seconds: float
    results: tuple[BenchmarkResult, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Enforce validation, tuple conversions, and secret checks."""
        if not isinstance(self.suite_id, str) or not self.suite_id.strip():
            raise ValueError("suite_id must be a non-empty string.")

        object.__setattr__(self, "results", tuple(self.results))
        if not isinstance(self.metadata, Mapping):
            raise TypeError(f"metadata must be a Mapping, got {type(self.metadata).__name__}.")
        _check_for_secret_leakage(self.metadata, "BenchmarkSuiteResult.metadata")
        object.__setattr__(self, "metadata", _deep_freeze_dict(self.metadata))

    @property
    def results_by_id(self) -> dict[str, BenchmarkResult]:
        """Convenience dictionary mapping benchmark_id to BenchmarkResult for safe ID-based lookup."""
        return {r.benchmark_id: r for r in self.results}

    def get_result(self, benchmark_id: str) -> BenchmarkResult | None:
        """Retrieve benchmark result for a specific benchmark identifier."""
        return self.results_by_id.get(benchmark_id)


# ==============================================================================
# Benchmark Execution Engine
# ==============================================================================

def run_benchmark(benchmark: BenchmarkScenario) -> BenchmarkResult:
    """Execute a single benchmark specification deterministically.

    Timing Methodology:
        1. Executes warmup iterations (if configured). Warmup timings are discarded
           and strictly excluded from measurement statistics.
        2. Measures individual iterations using time.perf_counter().
        3. Measures process CPU time using time.process_time().
        4. Calculates statistical metrics: min, max, mean, median, p95, throughput.
        5. Observes M12 verdicts produced by the pipeline without altering or re-interpreting them.
        6. Enforces zero-denominator rules: returns None for undefined metrics.

    Args:
        benchmark: Validated BenchmarkScenario definition.

    Returns:
        Immutable BenchmarkResult recording statistical metrics and observational diagnostics.
    """
    if not isinstance(benchmark, BenchmarkScenario):
        raise TypeError(f"benchmark must be BenchmarkScenario, got {type(benchmark).__name__}.")

    # --- Warmup Phase (Discarded from Timing) ---
    for _ in range(benchmark.warmup_iterations):
        _execute_workload_iteration(benchmark)

    # --- Measurement Phase ---
    raw_latencies: list[float] = []
    errors: list[str] = []
    verdict_counts: dict[str, int] = {
        DecisionVerdict.ACCEPT.value: 0,
        DecisionVerdict.SUSPICIOUS.value: 0,
        DecisionVerdict.ATTACK.value: 0,
    }

    cpu_start = time.process_time()
    total_start = time.perf_counter()

    for _ in range(benchmark.iterations):
        t0 = time.perf_counter()
        try:
            observed_verdicts = _execute_workload_iteration(benchmark)
            t1 = time.perf_counter()
            duration = t1 - t0
            raw_latencies.append(duration)
            for v in observed_verdicts:
                verdict_counts[v.value] += 1
        except Exception as exc:
            t1 = time.perf_counter()
            errors.append(f"{type(exc).__name__}: {exc}")

    total_end = time.perf_counter()
    cpu_end = time.process_time()

    total_elapsed = total_end - total_start
    cpu_time = cpu_end - cpu_start

    successful_count = len(raw_latencies)
    failed_count = len(errors)
    executed_count = successful_count + failed_count

    # --- Statistical Calculations (with Zero-Denominator Protections) ---
    mean_lat: float | None = None
    min_lat: float | None = None
    max_lat: float | None = None
    median_lat: float | None = None
    p95_lat: float | None = None
    throughput: float | None = None

    if successful_count > 0:
        sum_lat = sum(raw_latencies)
        mean_lat = sum_lat / float(successful_count)
        min_lat = min(raw_latencies)
        max_lat = max(raw_latencies)

        sorted_lats = sorted(raw_latencies)
        # Median calculation
        mid = successful_count // 2
        if successful_count % 2 == 1:
            median_lat = sorted_lats[mid]
        else:
            median_lat = (sorted_lats[mid - 1] + sorted_lats[mid]) / 2.0

        # p95 calculation (nearest-rank method)
        p95_idx = int(math.ceil(0.95 * successful_count)) - 1
        p95_idx = max(0, min(p95_idx, successful_count - 1))
        p95_lat = sorted_lats[p95_idx]

        # Throughput = total operations / total elapsed seconds
        total_ops = successful_count * benchmark.workload_size
        if total_elapsed > 0.0:
            throughput = float(total_ops) / total_elapsed

    return BenchmarkResult(
        benchmark_id=benchmark.benchmark_id,
        benchmark_name=benchmark.name,
        category=benchmark.category,
        workload_size=benchmark.workload_size,
        target_iterations=benchmark.iterations,
        warmup_iterations=benchmark.warmup_iterations,
        executed_iterations=executed_count,
        successful_iterations=successful_count,
        failed_iterations=failed_count,
        total_elapsed_seconds=total_elapsed,
        cpu_time_seconds=cpu_time,
        mean_latency_seconds=mean_lat,
        min_latency_seconds=min_lat,
        max_latency_seconds=max_lat,
        median_latency_seconds=median_lat,
        p95_latency_seconds=p95_lat,
        throughput_ops_per_sec=throughput,
        raw_latencies=tuple(raw_latencies),
        observed_verdict_counts=verdict_counts,
        errors=tuple(errors),
        session_id=benchmark.session_id,
        configuration_hash=benchmark.configuration_hash,
        metadata=benchmark.metadata,
    )


def _execute_workload_iteration(benchmark: BenchmarkScenario) -> list[DecisionVerdict]:
    """Internal helper to execute one workload iteration and extract observed verdicts."""
    verdicts: list[DecisionVerdict] = []

    if benchmark.scenario_suite:
        # Batch scenario suite evaluation
        summary = run_security_evaluation(benchmark.scenario_suite)
        for r in summary.results:
            verdicts.append(r.observed_verdict)
    elif benchmark.scenario is not None:
        # Single scenario evaluated workload_size times
        for _ in range(benchmark.workload_size):
            res = evaluate_scenario(benchmark.scenario)
            verdicts.append(res.observed_verdict)
    elif benchmark.category == BenchmarkCategory.EVIDENCE_FUSION:
        # Synthetic fusion workload
        m13 = make_clean_impersonation_evidence(session_id=benchmark.session_id, configuration_hash=benchmark.configuration_hash)
        m14 = make_clean_authorization_evidence(session_id=benchmark.session_id, configuration_hash=benchmark.configuration_hash)
        m15 = make_clean_channel_evidence(session_id=benchmark.session_id, configuration_hash=benchmark.configuration_hash)
        for _ in range(benchmark.workload_size):
            fused = fuse_security_evidence(
                impersonation_evidence=m13,
                authorization_evidence=m14,
                channel_evidence=m15,
                required_sources=(EvidenceSource.IMPERSONATION.value, EvidenceSource.AUTHORIZATION.value, EvidenceSource.QUANTUM_CHANNEL.value),
                expected_session_id=benchmark.session_id,
                expected_configuration_hash=benchmark.configuration_hash,
            )
            verdicts.append(DecisionVerdict.ACCEPT if fused.is_complete and not fused.is_explicit_violation else DecisionVerdict.SUSPICIOUS)
    else:
        # Empty workload fallback: evaluate default clean scenario
        sc_clean = EvaluationScenario(
            scenario_id="SCEN_INTERNAL_BENCH_CLEAN",
            name="Internal Clean Scenario",
            description="Default clean workload",
            category=EvaluationCategory.CLEAN_HONEST,
            expected_verdict=DecisionVerdict.ACCEPT,
            expected_session_id=benchmark.session_id,
            expected_configuration_hash=benchmark.configuration_hash,
        )
        for _ in range(benchmark.workload_size):
            res = evaluate_scenario(sc_clean)
            verdicts.append(res.observed_verdict)

    return verdicts


def run_benchmark_suite(
    benchmarks: Sequence[BenchmarkScenario],
    suite_id: str = "suite_qshield_benchmarks",
    metadata: Mapping[str, Any] | None = None,
) -> BenchmarkSuiteResult:
    """Execute a sequence of benchmark specifications and return an aggregate suite report.

    Args:
        benchmarks: Sequence of BenchmarkScenario objects to execute.
        suite_id: Identifier for the suite.
        metadata: Contextual metadata dictionary.

    Returns:
        Immutable BenchmarkSuiteResult containing all individual benchmark results.
    """
    if not isinstance(benchmarks, Sequence) or isinstance(benchmarks, (str, bytes)):
        raise TypeError(f"benchmarks must be a Sequence of BenchmarkScenario, got {type(benchmarks).__name__}.")

    results: list[BenchmarkResult] = []
    total_elapsed = 0.0
    successful_count = 0
    failed_count = 0

    meta_dict = dict(metadata) if metadata is not None else {}
    seen_ids: set[str] = set()

    for b in benchmarks:
        if not isinstance(b, BenchmarkScenario):
            raise TypeError(f"Each item in benchmarks must be a BenchmarkScenario, got {type(b).__name__}.")
        if b.benchmark_id in seen_ids:
            raise ValueError(f"Duplicate benchmark_id '{b.benchmark_id}' in benchmark suite.")
        seen_ids.add(b.benchmark_id)
        res = run_benchmark(b)
        results.append(res)
        total_elapsed += res.total_elapsed_seconds
        if res.failed_iterations == 0:
            successful_count += 1
        else:
            failed_count += 1

    return BenchmarkSuiteResult(
        suite_id=suite_id,
        total_benchmarks=len(results),
        successful_benchmarks=successful_count,
        failed_benchmarks=failed_count,
        total_elapsed_seconds=total_elapsed,
        results=tuple(results),
        metadata=meta_dict,
    )


# ==============================================================================
# Standard Baseline Benchmark Suite Builder
# ==============================================================================

def build_baseline_benchmark_suite(
    session_id: str = "sess_bench_baseline",
    configuration_hash: str = "hash_bench_canon_sha256",
) -> tuple[BenchmarkScenario, ...]:
    """Construct a standardized baseline benchmark suite covering all operational categories.

    Covers:
        1. BASELINE_EVALUATION: Operational latency of clean honest scenario.
        2. SUSPICIOUS_EVALUATION: Operational latency of channel anomaly scenario.
        3. ATTACK_EVALUATION: Operational latency of explicit impersonation violation scenario.
        4. EVIDENCE_FUSION: Multi-source evidence fusion latency.
        5. SCENARIO_SCALING (N=1): Unit scenario scaling baseline.
        6. SCENARIO_SCALING (N=10): Workload size 10 scenario batch.
        7. SCENARIO_SCALING (N=50): Workload size 50 scenario batch.
        8. SCENARIO_SCALING (N=100): Workload size 100 scenario batch.
        9. END_TO_END_PIPELINE: Complete 16-scenario baseline evaluation suite execution.

    Args:
        session_id: Context session identifier.
        configuration_hash: Context configuration hash.

    Returns:
        Sorted tuple of BenchmarkScenario specifications.
    """
    benchmarks: list[BenchmarkScenario] = []

    # Clean scenario fixture
    m13_clean = make_clean_impersonation_evidence(session_id=session_id, configuration_hash=configuration_hash)
    m14_clean = make_clean_authorization_evidence(session_id=session_id, configuration_hash=configuration_hash)
    m15_clean = make_clean_channel_evidence(session_id=session_id, configuration_hash=configuration_hash)
    sc_clean = EvaluationScenario(
        scenario_id="SCEN_BENCH_CLEAN",
        name="Clean Scenario",
        description="Clean honest evaluation",
        category=EvaluationCategory.CLEAN_HONEST,
        expected_verdict=DecisionVerdict.ACCEPT,
        impersonation_evidence=m13_clean,
        authorization_evidence=m14_clean,
        channel_evidence=m15_clean,
        expected_session_id=session_id,
        expected_configuration_hash=configuration_hash,
    )

    # Suspicious anomaly scenario fixture
    m15_anom = make_anomalous_channel_evidence(session_id=session_id, configuration_hash=configuration_hash)
    sc_suspicious = EvaluationScenario(
        scenario_id="SCEN_BENCH_SUSPICIOUS",
        name="Suspicious Scenario",
        description="Quantum channel anomaly evaluation",
        category=EvaluationCategory.QUANTUM_CHANNEL_ANOMALY,
        expected_verdict=DecisionVerdict.SUSPICIOUS,
        impersonation_evidence=m13_clean,
        authorization_evidence=m14_clean,
        channel_evidence=m15_anom,
        expected_session_id=session_id,
        expected_configuration_hash=configuration_hash,
    )

    # Attack violation scenario fixture
    m13_viol = make_violating_impersonation_evidence(session_id=session_id, configuration_hash=configuration_hash)
    sc_attack = EvaluationScenario(
        scenario_id="SCEN_BENCH_ATTACK",
        name="Attack Scenario",
        description="Confirmed impersonation violation evaluation",
        category=EvaluationCategory.IMPERSONATION,
        expected_verdict=DecisionVerdict.ATTACK,
        expected_is_violation=True,
        expected_violation_types=("AUTHENTICATED_IDENTITY_MISMATCH",),
        impersonation_evidence=m13_viol,
        authorization_evidence=m14_clean,
        channel_evidence=m15_clean,
        expected_session_id=session_id,
        expected_configuration_hash=configuration_hash,
    )

    # Complete 16-scenario evaluation suite
    eval_suite = build_baseline_evaluation_suite(session_id=session_id, configuration_hash=configuration_hash)

    # 1. Baseline Clean Benchmark
    benchmarks.append(
        BenchmarkScenario(
            benchmark_id="BENCH_01_BASELINE_CLEAN",
            name="Baseline Clean Scenario Latency",
            description="Measures operational latency of clean honest scenario evaluation",
            category=BenchmarkCategory.BASELINE_EVALUATION,
            scenario=sc_clean,
            workload_size=1,
            iterations=10,
            warmup_iterations=2,
            session_id=session_id,
            configuration_hash=configuration_hash,
        )
    )

    # 2. Suspicious Anomaly Benchmark
    benchmarks.append(
        BenchmarkScenario(
            benchmark_id="BENCH_02_SUSPICIOUS_ANOMALY",
            name="Suspicious Channel Anomaly Latency",
            description="Measures operational latency of quantum channel anomaly evaluation",
            category=BenchmarkCategory.SUSPICIOUS_EVALUATION,
            scenario=sc_suspicious,
            workload_size=1,
            iterations=10,
            warmup_iterations=2,
            session_id=session_id,
            configuration_hash=configuration_hash,
        )
    )

    # 3. Attack Violation Benchmark
    benchmarks.append(
        BenchmarkScenario(
            benchmark_id="BENCH_03_ATTACK_IMPERSONATION",
            name="Attack Security Violation Latency",
            description="Measures operational latency of confirmed impersonation breach evaluation",
            category=BenchmarkCategory.ATTACK_EVALUATION,
            scenario=sc_attack,
            workload_size=1,
            iterations=10,
            warmup_iterations=2,
            session_id=session_id,
            configuration_hash=configuration_hash,
        )
    )

    # 4. Evidence Fusion Benchmark
    benchmarks.append(
        BenchmarkScenario(
            benchmark_id="BENCH_04_EVIDENCE_FUSION",
            name="Tri-Source Evidence Fusion Latency",
            description="Measures operational latency of M16 multi-source evidence fusion",
            category=BenchmarkCategory.EVIDENCE_FUSION,
            workload_size=1,
            iterations=10,
            warmup_iterations=2,
            session_id=session_id,
            configuration_hash=configuration_hash,
        )
    )

    # 5. Workload Scaling: N=1
    benchmarks.append(
        BenchmarkScenario(
            benchmark_id="BENCH_05_SCALING_N1",
            name="Workload Scaling (N=1)",
            description="Scenario workload scaling at N=1 scenario",
            category=BenchmarkCategory.SCENARIO_SCALING,
            scenario=sc_clean,
            workload_size=1,
            iterations=5,
            warmup_iterations=1,
            session_id=session_id,
            configuration_hash=configuration_hash,
        )
    )

    # 6. Workload Scaling: N=10
    benchmarks.append(
        BenchmarkScenario(
            benchmark_id="BENCH_06_SCALING_N10",
            name="Workload Scaling (N=10)",
            description="Scenario workload scaling at N=10 scenarios",
            category=BenchmarkCategory.SCENARIO_SCALING,
            scenario=sc_clean,
            workload_size=10,
            iterations=5,
            warmup_iterations=1,
            session_id=session_id,
            configuration_hash=configuration_hash,
        )
    )

    # 7. Workload Scaling: N=50
    benchmarks.append(
        BenchmarkScenario(
            benchmark_id="BENCH_07_SCALING_N50",
            name="Workload Scaling (N=50)",
            description="Scenario workload scaling at N=50 scenarios",
            category=BenchmarkCategory.SCENARIO_SCALING,
            scenario=sc_clean,
            workload_size=50,
            iterations=5,
            warmup_iterations=1,
            session_id=session_id,
            configuration_hash=configuration_hash,
        )
    )

    # 8. Workload Scaling: N=100
    benchmarks.append(
        BenchmarkScenario(
            benchmark_id="BENCH_08_SCALING_N100",
            name="Workload Scaling (N=100)",
            description="Scenario workload scaling at N=100 scenarios",
            category=BenchmarkCategory.SCENARIO_SCALING,
            scenario=sc_clean,
            workload_size=100,
            iterations=5,
            warmup_iterations=1,
            session_id=session_id,
            configuration_hash=configuration_hash,
        )
    )

    # 9. End-to-End Evaluation Pipeline Benchmark
    benchmarks.append(
        BenchmarkScenario(
            benchmark_id="BENCH_09_END_TO_END_PIPELINE",
            name="End-to-End Suite Pipeline Latency",
            description="Measures execution latency of the complete 16-scenario baseline evaluation suite",
            category=BenchmarkCategory.END_TO_END_PIPELINE,
            scenario_suite=eval_suite,
            workload_size=len(eval_suite),
            iterations=5,
            warmup_iterations=1,
            session_id=session_id,
            configuration_hash=configuration_hash,
        )
    )

    benchmarks.sort(key=lambda b: b.benchmark_id)
    return tuple(benchmarks)

"""Q-SHIELD — Performance and Operational Benchmarking Package (Milestone M18).

Provides deterministic, reproducible benchmarking capabilities that measure the
performance and operational characteristics (latency, throughput, workload scaling)
of the already-completed Q-SHIELD detection and evaluation pipeline.
"""

from __future__ import annotations

from src.benchmarking.benchmark import (
    BenchmarkCategory,
    BenchmarkResult,
    BenchmarkScenario,
    BenchmarkSuiteResult,
    build_baseline_benchmark_suite,
    run_benchmark,
    run_benchmark_suite,
)

__all__ = [
    "BenchmarkCategory",
    "BenchmarkScenario",
    "BenchmarkResult",
    "BenchmarkSuiteResult",
    "build_baseline_benchmark_suite",
    "run_benchmark",
    "run_benchmark_suite",
]

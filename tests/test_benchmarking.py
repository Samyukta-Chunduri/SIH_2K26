"""Q-SHIELD — Comprehensive Test Suite for Milestone M18 (Performance Benchmarking).

Validates:
1. Construction validation, input integrity, and typing.
2. Immutability guarantees (FrozenInstanceError, defensive copies).
3. Secret leakage guards (forbid raw keys, credentials, secrets in metadata).
4. Timing methodology (high-res monotonic timer, process CPU time, warmup exclusion).
5. Zero-denominator safety and empty data rules (iterations=0 produces None metrics).
6. Operational benchmark execution across all categories (Baseline, Suspicious, Attack, Fusion, Scaling, End-to-End).
7. Determinism: deterministic inputs and calculation from identical sample data.
8. Observational verdict recording vs. strict prohibition of security/risk scores.
9. Security boundary preservation (M12 authority unchanged, no duplicated detection).
10. Suite execution, aggregation, and stable identifier retrieval.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import Any
import pytest

from src.benchmarking.benchmark import (
    BenchmarkCategory,
    BenchmarkResult,
    BenchmarkScenario,
    BenchmarkSuiteResult,
    build_baseline_benchmark_suite,
    run_benchmark,
    run_benchmark_suite,
)
from src.detection.decision import DecisionVerdict
from src.evaluation.security_evaluation import (
    EvaluationCategory,
    EvaluationScenario,
    build_baseline_evaluation_suite,
    make_anomalous_channel_evidence,
    make_clean_authorization_evidence,
    make_clean_channel_evidence,
    make_clean_impersonation_evidence,
    make_violating_impersonation_evidence,
)


def _make_clean_test_scenario() -> EvaluationScenario:
    """Helper to construct a standardized clean evaluation scenario."""
    return EvaluationScenario(
        scenario_id="SCEN_TEST_CLEAN",
        name="Clean Test Scenario",
        description="Clean scenario for benchmarking tests",
        category=EvaluationCategory.CLEAN_HONEST,
        expected_verdict=DecisionVerdict.ACCEPT,
        impersonation_evidence=make_clean_impersonation_evidence(),
        authorization_evidence=make_clean_authorization_evidence(),
        channel_evidence=make_clean_channel_evidence(),
    )


# ==============================================================================
# 1. Construction & Validation Tests
# ==============================================================================

class TestBenchmarkScenarioConstruction:
    """Validates constructor constraints, typing, and validation on BenchmarkScenario."""

    def test_valid_scenario_minimal(self) -> None:
        """BenchmarkScenario instantiates with valid required fields."""
        sc = _make_clean_test_scenario()
        scenario = BenchmarkScenario(
            benchmark_id="BM-TEST-001",
            name="Minimal Benchmark",
            description="Minimal valid benchmark scenario",
            category=BenchmarkCategory.BASELINE_EVALUATION,
            scenario=sc,
            iterations=5,
            warmup_iterations=2,
        )
        assert scenario.benchmark_id == "BM-TEST-001"
        assert scenario.name == "Minimal Benchmark"
        assert scenario.description == "Minimal valid benchmark scenario"
        assert scenario.category == BenchmarkCategory.BASELINE_EVALUATION
        assert scenario.iterations == 5
        assert scenario.warmup_iterations == 2
        assert scenario.workload_size == 1
        assert isinstance(scenario.metadata, dict)

    @pytest.mark.parametrize(
        "invalid_id",
        [
            "",
            "   ",
            "\t\n",
            None,
            123,
            ["invalid"],
        ],
    )
    def test_invalid_benchmark_id_rejected(self, invalid_id: Any) -> None:
        """Reject empty, whitespace, non-string benchmark IDs."""
        with pytest.raises((ValueError, TypeError)):
            BenchmarkScenario(
                benchmark_id=invalid_id,
                name="Valid Name",
                description="Valid description",
                category=BenchmarkCategory.BASELINE_EVALUATION,
                iterations=5,
            )

    @pytest.mark.parametrize(
        "invalid_name",
        [
            "",
            "   ",
            "\n\t",
            None,
            456,
        ],
    )
    def test_invalid_name_rejected(self, invalid_name: Any) -> None:
        """Reject empty, whitespace, non-string names."""
        with pytest.raises((ValueError, TypeError)):
            BenchmarkScenario(
                benchmark_id="BM-001",
                name=invalid_name,
                description="Valid description",
                category=BenchmarkCategory.BASELINE_EVALUATION,
                iterations=5,
            )

    @pytest.mark.parametrize(
        "invalid_desc",
        [
            "",
            "   ",
            "\n\t",
            None,
            456,
        ],
    )
    def test_invalid_description_rejected(self, invalid_desc: Any) -> None:
        """Reject empty, whitespace, non-string descriptions."""
        with pytest.raises((ValueError, TypeError)):
            BenchmarkScenario(
                benchmark_id="BM-001",
                name="Valid Name",
                description=invalid_desc,
                category=BenchmarkCategory.BASELINE_EVALUATION,
                iterations=5,
            )

    @pytest.mark.parametrize(
        "invalid_cat",
        [
            "NOT_A_CATEGORY",
            123,
            None,
        ],
    )
    def test_invalid_category_rejected(self, invalid_cat: Any) -> None:
        """Reject invalid category values."""
        with pytest.raises((ValueError, TypeError)):
            BenchmarkScenario(
                benchmark_id="BM-001",
                name="Valid Name",
                description="Valid description",
                category=invalid_cat,
                iterations=5,
            )

    @pytest.mark.parametrize(
        "invalid_iterations",
        [
            -1,
            -10,
            3.14,
            "10",
            None,
        ],
    )
    def test_invalid_iterations_rejected(self, invalid_iterations: Any) -> None:
        """Reject negative, float, non-integer iteration counts."""
        with pytest.raises((ValueError, TypeError)):
            BenchmarkScenario(
                benchmark_id="BM-001",
                name="Valid Name",
                description="Valid description",
                category=BenchmarkCategory.BASELINE_EVALUATION,
                iterations=invalid_iterations,
            )

    @pytest.mark.parametrize(
        "invalid_warmup",
        [
            -1,
            -5,
            2.5,
            "2",
            None,
        ],
    )
    def test_invalid_warmup_rejected(self, invalid_warmup: Any) -> None:
        """Reject negative, float, non-integer warmup counts."""
        with pytest.raises((ValueError, TypeError)):
            BenchmarkScenario(
                benchmark_id="BM-001",
                name="Valid Name",
                description="Valid description",
                category=BenchmarkCategory.BASELINE_EVALUATION,
                iterations=5,
                warmup_iterations=invalid_warmup,
            )

    @pytest.mark.parametrize(
        "invalid_workload_size",
        [
            0,
            -1,
            -10,
            1.5,
            "10",
            None,
        ],
    )
    def test_invalid_workload_size_rejected(self, invalid_workload_size: Any) -> None:
        """Reject workload_size < 1, float, or non-integer values."""
        with pytest.raises((ValueError, TypeError)):
            BenchmarkScenario(
                benchmark_id="BM-001",
                name="Valid Name",
                description="Valid description",
                category=BenchmarkCategory.SCENARIO_SCALING,
                iterations=5,
                workload_size=invalid_workload_size,
            )

    def test_invalid_scenario_type_rejected(self) -> None:
        """Non-EvaluationScenario scenario raises TypeError."""
        with pytest.raises(TypeError):
            BenchmarkScenario(
                benchmark_id="BM-001",
                name="Valid Name",
                description="Valid description",
                category=BenchmarkCategory.BASELINE_EVALUATION,
                scenario="not_a_scenario",  # type: ignore[arg-type]
                iterations=5,
            )

    def test_invalid_scenario_suite_items_rejected(self) -> None:
        """Items in scenario_suite that are not EvaluationScenario raise TypeError."""
        with pytest.raises(TypeError):
            BenchmarkScenario(
                benchmark_id="BM-001",
                name="Valid Name",
                description="Valid description",
                category=BenchmarkCategory.END_TO_END_PIPELINE,
                scenario_suite=("invalid_item",),  # type: ignore[arg-type]
                iterations=5,
            )


# ==============================================================================
# 2. Immutability & Secret Guard Tests
# ==============================================================================

class TestImmutabilityAndSecretGuard:
    """Verifies that benchmark structures are deeply immutable and protected against secret leakage."""

    def test_benchmark_scenario_immutable(self) -> None:
        """BenchmarkScenario fields cannot be modified after instantiation."""
        sc = _make_clean_test_scenario()
        scenario = BenchmarkScenario(
            benchmark_id="BM-IMMUTABLE-001",
            name="Immutable Benchmark",
            description="Immutable test scenario",
            category=BenchmarkCategory.BASELINE_EVALUATION,
            scenario=sc,
            iterations=5,
        )
        with pytest.raises(FrozenInstanceError):
            scenario.iterations = 10  # type: ignore[misc]

        with pytest.raises(FrozenInstanceError):
            scenario.benchmark_id = "NEW-ID"  # type: ignore[misc]

    def test_scenario_metadata_defensively_copied(self) -> None:
        """Mutating the source metadata dict does not mutate the benchmark scenario's metadata."""
        meta = {"env": "test_lab", "tags": ["baseline", "perf"]}
        sc = _make_clean_test_scenario()
        scenario = BenchmarkScenario(
            benchmark_id="BM-DEFENSE-001",
            name="Defensive Benchmark",
            description="Defensive metadata test",
            category=BenchmarkCategory.BASELINE_EVALUATION,
            scenario=sc,
            iterations=5,
            metadata=meta,
        )
        # Mutate external source dictionary
        meta["env"] = "corrupted"
        meta["tags"].append("mutated")  # type: ignore[attr-defined]

        assert scenario.metadata["env"] == "test_lab"
        assert scenario.metadata["tags"] == ("baseline", "perf")

    @pytest.mark.parametrize(
        "secret_key",
        [
            "password",
            "db_secret",
            "private_key",
            "raw_key",
            "token_secret",
            "credential_raw",
            "api_key_secret",
        ],
    )
    def test_secret_leakage_guard_rejects_credentials(self, secret_key: str) -> None:
        """Metadata containing secret keywords raises ValueError."""
        sc = _make_clean_test_scenario()
        with pytest.raises(ValueError, match="Sensitive secret keyword"):
            BenchmarkScenario(
                benchmark_id="BM-SECRET-TEST",
                name="Leaky Benchmark",
                description="Leaky scenario",
                category=BenchmarkCategory.BASELINE_EVALUATION,
                scenario=sc,
                iterations=5,
                metadata={secret_key: "super_secret_value_123"},
            )

    def test_benchmark_result_immutable(self) -> None:
        """BenchmarkResult fields cannot be modified after construction."""
        res = BenchmarkResult(
            benchmark_id="BM-RES-001",
            benchmark_name="Result Test",
            category=BenchmarkCategory.BASELINE_EVALUATION,
            workload_size=1,
            target_iterations=5,
            warmup_iterations=2,
            executed_iterations=5,
            successful_iterations=5,
            failed_iterations=0,
            total_elapsed_seconds=0.05,
            cpu_time_seconds=0.04,
            mean_latency_seconds=0.01,
            min_latency_seconds=0.008,
            max_latency_seconds=0.012,
            median_latency_seconds=0.01,
            p95_latency_seconds=0.012,
            throughput_ops_per_sec=100.0,
            raw_latencies=(0.01, 0.008, 0.012, 0.01, 0.01),
        )
        with pytest.raises(FrozenInstanceError):
            res.mean_latency_seconds = 0.02  # type: ignore[misc]

        with pytest.raises(FrozenInstanceError):
            res.throughput_ops_per_sec = 200.0  # type: ignore[misc]


# ==============================================================================
# 3. Timing Methodology & Zero-Denominator Safety Tests
# ==============================================================================

class TestTimingAndZeroDenominator:
    """Verifies monotonic timing, warmup exclusion, and zero-denominator handling."""

    def test_zero_iterations_produces_none_metrics(self) -> None:
        """When configured iterations is 0, metric values must be None, not 0 or fabricated numbers."""
        sc = _make_clean_test_scenario()
        scenario = BenchmarkScenario(
            benchmark_id="BM-ZERO-001",
            name="Zero Iterations Benchmark",
            description="Zero iterations test",
            category=BenchmarkCategory.BASELINE_EVALUATION,
            scenario=sc,
            iterations=0,
            warmup_iterations=1,
        )
        result = run_benchmark(scenario)

        assert result.target_iterations == 0
        assert result.executed_iterations == 0
        assert result.successful_iterations == 0
        assert result.failed_iterations == 0
        assert result.mean_latency_seconds is None
        assert result.min_latency_seconds is None
        assert result.max_latency_seconds is None
        assert result.median_latency_seconds is None
        assert result.p95_latency_seconds is None
        assert result.throughput_ops_per_sec is None
        assert result.raw_latencies == ()
        assert result.total_elapsed_seconds >= 0.0

    def test_single_iteration_computes_consistent_quantiles(self) -> None:
        """When exactly 1 iteration is executed, min == max == mean == median == p95."""
        sc = _make_clean_test_scenario()
        scenario = BenchmarkScenario(
            benchmark_id="BM-SINGLE-001",
            name="Single Iteration Benchmark",
            description="Single iteration test",
            category=BenchmarkCategory.BASELINE_EVALUATION,
            scenario=sc,
            iterations=1,
            warmup_iterations=1,
        )
        result = run_benchmark(scenario)

        assert result.target_iterations == 1
        assert result.successful_iterations == 1
        assert result.failed_iterations == 0
        assert len(result.raw_latencies) == 1
        val = result.raw_latencies[0]
        assert result.min_latency_seconds == val
        assert result.max_latency_seconds == val
        assert result.mean_latency_seconds == val
        assert result.median_latency_seconds == val
        assert result.p95_latency_seconds == val
        assert result.throughput_ops_per_sec is not None
        assert result.throughput_ops_per_sec > 0.0

    def test_warmup_iterations_strictly_excluded_from_measured_metrics(self) -> None:
        """Warmup iterations execute without being included in raw_latencies or successful_iterations."""
        sc = _make_clean_test_scenario()
        scenario = BenchmarkScenario(
            benchmark_id="BM-WARMUP-001",
            name="Warmup Benchmark",
            description="Warmup isolation test",
            category=BenchmarkCategory.BASELINE_EVALUATION,
            scenario=sc,
            iterations=3,
            warmup_iterations=5,  # warmup > iterations
        )
        result = run_benchmark(scenario)

        assert result.warmup_iterations == 5
        assert result.target_iterations == 3
        assert result.successful_iterations == 3
        # raw_latencies length MUST equal configured iterations, NOT warmup + iterations
        assert len(result.raw_latencies) == 3

    def test_aggregates_calculated_correctly_from_samples(self) -> None:
        """Min <= Median <= Mean (or variation) <= Max and p95 within bounds."""
        sc = _make_clean_test_scenario()
        scenario = BenchmarkScenario(
            benchmark_id="BM-MULTI-001",
            name="Multi-Iteration Benchmark",
            description="Multi-iteration aggregate verification",
            category=BenchmarkCategory.BASELINE_EVALUATION,
            scenario=sc,
            iterations=10,
            warmup_iterations=2,
        )
        result = run_benchmark(scenario)

        assert result.successful_iterations == 10
        assert result.min_latency_seconds is not None
        assert result.max_latency_seconds is not None
        assert result.mean_latency_seconds is not None
        assert result.median_latency_seconds is not None
        assert result.p95_latency_seconds is not None
        assert result.throughput_ops_per_sec is not None

        assert result.min_latency_seconds <= result.max_latency_seconds
        assert result.min_latency_seconds <= result.mean_latency_seconds <= result.max_latency_seconds
        assert result.min_latency_seconds <= result.median_latency_seconds <= result.max_latency_seconds
        assert result.min_latency_seconds <= result.p95_latency_seconds <= result.max_latency_seconds
        assert result.throughput_ops_per_sec > 0.0


# ==============================================================================
# 4. Operational Benchmark Categories
# ==============================================================================

class TestOperationalCategories:
    """Executes benchmarks across all operational categories to verify pipeline execution."""

    def test_baseline_evaluation_category(self) -> None:
        """Category A: Baseline honest scenario execution."""
        clean_scenario = _make_clean_test_scenario()
        bm = BenchmarkScenario(
            benchmark_id="BM-CAT-A",
            name="Baseline Benchmark",
            description="Baseline evaluation benchmark",
            category=BenchmarkCategory.BASELINE_EVALUATION,
            scenario=clean_scenario,
            iterations=4,
            warmup_iterations=1,
        )
        res = run_benchmark(bm)
        assert res.category == BenchmarkCategory.BASELINE_EVALUATION
        assert res.successful_iterations == 4
        assert res.observed_verdict_counts.get("ACCEPT") == 4
        assert res.observed_verdict_counts.get("ATTACK", 0) == 0

    def test_suspicious_evaluation_category(self) -> None:
        """Category B: Suspicious scenario execution (e.g. anomalous channel evidence)."""
        eval_suite = build_baseline_evaluation_suite()
        # Find a suspicious scenario from baseline suite
        suspicious_scenario = next(
            s for s in eval_suite if s.category == EvaluationCategory.QUANTUM_CHANNEL_ANOMALY
        )
        bm = BenchmarkScenario(
            benchmark_id="BM-CAT-B",
            name="Suspicious Benchmark",
            description="Suspicious evaluation benchmark",
            category=BenchmarkCategory.SUSPICIOUS_EVALUATION,
            scenario=suspicious_scenario,
            iterations=4,
            warmup_iterations=1,
        )
        res = run_benchmark(bm)
        assert res.category == BenchmarkCategory.SUSPICIOUS_EVALUATION
        assert res.successful_iterations == 4
        assert res.observed_verdict_counts.get("SUSPICIOUS") == 4

    def test_attack_evaluation_category(self) -> None:
        """Category C: Explicit attack scenario execution (e.g. impersonation violation)."""
        attack_scenario = EvaluationScenario(
            scenario_id="SC-ATTACK-01",
            name="Attack Impersonation",
            description="Attack Scenario",
            category=EvaluationCategory.IMPERSONATION,
            impersonation_evidence=make_violating_impersonation_evidence(),
            authorization_evidence=make_clean_authorization_evidence(),
            channel_evidence=make_clean_channel_evidence(),
            expected_verdict=DecisionVerdict.ATTACK,
        )
        bm = BenchmarkScenario(
            benchmark_id="BM-CAT-C",
            name="Attack Benchmark",
            description="Attack evaluation benchmark",
            category=BenchmarkCategory.ATTACK_EVALUATION,
            scenario=attack_scenario,
            iterations=4,
            warmup_iterations=1,
        )
        res = run_benchmark(bm)
        assert res.category == BenchmarkCategory.ATTACK_EVALUATION
        assert res.successful_iterations == 4
        assert res.observed_verdict_counts.get("ATTACK") == 4

    def test_evidence_fusion_category(self) -> None:
        """Category D: Direct evidence fusion workload benchmark."""
        bm = BenchmarkScenario(
            benchmark_id="BM-CAT-D",
            name="Fusion Benchmark",
            description="Evidence fusion benchmark with 3 sources",
            category=BenchmarkCategory.EVIDENCE_FUSION,
            iterations=5,
            warmup_iterations=2,
        )
        res = run_benchmark(bm)
        assert res.category == BenchmarkCategory.EVIDENCE_FUSION
        assert res.successful_iterations == 5
        assert res.mean_latency_seconds is not None

    def test_scenario_scaling_category(self) -> None:
        """Category E: Scaling workload sizes (N=1, 10, 50)."""
        clean_scenario = _make_clean_test_scenario()

        results = []
        for n in (1, 10, 50):
            bm = BenchmarkScenario(
                benchmark_id=f"BM-SCALE-N{n}",
                name=f"Scale N={n}",
                description=f"Scaling with N={n}",
                category=BenchmarkCategory.SCENARIO_SCALING,
                scenario=clean_scenario,
                workload_size=n,
                iterations=2,
                warmup_iterations=1,
            )
            res = run_benchmark(bm)
            assert res.successful_iterations == 2
            assert res.workload_size == n
            assert res.observed_verdict_counts.get("ACCEPT") == 2 * n
            results.append(res)

        assert len(results) == 3
        # Verify elapsed time and workload sizes are recorded accurately
        assert results[0].workload_size == 1
        assert results[1].workload_size == 10
        assert results[2].workload_size == 50

    def test_end_to_end_pipeline_category(self) -> None:
        """Category F: Full evaluation suite execution."""
        eval_suite = build_baseline_evaluation_suite()
        bm = BenchmarkScenario(
            benchmark_id="BM-CAT-F",
            name="Suite Benchmark",
            description="End-to-end evaluation suite benchmark",
            category=BenchmarkCategory.END_TO_END_PIPELINE,
            scenario_suite=tuple(eval_suite),
            iterations=2,
            warmup_iterations=1,
        )
        res = run_benchmark(bm)
        assert res.category == BenchmarkCategory.END_TO_END_PIPELINE
        assert res.successful_iterations == 2
        assert res.workload_size == 1
        # Sum of observed verdicts across the 2 iterations must equal 2 * len(eval_suite)
        total_verdicts = sum(res.observed_verdict_counts.values())
        assert total_verdicts == 2 * len(eval_suite)


# ==============================================================================
# 5. Determinism, Ordering & Result Lookup Tests
# ==============================================================================

class TestDeterminismAndAggregation:
    """Verifies that results can be retrieved by stable ID and calculations are deterministic."""

    def test_identical_specifications_produce_identical_workload_semantics(self) -> None:
        """Identical scenario definitions have identical configuration hashes and IDs."""
        clean_scenario = _make_clean_test_scenario()
        bm1 = BenchmarkScenario(
            benchmark_id="BM-DET-001",
            name="Deterministic Benchmark",
            description="Deterministic test",
            category=BenchmarkCategory.BASELINE_EVALUATION,
            scenario=clean_scenario,
            iterations=3,
        )
        bm2 = BenchmarkScenario(
            benchmark_id="BM-DET-001",
            name="Deterministic Benchmark",
            description="Deterministic test",
            category=BenchmarkCategory.BASELINE_EVALUATION,
            scenario=clean_scenario,
            iterations=3,
        )
        assert bm1.benchmark_id == bm2.benchmark_id
        assert bm1.name == bm2.name
        assert bm1.category == bm2.category
        assert bm1.iterations == bm2.iterations

    def test_run_benchmark_suite_aggregates_and_permits_id_lookup(self) -> None:
        """BenchmarkSuiteResult permits lookup by stable ID regardless of list position."""
        clean_scenario = _make_clean_test_scenario()
        bm1 = BenchmarkScenario(
            benchmark_id="BM-ID-A",
            name="Benchmark A",
            description="Benchmark A description",
            category=BenchmarkCategory.BASELINE_EVALUATION,
            scenario=clean_scenario,
            iterations=2,
        )
        bm2 = BenchmarkScenario(
            benchmark_id="BM-ID-B",
            name="Benchmark B",
            description="Benchmark B description",
            category=BenchmarkCategory.BASELINE_EVALUATION,
            scenario=clean_scenario,
            iterations=2,
        )

        suite_res = run_benchmark_suite([bm1, bm2], suite_id="SUITE-TEST-01")

        assert suite_res.total_benchmarks == 2
        assert suite_res.successful_benchmarks == 2
        assert suite_res.failed_benchmarks == 0

        # Stable ID lookup
        res_a = suite_res.get_result("BM-ID-A")
        assert res_a is not None
        assert res_a.benchmark_id == "BM-ID-A"

        res_b = suite_res.get_result("BM-ID-B")
        assert res_b is not None
        assert res_b.benchmark_id == "BM-ID-B"

        assert suite_res.get_result("NON_EXISTENT") is None

        # Verify results_by_id property
        assert "BM-ID-A" in suite_res.results_by_id
        assert "BM-ID-B" in suite_res.results_by_id

    def test_suite_rejects_duplicate_benchmark_ids(self) -> None:
        """run_benchmark_suite rejects suites with duplicate benchmark IDs."""
        clean_scenario = _make_clean_test_scenario()
        bm1 = BenchmarkScenario(
            benchmark_id="BM-DUPLICATE",
            name="Benchmark 1",
            description="Benchmark 1",
            category=BenchmarkCategory.BASELINE_EVALUATION,
            scenario=clean_scenario,
            iterations=1,
        )
        bm2 = BenchmarkScenario(
            benchmark_id="BM-DUPLICATE",
            name="Benchmark 2",
            description="Benchmark 2 with same ID",
            category=BenchmarkCategory.BASELINE_EVALUATION,
            scenario=clean_scenario,
            iterations=1,
        )
        with pytest.raises(ValueError, match="Duplicate benchmark_id"):
            run_benchmark_suite([bm1, bm2])


# ==============================================================================
# 6. Baseline Benchmark Suite Factory
# ==============================================================================

class TestBaselineBenchmarkSuite:
    """Verifies that build_baseline_benchmark_suite constructs the complete standardized benchmark suite."""

    def test_baseline_benchmark_suite_structure(self) -> None:
        """Standardized suite contains 9 benchmarks covering categories A through F."""
        suite = build_baseline_benchmark_suite()
        assert len(suite) == 9

        categories = {b.category for b in suite}
        assert BenchmarkCategory.BASELINE_EVALUATION in categories
        assert BenchmarkCategory.SUSPICIOUS_EVALUATION in categories
        assert BenchmarkCategory.ATTACK_EVALUATION in categories
        assert BenchmarkCategory.EVIDENCE_FUSION in categories
        assert BenchmarkCategory.SCENARIO_SCALING in categories
        assert BenchmarkCategory.END_TO_END_PIPELINE in categories

        # Check unique IDs
        ids = [b.benchmark_id for b in suite]
        assert len(ids) == len(set(ids))

    def test_run_baseline_benchmark_suite_smoke(self) -> None:
        """Smoke test running the full standardized baseline benchmark suite."""
        suite = build_baseline_benchmark_suite()
        suite_res = run_benchmark_suite(suite, suite_id="BASELINE-BENCHMARK-RUN")

        assert suite_res.total_benchmarks == 9
        assert suite_res.successful_benchmarks == 9
        assert suite_res.failed_benchmarks == 0
        assert suite_res.total_elapsed_seconds > 0.0

        # Verify all 9 benchmarks are retrievable by ID
        for bm in suite:
            res = suite_res.get_result(bm.benchmark_id)
            assert res is not None
            assert res.successful_iterations == bm.iterations
            assert res.throughput_ops_per_sec is not None
            assert res.throughput_ops_per_sec > 0.0


# ==============================================================================
# 7. Strict Prohibition of Scoring & Security Boundaries
# ==============================================================================

class TestSecurityBoundariesAndScoringProhibition:
    """Verifies that M18 adheres to architectural boundaries: no scoring, M12 unaltered."""

    def test_no_security_scores_on_benchmark_result(self) -> None:
        """BenchmarkResult must NOT have risk/trust/security scoring fields."""
        prohibited_attributes = [
            "security_score",
            "risk_score",
            "trust_score",
            "threat_score",
            "confidence_score",
            "overall_security_percentage",
            "attack_probability",
            "system_trust_level",
        ]
        clean_scenario = _make_clean_test_scenario()
        bm = BenchmarkScenario(
            benchmark_id="BM-SCORE-CHECK",
            name="Score Check",
            description="Score prohibition check",
            category=BenchmarkCategory.BASELINE_EVALUATION,
            scenario=clean_scenario,
            iterations=1,
        )
        res = run_benchmark(bm)

        for attr in prohibited_attributes:
            assert not hasattr(res, attr), f"BenchmarkResult illegally exposes '{attr}'"

    def test_no_security_scores_on_suite_result(self) -> None:
        """BenchmarkSuiteResult must NOT have aggregate risk/trust/security scoring fields."""
        prohibited_attributes = [
            "security_score",
            "risk_score",
            "trust_score",
            "threat_score",
            "confidence_score",
            "overall_security_percentage",
            "attack_probability",
        ]
        clean_scenario = _make_clean_test_scenario()
        bm = BenchmarkScenario(
            benchmark_id="BM-SCORE-CHECK-2",
            name="Score Check 2",
            description="Score prohibition check 2",
            category=BenchmarkCategory.BASELINE_EVALUATION,
            scenario=clean_scenario,
            iterations=1,
        )
        suite_res = run_benchmark_suite([bm])

        for attr in prohibited_attributes:
            assert not hasattr(suite_res, attr), f"BenchmarkSuiteResult illegally exposes '{attr}'"

    def test_m12_decision_semantics_preserved_and_unaltered(self) -> None:
        """Running benchmarks does NOT alter M12 decision engine behavior or verdict distributions."""
        attack_scenario = EvaluationScenario(
            scenario_id="SC-VERDICT-CHECK",
            name="Attack Check",
            description="Attack scenario for verdict check",
            category=EvaluationCategory.IMPERSONATION,
            impersonation_evidence=make_violating_impersonation_evidence(),
            authorization_evidence=make_clean_authorization_evidence(),
            channel_evidence=make_clean_channel_evidence(),
            expected_verdict=DecisionVerdict.ATTACK,
        )
        bm = BenchmarkScenario(
            benchmark_id="BM-VERDICT-PRESERVED",
            name="Verdict Preserved",
            description="Verdict verification",
            category=BenchmarkCategory.ATTACK_EVALUATION,
            scenario=attack_scenario,
            iterations=5,
        )
        res = run_benchmark(bm)

        # Observed verdicts MUST reflect M12 ATTACK without reinterpretation
        assert res.observed_verdict_counts["ATTACK"] == 5
        assert res.observed_verdict_counts.get("ACCEPT", 0) == 0
        assert res.observed_verdict_counts.get("SUSPICIOUS", 0) == 0

"""Q-SHIELD — Deterministic Security Evaluation Layer (Milestone M17).

Evaluates the security behavior, correctness, and adherence to established
decision policy of the already-implemented Q-SHIELD detection pipeline under
controlled, deterministic evaluation scenarios.

Architectural Placement:
    Quantum Protocol / Simulation
                  ↓
    M8/M9 Baseline & Calibration
                  ↓
    M10 Statistical Comparison
                  ↓
    M11 Threshold Policy
                  ↓
    M12 Final Decision Engine (evaluate_security_decision)
                  ↓
    M13 Impersonation Evidence
    M14 Authorization Evidence
    M15 Quantum Channel Evidence
                  ↓
    M16 Deterministic Evidence Fusion (FusedSecurityEvidence)
                  ↓
    M17 Security Evaluation (THIS MODULE)

Core Architectural & Scientific Invariants:
    1. Evaluation Layer, NOT Decision Engine:
       M17 does NOT detect attacks and does NOT replace M12. M12 remains the SOLE
       final security decision authority (ACCEPT / SUSPICIOUS / ATTACK).
       M17 evaluates how the pipeline behaves when subjected to defined scenarios.
    2. Zero Recalculation:
       M17 does NOT duplicate M10 statistical tests, M11 threshold calculations,
       M12 decision logic, M13 impersonation checks, M14 authorization checks,
       M15 channel telemetry analysis, or M16 evidence fusion.
    3. Scientific Claim Discipline:
       "PASS" means the pipeline produced the expected verdict and evidence representation
       for a controlled test fixture. It does NOT imply "100% security", "guaranteed
       attack detection", or real-world threat protection probability.
    4. Categorical & Count-Based Metrics:
       Strictly zero arbitrary composite scores, trust scores, risk scores, or heuristic
       point systems. Metrics are purely count-based (scenarios evaluated, passed, failed,
       verdict distributions, confusion matrix counts).
    5. Deep Immutability & Determinism:
       Scenarios, results, metrics, and summaries are frozen dataclasses with defensive
       sequence copying, recursive deep-freezing of mappings, and secret-key leakage guards.
       Repeated runs on identical inputs yield bit-for-bit identical evaluation results.
    6. Fault-Tolerant Suite Execution:
       The evaluation runner evaluates all scenarios to completion without early abort
       upon individual scenario failure.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from src.detection.authorization import (
    AuthorizationEvidence,
    AuthorizationReasonCode,
    AuthorizationStatus,
)
from src.detection.channel import (
    ChannelEvidenceStatus,
    ChannelReasonCode,
    ChannelSecurityEvidence,
)
from src.detection.decision import (
    DecisionReasonCode,
    DecisionResult,
    DecisionVerdict,
    ProtocolSecurityEvidence,
    evaluate_security_decision,
)
from src.detection.fusion import (
    EvidenceSource,
    FusedEvidenceStatus,
    FusedSecurityEvidence,
    FusionReasonCode,
    evaluate_fused_security_decision,
    fuse_security_evidence,
)
from src.detection.impersonation import (
    IdentityEvidenceStatus,
    ImpersonationEvidence,
    ImpersonationReasonCode,
)
from src.statistics.thresholds import (
    MetricThresholdEvaluation,
    PolicyEvaluationReport,
    ThresholdDirection,
    ThresholdMethod,
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
                    "Raw credentials or cryptographic secrets must never be placed in evaluation structures."
                )
        if isinstance(val, Mapping):
            _check_for_secret_leakage(val, f"{container_name}['{key}']")
        elif isinstance(val, (list, tuple)):
            for idx, item in enumerate(val):
                if isinstance(item, Mapping):
                    _check_for_secret_leakage(item, f"{container_name}['{key}'][{idx}]")


# ==============================================================================
# Evaluation Categories
# ==============================================================================

class EvaluationCategory(str, Enum):
    """Categorical taxonomy of security evaluation scenarios.

    Covers baseline honest conditions, expected physical noise, explicit identity/
    authorization breaches, physical channel disturbances, evidence omissions,
    contextual incompatibilities, and multi-source combinations.
    """

    CLEAN_HONEST = "CLEAN_HONEST"
    BENIGN_NOISE = "BENIGN_NOISE"
    IMPERSONATION = "IMPERSONATION"
    UNAUTHORIZED_VERIFICATION = "UNAUTHORIZED_VERIFICATION"
    QUANTUM_CHANNEL_ANOMALY = "QUANTUM_CHANNEL_ANOMALY"
    EXPLICIT_QUANTUM_CHANNEL_VIOLATION = "EXPLICIT_QUANTUM_CHANNEL_VIOLATION"
    INCOMPLETE_EVIDENCE = "INCOMPLETE_EVIDENCE"
    INCOMPATIBLE_CONTEXT = "INCOMPATIBLE_CONTEXT"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"
    MULTI_SOURCE_SECURITY_VIOLATION = "MULTI_SOURCE_SECURITY_VIOLATION"


# ==============================================================================
# Evaluation Scenario Container
# ==============================================================================

@dataclass(frozen=True)
class EvaluationScenario:
    """Immutable definition of a controlled security evaluation scenario.

    Specifies the input evidence fixtures, operational context expectations,
    and expected M12 verdict / violation assertions against which the pipeline is evaluated.

    Attributes:
        scenario_id: Unique, non-empty identifier for the scenario.
        name: Short descriptive title.
        description: Detailed premise and security conditions of the scenario.
        category: Taxonomy category from EvaluationCategory.
        expected_verdict: Expected authoritative M12 decision verdict (ACCEPT, SUSPICIOUS, ATTACK).
        expected_is_violation: Expected boolean flag for confirmed explicit security violation.
        expected_violation_types: Sorted tuple of expected canonical violation identifiers.
        fused_evidence: Optional pre-fused FusedSecurityEvidence fixture.
        impersonation_evidence: Optional M13 ImpersonationEvidence fixture.
        authorization_evidence: Optional M14 AuthorizationEvidence fixture.
        channel_evidence: Optional M15 ChannelSecurityEvidence fixture.
        protocol_evidence: Optional direct ProtocolSecurityEvidence fixture.
        threshold_report: Optional M11 PolicyEvaluationReport fixture.
        expected_session_id: Optional session identifier constraint.
        expected_configuration_hash: Optional canonical baseline configuration hash constraint.
        required_sources: Tuple of required evidence sources for fusion evaluation.
        metadata: Contextual metadata dictionary.
    """

    scenario_id: str
    name: str
    description: str
    category: EvaluationCategory
    expected_verdict: DecisionVerdict
    expected_is_violation: bool = False
    expected_violation_types: tuple[str, ...] = ()
    fused_evidence: FusedSecurityEvidence | None = None
    impersonation_evidence: ImpersonationEvidence | None = None
    authorization_evidence: AuthorizationEvidence | None = None
    channel_evidence: ChannelSecurityEvidence | None = None
    protocol_evidence: ProtocolSecurityEvidence | None = None
    threshold_report: PolicyEvaluationReport | None = None
    expected_session_id: str | None = None
    expected_configuration_hash: str | None = None
    required_sources: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate typing, field invariants, immutability, and secret leakage."""
        if not isinstance(self.scenario_id, str):
            raise TypeError(f"scenario_id must be str, got {type(self.scenario_id).__name__}.")
        if not self.scenario_id.strip():
            raise ValueError("scenario_id cannot be empty or whitespace.")

        if not isinstance(self.name, str):
            raise TypeError(f"name must be str, got {type(self.name).__name__}.")
        if not self.name.strip():
            raise ValueError("name cannot be empty or whitespace.")

        if not isinstance(self.description, str):
            raise TypeError(f"description must be str, got {type(self.description).__name__}.")
        if not self.description.strip():
            raise ValueError("description cannot be empty or whitespace.")

        # Category normalization & validation
        if not isinstance(self.category, EvaluationCategory):
            if isinstance(self.category, str):
                try:
                    object.__setattr__(self, "category", EvaluationCategory(self.category.strip()))
                except ValueError as exc:
                    raise ValueError(f"Invalid EvaluationCategory: '{self.category}'.") from exc
            else:
                raise TypeError(f"category must be EvaluationCategory, got {type(self.category).__name__}.")

        # Verdict normalization & validation
        if not isinstance(self.expected_verdict, DecisionVerdict):
            if isinstance(self.expected_verdict, str):
                try:
                    object.__setattr__(self, "expected_verdict", DecisionVerdict(self.expected_verdict.strip().upper()))
                except ValueError as exc:
                    raise ValueError(f"Invalid DecisionVerdict: '{self.expected_verdict}'.") from exc
            else:
                raise TypeError(f"expected_verdict must be DecisionVerdict, got {type(self.expected_verdict).__name__}.")

        if not isinstance(self.expected_is_violation, bool):
            raise TypeError(f"expected_is_violation must be bool, got {type(self.expected_is_violation).__name__}.")

        # Logical consistency of expected outcomes under M12 Precedence 1
        if self.expected_is_violation and self.expected_verdict == DecisionVerdict.ACCEPT:
            raise ValueError("Contradictory expected outcome: expected_is_violation=True cannot have expected_verdict=ACCEPT.")
        if self.expected_violation_types and not self.expected_is_violation:
            raise ValueError("Contradictory expected outcome: expected_violation_types is non-empty but expected_is_violation=False.")

        # Evidence fixture type validation
        if self.fused_evidence is not None and not isinstance(self.fused_evidence, FusedSecurityEvidence):
            raise TypeError(f"fused_evidence must be FusedSecurityEvidence or None, got {type(self.fused_evidence).__name__}.")
        if self.impersonation_evidence is not None and not isinstance(self.impersonation_evidence, ImpersonationEvidence):
            raise TypeError(f"impersonation_evidence must be ImpersonationEvidence or None, got {type(self.impersonation_evidence).__name__}.")
        if self.authorization_evidence is not None and not isinstance(self.authorization_evidence, AuthorizationEvidence):
            raise TypeError(f"authorization_evidence must be AuthorizationEvidence or None, got {type(self.authorization_evidence).__name__}.")
        if self.channel_evidence is not None and not isinstance(self.channel_evidence, ChannelSecurityEvidence):
            raise TypeError(f"channel_evidence must be ChannelSecurityEvidence or None, got {type(self.channel_evidence).__name__}.")
        if self.protocol_evidence is not None and not isinstance(self.protocol_evidence, (ProtocolSecurityEvidence, Mapping)):
            raise TypeError(f"protocol_evidence must be ProtocolSecurityEvidence, Mapping, or None, got {type(self.protocol_evidence).__name__}.")
        if self.threshold_report is not None and not isinstance(self.threshold_report, PolicyEvaluationReport):
            raise TypeError(f"threshold_report must be PolicyEvaluationReport or None, got {type(self.threshold_report).__name__}.")

        # Tuple conversions and deterministic sorting
        object.__setattr__(
            self,
            "expected_violation_types",
            tuple(sorted(str(v) for v in self.expected_violation_types)),
        )
        object.__setattr__(
            self,
            "required_sources",
            tuple(sorted(str(s) for s in self.required_sources)),
        )

        # Validate required source names
        valid_sources = {s.value for s in EvidenceSource}
        for s in self.required_sources:
            if s not in valid_sources:
                raise ValueError(f"Invalid required_source: '{s}'. Valid sources are {sorted(valid_sources)}.")

        # Context validation
        if self.expected_session_id is not None:
            if not isinstance(self.expected_session_id, str):
                raise TypeError(f"expected_session_id must be str or None, got {type(self.expected_session_id).__name__}.")
            if not self.expected_session_id.strip():
                raise ValueError("expected_session_id cannot be empty or whitespace when provided.")

        if self.expected_configuration_hash is not None:
            if not isinstance(self.expected_configuration_hash, str):
                raise TypeError(f"expected_configuration_hash must be str or None, got {type(self.expected_configuration_hash).__name__}.")
            if not self.expected_configuration_hash.strip():
                raise ValueError("expected_configuration_hash cannot be empty or whitespace when provided.")

        # Metadata validation, secret check and recursive deep freeze
        if not isinstance(self.metadata, Mapping):
            raise TypeError(f"metadata must be a Mapping, got {type(self.metadata).__name__}.")
        _check_for_secret_leakage(self.metadata, "EvaluationScenario.metadata")
        object.__setattr__(self, "metadata", _deep_freeze_dict(self.metadata))


# ==============================================================================
# Evaluation Result Container
# ==============================================================================

@dataclass(frozen=True)
class EvaluationResult:
    """Immutable result of evaluating a single security scenario against the pipeline.

    Captures the observed M12 decision, comparison with expected outcomes,
    mismatch explanations, and full diagnostic provenance.

    Attributes:
        scenario_id: Identifier of the evaluated scenario.
        scenario_name: Title of the evaluated scenario.
        category: Taxonomy category of the scenario.
        expected_verdict: Expected M12 DecisionVerdict.
        observed_verdict: Authoritative DecisionVerdict rendered by M12.
        passed: True if observed verdict matches expected verdict AND explicit violation matches expected.
        expected_is_violation: Expected explicit violation boolean.
        observed_is_violation: Authoritative explicit violation boolean reported by M12.
        decision_result: Complete DecisionResult container produced by M12.
        fused_evidence: Optional FusedSecurityEvidence container if evaluated through M16.
        mismatch_reasons: Sorted tuple of human-readable diagnostic strings explaining failures.
        session_id: Resolved session identifier if present.
        configuration_hash: Resolved configuration hash if present.
        timestamp: Deterministic provenance timestamp.
        metadata: Deep-frozen contextual metadata dictionary.
    """

    scenario_id: str
    scenario_name: str
    category: EvaluationCategory
    expected_verdict: DecisionVerdict
    observed_verdict: DecisionVerdict
    passed: bool
    expected_is_violation: bool
    observed_is_violation: bool
    decision_result: DecisionResult
    fused_evidence: FusedSecurityEvidence | None = None
    mismatch_reasons: tuple[str, ...] = ()
    session_id: str | None = None
    configuration_hash: str | None = None
    timestamp: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Enforce validation, sorting, deep-freezing, and secret checks."""
        if not isinstance(self.scenario_id, str) or not self.scenario_id.strip():
            raise ValueError("scenario_id must be a non-empty string.")
        if not isinstance(self.scenario_name, str) or not self.scenario_name.strip():
            raise ValueError("scenario_name must be a non-empty string.")
        if not isinstance(self.category, EvaluationCategory):
            raise TypeError(f"category must be EvaluationCategory, got {type(self.category).__name__}.")
        if not isinstance(self.expected_verdict, DecisionVerdict):
            raise TypeError(f"expected_verdict must be DecisionVerdict, got {type(self.expected_verdict).__name__}.")
        if not isinstance(self.observed_verdict, DecisionVerdict):
            raise TypeError(f"observed_verdict must be DecisionVerdict, got {type(self.observed_verdict).__name__}.")
        if not isinstance(self.passed, bool):
            raise TypeError(f"passed must be bool, got {type(self.passed).__name__}.")
        if not isinstance(self.expected_is_violation, bool):
            raise TypeError(f"expected_is_violation must be bool, got {type(self.expected_is_violation).__name__}.")
        if not isinstance(self.observed_is_violation, bool):
            raise TypeError(f"observed_is_violation must be bool, got {type(self.observed_is_violation).__name__}.")
        if not isinstance(self.decision_result, DecisionResult):
            raise TypeError(f"decision_result must be DecisionResult, got {type(self.decision_result).__name__}.")
        if self.fused_evidence is not None and not isinstance(self.fused_evidence, FusedSecurityEvidence):
            raise TypeError(f"fused_evidence must be FusedSecurityEvidence or None, got {type(self.fused_evidence).__name__}.")
        if not isinstance(self.metadata, Mapping):
            raise TypeError(f"metadata must be a Mapping, got {type(self.metadata).__name__}.")

        object.__setattr__(self, "mismatch_reasons", tuple(sorted(str(m) for m in self.mismatch_reasons)))
        _check_for_secret_leakage(self.metadata, "EvaluationResult.metadata")
        object.__setattr__(self, "metadata", _deep_freeze_dict(self.metadata))


# ==============================================================================
# Metrics & Summaries
# ==============================================================================

@dataclass(frozen=True)
class ConfusionMatrixMetrics:
    """Categorical count-based contingency metrics for evaluated security scenarios.

    Definitions:
        true_positives (TP): Scenario expected a confirmed security violation and M12 observed ATTACK.
        false_negatives (FN): Scenario expected a confirmed security violation but M12 observed non-ATTACK.
        false_positives (FP): Scenario expected a non-violation condition but M12 observed ATTACK.
        true_negatives (TN): Scenario expected a non-violation condition and M12 observed non-ATTACK.

    Note on Scientific Scope:
        These metrics represent deterministic performance strictly on the defined evaluation scenario
        fixtures. They do NOT represent empirical attack detection probabilities in real-world deployment.
    """

    true_positives: int
    false_negatives: int
    false_positives: int
    true_negatives: int
    sensitivity: float | None = None
    specificity: float | None = None

    def __post_init__(self) -> None:
        """Validate non-negative counts and compute sensitivity / specificity."""
        for name, val in [
            ("true_positives", self.true_positives),
            ("false_negatives", self.false_negatives),
            ("false_positives", self.false_positives),
            ("true_negatives", self.true_negatives),
        ]:
            if not isinstance(val, int) or val < 0:
                raise ValueError(f"{name} must be a non-negative integer, got {val}.")

        # Sensitivity (Recall on violations) = TP / (TP + FN)
        sens: float | None = None
        total_positives = self.true_positives + self.false_negatives
        if total_positives > 0:
            sens = float(self.true_positives) / float(total_positives)
        object.__setattr__(self, "sensitivity", sens)

        # Specificity (True negative rate) = TN / (TN + FP)
        spec: float | None = None
        total_negatives = self.true_negatives + self.false_positives
        if total_negatives > 0:
            spec = float(self.true_negatives) / float(total_negatives)
        object.__setattr__(self, "specificity", spec)


@dataclass(frozen=True)
class CategorySummary:
    """Evaluation summary for a specific scenario category."""

    category: EvaluationCategory
    total_scenarios: int
    passed_scenarios: int
    failed_scenarios: int
    pass_rate: float | None = None


@dataclass(frozen=True)
class EvaluationSummary:
    """Immutable aggregate report of an evaluation suite run.

    Attributes:
        total_scenarios: Total number of scenarios evaluated.
        passed_scenarios: Number of scenarios where expected and observed outcomes matched.
        failed_scenarios: Number of scenarios where expected and observed outcomes diverged.
        pass_rate: Fraction of scenarios passed (0.0 to 1.0), or None if total_scenarios is 0.
        verdict_counts: Count of observed verdicts across all scenarios (ACCEPT, SUSPICIOUS, ATTACK).
        expected_verdict_counts: Count of expected verdicts across all scenarios.
        confusion_matrix: Categorical confusion matrix metrics on defined scenario set.
        category_summaries: Breakdown of evaluation results by EvaluationCategory.
        failed_scenario_ids: Sorted tuple of scenario IDs that failed evaluation.
        results: Tuple of individual EvaluationResult objects in deterministic execution order.
        timestamp: Deterministic evaluation epoch / provenance timestamp.
    """

    total_scenarios: int
    passed_scenarios: int
    failed_scenarios: int
    pass_rate: float | None = None
    verdict_counts: dict[str, int] = field(default_factory=dict)
    expected_verdict_counts: dict[str, int] = field(default_factory=dict)
    confusion_matrix: ConfusionMatrixMetrics = field(
        default_factory=lambda: ConfusionMatrixMetrics(0, 0, 0, 0)
    )
    category_summaries: dict[str, CategorySummary] = field(default_factory=dict)
    failed_scenario_ids: tuple[str, ...] = ()
    results: tuple[EvaluationResult, ...] = ()
    timestamp: str = ""

    def __post_init__(self) -> None:
        """Enforce sorting, deep copy of mappings, and tuple immutability."""
        object.__setattr__(self, "failed_scenario_ids", tuple(sorted(self.failed_scenario_ids)))
        object.__setattr__(self, "results", tuple(self.results))
        object.__setattr__(self, "verdict_counts", dict(self.verdict_counts))
        object.__setattr__(self, "expected_verdict_counts", dict(self.expected_verdict_counts))
        object.__setattr__(self, "category_summaries", dict(self.category_summaries))

    @property
    def results_by_id(self) -> dict[str, EvaluationResult]:
        """Convenience dictionary mapping scenario_id to its EvaluationResult for deterministic ID-based lookup."""
        return {r.scenario_id: r for r in self.results}

    def get_result(self, scenario_id: str) -> EvaluationResult | None:
        """Retrieve evaluation result for a specific scenario identifier."""
        return self.results_by_id.get(scenario_id)


# ==============================================================================
# Evaluation Runner
# ==============================================================================

def evaluate_scenario(scenario: EvaluationScenario) -> EvaluationResult:
    """Evaluate a single security scenario through the established Q-SHIELD pipeline.

    Invokes the authoritative M12 decision engine (directly or via M16 evidence fusion)
    and compares the observed verdict and violation status against the scenario's
    expected outcomes.

    M12 remains the SOLE authority for security verdicts; this function does NOT
    independently implement decision logic.

    Args:
        scenario: Validated EvaluationScenario definition.

    Returns:
        Immutable EvaluationResult recording expected vs observed behavior and diagnostic details.
    """
    if not isinstance(scenario, EvaluationScenario):
        raise TypeError(f"scenario must be EvaluationScenario, got {type(scenario).__name__}.")

    mismatches: list[str] = []
    observed_decision: DecisionResult
    evaluated_fused: FusedSecurityEvidence | None = None

    # Determine execution pathway based on provided evidence fixtures
    if scenario.fused_evidence is not None:
        evaluated_fused = scenario.fused_evidence
        observed_decision = evaluate_fused_security_decision(
            fused_evidence=evaluated_fused,
            threshold_report=scenario.threshold_report,
            expected_session_id=scenario.expected_session_id,
            expected_configuration_hash=scenario.expected_configuration_hash,
            metadata=scenario.metadata,
        )
    elif (
        scenario.impersonation_evidence is not None
        or scenario.authorization_evidence is not None
        or scenario.channel_evidence is not None
        or bool(scenario.required_sources)
    ):
        req_sources = scenario.required_sources if scenario.required_sources else None
        evaluated_fused = fuse_security_evidence(
            impersonation_evidence=scenario.impersonation_evidence,
            authorization_evidence=scenario.authorization_evidence,
            channel_evidence=scenario.channel_evidence,
            required_sources=req_sources,
            expected_session_id=scenario.expected_session_id,
            expected_configuration_hash=scenario.expected_configuration_hash,
            metadata=scenario.metadata,
        )
        observed_decision = evaluate_fused_security_decision(
            fused_evidence=evaluated_fused,
            threshold_report=scenario.threshold_report,
            expected_session_id=scenario.expected_session_id,
            expected_configuration_hash=scenario.expected_configuration_hash,
            metadata=scenario.metadata,
        )
    elif scenario.protocol_evidence is not None or scenario.threshold_report is not None:
        observed_decision = evaluate_security_decision(
            threshold_report=scenario.threshold_report,
            protocol_evidence=scenario.protocol_evidence,
            expected_configuration_hash=scenario.expected_configuration_hash,
            metadata=scenario.metadata,
        )
    else:
        # Default: evaluate clean empty protocol evidence directly in M12
        observed_decision = evaluate_security_decision(
            expected_configuration_hash=scenario.expected_configuration_hash,
            metadata=scenario.metadata,
        )

    # Compare Observed vs Expected
    verdict_match = (observed_decision.verdict == scenario.expected_verdict)
    if not verdict_match:
        mismatches.append(
            f"VERDICT_MISMATCH: expected {scenario.expected_verdict.value}, "
            f"observed {observed_decision.verdict.value} (reason: {observed_decision.primary_reason})"
        )

    violation_match = (observed_decision.is_explicit_violation == scenario.expected_is_violation)
    if not violation_match:
        mismatches.append(
            f"VIOLATION_FLAG_MISMATCH: expected is_explicit_violation={scenario.expected_is_violation}, "
            f"observed {observed_decision.is_explicit_violation}"
        )

    # If violation types were explicitly expected, verify they are represented
    if scenario.expected_violation_types:
        observed_violations: set[str] = set()
        if evaluated_fused is not None:
            observed_violations.update(evaluated_fused.violations)
        if observed_decision.protocol_evidence is not None and observed_decision.protocol_evidence.violation_type:
            # Handle possible '+' joined violation strings from fusion bridge
            for part in observed_decision.protocol_evidence.violation_type.split("+"):
                observed_violations.add(part.strip())

        missing_types = [t for t in scenario.expected_violation_types if t not in observed_violations]
        if missing_types:
            mismatches.append(
                f"EXPECTED_VIOLATIONS_MISSING: missing expected violation types {missing_types}; "
                f"observed violations were {sorted(observed_violations)}"
            )

    passed = (verdict_match and violation_match and len(mismatches) == 0)

    # Derive deterministic timestamp from scenario/evidence provenance
    provenance_timestamp = ""
    if evaluated_fused is not None and evaluated_fused.timestamp:
        provenance_timestamp = evaluated_fused.timestamp
    elif observed_decision.timestamp:
        provenance_timestamp = observed_decision.timestamp

    # Resolve session ID and config hash
    res_session_id = scenario.expected_session_id
    if res_session_id is None and evaluated_fused is not None:
        res_session_id = evaluated_fused.session_id

    res_config_hash = scenario.expected_configuration_hash
    if res_config_hash is None and evaluated_fused is not None:
        res_config_hash = evaluated_fused.configuration_hash

    return EvaluationResult(
        scenario_id=scenario.scenario_id,
        scenario_name=scenario.name,
        category=scenario.category,
        expected_verdict=scenario.expected_verdict,
        observed_verdict=observed_decision.verdict,
        passed=passed,
        expected_is_violation=scenario.expected_is_violation,
        observed_is_violation=observed_decision.is_explicit_violation,
        decision_result=observed_decision,
        fused_evidence=evaluated_fused,
        mismatch_reasons=tuple(mismatches),
        session_id=res_session_id,
        configuration_hash=res_config_hash,
        timestamp=provenance_timestamp,
        metadata=scenario.metadata,
    )


def run_security_evaluation(scenarios: Sequence[EvaluationScenario]) -> EvaluationSummary:
    """Run an entire suite of security evaluation scenarios deterministically.

    Continues execution through individual scenario failures or errors so that
    complete diagnostic visibility is gathered across all evaluated conditions.

    Args:
        scenarios: Sequence of EvaluationScenario definitions to execute.

    Returns:
        Immutable EvaluationSummary with categorical metrics, confusion matrix counts,
        category summaries, and full result records.
    """
    if not isinstance(scenarios, Sequence) or isinstance(scenarios, (str, bytes)):
        raise TypeError(f"scenarios must be a Sequence of EvaluationScenario, got {type(scenarios).__name__}.")

    results_list: list[EvaluationResult] = []
    failed_ids: list[str] = []

    verdict_counts = {
        DecisionVerdict.ACCEPT.value: 0,
        DecisionVerdict.SUSPICIOUS.value: 0,
        DecisionVerdict.ATTACK.value: 0,
    }
    expected_verdict_counts = {
        DecisionVerdict.ACCEPT.value: 0,
        DecisionVerdict.SUSPICIOUS.value: 0,
        DecisionVerdict.ATTACK.value: 0,
    }

    category_data: dict[str, dict[str, int]] = {}

    tp = 0
    fn = 0
    fp = 0
    tn = 0

    latest_timestamp = ""

    for sc in scenarios:
        if not isinstance(sc, EvaluationScenario):
            raise TypeError(f"Each item in scenarios must be an EvaluationScenario, got {type(sc).__name__}.")

        expected_verdict_counts[sc.expected_verdict.value] += 1
        cat_key = sc.category.value
        if cat_key not in category_data:
            category_data[cat_key] = {"total": 0, "passed": 0, "failed": 0}
        category_data[cat_key]["total"] += 1

        res = evaluate_scenario(sc)
        results_list.append(res)
        verdict_counts[res.observed_verdict.value] += 1

        if res.timestamp and res.timestamp > latest_timestamp:
            latest_timestamp = res.timestamp

        if res.passed:
            category_data[cat_key]["passed"] += 1
        else:
            category_data[cat_key]["failed"] += 1
            failed_ids.append(res.scenario_id)

        # Update Confusion Matrix
        # Positive = Expected confirmed security violation
        # Negative = Expected non-violation
        is_expected_violation = sc.expected_is_violation or (sc.expected_verdict == DecisionVerdict.ATTACK)
        is_observed_attack = (res.observed_verdict == DecisionVerdict.ATTACK)

        if is_expected_violation:
            if is_observed_attack:
                tp += 1
            else:
                fn += 1
        else:
            if is_observed_attack:
                fp += 1
            else:
                tn += 1

    total = len(results_list)
    passed_cnt = total - len(failed_ids)
    pass_rate = (float(passed_cnt) / float(total)) if total > 0 else None

    # Build category summaries
    cat_summaries: dict[str, CategorySummary] = {}
    for cat_name, counts in sorted(category_data.items()):
        c_tot = counts["total"]
        c_pass = counts["passed"]
        c_fail = counts["failed"]
        c_rate = (float(c_pass) / float(c_tot)) if c_tot > 0 else None
        cat_summaries[cat_name] = CategorySummary(
            category=EvaluationCategory(cat_name),
            total_scenarios=c_tot,
            passed_scenarios=c_pass,
            failed_scenarios=c_fail,
            pass_rate=c_rate,
        )

    conf_matrix = ConfusionMatrixMetrics(
        true_positives=tp,
        false_negatives=fn,
        false_positives=fp,
        true_negatives=tn,
    )

    return EvaluationSummary(
        total_scenarios=total,
        passed_scenarios=passed_cnt,
        failed_scenarios=len(failed_ids),
        pass_rate=pass_rate,
        verdict_counts=verdict_counts,
        expected_verdict_counts=expected_verdict_counts,
        confusion_matrix=conf_matrix,
        category_summaries=cat_summaries,
        failed_scenario_ids=tuple(sorted(failed_ids)),
        results=tuple(results_list),
        timestamp=latest_timestamp,
    )


# ==============================================================================
# Evidence Factory Helpers for Evaluation
# ==============================================================================

def make_clean_impersonation_evidence(
    session_id: str | None = None,
    configuration_hash: str | None = None,
    timestamp: str = "2026-09-06T10:00:00Z",
) -> ImpersonationEvidence:
    """Helper to construct clean M13 ImpersonationEvidence."""
    return ImpersonationEvidence(
        is_impersonation_detected=False,
        is_indeterminate=False,
        status=IdentityEvidenceStatus.VALID,
        primary_reason=ImpersonationReasonCode.IDENTITY_VERIFIED,
        reason_codes=(ImpersonationReasonCode.IDENTITY_VERIFIED,),
        expected_identity="alice_signer",
        claimed_identity="alice_signer",
        authenticated_identity="alice_signer",
        session_id=session_id,
        configuration_hash=configuration_hash,
        is_evidence_complete=True,
        timestamp=timestamp,
    )


def make_clean_authorization_evidence(
    session_id: str | None = None,
    configuration_hash: str | None = None,
    timestamp: str = "2026-09-06T10:00:01Z",
) -> AuthorizationEvidence:
    """Helper to construct clean M14 AuthorizationEvidence."""
    return AuthorizationEvidence(
        is_authorized=True,
        is_unauthorized_detected=False,
        is_indeterminate=False,
        status=AuthorizationStatus.AUTHORIZED,
        primary_reason=AuthorizationReasonCode.AUTHORIZATION_GRANTED,
        reason_codes=(AuthorizationReasonCode.AUTHORIZATION_GRANTED,),
        participant_identity="bob_verifier",
        operation="verify_signature",
        role="verifier",
        session_id=session_id,
        configuration_hash=configuration_hash,
        is_evidence_complete=True,
        timestamp=timestamp,
    )


def make_clean_threshold_report(
    session_id: str | None = None,
    configuration_hash: str | None = None,
    timestamp: str = "2026-09-06T10:00:00Z",
) -> PolicyEvaluationReport:
    """Helper to construct clean M11 PolicyEvaluationReport with no thresholds exceeded."""
    cfg = configuration_hash or "a" * 64
    evals = {
        "qber:0": MetricThresholdEvaluation(
            metric_name="qber:0",
            observed_value=0.01,
            threshold_value=0.05,
            direction=ThresholdDirection.UPPER,
            exceeded=False,
            margin=0.04,
            signed_distance=-0.04,
            method=ThresholdMethod.FIXED_BOUND,
            boundary_status="strictly_inside",
        ),
        "fidelity:0": MetricThresholdEvaluation(
            metric_name="fidelity:0",
            observed_value=0.98,
            threshold_value=0.90,
            direction=ThresholdDirection.LOWER,
            exceeded=False,
            margin=0.08,
            signed_distance=0.08,
            method=ThresholdMethod.FIXED_BOUND,
            boundary_status="strictly_inside",
        ),
    }
    meta: dict[str, Any] = {}
    if session_id is not None:
        meta["session_id"] = session_id

    return PolicyEvaluationReport(
        policy_id="policy_clean_eval",
        baseline_configuration_hash=cfg,
        metric_evaluations=evals,
        any_exceeded=False,
        all_exceeded=False,
        exceeded_metrics=(),
        exceeded_count=0,
        total_metrics_evaluated=2,
        timestamp=timestamp,
        metadata=meta,
    )


def make_anomalous_threshold_report(
    session_id: str | None = None,
    configuration_hash: str | None = None,
    timestamp: str = "2026-09-06T10:00:00Z",
) -> PolicyEvaluationReport:
    """Helper to construct M11 PolicyEvaluationReport with QBER threshold exceeded."""
    cfg = configuration_hash or "a" * 64
    evals = {
        "qber:0": MetricThresholdEvaluation(
            metric_name="qber:0",
            observed_value=0.12,
            threshold_value=0.05,
            direction=ThresholdDirection.UPPER,
            exceeded=True,
            margin=-0.07,
            signed_distance=0.07,
            method=ThresholdMethod.FIXED_BOUND,
            boundary_status="strictly_exceeded",
        ),
    }
    meta: dict[str, Any] = {}
    if session_id is not None:
        meta["session_id"] = session_id

    return PolicyEvaluationReport(
        policy_id="policy_anom_eval",
        baseline_configuration_hash=cfg,
        metric_evaluations=evals,
        any_exceeded=True,
        all_exceeded=True,
        exceeded_metrics=("qber:0",),
        exceeded_count=1,
        total_metrics_evaluated=1,
        timestamp=timestamp,
        metadata=meta,
    )


def make_clean_channel_evidence(
    session_id: str | None = None,
    configuration_hash: str | None = None,
    timestamp: str = "2026-09-06T10:00:02Z",
    attach_threshold_report: bool = True,
) -> ChannelSecurityEvidence:
    """Helper to construct clean M15 ChannelSecurityEvidence."""
    rep = make_clean_threshold_report(session_id=session_id, configuration_hash=configuration_hash, timestamp=timestamp) if attach_threshold_report else None
    return ChannelSecurityEvidence(
        status=ChannelEvidenceStatus.CLEAN,
        primary_reason=ChannelReasonCode.CHANNEL_CLEAN,
        reason_codes=(ChannelReasonCode.CHANNEL_CLEAN,),
        is_anomalous=False,
        is_explicit_violation=False,
        is_evidence_complete=True,
        session_id=session_id,
        configuration_hash=configuration_hash,
        threshold_report=rep,
        timestamp=timestamp,
    )


def make_violating_impersonation_evidence(
    session_id: str | None = None,
    configuration_hash: str | None = None,
    timestamp: str = "2026-09-06T10:00:00Z",
) -> ImpersonationEvidence:
    """Helper to construct explicit M13 impersonation violation."""
    return ImpersonationEvidence(
        is_impersonation_detected=True,
        is_indeterminate=False,
        status=IdentityEvidenceStatus.IDENTITY_MISMATCH,
        primary_reason=ImpersonationReasonCode.AUTHENTICATED_IDENTITY_MISMATCH,
        reason_codes=(ImpersonationReasonCode.AUTHENTICATED_IDENTITY_MISMATCH,),
        expected_identity="alice_signer",
        claimed_identity="alice_signer",
        authenticated_identity="mallory_attacker",
        session_id=session_id,
        configuration_hash=configuration_hash,
        is_evidence_complete=True,
        timestamp=timestamp,
    )


def make_unauthorized_authorization_evidence(
    session_id: str | None = None,
    configuration_hash: str | None = None,
    timestamp: str = "2026-09-06T10:00:01Z",
) -> AuthorizationEvidence:
    """Helper to construct explicit M14 unauthorized verification violation."""
    return AuthorizationEvidence(
        is_authorized=False,
        is_unauthorized_detected=True,
        is_indeterminate=False,
        status=AuthorizationStatus.UNAUTHORIZED,
        primary_reason=AuthorizationReasonCode.AUTHORIZATION_DENIED,
        reason_codes=(AuthorizationReasonCode.AUTHORIZATION_DENIED,),
        participant_identity="unauthorized_actor",
        operation="verify_signature",
        role="unauthorized_role",
        session_id=session_id,
        configuration_hash=configuration_hash,
        is_evidence_complete=True,
        timestamp=timestamp,
    )


def make_anomalous_channel_evidence(
    session_id: str | None = None,
    configuration_hash: str | None = None,
    timestamp: str = "2026-09-06T10:00:02Z",
    attach_threshold_report: bool = True,
) -> ChannelSecurityEvidence:
    """Helper to construct M15 channel anomaly evidence."""
    rep = make_anomalous_threshold_report(session_id=session_id, configuration_hash=configuration_hash, timestamp=timestamp) if attach_threshold_report else None
    return ChannelSecurityEvidence(
        status=ChannelEvidenceStatus.ANOMALOUS,
        primary_reason=ChannelReasonCode.QBER_THRESHOLD_EXCEEDED,
        reason_codes=(ChannelReasonCode.QBER_THRESHOLD_EXCEEDED,),
        is_anomalous=True,
        is_explicit_violation=False,
        is_evidence_complete=True,
        exceeded_metrics=("qber:0",),
        exceeded_count=1,
        session_id=session_id,
        configuration_hash=configuration_hash,
        threshold_report=rep,
        timestamp=timestamp,
    )


def make_violating_channel_evidence(
    session_id: str | None = None,
    configuration_hash: str | None = None,
    timestamp: str = "2026-09-06T10:00:02Z",
) -> ChannelSecurityEvidence:
    """Helper to construct explicit M15 channel breach violation."""
    return ChannelSecurityEvidence(
        status=ChannelEvidenceStatus.SECURITY_VIOLATION,
        primary_reason=ChannelReasonCode.QUANTUM_CHANNEL_SECURITY_VIOLATION,
        reason_codes=(ChannelReasonCode.QUANTUM_CHANNEL_SECURITY_VIOLATION,),
        is_anomalous=False,
        is_explicit_violation=True,
        violation_type=ChannelReasonCode.QUANTUM_CHANNEL_SECURITY_VIOLATION.value,
        is_evidence_complete=True,
        session_id=session_id,
        configuration_hash=configuration_hash,
        timestamp=timestamp,
    )


def make_conflicting_impersonation_evidence(
    session_id: str | None = None,
    configuration_hash: str | None = None,
    timestamp: str = "2026-09-06T10:00:00Z",
) -> ImpersonationEvidence:
    """Helper to construct M13 conflicting identity evidence."""
    return ImpersonationEvidence(
        is_impersonation_detected=False,
        is_indeterminate=True,
        status=IdentityEvidenceStatus.CONFLICTING,
        primary_reason=ImpersonationReasonCode.CONFLICTING_IDENTITY_EVIDENCE,
        reason_codes=(ImpersonationReasonCode.CONFLICTING_IDENTITY_EVIDENCE,),
        expected_identity="alice_signer",
        claimed_identity="alice_signer",
        authenticated_identity=None,
        session_id=session_id,
        configuration_hash=configuration_hash,
        is_evidence_complete=False,
        timestamp=timestamp,
    )


def make_conflicting_authorization_evidence(
    session_id: str | None = None,
    configuration_hash: str | None = None,
    timestamp: str = "2026-09-06T10:00:01Z",
) -> AuthorizationEvidence:
    """Helper to construct M14 conflicting authorization evidence."""
    return AuthorizationEvidence(
        is_authorized=False,
        is_unauthorized_detected=False,
        is_indeterminate=True,
        status=AuthorizationStatus.CONFLICTING,
        primary_reason=AuthorizationReasonCode.CONFLICTING_AUTHORIZATION_EVIDENCE,
        reason_codes=(AuthorizationReasonCode.CONFLICTING_AUTHORIZATION_EVIDENCE,),
        participant_identity="bob_verifier",
        operation="verify_signature",
        role="verifier",
        session_id=session_id,
        configuration_hash=configuration_hash,
        is_evidence_complete=False,
        timestamp=timestamp,
    )


def make_conflicting_channel_evidence(
    session_id: str | None = None,
    configuration_hash: str | None = None,
    timestamp: str = "2026-09-06T10:00:02Z",
) -> ChannelSecurityEvidence:
    """Helper to construct M15 conflicting channel evidence."""
    return ChannelSecurityEvidence(
        status=ChannelEvidenceStatus.CONFLICTING,
        primary_reason=ChannelReasonCode.CONFLICTING_CHANNEL_EVIDENCE,
        reason_codes=(ChannelReasonCode.CONFLICTING_CHANNEL_EVIDENCE,),
        is_anomalous=False,
        is_explicit_violation=False,
        is_evidence_complete=False,
        session_id=session_id,
        configuration_hash=configuration_hash,
        timestamp=timestamp,
    )


# ==============================================================================
# Standard Baseline Evaluation Suite Builder
# ==============================================================================

def build_baseline_evaluation_suite(
    session_id: str = "sess_baseline_eval",
    configuration_hash: str = "hash_baseline_canon_sha256",
) -> tuple[EvaluationScenario, ...]:
    """Construct a comprehensive, deterministic baseline security evaluation suite.

    Includes representative scenarios for all 10 evaluation categories, as well as
    multi-source interaction combinations A through J:
        1. CLEAN / HONEST (All required sources clean -> ACCEPT)
        2. BENIGN NOISE / EXPECTED VARIATION (Slight noise within threshold policy -> ACCEPT)
        3. IMPERSONATION (M13 identity mismatch confirmed -> ATTACK)
        4. UNAUTHORIZED VERIFICATION (M14 verification attempt denied -> ATTACK)
        5. QUANTUM CHANNEL ANOMALY (M15 QBER/fidelity threshold crossing -> SUSPICIOUS)
        6. EXPLICIT QUANTUM CHANNEL VIOLATION (M15 confirmed channel breach -> ATTACK)
        7. INCOMPLETE EVIDENCE (Missing required M14 authorization evidence -> SUSPICIOUS)
        8. INCOMPATIBLE SESSION/CONFIGURATION (Cross-source session mismatch -> SUSPICIOUS)
        9. CONFLICTING EVIDENCE (Internal contradictory evidence -> SUSPICIOUS)
        10. MULTI-SOURCE SECURITY VIOLATION (M13 + M14 + M15 violations -> ATTACK)
        Plus Combinations A through J explicitly tested.

    Args:
        session_id: Canonical session identifier for coherent scenarios.
        configuration_hash: Canonical baseline SHA-256 configuration hash.

    Returns:
        Sorted tuple of EvaluationScenario objects covering the evaluation matrix.
    """
    scenarios: list[EvaluationScenario] = []

    # Common clean source evidence fixtures
    m13_clean = make_clean_impersonation_evidence(session_id=session_id, configuration_hash=configuration_hash)
    m14_clean = make_clean_authorization_evidence(session_id=session_id, configuration_hash=configuration_hash)
    m15_clean = make_clean_channel_evidence(session_id=session_id, configuration_hash=configuration_hash)

    # Violating / Anomalous / Conflicting fixtures
    m13_viol = make_violating_impersonation_evidence(session_id=session_id, configuration_hash=configuration_hash)
    m14_viol = make_unauthorized_authorization_evidence(session_id=session_id, configuration_hash=configuration_hash)
    m15_anom = make_anomalous_channel_evidence(session_id=session_id, configuration_hash=configuration_hash)
    m15_viol = make_violating_channel_evidence(session_id=session_id, configuration_hash=configuration_hash)
    m13_conflict = make_conflicting_impersonation_evidence(session_id=session_id, configuration_hash=configuration_hash)
    m14_conflict = make_conflicting_authorization_evidence(session_id=session_id, configuration_hash=configuration_hash)

    # --- Scenario 1: CLEAN / HONEST ---
    scenarios.append(
        EvaluationScenario(
            scenario_id="SCEN_01_CLEAN_HONEST",
            name="Clean Honest Protocol Execution",
            description="All security subsystems verify compliant execution under identical context.",
            category=EvaluationCategory.CLEAN_HONEST,
            expected_verdict=DecisionVerdict.ACCEPT,
            expected_is_violation=False,
            impersonation_evidence=m13_clean,
            authorization_evidence=m14_clean,
            channel_evidence=m15_clean,
            expected_session_id=session_id,
            expected_configuration_hash=configuration_hash,
        )
    )

    # --- Scenario 2: BENIGN NOISE / EXPECTED VARIATION ---
    scenarios.append(
        EvaluationScenario(
            scenario_id="SCEN_02_BENIGN_NOISE",
            name="Benign Quantum Channel Noise within Policy",
            description="Quantum channel experiences expected thermal/depolarizing noise within calibrated thresholds.",
            category=EvaluationCategory.BENIGN_NOISE,
            expected_verdict=DecisionVerdict.ACCEPT,
            expected_is_violation=False,
            impersonation_evidence=m13_clean,
            authorization_evidence=m14_clean,
            channel_evidence=m15_clean,
            expected_session_id=session_id,
            expected_configuration_hash=configuration_hash,
            metadata={"noise_type": "depolarizing", "noise_strength": 0.01},
        )
    )

    # --- Scenario 3: IMPERSONATION (Combination A: M13 violation only) ---
    scenarios.append(
        EvaluationScenario(
            scenario_id="SCEN_03_IMPERSONATION_SOLO",
            name="Confirmed Signer Impersonation Breach",
            description="M13 detects cryptographic signer identity mismatch while other subsystems are clean.",
            category=EvaluationCategory.IMPERSONATION,
            expected_verdict=DecisionVerdict.ATTACK,
            expected_is_violation=True,
            expected_violation_types=(ImpersonationReasonCode.AUTHENTICATED_IDENTITY_MISMATCH.value,),
            impersonation_evidence=m13_viol,
            authorization_evidence=m14_clean,
            channel_evidence=m15_clean,
            expected_session_id=session_id,
            expected_configuration_hash=configuration_hash,
        )
    )

    # --- Scenario 4: UNAUTHORIZED VERIFICATION (Combination B: M14 violation only) ---
    scenarios.append(
        EvaluationScenario(
            scenario_id="SCEN_04_UNAUTHORIZED_VERIFICATION_SOLO",
            name="Unauthorized Signature Verification Attempt",
            description="M14 explicitly denies verification operation for unauthorized participant.",
            category=EvaluationCategory.UNAUTHORIZED_VERIFICATION,
            expected_verdict=DecisionVerdict.ATTACK,
            expected_is_violation=True,
            expected_violation_types=(AuthorizationReasonCode.AUTHORIZATION_DENIED.value,),
            impersonation_evidence=m13_clean,
            authorization_evidence=m14_viol,
            channel_evidence=m15_clean,
            expected_session_id=session_id,
            expected_configuration_hash=configuration_hash,
        )
    )

    # --- Scenario 5: QUANTUM CHANNEL ANOMALY ---
    scenarios.append(
        EvaluationScenario(
            scenario_id="SCEN_05_CHANNEL_ANOMALY",
            name="Physical Quantum Channel Disturbance Anomaly",
            description="M15 observes elevated QBER without deterministic confirmation of breach; yields SUSPICIOUS.",
            category=EvaluationCategory.QUANTUM_CHANNEL_ANOMALY,
            expected_verdict=DecisionVerdict.SUSPICIOUS,
            expected_is_violation=False,
            impersonation_evidence=m13_clean,
            authorization_evidence=m14_clean,
            channel_evidence=m15_anom,
            expected_session_id=session_id,
            expected_configuration_hash=configuration_hash,
        )
    )

    # --- Scenario 6: EXPLICIT QUANTUM CHANNEL SECURITY VIOLATION (Combination C: M15 violation only) ---
    scenarios.append(
        EvaluationScenario(
            scenario_id="SCEN_06_EXPLICIT_CHANNEL_VIOLATION_SOLO",
            name="Confirmed Quantum Channel Protocol Violation",
            description="M15 confirms explicit quantum channel protocol breach; yields ATTACK.",
            category=EvaluationCategory.EXPLICIT_QUANTUM_CHANNEL_VIOLATION,
            expected_verdict=DecisionVerdict.ATTACK,
            expected_is_violation=True,
            expected_violation_types=(ChannelReasonCode.QUANTUM_CHANNEL_SECURITY_VIOLATION.value,),
            impersonation_evidence=m13_clean,
            authorization_evidence=m14_clean,
            channel_evidence=m15_viol,
            expected_session_id=session_id,
            expected_configuration_hash=configuration_hash,
        )
    )

    # --- Scenario 7: INCOMPLETE EVIDENCE ---
    scenarios.append(
        EvaluationScenario(
            scenario_id="SCEN_07_INCOMPLETE_EVIDENCE",
            name="Missing Required Authorization Evidence",
            description="M14 authorization evidence is omitted from evaluation suite; missing != clean yields SUSPICIOUS.",
            category=EvaluationCategory.INCOMPLETE_EVIDENCE,
            expected_verdict=DecisionVerdict.SUSPICIOUS,
            expected_is_violation=False,
            impersonation_evidence=m13_clean,
            authorization_evidence=None,
            channel_evidence=m15_clean,
            required_sources=(
                EvidenceSource.IMPERSONATION.value,
                EvidenceSource.AUTHORIZATION.value,
                EvidenceSource.QUANTUM_CHANNEL.value,
            ),
            expected_session_id=session_id,
            expected_configuration_hash=configuration_hash,
        )
    )

    # --- Scenario 8: INCOMPATIBLE SESSION/CONFIGURATION ---
    m15_wrong_session = make_clean_channel_evidence(
        session_id="sess_cross_contamination_999",
        configuration_hash=configuration_hash,
    )
    scenarios.append(
        EvaluationScenario(
            scenario_id="SCEN_08_INCOMPATIBLE_CONTEXT",
            name="Cross-Source Session Context Mismatch",
            description="M15 reports mismatched session ID relative to M13/M14; context mismatch yields SUSPICIOUS.",
            category=EvaluationCategory.INCOMPATIBLE_CONTEXT,
            expected_verdict=DecisionVerdict.SUSPICIOUS,
            expected_is_violation=False,
            impersonation_evidence=m13_clean,
            authorization_evidence=m14_clean,
            channel_evidence=m15_wrong_session,
            expected_session_id=session_id,
            expected_configuration_hash=configuration_hash,
        )
    )

    # --- Scenario 9: CONFLICTING EVIDENCE ---
    scenarios.append(
        EvaluationScenario(
            scenario_id="SCEN_09_CONFLICTING_EVIDENCE",
            name="Contradictory Identity Assertion Evidence",
            description="M13 reports internal credential conflict without explicit violation; yields SUSPICIOUS.",
            category=EvaluationCategory.CONFLICTING_EVIDENCE,
            expected_verdict=DecisionVerdict.SUSPICIOUS,
            expected_is_violation=False,
            impersonation_evidence=m13_conflict,
            authorization_evidence=m14_clean,
            channel_evidence=m15_clean,
            expected_session_id=session_id,
            expected_configuration_hash=configuration_hash,
        )
    )

    # --- Scenario 10: MULTI-SOURCE VIOLATION (Combination G: M13 + M14 + M15 violations) ---
    scenarios.append(
        EvaluationScenario(
            scenario_id="SCEN_10_MULTI_SOURCE_ALL_VIOLATIONS",
            name="Tri-Layer Simultaneous Explicit Security Violations",
            description="M13 impersonation, M14 unauthorized access, and M15 channel breach simultaneously confirmed.",
            category=EvaluationCategory.MULTI_SOURCE_SECURITY_VIOLATION,
            expected_verdict=DecisionVerdict.ATTACK,
            expected_is_violation=True,
            expected_violation_types=(
                ImpersonationReasonCode.AUTHENTICATED_IDENTITY_MISMATCH.value,
                AuthorizationReasonCode.AUTHORIZATION_DENIED.value,
                ChannelReasonCode.QUANTUM_CHANNEL_SECURITY_VIOLATION.value,
            ),
            impersonation_evidence=m13_viol,
            authorization_evidence=m14_viol,
            channel_evidence=m15_viol,
            expected_session_id=session_id,
            expected_configuration_hash=configuration_hash,
        )
    )

    # --- Additional Combinations D, E, F, H, I, J ---

    # Combination D: M13 + M14 violations
    scenarios.append(
        EvaluationScenario(
            scenario_id="SCEN_11_COMB_D_M13_M14_VIOLATIONS",
            name="Impersonation and Unauthorized Verification Simultaneous",
            description="Combination D: M13 and M14 confirm violations while quantum channel is clean.",
            category=EvaluationCategory.MULTI_SOURCE_SECURITY_VIOLATION,
            expected_verdict=DecisionVerdict.ATTACK,
            expected_is_violation=True,
            expected_violation_types=(
                ImpersonationReasonCode.AUTHENTICATED_IDENTITY_MISMATCH.value,
                AuthorizationReasonCode.AUTHORIZATION_DENIED.value,
            ),
            impersonation_evidence=m13_viol,
            authorization_evidence=m14_viol,
            channel_evidence=m15_clean,
            expected_session_id=session_id,
            expected_configuration_hash=configuration_hash,
        )
    )

    # Combination E: M13 + M15 violations
    scenarios.append(
        EvaluationScenario(
            scenario_id="SCEN_12_COMB_E_M13_M15_VIOLATIONS",
            name="Impersonation and Quantum Channel Violation Simultaneous",
            description="Combination E: M13 and M15 confirm violations while authorization is clean.",
            category=EvaluationCategory.MULTI_SOURCE_SECURITY_VIOLATION,
            expected_verdict=DecisionVerdict.ATTACK,
            expected_is_violation=True,
            expected_violation_types=(
                ImpersonationReasonCode.AUTHENTICATED_IDENTITY_MISMATCH.value,
                ChannelReasonCode.QUANTUM_CHANNEL_SECURITY_VIOLATION.value,
            ),
            impersonation_evidence=m13_viol,
            authorization_evidence=m14_clean,
            channel_evidence=m15_viol,
            expected_session_id=session_id,
            expected_configuration_hash=configuration_hash,
        )
    )

    # Combination F: M14 + M15 violations
    scenarios.append(
        EvaluationScenario(
            scenario_id="SCEN_13_COMB_F_M14_M15_VIOLATIONS",
            name="Unauthorized Verification and Channel Violation Simultaneous",
            description="Combination F: M14 and M15 confirm violations while identity authentication is clean.",
            category=EvaluationCategory.MULTI_SOURCE_SECURITY_VIOLATION,
            expected_verdict=DecisionVerdict.ATTACK,
            expected_is_violation=True,
            expected_violation_types=(
                AuthorizationReasonCode.AUTHORIZATION_DENIED.value,
                ChannelReasonCode.QUANTUM_CHANNEL_SECURITY_VIOLATION.value,
            ),
            impersonation_evidence=m13_clean,
            authorization_evidence=m14_viol,
            channel_evidence=m15_viol,
            expected_session_id=session_id,
            expected_configuration_hash=configuration_hash,
        )
    )

    # Combination H: Explicit violation + conflict
    scenarios.append(
        EvaluationScenario(
            scenario_id="SCEN_14_COMB_H_VIOLATION_AND_CONFLICT",
            name="Explicit Violation Preserved Despite Conflicting Evidence",
            description="Combination H: M13 confirms impersonation while M14 contains conflicting credentials; yields ATTACK.",
            category=EvaluationCategory.MULTI_SOURCE_SECURITY_VIOLATION,
            expected_verdict=DecisionVerdict.ATTACK,
            expected_is_violation=True,
            expected_violation_types=(ImpersonationReasonCode.AUTHENTICATED_IDENTITY_MISMATCH.value,),
            impersonation_evidence=m13_viol,
            authorization_evidence=m14_conflict,
            channel_evidence=m15_clean,
            expected_session_id=session_id,
            expected_configuration_hash=configuration_hash,
        )
    )

    # Combination I: Anomaly + incomplete evidence
    scenarios.append(
        EvaluationScenario(
            scenario_id="SCEN_15_COMB_I_ANOMALY_AND_INCOMPLETE",
            name="Quantum Channel Anomaly with Missing Evidence",
            description="Combination I: M15 reports anomaly and M14 authorization is missing; non-violation yields SUSPICIOUS.",
            category=EvaluationCategory.INCOMPLETE_EVIDENCE,
            expected_verdict=DecisionVerdict.SUSPICIOUS,
            expected_is_violation=False,
            impersonation_evidence=m13_clean,
            authorization_evidence=None,
            channel_evidence=m15_anom,
            required_sources=(
                EvidenceSource.IMPERSONATION.value,
                EvidenceSource.AUTHORIZATION.value,
                EvidenceSource.QUANTUM_CHANNEL.value,
            ),
            expected_session_id=session_id,
            expected_configuration_hash=configuration_hash,
        )
    )

    # Combination J: Clean + expected noise
    scenarios.append(
        EvaluationScenario(
            scenario_id="SCEN_16_COMB_J_CLEAN_AND_EXPECTED_NOISE",
            name="Clean Identity and Authorization with Tolerable Channel Noise",
            description="Combination J: Signer and verifier legitimate, quantum channel within normal thermal noise bounds.",
            category=EvaluationCategory.CLEAN_HONEST,
            expected_verdict=DecisionVerdict.ACCEPT,
            expected_is_violation=False,
            impersonation_evidence=m13_clean,
            authorization_evidence=m14_clean,
            channel_evidence=m15_clean,
            expected_session_id=session_id,
            expected_configuration_hash=configuration_hash,
        )
    )

    # Deterministically sort scenarios by scenario_id
    scenarios.sort(key=lambda s: s.scenario_id)
    return tuple(scenarios)


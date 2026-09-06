"""Q-SHIELD — Deterministic Security Decision Engine (Milestone M12).

Converts calibrated statistical evidence (from M10/M11) and protocol-level security
indicators into a final deterministic security verdict:
    ACCEPT / SUSPICIOUS / ATTACK

Intended Pipeline:
    M9 Honest Baseline
          ↓
    M10 Statistical Comparison (StatisticalEvidence)
          ↓
    M11 Threshold Policy Evaluation (PolicyEvaluationReport)
          ↓
    M12 Deterministic Decision Engine (evaluate_security_decision)
          ↓
    DecisionResult (ACCEPT / SUSPICIOUS / ATTACK)

Scientific & Scope Boundaries:
    - Verdicts are strictly: ACCEPT, SUSPICIOUS, ATTACK.
    - Anomaly != Attack: Threshold crossings indicate deviations beyond the calibrated
      honest operating region, yielding SUSPICIOUS. They are NOT classified as ATTACK
      without confirmed explicit protocol/security violations.
    - Rule-based & Explainable: Decisions are driven by deterministic precedence and
      report canonical reason codes.
    - Strictly NO composite security scores, trust scores, or risk scores.
    - Strictly NO AI, machine learning, neural networks, or clustering.
    - Strictly NO attack-specific simulations (forgery, replay, impersonation, channel attacks
      belong to M15+).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from src.statistics.comparison import ConfigurationCompatibilityError
from src.statistics.thresholds import (
    PolicyEvaluationReport,
    ThresholdPolicy,
    evaluate_policy,
)


# ==============================================================================
# Enums
# ==============================================================================

class DecisionVerdict(str, Enum):
    """Deterministic security verdict produced by the Q-SHIELD decision engine.

    ACCEPT: Evidence satisfies configured honest baseline criteria and no protocol violations exist.
    SUSPICIOUS: Evidence indicates statistical threshold anomaly or incomplete/indeterminate state,
                without explicit deterministic proof of an attack.
    ATTACK: Explicit, deterministic protocol/security violation confirmed.
    """

    ACCEPT = "ACCEPT"
    SUSPICIOUS = "SUSPICIOUS"
    ATTACK = "ATTACK"


class DecisionReasonCode(str, Enum):
    """Stable canonical reason codes explaining why a security verdict was reached."""

    ALL_EVIDENCE_WITHIN_POLICY = "ALL_EVIDENCE_WITHIN_POLICY"
    EXPLICIT_SECURITY_VIOLATION = "EXPLICIT_SECURITY_VIOLATION"
    QUANTUM_METRIC_THRESHOLD_EXCEEDED = "QUANTUM_METRIC_THRESHOLD_EXCEEDED"
    MISSING_THRESHOLD_EVALUATION = "MISSING_THRESHOLD_EVALUATION"
    INCOMPLETE_EVIDENCE = "INCOMPLETE_EVIDENCE"
    INCOMPATIBLE_CONFIGURATION = "INCOMPATIBLE_CONFIGURATION"
    REQUIRED_METRIC_MISSING = "REQUIRED_METRIC_MISSING"
    INDETERMINATE_EVIDENCE = "INDETERMINATE_EVIDENCE"


# ==============================================================================
# Evidence Containers
# ==============================================================================

@dataclass(frozen=True)
class ProtocolSecurityEvidence:
    """Immutable protocol-level security and verification evidence.

    Encapsulates deterministic, non-statistical security indicators (e.g. replay checks,
    identity checks, authorization checks) provided by protocol layers.
    Does NOT implement attack simulators; provides the typed contract for M15+ modules.

    Attributes:
        explicit_violation: True if an explicit protocol/security violation was confirmed.
        violation_type: Canonical identifier or category of confirmed violation (e.g. 'REPLAY_NONCE_REUSED').
        violation_details: Contextual metadata explaining the violation.
        is_complete: Whether required protocol verification steps were successfully completed.
        session_id: Optional session identifier.
        nonce: Optional nonce or sequence counter.
        metadata: Contextual provenance metadata.
    """

    explicit_violation: bool = False
    violation_type: str | None = None
    violation_details: dict[str, Any] = field(default_factory=dict)
    is_complete: bool = True
    session_id: str | None = None
    nonce: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate typing and structural invariants."""
        if not isinstance(self.explicit_violation, bool):
            raise TypeError(f"explicit_violation must be bool, got {type(self.explicit_violation).__name__}.")
        if not isinstance(self.is_complete, bool):
            raise TypeError(f"is_complete must be bool, got {type(self.is_complete).__name__}.")

        if self.explicit_violation and self.violation_type is not None:
            if not isinstance(self.violation_type, str) or not self.violation_type.strip():
                raise ValueError("violation_type must be a non-empty string when explicit_violation is True.")

        if self.session_id is not None and not isinstance(self.session_id, str):
            raise TypeError(f"session_id must be str or None, got {type(self.session_id).__name__}.")
        if self.nonce is not None and not isinstance(self.nonce, str):
            raise TypeError(f"nonce must be str or None, got {type(self.nonce).__name__}.")

        object.__setattr__(self, "violation_details", dict(self.violation_details))
        object.__setattr__(self, "metadata", dict(self.metadata))


@dataclass(frozen=True)
class DecisionResult:
    """Immutable decision record produced by the Q-SHIELD decision engine.

    Scientific Principle:
        Contains deterministic verdict and explainable canonical reason codes.
        Contains strictly NO arbitrary composite security score.

    Attributes:
        verdict: DecisionVerdict (ACCEPT, SUSPICIOUS, ATTACK).
        primary_reason: Top canonical reason code driving the verdict based on precedence.
        reason_codes: Sorted, deduplicated tuple of all applicable reason codes.
        exceeded_metrics: Sorted tuple of metric names that crossed calibrated thresholds.
        exceeded_count: Total count of exceeded metric thresholds.
        is_explicit_violation: True if an explicit security violation was flagged.
        is_evidence_complete: True if all required evidence was present and validated.
        policy_id: Identifier of the M11 ThresholdPolicy evaluated (if provided).
        configuration_hash: Canonical configuration hash of the evaluation (if provided).
        threshold_report: Optional reference to the underlying PolicyEvaluationReport.
        protocol_evidence: Optional reference to the underlying ProtocolSecurityEvidence.
        timestamp: ISO 8601 UTC timestamp of decision generation.
        metadata: Contextual evaluation metadata.
    """

    verdict: DecisionVerdict
    primary_reason: str
    reason_codes: tuple[str, ...]
    exceeded_metrics: tuple[str, ...]
    exceeded_count: int
    is_explicit_violation: bool
    is_evidence_complete: bool
    policy_id: str | None = None
    configuration_hash: str | None = None
    threshold_report: PolicyEvaluationReport | None = None
    protocol_evidence: ProtocolSecurityEvidence | None = None
    timestamp: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate fields, normalize collections, and compute timestamp."""
        if not isinstance(self.verdict, DecisionVerdict):
            if isinstance(self.verdict, str):
                try:
                    object.__setattr__(self, "verdict", DecisionVerdict(self.verdict.upper().strip()))
                except ValueError as exc:
                    raise ValueError(f"Invalid DecisionVerdict: '{self.verdict}'.") from exc
            else:
                raise TypeError(f"verdict must be DecisionVerdict, got {type(self.verdict).__name__}.")

        if not isinstance(self.primary_reason, str) or not self.primary_reason.strip():
            raise ValueError("primary_reason cannot be empty.")

        # Deterministic sorting and defensive copies
        object.__setattr__(self, "reason_codes", tuple(sorted(set(self.reason_codes))))
        object.__setattr__(self, "exceeded_metrics", tuple(sorted(self.exceeded_metrics)))
        object.__setattr__(self, "metadata", dict(self.metadata))

        if not self.timestamp:
            now_iso = datetime.now(timezone.utc).isoformat()
            object.__setattr__(self, "timestamp", now_iso)

    def to_dict(self) -> dict[str, Any]:
        """Serialize decision result to a JSON-serializable dictionary."""
        return {
            "verdict": self.verdict.value,
            "primary_reason": self.primary_reason,
            "reason_codes": list(self.reason_codes),
            "exceeded_metrics": list(self.exceeded_metrics),
            "exceeded_count": self.exceeded_count,
            "is_explicit_violation": self.is_explicit_violation,
            "is_evidence_complete": self.is_evidence_complete,
            "policy_id": self.policy_id,
            "configuration_hash": self.configuration_hash,
            "threshold_report": self.threshold_report.to_dict() if self.threshold_report is not None else None,
            "protocol_evidence": asdict(self.protocol_evidence) if self.protocol_evidence is not None else None,
            "timestamp": self.timestamp,
            "metadata": dict(self.metadata),
        }


# ==============================================================================
# Decision Engine
# ==============================================================================

def evaluate_security_decision(
    threshold_report: PolicyEvaluationReport | None = None,
    protocol_evidence: ProtocolSecurityEvidence | Mapping[str, Any] | None = None,
    required_metrics: Sequence[str] | None = None,
    expected_configuration_hash: str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> DecisionResult:
    """Evaluate statistical and protocol evidence to reach a deterministic security verdict.

    Precedence Hierarchy:
        1. CONFIRMED EXPLICIT SECURITY VIOLATION -> ATTACK
           (Protocol violation explicitly verified; takes precedence over statistical state).
        2. INCOMPATIBLE OPERATING CONFIGURATION -> SUSPICIOUS
           (Evidence collected under mismatched operating conditions cannot produce ACCEPT).
        3. MISSING OR INCOMPLETE EVIDENCE -> SUSPICIOUS
           (Incomplete verification evidence cannot produce ACCEPT).
        4. STATISTICAL THRESHOLD EXCEEDANCE -> SUSPICIOUS
           (Observed metric deviated beyond calibrated operating region; anomaly != confirmed attack).
        5. ALL EVIDENCE VALID & WITHIN POLICY -> ACCEPT
           (All required metrics verified, no threshold exceeded, no protocol violations).

    Args:
        threshold_report: M11 PolicyEvaluationReport summarizing statistical threshold evaluations.
        protocol_evidence: ProtocolSecurityEvidence or mapping describing protocol-level security checks.
        required_metrics: Optional sequence of metric names that must have been evaluated.
        expected_configuration_hash: Optional canonical configuration hash to enforce compatibility.
        metadata: Optional contextual metadata dictionary.

    Returns:
        Immutable DecisionResult containing the verdict and explainable evidence trace.

    Raises:
        TypeError: If input arguments have invalid types.
        ValueError: If parameters contain malformed or empty values.
    """
    # 1. Type validation for inputs
    if threshold_report is not None and not isinstance(threshold_report, PolicyEvaluationReport):
        raise TypeError(
            f"threshold_report must be PolicyEvaluationReport or None, got {type(threshold_report).__name__}."
        )

    proto: ProtocolSecurityEvidence
    if protocol_evidence is None:
        proto = ProtocolSecurityEvidence()
    elif isinstance(protocol_evidence, ProtocolSecurityEvidence):
        proto = protocol_evidence
    elif isinstance(protocol_evidence, Mapping):
        proto = ProtocolSecurityEvidence(
            explicit_violation=bool(protocol_evidence.get("explicit_violation", False)),
            violation_type=protocol_evidence.get("violation_type"),
            violation_details=dict(protocol_evidence.get("violation_details", {})),
            is_complete=bool(protocol_evidence.get("is_complete", True)),
            session_id=protocol_evidence.get("session_id"),
            nonce=protocol_evidence.get("nonce"),
            metadata=dict(protocol_evidence.get("metadata", {})),
        )
    else:
        raise TypeError(
            f"protocol_evidence must be ProtocolSecurityEvidence, Mapping, or None, got {type(protocol_evidence).__name__}."
        )

    if required_metrics is not None:
        if not isinstance(required_metrics, Sequence) or isinstance(required_metrics, (str, bytes)):
            raise TypeError(f"required_metrics must be a Sequence of strings, got {type(required_metrics).__name__}.")
        for idx, m in enumerate(required_metrics):
            if not isinstance(m, str):
                raise TypeError(f"required_metrics element at index {idx} must be str, got {type(m).__name__}.")

    if expected_configuration_hash is not None:
        if not isinstance(expected_configuration_hash, str):
            raise TypeError(
                f"expected_configuration_hash must be str or None, got {type(expected_configuration_hash).__name__}."
            )

    # 2. Extract context from threshold report
    reasons: list[str] = []
    exceeded_metrics_list: list[str] = []
    policy_id: str | None = None
    config_hash: str | None = None

    if threshold_report is not None:
        policy_id = threshold_report.policy_id
        config_hash = threshold_report.baseline_configuration_hash
        exceeded_metrics_list = list(threshold_report.exceeded_metrics)

    # 3. Apply Deterministic Precedence Hierarchy

    # PRECEDENCE 1: Confirmed Explicit Security Violation -> ATTACK
    if proto.explicit_violation:
        primary_reason = DecisionReasonCode.EXPLICIT_SECURITY_VIOLATION.value
        reasons.append(primary_reason)
        if proto.violation_type:
            reasons.append(proto.violation_type)
        if threshold_report is not None and threshold_report.any_exceeded:
            reasons.append(DecisionReasonCode.QUANTUM_METRIC_THRESHOLD_EXCEEDED.value)

        decision_meta = dict(metadata) if metadata is not None else {}
        return DecisionResult(
            verdict=DecisionVerdict.ATTACK,
            primary_reason=primary_reason,
            reason_codes=tuple(reasons),
            exceeded_metrics=tuple(exceeded_metrics_list),
            exceeded_count=len(exceeded_metrics_list),
            is_explicit_violation=True,
            is_evidence_complete=proto.is_complete and (threshold_report is not None),
            policy_id=policy_id,
            configuration_hash=config_hash,
            threshold_report=threshold_report,
            protocol_evidence=proto,
            metadata=decision_meta,
        )

    # PRECEDENCE 2: Incompatible Configuration -> SUSPICIOUS
    if expected_configuration_hash is not None and config_hash is not None:
        if config_hash != expected_configuration_hash:
            primary_reason = DecisionReasonCode.INCOMPATIBLE_CONFIGURATION.value
            reasons.append(primary_reason)
            if threshold_report is not None and threshold_report.any_exceeded:
                reasons.append(DecisionReasonCode.QUANTUM_METRIC_THRESHOLD_EXCEEDED.value)

            decision_meta = dict(metadata) if metadata is not None else {}
            decision_meta["configuration_mismatch"] = {
                "expected": expected_configuration_hash,
                "observed": config_hash,
            }
            return DecisionResult(
                verdict=DecisionVerdict.SUSPICIOUS,
                primary_reason=primary_reason,
                reason_codes=tuple(reasons),
                exceeded_metrics=tuple(exceeded_metrics_list),
                exceeded_count=len(exceeded_metrics_list),
                is_explicit_violation=False,
                is_evidence_complete=False,
                policy_id=policy_id,
                configuration_hash=config_hash,
                threshold_report=threshold_report,
                protocol_evidence=proto,
                metadata=decision_meta,
            )

    # PRECEDENCE 3: Missing or Incomplete Evidence -> SUSPICIOUS
    if threshold_report is None:
        primary_reason = DecisionReasonCode.MISSING_THRESHOLD_EVALUATION.value
        reasons.extend([primary_reason, DecisionReasonCode.INCOMPLETE_EVIDENCE.value])
        decision_meta = dict(metadata) if metadata is not None else {}
        return DecisionResult(
            verdict=DecisionVerdict.SUSPICIOUS,
            primary_reason=primary_reason,
            reason_codes=tuple(reasons),
            exceeded_metrics=(),
            exceeded_count=0,
            is_explicit_violation=False,
            is_evidence_complete=False,
            policy_id=None,
            configuration_hash=None,
            threshold_report=None,
            protocol_evidence=proto,
            metadata=decision_meta,
        )

    if threshold_report.total_metrics_evaluated == 0:
        primary_reason = DecisionReasonCode.INCOMPLETE_EVIDENCE.value
        reasons.append(primary_reason)
        decision_meta = dict(metadata) if metadata is not None else {}
        return DecisionResult(
            verdict=DecisionVerdict.SUSPICIOUS,
            primary_reason=primary_reason,
            reason_codes=tuple(reasons),
            exceeded_metrics=(),
            exceeded_count=0,
            is_explicit_violation=False,
            is_evidence_complete=False,
            policy_id=policy_id,
            configuration_hash=config_hash,
            threshold_report=threshold_report,
            protocol_evidence=proto,
            metadata=decision_meta,
        )

    if not proto.is_complete:
        primary_reason = DecisionReasonCode.INCOMPLETE_EVIDENCE.value
        reasons.append(primary_reason)
        if threshold_report.any_exceeded:
            reasons.append(DecisionReasonCode.QUANTUM_METRIC_THRESHOLD_EXCEEDED.value)

        decision_meta = dict(metadata) if metadata is not None else {}
        return DecisionResult(
            verdict=DecisionVerdict.SUSPICIOUS,
            primary_reason=primary_reason,
            reason_codes=tuple(reasons),
            exceeded_metrics=tuple(exceeded_metrics_list),
            exceeded_count=len(exceeded_metrics_list),
            is_explicit_violation=False,
            is_evidence_complete=False,
            policy_id=policy_id,
            configuration_hash=config_hash,
            threshold_report=threshold_report,
            protocol_evidence=proto,
            metadata=decision_meta,
        )

    if required_metrics is not None:
        missing_req = [m for m in required_metrics if m not in threshold_report.metric_evaluations]
        if missing_req:
            primary_reason = DecisionReasonCode.REQUIRED_METRIC_MISSING.value
            reasons.extend([primary_reason, DecisionReasonCode.INCOMPLETE_EVIDENCE.value])
            if threshold_report.any_exceeded:
                reasons.append(DecisionReasonCode.QUANTUM_METRIC_THRESHOLD_EXCEEDED.value)

            decision_meta = dict(metadata) if metadata is not None else {}
            decision_meta["missing_required_metrics"] = missing_req
            return DecisionResult(
                verdict=DecisionVerdict.SUSPICIOUS,
                primary_reason=primary_reason,
                reason_codes=tuple(reasons),
                exceeded_metrics=tuple(exceeded_metrics_list),
                exceeded_count=len(exceeded_metrics_list),
                is_explicit_violation=False,
                is_evidence_complete=False,
                policy_id=policy_id,
                configuration_hash=config_hash,
                threshold_report=threshold_report,
                protocol_evidence=proto,
                metadata=decision_meta,
            )

    # PRECEDENCE 4: Statistical Threshold Exceedance (Quantum / Channel Anomaly) -> SUSPICIOUS
    # Scientific Principle: Anomaly != Confirmed Attack. Threshold exceedance without explicit violation
    # indicates that the observation is outside the calibrated honest region, producing SUSPICIOUS.
    if threshold_report.any_exceeded:
        primary_reason = DecisionReasonCode.QUANTUM_METRIC_THRESHOLD_EXCEEDED.value
        reasons.append(primary_reason)
        decision_meta = dict(metadata) if metadata is not None else {}
        return DecisionResult(
            verdict=DecisionVerdict.SUSPICIOUS,
            primary_reason=primary_reason,
            reason_codes=tuple(reasons),
            exceeded_metrics=tuple(exceeded_metrics_list),
            exceeded_count=len(exceeded_metrics_list),
            is_explicit_violation=False,
            is_evidence_complete=True,
            policy_id=policy_id,
            configuration_hash=config_hash,
            threshold_report=threshold_report,
            protocol_evidence=proto,
            metadata=decision_meta,
        )

    # PRECEDENCE 5: All Evidence Valid & Within Policy -> ACCEPT
    primary_reason = DecisionReasonCode.ALL_EVIDENCE_WITHIN_POLICY.value
    reasons.append(primary_reason)
    decision_meta = dict(metadata) if metadata is not None else {}

    return DecisionResult(
        verdict=DecisionVerdict.ACCEPT,
        primary_reason=primary_reason,
        reason_codes=tuple(reasons),
        exceeded_metrics=(),
        exceeded_count=0,
        is_explicit_violation=False,
        is_evidence_complete=True,
        policy_id=policy_id,
        configuration_hash=config_hash,
        threshold_report=threshold_report,
        protocol_evidence=proto,
        metadata=decision_meta,
    )


def evaluate_decision_from_evidence(
    evidence_or_obs: Any,
    policy: ThresholdPolicy,
    protocol_evidence: ProtocolSecurityEvidence | Mapping[str, Any] | None = None,
    required_metrics: Sequence[str] | None = None,
    strict_hash: bool = True,
    atol: float = 1e-9,
    metadata: Mapping[str, Any] | None = None,
) -> DecisionResult:
    """Evaluate a final security decision directly from M10 StatisticalEvidence or VerificationObservation.

    Convenience adapter connecting M10 -> M11 -> M12:
        1. Evaluates evidence_or_obs against policy via M11 evaluate_policy().
        2. Handles configuration mismatch gracefully, producing SUSPICIOUS if strict_hash fails.
        3. Passes the resulting PolicyEvaluationReport to M12 evaluate_security_decision().

    Args:
        evidence_or_obs: M10 StatisticalEvidence, VerificationObservation, or Mapping.
        policy: Calibrated M11 ThresholdPolicy.
        protocol_evidence: Optional protocol-level security checks.
        required_metrics: Optional sequence of required metric names.
        strict_hash: If True, enforces exact configuration hash matching.
        atol: Numerical boundary tolerance for threshold evaluations. Default: 1e-9.
        metadata: Optional evaluation metadata.

    Returns:
        Immutable DecisionResult.
    """
    if not isinstance(policy, ThresholdPolicy):
        raise TypeError(f"policy must be ThresholdPolicy, got {type(policy).__name__}.")

    try:
        threshold_report = evaluate_policy(
            evidence_or_obs=evidence_or_obs,
            policy=policy,
            strict_hash=strict_hash,
            atol=atol,
        )
    except ConfigurationCompatibilityError:
        # Incompatible configuration cannot produce ACCEPT; maps deterministically to SUSPICIOUS
        return evaluate_security_decision(
            threshold_report=None,
            protocol_evidence=protocol_evidence,
            required_metrics=required_metrics,
            expected_configuration_hash=policy.baseline_configuration_hash,
            metadata={"configuration_error": "ConfigurationCompatibilityError caught during evaluation."},
        )

    return evaluate_security_decision(
        threshold_report=threshold_report,
        protocol_evidence=protocol_evidence,
        required_metrics=required_metrics,
        expected_configuration_hash=policy.baseline_configuration_hash,
        metadata=metadata,
    )

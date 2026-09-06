"""Q-SHIELD — Deterministic Quantum Channel Attack Detection (Milestone M15).

Evaluates whether observed quantum communication behavior (QBER, teleportation fidelity,
Bell correlations, Born probabilities/TVD, Pauli expectations) provides evidence of a
channel-level security anomaly, disturbance, or explicit protocol violation.

Architectural Placement:
    Quantum Protocol (M1–M7)
           ↓
    Measurements / Telemetry
           ↓
    M8 Noise + M9 Honest Baseline
           ↓
    M10 Statistical Comparison (StatisticalEvidence)
           ↓
    M11 Threshold Policy Evaluation (PolicyEvaluationReport)
           ↓
    M15 Quantum Channel Attack Detection (ChannelSecurityEvidence)  ← THIS MODULE
           ↓
    M12 Deterministic Decision Engine (ACCEPT / SUSPICIOUS / ATTACK)

Scientific & Scope Boundaries:
    - M15 answers: "Does the observed quantum communication behavior provide evidence
      of a channel-level security anomaly or disturbance?"
    - M15 does NOT answer: "Who attacked?" (Strictly owned by M13 Impersonation Detection).
    - M15 does NOT answer: "Was this participant authorized?" (Strictly owned by M14).
    - M15 does NOT produce the final security verdict (M12 remains sole decision authority).
    - Statistical Anomaly != Proven Attacker: Threshold crossings indicate channel
      anomalies (e.g. noise, drift, disturbance, interference), NOT proof of a specific adversary.
    - Zero Duplicate Calculations: Consumes M10/M11 evidence without recalculating statistics.
    - Zero Composite Scores: Strictly NO risk scores, trust scores, or composite scalar collapsing.
    - Zero Machine Learning / AI: Rule-based, deterministic, categorical evidence.
    - Zero Replay Detection: Nonce tracking and replay caches belong outside M15.
    - Strict Immutability & Secret Leakage Guards: Frozen dataclasses and defensive key-name filtering.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import math
from typing import Any

from src.detection.decision import (
    DecisionResult,
    ProtocolSecurityEvidence,
    evaluate_security_decision,
)
from src.statistics.comparison import (
    ConfigurationCompatibilityError,
    StatisticalEvidence,
)
from src.statistics.thresholds import (
    PolicyEvaluationReport,
    ThresholdPolicy,
    evaluate_policy,
)


# Forbidden secret key patterns to prevent secret leakage into evidence containers.
# Defensive key-name guard: rejects obvious secret material; not a complete memory sanitizer.
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
    elif isinstance(val, list):
        return [_deep_freeze_val(x) for x in val]
    elif isinstance(val, tuple):
        return tuple(_deep_freeze_val(x) for x in val)
    elif isinstance(val, set):
        return set(val)
    return val


def _deep_freeze_dict(d: Mapping[str, Any]) -> dict[str, Any]:
    """Recursively copy nested dictionaries and collections to prevent indirect mutation."""
    return {str(k): _deep_freeze_val(v) for k, v in d.items()}


def _check_for_secret_leakage(d: Mapping[str, Any], container_name: str) -> None:
    """Defensive key-name guard: inspect dictionary and nested structures for obvious secret keywords.

    Note: This is a defensive key-name-based guard against accidental credential/secret logging,
    not a mathematically complete memory sanitization guarantee.
    """
    for key, val in d.items():
        key_lower = str(key).lower()
        for forbidden in _FORBIDDEN_SECRET_SUBSTRINGS:
            if forbidden in key_lower:
                raise ValueError(
                    f"Sensitive secret keyword '{forbidden}' detected in {container_name} key '{key}'. "
                    "Raw credentials or cryptographic secrets must never be placed in security evidence."
                )
        if isinstance(val, Mapping):
            _check_for_secret_leakage(val, f"{container_name}['{key}']")
        elif isinstance(val, (list, tuple)):
            for idx, item in enumerate(val):
                if isinstance(item, Mapping):
                    _check_for_secret_leakage(item, f"{container_name}['{key}'][{idx}]")


# ==============================================================================
# Enums
# ==============================================================================

class ChannelEvidenceStatus(str, Enum):
    """Categorical status of quantum channel security evaluation.

    CLEAN: All required channel evidence present, context valid, no thresholds exceeded.
    ANOMALOUS: Required evidence present, context valid, one or more channel thresholds exceeded.
    SECURITY_VIOLATION: Confirmed channel security violation (explicit protocol/channel rule breach).
    INCOMPLETE: Required channel evidence or threshold report is missing or incomplete.
    INCOMPATIBLE_CONTEXT: Configuration hash or session identifier does not match expected context.
    CONFLICTING: Evidence contains contradictory assertions (e.g. conflicting reports or incompatible claims).
    """

    CLEAN = "CLEAN"
    ANOMALOUS = "ANOMALOUS"
    SECURITY_VIOLATION = "SECURITY_VIOLATION"
    INCOMPLETE = "INCOMPLETE"
    INCOMPATIBLE_CONTEXT = "INCOMPATIBLE_CONTEXT"
    CONFLICTING = "CONFLICTING"


class ChannelReasonCode(str, Enum):
    """Canonical machine-readable reason codes explaining channel security findings."""

    CHANNEL_CLEAN = "CHANNEL_CLEAN"
    QBER_THRESHOLD_EXCEEDED = "QBER_THRESHOLD_EXCEEDED"
    BELL_CORRELATION_ANOMALY = "BELL_CORRELATION_ANOMALY"
    TELEPORTATION_FIDELITY_ANOMALY = "TELEPORTATION_FIDELITY_ANOMALY"
    DISTRIBUTION_TVD_THRESHOLD_EXCEEDED = "DISTRIBUTION_TVD_THRESHOLD_EXCEEDED"
    PAULI_EXPECTATION_ANOMALY = "PAULI_EXPECTATION_ANOMALY"
    CHANNEL_STATISTICAL_ANOMALY = "CHANNEL_STATISTICAL_ANOMALY"
    MULTI_METRIC_CHANNEL_DISTURBANCE = "MULTI_METRIC_CHANNEL_DISTURBANCE"
    QUANTUM_CHANNEL_SECURITY_VIOLATION = "QUANTUM_CHANNEL_SECURITY_VIOLATION"
    MISSING_CHANNEL_EVIDENCE = "MISSING_CHANNEL_EVIDENCE"
    INCOMPLETE_CHANNEL_EVIDENCE = "INCOMPLETE_CHANNEL_EVIDENCE"
    CHANNEL_SESSION_MISMATCH = "CHANNEL_SESSION_MISMATCH"
    CHANNEL_CONFIGURATION_MISMATCH = "CHANNEL_CONFIGURATION_MISMATCH"
    CHANNEL_CONTEXT_MISMATCH = "CHANNEL_CONTEXT_MISMATCH"
    CONFLICTING_CHANNEL_EVIDENCE = "CONFLICTING_CHANNEL_EVIDENCE"
    UNSUPPORTED_CHANNEL_EVIDENCE = "UNSUPPORTED_CHANNEL_EVIDENCE"


# ==============================================================================
# Evidence Container
# ==============================================================================

@dataclass(frozen=True)
class ChannelSecurityEvidence:
    """Immutable quantum channel security evidence container produced by M15.

    Encapsulates channel anomaly evaluation findings derived from M10 statistical
    comparisons and M11 threshold policy evaluations.

    Attributes:
        status: ChannelEvidenceStatus categorical verdict.
        primary_reason: ChannelReasonCode indicating the primary finding by deterministic precedence.
        reason_codes: Sorted, deduplicated tuple of all applicable ChannelReasonCode values.
        is_anomalous: True if channel behavior deviates beyond calibrated thresholds.
        is_explicit_violation: True if confirmed as an explicit protocol channel security violation.
        is_evidence_complete: True if required telemetry and threshold reports were complete.
        violation_type: Canonical violation identifier string when is_explicit_violation is True.
        exceeded_metrics: Sorted tuple of metric names that crossed thresholds.
        exceeded_count: Total count of exceeded metric thresholds.
        session_id: Optional session identifier.
        configuration_hash: Canonical SHA-256 baseline configuration hash.
        policy_id: Identifier of the M11 ThresholdPolicy evaluated.
        threshold_report: Optional reference to the underlying M11 PolicyEvaluationReport.
        statistical_evidence: Optional reference to the underlying M10 StatisticalEvidence.
        timestamp: ISO 8601 UTC timestamp of evidence evaluation.
        metadata: Contextual provenance metadata dictionary.
    """

    status: ChannelEvidenceStatus
    primary_reason: ChannelReasonCode
    reason_codes: tuple[ChannelReasonCode, ...]
    is_anomalous: bool
    is_explicit_violation: bool
    is_evidence_complete: bool
    violation_type: str | None = None
    exceeded_metrics: tuple[str, ...] = ()
    exceeded_count: int = 0
    session_id: str | None = None
    configuration_hash: str | None = None
    policy_id: str | None = None
    threshold_report: PolicyEvaluationReport | None = None
    statistical_evidence: StatisticalEvidence | None = None
    timestamp: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate fields, enforce immutability, and apply defensive safeguards."""
        # Validate status
        if not isinstance(self.status, ChannelEvidenceStatus):
            if isinstance(self.status, str):
                try:
                    object.__setattr__(self, "status", ChannelEvidenceStatus(self.status.upper().strip()))
                except ValueError as exc:
                    raise ValueError(f"Invalid ChannelEvidenceStatus: '{self.status}'.") from exc
            else:
                raise TypeError(f"status must be ChannelEvidenceStatus, got {type(self.status).__name__}.")

        # Validate primary_reason
        if not isinstance(self.primary_reason, ChannelReasonCode):
            if isinstance(self.primary_reason, str):
                try:
                    object.__setattr__(self, "primary_reason", ChannelReasonCode(self.primary_reason.upper().strip()))
                except ValueError as exc:
                    raise ValueError(f"Invalid ChannelReasonCode: '{self.primary_reason}'.") from exc
            else:
                raise TypeError(f"primary_reason must be ChannelReasonCode, got {type(self.primary_reason).__name__}.")

        # Validate boolean flags
        for name, val in [
            ("is_anomalous", self.is_anomalous),
            ("is_explicit_violation", self.is_explicit_violation),
            ("is_evidence_complete", self.is_evidence_complete),
        ]:
            if not isinstance(val, bool):
                raise TypeError(f"{name} must be bool, got {type(val).__name__}.")

        # Validate violation_type
        if self.is_explicit_violation:
            if not self.violation_type or not isinstance(self.violation_type, str) or not self.violation_type.strip():
                raise ValueError("violation_type must be a non-empty string when is_explicit_violation is True.")
        elif self.violation_type is not None and not isinstance(self.violation_type, str):
            raise TypeError(f"violation_type must be str or None, got {type(self.violation_type).__name__}.")

        # Validate reason_codes
        if not isinstance(self.reason_codes, (Sequence, tuple)):
            raise TypeError(f"reason_codes must be a sequence of ChannelReasonCode, got {type(self.reason_codes).__name__}.")
        norm_reasons: list[ChannelReasonCode] = []
        for r in self.reason_codes:
            if isinstance(r, ChannelReasonCode):
                norm_reasons.append(r)
            elif isinstance(r, str):
                norm_reasons.append(ChannelReasonCode(r.upper().strip()))
            else:
                raise TypeError(f"reason_codes elements must be ChannelReasonCode, got {type(r).__name__}.")
        object.__setattr__(self, "reason_codes", tuple(sorted(set(norm_reasons), key=lambda x: x.value)))

        # Validate exceeded_count & exceeded_metrics
        if not isinstance(self.exceeded_count, int) or isinstance(self.exceeded_count, bool) or self.exceeded_count < 0:
            raise TypeError(f"exceeded_count must be non-negative int, got {self.exceeded_count}.")
        if not isinstance(self.exceeded_metrics, (Sequence, tuple)):
            raise TypeError(f"exceeded_metrics must be a sequence of str, got {type(self.exceeded_metrics).__name__}.")
        for m in self.exceeded_metrics:
            if not isinstance(m, str):
                raise TypeError(f"exceeded_metrics element must be str, got {type(m).__name__}.")
            if not m.strip():
                raise ValueError("exceeded_metrics element cannot be empty or whitespace.")
        dedup_exceeded = tuple(sorted(set(self.exceeded_metrics)))
        object.__setattr__(self, "exceeded_metrics", dedup_exceeded)
        if self.exceeded_count != len(dedup_exceeded):
            raise ValueError(
                f"exceeded_count must equal len(exceeded_metrics), got {self.exceeded_count} and {len(dedup_exceeded)}."
            )

        # Context fields
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
        if self.policy_id is not None:
            if not isinstance(self.policy_id, str):
                raise TypeError(f"policy_id must be str or None, got {type(self.policy_id).__name__}.")
            if not self.policy_id.strip():
                raise ValueError("policy_id cannot be empty or whitespace when provided.")

        if self.threshold_report is not None and not isinstance(self.threshold_report, PolicyEvaluationReport):
            raise TypeError(f"threshold_report must be PolicyEvaluationReport or None, got {type(self.threshold_report).__name__}.")
        if self.statistical_evidence is not None and not isinstance(self.statistical_evidence, StatisticalEvidence):
            raise TypeError(f"statistical_evidence must be StatisticalEvidence or None, got {type(self.statistical_evidence).__name__}.")

        # Secret checking and defensive deep copy of metadata
        _check_for_secret_leakage(self.metadata, "ChannelSecurityEvidence.metadata")
        object.__setattr__(self, "metadata", _deep_freeze_dict(self.metadata))

        if not self.timestamp:
            object.__setattr__(self, "timestamp", datetime.now(timezone.utc).isoformat())

    def to_protocol_security_evidence(self) -> ProtocolSecurityEvidence:
        """Bridge M15 channel security evidence into M12 ProtocolSecurityEvidence.

        Mapping Rules:
            - SECURITY_VIOLATION -> explicit_violation=True, violation_type="QUANTUM_CHANNEL_SECURITY_VIOLATION",
              is_complete=True. (M12 produces ATTACK).
            - ANOMALOUS -> explicit_violation=False, is_complete=True.
              (M12 produces SUSPICIOUS via threshold report or context).
            - INCOMPLETE / INCOMPATIBLE_CONTEXT / CONFLICTING -> explicit_violation=False, is_complete=False.
              (M12 produces SUSPICIOUS).
            - CLEAN -> explicit_violation=False, is_complete=True.
              (M12 produces ACCEPT assuming clean threshold report).
        """
        violation_type_str: str | None = None
        if self.is_explicit_violation:
            violation_type_str = self.violation_type or "QUANTUM_CHANNEL_SECURITY_VIOLATION"

        violation_details: dict[str, Any] = {
            "status": self.status.value,
            "primary_reason": self.primary_reason.value,
            "reason_codes": [r.value for r in self.reason_codes],
            "exceeded_metrics": list(self.exceeded_metrics),
            "exceeded_count": self.exceeded_count,
            "is_anomalous": self.is_anomalous,
            "policy_id": self.policy_id,
            "configuration_hash": self.configuration_hash,
        }

        return ProtocolSecurityEvidence(
            explicit_violation=self.is_explicit_violation,
            violation_type=violation_type_str,
            violation_details=violation_details,
            is_complete=self.is_evidence_complete,
            session_id=self.session_id,
            metadata=dict(self.metadata),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize evidence to a JSON-serializable dictionary."""
        return {
            "status": self.status.value,
            "primary_reason": self.primary_reason.value,
            "reason_codes": [r.value for r in self.reason_codes],
            "is_anomalous": self.is_anomalous,
            "is_explicit_violation": self.is_explicit_violation,
            "is_evidence_complete": self.is_evidence_complete,
            "violation_type": self.violation_type,
            "exceeded_metrics": list(self.exceeded_metrics),
            "exceeded_count": self.exceeded_count,
            "session_id": self.session_id,
            "configuration_hash": self.configuration_hash,
            "policy_id": self.policy_id,
            "threshold_report": self.threshold_report.to_dict() if self.threshold_report is not None else None,
            "statistical_evidence": self.statistical_evidence.to_dict() if self.statistical_evidence is not None else None,
            "timestamp": self.timestamp,
            "metadata": dict(self.metadata),
        }


# ==============================================================================
# Detection Engine
# ==============================================================================

# Deterministic Precedence for Primary Reason Selection
_REASON_PRECEDENCE: tuple[ChannelReasonCode, ...] = (
    ChannelReasonCode.QUANTUM_CHANNEL_SECURITY_VIOLATION,
    ChannelReasonCode.CONFLICTING_CHANNEL_EVIDENCE,
    ChannelReasonCode.CHANNEL_CONFIGURATION_MISMATCH,
    ChannelReasonCode.CHANNEL_SESSION_MISMATCH,
    ChannelReasonCode.CHANNEL_CONTEXT_MISMATCH,
    ChannelReasonCode.MISSING_CHANNEL_EVIDENCE,
    ChannelReasonCode.INCOMPLETE_CHANNEL_EVIDENCE,
    ChannelReasonCode.MULTI_METRIC_CHANNEL_DISTURBANCE,
    ChannelReasonCode.QBER_THRESHOLD_EXCEEDED,
    ChannelReasonCode.TELEPORTATION_FIDELITY_ANOMALY,
    ChannelReasonCode.BELL_CORRELATION_ANOMALY,
    ChannelReasonCode.DISTRIBUTION_TVD_THRESHOLD_EXCEEDED,
    ChannelReasonCode.PAULI_EXPECTATION_ANOMALY,
    ChannelReasonCode.CHANNEL_STATISTICAL_ANOMALY,
    ChannelReasonCode.CHANNEL_CLEAN,
    ChannelReasonCode.UNSUPPORTED_CHANNEL_EVIDENCE,
)


def _select_primary_reason(reasons: Sequence[ChannelReasonCode]) -> ChannelReasonCode:
    """Select top primary reason code following strict deterministic precedence."""
    for candidate in _REASON_PRECEDENCE:
        if candidate in reasons:
            return candidate
    return reasons[0] if reasons else ChannelReasonCode.CHANNEL_CLEAN


def detect_channel_anomalies(
    threshold_report: PolicyEvaluationReport | None = None,
    statistical_evidence: StatisticalEvidence | None = None,
    threshold_policy: ThresholdPolicy | None = None,
    required_metrics: Sequence[str] | None = None,
    session_id: str | None = None,
    expected_session_id: str | None = None,
    expected_configuration_hash: str | None = None,
    explicit_violation: bool = False,
    violation_type: str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> ChannelSecurityEvidence:
    """Evaluate quantum channel telemetry and threshold evaluations for anomalies or violations.

    Consumes M10 StatisticalEvidence and M11 PolicyEvaluationReport without recalculating
    means, variances, z-scores, TVD, or empirical thresholds.

    Precedence & Evaluation Workflow:
        1. Defensive typing and secret leakage validation.
        2. Context & Configuration Binding: Enforce session and configuration hash compatibility.
        3. Threshold Evaluation: If threshold_report is absent but statistical_evidence and
           threshold_policy are provided, delegates to M11 evaluate_policy(). Gracefully traps
           ConfigurationCompatibilityError as conflicting evidence.
        4. Incompleteness Detection: Missing or empty threshold evaluations yield INCOMPLETE.
        5. Metric Disturbance Categorization (NO "First Error Wins"):
           - Inspects ALL exceeded metrics and accumulates all applicable reason codes.
           - Emits MULTI_METRIC_CHANNEL_DISTURBANCE if multiple independent signals are anomalous.
        6. Explicit Violation Enforcement: If an explicit protocol security violation is confirmed,
           yields SECURITY_VIOLATION with explicit_violation=True.
        7. Clean Channel: If all required metrics present, context valid, and no threshold crossed,
           yields CLEAN.

    Args:
        threshold_report: Pre-evaluated M11 PolicyEvaluationReport.
        statistical_evidence: Pre-evaluated M10 StatisticalEvidence.
        threshold_policy: M11 ThresholdPolicy to evaluate against statistical_evidence if report is omitted.
        required_metrics: Optional sequence of metric names that must have been evaluated.
        session_id: Optional session identifier for this evaluation.
        expected_session_id: Optional expected session identifier to enforce compatibility.
        expected_configuration_hash: Optional canonical baseline configuration hash to enforce binding.
        explicit_violation: True if an explicit channel security violation is confirmed.
        violation_type: Canonical identifier string when explicit_violation is True.
        metadata: Optional contextual metadata dictionary.

    Returns:
        Immutable ChannelSecurityEvidence container.

    Raises:
        TypeError: If input parameters have invalid types.
        ValueError: If parameters contain forbidden secret keys or empty strings where invalid.
    """
    # 1. Secret leakage and input type validations
    meta_dict = dict(metadata) if metadata is not None else {}
    _check_for_secret_leakage(meta_dict, "metadata")

    if not isinstance(explicit_violation, bool):
        raise TypeError(f"explicit_violation must be bool, got {type(explicit_violation).__name__}.")

    if explicit_violation:
        if violation_type is None:
            violation_type = "QUANTUM_CHANNEL_SECURITY_VIOLATION"
        elif not isinstance(violation_type, str) or not violation_type.strip():
            raise ValueError("violation_type must be a non-empty string when explicit_violation is True.")
    elif violation_type is not None and not isinstance(violation_type, str):
        raise TypeError(f"violation_type must be str or None, got {type(violation_type).__name__}.")

    if session_id is not None:
        if not isinstance(session_id, str):
            raise TypeError(f"session_id must be str or None, got {type(session_id).__name__}.")
        if not session_id.strip():
            raise ValueError("session_id cannot be empty or whitespace.")

    if expected_session_id is not None:
        if not isinstance(expected_session_id, str):
            raise TypeError(f"expected_session_id must be str or None, got {type(expected_session_id).__name__}.")
        if not expected_session_id.strip():
            raise ValueError("expected_session_id cannot be empty or whitespace.")

    if expected_configuration_hash is not None:
        if not isinstance(expected_configuration_hash, str):
            raise TypeError(f"expected_configuration_hash must be str or None, got {type(expected_configuration_hash).__name__}.")
        if not expected_configuration_hash.strip():
            raise ValueError("expected_configuration_hash cannot be empty or whitespace.")

    if required_metrics is not None:
        if not isinstance(required_metrics, Sequence) or isinstance(required_metrics, (str, bytes)):
            raise TypeError(f"required_metrics must be a Sequence of strings, got {type(required_metrics).__name__}.")
        for idx, m in enumerate(required_metrics):
            if not isinstance(m, str):
                raise TypeError(f"required_metrics element at index {idx} must be str, got {type(m).__name__}.")
            if not m.strip():
                raise ValueError(f"required_metrics element at index {idx} cannot be empty or whitespace.")

    if threshold_report is not None and not isinstance(threshold_report, PolicyEvaluationReport):
        raise TypeError(f"threshold_report must be PolicyEvaluationReport or None, got {type(threshold_report).__name__}.")
    if statistical_evidence is not None and not isinstance(statistical_evidence, StatisticalEvidence):
        raise TypeError(f"statistical_evidence must be StatisticalEvidence or None, got {type(statistical_evidence).__name__}.")
    if threshold_policy is not None and not isinstance(threshold_policy, ThresholdPolicy):
        raise TypeError(f"threshold_policy must be ThresholdPolicy or None, got {type(threshold_policy).__name__}.")

    # 2. Delegate to M11 evaluate_policy if report missing but evidence & policy provided
    eval_report = threshold_report
    has_conflicting_evidence = False

    if eval_report is None and statistical_evidence is not None and threshold_policy is not None:
        try:
            eval_report = evaluate_policy(statistical_evidence, threshold_policy)
        except ConfigurationCompatibilityError:
            has_conflicting_evidence = True

    # 3. Detect conflicting lower-layer assertions
    if threshold_report is not None and threshold_policy is not None:
        if threshold_report.policy_id != threshold_policy.policy_id:
            has_conflicting_evidence = True
        if threshold_report.baseline_configuration_hash != threshold_policy.baseline_configuration_hash:
            has_conflicting_evidence = True

    if eval_report is not None and statistical_evidence is not None:
        if eval_report.baseline_configuration_hash != statistical_evidence.baseline_configuration_hash:
            has_conflicting_evidence = True

    # 4. Resolve session and configuration provenance
    report_session = eval_report.metadata.get("session_id") if eval_report is not None else None
    stat_session = statistical_evidence.metadata.get("session_id") if statistical_evidence is not None else None

    # Detect mutually contradictory session assertions
    if session_id is not None and report_session is not None and session_id != report_session:
        has_conflicting_evidence = True
    if session_id is not None and stat_session is not None and session_id != stat_session:
        has_conflicting_evidence = True
    if report_session is not None and stat_session is not None and report_session != stat_session:
        has_conflicting_evidence = True

    eff_session_id = session_id or report_session or stat_session

    eff_config_hash: str | None = None
    policy_id: str | None = None
    if eval_report is not None:
        eff_config_hash = eval_report.baseline_configuration_hash
        policy_id = eval_report.policy_id
    elif threshold_policy is not None:
        eff_config_hash = threshold_policy.baseline_configuration_hash
        policy_id = threshold_policy.policy_id
    elif statistical_evidence is not None:
        eff_config_hash = statistical_evidence.baseline_configuration_hash

    # Context compatibility checks
    is_session_mismatch = False
    if expected_session_id is not None:
        if eff_session_id is None or eff_session_id != expected_session_id:
            is_session_mismatch = True

    is_config_mismatch = False
    if expected_configuration_hash is not None:
        if eff_config_hash is None or eff_config_hash != expected_configuration_hash:
            is_config_mismatch = True

    # 5. Check completeness
    is_incomplete = False
    missing_report = eval_report is None
    missing_required: list[str] = []

    if eval_report is not None:
        if eval_report.total_metrics_evaluated == 0:
            is_incomplete = True
        if required_metrics is not None:
            for req_m in required_metrics:
                if req_m not in eval_report.metric_evaluations:
                    missing_required.append(req_m)
            if missing_required:
                is_incomplete = True
                meta_dict["missing_required_metrics"] = missing_required
    else:
        is_incomplete = True

    # 6. Accumulate anomaly reasons across all evaluated metrics (NO "First Error Wins")
    reasons: list[ChannelReasonCode] = []
    exceeded_metrics_list: list[str] = []
    signal_categories: set[str] = set()

    if eval_report is not None:
        exceeded_metrics_list = list(eval_report.exceeded_metrics)
        for m_name in exceeded_metrics_list:
            m_lower = m_name.lower().strip()
            if m_lower.startswith("qber") or ":qber" in m_lower:
                reasons.append(ChannelReasonCode.QBER_THRESHOLD_EXCEEDED)
                signal_categories.add("QBER")
            elif m_lower.startswith("fidelity") or ":fidelity" in m_lower:
                reasons.append(ChannelReasonCode.TELEPORTATION_FIDELITY_ANOMALY)
                signal_categories.add("FIDELITY")
            elif m_lower.startswith("bell") or "bell_" in m_lower or "chsh" in m_lower:
                reasons.append(ChannelReasonCode.BELL_CORRELATION_ANOMALY)
                signal_categories.add("BELL")
            elif (
                m_lower.startswith("tvd")
                or m_lower.startswith("prob_dev")
                or m_lower.startswith("probabilities")
                or m_lower.startswith("dist_")
                or m_lower.startswith("ks_")
            ):
                reasons.append(ChannelReasonCode.DISTRIBUTION_TVD_THRESHOLD_EXCEEDED)
                signal_categories.add("DISTRIBUTION")
            elif m_lower.startswith("pauli") or m_lower.startswith("exp_"):
                reasons.append(ChannelReasonCode.PAULI_EXPECTATION_ANOMALY)
                signal_categories.add("PAULI")
            else:
                reasons.append(ChannelReasonCode.CHANNEL_STATISTICAL_ANOMALY)
                signal_categories.add("OTHER")

        # Multi-signal disturbance detection
        if len(signal_categories) >= 2:
            reasons.append(ChannelReasonCode.MULTI_METRIC_CHANNEL_DISTURBANCE)

    # 7. Apply Deterministic State Precedence
    status: ChannelEvidenceStatus
    is_anomalous: bool = len(exceeded_metrics_list) > 0
    is_evidence_complete: bool = True

    if explicit_violation:
        status = ChannelEvidenceStatus.SECURITY_VIOLATION
        reasons.append(ChannelReasonCode.QUANTUM_CHANNEL_SECURITY_VIOLATION)
        is_evidence_complete = True
    elif has_conflicting_evidence:
        status = ChannelEvidenceStatus.CONFLICTING
        reasons.append(ChannelReasonCode.CONFLICTING_CHANNEL_EVIDENCE)
        is_evidence_complete = False
    elif is_session_mismatch or is_config_mismatch:
        status = ChannelEvidenceStatus.INCOMPATIBLE_CONTEXT
        if is_session_mismatch:
            reasons.append(ChannelReasonCode.CHANNEL_SESSION_MISMATCH)
        if is_config_mismatch:
            reasons.append(ChannelReasonCode.CHANNEL_CONFIGURATION_MISMATCH)
        reasons.append(ChannelReasonCode.CHANNEL_CONTEXT_MISMATCH)
        is_evidence_complete = False
    elif is_incomplete:
        status = ChannelEvidenceStatus.INCOMPLETE
        if missing_report:
            reasons.append(ChannelReasonCode.MISSING_CHANNEL_EVIDENCE)
        else:
            reasons.append(ChannelReasonCode.INCOMPLETE_CHANNEL_EVIDENCE)
        is_evidence_complete = False
    elif is_anomalous:
        status = ChannelEvidenceStatus.ANOMALOUS
        is_evidence_complete = True
    else:
        status = ChannelEvidenceStatus.CLEAN
        reasons.append(ChannelReasonCode.CHANNEL_CLEAN)
        is_evidence_complete = True

    # 8. Deterministic Primary Reason & Sorting
    dedup_reasons = tuple(sorted(set(reasons), key=lambda x: x.value))
    primary = _select_primary_reason(dedup_reasons)

    return ChannelSecurityEvidence(
        status=status,
        primary_reason=primary,
        reason_codes=dedup_reasons,
        is_anomalous=is_anomalous,
        is_explicit_violation=explicit_violation,
        is_evidence_complete=is_evidence_complete,
        violation_type=violation_type if explicit_violation else None,
        exceeded_metrics=tuple(sorted(set(exceeded_metrics_list))),
        exceeded_count=len(exceeded_metrics_list),
        session_id=eff_session_id,
        configuration_hash=eff_config_hash,
        policy_id=policy_id,
        threshold_report=eval_report,
        statistical_evidence=statistical_evidence,
        metadata=meta_dict,
    )


# ==============================================================================
# Integration Adapter (M15 -> M12)
# ==============================================================================

def evaluate_channel_attack_decision(
    channel_evidence: ChannelSecurityEvidence | None = None,
    threshold_report: PolicyEvaluationReport | None = None,
    statistical_evidence: StatisticalEvidence | None = None,
    threshold_policy: ThresholdPolicy | None = None,
    expected_configuration_hash: str | None = None,
    session_id: str | None = None,
    expected_session_id: str | None = None,
    required_metrics: Sequence[str] | None = None,
    explicit_violation: bool = False,
    violation_type: str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> DecisionResult:
    """Evaluate quantum channel security evidence and invoke M12 to obtain a deterministic verdict.

    This adapter bridges the lower-layer channel attack evaluation into M12's
    evaluate_security_decision engine.

    Returns:
        Immutable DecisionResult with verdict (ACCEPT, SUSPICIOUS, ATTACK) and reason codes.
    """
    # Validate session_id parameter if provided
    if session_id is not None:
        if not isinstance(session_id, str):
            raise TypeError(f"session_id must be str or None, got {type(session_id).__name__}.")
        if not session_id.strip():
            raise ValueError("session_id cannot be empty or whitespace.")

    # 1. Resolve or compute ChannelSecurityEvidence
    ev: ChannelSecurityEvidence
    if channel_evidence is not None:
        if not isinstance(channel_evidence, ChannelSecurityEvidence):
            raise TypeError(f"channel_evidence must be ChannelSecurityEvidence, got {type(channel_evidence).__name__}.")
        # If context constraints are passed with pre-constructed evidence, verify compatibility
        if expected_session_id is not None and channel_evidence.session_id != expected_session_id:
            ev = detect_channel_anomalies(
                threshold_report=channel_evidence.threshold_report,
                statistical_evidence=channel_evidence.statistical_evidence,
                session_id=channel_evidence.session_id,
                expected_session_id=expected_session_id,
                expected_configuration_hash=expected_configuration_hash or channel_evidence.configuration_hash,
                metadata=channel_evidence.metadata,
            )
        elif expected_configuration_hash is not None and channel_evidence.configuration_hash != expected_configuration_hash:
            ev = detect_channel_anomalies(
                threshold_report=channel_evidence.threshold_report,
                statistical_evidence=channel_evidence.statistical_evidence,
                session_id=channel_evidence.session_id,
                expected_session_id=expected_session_id,
                expected_configuration_hash=expected_configuration_hash,
                metadata=channel_evidence.metadata,
            )
        else:
            ev = channel_evidence
    else:
        ev = detect_channel_anomalies(
            threshold_report=threshold_report,
            statistical_evidence=statistical_evidence,
            threshold_policy=threshold_policy,
            required_metrics=required_metrics,
            session_id=session_id,
            expected_session_id=expected_session_id,
            expected_configuration_hash=expected_configuration_hash,
            explicit_violation=explicit_violation,
            violation_type=violation_type,
            metadata=metadata,
        )

    # 2. Bridge to M12 ProtocolSecurityEvidence
    proto = ev.to_protocol_security_evidence()

    # 3. Determine threshold report to pass to M12
    rep = ev.threshold_report if ev.threshold_report is not None else threshold_report

    # 4. Invoke M12 Decision Engine
    combined_meta = dict(ev.metadata)
    if metadata:
        combined_meta.update(metadata)

    return evaluate_security_decision(
        threshold_report=rep,
        protocol_evidence=proto,
        required_metrics=required_metrics,
        expected_configuration_hash=expected_configuration_hash,
        metadata=combined_meta,
    )

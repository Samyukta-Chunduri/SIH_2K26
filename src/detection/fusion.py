"""Q-SHIELD — Deterministic Evidence Fusion Layer (Milestone M16).

Aggregates, synthesizes, and audits independent security evidence produced by:
    - M13: Impersonation Detection (ImpersonationEvidence)
    - M14: Unauthorized Verification Detection (AuthorizationEvidence)
    - M15: Quantum Channel Attack Detection (ChannelSecurityEvidence)

into a single immutable, deterministic, auditable fused-evidence representation
(FusedSecurityEvidence) that bridges directly into the M12 Decision Engine.

Architectural Placement:
    M13 Impersonation Evidence      M14 Authorization Evidence      M15 Channel Evidence
               │                                │                               │
               └────────────────────────┬───────┴───────────────────────────────┘
                                        ↓
                         M16 Deterministic Evidence Fusion  (THIS MODULE)
                                        ↓
                       ProtocolSecurityEvidence (M12 Contract)
                                        ↓
                        M12 Deterministic Decision Engine
                                        ↓
                           ACCEPT / SUSPICIOUS / ATTACK

Core Scientific & Scope Invariants:
    1. Evidence Aggregation, NOT Decision Engine:
       M16 is strictly an evidence synthesis and compatibility audit layer.
       M12 remains the SOLE component authorized to render the final security decision
       (ACCEPT / SUSPICIOUS / ATTACK). M16 never bypasses or replaces M12.
    2. Preservation of Source Identity & Semantics:
       M16 preserves which subsystem produced each piece of evidence (IMPERSONATION,
       AUTHORIZATION, QUANTUM_CHANNEL) and retains exact source reason codes, statuses,
       and explicit violation flags without downgrading or upgrading.
    3. Statistical Anomaly != Confirmed Attack:
       Statistical anomalies (e.g. elevated QBER, degraded fidelity) indicate channel-level
       disturbances and evaluate to SUSPICIOUS in M12. They are NEVER converted into confirmed
       attacks or attributed to named adversaries by M16.
    4. Missing Evidence != Clean:
       Absence of evidence is never evidence of absence. Missing or incomplete sources
       explicitly produce INCOMPLETE, routing conservatively to M12 SUSPICIOUS.
    5. Conflicting Evidence Preserved:
       Contradictory assertions within or across subsystems produce CONFLICTING. M16 never
       applies arbitrary heuristics ("allow-wins" or "deny-wins") to mask real conflicts.
    6. Context & Session Binding:
       Session identifiers and canonical SHA-256 baseline configuration hashes must agree
       across all present sources. Disagreements produce INCOMPATIBLE_CONTEXT or CONFLICTING.
    7. Strictly Zero Composite Scores:
       Strictly NO scalar risk scores, trust scores, threat scores, confidence scores,
       weighted averages, probability of attack, or heuristic point tallies.
    8. Strictly Zero Machine Learning / AI:
       Deterministic, explainable, rule-based aggregation only.
    9. Strictly Zero Replay or Cryptographic Redesign:
       M16 does not implement nonces, replay caches, token validation, or IAM infrastructure.
    10. Immutability & Defensive Secret Leakage Guard:
        Frozen dataclasses, recursive deep-freezing of metadata, and defensive filtering of
        sensitive credential/secret keywords.
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
    DecisionResult,
    ProtocolSecurityEvidence,
    evaluate_security_decision,
)
from src.detection.impersonation import (
    IdentityEvidenceStatus,
    ImpersonationEvidence,
    ImpersonationReasonCode,
)
from src.statistics.thresholds import PolicyEvaluationReport


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
        return tuple(_deep_freeze_val(x) for x in val)
    elif isinstance(val, tuple):
        return tuple(_deep_freeze_val(x) for x in val)
    elif isinstance(val, set):
        return frozenset(val)
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

class EvidenceSource(str, Enum):
    """Identifier for the security subsystem that generated a piece of evidence.

    IMPERSONATION: Milestone M13 Impersonation Detection.
    AUTHORIZATION: Milestone M14 Unauthorized Verification Detection.
    QUANTUM_CHANNEL: Milestone M15 Quantum Channel Attack Detection.
    """

    IMPERSONATION = "IMPERSONATION"
    AUTHORIZATION = "AUTHORIZATION"
    QUANTUM_CHANNEL = "QUANTUM_CHANNEL"


class FusedEvidenceStatus(str, Enum):
    """Categorical status of fused multi-source security evidence.

    CLEAN: All required evidence sources present, operating context compatible, no anomalies or violations.
    ANOMALOUS: Required sources present, operating context compatible, one or more sources reported anomalies,
               with no confirmed explicit security violations.
    SECURITY_VIOLATION: One or more sources confirmed an explicit protocol or channel security violation.
    INCOMPLETE: One or more required evidence sources are missing or incomplete.
    INCOMPATIBLE_CONTEXT: Operating context (session identifier or configuration hash) mismatches across sources
                          or against the expected evaluation context.
    CONFLICTING: Evidence sources contain contradictory assertions or unresolved internal conflicts.
    """

    CLEAN = "CLEAN"
    ANOMALOUS = "ANOMALOUS"
    SECURITY_VIOLATION = "SECURITY_VIOLATION"
    INCOMPLETE = "INCOMPLETE"
    INCOMPATIBLE_CONTEXT = "INCOMPATIBLE_CONTEXT"
    CONFLICTING = "CONFLICTING"


class FusionReasonCode(str, Enum):
    """Canonical machine-readable reason codes explaining fused evidence evaluation findings."""

    ALL_SOURCES_CLEAN = "ALL_SOURCES_CLEAN"
    EXPLICIT_SECURITY_VIOLATION_PRESENT = "EXPLICIT_SECURITY_VIOLATION_PRESENT"
    STATISTICAL_CHANNEL_ANOMALY_PRESENT = "STATISTICAL_CHANNEL_ANOMALY_PRESENT"
    MULTI_SOURCE_ANOMALY_PRESENT = "MULTI_SOURCE_ANOMALY_PRESENT"
    MISSING_REQUIRED_SOURCE = "MISSING_REQUIRED_SOURCE"
    INCOMPLETE_SOURCE_EVIDENCE = "INCOMPLETE_SOURCE_EVIDENCE"
    SESSION_ID_MISMATCH = "SESSION_ID_MISMATCH"
    CONFIGURATION_HASH_MISMATCH = "CONFIGURATION_HASH_MISMATCH"
    CONTEXT_MISMATCH = "CONTEXT_MISMATCH"
    CONFLICTING_EVIDENCE_PRESENT = "CONFLICTING_EVIDENCE_PRESENT"
    UNSUPPORTED_SOURCE_EVIDENCE = "UNSUPPORTED_SOURCE_EVIDENCE"


# ==============================================================================
# Fused Evidence Container
# ==============================================================================

@dataclass(frozen=True)
class FusedSecurityEvidence:
    """Immutable multi-source security evidence container produced by Milestone M16.

    Aggregates and synthesizes evidence across identity (M13), authorization (M14),
    and quantum channel (M15) dimensions while preserving source provenance and exact
    semantics.

    Attributes:
        status: FusedEvidenceStatus categorical synthesis outcome.
        primary_reason: Top canonical reason code driving the evaluation by deterministic precedence.
        reason_codes: Sorted, deduplicated tuple of all applicable reason codes (fusion + preserved source).
        source_reason_codes: Mapping from EvidenceSource string to tuple of preserved source reason codes.
        is_clean: True if all required sources are present, compatible, and clean.
        is_anomalous: True if one or more sources reported anomalies without explicit violations.
        is_explicit_violation: True if any source confirmed an explicit protocol/security violation.
        is_complete: True if all required evidence sources were present and complete.
        violations: Sorted, deduplicated tuple of canonical violation identifiers from all violating sources.
        source_statuses: Mapping from EvidenceSource string to raw categorical status string.
        present_sources: Sorted tuple of EvidenceSource enums present in this evaluation.
        missing_sources: Sorted tuple of EvidenceSource enums required but missing.
        session_id: Resolved session identifier if consistent across sources, else None.
        configuration_hash: Resolved canonical configuration hash if consistent, else None.
        impersonation_evidence: Optional reference to underlying M13 ImpersonationEvidence.
        authorization_evidence: Optional reference to underlying M14 AuthorizationEvidence.
        channel_evidence: Optional reference to underlying M15 ChannelSecurityEvidence.
        timestamp: ISO 8601 UTC timestamp of fusion evaluation.
        metadata: Contextual provenance metadata dictionary.
    """

    status: FusedEvidenceStatus
    primary_reason: str
    reason_codes: tuple[str, ...]
    source_reason_codes: dict[str, tuple[str, ...]]
    is_clean: bool
    is_anomalous: bool
    is_explicit_violation: bool
    is_complete: bool
    violations: tuple[str, ...] = ()
    source_statuses: dict[str, str] = field(default_factory=dict)
    present_sources: tuple[EvidenceSource, ...] = ()
    missing_sources: tuple[EvidenceSource, ...] = ()
    session_id: str | None = None
    configuration_hash: str | None = None
    impersonation_evidence: ImpersonationEvidence | None = None
    authorization_evidence: AuthorizationEvidence | None = None
    channel_evidence: ChannelSecurityEvidence | None = None
    timestamp: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate fields, enforce immutability, and apply defensive safeguards."""
        # 1. Validate status
        if not isinstance(self.status, FusedEvidenceStatus):
            if isinstance(self.status, str):
                try:
                    object.__setattr__(self, "status", FusedEvidenceStatus(self.status.upper().strip()))
                except ValueError as exc:
                    raise ValueError(f"Invalid FusedEvidenceStatus: '{self.status}'.") from exc
            else:
                raise TypeError(f"status must be FusedEvidenceStatus, got {type(self.status).__name__}.")

        # 2. Validate primary_reason
        if not isinstance(self.primary_reason, str) or not self.primary_reason.strip():
            raise ValueError("primary_reason must be a non-empty string.")

        # 3. Validate boolean flags
        for name, val in [
            ("is_clean", self.is_clean),
            ("is_anomalous", self.is_anomalous),
            ("is_explicit_violation", self.is_explicit_violation),
            ("is_complete", self.is_complete),
        ]:
            if not isinstance(val, bool):
                raise TypeError(f"{name} must be bool, got {type(val).__name__}.")

        # 4. Validate reason_codes
        if not isinstance(self.reason_codes, (Sequence, tuple)):
            raise TypeError(f"reason_codes must be a sequence of str, got {type(self.reason_codes).__name__}.")
        norm_reasons: list[str] = []
        for r in self.reason_codes:
            if isinstance(r, (Enum, str)):
                val_str = r.value if isinstance(r, Enum) else str(r).strip()
                if not val_str:
                    raise ValueError("reason_codes cannot contain empty strings.")
                norm_reasons.append(val_str)
            else:
                raise TypeError(f"reason_codes elements must be str or Enum, got {type(r).__name__}.")
        object.__setattr__(self, "reason_codes", tuple(sorted(set(norm_reasons))))

        # 5. Validate violations
        if not isinstance(self.violations, (Sequence, tuple)):
            raise TypeError(f"violations must be a sequence of str, got {type(self.violations).__name__}.")
        norm_violations: list[str] = []
        for v in self.violations:
            if not isinstance(v, str) or not v.strip():
                raise ValueError("violations elements must be non-empty strings.")
            norm_violations.append(v.strip())
        dedup_violations = tuple(sorted(set(norm_violations)))
        object.__setattr__(self, "violations", dedup_violations)

        if self.is_explicit_violation and len(dedup_violations) == 0:
            raise ValueError("violations cannot be empty when is_explicit_violation is True.")
        if not self.is_explicit_violation and len(dedup_violations) > 0:
            raise ValueError("violations must be empty when is_explicit_violation is False.")

        # 6. Validate source collections
        for src_field, enum_type in [
            ("present_sources", EvidenceSource),
            ("missing_sources", EvidenceSource),
        ]:
            val_seq = getattr(self, src_field)
            if not isinstance(val_seq, (Sequence, tuple)):
                raise TypeError(f"{src_field} must be a sequence, got {type(val_seq).__name__}.")
            norm_sources: list[EvidenceSource] = []
            for s in val_seq:
                if isinstance(s, EvidenceSource):
                    norm_sources.append(s)
                elif isinstance(s, str):
                    norm_sources.append(EvidenceSource(s.upper().strip()))
                else:
                    raise TypeError(f"{src_field} elements must be EvidenceSource, got {type(s).__name__}.")
            object.__setattr__(self, src_field, tuple(sorted(set(norm_sources), key=lambda x: x.value)))

        # 7. Validate source mappings
        if not isinstance(self.source_statuses, Mapping):
            raise TypeError(f"source_statuses must be Mapping, got {type(self.source_statuses).__name__}.")
        object.__setattr__(self, "source_statuses", {str(k): str(v) for k, v in self.source_statuses.items()})

        if not isinstance(self.source_reason_codes, Mapping):
            raise TypeError(f"source_reason_codes must be Mapping, got {type(self.source_reason_codes).__name__}.")
        frozen_src_reasons: dict[str, tuple[str, ...]] = {}
        for k, v_list in self.source_reason_codes.items():
            if not isinstance(v_list, (Sequence, tuple)):
                raise TypeError(f"source_reason_codes['{k}'] must be a sequence of strings.")
            frozen_src_reasons[str(k)] = tuple(str(x) for x in v_list)
        object.__setattr__(self, "source_reason_codes", frozen_src_reasons)

        # 8. Context string validations
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

        # 9. Source evidence reference typing
        if self.impersonation_evidence is not None and not isinstance(self.impersonation_evidence, ImpersonationEvidence):
            raise TypeError(f"impersonation_evidence must be ImpersonationEvidence or None, got {type(self.impersonation_evidence).__name__}.")
        if self.authorization_evidence is not None and not isinstance(self.authorization_evidence, AuthorizationEvidence):
            raise TypeError(f"authorization_evidence must be AuthorizationEvidence or None, got {type(self.authorization_evidence).__name__}.")
        if self.channel_evidence is not None and not isinstance(self.channel_evidence, ChannelSecurityEvidence):
            raise TypeError(f"channel_evidence must be ChannelSecurityEvidence or None, got {type(self.channel_evidence).__name__}.")

        # 10. Secret leakage checking & defensive recursive deep copy of metadata
        _check_for_secret_leakage(self.metadata, "FusedSecurityEvidence.metadata")
        object.__setattr__(self, "metadata", _deep_freeze_dict(self.metadata))

        if not isinstance(self.timestamp, str):
            raise TypeError(f"timestamp must be str, got {type(self.timestamp).__name__}.")

    def to_protocol_security_evidence(self) -> ProtocolSecurityEvidence:
        """Bridge M16 fused security evidence into M12 ProtocolSecurityEvidence.

        Mapping Rules:
            - If is_explicit_violation is True:
                explicit_violation = True
                violation_type = "+".join(violations)
                is_complete = self.is_complete
                (Directs M12 to render ATTACK).
            - If is_explicit_violation is False:
                explicit_violation = False
                violation_type = None
                is_complete = self.is_complete
                (Directs M12 to render ACCEPT if clean/complete, or SUSPICIOUS if anomalous/incomplete).
        """
        violation_type_str: str | None = None
        if self.is_explicit_violation:
            violation_type_str = "+".join(self.violations) if self.violations else "EXPLICIT_SECURITY_VIOLATION"

        has_conflict_flag = (
            self.status == FusedEvidenceStatus.CONFLICTING
            or FusionReasonCode.CONFLICTING_EVIDENCE_PRESENT.value in self.reason_codes
        )

        violation_details: dict[str, Any] = {
            "fused_status": self.status.value,
            "primary_reason": self.primary_reason,
            "reason_codes": list(self.reason_codes),
            "violations": list(self.violations),
            "present_sources": [s.value for s in self.present_sources],
            "missing_sources": [s.value for s in self.missing_sources],
            "source_statuses": dict(self.source_statuses),
            "is_anomalous": self.is_anomalous,
            "has_conflict": has_conflict_flag,
            "configuration_hash": self.configuration_hash,
            "fused_timestamp": self.timestamp,
        }

        return ProtocolSecurityEvidence(
            explicit_violation=self.is_explicit_violation,
            violation_type=violation_type_str,
            violation_details=violation_details,
            is_complete=self.is_complete,
            session_id=self.session_id,
            metadata=dict(self.metadata),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize fused evidence into an inspectable dictionary."""
        return {
            "status": self.status.value,
            "primary_reason": self.primary_reason,
            "reason_codes": list(self.reason_codes),
            "source_reason_codes": {k: list(v) for k, v in self.source_reason_codes.items()},
            "is_clean": self.is_clean,
            "is_anomalous": self.is_anomalous,
            "is_explicit_violation": self.is_explicit_violation,
            "is_complete": self.is_complete,
            "violations": list(self.violations),
            "source_statuses": dict(self.source_statuses),
            "present_sources": [s.value for s in self.present_sources],
            "missing_sources": [s.value for s in self.missing_sources],
            "session_id": self.session_id,
            "configuration_hash": self.configuration_hash,
            "timestamp": self.timestamp,
            "metadata": _deep_freeze_dict(self.metadata),
        }


# ==============================================================================
# Deterministic Evidence Fusion Engine
# ==============================================================================

def fuse_security_evidence(
    impersonation_evidence: ImpersonationEvidence | None = None,
    authorization_evidence: AuthorizationEvidence | None = None,
    channel_evidence: ChannelSecurityEvidence | None = None,
    required_sources: Sequence[EvidenceSource | str] | None = None,
    expected_session_id: str | None = None,
    expected_configuration_hash: str | None = None,
    timestamp: str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> FusedSecurityEvidence:
    """Deterministically aggregate and audit independent security evidence from M13, M14, and M15.

    Precedence & Aggregation Workflow:
        1. Type validation and secret leakage checks on metadata.
        2. Source presence and required completeness audit.
        3. Context & Configuration Binding:
           Enforce session ID and configuration hash consistency across all present sources
           and against expected context constraints.
        4. Lower-Layer Evidence Extraction:
           Extract raw statuses, reason codes, explicit violation flags, and anomalies without
           altering or re-interpreting source semantics.
        5. Multiple Explicit Violation Accumulation:
           If one or more sources confirm an explicit security violation, collect ALL violation
           identifiers deterministically (no "first violation wins").
        6. Deterministic Status Precedence:
           - Precedence 1: Conflicting Evidence Present -> CONFLICTING (evaluates to M12 ATTACK if explicit violation present, else SUSPICIOUS).
           - Precedence 2: Explicit Violation Present -> SECURITY_VIOLATION (evaluates to M12 ATTACK).
           - Precedence 3: Context Mismatch -> INCOMPATIBLE_CONTEXT (evaluates to M12 SUSPICIOUS).
           - Precedence 4: Missing or Incomplete Sources -> INCOMPLETE (evaluates to M12 SUSPICIOUS).
           - Precedence 5: Channel/Source Anomaly Present -> ANOMALOUS (evaluates to M12 SUSPICIOUS).
           - Precedence 6: All Required Sources Clean -> CLEAN (evaluates to M12 ACCEPT).

    Args:
        impersonation_evidence: M13 ImpersonationEvidence record.
        authorization_evidence: M14 AuthorizationEvidence record.
        channel_evidence: M15 ChannelSecurityEvidence record.
        required_sources: Sequence of EvidenceSource elements required for completeness.
                          Defaults to (IMPERSONATION, AUTHORIZATION, QUANTUM_CHANNEL).
        expected_session_id: Optional expected session identifier to enforce binding.
        expected_configuration_hash: Optional canonical configuration hash to enforce binding.
        timestamp: Optional explicit ISO 8601 UTC timestamp. If None, deterministically derived
                   from contributing source observation timestamps (latest observation epoch),
                   ensuring repeated evaluations remain 100% bit-for-bit deterministic.
        metadata: Optional contextual provenance metadata.

    Returns:
        Immutable FusedSecurityEvidence container.

    Raises:
        TypeError: If input parameters have invalid types.
        ValueError: If parameters contain forbidden secret keys or empty/whitespace strings.
    """
    # 0. Deterministic Timestamp Resolution
    resolved_timestamp: str = ""
    if timestamp is not None:
        if not isinstance(timestamp, str):
            raise TypeError(f"timestamp must be str or None, got {type(timestamp).__name__}.")
        resolved_timestamp = timestamp.strip()
    else:
        # Deterministically derive observation epoch from contributing source timestamps
        src_timestamps: list[str] = []
        for src in (impersonation_evidence, authorization_evidence, channel_evidence):
            if src is not None and getattr(src, "timestamp", None):
                ts_val = str(src.timestamp).strip()
                if ts_val:
                    src_timestamps.append(ts_val)
        if src_timestamps:
            # Lexicographical max of ISO-8601 UTC strings yields the latest observation epoch
            resolved_timestamp = max(src_timestamps)

    # 1. Type validation for metadata and secret leakage check
    meta_dict = dict(metadata) if metadata is not None else {}
    _check_for_secret_leakage(meta_dict, "metadata")

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

    if impersonation_evidence is not None and not isinstance(impersonation_evidence, ImpersonationEvidence):
        raise TypeError(f"impersonation_evidence must be ImpersonationEvidence or None, got {type(impersonation_evidence).__name__}.")
    if authorization_evidence is not None and not isinstance(authorization_evidence, AuthorizationEvidence):
        raise TypeError(f"authorization_evidence must be AuthorizationEvidence or None, got {type(authorization_evidence).__name__}.")
    if channel_evidence is not None and not isinstance(channel_evidence, ChannelSecurityEvidence):
        raise TypeError(f"channel_evidence must be ChannelSecurityEvidence or None, got {type(channel_evidence).__name__}.")

    # 2. Normalize and validate required_sources
    default_req = (
        EvidenceSource.IMPERSONATION,
        EvidenceSource.AUTHORIZATION,
        EvidenceSource.QUANTUM_CHANNEL,
    )
    norm_req_sources: list[EvidenceSource] = []
    if required_sources is None:
        norm_req_sources = list(default_req)
    else:
        if not isinstance(required_sources, Sequence) or isinstance(required_sources, (str, bytes)):
            raise TypeError(f"required_sources must be a Sequence of EvidenceSource, got {type(required_sources).__name__}.")
        for idx, src in enumerate(required_sources):
            if isinstance(src, EvidenceSource):
                norm_req_sources.append(src)
            elif isinstance(src, str):
                if not src.strip():
                    raise ValueError(f"required_sources element at index {idx} cannot be empty or whitespace.")
                try:
                    norm_req_sources.append(EvidenceSource(src.upper().strip()))
                except ValueError as exc:
                    raise ValueError(f"Invalid EvidenceSource in required_sources at index {idx}: '{src}'.") from exc
            else:
                raise TypeError(f"required_sources element at index {idx} must be EvidenceSource, got {type(src).__name__}.")

    dedup_required = tuple(sorted(set(norm_req_sources), key=lambda x: x.value))

    # 3. Identify present and missing sources
    present_list: list[EvidenceSource] = []
    if impersonation_evidence is not None:
        present_list.append(EvidenceSource.IMPERSONATION)
    if authorization_evidence is not None:
        present_list.append(EvidenceSource.AUTHORIZATION)
    if channel_evidence is not None:
        present_list.append(EvidenceSource.QUANTUM_CHANNEL)

    dedup_present = tuple(sorted(set(present_list), key=lambda x: x.value))
    missing_list = [s for s in dedup_required if s not in dedup_present]
    dedup_missing = tuple(sorted(set(missing_list), key=lambda x: x.value))

    # 4. Context & Session Binding Audit
    reasons: list[str] = []
    source_reasons: dict[str, tuple[str, ...]] = {}
    source_statuses_dict: dict[str, str] = {}
    violations_list: list[str] = []

    has_context_mismatch = False
    has_context_conflict = False
    has_internal_conflict = False
    is_source_incomplete = len(dedup_missing) > 0
    has_anomaly = False
    has_explicit_violation = False

    # Check Session IDs
    observed_sessions: dict[EvidenceSource, str] = {}
    if impersonation_evidence is not None and impersonation_evidence.session_id:
        observed_sessions[EvidenceSource.IMPERSONATION] = impersonation_evidence.session_id
    if authorization_evidence is not None and authorization_evidence.session_id:
        observed_sessions[EvidenceSource.AUTHORIZATION] = authorization_evidence.session_id
    if channel_evidence is not None and channel_evidence.session_id:
        observed_sessions[EvidenceSource.QUANTUM_CHANNEL] = channel_evidence.session_id

    distinct_sessions = set(observed_sessions.values())
    if len(distinct_sessions) > 1:
        has_context_conflict = True
        reasons.append(FusionReasonCode.SESSION_ID_MISMATCH.value)
    elif len(distinct_sessions) == 1:
        resolved_session = next(iter(distinct_sessions))
        if expected_session_id is not None and resolved_session != expected_session_id:
            has_context_mismatch = True
            reasons.append(FusionReasonCode.SESSION_ID_MISMATCH.value)
    elif expected_session_id is not None:
        # None of the sources provided a session ID, but one was expected
        has_context_mismatch = True
        reasons.append(FusionReasonCode.SESSION_ID_MISMATCH.value)

    # Check Configuration Hashes
    observed_hashes: dict[EvidenceSource, str] = {}
    if impersonation_evidence is not None and impersonation_evidence.configuration_hash:
        observed_hashes[EvidenceSource.IMPERSONATION] = impersonation_evidence.configuration_hash
    if authorization_evidence is not None and authorization_evidence.configuration_hash:
        observed_hashes[EvidenceSource.AUTHORIZATION] = authorization_evidence.configuration_hash
    if channel_evidence is not None and channel_evidence.configuration_hash:
        observed_hashes[EvidenceSource.QUANTUM_CHANNEL] = channel_evidence.configuration_hash

    distinct_hashes = set(observed_hashes.values())
    if len(distinct_hashes) > 1:
        has_context_conflict = True
        reasons.append(FusionReasonCode.CONFIGURATION_HASH_MISMATCH.value)
    elif len(distinct_hashes) == 1:
        resolved_hash = next(iter(distinct_hashes))
        if expected_configuration_hash is not None and resolved_hash != expected_configuration_hash:
            has_context_mismatch = True
            reasons.append(FusionReasonCode.CONFIGURATION_HASH_MISMATCH.value)
    elif expected_configuration_hash is not None:
        # None of the sources provided a configuration hash, but one was expected
        has_context_mismatch = True
        reasons.append(FusionReasonCode.CONFIGURATION_HASH_MISMATCH.value)

    # 5. Extract Source Semantics Without Alteration
    # M13 Impersonation Evidence
    if impersonation_evidence is not None:
        source_statuses_dict[EvidenceSource.IMPERSONATION.value] = impersonation_evidence.status.value
        src_r = tuple(r.value for r in impersonation_evidence.reason_codes)
        source_reasons[EvidenceSource.IMPERSONATION.value] = src_r
        reasons.extend(src_r)

        if impersonation_evidence.status == IdentityEvidenceStatus.CONFLICTING:
            has_internal_conflict = True
        elif impersonation_evidence.status == IdentityEvidenceStatus.INCOMPATIBLE_CONTEXT:
            has_context_mismatch = True
        elif impersonation_evidence.status == IdentityEvidenceStatus.INCOMPLETE or not impersonation_evidence.is_evidence_complete:
            is_source_incomplete = True

        if impersonation_evidence.is_impersonation_detected:
            has_explicit_violation = True
            violations_list.append(impersonation_evidence.primary_reason.value)

    # M14 Authorization Evidence
    if authorization_evidence is not None:
        source_statuses_dict[EvidenceSource.AUTHORIZATION.value] = authorization_evidence.status.value
        src_r = tuple(r.value for r in authorization_evidence.reason_codes)
        source_reasons[EvidenceSource.AUTHORIZATION.value] = src_r
        reasons.extend(src_r)

        if authorization_evidence.status == AuthorizationStatus.CONFLICTING:
            has_internal_conflict = True
        elif authorization_evidence.status == AuthorizationStatus.INCOMPATIBLE_CONTEXT:
            has_context_mismatch = True
        elif authorization_evidence.status == AuthorizationStatus.INCOMPLETE or not authorization_evidence.is_evidence_complete:
            is_source_incomplete = True

        if authorization_evidence.is_unauthorized_detected:
            has_explicit_violation = True
            violations_list.append(authorization_evidence.primary_reason.value)

    # M15 Quantum Channel Attack Evidence
    if channel_evidence is not None:
        source_statuses_dict[EvidenceSource.QUANTUM_CHANNEL.value] = channel_evidence.status.value
        src_r = tuple(r.value for r in channel_evidence.reason_codes)
        source_reasons[EvidenceSource.QUANTUM_CHANNEL.value] = src_r
        reasons.extend(src_r)

        if channel_evidence.status == ChannelEvidenceStatus.CONFLICTING:
            has_internal_conflict = True
        elif channel_evidence.status == ChannelEvidenceStatus.INCOMPATIBLE_CONTEXT:
            has_context_mismatch = True
        elif channel_evidence.status == ChannelEvidenceStatus.INCOMPLETE or not channel_evidence.is_evidence_complete:
            is_source_incomplete = True

        if channel_evidence.is_anomalous:
            has_anomaly = True
            reasons.append(FusionReasonCode.STATISTICAL_CHANNEL_ANOMALY_PRESENT.value)

        if channel_evidence.is_explicit_violation:
            has_explicit_violation = True
            v_type = channel_evidence.violation_type or ChannelReasonCode.QUANTUM_CHANNEL_SECURITY_VIOLATION.value
            violations_list.append(v_type)

    # Check for missing sources
    if len(dedup_missing) > 0:
        is_source_incomplete = True
        reasons.append(FusionReasonCode.MISSING_REQUIRED_SOURCE.value)

    # Multi-source anomaly check
    anomalous_source_count = 0
    if has_anomaly:
        anomalous_source_count += 1
    if is_source_incomplete and not has_explicit_violation:
        anomalous_source_count += 1
    if anomalous_source_count > 1:
        reasons.append(FusionReasonCode.MULTI_SOURCE_ANOMALY_PRESENT.value)

    # 6. Apply Deterministic Precedence Hierarchy for Fused Status & Primary Reason
    status: FusedEvidenceStatus
    primary_reason: str
    is_complete: bool

    # PRECEDENCE 1: Conflicting Evidence Assertions (Unreconciled Contradictions)
    if has_context_conflict or has_internal_conflict:
        status = FusedEvidenceStatus.CONFLICTING
        primary_reason = FusionReasonCode.CONFLICTING_EVIDENCE_PRESENT.value
        reasons.append(primary_reason)
        is_complete = False
        if has_explicit_violation:
            # Preserve explicit violation fact in reason codes without erasing violations_list
            reasons.append(FusionReasonCode.EXPLICIT_SECURITY_VIOLATION_PRESENT.value)

    # PRECEDENCE 2: Explicit Security Violation (Confirmed deterministic violation)
    elif has_explicit_violation:
        status = FusedEvidenceStatus.SECURITY_VIOLATION
        primary_reason = FusionReasonCode.EXPLICIT_SECURITY_VIOLATION_PRESENT.value
        reasons.append(primary_reason)
        is_complete = not is_source_incomplete and not has_context_mismatch

    # PRECEDENCE 3: Incompatible Context
    elif has_context_mismatch:
        status = FusedEvidenceStatus.INCOMPATIBLE_CONTEXT
        primary_reason = FusionReasonCode.CONTEXT_MISMATCH.value
        reasons.append(primary_reason)
        is_complete = False

    # PRECEDENCE 4: Missing or Incomplete Evidence
    elif is_source_incomplete:
        status = FusedEvidenceStatus.INCOMPLETE
        primary_reason = (
            FusionReasonCode.MISSING_REQUIRED_SOURCE.value
            if len(dedup_missing) > 0
            else FusionReasonCode.INCOMPLETE_SOURCE_EVIDENCE.value
        )
        reasons.append(primary_reason)
        is_complete = False

    # PRECEDENCE 5: Statistical / Channel Anomaly Present
    elif has_anomaly:
        status = FusedEvidenceStatus.ANOMALOUS
        primary_reason = FusionReasonCode.STATISTICAL_CHANNEL_ANOMALY_PRESENT.value
        is_complete = True

    # PRECEDENCE 6: All Clean & Complete
    else:
        status = FusedEvidenceStatus.CLEAN
        primary_reason = FusionReasonCode.ALL_SOURCES_CLEAN.value
        reasons.append(primary_reason)
        is_complete = True

    # 7. Deduplicate and sort reason codes deterministically
    dedup_reasons = tuple(sorted(set(reasons)))
    dedup_violations = tuple(sorted(set(violations_list)))

    # Resolve session ID and configuration hash for fused container
    eff_session_id = next(iter(distinct_sessions)) if len(distinct_sessions) == 1 else (expected_session_id if not distinct_sessions else None)
    eff_config_hash = next(iter(distinct_hashes)) if len(distinct_hashes) == 1 else (expected_configuration_hash if not distinct_hashes else None)

    return FusedSecurityEvidence(
        status=status,
        primary_reason=primary_reason,
        reason_codes=dedup_reasons,
        source_reason_codes=source_reasons,
        is_clean=(status == FusedEvidenceStatus.CLEAN),
        is_anomalous=(status == FusedEvidenceStatus.ANOMALOUS),
        is_explicit_violation=has_explicit_violation,
        is_complete=is_complete,
        violations=dedup_violations,
        source_statuses=source_statuses_dict,
        present_sources=dedup_present,
        missing_sources=dedup_missing,
        session_id=eff_session_id,
        configuration_hash=eff_config_hash,
        impersonation_evidence=impersonation_evidence,
        authorization_evidence=authorization_evidence,
        channel_evidence=channel_evidence,
        timestamp=resolved_timestamp,
        metadata=meta_dict,
    )


# ==============================================================================
# Integration Adapter (M16 -> M12)
# ==============================================================================

def evaluate_fused_security_decision(
    fused_evidence: FusedSecurityEvidence | None = None,
    impersonation_evidence: ImpersonationEvidence | None = None,
    authorization_evidence: AuthorizationEvidence | None = None,
    channel_evidence: ChannelSecurityEvidence | None = None,
    threshold_report: PolicyEvaluationReport | None = None,
    required_sources: Sequence[EvidenceSource | str] | None = None,
    expected_session_id: str | None = None,
    expected_configuration_hash: str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> DecisionResult:
    """Evaluate multi-source fused security evidence and invoke M12 to obtain a deterministic decision.

    This adapter bridges the fused evidence into M12 evaluate_security_decision without
    bypassing M12's decision logic.

    Args:
        fused_evidence: Pre-evaluated FusedSecurityEvidence container.
        impersonation_evidence: Optional M13 evidence (evaluated if fused_evidence is None).
        authorization_evidence: Optional M14 evidence (evaluated if fused_evidence is None).
        channel_evidence: Optional M15 evidence (evaluated if fused_evidence is None).
        threshold_report: Optional M11 PolicyEvaluationReport (defaults to channel_evidence.threshold_report if omitted).
        required_sources: Optional sequence of required evidence sources.
        expected_session_id: Optional expected session identifier.
        expected_configuration_hash: Optional canonical baseline configuration hash.
        metadata: Optional contextual metadata.

    Returns:
        Immutable DecisionResult with verdict (ACCEPT, SUSPICIOUS, ATTACK) and explainable reason codes.
    """
    # 1. Resolve or compute FusedSecurityEvidence
    ev: FusedSecurityEvidence
    if fused_evidence is not None:
        if not isinstance(fused_evidence, FusedSecurityEvidence):
            raise TypeError(f"fused_evidence must be FusedSecurityEvidence, got {type(fused_evidence).__name__}.")
        # If context constraints are passed with pre-fused evidence, verify compatibility
        if expected_session_id is not None and fused_evidence.session_id != expected_session_id:
            ev = fuse_security_evidence(
                impersonation_evidence=fused_evidence.impersonation_evidence,
                authorization_evidence=fused_evidence.authorization_evidence,
                channel_evidence=fused_evidence.channel_evidence,
                required_sources=required_sources,
                expected_session_id=expected_session_id,
                expected_configuration_hash=expected_configuration_hash or fused_evidence.configuration_hash,
                metadata=fused_evidence.metadata,
            )
        elif expected_configuration_hash is not None and fused_evidence.configuration_hash != expected_configuration_hash:
            ev = fuse_security_evidence(
                impersonation_evidence=fused_evidence.impersonation_evidence,
                authorization_evidence=fused_evidence.authorization_evidence,
                channel_evidence=fused_evidence.channel_evidence,
                required_sources=required_sources,
                expected_session_id=expected_session_id or fused_evidence.session_id,
                expected_configuration_hash=expected_configuration_hash,
                metadata=fused_evidence.metadata,
            )
        else:
            ev = fused_evidence
    else:
        ev = fuse_security_evidence(
            impersonation_evidence=impersonation_evidence,
            authorization_evidence=authorization_evidence,
            channel_evidence=channel_evidence,
            required_sources=required_sources,
            expected_session_id=expected_session_id,
            expected_configuration_hash=expected_configuration_hash,
            metadata=metadata,
        )

    # 2. Bridge to M12 ProtocolSecurityEvidence
    proto = ev.to_protocol_security_evidence()

    # 3. Determine threshold report for M12
    rep: PolicyEvaluationReport | None = threshold_report
    if rep is None and ev.channel_evidence is not None:
        rep = ev.channel_evidence.threshold_report

    # 4. Invoke M12 Decision Engine
    combined_meta = dict(ev.metadata)
    if metadata:
        combined_meta.update(metadata)

    return evaluate_security_decision(
        threshold_report=rep,
        protocol_evidence=proto,
        expected_configuration_hash=expected_configuration_hash or ev.configuration_hash,
        metadata=combined_meta,
    )

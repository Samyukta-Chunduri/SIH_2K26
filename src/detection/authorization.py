"""Q-SHIELD — Deterministic Unauthorized Verification Detection Layer (Milestone M14).

Evaluates whether an identified/authenticated participant is authorized to perform
a verification operation within the defined protocol and security context.

Conceptual Model:
    Authenticated Identity
            +
    Requested Operation (VERIFY, VERIFY_TELEPORTATION, AUDIT_VERIFICATION)
            +
    Security Context / Verification Policy
            ↓
    Deterministic Authorization Evaluation
            ↓
    Authorization Evidence (AuthorizationEvidence)
            ↓
    Protocol Security Evidence (ProtocolSecurityEvidence)
            ↓
    Decision Engine (M12 evaluate_security_decision)
            ↓
    DecisionResult (ACCEPT / SUSPICIOUS / ATTACK)

Authentication vs. Authorization Boundary:
    - Authentication (M13) answers: "Who are you?"
    - Authorization (M14) answers: "What are you permitted to do?"
    - authenticated = True does NOT imply authorized = True.
    - authorized = False does NOT imply impersonation = True.
    - An entity genuinely authenticated as Alice may still be denied permission
      to perform a verification operation. This produces an explicit unauthorized
      verification violation (M14 -> ATTACK), NOT an impersonation violation (M13).

Scientific & Scope Invariants:
    1. Quantum Anomaly != Unauthorized Verification: Quantum metrics (QBER, fidelity,
       Bell correlations, threshold crossings) describe quantum channel physics, NOT
       authorization permissions. High noise with a valid verifier produces AUTHORIZED
       in M14 (evaluating to SUSPICIOUS in M12 via M11).
    2. Unauthorized Verification != Impersonation: M14 consumes authenticated identity
       evidence where available, but does NOT perform identity claiming or authentication
       credential verification (M13).
    3. Unauthorized Verification != Replay: M14 does not track message freshness, nonces,
       or replay windows.
    4. Unauthorized Verification != Quantum Channel Attacks: Channel manipulation,
       intercept-resend, and photon splitting belong strictly to M15.
    5. Missing Evidence != Confirmed Attack: Missing policy produces INCOMPLETE
       (evaluating to SUSPICIOUS in M12), NEVER an automatic ATTACK verdict.
    6. Explicit Denial Produces ATTACK: An explicit policy denial produces UNAUTHORIZED
       with explicit_violation=True, yielding an ATTACK verdict in M12.
    7. Strictly NO composite security scores, trust scores, risk scores, or scalar collapsing.
    8. Strictly NO enterprise IAM, OAuth, JWT, X.509, LDAP, or external IdPs.
    9. Strictly NO AI, machine learning, neural networks, or clustering.
    10. Defensive Secret Leakage Guard: Rejects known secret-bearing keywords (password,
        secret, private_key, etc.) in metadata to prevent accidental credential propagation
        (defensive guard, not a claim of complete cryptographic memory sanitization).

Research Prototype Boundary:
    M14 is a deterministic, research-grade, memory-resident authorization evaluator
    for the Q-SHIELD prototype. It does not implement enterprise IAM, OAuth, JWT,
    LDAP, Active Directory, or cloud IAM, and makes no claim of universal detection
    or mathematically complete security.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from src.detection.decision import (
    DecisionReasonCode,
    DecisionResult,
    ProtocolSecurityEvidence,
    evaluate_security_decision,
)
from src.detection.impersonation import AuthenticationEvidence
from src.statistics.thresholds import PolicyEvaluationReport


# Forbidden secret key patterns to prevent secret leakage into evidence containers
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


def _deep_freeze_dict(d: Mapping[str, Any]) -> dict[str, Any]:
    """Recursively copy nested dictionaries to prevent indirect mutation."""
    result: dict[str, Any] = {}
    for k, v in d.items():
        if isinstance(v, Mapping):
            result[str(k)] = _deep_freeze_dict(v)
        elif isinstance(v, list):
            result[str(k)] = list(v)
        elif isinstance(v, set):
            result[str(k)] = set(v)
        else:
            result[str(k)] = v
    return result


def _check_for_secret_leakage(d: Mapping[str, Any], container_name: str) -> None:
    """Inspect dictionary keys and reject any containing raw credential/secret keywords."""
    for key in d.keys():
        key_lower = str(key).lower()
        for forbidden in _FORBIDDEN_SECRET_SUBSTRINGS:
            if forbidden in key_lower:
                raise ValueError(
                    f"Sensitive secret keyword '{forbidden}' detected in {container_name} key '{key}'. "
                    "Raw credentials or cryptographic secrets must never be placed in security evidence."
                )


# ==============================================================================
# Enums
# ==============================================================================

class VerificationOperation(str, Enum):
    """Permitted verification operations within the Q-SHIELD protocol.

    VERIFY: Generic digital signature or quantum state verification.
    VERIFY_TELEPORTATION: Verification of quantum teleportation channel fidelity and state.
    AUDIT_VERIFICATION: Independent audit or inspection of verification transcripts.
    """

    VERIFY = "VERIFY"
    VERIFY_TELEPORTATION = "VERIFY_TELEPORTATION"
    AUDIT_VERIFICATION = "AUDIT_VERIFICATION"


class AuthorizationStatus(str, Enum):
    """Deterministic categorical status of verification authorization evaluation.

    AUTHORIZED: Authenticated participant is explicitly permitted to perform verification.
    UNAUTHORIZED: Authenticated participant is explicitly denied authorization (security violation).
    INCOMPLETE: Required authorization policy or evidence is missing or incomplete.
    INCOMPATIBLE_CONTEXT: Operational context (session ID, configuration hash, or operation)
                          does not match expected evaluation context.
    CONFLICTING: Contradictory authorization directives exist within the policy or evidence.
    """

    AUTHORIZED = "AUTHORIZED"
    UNAUTHORIZED = "UNAUTHORIZED"
    INCOMPLETE = "INCOMPLETE"
    INCOMPATIBLE_CONTEXT = "INCOMPATIBLE_CONTEXT"
    CONFLICTING = "CONFLICTING"


class AuthorizationReasonCode(str, Enum):
    """Stable, canonical reason codes explaining why an authorization decision was reached."""

    AUTHORIZATION_GRANTED = "AUTHORIZATION_GRANTED"
    AUTHORIZATION_DENIED = "AUTHORIZATION_DENIED"
    ROLE_NOT_AUTHORIZED = "ROLE_NOT_AUTHORIZED"
    OPERATION_NOT_PERMITTED = "OPERATION_NOT_PERMITTED"
    RESOURCE_NOT_AUTHORIZED = "RESOURCE_NOT_AUTHORIZED"
    MISSING_AUTHORIZATION_POLICY = "MISSING_AUTHORIZATION_POLICY"
    MISSING_AUTHENTICATED_IDENTITY = "MISSING_AUTHENTICATED_IDENTITY"
    INCOMPLETE_AUTHORIZATION_EVIDENCE = "INCOMPLETE_AUTHORIZATION_EVIDENCE"
    IDENTITY_NOT_AUTHENTICATED = "IDENTITY_NOT_AUTHENTICATED"
    AUTHORIZATION_SESSION_MISMATCH = "AUTHORIZATION_SESSION_MISMATCH"
    AUTHORIZATION_CONTEXT_MISMATCH = "AUTHORIZATION_CONTEXT_MISMATCH"
    CONFLICTING_AUTHORIZATION_EVIDENCE = "CONFLICTING_AUTHORIZATION_EVIDENCE"
    UNSUPPORTED_OPERATION = "UNSUPPORTED_OPERATION"


# ==============================================================================
# Evidence & Policy Containers
# ==============================================================================

@dataclass(frozen=True)
class VerificationPolicy:
    """Immutable authorization policy governing verification operations.

    Attributes:
        policy_id: Unique canonical identifier for the policy.
        allowed_identities: Tuple of participant identities explicitly permitted to verify.
        allowed_roles: Tuple of roles explicitly permitted to verify (e.g. 'VERIFIER', 'AUDITOR').
        allowed_operations: Tuple of verification operations permitted under this policy.
        allowed_resources: Tuple of resource/context identifiers permitted to be verified.
        denied_identities: Tuple of participant identities explicitly denied verification.
        denied_roles: Tuple of roles explicitly denied verification.
        session_id: Optional session identifier binding the policy to an execution.
        configuration_hash: Optional canonical baseline configuration hash binding.
        metadata: Contextual metadata dictionary.
    """

    policy_id: str
    allowed_identities: tuple[str, ...] = field(default_factory=tuple)
    allowed_roles: tuple[str, ...] = field(default_factory=tuple)
    allowed_operations: tuple[str, ...] = field(default_factory=tuple)
    allowed_resources: tuple[str, ...] = field(default_factory=tuple)
    denied_identities: tuple[str, ...] = field(default_factory=tuple)
    denied_roles: tuple[str, ...] = field(default_factory=tuple)
    denied_operations: tuple[str, ...] = field(default_factory=tuple)
    denied_resources: tuple[str, ...] = field(default_factory=tuple)
    session_id: str | None = None
    configuration_hash: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate input types, reject whitespace, prevent secret leakage, and defensively copy."""
        if not isinstance(self.policy_id, str):
            raise TypeError(f"policy_id must be str, got {type(self.policy_id).__name__}.")
        if not self.policy_id.strip():
            raise ValueError("policy_id cannot be empty or whitespace.")

        def _validate_str_tuple(t: Any, field_name: str) -> tuple[str, ...]:
            if not isinstance(t, (tuple, list, set)):
                raise TypeError(f"{field_name} must be a sequence of strings, got {type(t).__name__}.")
            result: list[str] = []
            for item in t:
                if not isinstance(item, str):
                    raise TypeError(f"Items in {field_name} must be str, got {type(item).__name__}.")
                if not item.strip():
                    raise ValueError(f"Items in {field_name} cannot be empty or whitespace.")
                result.append(item.strip())
            return tuple(sorted(set(result)))

        object.__setattr__(self, "allowed_identities", _validate_str_tuple(self.allowed_identities, "allowed_identities"))
        object.__setattr__(self, "allowed_roles", _validate_str_tuple(self.allowed_roles, "allowed_roles"))
        object.__setattr__(self, "allowed_operations", _validate_str_tuple(self.allowed_operations, "allowed_operations"))
        object.__setattr__(self, "allowed_resources", _validate_str_tuple(self.allowed_resources, "allowed_resources"))
        object.__setattr__(self, "denied_identities", _validate_str_tuple(self.denied_identities, "denied_identities"))
        object.__setattr__(self, "denied_roles", _validate_str_tuple(self.denied_roles, "denied_roles"))
        object.__setattr__(self, "denied_operations", _validate_str_tuple(self.denied_operations, "denied_operations"))
        object.__setattr__(self, "denied_resources", _validate_str_tuple(self.denied_resources, "denied_resources"))

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

        _check_for_secret_leakage(self.metadata, "VerificationPolicy.metadata")
        object.__setattr__(self, "metadata", _deep_freeze_dict(self.metadata))


@dataclass(frozen=True)
class AuthorizationRequest:
    """Immutable request to perform a verification operation.

    Attributes:
        participant_identity: Identifier of the authenticated participant requesting verification.
        operation: Operation requested (default: 'VERIFY').
        role: Role of the participant (default: 'VERIFIER').
        resource_id: Optional identifier of the resource or document being verified.
        session_id: Optional session identifier binding the request to an execution.
        configuration_hash: Optional canonical baseline configuration hash binding.
        metadata: Contextual metadata dictionary.
    """

    participant_identity: str
    operation: str = VerificationOperation.VERIFY.value
    role: str = "VERIFIER"
    resource_id: str | None = None
    session_id: str | None = None
    configuration_hash: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate input types, reject whitespace, prevent secret leakage, and defensively copy."""
        if not isinstance(self.participant_identity, str):
            raise TypeError(f"participant_identity must be str, got {type(self.participant_identity).__name__}.")
        if not self.participant_identity.strip():
            raise ValueError("participant_identity cannot be empty or whitespace.")

        if not isinstance(self.operation, str):
            raise TypeError(f"operation must be str, got {type(self.operation).__name__}.")
        if not self.operation.strip():
            raise ValueError("operation cannot be empty or whitespace.")

        if not isinstance(self.role, str):
            raise TypeError(f"role must be str, got {type(self.role).__name__}.")
        if not self.role.strip():
            raise ValueError("role cannot be empty or whitespace.")

        if self.resource_id is not None:
            if not isinstance(self.resource_id, str):
                raise TypeError(f"resource_id must be str or None, got {type(self.resource_id).__name__}.")
            if not self.resource_id.strip():
                raise ValueError("resource_id cannot be empty or whitespace when provided.")

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

        _check_for_secret_leakage(self.metadata, "AuthorizationRequest.metadata")
        object.__setattr__(self, "metadata", _deep_freeze_dict(self.metadata))


@dataclass(frozen=True)
class AuthorizationEvidence:
    """Immutable evidence record produced by the unauthorized verification detector.

    Scientific Principle:
        Captures explicit, inspectable authorization verification facts.
        Directly converts to M12 ProtocolSecurityEvidence for unified security decisions.

    Attributes:
        is_authorized: True if the participant is confirmed authorized for this operation.
        is_unauthorized_detected: True if a confirmed unauthorized verification attempt is established.
        is_indeterminate: True if authorization could not be established due to missing/incompatible data.
        status: AuthorizationStatus indicating categorical outcome.
        primary_reason: Top canonical reason code driving the evaluation.
        reason_codes: Sorted, deduplicated tuple of all applicable reason codes.
        participant_identity: Participant identifier evaluated.
        operation: Operation evaluated.
        role: Role evaluated.
        resource_id: Resource identifier evaluated (if any).
        policy_id: Policy identifier evaluated (if any).
        session_id: Session identifier bound to the evaluation.
        configuration_hash: Canonical configuration hash bound to the evaluation.
        is_evidence_complete: Whether all required authorization evidence was present.
        timestamp: ISO 8601 UTC timestamp.
        metadata: Contextual evaluation metadata.
    """

    is_authorized: bool
    is_unauthorized_detected: bool
    is_indeterminate: bool
    status: AuthorizationStatus
    primary_reason: AuthorizationReasonCode
    reason_codes: tuple[AuthorizationReasonCode, ...]
    participant_identity: str | None
    operation: str | None
    role: str | None
    resource_id: str | None = None
    policy_id: str | None = None
    session_id: str | None = None
    configuration_hash: str | None = None
    is_evidence_complete: bool = True
    timestamp: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate fields, normalize collections, and generate timestamp."""
        if not isinstance(self.is_authorized, bool):
            raise TypeError(f"is_authorized must be bool, got {type(self.is_authorized).__name__}.")
        if not isinstance(self.is_unauthorized_detected, bool):
            raise TypeError(f"is_unauthorized_detected must be bool, got {type(self.is_unauthorized_detected).__name__}.")
        if not isinstance(self.is_indeterminate, bool):
            raise TypeError(f"is_indeterminate must be bool, got {type(self.is_indeterminate).__name__}.")
        if not isinstance(self.status, AuthorizationStatus):
            raise TypeError(f"status must be AuthorizationStatus, got {type(self.status).__name__}.")
        if not isinstance(self.primary_reason, AuthorizationReasonCode):
            raise TypeError(f"primary_reason must be AuthorizationReasonCode, got {type(self.primary_reason).__name__}.")

        object.__setattr__(self, "reason_codes", tuple(sorted(set(self.reason_codes), key=lambda x: x.value)))
        object.__setattr__(self, "metadata", _deep_freeze_dict(self.metadata))

        if not self.timestamp:
            object.__setattr__(self, "timestamp", datetime.now(timezone.utc).isoformat())

    def to_protocol_security_evidence(self) -> ProtocolSecurityEvidence:
        """Convert this AuthorizationEvidence into M12 ProtocolSecurityEvidence.

        Scientific Contract:
            - If is_unauthorized_detected is True:
                Produces explicit_violation=True, violation_type='UNAUTHORIZED_VERIFICATION'.
                In M12, this triggers PRECEDENCE 1 -> ATTACK.
            - If is_indeterminate is True:
                Produces explicit_violation=False, is_complete=False.
                In M12, this triggers PRECEDENCE 3 -> SUSPICIOUS.
            - If authorized and complete:
                Produces explicit_violation=False, is_complete=True.
                In M12, this allows PRECEDENCE 5 -> ACCEPT (provided quantum metrics agree).
        """
        if self.is_unauthorized_detected:
            return ProtocolSecurityEvidence(
                explicit_violation=True,
                violation_type="UNAUTHORIZED_VERIFICATION",
                violation_details={
                    "status": self.status.value,
                    "primary_reason": self.primary_reason.value,
                    "reason_codes": [r.value for r in self.reason_codes],
                    "participant_identity": self.participant_identity,
                    "operation": self.operation,
                    "role": self.role,
                    "resource_id": self.resource_id,
                    "policy_id": self.policy_id,
                    "session_id": self.session_id,
                },
                is_complete=self.is_evidence_complete,
                session_id=self.session_id,
                metadata=dict(self.metadata),
            )

        if self.is_indeterminate:
            return ProtocolSecurityEvidence(
                explicit_violation=False,
                violation_type=None,
                violation_details={
                    "status": self.status.value,
                    "primary_reason": self.primary_reason.value,
                    "reason_codes": [r.value for r in self.reason_codes],
                    "participant_identity": self.participant_identity,
                    "operation": self.operation,
                },
                is_complete=False,
                session_id=self.session_id,
                metadata=dict(self.metadata),
            )

        return ProtocolSecurityEvidence(
            explicit_violation=False,
            violation_type=None,
            violation_details={
                "status": self.status.value,
                "primary_reason": self.primary_reason.value,
                "participant_identity": self.participant_identity,
                "operation": self.operation,
            },
            is_complete=True,
            session_id=self.session_id,
            metadata=dict(self.metadata),
        )


# ==============================================================================
# Detector Implementation
# ==============================================================================

def evaluate_verification_authorization(
    request: AuthorizationRequest | Mapping[str, Any],
    policy: VerificationPolicy | Mapping[str, Any] | None = None,
    auth_evidence: AuthenticationEvidence | Mapping[str, Any] | None = None,
    expected_session_id: str | None = None,
    expected_configuration_hash: str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> AuthorizationEvidence:
    """Evaluate authorization request against verification policy and context.

    Deterministic Evaluation & Authority Hierarchy:
        1. Malformed / Invalid Input Types -> TypeError / ValueError
        2. Scope Validation: Operation must be a recognized verification operation
           (otherwise UNSUPPORTED_OPERATION / INCOMPATIBLE_CONTEXT, NOT ATTACK).
        3. Configuration Compatibility Check -> INCOMPATIBLE_CONTEXT / AUTHORIZATION_CONTEXT_MISMATCH
        4. Session Binding Mismatch -> INCOMPATIBLE_CONTEXT / AUTHORIZATION_SESSION_MISMATCH
        5. Authentication Prerequisite Verification (M13 Boundary):
           - Missing / Failed auth -> INCOMPLETE / IDENTITY_NOT_AUTHENTICATED (M12 SUSPICIOUS, NOT M14 ATTACK)
           - Identity mismatch between claim and auth -> CONFLICTING (M12 SUSPICIOUS)
        6. Policy Availability & Completeness:
           - Missing policy -> INCOMPLETE / MISSING_AUTHORIZATION_POLICY
           - Empty policy (no rules) -> INCOMPLETE / INCOMPLETE_AUTHORIZATION_EVIDENCE
        7. Conflicting Directives Check:
           - Identity simultaneously in allowed and denied -> CONFLICTING
           - Role simultaneously in allowed and denied -> CONFLICTING
           - Identity allowed but role denied (or vice versa) -> CONFLICTING
        8. Explicit Denials:
           - Denied identity -> UNAUTHORIZED / AUTHORIZATION_DENIED (Explicit Violation -> ATTACK)
           - Denied role -> UNAUTHORIZED / ROLE_NOT_AUTHORIZED (Explicit Violation -> ATTACK)
        9. Operation and Resource Restrictions:
           - Operation not in allowed_operations -> UNAUTHORIZED / OPERATION_NOT_PERMITTED
           - Resource not in allowed_resources -> UNAUTHORIZED / RESOURCE_NOT_AUTHORIZED
        10. Whitelist Enforcement:
           - Role not in allowed_roles (when specified) -> UNAUTHORIZED / ROLE_NOT_AUTHORIZED
           - Identity not in allowed_identities (when specified) -> UNAUTHORIZED / AUTHORIZATION_DENIED
        11. Granted:
           - AUTHORIZED / AUTHORIZATION_GRANTED (Clean -> ACCEPT in M12)

    Args:
        request: AuthorizationRequest or mapping representing the verification request.
        policy: Optional VerificationPolicy or mapping defining authorization rules.
        auth_evidence: Optional AuthenticationEvidence or mapping proving authenticated identity.
        expected_session_id: Optional expected session identifier to enforce binding.
        expected_configuration_hash: Optional canonical configuration hash to enforce binding.
        metadata: Optional evaluation context metadata.

    Returns:
        Immutable AuthorizationEvidence containing categorical status and explainable reason codes.

    Raises:
        TypeError: If arguments have invalid types.
        ValueError: If request or context fields contain empty or malformed strings.
    """
    # 1. Input Type Normalization & Explicit Parameter Validation
    if expected_session_id is not None:
        if not isinstance(expected_session_id, str):
            raise TypeError(f"expected_session_id must be str or None, got {type(expected_session_id).__name__}.")
        if not expected_session_id.strip():
            raise ValueError("expected_session_id cannot be empty or whitespace when provided.")

    if expected_configuration_hash is not None:
        if not isinstance(expected_configuration_hash, str):
            raise TypeError(f"expected_configuration_hash must be str or None, got {type(expected_configuration_hash).__name__}.")
        if not expected_configuration_hash.strip():
            raise ValueError("expected_configuration_hash cannot be empty or whitespace when provided.")

    resolved_request: AuthorizationRequest
    if isinstance(request, AuthorizationRequest):
        resolved_request = request
    elif isinstance(request, Mapping):
        p_id = request.get("participant_identity")
        if p_id is None:
            raise TypeError("request mapping must contain a string 'participant_identity'.")
        if not isinstance(p_id, str):
            raise TypeError(f"participant_identity must be str, got {type(p_id).__name__}.")
        resolved_request = AuthorizationRequest(
            participant_identity=p_id,
            operation=str(request.get("operation", VerificationOperation.VERIFY.value)),
            role=str(request.get("role", "VERIFIER")),
            resource_id=request.get("resource_id"),
            session_id=request.get("session_id"),
            configuration_hash=request.get("configuration_hash"),
            metadata=dict(request.get("metadata", {})),
        )
    else:
        raise TypeError(f"request must be AuthorizationRequest or Mapping, got {type(request).__name__}.")

    resolved_policy: VerificationPolicy | None = None
    if policy is not None:
        if isinstance(policy, VerificationPolicy):
            resolved_policy = policy
        elif isinstance(policy, Mapping):
            p_id = policy.get("policy_id")
            if p_id is None:
                raise TypeError("policy mapping must contain a string 'policy_id'.")
            if not isinstance(p_id, str):
                raise TypeError(f"policy_id must be str, got {type(p_id).__name__}.")
            resolved_policy = VerificationPolicy(
                policy_id=p_id,
                allowed_identities=tuple(policy.get("allowed_identities", ())),
                allowed_roles=tuple(policy.get("allowed_roles", ())),
                allowed_operations=tuple(policy.get("allowed_operations", ())),
                allowed_resources=tuple(policy.get("allowed_resources", ())),
                denied_identities=tuple(policy.get("denied_identities", ())),
                denied_roles=tuple(policy.get("denied_roles", ())),
                denied_operations=tuple(policy.get("denied_operations", ())),
                denied_resources=tuple(policy.get("denied_resources", ())),
                session_id=policy.get("session_id"),
                configuration_hash=policy.get("configuration_hash"),
                metadata=dict(policy.get("metadata", {})),
            )
        else:
            raise TypeError(f"policy must be VerificationPolicy, Mapping, or None, got {type(policy).__name__}.")

    resolved_auth: AuthenticationEvidence | None = None
    if auth_evidence is not None:
        if isinstance(auth_evidence, AuthenticationEvidence):
            resolved_auth = auth_evidence
        elif isinstance(auth_evidence, Mapping):
            resolved_auth = AuthenticationEvidence(
                authenticated_identity=auth_evidence.get("authenticated_identity"),
                is_authenticated=bool(auth_evidence.get("is_authenticated", True)),
                credential_type=auth_evidence.get("credential_type"),
                auth_details=dict(auth_evidence.get("auth_details", {})),
                is_complete=bool(auth_evidence.get("is_complete", True)),
                session_id=auth_evidence.get("session_id"),
                metadata=dict(auth_evidence.get("metadata", {})),
            )
        else:
            raise TypeError(f"auth_evidence must be AuthenticationEvidence, Mapping, or None, got {type(auth_evidence).__name__}.")

    reasons: list[AuthorizationReasonCode] = []
    meta = dict(metadata) if metadata is not None else {}

    # 2. Scope Validation: Operation must be a recognized verification operation
    recognized_ops = {op.value for op in VerificationOperation}
    if resolved_request.operation not in recognized_ops:
        reasons.append(AuthorizationReasonCode.UNSUPPORTED_OPERATION)
        meta["operation_scope_error"] = {
            "requested_operation": resolved_request.operation,
            "supported_operations": sorted(recognized_ops),
        }
        return AuthorizationEvidence(
            is_authorized=False,
            is_unauthorized_detected=False,
            is_indeterminate=True,
            status=AuthorizationStatus.INCOMPATIBLE_CONTEXT,
            primary_reason=AuthorizationReasonCode.UNSUPPORTED_OPERATION,
            reason_codes=tuple(reasons),
            participant_identity=resolved_request.participant_identity,
            operation=resolved_request.operation,
            role=resolved_request.role,
            resource_id=resolved_request.resource_id,
            policy_id=resolved_policy.policy_id if resolved_policy else None,
            session_id=resolved_request.session_id,
            configuration_hash=resolved_request.configuration_hash,
            is_evidence_complete=False,
            metadata=meta,
        )

    # 3. Configuration Compatibility Check
    if expected_configuration_hash is not None:
        if resolved_request.configuration_hash != expected_configuration_hash:
            reasons.append(AuthorizationReasonCode.AUTHORIZATION_CONTEXT_MISMATCH)
            meta["configuration_mismatch"] = {
                "expected": expected_configuration_hash,
                "request": resolved_request.configuration_hash,
            }
            return AuthorizationEvidence(
                is_authorized=False,
                is_unauthorized_detected=False,
                is_indeterminate=True,
                status=AuthorizationStatus.INCOMPATIBLE_CONTEXT,
                primary_reason=AuthorizationReasonCode.AUTHORIZATION_CONTEXT_MISMATCH,
                reason_codes=tuple(reasons),
                participant_identity=resolved_request.participant_identity,
                operation=resolved_request.operation,
                role=resolved_request.role,
                resource_id=resolved_request.resource_id,
                policy_id=resolved_policy.policy_id if resolved_policy else None,
                session_id=resolved_request.session_id,
                configuration_hash=resolved_request.configuration_hash,
                is_evidence_complete=False,
                metadata=meta,
            )

    if (
        resolved_policy is not None
        and resolved_policy.configuration_hash is not None
        and resolved_request.configuration_hash is not None
        and resolved_policy.configuration_hash != resolved_request.configuration_hash
    ):
        reasons.append(AuthorizationReasonCode.AUTHORIZATION_CONTEXT_MISMATCH)
        meta["policy_configuration_mismatch"] = {
            "policy": resolved_policy.configuration_hash,
            "request": resolved_request.configuration_hash,
        }
        return AuthorizationEvidence(
            is_authorized=False,
            is_unauthorized_detected=False,
            is_indeterminate=True,
            status=AuthorizationStatus.INCOMPATIBLE_CONTEXT,
            primary_reason=AuthorizationReasonCode.AUTHORIZATION_CONTEXT_MISMATCH,
            reason_codes=tuple(reasons),
            participant_identity=resolved_request.participant_identity,
            operation=resolved_request.operation,
            role=resolved_request.role,
            resource_id=resolved_request.resource_id,
            policy_id=resolved_policy.policy_id,
            session_id=resolved_request.session_id,
            configuration_hash=resolved_request.configuration_hash,
            is_evidence_complete=False,
            metadata=meta,
        )

    # 4. Session Binding Check
    if expected_session_id is not None:
        if resolved_request.session_id != expected_session_id:
            reasons.append(AuthorizationReasonCode.AUTHORIZATION_SESSION_MISMATCH)
            meta["session_mismatch"] = {
                "expected": expected_session_id,
                "request": resolved_request.session_id,
            }
            return AuthorizationEvidence(
                is_authorized=False,
                is_unauthorized_detected=False,
                is_indeterminate=True,
                status=AuthorizationStatus.INCOMPATIBLE_CONTEXT,
                primary_reason=AuthorizationReasonCode.AUTHORIZATION_SESSION_MISMATCH,
                reason_codes=tuple(reasons),
                participant_identity=resolved_request.participant_identity,
                operation=resolved_request.operation,
                role=resolved_request.role,
                resource_id=resolved_request.resource_id,
                policy_id=resolved_policy.policy_id if resolved_policy else None,
                session_id=resolved_request.session_id,
                configuration_hash=resolved_request.configuration_hash,
                is_evidence_complete=False,
                metadata=meta,
            )

    if (
        resolved_policy is not None
        and resolved_policy.session_id is not None
        and resolved_request.session_id is not None
        and resolved_policy.session_id != resolved_request.session_id
    ):
        reasons.append(AuthorizationReasonCode.AUTHORIZATION_SESSION_MISMATCH)
        meta["policy_session_mismatch"] = {
            "policy": resolved_policy.session_id,
            "request": resolved_request.session_id,
        }
        return AuthorizationEvidence(
            is_authorized=False,
            is_unauthorized_detected=False,
            is_indeterminate=True,
            status=AuthorizationStatus.INCOMPATIBLE_CONTEXT,
            primary_reason=AuthorizationReasonCode.AUTHORIZATION_SESSION_MISMATCH,
            reason_codes=tuple(reasons),
            participant_identity=resolved_request.participant_identity,
            operation=resolved_request.operation,
            role=resolved_request.role,
            resource_id=resolved_request.resource_id,
            policy_id=resolved_policy.policy_id,
            session_id=resolved_request.session_id,
            configuration_hash=resolved_request.configuration_hash,
            is_evidence_complete=False,
            metadata=meta,
        )

    # 5. Authentication Prerequisite Verification (M13 Boundary)
    if resolved_auth is not None:
        if resolved_auth.authenticated_identity is None:
            reasons.append(AuthorizationReasonCode.MISSING_AUTHENTICATED_IDENTITY)
            meta["auth_error"] = "Authentication evidence is missing authenticated_identity."
            return AuthorizationEvidence(
                is_authorized=False,
                is_unauthorized_detected=False,
                is_indeterminate=True,
                status=AuthorizationStatus.INCOMPLETE,
                primary_reason=AuthorizationReasonCode.MISSING_AUTHENTICATED_IDENTITY,
                reason_codes=tuple(reasons),
                participant_identity=resolved_request.participant_identity,
                operation=resolved_request.operation,
                role=resolved_request.role,
                resource_id=resolved_request.resource_id,
                policy_id=resolved_policy.policy_id if resolved_policy else None,
                session_id=resolved_request.session_id,
                configuration_hash=resolved_request.configuration_hash,
                is_evidence_complete=False,
                metadata=meta,
            )

        if not resolved_auth.is_authenticated:
            # Authentication failed: M13 handles authentication violation -> M14 must not double-count as ATTACK
            reasons.append(AuthorizationReasonCode.IDENTITY_NOT_AUTHENTICATED)
            meta["auth_error"] = "Authentication explicitly failed for participant."
            return AuthorizationEvidence(
                is_authorized=False,
                is_unauthorized_detected=False,
                is_indeterminate=True,
                status=AuthorizationStatus.INCOMPLETE,
                primary_reason=AuthorizationReasonCode.IDENTITY_NOT_AUTHENTICATED,
                reason_codes=tuple(reasons),
                participant_identity=resolved_request.participant_identity,
                operation=resolved_request.operation,
                role=resolved_request.role,
                resource_id=resolved_request.resource_id,
                policy_id=resolved_policy.policy_id if resolved_policy else None,
                session_id=resolved_request.session_id,
                configuration_hash=resolved_request.configuration_hash,
                is_evidence_complete=False,
                metadata=meta,
            )

        if resolved_auth.authenticated_identity != resolved_request.participant_identity:
            # Claimed identity does not match authenticated identity: owned by M13
            reasons.append(AuthorizationReasonCode.IDENTITY_NOT_AUTHENTICATED)
            reasons.append(AuthorizationReasonCode.CONFLICTING_AUTHORIZATION_EVIDENCE)
            meta["auth_mismatch"] = {
                "request_identity": resolved_request.participant_identity,
                "authenticated_identity": resolved_auth.authenticated_identity,
            }
            return AuthorizationEvidence(
                is_authorized=False,
                is_unauthorized_detected=False,
                is_indeterminate=True,
                status=AuthorizationStatus.CONFLICTING,
                primary_reason=AuthorizationReasonCode.IDENTITY_NOT_AUTHENTICATED,
                reason_codes=tuple(reasons),
                participant_identity=resolved_request.participant_identity,
                operation=resolved_request.operation,
                role=resolved_request.role,
                resource_id=resolved_request.resource_id,
                policy_id=resolved_policy.policy_id if resolved_policy else None,
                session_id=resolved_request.session_id,
                configuration_hash=resolved_request.configuration_hash,
                is_evidence_complete=False,
                metadata=meta,
            )

        if not resolved_auth.is_complete:
            reasons.append(AuthorizationReasonCode.INCOMPLETE_AUTHORIZATION_EVIDENCE)
            meta["auth_error"] = "Authentication evidence is marked incomplete."
            return AuthorizationEvidence(
                is_authorized=False,
                is_unauthorized_detected=False,
                is_indeterminate=True,
                status=AuthorizationStatus.INCOMPLETE,
                primary_reason=AuthorizationReasonCode.INCOMPLETE_AUTHORIZATION_EVIDENCE,
                reason_codes=tuple(reasons),
                participant_identity=resolved_request.participant_identity,
                operation=resolved_request.operation,
                role=resolved_request.role,
                resource_id=resolved_request.resource_id,
                policy_id=resolved_policy.policy_id if resolved_policy else None,
                session_id=resolved_request.session_id,
                configuration_hash=resolved_request.configuration_hash,
                is_evidence_complete=False,
                metadata=meta,
            )

    # 6. Policy Availability & Completeness Check
    if resolved_policy is None:
        reasons.append(AuthorizationReasonCode.MISSING_AUTHORIZATION_POLICY)
        meta["policy_error"] = "No authorization policy provided for verification."
        return AuthorizationEvidence(
            is_authorized=False,
            is_unauthorized_detected=False,
            is_indeterminate=True,
            status=AuthorizationStatus.INCOMPLETE,
            primary_reason=AuthorizationReasonCode.MISSING_AUTHORIZATION_POLICY,
            reason_codes=tuple(reasons),
            participant_identity=resolved_request.participant_identity,
            operation=resolved_request.operation,
            role=resolved_request.role,
            resource_id=resolved_request.resource_id,
            policy_id=None,
            session_id=resolved_request.session_id,
            configuration_hash=resolved_request.configuration_hash,
            is_evidence_complete=False,
            metadata=meta,
        )

    # Empty policy: no allowed or denied rules defined
    is_empty_policy = (
        not resolved_policy.allowed_identities
        and not resolved_policy.allowed_roles
        and not resolved_policy.denied_identities
        and not resolved_policy.denied_roles
        and not resolved_policy.denied_operations
        and not resolved_policy.allowed_resources
        and not resolved_policy.denied_resources
    )
    if is_empty_policy:
        reasons.append(AuthorizationReasonCode.INCOMPLETE_AUTHORIZATION_EVIDENCE)
        meta["policy_error"] = "Verification policy contains no authorization rules."
        return AuthorizationEvidence(
            is_authorized=False,
            is_unauthorized_detected=False,
            is_indeterminate=True,
            status=AuthorizationStatus.INCOMPLETE,
            primary_reason=AuthorizationReasonCode.INCOMPLETE_AUTHORIZATION_EVIDENCE,
            reason_codes=tuple(reasons),
            participant_identity=resolved_request.participant_identity,
            operation=resolved_request.operation,
            role=resolved_request.role,
            resource_id=resolved_request.resource_id,
            policy_id=resolved_policy.policy_id,
            session_id=resolved_request.session_id,
            configuration_hash=resolved_request.configuration_hash,
            is_evidence_complete=False,
            metadata=meta,
        )

    p_id = resolved_request.participant_identity
    p_role = resolved_request.role
    p_op = resolved_request.operation
    p_res = resolved_request.resource_id

    # 7. Conflicting Directives Check
    in_allowed_ids = p_id in resolved_policy.allowed_identities
    in_denied_ids = p_id in resolved_policy.denied_identities
    in_allowed_roles = p_role in resolved_policy.allowed_roles
    in_denied_roles = p_role in resolved_policy.denied_roles
    in_allowed_ops = p_op in resolved_policy.allowed_operations
    in_denied_ops = p_op in resolved_policy.denied_operations
    in_allowed_res = (p_res is not None) and (p_res in resolved_policy.allowed_resources)
    in_denied_res = (p_res is not None) and (p_res in resolved_policy.denied_resources)

    # Contradictory directive: entity, role, operation, or resource simultaneously in allowed and denied sets
    if (
        (in_allowed_ids and in_denied_ids)
        or (in_allowed_roles and in_denied_roles)
        or (in_allowed_ops and in_denied_ops)
        or (in_allowed_res and in_denied_res)
    ):
        reasons.append(AuthorizationReasonCode.CONFLICTING_AUTHORIZATION_EVIDENCE)
        meta["conflict_error"] = "Entity, role, operation, or resource is present in both allowed and denied policy sets."
        return AuthorizationEvidence(
            is_authorized=False,
            is_unauthorized_detected=False,
            is_indeterminate=True,
            status=AuthorizationStatus.CONFLICTING,
            primary_reason=AuthorizationReasonCode.CONFLICTING_AUTHORIZATION_EVIDENCE,
            reason_codes=tuple(reasons),
            participant_identity=p_id,
            operation=p_op,
            role=p_role,
            resource_id=p_res,
            policy_id=resolved_policy.policy_id,
            session_id=resolved_request.session_id,
            configuration_hash=resolved_request.configuration_hash,
            is_evidence_complete=False,
            metadata=meta,
        )

    # Cross-rule conflict: role explicitly allowed, but identity explicitly denied
    if in_allowed_roles and in_denied_ids:
        reasons.append(AuthorizationReasonCode.CONFLICTING_AUTHORIZATION_EVIDENCE)
        meta["conflict_error"] = f"Role '{p_role}' is allowed, but identity '{p_id}' is explicitly denied."
        return AuthorizationEvidence(
            is_authorized=False,
            is_unauthorized_detected=False,
            is_indeterminate=True,
            status=AuthorizationStatus.CONFLICTING,
            primary_reason=AuthorizationReasonCode.CONFLICTING_AUTHORIZATION_EVIDENCE,
            reason_codes=tuple(reasons),
            participant_identity=p_id,
            operation=p_op,
            role=p_role,
            resource_id=p_res,
            policy_id=resolved_policy.policy_id,
            session_id=resolved_request.session_id,
            configuration_hash=resolved_request.configuration_hash,
            is_evidence_complete=False,
            metadata=meta,
        )

    # Cross-rule conflict: identity explicitly allowed, but role explicitly denied
    if in_allowed_ids and in_denied_roles:
        reasons.append(AuthorizationReasonCode.CONFLICTING_AUTHORIZATION_EVIDENCE)
        meta["conflict_error"] = f"Identity '{p_id}' is allowed, but role '{p_role}' is explicitly denied."
        return AuthorizationEvidence(
            is_authorized=False,
            is_unauthorized_detected=False,
            is_indeterminate=True,
            status=AuthorizationStatus.CONFLICTING,
            primary_reason=AuthorizationReasonCode.CONFLICTING_AUTHORIZATION_EVIDENCE,
            reason_codes=tuple(reasons),
            participant_identity=p_id,
            operation=p_op,
            role=p_role,
            resource_id=p_res,
            policy_id=resolved_policy.policy_id,
            session_id=resolved_request.session_id,
            configuration_hash=resolved_request.configuration_hash,
            is_evidence_complete=False,
            metadata=meta,
        )

    # 8. Explicit Denials (Explicit Violation -> ATTACK)
    if in_denied_ids:
        reasons.append(AuthorizationReasonCode.AUTHORIZATION_DENIED)
        meta["denial_reason"] = f"Identity '{p_id}' is explicitly denied by policy."
        return AuthorizationEvidence(
            is_authorized=False,
            is_unauthorized_detected=True,
            is_indeterminate=False,
            status=AuthorizationStatus.UNAUTHORIZED,
            primary_reason=AuthorizationReasonCode.AUTHORIZATION_DENIED,
            reason_codes=tuple(reasons),
            participant_identity=p_id,
            operation=p_op,
            role=p_role,
            resource_id=p_res,
            policy_id=resolved_policy.policy_id,
            session_id=resolved_request.session_id,
            configuration_hash=resolved_request.configuration_hash,
            is_evidence_complete=True,
            metadata=meta,
        )

    if in_denied_roles:
        reasons.append(AuthorizationReasonCode.ROLE_NOT_AUTHORIZED)
        meta["denial_reason"] = f"Role '{p_role}' is explicitly denied by policy."
        return AuthorizationEvidence(
            is_authorized=False,
            is_unauthorized_detected=True,
            is_indeterminate=False,
            status=AuthorizationStatus.UNAUTHORIZED,
            primary_reason=AuthorizationReasonCode.ROLE_NOT_AUTHORIZED,
            reason_codes=tuple(reasons),
            participant_identity=p_id,
            operation=p_op,
            role=p_role,
            resource_id=p_res,
            policy_id=resolved_policy.policy_id,
            session_id=resolved_request.session_id,
            configuration_hash=resolved_request.configuration_hash,
            is_evidence_complete=True,
            metadata=meta,
        )

    if in_denied_ops:
        reasons.append(AuthorizationReasonCode.OPERATION_NOT_PERMITTED)
        meta["denial_reason"] = f"Operation '{p_op}' is explicitly denied by policy."
        return AuthorizationEvidence(
            is_authorized=False,
            is_unauthorized_detected=True,
            is_indeterminate=False,
            status=AuthorizationStatus.UNAUTHORIZED,
            primary_reason=AuthorizationReasonCode.OPERATION_NOT_PERMITTED,
            reason_codes=tuple(reasons),
            participant_identity=p_id,
            operation=p_op,
            role=p_role,
            resource_id=p_res,
            policy_id=resolved_policy.policy_id,
            session_id=resolved_request.session_id,
            configuration_hash=resolved_request.configuration_hash,
            is_evidence_complete=True,
            metadata=meta,
        )

    if in_denied_res:
        reasons.append(AuthorizationReasonCode.RESOURCE_NOT_AUTHORIZED)
        meta["denial_reason"] = f"Resource '{p_res}' is explicitly denied by policy."
        return AuthorizationEvidence(
            is_authorized=False,
            is_unauthorized_detected=True,
            is_indeterminate=False,
            status=AuthorizationStatus.UNAUTHORIZED,
            primary_reason=AuthorizationReasonCode.RESOURCE_NOT_AUTHORIZED,
            reason_codes=tuple(reasons),
            participant_identity=p_id,
            operation=p_op,
            role=p_role,
            resource_id=p_res,
            policy_id=resolved_policy.policy_id,
            session_id=resolved_request.session_id,
            configuration_hash=resolved_request.configuration_hash,
            is_evidence_complete=True,
            metadata=meta,
        )

    # 9. Operation and Resource Restrictions
    if resolved_policy.allowed_operations and p_op not in resolved_policy.allowed_operations:
        reasons.append(AuthorizationReasonCode.OPERATION_NOT_PERMITTED)
        meta["restriction_error"] = f"Operation '{p_op}' is not in allowed_operations for policy."
        return AuthorizationEvidence(
            is_authorized=False,
            is_unauthorized_detected=True,
            is_indeterminate=False,
            status=AuthorizationStatus.UNAUTHORIZED,
            primary_reason=AuthorizationReasonCode.OPERATION_NOT_PERMITTED,
            reason_codes=tuple(reasons),
            participant_identity=p_id,
            operation=p_op,
            role=p_role,
            resource_id=p_res,
            policy_id=resolved_policy.policy_id,
            session_id=resolved_request.session_id,
            configuration_hash=resolved_request.configuration_hash,
            is_evidence_complete=True,
            metadata=meta,
        )

    if resolved_policy.allowed_resources:
        if p_res is None or p_res not in resolved_policy.allowed_resources:
            reasons.append(AuthorizationReasonCode.RESOURCE_NOT_AUTHORIZED)
            meta["restriction_error"] = f"Resource '{p_res}' is not permitted by policy."
            return AuthorizationEvidence(
                is_authorized=False,
                is_unauthorized_detected=True,
                is_indeterminate=False,
                status=AuthorizationStatus.UNAUTHORIZED,
                primary_reason=AuthorizationReasonCode.RESOURCE_NOT_AUTHORIZED,
                reason_codes=tuple(reasons),
                participant_identity=p_id,
                operation=p_op,
                role=p_role,
                resource_id=p_res,
                policy_id=resolved_policy.policy_id,
                session_id=resolved_request.session_id,
                configuration_hash=resolved_request.configuration_hash,
                is_evidence_complete=True,
                metadata=meta,
            )

    # 10. Whitelist Enforcement (Roles & Identities)
    # If allowed_roles is non-empty, role must be permitted
    if resolved_policy.allowed_roles and not in_allowed_roles:
        reasons.append(AuthorizationReasonCode.ROLE_NOT_AUTHORIZED)
        meta["denial_reason"] = f"Role '{p_role}' is not in allowed_roles: {resolved_policy.allowed_roles}."
        return AuthorizationEvidence(
            is_authorized=False,
            is_unauthorized_detected=True,
            is_indeterminate=False,
            status=AuthorizationStatus.UNAUTHORIZED,
            primary_reason=AuthorizationReasonCode.ROLE_NOT_AUTHORIZED,
            reason_codes=tuple(reasons),
            participant_identity=p_id,
            operation=p_op,
            role=p_role,
            resource_id=p_res,
            policy_id=resolved_policy.policy_id,
            session_id=resolved_request.session_id,
            configuration_hash=resolved_request.configuration_hash,
            is_evidence_complete=True,
            metadata=meta,
        )

    # If allowed_identities is non-empty, identity must be permitted
    if resolved_policy.allowed_identities and not in_allowed_ids:
        reasons.append(AuthorizationReasonCode.AUTHORIZATION_DENIED)
        meta["denial_reason"] = f"Identity '{p_id}' is not in allowed_identities: {resolved_policy.allowed_identities}."
        return AuthorizationEvidence(
            is_authorized=False,
            is_unauthorized_detected=True,
            is_indeterminate=False,
            status=AuthorizationStatus.UNAUTHORIZED,
            primary_reason=AuthorizationReasonCode.AUTHORIZATION_DENIED,
            reason_codes=tuple(reasons),
            participant_identity=p_id,
            operation=p_op,
            role=p_role,
            resource_id=p_res,
            policy_id=resolved_policy.policy_id,
            session_id=resolved_request.session_id,
            configuration_hash=resolved_request.configuration_hash,
            is_evidence_complete=True,
            metadata=meta,
        )

    # 11. Granted: All policy checks successfully passed
    reasons.append(AuthorizationReasonCode.AUTHORIZATION_GRANTED)
    return AuthorizationEvidence(
        is_authorized=True,
        is_unauthorized_detected=False,
        is_indeterminate=False,
        status=AuthorizationStatus.AUTHORIZED,
        primary_reason=AuthorizationReasonCode.AUTHORIZATION_GRANTED,
        reason_codes=tuple(reasons),
        participant_identity=p_id,
        operation=p_op,
        role=p_role,
        resource_id=p_res,
        policy_id=resolved_policy.policy_id,
        session_id=resolved_request.session_id,
        configuration_hash=resolved_request.configuration_hash,
        is_evidence_complete=True,
        metadata=meta,
    )


# ==============================================================================
# M14 -> M12 Integration Adapter
# ==============================================================================

def evaluate_authorization_decision(
    request: AuthorizationRequest | Mapping[str, Any],
    policy: VerificationPolicy | Mapping[str, Any] | None = None,
    threshold_report: PolicyEvaluationReport | None = None,
    auth_evidence: AuthenticationEvidence | Mapping[str, Any] | None = None,
    expected_session_id: str | None = None,
    expected_configuration_hash: str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> DecisionResult:
    """Evaluate an end-to-end security verdict integrating M14 Authorization with M12 Decision Engine.

    Execution Flow:
        1. Evaluates request, policy, and optional auth_evidence via evaluate_verification_authorization().
        2. Converts resulting AuthorizationEvidence into M12 ProtocolSecurityEvidence.
        3. Submits ProtocolSecurityEvidence along with threshold_report to M12 evaluate_security_decision().

    Args:
        request: AuthorizationRequest or mapping representing the verification request.
        policy: Optional VerificationPolicy or mapping defining authorization rules.
        threshold_report: Optional M11 PolicyEvaluationReport summarizing quantum/statistical checks.
        auth_evidence: Optional AuthenticationEvidence or mapping proving identity.
        expected_session_id: Optional expected session identifier.
        expected_configuration_hash: Optional expected configuration hash.
        metadata: Optional evaluation context metadata.

    Returns:
        Immutable DecisionResult containing the final security verdict (ACCEPT, SUSPICIOUS, ATTACK).
    """
    auth_ev = evaluate_verification_authorization(
        request=request,
        policy=policy,
        auth_evidence=auth_evidence,
        expected_session_id=expected_session_id,
        expected_configuration_hash=expected_configuration_hash,
        metadata=metadata,
    )

    proto_ev = auth_ev.to_protocol_security_evidence()

    config_hash = expected_configuration_hash
    if config_hash is None:
        config_hash = auth_ev.configuration_hash

    combined_meta = dict(metadata) if metadata is not None else {}
    combined_meta["authorization_evidence"] = {
        "status": auth_ev.status.value,
        "primary_reason": auth_ev.primary_reason.value,
        "is_authorized": auth_ev.is_authorized,
        "is_unauthorized_detected": auth_ev.is_unauthorized_detected,
        "is_indeterminate": auth_ev.is_indeterminate,
    }

    return evaluate_security_decision(
        threshold_report=threshold_report,
        protocol_evidence=proto_ev,
        expected_configuration_hash=config_hash,
        metadata=combined_meta,
    )

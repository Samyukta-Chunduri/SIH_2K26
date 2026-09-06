"""Q-SHIELD — Impersonation Detection Layer (Milestone M13).

Detects entities attempting to participate in or authenticate within the Q-SHIELD
protocol while claiming an identity that they are not legitimately authorized or
authenticated to represent.

Conceptual Model:
    Expected Authorized Identity
            ↓
    Claimed Identity
            ↓
    Authentication / Identity Evidence
            ↓
    Deterministic Validation & Authority Hierarchy
            ↓
    Impersonation Evidence (ImpersonationEvidence)
            ↓
    Protocol Security Evidence (ProtocolSecurityEvidence)
            ↓
    Decision Engine (M12 evaluate_security_decision)
            ↓
    DecisionResult (ACCEPT / SUSPICIOUS / ATTACK)

Identity Authority Model:
    - authenticated_identity is authoritative for who the participant actually is.
    - expected_identity is authoritative for who the session/protocol context permits.
    - claimed_identity is the asserted claim that must agree with both.
    - When claimed != authenticated: AUTHENTICATED_IDENTITY_MISMATCH (Explicit Violation -> ATTACK).
    - When claimed != expected: CLAIMED_IDENTITY_MISMATCH (Explicit Violation -> ATTACK).
    - When claimed, authenticated, and expected all differ: CONFLICTING_IDENTITY_EVIDENCE.
    - When authentication is missing or incomplete: INCOMPLETE (Indeterminate -> SUSPICIOUS).
    - When authentication explicitly fails: AUTHENTICATION_FAILED (Explicit Violation -> ATTACK).

Scientific & Scope Invariants:
    1. Quantum Anomaly != Impersonation: Physical noise, decoherence, and threshold
       exceedance indicate operational/physical deviations, NOT confirmed impersonation.
    2. Impersonation != Replay: Reused nonces, timestamps, and session freshness
       belong strictly to Replay Detection.
    3. Impersonation != Signature Forgery: Mathematical signature invalidity belongs
       strictly to Signature Forgery Detection.
    4. Impersonation != Unauthorized Verification: A valid identity lacking verification
       permission belongs strictly to M14 (Unauthorized Verification).
    5. Impersonation != Quantum Channel Attack: Physical channel eavesdropping or
       tampering belongs strictly to M15 (Quantum Channel Attacks).
    6. Missing Evidence != Confirmed Impersonation: Missing or incomplete authentication
       evidence produces indeterminate/incomplete status (evaluating to SUSPICIOUS in M12),
       NEVER an automatic ATTACK verdict.
    7. Explicit Violation Produces ATTACK: Confirmed identity mismatch or failed authentication
       evidence constitutes explicit security violation evidence for M12 ATTACK.
    8. Strictly NO composite security scores, trust scores, risk scores, or scalar collapsing.
    9. Strictly NO real-world authentication infrastructure (OAuth, JWT, X.509, TLS, blockchain).
    10. Zero Secret Leakage: Evidence containers never store raw passwords, private keys, or credentials.
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

class IdentityEvidenceStatus(str, Enum):
    """Categorical status of identity and authentication evaluation.

    VALID: Claimed identity matches expected and authenticated identity; authentication valid.
    IDENTITY_MISMATCH: Claimed identity does not match expected identity, or does not match
                       authoritatively authenticated identity.
    AUTHENTICATION_FAILED: Authentication evidence explicitly failed validation.
    INCOMPLETE: Required identity claim or authentication evidence is missing or incomplete.
    CONFLICTING: Contradictory identity assertions present across claimed, expected, and authenticated identities.
    INCOMPATIBLE_CONTEXT: Session ID or baseline configuration hash mismatch between claim
                          and evaluation context.
    """

    VALID = "VALID"
    IDENTITY_MISMATCH = "IDENTITY_MISMATCH"
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    INCOMPLETE = "INCOMPLETE"
    CONFLICTING = "CONFLICTING"
    INCOMPATIBLE_CONTEXT = "INCOMPATIBLE_CONTEXT"


class ImpersonationReasonCode(str, Enum):
    """Stable, canonical reason codes explaining why an impersonation decision was reached."""

    IDENTITY_VERIFIED = "IDENTITY_VERIFIED"
    CLAIMED_IDENTITY_MISMATCH = "CLAIMED_IDENTITY_MISMATCH"
    AUTHENTICATED_IDENTITY_MISMATCH = "AUTHENTICATED_IDENTITY_MISMATCH"
    AUTHENTICATION_INVALID = "AUTHENTICATION_INVALID"
    MISSING_IDENTITY_CLAIM = "MISSING_IDENTITY_CLAIM"
    MISSING_EXPECTED_IDENTITY = "MISSING_EXPECTED_IDENTITY"
    MISSING_AUTHENTICATION_EVIDENCE = "MISSING_AUTHENTICATION_EVIDENCE"
    INCOMPLETE_AUTHENTICATION_EVIDENCE = "INCOMPLETE_AUTHENTICATION_EVIDENCE"
    IDENTITY_SESSION_MISMATCH = "IDENTITY_SESSION_MISMATCH"
    IDENTITY_CONTEXT_MISMATCH = "IDENTITY_CONTEXT_MISMATCH"
    CONFLICTING_IDENTITY_EVIDENCE = "CONFLICTING_IDENTITY_EVIDENCE"


# ==============================================================================
# Evidence Containers
# ==============================================================================

@dataclass(frozen=True)
class IdentityClaim:
    """Immutable identity claim submitted by or on behalf of a protocol participant.

    Attributes:
        claimed_identity: Identifier claimed by the participant (e.g., 'Alice', 'Signer_1').
        expected_identity: Optional expected identifier established by protocol context.
        role: Protocol role of the participant (e.g., 'SIGNER', 'VERIFIER'). Default: 'SIGNER'.
        session_id: Optional session identifier binding the claim to an execution.
        configuration_hash: Optional canonical baseline configuration hash binding.
        metadata: Contextual metadata dictionary.
    """

    claimed_identity: str
    expected_identity: str | None = None
    role: str = "SIGNER"
    session_id: str | None = None
    configuration_hash: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate input types, reject whitespace, prevent secret leakage, and defensively copy."""
        if not isinstance(self.claimed_identity, str):
            raise TypeError(f"claimed_identity must be str, got {type(self.claimed_identity).__name__}.")
        if not self.claimed_identity.strip():
            raise ValueError("claimed_identity cannot be empty or whitespace.")

        if self.expected_identity is not None:
            if not isinstance(self.expected_identity, str):
                raise TypeError(f"expected_identity must be str or None, got {type(self.expected_identity).__name__}.")
            if not self.expected_identity.strip():
                raise ValueError("expected_identity cannot be empty or whitespace when provided.")

        if not isinstance(self.role, str) or not self.role.strip():
            raise ValueError("role must be a non-empty string.")

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

        _check_for_secret_leakage(self.metadata, "IdentityClaim.metadata")
        object.__setattr__(self, "metadata", _deep_freeze_dict(self.metadata))


@dataclass(frozen=True)
class AuthenticationEvidence:
    """Immutable evidence produced by an authentication or credential-validation mechanism.

    Research Prototype Boundary:
        Represents explicit, typed authentication facts. Does NOT simulate production
        OAuth/TLS/PKI infrastructure.
        Zero secret leakage: rejects raw passwords, private keys, or cryptographic secrets.

    Attributes:
        authenticated_identity: Authoritative identity established by authentication (if any).
        is_authenticated: True if authentication verification succeeded, False if explicitly failed.
        credential_type: Type of credential evaluated (e.g. 'PRE_SHARED_KEY', 'PROTOCOL_NONCE').
        auth_details: Machine-readable details regarding the authentication check.
        is_complete: Whether authentication evaluation was completely executed. Default: True.
        session_id: Optional session identifier bound to this authentication evidence.
        metadata: Contextual evaluation metadata.
    """

    authenticated_identity: str | None = None
    is_authenticated: bool = True
    credential_type: str | None = None
    auth_details: dict[str, Any] = field(default_factory=dict)
    is_complete: bool = True
    session_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate typing, reject whitespace, prevent secret leakage, and defensively copy."""
        if self.authenticated_identity is not None:
            if not isinstance(self.authenticated_identity, str):
                raise TypeError(f"authenticated_identity must be str or None, got {type(self.authenticated_identity).__name__}.")
            if not self.authenticated_identity.strip():
                raise ValueError("authenticated_identity cannot be empty or whitespace when provided.")

        if not isinstance(self.is_authenticated, bool):
            raise TypeError(f"is_authenticated must be bool, got {type(self.is_authenticated).__name__}.")

        if not isinstance(self.is_complete, bool):
            raise TypeError(f"is_complete must be bool, got {type(self.is_complete).__name__}.")

        if self.credential_type is not None:
            if not isinstance(self.credential_type, str):
                raise TypeError(f"credential_type must be str or None, got {type(self.credential_type).__name__}.")
            if not self.credential_type.strip():
                raise ValueError("credential_type cannot be empty or whitespace when provided.")

        if self.session_id is not None:
            if not isinstance(self.session_id, str):
                raise TypeError(f"session_id must be str or None, got {type(self.session_id).__name__}.")
            if not self.session_id.strip():
                raise ValueError("session_id cannot be empty or whitespace when provided.")

        # Zero Secret Leakage enforcement
        _check_for_secret_leakage(self.auth_details, "AuthenticationEvidence.auth_details")
        _check_for_secret_leakage(self.metadata, "AuthenticationEvidence.metadata")

        object.__setattr__(self, "auth_details", _deep_freeze_dict(self.auth_details))
        object.__setattr__(self, "metadata", _deep_freeze_dict(self.metadata))


@dataclass(frozen=True)
class ImpersonationEvidence:
    """Immutable evidence record produced by the impersonation detector.

    Scientific Principle:
        Captures explicit, inspectable identity verification facts.
        Directly converts to M12 ProtocolSecurityEvidence for unified security decisions.

    Attributes:
        is_impersonation_detected: True if a confirmed identity violation is established.
        is_indeterminate: True if identity could not be established due to missing/incomplete data.
        status: IdentityEvidenceStatus indicating categorical outcome.
        primary_reason: Top canonical reason code driving the evaluation.
        reason_codes: Sorted, deduplicated tuple of all applicable reason codes.
        expected_identity: Expected participant identifier.
        claimed_identity: Claimed participant identifier.
        authenticated_identity: Identity established by authentication.
        session_id: Session identifier bound to the evaluation.
        configuration_hash: Canonical configuration hash bound to the evaluation.
        is_evidence_complete: Whether all required identity/auth evidence was present.
        timestamp: ISO 8601 UTC timestamp.
        metadata: Contextual evaluation metadata.
    """

    is_impersonation_detected: bool
    is_indeterminate: bool
    status: IdentityEvidenceStatus
    primary_reason: ImpersonationReasonCode
    reason_codes: tuple[ImpersonationReasonCode, ...]
    expected_identity: str | None
    claimed_identity: str | None
    authenticated_identity: str | None
    session_id: str | None = None
    configuration_hash: str | None = None
    is_evidence_complete: bool = True
    timestamp: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate fields, normalize collections, and generate timestamp."""
        if not isinstance(self.is_impersonation_detected, bool):
            raise TypeError(f"is_impersonation_detected must be bool, got {type(self.is_impersonation_detected).__name__}.")
        if not isinstance(self.is_indeterminate, bool):
            raise TypeError(f"is_indeterminate must be bool, got {type(self.is_indeterminate).__name__}.")
        if not isinstance(self.status, IdentityEvidenceStatus):
            raise TypeError(f"status must be IdentityEvidenceStatus, got {type(self.status).__name__}.")
        if not isinstance(self.primary_reason, ImpersonationReasonCode):
            raise TypeError(f"primary_reason must be ImpersonationReasonCode, got {type(self.primary_reason).__name__}.")

        object.__setattr__(self, "reason_codes", tuple(sorted(set(self.reason_codes), key=lambda x: x.value)))
        object.__setattr__(self, "metadata", _deep_freeze_dict(self.metadata))

        if not self.timestamp:
            object.__setattr__(self, "timestamp", datetime.now(timezone.utc).isoformat())

    def to_protocol_security_evidence(self) -> ProtocolSecurityEvidence:
        """Convert this ImpersonationEvidence into M12 ProtocolSecurityEvidence.

        Scientific Contract:
            - If is_impersonation_detected is True:
                Produces explicit_violation=True, violation_type='IMPERSONATION'.
                In M12, this triggers PRECEDENCE 1 -> ATTACK.
            - If is_indeterminate is True:
                Produces explicit_violation=False, is_complete=False.
                In M12, this triggers PRECEDENCE 3 -> SUSPICIOUS.
            - If legitimate and complete:
                Produces explicit_violation=False, is_complete=True.
                In M12, this allows PRECEDENCE 5 -> ACCEPT (provided quantum metrics agree).
        """
        if self.is_impersonation_detected:
            return ProtocolSecurityEvidence(
                explicit_violation=True,
                violation_type="IMPERSONATION",
                violation_details={
                    "status": self.status.value,
                    "primary_reason": self.primary_reason.value,
                    "reason_codes": [r.value for r in self.reason_codes],
                    "expected_identity": self.expected_identity,
                    "claimed_identity": self.claimed_identity,
                    "authenticated_identity": self.authenticated_identity,
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
            },
            is_complete=True,
            session_id=self.session_id,
            metadata=dict(self.metadata),
        )


# ==============================================================================
# Detector Implementation
# ==============================================================================

def detect_impersonation(
    claim: IdentityClaim | Mapping[str, Any],
    auth_evidence: AuthenticationEvidence | Mapping[str, Any] | None = None,
    expected_identity: str | None = None,
    expected_session_id: str | None = None,
    expected_configuration_hash: str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> ImpersonationEvidence:
    """Evaluate identity claim and authentication evidence to detect participant impersonation.

    Deterministic Evaluation & Authority Hierarchy:
        1. Malformed / Invalid Input Types -> TypeError / ValueError
        2. Configuration Incompatibility -> INCOMPATIBLE_CONTEXT (Indeterminate -> SUSPICIOUS in M12)
        3. Session Binding Mismatch -> INCOMPATIBLE_CONTEXT / IDENTITY_SESSION_MISMATCH (Indeterminate -> SUSPICIOUS in M12)
        4. Missing Authentication Evidence -> INCOMPLETE (Indeterminate -> SUSPICIOUS in M12)
        5. Incomplete Authentication Evidence -> INCOMPLETE (Indeterminate -> SUSPICIOUS in M12)
        6. Explicit Authentication Failure -> AUTHENTICATION_FAILED (Explicit Violation -> ATTACK in M12)
        7. Missing Authenticated Identity -> INCOMPLETE (Indeterminate -> SUSPICIOUS in M12)
        8. Authority Evaluation (Claimed vs Authenticated vs Expected):
           - Claimed != Authenticated AND Claimed != Expected -> CONFLICTING (Explicit Violation -> ATTACK in M12)
           - Claimed != Authenticated -> IDENTITY_MISMATCH (Explicit Violation -> ATTACK in M12)
           - Claimed != Expected -> IDENTITY_MISMATCH (Explicit Violation -> ATTACK in M12)
        9. Consistent & Valid Identity -> VALID (Clean evidence -> ACCEPT in M12)

    Args:
        claim: IdentityClaim or mapping representing the participant's identity assertion.
        auth_evidence: Optional AuthenticationEvidence or mapping proving identity.
        expected_identity: Optional expected identifier overriding or verifying claim.
        expected_session_id: Optional expected session identifier to enforce binding.
        expected_configuration_hash: Optional canonical configuration hash to enforce binding.
        metadata: Optional evaluation context metadata.

    Returns:
        Immutable ImpersonationEvidence containing categorical status and explainable reason codes.

    Raises:
        TypeError: If arguments have invalid types.
        ValueError: If claim or context fields contain empty or malformed strings.
    """
    # 1. Input Type Normalization & Explicit Parameter Validation
    if expected_identity is not None:
        if not isinstance(expected_identity, str):
            raise TypeError(f"expected_identity must be str or None, got {type(expected_identity).__name__}.")
        if not expected_identity.strip():
            raise ValueError("expected_identity cannot be empty or whitespace when provided.")

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

    resolved_claim: IdentityClaim
    if isinstance(claim, IdentityClaim):
        resolved_claim = claim
    elif isinstance(claim, Mapping):
        claimed_id = claim.get("claimed_identity")
        if claimed_id is None:
            raise TypeError("claim mapping must contain a string 'claimed_identity'.")
        if not isinstance(claimed_id, str):
            raise TypeError(f"claimed_identity must be str, got {type(claimed_id).__name__}.")
        resolved_claim = IdentityClaim(
            claimed_identity=claimed_id,
            expected_identity=claim.get("expected_identity"),
            role=str(claim.get("role", "SIGNER")),
            session_id=claim.get("session_id"),
            configuration_hash=claim.get("configuration_hash"),
            metadata=dict(claim.get("metadata", {})),
        )
    else:
        raise TypeError(f"claim must be IdentityClaim or Mapping, got {type(claim).__name__}.")

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

    # Resolve expected identity: explicit argument takes precedence over claim's embedded expected_identity
    effective_expected_id = expected_identity if expected_identity is not None else resolved_claim.expected_identity

    # Collect reason codes
    reasons: list[ImpersonationReasonCode] = []
    meta = dict(metadata) if metadata is not None else {}

    # 2. Configuration Compatibility Check
    # If expected_configuration_hash is required, claim's configuration_hash must match it
    if expected_configuration_hash is not None:
        if resolved_claim.configuration_hash != expected_configuration_hash:
            reasons.append(ImpersonationReasonCode.IDENTITY_CONTEXT_MISMATCH)
            meta["configuration_mismatch"] = {
                "expected": expected_configuration_hash,
                "claimed": resolved_claim.configuration_hash,
            }
            return ImpersonationEvidence(
                is_impersonation_detected=False,
                is_indeterminate=True,
                status=IdentityEvidenceStatus.INCOMPATIBLE_CONTEXT,
                primary_reason=ImpersonationReasonCode.IDENTITY_CONTEXT_MISMATCH,
                reason_codes=tuple(reasons),
                expected_identity=effective_expected_id,
                claimed_identity=resolved_claim.claimed_identity,
                authenticated_identity=resolved_auth.authenticated_identity if resolved_auth else None,
                session_id=resolved_claim.session_id,
                configuration_hash=resolved_claim.configuration_hash,
                is_evidence_complete=False,
                metadata=meta,
            )

    # 3. Session Binding Check
    # Check claim session against expected session
    if expected_session_id is not None:
        if resolved_claim.session_id != expected_session_id:
            reasons.append(ImpersonationReasonCode.IDENTITY_SESSION_MISMATCH)
            meta["session_mismatch"] = {
                "expected": expected_session_id,
                "claimed": resolved_claim.session_id,
            }
            return ImpersonationEvidence(
                is_impersonation_detected=False,
                is_indeterminate=True,
                status=IdentityEvidenceStatus.INCOMPATIBLE_CONTEXT,
                primary_reason=ImpersonationReasonCode.IDENTITY_SESSION_MISMATCH,
                reason_codes=tuple(reasons),
                expected_identity=effective_expected_id,
                claimed_identity=resolved_claim.claimed_identity,
                authenticated_identity=resolved_auth.authenticated_identity if resolved_auth else None,
                session_id=resolved_claim.session_id,
                configuration_hash=resolved_claim.configuration_hash,
                is_evidence_complete=False,
                metadata=meta,
            )

    # Check claim session against auth evidence session
    if (
        resolved_auth is not None
        and resolved_auth.session_id is not None
        and resolved_claim.session_id is not None
        and resolved_auth.session_id != resolved_claim.session_id
    ):
        reasons.append(ImpersonationReasonCode.IDENTITY_SESSION_MISMATCH)
        meta["auth_session_mismatch"] = {
            "claim_session": resolved_claim.session_id,
            "auth_session": resolved_auth.session_id,
        }
        return ImpersonationEvidence(
            is_impersonation_detected=False,
            is_indeterminate=True,
            status=IdentityEvidenceStatus.INCOMPATIBLE_CONTEXT,
            primary_reason=ImpersonationReasonCode.IDENTITY_SESSION_MISMATCH,
            reason_codes=tuple(reasons),
            expected_identity=effective_expected_id,
            claimed_identity=resolved_claim.claimed_identity,
            authenticated_identity=resolved_auth.authenticated_identity,
            session_id=resolved_claim.session_id,
            configuration_hash=resolved_claim.configuration_hash,
            is_evidence_complete=False,
            metadata=meta,
        )

    # 4. Missing Authentication Evidence Check
    # Scientific Principle: Missing evidence != Confirmed Attack.
    # Yields indeterminate / incomplete evidence -> SUSPICIOUS in M12.
    if resolved_auth is None:
        reasons.append(ImpersonationReasonCode.MISSING_AUTHENTICATION_EVIDENCE)
        return ImpersonationEvidence(
            is_impersonation_detected=False,
            is_indeterminate=True,
            status=IdentityEvidenceStatus.INCOMPLETE,
            primary_reason=ImpersonationReasonCode.MISSING_AUTHENTICATION_EVIDENCE,
            reason_codes=tuple(reasons),
            expected_identity=effective_expected_id,
            claimed_identity=resolved_claim.claimed_identity,
            authenticated_identity=None,
            session_id=resolved_claim.session_id,
            configuration_hash=resolved_claim.configuration_hash,
            is_evidence_complete=False,
            metadata=meta,
        )

    # 5. Incomplete Authentication Evidence Check
    if not resolved_auth.is_complete:
        reasons.append(ImpersonationReasonCode.INCOMPLETE_AUTHENTICATION_EVIDENCE)
        return ImpersonationEvidence(
            is_impersonation_detected=False,
            is_indeterminate=True,
            status=IdentityEvidenceStatus.INCOMPLETE,
            primary_reason=ImpersonationReasonCode.INCOMPLETE_AUTHENTICATION_EVIDENCE,
            reason_codes=tuple(reasons),
            expected_identity=effective_expected_id,
            claimed_identity=resolved_claim.claimed_identity,
            authenticated_identity=resolved_auth.authenticated_identity,
            session_id=resolved_claim.session_id,
            configuration_hash=resolved_claim.configuration_hash,
            is_evidence_complete=False,
            metadata=meta,
        )

    # 6. Explicit Authentication Failure Check (Explicit Security Violation)
    if not resolved_auth.is_authenticated:
        reasons.append(ImpersonationReasonCode.AUTHENTICATION_INVALID)
        if (
            resolved_auth.authenticated_identity is not None
            and resolved_auth.authenticated_identity != resolved_claim.claimed_identity
        ):
            reasons.append(ImpersonationReasonCode.AUTHENTICATED_IDENTITY_MISMATCH)
        if (
            effective_expected_id is not None
            and resolved_claim.claimed_identity != effective_expected_id
        ):
            reasons.append(ImpersonationReasonCode.CLAIMED_IDENTITY_MISMATCH)

        return ImpersonationEvidence(
            is_impersonation_detected=True,
            is_indeterminate=False,
            status=IdentityEvidenceStatus.AUTHENTICATION_FAILED,
            primary_reason=ImpersonationReasonCode.AUTHENTICATION_INVALID,
            reason_codes=tuple(reasons),
            expected_identity=effective_expected_id,
            claimed_identity=resolved_claim.claimed_identity,
            authenticated_identity=resolved_auth.authenticated_identity,
            session_id=resolved_claim.session_id,
            configuration_hash=resolved_claim.configuration_hash,
            is_evidence_complete=True,
            metadata=meta,
        )

    # 7. Missing Authenticated Identity Check
    # If is_authenticated is True but authenticated_identity is None, the mechanism verified
    # a credential but failed to attribute who the entity is. This cannot verify a named claim.
    if resolved_auth.authenticated_identity is None:
        reasons.append(ImpersonationReasonCode.INCOMPLETE_AUTHENTICATION_EVIDENCE)
        return ImpersonationEvidence(
            is_impersonation_detected=False,
            is_indeterminate=True,
            status=IdentityEvidenceStatus.INCOMPLETE,
            primary_reason=ImpersonationReasonCode.INCOMPLETE_AUTHENTICATION_EVIDENCE,
            reason_codes=tuple(reasons),
            expected_identity=effective_expected_id,
            claimed_identity=resolved_claim.claimed_identity,
            authenticated_identity=None,
            session_id=resolved_claim.session_id,
            configuration_hash=resolved_claim.configuration_hash,
            is_evidence_complete=False,
            metadata=meta,
        )

    # 8. Authority & Identity Discrepancy Evaluation
    claimed_id = resolved_claim.claimed_identity
    auth_id = resolved_auth.authenticated_identity

    auth_mismatch = auth_id != claimed_id
    expected_mismatch = (effective_expected_id is not None) and (claimed_id != effective_expected_id)
    auth_expected_mismatch = (effective_expected_id is not None) and (auth_id != effective_expected_id)

    # Multi-assertional conflict: claimed, expected, and authenticated disagree across multiple boundaries
    if (auth_mismatch and expected_mismatch) or (auth_mismatch and not auth_expected_mismatch):
        reasons.append(ImpersonationReasonCode.AUTHENTICATED_IDENTITY_MISMATCH)
        reasons.append(ImpersonationReasonCode.CLAIMED_IDENTITY_MISMATCH)
        reasons.append(ImpersonationReasonCode.CONFLICTING_IDENTITY_EVIDENCE)
        meta["identity_conflict"] = {
            "claimed": claimed_id,
            "authenticated": auth_id,
            "expected": effective_expected_id,
        }
        return ImpersonationEvidence(
            is_impersonation_detected=True,
            is_indeterminate=False,
            status=IdentityEvidenceStatus.CONFLICTING,
            primary_reason=ImpersonationReasonCode.AUTHENTICATED_IDENTITY_MISMATCH,
            reason_codes=tuple(reasons),
            expected_identity=effective_expected_id,
            claimed_identity=claimed_id,
            authenticated_identity=auth_id,
            session_id=resolved_claim.session_id,
            configuration_hash=resolved_claim.configuration_hash,
            is_evidence_complete=True,
            metadata=meta,
        )

    # Claimed vs Authenticated Mismatch (Entity authenticated as someone else)
    if auth_mismatch:
        reasons.append(ImpersonationReasonCode.AUTHENTICATED_IDENTITY_MISMATCH)
        meta["identity_discrepancy"] = {
            "claimed": claimed_id,
            "authenticated": auth_id,
        }
        return ImpersonationEvidence(
            is_impersonation_detected=True,
            is_indeterminate=False,
            status=IdentityEvidenceStatus.IDENTITY_MISMATCH,
            primary_reason=ImpersonationReasonCode.AUTHENTICATED_IDENTITY_MISMATCH,
            reason_codes=tuple(reasons),
            expected_identity=effective_expected_id,
            claimed_identity=claimed_id,
            authenticated_identity=auth_id,
            session_id=resolved_claim.session_id,
            configuration_hash=resolved_claim.configuration_hash,
            is_evidence_complete=True,
            metadata=meta,
        )

    # Claimed vs Expected Mismatch (Claimed/Authenticated entity is not the expected participant)
    if expected_mismatch:
        reasons.append(ImpersonationReasonCode.CLAIMED_IDENTITY_MISMATCH)
        meta["expected_discrepancy"] = {
            "claimed": claimed_id,
            "expected": effective_expected_id,
        }
        return ImpersonationEvidence(
            is_impersonation_detected=True,
            is_indeterminate=False,
            status=IdentityEvidenceStatus.IDENTITY_MISMATCH,
            primary_reason=ImpersonationReasonCode.CLAIMED_IDENTITY_MISMATCH,
            reason_codes=tuple(reasons),
            expected_identity=effective_expected_id,
            claimed_identity=claimed_id,
            authenticated_identity=auth_id,
            session_id=resolved_claim.session_id,
            configuration_hash=resolved_claim.configuration_hash,
            is_evidence_complete=True,
            metadata=meta,
        )

    # 9. All Evidence Valid & Consistent
    reasons.append(ImpersonationReasonCode.IDENTITY_VERIFIED)
    return ImpersonationEvidence(
        is_impersonation_detected=False,
        is_indeterminate=False,
        status=IdentityEvidenceStatus.VALID,
        primary_reason=ImpersonationReasonCode.IDENTITY_VERIFIED,
        reason_codes=tuple(reasons),
        expected_identity=effective_expected_id,
        claimed_identity=claimed_id,
        authenticated_identity=auth_id,
        session_id=resolved_claim.session_id,
        configuration_hash=resolved_claim.configuration_hash,
        is_evidence_complete=True,
        metadata=meta,
    )


# ==============================================================================
# M13 -> M12 Integration Adapter
# ==============================================================================

def evaluate_impersonation_decision(
    claim: IdentityClaim | Mapping[str, Any],
    auth_evidence: AuthenticationEvidence | Mapping[str, Any] | None = None,
    threshold_report: PolicyEvaluationReport | None = None,
    expected_identity: str | None = None,
    expected_session_id: str | None = None,
    expected_configuration_hash: str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> DecisionResult:
    """Evaluate an end-to-end security verdict integrating M13 Impersonation with M12 Decision Engine.

    Execution Flow:
        1. Evaluates claim and auth_evidence via detect_impersonation().
        2. Converts resulting ImpersonationEvidence into M12 ProtocolSecurityEvidence.
        3. Submits ProtocolSecurityEvidence along with threshold_report to M12 evaluate_security_decision().

    Args:
        claim: IdentityClaim or mapping representing the participant's identity assertion.
        auth_evidence: Optional AuthenticationEvidence or mapping proving identity.
        threshold_report: Optional M11 PolicyEvaluationReport summarizing quantum/statistical checks.
        expected_identity: Optional expected identifier.
        expected_session_id: Optional expected session identifier.
        expected_configuration_hash: Optional expected configuration hash.
        metadata: Optional evaluation context metadata.

    Returns:
        Immutable DecisionResult containing the final security verdict (ACCEPT, SUSPICIOUS, ATTACK).
    """
    impersonation_ev = detect_impersonation(
        claim=claim,
        auth_evidence=auth_evidence,
        expected_identity=expected_identity,
        expected_session_id=expected_session_id,
        expected_configuration_hash=expected_configuration_hash,
        metadata=metadata,
    )

    proto_ev = impersonation_ev.to_protocol_security_evidence()

    config_hash = expected_configuration_hash
    if config_hash is None:
        config_hash = impersonation_ev.configuration_hash

    combined_meta = dict(metadata) if metadata is not None else {}
    combined_meta["impersonation_evidence"] = {
        "status": impersonation_ev.status.value,
        "primary_reason": impersonation_ev.primary_reason.value,
        "is_impersonation_detected": impersonation_ev.is_impersonation_detected,
        "is_indeterminate": impersonation_ev.is_indeterminate,
    }

    return evaluate_security_decision(
        threshold_report=threshold_report,
        protocol_evidence=proto_ev,
        expected_configuration_hash=config_hash,
        metadata=combined_meta,
    )

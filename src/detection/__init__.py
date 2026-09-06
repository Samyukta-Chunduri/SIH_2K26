"""Q-SHIELD Detection and Decision Module (Milestones M12–M15).

Exports the deterministic security decision engine, verdicts, reason codes,
and evidence containers:
    - DecisionVerdict: ACCEPT, SUSPICIOUS, ATTACK
    - DecisionReasonCode: Canonical, explainable reason codes
    - ProtocolSecurityEvidence: Immutable container for protocol-level security indicators
    - DecisionResult: Immutable final decision record
    - evaluate_security_decision: Core deterministic decision engine
    - evaluate_decision_from_evidence: Integration adapter from M10/M11 to M12

Milestone M13 Impersonation Detection:
    - IdentityEvidenceStatus: Categorical evaluation status
    - ImpersonationReasonCode: Canonical impersonation reason codes
    - IdentityClaim: Participant identity assertion
    - AuthenticationEvidence: Explicit authentication evaluation facts
    - ImpersonationEvidence: Immutable impersonation detection record
    - detect_impersonation: Deterministic impersonation validation engine
    - evaluate_impersonation_decision: End-to-end M13 -> M12 integration adapter

Milestone M14 Unauthorized Verification Detection:
    - VerificationOperation: Permitted verification operations (VERIFY, VERIFY_TELEPORTATION, AUDIT_VERIFICATION)
    - AuthorizationStatus: Categorical evaluation status (AUTHORIZED, UNAUTHORIZED, INCOMPLETE, etc.)
    - AuthorizationReasonCode: Canonical authorization reason codes
    - VerificationPolicy: Immutable authorization policy container
    - AuthorizationRequest: Immutable verification request container
    - AuthorizationEvidence: Immutable unauthorized verification detection record
    - evaluate_verification_authorization: Deterministic authorization evaluation engine
    - evaluate_authorization_decision: End-to-end M14 -> M12 integration adapter

Milestone M15 Quantum Channel Attack Detection:
    - ChannelEvidenceStatus: Categorical channel evaluation status (CLEAN, ANOMALOUS, SECURITY_VIOLATION, etc.)
    - ChannelReasonCode: Canonical channel security reason codes
    - ChannelSecurityEvidence: Immutable channel anomaly and security evidence container
    - detect_channel_anomalies: Deterministic channel anomaly detection engine
    - evaluate_channel_attack_decision: End-to-end M15 -> M12 integration adapter
"""

from .authorization import (
    AuthorizationEvidence,
    AuthorizationReasonCode,
    AuthorizationRequest,
    AuthorizationStatus,
    VerificationOperation,
    VerificationPolicy,
    evaluate_authorization_decision,
    evaluate_verification_authorization,
)
from .channel import (
    ChannelEvidenceStatus,
    ChannelReasonCode,
    ChannelSecurityEvidence,
    detect_channel_anomalies,
    evaluate_channel_attack_decision,
)
from .decision import (
    DecisionReasonCode,
    DecisionResult,
    DecisionVerdict,
    ProtocolSecurityEvidence,
    evaluate_decision_from_evidence,
    evaluate_security_decision,
)
from .impersonation import (
    AuthenticationEvidence,
    IdentityClaim,
    IdentityEvidenceStatus,
    ImpersonationEvidence,
    ImpersonationReasonCode,
    detect_impersonation,
    evaluate_impersonation_decision,
)
from .fusion import (
    EvidenceSource,
    FusedEvidenceStatus,
    FusionReasonCode,
    FusedSecurityEvidence,
    evaluate_fused_security_decision,
    fuse_security_evidence,
)

__all__ = [
    "AuthenticationEvidence",
    "AuthorizationEvidence",
    "AuthorizationReasonCode",
    "AuthorizationRequest",
    "AuthorizationStatus",
    "ChannelEvidenceStatus",
    "ChannelReasonCode",
    "ChannelSecurityEvidence",
    "DecisionReasonCode",
    "DecisionResult",
    "DecisionVerdict",
    "EvidenceSource",
    "FusedEvidenceStatus",
    "FusedSecurityEvidence",
    "FusionReasonCode",
    "IdentityClaim",
    "IdentityEvidenceStatus",
    "ImpersonationEvidence",
    "ImpersonationReasonCode",
    "ProtocolSecurityEvidence",
    "VerificationOperation",
    "VerificationPolicy",
    "detect_channel_anomalies",
    "detect_impersonation",
    "evaluate_authorization_decision",
    "evaluate_channel_attack_decision",
    "evaluate_decision_from_evidence",
    "evaluate_fused_security_decision",
    "evaluate_impersonation_decision",
    "evaluate_security_decision",
    "evaluate_verification_authorization",
    "fuse_security_evidence",
]



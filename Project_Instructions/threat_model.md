# Q-SHIELD — Threat Model

## 1. Purpose

This document defines the security threat model for Q-SHIELD.

It specifies:

* Who the legitimate participants are
* Who the attacker is
* What attackers can and cannot do
* Which assets must be protected
* Which attacks are in scope
* Which attacks are out of scope
* How attacks affect the quantum and protocol layers
* What evidence Q-SHIELD should observe
* How attacks should be detected
* What security claims can and cannot be made

The threat model is essential because the detection engine must never classify an event as an attack without a defined attacker capability and observable evidence.

---

# 2. Security Objective

The primary security objective of Q-SHIELD is:

> **Detect security-relevant deviations in a simulated teleportation-based quantum digital-signature environment using quantum measurement statistics, protocol validation, and deterministic statistical rules.**

The system should identify attempts involving:

```text
Forgery
Replay
Impersonation
Unauthorized verification
Quantum-channel manipulation
```

The detector should provide:

```text
Attack type
+
Evidence
+
Relevant metrics
+
Decision
```

---

# 3. System Participants

The model contains four primary participants:

```text
Signer
Verifier
Attacker
Q-SHIELD Detector
```

---

# 4. Signer

The **Signer** is the legitimate party responsible for creating or authorizing a digital signature.

The signer:

* Possesses legitimate signing information
* Creates the signature representation
* Initiates or participates in the quantum-signature process
* Is associated with a legitimate identity
* Creates legitimate protocol/session information

For simulation purposes, the signer may be represented by software-generated state and protocol metadata.

---

# 5. Verifier

The **Verifier** is the legitimate party attempting to verify a signature.

The verifier:

* Receives a message/signature
* Performs or requests verification
* Participates in the quantum verification process
* Uses the defined measurement procedure
* Must satisfy authorization rules where applicable

---

# 6. Attacker

The **Attacker** is an adversarial participant attempting to cause an invalid signature or unauthorized verification attempt to be accepted.

The attacker may attempt to:

* Forge a signature
* Replay previously valid data
* Impersonate a legitimate signer
* Perform unauthorized verification
* Manipulate the simulated quantum channel
* Modify protocol data
* Exploit weaknesses in the verification procedure

The attacker does not automatically have unlimited capabilities.

Each attack must explicitly define its capability.

---

# 7. Q-SHIELD Detector

Q-SHIELD is the defensive system.

It receives:

```text
Signature information
+
Protocol metadata
+
Quantum measurement results
+
Statistical metrics
```

and produces:

```text
ACCEPT
SUSPICIOUS
ATTACK
```

along with evidence explaining the decision.

---

# 8. Protected Assets

The following assets are considered security-relevant.

## 8.1 Message Integrity

The verifier must be able to determine whether the message being verified corresponds to the legitimate signature context.

---

## 8.2 Signature Integrity

A modified or forged signature should not be accepted as legitimate under the defined verification rules.

---

## 8.3 Signer Identity

The system must distinguish the legitimate signer from an impersonator.

---

## 8.4 Verification Authorization

Only authorized entities should be allowed to perform or request verification where authorization is part of the protocol.

---

## 8.5 Session Integrity

A signature or verification event should belong to the correct protocol session.

---

## 8.6 Nonce Integrity

Where nonces are used, they should prevent inappropriate reuse of previously valid protocol data.

---

## 8.7 Quantum Measurement Integrity

Quantum measurement statistics should remain consistent with the expected honest operating region, subject to modeled noise.

---

## 8.8 Audit Information

Verification events and security decisions should be traceable.

A later blockchain layer may provide immutable audit records.

Blockchain is not part of the core threat-detection mechanism.

---

# 9. Security Goals

Q-SHIELD aims to detect:

```text
1. Invalid/forged signatures
2. Reused protocol messages
3. Signer impersonation
4. Unauthorized verification
5. Deliberate quantum-channel disturbances
```

The system should also distinguish malicious behavior from legitimate operation under expected noise.

---

# 10. Trust Boundaries

The major trust boundaries are:

```text
                 TRUSTED
                    │
        ┌───────────┴───────────┐
        │                       │
     Signer                  Verifier
        │                       │
        └───────────┬───────────┘
                    │
             Verification Input
                    │
              ──────┼──────
                 TRUST
              BOUNDARY
                    │
                 Attacker
                    │
              Manipulated Input
                    │
                    ▼
              Q-SHIELD
```

The attacker is not trusted.

The detector must not blindly trust attacker-controlled metadata.

---

# 11. Attack Surface

The primary attack surfaces are:

```text
Message
Signature
Identity
Session
Nonce
Authorization
Quantum channel
Measurement process
Verification request
```

Each surface belongs to one or more security layers.

---

# 12. Security Layers

Q-SHIELD separates threats into:

```text
Quantum layer
Signature/message layer
Protocol layer
Detection/statistical layer
```

---

# 13. Quantum-Layer Threats

Quantum-layer threats affect the simulated quantum communication or state.

Examples include:

```text
Bit-flip manipulation
Phase-flip manipulation
Y-type manipulation
Depolarizing disturbance
Other deliberate channel modifications
```

These attacks may alter:

* Measurement probabilities
* Expectation values
* Fidelity
* QBER/error rate
* Bell-state correlations
* X/Y/Z statistics

---

# 14. Signature-Level Threats

Signature-level attacks target the relationship between:

```text
Message
+
Signature
+
Signer
```

The main example is:

> Forgery

The attacker attempts to create or modify signature information so that the verifier accepts it as legitimate.

---

# 15. Protocol-Level Threats

Protocol attacks target the verification process rather than quantum physics itself.

Examples:

```text
Replay
Impersonation
Unauthorized verification
Invalid session
Invalid nonce
```

These should be detected using protocol evidence.

Quantum statistics alone should not be expected to detect every protocol attack.

---

# 16. Attack 1 — Signature Forgery

## Objective

Cause an invalid signature to be accepted as a legitimate signature.

---

## Attacker Capability

The attacker may attempt to construct a signature representation without possessing the legitimate signing information.

The exact forgery model must be defined by `QDS_PROTOCOL.md`.

---

## Attacker Does Not Automatically Have

Unless explicitly defined:

* Legitimate signing secret
* Legitimate private protocol information
* Ability to modify the underlying simulator
* Ability to change Q-SHIELD detection rules

---

## Attack Mechanism

Conceptually:

```text
Legitimate message
        ↓
Attacker creates forged signature
        ↓
Verification request
        ↓
Q-SHIELD
```

---

## Expected Evidence

Potential evidence includes:

```text
Signature mismatch
Quantum-statistical deviation
Low fidelity
Abnormal measurement distribution
Protocol inconsistency
```

The exact evidence depends on the finalized QDS protocol model.

---

## Detection Goal

The system should reject forged signatures according to the defined verification rule.

---

# 17. Attack 2 — Replay Attack

## Objective

Reuse previously valid verification data in a new or inappropriate session.

---

## Attacker Capability

The attacker may capture previously valid protocol information and attempt to submit it again.

---

## Attack Mechanism

```text
Valid session
      ↓
Capture verification data
      ↓
Later session
      ↓
Replay captured data
      ↓
Q-SHIELD
```

---

## Expected Evidence

Protocol evidence may include:

```text
Repeated nonce
Repeated session identifier
Expired timestamp
Previously processed message
Previously used verification identifier
```

---

## Detection

Replay should primarily be detected by protocol validation.

Quantum measurements may remain perfectly normal during a replay.

Therefore:

> A replay attack does not need to produce abnormal quantum statistics.

---

# 18. Attack 3 — Impersonation

## Objective

Pretend to be the legitimate signer.

---

## Attacker Capability

The attacker supplies identity information associated with another participant.

---

## Attack Mechanism

```text
Attacker
   ↓
Claims identity = legitimate signer
   ↓
Verification request
   ↓
Identity validation
```

---

## Expected Evidence

Examples:

```text
Identity mismatch
Invalid signer credential
Unexpected signer/session relationship
Invalid authorization
Signature/identity inconsistency
```

---

## Detection

Impersonation is primarily a protocol/authentication-layer problem.

Quantum measurements alone must not be treated as proof of identity.

---

# 19. Attack 4 — Unauthorized Verification

## Objective

Perform or request verification without having the required authorization.

---

## Attacker Capability

The attacker may submit a verification request while not being an authorized verifier.

---

## Attack Mechanism

```text
Unauthorized verifier
        ↓
Verification request
        ↓
Authorization check
```

---

## Expected Evidence

Examples:

```text
Verifier not authorized
Invalid role
Invalid session
Missing authorization
```

---

## Detection

The protocol-security layer should reject unauthorized requests.

Quantum measurement behavior may remain normal.

---

# 20. Attack 5 — Quantum Channel Manipulation

## Objective

Deliberately alter the simulated quantum information during transmission or processing.

---

## Attacker Capability

The attacker is allowed to introduce a defined disturbance into the simulated quantum channel.

Possible manipulations include:

```text
X operation
Y operation
Z operation
Bit-flip channel
Phase-flip channel
Depolarizing channel
```

Attack strength should be configurable.

---

## Expected Effects

Depending on the attack, quantum statistics may change.

Potential evidence:

```text
X-basis deviation
Y-basis deviation
Z-basis deviation
Fidelity reduction
QBER increase
Bell-correlation degradation
```

---

# 21. Attack Strength

Quantum-channel attacks should support configurable strength where meaningful.

For example:

```text
Attack strength = 0
Attack strength = low
Attack strength = medium
Attack strength = high
```

The exact numerical mapping must be defined in the implementation.

The system must document how attack strength changes the quantum channel.

---

# 22. Honest Noise Model

The threat model explicitly recognizes that quantum systems can experience noise without an attacker.

Therefore the system must support:

```text
HONEST + NOISE
```

as a legitimate condition.

Examples:

```text
Bit-flip noise
Phase-flip noise
Depolarizing noise
Readout error
```

The exact models implemented will be defined by the development plan.

---

# 23. Noise vs Attack

The detector must distinguish:

```text
Natural / configured noise
```

from:

```text
Deliberate manipulation
```

Conceptually:

```text
                    Measurement deviation
                            │
                ┌───────────┴───────────┐
                │                       │
          Within honest              Outside
          operating region        operating region
                │                       │
             ACCEPT             SUSPICIOUS / ATTACK
```

However, being outside the operating region does not automatically prove malicious intent.

The final classification must follow the documented detection rules.

---

# 24. Honest Baseline

The detector should establish an honest baseline under the configured noise conditions.

Example:

```text
Honest execution 1
Honest execution 2
Honest execution 3
...
Honest execution N
        ↓
Statistical analysis
        ↓
Honest operating region
```

Potential baseline metrics:

```text
X-basis probability
Y-basis probability
Z-basis probability
Fidelity
QBER
Bell correlation
Expectation values
```

---

# 25. Baseline Isolation

Attack samples must not silently contaminate the honest baseline.

Data should be categorized as:

```text
HONEST_BASELINE
HONEST_EVALUATION
ATTACK_EVALUATION
```

This is necessary for meaningful performance evaluation.

---

# 26. Detection Evidence

Q-SHIELD should maintain evidence from multiple layers.

## Quantum Evidence

Examples:

```text
Fidelity
QBER
X/Y/Z distributions
Bell correlations
Expectation values
```

## Protocol Evidence

Examples:

```text
Identity
Session
Nonce
Timestamp
Authorization
Replay history
```

## Signature Evidence

Examples:

```text
Message/signature consistency
Signature validity
Signature-state consistency
```

---

# 27. Evidence Severity

Evidence may be categorized as:

```text
NORMAL
DEVIATION
CRITICAL
```

The exact scoring/rule system must be defined in the detection model.

Avoid arbitrary numerical scoring unless scientifically justified.

---

# 28. Security Decision

The final decision should be deterministic.

Conceptually:

```text
Evidence
   ↓
Statistical evaluation
   ↓
Protocol validation
   ↓
Decision rules
   ↓
┌────────────┬─────────────┬────────────┐
│   ACCEPT   │ SUSPICIOUS  │   ATTACK   │
└────────────┴─────────────┴────────────┘
```

The same evidence and configuration must produce the same result.

---

# 29. Attack Classification

Where evidence is sufficient, the system may classify the event as:

```text
FORGERY
REPLAY
IMPERSONATION
UNAUTHORIZED_VERIFICATION
QUANTUM_CHANNEL_MANIPULATION
```

If evidence is insufficient to confidently identify an attack type, the system should prefer:

```text
SUSPICIOUS / UNKNOWN
```

rather than inventing an attack type.

---

# 30. Unknown Attacks

The system may encounter behavior not represented by the predefined attack models.

Q-SHIELD should not claim:

> "No known attack detected = secure."

Instead:

```text
No modeled attack detected
```

is a more accurate statement.

The project is a prototype with a defined threat model, not a universal attack detector.

---

# 31. Attack Capability Matrix

| Attack                       | Attacker Modifies Signature | Attacker Reuses Data | Attacker Changes Identity | Attacker Changes Quantum Channel | Primary Detection Layer |
| ---------------------------- | --------------------------: | -------------------: | ------------------------: | -------------------------------: | ----------------------- |
| Forgery                      |                         Yes |                   No |                  Possibly |                         Possibly | Signature + Quantum     |
| Replay                       |                          No |                  Yes |                        No |                               No | Protocol                |
| Impersonation                |                    Possibly |             Possibly |                       Yes |                               No | Protocol                |
| Unauthorized Verification    |                          No |             Possibly |                  Possibly |                               No | Authorization           |
| Quantum Channel Manipulation |                          No |                   No |                        No |                              Yes | Quantum                 |

The exact capability assumptions must be refined if the finalized QDS protocol requires additional constraints.

---

# 32. Attack-to-Evidence Mapping

| Attack                       | Expected Evidence                                         | Primary Detection       |
| ---------------------------- | --------------------------------------------------------- | ----------------------- |
| Forgery                      | Signature inconsistency, abnormal quantum statistics      | Signature + statistical |
| Replay                       | Duplicate nonce/session/timestamp                         | Protocol                |
| Impersonation                | Identity mismatch                                         | Protocol                |
| Unauthorized verification    | Authorization failure                                     | Protocol                |
| Quantum channel manipulation | X/Y/Z deviation, fidelity/QBER change, correlation change | Quantum + statistical   |

This table is a design guide rather than a guarantee that every attack will always produce every listed signal.

---

# 33. False Positives

A false positive occurs when legitimate behavior is classified as suspicious or malicious.

Potential causes:

```text
High legitimate noise
Insufficient shots
Poor baseline
Poor threshold selection
Statistical fluctuation
Measurement error
Model mismatch
```

The project must measure false-positive behavior.

---

# 34. False Negatives

A false negative occurs when an attack is incorrectly accepted as legitimate.

This is particularly important for:

```text
Forgery
Replay
Impersonation
Unauthorized verification
```

The project must measure false acceptance where applicable.

---

# 35. Detection Performance

Important metrics include:

### Legitimate Acceptance Rate

$$
LAR =
\frac{N_{\text{legitimate accepted}}}
{N_{\text{legitimate attempts}}}
$$

---

### False Rejection Rate

$$
FRR =
\frac{N_{\text{legitimate rejected}}}
{N_{\text{legitimate attempts}}}
$$

---

### False Acceptance Rate

$$
FAR =
\frac{N_{\text{malicious accepted}}}
{N_{\text{malicious attempts}}}
$$

---

### Attack Detection Rate

$$
ADR =
\frac{N_{\text{attacks detected}}}
{N_{\text{attack attempts}}}
$$

These definitions may be refined in `MATHEMATICAL_MODEL.md`.

---

# 36. Forgery Success Probability

For experimental evaluation:

$$
\hat p_f =
\frac{N_{\text{false accepts}}}
{N_{\text{forgery attempts}}}
$$

This is an empirical estimate.

It must not be confused with a theoretical QDS security bound.

The experiment must document:

* Number of attempts
* Forgery strategy
* Acceptance rule
* False acceptances
* Statistical uncertainty

---

# 37. Attacker Knowledge

The attacker knowledge model must be explicit.

Possible levels include:

```text
Limited knowledge
```

where the attacker knows only public protocol information,

or:

```text
Protocol-aware attacker
```

where the attacker understands the protocol structure and attempts targeted manipulation.

The final QDS protocol document must specify which model is used.

---

# 38. Attacker Control

Unless explicitly specified, the attacker is assumed to control only the attack surface being modeled.

For example:

A quantum-channel attacker may modify the simulated channel.

That does not automatically mean the attacker can:

* Modify the detector
* Modify the baseline
* Modify source code
* Change threshold configuration
* Access protected internal state

Those would constitute separate threat assumptions.

---

# 39. Detector Trust Assumption

For the prototype, Q-SHIELD's detection logic is considered trusted.

The attacker is assumed not to directly modify:

```text
Detection code
Baseline database
Threshold configuration
Experiment results
```

unless a future threat model explicitly adds such attacks.

---

# 40. Baseline Security

The honest baseline is a security-sensitive component of the detection framework.

If an attacker could manipulate the baseline, detection could become unreliable.

Therefore the prototype should treat baseline generation as a controlled process.

A future production implementation would require additional protection for:

* Baseline storage
* Configuration
* Thresholds
* Audit logs

---

# 41. Replay History

Replay detection requires some notion of previously observed protocol information.

The prototype may maintain:

```text
Session IDs
Nonces
Timestamps
Verification identifiers
Message identifiers
```

The exact persistence mechanism may initially be in-memory or SQLite.

It should remain independent of the quantum simulator.

---

# 42. Attack Experiments

Every attack should have a corresponding experiment.

Example:

```text
Experiment:
Honest baseline
        vs
Forgery
        vs
Replay
        vs
Impersonation
        vs
Channel manipulation
```

The experiment should record:

```text
Attack type
Attack strength
Noise level
Shots
Trials
Detection result
Quantum metrics
Protocol evidence
False acceptance/rejection
```

---

# 43. Controlled Attack Comparison

Whenever possible, compare attacks under the same environment.

For example:

```text
Honest + noise p
```

versus:

```text
Channel attack + noise p
```

This helps determine whether the detector is responding to the attack rather than simply responding to increased noise.

---

# 44. Security Operating Region

Detection performance may depend strongly on noise.

Conceptually:

```text
Low noise
    ↓
Strong separation between honest and attack distributions

Moderate noise
    ↓
Reduced separation

High noise
    ↓
Distribution overlap
    ↓
Higher false positives / false negatives
```

Q-SHIELD should experimentally investigate this relationship.

The project must not assume perfect detection at all noise levels.

---

# 45. Attack Combinations

Multiple attacks may occur simultaneously in real systems.

Examples:

```text
Replay + impersonation
Forgery + channel manipulation
Impersonation + unauthorized verification
```

Combined attacks are not required for the first MVP.

They may be explored later.

If implemented, the attack model must explicitly define how combined attacks behave.

---

# 46. Out-of-Scope Threats

The following are outside the initial Q-SHIELD prototype threat model unless explicitly added later:

* Physical hardware tampering
* Quantum-device side-channel attacks
* Laser/source attacks
* Detector blinding
* Hardware backdoors
* Supply-chain attacks
* Operating-system compromise
* Malware
* Distributed denial-of-service
* Network infrastructure attacks unrelated to the protocol
* Theft of physical quantum hardware
* Full cryptographic key-management infrastructure
* Complete production identity-management systems
* Real-world physical-layer attacks not represented by the simulator

These may be relevant to a production system but are not necessary for the initial SIH prototype.

---

# 47. Threat Model Limitations

This threat model is designed for a software prototype.

Important limitations include:

1. Quantum communication is simulated.
2. Physical hardware behavior is simplified.
3. The QDS model is an abstraction.
4. The attacker capabilities are controlled by the experiment.
5. Only predefined attacks are evaluated.
6. Detection performance depends on the statistical baseline.
7. Finite measurement shots introduce uncertainty.
8. Noise may make honest and malicious distributions overlap.
9. Detection does not constitute a security proof.
10. The system does not guarantee detection of unknown attacks.

---

# 48. Security Claim Boundary

Q-SHIELD may claim:

> "The prototype detects predefined simulated attacks under the tested assumptions and operating conditions."

Q-SHIELD should not claim:

> "Q-SHIELD detects every possible cyberattack."

It should not claim:

> "Q-SHIELD guarantees information-theoretic security."

It should not claim:

> "Q-SHIELD provides 100% attack detection."

---

# 49. Threat Model Summary

The overall model is:

```text
                         SIGNER
                           │
                           │
                    Legitimate signature
                           │
                           ▼
                      VERIFIER
                           │
                           │
                    Verification request
                           │
                           ▼
                    ┌──────────────┐
                    │  Q-SHIELD    │
                    │   DETECTOR   │
                    └──────┬───────┘
                           │
          ┌────────────────┼─────────────────┐
          │                │                 │
          ▼                ▼                 ▼
       Quantum          Signature         Protocol
       Evidence         Evidence          Evidence
          │                │                 │
          └────────────────┼─────────────────┘
                           ▼
                    Statistical Engine
                           │
                           ▼
                    Deterministic Rules
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
           ACCEPT      SUSPICIOUS      ATTACK
                                        │
                    ┌───────────────────┼─────────────────┐
                    ▼                   ▼                 ▼
                 Forgery             Replay          Impersonation
                                        │
                                        ▼
                              Unauthorized Verification
                                        │
                                        ▼
                              Channel Manipulation
```

---

# 50. Final Threat-Model Principle

The central principle is:

> **An abnormal measurement is evidence of deviation, not automatic proof of an attack.**

Q-SHIELD must establish expected honest behavior first, then evaluate deviations using statistical and protocol-aware rules.

The system must always distinguish:

```text
Noise
≠
Deviation
≠
Attack
```

while allowing the detector to determine when evidence is sufficiently strong to classify a deviation as suspicious or malicious.

---

# 51. Final Rule for Implementation

Before implementing any attack, the AI must verify that the attack is defined in this document or has been formally added to it.

If an attack is not defined:

```text
STOP
```

Then report:

```text
Attack name
Attacker capability
Target layer
Attack mechanism
Expected evidence
Detection strategy
Required documentation changes
```

Do not invent an attacker model during implementation.

The threat model must remain the foundation for all security experiments in Q-SHIELD.

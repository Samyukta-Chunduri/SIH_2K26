# Q-SHIELD — Security Model

## 1. Purpose

This document defines how Q-SHIELD converts quantum measurements, statistical evidence, signature information, and protocol-level evidence into deterministic security decisions.

The security model covers:

* Legitimate signature verification
* Forgery detection
* Replay detection
* Impersonation detection
* Unauthorized verification detection
* Quantum-channel manipulation detection
* Honest noise handling
* Statistical threshold evaluation
* Evidence fusion
* Deterministic decisions
* Security performance evaluation
* Security claim boundaries

The purpose is to ensure that the implementation does not rely on arbitrary security scores, machine learning, or unsupported cryptographic claims.

---

# 2. Security Objective

The primary objective of Q-SHIELD is:

> Detect deviations from legitimate teleportation-based quantum-signature verification behaviour and identify security-relevant attacks using deterministic quantum-statistical and protocol-level rules.

The system should:

1. Accept legitimate signatures under the calibrated operating conditions.
2. Reject or flag forged signatures.
3. Detect replayed verification requests.
4. Detect signer impersonation.
5. Detect unauthorized verification attempts.
6. Detect significant quantum-channel manipulation.
7. Distinguish normal noise from suspicious deviations as far as the calibrated model allows.
8. Provide evidence explaining every decision.

---

# 3. Security Model Boundary

Q-SHIELD consists of two related but different security layers:

```text id="2t7p3d"
Underlying QDS protocol
        ↓
Provides cryptographic/security properties
        ↓
Q-SHIELD detector
        ↓
Monitors and evaluates observed behaviour
```

The detector does not replace the QDS protocol.

The detector does not create information-theoretic security by itself.

---

# 4. Participants

The security model contains four primary participants.

## 4.1 Signer

The legitimate party associated with the signature.

The signer is expected to:

* Produce the legitimate signature representation.
* Participate in the defined signing protocol.
* Maintain valid session information.
* Not intentionally manipulate the protocol.

---

## 4.2 Verifier

The party performing verification.

The verifier is expected to:

* Submit a valid verification request.
* Possess appropriate authorization.
* Validate the signature.
* Follow the defined verification protocol.

---

## 4.3 Attacker

The attacker attempts to cause an invalid or unauthorized verification request to be accepted or to disrupt the protocol.

The attacker may operate at different layers.

---

## 4.4 Detector

The detector:

* Collects evidence.
* Computes statistical metrics.
* Checks protocol conditions.
* Applies deterministic rules.
* Produces a final decision.

The detector does not learn from examples.

---

# 5. Protected Assets

Q-SHIELD protects or monitors:

```text id="n2w5j8"
1. Message integrity
2. Signature integrity
3. Signer identity
4. Verification authorization
5. Session integrity
6. Nonce integrity
7. Quantum-state/measurement integrity
8. Quantum-channel behaviour
9. Verification history
10. Security evidence
```

---

# 6. Security Goals

The system should satisfy the following practical security goals.

### G1 — Legitimate Acceptance

A legitimate signature should be accepted under the configured honest operating conditions.

### G2 — Forgery Rejection

A forged signature should not satisfy the legitimate verification conditions.

### G3 — Replay Rejection

A previously consumed verification request should not be accepted as a new request.

### G4 — Identity Validation

A request should be associated with the expected signer and valid identity information.

### G5 — Authorization

Only authorized entities should be allowed to perform the defined verification operation.

### G6 — Quantum Integrity

Unexpected changes in quantum measurement behaviour should be detected when statistically distinguishable from the honest baseline.

### G7 — Explainability

Every security decision should provide evidence explaining why it was made.

---

# 7. Trust Boundaries

The major trust boundaries are:

```text id="g8z2wq"
Signer
   │
   ▼
Signature / Protocol Data
   │
   ▼
Quantum Channel
   │
   ▼
Verifier
   │
   ▼
Detection System
```

The attacker may attempt to interfere at any boundary that is included in the threat model.

---

# 8. Security Layers

Q-SHIELD evaluates security at three primary levels.

```text id="7p4z2x"
┌──────────────────────────────┐
│ Protocol Security             │
│ Identity / Session / Nonce    │
│ Authorization / Replay        │
└──────────────┬───────────────┘
               │
┌──────────────▼───────────────┐
│ Signature Security            │
│ Message / Signature relation  │
│ Forgery validation            │
└──────────────┬───────────────┘
               │
┌──────────────▼───────────────┐
│ Quantum Security Evidence     │
│ States / Measurements / Noise │
│ Fidelity / QBER / Correlation │
└──────────────────────────────┘
```

---

# 9. Evidence Categories

Every verification attempt produces evidence belonging to one or more categories.

## 9.1 Protocol Evidence

Examples:

```text id="g5k3va"
identity_valid
session_valid
nonce_valid
authorization_valid
replay_detected
```

---

## 9.2 Signature Evidence

Examples:

```text id="z7c2qk"
message_valid
signature_valid
state_mapping_valid
signature_consistency
```

---

## 9.3 Quantum Evidence

Examples:

```text id="m8s1cv"
measurement_probability
Pauli expectation
teleportation fidelity
QBER
Bell correlation
distribution deviation
```

---

## 9.4 Statistical Evidence

Examples:

```text id="x1r4pw"
baseline_mean
baseline_variance
confidence_interval
threshold
observed_deviation
```

---

# 10. Evidence Record

Each verification should produce a structured evidence record.

Conceptually:

```text id="7m0jsk"
VerificationEvidence
├── protocol_evidence
├── signature_evidence
├── quantum_evidence
├── statistical_evidence
├── attack_evidence
└── decision
```

The exact Python data structure will be defined during implementation.

---

# 11. Security Decision States

Q-SHIELD uses three primary final states:

```text id="2g1b5e"
ACCEPT
SUSPICIOUS
ATTACK
```

These states have distinct meanings.

---

# 12. ACCEPT

`ACCEPT` means:

* Required protocol checks passed.
* Signature checks passed.
* Quantum evidence is consistent with the calibrated honest operating region.
* No attack rule was triggered.

It does **not** mean:

> "The signature is mathematically proven secure under every possible attack."

It means the verification attempt satisfied the implemented and configured verification criteria.

---

# 13. SUSPICIOUS

`SUSPICIOUS` means:

* Some evidence deviates from normal behaviour,
* but the evidence is insufficient to confidently attribute the event to a specific attack.

Examples:

```text id="7r8m4h"
Unexpected quantum deviation
but
no replay / identity / authorization violation
```

or:

```text id="0f5v2n"
Moderate statistical deviation
that overlaps with calibrated noise behaviour
```

This state prevents the detector from forcing every anomaly into either "safe" or "attack."

---

# 14. ATTACK

`ATTACK` means that one or more explicit security rules have been satisfied.

Examples:

```text id="0q5x5e"
Replay detected
Identity invalid
Authorization invalid
Forgery criteria satisfied
Quantum-channel attack criteria satisfied
```

The attack type should be included in the evidence.

---

# 15. Deterministic Decision Principle

The final decision is:

$$
D(E,C)
\rightarrow
\{
ACCEPT,SUSPICIOUS,ATTACK
\}
$$

where:

* \(E\) = collected evidence
* \(C\) = configuration and thresholds

Once \(E\) and \(C\) are fixed, \(D\) must produce the same result.

No machine-learning model is involved.

---

# 16. Decision Priority

The initial decision hierarchy should follow this principle:

```text id="2x9xqf"
Explicit protocol violation
        ↓
Explicit attack condition
        ↓
Signature failure
        ↓
Severe quantum/statistical deviation
        ↓
Moderate unexplained deviation
        ↓
All checks passed
```

The exact final implementation ordering must be tested because some conditions can overlap.

---

# 17. Protocol-Level Checks

Protocol checks should be evaluated before relying on quantum evidence.

The following checks are required where applicable:

```text id="j1c7qk"
1. Identity
2. Session
3. Nonce
4. Authorization
5. Replay history
```

---

# 18. Identity Validation

Let:

$$
I_{\text{expected}}
$$

be the expected signer identity and:

$$
I_{\text{provided}}
$$

the identity supplied with the request.

The identity check is:

$$
I_{\text{valid}}
=
(I_{\text{expected}}=I_{\text{provided}})
$$

A failed identity check is strong evidence for an impersonation attempt.

---

# 19. Session Validation

Each verification request should belong to a valid session.

Conceptually:

$$
S_{\text{valid}}
=
S_{\text{provided}}\in S_{\text{active}}
$$

Invalid or expired sessions should not be accepted.

---

# 20. Nonce Validation

A nonce should provide freshness for the verification request.

Let:

$$
N_{\text{current}}
$$

represent the current request nonce.

A nonce should satisfy the protocol's freshness requirements.

A reused nonce may indicate replay.

---

# 21. Replay Detection

Maintain a record of previously accepted/consumed request identifiers or nonces.

For request identifier \(r\):

$$
Replay(r)=
\begin{cases}
1,&r\in H\\
0,&r\notin H
\end{cases}
$$

where \(H\) is the history of previously processed identifiers.

If:

$$
Replay(r)=1
$$

the request should not be accepted as a new verification.

---

# 22. Impersonation Detection

Impersonation is primarily a protocol/identity-layer threat.

Evidence may include:

```text id="k4y2qs"
invalid signer identity
invalid credentials/identity token
identity-signature mismatch
unexpected signer/session combination
```

Quantum measurement anomalies alone should not automatically be labelled impersonation.

---

# 23. Unauthorized Verification

A verifier must satisfy the authorization requirement.

Conceptually:

$$
AuthorizationValid
=
Verify(Verifier,Resource,Permission)
$$

If:

$$
AuthorizationValid=False
$$

the request is unauthorized regardless of whether the quantum measurements appear normal.

This is an important security boundary.

---

# 24. Forgery Model

A forgery attempt tries to construct a signature or quantum-signature representation that passes verification without being generated legitimately.

The attacker may attempt to modify:

```text id="v5q3ay"
message
signature
state selection
state preparation
measurement-related information
protocol metadata
```

The exact capabilities depend on the experiment configuration.

---

# 25. Forgery Detection

Forgery detection should combine:

```text id="d8x4jm"
Signature evidence
+
Quantum evidence
+
Protocol evidence
```

A forgery should not be identified from one arbitrary metric.

The detector should evaluate whether the forged representation remains consistent with the expected legitimate verification behaviour.

---

# 26. Quantum Channel Manipulation

The attacker may modify the quantum state during transmission.

The simulation may model attacks using operations such as:

$$
X
$$

$$
Y
$$

$$
Z
$$

or configured noise/error channels.

Possible effects include changes in:

* Measurement probabilities
* Pauli expectations
* Fidelity
* QBER
* Bell correlations

---

# 27. Noise Is Not Automatically an Attack

This is a critical security rule.

A noisy but honest execution is not necessarily malicious.

Therefore:

```text id="m4y0vf"
Noise
≠
Attack
```

The system must first characterize honest noisy behaviour.

---

# 28. Honest Noise Baseline

For a configured noise model \(\eta\):

$$
B_H(\eta)
$$

represents the honest baseline.

The baseline should be generated using legitimate executions under the same or appropriately matched conditions.

Examples:

```text id="j8w5h1"
Depolarizing noise
Readout error
Bit-flip noise
Phase-flip noise
Thermal relaxation
```

Only noise models intentionally included in the project should be used.

---

# 29. Baseline Isolation

An attack experiment must not silently contaminate the honest baseline.

Correct:

```text id="z2d7qf"
Honest runs
    ↓
Baseline
    ↓
Attack runs
    ↓
Evaluation
```

Incorrect:

```text id="h8x1pk"
Honest + attack runs
        ↓
Single baseline
```

The second approach can make attacks appear normal.

---

# 30. Quantum Evidence Evaluation

Suppose the detector observes:

$$
E_Q=
\{
F,QBER,
\langle X\rangle,
\langle Y\rangle,
\langle Z\rangle,
C_{Bell},
D_{TV},...
\}
$$

Each metric is compared against its calibrated honest operating region.

---

# 31. Metric-Level Evidence

For metric \(M\), define:

$$
Deviation(M)=
\begin{cases}
0,&M\in R_H\\
1,&M\notin R_H
\end{cases}
$$

where \(R_H\) is the configured honest region.

The detector should also preserve:

```text id="h6h2d9"
observed value
expected value
allowed region
deviation magnitude
baseline ID
```

---

# 32. Severe and Moderate Deviations

The detector may distinguish:

```text id="5m4g4h"
NORMAL
MODERATE DEVIATION
SEVERE DEVIATION
```

The boundaries must be statistically justified.

They must not be arbitrary values chosen to produce attractive demo results.

---

# 33. Attack-Specific Rules

Attack classification should be based on evidence patterns.

Conceptually:

### Replay

```text id="z6c2c3"
replay_detected = TRUE
```

→ `ATTACK / REPLAY`

### Impersonation

```text id="8g6h5r"
identity_invalid = TRUE
```

→ `ATTACK / IMPERSONATION`

### Unauthorized verification

```text id="f9k2s8"
authorization_invalid = TRUE
```

→ `ATTACK / UNAUTHORIZED_VERIFICATION`

### Forgery

```text id="e4d2a1"
signature_inconsistent
AND
verification_failure/evidence
```

→ `ATTACK / FORGERY`

### Quantum channel manipulation

```text id="s3x7v4"
quantum_deviation
AND
channel_attack_condition
```

→ `ATTACK / QUANTUM_CHANNEL_MANIPULATION`

These are conceptual rules and require experimental validation.

---

# 34. Unknown Anomalies

Not every anomaly should be forced into a known attack category.

If:

```text id="k8r1a2"
quantum deviation = TRUE
protocol violation = FALSE
known attack condition = FALSE
```

the preferred result may be:

```text
SUSPICIOUS
```

This prevents unsupported attribution.

---

# 35. Evidence Fusion

Evidence can be represented as:

$$
E=
(E_P,E_S,E_Q,E_T)
$$

where:

* \(E_P\) = protocol evidence
* \(E_S\) = signature evidence
* \(E_Q\) = quantum evidence
* \(E_T\) = statistical evidence

The decision function is:

$$
D=f(E)
$$

The function \(f\) must consist of explicit deterministic rules.

---

# 36. No Machine Learning

The detector must not use:

* Neural networks
* Decision-tree training
* Random forests
* Support vector machines
* Clustering
* Reinforcement learning
* Learned embeddings
* AI classifiers
* Trained anomaly detectors

Detection is based on:

```text id="c1x4v8"
Quantum measurements
+
Mathematical metrics
+
Statistical calibration
+
Explicit rules
```

---

# 37. Threshold Calibration

Thresholds should be obtained from honest calibration and security experiments.

The process is:

```text id="j4k9c2"
Honest executions
       ↓
Metric distributions
       ↓
Statistical analysis
       ↓
Operating region
       ↓
Threshold candidate
       ↓
Attack evaluation
       ↓
Threshold validation
```

A threshold is not considered final until it has been evaluated against both legitimate and attack cases.

---

# 38. Threshold Trade-Off

A threshold that is too strict may cause:

```text id="v6p2s8"
High false rejection
```

A threshold that is too permissive may cause:

```text id="m3d7q1"
High false acceptance
```

Therefore threshold selection should evaluate both.

---

# 39. Legitimate Acceptance

For legitimate attempts:

$$
LAR=
\frac{
N_{\text{legitimate accepted}}
}{
N_{\text{legitimate attempts}}
}
$$

The project should target high legitimate acceptance within the calibrated operating region.

---

# 40. False Rejection

$$
FRR=
\frac{
N_{\text{legitimate rejected}}
}{
N_{\text{legitimate attempts}}
}
$$

A useful detector should minimize unnecessary rejection of legitimate signatures.

---

# 41. False Acceptance

For malicious attempts:

$$
FAR=
\frac{
N_{\text{malicious accepted}}
}{
N_{\text{malicious attempts}}
}
$$

A useful detector should minimize malicious acceptance.

---

# 42. Attack Detection Rate

$$
ADR=
\frac{
N_{\text{attacks detected}}
}{
N_{\text{attack attempts}}
}
$$

ADR must always be reported together with:

* Attack type
* Attack strength
* Noise model
* Noise parameters
* Shots
* Number of trials
* Threshold configuration

---

# 43. Forgery Success Probability

The empirical forgery success probability is:

$$
\hat p_F
=
\frac{
N_{\text{false accepts}}
}{
N_{\text{forgery attempts}}
}
$$

This is an experimental estimate.

It must not be presented as a formal theoretical QDS security bound.

---

# 44. Zero False Acceptances

If:

$$
N_{\text{false accepts}}=0
$$

then:

$$
\hat p_F=0
$$

for the observed experiment.

The correct statement is:

> No false acceptances were observed in the tested number of forgery attempts.

The system must not claim that the true probability is mathematically zero.

---

# 45. Confidence in Experimental Results

Experimental rates should be interpreted with finite-sample uncertainty.

For example, observing:

```text id="s6w2e9"
0 false accepts
```

in:

```text id="a9m5z1"
20 attempts
```

does not provide the same evidence as:

```text
0 false accepts
```

in:

```text
100,000 attempts
```

Therefore the number of trials must always be recorded.

---

# 46. Security Operating Region

Q-SHIELD should experimentally identify the conditions under which the detector behaves reliably.

Important variables include:

$$
(\eta,a,N)
$$

where:

* \(\eta\) = noise condition
* \(a\) = attack strength
* \(N\) = number of measurement shots

The result may be represented as:

```text id="k4z8wq"
                 Attack Strength
              low     medium     high
Noise low     ...       ...        ...
Noise medium  ...       ...        ...
Noise high    ...       ...        ...
```

This demonstrates where the prototype is effective and where it becomes uncertain.

---

# 47. Security vs Noise

A legitimate noisy system should remain acceptable within its calibrated operating region.

Conceptually:

```text id="3h2f9c"
Noise increases
      ↓
Measurement variation increases
      ↓
Honest baseline widens/changes
      ↓
Detection becomes harder
```

This relationship should be experimentally measured rather than assumed.

---

# 48. Security vs Number of Shots

Increasing the number of shots generally provides more measurement observations.

Conceptually:

```text id="r5q9t3"
More shots
   ↓
More observations
   ↓
More stable empirical estimates
```

However:

```text id="w3k7p1"
More shots
   ↓
Higher computational cost
```

Therefore the project should evaluate the trade-off.

---

# 49. Quantum Integrity Fingerprint

Q-SHIELD may represent the expected honest quantum behaviour as a collection of calibrated measurements:

$$
QIF=
\{
P_X,P_Y,P_Z,
F,
QBER,
C_{Bell},
...
\}
$$

This can be called the:

> **Quantum Integrity Fingerprint**

The fingerprint is not a cryptographic hash.

It is a statistical representation of expected quantum verification behaviour.

---

# 50. Noise-Calibrated Quantum Integrity Fingerprinting

The recommended detection workflow is:

```text id="c4p1m8"
Noise configuration
       ↓
Honest calibration
       ↓
Quantum Integrity Fingerprint
       ↓
New verification
       ↓
Observed quantum statistics
       ↓
Compare with fingerprint
       ↓
Statistical evidence
       ↓
Deterministic decision
```

The fingerprint should be versioned with its calibration conditions.

---

# 51. Fingerprint Metadata

A fingerprint should include:

```text id="v8r2n6"
fingerprint_id
noise_model
noise_parameters
shots
calibration_runs
measurement_bases
expected_probabilities
baseline_statistics
threshold_configuration
creation_version
```

---

# 52. Multi-Layer Security Evidence

The final security decision should use:

```text id="q6m4y2"
Protocol Evidence
        +
Signature Evidence
        +
Quantum Evidence
        +
Statistical Evidence
```

This is stronger than relying only on a single quantum metric.

---

# 53. Example: Legitimate Verification

```text id="j8n3v1"
Identity valid
Session valid
Nonce valid
Authorization valid
Replay = false
Signature valid
Teleportation fidelity within baseline
QBER within baseline
Pauli statistics within baseline
Bell correlations within baseline
        ↓
ACCEPT
```

---

# 54. Example: Forgery

```text id="p2c6m7"
Identity valid
Session valid
Nonce valid
Authorization valid
Replay = false
Signature inconsistent
Quantum evidence deviates
        ↓
FORGERY RULE
        ↓
ATTACK / FORGERY
```

---

# 55. Example: Replay

```text id="r8v4q2"
Identity valid
Signature valid
Quantum statistics normal
Nonce already used
        ↓
REPLAY RULE
        ↓
ATTACK / REPLAY
```

Notice that the quantum layer may appear completely normal during a replay attack.

This is why protocol-level security checks are necessary.

---

# 56. Example: Impersonation

```text id="z1x5c9"
Provided signer ≠ expected signer
        ↓
Identity validation fails
        ↓
ATTACK / IMPERSONATION
```

Quantum measurements alone are not sufficient to determine this.

---

# 57. Example: Unauthorized Verification

```text id="f4m8k3"
Verifier identity valid
BUT
Verifier is not authorized
        ↓
ATTACK / UNAUTHORIZED_VERIFICATION
```

The quantum signature may itself be completely legitimate.

---

# 58. Example: Quantum Channel Manipulation

```text id="n7b2v5"
Protocol valid
Signature valid
        ↓
Quantum channel manipulated
        ↓
Measurement distribution deviates
        ↓
Fidelity decreases / QBER increases
        ↓
Attack criteria satisfied
        ↓
ATTACK / QUANTUM_CHANNEL_MANIPULATION
```

The exact evidence pattern must be established experimentally.

---

# 59. Example: Honest Noise

```text id="h3d9q6"
Protocol valid
Signature valid
Quantum deviation observed
        ↓
Deviation lies within calibrated
honest noisy operating region
        ↓
ACCEPT
```

This example is critical because the detector must not mistake normal noise for an attack.

---

# 60. Example: Uncertain Anomaly

```text id="u5s2a7"
Protocol valid
Signature appears valid
Quantum deviation observed
Deviation exceeds normal region
BUT
No known attack condition is satisfied
        ↓
SUSPICIOUS
```

This is preferable to falsely claiming a specific attack.

---

# 61. Attack Combination

Real attacks may combine multiple behaviours.

For example:

```text id="c8x3p4"
Replay
+
Identity manipulation
```

or:

```text
Forgery
+
Quantum channel manipulation
```

The detector should preserve all relevant evidence instead of overwriting one attack with another.

---

# 62. Attack Evidence Structure

Each detected attack should contain:

```text id="e2v7m1"
attack_type
attack_parameters
triggered_rules
quantum_evidence
protocol_evidence
signature_evidence
statistical_evidence
confidence/uncertainty information where applicable
```

The word "confidence" must not imply a machine-learning probability.

---

# 63. Explainable Security Decision

A final result should be understandable to a human.

Example:

```text id="a6k4z8"
Decision: ATTACK

Attack type:
Quantum Channel Manipulation

Reasons:
- X-basis distribution exceeded calibrated region.
- QBER exceeded configured threshold.
- Teleportation fidelity decreased.
- Protocol identity remained valid.

Baseline:
QIF-003

Noise:
Depolarizing channel, configured parameter = ...

Shots:
10,000
```

The exact values will come from the implementation.

---

# 64. No Hidden Security Logic

Every security decision should be traceable to explicit rules.

The system should be able to answer:

```text id="q2n8w4"
Why was this accepted?
```

or:

```text id="x7m3p5"
Why was this rejected?
```

or:

```text id="v4c9k2"
Why was this classified as suspicious?
```

---

# 65. Security Logging

Each verification event should record:

```text id="m5h8r1"
timestamp
verification_id
signer_id
verifier_id
message_id/hash
session_id
nonce
decision
attack_type
baseline_id
noise_configuration
shots
quantum_metrics
protocol_results
triggered_rules
```

Sensitive credentials must never be logged directly.

---

# 66. Replay History

Replay detection requires persistent or session-level history.

For the MVP, a simple local store may be sufficient.

Possible implementation:

```text id="x3j6q9"
SQLite
```

or an in-memory structure for controlled experiments.

Persistence requirements can be expanded later.

---

# 67. Security Failure Modes

The detector should distinguish:

### Verification failure

The signature did not satisfy verification.

### Security attack

An explicit attack rule was satisfied.

### Suspicious anomaly

Unexpected behaviour was observed but attribution is insufficient.

### System error

The verification system itself failed.

These must not be silently merged.

---

# 68. System Error ≠ Attack

For example:

```text id="y8p4c2"
Qiskit simulation crashed
```

does not mean:

```text
ATTACK
```

It means:

```text
SYSTEM_ERROR
```

The application should report infrastructure failures separately.

---

# 69. Fail-Safe Behaviour

If required evidence is missing, the implementation must not automatically claim success.

For example:

```text id="g6r2n9"
Required quantum evidence unavailable
```

should not silently become:

```text
ACCEPT
```

The system should use an explicitly defined failure state or conservative decision rule.

---

# 70. Security Assumptions

The prototype assumes:

1. The quantum simulation correctly implements the configured circuit.
2. The verifier's trusted software environment has not been compromised.
3. Honest baseline calibration is performed using legitimate executions.
4. Attack experiments are correctly configured.
5. Protocol metadata used for detection is available and trustworthy according to the model.
6. The selected QDS abstraction is clearly documented.
7. Statistical conclusions are interpreted within their experimental conditions.

---

# 71. Information-Theoretic Security Boundary

Q-SHIELD must distinguish:

```text
QDS protocol security
```

from:

```text
Q-SHIELD detection performance
```

A statement such as:

> "The QDS protocol provides information-theoretic security under its assumptions"

is fundamentally different from:

> "Q-SHIELD detected 96% of simulated channel attacks."

The second is an empirical software result.

The first is a property requiring a valid protocol and security analysis.

---

# 72. Claims Q-SHIELD May Make

Subject to experimental validation, the project may report:

* Successful simulation of Bell-state entanglement.
* Successful simulation of quantum teleportation.
* Correct application of Pauli corrections.
* Statistical characterization of honest measurements.
* Detection of selected simulated attacks.
* Forgery experiments.
* Replay detection.
* Impersonation detection.
* Unauthorized verification detection.
* Quantum-channel manipulation experiments.
* Legitimate acceptance rate.
* False acceptance rate.
* False rejection rate.
* Attack detection rate.
* Empirical forgery success rate.
* Performance under selected noise conditions.

---

# 73. Claims Q-SHIELD Must Not Make

Do not claim:

* Absolute security.
* Perfect attack detection.
* Zero probability of forgery.
* A complete implementation of every physical QDS protocol.
* A formal proof of information-theoretic security by the detector.
* Real-world quantum hardware security from simulation alone.
* Protection against every possible quantum attack.
* That replay is inherently a quantum attack.
* That noise automatically indicates an attack.
* That a statistical threshold is a cryptographic proof.

---

# 74. Security Evaluation Matrix

The final evaluation should include at least:

| Scenario                  | Legitimate? |      Noise | Attack         | Expected Result   |
| ------------------------- | ----------: | ---------: | -------------- | ----------------- |
| Honest ideal              |         Yes |       None | None           | ACCEPT            |
| Honest noisy              |         Yes | Configured | None           | ACCEPT            |
| Forgery                   |          No | Configured | Forgery        | ATTACK            |
| Replay                    |          No | Configured | Replay         | ATTACK            |
| Impersonation             |          No | Configured | Impersonation  | ATTACK            |
| Unauthorized verification |          No | Configured | Unauthorized   | ATTACK            |
| Channel manipulation      |          No | Configured | Quantum attack | ATTACK/SUSPICIOUS |
| Unknown anomaly           |     Unknown | Configured | Unknown        | SUSPICIOUS        |

The exact result for channel manipulation depends on experimental distinguishability.

---

# 75. Security Metrics

At minimum, report:

$$
LAR
$$

$$
FRR
$$

$$
FAR
$$

$$
ADR
$$

$$
\hat p_F
$$

Additionally report:

* Number of trials
* Shots
* Noise parameters
* Attack strength
* Threshold configuration
* Baseline version

---

# 76. Security Experiment Design

Every attack experiment should compare:

```text id="n5c8v2"
Control:
Honest + same noise

versus

Experiment:
Attack + same noise
```

This isolates the attack effect more effectively.

---

# 77. Attack Strength Sweep

For attacks that have a tunable parameter, evaluate multiple strengths.

Conceptually:

$$
a_1<a_2<a_3<\cdots<a_n
$$

Then measure:

$$
ADR(a)
$$

and:

$$
FAR(a)
$$

This shows how detection changes with attack severity.

---

# 78. Noise Sweep

Similarly evaluate multiple noise levels:

$$
\eta_1<\eta_2<\cdots<\eta_n
$$

Measure:

$$
LAR(\eta)
$$

$$
FAR(\eta)
$$

$$
ADR(\eta)
$$

This identifies where the detector becomes unreliable.

---

# 79. Shots Sweep

Evaluate multiple shot counts:

$$
N_1<N_2<\cdots<N_n
$$

Measure:

$$
\text{metric stability}(N)
$$

and:

$$
\text{verification cost}(N)
$$

This supports the efficient-verification requirement.

---

# 80. Security and Performance Trade-Off

Increasing statistical confidence may require more observations.

Therefore:

```text id="q9f3m6"
More shots
    ↓
More stable statistics
    ↓
Potentially better detection
    ↓
Higher computation
```

The project should identify a practical operating point rather than simply maximizing shots.

---

# 81. Security Model Implementation Order

Implementation should proceed in this order:

```text id="r4m8s2"
1. Protocol validity
2. Signature validity
3. Honest quantum baseline
4. Quantum metric calculation
5. Statistical threshold engine
6. Forgery detection
7. Replay detection
8. Impersonation detection
9. Unauthorized verification detection
10. Quantum-channel attack detection
11. Evidence fusion
12. Final deterministic decision
13. Evaluation
```

---

# 82. Security Model Dependency

This document depends on:

```text id="x5n1q7"
PROJECT_CONTEXT.md
REQUIREMENTS.md
ARCHITECTURE.md
SCIENTIFIC_RULES.md
THREAT_MODEL.md
QDS_PROTOCOL.md
MATHEMATICAL_MODEL.md
```

Changes to the QDS protocol or mathematical model may require corresponding updates here.

---

# 83. Critical STOP Rule

If implementation reaches a point where the security behaviour cannot be determined from the documented protocol and mathematical model:

```text
STOP
```

Do not invent a security rule.

Instead report:

```text
Missing security decision:
<description>

Why it matters:
<description>

Possible choices:
<option A>
<option B>

Required decision:
<what must be decided>
```

The decision should then be recorded in:

```text
DECISIONS.md
```

---

# 84. Security Model Completion Criteria

This document is considered implementation-ready when:

* Security participants are defined.
* Protected assets are defined.
* Security goals are defined.
* Trust boundaries are defined.
* Protocol checks are defined.
* Forgery model is defined.
* Replay model is defined.
* Impersonation model is defined.
* Unauthorized verification model is defined.
* Quantum-channel attack model is defined.
* Honest noise is separated from attacks.
* Honest baseline methodology is defined.
* Quantum evidence is defined.
* Statistical evidence is defined.
* Evidence fusion is defined.
* ACCEPT/SUSPICIOUS/ATTACK states are defined.
* Deterministic decision logic is defined.
* Security metrics are defined.
* Experimental conditions are recorded.
* Information-theoretic security claims are properly bounded.
* No AI/ML is used.
* Unknown anomalies can remain SUSPICIOUS.
* System errors are separated from attacks.

---

# 85. Final Security Principle

Q-SHIELD follows:

```text id="m7q2v9"
VALIDATE THE PROTOCOL
        ↓
VALIDATE THE SIGNATURE
        ↓
MEASURE QUANTUM BEHAVIOUR
        ↓
COMPARE WITH HONEST BASELINE
        ↓
EVALUATE STATISTICAL EVIDENCE
        ↓
APPLY EXPLICIT SECURITY RULES
        ↓
FUSE EVIDENCE
        ↓
MAKE DETERMINISTIC DECISION
```

The central rule is:

> **An anomaly is evidence, not automatically an attack. An attack classification requires an explicit, testable rule.**

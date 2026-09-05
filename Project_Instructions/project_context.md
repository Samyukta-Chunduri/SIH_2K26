# Q-SHIELD — Project Context

## 1. Project Identity

**Project Name:** Q-SHIELD
**Full Name:** Quantum Signature Security & Threat Detection Framework

**Hackathon:** Smart India Hackathon (SIH)

**Problem Statement:** SIH 26141 — Quantum-Inspired Cyber Threat Detection for Digital Signature Security

**Domain:** Cybersecurity / Quantum Computing / Digital Signatures

**Project Type:** Software-based quantum protocol simulation and security analysis framework

---

# 2. Project Objective

Q-SHIELD is a software framework designed to simulate and analyze a teleportation-based Quantum Digital Signature (QDS)-inspired environment and detect malicious verification attempts using quantum measurement statistics and deterministic mathematical rules.

The project focuses on demonstrating how quantum information and statistical analysis can be used to identify suspicious deviations from expected legitimate-signature behaviour.

The system is intended to be a **prototype and simulation**, not a replacement for a physically deployed quantum digital-signature system.

The framework should:

1. Simulate quantum states.
2. Prepare Pauli eigenstates.
3. Create Bell-state entanglement.
4. Demonstrate quantum teleportation.
5. Apply the required Pauli corrections.
6. Perform projective measurements.
7. Collect measurement outcomes over multiple shots.
8. Calculate statistical properties of the measurements.
9. Establish an honest-operation baseline.
10. Detect deviations from the honest baseline.
11. Simulate forgery attacks.
12. Simulate replay attacks.
13. Simulate impersonation attacks.
14. Simulate unauthorized verification attempts.
15. Simulate quantum-channel manipulation.
16. Calculate empirical forgery/false-accept probabilities.
17. Evaluate legitimate acceptance and malicious rejection.
18. Produce deterministic security decisions.
19. Explain the evidence behind every decision.
20. Provide a visual dashboard for experimentation and demonstration.

---

# 3. Core Design Philosophy

The project must prioritize:

* Scientific correctness
* Mathematical transparency
* Explainability
* Reproducibility
* Testability
* Incremental development
* SIH requirement compliance
* Beginner-friendly implementation
* Honest security claims

The system must not use artificial intelligence or machine learning to classify attacks.

Detection must be based on:

* Quantum measurement outcomes
* Probabilities
* Statistical distributions
* Error rates
* Fidelity
* QBER where applicable
* Bell-state correlations
* Thresholds
* Confidence intervals
* Protocol validation rules
* Deterministic decision logic

---

# 4. Core Pipeline

The main quantum verification pipeline is:

```text
Message
    ↓
Signature Representation
    ↓
Quantum State Preparation
    ↓
Bell-State Entanglement
    ↓
Quantum Teleportation
    ↓
Pauli Correction
    ↓
Projective Measurement
    ↓
Measurement Statistics
    ↓
Quantum Verification Metrics
    ↓
Honest Baseline Comparison
    ↓
Statistical Threshold Engine
    ↓
Security Evidence
    ↓
Deterministic Decision
    ↓
ACCEPT / SUSPICIOUS / ATTACK
```

Protocol-level security checks operate alongside the quantum pipeline:

```text
Signer Identity
    ↓
Verifier Identity
    ↓
Session Validation
    ↓
Nonce Validation
    ↓
Timestamp / Freshness
    ↓
Authorization
    ↓
Replay Detection
```

The final security decision combines quantum evidence and protocol evidence.

---

# 5. Main Participants

The conceptual security model uses three participants.

## Alice — Signer

Alice is the legitimate signer.

She creates or authorizes a digital signature associated with a message.

---

## Bob — Authorized Verifier

Bob is the legitimate verifier or recipient.

Bob verifies whether the signature is valid and whether the associated quantum/statistical evidence is consistent with legitimate behaviour.

---

## Eve — Adversary

Eve represents an attacker.

Depending on the experiment, Eve may attempt to:

* Forge a signature
* Replay an old valid signature
* Impersonate Alice
* Perform unauthorized verification
* Manipulate the quantum communication channel
* Introduce quantum operations or disturbances

The exact attacker capability must be explicitly defined for every experiment.

---

# 6. Quantum Model

The project uses a **qubit-level simulation model**.

The model will use quantum states such as:

```text
|0>
|1>
|+>
|->
|+i>
|-i>
```

These correspond to eigenstates of the Pauli operators.

### Pauli X

The Pauli-X operator performs a bit-flip:

```text
X|0> = |1>
X|1> = |0>
```

### Pauli Y

The Pauli-Y operator performs a bit-and-phase transformation.

### Pauli Z

The Pauli-Z operator performs a phase flip:

```text
Z|0> = |0>
Z|1> = -|1>
```

These states and operators are important for the quantum verification and channel-manipulation experiments.

---

# 7. Bell-State Entanglement

The system must explicitly demonstrate Bell-state generation.

The Bell states are:

```text
|Φ+> = (|00> + |11>) / √2

|Φ-> = (|00> - |11>) / √2

|Ψ+> = (|01> + |10>) / √2

|Ψ-> = (|01> - |10>) / √2
```

At minimum, the implementation must generate and verify one Bell state and demonstrate the expected measurement correlations.

Bell-state generation is a required component because teleportation depends on shared entanglement.

---

# 8. Quantum Teleportation

Quantum teleportation is a core requirement of the project.

The conceptual process is:

```text
Unknown/Input Qubit
        +
Shared Bell Pair
        ↓
Alice's Bell Measurement
        ↓
Two Classical Measurement Bits
        ↓
Bob's Qubit
        ↓
Pauli Correction
        ↓
Recovered Quantum State
```

The classical measurement results determine which correction Bob applies.

The correction operations are:

```text
00 → I
01 → X
10 → Z
11 → XZ
```

The exact circuit convention must be documented and tested carefully because the ordering of classical bits and correction operations depends on the circuit implementation.

The implementation must verify that the corrected output reproduces the expected input state statistically.

---

# 9. Projective Measurement

The system must use projective measurements rather than treating quantum states as ordinary deterministic variables.

For a measurement basis containing projectors:

```text
P_i
```

the probability of obtaining outcome `i` is:

```text
P(i) = <ψ|P_i|ψ>
```

Measurement outcomes are inherently probabilistic.

Therefore:

```text
Quantum measurement = probabilistic
Final security decision = deterministic
```

This distinction is fundamental to the project.

---

# 10. Measurement Statistics

The detector will collect multiple measurement outcomes, commonly referred to as **shots**.

For example:

```text
Shots = 1000
```

may produce:

```text
0 → 493
1 → 507
```

The system converts raw measurement counts into empirical probabilities.

For outcome `i`:

```text
p̂_i = n_i / N
```

where:

* `n_i` = number of occurrences of outcome `i`
* `N` = total number of shots
* `p̂_i` = empirical probability

These statistics become the input to the detection engine.

---

# 11. Honest Baseline

Noise must not automatically be treated as an attack.

The system therefore requires an **honest-operation baseline**.

The baseline is obtained by running legitimate executions under defined conditions.

For example:

```text
Honest execution
      ↓
Known noise configuration
      ↓
Many trials
      ↓
Measurement statistics
      ↓
Mean / variance / confidence interval
      ↓
Expected operating region
```

A new verification attempt is compared against this operating region.

This prevents the detector from simply treating every deviation caused by normal system noise as malicious activity.

---

# 12. Noise-Calibrated Quantum Integrity Fingerprinting

One of the primary proposed features of Q-SHIELD is a **Noise-Calibrated Quantum Integrity Fingerprint**.

The concept is:

```text
Legitimate executions
        ↓
Quantum measurements
        ↓
Statistical characterization
        ↓
Honest operating region
        ↓
Quantum integrity fingerprint
```

A new verification attempt produces another statistical fingerprint.

The detector compares the new fingerprint with the expected legitimate region.

Possible metrics include:

* X-basis distribution
* Y-basis distribution
* Z-basis distribution
* Measurement error rate
* QBER
* State fidelity
* Bell-state correlation
* Other mathematically justified metrics

The detector then applies predefined statistical rules.

This is not machine learning.

The fingerprint is a mathematical/statistical representation of expected quantum behaviour.

---

# 13. Multi-Layer Security Evidence

Q-SHIELD uses two major categories of security evidence.

## Quantum Evidence

Examples:

* Measurement distribution
* X/Y/Z statistics
* Fidelity
* QBER
* Bell correlations
* Disturbance level
* Channel-operation effects

## Protocol Evidence

Examples:

* Signer identity
* Verifier identity
* Session identifier
* Nonce
* Timestamp
* Authorization
* Replay history
* Message/signature relationship

The final detector combines these through deterministic rules.

Conceptually:

```text
Quantum Evidence
        +
Protocol Evidence
        ↓
Evidence Fusion
        ↓
Deterministic Rule Engine
        ↓
Security Decision
```

---

# 14. Final Decision States

The system should support three high-level outcomes:

```text
ACCEPT
SUSPICIOUS
ATTACK
```

## ACCEPT

The verification satisfies the required protocol and quantum/statistical conditions.

## SUSPICIOUS

The evidence is abnormal or inconclusive but does not satisfy the conditions required to confidently classify the event as an attack.

## ATTACK

The evidence violates one or more clearly defined security conditions.

The exact decision boundaries must be defined mathematically and documented.

---

# 15. Attack Categories

The system must support at least the following attack categories.

## 15.1 Forgery

An attacker attempts to construct or modify a signature such that the verifier accepts it despite the legitimate signer not authorizing that signature/message combination.

Relevant evidence may include:

* Quantum-state mismatch
* Measurement-statistics deviation
* Fidelity reduction
* Increased error rate
* Threshold violation
* Protocol inconsistency

The system should estimate an empirical false-accept/forgery probability from repeated trials.

---

## 15.2 Replay Attack

An attacker captures a previously valid signed transaction and submits it again.

Replay is primarily a **protocol-layer attack**.

Detection should use mechanisms such as:

* Nonce
* Session identifier
* Timestamp/freshness
* Previously-used transaction/session tracking

A replayed message can have perfectly valid quantum statistics and still be rejected because the protocol state is invalid.

---

## 15.3 Impersonation

An attacker claims to be the legitimate signer.

Detection may use:

* Identity validation
* Authentication context
* Session validation
* Authorization
* Signature ownership relationship

Impersonation is primarily an authentication/protocol-layer problem.

---

## 15.4 Unauthorized Verification

An unauthorized entity attempts to verify or access verification information.

Detection should use:

* Verifier identity
* Authorization state
* Session validity
* Access policy

This attack does not necessarily produce quantum-channel disturbance.

---

## 15.5 Quantum-Channel Manipulation

An attacker manipulates the quantum communication channel.

Possible simulated operations include:

```text
X
Y
Z
```

and configurable noise/disturbance models such as:

```text
Bit flip
Phase flip
Depolarizing noise
Readout error
```

The system should analyze how increasing disturbance affects:

* Measurement distributions
* Fidelity
* QBER
* Bell correlations
* Acceptance probability
* Detection probability

---

# 16. Noise vs Attack

The project must explicitly distinguish:

```text
Normal Noise ≠ Attack
```

Noise may naturally alter measurement outcomes.

An attack represents intentional or modeled malicious interference.

Therefore the system should first establish expected honest behaviour under the configured noise conditions.

Example:

```text
Low deviation
    ↓
Within honest operating region
    ↓
ACCEPT
```

versus:

```text
Large deviation
    ↓
Outside honest operating region
    ↓
Suspicious / Attack
```

The thresholds must be statistically justified rather than arbitrarily chosen.

---

# 17. Statistical Detection Philosophy

The detector must not use:

* Neural networks
* Machine learning
* AI classifiers
* Clustering
* Learned attack models

Instead it should use mathematical rules.

Possible methods include:

* Empirical probability
* Mean
* Variance
* Standard deviation
* Confidence intervals
* Hypothesis-testing concepts
* QBER thresholds
* Fidelity thresholds
* Distribution comparison
* Statistically derived operating regions

The final decision must be deterministic once the measurement data and protocol information are available.

---

# 18. Deterministic Acceptance

Quantum measurements are probabilistic, but the verification decision can be deterministic.

For example:

```text
Measurement experiment
        ↓
Probabilistic outcomes
        ↓
Aggregate statistics
        ↓
Compare with predefined criteria
        ↓
Deterministic result
```

Therefore the project should demonstrate:

> Probabilistic quantum measurements can be converted into a deterministic verification decision through statistically defined acceptance rules.

This satisfies the requirement for deterministic legitimate acceptance without incorrectly claiming that individual quantum measurements are deterministic.

---

# 19. Information-Theoretic Security

Q-SHIELD must carefully distinguish between the underlying QDS security model and the software detector.

The detector itself does **not** create information-theoretic security.

Information-theoretic security claims belong to the underlying QDS protocol and its assumptions.

The project should therefore state:

```text
QDS protocol
    ↓
Provides security guarantees under its assumptions

Q-SHIELD
    ↓
Simulates / analyzes protocol behaviour
    ↓
Detects deviations and attacks
```

The software must not claim:

> "Our detector guarantees information-theoretic security."

Instead it should claim:

> "The framework is designed to analyze a QDS-inspired protocol while preserving the conceptual distinction between information-theoretic QDS security assumptions and empirical software-based threat detection."

---

# 20. Published QDS vs Our Prototype

The project uses a **qubit-level teleportation-based QDS-inspired model** for software simulation.

This is an engineering abstraction intended to satisfy the SIH requirements while remaining understandable, testable and implementable.

Published teleportation-based QDS protocols may use different physical models, including continuous-variable quantum systems and specific optical implementations.

Therefore Q-SHIELD must not claim:

> "This software exactly implements a published physical QDS protocol."

Instead:

> "Q-SHIELD implements a qubit-level simulation model inspired by teleportation-based QDS concepts and explicitly documents the abstraction from physical QDS protocols."

Any difference between the literature protocol and the prototype must be documented.

---

# 21. Simulation Rather Than Physical Quantum Hardware

A real quantum computer is not required.

The system will use quantum-circuit simulation.

The primary development stack is:

* Python
* Qiskit
* Qiskit Aer
* NumPy
* SciPy
* Pandas
* Matplotlib
* Streamlit

The simulator allows the team to:

* Construct quantum circuits
* Execute teleportation
* Apply noise
* Perform measurements
* Collect many shots
* Analyze statistical behaviour
* Reproduce experiments

---

# 22. Development Philosophy

Development follows a divide-and-conquer approach.

The project will not attempt to implement the complete system at once.

The intended development loop is:

```text
Requirement
    ↓
Understand
    ↓
Design
    ↓
Implement
    ↓
Test
    ↓
Experiment
    ↓
Verify
    ↓
Document
    ↓
Update Progress
    ↓
Next Module
```

Every major module must be independently testable.

---

# 23. Development Order

The implementation should progress approximately in this order:

```text
M0  Environment Setup
M1  Qubit Fundamentals
M2  Pauli Operators
M3  Projective Measurement
M4  Bell States
M5  Quantum Teleportation
M6  Noise Models
M7  QDS Protocol Specification
M8  Quantum Signature Verification
M9  Honest Baseline
M10 Statistical Threshold Engine
M11 Forgery Detection
M12 Replay Detection
M13 Impersonation Detection
M14 Unauthorized Verification
M15 Quantum Channel Attacks
M16 Evidence Fusion
M17 Security Evaluation
M18 Performance Evaluation
M19 Dashboard
M20 Blockchain Audit Layer
```

Blockchain is intentionally postponed until the core security model works.

---

# 24. Minimum Viable Product

The minimum viable Q-SHIELD system should contain:

```text
Qubit States
+
Pauli Operators
+
Projective Measurement
+
Bell State
+
Quantum Teleportation
+
Pauli Corrections
+
Noise
+
Honest Baseline
+
Statistical Threshold
+
Forgery Simulation
+
Replay Detection
+
Quantum Channel Attack
+
Deterministic Decision
```

The system must be able to demonstrate at least one complete end-to-end verification experiment.

---

# 25. Competition-Level Version

The competition-ready version should add:

* Noise-calibrated baseline
* Quantum integrity fingerprint
* Multi-layer evidence fusion
* Explainable security decisions
* Attack laboratory
* Forgery probability experiments
* FAR/FRR analysis
* Detection probability
* Noise-vs-detection experiments
* Attack-strength-vs-detection experiments
* Performance benchmarking
* Interactive dashboard
* Verification history
* Optional blockchain audit layer

---

# 26. Blockchain Position

Blockchain is not part of the core quantum security mechanism.

It is an optional later-stage audit layer.

The intended architecture is:

```text
Quantum Verification
        ↓
Security Decision
        ↓
Verification Record
        ↓
Hash / Audit Data
        ↓
Blockchain
```

Blockchain may be used to provide tamper-evident logging of verification events.

It must not be presented as the mechanism that provides QDS's information-theoretic security.

---

# 27. Expected Evaluation Metrics

The system should measure:

## Security Metrics

* Legitimate acceptance rate
* False rejection rate (FRR)
* False acceptance rate (FAR)
* Attack detection rate
* Empirical forgery probability
* Replay detection rate
* Impersonation detection rate
* Unauthorized verification rejection rate
* Channel-attack detection rate

## Quantum Metrics

* Measurement probability
* Fidelity
* QBER where applicable
* Bell-state correlation
* Measurement deviation
* Quantum-state mismatch

## Performance Metrics

* Number of qubits
* Number of gates
* Circuit depth
* Number of shots
* Simulation time
* Verification time
* Statistical processing time
* Total verification latency
* Throughput
* Memory usage

---

# 28. Explainability Requirement

Every security decision should provide evidence.

Example:

```text
Decision: ATTACK

Attack Type: Quantum Channel Manipulation

Evidence:
- Z-basis error rate: 0.31
- Honest baseline: 0.04
- Threshold: 0.10
- Fidelity: 0.71
- Honest fidelity region: ≥ 0.93
- Protocol checks: PASS

Reason:
Quantum measurement statistics significantly
deviate from the calibrated honest operating region.
```

The actual values must come from the experiment rather than being hard-coded examples.

---

# 29. Reproducibility

Every experiment should record:

* Experiment ID
* Date/time
* Number of shots
* Number of trials
* Quantum state
* Measurement basis
* Noise model
* Noise strength
* Attack type
* Attack strength
* Threshold configuration
* Statistical method
* Results
* Interpretation
* Limitations

Random seeds should be supported where appropriate so experiments can be reproduced.

---

# 30. Security Claim Boundaries

Q-SHIELD must never claim:

* Perfect security
* 100% attack detection
* Zero false positives
* Zero false negatives
* Absolute information-theoretic security of the software
* Exact physical implementation of every QDS protocol
* Quantum hardware deployment when only simulation is used

The project should clearly distinguish:

```text
Theoretical security
        vs
Simulation results
        vs
Empirical experimental evidence
```

---

# 31. Core Innovation

The primary proposed innovation is:

## Noise-Calibrated Quantum Integrity Fingerprinting

Instead of using a fixed arbitrary threshold, the system establishes expected legitimate behaviour under the selected noise conditions and compares new verification attempts against that calibrated region.

This makes the detector more scientifically defensible than simply declaring:

```text
error > 10% → attack
```

without explaining why 10% is valid.

---

# 32. Secondary Innovation

The second proposed innovation is:

## Multi-Layer Security Evidence

The system combines:

```text
Quantum Evidence
+
Protocol Evidence
+
Statistical Evidence
```

to produce:

```text
Attack Type
+
Security Decision
+
Explanation
```

This is important because not every security attack is visible through quantum measurements.

For example:

```text
Replay attack
→ protocol evidence

Unauthorized verification
→ authorization evidence

Quantum-channel manipulation
→ quantum evidence

Forgery
→ quantum + protocol evidence
```

---

# 33. Technology Direction

The initial technology stack is:

```text
Programming Language:
Python

Quantum Framework:
Qiskit

Quantum Simulator:
Qiskit Aer

Numerical Computing:
NumPy

Scientific Statistics:
SciPy

Data Analysis:
Pandas

Visualization:
Matplotlib

Dashboard:
Streamlit

Initial Persistence:
SQLite if required

Optional API:
FastAPI

Optional Blockchain:
Local Ethereum-compatible development network
```

Only required dependencies should be installed at each development stage.

---

# 34. Repository Philosophy

The repository should remain organized according to responsibility.

Expected eventual structure:

```text
Q-SHIELD/
│
├── README.md
├── PROJECT_CONTEXT.md
├── REQUIREMENTS.md
├── ARCHITECTURE.md
├── DEVELOPMENT_PLAN.md
├── AI_INSTRUCTIONS.md
├── SCIENTIFIC_RULES.md
├── THREAT_MODEL.md
├── QDS_PROTOCOL.md
├── MATHEMATICAL_MODEL.md
├── SECURITY_MODEL.md
├── TESTING_STRATEGY.md
├── EXPERIMENT_PLAN.md
├── PERFORMANCE_PLAN.md
├── DECISIONS.md
├── PROGRESS.md
├── GLOSSARY.md
│
├── docs/
│
├── src/
│
├── tests/
│
├── experiments/
│
├── dashboard/
│
├── data/
│
└── requirements.txt
```

Source directories should be created progressively as milestones are implemented.

---

# 35. Current Project State

At the beginning of implementation:

```text
Documentation:
IN PROGRESS

Quantum implementation:
NOT STARTED

QDS implementation:
NOT STARTED

Attack detection:
NOT STARTED

Dashboard:
NOT STARTED

Blockchain:
NOT STARTED
```

The first technical milestone is environment setup.

---

# 36. Important Rule for AI-Assisted Development

AI coding agents such as Antigravity must not invent missing scientific or protocol decisions.

If an implementation requires an undefined security or QDS protocol decision, the AI must stop that portion of implementation and report:

```text
1. What decision is missing
2. Why the decision matters
3. Possible alternatives
4. Recommended choice, if enough evidence exists
5. What documentation must be updated
```

Only after the decision is explicitly accepted should implementation continue.

---

# 37. Final Project Vision

Q-SHIELD should ultimately provide an interactive environment where a user can:

```text
Create / select a signature
        ↓
Run teleportation-based quantum verification
        ↓
Observe quantum measurements
        ↓
Apply statistical analysis
        ↓
Introduce noise or an attack
        ↓
Run verification again
        ↓
Compare against honest baseline
        ↓
Receive deterministic decision
        ↓
See the evidence explaining the decision
        ↓
Inspect security/performance analytics
```

The final product should therefore demonstrate not merely that quantum circuits can be simulated, but that **quantum measurement statistics can be integrated with deterministic security rules to analyze digital-signature verification behaviour and simulated attacks.**

---

# 38. Non-Negotiable Project Principles

The following principles apply throughout the project:

1. No AI/ML-based threat detection.
2. Teleportation must be explicitly demonstrated.
3. Bell-state entanglement must be explicitly demonstrated.
4. Pauli corrections must be explicitly demonstrated.
5. Projective measurement must be used and explained.
6. Measurement statistics must be collected over multiple shots.
7. Honest noise must be distinguished from malicious manipulation.
8. Thresholds must be statistically justified.
9. Forgery probability must be experimentally evaluated.
10. Legitimate verification must be evaluated.
11. Malicious verification must be evaluated.
12. Replay, impersonation and authorization attacks must be treated as protocol-level threats where appropriate.
13. Quantum-channel attacks must be modeled explicitly.
14. Security decisions must be deterministic after measurement data is collected.
15. Information-theoretic security claims must remain tied to the underlying QDS assumptions.
16. The prototype must not falsely claim to reproduce a physical QDS deployment.
17. Every major module must have tests.
18. Every major experiment must be documented.
19. Blockchain must not be allowed to complicate the core implementation.
20. Scientific correctness takes priority over adding flashy features.

---

# 39. Definition of Success

The project is successful if it can demonstrate, using a reproducible software simulation:

```text
Legitimate signature
        ↓
Quantum teleportation
        ↓
Pauli correction
        ↓
Measurement
        ↓
Expected statistical behaviour
        ↓
Deterministic ACCEPT
```

and:

```text
Malicious modification / attack
        ↓
Changed quantum or protocol evidence
        ↓
Statistical / rule-based analysis
        ↓
Deterministic SUSPICIOUS or ATTACK
        ↓
Explainable security evidence
```

while remaining scientifically honest about the difference between:

```text
QDS theory
Quantum simulation
Threat detection
Physical deployment
```

This distinction is central to the credibility of Q-SHIELD.
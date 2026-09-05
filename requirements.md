# Q-SHIELD — System Requirements

## 1. Purpose

This document defines the functional, scientific, security, performance and project constraints for Q-SHIELD.

Q-SHIELD is a software-based simulation and threat-detection framework for a teleportation-based Quantum Digital Signature (QDS)-inspired model.

The requirements in this document are binding for development.

If a proposed implementation conflicts with a requirement, the requirement takes priority unless the requirement is explicitly revised and documented in `DECISIONS.md`.

---

# 2. Requirement Categories

Requirements are divided into:

* Core Quantum Requirements
* QDS Requirements
* Threat Detection Requirements
* Statistical Requirements
* Security Requirements
* Performance Requirements
* Simulation Requirements
* Evaluation Requirements
* UI Requirements
* Future Blockchain Requirements
* Development Restrictions

---

# 3. Core Quantum Requirements

## RQ-01 — Qubit Representation

The system SHALL represent and manipulate qubit states using an appropriate quantum-computing framework.

The initial implementation will use Qiskit.

The system must support, at minimum:

```text
|0>
|1>
|+>
|->
|+i>
|-i>
```

These states are important because they represent eigenstates of the Pauli operators.

---

## RQ-02 — Pauli Operators

The system SHALL explicitly implement or use the following Pauli operators:

```text
X
Y
Z
```

The implementation must demonstrate their effects on appropriate quantum states.

At minimum, tests must verify:

```text
X|0> = |1>
X|1> = |0>

Z|0> = |0>
Z|1> = -|1>
```

The Y operator must also be tested using the appropriate complex-valued state representation.

---

## RQ-03 — Pauli Eigenstates

The system SHALL support the eigenstates of the Pauli operators.

### Z basis

```text
|0>
|1>
```

### X basis

```text
|+>  = (|0> + |1>) / √2
|->  = (|0> - |1>) / √2
```

### Y basis

```text
|+i> = (|0> + i|1>) / √2
|-i> = (|0> - i|1>) / √2
```

The implementation must verify that these states behave as expected when measured in their corresponding bases.

---

## RQ-04 — Projective Measurement

The system SHALL use projective measurement concepts.

For a projector `P_i`, the probability of measurement outcome `i` is:

```text
P(i) = <ψ|P_i|ψ>
```

The implementation must distinguish theoretical probability from experimentally observed frequency.

---

## RQ-05 — Measurement Statistics

Quantum measurements SHALL be performed over multiple shots.

The system must collect raw measurement counts and convert them into empirical probabilities.

For outcome `i`:

```text
p_hat_i = n_i / N
```

where:

* `n_i` = number of observations of outcome `i`
* `N` = total number of shots
* `p_hat_i` = empirical probability

The number of shots must be configurable.

---

# 4. Bell-State Requirements

## RQ-06 — Bell-State Generation

The system SHALL explicitly simulate Bell-state entanglement.

At least one Bell state must be generated and verified.

The preferred initial state is:

```text
|Phi+> = (|00> + |11>) / sqrt(2)
```

The system should demonstrate the expected correlation between measurements.

---

## RQ-07 — Bell-State Verification

The system SHALL include tests verifying that the generated Bell state produces the expected measurement correlations within statistical variation.

The test must not expect every individual shot to behave identically.

The test must evaluate aggregate statistics.

---

# 5. Quantum Teleportation Requirements

## RQ-08 — Quantum Teleportation

The system SHALL explicitly simulate quantum teleportation.

The teleportation pipeline must include:

```text
Input qubit
      ↓
Shared Bell pair
      ↓
Bell measurement
      ↓
Classical measurement results
      ↓
Pauli correction
      ↓
Recovered state
```

---

## RQ-09 — Pauli Corrections

The teleportation implementation SHALL apply the appropriate Pauli correction operations based on the Bell-measurement results.

The correction mapping must be explicitly documented and tested.

The implementation must account for the chosen circuit/classical-bit convention.

---

## RQ-10 — Teleportation Verification

The system SHALL verify that the output of teleportation statistically agrees with the intended input state after the required Pauli correction.

Verification must be performed for multiple input states.

At minimum, the implementation should test representative states from the Z, X and Y bases.

---

# 6. QDS Requirements

## RQ-11 — Teleportation-Based QDS

The project SHALL specifically target a teleportation-based Quantum Digital Signature framework.

It must not become a generic quantum-signature project unrelated to teleportation.

---

## RQ-12 — QDS-Inspired Simulation Model

The implementation will use a clearly documented qubit-level simulation abstraction.

The system must explicitly state which parts are:

```text
Published QDS concepts
```

and which parts are:

```text
Engineering simplifications / simulation choices
```

The project must not falsely claim that the simulation is an exact physical implementation of every published teleportation-based QDS protocol.

---

## RQ-13 — QDS Participants

The system SHALL model:

```text
Alice → Signer
Bob   → Authorized verifier
Eve   → Adversary
```

The roles must be clearly represented in the protocol and security model.

---

## RQ-14 — Message-Signature Relationship

The system SHALL represent a relationship between a message and its corresponding signature.

The implementation must be able to distinguish:

```text
Valid message + valid signature
```

from:

```text
Modified message
Modified signature
Mismatched message/signature
```

The exact signature representation must be defined in `QDS_PROTOCOL.md` before implementation of the final QDS layer.

---

# 7. Threat Detection Requirements

## RQ-15 — Threat Detection Is Core

Threat detection SHALL be a core component of the system.

The project must not stop at demonstrating quantum teleportation.

The system must use quantum and/or protocol evidence to determine whether a verification attempt is legitimate or suspicious.

---

## RQ-16 — Forgery Detection

The system SHALL simulate signature-forgery attempts.

A forgery attempt represents an attacker attempting to cause acceptance of a signature/message combination that was not legitimately authorized.

The system must evaluate:

* Forged acceptance
* Forged rejection
* Empirical forgery probability
* Detection rate

---

## RQ-17 — Replay Detection

The system SHALL detect replay attacks.

Replay detection must use protocol-level information such as:

* Nonce
* Session identifier
* Timestamp/freshness
* Previously observed transaction/session information

A replayed valid signature must not automatically be considered a valid new transaction.

---

## RQ-18 — Impersonation Detection

The system SHALL simulate and detect impersonation attempts.

The implementation may use:

* Signer identity
* Authentication context
* Authorization
* Session information
* Signature ownership relationship

Impersonation must not be incorrectly represented as purely a quantum-channel attack.

---

## RQ-19 — Unauthorized Verification Detection

The system SHALL detect verification attempts made by an unauthorized verifier.

The system must support:

```text
Authorized verifier
Unauthorized verifier
```

and produce different security outcomes according to the configured authorization policy.

---

## RQ-20 — Quantum-Channel Attack Detection

The system SHALL simulate manipulation of the quantum communication channel.

At minimum, the attack framework should support:

```text
X operation
Y operation
Z operation
```

and configurable channel disturbances such as:

```text
Bit-flip noise
Phase-flip noise
Depolarizing noise
Readout error
```

Where appropriate, additional channel models may be added later.

---

# 8. Statistical Detection Requirements

## RQ-21 — No AI/ML Detection

Threat detection SHALL NOT use:

* Artificial intelligence
* Machine learning
* Neural networks
* Deep learning
* Classification models
* Clustering
* Learned anomaly detectors
* Trained prediction models

Detection must be based on deterministic mathematical and statistical rules.

---

## RQ-22 — Statistical Detection

The system SHALL analyze measurement statistics.

Potential evidence includes:

* Measurement probabilities
* Frequency distributions
* Mean
* Variance
* Standard deviation
* Confidence intervals
* Fidelity
* QBER where applicable
* Bell-state correlations
* Statistical deviation from baseline

Only mathematically justified metrics should be used.

---

## RQ-23 — Threshold-Based Decisions

The system SHALL use threshold or statistically defined acceptance criteria.

Thresholds must not simply be arbitrary hard-coded numbers.

The system should derive thresholds from:

* Honest baseline experiments
* Statistical confidence
* Defined protocol parameters
* Literature-supported parameters where appropriate

The reason for every security threshold must be documented.

---

## RQ-24 — Honest Baseline

The system SHALL establish a baseline representing legitimate operation under defined noise conditions.

The baseline should be generated using repeated honest executions.

The baseline may include:

```text
Mean
Variance
Standard deviation
Confidence interval
Expected measurement distribution
Expected fidelity
Expected QBER
Expected Bell correlation
```

depending on the metric.

---

## RQ-25 — Noise Calibration

The system SHALL account for expected system noise when establishing the honest operating region.

A verification attempt should be compared against the appropriate baseline.

The system must avoid treating all noise-induced deviations as attacks.

---

## RQ-26 — Quantum Integrity Fingerprint

The system SHOULD implement a statistical representation of expected legitimate quantum behaviour.

The fingerprint may contain:

```text
X-basis statistics
Y-basis statistics
Z-basis statistics
Fidelity
QBER
Bell correlation
Measurement deviation
```

The exact fingerprint structure must be documented before final implementation.

---

# 9. Security Decision Requirements

## RQ-27 — Deterministic Final Decision

The final verification decision SHALL be deterministic after the measurement data and protocol information have been collected.

Possible states:

```text
ACCEPT
SUSPICIOUS
ATTACK
```

Quantum measurements themselves remain probabilistic.

The system must not incorrectly describe quantum measurement as deterministic.

---

## RQ-28 — Legitimate Signature Acceptance

The system SHALL evaluate whether legitimate signatures are accepted.

A legitimate signature operating inside the statistically defined honest region should be accepted according to the configured verification policy.

The system must measure legitimate acceptance performance.

---

## RQ-29 — Malicious Signature Rejection

The system SHALL evaluate whether malicious or invalid signatures are rejected.

The system must measure the rejection performance under simulated attacks.

---

## RQ-30 — Explainable Decision

Every final security decision SHOULD include evidence explaining why the decision was produced.

Example:

```text
Decision:
ATTACK

Attack:
Quantum Channel Manipulation

Evidence:
QBER exceeded calibrated operating region.
Fidelity decreased below the configured acceptance region.
Bell correlation deviated from the honest baseline.
```

The actual evidence must be generated from the experiment.

---

# 10. Forgery Probability Requirements

## RQ-31 — Empirical Forgery Probability

The system SHALL estimate the probability that a forged signature is incorrectly accepted.

For repeated forgery trials:

```text
P_forge ≈ number of accepted forged attempts
          --------------------------------
          total forgery attempts
```

The system must clearly label this as an **empirical estimate** rather than an absolute theoretical security guarantee.

---

## RQ-32 — Forgery Experiments

Forgery experiments SHALL support configurable:

* Number of trials
* Number of shots
* Input states
* Attack strategy
* Noise configuration
* Verification thresholds

Results must be recorded for analysis.

---

# 11. Verification Accuracy Requirements

## RQ-33 — False Acceptance Rate

The system SHALL calculate the False Acceptance Rate (FAR) where appropriate.

Conceptually:

```text
FAR =
malicious attempts incorrectly accepted
---------------------------------------
total malicious attempts
```

The exact experimental definition must be documented.

---

## RQ-34 — False Rejection Rate

The system SHALL calculate the False Rejection Rate (FRR).

Conceptually:

```text
FRR =
legitimate attempts incorrectly rejected
----------------------------------------
total legitimate attempts
```

---

## RQ-35 — Detection Rate

The system SHALL evaluate attack detection performance.

For a defined attack experiment:

```text
Detection Rate =
correctly detected attacks
--------------------------
total attack attempts
```

The attack definition and experimental conditions must always accompany the metric.

---

# 12. Information-Theoretic Security Requirements

## RQ-36 — Security Claim Boundary

The system SHALL NOT claim that the software detector itself provides information-theoretic security.

Information-theoretic security claims must be associated with the underlying QDS protocol and its assumptions.

---

## RQ-37 — Theoretical vs Empirical Security

The project SHALL distinguish:

```text
Theoretical QDS security
```

from:

```text
Simulation results
```

and:

```text
Empirical detector performance
```

These must not be presented as equivalent.

---

# 13. Attack Model Requirements

## RQ-38 — Explicit Attacker Capabilities

Every attack experiment SHALL define:

* Attacker identity
* Attacker capabilities
* Attacker inputs
* Attacker actions
* Expected effect
* Observable evidence
* Detection rule
* Expected result

No attack model should be left ambiguous.

---

## RQ-39 — Attack vs Noise

The system SHALL distinguish between:

```text
Honest noise
```

and:

```text
Intentional attack disturbance
```

The same physical operation may represent noise in one experiment and malicious manipulation in another, depending on the threat model.

---

# 14. Simulation Requirements

## RQ-40 — Quantum Simulation

The system SHALL operate using quantum simulation.

A physical quantum computer is not required.

---

## RQ-41 — Configurable Shots

The number of circuit shots SHALL be configurable.

Suggested experiment values include:

```text
100
500
1000
4096
8192
```

Additional values may be tested.

---

## RQ-42 — Configurable Noise

Noise configuration SHALL be adjustable for experiments.

The system should allow researchers to vary:

```text
Noise type
Noise strength
Measurement error
Attack strength
```

---

# 15. Evaluation Requirements

## RQ-43 — Security Evaluation

The system SHALL provide experiments for:

* Honest verification
* Forgery
* Replay
* Impersonation
* Unauthorized verification
* Quantum-channel manipulation

---

## RQ-44 — Noise Sensitivity Evaluation

The system SHOULD evaluate how increasing noise affects:

* Legitimate acceptance
* False rejection
* Fidelity
* QBER
* Measurement statistics

---

## RQ-45 — Attack Strength Evaluation

The system SHOULD evaluate how increasing attack strength affects:

* Detection rate
* False acceptance
* Quantum metrics
* Statistical deviation

---

## RQ-46 — Shot Stability Evaluation

The system SHOULD evaluate how the number of shots affects the stability of the measured statistics.

Example:

```text
100 shots
500 shots
1000 shots
4096 shots
8192 shots
```

---

# 16. Performance Requirements

## RQ-47 — Efficient Verification

The verification pipeline SHOULD minimize unnecessary computation.

The system must measure:

* Circuit size
* Qubit count
* Gate count
* Circuit depth
* Number of shots
* Simulation time
* Statistical processing time
* Total verification time

---

## RQ-48 — Performance Benchmarking

The system SHALL provide performance experiments for multiple shot counts.

Performance results must be reported rather than assumed.

---

# 17. Dashboard Requirements

## RQ-49 — Interactive Dashboard

A Streamlit dashboard SHOULD be implemented after the core engine is working.

The dashboard must not be developed before the underlying verification and detection modules are sufficiently stable.

---

## RQ-50 — Dashboard Pages

The intended dashboard structure is:

```text
1. Dashboard
2. Signature Verification
3. Quantum Monitor
4. Attack Laboratory
5. Security Analytics
6. Verification History
```

---

## RQ-51 — Verification Page

The verification interface should allow the user to configure appropriate parameters such as:

* Signer
* Verifier
* Message
* Signature
* Session
* Nonce
* Noise
* Shots

and execute a verification experiment.

---

## RQ-52 — Quantum Monitor

The dashboard should display, where appropriate:

* Bell-state circuit
* Teleportation circuit
* Pauli corrections
* Measurement results
* Measurement distributions
* Fidelity
* QBER
* Bell correlations

---

## RQ-53 — Attack Laboratory

The dashboard should allow users to select simulated attacks and configure relevant attack parameters.

Supported categories:

```text
Forgery
Replay
Impersonation
Unauthorized verification
Quantum-channel manipulation
```

---

## RQ-54 — Security Analytics

The dashboard should provide visualizations for:

* Honest baseline
* Thresholds
* FAR
* FRR
* Detection rate
* Forgery probability
* Noise vs detection
* Attack strength vs detection
* Shots vs statistical stability

---

# 18. Verification History Requirements

## RQ-55 — Verification Records

The system SHOULD store verification results.

A verification record may contain:

```text
Timestamp
Signer
Verifier
Message hash
Session
Nonce
Decision
Attack type
Quantum metrics
Statistical metrics
Noise configuration
```

---

## RQ-56 — Persistence

SQLite may be used for initial local persistence if required.

Persistence should remain simple until the core detection system is stable.

---

# 19. Blockchain Requirements

## RQ-57 — Blockchain Is Optional/Late Stage

Blockchain SHALL NOT be required for the first working prototype.

It must be implemented only after the core quantum verification and threat-detection pipeline is working.

---

## RQ-58 — Blockchain Purpose

If implemented, blockchain SHALL be used primarily for:

* Audit logging
* Tamper-evident verification records
* Verification-event integrity

Blockchain must not be described as the source of QDS information-theoretic security.

---

## RQ-59 — Blockchain Separation

The core detection system must work without blockchain.

The blockchain layer must therefore be modular and replaceable.

---

# 20. Scientific Integrity Requirements

## RQ-60 — No Unsupported Claims

The project SHALL NOT make claims that are unsupported by:

* Mathematical analysis
* Experimental results
* Published literature
* Explicit simulation assumptions

---

## RQ-61 — No 100% Security Claims

The project SHALL NOT claim:

```text
100% attack detection
100% forgery prevention
100% legitimate acceptance
Zero false positives
Zero false negatives
```

unless such a claim is explicitly proven under a precisely defined theoretical model, which is not expected for this prototype.

---

## RQ-62 — Physical vs Simulated System

The project SHALL clearly state that it is a software simulation.

The dashboard and documentation must not imply that a physical quantum network has been deployed.

---

## RQ-63 — Literature Alignment

Important scientific choices should be supported by appropriate quantum computing and QDS literature.

When an engineering simplification is made, it must be documented as a simplification.

---

# 21. Software Engineering Requirements

## RQ-64 — Modular Architecture

The implementation SHALL be modular.

Quantum functionality must not be tightly coupled to:

* Dashboard code
* Database code
* Attack generation
* Statistical analysis
* Blockchain code

---

## RQ-65 — Unit Testing

Each major module SHALL have unit tests.

Tests should cover:

* Normal behaviour
* Boundary conditions
* Invalid inputs
* Statistical variation
* Attack cases
* Regression cases

---

## RQ-66 — Integration Testing

After individual modules are stable, integration tests SHALL verify the complete pipeline.

Example:

```text
State preparation
→ Teleportation
→ Measurement
→ Statistics
→ Baseline
→ Threshold
→ Detection
→ Decision
```

---

## RQ-67 — Reproducibility

Experiments SHOULD support reproducible configurations.

Where randomness is involved, random seeds should be configurable where technically appropriate.

---

# 22. AI-Assisted Development Requirements

## RQ-68 — AI Coding Restrictions

AI coding agents may assist with:

* Code generation
* Refactoring
* Testing
* Documentation
* Debugging
* Explanations

However, AI must not independently invent undefined security or QDS protocol decisions.

---

## RQ-69 — Incremental Development

AI-assisted implementation SHALL follow the milestone sequence defined in `DEVELOPMENT_PLAN.md`.

Future modules must not be implemented prematurely merely for convenience.

---

## RQ-70 — Scientific Decision Escalation

If an AI coding agent encounters an undefined scientific or protocol decision, it must stop that part of the implementation and report the missing decision.

It must not silently invent a protocol.

---

# 23. Non-Functional Requirements

## RNF-01 — Understandability

The code should be understandable to developers who are beginners in quantum computing.

---

## RNF-02 — Explainability

Security decisions must be explainable using observable evidence.

---

## RNF-03 — Maintainability

Each major component should have a clear responsibility.

---

## RNF-04 — Testability

Quantum, statistical, security and protocol components must be independently testable.

---

## RNF-05 — Reproducibility

Experiments should be reproducible from documented parameters.

---

## RNF-06 — Extensibility

The architecture should allow future addition of:

* Additional quantum states
* Additional noise models
* Additional attacks
* Additional statistical tests
* Additional QDS protocol variants
* Blockchain audit
* API layer

without rewriting the core system.

---

# 24. Requirement Traceability

The following table summarizes the most important SIH requirements.

| ID    | Requirement                | Priority | Planned Phase |
| ----- | -------------------------- | -------- | ------------- |
| RQ-01 | Qubit representation       | MUST     | M1            |
| RQ-02 | Pauli X/Y/Z                | MUST     | M2            |
| RQ-03 | Pauli eigenstates          | MUST     | M2            |
| RQ-04 | Projective measurement     | MUST     | M3            |
| RQ-05 | Measurement statistics     | MUST     | M3            |
| RQ-06 | Bell-state generation      | MUST     | M4            |
| RQ-07 | Bell-state verification    | MUST     | M4            |
| RQ-08 | Quantum teleportation      | MUST     | M5            |
| RQ-09 | Pauli corrections          | MUST     | M5            |
| RQ-10 | Teleportation verification | MUST     | M5            |
| RQ-11 | Teleportation-based QDS    | MUST     | M7            |
| RQ-12 | QDS-inspired simulation    | MUST     | M7            |
| RQ-15 | Threat detection           | MUST     | M10+          |
| RQ-16 | Forgery detection          | MUST     | M11           |
| RQ-17 | Replay detection           | MUST     | M12           |
| RQ-18 | Impersonation detection    | MUST     | M13           |
| RQ-19 | Unauthorized verification  | MUST     | M14           |
| RQ-20 | Quantum-channel attacks    | MUST     | M15           |
| RQ-21 | No AI/ML                   | MUST     | ALL           |
| RQ-23 | Statistical thresholds     | MUST     | M10           |
| RQ-24 | Honest baseline            | MUST     | M9            |
| RQ-25 | Noise calibration          | MUST     | M9            |
| RQ-27 | Deterministic decision     | MUST     | M10+          |
| RQ-31 | Forgery probability        | MUST     | M11           |
| RQ-33 | FAR                        | MUST     | M17           |
| RQ-34 | FRR                        | MUST     | M17           |
| RQ-35 | Detection rate             | MUST     | M17           |
| RQ-36 | Security claim boundary    | MUST     | ALL           |
| RQ-40 | Quantum simulation         | MUST     | ALL           |
| RQ-47 | Efficient verification     | SHOULD   | M18           |
| RQ-49 | Dashboard                  | SHOULD   | M19           |
| RQ-57 | Blockchain late stage      | SHOULD   | M20           |

---

# 25. Absolute Development Constraints

The following are non-negotiable unless explicitly changed in `DECISIONS.md`.

```text
NO AI/ML
NO ARBITRARY SECURITY THRESHOLDS
NO UNSUPPORTED SECURITY CLAIMS
NO 100% DETECTION CLAIMS
NO FALSE INFORMATION-THEORETIC SECURITY CLAIMS
NO PRETENDING SIMULATION IS PHYSICAL DEPLOYMENT
NO UNDOCUMENTED QDS PROTOCOL INVENTION
NO BLOCKCHAIN BEFORE CORE SYSTEM
NO UI BEFORE CORE ENGINE
NO LARGE MONOLITHIC IMPLEMENTATION
```

---

# 26. Definition of Done

A requirement is considered implemented only when:

```text
Implementation
+
Unit Tests
+
Integration Tests where applicable
+
Expected Behaviour Verified
+
Edge Cases Considered
+
Documentation Updated
+
Limitations Documented
```

A feature is not considered complete merely because its code executes without an error.

---

# 27. Requirement Change Policy

Requirements may change during development.

When a requirement changes:

1. Record the change in `DECISIONS.md`.
2. Explain why the change is necessary.
3. Identify affected modules.
4. Update this document.
5. Update the architecture if required.
6. Update the development plan if required.
7. Update tests.
8. Continue implementation only after the change is documented.

---

# 28. Final Requirement Principle

The most important requirement of Q-SHIELD is:

> Build a scientifically defensible simulation that demonstrates how quantum-state preparation, teleportation, Pauli correction, projective measurement and statistical analysis can be combined with deterministic protocol rules to detect simulated digital-signature security threats.

The project should prioritize **correctness and defensibility over complexity or visual features**.
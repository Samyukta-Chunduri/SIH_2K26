# Q-SHIELD — System Architecture

## 1. Purpose

This document defines the software architecture of Q-SHIELD.

Q-SHIELD is designed as a modular simulation and security-analysis framework for a teleportation-based Quantum Digital Signature (QDS)-inspired model.

The architecture separates:

* Quantum computation
* QDS protocol logic
* Protocol security
* Statistical analysis
* Attack simulation
* Threat detection
* Evaluation
* User interface
* Persistence
* Blockchain audit

The core security engine must remain independent from the dashboard and optional blockchain layer.

---

# 2. Architectural Principles

The system SHALL follow these principles:

1. Modular design
2. Separation of concerns
3. Testability
4. Explainability
5. Reproducibility
6. Incremental development
7. Scientific transparency
8. Minimal coupling
9. No AI/ML
10. Quantum simulation before UI
11. Core security before blockchain
12. Explicit protocol assumptions

---

# 3. High-Level Architecture

The overall system is organized as follows:

```text id="2b0z5h"
                         USER
                           │
                           ▼
                  ┌─────────────────┐
                  │  APPLICATION /  │
                  │    DASHBOARD    │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ SECURITY REQUEST│
                  └────────┬────────┘
                           │
             ┌─────────────┴─────────────┐
             │                           │
             ▼                           ▼
    ┌─────────────────┐        ┌─────────────────┐
    │ PROTOCOL LAYER  │        │  QUANTUM LAYER  │
    └────────┬────────┘        └────────┬────────┘
             │                          │
             │                          ▼
             │                 State Preparation
             │                          │
             │                          ▼
             │                    Bell State
             │                          │
             │                          ▼
             │                    Teleportation
             │                          │
             │                          ▼
             │                  Pauli Correction
             │                          │
             │                          ▼
             │                     Measurement
             │                          │
             │                          ▼
             │                  Quantum Statistics
             │                          │
             └─────────────┬────────────┘
                           │
                           ▼
                 ┌─────────────────────┐
                 │ STATISTICAL ENGINE  │
                 └──────────┬──────────┘
                            │
                ┌───────────┼───────────┐
                │           │           │
                ▼           ▼           ▼
             Fidelity     QBER        X/Y/Z
                │           │        Statistics
                └───────────┼───────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │  HONEST BASELINE    │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │ THRESHOLD ENGINE    │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │  EVIDENCE FUSION    │
                 └──────────┬──────────┘
                            │
             ┌──────────────┼──────────────┐
             │              │              │
             ▼              ▼              ▼
          ACCEPT        SUSPICIOUS       ATTACK
                                           │
                  ┌────────────────────────┼──────────────────────┐
                  │                        │                      │
                  ▼                        ▼                      ▼
               Forgery                  Replay              Impersonation
                  │                        │                      │
                  └────────────────────────┼──────────────────────┘
                                           │
                                           ▼
                                  Channel Manipulation
                                           │
                                           ▼
                                   SECURITY REPORT
                                           │
                                           ▼
                                      PERSISTENCE
                                           │
                                           ▼
                              BLOCKCHAIN AUDIT (OPTIONAL)
```

---

# 4. Architectural Layers

Q-SHIELD consists of the following logical layers:

```text id="1h1l8k"
1. Presentation Layer
2. Application Layer
3. Security/Detection Layer
4. Statistical Layer
5. QDS Protocol Layer
6. Quantum Layer
7. Attack/Noise Layer
8. Evaluation Layer
9. Persistence Layer
10. Blockchain Audit Layer
```

The implementation does not need to create a separate Python package for every logical layer immediately.

The logical separation must exist even if some modules are initially combined.

---

# 5. Layer 1 — Presentation Layer

## Responsibility

The presentation layer provides the user interface.

The planned technology is:

```text id="f72r8m"
Streamlit
```

The UI must display information produced by the underlying engine.

It must not contain core quantum or security logic.

---

## Responsibilities

The presentation layer may:

* Accept user inputs
* Display quantum circuits
* Display measurement results
* Display statistics
* Display security decisions
* Display attack results
* Display graphs
* Display verification history
* Display performance metrics

---

## Must Not

The UI must not:

* Implement teleportation mathematics
* Implement security thresholds directly
* Duplicate attack logic
* Contain QDS protocol definitions
* Directly manipulate quantum state internals unnecessarily

The UI should call application/service functions instead.

---

# 6. Layer 2 — Application Layer

## Responsibility

The application layer coordinates the execution of a verification request.

It acts as the bridge between the UI and the underlying modules.

Example:

```text id="k74s3m"
User Request
     ↓
Application Service
     ↓
Protocol Validation
     ↓
Quantum Verification
     ↓
Statistics
     ↓
Detection
     ↓
Security Result
```

---

## Example Responsibilities

The application layer may:

* Create a verification request
* Validate request parameters
* Invoke the QDS verification process
* Invoke statistical analysis
* Invoke attack detection
* Combine results
* Produce a final verification report

---

# 7. Layer 3 — Security and Detection Layer

This is the core security layer.

Its responsibility is to determine whether a verification attempt is:

```text id="5f9lmy"
ACCEPT
SUSPICIOUS
ATTACK
```

---

## Components

The detection layer should eventually contain components for:

```text id="r4am5d"
Threshold Evaluation
Evidence Fusion
Decision Engine
Attack Classification
Security Report
```

---

## Important Rule

The detection layer must not use:

* Machine learning
* Neural networks
* AI classifiers
* Learned anomaly detection

It must use deterministic mathematical and statistical rules.

---

# 8. Layer 4 — Statistical Layer

The statistical layer transforms raw quantum measurements into useful security evidence.

---

## Inputs

Possible inputs:

```text id="j57xqz"
Measurement counts
Number of shots
Expected probabilities
Baseline statistics
Noise configuration
```

---

## Outputs

Possible outputs:

```text id="d1i8wo"
Empirical probabilities
Mean
Variance
Standard deviation
Confidence intervals
Fidelity
QBER
Distribution differences
Deviation scores
```

Only metrics that are scientifically justified should be implemented.

---

# 9. Layer 5 — QDS Protocol Layer

The QDS layer defines the simulated signature protocol.

It represents:

```text id="y6af6e"
Alice
Bob
Eve
Message
Signature
Quantum states
Verification procedure
Protocol metadata
```

---

## Important Constraint

The QDS protocol must be explicitly specified before its final implementation.

The initial `QDS_PROTOCOL.md` is intentionally a draft.

The AI coding agent must not invent unspecified QDS security mechanisms.

---

## Responsibilities

The QDS layer should eventually:

1. Represent a message.
2. Represent a signature.
3. Associate the signature with the signer.
4. Represent verification information.
5. Invoke quantum verification.
6. Return verification evidence.

---

# 10. Layer 6 — Quantum Layer

The quantum layer contains the fundamental quantum operations.

Planned location:

```text id="r8nqjh"
src/quantum/
```

Expected modules:

```text id="6c2nkj"
states.py
pauli.py
measurements.py
bell.py
teleportation.py
```

Additional modules may be added later if necessary.

---

# 11. Quantum State Module

Expected responsibility:

```text id="vq7ctw"
State preparation
```

Supported states should include:

```text id="7myxw4"
|0>
|1>
|+>
|->
|+i>
|-i>
```

The module should provide clean interfaces for preparing these states.

---

# 12. Pauli Module

Expected responsibility:

```text id="91k77j"
Pauli X
Pauli Y
Pauli Z
```

It should support:

* Applying operators
* Representing operators
* Testing eigenstates
* Supporting teleportation corrections
* Supporting channel attacks

---

# 13. Measurement Module

Expected responsibility:

* Measurement basis preparation
* Projective measurement
* Shot execution
* Measurement counts
* Probability conversion

Example:

```text id="8f9t5c"
Counts:
0 → 493
1 → 507

Probabilities:
P(0) = 0.493
P(1) = 0.507
```

---

# 14. Bell-State Module

Expected responsibility:

* Bell-state circuit construction
* Bell-state simulation
* Measurement
* Correlation verification

At least:

```text id="q0bqf6"
|Φ+> = (|00> + |11>) / √2
```

must be supported.

---

# 15. Teleportation Module

Expected responsibility:

```text id="m7kh4g"
Input state
     ↓
Bell pair
     ↓
Bell measurement
     ↓
Classical bits
     ↓
Pauli correction
     ↓
Output state
```

The implementation must be tested against multiple input states.

---

# 16. Layer 7 — Noise and Attack Layer

Planned locations:

```text id="d1w3h7"
src/noise/
src/attacks/
```

These are logically related but must remain conceptually distinct.

---

# 17. Noise Module

The noise module represents expected imperfections.

Possible models:

```text id="p1k6sb"
Bit-flip noise
Phase-flip noise
Depolarizing noise
Readout error
```

Additional noise models may be introduced if scientifically justified.

---

# 18. Attack Module

The attack module represents malicious actions.

Possible attacks:

```text id="5d1n8z"
Forgery
Replay
Impersonation
Unauthorized verification
Quantum-channel manipulation
```

---

## Attack Separation

Not every attack belongs to the quantum layer.

For example:

```text id="e5z9c0"
Replay
→ Protocol layer

Impersonation
→ Authentication/protocol layer

Unauthorized verification
→ Authorization/protocol layer

Quantum-channel manipulation
→ Quantum layer
```

Forgery may involve both protocol and quantum evidence.

---

# 19. Noise and Attack Interaction

The architecture must support experiments such as:

```text id="x2xv6f"
Honest + Low Noise
Honest + Medium Noise
Honest + High Noise

Attack + Low Noise
Attack + Medium Noise
Attack + High Noise
```

This allows the project to investigate whether the detector can distinguish expected noise from malicious deviations.

---

# 20. Layer 8 — Evaluation Layer

Planned location:

```text id="k6n2xx"
src/evaluation/
```

This layer evaluates system performance.

---

## Security Evaluation

It should calculate:

```text id="f5n5id"
FAR
FRR
Detection Rate
Legitimate Acceptance Rate
Empirical Forgery Probability
```

---

## Quantum Evaluation

It may calculate:

```text id="lqklcv"
Fidelity
QBER
Bell correlation
Measurement statistics
Statistical deviation
```

---

## Performance Evaluation

It should record:

```text id="t5z7uw"
Qubit count
Gate count
Circuit depth
Shots
Simulation time
Verification time
Statistical processing time
Total latency
Memory usage
```

---

# 21. Layer 9 — Persistence Layer

Persistence is optional during the early milestones.

If required, the initial implementation may use:

```text id="3f93f2"
SQLite
```

The database should store verification records rather than quantum internals unless required.

---

## Possible Verification Record

```text id="9ldg4q"
verification_id
timestamp
signer
verifier
message_hash
session_id
nonce
decision
attack_type
fidelity
qber
measurement_statistics
noise_configuration
```

The exact schema will be finalized when persistence is implemented.

---

# 22. Layer 10 — Blockchain Audit Layer

Blockchain is a late-stage optional component.

Planned conceptual flow:

```text id="2b0i1k"
Verification Result
        ↓
Audit Record
        ↓
Hash
        ↓
Blockchain Transaction
        ↓
Immutable/Tamper-Evident Audit Reference
```

---

## Important Boundary

Blockchain does not provide the information-theoretic security of QDS.

Its role is:

```text id="wq3w1v"
Auditability
+
Tamper-evident logging
```

The core Q-SHIELD detector must work without blockchain.

---

# 23. Data Flow

A normal verification request should conceptually follow:

```text id="k0f4jc"
User Input
    ↓
Verification Request
    ↓
Protocol Validation
    ↓
Message/Signature Validation
    ↓
Quantum State Preparation
    ↓
Bell Pair Generation
    ↓
Teleportation
    ↓
Pauli Correction
    ↓
Projective Measurement
    ↓
Measurement Counts
    ↓
Statistical Processing
    ↓
Baseline Comparison
    ↓
Threshold Evaluation
    ↓
Evidence Fusion
    ↓
Decision Engine
    ↓
Security Report
    ↓
History / Dashboard
```

---

# 24. Attack Data Flow

For a simulated attack:

```text id="y6h2g8"
Attack Configuration
        ↓
Attack Generator
        ↓
Modified Protocol / Quantum Input
        ↓
Quantum Verification
        ↓
Measurement
        ↓
Statistical Analysis
        ↓
Baseline Comparison
        ↓
Protocol Checks
        ↓
Evidence Fusion
        ↓
Attack Classification
        ↓
Security Decision
```

---

# 25. Evidence Model

The system should represent security evidence in a structured form.

Conceptually:

```text id="h3e8r1"
SecurityEvidence
│
├── Quantum Evidence
│   ├── Measurement Statistics
│   ├── Fidelity
│   ├── QBER
│   └── Bell Correlation
│
├── Protocol Evidence
│   ├── Identity
│   ├── Session
│   ├── Nonce
│   ├── Timestamp
│   └── Authorization
│
└── Statistical Evidence
    ├── Baseline
    ├── Threshold
    ├── Deviation
    └── Confidence Region
```

The exact data structures will be defined during implementation.

---

# 26. Decision Engine

The decision engine receives evidence and applies deterministic rules.

Conceptual interface:

```text id="r5xx3m"
Evidence
   ↓
Rule Evaluation
   ↓
Decision
```

Possible output:

```text id="7k3p1s"
Decision:
ACCEPT

or

Decision:
SUSPICIOUS

or

Decision:
ATTACK
```

The decision engine must also provide the reason/evidence for the decision.

---

# 27. Evidence Fusion

Evidence fusion combines independent evidence sources.

Example:

```text id="v2b8f1"
Quantum Evidence:
PASS

Protocol Evidence:
FAIL

Final:
ATTACK

Reason:
Replay detected through previously-used nonce.
```

Another example:

```text id="hj4m8s"
Quantum Evidence:
FAIL

Protocol Evidence:
PASS

Final:
ATTACK / SUSPICIOUS

Reason:
Quantum measurement statistics fall outside
the calibrated honest operating region.
```

The exact decision policy must be documented before final implementation.

---

# 28. Honest Baseline Architecture

The baseline subsystem should operate independently of attack experiments.

Conceptually:

```text id="4xq9ye"
Honest Configuration
        ↓
Repeated Executions
        ↓
Measurement Data
        ↓
Statistical Processing
        ↓
Baseline Model
        ↓
Stored Baseline
```

A baseline may be associated with configuration parameters such as:

```text id="6h1x0e"
Input state
Measurement basis
Noise model
Noise strength
Shots
```

The exact baseline key must be defined during implementation.

---

# 29. Verification Against Baseline

For a new verification:

```text id="z6d0vn"
Verification
     ↓
Generate Measurements
     ↓
Calculate Metrics
     ↓
Load Appropriate Baseline
     ↓
Calculate Deviation
     ↓
Evaluate Threshold
     ↓
Generate Evidence
```

This architecture supports noise-calibrated detection.

---

# 30. Module Dependency Direction

The preferred dependency direction is:

```text id="qf7d8v"
Presentation
     ↓
Application
     ↓
Detection / Evaluation
     ↓
Statistics
     ↓
QDS
     ↓
Quantum
     ↓
Qiskit / Aer
```

Noise and attack components may be invoked by the application/QDS/quantum verification workflow as appropriate.

Lower-level modules should not depend on the Streamlit UI.

---

# 31. Dependency Rules

## Rule 1

Quantum modules must not import Streamlit.

## Rule 2

Statistical modules must not depend on UI code.

## Rule 3

Attack generators must not directly manipulate dashboard widgets.

## Rule 4

The blockchain module must not be required by the detection engine.

## Rule 5

The core verification engine must work without a database.

## Rule 6

The dashboard must consume results rather than reproduce security calculations.

---

# 32. Proposed Repository Architecture

The eventual repository should resemble:

```text id="9u8m3c"
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
│   ├── quantum/
│   ├── qds/
│   └── experiments/
│
├── src/
│   ├── quantum/
│   │   ├── states.py
│   │   ├── pauli.py
│   │   ├── measurements.py
│   │   ├── bell.py
│   │   └── teleportation.py
│   │
│   ├── qds/
│   │
│   ├── noise/
│   │
│   ├── statistics/
│   │
│   ├── attacks/
│   │
│   ├── detection/
│   │
│   ├── evaluation/
│   │
│   └── utils/
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

This is the target architecture, not a requirement to create every directory immediately.

---

# 33. Incremental Creation Rule

The repository must be developed progressively.

### Early stage

Only documentation and environment setup are required.

### Quantum stage

Create:

```text id="e1y8cq"
src/quantum/
tests/quantum/
```

### Noise stage

Create:

```text id="t6v9xk"
src/noise/
tests/noise/
```

### Statistical stage

Create:

```text id="4e8n7v"
src/statistics/
tests/statistics/
```

### Security stage

Create:

```text id="h7c2pz"
src/attacks/
src/detection/
tests/attacks/
tests/detection/
```

### Evaluation stage

Create:

```text id="n6m2ry"
src/evaluation/
tests/evaluation/
```

### Dashboard stage

Create:

```text id="3y4g5k"
dashboard/
```

### Blockchain stage

Create blockchain-related code only after the core system is stable.

---

# 34. Interface-Based Design

Modules should communicate through clear interfaces.

For example:

```text id="8jv2qh"
Quantum Simulator
        ↓
Measurement Result
        ↓
Statistics Engine
        ↓
Verification Metrics
        ↓
Detection Engine
        ↓
Security Decision
```

The exact Python classes/functions will be decided during implementation.

The architecture intentionally does not prescribe unnecessary abstractions before they are needed.

---

# 35. Error Handling

Each layer should validate its inputs.

Examples:

### Quantum Layer

Reject:

* Invalid state dimensions
* Invalid quantum state definitions
* Invalid circuit parameters

### Protocol Layer

Reject:

* Missing signer
* Missing verifier
* Invalid session
* Missing nonce
* Invalid signature representation

### Statistics Layer

Reject:

* Zero shots where measurements are required
* Invalid counts
* Negative counts
* Inconsistent totals

### Detection Layer

Reject:

* Missing baseline
* Incompatible baseline configuration
* Undefined threshold

---

# 36. Reproducibility Architecture

Experiments should use configuration objects or structured parameters where appropriate.

A configuration may contain:

```text id="v6p2tk"
experiment_id
input_state
measurement_basis
shots
trials
noise_model
noise_strength
attack_type
attack_strength
threshold_configuration
random_seed
```

This allows experiments to be repeated consistently.

---

# 37. Configuration Management

Security-sensitive parameters must not be scattered throughout the source code.

Examples include:

```text id="0ykr5a"
Thresholds
Noise parameters
Shot counts
Experiment settings
Attack strengths
```

These should eventually be represented through centralized configuration structures or experiment configuration files.

Hard-coded magic numbers should be avoided.

---

# 38. Logging

The system should eventually maintain structured logs for:

* Verification requests
* Quantum execution
* Attack execution
* Statistical evaluation
* Final decisions
* Errors

Logging must not expose unnecessary sensitive information.

---

# 39. Testing Architecture

Testing follows the same modular architecture.

```text id="r1c2vy"
tests/
│
├── quantum/
├── qds/
├── noise/
├── statistics/
├── attacks/
├── detection/
└── evaluation/
```

Integration tests should additionally test the complete pipeline.

---

# 40. Security Boundaries

The system contains several security boundaries:

```text id="6t6d6v"
Input Validation
       ↓
Protocol Validation
       ↓
Quantum Verification
       ↓
Statistical Verification
       ↓
Detection
       ↓
Decision
```

A failure at any required security boundary should be represented in the final evidence.

---

# 41. Explainability Architecture

The final security result should contain:

```text id="o4j8iz"
Decision
Attack Type
Confidence / Statistical Context where applicable
Quantum Evidence
Protocol Evidence
Threshold Information
Reason
```

The word "confidence" must not be used as a vague AI-style confidence score.

If statistical confidence intervals or probabilities are shown, they must have a mathematically defined meaning.

---

# 42. Example End-to-End Legitimate Flow

```text id="p2c4sd"
Alice
  │
  ├── Creates message
  │
  ├── Creates valid signature representation
  │
  ▼
QDS Protocol
  │
  ▼
Quantum State Preparation
  │
  ▼
Bell-State Generation
  │
  ▼
Teleportation
  │
  ▼
Pauli Correction
  │
  ▼
Projective Measurement
  │
  ▼
Measurement Statistics
  │
  ▼
Baseline Comparison
  │
  ▼
Threshold Engine
  │
  ▼
ACCEPT
```

---

# 43. Example Forgery Flow

```text id="h5m2cn"
Eve
  │
  ├── Attempts forged signature
  │
  ▼
Protocol Verification
  │
  ▼
Quantum Verification
  │
  ▼
Measurement Statistics
  │
  ▼
Baseline Comparison
  │
  ▼
Threshold Evaluation
  │
  ▼
Evidence Fusion
  │
  ▼
ATTACK / SUSPICIOUS
```

The exact outcome depends on the experimental model and observed evidence.

---

# 44. Example Replay Flow

```text id="3v7k2q"
Eve
  │
  ├── Reuses previously valid request
  │
  ▼
Nonce / Session Check
  │
  ▼
Previously Seen
  │
  ▼
Replay Detected
  │
  ▼
ATTACK
```

Quantum verification may still produce legitimate-looking statistics.

This is expected because replay is primarily a protocol-layer threat.

---

# 45. Example Quantum Channel Attack

```text id="8x3n6c"
Alice
  │
  ▼
Quantum State
  │
  ▼
Quantum Channel
  │
  ├── Eve applies disturbance
  │
  ▼
Teleportation / Verification
  │
  ▼
Measurement
  │
  ▼
Changed Statistics
  │
  ▼
Fidelity / QBER / Correlation Analysis
  │
  ▼
Baseline Comparison
  │
  ▼
ATTACK / SUSPICIOUS
```

---

# 46. Architecture Evolution

The architecture may evolve during implementation.

Any structural change must be recorded in:

```text id="w5k7s1"
DECISIONS.md
```

Changes should include:

* What changed
* Why it changed
* Alternatives considered
* Impact on existing modules
* Updated architecture if necessary

---

# 47. What Must NOT Happen

The architecture must not evolve into:

```text id="v9h4yx"
One giant Python file
```

or:

```text id="m2z7ab"
Quantum code mixed with Streamlit widgets
```

or:

```text id="k8p1dw"
Blockchain required for verification
```

or:

```text id="6y2w9e"
Machine-learning classifier deciding attacks
```

or:

```text id="q7s4nm"
Hard-coded arbitrary security thresholds scattered throughout code
```

---

# 48. Architectural Priority

When there is a conflict between:

```text id="8v2b4n"
Feature complexity
```

and:

```text id="m5k9xd"
Scientific correctness
```

scientific correctness takes priority.

When there is a conflict between:

```text id="p7c1zx"
Visual features
```

and:

```text id="a4n6vk"
Core verification correctness
```

core verification takes priority.

When there is a conflict between:

```text id="z3r8qw"
Blockchain integration
```

and:

```text id="u6j2ns"
Quantum/security functionality
```

quantum/security functionality takes priority.

---

# 49. Final Architecture Principle

The architecture of Q-SHIELD is built around one central concept:

```text id="e8s3vp"
Quantum Protocol
      +
Quantum Measurements
      +
Statistical Analysis
      +
Protocol Security
      +
Deterministic Rules
      ↓
Explainable Threat Detection
```

The system must remain modular enough that each part can be independently tested, experimentally evaluated and scientifically explained.

The dashboard and blockchain are supporting layers.

The **quantum verification + statistical detection pipeline is the core of Q-SHIELD.**
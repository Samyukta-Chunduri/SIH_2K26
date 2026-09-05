# DECISIONS.md

# Q-SHIELD — Engineering & Scientific Decision Log

**Project:** Q-SHIELD — Quantum Signature Security & Threat Detection Framework
**Problem Statement:** SIH 26141 — Quantum-Inspired Cyber Threat Detection for Digital Signature Security
**Status:** ACTIVE
**Purpose:** Record important scientific, architectural, implementation, and experimental decisions made during development.

---

# 1. Purpose

This document records decisions that affect the correctness, security interpretation, architecture, reproducibility, and implementation of Q-SHIELD.

The purpose is to prevent undocumented assumptions.

Q-SHIELD must not evolve through:

```text
Developer/AI assumption
        ↓
Implementation
        ↓
Assumption becomes "fact"
```

Instead:

```text
Question
   ↓
Options
   ↓
Evidence / reasoning
   ↓
Decision
   ↓
Documentation
   ↓
Implementation
```

---

# 2. Decision Statuses

Every decision should have one of these statuses:

| Status       | Meaning                                |
| ------------ | -------------------------------------- |
| PROPOSED     | Suggested but not yet approved         |
| OPEN         | Requires a decision                    |
| ACCEPTED     | Decision approved for implementation   |
| REJECTED     | Option explicitly rejected             |
| SUPERSEDED   | Previously accepted decision replaced  |
| EXPERIMENTAL | Temporary decision for experimentation |

---

# 3. Decision Format

Every important decision should use:

```text
Decision ID:
Date:
Status:
Question:
Options:
Decision:
Reason:
Scientific impact:
Implementation impact:
Related documents:
```

---

# 4. Core Rules

The following are project-level decisions.

---

## DEC-001 — No AI/ML for Threat Detection

**Status:** ACCEPTED

### Question

Should Q-SHIELD use AI/ML to classify threats?

### Options

1. Use machine learning.
2. Use a hybrid ML/statistical approach.
3. Use deterministic statistical rules.

### Decision

Use **deterministic statistical and protocol-based rules only**.

### Reason

The SIH problem specifically requires statistical/threshold-based detection and does not permit AI/ML as the threat-detection mechanism.

### Implementation impact

The detection engine must use:

* quantum measurement statistics
* statistical deviation
* calibrated thresholds
* protocol checks
* deterministic evidence rules

No trained classifier may be introduced.

### Related documents

* `REQUIREMENTS.md`
* `SCIENTIFIC_RULES.md`
* `SECURITY_MODEL.md`

---

# 5. DEC-002 — Simulation Instead of Physical Quantum Hardware

**Status:** ACCEPTED

### Question

Should the project require a physical quantum computer?

### Decision

No.

Q-SHIELD will initially use quantum simulation.

### Reason

The SIH prototype must be practical to develop and demonstrate without requiring access to physical quantum hardware.

### Implementation

Use:

* Qiskit
* Qiskit Aer
* NumPy
* SciPy

where appropriate.

### Scientific boundary

Simulation results must not be presented as direct experimental results from physical quantum hardware.

---

# 6. DEC-003 — Qubit-Level Teleportation-Based QDS Abstraction

**Status:** ACCEPTED

### Question

Should Q-SHIELD reproduce a complete published physical QDS implementation?

### Options

1. Implement a complete physical QDS protocol.
2. Implement an exact continuous-variable teleportation-based QDS protocol.
3. Implement a qubit-level teleportation-based QDS abstraction suitable for simulation.

### Decision

Use a **qubit-level teleportation-based QDS abstraction**.

### Reason

The project requires Bell-state entanglement, teleportation, Pauli corrections, projective measurements, and statistical verification.

A full physical implementation would introduce unnecessary complexity for the prototype.

### Important limitation

The implementation must not claim to be an exact reproduction of every published teleportation-based QDS protocol.

### Related document

`QDS_PROTOCOL.md`

---

# 7. DEC-004 — Six Pauli Eigenstates

**Status:** ACCEPTED

### Decision

The initial quantum signature-state set will use:

```text
|0>
|1>
|+>
|->
|+i>
|-i>
```

These are eigenstates of the Pauli operators X, Y, and Z.

### Reason

The six states provide coverage across the three standard Pauli measurement bases and are directly relevant to the SIH requirements.

### Implementation impact

The quantum verification layer must support:

```text
Z basis
X basis
Y basis
```

---

# 8. DEC-005 — Message-to-State Mapping Must Be Explicit

**Status:** OPEN

### Question

How exactly should a classical message determine the quantum signature-state sequence?

### Possible options

### Option A — Deterministic demonstration mapping

Use a deterministic function that maps message data to the six-state set.

### Option B — Keyed state selection

Use a secret key to determine the state sequence.

### Option C — Protocol-specific state preparation

Use a more formal QDS state-generation mechanism.

### Current decision

**OPEN.**

The implementation must not silently choose one.

### Required action

Before implementing the final signature-generation mechanism, evaluate:

* security meaning
* reproducibility
* implementation complexity
* suitability for SIH
* relationship to the selected QDS abstraction

The selected approach must be recorded here.

---

# 9. DEC-006 — Bell State

**Status:** ACCEPTED

### Decision

Use:

$$
|\Phi^+\rangle =
\frac{|00\rangle+|11\rangle}{\sqrt{2}}
$$

as the primary Bell state for teleportation.

### Preparation

Use the standard:

```text
H
↓
CNOT
```

construction.

---

# 10. DEC-007 — Standard Quantum Teleportation

**Status:** ACCEPTED

### Decision

The project will implement standard three-qubit quantum teleportation:

```text
Input qubit
      +
Bell pair
      ↓
Bell measurement
      ↓
Classical measurement results
      ↓
Pauli correction
      ↓
Recovered state
```

### Validation

Teleportation must first be validated using ideal simulation before noise and attack experiments.

---

# 11. DEC-008 — Pauli Correction

**Status:** ACCEPTED

The implementation must explicitly account for the teleportation correction operations.

Conceptually:

| Classical result | Correction |
| ---------------- | ---------- |
| 00               | I          |
| 01               | X          |
| 10               | Z          |
| 11               | XZ         |

### Critical implementation note

The conceptual table must not be copied blindly into code.

Qiskit classical-bit ordering must be explicitly tested.

A dedicated test must verify every correction branch.

---

# 12. DEC-009 — Projective Measurement

**Status:** ACCEPTED

### Decision

Verification will use projective measurements in the X, Y, and Z bases.

### Reason

Projective measurement produces the measurement-outcome statistics required for deterministic statistical analysis.

### Related document

`MATHEMATICAL_MODEL.md`

---

# 13. DEC-010 — Noise Must Be Calibrated

**Status:** ACCEPTED

### Decision

Noise must not automatically be classified as malicious behaviour.

The system must first establish honest noisy behaviour.

### Principle

```text
Honest noise
     ↓
Baseline
     ↓
Expected operating region
     ↓
Observed deviation
     ↓
Detection
```

### Reason

A noisy quantum channel is not necessarily under attack.

---

# 14. DEC-011 — Honest Baseline and Attack Data Must Be Separate

**Status:** ACCEPTED

### Decision

Attack results must not be used to construct the honest baseline.

### Required workflow

```text
Honest calibration data
        ↓
Baseline
        ↓
Threshold
        ↓
Freeze
        ↓
Attack evaluation
```

### Reason

Otherwise the detector could be unintentionally calibrated to tolerate the very attacks it is supposed to detect.

---

# 15. DEC-012 — Thresholds Must Not Be Arbitrary

**Status:** ACCEPTED

### Decision

The project must not use unexplained hard-coded security thresholds.

For example:

```python
if qber > 0.05:
    attack = True
```

is not acceptable unless the value has a documented justification.

### Preferred approach

```text
Honest observations
        ↓
Statistical analysis
        ↓
Threshold-selection procedure
        ↓
Independent validation
        ↓
Frozen threshold
```

---

# 16. DEC-013 — Deterministic Final Decision

**Status:** ACCEPTED

### Decision

The final security decision must be deterministic once all evidence and configuration are fixed.

Possible outputs:

```text
ACCEPT
SUSPICIOUS
ATTACK
```

### Important clarification

Quantum measurements themselves are probabilistic.

The deterministic property applies to the decision procedure **after measurement data has been collected**.

---

# 17. DEC-014 — Three-Level Security Decision

**Status:** ACCEPTED

### Decision

Use:

```text
ACCEPT
SUSPICIOUS
ATTACK
```

rather than only:

```text
VALID
INVALID
```

### Reason

Some anomalous behaviour may not provide enough evidence to confidently attribute a specific attack.

The intermediate state prevents forced binary classification.

---

# 18. DEC-015 — Protocol Attacks Are Separate From Quantum Attacks

**Status:** ACCEPTED

The following are primarily protocol/security-layer attacks:

* replay
* impersonation
* unauthorized verification

The following are quantum-layer attacks:

* bit flip
* phase flip
* Y-type manipulation
* depolarizing disturbance
* other explicitly modelled quantum-channel manipulation

### Reason

Different attacks require different evidence.

The system must not falsely claim that quantum measurement statistics alone detect identity or authorization violations.

---

# 19. DEC-016 — Replay Detection Requires State

**Status:** ACCEPTED

### Decision

Replay detection will use protocol information and verification history.

Relevant information may include:

```text
session ID
nonce
timestamp
message identifier
signature identifier
verification status
```

### Reason

Replay is fundamentally a protocol-level problem.

Quantum measurements alone are insufficient to establish that a previously valid request is being replayed.

---

# 20. DEC-017 — Impersonation Detection Uses Identity Evidence

**Status:** ACCEPTED

Identity-related evidence must be checked independently.

Possible evidence:

```text
claimed signer
known signer
authorization
signature association
session
quantum evidence
```

A quantum anomaly must not be required for an impersonation attempt to be rejected.

---

# 21. DEC-018 — Unauthorized Verification Is an Authorization Failure

**Status:** ACCEPTED

### Decision

Unauthorized verification attempts must be rejected through protocol/application authorization checks.

### Reason

Authorization is not inherently a quantum property.

---

# 22. DEC-019 — Evidence Fusion

**Status:** ACCEPTED

The final detector may combine:

```text
Protocol evidence
+
Signature evidence
+
Quantum evidence
+
Statistical evidence
```

### Decision principle

Evidence fusion must use explicit deterministic rules.

It must not use:

* neural networks
* learned weights
* hidden scoring models
* unexplained probability scores

---

# 23. DEC-020 — Quantum Integrity Fingerprint

**Status:** ACCEPTED AS A DESIGN CONCEPT

### Decision

Q-SHIELD will explore a composite set of measurable quantum features called:

> **Quantum Integrity Fingerprint (QIF)**

Possible components:

```text
QBER
fidelity
Pauli expectation values
measurement probabilities
Bell correlations
distribution deviation
```

### Important limitation

QIF is an engineering representation of measured evidence.

It is **not** a universal cryptographic security quantity.

The project must not invent a single arbitrary "quantum security score" and present it as a formally defined security metric.

---

# 24. DEC-021 — No Universal Security Score

**Status:** ACCEPTED

### Decision

Do not create an unexplained number such as:

```text
Quantum Security Score = 94.7
```

unless its mathematical meaning and validation are rigorously defined.

### Reason

A visually attractive score can create a false impression of cryptographic validity.

The dashboard should instead display interpretable metrics:

```text
Fidelity
QBER
Bell correlation
Threshold deviation
Protocol status
Detection evidence
```

---

# 25. DEC-022 — Empirical Forgery Probability

**Status:** ACCEPTED

### Decision

The project will calculate empirical forgery success probability from repeated simulated attacks.

$$
\hat P_{forge}
=
\frac{\text{successful accepted forgeries}}
{\text{total forgery attempts}}
$$

### Important distinction

This is an experimental estimate.

It must not automatically be described as a formal QDS security bound.

---

# 26. DEC-023 — Information-Theoretic Security Boundary

**Status:** ACCEPTED

### Decision

Q-SHIELD will preserve the distinction between:

```text
QDS protocol security assumptions
```

and:

```text
Q-SHIELD software detection performance
```

The detector itself does not create information-theoretic security merely because it uses quantum simulation.

### Allowed statement

> Q-SHIELD evaluates security-relevant behaviour within a simulated teleportation-based QDS framework.

### Forbidden overclaim

> Q-SHIELD mathematically guarantees information-theoretic security for all attacks.

---

# 27. DEC-024 — Statistical Metrics

**Status:** ACCEPTED

The system may use:

* empirical probabilities
* QBER
* fidelity
* expectation values
* Bell correlations
* total variation distance
* mean
* variance
* standard error
* confidence intervals
* empirical quantiles

The final set will be determined during implementation and experimentation.

---

# 28. DEC-025 — False Acceptance and False Rejection

**Status:** ACCEPTED

The evaluation must distinguish:

$$
FAR =
\frac{\text{malicious accepted}}
{\text{malicious attempts}}
$$

from:

$$
FRR =
\frac{\text{legitimate rejected}}
{\text{legitimate attempts}}
$$

Also report:

$$
LAR =
\frac{\text{legitimate accepted}}
{\text{legitimate attempts}}
$$

and:

$$
ADR =
\frac{\text{malicious detected}}
{\text{malicious attempts}}
$$

---

# 29. DEC-026 — Security Operating Region

**Status:** ACCEPTED

### Decision

The system will evaluate security performance across combinations of:

```text
noise
attack strength
shot count
```

### Purpose

Instead of claiming universal robustness, Q-SHIELD should identify the tested region where its detector performs reliably.

---

# 30. DEC-027 — Reproducibility

**Status:** ACCEPTED

Experiments must record relevant configuration metadata.

At minimum:

```text
experiment ID
software version
quantum library versions
noise model
noise parameters
attack type
attack strength
shot count
state configuration
random seed
baseline version
threshold version
```

---

# 31. DEC-028 — Numerical Tolerance vs Security Threshold

**Status:** ACCEPTED

The project must distinguish:

### Numerical tolerance

Used for floating-point calculations.

Example:

```text
|a-b| < ε
```

### Security threshold

Used to determine whether observed behaviour is outside an accepted operating region.

These are fundamentally different concepts.

A floating-point tolerance must never silently become a security threshold.

---

# 32. DEC-029 — Ideal Simulation Comes First

**Status:** ACCEPTED

Development order:

```text
Ideal quantum circuit
        ↓
Correctness tests
        ↓
Noise
        ↓
Baseline
        ↓
Attacks
        ↓
Detection
```

No attack detector should be trusted before the underlying teleportation implementation is validated.

---

# 33. DEC-030 — Six-State Full Validation

**Status:** ACCEPTED

All core teleportation and measurement functionality should eventually be validated for:

```text
|0>
|1>
|+>
|->
|+i>
|-i>
```

This prevents the implementation from accidentally working only for computational-basis states.

---

# 34. DEC-031 — Blockchain Is Not Core Quantum Security

**Status:** ACCEPTED

Blockchain will be treated as a later audit/integrity layer.

It may eventually store:

```text
verification hash
decision
timestamp
experiment ID
configuration hash
audit information
```

### It must not be presented as:

* the mechanism providing QDS security
* a replacement for quantum verification
* proof of information-theoretic security

---

# 35. DEC-032 — Blockchain Implementation Is Deferred

**Status:** ACCEPTED

Blockchain will be implemented only after the following are working:

```text
quantum protocol
verification
baseline
threshold engine
attack detection
evaluation
dashboard
```

### Reason

Blockchain should not consume development time before the core SIH requirement is demonstrated.

---

# 36. DEC-033 — SQLite Before Blockchain

**Status:** ACCEPTED

If persistent local storage is required before blockchain integration, use SQLite.

### Reason

SQLite provides a simple local persistence layer for:

* verification history
* experiment results
* attack records
* configuration versions

Blockchain can be added later without making it a dependency of the core detector.

---

# 37. DEC-034 — Streamlit for Initial Dashboard

**Status:** ACCEPTED

The initial user interface will use Streamlit.

### Reason

It allows rapid development of:

* experiment controls
* charts
* quantum circuit display
* measurement results
* security decisions
* attack laboratory
* analytics

A separate frontend/backend architecture can be introduced later if required.

---

# 38. DEC-035 — FastAPI Is Optional

**Status:** PROPOSED

FastAPI may be introduced if the project later requires:

* REST APIs
* frontend/backend separation
* external integrations
* multiple clients

It is not required for the initial prototype.

---

# 39. DEC-036 — Development Is Module-by-Module

**Status:** ACCEPTED

Implementation must follow divide-and-conquer.

Preferred workflow:

```text
Understand module
      ↓
Design module
      ↓
Implement module
      ↓
Write tests
      ↓
Run experiments
      ↓
Validate
      ↓
Document
      ↓
Proceed
```

Do not generate the entire application in one step.

---

# 40. DEC-037 — AI Coding Agent Must Follow Project Documents

**Status:** ACCEPTED

Antigravity or another coding agent must treat:

```text
SCIENTIFIC_RULES.md
REQUIREMENTS.md
ARCHITECTURE.md
QDS_PROTOCOL.md
MATHEMATICAL_MODEL.md
SECURITY_MODEL.md
TESTING_STRATEGY.md
EXPERIMENT_PLAN.md
DECISIONS.md
```

as project constraints.

If an implementation conflicts with these documents, the agent must stop and request a decision rather than silently changing the specification.

---

# 41. DEC-038 — Critical Scientific STOP Rule

**Status:** ACCEPTED

The coding agent must stop implementation when a decision affects:

* QDS protocol semantics
* security assumptions
* message-to-state mapping
* signature construction
* teleportation correction semantics
* security thresholds
* information-theoretic security claims
* attack definitions
* interpretation of experimental results

The agent may continue automatically for ordinary implementation details that do not alter scientific meaning.

---

# 42. DEC-039 — Experimental Thresholds Are Frozen

**Status:** ACCEPTED

Once a threshold configuration has been calibrated and independently validated for a specific experiment, it must be frozen before attack evaluation.

Changing it after seeing attack results creates a risk of experimental bias.

Any change must produce:

```text
new threshold version
new calibration
new validation
new experiment run
```

---

# 43. DEC-040 — Security Decisions Must Be Explainable

**Status:** ACCEPTED

Every non-ACCEPT decision should provide evidence.

Example:

```text
Decision:
ATTACK

Reason:
QBER exceeded calibrated upper operating boundary.

Supporting evidence:
QBER = ...
Baseline upper bound = ...
Fidelity = ...
Identity = valid
Nonce = valid
Attack model = phase-flip
```

The exact evidence format will be finalized during implementation.

---

# 44. DEC-041 — Unknown Anomalies Must Remain Unknown

**Status:** ACCEPTED

If an execution violates a security threshold but does not match a known attack rule, the detector should prefer:

```text
SUSPICIOUS
```

rather than inventing an attack type.

### Reason

Unknown behaviour should not be falsely attributed.

---

# 45. DEC-042 — Legitimate Acceptance Must Be Deterministic

**Status:** ACCEPTED

Under a fixed configuration and within the calibrated honest operating region, the verification decision should be deterministic after measurement data is collected.

This does not mean quantum measurements themselves become deterministic.

---

# 46. DEC-043 — Test Before Optimization

**Status:** ACCEPTED

Performance optimization must occur only after correctness and security regression tests exist.

Preferred order:

```text
Correct
   ↓
Tested
   ↓
Measured
   ↓
Optimized
   ↓
Retested
```

---

# 47. DEC-044 — Security Claims Require Experimental Evidence

**Status:** ACCEPTED

Any project claim about detection performance must be supported by measured results.

For example:

```text
Claim:
"Channel attacks are detected."

Required:
Attack experiments
+
Detection rate
+
False acceptance analysis
```

---

# 48. DEC-045 — No Hidden Assumptions

**Status:** ACCEPTED

If implementation requires a choice that is not specified in project documents, the developer/AI agent must:

1. identify the missing decision
2. list reasonable alternatives
3. explain consequences
4. request approval
5. record the final decision

---

# 49. Open Decisions

The following decisions remain open and must be resolved before final implementation.

| ID       | Decision                                      |
| -------- | --------------------------------------------- |
| OPEN-001 | Exact message-to-quantum-state mapping        |
| OPEN-002 | Exact signature-record structure              |
| OPEN-003 | Exact baseline estimation procedure           |
| OPEN-004 | Exact threshold-selection procedure           |
| OPEN-005 | Exact evidence-fusion rules                   |
| OPEN-006 | Exact quantum-channel attack parameterization |
| OPEN-007 | Final persistence schema                      |
| OPEN-008 | Optional blockchain architecture              |
| OPEN-009 | Final dashboard implementation details        |

---

# 50. Decision History

Use this section to record changes.

Example:

```text
Date:
Decision:
Previous value:
New value:
Reason:
Impact:
```

Never silently overwrite an important scientific decision.

---

# 51. Decision Change Rule

If an accepted decision changes:

```text
Old decision
      ↓
Reason for change
      ↓
New decision
      ↓
Impact analysis
      ↓
Affected files
      ↓
Tests requiring updates
      ↓
Experiments requiring rerun
```

A protocol change may invalidate previous experimental results.

---

# 52. Implementation Rule

The codebase must reflect the latest accepted decisions.

If documentation and implementation disagree:

```text
STOP
↓
Identify disagreement
↓
Determine intended decision
↓
Update documentation
↓
Update implementation
↓
Run affected tests
```

Do not silently choose whichever version is easier to implement.

---

---

# 54. DEC-054 — Single-Qubit Noise Channels, Density Matrix Representation, and Depolarizing Parameter Convention

**Status:** ACCEPTED (Milestone M8)

### Decision

1. **State Representation Under Noise:**
   A noisy quantum channel transforms pure states into mixed states. Therefore, channel noise outputs are represented as Hermitian, unit-trace, positive semidefinite $2\times 2$ density matrices $\rho$:
   $$\rho = \rho^\dagger, \quad \operatorname{Tr}(\rho) = 1, \quad \rho \succeq 0$$
   Pure state to density matrix mapping requires complex conjugation: $\rho = |\psi\rangle\langle\psi| = \text{np.outer}(\psi, \psi^*)$.

2. **Kraus Representation:**
   Single-qubit CPTP channels are represented via Kraus operators satisfying completeness:
   $$\rho' = \sum_i K_i \rho K_i^\dagger, \quad \sum_i K_i^\dagger K_i = I$$

3. **Noise Channel Models:**
   - **Bit-flip:** $\rho' = (1-p)\rho + p X \rho X$, $K_0 = \sqrt{1-p}I, K_1 = \sqrt{p}X$
   - **Phase-flip:** $\rho' = (1-p)\rho + p Z \rho Z$, $K_0 = \sqrt{1-p}I, K_1 = \sqrt{p}Z$
   - **Depolarizing Channel Convention:** Q-SHIELD adopts the standard Pauli error convention:
     $$\rho' = (1-p)\rho + \frac{p}{3}(X\rho X + Y\rho Y + Z\rho Z)$$
     with Kraus operators $K_0 = \sqrt{1-p}I, K_{1,2,3} = \sqrt{p/3}\{X, Y, Z\}$.
   - **Qiskit Aer Depolarizing Mapping:** Qiskit Aer's `depolarizing_error(p_{\text{aer}}, 1)` implements $\rho' = (1-p_{\text{aer}})\rho + p_{\text{aer}}(I/2)$. Since $I/2 = \frac{1}{4}(\rho + X\rho X + Y\rho Y + Z\rho Z)$, the exact parameter equivalence mapping is $p_{\text{aer}} = \frac{4}{3}p$.

4. **Zero-Noise Identity Limit:**
   At $p = 0$, every channel reduces identically to the identity channel: $\mathcal{E}(p=0)(\rho) = \rho$.

5. **Physical Distinction:**
   Noise channels represent honest physical imperfections. NOISE $\neq$ ATTACK. M8 outputs physical metrics (fidelity, Born measurement distributions) without making security decisions or classifying attacks.

---

# 55. DEC-055 — Honest Baseline Calibration, Sample Variance Convention, and Metric Aggregation

**Status:** ACCEPTED (Milestone M9)

### Decision

1. **Purpose of Honest Baseline:**
   An honest baseline characterizes the statistical distribution of quantum verification metrics under explicitly defined legitimate operating conditions. It is NOT an attack detector, contains no security decision thresholds, and does not label executions as attacks.
   $$\text{Honest Configuration} \implies \text{Repeated Honest Trials} \implies \text{Metric Statistics} \implies \text{Honest Baseline}$$

2. **Unbiased Sample Variance (Bessel's Correction):**
   In accordance with statistical estimation for sampled observational data, the sample variance uses denominator $N - 1$:
   $$s^2 = \frac{1}{N - 1} \sum_{i=1}^N (x_i - \mu)^2 \quad (N \ge 2)$$
   For $N = 1$, sample variance is defined as $0.0$, and $N = 0$ is rejected with `ValueError`.

3. **Metric Coverage:**
   Baselines record distributions for:
   - State overlap fidelity $F \in [0.0, 1.0]$
   - Quantum bit error rate $\text{QBER} \in [0.0, 1.0]$
   - Born measurement probabilities across $Z, X, Y$ bases
   - Pauli expectation values $\langle X \rangle, \langle Y \rangle, \langle Z \rangle \in [-1.0, 1.0]$
   - Bell correlation expectations $E_{XX}, E_{YY}, E_{ZZ} \in [-1.0, 1.0]$

4. **Strict Configuration Conditioning & Canonical Fingerprinting:**
   Baselines are strictly conditioned on their configuration (noise model, noise strength $p$, shot count, evaluated states, backend, calibration run count). Different configurations produce distinct, isolated baselines. `BaselineConfiguration.canonical_hash` computes a deterministic SHA-256 digest over all operating parameters to guarantee that incompatible configurations cannot share identity. They are never merged into a single multi-condition baseline.

5. **Contamination Prevention & Provenance Validation:**
   The calibration pipeline accepts only legitimate honest quantum executions. `CalibrationObservation` includes an explicit `is_honest: bool = True` invariant and defensive copying to protect against external mutation. `build_honest_baseline_from_observations` strictly rejects any observation marked with `is_honest=False`.

6. **Small Sample Confidence Interval Convention:**
   For $N \ge 2$, confidence intervals are calculated using Student's $t$ critical values ($df = N - 1$) and clamped to physical metric domains ($[0, 1]$ or $[-1, 1]$). For $N = 1$, degrees of freedom is $0$, and `confidence_interval` is explicitly set to `None` to prevent unscientific pseudo-intervals.

---

# 56. Final Decision Principle

Q-SHIELD follows:

```text
QUESTION
   ↓
OPTIONS
   ↓
SCIENTIFIC REASONING
   ↓
DECISION
   ↓
DOCUMENTATION
   ↓
IMPLEMENTATION
   ↓
TEST
   ↓
EXPERIMENT
   ↓
VALIDATION
```

The purpose of this file is simple:

> **No scientifically meaningful behaviour should enter Q-SHIELD by accident.**

Every major assumption must be visible, reviewable, testable, and changeable.

**Status:** ACTIVE



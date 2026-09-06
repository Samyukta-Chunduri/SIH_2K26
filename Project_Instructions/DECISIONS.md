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

# 56. DEC-056 — Statistical Comparison Engine Architecture, Non-Normality of Bounded Metrics, Descriptive Z-Scores vs Decision Thresholds, Safe Relative Deviations, Total Variation Distance, and Strict Separation from Decision Engine

**Status:** ACCEPTED (Milestone M10)

### Decision

1. **Purpose and Boundaries of Statistical Comparison Layer:**
   Milestone M10 implements a purely descriptive statistical comparison engine. It quantifies the degree of divergence between newly observed quantum verification metrics and a compatible M9 honest baseline.
   $$\text{Observation} + \text{Honest Baseline} \implies \text{Statistical Comparison} \implies \text{Statistical Evidence}$$
   - M10 produces **statistical evidence only**.
   - M10 contains **strictly no attack detection, no security decision thresholds, no threat classification, and no ACCEPT/SUSPICIOUS/ATTACK logic** (strictly reserved for M11 and M12).
   - M10 contains **no AI/ML, neural networks, anomaly classifiers, or composite "security scores"**.

2. **Absolute and Signed Deviations:**
   For scalar metrics $x$ against baseline mean $\mu$:
   - Absolute deviation: $d = |x - \mu| \ge 0$
   - Signed deviation: $\delta = x - \mu$

3. **Safe Relative Deviation Policy:**
   Relative deviation is defined as $d_{\text{rel}} = \frac{|x - \mu|}{|\mu|}$ for $|\mu| \ge 10^{-12}$.
   When $|\mu| < 10^{-12}$ (e.g., zero error rate under ideal teleportation), division by zero is avoided by explicitly returning `None` instead of producing `NaN` or `Inf`.

4. **Baseline Uncertainty and Standard Error:**
   The baseline mean $\mu$ is an empirical sample estimate with sampling uncertainty. For $N \ge 2$, the standard error of the mean is:
   $$\text{SE} = \frac{s}{\sqrt{N}}$$
   For $N = 1$, standard error is undefined and returns `None`.

5. **Descriptive Standardized Deviation ($z$-score) vs. Bounded Non-Gaussian Metrics:**
   Standardized deviation is computed as $z = \frac{x - \mu}{s}$ for $s > 10^{-12}$ and $N \ge 2$.
   - **Non-Normality Notice:** Quantum verification metrics (state fidelity $F \in [0, 1]$, error rates $\text{QBER} \in [0, 1]$, Born probabilities $P \in [0, 1]$, and Pauli expectations $\langle P \rangle \in [-1, 1]$) are strictly bounded. Under finite calibration samples ($N \sim 5$ to $100$) or near boundary saturation (e.g. ideal fidelity near $1.0$), empirical distributions are truncated and non-Gaussian.
   - **Descriptive Scale Only:** $z$ is exposed solely as a descriptive scale (number of sample standard deviations from the sample mean). It is **never** used as a hardcoded anomaly or attack threshold (e.g. $|z| > 3$).

6. **Confidence Interval Containment:**
   Evaluates whether the observed point $x$ lies within the baseline Student's $t$ confidence interval $[\text{CI}_{\text{low}}, \text{CI}_{\text{high}}]$. Results are categorized as:
   - `'inside'`: $\text{CI}_{\text{low}} < x < \text{CI}_{\text{high}}$
   - `'outside'`: $x < \text{CI}_{\text{low}} - \text{atol}$ or $x > \text{CI}_{\text{high}} + \text{atol}$
   - `'boundary'`: within numerical tolerance $\text{atol} = 10^{-9}$ of an interval boundary
   - `'unavailable'`: when $N=1$ and baseline CI is `None`.

7. **Discrete Total Variation Distance for Probability Distributions:**
   Born probability distribution divergence across measurement bases ($Z, X, Y$) is evaluated via Total Variation (TV) distance:
   $$\text{TV}(P, Q) = \frac{1}{2} \sum_{i \in \Omega} |P(i) - Q(i)| \in [0.0, 1.0]$$
   Distributions must be normalized ($\sum P_i = 1.0 \pm 10^{-4}$ with $P_i \in [0, 1]$). Missing outcomes in either distribution are explicitly treated as probability $0.0$.

8. **Strict Configuration Compatibility & Isolation:**
   Observations must match the calibrated operating environment of the baseline (state set, noise model, noise strength, channel location, shot count, backend, and canonical hash). Any attempt to evaluate an observation against an incompatible baseline raises a `ConfigurationCompatibilityError`.

9. **Baseline Immutability & Contamination Prevention:**
   The honest baseline is an immutable reference model. Evaluation observations are held in `VerificationObservation` containers separate from `CalibrationObservation`. Comparison functions never mutate the baseline, update baseline statistics, or append evaluation data to calibration sets.

---

# 57. DEC-057 — Strict Baseline Distribution Validation & Non-Repair Policy (Bug L Elimination)

**Status:** ACCEPTED

### Decision

The M10 statistical comparison engine shall strictly validate all candidate probability distributions before comparison and **shall NEVER perform silent normalization** (such as dividing by `sum(probabilities)`).

1. If a baseline probability distribution for any basis does not sum to $1.0$ within the configured numerical tolerance (`prob_atol = 1e-4`), the engine immediately raises a `ValueError`.
2. Silent re-normalization is strictly prohibited because repairing corrupted baseline distributions conceals calibration defects, invalidates statistical error bounds, and creates false confidence in uncalibrated outcomes.
3. Outcome keys must be strictly validated as strings, and probability values must be finite floats within $[0.0, 1.0]$.
4. Configuration compatibility checks must evaluate both observation configuration dictionaries and direct `observation.shots` values against baseline operating parameters.

# 58. DEC-058 — Statistical Threshold Policy Architecture, Empirical Quantile Calibration, Configuration Binding, Exact Boundary Conventions, and Strict Scope Isolation (Milestone M11)

**Status:** ACCEPTED (Milestone M11)

### Decision

1. **Purpose and Boundaries of the Threshold Policy Layer:**
   Milestone M11 establishes the statistical threshold policy layer that consumes M9 honest baselines and M10 statistical evidence to determine whether newly observed metrics cross calibrated operational boundaries.
   $$\text{M9 Honest Baseline} + \text{Honest Observations} \implies \text{M11 Threshold Policy} \implies \text{Threshold Evidence}$$
   - M11 produces **calibrated threshold evidence only** (`exceeded = True/False`, `margin`, `boundary_status`).
   - M11 contains **strictly NO final security verdicts** (`ACCEPT`, `SUSPICIOUS`, `ATTACK`) — strictly reserved for M12.
   - M11 contains **strictly NO attack detection, forgery detection, replay detection, impersonation detection, or classification**.
   - M11 contains **strictly NO AI/ML, neural networks, or composite "security scores"**.

2. **Raw Metric vs. Deviation Metric Semantics (Comprehensive Calibration Table):**
   The threshold policy strictly differentiates metrics evaluated on raw values from signed/symmetric metrics evaluated on baseline deviations:

   | Metric Name | Thresholded Quantity | Threshold Direction | Scientific Rationale |
   | :--- | :--- | :--- | :--- |
   | **Fidelity** (`fidelity:{state}`) | Raw observed value $F \in [0, 1]$ | **LOWER** ($T = Q_\alpha$) | Honest behavior is high ($F \approx 1.0$); physical degradation drops fidelity below $T$. |
   | **QBER** (`qber:{state}`) | Raw observed error rate $\in [0, 1]$ | **UPPER** ($T = Q_{1-\alpha}$) | Honest error is low ($\approx 0.0$); channel disruption or noise increases QBER above $T$. |
   | **TV Distance** (`probabilities_{basis}:{state}`) | Distributional deviation $TV(P_{\text{obs}}, P_{\text{base}})$ | **UPPER** ($T = Q_{1-\alpha}$) | Total variation distance is non-negative ($0 \le TV \le 1$); larger values indicate greater distributional shift. |
   | **Pauli Expectations** (`pauli_{op}:{state}`) | Absolute deviation $|\langle \sigma \rangle - \mu_{\text{base}}|$ | **UPPER** ($T = Q_{1-\alpha}$) | Signed in $[-1, +1]$ ($+1$ for $\|0\rangle$, $-1$ for $\|1\rangle$). Raw directional thresholding fails; absolute deviation $|x - \mu|$ detects shifts in either direction. |
   | **Bell Correlations** (`bell_{xx,yy,zz}`) | Absolute deviation $\|\langle O \rangle - \mu_{\text{base}}\|$ | **UPPER** ($T = Q_{1-\alpha}$) | Theoretical correlations can be $+1.0$ or $-1.0$ across Bell states ($\Phi^+, \Phi^-, \Psi^+, \Psi^-$). Deviation $\|\langle O \rangle - \mu\|$ detects decoherence towards 0 symmetrically. |
   | **Individual Probabilities** (`prob_dev_{basis}_{outcome}:{state}`) | Absolute deviation $\|p - \mu_p\|$ | **UPPER** ($T = Q_{1-\alpha}$) | Expected honest probabilities can be $0.5, 1.0, 0.0$. Anomaly is an absolute shift $\|p - \mu_p\|$ exceeding calibrated upper tolerance. |
   | **Generic Absolute Deviation** (`{metric}:abs_dev`) | M10 absolute deviation $\|x - \mu\|$ | **UPPER** ($T = Q_{1-\alpha}$) | Evaluates M10 absolute deviation directly without applying a second baseline subtraction ($d \le T$). |

3. **Empirical Quantile Calibration (Primary Method for Bounded Quantum Metrics):**
   Because quantum verification metrics (overlap fidelity $F \in [0, 1]$, QBER $\in [0, 1]$, total variation distance $TVD \in [0, 1]$, and expectation deviations) are non-Gaussian and strictly bounded, non-parametric empirical quantiles from honest calibration observations provide the most robust operational boundaries:
   - For **LOWER**-tail metrics (e.g. Fidelity): $T = Q_{\alpha}(\{x_1, \dots, x_N\})$, where observed $x < T$ indicates degradation.
   - For **UPPER**-tail metrics (e.g. QBER, TVD, absolute deviations): $T = Q_{1 - \alpha}(\{x_1, \dots, x_N\})$, where observed $x > T$ indicates degradation.
   - Linear interpolation: NumPy `method='linear'` is the standard, deterministic quantile convention.

4. **Parametric Statistical Multiplier ($\mu \pm k\sigma$) & Clamping Transparency:**
   For approximately continuous metrics where baseline sample variance is available:
   - LOWER threshold: $T = \max(0.0, \mu - k\sigma)$ (for metrics with physical bound at 0.0)
   - UPPER threshold: $T = \min(1.0, \mu + k\sigma)$ (for metrics with physical bound at 1.0)
   - Note: If clamping occurs at $1.0$ for an upper threshold, strict exceedance ($x > 1.0 + \text{atol}$) becomes uncrossable for bounded metrics. Empirical quantiles are therefore preferred over parametric multipliers for bounded quantum metrics.

5. **Small-Sample Policy & Statistical Reliability Distinction:**
   - $N = 0$: Rejected immediately with `ValueError`.
   - $N = 1$: Rejected immediately with `ValueError` ("Insufficient calibration samples (N=1). Minimum N >= 2 is required for statistical threshold calibration").
   - $N \ge 2$: Mathematically computable (computational minimum for sample variance and linear quantile). When $N < \max(10, \lceil 1/\alpha \rceil)$, metadata flags `statistical_reliability = "low_sample_count"`.
   - $N \ge \max(10, \lceil 1/\alpha \rceil)$: Sufficient sample support for extreme quantile estimation, flagged as `statistical_reliability = "statistically_reliable"`.

6. **Exact Boundary Behavior and Tolerance:**
   To avoid ambiguous floating-point equality near thresholds, a numerical boundary tolerance ($\text{atol} = 10^{-9}$) is strictly enforced:
   - For UPPER threshold:
     - $x > T + \text{atol} \implies \text{exceeded} = \text{True}, \text{boundary\_status} = \text{'strictly\_exceeded'}$
     - $|x - T| \le \text{atol} \implies \text{exceeded} = \text{False}, \text{boundary\_status} = \text{'at\_boundary'}$
     - $x < T - \text{atol} \implies \text{exceeded} = \text{False}, \text{boundary\_status} = \text{'strictly\_inside'}$
   - For LOWER threshold:
     - $x < T - \text{atol} \implies \text{exceeded} = \text{True}, \text{boundary\_status} = \text{'strictly\_exceeded'}$
     - $|x - T| \le \text{atol} \implies \text{exceeded} = \text{False}, \text{boundary\_status} = \text{'at\_boundary'}$
     - $x > T + \text{atol} \implies \text{exceeded} = \text{False}, \text{boundary\_status} = \text{'strictly\_inside'}$
   - Signed Exceedance Margin:
     - UPPER: $margin = x - T$ (positive indicates exceedance)
     - LOWER: $margin = T - x$ (positive indicates exceedance)

7. **Configuration Binding & Deterministic Fingerprinting:**
   - Every `ThresholdPolicy` is strictly bound to the `baseline_configuration_hash` of its generating M9 baseline.
   - Evaluations check configuration compatibility and reject mismatched operating conditions with `ConfigurationCompatibilityError`.
   - Policies compute a canonical SHA-256 `policy_fingerprint` across sorted threshold parameters to guarantee immutable provenance and detect any policy drift.

8. **Data Leakage Prevention in False-Alarm Rate Estimation:**
   - Empirical false-alarm rate (FAR) evaluation functions require separate held-out validation observations.
   - Deep element-level identity checks verify that no calibration observation objects are present in the validation dataset, preventing subtle data leakage from container copying or slicing.

---

# 59. DEC-059 — Deterministic Security Decision Engine Architecture, Precedence, Anomaly vs. Attack Distinction, and Absence of Composite Scoring (Milestone M12)

**Status:** ACCEPTED (Milestone M12)

### Decision

1. **Deterministic Verdict Model:**
   Milestone M12 establishes the deterministic security decision engine that consumes M10 statistical evidence, M11 threshold policy evaluation reports, and protocol security evidence to produce unambiguous security verdicts:
   $$\text{Evidence (M10, M11, Protocol)} \implies \text{M12 Decision Engine} \implies \text{ACCEPT} \mid \text{SUSPICIOUS} \mid \text{ATTACK}$$
   - Output states are strictly: `ACCEPT`, `SUSPICIOUS`, `ATTACK`.
   - Security verdicts are explainable state classifications, NOT statistical measurements and NOT arbitrary scalar scores.

2. **Strict Scientific Distinction: Anomaly $\ne$ Confirmed Attack:**
   - Threshold crossing means: *The observation deviated beyond the calibrated honest operating region.*
   - An anomaly indicates unexpected or anomalous physical/statistical behavior; it does NOT constitute proof of an adversarial attack.
   - Therefore:
     $$\text{Threshold Exceeded} + \text{No Explicit Violation} \implies \text{SUSPICIOUS}$$
     $$\text{Threshold Exceeded} \not\implies \text{ATTACK}$$
   - `ATTACK` is strictly reserved for deterministic, confirmed protocol/security violations.

3. **Deterministic Rule Hierarchy and Precedence:**
   The evaluation precedence is strictly ordered and non-probabilistic:
   ```text
   CONFIRMED EXPLICIT SECURITY VIOLATION
           ↓
         ATTACK
   
   INCOMPATIBLE CONFIGURATION / POLICY HASH MISMATCH
           ↓
       SUSPICIOUS
   
   INCOMPLETE / MISSING REQUIRED EVIDENCE
           ↓
       SUSPICIOUS
   
   STATISTICAL ANOMALY / THRESHOLD EXCEEDANCE
           ↓
       SUSPICIOUS
   
   ALL REQUIRED EVIDENCE PRESENT & WITHIN POLICY + COMPATIBLE CONFIGURATION
           ↓
        ACCEPT
   ```
   Rule evaluation never depends on dictionary key iteration order or system timestamps.

4. **ACCEPT Semantics (Deliberately Strict):**
   A verification attempt is accepted IF AND ONLY IF:
   - Required evidence (threshold report or statistical evidence) is present and non-empty.
   - Configuration is compatible (`baseline_configuration_hash` matches).
   - No evaluated threshold is exceeded (`exceeded_count == 0`).
   - No explicit protocol/security violation exists (`explicit_violation is False`).
   - The protocol evidence is complete (`is_evidence_complete is True`).
   `ACCEPT` is never a default fallback for missing or indeterminate information.

5. **SUSPICIOUS Semantics (Honest Uncertainty):**
   `SUSPICIOUS` represents an anomalous or indeterminate state where acceptance is unwarranted, but an explicit attack cannot be proven:
   - One or more statistical thresholds exceeded without confirmed explicit violation.
   - Missing or incomplete evidence (e.g. absent metric evaluations, missing expected metrics).
   - Configuration context mismatches.
   - Indeterminate protocol evidence.

6. **ATTACK Semantics (Explicit Deterministic Violation):**
   `ATTACK` requires an explicit, confirmed violation flag provided by protocol verification layers (e.g., future M15 Forgery, M16 Replay, M17 Impersonation, M18 Unauthorized Verification, M19 Channel Attack modules via `ProtocolSecurityEvidence`).
   M12 does not simulate or classify attack types; it consumes typed violation signals.

7. **Strict Absence of Composite Security Scores:**
   - Strictly NO composite scores (`security_score`, `trust_score`, `risk_score`, `weighted_score`, `quantum_score`).
   - No weighted metric collapse or hidden scoring models.
   - All evaluated metrics, exceeded metric names, and threshold margins are preserved individually in `DecisionResult.exceeded_metrics` and `DecisionResult.threshold_report`.

8. **Missing/Invalid Evidence vs. Programming Errors:**
   - Malformed data or wrong types raise `TypeError` or `ValueError` at runtime validation.
   - Valid data structures indicating incomplete or indeterminate operational evidence deterministically evaluate to `SUSPICIOUS`, never `ACCEPT`.

9. **Immutability and Determinism:**
   - `DecisionResult`, `ProtocolSecurityEvidence`, and `DecisionReasonCode` are immutable (frozen dataclasses and StrEnum).
   - Evaluator functions are pure and side-effect free: repeated evaluations of identical inputs yield identical outputs.

---

# 60. DEC-060 — Impersonation Detection Architecture, Identity/Authentication Evidence Model, Precedence, and Boundary Guarantees (Milestone M13)

**Status:** ACCEPTED (Milestone M13)

### Decision

1. **Formal Definition of Impersonation:**
   An impersonation attempt in Q-SHIELD is defined as an entity attempting to participate in or authenticate within the protocol while asserting an identity that it is not legitimately authorized or authenticated to represent:
   $$\text{Claimed Identity} \ne \text{Expected Identity} \quad \lor \quad \text{Claimed Identity} \ne \text{Authenticated Identity}$$
   Impersonation is fundamentally a protocol- and identity-layer security event, NOT a quantum physical measurement anomaly.

2. **Absolute Boundary Guarantees & Scientific Distinctions:**
   - **Quantum Anomaly $\ne$ Impersonation:** Physical decoherence, noise, and statistical threshold exceedance (e.g. low fidelity, high QBER) indicate operational or channel degradation, NEVER proof of impersonation.
   - **Impersonation $\ne$ Replay:** Freshness, session reuse, and timestamp replays are strictly separated from identity assertion validation.
   - **Impersonation $\ne$ Signature Forgery:** Cryptographic signature invalidity is evaluated at the signature layer, not conflated with identity claims.
   - **Impersonation $\ne$ Unauthorized Verification:** A legitimate identity lacking verification permission belongs to authorization (M14), not identity assertion.
   - **Impersonation $\ne$ Quantum Channel Attack:** Eavesdropping or physical tampering on the quantum channel belongs strictly to M15.

3. **Identity and Authentication Evidence Model:**
   - `IdentityClaim`: Frozen dataclass capturing `claimed_identity`, `expected_identity`, `role`, `session_id`, and `configuration_hash`. Rejects empty/whitespace strings and secret keywords.
   - `AuthenticationEvidence`: Frozen dataclass capturing `authenticated_identity`, `is_authenticated`, `credential_type`, `auth_details`, `is_complete`, and `session_id`. Enforces zero secret leakage by rejecting raw password/private_key keys.
   - `ImpersonationEvidence`: Frozen dataclass capturing categorical status (`IdentityEvidenceStatus`), canonical reason codes (`ImpersonationReasonCode`), and providing direct conversion to M12 `ProtocolSecurityEvidence`. Nested dictionaries are recursively frozen.

4. **Identity Authority Hierarchy & Conflict Resolution:**
   - `authenticated_identity` is authoritative for who the entity actually is.
   - `expected_identity` is authoritative for who the protocol/session context expects.
   - `claimed_identity` is the asserted claim that must agree with both.
   - **Case 1 (`expected == claimed != authenticated`):** Claimant claims to be expected party but authenticated as someone else $\to$ `status = IDENTITY_MISMATCH`, primary reason `AUTHENTICATED_IDENTITY_MISMATCH` (Explicit Violation $\to$ ATTACK).
   - **Case 2 (`expected == authenticated != claimed`):** Claimant claims to be Eve but credentials prove Alice for an Alice session $\to$ `status = CONFLICTING`, reason codes record both `AUTHENTICATED_IDENTITY_MISMATCH`, `CLAIMED_IDENTITY_MISMATCH`, and `CONFLICTING_IDENTITY_EVIDENCE` (Explicit Violation $\to$ ATTACK).
   - **Case 3 (`expected != claimed != authenticated`):** All three disagree $\to$ `status = CONFLICTING`, recording multi-assertional conflict (Explicit Violation $\to$ ATTACK).
   - **Missing Authenticated Identity in Valid Auth:** When `is_authenticated=True` but `authenticated_identity=None`, the mechanism verified a credential but failed to attribute who the entity is. This cannot verify a named claim $\to$ `status = INCOMPLETE`, reason `INCOMPLETE_AUTHENTICATION_EVIDENCE` (Indeterminate $\to$ M12 SUSPICIOUS).

5. **Missing vs. Failed Authentication Semantics:**
   - **Missing Authentication Evidence:** Absence of authentication evidence (`auth_evidence is None` or `is_complete is False`) represents operational incompleteness / uncertainty (`status = INCOMPLETE`, `is_indeterminate = True`). This routes to `is_complete = False` in M12, deterministically evaluating to `SUSPICIOUS`, NEVER `ATTACK`.
   - **Failed Authentication:** Present authentication evidence that explicitly failed (`is_authenticated = False`) constitutes a confirmed protocol violation (`status = AUTHENTICATION_FAILED`, `is_impersonation_detected = True`), routing to `explicit_violation = True` in M12 and evaluating to `ATTACK`.

6. **Explicit Violation Semantics:**
   `is_impersonation_detected = True` is triggered IF AND ONLY IF:
   - Authentication explicitly failed (`is_authenticated is False`), OR
   - Claimed identity does not match authoritatively authenticated identity (`claimed != authenticated`), OR
   - Claimed identity does not match expected identity (`claimed != expected`).

7. **Zero Secret Leakage Enforcement:**
   Raw passwords, private keys, API keys, or cryptographic secrets are strictly prohibited from entering evidence structures (`AuthenticationEvidence`, `IdentityClaim`, `ImpersonationEvidence`). Any attempt to include forbidden secret keywords raises an immediate `ValueError`.

8. **M13 $\to$ M12 Integration Contract:**
   M13 does not duplicate M12's verdict engine. Instead:
   $$\text{M13 ImpersonationEvidence} \xrightarrow{\text{to\_protocol\_security\_evidence()}} \text{M12 ProtocolSecurityEvidence} \xrightarrow{\text{evaluate\_security\_decision()}} \text{DecisionResult}$$
   - When impersonation is detected, M12 Precedence 1 triggers `ATTACK`.
   - When authentication is missing or incomplete, M12 Precedence 3 triggers `SUSPICIOUS`.
   - When identity is valid, M12 Precedence 5 allows `ACCEPT` (if quantum metrics are within policy).

9. **Prohibition of Composite Scoring:**
   Strictly zero scalar composite scores (`impersonation_score`, `identity_score`, `trust_score`, `risk_score`, or weighted combinations). All evidence fields remain individually inspectable and explainable.

10. **Research Prototype Limitations & Assumptions:**
   - Q-SHIELD does not implement production IAM infrastructure (OAuth, JWT, X.509, TLS certificates, blockchain identity).
   - In this research prototype, explicit deterministic typed containers represent identity assertions and credential validations.

---

# 61. DEC-061 — Deterministic Unauthorized Verification Detection Architecture, Verification Policy Model, Boundary Guarantees, and M12 Integration (Milestone M14)

**Status:** ACCEPTED (Milestone M14)

### Decision

1. **Purpose and Formal Definition of Unauthorized Verification:**
   Milestone M14 establishes the deterministic unauthorized verification detection layer for Q-SHIELD.
   Unauthorized verification is defined as an otherwise authenticated participant attempting to perform a verification operation that they are not authorized or permitted to perform within the defined protocol and security context:
   $$\text{Participant Is Authenticated} \land \neg \text{Authorized}(\text{Participant}, \text{Operation}, \text{Resource}, \text{Context})$$
   M14 answers: *"Is this authenticated participant authorized to perform this verification operation in this security context?"*

2. **Authentication vs. Authorization Boundary (M13 vs. M14):**
   - **Authentication (M13)** answers: *"Who are you?"* (Identity assertion validation and credential verification).
   - **Authorization (M14)** answers: *"What are you permitted to do?"* (Policy evaluation on whether an entity is permitted to perform a specific verification operation).
   - $\text{authenticated} = \text{True}$ does NOT imply $\text{authorized} = \text{True}$.
   - $\text{authorized} = \text{False}$ does NOT imply $\text{impersonation} = \text{True}$.
   - Example: Alice is genuinely authenticated as Alice. Alice requests verification. If Alice lacks verification permission under the active policy, M14 flags an explicit unauthorized verification violation (`status = UNAUTHORIZED`, `violation_type = UNAUTHORIZED_VERIFICATION` $\to$ M12 `ATTACK`). This is an authorization violation, NOT an impersonation violation.

3. **Quantum Anomaly Independence (Strict Scientific Rule):**
   - M14 must NEVER infer authorization from quantum measurement anomalies (QBER, fidelity, Bell correlation, threshold crossings).
   - Quantum metrics describe channel physics and hardware noise, not security permissions.
   - Therefore:
     $$\text{Authorized Verifier} + \text{High Quantum Noise / Anomaly} \implies \text{M14 AUTHORIZED}, \text{M12 SUSPICIOUS (via M11)}$$
     $$\text{Unauthorized Verifier} + \text{Clean Quantum Statistics} \implies \text{M14 UNAUTHORIZED}, \text{M12 ATTACK}$$
   - Clean quantum metrics can never override an explicit authorization violation.

4. **Deterministic Authorization Policy Model:**
   - `VerificationOperation`: Categorical enum of supported verification operations (`VERIFY`, `VERIFY_TELEPORTATION`, `AUDIT_VERIFICATION`). Unrelated operations (e.g. `SIGN`, `REGISTER`, `DELETE`, `LOGIN`, `TRANSMIT`) are rejected as unsupported verification scope (`INCOMPATIBLE_CONTEXT` / `UNSUPPORTED_OPERATION`), NEVER misclassified as unauthorized verification attacks.
   - `VerificationPolicy`: Immutable container holding `policy_id`, `allowed_identities`, `allowed_roles`, `allowed_operations`, `allowed_resources`, `denied_identities`, `denied_roles`, `denied_operations`, `denied_resources`, `session_id`, `configuration_hash`, and metadata.
   - `AuthorizationRequest`: Immutable container holding `participant_identity`, `operation`, `role`, `resource_id`, `session_id`, `configuration_hash`, and metadata.
   - `AuthorizationEvidence`: Immutable container holding evaluation outcome (`is_authorized`, `is_unauthorized_detected`, `is_indeterminate`, `status`, `primary_reason`, `reason_codes`, and metadata).

5. **Policy Evaluation Precedence and Explicit Denial Semantics:**
   Evaluation proceeds through strict, deterministic precedence:
   1. Scope check: Operation must be a recognized verification operation.
   2. Context check: Configuration hash and session ID compatibility.
   3. Authentication prerequisite check: Failed or missing authentication routes to `INCOMPLETE` (owned by M13).
   4. Policy availability check: Missing or empty policy routes to `INCOMPLETE`.
   5. Conflicting directives check: Mutual inclusion in allowed and denied sets (identities, roles, operations, or resources) routes to `CONFLICTING`.
   6. Explicit denials: Denied identity, denied role, denied operation, or denied resource triggers `UNAUTHORIZED` (`explicit_violation = True` $\to$ M12 `ATTACK`).
   7. Restriction checks: Operation not in allowed operations or resource not in allowed resources triggers `UNAUTHORIZED` (`explicit_violation = True` $\to$ M12 `ATTACK`).
   8. Whitelist checks: Role not in allowed roles or identity not in allowed identities triggers `UNAUTHORIZED` (`explicit_violation = True` $\to$ M12 `ATTACK`).
   9. Granted: All policy checks satisfied triggers `AUTHORIZED` (`explicit_violation = False`, `is_complete = True` $\to$ M12 `ACCEPT` if quantum metrics clean).

6. **Missing Evidence vs. Explicit Violation Semantics:**
   - **Missing Policy / Incomplete Evidence:** If `policy is None` or policy contains no rules, `status = INCOMPLETE`, `is_unauthorized_detected = False`, `is_indeterminate = True`. M12 evaluates this to `SUSPICIOUS`, NEVER `ATTACK`. Uncertainty is never converted into an attack.
   - **Explicit Denial:** Confirmed policy denial (explicit deny or whitelist exclusion) produces `status = UNAUTHORIZED`, `is_unauthorized_detected = True`, yielding `explicit_violation = True` and M12 `ATTACK`.

7. **Conflicting Evidence Semantics:**
   Contradictory directives (identity, role, operation, or resource simultaneously present in both allowed and denied sets, or role allowed while identity denied) deterministically produce `status = CONFLICTING`, `primary_reason = CONFLICTING_AUTHORIZATION_EVIDENCE`, and `is_indeterminate = True`, evaluating to `SUSPICIOUS` in M12. Neither "deny wins" nor "allow wins" is applied; genuine conflicts remain explicitly visible as conflicts.

8. **Context and Session Binding Semantics:**
   Mismatched `session_id` or `configuration_hash` produces `status = INCOMPATIBLE_CONTEXT` (`is_indeterminate = True`), routing to `SUSPICIOUS` in M12 and NEVER an accidental `ACCEPT`.

9. **M12 Decision Engine Integration:**
   M14 integrates into M12 via `AuthorizationEvidence.to_protocol_security_evidence()` and `evaluate_authorization_decision()`:
   $$\text{AuthorizationEvidence} \to \text{ProtocolSecurityEvidence} \to \text{M12 evaluate\_security\_decision}() \to \text{DecisionResult}$$
   M14 does not replace M12; M12 remains the sole final decision authority.

10. **Strict Scope & Engineering Boundaries:**
    - **No Impersonation Detection (M13):** M14 consumes authenticated identity evidence; it does not validate credentials or detect identity spoofing.
    - **No Replay Detection:** M14 has no nonce reuse tracking, freshness windows, or timestamp caching.
    - **No Quantum Channel Attack Detection (M15):** M14 has no photon-level monitoring, intercept-resend, or eavesdropping detectors.
    - **No Composite Scoring:** Strictly zero scalar trust scores, risk scores, or security scores.
    - **No AI / Machine Learning:** Rule-based deterministic evaluation only.
    - **No Enterprise IAM:** M14 is a research-grade, memory-resident authorization evaluator for the Q-SHIELD prototype; it does not implement OAuth, JWT, X.509, LDAP, Active Directory, or cloud IAM.
    - **Defensive Secret Leakage Guard:** Rejects known secret-bearing field names (`password`, `secret`, `private_key`, etc.) in metadata; does not claim mathematically complete secret discovery.
    - **Proportional Scientific Claims:** M14 is scientifically and architecturally reviewed, deterministically tested, and regression validated; it makes no claims of 100% universal security or mathematically complete verification.

---

# 62. DEC-062 — Deterministic Quantum Channel Attack Detection Layer Architecture, Lower-Layer Statistical Evidence Reuse, Anomaly vs Attack Distinctions, Categorical Channel States, and Decision Engine Bridge

**Status:** ACCEPTED (Milestone M15)

### Decision

1. **Purpose and Scientific Boundaries of M15:**
   Milestone M15 establishes the deterministic quantum channel attack and anomaly detection layer for Q-SHIELD. It deterministically evaluates whether observed quantum communication telemetry (QBER, teleportation fidelity, Bell correlations, Born measurement distributions / TVD, and Pauli expectation values) is inconsistent with the calibrated honest quantum channel baseline.
   $$\text{M10 Statistical Evidence} + \text{M11 Threshold Report} \implies \text{M15 Channel Detection} \implies \text{ChannelSecurityEvidence}$$
   - M15 answers: *"Does the observed quantum communication behavior provide evidence of a channel-level security anomaly or disturbance?"*
   - M15 does **NOT** answer: *"Who attacked?"* (Strictly owned by M13 Impersonation Detection).
   - M15 does **NOT** answer: *"Was this participant authorized?"* (Strictly owned by M14 Unauthorized Verification Detection).
   - M15 does **NOT** produce the final security decision (`ACCEPT`, `SUSPICIOUS`, `ATTACK`). M12 remains the sole final decision authority.

2. **Zero Duplicate Calculations & Lower-Layer Consumption:**
   M15 strictly consumes lower-layer evidence from M10 (`StatisticalEvidence`) and M11 (`PolicyEvaluationReport`, `MetricThresholdEvaluation`). M15 does **NOT** independently recalculate sample means, variances, standard errors, z-scores, Total Variation Distance (TVD), Kolmogorov-Smirnov (KS) statistics, Welch's t-tests, or empirical quantiles. Threshold boundaries and directionalities are owned by M11 and never overridden by hardcoded heuristics in M15.

3. **Important Semantic Distinction — Statistical Anomaly $\ne$ Proven Attacker:**
   A threshold exceedance (e.g. $\text{QBER} > \text{threshold}$) represents a statistically significant channel anomaly beyond the calibrated honest operating bounds. It does **NOT** constitute proof of a specific named adversary (e.g. Eve performing intercept-resend). Possible physical causes include uncalibrated environmental fluctuations, device thermal drift, fiber perturbation, hardware misalignment, or active interference. M15 uses categorical, explainable language (`CHANNEL_ANOMALY`, `CHANNEL_SECURITY_VIOLATION`, `ATTACK_CONSISTENT_CHANNEL_BEHAVIOR`) rather than speculative claims of confirmed attacker identity.

4. **Categorical Evidence States (`ChannelEvidenceStatus`):**
   M15 defines deterministic, mutually exclusive categorical states:
   - `CLEAN`: Required telemetry and threshold evaluations present, operating context matches, no threshold exceeded.
   - `ANOMALOUS`: Required telemetry present, operating context matches, one or more calibrated thresholds exceeded.
   - `SECURITY_VIOLATION`: Explicit channel-security violation confirmed under defined protocol criteria.
   - `INCOMPLETE`: Required telemetry or threshold report is missing or contains insufficient data.
   - `INCOMPATIBLE_CONTEXT`: Session identifier or baseline configuration hash does not match expected operating context.
   - `CONFLICTING`: Channel evidence contains contradictory lower-layer assertions (e.g. incompatible policy/report hashes).

5. **Canonical Machine-Readable Reason Codes (`ChannelReasonCode`):**
   Decisions are explained using typed, canonical reason codes:
   - `CHANNEL_CLEAN`: All evaluated metrics within calibrated threshold boundaries.
   - `QBER_THRESHOLD_EXCEEDED`: Quantum bit error rate crossed upper calibrated threshold.
   - `BELL_CORRELATION_ANOMALY`: Bell-state correlation crossed calibrated boundary.
   - `TELEPORTATION_FIDELITY_ANOMALY`: Teleportation fidelity dropped below lower threshold.
   - `DISTRIBUTION_TVD_THRESHOLD_EXCEEDED`: Born probability total variation distance crossed upper threshold.
   - `PAULI_EXPECTATION_ANOMALY`: Pauli expectation absolute deviation crossed upper threshold.
   - `CHANNEL_STATISTICAL_ANOMALY`: General metric deviation crossed calibrated threshold.
   - `MULTI_METRIC_CHANNEL_DISTURBANCE`: Multiple independent physical signal categories anomalous simultaneously.
   - `QUANTUM_CHANNEL_SECURITY_VIOLATION`: Confirmed explicit channel security violation.
   - `MISSING_CHANNEL_EVIDENCE`: Telemetry or threshold report missing entirely.
   - `INCOMPLETE_CHANNEL_EVIDENCE`: Required metrics absent from evaluation report.
   - `CHANNEL_SESSION_MISMATCH`: Session identifier mismatch against expected context.
   - `CHANNEL_CONFIGURATION_MISMATCH`: Configuration hash mismatch against expected context.
   - `CHANNEL_CONTEXT_MISMATCH`: General provenance or context incompatibility.
   - `CONFLICTING_CHANNEL_EVIDENCE`: Contradictory reports or configuration assertions.
   - `UNSUPPORTED_CHANNEL_EVIDENCE`: Unrecognized or malformed evidence structure.

6. **Multi-Signal Evidence & No "First Error Wins":**
   M15 never aborts processing upon encountering the first threshold exceedance. When multiple independent metrics cross thresholds (e.g. QBER elevated AND Bell correlation degraded AND teleportation fidelity degraded), M15 preserves **ALL** applicable reason codes and records `MULTI_METRIC_CHANNEL_DISTURBANCE`. Primary reason selection follows strict deterministic precedence.

7. **Context and Configuration Binding:**
   M15 enforces exact SHA-256 baseline configuration hash and session identifier matching. Incompatible operating conditions route to `INCOMPATIBLE_CONTEXT` and evaluate to `SUSPICIOUS` in M12, preventing false acceptance while never misclassifying configuration mismatches as attacks.

8. **Missing Evidence vs. Explicit Violation Semantics:**
   - **Missing Evidence:** If telemetry or threshold reports are missing, `status = INCOMPLETE`, `is_evidence_complete = False`. M12 evaluates this to `SUSPICIOUS`, NEVER `ATTACK`.
   - **Explicit Violation:** If an explicit channel security breach is verified, `status = SECURITY_VIOLATION`, `is_explicit_violation = True`, `violation_type = "QUANTUM_CHANNEL_SECURITY_VIOLATION"`, yielding M12 `ATTACK`.

9. **Noise Model Operational Boundary:**
   Calibrated honest noise (M8/M9) produces physical metrics within M11 threshold policies. M15 evaluates compliant noise as `CLEAN` (M12 `ACCEPT`), ensuring legitimate physical noise is never classified as an attack.

10. **M12 Decision Engine Integration:**
    M15 bridges to M12 via `ChannelSecurityEvidence.to_protocol_security_evidence()` and `evaluate_channel_attack_decision()`:
    $$\text{ChannelSecurityEvidence} \to \text{ProtocolSecurityEvidence} \to \text{M12 evaluate\_security\_decision}() \to \text{DecisionResult}$$
    M15 does not usurp M12; M12 remains the sole final decision authority.

11. **Strict Scope & Engineering Boundaries:**
    - **No Impersonation Detection (M13):** Channel anomalies do not imply or modify identity claims.
    - **No Unauthorized Verification Detection (M14):** Channel anomalies do not imply or modify authorization status.
    - **No Replay Detection:** M15 contains no nonce tracking, timestamp caches, or replay windows.
    - **No Composite Scoring:** Strictly zero scalar trust scores, risk scores, or composite scalar collapsing.
    - **No AI / Machine Learning:** Rule-based deterministic evaluation only.
    - **Strict Immutability & Secret Leakage Guards:** Frozen dataclasses, recursive deep copying, and rejection of credentials/secrets in metadata.

---

# 63. DEC-063 — Deterministic Evidence Fusion Layer Architecture, Multi-Source Synthesis (M13/M14/M15), Absolute Scope Boundaries, Categorical Fused States, Missing Evidence and Conflict Semantics, and Sole M12 Final Decision Authority

**Status:** ACCEPTED (Milestone M16)

### Decision

1. **Purpose and Scope Boundary of M16:**
   Milestone M16 establishes the deterministic evidence fusion layer for Q-SHIELD. It aggregates, synthesizes, and audits independent security evidence across identity (M13 Impersonation), authorization (M14 Unauthorized Verification), and quantum channel physics (M15 Quantum Channel Attacks) into an immutable, deterministic, auditable container (`FusedSecurityEvidence`).
   $$\text{M13 Evidence} + \text{M14 Evidence} + \text{M15 Evidence} \implies \text{M16 Evidence Fusion} \implies \text{FusedSecurityEvidence} \to \text{M12 Engine} \implies \text{DecisionResult}$$
   - M16 answers: *"What security evidence is present across identity, authorization, and quantum-channel dimensions, and are those evidence assertions mutually compatible and complete?"*
   - M16 does **NOT** answer: *"Is the system secure?"*, *"What is the risk score?"*, or *"Who attacked?"*
   - **M16 is strictly an evidence aggregation and synthesis layer, NOT a second final decision engine.** M12 remains the **sole authorized decision authority** (`ACCEPT / SUSPICIOUS / ATTACK`).

2. **Zero Composite Scoring, Zero Machine Learning & Zero Weighted Voting:**
   M16 strictly prohibits:
   - Scalar risk scores, trust scores, threat scores, confidence scores, attack probabilities, or severity ratings (e.g. no 0–100 scale).
   - Numerical combinations, weighted voting, majority voting, Bayesian attack probabilities, or heuristic points.
   - Machine learning, neural networks, or classifiers.
   Evidence fusion remains entirely categorical, rule-based, and auditable.

3. **Source Evidence Provenance and Identity Preservation:**
   The fused container retains the distinct identity and semantics of each contributing subsystem:
   - `IMPERSONATION` (M13): Identity authentication, credential matching, and impersonation detection.
   - `AUTHORIZATION` (M14): Verification operation permissions, role/resource policy evaluation.
   - `QUANTUM_CHANNEL` (M15): Channel telemetry, physical disturbance, and calibrated threshold evaluations.
   All individual reason codes and subsystem statuses are preserved without flattening, loss of attribution, or semantic reinterpretation.

4. **Preservation of Semantic Distinctions (Anomaly vs Explicit Violation):**
   M16 strictly preserves the boundary between:
   - **Statistical / Physical Anomalies:** (e.g. M15 QBER or fidelity threshold exceedances) $\to$ preserved as `ANOMALOUS` (evaluating to M12 `SUSPICIOUS`). Anomalies are never upgraded into confirmed attacks.
   - **Explicit Security Violations:** (e.g. M13 impersonation mismatch, M14 unauthorized verification denial, M15 explicit channel breach) $\to$ preserved as `SECURITY_VIOLATION` (evaluating to M12 `ATTACK`). Explicit violations are never downgraded into generic anomalies.

5. **Multi-Signal & Multiple Explicit Violation Accumulation:**
   When multiple subsystems independently confirm explicit security violations (e.g. M13 impersonation detected AND M14 unauthorized verification attempt AND M15 channel security breach), M16 preserves **ALL** confirmed violation identifiers deterministically without "first violation wins" or overwrite.

6. **Missing Evidence Semantics ($\text{Missing} \ne \text{Clean}$):**
   Missing or omitted required evidence sources (e.g. unprovided M14 authorization report) deterministically evaluate to `status = INCOMPLETE` and `is_complete = False`, routing to M12 `SUSPICIOUS`. Missing evidence is never converted into clean evidence or confirmed attack.

7. **Context & Configuration Compatibility:**
   M16 audits operational context across all contributing evidence records:
   - `session_id` must match across all sources and against expected context constraints.
   - `configuration_hash` (canonical SHA-256) must match across all sources and against expected baseline.
   - Discrepancies produce `INCOMPATIBLE_CONTEXT` or `CONFLICTING`, routing to M12 `SUSPICIOUS` and preventing cross-session or mismatched configuration fusion.

8. **Conflict Handling & Explicit Violation Preservation:**
   If contributing sources report contradictory evidence assertions (e.g. M13 reports internal credential conflict, or sources assert contradictory session contexts):
   - M16 marks `status = CONFLICTING` and `is_complete = False`.
   - **Crucial Invariant:** If any source independently confirms an explicit security violation (e.g. M13 impersonation mismatch, M14 unauthorized verification attempt, M15 quantum channel breach), that explicit violation is **preserved** (`is_explicit_violation = True`, `violations = (...)`, reason code `EXPLICIT_SECURITY_VIOLATION_PRESENT`). Conflicting peripheral or contextual evidence does not suppress or erase confirmed explicit violations.
   - If no explicit violation is present, a conflict evaluates to M12 `SUSPICIOUS` (`explicit_violation = False`).
   - M16 never applies arbitrary heuristics ("allow wins", "deny wins") or numerical voting to conceal contradictions.

9. **Deterministic Fused Status Precedence Hierarchy:**
   Fused status is determined via strict deterministic precedence:
   1. *Conflicting Evidence Assertions* $\to$ `CONFLICTING` (Preserves explicit violations if present $\to$ M12 `ATTACK`; otherwise M12 `SUSPICIOUS`)
   2. *Confirmed Explicit Security Violation* $\to$ `SECURITY_VIOLATION` (M12 `ATTACK`)
   3. *Context / Configuration Hash Incompatibility* $\to$ `INCOMPATIBLE_CONTEXT` (Preserves explicit violations if present $\to$ M12 `ATTACK`; otherwise M12 `SUSPICIOUS`)
   4. *Missing Required Source / Incomplete Evidence* $\to$ `INCOMPLETE` (Preserves explicit violations if present $\to$ M12 `ATTACK`; otherwise M12 `SUSPICIOUS`)
   5. *Physical / Statistical Channel Anomaly* $\to$ `ANOMALOUS` (M12 `SUSPICIOUS`)
   6. *All Required Sources Present & Clean* $\to$ `CLEAN` (M12 `ACCEPT`)

10. **M12 Decision Engine Integration:**
    M16 integrates seamlessly into M12 via `FusedSecurityEvidence.to_protocol_security_evidence()` and `evaluate_fused_security_decision()`:
    $$\text{FusedSecurityEvidence} \to \text{ProtocolSecurityEvidence} \to \text{M12 evaluate\_security\_decision}() \to \text{DecisionResult}$$
    In `ProtocolSecurityEvidence`, M16 maps `explicit_violation = self.is_explicit_violation`, `violation_type = "+".join(self.violations)`, and `is_complete = self.is_complete`.
    Under established M12 Precedence 1 ("Confirmed Explicit Violation $\to$ ATTACK"), M12 evaluates confirmed explicit violations with highest authority, yielding `DecisionVerdict.ATTACK`.
    M16 does not bypass or replace M12; M12 remains the sole final decision authority.

11. **Deep Immutability & Defensive Secret Leakage Guard:**
    `FusedSecurityEvidence` is a frozen dataclass with defensive copies of all sequences and deep-freezing of metadata dictionaries. Any dictionary key containing prohibited secret substrings (`password`, `secret`, `private_key`, `raw_key`, `token_secret`, `credential_raw`, `key_material`, `shared_secret`, `api_key`) is immediately rejected with `ValueError`.

12. **Timestamp Provenance & Bit-for-Bit Determinism:**
    `FusedSecurityEvidence.timestamp` represents deterministic observation provenance.
    - When an explicit timestamp is supplied by the caller, it is preserved.
    - When omitted, it is derived deterministically from the latest timestamp present in contributing source evidence (or empty string if none provided).
    - Fusion performs no runtime clock evaluations (`datetime.now()`), guaranteeing that repeated fusions with identical inputs, context, and source evidence produce bit-for-bit identical outputs.

---

# 64. DEC-064 — Deterministic Security Evaluation Layer Architecture, Scenario-Driven Pipeline Auditing, Controlled Evaluation Boundary, and Prohibition of Unjustified Security Claims

**Status:** ACCEPTED (Milestone M17)

### Decision

1. **Purpose and Scope Boundary of M17:**
   Milestone M17 establishes the deterministic security evaluation layer for Q-SHIELD.
   $$\text{EvaluationScenario} \to \text{M17 Evaluator} \to \text{M12 Decision Authority} \to \text{EvaluationResult} \to \text{EvaluationSummary}$$
   - M17 answers: *"How does the implemented Q-SHIELD security pipeline behave when evaluated against controlled, known security scenarios?"*
   - M17 does **NOT** detect attacks.
   - M17 does **NOT** replace or bypass M12.
   - M17 evaluates how the system behaves under defined, reproducible security scenarios and produces auditable, deterministic evaluation records.

2. **Absolute Decision Authority (M12 Sole Authority):**
   M17 is strictly an evaluation harness and contains zero attack decision logic. M17 does not independently calculate:
   $$\text{if violation } \to \text{ATTACK, else if anomaly } \to \text{SUSPICIOUS}$$
   Instead, M17 submits the scenario evidence fixture to M12 (`evaluate_security_decision`), observes M12's verdict and reason codes, and compares the observed decision with the scenario's expected outcome. M12 remains the sole final decision authority.

3. **Controlled Evaluation Scenarios (Fixtures vs Real-World Claims):**
   M17 defines ten canonical evaluation categories representing controlled evaluation fixtures:
   - `CLEAN_HONEST`: Legitimate signature and quantum transmission under ideal operating conditions.
   - `BENIGN_NOISE`: Legitimate transmission experiencing calibrated channel noise within operating tolerance.
   - `IMPERSONATION`: Identity mismatch / spoofed signature detection (M13).
   - `UNAUTHORIZED_VERIFICATION`: Verification attempt by unpermitted participant / role (M14).
   - `QUANTUM_CHANNEL_ANOMALY`: Calibrated threshold exceedance on quantum channel telemetry (M15).
   - `EXPLICIT_QUANTUM_CHANNEL_VIOLATION`: Confirmed explicit physical channel security breach (M15).
   - `INCOMPLETE_EVIDENCE`: Missing telemetry, absent policies, or incomplete evidence fixtures.
   - `INCOMPATIBLE_CONTEXT`: Mismatched session identifiers or baseline configuration hashes.
   - `CONFLICTING_EVIDENCE`: Contradictory evidence assertions across or within subsystems.
   - `MULTI_SOURCE_SECURITY_VIOLATION`: Combinations of independent explicit violations across M13, M14, and M15.
   These scenarios are controlled test fixtures; they do not represent real-world attack detection probability.

4. **Expected vs Observed Evaluation Semantics:**
   M17 evaluates scenarios categorically:
   - `PASS`: The system produced the exact expected verdict (`ACCEPT`, `SUSPICIOUS`, or `ATTACK`) for this defined evaluation scenario.
   - `FAIL`: The observed system verdict did not match the expected verdict for the scenario.
   M17 PASS does **NOT** mean "the system is cryptographically secure." M17 FAIL does **NOT** mean "the detector is broken in the real world."

5. **Deterministic Categorical & Count-Based Metrics:**
   M17 reports deterministic counts and dataset-bound metrics:
   - Total scenarios, passed scenarios, failed scenarios, and pass rate.
   - Categorical verdict distribution: counts of `ACCEPT`, `SUSPICIOUS`, and `ATTACK`.
   - Confusion matrix counts on the evaluation dataset:
     - True Positive (TP): Expected security violation (`ATTACK`) and observed `ATTACK`.
     - False Negative (FN): Expected security violation (`ATTACK`) but observed non-`ATTACK`.
     - False Positive (FP): Expected non-violation scenario and observed `ATTACK`.
     - True Negative (TN): Expected non-violation scenario and observed non-`ATTACK`.
     - Sensitivity and Specificity strictly on the defined evaluation dataset.
   M17 strictly prohibits scalar trust scores, risk scores, weighted combination scores, or speculative real-world attack probability percentages.

6. **Strict Prohibition of Unjustified Security Claims:**
   The implementation, documentation, and reports strictly forbid claiming:
   - 100% security or zero-day protection.
   - Guaranteed quantum attack detection or universal threat mitigation.
   - Information-theoretic detector guarantees (distinguished from protocol assumptions per DEC-023).
   - Real-world attack detection probability.
   - Attacker identification (distinguished from channel anomaly per DEC-062).
   Approved scientific phrasing: *"observed on the defined evaluation scenarios under the tested assumptions within the calibrated simulation"*.

7. **Multi-Source Evaluation Combinations:**
   M17 systematically evaluates multi-source interaction combinations (A through J):
   - M13 violation only
   - M14 violation only
   - M15 violation only
   - M13 + M14 violations
   - M13 + M15 violations
   - M14 + M15 violations
   - M13 + M14 + M15 violations
   - Explicit violation + conflict
   - Anomaly + incomplete evidence
   - Clean + expected noise
   All combinations observe existing M16/M12 fusion precedence without creating ad-hoc precedence rules.

8. **Deterministic Suite Execution & Continuation on Failure:**
   The evaluation runner (`run_security_evaluation`):
   - Executes all scenarios to completion without early abort upon failure.
   - Preserves deterministic scenario ordering.
   - Never mutates input scenarios or evidence fixtures.
   - Employs zero runtime timestamps (`datetime.now()`), ensuring bit-for-bit reproducible results across repeated runs.

9. **Deep Immutability & Defensive Secret Leakage Guard:**
   `EvaluationScenario`, `EvaluationResult`, `ConfusionMatrixMetrics`, `CategorySummary`, and `EvaluationSummary` are frozen dataclasses with defensively frozen tuples and mapping proxies. Scenario metadata is recursively scanned to reject sensitive secret-bearing keys (`password`, `secret`, `private_key`, `key_material`, etc.).

10. **Scope Discipline:**
    M17 contains zero dependencies on future modules (M18 benchmarking, M19 dashboard, M20 blockchain). M17 operates entirely on the frozen M1–M16 architecture.

---

# 65. DEC-065 — Deterministic Performance Benchmarking Architecture, Monotonic High-Resolution Timing, Warmup Isolation, Zero-Denominator Semantics, Observational Metrics vs Scoring Prohibition, and Scientific Claim Discipline

**Status:** ACCEPTED (Milestone M18)

### Decision

1. **Purpose and Scope Boundary of M18:**
   Milestone M18 establishes the deterministic performance and operational benchmarking layer for Q-SHIELD.
   $$\text{Controlled Benchmark Workload} \to \text{Pipeline Execution} \to \text{Monotonic Timing Measurement} \to \text{BenchmarkResult} \to \text{BenchmarkSuiteResult}$$
   - M18 answers: *"How long does a Q-SHIELD evaluation take under controlled workloads, how does execution scale as volume increases, what is the throughput, and are benchmark specifications reproducible?"*
   - M18 does **NOT** detect attacks.
   - M18 does **NOT** decide security outcomes (M12 remains sole authority).
   - M18 does **NOT** evaluate security correctness (M17 role).
   - M18 does **NOT** optimize or adapt thresholds or detection logic.
   - M18 is **strictly a performance and operational measurement layer**.

2. **Absolute Architectural Hierarchy:**
   The architectural authority chain is invariant:
   $$\text{M12 (Sole Final Security Decision)} \longrightarrow \text{M17 (Security Evaluation)} \longrightarrow \text{M18 (Operational Benchmarking)}$$
   Neither M17 nor M18 may replace, reinterpret, or bypass M12 verdicts (`ACCEPT / SUSPICIOUS / ATTACK`).

3. **High-Resolution Monotonic Timing Methodology:**
   Elapsed execution durations are measured using the platform's high-resolution monotonic timer:
   - `time.perf_counter()` is used exclusively for measuring elapsed execution latency per iteration.
   - `time.process_time()` is captured to record process CPU time.
   - Wall-clock timestamps (`datetime.now()`, `time.time()`) are **strictly forbidden** for elapsed duration calculations.

4. **Warmup Phase Isolation:**
   To mitigate cold-cache, import, and JIT/interpreter startup transients:
   - Configured warmup iterations execute before measured iterations.
   - All warmup execution timings are **strictly excluded** from measured sample collections (`raw_latencies`), aggregate metrics (`min`, `max`, `mean`, `median`, `p95`), and throughput calculations.

5. **Determinism vs. Empirical Timing Reality:**
   M18 rigorously distinguishes:
   - **Deterministic Specifications & Formulas:** Benchmark definitions, input scenario fixtures, configuration hashes, session bindings, and statistical calculation algorithms are 100% deterministic and bit-for-bit reproducible.
   - **Empirical Timing Reality:** Elapsed execution time is an empirical physical measurement subject to CPU frequency, OS scheduling, background processes, memory bus contention, and hardware architecture. M18 **never** claims that physical timing values are mathematically deterministic or guaranteed across different hardware environments.

6. **Zero-Denominator & Empty Data Semantics:**
   Consistent with M17's scientific rigor, metrics are never fabricated:
   - If configured iterations or successful iterations are 0:
     $$\text{mean} = \text{None}, \quad \text{min} = \text{None}, \quad \text{max} = \text{None}, \quad \text{median} = \text{None}, \quad \text{p95} = \text{None}, \quad \text{throughput} = \text{None}$$
   - Metrics are never defaulted to `0.0`, `1.0`, or arbitrary placeholders when the mathematical denominator is zero.

7. **Strict Prohibition of Security & Risk Scoring:**
   M18 strictly prohibits:
   - `security_score`, `risk_score`, `trust_score`, `threat_score`, `confidence_score`, `attack_probability`, or composite heuristic points.
   - Using low latency to imply higher security. Performance $\ne$ security.
   - M12 verdict distributions (counts of `ACCEPT`, `SUSPICIOUS`, `ATTACK`) are recorded purely as observational measurements of what the pipeline produced during the benchmark workload.

8. **Categorical Benchmark Coverage (Categories A through F):**
   M18 standardizes six operational categories:
   - `BASELINE_EVALUATION`: Operational latency of clean honest scenario evaluations.
   - `SUSPICIOUS_EVALUATION`: Latency of channel anomaly evaluations.
   - `ATTACK_EVALUATION`: Latency of confirmed explicit security violation evaluations.
   - `EVIDENCE_FUSION`: Multi-source M16 evidence fusion throughput and latency.
   - `SCENARIO_SCALING`: Multi-scenario workload batch scaling ($N = 1, 10, 50, 100$).
   - `END_TO_END_PIPELINE`: Complete 16-scenario baseline evaluation suite execution.

9. **Deep Immutability, Stable Identifier Retrieval & Secret Guard:**
   - `BenchmarkScenario`, `BenchmarkResult`, and `BenchmarkSuiteResult` are frozen dataclasses with defensive sequence copies and recursively frozen metadata.
   - Suite results allow direct, stable retrieval by benchmark identifier (`results_by_id`, `get_result(benchmark_id)`), avoiding fragile list-index assumptions.
   - Metadata is recursively inspected to reject sensitive secret keywords (`password`, `secret`, `private_key`, `key_material`, etc.).

10. **Scientific Claim Boundary:**
    M18 benchmark reports may legitimately state:
    > *"Under the documented benchmark environment and workload parameters, Q-SHIELD exhibited the measured latency, throughput, and scaling characteristics."*
    They must **never** claim:
    - *"The benchmark proves 100% security or complete attack immunity."*
    - *"Low latency proves cryptographic robustness."*

---

# 66. Final Decision Principle

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








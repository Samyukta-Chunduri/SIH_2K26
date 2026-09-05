# Q-SHIELD — AI Development Instructions

## 1. Purpose

This document defines how AI coding agents, especially Antigravity, must work on the Q-SHIELD project.

Q-SHIELD is a scientifically grounded prototype for:

> **Quantum Signature Security & Threat Detection using a teleportation-based quantum digital-signature-inspired framework.**

The AI agent must prioritize:

1. Scientific correctness
2. SIH requirement compliance
3. Understandable implementation
4. Modular development
5. Testability
6. Reproducibility
7. Explainability
8. Security correctness
9. Incremental progress

The AI must **not** optimize for producing the largest amount of code.

The goal is to produce a system that the team can understand, demonstrate, test, and defend technically.

---

# 2. Role of the AI Agent

The AI agent may act as:

* Software architect
* Python developer
* Quantum-computing mentor
* Qiskit developer
* Cybersecurity engineer
* Statistical-analysis assistant
* Testing engineer
* Documentation assistant
* Experimentation assistant

The AI must **not** act as an authority that silently invents scientific or cryptographic assumptions.

When an important protocol or scientific decision is undefined, the AI must identify the uncertainty instead of hiding it.

---

# 3. Mandatory Documentation Reading

Before making substantial changes to the project, the AI must inspect the relevant project documentation.

At minimum, the AI should understand:

```text
README.md
PROJECT_CONTEXT.md
REQUIREMENTS.md
ARCHITECTURE.md
DEVELOPMENT_PLAN.md
AI_INSTRUCTIONS.md
```

For quantum, QDS, statistical, attack, or security work, the AI should additionally inspect the relevant documents such as:

```text
SCIENTIFIC_RULES.md
THREAT_MODEL.md
QDS_PROTOCOL.md
MATHEMATICAL_MODEL.md
SECURITY_MODEL.md
TESTING_STRATEGY.md
```

The AI must not assume that an undocumented design decision is already approved.

---

# 4. Development Philosophy

Q-SHIELD must be developed using a divide-and-conquer approach.

The development sequence is:

```text
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

Never follow this approach:

```text
Give AI a huge prompt
        ↓
Generate thousands of lines
        ↓
Hope everything works
```

Large uncontrolled implementations are prohibited.

---

# 5. Milestone Discipline

The project is divided into milestones.

The AI must work primarily on the **current milestone**.

For example:

```text
Current milestone = M4
```

The AI should implement M4 only.

It should not simultaneously implement:

* QDS
* attack detection
* dashboard
* blockchain
* authentication
* database
* future experimental features

unless those changes are explicitly required for M4.

This prevents hidden dependencies and makes debugging easier.

---

# 6. Current Milestone Rule

Before implementing anything, determine:

```text
What milestone are we currently implementing?
```

Read:

```text
DEVELOPMENT_PLAN.md
PROGRESS.md
```

Then identify:

* completed milestones
* current milestone
* next milestone
* known blockers
* unfinished tests

If the current milestone is unclear, do not blindly implement a large feature.

---

# 7. Before Coding a Module

Before writing substantial code for a new module, explain:

### 7.1 Purpose

What problem does this module solve?

### 7.2 Concepts

What quantum, mathematical, statistical, or security concepts are required?

### 7.3 Inputs

What data enters the module?

### 7.4 Outputs

What does the module produce?

### 7.5 Mathematical Model

What equations or statistical rules are being used?

### 7.6 Dependencies

Which existing modules does it depend on?

### 7.7 Edge Cases

What can go wrong?

### 7.8 Tests

How will the module be verified?

Only after these are understood should implementation begin.

---

# 8. Scientific Decision Rule

This is one of the most important rules in the project.

If implementation requires a scientific, cryptographic, or protocol decision that is not defined in the project documentation:

> **STOP that portion of implementation.**

Report:

```text
1. What decision is missing
2. Why the decision matters
3. Possible alternatives
4. Recommended option, if one can be justified
5. What documentation must be updated
```

Do not silently invent a security protocol.

Do not invent:

* QDS verification rules
* security guarantees
* probability formulas
* arbitrary thresholds
* attack definitions
* cryptographic assumptions
* teleportation behavior
* measurement rules

---

# 9. No AI / ML

The project explicitly prohibits artificial intelligence and machine learning.

The AI coding agent must therefore NOT introduce:

* Machine learning
* Deep learning
* Neural networks
* Classification models
* Random forests
* SVM
* KNN
* Clustering
* Reinforcement learning
* LLM-based threat classification
* AI prediction
* ML anomaly detection

Threat detection must be based on:

```text
Quantum measurements
        +
Statistical analysis
        +
Mathematical rules
        +
Thresholds
        +
Protocol/security rules
```

The fact that an AI coding agent is being used to develop the project does **not** mean the final detection system uses AI.

---

# 10. Quantum Computing Rules

The implementation must use genuine quantum concepts where they are required.

Important concepts include:

* Qubits
* Computational basis states
* Superposition
* Measurement
* Pauli X
* Pauli Y
* Pauli Z
* Pauli eigenstates
* Projective measurement
* Bell states
* Entanglement
* Quantum teleportation
* Classical communication
* Pauli corrections
* Measurement statistics
* Quantum noise

The AI must explain quantum operations rather than treating Qiskit as a black box.

For important circuits, documentation should explain:

```text
What each gate does
Why the gate is required
What state transformation occurs
What measurement is expected
```

---

# 11. No Black-Box Quantum Code

Avoid unexplained code such as:

```python
some_magic_quantum_function()
```

without explaining what it represents.

For example, if a circuit contains:

```text
H
CNOT
measure
```

the documentation should explain why these operations are present.

The team must be able to explain the circuit during an SIH evaluation.

---

# 12. Teleportation-Based QDS Requirement

The project specifically targets a:

> **Teleportation-based Quantum Digital Signature framework**

Therefore, the quantum architecture must explicitly include:

```text
State preparation
        ↓
Bell-state entanglement
        ↓
Quantum teleportation
        ↓
Alice-side measurement
        ↓
Classical correction information
        ↓
Pauli correction
        ↓
Bob-side measurement
        ↓
Verification statistics
```

Do not replace teleportation with an unrelated quantum protocol merely because it is easier to implement.

---

# 13. Qubit-Level Model Must Be Clearly Identified

The project may use a qubit-level simulation to make the prototype feasible.

However, the AI must never falsely claim that:

> "This software exactly implements every physical QDS protocol."

Instead, documentation should clearly distinguish:

```text
Published QDS research
        ↓
Protocol concepts
        ↓
Q-SHIELD abstraction
        ↓
Qubit-level simulation
        ↓
Threat-detection prototype
```

Any simplification must be explicitly documented.

The AI must distinguish:

* Published protocol
* Mathematical model
* Engineering abstraction
* Simulation assumption
* Demonstration feature

---

# 14. Noise Is Not Automatically an Attack

The AI must distinguish:

### Honest noise

Examples:

* Bit-flip noise
* Phase-flip noise
* Depolarizing noise
* Readout error
* Other configured channel imperfections

from:

### Deliberate attacks

Examples:

* Signature forgery
* Replay
* Impersonation
* Unauthorized verification
* Deliberate quantum-channel manipulation

A noisy legitimate execution should not automatically be classified as an attack.

The system therefore needs an:

> **Honest noisy baseline**

before meaningful anomaly thresholds are established.

---

# 15. Honest Baseline

The AI should support repeated honest executions under controlled conditions.

For example:

```text
Honest execution
Honest execution
Honest execution
...
Honest execution
```

Collect measurements and derive expected operating behavior.

Potential measurements include:

* X-basis probabilities
* Y-basis probabilities
* Z-basis probabilities
* Fidelity
* QBER/error rate
* Bell-state correlations
* Measurement distributions

The baseline should be represented statistically rather than as a single hard-coded expected value.

---

# 16. Threshold Rules

Thresholds must not be arbitrary.

Bad implementation:

```python
if fidelity < 0.8:
    attack = True
```

unless the value has a documented scientific/statistical justification.

A better approach is:

```text
Honest baseline
       ↓
Repeated measurements
       ↓
Mean
Variance
Standard deviation
Confidence interval / statistical bound
       ↓
Operating region
       ↓
Detection threshold
```

The exact statistical method must be documented in:

```text
MATHEMATICAL_MODEL.md
```

and/or

```text
SCIENTIFIC_RULES.md
```

---

# 17. Deterministic Decision Rule

Quantum measurements are inherently probabilistic.

However, once measurement data has been collected, the final security decision must be deterministic.

For example:

```text
Measurement data
       ↓
Calculate statistics
       ↓
Apply documented rules
       ↓
ACCEPT
SUSPICIOUS
or
ATTACK
```

Running the same decision engine on the same collected evidence must produce the same decision.

Do not use random classification.

Do not use probabilistic AI prediction.

---

# 18. Detection States

The system should support at least:

```text
ACCEPT
SUSPICIOUS
ATTACK
```

The exact boundaries must be defined by the statistical/security model.

The system should also provide an explanation such as:

```text
Decision: ATTACK

Evidence:
- Fidelity outside honest operating region
- X-basis distribution deviation
- Invalid session nonce
- Signature mismatch

Likely attack:
Forgery / Replay
```

The goal is explainable detection.

---

# 19. Attack Implementation Rule

Every attack must have a defined model.

Before implementing an attack, document:

```text
Attack name
Attacker capability
Attacker input
Attack mechanism
Affected layer
Expected quantum effect
Expected protocol effect
Evidence generated
Detection rule
Test cases
Limitations
```

---

# 20. Do Not Treat Every Attack as Quantum

Some attacks occur at the protocol layer.

### Quantum-layer examples

* Bit-flip manipulation
* Phase-flip manipulation
* Depolarizing channel manipulation
* Measurement/readout manipulation
* Other deliberate quantum-channel modifications

### Protocol-layer examples

* Replay
* Impersonation
* Unauthorized verification

### Signature-level examples

* Forgery
* Modified message/signature relationship

The AI must place attacks in the correct layer.

---

# 21. Forgery Probability

Forgery probability must be evaluated using measurement/statistical evidence.

The AI must not simply generate a random number and call it:

```text
forgery probability
```

The value must be derived from the defined experimental procedure.

The documentation must specify:

```text
Number of trials
Number of successful false acceptances
Acceptance rule
Empirical probability estimate
Uncertainty/statistical treatment
```

If a theoretical security bound is used, its assumptions must also be documented.

---

# 22. Verification Accuracy

The system must evaluate both:

### Legitimate acceptance

How often a legitimate signature is accepted.

### Malicious rejection

How often malicious attempts are rejected.

Useful metrics include:

```text
True acceptance rate
False rejection rate
False acceptance rate
Attack detection rate
Forging success rate
```

The AI should not report only a single "accuracy" number because security systems have asymmetric error types.

---

# 23. Information-Theoretic Security Rule

The AI must be extremely careful with the phrase:

> Information-theoretic security

The detector itself does NOT automatically create information-theoretic security.

Do not claim:

```text
Q-SHIELD guarantees information-theoretic security.
```

Instead, distinguish:

```text
QDS protocol
    ↓
Security assumptions / theoretical guarantees
    ↓
Q-SHIELD simulation
    ↓
Threat detection and experimental evaluation
```

The detector analyzes security-relevant evidence.

It does not replace the underlying QDS security proof.

---

# 24. Protocol Security Checks

The system should support protocol-level checks including, where applicable:

* Signer identity
* Verifier identity
* Session identifier
* Nonce
* Timestamp
* Authorization
* Replay history
* Message/signature association

These checks must be separated from quantum measurements.

Example:

```text
Quantum evidence
        +
Protocol evidence
        ↓
Evidence fusion
        ↓
Security decision
```

---

# 25. Evidence Fusion

The final detector should combine multiple forms of evidence where appropriate.

Example:

```text
Quantum evidence:
    Fidelity deviation
    QBER deviation
    X/Y/Z deviation
    Bell correlation deviation

Protocol evidence:
    Identity mismatch
    Invalid nonce
    Expired session
    Unauthorized verifier
    Replay detected

                    ↓

          Deterministic rule engine

                    ↓

             Security decision
```

The evidence fusion mechanism must be rule-based.

It must not be a machine-learning classifier.

---

# 26. Pauli Operators

The AI must correctly implement and document:

```text
X = [[0, 1],
     [1, 0]]

Y = [[0, -i],
     [i,  0]]

Z = [[1,  0],
     [0, -1]]
```

Important eigenstates should include:

### Z basis

```text
|0>
|1>
```

### X basis

```text
|+>
|->
```

### Y basis

```text
|+i>
|-i>
```

The AI must not confuse:

* computational basis
* X basis
* Y basis
* Z basis

---

# 27. Projective Measurement

Measurement must be understood through projectors and probabilities.

For a state:

```text
|ψ>
```

and projector:

```text
P
```

the probability of the corresponding outcome is:

```text
P(outcome) = <ψ|P|ψ>
```

The implementation must preserve the distinction between:

```text
Quantum state
Measurement probability
Individual measurement outcome
Aggregated measurement statistics
```

---

# 28. Bell-State Requirement

The system must explicitly simulate Bell-state entanglement.

The AI should support at least the standard Bell-state construction involving:

```text
|00>
    ↓
Hadamard on first qubit
    ↓
CNOT
    ↓
Bell state
```

Expected correlations must be tested.

Do not merely display a circuit diagram without verifying the resulting measurement statistics.

---

# 29. Teleportation Requirement

The teleportation implementation must demonstrate:

```text
Unknown state
        +
Bell pair
        ↓
Alice performs measurement
        ↓
Two classical bits
        ↓
Bob applies Pauli correction
        ↓
Recovered state
```

The AI must test that the corrected state corresponds to the intended input state within the limitations of the simulator/noise model.

---

# 30. Noise Modeling

Noise should be configurable.

Potential models include:

```text
Bit flip
Phase flip
Depolarizing
Readout error
Thermal relaxation
```

Not every model must be implemented immediately.

The AI should add models incrementally based on the development plan.

Noise parameters must be explicit and reproducible.

Example:

```text
noise_type = depolarizing
error_probability = p
shots = N
```

---

# 31. Reproducibility

Experiments should be reproducible wherever practical.

The AI should support:

* Explicit configuration
* Fixed random seeds where appropriate
* Recorded shot counts
* Recorded noise parameters
* Recorded attack parameters
* Recorded protocol parameters
* Experiment identifiers

A result should be traceable to the configuration that produced it.

---

# 32. Testing Requirement

Every meaningful module must have tests.

Examples:

```text
State preparation
    → state tests

Pauli operators
    → operator/eigenstate tests

Measurement
    → probability tests

Bell states
    → correlation tests

Teleportation
    → state-recovery tests

Noise
    → expected-noise-behavior tests

Statistics
    → known-distribution tests

Detection
    → acceptance/rejection tests

Replay
    → duplicate-session tests

Forgery
    → false-acceptance experiments
```

Do not consider a module complete merely because it runs.

---

# 33. Test Types

Use multiple levels of testing.

### Unit tests

Test individual functions/classes.

### Integration tests

Test multiple modules working together.

### Statistical tests

Verify expected distributions and statistical behavior.

### Security tests

Verify attacks are handled according to the defined threat model.

### Regression tests

Ensure later changes do not break completed milestones.

---

# 34. Edge Cases

The AI must consider edge cases.

Examples:

```text
0 shots
Very low shot count
Very high noise
Invalid state
Invalid message
Missing identity
Invalid nonce
Reused nonce
Expired session
Unauthorized verifier
Malformed signature
Unknown attack type
Missing baseline
Baseline with insufficient samples
Threshold boundary
```

Behavior for important edge cases must be deterministic and documented.

---

# 35. Dependency Management

Do not install libraries unnecessarily.

Use the smallest practical stack.

Primary direction:

```text
Python
Qiskit
Qiskit Aer
NumPy
SciPy
Pandas
Matplotlib
Streamlit
```

Additional dependencies require justification.

Do not add:

```text
TensorFlow
PyTorch
scikit-learn
```

for threat detection.

They are unnecessary and conflict with the project's no-ML requirement.

---

# 36. UI Development Rule

Do not build the dashboard before the core system works.

Correct order:

```text
Quantum core
    ↓
QDS model
    ↓
Statistics
    ↓
Detection
    ↓
Evaluation
    ↓
API/persistence if needed
    ↓
Dashboard
```

The UI should visualize working logic.

It must not contain the actual security logic in scattered UI callbacks.

---

# 37. Blockchain Development Rule

Blockchain is a later enhancement.

Do not introduce blockchain into the core verification mechanism before the core project is functional.

Correct order:

```text
Quantum simulation
        ↓
QDS verification
        ↓
Threat detection
        ↓
Security evaluation
        ↓
Dashboard
        ↓
Blockchain audit layer
```

Blockchain should primarily provide:

* Immutable audit records
* Verification event hashes
* Timestamped records
* Transaction references

It must not be presented as the mechanism that makes the quantum protocol secure.

---

# 38. Separation of Concerns

The AI must keep modules separate.

For example:

```text
src/
├── quantum/
├── qds/
├── noise/
├── statistics/
├── attacks/
├── detection/
├── evaluation/
└── utils/
```

Quantum simulation code should not contain UI logic.

UI code should not implement statistical security rules.

Detection code should not directly manipulate database internals.

Blockchain code should not determine whether a signature is mathematically valid.

---

# 39. Configuration Over Hard-Coding

Important parameters should be configurable.

Examples:

```text
shots
noise level
attack strength
baseline sample count
confidence level
threshold parameters
session duration
nonce policy
```

Avoid scattering constants throughout the codebase.

Every scientifically meaningful constant should have documentation explaining its purpose.

---

# 40. Logging

Important events should be logged where appropriate.

Examples:

```text
Verification started
Quantum circuit executed
Measurement completed
Statistics calculated
Baseline loaded
Threshold evaluated
Attack detected
Verification completed
```

Logs should help debug the system without exposing unnecessary sensitive information.

---

# 41. Error Handling

The AI must not hide errors.

Avoid:

```python
try:
    ...
except:
    pass
```

Errors should either:

* be handled explicitly, or
* be propagated with meaningful context.

Invalid inputs should produce clear errors.

---

# 42. Documentation Synchronization

When implementation changes an important design decision, documentation must be updated.

Examples:

If the acceptance rule changes:

```text
MATHEMATICAL_MODEL.md
SCIENTIFIC_RULES.md
```

may need updates.

If the threat model changes:

```text
THREAT_MODEL.md
SECURITY_MODEL.md
```

may need updates.

If architecture changes:

```text
ARCHITECTURE.md
```

must be updated.

The documentation and implementation must not contradict each other.

---

# 43. Progress Reporting

After completing a milestone/module, report:

```text
Milestone:
Status:

Implemented:
- ...

Files changed:
- ...

Concepts implemented:
- ...

Tests added:
- ...

Tests passed:
- ...

Experiments performed:
- ...

Known limitations:
- ...

Scientific assumptions:
- ...

Next milestone:
- ...
```

Then update:

```text
PROGRESS.md
```

---

# 44. Never Hide Limitations

The AI must explicitly identify limitations.

Examples:

```text
This is a simulation.
This is a qubit-level abstraction.
This is not a physical QDS deployment.
This threshold is experimentally calibrated.
This result is based on finite-shot simulation.
This attack model does not represent every real-world attack.
```

A limitation is better than an unsupported security claim.

---

# 45. Scientific Honesty

The AI must never optimize the implementation to produce impressive-looking results.

Do not:

* manipulate experiments to guarantee detection
* tune thresholds only on attack data
* hide false positives
* hide false negatives
* report only successful experiments
* claim security without evidence
* claim physical implementation when using simulation
* claim 100% detection
* claim 100% legitimate acceptance
* claim unconditional security from the detector

Experiments should report both successes and failures.

---

# 46. Statistical Integrity

When reporting experimental results, include enough information to interpret them.

At minimum, where applicable:

```text
Number of trials
Number of shots
Noise level
Attack type
Attack strength
Baseline parameters
Threshold parameters
Accepted samples
Rejected samples
False acceptances
False rejections
```

Do not report a percentage without explaining what it represents.

---

# 47. Security Decision Explainability

Every security decision should ideally be traceable to evidence.

Example:

```text
Decision: SUSPICIOUS

Reasons:
- Fidelity is outside the normal operating region.
- Z-basis error exceeded threshold.
- Protocol identity is valid.
- Nonce is valid.

Interpretation:
Possible quantum-channel disturbance.
```

The system should make it possible for a judge/developer to understand:

> **Why did the system make this decision?**

---

# 48. Attack Laboratory

The final application should provide an experimental environment where users can intentionally simulate attacks.

Possible controls:

```text
Attack type
Attack strength
Noise level
Number of shots
Number of trials
```

Possible outputs:

```text
Detection result
Quantum evidence
Protocol evidence
Statistical evidence
Detection rate
False acceptance rate
False rejection rate
Forging probability
```

The attack laboratory must use the same core detection engine as normal verification.

Do not create a separate fake detector for the UI.

---

# 49. Security Operating Region

Where useful, experiments should explore the relationship between:

```text
Noise
        vs
Detection reliability
```

For example:

```text
Low noise
    → strong separation

Moderate noise
    → reduced separation

High noise
    → legitimate/attack distributions may overlap
```

The AI should not assume that detection remains perfect as noise increases.

This analysis is scientifically important.

---

# 50. Quantum Integrity Fingerprint

Q-SHIELD may use the concept of a:

> **Noise-Calibrated Quantum Integrity Fingerprint**

This means representing expected legitimate behavior using measurable quantum/statistical characteristics.

Possible components:

```text
X-basis statistics
Y-basis statistics
Z-basis statistics
Fidelity
QBER
Bell correlations
```

The fingerprint should be calibrated from legitimate executions.

It must not be presented as a cryptographic hash unless it actually is one.

The word "fingerprint" refers to a statistical behavior profile.

---

# 51. Multi-Layer Security Evidence

The project may combine:

```text
Quantum evidence
+
Protocol evidence
+
Statistical evidence
```

into an explainable deterministic decision.

Example:

```text
Quantum:
    Fidelity abnormal
    X-basis deviation

Protocol:
    Valid identity
    Valid nonce

Statistical:
    Outside honest confidence region

Result:
    SUSPICIOUS

Likely cause:
    Quantum-channel disturbance
```

The evidence must remain inspectable.

---

# 52. Do Not Over-Engineer

The project is a prototype.

Avoid unnecessary complexity such as:

* Microservices
* Kubernetes
* Distributed infrastructure
* Complex cloud deployment
* Large authentication systems
* Unnecessary databases
* Unnecessary APIs
* Complex blockchain architecture

Build what is required to demonstrate the core idea.

---

# 53. Prototype First

When choosing between:

```text
Complex theoretically complete system
```

and

```text
Small scientifically defensible prototype
```

prefer the scientifically defensible prototype.

The project must demonstrate:

```text
Quantum protocol
+
Threat simulation
+
Measurement statistics
+
Statistical detection
+
Explainable security decision
```

before adding advanced infrastructure.

---

# 54. Required Development Order

The preferred order is:

```text
M0  Environment
 ↓
M1  Qubit fundamentals
 ↓
M2  Pauli operators
 ↓
M3  Projective measurement
 ↓
M4  Bell states
 ↓
M5  Teleportation
 ↓
M6  Noise
 ↓
M7  QDS protocol specification
 ↓
M8  Quantum signature verification
 ↓
M9  Honest baseline
 ↓
M10 Statistical threshold engine
 ↓
M11 Forgery
 ↓
M12 Replay
 ↓
M13 Impersonation
 ↓
M14 Unauthorized verification
 ↓
M15 Quantum channel attacks
 ↓
M16 Evidence fusion
 ↓
M17 Security evaluation
 ↓
M18 Performance evaluation
 ↓
M19 Dashboard
 ↓
M20 Blockchain audit
```

Do not skip directly to M19 because the dashboard looks impressive.

---

# 55. Definition of "Done"

A module is not complete simply because its code executes.

A module is complete when:

```text
Implementation exists
        +
Tests exist
        +
Tests pass
        +
Expected behavior is demonstrated
        +
Edge cases are considered
        +
Documentation is updated
        +
No project requirement is violated
```

---

# 56. Module Completion Checklist

Before marking a module complete, ask:

### Understanding

* Do we understand what the module does?
* Can the team explain it?

### Implementation

* Is the implementation modular?
* Are inputs and outputs clear?

### Scientific correctness

* Are equations correct?
* Are quantum operations correct?
* Are assumptions documented?

### Security

* Does it respect the threat model?
* Does it avoid unsupported security claims?

### Testing

* Are unit tests present?
* Are important edge cases tested?
* Are expected results verified?

### Reproducibility

* Are important parameters recorded?

### Documentation

* Are relevant `.md` files updated?

### Integration

* Does it work with previously completed modules?

Only then should the milestone be marked complete.

---

# 57. Critical STOP Rule

The following rule overrides the desire to keep coding:

> **If a scientific or protocol decision required for implementation is not defined, stop implementing that portion and report the missing decision.**

Do not invent a protocol.

Do not invent a security assumption.

Do not invent a threshold.

Do not invent a QDS verification procedure.

Do not silently replace the project's intended model with an easier unrelated model.

Ask for clarification or propose documented alternatives.

---

# 58. AI Response Format During Development

When working interactively with the team, the AI should preferably structure substantial implementation responses as:

```text
## Current Milestone

## What We Are Implementing

## Why It Is Needed

## Scientific / Technical Concept

## Design

## Implementation

## Tests

## Test Results

## Limitations

## Documentation Updated

## Next Step
```

Keep explanations understandable to beginners while maintaining technical accuracy.

---

# 59. Final Priority Order

When multiple goals conflict, use this priority order:

```text
1. Scientific correctness
2. SIH requirement compliance
3. Security correctness
4. Testability
5. Understandability
6. Reproducibility
7. Explainability
8. Performance
9. UI quality
10. Extra features
```

A visually impressive feature must never be allowed to compromise scientific correctness.

---

# 60. Final Rule

The most important principle for every AI-assisted change to Q-SHIELD is:

> **Build less, understand more, test everything, and never invent security claims.**

Q-SHIELD should be a project that the team can confidently demonstrate and explain—not merely a project that happens to run.
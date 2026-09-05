# Q-SHIELD — Development Plan

## 1. Purpose

This document defines the incremental development roadmap for Q-SHIELD.

The project will be developed using a divide-and-conquer approach.

The complete system must NOT be implemented in one step.

Each milestone must be:

```text
Understood
→ Designed
→ Implemented
→ Tested
→ Experimentally Verified
→ Documented
→ Marked Complete
```

Only after a milestone is stable should development move to the next milestone.

---

# 2. Development Philosophy

The development strategy is:

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
Update PROGRESS.md
    ↓
Next Milestone
```

The project must avoid:

```text
Prompt AI
    ↓
Generate hundreds of lines
    ↓
Hope it works
```

---

# 3. Development Priorities

The order of priorities is:

1. Scientific correctness
2. Core quantum functionality
3. Correct QDS abstraction
4. Statistical verification
5. Threat detection
6. Security evaluation
7. Performance evaluation
8. Dashboard
9. Persistence
10. Blockchain audit

Visual features must never take priority over core correctness.

---

# 4. Milestone Overview

| Milestone | Name                           | Priority      | Status      |
| --------- | ------------------------------ | ------------- | ----------- |
| M0        | Environment Setup              | MUST          | NOT STARTED |
| M1        | Qubit Fundamentals             | MUST          | NOT STARTED |
| M2        | Pauli Operators                | MUST          | NOT STARTED |
| M3        | Projective Measurement         | MUST          | NOT STARTED |
| M4        | Bell States                    | MUST          | NOT STARTED |
| M5        | Quantum Teleportation          | MUST          | NOT STARTED |
| M6        | Noise Models                   | MUST          | NOT STARTED |
| M7        | QDS Protocol Specification     | MUST          | NOT STARTED |
| M8        | Quantum Signature Verification | MUST          | NOT STARTED |
| M9        | Honest Baseline                | MUST          | NOT STARTED |
| M10       | Statistical Threshold Engine   | MUST          | NOT STARTED |
| M11       | Forgery Detection              | MUST          | NOT STARTED |
| M12       | Replay Detection               | MUST          | NOT STARTED |
| M13       | Impersonation Detection        | MUST          | NOT STARTED |
| M14       | Unauthorized Verification      | MUST          | NOT STARTED |
| M15       | Quantum Channel Attacks        | MUST          | NOT STARTED |
| M16       | Evidence Fusion                | MUST          | NOT STARTED |
| M17       | Security Evaluation            | MUST          | NOT STARTED |
| M18       | Performance Evaluation         | SHOULD        | NOT STARTED |
| M19       | Dashboard                      | SHOULD        | NOT STARTED |
| M20       | Blockchain Audit               | OPTIONAL/LATE | NOT STARTED |

---

# 5. M0 — Environment Setup

## Objective

Prepare the Python development environment and verify the quantum-computing stack.

## Tasks

1. Verify Python installation.
2. Create a virtual environment.
3. Activate the virtual environment.
4. Install only the required initial dependencies.
5. Verify Qiskit installation.
6. Verify Qiskit Aer installation.
7. Verify NumPy.
8. Verify SciPy.
9. Verify Pandas.
10. Verify Matplotlib.
11. Run a minimal quantum circuit.
12. Confirm that the simulator executes successfully.
13. Create the initial project structure if required.

## Initial Technology

```text
Python
Qiskit
Qiskit Aer
NumPy
SciPy
Pandas
Matplotlib
```

Streamlit should be installed when dashboard development begins unless needed earlier for environment verification.

## Deliverables

```text
Working Python environment
requirements.txt
Minimal quantum execution
Updated PROGRESS.md
```

## Restrictions

Do NOT implement:

* QDS
* Teleportation
* Attacks
* Detection
* Dashboard
* Blockchain

## Completion Criteria

M0 is complete when:

```text
Python works
+
Virtual environment works
+
Qiskit works
+
Aer simulator works
+
Minimal circuit executes
+
Dependencies are recorded
```

---

# 6. M1 — Qubit Fundamentals

## Objective

Understand and implement basic qubit state preparation and measurement.

## Concepts

* Classical bit
* Qubit
* Computational basis
* State vector
* Superposition
* Measurement
* Probability
* Shots

## Required States

```text
|0>
|1>
|+>
|->
|+i>
|-i>
```

## Planned Module

```text
src/quantum/states.py
```

and, if necessary:

```text
src/quantum/measurements.py
```

## Tests

Verify:

* `|0>` behaves as expected.
* `|1>` behaves as expected.
* `|+>` produces approximately equal computational-basis outcomes.
* `|->` produces approximately equal computational-basis outcomes.
* Y-basis states are represented correctly.

## Experiment

Run each supported state over multiple shots and compare empirical frequencies with theoretical probabilities.

## Completion Criteria

M1 is complete when state preparation and basic measurement are tested and understood.

---

# 7. M2 — Pauli Operators

## Objective

Implement and verify Pauli X, Y and Z operations.

## Operators

```text
X = [[0, 1],
     [1, 0]]

Y = [[0, -i],
     [i,  0]]

Z = [[1,  0],
     [0, -1]]
```

## Required Behaviour

```text
X|0> = |1>
X|1> = |0>

Z|0> = |0>
Z|1> = -|1>
```

Y behaviour must be verified using the correct complex-valued representation.

## Planned Module

```text
src/quantum/pauli.py
```

## Tests

* Matrix/operator correctness
* State transformation
* Eigenstate behaviour
* Numerical tolerance handling

## Experiment

Prepare Pauli eigenstates and verify their expected measurement behaviour.

---

# 8. M3 — Projective Measurement

## Objective

Implement and understand projective measurement and empirical measurement statistics.

## Concepts

* Projector
* Born rule
* Measurement basis
* Outcome probability
* Empirical probability
* Shot count

## Mathematical Model

For projector `P_i`:

```text
P(i) = <ψ|P_i|ψ>
```

Empirical probability:

```text
p_hat_i = n_i / N
```

## Tasks

1. Define measurement bases.
2. Implement basis transformations where required.
3. Execute measurements.
4. Collect counts.
5. Convert counts to probabilities.
6. Compare empirical and theoretical values.

## Tests

Test:

* Computational basis
* X basis
* Y basis
* Multiple shot counts

## Completion Criteria

M3 is complete when the project can reliably compare theoretical and simulated measurement probabilities.

---

# 9. M4 — Bell States

## Objective

Create and verify Bell-state entanglement.

## Primary State

```text
|Phi+> = (|00> + |11>) / sqrt(2)
```

## Optional Additional States

```text
|Phi->
|Psi+>
|Psi->
```

Additional states should only be implemented if useful.

## Planned Module

```text
src/quantum/bell.py
```

## Tasks

1. Create Bell-state circuit.
2. Simulate the circuit.
3. Measure both qubits.
4. Analyze correlations.
5. Compare results with theoretical expectations.

## Expected Correlation

For `|Phi+>` measured in the computational basis:

```text
00
11
```

should dominate, within statistical variation.

## Tests

* Circuit construction
* State preparation
* Correlation behaviour
* Statistical tolerance

## Experiment

Record measurement counts and demonstrate Bell-state correlation.

---

# 10. M5 — Quantum Teleportation

## Objective

Implement complete quantum teleportation.

## Required Pipeline

```text
Input Qubit
     ↓
Shared Bell Pair
     ↓
Alice Bell Measurement
     ↓
Classical Measurement Results
     ↓
Bob Pauli Correction
     ↓
Recovered State
```

## Required Corrections

The exact correction mapping depends on the chosen circuit convention.

The implementation must explicitly document the convention used.

A common mapping is:

```text
00 → I
01 → X
10 → Z
11 → XZ
```

The implementation must verify that its classical-bit ordering matches the mapping.

## Planned Module

```text
src/quantum/teleportation.py
```

## Tests

Teleport representative input states:

```text
|0>
|1>
|+>
|->
|+i>
|-i>
```

and verify the recovered output statistically.

## Experiment

Compare input and recovered-state behaviour.

## Completion Criteria

M5 is complete only when teleportation works for multiple states and the Pauli corrections are demonstrably correct.

---

# 11. M6 — Noise Models

## Objective

Introduce controlled quantum noise.

## Initial Models

```text
Bit-flip
Phase-flip
Depolarizing
Readout error
```

Additional models may be added later if justified.

## Planned Module

```text
src/noise/
```

## Tasks

1. Create configurable noise models.
2. Apply noise to quantum circuits.
3. Vary noise strength.
4. Measure its effect.
5. Record changes in statistics.

## Important Principle

```text
Noise ≠ Attack
```

Noise represents expected or controlled imperfections.

Attacks represent malicious actions.

## Experiments

Run:

```text
No noise
Low noise
Medium noise
High noise
```

and compare:

* Measurement distributions
* Fidelity
* QBER where applicable
* Bell correlation

## Completion Criteria

M6 is complete when noise can be introduced reproducibly and its statistical effect is measurable.

---

# 12. M7 — QDS Protocol Specification

## Objective

Finalize the exact QDS-inspired protocol abstraction before implementing the security layer.

## Critical Status

This milestone is a **scientific design milestone**, not simply a coding milestone.

## Must Define

1. Alice's role
2. Bob's role
3. Eve's role
4. Message representation
5. Signature representation
6. Quantum state representation
7. State preparation process
8. Teleportation role
9. Bell-state role
10. Measurement basis
11. Verification procedure
12. Valid signature conditions
13. Forgery model
14. Security assumptions
15. Protocol metadata
16. Nonce/session mechanism
17. Relationship to published QDS work
18. Simplifications made for the prototype

## Main Document

```text
QDS_PROTOCOL.md
```

## Critical Rule

If any of the above decisions remain undefined, implementation of the final QDS layer must stop.

The AI coding agent must not invent a protocol.

## Completion Criteria

M7 is complete only when the team has an explicit, documented and internally consistent protocol specification.

---

# 13. M8 — Quantum Signature Verification

## Objective

Connect the QDS abstraction to the working quantum teleportation engine.

## Pipeline

```text
Message
   ↓
Signature Representation
   ↓
Quantum State
   ↓
Bell Pair
   ↓
Teleportation
   ↓
Pauli Correction
   ↓
Measurement
   ↓
Verification Metrics
```

## Tasks

1. Create valid signature representation.
2. Generate corresponding quantum state.
3. Perform teleportation.
4. Apply correction.
5. Measure output.
6. Calculate verification metrics.
7. Compare expected and observed behaviour.

## Tests

* Valid signature
* Modified message
* Modified signature
* Mismatched signature
* Invalid state

## Completion Criteria

A complete legitimate quantum verification path works.

---

# 14. M9 — Honest Baseline

## Objective

Establish expected legitimate behaviour under defined conditions.

## Concept

```text
Honest Executions
       ↓
Repeated Measurements
       ↓
Statistics
       ↓
Baseline
```

## Baseline Parameters

Potential parameters:

```text
Input state
Measurement basis
Noise model
Noise strength
Shots
Trials
```

## Baseline Statistics

Depending on the selected metric:

```text
Mean
Variance
Standard deviation
Confidence interval
Expected distribution
Fidelity
QBER
Bell correlation
```

## Tasks

1. Define baseline configuration.
2. Run repeated honest trials.
3. Collect statistics.
4. Calculate baseline.
5. Store baseline.
6. Make baseline reproducible.

## Important

A baseline must be associated with the conditions under which it was generated.

A baseline generated under zero noise should not automatically be used to judge a system configured with high noise.

---

# 15. M10 — Statistical Threshold Engine

## Objective

Build deterministic mathematical rules for evaluating verification evidence.

## Inputs

```text
Observed statistics
Baseline statistics
Noise configuration
Protocol evidence
Threshold configuration
```

## Outputs

```text
PASS
FAIL
SUSPICIOUS
```

or an internal representation that is later converted into:

```text
ACCEPT
SUSPICIOUS
ATTACK
```

## Possible Statistical Methods

Depending on scientific justification:

* Confidence intervals
* Standard deviation bounds
* Hypothesis-test concepts
* Probability deviation
* Fidelity thresholds
* QBER thresholds
* Distribution comparisons

## Important Rule

Thresholds must not be arbitrary.

Every threshold must have:

```text
Value
Meaning
Derivation
Applicable configuration
Statistical interpretation
```

## Tests

Test:

* Clearly valid samples
* Borderline samples
* Clearly abnormal samples
* Small and large shot counts

---

# 16. M11 — Forgery Detection

## Objective

Simulate forged signatures and evaluate whether the detector rejects them.

## Attack

Eve attempts to produce a signature/message combination that should not be accepted as legitimate.

## Tasks

1. Define forgery strategy.
2. Generate forged signatures.
3. Run verification.
4. Collect measurement statistics.
5. Compare against baseline.
6. Produce security decision.
7. Repeat over many trials.

## Metrics

```text
Forged attempts
Accepted forged attempts
Rejected forged attempts
Empirical forgery probability
Detection rate
FAR
```

## Empirical Forgery Probability

```text
P_forge ≈
accepted forged attempts
------------------------
total forged attempts
```

This is an experimental estimate, not an absolute theoretical security guarantee.

---

# 17. M12 — Replay Detection

## Objective

Detect reuse of a previously valid signed request.

## Required Protocol Evidence

At least one or more of:

```text
Nonce
Session ID
Timestamp
Previously-used request identifier
```

## Flow

```text
Valid Request
     ↓
Stored / Observed
     ↓
Same Request Reused
     ↓
Replay Check
     ↓
REJECT / ATTACK
```

## Important

A replay attack may preserve perfectly valid quantum statistics.

Therefore replay detection must not depend entirely on quantum measurements.

---

# 18. M13 — Impersonation Detection

## Objective

Detect an attacker claiming to be the legitimate signer.

## Evidence

Possible evidence:

```text
Signer identity
Authentication context
Authorization
Session information
Signature ownership
```

## Tasks

1. Define legitimate identity.
2. Define attacker identity.
3. Simulate mismatch.
4. Execute verification.
5. Produce deterministic decision.

---

# 19. M14 — Unauthorized Verification

## Objective

Detect attempts by unauthorized entities to perform verification.

## Required Information

```text
Verifier identity
Authorization status
Session
Access policy
```

## Test Cases

```text
Authorized Bob
Unauthorized Eve
Invalid session
Expired authorization
```

## Expected Behaviour

Authorized verifier:

```text
Allowed to proceed
```

Unauthorized verifier:

```text
Rejected
```

---

# 20. M15 — Quantum Channel Attacks

## Objective

Simulate malicious manipulation of the quantum communication channel.

## Initial Attack Operations

```text
X
Y
Z
```

## Additional Disturbance Models

```text
Bit flip
Phase flip
Depolarizing disturbance
Readout manipulation/error
```

## Attack Strength

The experiment should support configurable attack strength where technically meaningful.

For example:

```text
Low
Medium
High
```

or a continuous parameter.

The exact parameterization must be documented.

## Metrics

Measure effects on:

* Measurement statistics
* Fidelity
* QBER
* Bell correlations
* Acceptance probability
* Detection rate

## Experiments

```text
Attack strength vs detection rate
Attack strength vs fidelity
Attack strength vs QBER
Attack strength vs acceptance rate
```

---

# 21. M16 — Evidence Fusion

## Objective

Combine quantum, statistical and protocol evidence into a single deterministic security decision.

## Inputs

### Quantum Evidence

```text
Measurement statistics
Fidelity
QBER
Bell correlation
Deviation
```

### Protocol Evidence

```text
Identity
Session
Nonce
Timestamp
Authorization
Replay state
```

### Statistical Evidence

```text
Baseline
Threshold
Confidence region
Deviation
```

## Output

```text
Decision
Attack Type
Evidence
Reason
```

## Example

```text
Quantum:
PASS

Protocol:
FAIL

Reason:
Nonce already used.

Decision:
ATTACK

Attack Type:
REPLAY
```

Another example:

```text
Quantum:
FAIL

Protocol:
PASS

Reason:
Observed quantum statistics fall outside
the calibrated honest operating region.

Decision:
SUSPICIOUS / ATTACK
```

The exact policy must be documented.

---

# 22. M17 — Security Evaluation

## Objective

Evaluate the complete detector quantitatively.

## Required Metrics

### Legitimate Traffic

```text
Legitimate acceptance rate
False rejection rate
```

### Malicious Traffic

```text
False acceptance rate
Detection rate
```

### Forgery

```text
Empirical forgery probability
```

### Attack-Specific

```text
Replay detection rate
Impersonation detection rate
Unauthorized verification rejection rate
Channel attack detection rate
```

## Required Experiments

At minimum:

```text
Honest baseline
Forgery
Replay
Impersonation
Unauthorized verification
Channel manipulation
```

---

# 23. M18 — Performance Evaluation

## Objective

Measure the computational cost of the system.

## Metrics

Record:

```text
Number of qubits
Gate count
Circuit depth
Shots
Simulation time
Verification time
Statistical processing time
Total latency
Memory usage
```

## Shot Configurations

At minimum test:

```text
100
500
1000
4096
8192
```

## Output

Create performance tables and graphs.

The project must report measured performance rather than making unsupported efficiency claims.

---

# 24. M19 — Dashboard

## Objective

Build the user-facing Streamlit application after the core engine is stable.

## Dashboard Pages

### Page 1 — Dashboard

Display:

```text
Total verifications
Accepted
Suspicious
Attacks
Current noise configuration
Recent verification events
```

---

### Page 2 — Signature Verification

Inputs:

```text
Signer
Verifier
Message
Signature
Session
Nonce
Noise
Shots
```

Output:

```text
Decision
Attack type
Quantum metrics
Protocol checks
Statistical evidence
Explanation
```

---

### Page 3 — Quantum Monitor

Display:

```text
Bell circuit
Teleportation circuit
Pauli corrections
Measurement histogram
X/Y/Z statistics
Fidelity
QBER
Bell correlations
```

---

### Page 4 — Attack Laboratory

Allow selection of:

```text
Forgery
Replay
Impersonation
Unauthorized verification
Quantum-channel manipulation
```

Allow configuration of:

```text
Attack strength
Noise
Shots
Trials
```

Display experimental results.

---

### Page 5 — Security Analytics

Display:

```text
Baseline
Thresholds
FAR
FRR
Detection rate
Forgery probability
Noise vs detection
Attack strength vs detection
Shots vs stability
```

---

### Page 6 — Verification History

Display:

```text
Timestamp
Signer
Verifier
Message hash
Decision
Attack type
Key metrics
```

---

# 25. M20 — Blockchain Audit Layer

## Objective

Add an optional tamper-evident audit mechanism.

## Prerequisite

All core milestones must be stable.

Blockchain must not be started simply because it is visually attractive for the final demo.

## Flow

```text
Verification Result
      ↓
Audit Record
      ↓
Hash
      ↓
Blockchain Transaction
      ↓
Transaction Reference
```

## Possible Technology

A local Ethereum-compatible development environment may be used.

Possible components include:

```text
Hardhat / Anvil
Solidity
Web3 library
```

The final choice must be made when M20 begins.

## Blockchain Record

Potential fields:

```text
Verification ID
Message hash
Decision
Attack type
Timestamp
Evidence hash
```

The exact schema will be decided later.

---

# 26. Dependency Installation Strategy

Do not install every possible dependency at M0.

### Initial

```text
Python
Qiskit
Qiskit Aer
NumPy
SciPy
Pandas
Matplotlib
```

### Dashboard Stage

```text
Streamlit
```

### Persistence Stage

Use Python's SQLite support or the selected database library only if necessary.

### Blockchain Stage

Install blockchain dependencies only when M20 starts.

---

# 27. Documentation Strategy

Documentation must evolve with implementation.

At minimum:

```text
PROJECT_CONTEXT.md
REQUIREMENTS.md
ARCHITECTURE.md
DEVELOPMENT_PLAN.md
AI_INSTRUCTIONS.md
SCIENTIFIC_RULES.md
THREAT_MODEL.md
QDS_PROTOCOL.md
MATHEMATICAL_MODEL.md
SECURITY_MODEL.md
TESTING_STRATEGY.md
EXPERIMENT_PLAN.md
PERFORMANCE_PLAN.md
DECISIONS.md
PROGRESS.md
GLOSSARY.md
```

Relevant documents must be updated whenever a scientific or architectural decision changes.

---

# 28. Module Completion Protocol

After every milestone, the developer/AI agent must report:

```text
Milestone:
M#

Status:
COMPLETE / BLOCKED / PARTIAL

Implemented:
...

Files Created/Modified:
...

Concepts Learned:
...

Tests Added:
...

Tests Passed:
...

Experiments Run:
...

Results:
...

Limitations:
...

Documentation Updated:
...

Next Milestone:
...
```

This report should be recorded in `PROGRESS.md` where appropriate.

---

# 29. Scientific Decision Protocol

If a scientific or security decision is undefined:

```text
STOP
```

Do not invent the decision.

Instead report:

```text
Missing decision:
...

Why it matters:
...

Possible options:
...

Recommended option:
...

Required documentation:
...
```

The team must decide before implementation continues.

---

# 30. Testing Strategy During Development

Every milestone must contain appropriate tests.

### Quantum Modules

Test:

```text
State preparation
Operators
Measurements
Bell correlations
Teleportation
```

### Noise

Test:

```text
No noise
Low noise
Medium noise
High noise
```

### Statistics

Test:

```text
Probability conversion
Mean
Variance
Confidence intervals
Threshold behaviour
```

### Security

Test:

```text
Valid signature
Forgery
Replay
Impersonation
Unauthorized verification
Channel manipulation
```

### Integration

Test:

```text
End-to-end legitimate verification
End-to-end attack verification
```

---

# 31. Experimental Development Strategy

Experiments must be developed progressively.

### Quantum Experiments

```text
E01 Bell state
E02 Teleportation
E03 Teleportation + noise
```

### Baseline Experiments

```text
E04 Honest baseline
E05 Threshold calibration
```

### Attack Experiments

```text
E06 Forgery
E07 Replay
E08 Impersonation
E09 Unauthorized verification
E10 Quantum channel manipulation
```

### Evaluation Experiments

```text
E11 FAR/FRR
E12 Detection probability
E13 Shots vs stability
E14 Noise vs false rejection
E15 Attack strength vs detection
E16 Performance
```

---

# 32. Recommended Development Order for the Team

The team should learn and implement in this order:

```text
1. Qubit
2. Measurement
3. Pauli operators
4. Bell states
5. Teleportation
6. Noise
7. QDS protocol
8. Signature verification
9. Statistics
10. Baseline
11. Thresholds
12. Forgery
13. Replay
14. Impersonation
15. Unauthorized verification
16. Channel attacks
17. Evidence fusion
18. Evaluation
19. Dashboard
20. Blockchain
```

Do not skip directly from basic Qiskit to blockchain.

---

# 33. Minimum Demo Milestone

Before the dashboard is started, the system should be able to demonstrate:

```text
Valid Signature
     ↓
Quantum State
     ↓
Bell State
     ↓
Teleportation
     ↓
Pauli Correction
     ↓
Measurement
     ↓
Statistics
     ↓
Baseline
     ↓
Threshold
     ↓
ACCEPT
```

and at least one malicious scenario:

```text
Attack
     ↓
Modified Quantum / Protocol Evidence
     ↓
Statistical / Rule-Based Detection
     ↓
ATTACK
```

---

# 34. Final Demo Target

The final demonstration should ideally show:

### Scenario A — Legitimate

```text
Alice signs
↓
Bob verifies
↓
Quantum verification succeeds
↓
Statistics match honest baseline
↓
ACCEPT
```

### Scenario B — Forgery

```text
Eve modifies/forges signature
↓
Verification
↓
Statistics deviate
↓
Forgery evidence
↓
ATTACK / SUSPICIOUS
```

### Scenario C — Replay

```text
Previously valid request
↓
Eve resubmits
↓
Nonce/session check fails
↓
REPLAY
↓
ATTACK
```

### Scenario D — Channel Manipulation

```text
Quantum state
↓
Eve introduces X/Y/Z disturbance
↓
Measurement statistics change
↓
Fidelity/QBER/correlation deviation
↓
ATTACK / SUSPICIOUS
```

---

# 35. Definition of Project Completion

The core project is considered complete when:

```text
Qubit simulation
        +
Pauli operations
        +
Projective measurement
        +
Bell entanglement
        +
Quantum teleportation
        +
Pauli correction
        +
Noise simulation
        +
QDS-inspired verification
        +
Honest baseline
        +
Statistical thresholds
        +
Forgery detection
        +
Replay detection
        +
Impersonation detection
        +
Unauthorized verification
        +
Quantum-channel attack detection
        +
Evidence fusion
        +
Security evaluation
        +
Performance evaluation
```

are working, tested and documented.

The dashboard and blockchain are enhancements after this core is functional.

---

# 36. Final Development Rule

The project must always prefer:

```text
Small correct module
```

over:

```text
Large unfinished system
```

and:

```text
Scientifically justified simplification
```

over:

```text
Impressive but unsupported claim
```

The goal is not merely to produce a working application.

The goal is to produce a **working, explainable, reproducible and scientifically defensible prototype**.
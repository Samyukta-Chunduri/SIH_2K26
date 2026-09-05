# Q-SHIELD — Testing Strategy

## 1. Purpose

This document defines how Q-SHIELD will be tested throughout development.

The testing strategy covers:

* Quantum-state preparation
* Pauli operations
* Projective measurements
* Bell-state generation
* Quantum teleportation
* Pauli corrections
* Noise simulation
* Quantum signature verification
* Honest baseline calibration
* Statistical calculations
* Threshold detection
* Forgery detection
* Replay detection
* Impersonation detection
* Unauthorized verification detection
* Quantum-channel attack detection
* Evidence fusion
* Deterministic decisions
* Security metrics
* Performance
* End-to-end behaviour

The primary goal is:

> Every important security or quantum claim made by Q-SHIELD must be supported by a reproducible test.

---

# 2. Testing Principles

Q-SHIELD follows these principles:

1. Test every module independently before integration.
2. Test mathematical functions against known results.
3. Test ideal quantum behaviour before introducing noise.
4. Test honest noisy behaviour before testing attacks.
5. Test each attack independently before combining attacks.
6. Test expected failures as carefully as expected successes.
7. Never use attack-generated data to silently calibrate the honest baseline.
8. Do not use machine learning for testing or detection.
9. Use deterministic random seeds where randomness is required for reproducibility.
10. Record the configuration used for important experiments.
11. Test both normal and edge cases.
12. Never declare a security feature complete because it "works once."

---

# 3. Testing Pyramid

The project should use multiple testing levels.

```text
                    ┌───────────────┐
                    │ End-to-End    │
                    │ Tests         │
                    └───────┬───────┘
                            │
                    ┌───────▼───────┐
                    │ Integration   │
                    │ Tests         │
                    └───────┬───────┘
                            │
                 ┌──────────▼──────────┐
                 │ Component / Module  │
                 │ Tests               │
                 └──────────┬──────────┘
                            │
                ┌───────────▼───────────┐
                │ Unit + Mathematical   │
                │ Tests                  │
                └────────────────────────┘
```

All four levels are required.

---

# 4. Test Categories

Q-SHIELD will use:

```text
1. Unit tests
2. Mathematical correctness tests
3. Quantum correctness tests
4. Statistical tests
5. Integration tests
6. Security tests
7. Attack simulation tests
8. Regression tests
9. Performance tests
10. End-to-end tests
```

---

# 5. Unit Testing

Unit tests verify individual functions independently.

Examples:

```text
prepare_state()
apply_pauli_x()
apply_pauli_y()
apply_pauli_z()
measure_state()
calculate_probability()
calculate_qber()
calculate_fidelity()
calculate_baseline()
evaluate_threshold()
detect_replay()
validate_identity()
validate_authorization()
```

A unit test should have:

```text
Input
Expected output
Actual output
Pass/fail result
```

---

# 6. Test Naming Convention

Test names should describe behaviour.

Preferred:

```text
test_pauli_x_flips_zero_to_one()
test_bell_state_has_expected_measurement_distribution()
test_replay_nonce_is_rejected()
test_legitimate_signature_is_accepted()
test_forged_signature_is_rejected()
```

Avoid vague names such as:

```text
test_quantum()
test_security()
test_function1()
```

---

# 7. Test Directory

Tests should eventually be organized approximately as:

```text
tests/
├── quantum/
│   ├── test_states.py
│   ├── test_pauli.py
│   ├── test_measurement.py
│   ├── test_bell.py
│   └── test_teleportation.py
│
├── noise/
│   └── test_noise_models.py
│
├── qds/
│   ├── test_protocol.py
│   └── test_verification.py
│
├── statistics/
│   ├── test_probabilities.py
│   ├── test_metrics.py
│   └── test_baseline.py
│
├── attacks/
│   ├── test_forgery.py
│   ├── test_replay.py
│   ├── test_impersonation.py
│   ├── test_authorization.py
│   └── test_channel_attacks.py
│
├── detection/
│   ├── test_thresholds.py
│   ├── test_evidence.py
│   └── test_decision_engine.py
│
└── integration/
    └── test_end_to_end.py
```

The exact structure may evolve.

---

# 8. Quantum Testing Philosophy

Quantum modules should first be tested against ideal theoretical behaviour.

The development order should be:

```text
Ideal state
    ↓
Ideal operation
    ↓
Ideal measurement
    ↓
Expected statistics
    ↓
Noise
    ↓
Attack
```

Do not introduce noise and attacks before proving that the ideal implementation works.

---

# 9. Qubit State Tests

Test all six Pauli eigenstates.

Required states:

```text
|0>
|1>
|+>
|->
|+i>
|-i>
```

For each state verify:

* Correct state vector or circuit representation.
* Normalization.
* Expected basis measurement behaviour.

---

# 10. Normalization Test

For a state:

$$
|\psi\rangle=\alpha|0\rangle+\beta|1\rangle
$$

verify:

$$
|\alpha|^2+|\beta|^2=1
$$

within an appropriate numerical tolerance.

A state that violates normalization should not silently pass validation.

---

# 11. Pauli-X Tests

Verify:

$$
X|0\rangle=|1\rangle
$$

and:

$$
X|1\rangle=|0\rangle
$$

The test should also verify the effect on relevant superposition states.

---

# 12. Pauli-Y Tests

Verify the mathematical action of:

$$
Y=
\begin{bmatrix}
0&-i\\
i&0
\end{bmatrix}
$$

including the complex phase.

Do not test only measurement probabilities because some phase differences may not be visible in a single measurement basis.

---

# 13. Pauli-Z Tests

Verify:

$$
Z|0\rangle=|0\rangle
$$

and:

$$
Z|1\rangle=-|1\rangle
$$

The relative phase must be preserved correctly.

---

# 14. Pauli Eigenstate Tests

For each eigenstate, verify the expected eigenvalue.

Examples:

```text
X|+>  = +|+>
X|->  = -|->

Y|+i> = +|+i>
Y|-i> = -|-i>

Z|0>  = +|0>
Z|1>  = -|1>
```

Numerical tolerance must be used for floating-point comparisons.

---

# 15. Projective Measurement Tests

For each eigenstate, measure in its corresponding basis.

Expected behaviour:

```text
|0>   measured in Z → 0
|1>   measured in Z → 1

|+>   measured in X → +
|->   measured in X → -

|+i>  measured in Y → +i
|-i>  measured in Y → -i
```

In an ideal simulator, the corresponding eigenstate measurement should produce the expected eigenvalue deterministically apart from numerical/simulation representation issues.

---

# 16. Wrong-Basis Measurement Tests

Also test measurements in bases different from the eigenbasis.

For example:

$$
|0\rangle
$$

measured in the X basis should produce approximately:

$$
P(+)=\frac12
$$

$$
P(-)=\frac12
$$

with finite-shot variation.

This verifies that the measurement implementation is not accidentally hard-coded to produce deterministic outcomes.

---

# 17. Probability Conservation Test

For every measurement distribution:

$$
\sum_i \hat p_i=1
$$

within numerical tolerance.

The implementation must reject or flag invalid probability distributions.

---

# 18. Bell-State Tests

The Bell-state module must verify:

$$
|\Phi^+\rangle
=
\frac{|00\rangle+|11\rangle}{\sqrt2}
$$

Tests should verify:

* Correct state preparation.
* Correct normalization.
* Expected computational-basis distribution.
* Expected correlations.

---

# 19. Bell Measurement Distribution Test

For sufficiently large shot count:

$$
P(00)\approx0.5
$$

$$
P(11)\approx0.5
$$

and:

$$
P(01)\approx0
$$

$$
P(10)\approx0
$$

The test must use an appropriate statistical tolerance rather than requiring exact finite-shot equality.

---

# 20. Bell Correlation Tests

Verify:

$$
\langle X\otimes X\rangle=1
$$

$$
\langle Y\otimes Y\rangle=-1
$$

$$
\langle Z\otimes Z\rangle=1
$$

for the ideal:

$$
|\Phi^+\rangle
$$

state.

---

# 21. Teleportation Tests

Teleportation is a critical module.

Test all six Pauli eigenstates as input states.

For each input:

```text
Prepare input state
        ↓
Prepare Bell pair
        ↓
Perform Bell measurement
        ↓
Apply conditional Pauli corrections
        ↓
Recover state
        ↓
Compare with input
```

---

# 22. Teleportation Correctness

For each input state:

$$
|\psi\rangle
$$

the recovered state:

$$
|\psi_{\text{out}}\rangle
$$

should satisfy:

$$
F=
|\langle\psi|\psi_{\text{out}}\rangle|^2
\approx1
$$

under ideal simulation.

---

# 23. Teleportation Branch Tests

Teleportation produces four classical measurement branches:

```text
00
01
10
11
```

Every branch must be tested.

This is important because a teleportation implementation may appear correct overall while incorrectly handling one conditional correction branch.

---

# 24. Pauli Correction Tests

Verify the correction mapping used by the implementation.

The project protocol currently specifies the conceptual mapping:

```text
Alice bits
00 → I
01 → X
10 → Z
11 → XZ
```

However, Qiskit classical-bit ordering must be explicitly tested.

The implementation must not assume that the displayed bit string automatically corresponds to the mathematical \((a,b)\) ordering.

---

# 25. Classical-Bit Ordering Test

Create dedicated tests for:

```text
Qiskit classical register
        ↓
Measurement result
        ↓
Mathematical correction bits
        ↓
Pauli correction
```

Each of the four possible measurement results must produce the correct recovery.

This test is mandatory.

---

# 26. Teleportation Regression Test

Once teleportation passes all tests, preserve those tests permanently.

Any later change to:

* Circuit construction
* Classical registers
* Measurement order
* Pauli corrections
* Qiskit version

must run the teleportation regression suite.

---

# 27. Noise Testing

Noise testing begins only after ideal quantum tests pass.

The noise test structure is:

```text
Ideal circuit
      ↓
Known noise model
      ↓
Repeated simulation
      ↓
Measurement statistics
      ↓
Compare with expected degradation
```

---

# 28. Honest Noise Tests

For each supported noise model, verify that:

* The circuit still executes.
* Measurement probabilities remain valid.
* Noise changes the expected statistics.
* The implementation does not label every noisy execution as an attack.
* Baselines can be generated.

---

# 29. Noise Model Isolation

Each noise model should be tested independently.

For example:

```text
Depolarizing noise
Bit-flip noise
Phase-flip noise
Readout error
Thermal relaxation
```

Do not combine multiple noise models until individual behaviour is understood.

---

# 30. Noise Parameter Tests

For a noise parameter:

$$
\eta
$$

test several values.

For example:

```text
η = 0
η = low
η = medium
η = high
```

The exact values will be defined in the experiment configuration.

The test should verify that changing the parameter actually changes the simulator behaviour.

---

# 31. Noise vs Attack Test

A central test is:

```text
Honest + noise
```

versus:

```text
Attack + same noise
```

The two cases must remain distinguishable in the test configuration where the attack is expected to be detectable.

---

# 32. Statistical Testing

Statistical functions must be tested independently from quantum circuits.

Examples:

```text
probability estimation
mean
variance
standard deviation
standard error
QBER
fidelity
distribution distance
confidence interval
baseline
threshold evaluation
```

---

# 33. Probability Estimation Tests

Given:

```text
counts = {0: 500, 1: 500}
shots = 1000
```

verify:

$$
\hat p(0)=0.5
$$

and:

$$
\hat p(1)=0.5
$$

Also test:

```text
0 counts
1 count
all outcomes identical
missing outcomes
invalid shot count
```

---

# 34. Probability Sum Test

For every valid count dictionary:

$$
\sum_i \hat p_i=1
$$

within numerical tolerance.

---

# 35. Invalid Statistics Tests

The implementation should correctly handle:

```text
shots = 0
negative counts
counts > shots
empty measurement data
invalid outcome labels
NaN values
infinite values
```

These should produce controlled errors rather than silently generating security decisions.

---

# 36. QBER Tests

Given:

$$
N_{\text{errors}}
$$

and:

$$
N_{\text{valid}}
$$

verify:

$$
QBER=
\frac{N_{\text{errors}}}
{N_{\text{valid}}}
$$

Test:

```text
0 errors
all errors
partial errors
zero valid comparisons
```

For zero valid comparisons, the system must not divide by zero or report a misleading QBER.

---

# 37. Fidelity Tests

For identical states:

$$
F=1
$$

For orthogonal pure states:

$$
F=0
$$

Test intermediate states as well.

Also verify:

$$
0\leq F\leq1
$$

within numerical tolerance.

---

# 38. Baseline Tests

Given a known set of honest observations:

```text
M1, M2, ..., MN
```

verify:

$$
\bar M
=
\frac1N\sum_iM_i
$$

and:

$$
s^2
=
\frac1{N-1}
\sum_i(M_i-\bar M)^2
$$

The implementation should be checked against independently calculated expected values.

---

# 39. Baseline Contamination Test

Create:

```text
Honest dataset
Attack dataset
```

Verify that the baseline-generation function uses only the designated honest dataset.

The system must not accidentally include attack observations.

---

# 40. Threshold Tests

Threshold evaluation should test:

```text
value exactly at threshold
value just below threshold
value just above threshold
value far outside threshold
```

This prevents boundary bugs.

---

# 41. Threshold Direction Tests

Metrics can behave differently.

For a metric where higher is worse:

```text
value > threshold → deviation
```

For a metric where lower is worse:

```text
value < threshold → deviation
```

Both directions must have dedicated tests.

---

# 42. Deterministic Decision Tests

Given identical:

```text
Evidence
Baseline
Threshold configuration
Protocol state
```

the decision must always be identical.

Example:

```text
Input evidence → ATTACK
Input evidence → ATTACK
Input evidence → ATTACK
```

No randomness should change the final result.

---

# 43. ACCEPT Tests

Test a complete legitimate scenario:

```text
Valid identity
Valid session
Valid nonce
Authorized verifier
No replay
Valid signature
Quantum statistics within baseline
```

Expected:

```text
ACCEPT
```

---

# 44. SUSPICIOUS Tests

Test cases where:

```text
Protocol valid
Signature not clearly invalid
Quantum evidence deviates
No explicit attack rule satisfied
```

Expected:

```text
SUSPICIOUS
```

The exact numerical conditions will depend on calibrated thresholds.

---

# 45. ATTACK Tests

Each known attack must have a dedicated test.

Required:

```text
Forgery
Replay
Impersonation
Unauthorized verification
Quantum-channel manipulation
```

Each test must verify both:

1. Attack is correctly detected when conditions are satisfied.
2. Similar honest behaviour does not automatically trigger the attack rule.

---

# 46. Forgery Tests

Minimum forgery test cases:

```text
Valid signature
Modified message
Modified signature
Incorrect state representation
Strong forgery
Weak forgery
Forgery under low noise
Forgery under moderate noise
```

The test must record whether each attack is:

```text
Detected
Suspicious
Missed
```

---

# 47. Replay Tests

Test:

```text
Fresh nonce
Used nonce
Repeated request ID
Repeated session/nonce combination
Different session with same nonce
```

Expected behaviour must follow the protocol's freshness definition.

---

# 48. Impersonation Tests

Test:

```text
Correct signer
Incorrect signer
Unknown signer
Missing signer identity
Signer/signature mismatch
```

Identity failures must not be incorrectly labelled as quantum-channel attacks.

---

# 49. Authorization Tests

Test:

```text
Authorized verifier
Unauthorized verifier
Unknown verifier
Missing authorization information
Expired authorization
```

Unauthorized verification must be detected at the protocol layer.

---

# 50. Quantum-Channel Attack Tests

For each supported simulated channel manipulation:

```text
No attack
Weak attack
Medium attack
Strong attack
```

Measure:

```text
fidelity
QBER
Pauli statistics
Bell correlations
distribution deviation
detection result
```

---

# 51. Attack Attribution Tests

A quantum anomaly should not automatically be classified as every possible attack.

For example:

```text
Quantum deviation
+
No identity violation
+
No replay
+
No authorization violation
```

should not automatically produce:

```text
IMPERSONATION
```

The classification must correspond to the evidence.

---

# 52. Unknown Attack Test

Create an anomalous condition that does not match any known attack rule.

Expected:

```text
SUSPICIOUS
```

rather than an invented attack category.

This verifies that the detector can represent uncertainty.

---

# 53. Noise False-Positive Tests

Run honest noisy experiments.

The detector should evaluate whether the observed behaviour lies inside the calibrated honest operating region.

The test should measure:

$$
FRR
$$

and:

$$
LAR
$$

rather than assuming all honest noisy runs will be accepted.

---

# 54. Security Metric Tests

Verify:

$$
FAR=
\frac{
N_{\text{malicious accepted}}
}{
N_{\text{malicious attempts}}
}
$$

$$
FRR=
\frac{
N_{\text{legitimate rejected}}
}{
N_{\text{legitimate attempts}}
}
$$

$$
LAR=
\frac{
N_{\text{legitimate accepted}}
}{
N_{\text{legitimate attempts}}
}
$$

$$
ADR=
\frac{
N_{\text{attacks detected}}
}{
N_{\text{attack attempts}}
}
$$

and:

$$
\hat p_F=
\frac{
N_{\text{false accepts}}
}{
N_{\text{forgery attempts}}
}
$$

Test zero-denominator cases explicitly.

---

# 55. Zero-Denominator Handling

Examples:

```text
0 legitimate attempts
0 attack attempts
0 forgery attempts
0 valid measurements
```

The system must not return:

```text
NaN
Infinity
```

as a security result without explicitly handling the condition.

Possible behaviour:

```text
Not available
Insufficient data
Configuration error
```

The exact representation should be standardized during implementation.

---

# 56. Edge-Case Testing

Important edge cases include:

```text
Empty input
Very small shot count
One-shot measurement
Very large shot count
All outcomes identical
No expected outcomes
Invalid state
Invalid basis
Unknown attack type
Missing baseline
Mismatched baseline/noise configuration
Missing protocol metadata
Invalid nonce
Duplicate request
```

---

# 57. Configuration Mismatch Tests

A verification using:

```text
Noise configuration A
```

should not silently use a baseline created for:

```text
Noise configuration B
```

unless the configuration explicitly allows it.

The system should detect the mismatch.

---

# 58. Baseline Version Tests

Verify that:

```text
baseline_id
```

is preserved through verification and evaluation.

Changing the baseline should produce a different configuration/version identifier.

---

# 59. Reproducibility Tests

Experiments requiring randomness should use a recorded seed.

For the same:

```text
seed
configuration
circuit
shots
software version
```

the simulator should produce reproducible results where the underlying simulator supports deterministic seeded execution.

---

# 60. Regression Testing

Every completed milestone should add regression tests.

Example:

```text
M2 Pauli
    ↓
Pauli tests preserved

M4 Bell
    ↓
Pauli + Bell tests preserved

M5 Teleportation
    ↓
Pauli + Bell + teleportation tests preserved

M10 Detection
    ↓
All previous tests + statistical/detection tests
```

No completed module should be allowed to silently regress.

---

# 61. Integration Testing

Integration tests verify communication between modules.

Examples:

```text
State preparation
→ teleportation
→ measurement
→ statistics
```

and:

```text
Quantum verification
→ baseline
→ threshold engine
→ evidence
→ decision
```

---

# 62. End-to-End Test

At least one complete test must execute:

```text
Message
   ↓
Signature representation
   ↓
Quantum state
   ↓
Bell state
   ↓
Teleportation
   ↓
Pauli correction
   ↓
Measurement
   ↓
Quantum metrics
   ↓
Protocol checks
   ↓
Baseline comparison
   ↓
Security rules
   ↓
Decision
```

Expected result:

```text
ACCEPT
```

for a valid honest scenario.

---

# 63. End-to-End Attack Tests

Repeat the complete pipeline for:

```text
Forgery
Replay
Impersonation
Unauthorized verification
Quantum-channel manipulation
```

The expected result depends on the configured attack and statistical operating region.

---

# 64. Test Matrix

The project should maintain a matrix similar to:

| Component        | Ideal | Honest Noise | Attack | Edge Cases | Integration |
| ---------------- | ----: | -----------: | -----: | ---------: | ----------: |
| Qubit states     |     ✓ |              |        |          ✓ |           ✓ |
| Pauli operations |     ✓ |              |        |          ✓ |           ✓ |
| Measurement      |     ✓ |            ✓ |        |          ✓ |           ✓ |
| Bell state       |     ✓ |            ✓ |        |          ✓ |           ✓ |
| Teleportation    |     ✓ |            ✓ |      ✓ |          ✓ |           ✓ |
| Noise            |     ✓ |            ✓ |        |          ✓ |           ✓ |
| QDS verification |     ✓ |            ✓ |      ✓ |          ✓ |           ✓ |
| Statistics       |     ✓ |            ✓ |      ✓ |          ✓ |           ✓ |
| Baseline         |     ✓ |            ✓ |        |          ✓ |           ✓ |
| Thresholds       |     ✓ |            ✓ |      ✓ |          ✓ |           ✓ |
| Forgery          |       |            ✓ |      ✓ |          ✓ |           ✓ |
| Replay           |       |              |      ✓ |          ✓ |           ✓ |
| Impersonation    |       |              |      ✓ |          ✓ |           ✓ |
| Authorization    |       |              |      ✓ |          ✓ |           ✓ |
| Channel attacks  |       |            ✓ |      ✓ |          ✓ |           ✓ |
| Decision engine  |     ✓ |            ✓ |      ✓ |          ✓ |           ✓ |

---

# 65. Statistical Experiment Testing

Unit tests are not enough for security evaluation.

The project must also run repeated experiments.

For example:

```text
100 honest runs
100 forgery attempts
100 replay attempts
100 impersonation attempts
100 channel attacks
```

The exact number should be increased when meaningful probability estimates are required.

---

# 66. Experiment Repetition

A single successful attack detection is not sufficient evidence.

For each experiment record:

```text
number of trials
number detected
number missed
number suspicious
number falsely accepted
number falsely rejected
```

---

# 67. Threshold Validation

Thresholds must be tested against both:

```text
Honest data
```

and:

```text
Attack data
```

A threshold that detects every attack but rejects every legitimate signature is not useful.

Likewise, a threshold that accepts every legitimate signature but accepts attacks is not useful.

---

# 68. Threshold Sensitivity Testing

For candidate thresholds:

$$
T_1,T_2,\ldots,T_n
$$

evaluate:

$$
FAR(T)
$$

$$
FRR(T)
$$

and:

$$
ADR(T)
$$

This allows the team to understand the trade-off before selecting a final configuration.

---

# 69. Noise Sensitivity Testing

Evaluate detector behaviour across:

$$
\eta_1,\eta_2,\ldots,\eta_n
$$

and record:

```text
LAR
FRR
FAR
ADR
```

This demonstrates whether the detector remains useful as noise increases.

---

# 70. Shot Sensitivity Testing

Evaluate multiple shot counts.

For example:

```text
100
500
1,000
5,000
10,000
```

The exact final values should be selected based on runtime and experimental needs.

Measure:

```text
metric stability
detection rate
false acceptance
false rejection
runtime
```

---

# 71. Performance Testing

Performance testing should measure:

```text
Circuit construction time
Simulation time
Measurement processing time
Statistical analysis time
Decision time
Total verification time
```

For repeated-shot simulation, distinguish:

```text
Quantum simulation time
```

from:

```text
Classical processing time
```

---

# 72. Verification Efficiency

The project should measure:

$$
T_{\text{verification}}
$$

as the total time required for one verification under a specified configuration.

Record:

```text
shots
number of qubits
noise model
attack state
hardware/software environment
```

---

# 73. Performance Regression

If a later implementation makes verification significantly slower, investigate the reason.

Do not optimize prematurely.

Correctness comes first.

---

# 74. Security Regression

Every new feature must verify that it does not weaken previous security behaviour.

Examples:

```text
Adding dashboard
    ↓
must not change detector logic

Adding blockchain
    ↓
must not change verification result

Changing UI
    ↓
must not alter protocol state
```

---

# 75. Separation of UI and Security Tests

UI tests must not be the primary security tests.

The security engine must be testable without Streamlit.

Preferred architecture:

```text
UI
 ↓
Application layer
 ↓
Security engine
 ↓
Quantum/statistical modules
```

The lower layers must have independent tests.

---

# 76. Test Data

Test datasets should be separated into:

```text
tests/data/
├── honest/
├── forgery/
├── replay/
├── impersonation/
├── unauthorized/
└── channel_attacks/
```

Synthetic data is acceptable for controlled experiments.

The origin and configuration of generated data should be documented.

---

# 77. No Test Leakage

Attack data must not accidentally appear in:

```text
honest baseline
threshold calibration
validation data
```

unless the experiment explicitly studies such contamination.

---

# 78. Test Fixtures

Reusable fixtures should be created for common objects such as:

```text
valid message
valid signature
valid signer
valid verifier
valid session
valid nonce
default noise configuration
default baseline
default threshold configuration
```

This reduces duplicated test setup.

---

# 79. Test Configuration

Testing configuration should be separated from production/demo configuration.

Conceptually:

```text
config/
├── development
├── testing
├── experiments
└── demo
```

The exact implementation can use YAML, JSON, TOML, or Python configuration as appropriate.

---

# 80. Test Output

A useful test report should contain:

```text
Test name
Status
Execution time
Configuration
Expected result
Actual result
Failure reason
```

Security experiments should additionally report metrics.

---

# 81. Failure Reporting

When a test fails, the output should identify:

```text
What failed?
Expected value?
Actual value?
Configuration?
Seed?
Noise?
Shots?
Relevant module?
```

This is especially important for stochastic quantum simulations.

---

# 82. Quantum Numerical Tolerance

Quantum-state comparisons must use numerical tolerances.

Avoid:

```python
actual == expected
```

for floating-point quantum state vectors.

Prefer an appropriate tolerance-based comparison.

The tolerance must be documented.

---

# 83. Security Threshold vs Test Tolerance

These must never be confused.

### Test tolerance

Used to determine whether a numerical implementation matches an expected mathematical result.

### Security threshold

Used to determine whether observed behaviour is statistically unusual.

They serve different purposes.

---

# 84. Test Coverage

The project should aim for strong coverage of:

* Core mathematical functions
* Quantum primitives
* Security rules
* Attack logic
* Error handling
* Decision engine

Code coverage is useful but is not by itself a security guarantee.

A system can have high code coverage while testing the wrong assumptions.

---

# 85. Scientific Validation

Where possible, compare implementation results against:

```text
Analytical calculation
```

before relying only on:

```text
Simulator output
```

For example:

```text
Bell-state theoretical probability
vs
simulated probability
```

and:

```text
Teleportation theoretical correctness
vs
simulated fidelity
```

---

# 86. Manual Verification

For the first implementation of a quantum module, manually inspect:

* Circuit diagram
* State representation
* Measurement basis
* Classical registers
* Measurement counts
* Pauli correction branch
* Output state

This is especially important during early development.

---

# 87. Testing the Six-State Model

The six-state model should be treated as a mandatory test suite.

For each:

```text
|0>
|1>
|+>
|->
|+i>
|-i>
```

test:

```text
Preparation
Measurement
Teleportation
Recovery
Verification
```

This provides broad coverage of the three Pauli bases.

---

# 88. Testing Deterministic Legitimate Acceptance

The SIH requirement for deterministic legitimate acceptance must be explicitly tested.

The test should establish that:

```text
Same valid protocol state
+
Same configured honest conditions
+
Same verification rules
```

produces:

```text
ACCEPT
```

as the deterministic final decision once the measurement evidence is fixed.

The quantum measurement process itself remains probabilistic.

---

# 89. Important Distinction

Testing must preserve the distinction:

```text
Quantum measurement
→ probabilistic
```

versus:

```text
Decision rule
→ deterministic
```

The test suite must not incorrectly demand that every raw quantum measurement be deterministic.

---

# 90. Security Claim Testing

Whenever the project makes a statement such as:

```text
"Channel attack was detected"
```

there must be an experiment showing:

```text
Attack condition
+
Observed evidence
+
Detection rule
+
Result
```

Similarly:

```text
"No false acceptance observed"
```

must specify the number of trials.

---

# 91. Reproducible Experiment Record

Each major experiment should produce a record containing:

```text
experiment_id
date/time
software version
Qiskit version
Aer version
random seed
protocol version
baseline_id
threshold configuration
noise configuration
attack configuration
shots
number of trials
results
```

---

# 92. Test Completion Criteria for a Module

A module is not complete merely because its code executes.

A module should have:

```text
Implementation
+
Unit tests
+
Expected mathematical behaviour
+
Edge-case tests
+
Integration test where applicable
+
Documentation
```

---

# 93. Module Completion Gate

Before moving to the next milestone:

```text
1. Implementation complete
2. Unit tests pass
3. Mathematical checks pass
4. Edge cases handled
5. Integration tests pass
6. No known protocol violation
7. Documentation updated
8. PROGRESS.md updated
```

Only then proceed.

---

# 94. MVP Testing Requirements

Before calling the MVP complete, the following must pass:

```text
✓ Six Pauli eigenstates
✓ Pauli operations
✓ Projective measurements
✓ Bell-state preparation
✓ Bell-state measurements
✓ Teleportation
✓ All four correction branches
✓ Noise simulation
✓ Honest baseline
✓ Statistical metrics
✓ Threshold engine
✓ Forgery simulation
✓ Replay detection
✓ Quantum-channel attack simulation
✓ Deterministic decision engine
✓ End-to-end verification
```

---

# 95. Competition-Demo Testing Requirements

Before the final SIH demonstration, additionally test:

```text
✓ Impersonation
✓ Unauthorized verification
✓ Multiple attack strengths
✓ Multiple noise levels
✓ Multiple shot counts
✓ Forgery probability experiment
✓ FAR
✓ FRR
✓ LAR
✓ ADR
✓ Explainable evidence
✓ Security operating region
✓ Performance benchmark
✓ Reproducible experiments
```

---

# 96. Final End-to-End Test Set

The final test suite should include at least:

### Test 1 — Honest Ideal

```text
Expected:
ACCEPT
```

### Test 2 — Honest Noisy

```text
Expected:
ACCEPT
or
SUSPICIOUS depending on calibrated operating region
```

### Test 3 — Forgery

```text
Expected:
ATTACK
or
SUSPICIOUS if the attack is below reliable detection conditions
```

### Test 4 — Replay

```text
Expected:
ATTACK / REPLAY
```

### Test 5 — Impersonation

```text
Expected:
ATTACK / IMPERSONATION
```

### Test 6 — Unauthorized Verification

```text
Expected:
ATTACK / UNAUTHORIZED_VERIFICATION
```

### Test 7 — Quantum Channel Manipulation

```text
Expected:
ATTACK or SUSPICIOUS depending on statistical distinguishability
```

### Test 8 — Unknown Anomaly

```text
Expected:
SUSPICIOUS
```

### Test 9 — Invalid System Configuration

```text
Expected:
CONTROLLED ERROR
```

---

# 97. Definition of Test Success

A test passes only when:

```text
Actual behaviour
```

matches:

```text
Expected behaviour
```

under:

```text
Documented assumptions
+
Documented configuration
```

A visually convincing result is not sufficient.

---

# 98. Testing Anti-Patterns

Do not:

```text
❌ Test only the happy path
❌ Test only with ideal simulation
❌ Test only one shot count
❌ Test only one noise level
❌ Test attacks without honest controls
❌ Calibrate baseline using attack data
❌ Hard-code expected attack results without justification
❌ Ignore numerical precision
❌ Treat every anomaly as an attack
❌ Claim zero probability from zero observed events
❌ Skip regression tests
❌ Depend on UI testing for security correctness
❌ Use ML to improve test results
```

---

# 99. Testing Workflow

For every new module:

```text
REQUIREMENT
    ↓
MATHEMATICAL EXPECTATION
    ↓
UNIT TEST
    ↓
IMPLEMENTATION
    ↓
UNIT TEST
    ↓
INTEGRATION TEST
    ↓
EXPERIMENT
    ↓
RESULT VALIDATION
    ↓
DOCUMENTATION
    ↓
REGRESSION TEST
```

---

# 100. Final Testing Principle

Q-SHIELD follows:

```text
DON'T TRUST THE IMPLEMENTATION
        ↓
TEST THE MATHEMATICS
        ↓
TEST THE QUANTUM BEHAVIOUR
        ↓
TEST THE STATISTICS
        ↓
TEST THE ATTACKS
        ↓
TEST THE EDGE CASES
        ↓
TEST THE COMPLETE SYSTEM
        ↓
ONLY THEN TRUST THE RESULT
```

The central rule is:

> **Every important security claim must be reproducible, measurable, and testable under explicitly documented conditions.**

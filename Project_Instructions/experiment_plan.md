# EXPERIMENT_PLAN.md

# Q-SHIELD — Experimental Plan

**Project:** Q-SHIELD — Quantum Signature Security & Threat Detection Framework
**Problem Statement:** SIH 26141 — Quantum-Inspired Cyber Threat Detection for Digital Signature Security
**Status:** DRAFT
**Purpose:** Define reproducible experiments for validating the quantum protocol simulation, statistical threat detection, attack behaviour, and system performance.

---

## 1. Purpose

This document defines the experiments required to validate Q-SHIELD.

The experiments must demonstrate that the system can:

1. Simulate Bell-state entanglement.
2. Perform quantum teleportation.
3. Apply the required Pauli corrections.
4. Perform projective measurements.
5. Establish honest measurement behaviour.
6. Model realistic quantum-channel noise.
7. Distinguish expected noise from anomalous behaviour.
8. Detect simulated forgery.
9. Detect replay attacks.
10. Detect impersonation.
11. Detect unauthorized verification.
12. Detect quantum-channel manipulation.
13. Calculate empirical forgery probability.
14. Evaluate legitimate acceptance and malicious rejection.
15. Measure FAR, FRR, LAR, and ADR.
16. Evaluate threshold sensitivity.
17. Determine a security operating region.
18. Measure computational and simulation performance.
19. Produce reproducible evidence suitable for the SIH demonstration.

---

# 2. Experimental Principles

All experiments must follow these principles.

### 2.1 No AI/ML

The detector must not use:

* machine learning
* neural networks
* classification models
* clustering
* trained AI models
* learned embeddings
* predictive models

Detection must be based on:

```text
Quantum measurements
        ↓
Statistical metrics
        ↓
Calibrated thresholds
        ↓
Deterministic rules
        ↓
Security decision
```

---

### 2.2 Honest behaviour must be measured first

Thresholds must not be selected arbitrarily.

The preferred workflow is:

```text
Honest executions
      ↓
Estimate baseline
      ↓
Validate baseline
      ↓
Determine acceptable operating region
      ↓
Freeze thresholds/configuration
      ↓
Run attack experiments
```

Attack results must not be used to secretly redefine the honest baseline.

---

### 2.3 Noise is not automatically an attack

An honest execution under noise may produce imperfect results.

Therefore:

```text
Noise
≠
Attack
```

The system must first characterize expected honest noisy behaviour.

Only deviations beyond the configured/calibrated operating region should be treated as suspicious or malicious.

---

### 2.4 Statistical results are empirical

Measurements from finite quantum shots are statistical.

Therefore results must report:

* number of shots
* measured counts
* empirical probabilities
* estimated uncertainty where appropriate
* noise configuration
* random seed where applicable

---

# 3. Experiment Categories

The experiments are divided into the following groups.

| ID  | Category                             |
| --- | ------------------------------------ |
| E01 | Teleportation correctness            |
| E02 | Honest baseline calibration          |
| E03 | Ideal vs noisy behaviour             |
| E04 | Noise sweep                          |
| E05 | Shot-count sweep                     |
| E06 | Forgery experiment                   |
| E07 | Replay experiment                    |
| E08 | Impersonation experiment             |
| E09 | Unauthorized verification experiment |
| E10 | Quantum-channel attack               |
| E11 | Attack-strength sweep                |
| E12 | Threshold sensitivity                |
| E13 | Security operating region            |
| E14 | Security metrics                     |
| E15 | Performance benchmark                |
| E16 | End-to-end demonstration             |

---

# 4. Standard Experimental Configuration

Every experiment should have an explicit configuration.

Example:

```text
Experiment configuration

state_set:
    six Pauli eigenstates

shots:
    1000

noise_model:
    configurable

noise_strength:
    configurable

measurement_bases:
    X, Y, Z

random_seed:
    fixed when reproducibility is required

baseline_version:
    explicit identifier

threshold_version:
    explicit identifier
```

The actual values should be stored with the experiment results.

---

# 5. E01 — Teleportation Correctness

## Objective

Verify that the basic quantum teleportation implementation behaves correctly before introducing attacks or statistical detection.

---

## 5.1 States

Test all six Pauli eigenstates:

```text
|0>
|1>
|+>
|->
|+i>
|-i>
```

---

## 5.2 Procedure

For every input state:

1. Prepare the input qubit.
2. Prepare the Bell pair.
3. Perform Bell-state measurement operations.
4. Obtain classical measurement results.
5. Apply the corresponding Pauli correction.
6. Measure the output state.
7. Compare the output with the original input state.

---

## 5.3 Required correction branches

Test all four possible classical correction outcomes:

```text
00 → I
01 → X
10 → Z
11 → XZ
```

The implementation must account for the actual classical-bit ordering used by the simulator.

---

## 5.4 Measurements

Record:

* input state
* correction branch
* output counts
* output probabilities
* fidelity
* measurement basis

---

## 5.5 Expected result

Under ideal simulation:

```text
Teleportation fidelity ≈ 1
```

within the numerical/statistical tolerance appropriate to the simulation.

This experiment must pass before continuing to attack experiments.

---

# 6. E02 — Honest Baseline Calibration

## Objective

Establish the expected statistical behaviour of legitimate signatures under honest operating conditions.

This is one of the most important experiments in Q-SHIELD.

---

## 6.1 Why baseline calibration is required

Suppose an honest system normally produces:

```text
QBER = 0.03
```

and an attack produces:

```text
QBER = 0.04
```

It would be scientifically incorrect to automatically classify the second result as an attack without understanding natural variation.

The baseline establishes:

```text
What does legitimate behaviour normally look like?
```

---

## 6.2 Baseline data

Run many independent honest executions.

Vary only controlled experimental factors such as:

* input state
* measurement basis
* shot count
* configured honest noise
* random seed

Do not introduce attacks during baseline collection.

---

## 6.3 Metrics

Possible baseline metrics include:

* QBER
* fidelity
* Pauli expectation values
* measurement probabilities
* total variation distance
* Bell-state correlation
* teleportation output error

---

## 6.4 Baseline statistics

For every metric calculate appropriate statistics such as:

$$
\bar{x}=\frac{1}{n}\sum_{i=1}^{n}x_i
$$

and sample variance:

$$
s^2=\frac{1}{n-1}
\sum_{i=1}^{n}(x_i-\bar{x})^2
$$

Where appropriate, calculate:

* standard deviation
* standard error
* confidence interval
* empirical quantiles

---

## 6.5 Baseline operating region

The system should define an honest operating region using a documented statistical procedure.

Possible approaches include:

### Approach A — Confidence interval

Estimate the expected range of honest behaviour.

### Approach B — Empirical quantiles

Use quantiles obtained from independent honest validation data.

### Approach C — Metric-specific statistical bounds

Use an appropriate statistical bound for the metric.

The chosen method must be documented in:

```text
DECISIONS.md
```

---

## 6.6 Baseline validation

The baseline must be validated on separate honest executions.

Do not calibrate and validate on exactly the same dataset.

Preferred structure:

```text
Honest dataset
      ↓
Calibration subset
      ↓
Baseline
      ↓
Independent validation subset
      ↓
False rejection estimate
```

---

# 7. E03 — Ideal vs Noisy Teleportation

## Objective

Demonstrate the difference between ideal quantum behaviour and realistic noisy behaviour.

---

## Conditions

Run the same protocol under:

```text
Condition A:
Ideal simulation

Condition B:
Noisy simulation
```

---

## Metrics

Compare:

* fidelity
* QBER
* measurement distributions
* Pauli expectations
* Bell correlations

---

## Expected observation

Ideal simulation should produce behaviour close to the theoretical expectation.

Noisy simulation should introduce measurable deviations.

The experiment demonstrates why a noise-calibrated detector is necessary.

---

# 8. E04 — Noise Sweep

## Objective

Measure how honest verification behaviour changes as channel noise increases.

---

## Independent variable

Noise strength.

For example:

```text
low
medium-low
medium
medium-high
high
```

The exact numerical levels must be defined by the selected simulator noise model.

Possible noise models include:

* bit-flip
* phase-flip
* depolarizing noise
* readout error
* combinations of supported noise processes

---

## Procedure

For each noise level:

1. Run honest verification.
2. Repeat for multiple states.
3. Collect measurement statistics.
4. Calculate quantum metrics.
5. Record acceptance/rejection behaviour.

---

## Required plots

At minimum:

```text
Noise strength vs QBER
Noise strength vs fidelity
Noise strength vs legitimate acceptance rate
```

---

## Important observation

The experiment should identify the region where honest verification remains reliable.

This becomes part of the:

> **Security Operating Region**

---

# 9. E05 — Shot-Count Sweep

## Objective

Determine how the number of quantum measurement shots affects statistical stability.

---

## Example shot levels

```text
100
250
500
1000
2500
5000
10000
```

The exact values may be adjusted depending on runtime.

---

## Procedure

For each shot count:

1. Execute the same experiment.
2. Calculate measurement probabilities.
3. Calculate QBER/fidelity/other metrics.
4. Repeat multiple times.
5. Measure variation.

---

## Expected observation

Generally:

```text
More shots
    ↓
Lower statistical uncertainty
    ↓
More stable estimates
```

But:

```text
More shots
    ↓
Higher simulation cost
```

This experiment therefore supports the efficient-verification requirement.

---

## Required plots

```text
Shots vs metric variance
Shots vs runtime
Shots vs legitimate acceptance rate
```

---

# 10. E06 — Forgery Experiment

## Objective

Measure whether an attacker using an incorrect signature/state can be detected.

---

## Honest condition

The verifier receives the correct signature corresponding to the message.

Expected:

```text
ACCEPT
```

---

## Forged condition

The attacker modifies or substitutes the signature representation.

Possible simulated cases:

```text
wrong state
wrong state sequence
modified signature
incorrect message-signature relationship
```

---

## Procedure

For each forged attempt:

1. Generate or select an invalid signature.
2. Run the verification procedure.
3. Collect quantum measurements.
4. Perform protocol checks.
5. Calculate security metrics.
6. Apply deterministic detection rules.
7. Record the result.

---

# 11. Empirical Forgery Probability

The system must distinguish between:

### Formal cryptographic forging probability

A theoretical security quantity derived from a QDS protocol/security proof.

and:

### Empirical forgery success probability

The probability estimated from simulation experiments.

The project should primarily report the second unless a formal protocol bound has been established.

---

## Formula

If an attacker successfully causes acceptance in \(S\) out of \(N\) independent attempts:

$$
\hat{P}_{forge}=\frac{S}{N}
$$

Example:

```text
1000 forgery attempts
7 accepted
```

Then:

$$
\hat{P}_{forge}=\frac{7}{1000}=0.007
$$

or:

```text
0.7%
```

---

## Required reporting

Always report:

```text
Number of attempts
Number of successful forgeries
Empirical forgery probability
Experimental configuration
```

Where appropriate, also report uncertainty/confidence intervals.

---

# 12. E07 — Replay Attack Experiment

## Objective

Determine whether a previously valid verification request can be reused.

---

## Procedure

### Step 1

Perform a legitimate verification.

Record:

```text
session ID
nonce
timestamp
message identifier
signature identifier
```

### Step 2

Replay the same request.

### Step 3

Run the security checks.

---

## Expected result

The first legitimate request:

```text
ACCEPT
```

The replayed request:

```text
ATTACK
```

or another explicitly configured security failure state.

---

## Important principle

Replay detection is primarily a protocol-layer security mechanism.

Quantum measurement statistics alone should not be falsely claimed to detect every replay attack.

---

# 13. E08 — Impersonation Experiment

## Objective

Test whether a malicious participant can claim to be the legitimate signer.

---

## Procedure

Create:

```text
Legitimate signer identity
Attacker identity
```

Attempt verification using the attacker identity while presenting an invalid or unauthorized signature/session.

---

## Evidence

Use:

* signer identity
* authorization status
* signature consistency
* session information
* quantum verification evidence

---

## Expected result

The impersonation attempt must not be accepted as a legitimate signer.

---

# 14. E09 — Unauthorized Verification Experiment

## Objective

Test whether an unauthorized verifier can perform a protected verification operation.

---

## Procedure

Create verification requests with:

```text
authorized verifier
unauthorized verifier
```

Keep the message/signature identical.

---

## Expected result

Authorized request:

```text
ACCEPT
```

Unauthorized request:

```text
ATTACK
```

---

## Security principle

Authorization is a protocol/application-layer property.

It must not be represented as purely quantum evidence.

---

# 15. E10 — Quantum-Channel Attack Experiment

## Objective

Evaluate the effect of manipulation of the quantum state/channel.

---

## Attack types

Possible simulated attacks include:

```text
Bit flip
Phase flip
Y error
Depolarizing disturbance
Readout manipulation
```

The exact attacks supported must be recorded in the implementation.

---

## Procedure

For every attack:

1. Prepare an honest state.
2. Apply the selected manipulation.
3. Perform teleportation.
4. Apply Pauli corrections.
5. Measure the output.
6. Calculate quantum metrics.
7. Compare against honest baseline.
8. Apply detection rules.

---

## Expected observation

Increasing channel manipulation should generally increase measurable deviation from honest behaviour.

However, detection performance must be measured rather than assumed.

---

# 16. E11 — Attack-Strength Sweep

## Objective

Determine how detection changes as attack intensity increases.

---

## Example structure

```text
Attack strength:
0
low
medium
high
very high
```

The numerical meaning of each level must be explicitly defined for each attack model.

---

## Metrics

For every attack strength calculate:

* detection rate
* false acceptance rate
* false rejection rate
* quantum metric deviation
* empirical forgery success
* runtime

---

## Required plot

```text
Attack strength
       ↓
Detection rate
```

This provides a much stronger demonstration than showing only one attack example.

---

# 17. E12 — Threshold Sensitivity Experiment

## Objective

Determine how detector performance changes when statistical thresholds change.

---

## Why this matters

A threshold that is too strict may reject legitimate signatures.

A threshold that is too loose may allow attacks.

Therefore there is a trade-off:

```text
Strict threshold
→ stronger anomaly detection
→ potentially higher false rejection

Loose threshold
→ fewer false rejections
→ potentially higher false acceptance
```

---

## Procedure

Evaluate multiple threshold configurations around the calibrated operating point.

Do not select the final threshold solely because it produces the most attractive demo result.

---

## Metrics

Calculate:

* FAR
* FRR
* LAR
* ADR

---

## Required output

A threshold-performance table and graph.

Example structure:

| Threshold Configuration | FAR | FRR | LAR | ADR |
| ----------------------- | --: | --: | --: | --: |
| T1                      | ... | ... | ... | ... |
| T2                      | ... | ... | ... | ... |
| T3                      | ... | ... | ... | ... |

---

# 18. E13 — Security Operating Region

## Objective

Determine under which combinations of:

* noise
* attack strength
* shots

the detector performs reliably.

---

## Experimental dimensions

Example:

```text
Noise:
low → high

Attack:
none → strong

Shots:
low → high
```

---

## Concept

The result can be represented as a region:

```text
                 Attack strength
                       ↑
                       │
            Detection │
              region  │
                       │
───────────────────────┼────────→ Noise
                       │
          Reliable    │
          operating   │
          region      │
                       │
```

The exact visualization should be generated from experimental data.

---

## Purpose

This prevents unsupported claims such as:

> “The detector works under all noise levels.”

Instead, the system can state:

> “Under the tested configuration, reliable detection was observed within the measured operating region.”

---

# 19. E14 — Security Metrics

The following metrics should be calculated.

---

## 19.1 Legitimate Acceptance Rate

$$
LAR =
\frac{\text{legitimate accepted}}
{\text{legitimate attempts}}
$$

High LAR is desirable.

---

## 19.2 False Rejection Rate

$$
FRR =
\frac{\text{legitimate rejected}}
{\text{legitimate attempts}}
$$

Low FRR is desirable.

---

## 19.3 False Acceptance Rate

$$
FAR =
\frac{\text{malicious accepted}}
{\text{malicious attempts}}
$$

Low FAR is desirable.

---

## 19.4 Attack Detection Rate

$$
ADR =
\frac{\text{malicious attempts detected}}
{\text{malicious attempts}}
$$

High ADR is desirable.

---

## 19.5 Empirical Forgery Probability

$$
\hat{P}_{forge}
=
\frac{\text{successful forgery attempts}}
{\text{total forgery attempts}}
$$

---

## 19.6 Runtime

Record:

```text
protocol simulation time
measurement simulation time
statistics calculation time
decision time
total verification time
```

The timing methodology must be consistent.

---

# 20. E15 — Performance Benchmark

## Objective

Evaluate whether verification remains computationally practical for a software simulation.

---

## Variables

Measure runtime against:

```text
number of shots
number of verification states
number of experiments
noise-model complexity
```

---

## Metrics

Record:

* total execution time
* average verification time
* throughput where meaningful
* memory usage where practical

---

## Important distinction

Simulation performance is not the same as performance on physical quantum hardware.

The project must clearly state that these benchmarks measure the software simulator.

---

# 21. E16 — End-to-End SIH Demonstration

This is the primary competition demonstration.

---

## Scenario A — Legitimate signature

```text
Message
 ↓
Valid signer
 ↓
Valid session
 ↓
Valid nonce
 ↓
Quantum teleportation
 ↓
Pauli correction
 ↓
Measurement
 ↓
Statistics
 ↓
Verification
 ↓
ACCEPT
```

Display:

* message
* signer
* quantum circuit
* measurement statistics
* fidelity/QBER
* decision evidence

---

## Scenario B — Forgery

```text
Modified signature
        ↓
Quantum verification
        ↓
Statistical deviation
        ↓
Detection rule
        ↓
ATTACK
```

---

## Scenario C — Replay

```text
Previously valid request
        ↓
Same nonce/session
        ↓
Replay detection
        ↓
ATTACK
```

---

## Scenario D — Quantum-channel manipulation

```text
Valid signature
        ↓
Channel disturbance
        ↓
Measurement deviation
        ↓
Baseline comparison
        ↓
ATTACK / SUSPICIOUS
```

---

## Scenario E — Impersonation

```text
Attacker identity
        ↓
Identity/authentication failure
        ↓
ATTACK
```

---

# 22. Experimental Controls

Every experiment must identify its control condition.

Examples:

| Experiment      | Control                     |
| --------------- | --------------------------- |
| Teleportation   | Ideal teleportation         |
| Noise sweep     | Zero/no-noise condition     |
| Forgery         | Valid signature             |
| Replay          | First legitimate request    |
| Impersonation   | Legitimate signer           |
| Channel attack  | Same channel without attack |
| Threshold study | Calibrated threshold        |
| Shot sweep      | Reference shot count        |

The control allows the measured effect to be attributed to the experimental variable.

---

# 23. Independent Variables

Possible independent variables:

```text
noise strength
attack type
attack strength
number of shots
input state
measurement basis
threshold
number of trials
```

Only controlled variables should be changed during a specific experiment unless the experiment is explicitly multidimensional.

---

# 24. Dependent Variables

Possible dependent variables:

```text
fidelity
QBER
measurement probability
Pauli expectation
Bell correlation
TV distance
legitimate acceptance
attack detection
FAR
FRR
LAR
ADR
forgery success
runtime
```

---

# 25. Reproducibility Metadata

Every experiment result must store sufficient information for reproduction.

Minimum metadata:

```text
experiment_id
experiment_name
timestamp
software_version
Qiskit version
Aer version
Python version
state configuration
noise model
noise strength
attack type
attack strength
shot count
random seed
baseline version
threshold version
number of trials
```

---

# 26. Experiment Result Format

A machine-readable result should follow a structure similar to:

```json
{
  "experiment_id": "E10",
  "experiment_name": "quantum_channel_attack",
  "state": "|+>",
  "shots": 1000,
  "noise_model": "depolarizing",
  "noise_strength": 0.02,
  "attack_type": "phase_flip",
  "attack_strength": 0.10,
  "fidelity": 0.91,
  "qber": 0.08,
  "decision": "ATTACK"
}
```

The exact schema may evolve during implementation.

---

# 27. Repeated Trials

Single executions are insufficient for statistical claims.

Experiments involving probabilities or detection rates should use repeated independent trials.

The number of trials must be reported.

For example:

```text
N = 100
N = 500
N = 1000
```

depending on runtime and required precision.

---

# 28. Random Seeds

When the simulator uses randomness:

* record the seed
* use controlled seeds for debugging/reproducibility
* use multiple seeds when evaluating general behaviour

A result that only works for one favourable seed must not be treated as robust evidence.

---

# 29. Train/Test Language

Because this project does not use AI/ML, avoid terminology such as:

```text
training data
model training
classifier training
test accuracy of a trained model
```

Instead use:

```text
calibration data
validation data
evaluation data
attack dataset
honest dataset
```

---

# 30. Calibration and Evaluation Separation

The recommended workflow is:

```text
                 Honest executions
                        │
              ┌─────────┴─────────┐
              ↓                   ↓
       Calibration set       Validation set
              │                   │
              ↓                   ↓
       Baseline/threshold    Honest performance
              │
              ↓
       Freeze configuration
              │
              ↓
       Attack evaluation
```

This prevents threshold tuning from being hidden inside the attack results.

---

# 31. Avoiding Arbitrary Thresholds

The implementation must not contain unexplained rules such as:

```text
if qber > 0.05:
    attack
```

unless the value has a documented experimental/statistical justification.

Instead:

```text
Honest calibration
        ↓
Statistical estimate
        ↓
Threshold selection procedure
        ↓
Independent validation
        ↓
Frozen threshold
        ↓
Attack evaluation
```

If a provisional threshold is required during early development, label it explicitly:

```text
PROVISIONAL DEVELOPMENT THRESHOLD
```

and do not present it as a scientifically validated security threshold.

---

# 32. Required Visualizations

The dashboard/report should eventually provide the following.

### Quantum behaviour

* Bell-state measurement distribution
* teleportation measurement distribution
* X-basis distribution
* Y-basis distribution
* Z-basis distribution

### Noise

* noise vs fidelity
* noise vs QBER
* noise vs LAR

### Statistics

* empirical probability distributions
* confidence/operating intervals
* baseline vs observed metrics

### Attacks

* attack strength vs detection rate
* attack strength vs FAR
* attack type comparison

### Forgery

* forgery attempts vs successful forgeries
* empirical forgery probability

### Performance

* shots vs runtime
* shots vs statistical stability

### Security operating region

* noise vs attack strength
* reliable/suspicious/attack regions

---

# 33. Required Tables

The final experiment report should contain at least:

### Table 1 — Teleportation correctness

| State | Correction | Fidelity | Result |
| ----- | ---------- | -------: | ------ |
| |0⟩   | I          |      ... | ...    |
| |1⟩   | X          |      ... | ...    |
| |+⟩   | Z          |      ... | ...    |
| |-⟩   | XZ         |      ... | ...    |
| |+i⟩  | ...        |      ... | ...    |
| |-i⟩  | ...        |      ... | ...    |

The exact correction mapping must follow the implemented teleportation circuit and Qiskit classical-bit convention.

---

### Table 2 — Attack performance

| Attack                    | Attempts | Detected | FAR | ADR |
| ------------------------- | -------: | -------: | --: | --: |
| Forgery                   |      ... |      ... | ... | ... |
| Replay                    |      ... |      ... | ... | ... |
| Impersonation             |      ... |      ... | ... | ... |
| Unauthorized verification |      ... |      ... | ... | ... |
| Channel manipulation      |      ... |      ... | ... | ... |

---

### Table 3 — Noise performance

| Noise | Fidelity | QBER | LAR | FRR |
| ----- | -------: | ---: | --: | --: |
| ...   |      ... |  ... | ... | ... |

---

### Table 4 — Shot performance

| Shots | Runtime | Metric variation | LAR |
| ----: | ------: | ---------------: | --: |
|   ... |     ... |              ... | ... |

---

# 34. Minimum SIH Experiment Set

If time is limited, the following experiments are mandatory.

```text
1. Bell-state generation
2. Six-state teleportation
3. Pauli correction validation
4. Honest ideal baseline
5. Honest noisy baseline
6. Noise sweep
7. Forgery experiment
8. Replay experiment
9. Quantum-channel attack
10. Threshold-based detection
11. Forgery probability
12. LAR / FRR / FAR / ADR
13. End-to-end demo
```

This is the minimum credible demonstration.

---

# 35. Competition-Level Experiment Set

For a stronger SIH submission, add:

```text
14. Shot-count sweep
15. Attack-strength sweep
16. Threshold sensitivity
17. Security operating region
18. Impersonation experiment
19. Unauthorized verification experiment
20. Multiple quantum-channel attack types
21. Reproducibility across random seeds
22. Performance benchmark
23. Explainable evidence comparison
24. Automated experiment report
```

---

# 36. Expected Final Results

The project should ideally demonstrate experimentally that:

### Legitimate signatures

```text
High LAR
Low FRR
```

within the calibrated operating region.

### Malicious signatures

```text
Low FAR
High ADR
```

for the tested attack configurations.

### Noise

Honest noise should cause measurable statistical variation without automatically causing all legitimate signatures to be rejected.

### Attacks

Increasing attack strength should generally produce stronger measurable deviations, although the exact relationship must be determined experimentally rather than assumed.

### Forgery

The empirical forgery success rate should be measurable and reported with the number of attempts.

### Performance

Increasing shots should improve statistical stability while increasing simulation cost.

---

# 37. Scientific Interpretation Rules

The following rules are mandatory when interpreting results.

### Rule 1

A simulation result is not automatically a proof of real-world security.

### Rule 2

A high detection rate in a selected experiment does not mean universal attack detection.

### Rule 3

A low empirical forgery probability is not automatically a formal QDS security bound.

### Rule 4

A good simulator result does not guarantee physical quantum hardware performance.

### Rule 5

Noise tolerance demonstrated for one noise model does not imply tolerance for every physical noise source.

### Rule 6

Protocol-layer attacks must not be falsely described as purely quantum attacks.

### Rule 7

The detector's information-theoretic security must not be claimed unless supported by a formal security analysis.

---

# 38. Simulation Result vs Formal Security Claim

The project must explicitly separate:

```text
WHAT WE MEASURE
```

from:

```text
WHAT THE QDS SECURITY THEORY GUARANTEES
```

For example:

### Defensible statement

> “Under the simulated conditions, the deterministic detector rejected the tested forged signatures with an empirical false-acceptance rate of X%.”

### Not automatically defensible

> “The system guarantees zero probability of forgery.”

Similarly:

### Defensible

> “The teleportation-based simulation exhibited the expected measurement behaviour under the tested configuration.”

### Not automatically defensible

> “Our simulator proves information-theoretic security.”

---

# 39. Experiment Completion Criteria

An experiment is considered complete only when:

* objective is defined
* configuration is recorded
* control condition exists
* procedure is documented
* data is generated
* metrics are calculated
* result is reproducible
* interpretation is documented
* limitations are recorded

---

# 40. Experiment Tracking

Experiment progress should be maintained in:

```text
docs/experiments/results.md
```

Each completed experiment should contain:

```text
Experiment ID
Date
Configuration
Objective
Procedure
Results
Plots
Interpretation
Limitations
Conclusion
```

---

# 41. Recommended Execution Order

Experiments must be executed in this order:

```text
E01 Teleportation correctness
        ↓
E02 Honest baseline
        ↓
E03 Ideal vs noisy
        ↓
E04 Noise sweep
        ↓
E05 Shot sweep
        ↓
E06 Forgery
        ↓
E07 Replay
        ↓
E08 Impersonation
        ↓
E09 Unauthorized verification
        ↓
E10 Quantum-channel attack
        ↓
E11 Attack-strength sweep
        ↓
E12 Threshold sensitivity
        ↓
E13 Security operating region
        ↓
E14 Security metrics
        ↓
E15 Performance
        ↓
E16 End-to-end SIH demonstration
```

This order ensures that detection is built on validated quantum behaviour and calibrated honest behaviour rather than arbitrary thresholds.

---

# 42. Final Experimental Principle

Q-SHIELD experiments must follow:

```text
THEORY
   ↓
QUANTUM SIMULATION
   ↓
MEASUREMENT
   ↓
STATISTICS
   ↓
HONEST CALIBRATION
   ↓
THRESHOLD VALIDATION
   ↓
ATTACK SIMULATION
   ↓
DETECTION
   ↓
SECURITY METRICS
   ↓
PERFORMANCE EVALUATION
   ↓
SCIENTIFIC INTERPRETATION
```

The objective is not to manufacture impressive numbers.

The objective is to produce **reproducible evidence showing exactly when, why, and under which conditions the Q-SHIELD detector accepts legitimate behaviour or identifies suspicious/malicious behaviour.**

**Status:** DRAFT — update with measured results as implementation progresses.

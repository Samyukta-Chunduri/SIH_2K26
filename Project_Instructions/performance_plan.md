# PERFORMANCE_PLAN.md

# Q-SHIELD — Performance Evaluation Plan

**Project:** Q-SHIELD — Quantum Signature Security & Threat Detection Framework
**Problem Statement:** SIH 26141 — Quantum-Inspired Cyber Threat Detection for Digital Signature Security
**Status:** DRAFT
**Purpose:** Define how the computational efficiency, simulation performance, scalability, and verification cost of Q-SHIELD will be measured.

---

# 1. Purpose

Performance evaluation determines whether Q-SHIELD can perform quantum-signature verification and threat detection efficiently enough for a practical software prototype.

The performance study must answer:

1. How long does one verification take?
2. How does verification time change with the number of shots?
3. How does the number of states affect runtime?
4. How much additional cost does noise simulation introduce?
5. How much additional cost does attack simulation introduce?
6. How much time is spent on quantum simulation versus statistical detection?
7. How does repeated verification affect throughput?
8. What configuration provides a reasonable balance between statistical stability and runtime?
9. Can the dashboard remain responsive for normal demonstrations?

---

# 2. Important Scope

Q-SHIELD is primarily a **quantum-protocol simulation and detection framework**.

Therefore performance measurements refer to:

> **Classical computer simulation of the quantum protocol.**

They do not represent the execution speed of a physical quantum computer.

The report must clearly distinguish:

```text
Simulation performance
        ≠
Physical quantum hardware performance
```

---

# 3. Performance Goals

The prototype should aim for:

### Goal 1 — Efficient verification

A normal verification should complete within a practical time for an interactive demonstration.

### Goal 2 — Stable statistics

The selected shot count should provide sufficiently stable measurements without unnecessary simulation cost.

### Goal 3 — Explainable detection

Statistical analysis and security decision logic should add relatively small overhead compared with quantum-circuit simulation.

### Goal 4 — Reproducibility

Performance results should be measured under documented hardware and software conditions.

### Goal 5 — Scalable experimentation

The system should support larger batches of experiments without unnecessary repeated computation.

---

# 4. Performance Metrics

The following metrics should be considered.

---

## 4.1 Total Verification Time

$$
T_{total}
$$

Time required from verification start until final security decision.

This should include:

```text
quantum simulation
+
measurement processing
+
statistical analysis
+
protocol checks
+
decision engine
```

---

## 4.2 Quantum Simulation Time

$$
T_{quantum}
$$

Time spent executing the quantum circuit simulation.

---

## 4.3 Statistical Processing Time

$$
T_{stats}
$$

Time required to calculate:

* probabilities
* QBER
* fidelity
* expectation values
* baseline deviation
* threshold comparisons

---

## 4.4 Protocol Security Time

$$
T_{protocol}
$$

Time required for:

* identity validation
* session validation
* nonce checking
* replay checking
* authorization

---

## 4.5 Decision Time

$$
T_{decision}
$$

Time required by the deterministic rule engine to produce:

```text
ACCEPT
SUSPICIOUS
ATTACK
```

---

## 4.6 Throughput

Where meaningful:

$$
Throughput =
\frac{\text{number of verifications}}
{\text{execution time}}
$$

Report the unit clearly, for example:

```text
verifications/second
```

or:

```text
verifications/minute
```

---

# 5. Timing Breakdown

The preferred timing structure is:

```text
Verification
      │
      ├── Protocol checks
      │
      ├── Quantum circuit construction
      │
      ├── Quantum simulation
      │
      ├── Measurement processing
      │
      ├── Statistical analysis
      │
      └── Decision engine
```

The system should record each component separately where practical.

This makes optimization easier.

---

# 6. E-P01 — Baseline Verification Benchmark

## Objective

Measure the normal runtime of one honest verification.

---

## Configuration

Record:

```text
input state
number of shots
noise model
measurement bases
number of verification states
hardware
software versions
random seed
```

---

## Procedure

1. Start timer.
2. Execute verification.
3. Stop timer.
4. Record all timing components.
5. Repeat multiple times.
6. Calculate summary statistics.

---

## Required results

Report:

* mean runtime
* median runtime
* minimum runtime
* maximum runtime
* standard deviation where useful

The median is particularly useful when occasional operating-system or simulator delays produce outliers.

---

# 7. E-P02 — Shot-Count Benchmark

## Objective

Measure the relationship between measurement shots and runtime.

---

## Example configurations

```text
100 shots
250 shots
500 shots
1000 shots
2500 shots
5000 shots
10000 shots
```

The final values may be reduced if execution time becomes excessive.

---

## Procedure

For every shot count:

1. Run identical verification.
2. Record runtime.
3. Repeat.
4. Calculate average and variation.

---

## Required plot

```text
Number of shots
        ↓
Verification runtime
```

---

## Scientific purpose

This experiment demonstrates the trade-off:

```text
More shots
    ↓
More statistical stability
    ↓
Higher simulation cost
```

The selected demonstration shot count should therefore be justified experimentally.

---

# 8. E-P03 — State-Count Benchmark

## Objective

Measure the effect of verifying multiple quantum signature states.

---

## Example configurations

```text
1 state
2 states
3 states
4 states
6 states
```

The six-state configuration corresponds to the Pauli eigenstate set:

```text
|0>
|1>
|+>
|->
|+i>
|-i>
```

---

## Metrics

Record:

* total runtime
* runtime per state
* statistical processing time
* total verification time

---

## Required result

Determine whether runtime grows approximately with the number of independently simulated circuits.

Do not assume linearity without measuring it.

---

# 9. E-P04 — Noise Model Benchmark

## Objective

Measure how different noise configurations affect simulation cost.

---

## Conditions

Possible conditions:

```text
ideal
bit-flip
phase-flip
depolarizing
readout error
combined noise
```

Only noise models actually implemented should be tested.

---

## Metrics

Measure:

* runtime
* fidelity
* QBER
* LAR

This allows both performance and security effects to be studied.

---

# 10. E-P05 — Attack Simulation Benchmark

## Objective

Measure whether attack simulation introduces significant computational overhead.

---

## Attack categories

```text
forgery
replay
impersonation
unauthorized verification
quantum-channel manipulation
```

---

## Comparison

Compare:

```text
Honest verification
vs
Attack verification
```

Measure:

$$
\Delta T =
T_{attack}-T_{honest}
$$

and, where useful:

$$
Overhead =
\frac{T_{attack}-T_{honest}}
{T_{honest}}
\times100
$$

---

# 11. E-P06 — Statistical Detection Overhead

## Objective

Determine how much computational cost is added by statistical threat detection.

---

## Compare two pipelines

### Pipeline A

```text
Quantum simulation
→ measurement result
```

### Pipeline B

```text
Quantum simulation
→ measurement result
→ statistics
→ baseline comparison
→ evidence fusion
→ decision
```

---

## Metric

$$
T_{detection\ overhead}
=
T_{full}-T_{quantum}
$$

This demonstrates that the deterministic detection layer does not unnecessarily dominate computation.

---

# 12. E-P07 — Batch Verification Benchmark

## Objective

Measure performance when multiple verification requests are processed.

---

## Example batch sizes

```text
1
10
50
100
500
1000
```

Use smaller values if simulator runtime becomes excessive.

---

## Metrics

Record:

* total batch runtime
* average runtime per verification
* throughput
* memory usage where practical

---

## Important observation

The relationship between batch size and average runtime should be measured rather than assumed.

---

# 13. E-P08 — Repeated Experiment Performance

The attack laboratory may execute many simulations.

Measure:

```text
10 experiments
50 experiments
100 experiments
500 experiments
```

where practical.

---

## Metrics

* total runtime
* average experiment runtime
* throughput
* memory consumption
* data storage growth

---

# 14. Memory Usage

Memory should be monitored where practical.

Important factors include:

* number of shots
* number of circuits
* number of experiments
* stored measurement results
* stored history
* dashboard data

---

## Principle

The application should avoid unnecessarily retaining large raw datasets when only summary statistics are required.

However, raw results required for reproducibility should be retained according to the experiment-data policy.

---

# 15. Performance Hardware Metadata

Every benchmark should record the machine used.

Example:

```text
CPU:
GPU:
RAM:
Operating system:
Python version:
Qiskit version:
Qiskit Aer version:
NumPy version:
SciPy version:
```

For GPU experiments, also record:

```text
GPU model
GPU backend
GPU configuration
```

Do not compare benchmark numbers from different machines without identifying the hardware difference.

---

# 16. CPU vs GPU

If GPU simulation is supported and stable in the selected simulator configuration, an optional comparison can be performed.

Compare:

```text
CPU simulation
vs
GPU simulation
```

under identical experiment configurations.

---

## Metrics

* runtime
* throughput
* memory usage
* statistical results

The quantum-security decision must remain identical within expected numerical/statistical variation.

---

# 17. GPU Is Not a Security Requirement

Q-SHIELD must not require a GPU for correctness.

The architecture should support:

```text
CPU-only execution
```

as the baseline.

A GPU should be treated as an optional performance optimization.

---

# 18. Performance vs Statistical Accuracy

Performance cannot be optimized independently from verification reliability.

For example:

```text
100 shots
```

may be faster than:

```text
10,000 shots
```

but the smaller sample may produce less stable estimates.

Therefore the system should study:

$$
Performance
\leftrightarrow
Statistical\ Stability
$$

---

# 19. Recommended Shot Selection

The demonstration shot count should be selected using experimental evidence.

Recommended procedure:

```text
Test multiple shot counts
        ↓
Measure runtime
        ↓
Measure metric variation
        ↓
Measure LAR/FRR/ADR
        ↓
Select practical operating point
```

Do not simply select the largest possible shot count.

---

# 20. Performance Operating Point

The final demonstration configuration should identify a practical operating point.

Example:

```text
Shots:
1000

States:
6

Noise:
configured honest baseline

Detection:
enabled
```

The actual values must come from experiments.

---

# 21. Performance and Security Trade-Off

Increasing computational effort may improve statistical confidence.

For example:

```text
More shots
    ↓
Better probability estimates
    ↓
Potentially more reliable threshold comparison
    ↓
Higher runtime
```

Therefore the project should not optimize solely for minimum runtime.

The goal is:

> **Minimum practical computational cost that maintains the required experimental reliability.**

---

# 22. Performance Benchmark Repetition

A single timing measurement is insufficient.

For each configuration:

1. Perform a warm-up run if appropriate.
2. Execute multiple measured runs.
3. Record all timings.
4. Calculate summary statistics.
5. Report outliers where relevant.

---

# 23. Warm-Up Runs

If the environment has initialization overhead, use a warm-up execution.

Example:

```text
Warm-up:
1 run

Measured:
10+ runs
```

The warm-up run should not be included in the final average if its purpose is only to initialize the simulator/runtime.

The exact methodology must be documented.

---

# 24. Timing Methodology

Use a high-resolution monotonic timer suitable for performance measurement.

Do not use wall-clock timestamps such as:

```text
09:31:12
09:31:13
```

to calculate short execution times.

---

# 25. Avoiding Misleading Benchmarks

Do not compare:

```text
optimized implementation
```

against:

```text
unoptimized implementation
```

without documenting the differences.

Do not change:

* shot count
* noise model
* number of states
* hardware
* software version

between two configurations unless that variable is the subject of the experiment.

---

# 26. Performance Result Format

A benchmark result may use:

```json
{
  "experiment_id": "E-P02",
  "shots": 1000,
  "states": 6,
  "noise_model": "depolarizing",
  "noise_strength": 0.01,
  "runs": 20,
  "mean_runtime_ms": 0,
  "median_runtime_ms": 0,
  "std_runtime_ms": 0,
  "throughput": 0
}
```

The actual values must be generated by the experiment.

---

# 27. Required Performance Charts

The final project should produce at least:

### Chart 1

**Shots vs runtime**

```text
X-axis:
number of shots

Y-axis:
runtime
```

---

### Chart 2

**Shots vs statistical stability**

```text
X-axis:
number of shots

Y-axis:
metric variation
```

---

### Chart 3

**Number of states vs runtime**

```text
X-axis:
number of states

Y-axis:
runtime
```

---

### Chart 4

**Noise model vs runtime**

```text
X-axis:
noise configuration

Y-axis:
runtime
```

---

### Chart 5

**Attack type vs runtime**

```text
X-axis:
attack type

Y-axis:
verification runtime
```

---

# 28. Required Performance Tables

## Table A — Shot benchmark

| Shots | Mean Runtime | Median Runtime | Metric Variation |
| ----: | -----------: | -------------: | ---------------: |
|   100 |          ... |            ... |              ... |
|   500 |          ... |            ... |              ... |
|  1000 |          ... |            ... |              ... |
|  5000 |          ... |            ... |              ... |
| 10000 |          ... |            ... |              ... |

---

## Table B — Verification breakdown

| Component              | Mean Time |
| ---------------------- | --------: |
| Protocol checks        |       ... |
| Circuit construction   |       ... |
| Quantum simulation     |       ... |
| Measurement processing |       ... |
| Statistics             |       ... |
| Detection              |       ... |
| Total                  |       ... |

---

## Table C — Attack overhead

| Scenario       | Runtime | Overhead |
| -------------- | ------: | -------: |
| Honest         |     ... |        — |
| Forgery        |     ... |      ... |
| Replay         |     ... |      ... |
| Impersonation  |     ... |      ... |
| Channel attack |     ... |      ... |

---

# 29. Performance Acceptance Criteria

Performance criteria should be defined after initial measurements rather than invented before benchmarking.

The project should evaluate:

```text
Is interactive verification practical?
Is statistical accuracy acceptable?
Is simulation cost reasonable?
Does the detector introduce significant overhead?
Can the attack laboratory run a useful number of experiments?
```

The exact numerical targets should be documented in:

```text
DECISIONS.md
```

after initial benchmarking.

---

# 30. Performance Optimization Priorities

Optimization should follow this order.

### Priority 1 — Correctness

Never sacrifice scientific correctness for speed.

### Priority 2 — Avoid unnecessary recomputation

Reuse results where scientifically valid.

### Priority 3 — Reduce unnecessary data processing

Process measurement results efficiently.

### Priority 4 — Batch compatible experiments

Where supported and scientifically equivalent.

### Priority 5 — Parallelize independent experiments

Only when reproducibility and resource usage remain controlled.

### Priority 6 — Optional hardware acceleration

Use GPU acceleration only if it provides a meaningful benefit.

---

# 31. Caching

Caching may be used for expensive deterministic computations.

However, cached results must never hide experimental randomness or invalidate attack experiments.

A cached result should include enough metadata to ensure configuration equivalence.

For example:

```text
state
circuit configuration
shots
noise model
noise parameters
random seed
software version
```

If any security-relevant configuration changes, the cached result must not automatically be reused.

---

# 32. Parallel Experiment Execution

Independent attack experiments may be executed in parallel.

Example:

```text
Experiment A ─┐
Experiment B ─┼──→ Result aggregation
Experiment C ─┤
Experiment D ─┘
```

Parallel execution must not mix results between experiments.

Each result must retain:

* experiment ID
* configuration
* seed
* attack type
* trial number

---

# 33. Dashboard Performance

The Streamlit dashboard should remain responsive for normal interactive use.

Avoid:

```text
User clicks Verify
        ↓
Thousands of unnecessary simulations
        ↓
UI appears frozen
```

Instead:

```text
User clicks Verify
        ↓
Run configured simulation
        ↓
Display results
```

Large experiments should be available through the Attack Laboratory or experiment runner rather than blocking the primary verification screen.

---

# 34. Large Experiment Mode

Large experiment sweeps should be separated from interactive verification.

Example:

```text
Interactive Mode
→ one verification
→ immediate result

Experiment Mode
→ many trials
→ statistical aggregation
→ plots
→ saved results
```

This separation improves usability.

---

# 35. Performance and Determinism

The security decision must be deterministic for the same:

```text
input
configuration
measurement data
baseline
threshold configuration
```

Performance optimizations must not alter the decision logic.

If random simulation is used, reproducibility should be possible through recorded seeds.

---

# 36. Performance Regression Testing

Performance should be monitored after major changes.

For important releases compare:

```text
previous version
vs
current version
```

under identical configurations.

Track:

* runtime
* memory
* throughput
* detection metrics

A significant performance regression should be investigated.

---

# 37. Performance-Security Regression

A performance optimization must not silently change:

* measurement distributions
* QBER
* fidelity
* baseline
* threshold decisions
* attack detection
* legitimate acceptance

Therefore important optimizations require both:

```text
Performance tests
+
Security regression tests
```

---

# 38. Complexity Considerations

At a high level, simulation cost depends on factors including:

```text
number of circuits
number of shots
circuit depth
number of qubits
noise-model complexity
number of experiments
```

The project should report measured performance rather than making unsupported asymptotic claims about a specific simulator implementation.

---

# 39. Minimum SIH Performance Evaluation

If time is limited, perform:

```text
1. Baseline verification timing
2. Shot-count sweep
3. State-count sweep
4. Quantum-vs-detection timing breakdown
5. Attack runtime comparison
```

These are sufficient for a basic performance story.

---

# 40. Competition-Level Performance Evaluation

For a stronger submission, additionally perform:

```text
6. Noise-model benchmark
7. Batch verification
8. Attack-strength performance
9. Memory measurements
10. CPU/GPU comparison if supported
11. Parallel experiment benchmark
12. Performance regression benchmark
13. Dashboard responsiveness test
```

---

# 41. Performance Report Structure

The final performance report should contain:

```text
1. Hardware
2. Software environment
3. Benchmark methodology
4. Baseline runtime
5. Shot-count results
6. State-count results
7. Noise results
8. Attack results
9. Statistical overhead
10. Batch performance
11. Memory usage
12. Optimization results
13. Selected operating point
14. Limitations
15. Conclusion
```

---

# 42. Performance Limitations

The report must explicitly mention limitations such as:

* simulator-dependent runtime
* hardware-dependent runtime
* operating-system scheduling
* Python overhead
* noise-model implementation differences
* finite experimental sample sizes
* simulator scaling limitations
* absence of physical quantum hardware measurements

---

# 43. What Must Not Be Claimed

Do not claim:

> “Q-SHIELD is faster than real quantum computers.”

Do not claim:

> “Q-SHIELD has constant-time quantum verification.”

Do not claim:

> “The simulator performance proves real-world quantum-system performance.”

Do not claim:

> “GPU acceleration is required.”

Do not claim:

> “More shots always mean better security.”

More shots generally improve statistical estimation, but security depends on the protocol, detector, thresholds, assumptions, and attack model.

---

# 44. Final Performance Principle

Q-SHIELD performance evaluation follows:

```text
CORRECTNESS
     ↓
STATISTICAL RELIABILITY
     ↓
MEASURED RUNTIME
     ↓
OPTIMIZATION
     ↓
REGRESSION TESTING
```

The goal is not simply:

```text
FASTEST POSSIBLE
```

The goal is:

```text
FAST ENOUGH
+
STATISTICALLY RELIABLE
+
SCIENTIFICALLY CORRECT
+
REPRODUCIBLE
```

---

# 45. Final Performance Objective

The final Q-SHIELD implementation should be able to demonstrate:

```text
Quantum protocol simulation
        ↓
Measurement
        ↓
Statistical analysis
        ↓
Threat detection
        ↓
Deterministic decision
```

with a measured and documented computational cost.

The project should use experimental evidence to select its operating configuration rather than choosing performance parameters arbitrarily.

**Status:** DRAFT — update with measured benchmark results after implementation.

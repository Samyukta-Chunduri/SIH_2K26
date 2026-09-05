# Q-SHIELD — Mathematical Model

## 1. Purpose

This document defines the mathematical quantities used by Q-SHIELD for:

* Quantum-state representation
* Pauli operators
* Projective measurements
* Bell-state verification
* Quantum teleportation
* Measurement statistics
* Expectation values
* Variance
* Fidelity
* QBER/error rate
* Honest operating regions
* Statistical thresholds
* Forgery probability
* False acceptance/rejection
* Attack detection performance

The purpose is to ensure that the implementation uses mathematically defined quantities rather than arbitrary scores.

---

# 2. Mathematical Design Principles

Q-SHIELD follows these principles:

1. Quantum behavior is represented mathematically.
2. Measurement outcomes are probabilistic.
3. Statistical quantities are estimated from repeated measurements.
4. Thresholds must have a documented statistical justification.
5. Final decisions are deterministic once the observations and configuration are fixed.
6. No machine-learning model is used.
7. No arbitrary "security score" should replace meaningful physical/statistical quantities.
8. Empirical estimates must not be confused with theoretical security bounds.
9. Simulation results must include their experimental conditions.

---

# 3. Basic Quantum State Representation

A single qubit can be represented as:

$$
|\psi\rangle
=
\alpha|0\rangle+\beta|1\rangle
$$

where:

$$
\alpha,\beta\in\mathbb{C}
$$

and:

$$
|\alpha|^2+|\beta|^2=1
$$

The computational basis states are:

$$
|0\rangle=
\begin{bmatrix}
1\\
0
\end{bmatrix}
$$

and:

$$
|1\rangle=
\begin{bmatrix}
0\\
1
\end{bmatrix}
$$

---

# 4. Measurement Probability

For a state:

$$
|\psi\rangle=\alpha|0\rangle+\beta|1\rangle
$$

measurement in the computational basis gives:

$$
P(0)=|\alpha|^2
$$

and:

$$
P(1)=|\beta|^2
$$

Therefore:

$$
P(0)+P(1)=1
$$

This is the basis for interpreting repeated quantum measurements.

---

# 5. Born Rule

For a projective measurement represented by projector \(P_i\):

$$
P(i)
=
\langle\psi|P_i|\psi\rangle
$$

For a density matrix \(\rho\):

$$
P(i)
=
\operatorname{Tr}(P_i\rho)
$$

The implementation should use the appropriate representation for the simulation being performed.

---

# 6. Pauli Operators

The Pauli matrices are:

## Pauli-X

$$
X=
\begin{bmatrix}
0&1\\
1&0
\end{bmatrix}
$$

It produces:

$$
X|0\rangle=|1\rangle
$$

$$
X|1\rangle=|0\rangle
$$

---

## Pauli-Y

$$
Y=
\begin{bmatrix}
0&-i\\
i&0
\end{bmatrix}
$$

---

## Pauli-Z

$$
Z=
\begin{bmatrix}
1&0\\
0&-1
\end{bmatrix}
$$

It produces:

$$
Z|0\rangle=|0\rangle
$$

$$
Z|1\rangle=-|1\rangle
$$

---

# 7. Identity Operator

The identity operator is:

$$
I=
\begin{bmatrix}
1&0\\
0&1
\end{bmatrix}
$$

It leaves the quantum state unchanged:

$$
I|\psi\rangle=|\psi\rangle
$$

---

# 8. Pauli Eigenstates

The Pauli eigenstates used by the prototype are:

### Z eigenstates

$$
|0\rangle,\ |1\rangle
$$

### X eigenstates

$$
|+\rangle
=
\frac{|0\rangle+|1\rangle}{\sqrt2}
$$

$$
|-\rangle
=
\frac{|0\rangle-|1\rangle}{\sqrt2}
$$

### Y eigenstates

$$
|+i\rangle
=
\frac{|0\rangle+i|1\rangle}{\sqrt2}
$$

$$
|-i\rangle
=
\frac{|0\rangle-i|1\rangle}{\sqrt2}
$$

---

# 9. Hadamard Operator

The Hadamard gate is:

$$
H=
\frac{1}{\sqrt2}
\begin{bmatrix}
1&1\\
1&-1
\end{bmatrix}
$$

It transforms:

$$
H|0\rangle=|+\rangle
$$

and:

$$
H|1\rangle=|-\rangle
$$

The Hadamard gate is used in Bell-state preparation and teleportation.

---

# 10. Bell State

The prototype uses the Bell state:

$$
|\Phi^+\rangle
=
\frac{|00\rangle+|11\rangle}{\sqrt2}
$$

The corresponding state vector is:

$$
|\Phi^+\rangle
=
\frac{1}{\sqrt2}
\begin{bmatrix}
1\\
0\\
0\\
1
\end{bmatrix}
$$

---

# 11. Bell-State Preparation

The standard circuit is:

```text
q0: ──H────●──
           │
q1: ───────X──
```

Starting from:

$$
|00\rangle
$$

after \(H\):

$$
\frac{|00\rangle+|10\rangle}{\sqrt2}
$$

After CNOT:

$$
\frac{|00\rangle+|11\rangle}{\sqrt2}
$$

which is:

$$
|\Phi^+\rangle
$$

---

# 12. Bell-State Measurement Statistics

For ideal computational-basis measurement:

$$
P(00)=\frac12
$$

$$
P(11)=\frac12
$$

and:

$$
P(01)=P(10)=0
$$

With a finite number of shots, measured frequencies will fluctuate around these theoretical probabilities.

---

# 13. Empirical Probability

Suppose a circuit is executed \(N\) times.

If outcome \(i\) occurs \(n_i\) times:

$$
\hat p_i=
\frac{n_i}{N}
$$

where:

* \(N\) = total shots
* \(n_i\) = count for outcome \(i\)
* \(\hat p_i\) = observed probability

The symbol \(\hat p\) indicates an estimate rather than the exact theoretical probability.

---

# 14. Measurement Counts

The simulator should preserve raw measurement counts.

For example:

```text
00 → 498
11 → 502
```

with:

$$
N=1000
$$

Then:

$$
\hat p(00)=0.498
$$

and:

$$
\hat p(11)=0.502
$$

Raw counts should be retained because they allow later statistical analysis.

---

# 15. Sample Mean

Suppose a measured variable produces values:

$$
x_1,x_2,\ldots,x_N
$$

The sample mean is:

$$
\bar{x}
=
\frac{1}{N}
\sum_{i=1}^{N}x_i
$$

The sample mean estimates the expected value.

---

# 16. Sample Variance

The sample variance is:

$$
s^2
=
\frac{1}{N-1}
\sum_{i=1}^{N}
(x_i-\bar{x})^2
$$

The sample standard deviation is:

$$
s=\sqrt{s^2}
$$

The \(N-1\) denominator is used for the usual unbiased sample variance estimate.

---

# 17. Standard Error

For an estimated sample mean:

$$
SE=
\frac{s}{\sqrt N}
$$

The standard error describes uncertainty in the estimated mean.

---

# 18. Bernoulli Measurement Outcomes

Many quantum measurement quantities can be represented as binary variables.

For example:

```text
correct = 1
incorrect = 0
```

If the probability of a correct outcome is \(p\), then:

$$
E[X]=p
$$

and:

$$
\operatorname{Var}(X)=p(1-p)
$$

For \(N\) independent observations, the estimated proportion is:

$$
\hat p=\frac{k}{N}
$$

where \(k\) is the number of successes.

---

# 19. Measurement Error Rate

Suppose:

$$
N_{\text{total}}
$$

measurements are performed and:

$$
N_{\text{error}}
$$

are inconsistent with the expected result.

Define:

$$
\widehat{e}
=
\frac{N_{\text{error}}}
{N_{\text{total}}}
$$

This may be used as an empirical error rate.

---

# 20. QBER

Quantum Bit Error Rate (QBER) can be represented as:

$$
QBER=
\frac{N_{\text{errors}}}
{N_{\text{valid comparisons}}}
$$

where an error occurs when an observed result disagrees with the expected result under the defined comparison rule.

Important:

> QBER is meaningful only after the expected state/basis and comparison procedure have been explicitly defined.

Q-SHIELD must not calculate a QBER without documenting what constitutes an error.

---

# 21. Fidelity

For two pure states:

$$
|\psi\rangle
$$

and:

$$
|\phi\rangle
$$

the state fidelity can be defined as:

$$
F=
|\langle\psi|\phi\rangle|^2
$$

where:

$$
0\leq F\leq1
$$

Interpretation:

```text
F = 1
```

means identical pure states up to global phase.

A smaller value indicates greater difference.

---

# 22. Fidelity for Density Matrices

If mixed states are used, fidelity requires an appropriate density-matrix definition.

The implementation must use a standard, documented definition rather than inventing one.

For two density matrices \(\rho\) and \(\sigma\), one common convention is:

$$
F(\rho,\sigma)
=
\left(
\operatorname{Tr}
\sqrt{
\sqrt{\rho}\sigma\sqrt{\rho}
}
\right)^2
$$

If a library uses a different convention, the project must document that convention explicitly.

---

# 23. Teleportation Fidelity

Teleportation quality may be evaluated by comparing:

```text
Input state
```

with:

```text
Recovered state
```

using:

$$
F_{\text{teleport}}
=
|\langle\psi_{\text{input}}
|
\psi_{\text{recovered}}\rangle|^2
$$

for pure states.

Under an ideal noiseless simulation:

$$
F_{\text{teleport}}\approx1
$$

subject to the simulation representation and numerical precision.

---

# 24. Expected Measurement Distribution

For a given expected state and measurement basis, define:

$$
p_i^{(H)}
$$

as the expected honest probability for outcome \(i\).

The superscript \(H\) denotes honest operation.

The observed distribution is:

$$
\hat p_i
$$

The detector compares:

$$
\hat p_i
$$

against:

$$
p_i^{(H)}
$$

or against an experimentally calibrated honest distribution.

---

# 25. Distribution Difference

A simple probability deviation is:

$$
d_i=
|\hat p_i-p_i^{(H)}|
$$

A maximum deviation can be defined as:

$$
D_{\infty}
=
\max_i
|\hat p_i-p_i^{(H)}|
$$

This provides a straightforward measure of distributional deviation.

The final detector should not rely on this metric alone unless justified by experiments.

---

# 26. Total Variation Distance

For two discrete probability distributions \(P\) and \(Q\):

$$
D_{TV}(P,Q)
=
\frac12
\sum_i |P_i-Q_i|
$$

For the observed and expected distributions:

$$
D_{TV}
=
\frac12
\sum_i
|\hat p_i-p_i^{(H)}|
$$

This can be used as an interpretable distribution-distance metric.

---

# 27. Expectation Values

For an observable \(A\) and state \(\rho\):

$$
\langle A\rangle
=
\operatorname{Tr}(\rho A)
$$

For a pure state:

$$
\langle A\rangle
=
\langle\psi|A|\psi\rangle
$$

For Pauli observables:

$$
\langle X\rangle,\quad
\langle Y\rangle,\quad
\langle Z\rangle
$$

can characterize the state.

---

# 28. Relationship Between Pauli Measurements and State

For a qubit state:

$$
\rho
=
\frac12
(I+r_xX+r_yY+r_zZ)
$$

where:

$$
r_x=\langle X\rangle
$$

$$
r_y=\langle Y\rangle
$$

$$
r_z=\langle Z\rangle
$$

The vector:

$$
\mathbf r=(r_x,r_y,r_z)
$$

is the Bloch vector.

For a valid single-qubit state:

$$
|\mathbf r|\leq1
$$

---

# 29. Empirical Pauli Expectations

For measurement results encoded as:

```text
+1
-1
```

the expectation can be estimated by:

$$
\widehat{\langle P\rangle}
=
\frac{N_{+}-N_{-}}
{N}
$$

where:

* \(N_+\) = number of \(+1\) outcomes
* \(N_-\) = number of \(-1\) outcomes
* \(N=N_++N_-\)

This allows the detector to compare observed Pauli statistics against an honest baseline.

---

# 30. Pauli-Eigenstate Expectations

For ideal states:

### \(|0\rangle\)

$$
\langle Z\rangle=1
$$

### \(|1\rangle\)

$$
\langle Z\rangle=-1
$$

### \(|+\rangle\)

$$
\langle X\rangle=1
$$

### \(|-\rangle\)

$$
\langle X\rangle=-1
$$

### \(|+i\rangle\)

$$
\langle Y\rangle=1
$$

### \(|-i\rangle\)

$$
\langle Y\rangle=-1
$$

The corresponding expectations for the other Pauli operators are zero for these ideal eigenstates.

---

# 31. Bell Correlation

For a Bell state, correlations can be evaluated using joint measurements.

Possible observables include:

$$
X\otimes X
$$

$$
Y\otimes Y
$$

$$
Z\otimes Z
$$

For:

$$
|\Phi^+\rangle
$$

the ideal correlations include:

$$
\langle X\otimes X\rangle=1
$$

$$
\langle Y\otimes Y\rangle=-1
$$

$$
\langle Z\otimes Z\rangle=1
$$

These quantities can be used to verify entanglement behavior and detect degradation.

---

# 32. Bell Correlation Estimate

If joint measurement outcomes are encoded as \(+1\) or \(-1\), the empirical correlation can be estimated by:

$$
\widehat C
=
\frac1N
\sum_{i=1}^{N}
a_i b_i
$$

where:

$$
a_i,b_i\in\{-1,+1\}
$$

For ideal correlated measurements:

$$
\widehat C\approx1
$$

For ideal anti-correlated measurements:

$$
\widehat C\approx-1
$$

subject to finite-shot fluctuations.

---

# 33. Honest Baseline Model

For a metric \(M\), suppose \(N_H\) honest calibration runs produce:

$$
M_1,M_2,\ldots,M_{N_H}
$$

The baseline mean is:

$$
\bar M_H
=
\frac{1}{N_H}
\sum_{i=1}^{N_H}M_i
$$

The sample standard deviation is:

$$
s_H
=
\sqrt{
\frac{1}{N_H-1}
\sum_{i=1}^{N_H}
(M_i-\bar M_H)^2
}
$$

---

# 34. Baseline Operating Region

A simple baseline interval can be defined as:

$$
[\bar M_H-k s_H,\,
\bar M_H+k s_H]
$$

where \(k\) is a documented statistical parameter.

The value of \(k\) must not be arbitrarily selected.

It must be:

* justified statistically,
* configurable,
* documented,
* evaluated experimentally.

---

# 35. Confidence Intervals

For sufficiently appropriate conditions, an approximate confidence interval for a mean can be represented as:

$$
\bar M
\pm
z_{\alpha/2}
\frac{s}{\sqrt N}
$$

where:

* \(1-\alpha\) is the confidence level,
* \(z_{\alpha/2}\) is the corresponding standard-normal critical value.

For small samples or non-normal data, a different appropriate statistical method may be required.

The implementation must not blindly assume normality.

---

# 36. Proportion Confidence Intervals

Measurement probabilities are proportions.

For:

$$
\hat p=\frac{k}{N}
$$

a simple normal approximation is:

$$
\hat p
\pm
z_{\alpha/2}
\sqrt{
\frac{\hat p(1-\hat p)}{N}
}
$$

However, this approximation can behave poorly for probabilities near 0 or 1 or for small sample sizes.

Therefore, an appropriate proportion interval method should be selected during implementation.

---

# 37. Threshold Definition

A threshold is a rule boundary separating expected and unexpected behavior.

For a metric where higher values indicate worse behavior:

$$
M>T
$$

may indicate deviation.

For a metric where lower values indicate worse behavior:

$$
M<T
$$

may indicate deviation.

The direction must be documented for every metric.

---

# 38. Threshold Categories

The system may use:

```text
Normal region
Suspicious region
Attack region
```

Conceptually:

```text
NORMAL
    │
    ▼
SUSPICIOUS
    │
    ▼
ATTACK
```

However, multiple metrics may be needed to make a final attack decision.

---

# 39. Deterministic Threshold Rule

For a metric \(M\), a simple rule can be:

$$
D(M)=
\begin{cases}
0,&M\in R_H\\
1,&M\notin R_H
\end{cases}
$$

where \(R_H\) is the documented honest operating region.

The result is deterministic.

---

# 40. Multi-Metric Detection

Suppose the detector observes:

$$
M_1,M_2,\ldots,M_k
$$

Examples:

```text
Fidelity
QBER
X deviation
Y deviation
Z deviation
Bell correlation
Protocol validity
```

Each metric produces evidence.

The detector then applies explicit rules.

Example:

```text
IF
    fidelity is outside allowed region
AND
    QBER is above threshold
THEN
    quantum deviation = TRUE
```

This is a rule-based detector, not machine learning.

---

# 41. Evidence Fusion

A conceptual deterministic rule may be:

$$
Decision
=
f(
E_Q,
E_S,
E_P
)
$$

where:

* \(E_Q\) = quantum evidence
* \(E_S\) = signature evidence
* \(E_P\) = protocol evidence

The function \(f\) must be explicitly defined.

It must not be a learned classifier.

---

# 42. Example Evidence Logic

For example:

```text
IF replay_detected
    → ATTACK / REPLAY

ELSE IF identity_invalid
    → ATTACK / IMPERSONATION

ELSE IF verifier_unauthorized
    → ATTACK / UNAUTHORIZED_VERIFICATION

ELSE IF quantum_deviation AND signature_invalid
    → ATTACK / FORGERY

ELSE IF quantum_deviation
    → SUSPICIOUS or CHANNEL_MANIPULATION
```

This is only an initial conceptual rule.

The final ordering and conditions must be finalized in `SECURITY_MODEL.md`.

---

# 43. Forgery Probability

Suppose there are:

$$
N_F
$$

forgery attempts and:

$$
N_{FA}
$$

false acceptances.

The empirical forgery success probability is:

$$
\hat p_F
=
\frac{N_{FA}}{N_F}
$$

This quantity should be reported with its experimental conditions.

---

# 44. Zero-Observation Case

If:

$$
N_{FA}=0
$$

then:

$$
\hat p_F=0
$$

is the observed empirical rate.

However:

> Observing zero successful forgeries does not mathematically prove that the true forgery probability is zero.

The report should therefore state:

```text
No false acceptances observed in N attempts.
```

rather than:

```text
Forgery probability is exactly zero.
```

---

# 45. False Acceptance Rate

For malicious attempts:

$$
FAR
=
\frac{
N_{\text{malicious accepted}}
}{
N_{\text{malicious attempts}}
}
$$

A lower FAR is generally desirable.

---

# 46. False Rejection Rate

For legitimate attempts:

$$
FRR
=
\frac{
N_{\text{legitimate rejected}}
}{
N_{\text{legitimate attempts}}
}
$$

A lower FRR indicates fewer legitimate signatures being incorrectly rejected.

---

# 47. Legitimate Acceptance Rate

$$
LAR
=
\frac{
N_{\text{legitimate accepted}}
}{
N_{\text{legitimate attempts}}
}
$$

Ideally:

$$
LAR\rightarrow1
$$

under the tested operating conditions.

---

# 48. Attack Detection Rate

$$
ADR
=
\frac{
N_{\text{attacks detected}}
}{
N_{\text{attack attempts}}
}
$$

The value depends on:

* Attack type
* Attack strength
* Noise
* Number of shots
* Thresholds
* Statistical uncertainty

Therefore ADR must always be reported with experimental conditions.

---

# 49. Confusion Matrix

For binary attack detection:

|                   | Predicted Legitimate | Predicted Attack |
| ----------------- | -------------------: | ---------------: |
| Actual Legitimate |        True Negative |   False Positive |
| Actual Attack     |       False Negative |    True Positive |

Depending on the terminology used by the project, the labels must be defined carefully.

The project should avoid mixing classification terminology with cryptographic terminology without definitions.

---

# 50. Three-State Decision

Because Q-SHIELD includes a suspicious state:

```text
ACCEPT
SUSPICIOUS
ATTACK
```

evaluation should not reduce everything to binary classification.

The system should report:

* Accepted legitimate attempts
* Suspicious legitimate attempts
* Rejected legitimate attempts
* Accepted attacks
* Suspicious attacks
* Detected attacks

This gives a more accurate view of detector behavior.

---

# 51. Statistical Significance

When comparing honest and attack distributions, the project may use statistical hypothesis testing where appropriate.

Possible hypotheses:

$$
H_0:
\text{observed behavior is consistent with honest behavior}
$$

$$
H_1:
\text{observed behavior is inconsistent with honest behavior}
$$

The choice of test must depend on the data type and assumptions.

The AI must not select a statistical test merely because it is convenient.

---

# 52. Shot Dependence

The number of shots affects measurement uncertainty.

Generally:

```text
More shots
    ↓
More stable empirical probabilities
    ↓
Better estimate of underlying distribution
```

But:

```text
More shots
    ↓
Higher simulation/verification cost
```

Therefore Q-SHIELD should experimentally study:

$$
\text{shots}
\rightarrow
\text{statistical stability}
$$

and:

$$
\text{shots}
\rightarrow
\text{verification cost}
$$

---

# 53. Noise Dependence

Let:

$$
\eta
$$

represent a noise parameter.

Then an honest metric can be considered as:

$$
M_H(\eta)
$$

The baseline should therefore be associated with its noise configuration.

Conceptually:

```text
Noise configuration
        ↓
Honest calibration
        ↓
Noise-specific baseline
        ↓
Verification
```

A baseline generated under one noise condition should not automatically be applied to a substantially different noise condition.

---

# 54. Attack Strength

Let:

$$
a
$$

represent attack strength.

The observed metric may then be represented conceptually as:

$$
M(\eta,a)
$$

Experiments should investigate how detection changes as:

$$
a
$$

increases.

---

# 55. Noise-Attack Separation

The detector should evaluate:

$$
M_H(\eta)
$$

against:

$$
M_A(\eta,a)
$$

rather than comparing an attack at one noise level against an honest baseline at another unrelated noise level.

This allows a fairer experiment:

```text
Same noise
+
Different attack condition
```

---

# 56. Security Operating Region

Define a region of operating conditions where the detector meets the desired experimental criteria.

For example:

```text
Noise level
    ×
Attack strength
    ×
Shots
```

The resulting experimental surface can show:

```text
Reliable detection
Marginal detection
Poor detection
```

The exact boundaries must be measured experimentally.

---

# 57. Statistical Calibration

The recommended Q-SHIELD process is:

```text
1. Select noise configuration.

2. Run many honest executions.

3. Collect measurement statistics.

4. Estimate baseline distributions.

5. Determine statistically justified operating regions.

6. Freeze/version the baseline.

7. Run attack experiments.

8. Compare attack behavior against the honest baseline.

9. Measure FAR, FRR, ADR and related metrics.

10. Repeat for other noise levels and shot counts.
```

---

# 58. Baseline Version

Every baseline should have an identifier.

Conceptually:

```text
baseline_id
noise_model
noise_parameters
shots
number_of_calibration_runs
creation_time
statistical_method
threshold_configuration
```

This is important for reproducibility.

---

# 59. Reproducibility Metadata

Every experiment should record:

```text
experiment_id
random_seed where applicable
software version
Qiskit version
Aer version
noise configuration
number of shots
number of trials
protocol configuration
baseline_id
threshold configuration
attack configuration
```

The exact fields may evolve.

---

# 60. Numerical Precision

Quantum-state calculations may involve floating-point arithmetic.

Therefore mathematically zero quantities may appear as very small values such as:

$$
10^{-15}
$$

The implementation should use appropriate numerical tolerances.

It must not interpret every tiny floating-point deviation as a security event.

---

# 61. Numerical Tolerance

For comparing floating-point quantities:

$$
|x-y|<\epsilon
$$

may be considered numerically equivalent.

The tolerance \(\epsilon\) must be:

* Explicit
* Configurable where appropriate
* Tested
* Documented

It must not be confused with a security threshold.

---

# 62. Security Threshold vs Numerical Tolerance

These are different concepts.

### Numerical tolerance

Handles:

```text
Floating-point precision
```

### Security threshold

Handles:

```text
Statistical deviation from expected behavior
```

Never use one as a substitute for the other.

---

# 63. Statistical Threshold vs Cryptographic Security Bound

These are also different.

A detector threshold answers:

> "Is this observed behavior unusual under our calibrated honest model?"

A cryptographic security bound answers:

> "What is the theoretically bounded probability of a successful attack under the protocol assumptions?"

Q-SHIELD must not present a detector threshold as a cryptographic security proof.

---

# 64. Information-Theoretic Security

The mathematical detector does not itself establish information-theoretic security.

Any information-theoretic security claim must come from the underlying QDS protocol and its assumptions.

Q-SHIELD instead evaluates:

```text
Observed behavior
+
Statistical evidence
+
Protocol evidence
```

---

# 65. Minimum Mathematical Metrics

The MVP should implement at least:

```text
Measurement counts
Measurement probabilities
Expected probabilities
Measurement error rate / QBER
Teleportation fidelity
Pauli expectation values
Honest baseline statistics
Threshold comparison
Forgery probability
FAR
FRR
Attack detection rate
```

---

# 66. Recommended Extended Metrics

If implementation time permits:

```text
Total variation distance
Bell correlations
Confidence intervals
Standard error
Distribution comparison
Noise-vs-attack separation
Shots-vs-stability analysis
```

---

# 67. Metrics That Must Not Be Invented

Do not introduce unexplained quantities such as:

```text
Quantum Security Score = 87.4
Quantum Trust Index = 0.92
AI Threat Probability = 0.83
```

unless the mathematical definition, purpose, interpretation, and validation are explicitly documented.

A visually attractive score is not automatically scientifically meaningful.

---

# 68. Mathematical Dependency Flow

The mathematical pipeline is:

```text
Quantum state
     ↓
Quantum circuit
     ↓
Measurement
     ↓
Raw counts
     ↓
Empirical probabilities
     ↓
Expectations / fidelity / QBER / correlations
     ↓
Honest baseline
     ↓
Statistical deviation
     ↓
Threshold evaluation
     ↓
Security evidence
     ↓
Deterministic decision
```

---

# 69. Mathematical Model for Honest Verification

For an honest execution:

$$
O_H
\sim
P_H
$$

where:

* \(O_H\) represents observed honest measurements
* \(P_H\) represents the honest operating distribution

The detector checks whether the observed metrics remain consistent with the calibrated honest behavior.

---

# 70. Mathematical Model for Attack Verification

For an attack:

$$
O_A
\sim
P_A
$$

The detector evaluates whether:

$$
P_A
$$

is sufficiently distinguishable from:

$$
P_H
$$

under the chosen experiment.

This distinction is important because some attacks may produce distributions that overlap strongly with honest behavior.

---

# 71. No Perfect Separation Assumption

Q-SHIELD must not assume:

$$
P_H\cap P_A=\emptyset
$$

In realistic noisy conditions, honest and attack distributions may overlap.

Therefore:

```text
Attack detection
≠
Perfect classification
```

The project must measure the overlap experimentally.

---

# 72. Deterministic Final Decision

Once:

```text
Measurement data
Baseline
Threshold configuration
Protocol evidence
```

are fixed, the decision function must be deterministic:

$$
D:
E
\rightarrow
\{
ACCEPT,
SUSPICIOUS,
ATTACK
\}
$$

where \(E\) is the complete evidence set.

No ML model is used.

No hidden randomness should alter the final classification.

---

# 73. Example Deterministic Rule

A simplified conceptual rule:

$$
D(E)=
\begin{cases}
ATTACK,&
\text{replay detected}\\
ATTACK,&
\text{identity invalid}\\
ATTACK,&
\text{authorization invalid}\\
ATTACK,&
\text{forgery criteria satisfied}\\
SUSPICIOUS,&
\text{quantum deviation detected but attack attribution insufficient}\\
ACCEPT,&
\text{all required checks pass}
\end{cases}
$$

The final rule hierarchy must be specified in `SECURITY_MODEL.md`.

---

# 74. Experimental Reporting

Every reported metric should include its context.

For example:

```text
Attack:
    Channel manipulation

Noise:
    Depolarizing p = ...

Shots:
    10,000

Trials:
    1,000

Detection rate:
    ...

False acceptance:
    ...

Baseline:
    baseline_003
```

A metric without experimental context can be misleading.

---

# 75. Statistical Model Limitations

The mathematical model has important limitations:

1. Finite shots produce statistical uncertainty.
2. Simulation is not identical to physical quantum hardware.
3. Noise models are abstractions.
4. Thresholds depend on calibration.
5. Different protocols require different security analyses.
6. Empirical forgery probability is not a formal QDS security bound.
7. Detection performance depends on attack strength.
8. Honest and attack distributions can overlap.
9. Statistical evidence does not prove malicious intent.
10. A detector cannot guarantee detection of unknown attacks.

---

# 76. Mathematical Completion Criteria

This document is considered implementation-ready when:

* Quantum-state notation is defined.
* Measurement probability is defined.
* Pauli operators are defined.
* Bell-state mathematics is defined.
* Teleportation correctness is defined.
* Measurement statistics are defined.
* Fidelity is defined.
* QBER/error rate is defined.
* Honest baseline methodology is defined.
* Threshold methodology is defined.
* Forgery probability is defined.
* FAR/FRR/ADR are defined.
* Numerical tolerance is distinguished from security thresholds.
* Statistical thresholds are distinguished from cryptographic security bounds.
* Final decision determinism is defined.

---

# 77. Final Mathematical Principle

Q-SHIELD should follow:

```text
PHYSICS
   ↓
MEASUREMENT
   ↓
STATISTICS
   ↓
CALIBRATION
   ↓
THRESHOLD
   ↓
EVIDENCE
   ↓
DETERMINISTIC DECISION
```

The project must never reverse this process by choosing a desired security result first and then inventing mathematics to support it.

> **Measure first. Model honestly. Calibrate statistically. Decide deterministically.**

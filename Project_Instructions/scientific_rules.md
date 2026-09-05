# Q-SHIELD — Scientific Rules

## 1. Purpose

This document defines the scientific rules that govern the Q-SHIELD implementation.

The purpose is to ensure that the project remains:

* Scientifically correct
* Quantum-mechanically consistent
* Statistically defensible
* Security-aware
* Reproducible
* Honest about simulation limitations
* Compliant with the SIH problem statement

These rules apply to:

* Quantum circuits
* Quantum states
* Measurements
* Teleportation
* Bell-state entanglement
* Noise
* QDS modeling
* Statistical analysis
* Threat detection
* Security claims
* Experimental evaluation

If an implementation conflicts with these rules, the implementation must be corrected or the relevant scientific decision must be explicitly documented.

---

# 2. Scientific Position of Q-SHIELD

Q-SHIELD is a **software simulation and threat-detection framework**.

It is not a physical quantum communication system.

It does not claim to implement a complete physical deployment of a quantum digital-signature system.

The project uses a:

> **Qubit-level simulation abstraction of a teleportation-based QDS environment for security experimentation and threat detection.**

This distinction must be maintained throughout the project.

---

# 3. Quantum State Rules

A qubit is represented mathematically by a normalized state:

$$
|\psi\rangle = \alpha|0\rangle + \beta|1\rangle
$$

where:

$$
|\alpha|^2 + |\beta|^2 = 1
$$

The values:

$$
|\alpha|^2
$$

and

$$
|\beta|^2
$$

represent measurement probabilities in the computational basis.

The implementation must preserve state normalization unless a mathematical operation explicitly represents a non-unitary process such as measurement or noise.

---

# 4. Computational Basis

The standard computational basis is:

$$
|0\rangle =
\begin{bmatrix}
1\\
0
\end{bmatrix}
$$

and

$$
|1\rangle =
\begin{bmatrix}
0\\
1
\end{bmatrix}
$$

These states form the Z basis.

The system must not confuse computational/Z-basis measurement with X- or Y-basis measurement.

---

# 5. Superposition

A general pure qubit may exist in a superposition:

$$
|\psi\rangle = \alpha|0\rangle + \beta|1\rangle
$$

Superposition does not mean that the qubit is simply "both 0 and 1" in the classical sense.

Measurement produces outcomes according to quantum probabilities.

The AI must avoid misleading explanations such as:

> "A qubit is literally 0 and 1 simultaneously."

Prefer:

> "A qubit can exist in a superposition of computational basis states, with measurement outcomes governed by the state's amplitudes."

---

# 6. Normalization

Every valid pure quantum state must satisfy:

$$
\langle\psi|\psi\rangle = 1
$$

For:

$$
|\psi\rangle = \alpha|0\rangle+\beta|1\rangle
$$

this becomes:

$$
|\alpha|^2+|\beta|^2=1
$$

Tests should verify normalization for generated states whenever appropriate.

---

# 7. Global Phase

States that differ only by a global phase represent the same physical quantum state:

$$
|\psi\rangle
$$

and

$$
e^{i\phi}|\psi\rangle
$$

are physically equivalent.

Therefore, state-comparison functions must not incorrectly classify two states as physically different solely because of a global phase.

Where numerical state comparison is required, the implementation should use an appropriate phase-insensitive comparison.

---

# 8. Pauli Operators

Q-SHIELD must correctly represent the Pauli matrices:

## Pauli-X

$$
X =
\begin{bmatrix}
0&1\\
1&0
\end{bmatrix}
$$

It acts as a bit-flip:

$$
X|0\rangle=|1\rangle
$$

$$
X|1\rangle=|0\rangle
$$

---

## Pauli-Y

$$
Y =
\begin{bmatrix}
0&-i\\
i&0
\end{bmatrix}
$$

It introduces both a bit transformation and a phase transformation.

---

## Pauli-Z

$$
Z =
\begin{bmatrix}
1&0\\
0&-1
\end{bmatrix}
$$

It performs a phase flip:

$$
Z|0\rangle=|0\rangle
$$

$$
Z|1\rangle=-|1\rangle
$$

---

# 9. Pauli Eigenstates

The project must correctly recognize the major Pauli eigenstates.

## Z eigenstates

$$
|0\rangle,\ |1\rangle
$$

## X eigenstates

$$
|+\rangle =
\frac{|0\rangle+|1\rangle}{\sqrt2}
$$

$$
|-\rangle =
\frac{|0\rangle-|1\rangle}{\sqrt2}
$$

## Y eigenstates

$$
|+i\rangle =
\frac{|0\rangle+i|1\rangle}{\sqrt2}
$$

$$
|-i\rangle =
\frac{|0\rangle-i|1\rangle}{\sqrt2}
$$

These states are important because Q-SHIELD uses measurements associated with Pauli observables and bases.

---

# 10. Measurement Basis

A measurement basis defines which observable is being measured.

Q-SHIELD may use:

```text
Z basis
X basis
Y basis
```

These provide complementary information about the quantum state.

The implementation must clearly record which basis was used for every measurement result.

---

# 11. Projective Measurement

For a projective measurement with projectors:

$$
\{P_i\}
$$

the projectors satisfy:

$$
P_iP_j = 0 \quad \text{for } i\neq j
$$

and:

$$
\sum_iP_i=I
$$

For a state:

$$
|\psi\rangle
$$

the probability of outcome \(i\) is:

$$
p_i=\langle\psi|P_i|\psi\rangle
$$

The probabilities must satisfy:

$$
\sum_i p_i=1
$$

up to numerical precision.

---

# 12. Born Rule

Measurement probabilities must follow the Born rule.

For a projector \(P_i\):

$$
P(i)=\langle\psi|P_i|\psi\rangle
$$

For a general density matrix \(\rho\):

$$
P(i)=\mathrm{Tr}(P_i\rho)
$$

The implementation must not use arbitrary probability formulas when quantum measurement probabilities are required.

---

# 13. Individual Outcomes vs Statistics

A crucial distinction must be maintained:

```text
Quantum state
        ↓
Measurement probability
        ↓
Individual measurement outcome
        ↓
Repeated measurements
        ↓
Observed statistics
```

For example:

If:

$$
P(0)=0.7
$$

this does not mean every measurement produces 0.

It means that, over many equivalent measurements, approximately 70% of outcomes are expected to be 0.

Finite-shot results will fluctuate.

---

# 14. Shots

A quantum simulator generally estimates measurement distributions by executing a circuit repeatedly.

The number of repetitions is called the number of:

> **shots**

For example:

```text
shots = 1000
```

means approximately 1000 circuit executions for the measurement experiment.

Increasing shots generally improves the statistical stability of empirical probabilities, but does not remove statistical uncertainty completely.

---

# 15. Finite-Sample Rule

Observed probabilities must not automatically be treated as exact theoretical probabilities.

For example:

Theoretical:

$$
P(0)=0.5
$$

Observed:

$$
\hat P(0)=0.487
$$

may be completely consistent with finite sampling.

Therefore, the detector must consider statistical variation before declaring an abnormal result.

---

# 16. Bell-State Rules

Q-SHIELD must explicitly simulate Bell-state entanglement.

A standard Bell state can be generated using:

```text
|00>
 ↓
H on qubit 0
 ↓
CNOT
 ↓
Bell state
```

For example:

$$
|\Phi^+\rangle =
\frac{|00\rangle+|11\rangle}{\sqrt2}
$$

When measured in the computational basis, the ideal state produces correlated outcomes:

```text
00
11
```

with approximately equal probability.

The outcomes:

```text
01
10
```

should have zero probability in the ideal noiseless theoretical model.

Finite-shot simulation may produce small deviations depending on implementation details, but an ideal simulation should demonstrate the expected correlation.

---

# 17. Entanglement Rule

Entanglement must not be confused with ordinary correlation.

A Bell state cannot be represented as a simple product:

$$
|\psi_A\rangle\otimes|\psi_B\rangle
$$

of two independent single-qubit states.

The project should use Bell states as the entangled resource required by teleportation.

---

# 18. Quantum Teleportation Rules

Teleportation must use:

```text
Unknown input state
+
Entangled Bell pair
```

The standard conceptual process is:

```text
Alice
 ├── Unknown state
 └── Entangled qubit
          ↓
      Bell measurement
          ↓
    Two classical bits
          ↓
        Bob
          ↓
   Pauli correction
          ↓
   Recovered state
```

Teleportation does not transmit the unknown quantum state through the classical channel.

The quantum information is transferred using shared entanglement plus classical communication.

---

# 19. No Faster-Than-Light Communication

Teleportation must not be described as faster-than-light communication.

Two classical bits are required to determine the appropriate correction.

Therefore, teleportation does not violate causality.

---

# 20. Pauli Corrections in Teleportation

Depending on Alice's measurement outcomes, Bob applies the appropriate Pauli correction.

The correction table must be explicitly implemented and tested.

Conceptually:

| Alice's measurement | Bob's correction                      |
| ------------------- | ------------------------------------- |
| 00                  | \(I\)                                 |
| 01                  | \(X\)                                 |
| 10                  | \(Z\)                                 |
| 11                  | \(XZ\) / equivalent Pauli combination |

The exact circuit convention must be documented because qubit ordering and classical-bit ordering can vary between implementations.

The AI must test the actual convention used in Qiskit rather than assuming a bit ordering.

---

# 21. Teleportation Verification

A teleportation implementation is not considered correct merely because the circuit executes.

It must demonstrate that:

```text
Input state
        ≈
Recovered state
```

under ideal conditions.

Comparison may use:

* Statevector comparison
* Fidelity
* Measurement distributions
* Appropriate phase-insensitive state comparison

under the assumptions documented by the implementation.

---

# 22. Noise Rules

Noise represents imperfections or disturbances in the simulated quantum system.

Examples include:

```text
Bit-flip error
Phase-flip error
Depolarizing noise
Readout error
Thermal relaxation
```

Not every model must be implemented immediately.

Each model must have:

* Definition
* Parameters
* Intended interpretation
* Expected effect
* Tests

---

# 23. Noise Is Not Automatically Malicious

This is a fundamental rule.

A legitimate quantum communication process can experience noise.

Therefore:

```text
Observed deviation
≠
Attack
```

by default.

Instead:

```text
Observed deviation
        ↓
Compare with honest noisy baseline
        ↓
Determine whether deviation is statistically abnormal
```

Only then should the system consider a possible attack.

---

# 24. Honest Operating Baseline

Q-SHIELD must establish expected legitimate behavior.

The baseline should be generated using repeated legitimate executions.

For example:

```text
Noise configuration
        ↓
Many honest executions
        ↓
Measurement statistics
        ↓
Distribution of metrics
        ↓
Mean / variance / confidence region
        ↓
Honest operating region
```

This prevents thresholds from being chosen arbitrarily.

---

# 25. Baseline Must Not Be Contaminated

Attack samples should not be silently included in the honest baseline.

Otherwise, the baseline may adapt to malicious behavior.

The system should clearly distinguish:

```text
HONEST BASELINE DATA
```

from:

```text
ATTACK EXPERIMENT DATA
```

and:

```text
EVALUATION DATA
```

---

# 26. Statistical Threshold Rules

A threshold must have a documented reason.

Acceptable approaches may include:

* Empirical confidence intervals
* Standard-deviation-based regions
* Hypothesis-testing rules
* Statistically derived bounds
* Protocol-specific theoretical bounds

The selected method must be documented in:

```text
MATHEMATICAL_MODEL.md
```

and/or:

```text
SECURITY_MODEL.md
```

Do not hard-code unexplained values such as:

```text
0.8
0.9
0.95
```

and call them security thresholds without justification.

---

# 27. Confidence and Significance

Statistical decisions must identify the assumptions behind them.

Where a confidence level or significance level is used, the value must be recorded.

For example:

```text
confidence_level = 0.95
```

must not be treated as a magical number.

The documentation should explain:

* Why the level was selected
* What population is being considered
* What the interval means
* What limitations finite sampling introduces

---

# 28. Statistical Independence

Where statistical formulas assume independent observations, the implementation must state that assumption.

The AI must not blindly apply an independent-sample formula to correlated data.

If measurements are correlated due to:

* Circuit reuse
* Temporal effects
* Experimental configuration
* Simulation design

that limitation must be considered.

---

# 29. QBER / Error Rate

If QBER or a related error rate is used, its definition must be explicit.

A general empirical error rate may be represented as:

$$
\hat q=\frac{N_{\text{errors}}}{N_{\text{total}}}
$$

where:

* \(N_{\text{errors}}\) = observed erroneous outcomes
* \(N_{\text{total}}\) = total relevant outcomes

The project must define precisely what counts as an error for each experiment.

QBER must not be treated as a universal single number independent of the protocol.

---

# 30. Fidelity

If quantum-state fidelity is used, the definition must be stated.

For pure states:

$$
F(|\psi\rangle,|\phi\rangle)
=
|\langle\psi|\phi\rangle|^2
$$

For more general states, an appropriate density-matrix definition must be used.

The implementation must specify which definition is being used.

---

# 31. Fidelity Is Not a Universal Security Score

A high fidelity does not automatically prove that a signature is secure.

Likewise:

A low fidelity does not automatically prove that an attacker exists.

Fidelity is one piece of evidence.

It should be interpreted together with:

* Measurement statistics
* Baseline
* Protocol checks
* Attack configuration
* Other relevant metrics

---

# 32. Quantum Integrity Fingerprint

Q-SHIELD may construct a statistical profile of legitimate quantum behavior.

This may include:

```text
X-basis distribution
Y-basis distribution
Z-basis distribution
Fidelity
QBER/error rate
Bell-state correlation
Other documented metrics
```

This is called the:

> **Noise-Calibrated Quantum Integrity Fingerprint**

It is a statistical profile.

It is **not**:

* A cryptographic hash
* A digital signature
* A cryptographic key
* A proof of security

unless a separate cryptographic mechanism explicitly implements those properties.

---

# 33. Attack Detection Rule

Attack detection must be based on observable evidence and documented rules.

The conceptual process is:

```text
Measurement
      ↓
Statistics
      ↓
Baseline comparison
      ↓
Protocol checks
      ↓
Threshold evaluation
      ↓
Evidence fusion
      ↓
Decision
```

The AI must not replace this with an ML model.

---

# 34. Deterministic Final Decision

Quantum experiments are probabilistic.

The final decision logic must be deterministic once the experimental evidence is fixed.

For identical:

```text
Input
+
Measurement data
+
Baseline
+
Threshold configuration
```

the detector should return the same result.

Possible results:

```text
ACCEPT
SUSPICIOUS
ATTACK
```

The precise decision boundaries must be defined separately.

---

# 35. Legitimate Acceptance

The project expects legitimate signatures to be accepted under the defined ideal/operating conditions.

This means the verification rule should provide deterministic acceptance once the observed evidence satisfies the defined criteria.

This does **not** mean every physical execution will always be accepted under arbitrary noise.

Instead:

```text
Within defined honest operating region
        ↓
Legitimate signature
        ↓
ACCEPT
```

Outside that region, rejection or suspicion may occur.

---

# 36. Forgery Probability

Forgery probability must be experimentally or theoretically defined.

An empirical estimate may be expressed as:

$$
\hat p_f =
\frac{N_{\text{false accepts}}}
{N_{\text{forgery attempts}}}
$$

where:

* \(N_{\text{false accepts}}\) = number of malicious/forged attempts incorrectly accepted
* \(N_{\text{forgery attempts}}\) = total forgery attempts

The experiment must document:

* Forgery model
* Number of trials
* Acceptance rule
* Number of false acceptances
* Statistical uncertainty
* Limitations

A random value must never be used as a "forgery probability."

---

# 37. False Acceptance and False Rejection

Security evaluation must distinguish:

### False Acceptance

A malicious attempt is accepted.

This is especially important for signature security.

### False Rejection

A legitimate attempt is rejected.

This affects usability and availability.

Both must be measured.

---

# 38. No Perfect Security Claims

The project must not claim:

```text
100% secure
100% attack detection
100% forgery prevention
100% legitimate acceptance
```

unless such a claim is mathematically proven under explicitly stated assumptions—which is outside the intended scope of this prototype.

Experimental results must be presented with their assumptions and limitations.

---

# 39. QDS Security Claims

QDS security claims belong to the underlying quantum digital-signature protocol and its assumptions.

Q-SHIELD is primarily a:

> **simulation and threat-detection framework**

It does not create an information-theoretic security proof merely by measuring quantum states.

Therefore:

```text
QDS theoretical security
```

and

```text
Q-SHIELD detection performance
```

must remain separate concepts.

---

# 40. Classical vs Quantum Threats

Not every security threat is a quantum attack.

The project must distinguish:

### Quantum-layer threats

Examples:

* Bit-flip manipulation
* Phase-flip manipulation
* Depolarizing disturbance
* Other deliberate channel manipulation

### Protocol-layer threats

Examples:

* Replay
* Impersonation
* Unauthorized verification

### Signature/message-level threats

Examples:

* Forged signature
* Modified message/signature relationship

This separation must appear in the threat model and implementation.

---

# 41. Replay Attack Rules

A replay attack involves reusing previously valid protocol data in an inappropriate session/context.

Detection may use:

```text
Nonce
Session ID
Timestamp
Replay history
Message identifier
```

A replay attack should not be detected solely because quantum measurements fluctuate.

It is primarily a protocol-level security check.

---

# 42. Impersonation Rules

Impersonation concerns identity/authentication.

The system should be able to distinguish:

```text
Valid signer identity
```

from:

```text
Unexpected / unauthorized signer identity
```

Identity validation should be treated as protocol evidence rather than pretending that quantum measurement alone proves human identity.

---

# 43. Unauthorized Verification Rules

The system should distinguish between:

```text
Authorized verifier
```

and:

```text
Unauthorized verification request
```

This is primarily an authorization/protocol-layer property.

Quantum evidence may supplement the overall security decision, but authorization itself must be checked through explicit protocol rules.

---

# 44. Quantum Channel Attack Rules

A deliberate modification to the simulated quantum channel may be represented through operations or noise mechanisms such as:

```text
X
Y
Z
Bit flip
Phase flip
Depolarizing disturbance
```

The attack strength must be configurable.

The experiment must compare:

```text
Honest channel
```

against:

```text
Manipulated channel
```

under comparable conditions.

---

# 45. Attack vs Noise Experiment Design

When evaluating an attack, use controlled comparisons.

Example:

```text
Experiment A:
Honest + noise level p

Experiment B:
Attack + same noise level p
```

This makes it possible to investigate whether the detector is identifying malicious behavior rather than merely detecting noise.

---

# 46. Measurement Statistics as Evidence

Measurement statistics are central to Q-SHIELD.

Possible evidence includes:

```text
Counts
Probabilities
Expectation values
Variance
QBER
Fidelity
Bell correlations
Basis-specific deviations
```

The project must preserve the raw or sufficiently detailed measurement information needed to reproduce derived metrics where practical.

---

# 47. Expectation Values

For an observable \(O\), the expectation value is:

$$
\langle O\rangle
=
\langle\psi|O|\psi\rangle
$$

for a pure state.

For a density matrix:

$$
\langle O\rangle
=
\mathrm{Tr}(\rho O)
$$

Experimental estimates must be distinguished from exact theoretical values.

---

# 48. Numerical Precision

Quantum simulation involves floating-point numerical calculations.

Tiny numerical deviations should not automatically be treated as security anomalies.

For example:

```text
0.0000000001
```

may effectively represent zero within numerical precision.

Numerical tolerances must be documented and tested.

---

# 49. Randomness

Quantum measurement sampling is probabilistic.

Where simulation randomness is involved:

* Random seeds should be configurable where practical.
* Experiments should record relevant seeds/configuration.
* Statistical results should be based on sufficient repetitions.

The AI must not confuse simulator randomness with a security guarantee.

---

# 50. Reproducibility

Every major experiment should record:

```text
Experiment ID
Circuit/configuration
Number of qubits
Number of shots
Noise model
Noise parameters
Attack model
Attack strength
Baseline configuration
Threshold configuration
Random seed, where applicable
Software/environment information where useful
```

This allows the team to reproduce important results.

---

# 51. Simulation Limitations

Simulation does not perfectly reproduce every physical quantum communication system.

A simulator may omit or simplify:

* Physical hardware imperfections
* Optical losses
* Detector characteristics
* Environmental effects
* Real channel distance
* Hardware calibration
* Side-channel behavior
* Device-specific noise

Therefore, simulation results must be described as simulation results.

---

# 52. Physical QDS vs Q-SHIELD Model

The following distinction must remain explicit:

```text
Physical QDS protocol
        ↓
Real quantum hardware/channel
        ↓
Physical imperfections
        ↓
Experimental security analysis
```

versus:

```text
Q-SHIELD
        ↓
Qubit-level simulation
        ↓
Controlled noise/attack models
        ↓
Statistical threat detection
```

Q-SHIELD is designed to demonstrate the second.

---

# 53. Published Research vs Engineering Simplification

Whenever a protocol element is simplified for implementation, document:

```text
Published concept
        ↓
Required property
        ↓
Q-SHIELD abstraction
        ↓
Reason for simplification
```

The AI must not present an engineering abstraction as if it were an exact reproduction of a published physical protocol.

---

# 54. Security Evidence Must Be Traceable

Every final decision should ideally be traceable to measurable evidence.

Example:

```text
Decision: ATTACK

Evidence:
- Fidelity below calibrated operating region
- Z-basis error above threshold
- Invalid nonce
```

The system should allow the user to understand why the decision occurred.

---

# 55. No Post-Hoc Threshold Manipulation

Thresholds must not be repeatedly changed until the desired experimental result appears.

If thresholds are changed:

```text
Old threshold
New threshold
Reason
Experiment version
Result before/after
```

should be documented where relevant.

Threshold tuning should use a defensible methodology.

---

# 56. Training/Evaluation Separation

If data is used to construct the honest baseline, evaluation must avoid using the same observations in a way that produces misleading performance claims.

At minimum, distinguish:

```text
Baseline/calibration data
```

from:

```text
Evaluation data
```

Attack experiments must also be separately identified.

---

# 57. Performance Measurements

Performance evaluation should distinguish:

### Quantum simulation time

Time spent executing the quantum circuit simulation.

### Statistical processing time

Time spent calculating metrics and thresholds.

### Detection time

Time required for the decision engine.

### Total verification latency

Overall time from request to final decision.

Do not report only one runtime number if the components behave very differently.

---

# 58. Resource Reporting

Where practical, record:

```text
Qubit count
Circuit depth
Gate count
Shots
Memory usage
Execution time
Statistical processing time
```

This helps evaluate efficient verification.

---

# 59. Efficient Verification

The project should avoid unnecessary quantum resources.

Possible optimization considerations include:

* Reasonable shot counts
* Minimal required qubits
* Reusable circuit structures
* Efficient statistical processing
* Avoiding redundant simulation

However, optimization must never remove measurements required for scientifically meaningful detection.

---

# 60. Scientific Change Control

If an implementation change affects:

* Quantum mathematics
* QDS protocol
* Security assumptions
* Statistical model
* Detection threshold
* Attack model
* Measurement procedure

the relevant documentation must be updated.

The change should also be recorded in:

```text
DECISIONS.md
```

when it represents a significant architectural or scientific decision.

---

# 61. Forbidden Scientific Practices

The following are prohibited:

* Inventing quantum formulas
* Inventing QDS security proofs
* Claiming simulation equals physical deployment
* Treating noise as automatic evidence of attack
* Using arbitrary thresholds
* Using ML for detection
* Reporting fabricated experimental results
* Generating fake probabilities
* Hiding failed experiments
* Claiming perfect detection
* Claiming the detector itself provides information-theoretic security
* Presenting an abstraction as an exact published protocol
* Using quantum terminology merely for appearance

---

# 62. Scientific Review Checklist

Before accepting a major quantum/security feature, ask:

### Quantum correctness

* Are the states valid?
* Are operators correct?
* Are gates applied correctly?
* Are measurement bases correct?
* Are probabilities normalized?
* Are expected correlations demonstrated?

### Statistical correctness

* Is the metric defined?
* Are finite-shot effects considered?
* Is the threshold justified?
* Is the baseline independent of attack data?
* Are false acceptance and rejection measured?

### Security correctness

* Is the attacker capability defined?
* Is the attack in the correct layer?
* Is the evidence observable?
* Is the detection rule deterministic?
* Are limitations documented?

### Reproducibility

* Are parameters recorded?
* Can the experiment be repeated?

### Scientific honesty

* Are claims proportional to evidence?
* Are simulation limitations stated?
* Are theoretical guarantees distinguished from experimental results?

---

# 63. Final Scientific Principle

The central scientific principle of Q-SHIELD is:

> **Quantum measurements provide probabilistic evidence; statistical analysis converts that evidence into measurable security indicators; documented deterministic rules convert those indicators into reproducible security decisions.**

The project should always maintain the chain:

```text
Quantum Physics
      ↓
Quantum Simulation
      ↓
Measurement
      ↓
Statistics
      ↓
Evidence
      ↓
Deterministic Rules
      ↓
Security Decision
```

Never skip the scientific reasoning between these stages.

---

# 64. Final Rule

When there is a choice between:

```text
A more impressive claim
```

and:

```text
A more scientifically defensible claim
```

Q-SHIELD must always choose:

> **The scientifically defensible claim.**

The objective is not to make the project sound quantum.

The objective is to make the quantum, statistical, and security reasoning **correct, measurable, testable, and explainable**.

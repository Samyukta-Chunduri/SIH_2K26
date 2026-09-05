# Q-SHIELD Glossary

> A beginner-friendly reference for the quantum, QDS, security, statistics, and software terminology used throughout the Q-SHIELD project.

---

## 1. Quantum Computing Basics

### Qubit

A **qubit (quantum bit)** is the basic unit of quantum information.

A classical bit can be either:

```text
0
```

or

```text
1
```

A qubit can be in a quantum state represented as:

$$
|\psi\rangle = \alpha|0\rangle + \beta|1\rangle
$$

where \(\alpha\) and \(\beta\) are complex amplitudes.

The probabilities of measuring `0` or `1` are:

$$
P(0)=|\alpha|^2
$$

$$
P(1)=|\beta|^2
$$

with:

$$
|\alpha|^2+|\beta|^2=1
$$

---

### Classical Bit

A classical bit has exactly one value at a time:

```text
0 or 1
```

It is different from a qubit because a qubit can have a superposition of basis states before measurement.

---

### Computational Basis

The standard basis for a qubit is:

$$
|0\rangle =
\begin{bmatrix}
1\\
0
\end{bmatrix}
$$

$$
|1\rangle =
\begin{bmatrix}
0\\
1
\end{bmatrix}
$$

This is also called the **Z basis**.

---

### Superposition

A qubit can be represented as a combination of basis states:

$$
|\psi\rangle=\alpha|0\rangle+\beta|1\rangle
$$

This combination is called **superposition**.

Superposition does **not** mean that measuring the qubit gives both `0` and `1`.

A measurement produces one outcome.

---

### State Vector

A **state vector** is a mathematical representation of a quantum state.

For one qubit:

$$
|\psi\rangle =
\begin{bmatrix}
\alpha\\
\beta
\end{bmatrix}
$$

For multiple qubits, the state vector grows exponentially with the number of qubits.

---

### Amplitude

An **amplitude** is a complex number associated with a quantum state.

Amplitudes themselves are not probabilities.

Probability is obtained from the squared magnitude:

$$
P(x)=|\alpha_x|^2
$$

---

### Normalization

A valid quantum state must have total probability equal to 1.

For:

$$
|\psi\rangle=\alpha|0\rangle+\beta|1\rangle
$$

the normalization condition is:

$$
|\alpha|^2+|\beta|^2=1
$$

---

### Born Rule

The **Born rule** converts quantum amplitudes into measurement probabilities.

If a state has amplitude \(\alpha\) for an outcome, then:

$$
P=|\alpha|^2
$$

This is fundamental to Q-SHIELD because our detector uses **measurement outcomes and their statistics**.

---

### Measurement

Quantum measurement extracts classical information from a quantum state.

For example, measuring a qubit in the computational basis produces:

```text
0
```

or

```text
1
```

The exact outcome is probabilistic according to the quantum state.

---

### Projective Measurement

A **projective measurement** measures a quantum state with respect to a set of orthogonal measurement states.

For example:

* Z basis → measure `|0⟩` / `|1⟩`
* X basis → measure `|+⟩` / `|-⟩`
* Y basis → measure `|+i⟩` / `|-i⟩`

Q-SHIELD uses projective measurements to obtain evidence about the quantum signature.

---

### Measurement Basis

The **measurement basis** determines which quantum property is being measured.

The main bases used in Q-SHIELD are:

| Basis | States |            |            |
| ----- | ------ | ---------- | ---------- |
| Z     | (      | 0\rangle,  | 1\rangle)  |
| X     | (      | +\rangle,  | -\rangle)  |
| Y     | (      | +i\rangle, | -i\rangle) |

---

### Eigenstate

An **eigenstate** of an operator is a state that remains the same state up to a multiplicative factor when that operator acts on it.

For Q-SHIELD, important eigenstates are the eigenstates of the Pauli operators.

---

## 2. Pauli Operators and Quantum Gates

### Pauli I

Identity operator:

$$
I=
\begin{bmatrix}
1&0\\
0&1
\end{bmatrix}
$$

It leaves the qubit unchanged.

---

### Pauli X

$$
X=
\begin{bmatrix}
0&1\\
1&0
\end{bmatrix}
$$

It performs a bit-flip:

$$
|0\rangle\rightarrow|1\rangle
$$

$$
|1\rangle\rightarrow|0\rangle
$$

---

### Pauli Y

$$
Y=
\begin{bmatrix}
0&-i\\
i&0
\end{bmatrix}
$$

It introduces both a bit and phase transformation.

---

### Pauli Z

$$
Z=
\begin{bmatrix}
1&0\\
0&-1
\end{bmatrix}
$$

It changes the relative phase:

$$
|0\rangle\rightarrow|0\rangle
$$

$$
|1\rangle\rightarrow-|1\rangle
$$

---

### Pauli Eigenstates

The six states used by Q-SHIELD are:

#### Z basis

$$
|0\rangle,\quad |1\rangle
$$

#### X basis

$$
|+\rangle=\frac{|0\rangle+|1\rangle}{\sqrt2}
$$

$$
|-\rangle=\frac{|0\rangle-|1\rangle}{\sqrt2}
$$

#### Y basis

$$
|+i\rangle=\frac{|0\rangle+i|1\rangle}{\sqrt2}
$$

$$
|-i\rangle=\frac{|0\rangle-i|1\rangle}{\sqrt2}
$$

---

### Hadamard Gate

The Hadamard gate is:

$$
H=\frac{1}{\sqrt2}
\begin{bmatrix}
1&1\\
1&-1
\end{bmatrix}
$$

It is commonly used to create superposition.

For example:

$$
H|0\rangle=|+\rangle
$$

The Hadamard gate is also used when constructing Bell states.

---

### Phase

A **phase** is part of the mathematical description of a quantum state.

Relative phase can affect interference and measurement statistics.

---

### Global Phase

Multiplying an entire quantum state by the same phase factor does not change physical measurement probabilities.

For example:

$$
|\psi\rangle
$$

and

$$
e^{i\theta}|\psi\rangle
$$

represent physically equivalent states for measurement purposes.

---

### Relative Phase

The phase relationship between components of a superposition is physically meaningful.

For example:

$$
\frac{|0\rangle+|1\rangle}{\sqrt2}
$$

and

$$
\frac{|0\rangle-|1\rangle}{\sqrt2}
$$

have the same computational-basis probabilities but different behaviour in other measurement bases.

---

### Bloch Sphere

The **Bloch sphere** is a geometric representation of a single-qubit state.

It provides an intuitive way to visualize:

* X direction
* Y direction
* Z direction
* pure states
* mixed states

Q-SHIELD may use Bloch-vector information as an optional representation of quantum evidence.

---

### Density Matrix

A **density matrix** represents quantum states, especially when dealing with mixed states or noise.

For a state \(|\psi\rangle\):

$$
\rho=|\psi\rangle\langle\psi|
$$

Density matrices are useful when modelling noisy quantum channels.

---

# 3. Entanglement and Bell States

## Entanglement

**Quantum entanglement** is a correlation between quantum systems that cannot generally be described as independent states.

Entangled states are essential to quantum teleportation.

---

## Bell State

A **Bell state** is one of four maximally entangled two-qubit states.

Q-SHIELD uses:

$$
|\Phi^+\rangle=
\frac{|00\rangle+|11\rangle}{\sqrt2}
$$

---

## Bell Pair

A pair of qubits prepared in an entangled Bell state is called a **Bell pair**.

The Bell pair acts as the shared quantum resource in teleportation.

---

## Bell Measurement

A **Bell measurement** is a measurement in the Bell-state basis.

In standard quantum teleportation, the sender performs a Bell-basis measurement on the input qubit and one half of the Bell pair.

The result produces two classical bits.

---

## Bell Correlation

A **Bell correlation** describes correlations between measurement outcomes of entangled qubits.

Q-SHIELD can use Bell correlations as quantum evidence when evaluating whether a quantum process behaved as expected.

---

# 4. Quantum Teleportation

## Quantum Teleportation

**Quantum teleportation** is a protocol for transferring an unknown quantum state from one location to another using:

1. An entangled Bell pair
2. A joint measurement
3. Two classical bits
4. Conditional Pauli correction

It does **not** physically transport the original qubit.

---

## EPR Pair

An **EPR pair** is another common term for a pair of entangled quantum systems.

In our project, the Bell pair provides the entanglement resource.

---

## Classical Bits

Quantum teleportation requires two classical bits produced by the sender's measurement.

These bits determine which Pauli correction the receiver applies.

---

## Pauli Correction

Depending on the two classical measurement bits, the receiver applies a correction:

| Measurement result | Correction |
| ------------------ | ---------- |
| 00                 | \(I\)      |
| 01                 | \(X\)      |
| 10                 | \(Z\)      |
| 11                 | \(XZ\)     |

The exact interpretation of classical-bit ordering must be explicitly tested in Qiskit.

---

## Teleportation Fidelity

**Teleportation fidelity** measures how closely the received state matches the intended state.

For pure states:

$$
F=|\langle\psi|\phi\rangle|^2
$$

where:

* \(|\psi\rangle\) = expected state
* \(|\phi\rangle\) = received state

A perfect ideal teleportation has:

$$
F=1
$$

---

# 5. Digital Signatures and QDS

## Digital Signature

A **digital signature** is a cryptographic mechanism used to provide properties such as:

* authenticity
* integrity
* signer identification
* non-repudiation, depending on the scheme and legal/protocol context

A digital signature is **not encryption**.

---

## Quantum Digital Signature (QDS)

A **Quantum Digital Signature** uses quantum information and quantum communication as part of its security mechanism.

QDS research aims to provide properties such as:

* unforgeability
* non-repudiation
* transferability

under appropriate protocol assumptions.

---

## Teleportation-Based QDS

A **teleportation-based QDS** uses quantum teleportation as part of the quantum communication/signature process.

In Q-SHIELD, we implement a **qubit-level teleportation-based QDS abstraction** for simulation.

It should not be described as an exact implementation of every physical QDS protocol in the research literature.

---

## Signer

The **signer** is the participant who creates or authorizes the quantum signature associated with a message.

---

## Verifier

The **verifier** checks whether a signature should be accepted.

The verifier is responsible for applying the configured verification procedure.

---

## Attacker

The **attacker** attempts to violate one or more security properties.

Examples include:

* forging a signature
* replaying an old signature
* impersonating a signer
* manipulating the quantum channel
* making an unauthorized verification request

---

## Signature

In Q-SHIELD, the signature is an abstraction connecting:

```text
message
+
signer
+
quantum state information
+
protocol metadata
```

The exact signature-record structure remains a project design decision.

---

## Message Identifier

A **message identifier** uniquely represents a message or verification object.

It may be based on a cryptographic hash or another deterministic identifier.

---

## Verification Request

A verification request contains the information required to determine whether a signature should be verified.

It can contain:

* signer identity
* verifier identity
* message
* signature
* session identifier
* nonce
* timestamp
* authorization information

---

## Information-Theoretic Security

A system has **information-theoretic security** when security does not fundamentally depend on an attacker's computational limitations.

QDS protocols may provide information-theoretic security properties under specific protocol and physical assumptions.

Q-SHIELD must **not claim that its software detector alone creates information-theoretic security**.

---

# 6. Quantum Noise and Channel Effects

## Quantum Channel

A **quantum channel** represents the physical or simulated mechanism through which quantum information travels or is transformed.

Q-SHIELD models channel imperfections and channel manipulation.

---

## Noise

**Noise** represents unintended disturbances or imperfections in the quantum system.

Examples:

* bit-flip errors
* phase-flip errors
* depolarizing noise
* readout errors
* other configured simulation imperfections

Important:

> Noise is not automatically an attack.

---

## Bit-Flip Error

A bit-flip transforms:

$$
|0\rangle\leftrightarrow|1\rangle
$$

It corresponds conceptually to a Pauli-X error.

---

## Phase-Flip Error

A phase-flip changes the relative phase of a state.

It corresponds conceptually to a Pauli-Z error.

---

## Y Error

A Pauli-Y error combines bit and phase transformations.

---

## Depolarizing Noise

Depolarizing noise randomly disturbs a quantum state according to a configured probability model.

It is useful for simulating generalized channel imperfections.

---

## Readout Error

A **readout error** occurs when the quantum state may be correct but the measurement device reports the wrong classical result.

This distinction matters because:

```text
quantum-state error
```

and

```text
measurement/readout error
```

are not necessarily the same thing.

---

## Channel Manipulation

A **channel manipulation attack** intentionally alters quantum information during transmission or processing.

Examples in the simulation may include:

* X manipulation
* Y manipulation
* Z manipulation
* configurable error probability
* stronger channel disturbance

The attack model must be explicitly documented.

---

# 7. Security Attacks

## Attack

An **attack** is an intentional attempt to violate the security requirements of the system.

---

## Forgery

A **forgery attack** attempts to create or modify a signature so that an invalid signature is accepted as legitimate.

Q-SHIELD evaluates forgery experimentally using measurement outcomes and verification rules.

---

## Replay Attack

A **replay attack** reuses a previously valid verification object.

Typical protection mechanisms include:

* nonce
* session identifier
* timestamp
* verification history

Replay is primarily a **protocol-level attack**, not inherently a quantum attack.

---

## Impersonation

An **impersonation attack** occurs when an attacker attempts to act as another participant.

Q-SHIELD handles this primarily through identity and authentication evidence.

---

## Unauthorized Verification

An unauthorized verification attempt occurs when a participant without the required authorization attempts to perform a verification operation.

This is a protocol/authorization issue.

---

## Anomaly

An **anomaly** is behaviour that differs from the expected honest operating region.

An anomaly does not automatically mean that a specific attack has been identified.

Therefore Q-SHIELD supports:

```text
SUSPICIOUS
```

for unexplained deviations.

---

# 8. Statistics

## Shot

A **shot** is one execution of a quantum circuit followed by measurement.

For example:

```text
1000 shots
```

means the circuit is executed and measured 1000 times.

---

## Trial

A **trial** is one experimental observation or repeated experiment.

Depending on context, a trial may contain multiple quantum shots.

The project documentation must distinguish these meanings where necessary.

---

## Count

A **count** is the number of times a particular measurement result occurs.

Example:

```text
00 → 503
01 → 497
```

means the corresponding outcomes were observed 503 and 497 times.

---

## Empirical Probability

The empirical probability of an outcome is:

$$
\hat p=\frac{k}{N}
$$

where:

* \(k\) = observed count
* \(N\) = total number of observations

---

## Mean

The **mean** is the average value of observations:

$$
\bar{x}=\frac{1}{n}\sum_{i=1}^{n}x_i
$$

---

## Variance

Variance measures how much observations vary around the mean.

$$
s^2=\frac{1}{n-1}\sum_{i=1}^{n}(x_i-\bar{x})^2
$$

---

## Standard Deviation

The standard deviation is:

$$
s=\sqrt{s^2}
$$

It measures the typical spread of observations.

---

## Standard Error

The standard error measures uncertainty in an estimated mean:

$$
SE=\frac{s}{\sqrt n}
$$

It becomes smaller as the number of independent observations increases.

---

## Confidence Interval

A **confidence interval** provides a statistical range associated with an estimated parameter.

Q-SHIELD can use confidence intervals when estimating honest operating regions.

---

## Quantile

A **quantile** is a value dividing a distribution according to a specified proportion.

For example, the 95th percentile is a value below which approximately 95% of observations fall.

Quantiles can be useful for empirical threshold calibration.

---

# 9. Quantum Security Metrics

## QBER

**Quantum Bit Error Rate (QBER)** measures the fraction of outcomes that disagree with expected outcomes.

A simple form is:

$$
QBER=\frac{\text{number of erroneous outcomes}}
{\text{total outcomes}}
$$

Lower QBER generally indicates closer agreement with the expected behaviour.

---

## Fidelity

Fidelity measures similarity between quantum states.

A value closer to:

$$
1
$$

means greater similarity.

The exact formula depends on whether the states are pure or mixed.

---

## Expectation Value

An expectation value describes the average measurement result associated with an observable.

For observable \(A\):

$$
\langle A\rangle=\langle\psi|A|\psi\rangle
$$

For Q-SHIELD, Pauli expectation values can provide quantum evidence.

---

## Bell Correlation

Bell correlations quantify correlations between measurements of entangled systems.

They can help determine whether an entanglement-based process behaves as expected.

---

## Total Variation Distance

For two discrete probability distributions \(P\) and \(Q\):

$$
TV(P,Q)=\frac12\sum_x|P(x)-Q(x)|
$$

It measures how different two probability distributions are.

---

# 10. Baseline and Thresholds

## Honest Baseline

The **honest baseline** describes the expected behaviour of legitimate executions under specified conditions.

It should be measured separately from attack experiments.

Example:

```text
Honest + ideal
Honest + low noise
Honest + medium noise
```

---

## Calibration

**Calibration** means measuring legitimate system behaviour and using those measurements to establish expected operating ranges.

Calibration is **not machine learning training**.

---

## Validation

**Validation** checks whether the calibrated rules work correctly on data that was not used to establish the thresholds.

---

## Threshold

A **threshold** is a predetermined boundary used to make a decision.

Example:

```text
If QBER > threshold:
    deviation detected
```

Thresholds must be justified by calibration or documented security/statistical requirements.

They must not simply be chosen because they "look good."

---

## Operating Region

The **operating region** is the range of conditions under which the system behaves acceptably.

It can depend on:

* noise level
* attack strength
* number of shots
* threshold configuration

---

## Security Operating Region

The **security operating region** describes conditions under which legitimate verification remains reliable while malicious behaviour can be detected with acceptable performance.

---

# 11. Security Metrics

## FAR

**False Acceptance Rate (FAR)** is the fraction of malicious/invalid attempts incorrectly accepted.

$$
FAR=
\frac{\text{malicious attempts accepted}}
{\text{total malicious attempts}}
$$

Lower is generally better.

---

## FRR

**False Rejection Rate (FRR)** is the fraction of legitimate attempts incorrectly rejected.

$$
FRR=
\frac{\text{legitimate attempts rejected}}
{\text{total legitimate attempts}}
$$

Lower is generally better.

---

## LAR

**Legitimate Acceptance Rate (LAR)** measures how often legitimate signatures are accepted.

$$
LAR=
\frac{\text{legitimate attempts accepted}}
{\text{total legitimate attempts}}
$$

---

## ADR

**Attack Detection Rate (ADR)** measures how often configured attacks are detected.

$$
ADR=
\frac{\text{detected attacks}}
{\text{total attack attempts}}
$$

---

## Empirical Forgery Probability

The empirical forgery probability is the observed fraction of forgery attempts that succeed.

$$
P_{\text{forge,emp}}=
\frac{\text{successful forgery attempts}}
{\text{total forgery attempts}}
$$

This is an **experimental result**, not automatically a formal cryptographic security bound.

---

# 12. Detection and Evidence

## Evidence

Evidence is information used to support a security decision.

Q-SHIELD uses multiple categories of evidence.

---

## Protocol Evidence

Examples:

* signer identity
* verifier identity
* session validity
* nonce validity
* authorization
* replay status

---

## Quantum Evidence

Examples:

* measurement distributions
* QBER
* fidelity
* Pauli expectations
* Bell correlations
* teleportation correctness

---

## Statistical Evidence

Examples:

* baseline deviation
* confidence interval
* threshold comparison
* distribution distance
* estimated error rate

---

## Evidence Fusion

**Evidence fusion** means combining multiple independent evidence categories using deterministic rules.

Conceptually:

```text
Protocol Evidence
        +
Quantum Evidence
        +
Statistical Evidence
        ↓
Deterministic Rule Engine
        ↓
Decision
```

No machine-learning classifier is required.

---

## Deterministic Decision

A decision is deterministic when the same:

```text
measurement data
+
protocol data
+
configuration
+
thresholds
```

produces the same final result.

The quantum measurement itself can be probabilistic while the final decision is deterministic.

---

## ACCEPT

Means:

> All required verification and security checks passed under the configured operating conditions.

It does **not** mean:

> The signature is mathematically proven secure against every possible attack.

---

## SUSPICIOUS

Means:

> The system detected a deviation or inconsistency, but the available evidence does not satisfy a specific attack rule strongly enough to classify it.

---

## ATTACK

Means:

> A documented attack-detection rule was satisfied.

---

## QIF — Quantum Integrity Fingerprint

**Quantum Integrity Fingerprint (QIF)** is a Q-SHIELD design concept representing a collection of quantum/statistical characteristics used to describe expected legitimate behaviour.

Possible components include:

* X-basis statistics
* Y-basis statistics
* Z-basis statistics
* QBER
* fidelity
* Bell correlations
* distribution distances

QIF is **not a universal cryptographic security score**.

---

## Explainability

A security decision is explainable when the system can show **why** it reached the decision.

Example:

```text
Decision: ATTACK

Evidence:
- Replay check: FAILED
- Nonce check: FAILED
- QBER: within baseline
- Fidelity: within baseline

Triggered rule:
REPLAY_DETECTED
```

---

# 13. Performance Terms

## Runtime

The amount of time required to perform an operation.

Q-SHIELD may measure:

* quantum simulation time
* statistical processing time
* protocol-check time
* decision time
* total verification time

---

## Throughput

The number of verification operations completed per unit time.

Example:

```text
100 verifications/second
```

---

## Batch Verification

Processing multiple verification requests together instead of one at a time.

---

## Overhead

Additional computational or time cost introduced by a feature.

For example:

```text
basic verification
vs.
verification + statistical detection
```

The difference is detection overhead.

---

## Scalability

How system performance changes as workload increases.

Possible variables:

* number of signatures
* number of shots
* number of states
* number of experiments
* number of users

---

## CPU

A **Central Processing Unit** used to execute general-purpose computation.

Quantum simulation can run on a CPU.

---

## GPU

A **Graphics Processing Unit** can accelerate certain highly parallel computations.

GPU support is an optional performance optimization, not a security requirement.

---

## Simulation

A **simulation** models quantum behaviour using classical computational resources.

Q-SHIELD is initially a simulation project.

---

## Quantum Hardware

Actual physical quantum computing hardware.

Q-SHIELD does not require physical quantum hardware for the prototype.

---

# 14. Qiskit and Software Terms

## Qiskit

**Qiskit** is an open-source software framework for building and executing quantum circuits.

Q-SHIELD uses it to construct and simulate quantum operations.

---

## Qiskit Aer

**Qiskit Aer** provides high-performance quantum circuit simulation capabilities, including configurable noise models.

---

## Quantum Circuit

A quantum circuit represents a sequence of quantum operations and measurements.

Conceptually:

```text
Qubit
 │
 H
 │
 CNOT
 │
 X
 │
 Measure
```

---

## Backend

A Qiskit **backend** represents a target on which a circuit can be executed or simulated.

It may represent:

* a simulator
* quantum hardware

---

## Simulator

A simulator reproduces quantum-circuit behaviour computationally without requiring physical quantum hardware.

---

## Seed

A **random seed** controls pseudo-random behaviour in simulations where supported.

Recording seeds helps improve reproducibility.

---

## Shot Count

The number of times a circuit is executed for measurement.

Example:

```text
shots = 10,000
```

means 10,000 circuit executions.

---

## Streamlit

**Streamlit** is a Python framework for creating interactive data and scientific applications.

Q-SHIELD plans to use Streamlit for the initial dashboard.

---

## SQLite

**SQLite** is a lightweight relational database.

It may be used for local storage of:

* verification history
* experiment results
* attack results
* configuration metadata

---

## FastAPI

**FastAPI** is a Python framework for creating APIs.

It is optional and can be introduced if Q-SHIELD later needs a separate backend API.

---

# 15. Security Terminology

## Computational Security

Security based on assumptions about the computational difficulty of solving a problem.

RSA and ECC are examples of classical cryptographic systems whose security relies on computational assumptions.

---

## Information-Theoretic Security

Security that does not fundamentally rely on an attacker's computational limitations.

QDS protocols can provide information-theoretic security properties under appropriate assumptions.

---

## Security Assumption

A condition that must hold for a security claim to remain valid.

Examples:

* trusted protocol components
* authenticated classical communication
* specified channel assumptions
* bounded noise
* correct implementation

---

## Security Claim

A statement about what security property the system provides or demonstrates.

Every major Q-SHIELD security claim should be supported by:

```text
assumption
+
method
+
experiment
+
result
```

---

## Formal Security Proof

A mathematical proof establishing a security property under explicitly stated assumptions.

An experimental simulation is **not automatically a formal security proof**.

---

## Empirical Result

A result obtained experimentally or through simulation.

Example:

```text
Under noise p = 0.02 and 10,000 shots,
the measured false rejection rate was 1.3%.
```

This is an empirical result, not a universal theorem.

---

# 16. Development and Experiment Terminology

## Experiment

A controlled procedure used to investigate system behaviour.

Example:

```text
Independent variable:
channel noise

Dependent variables:
QBER
fidelity
FAR
FRR
ADR
```

---

## Independent Variable

A parameter deliberately changed during an experiment.

Examples:

* noise probability
* attack strength
* shot count

---

## Dependent Variable

A quantity measured as a result of changing an independent variable.

Examples:

* QBER
* fidelity
* detection rate
* runtime

---

## Control

A baseline condition used for comparison.

Example:

```text
Control:
honest + no attack

Experiment:
honest + channel manipulation
```

---

## Reproducibility

The ability to repeat an experiment and obtain comparable results under the same documented conditions.

Record:

* software versions
* hardware
* configuration
* random seeds
* shot count
* noise model
* attack parameters
* threshold version

---

## Numerical Tolerance

A small tolerance used when comparing floating-point numerical values.

Example:

```text
abs(actual - expected) < 1e-8
```

Numerical tolerance is an implementation detail.

It is **not the same as a security threshold**.

---

## Security Threshold

A statistically or security-motivated boundary used to classify system behaviour.

Example:

```text
QBER > calibrated_threshold
```

Security thresholds require scientific justification.

---

## Calibration vs Training

Q-SHIELD uses **calibration**, not machine-learning training.

Calibration means:

```text
Run honest system
→ measure behaviour
→ estimate baseline
→ establish thresholds
```

There is no:

```text
dataset
→ ML model
→ prediction
```

---

# 17. Common Confusions

## Qubit ≠ Classical Bit

A classical bit is `0` or `1`.

A qubit can be represented by a superposition before measurement.

---

## Measurement Outcome ≠ Deterministic Quantum State

Quantum measurement can be probabilistic.

For example, repeated measurements may produce:

```text
0 → 497
1 → 503
```

The **decision made from those measurements** can nevertheless be deterministic.

---

## Teleportation ≠ Faster-Than-Light Communication

Quantum teleportation requires classical communication.

Therefore it does not provide faster-than-light signalling.

---

## Teleportation ≠ Digital Signature

Teleportation is a quantum-information protocol.

A digital signature is a security mechanism.

In Q-SHIELD, teleportation is part of the simulated quantum-signature environment; it is not itself the signature.

---

## QDS ≠ PQC

**QDS**:

```text
Quantum Digital Signatures
```

uses quantum information/communication.

**PQC**:

```text
Post-Quantum Cryptography
```

uses classical cryptographic algorithms designed to resist quantum-computer attacks.

They are different technologies.

---

## Noise ≠ Attack

Noise can occur during honest operation.

An attack is intentional malicious behaviour.

Therefore:

```text
Noise
→ calibrate

Attack
→ detect
```

A detector should not simply classify every noisy event as malicious.

---

## Empirical Forgery Probability ≠ Formal Cryptographic Bound

If an experiment observes:

```text
5 successful forgeries / 10,000 attempts
```

then:

$$
P_{\text{forge,emp}}=0.0005
$$

This is an empirical observation.

It is not automatically a formal QDS security bound.

---

## Deterministic Decision ≠ Deterministic Measurement

Measurement outcomes can be random.

But once the outcomes are collected, a fixed rule can produce a deterministic decision:

```text
same evidence
+
same configuration
→
same decision
```

---

## QIF ≠ Formal Security Score

The Quantum Integrity Fingerprint is a project-specific collection of quantum/statistical evidence.

It is not a universally recognized cryptographic security metric.

---

## Replay/Impersonation ≠ Purely Quantum Attacks

These attacks mainly involve protocol and identity mechanisms.

They should not be artificially represented as quantum errors just to make them "quantum."

---

## Simulation ≠ Real Quantum Hardware

A simulator models quantum behaviour using classical computation.

Simulation results demonstrate the behaviour of the model.

They do not automatically prove that the same implementation will perform identically on physical quantum hardware.

---

# 18. How the Terms Connect in Q-SHIELD

The overall relationship can be summarized as:

```text
                 MESSAGE
                    │
                    ▼
              QDS SIGNATURE
                    │
                    ▼
            QUANTUM STATE
                    │
                    ▼
          BELL-STATE ENTANGLEMENT
                    │
                    ▼
          QUANTUM TELEPORTATION
                    │
                    ▼
           PAULI CORRECTION
                    │
                    ▼
          PROJECTIVE MEASUREMENT
                    │
                    ▼
          MEASUREMENT OUTCOMES
                    │
                    ▼
          QUANTUM STATISTICS
          ┌─────────┼──────────┐
          │         │          │
         QBER    Fidelity   Correlations
          │         │          │
          └─────────┼──────────┘
                    ▼
             HONEST BASELINE
                    │
                    ▼
          THRESHOLD COMPARISON
                    │
       ┌────────────┼────────────┐
       │            │            │
       ▼            ▼            ▼
   Protocol       Quantum     Statistical
    Evidence      Evidence      Evidence
       │            │            │
       └────────────┼────────────┘
                    ▼
             EVIDENCE FUSION
                    │
                    ▼
          DETERMINISTIC DECISION
                    │
          ┌─────────┼─────────┐
          ▼         ▼         ▼
       ACCEPT   SUSPICIOUS   ATTACK
```

---

# 19. Quick Reference Table

| Term             | Simple meaning                                                           |
| ---------------- | ------------------------------------------------------------------------ |
| Qubit            | Basic unit of quantum information                                        |
| Superposition    | Combination of quantum basis states                                      |
| Measurement      | Extracting classical information from a quantum state                    |
| Pauli X          | Bit-flip operation                                                       |
| Pauli Y          | Bit + phase transformation                                               |
| Pauli Z          | Phase-flip operation                                                     |
| Bell state       | Entangled two-qubit state                                                |
| Teleportation    | Transfer of a quantum state using entanglement + classical communication |
| Pauli correction | Operation used to recover the teleported state                           |
| QDS              | Quantum Digital Signature                                                |
| Noise            | Unintentional quantum disturbance                                        |
| Forgery          | Attempt to create an invalid accepted signature                          |
| Replay           | Reuse of an old valid request/signature                                  |
| Impersonation    | Pretending to be another participant                                     |
| QBER             | Quantum error rate                                                       |
| Fidelity         | Similarity between quantum states                                        |
| Baseline         | Expected honest behaviour                                                |
| Calibration      | Establishing the honest baseline                                         |
| Threshold        | Boundary used for a decision                                             |
| FAR              | Invalid attempts incorrectly accepted                                    |
| FRR              | Valid attempts incorrectly rejected                                      |
| LAR              | Valid attempts correctly accepted                                        |
| ADR              | Attacks correctly detected                                               |
| QIF              | Project-specific quantum integrity evidence representation               |
| Shot             | One quantum circuit execution + measurement                              |
| Simulator        | Classical program that models quantum circuits                           |
| Reproducibility  | Ability to repeat experiments under documented conditions                |

---

# 20. Core Vocabulary Rule

Whenever implementing or discussing Q-SHIELD, maintain this conceptual separation:

```text
QUANTUM PHYSICS
      ↓
Measurement
      ↓
STATISTICS
      ↓
Calibration
      ↓
Thresholds
      ↓
Evidence
      ↓
Deterministic Decision
```

Do not skip directly from:

```text
quantum circuit
```

to:

```text
"secure"
```

The system must show the intermediate evidence and assumptions.

---

## Final Principle

Q-SHIELD should always distinguish between:

**what quantum mechanics produces,**

**what the simulator measures,**

**what statistics show,**

**what the security rules infer,**

and

**what the project can legitimately claim.**

This separation is essential for keeping the project scientifically defensible.

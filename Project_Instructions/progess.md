# PROGRESS.md

# Q-SHIELD — Project Progress Tracker

**Project:** Q-SHIELD — Quantum Signature Security & Threat Detection Framework
**Problem Statement:** SIH 26141 — Quantum-Inspired Cyber Threat Detection for Digital Signature Security
**Status:** ACTIVE
**Last Updated:** Update whenever a milestone changes.

---

# 1. Purpose

This file tracks the actual development state of Q-SHIELD.

It must distinguish between:

```text
PLANNED
UNDERSTOOD
IMPLEMENTED
TESTED
EXPERIMENTALLY VALIDATED
DEMO READY
```

A feature must not be marked complete merely because code exists.

The preferred progression is:

```text
Requirement
    ↓
Design
    ↓
Implementation
    ↓
Unit tests
    ↓
Integration tests
    ↓
Experiment
    ↓
Validation
    ↓
Documentation
    ↓
Demo ready
```

---

# 2. Status Definitions

| Status      | Meaning                                      |
| ----------- | -------------------------------------------- |
| NOT STARTED | No meaningful work completed                 |
| PLANNED     | Requirement/design exists                    |
| IN PROGRESS | Currently being implemented                  |
| IMPLEMENTED | Code exists                                  |
| TESTED      | Automated/manual tests pass                  |
| VALIDATED   | Experimental/scientific validation completed |
| DEMO READY  | Stable enough for SIH demonstration          |
| BLOCKED     | Cannot continue because of unresolved issue  |
| DEFERRED    | Intentionally postponed                      |

---

# 3. Overall Project Status

```text
Current Phase:
M0 — Environment / Foundation

Overall Completion:
0% initially

Core Quantum Layer:
NOT STARTED

QDS Layer:
PLANNED

Statistical Detection:
PLANNED

Attack Simulation:
PLANNED

Evaluation:
PLANNED

Dashboard:
PLANNED

Blockchain:
DEFERRED
```

The percentage must be updated based on actual completed milestones, not estimated effort.

---

# 4. Critical Rule

Never mark a feature:

```text
DONE
```

just because:

```text
code runs once
```

For security-relevant functionality, the minimum acceptable progression is:

```text
Implemented
→ Tested
→ Experimentally validated
```

---

# 5. Milestone Tracker

| ID  | Milestone                      | Status      |
| --- | ------------------------------ | ----------- |
| M0  | Environment setup              | COMPLETE    |
| M1  | Qubit fundamentals             | COMPLETE    |
| M2  | Pauli operators                | COMPLETE    |
| M3  | Projective measurement         | COMPLETE    |
| M4  | Bell states                    | COMPLETE    |
| M5  | Bell correlation               | COMPLETE    |
| M6  | Quantum teleportation          | COMPLETE    |
| M7  | Teleportation verification     | COMPLETE    |
| M8  | Noise and channel imperfections | COMPLETE — REVIEWED & VALIDATED |
| M9  | Honest baseline                | COMPLETE — REVIEWED & VALIDATED |
| M10 | Statistical threshold engine   | NOT STARTED |
| M11 | Forgery detection              | NOT STARTED |
| M12 | Replay detection               | NOT STARTED |
| M13 | Impersonation detection        | NOT STARTED |
| M14 | Unauthorized verification      | NOT STARTED |
| M15 | Quantum-channel attacks        | NOT STARTED |
| M16 | Evidence fusion                | NOT STARTED |
| M17 | Security evaluation            | NOT STARTED |
| M18 | Performance evaluation         | NOT STARTED |
| M19 | Dashboard                      | NOT STARTED |
| M20 | Blockchain audit layer         | DEFERRED    |

---

# 6. M0 — Environment Setup

## Objective

Prepare the development environment.

### Tasks

* [x] Verify Python installation
* [x] Create virtual environment
* [x] Install Qiskit
* [x] Install Qiskit Aer
* [x] Install NumPy
* [x] Install SciPy
* [x] Install Pandas
* [x] Install Matplotlib
* [ ] Install Streamlit
* [x] Create `requirements.txt`
* [x] Verify imports
* [x] Run a minimal Qiskit circuit
* [x] Run a minimal Aer simulation
* [x] Record package versions

### Tests

* [x] Python environment works
* [x] Qiskit imports
* [x] Aer imports
* [x] Simulator executes
* [x] Basic measurement works

### Status

```text
COMPLETE
```

### Environment Details

* **Python Version:** 3.13.5 (Windows AMD64)
* **Qiskit Version:** 2.5.2
* **Qiskit Aer Version:** 0.17.2
* **NumPy Version:** 2.5.2
* **SciPy Version:** 1.18.1
* **Pandas Version:** 3.0.5
* **Matplotlib Version:** 3.11.1
* **Decisions/Problems:** Fixed cross-platform setup issue where macOS virtual environment binaries and macOS-specific settings had been committed to git. Removed broken macOS `.venv`, added `.gitignore`, configured Windows virtual environment (`.venv`), installed required quantum and scientific stack packages, and configured `.vscode/settings.json` with pytest and Windows interpreter path. Tests passed successfully.

---

# 7. M1 — Qubit Fundamentals

## Objective

Understand and implement the basic qubit representation required by the project.

### Tasks

* [x] Represent \(|0\rangle\)
* [x] Represent \(|1\rangle\)
* [x] Understand superposition
* [x] Implement/verify normalized state vectors
* [x] Verify measurement probabilities
* [x] Verify probability normalization

### Tests

* [x] State normalization
* [x] Born-rule probabilities
* [x] Probability sum equals 1 within numerical tolerance
* [x] Single-qubit Qiskit Aer measurements
* [x] Empirical probability derivation and statistical tolerance validation

### Status

```text
COMPLETE
```

### Implementation Details

* **Modules:** `src/quantum/states.py`, `src/quantum/measurements.py`, `src/quantum/__init__.py`
* **Test Suite:** `tests/quantum/test_states.py`, `tests/quantum/test_measurements.py`
* **Supported States:** \(|0\rangle, |1\rangle, |+\rangle, |-\rangle, |+i\rangle, |-i\rangle\) (including 1D arrays, 2D column-vector kets, and `QubitState` dataclass)
* **Qiskit Compatibility:** Qiskit 2.5.2 and Qiskit Aer 0.17.2 using `QuantumCircuit.initialize` and `AerSimulator.run`
* **Review & Verification:** All 52 tests (2 M0 regression tests, 31 state tests, 19 measurement tests) passing cleanly with zero warnings (`pytest -W error`). Scientific review verified exact state vectors, normalization, Born rule computational probabilities, and empirical distributions for \(|0\rangle, |1\rangle, |+\rangle, |-\rangle, |+i\rangle, |-i\rangle\). Edge-case handling verified for ket shapes, zero vector, non-finite values, type checks, shot validation, and integer/string count dictionaries.

---

# 8. M2 — Pauli Operators

## Objective

Implement and validate Pauli operations.

### Required operators

```text
I
X
Y
Z
```

### Required tasks

* [x] Define operators
* [x] Apply X
* [x] Apply Y
* [x] Apply Z
* [x] Validate eigenstates
* [x] Validate matrix operations
* [x] Test numerical correctness

### Required states

```text
|0>
|1>
|+>
|->
|+i>
|-i>
```

### Status

```text
COMPLETE
```

### Implementation Details

* **Modules:** `src/quantum/pauli.py`, `src/quantum/__init__.py`
* **Test Suite:** `tests/test_pauli.py` (40 passing unit, property, and edge-case tests)
* **Operators:** 
  * $I = \begin{bmatrix}1 & 0 \\ 0 & 1\end{bmatrix}$
  * $X = \begin{bmatrix}0 & 1 \\ 1 & 0\end{bmatrix}$
  * $Y = \begin{bmatrix}0 & -i \\ i & 0\end{bmatrix}$ (verified complex, not real)
  * $Z = \begin{bmatrix}1 & 0 \\ 0 & -1\end{bmatrix}$
* **Algebraic Properties Verified:**
  * Hermiticity: $U^\dagger = U$ for all 4 operators
  * Unitarity: $U^\dagger U = I$ for all 4 operators
  * Squaring / Involutory: $I^2 = X^2 = Y^2 = Z^2 = I$
  * Anti-commutation: $XY = -YX = iZ$, $YZ = -ZY = iX$, $ZX = -XZ = iY$
* **State Transformations Verified:**
  * Computational basis: $I|0\rangle=|0\rangle, I|1\rangle=|1\rangle, X|0\rangle=|1\rangle, X|1\rangle=|0\rangle, Y|0\rangle=i|1\rangle, Y|1\rangle=-i|0\rangle, Z|0\rangle=|0\rangle, Z|1\rangle=-|1\rangle$
  * X-basis: $X|+\rangle=|+\rangle, X|-\rangle=-|-\rangle, Z|+\rangle=|-\rangle, Z|-\rangle=|+\rangle$
  * Y-basis: $Y|+i\rangle=+|+i\rangle, Y|-i\rangle=-|-i\rangle$
  * Normalization preservation: verified $\langle U\psi|U\psi\rangle = 1$ across all 4 operators on all 6 standard states
* **Regression Status:** All 92 tests passing (2 M0 environment tests, 50 M1 state/measurement tests, 40 M2 Pauli tests) with zero warnings (`pytest -W error`).

---

# 9. M3 — Projective Measurement

## Objective

Implement measurement in:

```text
X basis
Y basis
Z basis
```

### Tasks

* [x] Z-basis measurement
* [x] X-basis measurement
* [x] Y-basis measurement
* [x] Measurement probabilities (Born rule: $P(i) = \langle\psi|P_i|\psi\rangle$)
* [x] Measurement counts (deterministic theoretical & reproducible sampling)
* [x] Empirical probability calculation ($\hat{p}_i = n_i / N$)
* [x] Pauli expectation values ($\langle Z\rangle, \langle X\rangle, \langle Y\rangle$)
* [x] Wrong-basis experiment (50/50 uniform statistics across all 6 Pauli eigenstates)

### Tests

* [x] Basis orthonormality ($\langle b_i|b_j\rangle = \delta_{ij}$ for $Z, X, Y$)
* [x] Projector properties (idempotence $P^2=P$, Hermiticity $P^\dagger=P$, completeness $\sum P=I$, orthogonality $P_0 P_1=0$)
* [x] Native eigenstate measurement (deterministic 1.0 probability on all 6 Pauli eigenstates)
* [x] Wrong-basis measurement (all 12 cross-basis combinations yielding $\approx 0.5$ within tight statistical bounds)
* [x] Six-state measurement validation ($|0\rangle, |1\rangle, |+\rangle, |-\rangle, |+i\rangle, |-i\rangle$)
* [x] Probability normalization ($\sum P(i) = 1.0$, $P(i) \in [0, 1]$)
* [x] Qiskit Aer simulation cross-validation with basis rotation circuits ($H$ for $X$, $S^\dagger H$ for $Y$)
* [x] Error handling & edge cases (invalid basis, non-finite values, zero vectors, unnormalized vectors, shot/seed validation)

### Status

```text
COMPLETE
```

### Implementation Details

* **Files Created/Modified:**
  * Modified: `src/quantum/measurements.py`
  * Modified: `src/quantum/__init__.py`
  * Created: `tests/test_projective_measurement.py`
* **Measurement Bases Implemented:**
  * $Z$ basis (computational): $\{|0\rangle, |1\rangle\}$ with projectors $P_0 = |0\rangle\langle 0|$, $P_1 = |1\rangle\langle 1|$, labels `("0", "1")`
  * $X$ basis (Hadamard): $\{|+\rangle, |-\rangle\}$ with projectors $P_+ = |+\rangle\langle +|$, $P_- = |-\rangle\langle -|$, labels `("+", "-")`
  * $Y$ basis (circular): $\{|+i\rangle, |-i\rangle\}$ with projectors $P_{+i} = |+i\rangle\langle +i|$, $P_{-i} = |-i\rangle\langle -i|$, labels `("+i", "-i")` (essential complex phase preserved)
* **Theoretical Probabilities:**
  * Born-rule calculation: $P(i) = \langle\psi|P_i|\psi\rangle = |\langle i|\psi\rangle|^2$ via `projective_probabilities(state, basis, atol)`
  * Probability normalization strictly enforced with machine tolerance residual cleaning.
* **Sampling Support:**
  * Multinomial sampling via `sample_measurement(probabilities, shots, seed)` supporting deterministic random seeds.
  * Empirical probabilities: $\hat{p}_i = n_i / N$ via `calculate_empirical_probabilities(counts, total_shots)`.
  * Single-call high-level interface: `measure_projective(state, basis, shots, seed)`.
  * Pauli expectation values: $\langle Z\rangle = P(0) - P(1)$, $\langle X\rangle = P(+) - P(-)$, $\langle Y\rangle = P(+i) - P(-i)$ via `calculate_expectation_value(probabilities_or_counts, basis)`.
  * Qiskit circuit representation: `create_basis_measurement_circuit(state, basis)` implementing basis rotations ($H$ for $X$, $S^\dagger H$ for $Y$) measured in the standard computational basis.
* **Test Suite:** 52 tests in `tests/test_projective_measurement.py` covering orthonormality, projectors, 6 native eigenstates, 12 wrong-basis cross tests, general state Born-rule checks, expectation values, Qiskit Aer simulation, input validation, and bug-catching sensitivity.
* **Regression Result:**
  * M0: PASS (2 tests)
  * M1: PASS (50 tests)
  * M2: PASS (40 tests)
  * M3: PASS (52 tests)
  * Total: 144 passed in 1.88s with zero warnings (`pytest -v -W error`).
* **Scientific Decisions:**
  * Projector operators $P_i = |i\rangle\langle i|$ satisfy idempotence, Hermiticity, completeness, and orthogonality.
  * Outcome labels standardize as `("0", "1")` for $Z$, `("+", "-")` for $X$, and `("+i", "-i")` for $Y$.
  * Circuit simulation uses unitary pre-measurement rotations: $H$ for $X$-basis and $H S^\dagger$ for $Y$-basis.

---

# 10. M4 — Bell States

## Objective

Implement Bell-state preparation.

### Primary state

$$
|\Phi^+\rangle =
\frac{|00\rangle+|11\rangle}{\sqrt{2}}
$$

### Tasks

* [x] Create two-qubit circuit ($H$ on $q_0$, $CNOT(0, 1)$)
* [x] Apply H gate
* [x] Apply CNOT
* [x] Measure Bell state in computational basis
* [x] Verify expected distribution ($P(00)=0.5, P(11)=0.5, P(01)=0, P(10)=0$)
* [x] Calculate correlations ($P(q_0=q_1)=1.0, P(q_0\neq q_1)=0.0, \langle Z\otimes Z\rangle = +1.0$)
* [x] Entanglement proof (Schmidt rank = 2, non-factorizable)
* [x] Validate distinction from classical mixture ($\langle X\otimes X\rangle = +1.0$ vs $0.0$)
* [x] Partial trace reduced density matrices ($\rho_A = \rho_B = I_2 / 2$, maximally mixed)

### Expected ideal behaviour

The computational-basis measurement produces strictly correlated outcomes `00` and `11` with zero `01`/`10` outcomes under ideal simulation.

### Status

```text
COMPLETE
```

### Implementation Details

* **Files Created/Modified:**
  * Created: `src/quantum/bell.py`
  * Modified: `src/quantum/__init__.py`
  * Created: `tests/test_bell.py`
* **Bell State Definition:**
  * Canonical state: $|\Phi^+\rangle = \frac{|00\rangle+|11\rangle}{\sqrt{2}} = \left[\frac{1}{\sqrt{2}}, 0, 0, \frac{1}{\sqrt{2}}\right]^T$
  * Standard computational basis ordering: $|00\rangle, |01\rangle, |10\rangle, |11\rangle$
* **Mathematical & Physical Validation:**
  * Normalization: $\langle\Phi^+|\Phi^+\rangle = 1.0$ strictly verified.
  * Born probabilities: $P(00)=0.5, P(11)=0.5, P(01)=0.0, P(10)=0.0$.
  * Correlation: Perfect correlation $P(q_0=q_1)=1.0, P(q_0\neq q_1)=0.0$.
  * Observable correlations: $\langle Z\otimes Z\rangle = +1.0, \langle X\otimes X\rangle = +1.0, \langle Y\otimes Y\rangle = -1.0, \langle Z\otimes X\rangle = 0.0$.
  * Entanglement: Schmidt decomposition on coefficient matrix $C = \begin{bmatrix} 1/\sqrt{2} & 0 \\ 0 & 1/\sqrt{2} \end{bmatrix}$ yields Schmidt rank 2 > 1, proving non-factorizability (pure entangled state).
  * Quantum Coherence: Distinct from classical mixture $\rho_{\text{mix}} = 0.5|00\rangle\langle 00| + 0.5|11\rangle\langle 11|$, where $\langle X\otimes X\rangle = 0.0$.
  * Reduced states: $\rho_A = \operatorname{Tr}_B(|\Phi^+\rangle\langle\Phi^+|) = I_2/2$, $\rho_B = \operatorname{Tr}_A(|\Phi^+\rangle\langle\Phi^+|) = I_2/2$ (maximally mixed, purity 0.5).
* **Qiskit Aer Simulation:**
  * Ideal circuit simulation with 10,000 shots produces only `00` and `11` counts (0 counts for `01` and `10`).
  * Measured frequencies are approximately 50/50 within statistical confidence intervals.
  * Explicit qubit-to-bit ordering documented and verified ($q_0 \to c_0, q_1 \to c_1$).
* **Test Suite:** 41 tests in `tests/test_bell.py` covering state creation, complete orthonormal Bell basis (|Phi+>, |Phi->, |Psi+>, |Psi->), normalization, Born-rule probabilities, correlations, Schmidt entanglement rank, product-state rejection (|00>, |11>, |++>, |+> (x) |0>), reduced density matrix Hermiticity and purity, Qiskit Statevector verification, asymmetric qubit-to-bit ordering verification through measure_bell_state, Kronecker ordering sensitivity (Bug F), complex conjugation sensitivity (Bug G), non-Hermitian operator rejection, negative-count rejection, and input validation.
* **Regression Result:**
  * M0: PASS (2 tests)
  * M1: PASS (50 tests)
  * M2: PASS (40 tests)
  * M3: PASS (52 tests)
  * M4: PASS (41 tests)
  * Total: 185 passed in 1.82s with zero warnings (`pytest -v -W error`).
* **Type-Check Result:** Pyright reports 0 errors, 0 warnings across all M4 files (`src/quantum/bell.py`, `tests/test_bell.py`).


---

# 11. M5 — Bell Correlation

## Objective

Establish a reliable mathematical and experimental mechanism for measuring two-qubit observable correlations on pure states and empirical binary measurement results.

### Primary target state

$$
|\Phi^+\rangle = \frac{|00\rangle + |11\rangle}{\sqrt{2}}
$$

Expected same-basis correlations:
* $\langle Z\otimes Z\rangle = +1.0$
* $\langle X\otimes X\rangle = +1.0$
* $\langle Y\otimes Y\rangle = -1.0$

### Tasks

* [x] Two-qubit observable expectation values ($\langle O_0\otimes O_1\rangle = \langle\psi|(O_0\otimes O_1)|\psi\rangle$)
* [x] Theoretical Bell correlations across complete Bell basis ($|\Phi^+\rangle, |\Phi^-\rangle, |\Psi^+\rangle, |\Psi^-\rangle$)
* [x] Empirical correlation from binary counts ($E = (N_{00} + N_{11} - N_{01} - N_{10}) / N_{\text{total}}$)
* [x] Mathematical equivalence with probability formula ($E = P(\text{same}) - P(\text{diff})$)
* [x] Arbitrary two-qubit state support (separable states $|00\rangle, |11\rangle, |++\rangle$, classical mixtures)
* [x] Complex state validation with conjugate transpose bra ($(|\00\rangle + i|11\rangle)/\sqrt{2}$)
* [x] Basis-rotation quantum circuits ($H$ for $X$, $S^\dagger H$ for $Y$, none for $Z$)
* [x] Qiskit Aer simulation cross-validation across $XX, YY, ZZ$
* [x] Qiskit Statevector and SparsePauliOp cross-validation within $10^{-14}$
* [x] Bug-catching sensitivity tests (Bugs A–H: tensor ordering, complex conjugation, $YY$ sign, Bell state signs, count validations)
* [x] Strict input validation (state dimension, finite counts, negative counts, non-empty shots, binary outcome labels)
* [x] Strict scope enforcement (no teleportation, noise, attacks, or security scores)

### Status

```text
COMPLETE
```

### Implementation Details

* **Files Created/Modified:**
  * Created: `src/quantum/correlations.py`
  * Modified: `src/quantum/bell.py` (added `bell_correlations` property on `BellState`, updated `calculate_bell_correlations`)
  * Modified: `src/quantum/__init__.py` (re-exported M5 functions)
  * Created: `tests/test_bell_correlation.py`
* **Mathematical & Empirical Results:**
  * $|\Phi^+\rangle$: $XX = +1.0$, $YY = -1.0$, $ZZ = +1.0$ (strictly negative for $YY$)
  * $|\Phi^-\rangle$: $XX = -1.0$, $YY = +1.0$, $ZZ = +1.0$
  * $|\Psi^+\rangle$: $XX = +1.0$, $YY = +1.0$, $ZZ = -1.0$
  * $|\Psi^-\rangle$: $XX = -1.0$, $YY = -1.0$, $ZZ = -1.0$
  * Asymmetric $|10\rangle$: $\langle Z\otimes I\rangle = -1.0$, $\langle I\otimes Z\rangle = +1.0$ (verifies tensor order)
  * Complex $(|00\rangle + i|11\rangle)/\sqrt{2}$: $\langle X\otimes Y\rangle = +1.0$ (verifies complex conjugate bra)
  * Aer simulation: $N=2000$ and $N=10000$ shots confirm empirical $E_{ZZ} \approx +1, E_{XX} \approx +1, E_{YY} \approx -1$ within $3\sigma$ bounds
  * Qiskit Statevector cross-validation: agreement within machine precision ($10^{-14}$)
* **Test Suite:** 38 tests in `tests/test_bell_correlation.py` covering theoretical calculations, empirical count formulas, basis rotations, Qiskit cross-validation, bugs A–L sensitivity tests, input validation, and scope verification.
* **Regression Result:**
  * M0: PASS (2 tests)
  * M1: PASS (50 tests)
  * M2: PASS (40 tests)
  * M3: PASS (52 tests)
  * M4: PASS (41 tests)
  * M5: PASS (38 tests)
  * Total: 223 passed in 2.13s with zero warnings (`pytest -v -W error`).
* **Type-Check Result:** Pyright reports 0 errors, 0 warnings across the entire repository.

---

# 12. M6 — Quantum Teleportation

## Objective

Implement and validate the standard three-qubit quantum teleportation protocol.

### Protocol Architecture

```text
Alice:
q0: Input state |psi> = alpha|0> + beta|1>
q1: Alice Bell-pair qubit
Bob:
q2: Bob Bell-pair qubit -> output recovered state |psi>

Classical Communication:
c_alice[0] = measurement outcome of q0 (m0, controls Z)
c_alice[1] = measurement outcome of q1 (m1, controls X)
Qiskit little-endian string: 'c1 c0'
```

### Tasks

* [x] Prepare input state (q0)
* [x] Prepare Bell pair (q1, q2 via H(q1), CX(q1, q2))
* [x] Perform Bell measurement (CX(q0, q1), H(q0), measure q0, q1)
* [x] Capture classical results (c_alice[0], c_alice[1])
* [x] Apply Pauli corrections ($U_{\text{corr}} = Z^{m_0} X^{m_1}$)
* [x] Measure output / state recovery on Bob's qubit
* [x] Compare input/output state vectors
* [x] Calculate fidelity ($F = |\langle\psi_{\text{in}}|\psi_{\text{out}}\rangle|^2 = 1.0$)
* [x] Six Pauli eigenstates validated ($|0\rangle, |1\rangle, |+\rangle, |-\rangle, |+i\rangle, |-i\rangle$)
* [x] Arbitrary complex states validated
* [x] All 4 correction branches independently validated (00 -> I, 01 -> X, 10 -> Z, 11 -> ZX)
* [x] Qiskit classical-bit ordering verified with deterministic tests
* [x] Bug-catching sensitivity tests (Bugs A through O covering wrong qubits, missing gates, wrong branch corrections, bit reversal, tensor ordering, conjugation, hardcoding, direct copying, unsquared fidelity, Alice correction, and correction ordering)
* [x] Strict divide-and-conquer scope boundary preserved (no QDS, noise, attacks, or thresholds)

### Status

```text
COMPLETE — REVIEWED & VALIDATED
```

### Implementation Details

* **Files Created/Modified:**
  * Created: `src/quantum/teleportation.py`
  * Modified: `src/quantum/__init__.py` (re-exported M6 functions and dataclasses)
  * Created: `tests/test_teleportation.py` (42 comprehensive test cases)
  * Modified: `tests/test_bell_correlation.py` (updated scope test to check M5 correlations module)
* **Protocol & Correction Rules:**
  * Initial 3-qubit state: $|\Psi_0\rangle = |\psi\rangle_0 \otimes |\Phi^+\rangle_{12}$
  * Alice Bell measurement: $CX(q_0, q_1)$ followed by $H(q_0)$
  * Alice measurements: $q_0 \to m_0 \in \{0, 1\}$, $q_1 \to m_1 \in \{0, 1\}$
  * Bob's correction operator: $U_{\text{corr}}(m_0, m_1) = Z^{m_0} X^{m_1}$
    * Branch $(0, 0) \to I$
    * Branch $(0, 1) \to X$
    * Branch $(1, 0) \to Z$
    * Branch $(1, 1) \to Z X$
  * Bob's post-correction state satisfies $|\psi_{\text{out}}\rangle = |\psi_{\text{in}}\rangle$ identically with zero phase shift across all branches.
  * Quantum state fidelity: $F = |\langle\psi_{\text{in}}|\psi_{\text{out}}\rangle|^2 = 1.0$ (via conjugating `np.vdot`).
* **Validation Results:**
  * 6 Pauli eigenstates: $|0\rangle, |1\rangle, |+\rangle, |-\rangle, |+i\rangle, |-i\rangle$ achieve $F = 1.0$ within $10^{-12}$.
  * Arbitrary complex superpositions (e.g. $(|0\rangle + i|1\rangle)/\sqrt{2}$, $(\sqrt{3}|0\rangle + (1-i)|1\rangle)/\sqrt{5}$, $(|0\rangle + \sqrt{2}e^{i\pi/4}|1\rangle)/\sqrt{3}$) achieve $F = 1.0$ within $10^{-12}$.
  * All four branches ($00, 01, 10, 11$) independently verified to correctly invert the pre-correction state $X^{m_1} Z^{m_0} |\psi\rangle$.
  * Aer simulation (4000 shots) verifies equal branch probabilities ($p \approx 0.25$ per branch) and 100% agreement of Bob's recovered states in computational, X, and Y bases.
  * Qiskit little-endian classical bitstring decoding (`'c1 c0'`) validated deterministically.
  * Full Bug-Catching Sensitivity Suite (Bugs A through O):
    * Bug A: Wrong Bell-pair qubits (H(q0), CX(q0, q1)) detected
    * Bug B: Missing Bell-pair CNOT (CX(q1, q2)) detected
    * Bug C: Missing Bell-measurement CNOT (CX(q0, q1)) detected
    * Bug D: Missing H(q0) detected
    * Bug E: Wrong 01 correction (I, Z, or ZX instead of X) detected
    * Bug F: Wrong 10 correction (I, X, or ZX instead of Z) detected
    * Bug G: Wrong 11 correction (I, X, or Z instead of ZX) detected
    * Bug H: Classical-bit reversal (swapping c0 and c1) detected
    * Bug I: Tensor-product ordering error (asymmetric state $|c_0|^2 = 0.8, |c_1|^2 = 0.2$) detected
    * Bug J: Missing complex conjugation (`np.dot` vs `np.vdot`) detected
    * Bug K: Hard-coded output detected
    * Bug L: Direct state copying detected
    * Bug M: Wrong fidelity formula ($|\langle a|b\rangle|$ instead of $|\langle a|b\rangle|^2$) detected
    * Bug N: Correction applied to Alice instead of Bob detected
    * Bug O: Correction ordering & global phase equivalence ($XZ = -ZX$) verified
* **Test Suite:** 42 tests in `tests/test_teleportation.py` covering circuit construction, Bell-pair isolation, 6 Pauli eigenstates, arbitrary complex states, 4 branches, Qiskit Aer simulation, classical-bit ordering, bugs A through O, input validation, and scope verification.
* **Regression Result:**
  * M0: PASS (2 tests)
  * M1: PASS (50 tests)
  * M2: PASS (40 tests)
  * M3: PASS (52 tests)
  * M4: PASS (41 tests)
  * M5: PASS (38 tests)
  * M6: PASS (42 tests)
  * Total: 265 passed in 2.99s with zero warnings (`pytest -v -W error`).
* **Type-Check Result:** Pyright reports 0 errors, 0 warnings across the entire repository.

---

# 13. M7 — Teleportation Verification

## Objective

Implement a mathematically rigorous verification layer for quantum teleportation to evaluate state overlap fidelity, numerical correctness tolerance, and basis-dependent measurement distributions.

### Tasks

* [x] Define `TeleportationVerificationResult` immutable frozen dataclass
* [x] Implement pure-state overlap fidelity calculation using conjugate inner product ($F = |\langle\psi_{\text{in}}|\psi_{\text{out}}\rangle|^2 = |\text{np.vdot}(\psi_{\text{in}}, \psi_{\text{out}})|^2$)
* [x] Implement numerical correctness tolerance validation (`validate_verification_tolerance`)
* [x] Enforce correctness criterion: $\text{verified} \iff F \ge 1.0 - \text{tolerance}$
* [x] Create core verification API: `verify_teleportation`
* [x] Create result adapter API: `verify_teleportation_result`
* [x] Implement supporting measurement distribution comparison (`compare_measurement_distributions`)
* [x] Validate all six standard Pauli eigenstates ($|0\rangle, |1\rangle, |+\rangle, |-\rangle, |+i\rangle, |-i\rangle$)
* [x] Validate arbitrary complex superposition states
* [x] Validate global-phase invariance ($|\psi\rangle$ vs $e^{i\theta}|\psi\rangle$)
* [x] Validate rejection of orthogonal and perturbed states
* [x] Input validation for invalid dimensions, non-normalized vectors, NaN, Inf, non-numeric types
* [x] Tolerance validation for negative, NaN, Inf, $\ge 1.0$, non-numeric, boolean types
* [x] Cross-validate fidelity against Qiskit public `state_fidelity` API
* [x] Bug-catching sensitivity suite (Bugs A through L)
* [x] Strict divide-and-conquer scope boundary preserved (no QDS, noise, attacks, or thresholds)

### Status

```text
COMPLETE — REVIEWED & VALIDATED
```

### Implementation Details

* **Files Created/Modified:**
  * Created: `src/quantum/teleportation_verification.py`
  * Modified: `src/quantum/__init__.py` (re-exported M7 functions and dataclasses)
  * Created: `tests/test_teleportation_verification.py` (46 comprehensive tests)
* **Mathematical & Scientific Verification:**
  * Fidelity formulation: $F = |\langle\psi_{\text{in}}|\psi_{\text{out}}\rangle|^2 = |\sum_i \psi_{\text{in}, i}^* \psi_{\text{out}, i}|^2$ via `np.vdot`.
  * Invariant under global phase: tested for $\theta \in \{\pi/4, \pi/2, \pi, 3\pi/2, 2\pi/3\}$ yielding $F = 1.0$.
  * Numerical correctness tolerance: default $\epsilon = 10^{-6}$ separates double-precision roundoff from actual divergence. Includes machine-precision boundary handling (`math.isclose(fidelity, threshold, abs_tol=1e-14)`).
  * Measurement distribution comparison: computes Total Variation Distance (TVD) and maximum probability difference across Z, X, Y bases. Proved that matching in one basis (e.g. Z basis for $|+\rangle$ vs $|-\rangle$) does NOT imply state equivalence (Bug O).
* **Validation Results:**
  * 6 Pauli eigenstates: $|0\rangle, |1\rangle, |+\rangle, |-\rangle, |+i\rangle, |-i\rangle$ achieve $F = 1.0$ and `verified = True` across all 4 teleportation branches.
  * Arbitrary complex superpositions (e.g. $(|0\rangle + \sqrt{2}e^{i\pi/4}|1\rangle)/\sqrt{3}$) achieve $F = 1.0$ and `verified = True`.
  * Orthogonal states ($|0\rangle$ vs $|1\rangle$, $|+\rangle$ vs $|-\rangle$) rejected with $F = 0.0$ and `verified = False`.
  * Perturbed states ($F = 0.999 < 1 - 10^{-6}$) rejected with `verified = False`.
  * Full Bug-Catching Sensitivity Suite (Bugs A through O):
    * Bug A: Missing complex conjugation caught (`np.vdot` vs `np.dot`).
    * Bug B: Missing fidelity square caught ($|\langle a|b\rangle| = 0.5 \implies F = 0.25 \ne 0.5$).
    * Bug C: Global phase invariance verified across multiple angles.
    * Bug D: Orthogonal states rejected.
    * Bug E: Non-trivial overlap calculated independently and accurately (0.25, 0.75, 0.5).
    * Bug F: Non-hardcoded fidelity verified on non-identical states.
    * Bug G: Non-hardcoded verification status verified.
    * Bug H: Malformed state vectors (NaN/Inf) rejected with `ValueError`.
    * Bug I: Non-normalized state vectors rejected with `ValueError`.
    * Bug J: Negative, non-finite, and >= 1.0 tolerances rejected with `ValueError`.
    * Bug K: Correct threshold direction ($F \ge 1 - \epsilon$) verified.
    * Bug L: Input and output state identity preserved on asymmetric states.
    * Bug M: Imaginary components truncation caught (complex vs real inner product).
    * Bug N: Wrong state dimensions (1D, 3D, 4D) rejected with `ValueError`.
    * Bug O: Single-basis measurement equality vs full state equality distinction demonstrated.
* **Test Suite:** 46 tests in `tests/test_teleportation_verification.py`.
* **Regression Result:**
  * M0: PASS (2 tests)
  * M1: PASS (50 tests)
  * M2: PASS (40 tests)
  * M3: PASS (52 tests)
  * M4: PASS (41 tests)
  * M5: PASS (38 tests)
  * M6: PASS (42 tests)
  * M7: PASS (46 tests)
  * Total: 311 passed in 2.43s with zero warnings (`pytest -v -W error`).
* **Type-Check Result:** Pyright reports 0 errors, 0 warnings, 0 informations across the entire repository.

---

# 14. M8 — Noise and Honest Quantum-Channel Imperfections

## Objective

Introduce controlled, honest quantum-channel noise into quantum states and the quantum teleportation pipeline to evaluate physical degradation, mixed-state density matrices, and basis-dependent measurement distributions.

### Critical Principle

```text
Noise ≠ Attack
```

M8 models honest, unintentional physical quantum channel degradation. It strictly avoids declaring any output as an attack, anomaly, or suspicious event, and avoids computing statistical baselines or decision thresholds (reserved for M9+).

### Tasks

* [x] Implement density matrix representation, validation, and operations (`src/noise/density_matrix.py`)
  * [x] Pure state to density matrix mapping with complex conjugation ($\rho = |\psi\rangle\langle\psi|$)
  * [x] Density matrix validation: shape (2, 2), Hermiticity ($\rho = \rho^\dagger$), unit trace ($\operatorname{Tr}(\rho) = 1$), positive semidefiniteness (eigenvalues $\ge -\epsilon$)
  * [x] Pure-mixed state fidelity calculation: $F(\psi, \rho) = \langle\psi|\rho|\psi\rangle$
  * [x] Born measurement probabilities in Z, X, and Y bases: $P(i) = \operatorname{Tr}(P_i \rho)$
* [x] Implement CPTP quantum noise channels (`src/noise/models.py`)
  * [x] Probability validation: rejects $p < 0$, $p > 1$, NaN, Inf, non-numeric, and boolean types
  * [x] Kraus completeness validation: $\sum_i K_i^\dagger K_i = I$
  * [x] Bit-flip channel: $\rho' = (1-p)\rho + p X \rho X$ ($K_0 = \sqrt{1-p}I, K_1 = \sqrt{p}X$)
  * [x] Phase-flip channel: $\rho' = (1-p)\rho + p Z \rho Z$ ($K_0 = \sqrt{1-p}I, K_1 = \sqrt{p}Z$)
  * [x] Depolarizing channel (Standard Pauli Convention): $\rho' = (1-p)\rho + \frac{p}{3}(X\rho X + Y\rho Y + Z\rho Z)$
  * [x] Qiskit Aer noise model converter (`create_qiskit_noise_model` with `target_qubits` and `instructions`)
* [x] Integrate noise with teleportation (`src/noise/teleportation_noise.py`)
  * [x] Mathematical simulation: `simulate_noisy_teleportation_mathematical`
  * [x] Circuit execution with targeted qubit noise on Bob's qubit: `simulate_noisy_teleportation_circuit`
  * [x] Parameter sweep utility: `run_noise_sweep`
* [x] Validate zero-noise identity limit across all 6 Pauli states and arbitrary complex superpositions
* [x] Validate basis-dependent distinguishability (bit-flip affects Z basis; phase-flip affects X/Y bases)
* [x] Implement full bug-catching sensitivity suite (Bugs A through O)
* [x] Enforce strict architectural and scientific boundaries (no M9+ baselines, thresholds, signatures, or attacks)

### Status

```text
COMPLETE — REVIEWED & VALIDATED
```

### Implementation Details

* **Files Created/Modified:**
  * Created: `src/noise/__init__.py`
  * Created: `src/noise/density_matrix.py`
  * Created: `src/noise/models.py`
  * Created: `src/noise/teleportation_noise.py`
  * Created: `tests/test_noise.py` (52 comprehensive tests)
  * Modified: `Project_Instructions/decisions.md` (added DEC-054)
  * Modified: `Project_Instructions/progess.md` (updated Milestone Tracker and M8 section)
* **Mathematical & Channel Validation:**
  * Probability checks: $p \in [0.0, 1.0]$, strictly rejecting out-of-bounds, negative, NaN, Inf, and boolean values without silent clipping.
  * Zero-noise identity: verified that $p=0.0$ returns identical density matrices and states within machine tolerance ($10^{-14}$) for $|0\rangle, |1\rangle, |+\rangle, |-\rangle, |+i\rangle, |-i\rangle$, and complex states.
  * Density matrix validation: enforces Hermiticity within numerical tolerance, unit trace within $10^{-7}$, and positive semidefiniteness (no negative eigenvalues).
  * Kraus completeness: verified $\sum K_i^\dagger K_i = I$ across all channels.
  * Depolarizing channel: exact Pauli convention $K = (\sqrt{1-p}I, \sqrt{p/3}X, \sqrt{p/3}Y, \sqrt{p/3}Z)$; verified that the Bloch vector contracts by exactly $(1 - \frac{4}{3}p)$ across all bases.
* **Teleportation Integration & Sweep:**
  * Verified degraded output fidelity across noise strengths: fidelity strictly decreases monotonically under depolarizing noise from $F=1.0$ at $p=0$ down to $F=0.5$ at $p=1.0$.
  * Verified basis sensitivity: bit-flip alters Z-basis statistics while preserving X-basis eigenstates ($|+\rangle$ is invariant under bit-flip); phase-flip alters X-basis statistics while preserving Z-basis computational states ($|0\rangle, |1\rangle$ invariant under phase-flip).
  * In-circuit transmission noise modeling on Bob's qubit validated on Qiskit Aer simulator.
* **Bug-Catching Suite (Bugs A through O):**
  * Bug A: Wrong bit-flip operator (Z or Y instead of X) detected
  * Bug B: Wrong phase-flip operator (X or Y instead of Z) detected
  * Bug C: Wrong depolarizing probabilities detected (unbalanced Pauli weights)
  * Bug D: Missing complex conjugation in outer product ($\psi \psi^T$ vs $\psi \psi^\dagger$) detected on complex states
  * Bug E: Invalid probabilities ($<0, >1$, NaN, Inf) rejected
  * Bug F: Zero-noise identity preservation verified
  * Bug G: Non-physical density matrices (non-Hermitian, trace $\ne 1$, negative eigenvalues) rejected
  * Bug H: Non-CPTP Kraus operators (completeness failure) rejected
  * Bug I: Multi-qubit noise targeting validated (targeted to Bob's qubit, verified in Aer `noise_qubits`)
  * Bug J: Single channel application verified (no duplicate noise multiplication)
  * Bug K: Noise strength sensitivity verified (distinct $p$ produce distinct output states)
  * Bug L: Noise type sensitivity verified (bit-flip, phase-flip, depolarizing produce distinct matrices)
  * Bug M: Reproducibility with explicit seeds verified
  * Bug N: Global RNG isolation verified
  * Bug O: Noise physical characterization verified (strictly physical outputs; no attack/threat labels)
* **Test Suite:** 52 tests in `tests/test_noise.py`.
* **Regression Result:**
  * M0: PASS (2 tests)
  * M1: PASS (50 tests)
  * M2: PASS (40 tests)
  * M3: PASS (52 tests)
  * M4: PASS (41 tests)
  * M5: PASS (38 tests)
  * M6: PASS (42 tests)
  * M7: PASS (46 tests)
  * M8: PASS (52 tests)
  * Total: 363 passed in 2.54s with zero warnings (`pytest -v -W error`).
* **Type-Check Result:** Pyright reports 0 errors, 0 warnings, 0 informations across the entire repository.

---

# 13. M7 — QDS Protocol

## Objective

Convert the teleportation simulation into the project's defined QDS abstraction.

### Tasks

* [ ] Define signer
* [ ] Define verifier
* [ ] Define message representation
* [ ] Define signature representation
* [ ] Define session
* [ ] Define nonce
* [ ] Define verification request
* [ ] Define quantum state sequence
* [ ] Define verification flow
* [ ] Define security assumptions

### Critical open issue

The exact message-to-state mapping must be resolved before final implementation.

### Status

```text
NOT STARTED
```

---

# 14. M8 — Quantum Signature Verification

## Objective

Implement legitimate signature verification.

### Tasks

* [ ] Generate valid signature representation
* [ ] Associate signature with message
* [ ] Run quantum verification
* [ ] Measure X/Y/Z statistics
* [ ] Calculate fidelity
* [ ] Calculate QBER
* [ ] Produce evidence
* [ ] Produce deterministic result

### Expected result

A legitimate signature under acceptable honest conditions should produce:

```text
ACCEPT
```

### Status

```text
NOT STARTED
```

---

# 15. M9 — Honest Baseline

## Objective

Establish the statistical description and baseline models of legitimate quantum verification behavior under honest operating conditions (ideal and noisy), measuring metrics such as fidelity, QBER, Born measurement probabilities, Pauli expectations, and Bell correlations across repeated trials.

### Critical Principle

```text
Noise ≠ Attack
Calibration ≠ Detection
```

M9 characterizes honest quantum behavior under documented operating configurations. It strictly contains no attack detection, no security thresholds, and no threat classification.

### Tasks

* [x] Implement core baseline data structures (`src/statistics/baseline.py`)
  * [x] `MetricStatistics`: Mean ($\mu$), sample variance ($s^2$ with Bessel's correction $N - 1$), standard deviation ($s$), sample count ($N$), bounds, and Student's $t$ confidence intervals ($N \ge 2$; None for $N=1$).
  * [x] `BaselineConfiguration`: Configuration identity, state sequence, noise model type, noise strength $p$, channel location, shot count, calibration runs $N \ge 1$, seed, backend, and deterministic `canonical_hash` (SHA-256).
  * [x] `CalibrationObservation`: Container for single-run metrics (fidelity, QBER, $Z/X/Y$ Born probabilities, Pauli expectations, Bell correlations), explicit `is_honest: bool = True` provenance tag, and defensive immutability.
  * [x] `HonestBaseline`: Immutable baseline container with structural validation, defensive immutability, and JSON-compatible `to_dict()` and `from_dict()` serialization.
  * [x] `calculate_sample_statistics`: Mathematical calculation of sample statistics with Bessel's correction, Student's $t$ confidence intervals, and domain clamping. Accepts sequences and NumPy 1D arrays without mutation.
  * [x] `validate_baseline`: Physical validity enforcement across metric domains (mean, min_value, max_value).
* [x] Implement calibration engine (`src/statistics/calibration.py`)
  * [x] `run_honest_calibration_trial`: Executes single honest teleportation + noise pipeline.
  * [x] `build_honest_baseline_from_observations`: Decoupled aggregation verifying honest provenance and preventing baseline contamination.
  * [x] `calibrate_honest_baseline`: Repeated honest execution ($N$ trials) and baseline construction.
  * [x] `calibrate_noise_sweep`: Parameter sweep generating isolated, unmerged baselines for each noise level.
* [x] Coverage across quantum states:
  * [x] All 6 standard Pauli eigenstates ($|0\rangle, |1\rangle, |+\rangle, |-\rangle, |+i\rangle, |-i\rangle$).
  * [x] Arbitrary complex superposition states ($\alpha|0\rangle + \beta|1\rangle$).
* [x] Operating condition coverage:
  * [x] Zero noise ($p = 0.0$ ideal teleportation baseline).
  * [x] Non-zero honest channel noise (bit-flip, phase-flip, depolarizing).
  * [x] Analytical (shots=None) and empirical sampling (shots>0 on Qiskit Aer).
* [x] Contamination prevention:
  * [x] Pipeline accepts only legitimate honest executions (zero attack simulation paths; rejects `is_honest=False`).
* [x] Full bug-catching sensitivity suite (Bugs A through O).
* [x] Scope enforcement (no M10+ thresholds, detectors, QDS signatures, or ML).

### Status

```text
COMPLETE — REVIEWED & VALIDATED
```

### Implementation Details

* **Files Created/Modified:**
  * Created: `src/statistics/baseline.py`
  * Created: `src/statistics/calibration.py`
  * Modified: `src/statistics/__init__.py`
  * Created: `tests/test_baseline.py` (39 comprehensive tests)
  * Modified: `Project_Instructions/decisions.md` (added DEC-055)
  * Modified: `Project_Instructions/progess.md` (updated Milestone Tracker and M9 section)
* **Statistical Conventions & Validation:**
  * Sample variance: $s^2 = \frac{1}{N - 1}\sum (x_i - \mu)^2$ for $N \ge 2$, $s^2 = 0.0$ for $N = 1$.
  * Confidence intervals: Student's $t$ distribution with $df = N - 1$ at $95\%$ confidence level, clamped to physical metric domains ($N \ge 2$; `None` for $N=1$).
  * Metric domains: fidelity $\in [0, 1]$, QBER $\in [0, 1]$, Born probabilities $\in [0, 1]$, Pauli expectations $\in [-1, 1]$, Bell correlations $\in [-1, 1]$. Validates mean, min, and max.
  * Configuration isolation: SHA-256 digest `canonical_hash` covers all security-relevant operational parameters.
* **Bug-Catching Suite (Bugs A through O):**
  * Bug A: Mean calculation error detected
  * Bug B: Variance denominator error (must be $N - 1$) detected
  * Bug C: Population variance ($N$) vs sample variance ($N - 1$) detected
  * Bug D: Standard deviation formula error detected
  * Bug E: Omitted Pauli eigenstate detected
  * Bug F: Omitted Y-basis states ($|+i\rangle, |-i\rangle$) detected
  * Bug G: Complex state mishandling detected
  * Bug H: Noise strength insensitivity detected
  * Bug I: Noise model insensitivity detected
  * Bug J: Shot count insensitivity detected
  * Bug K: Incompatible configurations sharing baseline identity detected
  * Bug L: Unphysical metric values rejected by validator
  * Bug M: Missing calibration metadata detected
  * Bug N: Accidental mutation of baseline observations detected
  * Bug O: Attack detection logic strictly prohibited from baseline code
* **Test Suite:** 39 tests in `tests/test_baseline.py`.
* **Regression Result:**
  * M0: PASS (2 tests)
  * M1: PASS (50 tests)
  * M2: PASS (40 tests)
  * M3: PASS (52 tests)
  * M4: PASS (41 tests)
  * M5: PASS (38 tests)
  * M6: PASS (42 tests)
  * M7: PASS (46 tests)
  * M8: PASS (52 tests)
  * M9: PASS (39 tests)
  * Total: 402 passed in 4.81s with zero warnings (`pytest -v -W error`).
* **Type-Check Result:** Pyright reports 0 errors, 0 warnings, 0 informations across the entire repository.

---

# 16. M10 — Statistical Threshold Engine

## Objective

Implement deterministic anomaly detection.

### Tasks

* [ ] Compare observed metrics against baseline
* [ ] Implement metric-specific thresholds
* [ ] Support threshold direction
* [ ] Support multiple metrics
* [ ] Generate evidence
* [ ] Produce ACCEPT/SUSPICIOUS/ATTACK
* [ ] Version thresholds
* [ ] Test deterministic decisions

### Critical rule

No unexplained arbitrary thresholds.

### Status

```text
NOT STARTED
```

---

# 17. M11 — Forgery Detection

## Objective

Detect invalid or manipulated signatures.

### Attack scenarios

* [ ] Wrong quantum state
* [ ] Modified signature
* [ ] Incorrect message-signature relationship
* [ ] Invalid signature sequence

### Metrics

* [ ] Detection rate
* [ ] FAR
* [ ] Empirical forgery probability

### Status

```text
NOT STARTED
```

---

# 18. M12 — Replay Detection

## Objective

Detect reuse of a previously valid verification request.

### Tasks

* [ ] Store session
* [ ] Store nonce
* [ ] Store verification history
* [ ] Detect reused nonce/session
* [ ] Reject replay
* [ ] Generate evidence

### Expected behaviour

```text
First request → ACCEPT
Replay → ATTACK
```

### Status

```text
NOT STARTED
```

---

# 19. M13 — Impersonation Detection

## Objective

Detect an attacker claiming to be another signer.

### Tasks

* [ ] Define signer identity
* [ ] Define attacker identity
* [ ] Validate identity
* [ ] Validate authorization
* [ ] Combine identity and signature evidence
* [ ] Generate security decision

### Status

```text
NOT STARTED
```

---

# 20. M14 — Unauthorized Verification

## Objective

Prevent unauthorized participants from performing protected verification operations.

### Tasks

* [ ] Define verifier roles
* [ ] Define authorization rules
* [ ] Validate authorization
* [ ] Reject unauthorized requests
* [ ] Generate evidence

### Status

```text
NOT STARTED
```

---

# 21. M15 — Quantum-Channel Attacks

## Objective

Simulate manipulation of quantum communication.

### Initial attack types

* [ ] Bit flip
* [ ] Phase flip
* [ ] Y-type manipulation
* [ ] Depolarizing disturbance
* [ ] Other explicitly documented attacks

### Tasks

* [ ] Define attack parameters
* [ ] Apply manipulation
* [ ] Run verification
* [ ] Calculate quantum metrics
* [ ] Compare against baseline
* [ ] Detect anomaly
* [ ] Measure ADR/FAR

### Status

```text
NOT STARTED
```

---

# 22. M16 — Evidence Fusion

## Objective

Combine independent security evidence.

### Evidence layers

```text
Protocol
Signature
Quantum
Statistical
```

### Tasks

* [ ] Define evidence schema
* [ ] Define deterministic rules
* [ ] Combine evidence
* [ ] Generate explanation
* [ ] Test conflicting evidence
* [ ] Test unknown anomalies

### Expected outputs

```text
ACCEPT
SUSPICIOUS
ATTACK
```

### Status

```text
NOT STARTED
```

---

# 23. M17 — Security Evaluation

## Objective

Evaluate actual detection performance.

### Required metrics

* [ ] LAR
* [ ] FRR
* [ ] FAR
* [ ] ADR
* [ ] Empirical forgery probability

### Experiments

* [ ] Honest baseline
* [ ] Forgery
* [ ] Replay
* [ ] Impersonation
* [ ] Unauthorized verification
* [ ] Quantum-channel attacks
* [ ] Attack-strength sweep
* [ ] Threshold sensitivity
* [ ] Security operating region

### Status

```text
NOT STARTED
```

---

# 24. M18 — Performance Evaluation

## Objective

Measure computational efficiency.

### Tasks

* [ ] Baseline verification runtime
* [ ] Shot-count benchmark
* [ ] State-count benchmark
* [ ] Noise benchmark
* [ ] Attack benchmark
* [ ] Statistical detection overhead
* [ ] Batch benchmark
* [ ] Memory measurement
* [ ] Optional GPU benchmark

### Status

```text
NOT STARTED
```

---

# 25. M19 — Dashboard

## Objective

Create the final interactive demonstration interface.

### Pages

* [ ] Home / Dashboard
* [ ] Signature Verification
* [ ] Quantum Monitor
* [ ] Attack Laboratory
* [ ] Security Analytics
* [ ] Verification History

### Dashboard must show

* [ ] quantum circuit
* [ ] measurement results
* [ ] QBER
* [ ] fidelity
* [ ] baseline
* [ ] thresholds
* [ ] decision
* [ ] explanation
* [ ] attack type
* [ ] experiment results

### Status

```text
NOT STARTED
```

---

# 26. M20 — Blockchain Audit Layer

## Objective

Add optional tamper-evident audit functionality.

### Status

```text
DEFERRED
```

### Prerequisites

Blockchain must not begin until:

```text
Quantum simulation ✓
QDS verification ✓
Threat detection ✓
Security evaluation ✓
Performance evaluation ✓
Dashboard ✓
```

are sufficiently complete.

---

# 27. Documentation Tracker

| Document                                 | Status            |
| ---------------------------------------- | ----------------- |
| `README.md`                              | COMPLETED         |
| `PROJECT_CONTEXT.md`                     | COMPLETED         |
| `REQUIREMENTS.md`                        | COMPLETED         |
| `ARCHITECTURE.md`                        | COMPLETED         |
| `DEVELOPMENT_PLAN.md`                    | COMPLETED         |
| `AI_INSTRUCTIONS.md`                     | COMPLETED         |
| `SCIENTIFIC_RULES.md`                    | COMPLETED         |
| `THREAT_MODEL.md`                        | COMPLETED         |
| `QDS_PROTOCOL.md`                        | COMPLETED — DRAFT |
| `MATHEMATICAL_MODEL.md`                  | COMPLETED         |
| `SECURITY_MODEL.md`                      | COMPLETED         |
| `TESTING_STRATEGY.md`                    | COMPLETED         |
| `EXPERIMENT_PLAN.md`                     | COMPLETED         |
| `PERFORMANCE_PLAN.md`                    | COMPLETED         |
| `DECISIONS.md`                           | COMPLETED         |
| `PROGRESS.md`                            | ACTIVE            |
| `GLOSSARY.md`                            | PLANNED           |
| `docs/quantum/qubits.md`                 | PLANNED           |
| `docs/quantum/pauli.md`                  | PLANNED           |
| `docs/quantum/projective_measurement.md` | PLANNED           |
| `docs/quantum/bell_states.md`            | PLANNED           |
| `docs/quantum/teleportation.md`          | PLANNED           |
| `docs/qds/qds_basics.md`                 | PLANNED           |
| `docs/qds/protocol.md`                   | PLANNED           |
| `docs/qds/security_assumptions.md`       | PLANNED           |
| `docs/experiments/results.md`            | PLANNED           |

---

# 28. Testing Tracker

## Quantum Tests

* [ ] Qubit normalization
* [ ] Born-rule probabilities
* [ ] Pauli operators
* [ ] Pauli eigenstates
* [ ] X measurement
* [ ] Y measurement
* [ ] Z measurement
* [ ] Bell-state preparation
* [ ] Bell correlations
* [ ] Teleportation
* [ ] All six input states
* [ ] All four correction branches
* [ ] Classical-bit ordering

---

## Noise Tests

* [ ] Ideal baseline
* [ ] Bit-flip noise
* [ ] Phase-flip noise
* [ ] Depolarizing noise
* [ ] Readout error
* [ ] Noise parameter validation

---

## Security Tests

* [ ] Legitimate verification
* [ ] Forgery
* [ ] Replay
* [ ] Impersonation
* [ ] Unauthorized verification
* [ ] Quantum-channel manipulation
* [ ] Unknown anomaly
* [ ] Evidence fusion
* [ ] Deterministic decision

---

# 29. Experiment Tracker

| Experiment                       | Status      |
| -------------------------------- | ----------- |
| E01 Teleportation correctness    | NOT STARTED |
| E02 Honest baseline              | NOT STARTED |
| E03 Ideal vs noisy               | NOT STARTED |
| E04 Noise sweep                  | NOT STARTED |
| E05 Shot-count sweep             | NOT STARTED |
| E06 Forgery                      | NOT STARTED |
| E07 Replay                       | NOT STARTED |
| E08 Impersonation                | NOT STARTED |
| E09 Unauthorized verification    | NOT STARTED |
| E10 Quantum-channel attack       | NOT STARTED |
| E11 Attack-strength sweep        | NOT STARTED |
| E12 Threshold sensitivity        | NOT STARTED |
| E13 Security operating region    | NOT STARTED |
| E14 Security metrics             | NOT STARTED |
| E15 Performance                  | NOT STARTED |
| E16 End-to-end SIH demonstration | NOT STARTED |

---

# 30. Current Blockers

Record anything preventing progress.

Example:

```text
BLOCKER-001
Description:
Exact message-to-state mapping has not yet been finalized.

Impact:
Prevents final signature-generation implementation.

Resolution:
Update DECISIONS.md after evaluating alternatives.
```

### Current blockers

```text
None recorded yet.
```

---

# 31. Open Questions

Important unresolved questions should be tracked here.

### Q1 — Message-to-state mapping

How should a classical message map to the quantum signature-state sequence?

**Status:** OPEN

---

### Q2 — Signature representation

What exact data structure represents a signature?

**Status:** OPEN

---

### Q3 — Baseline method

Which statistical procedure should determine the honest operating region?

**Status:** OPEN

---

### Q4 — Threshold method

How should thresholds be calculated for each metric?

**Status:** OPEN

---

### Q5 — Evidence fusion

What exact deterministic rules combine protocol, signature, and quantum evidence?

**Status:** OPEN

---

# 32. Current Development Focus

Only one primary milestone should be actively implemented at a time.

Example:

```text
CURRENT MILESTONE:
M0 — Environment Setup
```

After completion:

```text
M0
↓
TEST
↓
VALIDATE
↓
DOCUMENT
↓
M1
```

Avoid simultaneously implementing:

```text
quantum layer
+
dashboard
+
blockchain
+
attack engine
```

before the foundations are validated.

---

# 33. Change Log

Use this section to record significant progress.

Example:

```text
## YYYY-MM-DD

Completed:
- ...

Tests:
- ...

Experiments:
- ...

Decisions:
- ...

Blockers:
- ...

Next:
- ...
```

---

# 34. Definition of Done

A milestone is complete only when all applicable requirements are satisfied.

```text
[ ] Requirement understood
[ ] Design documented
[ ] Implementation completed
[ ] Unit tests passed
[ ] Integration tests passed
[ ] Scientific validation completed
[ ] Experiment completed
[ ] Results recorded
[ ] Documentation updated
[ ] No known blocker remains
```

---

# 35. SIH MVP Definition

The Q-SHIELD MVP is considered complete when the following pipeline works:

```text
Message
   ↓
Quantum state representation
   ↓
Bell-state generation
   ↓
Quantum teleportation
   ↓
Pauli correction
   ↓
Projective measurement
   ↓
Measurement statistics
   ↓
Honest baseline
   ↓
Statistical threshold comparison
   ↓
Threat detection
   ↓
ACCEPT / SUSPICIOUS / ATTACK
```

and at least the following attacks can be demonstrated:

```text
Forgery
Replay
Quantum-channel manipulation
```

with measurable experimental results.

---

# 36. SIH Competition-Ready Definition

A stronger competition-ready version should additionally provide:

```text
Six-state teleportation validation
+
Noise calibration
+
Noise sweep
+
Shot sweep
+
Forgery probability
+
Replay detection
+
Impersonation detection
+
Unauthorized verification
+
Multiple quantum-channel attacks
+
Threshold sensitivity
+
Security operating region
+
FAR / FRR / LAR / ADR
+
Performance benchmark
+
Explainable evidence
+
Interactive dashboard
```

---

# 37. Final Progress Principle

The project should never confuse:

```text
"I wrote the code"
```

with:

```text
"The feature is scientifically validated."
```

Q-SHIELD follows:

```text
CODE
 ↓
TEST
 ↓
MEASURE
 ↓
VALIDATE
 ↓
DOCUMENT
 ↓
DEMO
```

Every major security claim must eventually have experimental evidence behind it.

**Status:** ACTIVE

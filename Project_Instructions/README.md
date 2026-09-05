# SIH_2K26
Q-SHIELD

Quantum Signature Security & Threat Detection Framework

Project context file for Antigravity / AI coding agents, the
3-person development team, and future contributors.

Primary SIH Problem Statement: 26141
Title: Quantum-Inspired Cyber Threat Detection for Digital
Signature Security
Organization: Egreen Quanta
Category: Software
Theme: Blockchain & Cybersecurity

1. READ THIS FIRST

This repository is being developed by a 3-person student team for
Smart India Hackathon (SIH) Problem Statement 26141.

The team is starting with almost zero prior quantum-computing
knowledge. The project must therefore be developed incrementally, with
every important quantum concept understood before it is incorporated
into the final system.

The application is primarily a software simulation/prototype, not a
physical quantum-device implementation.

The development priority is:

Build and understand the basic quantum model.

Build the QDS-inspired verification model.

Build deterministic statistical threat detection.

Test honest behaviour and realistic simulated noise.

Implement attack simulations.

Evaluate security and performance.

Build the user-facing dashboard.

Add persistence/audit features.

Only after the core system is complete, optionally add blockchain
auditability.

Critical project principle

Do not start with blockchain, a large frontend, authentication,
deployment, or unnecessary infrastructure.

The quantum/security core is the product. Everything else supports it.

2. PROBLEM STATEMENT CONTEXT

The SIH problem concerns the security of digital signatures in the
context of quantum technologies.

Classical public-key cryptographic systems such as RSA and ECC rely on
computational hardness assumptions. A sufficiently capable quantum
computer running algorithms such as Shor's algorithm could threaten
important public-key cryptographic assumptions.

Quantum Digital Signatures (QDS) are a different approach: they use
quantum information/communication as part of the signature/security
protocol and investigate properties such as unforgeability,
non-repudiation, transferability, and information-theoretic security
under appropriate protocol assumptions.

The SIH requirement calls for a quantum-inspired cyber-threat
detection framework for digital-signature security and specifically
expects concepts including:

Pauli eigenstates

projective measurements

statistical measurement analysis

threshold-based decisions

Bell-state entanglement

QKD-related concepts

quantum teleportation

Pauli corrections

attack simulation

mathematical modelling

security analysis

performance evaluation

detection of forgery

detection of impersonation

detection of replay

detection of quantum-channel manipulation

unauthorized verification attempts

efficient verification

no AI/ML

3. OUR INTERPRETATION OF THE PROJECT

Q-SHIELD is not intended to claim that it creates a new, formally
proven QDS protocol.

The core system is a:

Qubit-based, QDS-inspired simulation and deterministic
threat-detection framework constructed to investigate the
security-detection requirements of SIH PS 26141.

This distinction must remain explicit in the documentation, code
comments, presentation, and final report.

Some published teleportation-based QDS protocols use
physical/continuous-variable optical implementations and are more
complex than our qubit simulator. Our project uses a deliberately
simplified qubit-level abstraction so that it can be implemented,
tested, explained, and demonstrated in a software-only SIH prototype.

Never make these unsupported claims

Do NOT claim:

"Q-SHIELD itself provides information-theoretic security."

"Q-SHIELD is a new formally proven QDS protocol."

"Q-SHIELD guarantees 100% attack detection."

"Quantum technology automatically makes the system secure."

"Every replay attack is detectable from quantum measurements."

"Every abnormal quantum measurement is an attack."

"Our simulation is equivalent to a physical QDS deployment."

Preferred wording

Use:

"simulation"

"prototype"

"QDS-inspired model"

"deterministic statistical detection"

"noise-calibrated baseline"

"simulated quantum channel"

"empirical detection probability"

"under the defined attack and noise models"

"security properties depend on protocol assumptions"

4. PROJECT VISION

One-line product description

Q-SHIELD simulates a quantum-signature verification environment,
characterizes honest noisy behaviour, measures quantum/statistical
integrity indicators, combines them with protocol-level security
checks, and deterministically classifies verification attempts as
ACCEPT, SUSPICIOUS, or ATTACK.

Core security idea

Instead of comparing every execution to an ideal noiseless quantum
system:

Ideal quantum behaviour
        |
        v
    compare
        |
        v
    anomaly?

Q-SHIELD first characterizes legitimate behaviour under the configured
honest noise conditions:

Honest executions
        |
        v
Noise characterization
        |
        v
Statistical baseline
        |
        v
Honest operating region
        |
        v
Incoming verification
        |
        v
Statistical comparison
        |
        v
Deterministic decision

This is the project's key design feature.

5. CORE PRODUCT CONCEPT

At a high level:

                +----------------+
                |     Alice      |
                |     Signer     |
                +-------+--------+
                        |
                     Message
                        |
                        v
                +---------------+
                | Message Hash  |
                +-------+-------+
                        |
                        v
              Quantum representation
                        |
                        v
                +---------------+
                | Bell State /  |
                | Entanglement  |
                +-------+-------+
                        |
                        v
                +---------------+
                | Teleportation |
                +-------+-------+
                        |
                  Quantum channel
                        |
               +--------+--------+
               |                 |
            Honest              Eve
               |              Attack
               |                 |
               +--------+--------+
                        |
                        v
                +---------------+
                | Pauli         |
                | Corrections   |
                +-------+-------+
                        |
                        v
                +---------------+
                | Projective    |
                | Measurement   |
                | X / Y / Z     |
                +-------+-------+
                        |
                        v
                +---------------+
                | Statistics    |
                +-------+-------+
                        |
                        v
                +---------------+
                | Baseline +    |
                | Thresholds    |
                +-------+-------+
                        |
                        v
                +---------------+
                | Evidence      |
                | Fusion        |
                +-------+-------+
                        |
            +-----------+-----------+
            |           |           |
            v           v           v
         ACCEPT     SUSPICIOUS    ATTACK
                                  |
                    +-------------+-------------+
                    |             |             |
                    v             v             v
                 Forgery       Replay      Impersonation
                                  |
                                  v
                         Channel manipulation

6. HIGH-LEVEL ARCHITECTURE

The system is divided into layers.

Layer 1: Quantum Layer

Responsible for:

qubits

quantum state preparation

Pauli operators

Pauli eigenstates

Bell-state generation

entanglement

teleportation

Pauli corrections

projective measurements

measurement sampling

Layer 2: QDS-Inspired Protocol Layer

Responsible for:

message handling

message digest/hash

quantum representation

signature state/model

signer information

verification protocol

session information

nonce

authorization metadata

Layer 3: Noise Layer

Responsible for simulated physical/system imperfections:

bit-flip errors

phase-flip errors

Pauli errors

depolarizing noise

readout error

thermal-relaxation-style noise where useful

Layer 4: Statistics Layer

Responsible for:

measurement counts

probabilities

expectation values

X/Y/Z statistics

QBER

fidelity

Bell correlations

means

variance

standard deviation

confidence intervals

hypothesis/statistical tests where justified

Layer 5: Baseline/Calibration Layer

Responsible for:

running honest executions

characterizing expected noisy behaviour

calculating baseline distributions

defining legitimate operating regions

calibrating thresholds

Layer 6: Attack Simulation Layer

Responsible for:

forgery

replay

impersonation

quantum-channel manipulation

attack intensity

controlled attack experiments

Layer 7: Detection Layer

Responsible for:

comparing observations to the baseline

threshold decisions

evidence fusion

deterministic rules

attack classification

ACCEPT/SUSPICIOUS/ATTACK decisions

Layer 8: Evaluation Layer

Responsible for:

false acceptance rate

false rejection rate

detection probability

attack detection rate

noise tolerance

shot-count analysis

latency

throughput

circuit depth

gate count

qubit count

Layer 9: Application Layer

Responsible for:

dashboard

verification interface

attack laboratory

quantum monitor

analytics

reports

verification history

Layer 10: Audit/Blockchain Layer --- FUTURE

Responsible for:

event hashing

immutable audit records

blockchain transaction references

Blockchain is optional and must not become a dependency of the core
quantum/security engine.

7. QUANTUM CONCEPTS REQUIRED

The team is learning quantum computing from scratch. The following
concepts are required.

7.1 Qubit

A classical bit is either 0 or 1.

A qubit can be in a quantum state such as:

|0>
|1>
a|0> + b|1>

where:

|a|^2 + |b|^2 = 1

7.2 Measurement

Measurement converts quantum information into classical outcomes.

The same state may produce different outcomes over repeated shots, so
statistical analysis is fundamental.

7.3 Pauli operators

The project uses:

X = [[0, 1],
     [1, 0]]

Y = [[0, -i],
     [i,  0]]

Z = [[1,  0],
     [0, -1]]

Important eigenstates:

Z basis

|0>
|1>

X basis

|+>
|->

Y basis

|+i>
|-i>

7.4 Projective measurement

For a state |psi> and projector P_i:

p_i = <psi|P_i|psi>

This provides the mathematical foundation for measurement probabilities.

7.5 Bell state

One important Bell state is:

|Phi+> = (|00> + |11>) / sqrt(2)

The simulator should demonstrate correlated outcomes.

7.6 Teleportation

Quantum teleportation transfers an unknown quantum state using:

an entangled pair

Alice's Bell-basis measurement

two classical bits

Bob's Pauli correction

The exact correction mapping must be implemented/tested carefully rather
than hard-coded from memory without verification.

8. QDS-INSPIRED PROTOCOL MODEL

The exact protocol must be specified before it becomes a security claim.

Initial abstraction:

Message
   |
   v
Cryptographic digest
   |
   v
Quantum-state representation
   |
   v
Signature/verification state
   |
   v
Quantum transmission / teleportation
   |
   v
Measurement
   |
   v
Statistical verification

The implementation should explicitly define:

What is Alice's secret/private information?

What is Bob's verification information?

What is public?

What does Eve know?

What can Eve modify?

What exactly constitutes a valid signature?

What measurements are performed?

What statistics are expected from an honest signer?

What constitutes verification success?

What security assumptions are being made?

Do not implement an ambiguous "quantum signature" and then retrofit a
security claim.

9. SECURITY THREAT MODEL

Actors:

Alice

Legitimate signer.

Bob

Legitimate recipient/verifier.

Eve

Adversary.

Potential attacker capabilities must be explicitly documented for each
attack.

10. ATTACK MODELS

10.1 Forgery

Goal:

Eve attempts to create or modify signature/message information such that
Bob accepts it as legitimate.

Detection evidence can include:

signature/message mismatch

quantum measurement inconsistency

fidelity degradation

QBER increase

Pauli-statistic deviation

baseline deviation

Important:

A detector does not create the formal unforgeability property of a QDS
protocol. We measure empirical rejection/false-acceptance behaviour
under our defined simulation model.

10.2 Replay

Eve resends a previously valid verification request/signature.

Important scientific point:

A replay can contain perfectly valid quantum data.

Therefore replay must primarily use protocol-level freshness mechanisms:

nonce

session ID

timestamp

transaction/request ID

used-nonce/session state

Example:

First:
nonce = 1001
=> ACCEPT

Second:
nonce = 1001
=> REPLAY

10.3 Impersonation

Eve claims to be Alice.

Use:

identity/session checks

authorization state

signer association

credential/identity metadata in the simulation

Quantum statistics alone should not be expected to solve all identity
problems.

10.4 Quantum-channel manipulation

Eve modifies/disturbs the quantum channel.

Simulation options:

X/bit-flip error

Z/phase-flip error

Y error

depolarizing channel

controlled Pauli error

readout manipulation/error

configurable attack strength

Expected evidence may include:

fidelity decrease

QBER increase

altered measurement distributions

Pauli expectation deviation

Bell-correlation degradation

11. NO AI / ML

The SIH requirement explicitly excludes AI/ML.

Therefore:

Allowed

mathematical models

probability

statistics

confidence intervals

z-scores

hypothesis tests

threshold rules

deterministic rule engines

empirical distributions

calibrated operating regions

logical evidence fusion

Not allowed as the core detector

neural networks

random forests

SVM

deep learning

clustering

ML classifiers

black-box anomaly detectors

If a future enhancement uses an ML comparison only for research, it must
not replace the required deterministic detector and must not be
presented as the core SIH solution.

12. HONEST BASELINE

This is a central subsystem.

We first execute the system under legitimate conditions.

Example:

Honest execution 1
Honest execution 2
...
Honest execution N

Collect:

X statistics

Y statistics

Z statistics

fidelity

QBER

Bell correlations

measurement distributions

Calculate:

mean
variance
standard deviation
confidence interval

This becomes the:

Honest Quantum Operating Region

The baseline must be generated under clearly documented conditions,
including:

circuit configuration

noise model

noise strength

shot count

state distribution

protocol parameters

random seed policy where relevant

13. THRESHOLD ENGINE

A threshold is not allowed to be arbitrary.

A conceptual starting point may be:

T = mu +/- k*sigma

but the final threshold methodology must be selected after
experimentation.

Possible deterministic approaches:

confidence intervals

z-score thresholds

empirical quantiles

hypothesis tests

separate lower/upper bounds

multivariate distance if justified

The chosen method must be documented.

Evaluate every threshold against:

false acceptance

false rejection

attack detection rate

honest-noise tolerance

14. DECISION ENGINE

The system should have three states:

ACCEPT

Observed behaviour is consistent with legitimate operating conditions.

SUSPICIOUS

Behaviour is abnormal, but evidence is insufficient for a confident
attack classification.

ATTACK

Defined security/protocol conditions are violated strongly enough to
trigger the configured attack rule.

Example:

Identity: VALID
Session: VALID
Nonce: FRESH
Fidelity: NORMAL
QBER: NORMAL
=> ACCEPT

Replay:

Identity: VALID
Session: VALID
Nonce: REUSED
Quantum metrics: NORMAL
=> ATTACK / REPLAY

Channel manipulation:

Identity: VALID
Nonce: FRESH
Fidelity: LOW
QBER: HIGH
Bell correlation: LOW
=> ATTACK / CHANNEL MANIPULATION

15. EVIDENCE FUSION

Q-SHIELD uses two major evidence categories.

Quantum evidence

fidelity

QBER

X expectation/statistics

Y expectation/statistics

Z expectation/statistics

Bell correlations

measurement distribution deviation

Protocol/cyber evidence

identity

authorization

session

nonce freshness

timestamp

transaction/request identity

signature/message relationship

These are combined using deterministic rules.

Example:

Quantum normal + nonce reused
=> Replay

Identity invalid
=> Impersonation

Identity valid + fresh session + severe quantum anomaly
=> Possible quantum-channel manipulation or signature anomaly

Message/signature mismatch + verification failure
=> Forgery attempt

Do not force every attack into a quantum-only explanation.

16. FINAL VERIFICATION REPORT

Every verification should produce an explainable report.

Example:

Q-SHIELD VERIFICATION REPORT

Message:
Transfer ₹5000 to Bob

Signer:
Alice

Identity:
VALID

Session:
VALID

Nonce:
FRESH

--------------------------------
QUANTUM METRICS

Fidelity:
0.982

Expected:
0.975 +/- 0.015

QBER:
0.018

Threshold:
0.040

X deviation:
0.41 sigma

Y deviation:
0.72 sigma

Z deviation:
0.38 sigma

Bell correlation:
0.961

--------------------------------
DECISION

ACCEPT

Reason:
Observed quantum statistics remain inside
the calibrated legitimate operating region.

Attack example:

DECISION:
ATTACK

Classification:
QUANTUM CHANNEL MANIPULATION

Evidence:
- Fidelity below lower operating bound
- QBER above threshold
- Bell correlation degraded
- Multiple measurement statistics deviate
- Identity and session remain valid

17. FINAL APPLICATION / UI

The final product should look like a security-analysis dashboard rather
than a generic quantum-circuit demo.

Page 1 --- Overview

Show:

system status

baseline status

verification count

attacks detected

recent decisions

current configuration

short explanation of Q-SHIELD

Example cards:

Verified: 128
Attacks: 12
Suspicious: 4
Detection Rate: 98%
Baseline: CALIBRATED

The exact values must come from actual stored results, never fabricated.

Page 2 --- Signature Verification

Inputs:

Message
Signer
Session ID
Nonce
Number of shots
Noise configuration

Button:

VERIFY SIGNATURE

Output:

Quantum metrics
Protocol checks
Baseline comparison
Thresholds
Decision
Explanation

Page 3 --- Quantum Monitor

Show:

Bell-state circuit

teleportation circuit

measurement basis

X/Y/Z distributions

fidelity

QBER

Bell correlation

observed vs expected statistics

Purpose:

Make the quantum mechanism understandable to judges.

Page 4 --- Attack Laboratory

Allow the evaluator to choose:

Attack:
[ None
  Forgery
  Replay
  Impersonation
  Bit Flip
  Phase Flip
  Pauli X
  Pauli Y
  Pauli Z
  Depolarizing ]

and:

Attack strength
Shots
Noise level

Then:

RUN ATTACK

Display:

before metrics

after metrics

deviation

threshold

classification

final decision

This should be one of the strongest demo features.

Page 5 --- Detection Analysis

Show:

Expected | Observed | Threshold | Status

for each metric.

Also show why the final decision was reached.

Page 6 --- Security Analytics

Graphs:

noise vs fidelity

noise vs false rejection

attack strength vs detection probability

threshold vs FAR

threshold vs FRR

shots vs measurement stability

attack type vs detection metric

signature length vs empirical forgery acceptance where meaningful

Page 7 --- Verification History

Store:

verification ID

timestamp

signer

message hash

session

attack type

metrics

decision

Use SQLite initially if persistence is required.

Page 8 --- Audit / Blockchain

Future feature only.

Display:

event hash

transaction ID

block

timestamp

blockchain status

Blockchain should record audit metadata/hash, not raw quantum data.

18. TECH STACK

Required initially

Language

Python

Quantum

Qiskit

Qiskit Aer

Numerical/statistical

NumPy

SciPy

Pandas

Matplotlib

Testing

pytest

Version control

Git

GitHub

Later

UI

Streamlit

Persistence

SQLite

API if needed

FastAPI

Blockchain

Solidity

Hardhat or Anvil

Web3 integration

Do not install every dependency on day one.

19. RECOMMENDED PROJECT STRUCTURE

Grow toward:

q-shield/
|
├── README.md
├── requirements.txt
├── pyproject.toml
├── .gitignore
|
├── src/
│   |
│   ├── quantum/
│   │   ├── __init__.py
│   │   ├── states.py
│   │   ├── pauli.py
│   │   ├── bell.py
│   │   ├── teleportation.py
│   │   └── measurements.py
│   |
│   ├── qds/
│   │   ├── __init__.py
│   │   ├── message.py
│   │   ├── signature.py
│   │   ├── verifier.py
│   │   └── protocol.py
│   |
│   ├── noise/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   └── calibration.py
│   |
│   ├── attacks/
│   │   ├── __init__.py
│   │   ├── forgery.py
│   │   ├── replay.py
│   │   ├── impersonation.py
│   │   └── channel.py
│   |
│   ├── statistics/
│   │   ├── __init__.py
│   │   ├── measurements.py
│   │   ├── fidelity.py
│   │   ├── qber.py
│   │   ├── baseline.py
│   │   ├── thresholds.py
│   │   └── tests.py
│   |
│   ├── detection/
│   │   ├── __init__.py
│   │   ├── detector.py
│   │   ├── classifier.py
│   │   └── rules.py
│   |
│   ├── experiments/
│   │   ├── baseline.py
│   │   ├── attacks.py
│   │   └── benchmark.py
│   |
│   └── utils/
|
├── tests/
│   ├── test_states.py
│   ├── test_pauli.py
│   ├── test_measurements.py
│   ├── test_bell.py
│   ├── test_teleportation.py
│   └── test_detection.py
|
├── experiments/
│   ├── results/
│   ├── plots/
│   └── datasets/
|
├── dashboard/
│   └── app.py
|
└── docs/
    ├── architecture.md
    ├── mathematics.md
    ├── protocol.md
    ├── security.md
    └── experiments.md

Do not create empty folders/files merely to match this structure. Build
the repository incrementally.

20. DEVELOPMENT PHASES

Phase 0 --- Environment

Install and verify:

Python

Qiskit

Qiskit Aer

NumPy

SciPy

Pandas

Matplotlib

pytest

Success:

A Python script can import and run Qiskit/Aer.

Phase 1 --- Quantum basics

Learn and implement:

|0>

|1>

X gate

H gate

measurement

shots

Pauli X/Y/Z

Pauli eigenstates

projective measurement

Success:

Team members can explain every operation used.

Phase 2 --- Bell state

Implement Bell-state generation.

Expected ideal behaviour:

00 ≈ 50%
11 ≈ 50%
01 ≈ 0%
10 ≈ 0%

Actual results should be measured rather than hard-coded.

Success:

Bell-state correlation works repeatedly.

Phase 3 --- Teleportation

Implement:

unknown input state

Bell pair

Alice operations

Alice measurements

classical correction bits

Bob Pauli correction

Bob measurement

Test multiple input states.

Success:

Bob's recovered state agrees with the input within expected
simulation/statistical tolerance.

Phase 4 --- Noise

Add:

bit flip

phase flip

Pauli errors

depolarizing

readout errors

other relevant Aer noise models

Measure how noise changes:

fidelity

QBER

measurement distributions

correlations

Success:

Noise causes measurable, reproducible changes.

Phase 5 --- QDS-inspired protocol

Define before coding:

actors

secrets

public information

signature representation

verification procedure

adversary capabilities

security assumptions

Success:

The protocol can be written as a clear step-by-step specification.

Phase 6 --- Quantum verification

Implement:

X/Y/Z measurements

expectation/statistical metrics

fidelity

QBER

Bell correlations

Success:

A verification execution returns a structured metrics object.

Phase 7 --- Honest baseline

Run many honest executions.

Calculate:

mean

variance

standard deviation

confidence/operating intervals

Success:

A reproducible baseline can be generated and saved.

Phase 8 --- Threshold engine

Implement deterministic threshold calculations.

Evaluate threshold choices using:

FAR

FRR

detection rate

Success:

Threshold selection is experimentally justified.

Phase 9 --- Forgery

Simulate legitimate and forged signatures.

Measure:

False Acceptance Rate
False Rejection Rate
Detection Probability

Success:

The detector can reject the defined forged cases under the tested model.

Phase 10 --- Replay

Add:

nonce

session

timestamp

request ID

used-request tracking

Success:

A previously accepted request cannot be accepted again under the replay
policy.

Phase 11 --- Impersonation

Implement deterministic identity/session/authorization checks.

Success:

Invalid signer identity is rejected/classified.

Phase 12 --- Quantum channel attacks

Implement configurable attack/noise strength.

Success:

Attack strength produces measurable changes and detection behaviour can
be plotted.

Phase 13 --- Evidence fusion

Combine quantum and protocol evidence.

Success:

System distinguishes the defined attack categories using deterministic
rules.

Phase 14 --- Three-state decision

Implement:

ACCEPT
SUSPICIOUS
ATTACK

Success:

Borderline cases do not have to be forced into a binary result.

Phase 15 --- Security experiments

Run systematic experiments.

Required results:

FAR

FRR

attack detection rate

noise tolerance

threshold operating region

shots vs stability

attack strength vs detection

comparison across attack types

Phase 16 --- Performance

Measure:

qubit count

circuit depth

gate count

shots

simulation time

statistical processing time

total verification latency

memory

throughput where meaningful

Phase 17 --- Dashboard

Implement Streamlit pages:

Overview

Signature Verification

Quantum Monitor

Attack Laboratory

Detection Analysis

Security Analytics

Verification History

Phase 18 --- Final polish

Add:

documentation

diagrams

test coverage

reproducibility

demo scenarios

report generation

error handling

Phase 19 --- Blockchain

Only after the above is stable.

Possible flow:

Verification result
      |
      v
Canonical event data
      |
      v
Cryptographic hash
      |
      v
Blockchain transaction
      |
      v
Immutable audit reference

Do not store unnecessary sensitive/raw quantum data on-chain.

21. TEAM OF 3 --- GIT WORKFLOW

The team uses one shared Git repository and three separate laptops.

Recommended branch model:

main
 |
 +-- develop
       |
       +-- feature/quantum
       +-- feature/security
       +-- feature/statistics
       +-- feature/ui

For a small student team, avoid creating dozens of long-lived branches.

A practical workflow:

main
  |
  +--- feature/quantum-teleportation
  +--- feature/attack-replay
  +--- feature/statistical-baseline

Each person should:

git pull origin main
git checkout -b feature/<name>

Work:

git add .
git commit -m "feat: implement Bell state simulator"
git push -u origin feature/<name>

Then create a Pull Request.

At least one teammate should review before merging important changes.

22. TEAM RESPONSIBILITY

Suggested division:

Member 1 --- Quantum Core

Own:

quantum basics

Bell states

teleportation

Pauli operations

measurement

noise models

Member 2 --- Security/Threat Model

Own:

QDS protocol model

forgery

replay

impersonation

channel manipulation

detection rules

Member 3 --- Statistics/Evaluation/Application

Own:

baseline

thresholds

fidelity

QBER

experiments

metrics

later Streamlit dashboard

However:

Every member must understand the complete architecture.

Do not create a situation where only one person understands quantum
mechanics.

23. SHARED CODE RULES

Because three laptops share one repository:

Do not commit generated cache files.

Do not commit virtual environments.

Do not commit secrets.

Do not commit huge generated experiment datasets unless deliberately
required.

Use deterministic random seeds for reproducible experiments when
appropriate.

Keep quantum functions small and testable.

Separate simulation from statistical analysis.

Separate attack generation from attack detection.

Never hide attack logic inside the detector.

Document assumptions.

Never silently change threshold definitions.

Never commit fabricated experimental results.

Every graph used in the report must have a reproducible experiment
behind it.

24. IMPORTANT ARCHITECTURAL RULE

Keep this separation:

ATTACK GENERATOR
       |
       v
SIMULATED SYSTEM
       |
       v
MEASUREMENTS
       |
       v
STATISTICAL ENGINE
       |
       v
DETECTOR

Do NOT do:

attack = true
if attack:
    return "ATTACK"

That would make the simulation meaningless.

The detector must infer the condition from observable evidence and
protocol checks.

25. DATA FLOW

A normal verification should approximately follow:

1. Receive message
2. Validate request structure
3. Validate signer/session/authorization
4. Check nonce freshness
5. Generate/obtain signature representation
6. Prepare quantum states
7. Create entanglement
8. Execute teleportation
9. Apply Pauli corrections
10. Apply configured honest noise
11. Perform projective measurements
12. Collect shots
13. Calculate quantum metrics
14. Compare to honest baseline
15. Calculate deviations/statistical evidence
16. Run deterministic security rules
17. Classify attack if applicable
18. Generate decision
19. Generate explanation
20. Record result
21. Optionally audit later

26. SOFTWARE OBJECTS / INTERFACES

Prefer structured objects instead of passing random dictionaries
everywhere.

Possible future data models:

QuantumState
QuantumExecution
MeasurementResult
BaselineProfile
ThresholdProfile
VerificationRequest
VerificationResult
AttackScenario
DetectionEvidence
SecurityDecision
ExperimentResult

Example conceptual verification result:

VerificationResult:
    verification_id
    message_hash
    signer
    session_id
    nonce
    quantum_metrics
    protocol_checks
    baseline_comparison
    evidence
    decision
    attack_type
    timestamp

Exact implementation is flexible.

27. QUANTUM METRICS

The exact metrics must be mathematically defined in
docs/mathematics.md.

Potential metrics:

Measurement probabilities

For each basis:

P(+)
P(-)

or equivalent computational outcomes.

Expectation values

For observable O:

< O > = <psi|O|psi>

estimated from repeated measurements.

Fidelity

Use a clearly defined fidelity formula appropriate to the states being
compared.

For pure states:

F = |<psi|phi>|^2

If mixed states are later used, use the appropriate mixed-state fidelity
definition.

QBER

Define exactly:

QBER = erroneous measurement outcomes / total relevant outcomes

The exact basis/bit definition must be documented.

Bell correlations

Potential quantities:

<XX>
<YY>
<ZZ>

depending on the protocol.

Do not calculate a metric merely because it sounds quantum. Every metric
must have a reason in the detection model.

28. EXPERIMENT DESIGN

Every experiment should specify:

Experiment ID
Goal
Protocol version
Input state(s)
Noise model
Noise strength
Attack model
Attack strength
Shot count
Number of trials
Random seed policy
Metrics
Expected result
Observed result
Conclusion

This makes the research reproducible.

29. REQUIRED SECURITY EVALUATION

At minimum:

Legitimate behaviour

Measure:

acceptance rate

false rejection rate

Forgery

Measure:

false acceptance rate

rejection rate

Replay

Measure:

replay rejection rate

Impersonation

Measure:

impersonation rejection rate

Channel manipulation

Measure:

detection probability versus attack strength

Noise

Measure:

honest acceptance versus noise strength

This last one is particularly important because a detector that rejects
everything is useless.

30. SECURITY OPERATING REGION

A strong final analysis should answer:

At what noise level can the system still accept legitimate executions
while reliably detecting attacks?

Create an operating-region plot:

                Detection
                   ^
                   |
          ATTACK   |************
                   |************
                   |
                   |
        ambiguous  |------------
                   |
                   |
          HONEST   |............
                   +-----------------> Noise

The actual graph must come from experimental data.

31. FALSE ACCEPTANCE VS FALSE REJECTION

These are both important.

False Acceptance

Bad input accepted.

Security problem.

False Rejection

Legitimate input rejected.

Availability/usability problem.

The project should seek a defensible trade-off rather than maximizing
one metric blindly.

32. PERFORMANCE TARGETS

Do not invent performance numbers before testing.

Measure actual:

circuit size

qubits

depth

shots

simulator execution time

detector execution time

total latency

The project should investigate the trade-off:

more shots
    |
    +--> more stable statistics
    |
    +--> more computation

The goal is to identify a reasonable operating point.

33. REPRODUCIBILITY

Experiments should be reproducible.

Use:

explicit configuration files where practical

fixed random seeds for benchmark experiments

versioned experiment definitions

saved baseline parameters

documented environment versions

deterministic detection rules

Never overwrite important experiment results without versioning.

34. TESTING STRATEGY

Tests are required at multiple levels.

Unit tests

Test:

Pauli matrices

state preparation

measurement conversion

Bell state

teleportation corrections

hash generation

nonce freshness

threshold calculation

Integration tests

Test:

message
 -> quantum protocol
 -> measurement
 -> statistics
 -> detector
 -> decision

Security scenario tests

Test:

honest

forged

replay

impersonation

channel manipulation

Regression tests

Every bug fixed should ideally get a regression test.

35. EXPECTED FINAL USER EXPERIENCE

A judge opens Q-SHIELD.

They see:

Q-SHIELD
Quantum Signature Security & Threat Detection

They go to:

Signature Verification

Enter a message and signer.

Click:

VERIFY

The system runs the quantum simulation.

Then displays:

Quantum state
Bell/teleportation process
Measurement results
Fidelity
QBER
X/Y/Z statistics
Baseline
Thresholds
Decision

Then the judge opens:

Attack Laboratory

Selects:

Depolarizing attack
20%

Clicks:

RUN

The system shows how the quantum statistics change and classifies the
attempt.

Then the judge opens:

Security Analytics

and sees experimental graphs demonstrating detection behaviour.

This is the intended final product.

36. DEMO SCENARIOS

Prepare at least five polished demonstrations.

Demo 1 --- Honest signature

Expected:

ACCEPT

Demo 2 --- Forgery

Expected:

ATTACK
FORGERY

Demo 3 --- Replay

Expected:

ATTACK
REPLAY

Demo 4 --- Impersonation

Expected:

ATTACK
IMPERSONATION

Demo 5 --- Quantum channel manipulation

Expected:

ATTACK
QUANTUM CHANNEL MANIPULATION

Also prepare a borderline/noisy case:

SUSPICIOUS

This demonstrates that the system does not simply label every deviation
as an attack.

37. WHAT WE WILL SAY ABOUT INFORMATION-THEORETIC SECURITY

Correct statement:

QDS research investigates information-theoretic security properties
under the assumptions of the underlying quantum protocol. Q-SHIELD is
a simulation and detection framework; it does not independently
establish an information-theoretic security proof.

This wording should be preserved.

38. WHAT WE WILL SAY ABOUT QUANTUM VS POST-QUANTUM CRYPTOGRAPHY

Do not confuse:

PQC

Classical algorithms designed to resist quantum attacks.

Examples include NIST-standardized ML-DSA and SLH-DSA.

QDS

Uses quantum information/communication as part of the security protocol.

Q-SHIELD is exploring QDS-inspired threat detection, not replacing
PQC standards.

39. BLOCKCHAIN FUTURE PLAN

Blockchain is a later enhancement.

Purpose:

Verification result
       |
       v
Event digest/hash
       |
       v
Blockchain
       |
       v
Immutable audit record

Possible fields:

verification_id
event_hash
decision
attack_type
timestamp
protocol_version
baseline_version

Avoid storing:

private information

unnecessary message contents

raw quantum state data

sensitive credentials

Blockchain should improve auditability, not be marketed as the
source of quantum security.

40. ANTI-GRAVITY / AI AGENT CONTEXT

This README is also intended to be consumed by an AI coding agent such
as Antigravity.

The agent should treat this file as the project's high-level source of
truth.

AI coding agent rules

Rule 1

Do not redesign the project architecture without discussing the impact.

Rule 2

Do not introduce AI/ML into the detector.

Rule 3

Do not add blockchain before the core system is stable.

Rule 4

Do not replace Qiskit/Aer with unrelated quantum frameworks without a
clear reason.

Rule 5

Do not invent QDS security claims.

Rule 6

Do not invent experimental results.

Rule 7

Do not use arbitrary thresholds without documenting their justification.

Rule 8

Do not hide attack knowledge inside the detector.

Rule 9

Keep quantum simulation, attacks, statistics, and detection as separate
modules.

Rule 10

Prefer small, testable functions.

Rule 11

When implementing a quantum algorithm, first verify the mathematical
convention and Qiskit implementation.

Rule 12

If a requirement is ambiguous, flag the ambiguity rather than silently
inventing a security assumption.

Rule 13

Do not create large amounts of boilerplate code before the relevant
milestone.

Rule 14

Before modifying shared architecture, inspect the existing repository
and current branch state.

Rule 15

Preserve backward compatibility for existing tests.

Rule 16

Every security metric must have a definition.

Rule 17

Every detection decision should be explainable.

Rule 18

Every experiment should be reproducible.

Rule 19

Never commit secrets, credentials, API keys, private keys, or local
environment files.

Rule 20

When suggesting dependencies, explain why they are needed and avoid
unnecessary packages.

41. AI AGENT DEVELOPMENT STYLE

The AI agent should work in this order:

Understand requirement
       |
       v
Inspect repository
       |
       v
Identify current milestone
       |
       v
Explain proposed change
       |
       v
Implement smallest useful change
       |
       v
Run tests
       |
       v
Inspect output
       |
       v
Document result

Avoid:

Generate entire application
       |
       v
Hope it works

The team is learning quantum computing, so generated code should be
explainable.

42. MILESTONE GATES

Do not move forward until the current milestone works.

Gate M1

Team understands:

qubit

gates

measurement

shots

Gate M2

Pauli X/Y/Z and eigenstates work.

Gate M3

Bell state works.

Gate M4

Teleportation works.

Gate M5

Teleportation works with controlled noise.

Gate M6

QDS-inspired verification specification is written.

Gate M7

Quantum metrics work.

Gate M8

Honest baseline is reproducible.

Gate M9

Threshold engine works.

Gate M10

Forgery experiment works.

Gate M11

Replay detection works.

Gate M12

Impersonation detection works.

Gate M13

Channel manipulation detection works.

Gate M14

Evidence fusion works.

Gate M15

Security evaluation works.

Gate M16

Performance evaluation works.

Gate M17

Dashboard works.

Gate M18

Final demo is stable.

Gate M19

Blockchain may be considered.

43. CURRENT PRIORITY

We are currently at DAY 1 / FOUNDATION.

Do not jump to:

Streamlit

FastAPI

blockchain

smart contracts

cloud deployment

complex authentication

fancy animations

Immediate target:

Python environment
        |
        v
Qiskit
        |
        v
Qubit basics
        |
        v
Pauli operators
        |
        v
Measurement
        |
        v
Bell state

The first major working quantum milestone is:

Generate a Bell state, execute it for many shots, observe the
expected correlations, and explain why the result occurs.

Then move to teleportation.

44. FIRST DEVELOPMENT TASK

Install:

Python
Qiskit
Qiskit Aer
NumPy
SciPy
Pandas
Matplotlib
pytest

Verify imports.

Then create the smallest possible Bell-state experiment.

Do not build the full folder structure yet.

45. DEFINITION OF DONE FOR THE BASIC MODEL

The "basic model" is considered complete when the following work
end-to-end:

[ ] Message input
[ ] Message digest
[ ] QDS-inspired quantum representation
[ ] Bell-state generation
[ ] Quantum teleportation
[ ] Pauli corrections
[ ] Projective measurements
[ ] X/Y/Z statistics
[ ] Fidelity
[ ] QBER
[ ] Bell correlations
[ ] Honest baseline
[ ] Noise simulation
[ ] Deterministic thresholds
[ ] Forgery simulation
[ ] Replay detection
[ ] Impersonation detection
[ ] Channel manipulation simulation
[ ] Attack classification
[ ] ACCEPT/SUSPICIOUS/ATTACK
[ ] Explainable verification report
[ ] Security experiments
[ ] Performance evaluation
[ ] Unit/integration tests

Only after this list is substantially complete should the team spend
significant time on:

[ ] Dashboard polish
[ ] Database improvements
[ ] API
[ ] Blockchain
[ ] Deployment

46. SUCCESS CRITERIA

The final project should demonstrate:

Technical

working quantum simulation

Bell entanglement

teleportation

Pauli corrections

projective measurements

deterministic statistical detection

realistic simulated noise

attack simulation

protocol-level security checks

Security

forgery detection/rejection under defined model

replay detection

impersonation detection

channel manipulation detection

measurable FAR/FRR

measurable detection probability

Scientific

explicit assumptions

reproducible experiments

mathematically justified metrics

calibrated thresholds

clear distinction between noise and attack

limitations documented

Product

interactive verification

attack laboratory

explainable decisions

analytics

clean dashboard

47. KNOWN LIMITATIONS

These limitations must be documented rather than hidden.

The system is a simulation/prototype.

Simulation results do not prove physical-device performance.

QDS security depends on the underlying protocol and assumptions.

The qubit QDS-inspired model is a simplification of some published
QDS implementations.

Real quantum hardware has additional imperfections.

Replay and impersonation require protocol-level controls.

Statistical thresholds are dependent on calibration conditions.

A detector cannot guarantee detection of an attack that is
indistinguishable from legitimate behaviour under the available
observations.

Empirical security metrics are not equivalent to a formal
cryptographic security proof.

Blockchain, if added, provides auditability rather than quantum
security.

48. RECOMMENDED DOCUMENTATION

Maintain:

docs/
├── architecture.md
├── mathematics.md
├── protocol.md
├── security.md
├── attack-models.md
├── experiments.md
└── limitations.md

These documents should explain the system independently of the code.

49. PROJECT PITCH

Short pitch:

Q-SHIELD is a deterministic quantum-security simulation framework
that detects digital-signature threats by combining quantum
measurement statistics with classical protocol security checks.
Instead of comparing executions against an unrealistic ideal quantum
system, Q-SHIELD first calibrates the expected behaviour of an honest
noisy environment and then identifies statistically significant
deviations. The framework simulates Bell entanglement, teleportation,
Pauli corrections, projective measurements, quantum-channel attacks,
forgery, replay and impersonation, and produces explainable ACCEPT,
SUSPICIOUS or ATTACK decisions without AI/ML.

50. JUDGE DEMO STORY

The intended demonstration flow:

1. Introduce Alice, Bob and Eve.
2. Enter a legitimate signed message.
3. Run verification.
4. Show Bell state / teleportation.
5. Show X/Y/Z measurement statistics.
6. Show honest baseline.
7. Show ACCEPT.
8. Open Attack Laboratory.
9. Launch replay.
10. Show replay rejection.
11. Launch forgery.
12. Show quantum/statistical verification failure.
13. Launch channel manipulation.
14. Show fidelity/QBER/Bell degradation.
15. Show deterministic attack classification.
16. Open Security Analytics.
17. Show detection probability, FAR/FRR and noise operating region.
18. Explain that blockchain is a future audit enhancement.

The demo should prove that Q-SHIELD is more than a quantum-computing
visualization.

51. CORE DESIGN PHILOSOPHY

The project should follow this chain:

MATH
  ↓
QUANTUM MODEL
  ↓
SIMULATION
  ↓
MEASUREMENT
  ↓
STATISTICS
  ↓
BASELINE
  ↓
THRESHOLD
  ↓
DETECTION
  ↓
SECURITY EVALUATION
  ↓
PRODUCT

Never reverse this order.

Do not start with UI and then invent the science behind it.

52. CURRENT REPOSITORY STATUS

At the start of development:

Core quantum model:       NOT IMPLEMENTED
Bell state:               NOT IMPLEMENTED
Teleportation:            NOT IMPLEMENTED
Noise model:              NOT IMPLEMENTED
QDS model:                NOT IMPLEMENTED
Statistics:               NOT IMPLEMENTED
Baseline:                 NOT IMPLEMENTED
Threshold engine:         NOT IMPLEMENTED
Attack simulator:         NOT IMPLEMENTED
Detection engine:         NOT IMPLEMENTED
Dashboard:                NOT IMPLEMENTED
Blockchain:               NOT IMPLEMENTED

This is intentional.

We will build incrementally.

53. FINAL ARCHITECTURE SUMMARY

                         Q-SHIELD
                            |
             +--------------+--------------+
             |                             |
             v                             v
       QUANTUM LAYER                 PROTOCOL LAYER
             |                             |
       Bell state                    Identity
       Teleportation                 Session
       Pauli                         Nonce
       Measurement                   Authorization
             |                             |
             +--------------+--------------+
                            |
                            v
                     NOISE / ATTACK
                         SIMULATOR
                            |
                            v
                     MEASUREMENT DATA
                            |
                            v
                    STATISTICAL ENGINE
                            |
               +------------+------------+
               |                         |
               v                         v
        HONEST BASELINE             OBSERVATION
               |                         |
               +------------+------------+
                            |
                            v
                    THRESHOLD ENGINE
                            |
                            v
                    EVIDENCE FUSION
                            |
                 +----------+----------+
                 |          |          |
                 v          v          v
              ACCEPT   SUSPICIOUS    ATTACK
                                      |
                         +------------+------------+
                         |            |            |
                         v            v            v
                      FORGERY      REPLAY    IMPERSONATION
                                      |
                                      v
                             CHANNEL MANIPULATION
                                      |
                                      v
                              EXPLAINABLE REPORT
                                      |
                                      v
                                  DASHBOARD
                                      |
                                      v
                         BLOCKCHAIN AUDIT (LATER)

54. THE GOLDEN RULE

Build the science first.

Build the detector second.

Build the product third.

Add blockchain last.

If an implementation decision conflicts with this principle, stop and
discuss the trade-off before proceeding.

55. REFERENCES / RESEARCH BASIS

The project should consult authoritative and primary sources when making
technical claims.

Recommended starting points:

NIST Digital Signatures:
https://csrc.nist.gov/projects/digital-signatures

NIST Post-Quantum Cryptography:
https://csrc.nist.gov/projects/post-quantum-cryptography

NIST FIPS 204 --- Module-Lattice-Based Digital Signature Standard
(ML-DSA): https://csrc.nist.gov/pubs/fips/204/final

NIST FIPS 205 --- Stateless Hash-Based Digital Signature Standard
(SLH-DSA): https://csrc.nist.gov/pubs/fips/205/final

IBM Quantum Learning --- Quantum Teleportation:
https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information/entanglement-in-action/quantum-teleportation

IBM Quantum --- Building noise models:
https://quantum.cloud.ibm.com/docs/en/guides/build-noise-models

Qiskit documentation: https://quantum.cloud.ibm.com/docs

The team should additionally maintain a project bibliography containing
the specific QDS papers used to justify the protocol abstraction,
security terminology, and experimental methodology.

56. FINAL NOTE TO AI AGENTS

When working on this repository, remember:

This is a student research prototype for SIH PS 26141, not a
production cryptographic library and not a formally proven QDS
implementation.

The objective is to build a technically coherent, reproducible,
explainable and demonstrable simulation framework.

When uncertain:

preserve scientific correctness;

preserve the SIH requirements;

prefer the simplest implementation that can be tested;

clearly document assumptions;

do not invent security guarantees;

do not introduce unnecessary technologies;

ask/flag ambiguity rather than silently making a major architectural
decision.

The core product is Q-SHIELD's quantum + statistical + deterministic
security detection pipeline.


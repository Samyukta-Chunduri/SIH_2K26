"""Tests for Quantum Teleportation (Milestone M6).

Validates:
1. 3-qubit circuit architecture and Bell-pair preparation on (q1, q2).
2. Bell measurement on (q0, q1) and conditional Pauli corrections on q2.
3. Teleportation of all 6 standard Pauli eigenstates (|0>, |1>, |+>, |->, |+i>, |-i>).
4. Teleportation of arbitrary complex states.
5. Independent validation of all 4 correction branches (00, 01, 10, 11).
6. Qiskit Aer simulation, little-endian bitstring decoding, and measurement statistics.
7. Bug-catching sensitivity tests specifically designed to fail under Bugs A through L.
8. Robust input validation and strict M6 scope enforcement.
"""

from __future__ import annotations

import numpy as np
import pytest
from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
from qiskit_aer import AerSimulator

from src.quantum.pauli import PAULI_I, PAULI_X, PAULI_Y, PAULI_Z
from src.quantum.states import (
    STATE_0,
    STATE_1,
    STATE_MINUS,
    STATE_MINUS_I,
    STATE_PLUS,
    STATE_PLUS_I,
    QubitState,
    get_standard_state,
)
from src.quantum.teleportation import (
    TELEPORTATION_CORRECTIONS,
    TeleportationResult,
    apply_teleportation_correction,
    calculate_teleportation_fidelity,
    create_teleportation_circuit,
    decode_teleportation_bitstring,
    get_teleportation_correction,
    simulate_teleportation_circuit,
    simulate_teleportation_mathematical,
)


# ==============================================================================
# 1. Circuit Construction & Gate Structure Tests
# ==============================================================================

class TestTeleportationCircuitConstruction:
    """Validates the structure of the quantum teleportation circuit."""

    def test_circuit_qubit_and_clbit_allocation(self) -> None:
        """Circuit must allocate 3 quantum bits and 2 classical bits by default."""
        qc = create_teleportation_circuit(STATE_0)
        assert qc.num_qubits == 3
        assert qc.num_clbits == 2

        # When Bob is measured, an additional classical bit is allocated
        qc_bob = create_teleportation_circuit(STATE_0, measure_bob=True)
        assert qc_bob.num_qubits == 3
        assert qc_bob.num_clbits == 3

    def test_bell_pair_prepared_on_q1_and_q2_not_q0(self) -> None:
        """Bell pair must be prepared strictly on (q1, q2), leaving q0 unentangled."""
        qc = create_teleportation_circuit(STATE_0)

        # Inspect operations before Alice's Bell measurement CX(0, 1)
        # Look for H gate on qubit 1 and CX gate on qubits (1, 2)
        h_qubits = [
            qc.find_bit(inst.qubits[0]).index
            for inst in qc.data
            if inst.operation.name == "h"
        ]
        # First H gate in circuit must be on qubit 1 (Bell-pair creation)
        assert h_qubits[0] == 1, f"First H gate must be on q1, got qubit {h_qubits[0]}"

        cx_pairs = [
            (qc.find_bit(inst.qubits[0]).index, qc.find_bit(inst.qubits[1]).index)
            for inst in qc.data
            if inst.operation.name == "cx"
        ]
        # First CX must be (1, 2) for Bell pair preparation
        assert cx_pairs[0] == (1, 2), f"First CX must be on (q1, q2), got {cx_pairs[0]}"
        # Second CX must be (0, 1) for Alice's Bell measurement
        assert cx_pairs[1] == (0, 1), f"Second CX must be on (q0, q1), got {cx_pairs[1]}"

    def test_alice_measurement_registers_and_gates(self) -> None:
        """Alice must measure q0 into c_alice[0] and q1 into c_alice[1]."""
        qc = create_teleportation_circuit(STATE_0)
        measurements = [
            (qc.find_bit(inst.qubits[0]).index, qc.find_bit(inst.clbits[0]).index)
            for inst in qc.data
            if inst.operation.name == "measure"
        ]
        assert (0, 0) in measurements, "q0 must be measured into c_alice[0]"
        assert (1, 1) in measurements, "q1 must be measured into c_alice[1]"


# ==============================================================================
# 2. Six Pauli Eigenstates Teleportation
# ==============================================================================

class TestPauliEigenstateTeleportation:
    """Validates teleportation of all 6 standard Pauli eigenstates."""

    @pytest.mark.parametrize(
        "state_name,expected_state",
        [
            ("0", STATE_0),
            ("1", STATE_1),
            ("+", STATE_PLUS),
            ("-", STATE_MINUS),
            ("+i", STATE_PLUS_I),
            ("-i", STATE_MINUS_I),
        ],
    )
    def test_mathematical_teleportation_of_pauli_eigenstates(
        self, state_name: str, expected_state: np.ndarray
    ) -> None:
        """Every Pauli eigenstate teleports with F = 1.0 across all branches."""
        for m0 in (0, 1):
            for m1 in (0, 1):
                res = simulate_teleportation_mathematical(state_name, branch=(m0, m1))
                assert np.isclose(res.fidelity, 1.0, atol=1e-12), (
                    f"Teleportation fidelity < 1.0 for |{state_name}> on branch ({m0}, {m1}): {res.fidelity}"
                )
                # Verify state vector fidelity matches
                fid_direct = calculate_teleportation_fidelity(expected_state, res.output_state)
                assert np.isclose(fid_direct, 1.0, atol=1e-12)

    def test_aer_simulation_teleportation_fidelity_pauli_states(self) -> None:
        """Ideal Aer simulation reproduces 100% agreement for eigenstates in their own basis."""
        sim = AerSimulator()
        shots = 1000

        # |0> in Z basis -> Bob strictly outputs 0 across all Alice branches
        sim_0 = simulate_teleportation_circuit(STATE_0, shots=shots, seed=42, simulator=sim, bob_basis="Z")
        for branch, outcomes in sim_0["bob_outcomes_by_branch"].items():
            if sim_0["branch_counts"][branch] > 0:
                assert outcomes["0"] == sim_0["branch_counts"][branch]
                assert outcomes["1"] == 0

        # |1> in Z basis -> Bob strictly outputs 1 across all Alice branches
        sim_1 = simulate_teleportation_circuit(STATE_1, shots=shots, seed=43, simulator=sim, bob_basis="Z")
        for branch, outcomes in sim_1["bob_outcomes_by_branch"].items():
            if sim_1["branch_counts"][branch] > 0:
                assert outcomes["1"] == sim_1["branch_counts"][branch]
                assert outcomes["0"] == 0

        # |+> in X basis -> Bob strictly outputs 0 (+ eigenvalue) across all branches
        sim_plus = simulate_teleportation_circuit(STATE_PLUS, shots=shots, seed=44, simulator=sim, bob_basis="X")
        for branch, outcomes in sim_plus["bob_outcomes_by_branch"].items():
            if sim_plus["branch_counts"][branch] > 0:
                assert outcomes["0"] == sim_plus["branch_counts"][branch]
                assert outcomes["1"] == 0

        # |+i> in Y basis -> Bob strictly outputs 0 (+i eigenvalue) across all branches
        sim_plus_i = simulate_teleportation_circuit(STATE_PLUS_I, shots=shots, seed=45, simulator=sim, bob_basis="Y")
        for branch, outcomes in sim_plus_i["bob_outcomes_by_branch"].items():
            if sim_plus_i["branch_counts"][branch] > 0:
                assert outcomes["0"] == sim_plus_i["branch_counts"][branch]
                assert outcomes["1"] == 0


# ==============================================================================
# 3. Arbitrary Complex State Teleportation
# ==============================================================================

class TestArbitraryComplexStateTeleportation:
    """Validates teleportation of non-eigenstate, complex superpositions."""

    def test_complex_superposition_state(self) -> None:
        """Teleport |psi> = (|0> + i|1>)/sqrt(2)."""
        complex_state = np.array([1.0 / np.sqrt(2.0), 1.0j / np.sqrt(2.0)], dtype=np.complex128)
        for m0 in (0, 1):
            for m1 in (0, 1):
                res = simulate_teleportation_mathematical(complex_state, branch=(m0, m1))
                assert np.isclose(res.fidelity, 1.0, atol=1e-12)

    def test_asymmetric_arbitrary_complex_state(self) -> None:
        """Teleport an arbitrary non-symmetric complex state with non-zero real and imaginary parts."""
        alpha = 0.6 + 0.2j
        beta = 0.3 - 0.7j
        norm = np.sqrt(abs(alpha) ** 2 + abs(beta) ** 2)
        complex_state = np.array([alpha / norm, beta / norm], dtype=np.complex128)

        for m0 in (0, 1):
            for m1 in (0, 1):
                res = simulate_teleportation_mathematical(complex_state, branch=(m0, m1))
                assert np.isclose(res.fidelity, 1.0, atol=1e-12)
                # Confirm output is not merely a constant or zero
                assert not np.allclose(res.output_state, 0.0)

    def test_qubit_state_instance_support(self) -> None:
        """API accepts QubitState instances seamlessly."""
        qs = QubitState(STATE_PLUS)
        res = simulate_teleportation_mathematical(qs, branch=(1, 1))
        assert np.isclose(res.fidelity, 1.0, atol=1e-12)


# ==============================================================================
# 4. Correction Branch Tests (00, 01, 10, 11)
# ==============================================================================

class TestTeleportationBranches:
    """Explicitly exercises and validates each of the four correction branches independently."""

    def test_branch_00_requires_identity_correction(self) -> None:
        """Branch (0, 0): Bob's state is already |psi>; correction is Identity."""
        name, mat = get_teleportation_correction(0, 0)
        assert name == "I"
        assert np.allclose(mat, PAULI_I)

        # Before correction, Bob's state is |psi>
        psi = np.array([0.8, 0.6], dtype=np.complex128)
        res = simulate_teleportation_mathematical(psi, branch=(0, 0))
        assert res.correction_name == "I"
        assert np.allclose(res.output_state, psi)
        assert np.isclose(res.fidelity, 1.0, atol=1e-12)

    def test_branch_01_requires_x_correction(self) -> None:
        """Branch (0, 1): Bob's uncorrected state is X|psi>; correction is X."""
        name, mat = get_teleportation_correction(0, 1)
        assert name == "X"
        assert np.allclose(mat, PAULI_X)

        psi = np.array([0.8, 0.6], dtype=np.complex128)
        res = simulate_teleportation_mathematical(psi, branch=(0, 1))
        assert res.correction_name == "X"
        assert np.isclose(res.fidelity, 1.0, atol=1e-12)

    def test_branch_10_requires_z_correction(self) -> None:
        """Branch (1, 0): Bob's uncorrected state is Z|psi>; correction is Z."""
        name, mat = get_teleportation_correction(1, 0)
        assert name == "Z"
        assert np.allclose(mat, PAULI_Z)

        psi = np.array([0.8, 0.6], dtype=np.complex128)
        res = simulate_teleportation_mathematical(psi, branch=(1, 0))
        assert res.correction_name == "Z"
        assert np.isclose(res.fidelity, 1.0, atol=1e-12)

    def test_branch_11_requires_zx_correction(self) -> None:
        """Branch (1, 1): Bob's uncorrected state is XZ|psi>; correction is ZX."""
        name, mat = get_teleportation_correction(1, 1)
        assert name == "ZX"
        assert np.allclose(mat, PAULI_Z @ PAULI_X)

        psi = np.array([0.8, 0.6], dtype=np.complex128)
        res = simulate_teleportation_mathematical(psi, branch=(1, 1))
        assert res.correction_name == "ZX"
        assert np.isclose(res.fidelity, 1.0, atol=1e-12)

    def test_all_four_branches_equal_probability(self) -> None:
        """In ideal teleportation, each branch occurs with probability 0.25."""
        sim = AerSimulator()
        shots = 4000
        sim_res = simulate_teleportation_circuit(STATE_0, shots=shots, seed=99, simulator=sim)
        branch_counts = sim_res["branch_counts"]

        # Expected counts per branch is 1000. 3-sigma tolerance: 3 * sqrt(4000 * 0.25 * 0.75) ≈ 82
        for branch, count in branch_counts.items():
            freq = count / shots
            assert abs(freq - 0.25) < 0.05, f"Branch {branch} frequency {freq} deviates from 0.25"


# ==============================================================================
# 5. Qiskit Classical-Bit Ordering & Decoding Tests
# ==============================================================================

class TestQiskitBitOrdering:
    """Verifies Qiskit classical-bit ordering conventions and bitstring decoding."""

    def test_decode_teleportation_bitstring_formats(self) -> None:
        """Validates decoding of various Qiskit bitstring formats."""
        # Format 'bob alice' with alice in 'c1 c0':
        # '0 10' -> bob=0, c1=1, c0=0 -> m0=0, m1=1
        m0, m1, bob = decode_teleportation_bitstring("0 10")
        assert m0 == 0
        assert m1 == 1
        assert bob == 0

        # '1 01' -> bob=1, c1=0, c0=1 -> m0=1, m1=0
        m0, m1, bob = decode_teleportation_bitstring("1 01")
        assert m0 == 1
        assert m1 == 0
        assert bob == 1

        # '11' (without Bob) -> c1=1, c0=1 -> m0=1, m1=1, bob=None
        m0, m1, bob = decode_teleportation_bitstring("11")
        assert m0 == 1
        assert m1 == 1
        assert bob is None

    def test_deterministic_qubit_to_classical_bit_mapping(self) -> None:
        """Confirms that q0 maps to c0 and q1 maps to c1 using a deterministic circuit."""
        # Prepare q0 in |1> and q1 in |0>, measure to c_alice
        qr = QuantumRegister(2, "q")
        cr = ClassicalRegister(2, "c")
        qc = QuantumCircuit(qr, cr)
        qc.x(0)  # q0 = 1, q1 = 0
        qc.measure(0, cr[0])
        qc.measure(1, cr[1])

        sim = AerSimulator()
        counts = sim.run(qc, shots=50).result().get_counts()
        # In Qiskit 'c1 c0', c1=0 and c0=1 -> '01'
        assert "01" in counts
        assert counts["01"] == 50

        # Decode: m0 must be 1, m1 must be 0
        m0, m1, _ = decode_teleportation_bitstring("01")
        assert m0 == 1, "m0 must be 1 (from q0)"
        assert m1 == 0, "m1 must be 0 (from q1)"


# ==============================================================================
# 6. Bug-Catching Sensitivity Tests (Section 12: Bugs A through O)
# ==============================================================================

class TestBugCatchingSensitivity:
    """Tests specifically designed to FAIL if common bugs or implementation defects are introduced."""

    def test_bug_a_wrong_bell_pair_qubits(self) -> None:
        """Bug A: Bell pair prepared on (q0, q1) instead of (q1, q2).

        If Bell pair is prepared on (q0, q1), Alice's input on q0 is overwritten and destroyed
        before teleportation, leaving Bob's qubit unentangled in |0>.
        """
        # Malformed circuit preparing Bell pair on (0, 1)
        qc_bug = QuantumCircuit(3, 2)
        qc_bug.x(0)  # Input |1>
        qc_bug.h(0)  # WRONG: entangling q0
        qc_bug.cx(0, 1)  # WRONG
        qc_bug.cx(0, 1)
        qc_bug.h(0)
        qc_bug.measure(0, 0)
        qc_bug.measure(1, 1)

        sim = AerSimulator()
        counts = sim.run(qc_bug, shots=100).result().get_counts()
        # Bob on q2 was never touched, remains |0>

        # Verify correct circuit has Bell pair strictly on (q1, q2)
        correct_qc = create_teleportation_circuit(STATE_1)
        cx_pairs = [
            (correct_qc.find_bit(inst.qubits[0]).index, correct_qc.find_bit(inst.qubits[1]).index)
            for inst in correct_qc.data
            if inst.operation.name == "cx"
        ]
        assert cx_pairs[0] == (1, 2), "Bug A detected: Bell pair not prepared on (q1, q2)!"

    def test_bug_b_missing_bell_pair_cnot(self) -> None:
        """Bug B: Missing CX(q1, q2) in Bell-pair preparation.

        If CX(q1, q2) is missing, q1 and q2 are in product state |+0>, not entangled.
        Bob's qubit q2 remains in |0> and never receives the state of q0.
        """
        qc = create_teleportation_circuit(STATE_1)
        cx_pairs = [
            (qc.find_bit(inst.qubits[0]).index, qc.find_bit(inst.qubits[1]).index)
            for inst in qc.data
            if inst.operation.name == "cx"
        ]
        assert (1, 2) in cx_pairs, "Bug B detected: missing CX(q1, q2) in Bell-pair preparation!"

        # In mathematical simulation without Bell entanglement, teleporting |1> leaves Bob in |0>
        psi_input = STATE_1
        bell_separable = np.kron(STATE_PLUS, STATE_0)  # missing CNOT
        psi_3q = np.kron(psi_input, bell_separable)
        # Apply Bell measurement CX(0, 1) and H(0)
        eye2 = PAULI_I
        p0 = np.array([[1.0, 0.0], [0.0, 0.0]], dtype=np.complex128)
        p1 = np.array([[0.0, 0.0], [0.0, 1.0]], dtype=np.complex128)
        cx_01 = np.kron(p0, np.kron(eye2, eye2)) + np.kron(p1, np.kron(PAULI_X, eye2))
        h_0 = np.kron((1.0 / np.sqrt(2.0)) * np.array([[1.0, 1.0], [1.0, -1.0]]), np.kron(eye2, eye2))
        psi_mid = h_0 @ cx_01 @ psi_3q
        # For branch (0, 0), Bob's uncorrected state remains |0>, fidelity with |1> is 0.0
        bob_raw = psi_mid[:2] / np.linalg.norm(psi_mid[:2])
        fid_bug = calculate_teleportation_fidelity(psi_input, bob_raw)
        assert fid_bug == 0.0, "Bug B check: missing CX(q1, q2) must fail state recovery!"

    def test_bug_c_missing_bell_measurement_cnot(self) -> None:
        """Bug C: Missing CX(q0, q1) in Alice's Bell measurement.

        Without CX(q0, q1), Alice's input state does not interact with the Bell pair.
        """
        qc = create_teleportation_circuit(STATE_1)
        cx_pairs = [
            (qc.find_bit(inst.qubits[0]).index, qc.find_bit(inst.qubits[1]).index)
            for inst in qc.data
            if inst.operation.name == "cx"
        ]
        assert (0, 1) in cx_pairs, "Bug C detected: missing CX(q0, q1) in Alice's Bell measurement!"

    def test_bug_d_missing_hadamard_on_alice_input(self) -> None:
        """Bug D: Missing H(q0) in Alice's Bell measurement."""
        qc = create_teleportation_circuit(STATE_0)
        h_qubits = [
            qc.find_bit(inst.qubits[0]).index
            for inst in qc.data
            if inst.operation.name == "h"
        ]
        assert 0 in h_qubits, "Bug D detected: missing H(q0) in Alice's Bell measurement!"

    def test_bug_e_wrong_01_correction(self) -> None:
        """Bug E: Wrong correction for branch (0, 1) (e.g. applying I, Z, or ZX instead of X).

        For input |0>, in branch (0, 1), Bob's uncorrected state is X|0> = |1>.
        - Applying I leaves |1> (F = 0.0 with |0>).
        - Applying Z leaves -|1> (F = 0.0 with |0>).
        - Applying ZX on input |+> leaves Z|+> = |-> (F = 0.0 with |+>).
        """
        name, mat = get_teleportation_correction(0, 1)
        assert name == "X"
        assert np.allclose(mat, PAULI_X), "Bug E detected: branch (0, 1) must apply Pauli-X!"

        # Applying I or Z fails on input |0>
        uncorrected_0 = PAULI_X @ STATE_0
        for wrong_op in (PAULI_I, PAULI_Z):
            bad_recovery = wrong_op @ uncorrected_0
            assert calculate_teleportation_fidelity(STATE_0, bad_recovery) == 0.0

        # Applying ZX fails on input |+>
        uncorrected_plus = PAULI_X @ STATE_PLUS
        bad_recovery_zx = (PAULI_Z @ PAULI_X) @ uncorrected_plus
        assert calculate_teleportation_fidelity(STATE_PLUS, bad_recovery_zx) == 0.0

    def test_bug_f_wrong_10_correction(self) -> None:
        """Bug F: Wrong correction for branch (1, 0) (e.g. applying I, X, or ZX instead of Z).

        For input |+>, in branch (1, 0), Bob's uncorrected state is Z|+> = |->.
        - Applying I leaves |-> (F = 0.0 with |+>).
        - Applying X leaves -|-> (F = 0.0 with |+>).
        - Applying ZX on input |0> leaves -|1> (F = 0.0 with |0>).
        """
        name, mat = get_teleportation_correction(1, 0)
        assert name == "Z"
        assert np.allclose(mat, PAULI_Z), "Bug F detected: branch (1, 0) must apply Pauli-Z!"

        # Applying I or X fails on input |+>
        uncorrected_plus = PAULI_Z @ STATE_PLUS
        for wrong_op in (PAULI_I, PAULI_X):
            bad_recovery = wrong_op @ uncorrected_plus
            assert calculate_teleportation_fidelity(STATE_PLUS, bad_recovery) == 0.0

        # Applying ZX fails on input |0>
        uncorrected_0 = PAULI_Z @ STATE_0
        bad_recovery_zx = (PAULI_Z @ PAULI_X) @ uncorrected_0
        assert calculate_teleportation_fidelity(STATE_0, bad_recovery_zx) == 0.0

    def test_bug_g_wrong_11_correction(self) -> None:
        """Bug G: Wrong correction for branch (1, 1) (e.g. applying I, X, or Z instead of ZX).

        For branch (1, 1), Bob's uncorrected state is XZ|psi>.
        - Applying I leaves XZ|psi> (fails on |0>, F = 0.0).
        - Applying Z leaves -X|psi> (fails on |0>, F = 0.0).
        - Applying X leaves Z|psi> (fails on |+>, F = 0.0).
        """
        name, mat = get_teleportation_correction(1, 1)
        assert name == "ZX"
        expected = PAULI_Z @ PAULI_X
        assert np.allclose(mat, expected), "Bug G detected: branch (1, 1) must apply Z @ X!"

        # Test on input |0>: uncorrected is XZ|0> = X|0> = |1>
        uncorr_0 = PAULI_X @ (PAULI_Z @ STATE_0)
        # Applying I leaves |1> (F = 0.0 with |0>)
        assert calculate_teleportation_fidelity(STATE_0, PAULI_I @ uncorr_0) == 0.0
        # Applying Z leaves -|1> (F = 0.0 with |0>)
        assert calculate_teleportation_fidelity(STATE_0, PAULI_Z @ uncorr_0) == 0.0

        # Test on input |+>: uncorrected is XZ|+> = X|-> = -|->
        uncorr_plus = PAULI_X @ (PAULI_Z @ STATE_PLUS)
        # Applying X leaves -X|-> = |-> (F = 0.0 with |+>)
        assert calculate_teleportation_fidelity(STATE_PLUS, PAULI_X @ uncorr_plus) == 0.0

    def test_bug_h_classical_bit_reversal(self) -> None:
        """Bug H: Classical bits c0 and c1 swapped in Pauli correction logic.

        If bits are swapped:
        - branch (0, 1) applies Z instead of X -> F = 0.0 on input |0>
        - branch (1, 0) applies X instead of Z -> F = 0.0 on input |+>
        """
        res = simulate_teleportation_mathematical(STATE_0, branch=(0, 1))
        assert np.isclose(res.fidelity, 1.0, atol=1e-12)

        # Swapped bits: apply Z to branch (0, 1) state
        wrong_corr = PAULI_Z @ (PAULI_X @ STATE_0)
        fid_wrong = calculate_teleportation_fidelity(STATE_0, wrong_corr)
        assert fid_wrong == 0.0, "Bug H check: swapped classical bits must fail state recovery!"

    def test_bug_i_tensor_product_ordering_error(self) -> None:
        """Bug I: Asymmetric state tensor/qubit ordering mistakes.

        Using asymmetric state |psi> = [sqrt(0.8), sqrt(0.2)], verifies that Bob's output
        preserves the exact amplitude ordering (|c0|^2 = 0.8, |c1|^2 = 0.2) rather than inverting.
        """
        psi = np.array([np.sqrt(0.8), np.sqrt(0.2)], dtype=np.complex128)
        res = simulate_teleportation_mathematical(psi, branch=(1, 0))
        assert np.isclose(res.fidelity, 1.0, atol=1e-12)
        assert np.isclose(abs(res.output_state[0]) ** 2, 0.8, atol=1e-12)
        assert np.isclose(abs(res.output_state[1]) ** 2, 0.2, atol=1e-12)

    def test_bug_j_missing_complex_conjugation(self) -> None:
        """Bug J: Using np.dot instead of np.vdot in fidelity calculation.

        For psi_a = [1, i]/sqrt(2) and psi_b = [1, -i]/sqrt(2) (orthogonal):
        vdot(psi_a, psi_b) = 1/2*(1*1 + (-i)*(-i)) = 1/2*(1 - 1) = 0 -> F = 0.0.
        If dot without conjugation is used:
        dot(psi_a, psi_b) = 1/2*(1*1 + i*(-i)) = 1/2*(1 + 1) = 1 -> erroneous F = 1.0!
        """
        psi_a = np.array([1.0 / np.sqrt(2.0), 1.0j / np.sqrt(2.0)], dtype=np.complex128)
        psi_b = np.array([1.0 / np.sqrt(2.0), -1.0j / np.sqrt(2.0)], dtype=np.complex128)

        fid = calculate_teleportation_fidelity(psi_a, psi_b)
        assert np.isclose(fid, 0.0, atol=1e-12), "Bug J detected: missing complex conjugation in fidelity!"

    def test_bug_k_hard_coded_output(self) -> None:
        """Bug K: Hardcoded constant output state."""
        res_0 = simulate_teleportation_mathematical(STATE_0, branch=(0, 0))
        res_1 = simulate_teleportation_mathematical(STATE_1, branch=(0, 0))
        res_plus = simulate_teleportation_mathematical(STATE_PLUS, branch=(0, 0))
        res_plus_i = simulate_teleportation_mathematical(STATE_PLUS_I, branch=(0, 0))

        # All four outputs must be distinct and match respective inputs
        all_outputs = [res_0.output_state, res_1.output_state, res_plus.output_state, res_plus_i.output_state]
        for i in range(len(all_outputs)):
            for j in range(i + 1, len(all_outputs)):
                assert not np.allclose(all_outputs[i], all_outputs[j]), (
                    f"Bug K detected: identical output for states {i} and {j}!"
                )

    def test_bug_l_direct_state_copying(self) -> None:
        """Bug L: Verifies teleportation actually executes quantum operations, not direct copy cheat."""
        qc = create_teleportation_circuit(STATE_1)
        gate_names = [inst.operation.name for inst in qc.data]

        assert "h" in gate_names
        assert "cx" in gate_names
        assert "measure" in gate_names
        assert gate_names.count("cx") >= 2
        assert gate_names.count("measure") >= 2

    def test_bug_m_wrong_fidelity_formula_unsquared(self) -> None:
        """Bug M: Fidelity using |<a|b>| instead of |<a|b>|^2.

        For states with overlap 0.5 (e.g. |0> and cos(pi/3)|0> + sin(pi/3)|1>):
            |<a|b>| = 0.5
            |<a|b>|^2 = 0.25
        The test fails if the fidelity formula omits the square.
        """
        theta = np.pi / 3.0  # cos(theta) = 0.5
        psi_overlap = np.array([np.cos(theta), np.sin(theta)], dtype=np.complex128)

        fid = calculate_teleportation_fidelity(STATE_0, psi_overlap)
        expected_fid = float(np.cos(theta) ** 2)  # 0.25
        unsquared = float(np.cos(theta))  # 0.5

        assert np.isclose(fid, expected_fid, atol=1e-12)
        assert not np.isclose(fid, unsquared, atol=1e-12), (
            "Bug M detected: fidelity returned unsquared overlap magnitude |<a|b>|!"
        )

    def test_bug_n_correction_applied_to_alice_instead_of_bob(self) -> None:
        """Bug N: Conditional Pauli corrections applied to Alice's qubits (q0, q1) instead of Bob (q2).

        Every conditional gate in the circuit must target strictly qubit index 2.
        """
        qc = create_teleportation_circuit(STATE_0)

        # Find all conditional blocks (with qc.if_test)
        for inst in qc.data:
            if inst.operation.name == "if_else":
                target_qubits = [qc.find_bit(q).index for q in inst.qubits]
                assert target_qubits == [2], (
                    f"Bug N detected: conditional operation targets {target_qubits} instead of Bob's qubit [2]!"
                )

    def test_bug_o_incorrect_correction_ordering_global_phase(self) -> None:
        """Bug O: Incorrect correction ordering for branch 11.

        XZ and ZX differ by global phase -1 (XZ = -ZX).
        - Applying ZX inverts XZ with zero global phase shift: (ZX)(XZ|psi>) = |psi>
        - Applying XZ inverts XZ with a global phase of -1: (XZ)(XZ|psi>) = -|psi>
        Fidelity must be phase-insensitive and yield F = 1.0 for both cases.
        """
        psi = np.array([0.8, 0.6], dtype=np.complex128)
        uncorrected_11 = PAULI_X @ (PAULI_Z @ psi)

        # Standard correction ZX
        corr_zx = (PAULI_Z @ PAULI_X) @ uncorrected_11
        assert np.allclose(corr_zx, psi), "ZX must yield exact state |psi> with zero phase shift."
        assert np.isclose(calculate_teleportation_fidelity(psi, corr_zx), 1.0, atol=1e-12)

        # Alternative correction XZ
        corr_xz = (PAULI_X @ PAULI_Z) @ uncorrected_11
        assert np.allclose(corr_xz, -psi), "XZ yields -|psi> differing only by global phase e^(i pi)."
        # Fidelity must recognize -|psi> as physically equivalent (F = 1.0)
        assert np.isclose(calculate_teleportation_fidelity(psi, corr_xz), 1.0, atol=1e-12), (
            "Bug O check: fidelity must handle equivalent global phase states correctly!"
        )


# ==============================================================================
# 7. Edge Cases & Scope Enforcement Tests
# ==============================================================================

class TestEdgeCasesAndScopeEnforcement:
    """Validates boundary conditions, input validation, and M6 milestone boundaries."""

    def test_invalid_state_dimensions_rejected(self) -> None:
        """States with length != 2 raise ValueError."""
        with pytest.raises(ValueError, match="shape"):
            calculate_teleportation_fidelity(np.array([1.0, 0.0, 0.0]), STATE_0)

        with pytest.raises(ValueError, match="shape"):
            create_teleportation_circuit(np.array([1.0, 0.0, 0.0]))

        with pytest.raises(ValueError, match="shape"):
            calculate_teleportation_fidelity(np.array([]), STATE_0)

    def test_non_finite_and_zero_vector_rejected(self) -> None:
        """NaN, Inf, and zero vectors raise ValueError."""
        nan_vec = np.array([np.nan, 1.0])
        with pytest.raises(ValueError, match="finite"):
            calculate_teleportation_fidelity(nan_vec, STATE_0)

        inf_vec = np.array([np.inf, 0.0])
        with pytest.raises(ValueError, match="finite"):
            calculate_teleportation_fidelity(inf_vec, STATE_0)

        zero_vec = np.array([0.0, 0.0])
        with pytest.raises(ValueError, match="zero vector"):
            calculate_teleportation_fidelity(zero_vec, STATE_0)

    def test_unnormalized_state_rejected(self) -> None:
        """Unnormalized states raise ValueError."""
        unnorm = np.array([1.0, 1.0])
        with pytest.raises(ValueError, match="normalized"):
            calculate_teleportation_fidelity(unnorm, STATE_0)

    def test_invalid_branch_bits_rejected(self) -> None:
        """Non-binary or non-integer branch inputs raise ValueError or TypeError."""
        with pytest.raises(ValueError, match="must be in"):
            get_teleportation_correction(2, 0)

        with pytest.raises(TypeError, match="integer"):
            get_teleportation_correction("0", 1)  # type: ignore

        with pytest.raises(ValueError, match="must be in"):
            apply_teleportation_correction(STATE_0, -1, 0)

        with pytest.raises(TypeError):
            simulate_teleportation_mathematical(STATE_0, branch=123)  # type: ignore

        with pytest.raises(ValueError, match="bits must be in"):
            simulate_teleportation_mathematical(STATE_0, branch=(2, 0))

    def test_bitstring_decoding_validation(self) -> None:
        """decode_teleportation_bitstring validates input types and formats."""
        with pytest.raises(TypeError, match="str"):
            decode_teleportation_bitstring(123)  # type: ignore

        with pytest.raises(ValueError, match="Cannot parse"):
            decode_teleportation_bitstring("")

        with pytest.raises(ValueError, match="Bitstring must have 2 or 3 bits"):
            decode_teleportation_bitstring("1111")

        with pytest.raises(ValueError):
            decode_teleportation_bitstring("abc")

    def test_simulation_parameter_validation(self) -> None:
        """simulate_teleportation_circuit enforces valid parameters."""
        with pytest.raises(ValueError, match="strictly positive"):
            simulate_teleportation_circuit(STATE_0, shots=0)

        with pytest.raises(TypeError, match="integer"):
            simulate_teleportation_circuit(STATE_0, shots="100")  # type: ignore

        with pytest.raises(ValueError, match="non-negative"):
            simulate_teleportation_circuit(STATE_0, seed=-5)

        with pytest.raises(ValueError, match="Unsupported Bob measurement basis"):
            create_teleportation_circuit(STATE_0, measure_bob=True, bob_basis="invalid")

    def test_no_m7_plus_functionality_in_quantum_package(self) -> None:
        """M6 must NOT implement QDS, noise, attacks, threshold engines, or dashboards."""
        import src.quantum as q_pkg

        assert not hasattr(q_pkg, "qds_sign"), "QDS signing must not exist in M6."
        assert not hasattr(q_pkg, "qds_verify"), "QDS verification must not exist in M6."
        assert not hasattr(q_pkg, "apply_channel_noise"), "Noise must not exist in M6."
        assert not hasattr(q_pkg, "detect_forgery"), "Attack detection must not exist in M6."
        assert not hasattr(q_pkg, "statistical_threshold"), "Thresholds must not exist in M6."
        assert not hasattr(q_pkg, "dashboard"), "Dashboard must not exist in M6."
        assert not hasattr(q_pkg, "blockchain"), "Blockchain must not exist in M6."
        assert not hasattr(q_pkg, "qif"), "QIF must not exist in M6."

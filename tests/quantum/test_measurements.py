"""Tests for Qiskit Aer single-qubit measurement and empirical probabilities (Milestone M1)."""

import numpy as np
import pytest
from qiskit import QuantumCircuit

from src.quantum.states import (
    STATE_0,
    STATE_1,
    STATE_PLUS,
    STATE_MINUS,
    STATE_PLUS_I,
    STATE_MINUS_I,
    create_qubit_circuit,
    QubitState,
)
from src.quantum.measurements import (
    measure_qubit,
    calculate_empirical_probabilities,
    measure_state,
)


class TestSingleQubitMeasurements:
    """Tests for single-qubit measurement execution using Qiskit Aer."""

    def test_measure_state_0_deterministic(self) -> None:
        """Measuring |0> must yield outcome '0' for all shots."""
        shots = 1000
        counts, probs = measure_state(STATE_0, shots=shots, seed_simulator=42)

        assert counts["0"] == shots
        assert counts["1"] == 0
        assert probs["0"] == 1.0
        assert probs["1"] == 0.0
        assert np.isclose(probs["0"] + probs["1"], 1.0)

    def test_measure_state_1_deterministic(self) -> None:
        """Measuring |1> must yield outcome '1' for all shots."""
        shots = 1000
        counts, probs = measure_state(STATE_1, shots=shots, seed_simulator=42)

        assert counts["0"] == 0
        assert counts["1"] == shots
        assert probs["0"] == 0.0
        assert probs["1"] == 1.0
        assert np.isclose(probs["0"] + probs["1"], 1.0)

    def test_measure_state_plus_probabilistic(self) -> None:
        """Measuring |+> must yield approximately 50/50 outcomes within statistical tolerance.

        For N=10000 shots and p=0.5, standard error is sqrt(p*(1-p)/N) = 0.005.
        A tolerance of 0.035 corresponds to > 6.5 standard deviations (extremely safe against flakiness).
        The test explicitly verifies that the outcome is NOT deterministic.
        """
        shots = 10000
        counts, probs = measure_state(STATE_PLUS, shots=shots, seed_simulator=123)

        assert counts["0"] > 0
        assert counts["1"] > 0
        assert counts["0"] + counts["1"] == shots

        # Confirm non-deterministic, approximately 50/50 distribution
        assert not (counts["0"] == 0 or counts["1"] == 0)
        assert abs(probs["0"] - 0.5) < 0.035, f"P(0)={probs['0']} deviated beyond tolerance from 0.5"
        assert abs(probs["1"] - 0.5) < 0.035, f"P(1)={probs['1']} deviated beyond tolerance from 0.5"
        assert np.isclose(probs["0"] + probs["1"], 1.0)

    def test_measure_state_minus_probabilistic(self) -> None:
        """Measuring |-> must yield approximately 50/50 outcomes within statistical tolerance."""
        shots = 10000
        counts, probs = measure_state(STATE_MINUS, shots=shots, seed_simulator=456)

        assert counts["0"] > 0
        assert counts["1"] > 0
        assert counts["0"] + counts["1"] == shots

        assert abs(probs["0"] - 0.5) < 0.035, f"P(0)={probs['0']} deviated beyond tolerance from 0.5"
        assert abs(probs["1"] - 0.5) < 0.035, f"P(1)={probs['1']} deviated beyond tolerance from 0.5"
        assert np.isclose(probs["0"] + probs["1"], 1.0)

    def test_measure_state_plus_i_probabilistic(self) -> None:
        """Measuring |+i> in computational basis must yield ~50/50 outcomes."""
        shots = 10000
        counts, probs = measure_state(STATE_PLUS_I, shots=shots, seed_simulator=789)

        assert counts["0"] > 0
        assert counts["1"] > 0
        assert counts["0"] + counts["1"] == shots
        assert abs(probs["0"] - 0.5) < 0.035
        assert abs(probs["1"] - 0.5) < 0.035
        assert np.isclose(probs["0"] + probs["1"], 1.0)

    def test_measure_state_minus_i_probabilistic(self) -> None:
        """Measuring |-i> in computational basis must yield ~50/50 outcomes."""
        shots = 10000
        counts, probs = measure_state(STATE_MINUS_I, shots=shots, seed_simulator=321)

        assert counts["0"] > 0
        assert counts["1"] > 0
        assert counts["0"] + counts["1"] == shots
        assert abs(probs["0"] - 0.5) < 0.035
        assert abs(probs["1"] - 0.5) < 0.035
        assert np.isclose(probs["0"] + probs["1"], 1.0)

    def test_measure_state_with_qubit_state_instance(self) -> None:
        """measure_state should accept QubitState instances directly."""
        qs = QubitState(STATE_0)
        counts, probs = measure_state(qs, shots=500, seed_simulator=42)
        assert counts["0"] == 500
        assert counts["1"] == 0
        assert probs["0"] == 1.0
        assert probs["1"] == 0.0

    def test_configurable_shots(self) -> None:
        """Configurable shots should dictate total measured counts."""
        for requested_shots in [100, 500, 2048]:
            counts, probs = measure_state(STATE_PLUS, shots=requested_shots)
            assert counts["0"] + counts["1"] == requested_shots
            assert np.isclose(probs["0"] + probs["1"], 1.0)

    def test_reproducibility_with_seed(self) -> None:
        """Measurements using the same seed must produce identical counts."""
        circuit = create_qubit_circuit(STATE_PLUS)
        counts1 = measure_qubit(circuit, shots=1000, seed_simulator=999)
        counts2 = measure_qubit(circuit, shots=1000, seed_simulator=999)
        assert counts1 == counts2

    def test_circuit_with_pre_existing_measurement(self) -> None:
        """measure_qubit should correctly measure circuits that already have classical bits."""
        qc = QuantumCircuit(1, 1)
        qc.h(0)
        qc.measure(0, 0)

        counts = measure_qubit(qc, shots=500, seed_simulator=7)
        assert counts["0"] + counts["1"] == 500


class TestEmpiricalProbabilities:
    """Tests for calculation and validation of empirical probabilities."""

    def test_probability_calculation_balanced(self) -> None:
        counts = {"0": 500, "1": 500}
        probs = calculate_empirical_probabilities(counts)
        assert probs["0"] == 0.5
        assert probs["1"] == 0.5

    def test_probability_calculation_missing_outcome(self) -> None:
        """Missing key (e.g. from a deterministic measurement) should be treated as 0."""
        counts = {"0": 1000}
        probs = calculate_empirical_probabilities(counts, total_shots=1000)
        assert probs["0"] == 1.0
        assert probs["1"] == 0.0

    def test_empirical_probabilities_sum_to_one(self) -> None:
        counts = {"0": 341, "1": 659}
        probs = calculate_empirical_probabilities(counts)
        assert np.isclose(probs["0"] + probs["1"], 1.0)
        assert np.isclose(probs["0"], 0.341)
        assert np.isclose(probs["1"], 0.659)


    def test_probability_calculation_with_integer_keys(self) -> None:
        """Counts keyed by integers {0: c0, 1: c1} must be supported."""
        counts = {0: 400, 1: 600}
        probs = calculate_empirical_probabilities(counts)
        assert np.isclose(probs["0"], 0.4)
        assert np.isclose(probs["1"], 0.6)
        assert np.isclose(probs["0"] + probs["1"], 1.0)


class TestMeasurementEdgeCases:
    """Tests for edge cases and input validation in measurement routines."""

    def test_invalid_shots_raises(self) -> None:
        """Zero or negative shots must raise ValueError; non-integers raise TypeError."""
        circuit = create_qubit_circuit(STATE_0)

        with pytest.raises(ValueError, match="strictly positive integer"):
            measure_qubit(circuit, shots=0)

        with pytest.raises(ValueError, match="strictly positive integer"):
            measure_qubit(circuit, shots=-100)

        with pytest.raises(TypeError, match="Shots must be an integer"):
            measure_qubit(circuit, shots=100.5)  # type: ignore

        with pytest.raises(TypeError, match="Shots must be an integer"):
            measure_qubit(circuit, shots=True)  # type: ignore

    def test_invalid_seed_raises(self) -> None:
        """Negative seed or non-integer seed must raise ValueError/TypeError."""
        circuit = create_qubit_circuit(STATE_0)

        with pytest.raises(ValueError, match="non-negative integer"):
            measure_qubit(circuit, shots=100, seed_simulator=-1)

        with pytest.raises(TypeError, match="Seed must be an integer"):
            measure_qubit(circuit, shots=100, seed_simulator="seed")  # type: ignore

        with pytest.raises(TypeError, match="Seed must be an integer"):
            measure_qubit(circuit, shots=100, seed_simulator=True)  # type: ignore

    def test_invalid_circuit_type_raises(self) -> None:
        """Passing non-QuantumCircuit must raise TypeError."""
        with pytest.raises(TypeError, match="Expected a Qiskit QuantumCircuit"):
            measure_qubit("not_a_circuit", shots=100)  # type: ignore

    def test_circuit_with_no_qubits_raises(self) -> None:
        """Passing empty QuantumCircuit(0) must raise ValueError."""
        empty_qc = QuantumCircuit(0)
        with pytest.raises(ValueError, match="at least 1 qubit"):
            measure_qubit(empty_qc, shots=100)

    def test_invalid_counts_raises(self) -> None:
        """Negative counts, non-integer counts, or total shots <= 0 must raise ValueError/TypeError."""
        with pytest.raises(ValueError, match="cannot be negative"):
            calculate_empirical_probabilities({"0": -5, "1": 10})

        with pytest.raises(ValueError, match="positive number"):
            calculate_empirical_probabilities({"0": 0, "1": 0})

        with pytest.raises(TypeError, match="Counts values must be integers"):
            calculate_empirical_probabilities({"0": "100", "1": 200})  # type: ignore

        with pytest.raises(TypeError, match="Counts values must be integers"):
            calculate_empirical_probabilities({"0": True, "1": 200})  # type: ignore

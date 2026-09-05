import numpy as np
import pytest
from qiskit import QuantumCircuit
from src.quantum.measurement import measure_circuit, empirical_probabilities

def test_measure_zero_state():
    qc = QuantumCircuit(1, 1)
    qc.measure(0, 0)
    counts = measure_circuit(qc, shots=1000)
    assert counts.get('0', 0) == 1000
    assert counts.get('1', 0) == 0

def test_measure_one_state():
    qc = QuantumCircuit(1, 1)
    qc.x(0)
    qc.measure(0, 0)
    counts = measure_circuit(qc, shots=1000)
    assert counts.get('1', 0) == 1000
    assert counts.get('0', 0) == 0

def test_measure_plus_state():
    qc = QuantumCircuit(1, 1)
    qc.h(0)
    qc.measure(0, 0)
    counts = measure_circuit(qc, shots=10000)
    probs = empirical_probabilities(counts)
    assert np.isclose(probs.get('0', 0.0), 0.5, atol=0.05)
    assert np.isclose(probs.get('1', 0.0), 0.5, atol=0.05)

def test_measure_minus_state():
    qc = QuantumCircuit(1, 1)
    qc.x(0)
    qc.h(0)
    qc.measure(0, 0)
    counts = measure_circuit(qc, shots=10000)
    probs = empirical_probabilities(counts)
    assert np.isclose(probs.get('0', 0.0), 0.5, atol=0.05)
    assert np.isclose(probs.get('1', 0.0), 0.5, atol=0.05)

def test_empirical_probabilities_sum_to_one():
    counts = {'0': 300, '1': 700}
    probs = empirical_probabilities(counts)
    assert np.isclose(sum(probs.values()), 1.0)
    
def test_empirical_probabilities_no_shots():
    with pytest.raises(ValueError, match="No measurement shots"):
        empirical_probabilities({'0': 0, '1': 0})

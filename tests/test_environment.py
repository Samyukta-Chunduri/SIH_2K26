import sys
import numpy as np
import qiskit
import qiskit_aer

def test_environment():
    print(f"Python version: {sys.version}")
    print(f"NumPy version: {np.__version__}")
    print(f"Qiskit version: {qiskit.__version__}")
    print(f"Qiskit Aer version: {qiskit_aer.__version__}")
    
    # Create a small quantum circuit
    qc = qiskit.QuantumCircuit(2, 2)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure([0, 1], [0, 1])
    
    # Execute on Aer simulator
    simulator = qiskit_aer.AerSimulator()
    job = simulator.run(qc, shots=100)
    result = job.result()
    counts = result.get_counts()
    
    print("Measurement results:", counts)
    assert len(counts) > 0, "No results obtained!"
    
    print("Environment test passed!")

if __name__ == "__main__":
    test_environment()

from qiskit import QuantumCircuit
from src.quantum.measurement import measure_circuit

def manual_sanity_check():
    shots = 10000
    
    # |0>
    qc0 = QuantumCircuit(1, 1)
    qc0.measure(0, 0)
    counts0 = measure_circuit(qc0, shots)
    print(f"|0> state counts: {counts0}")
    
    # |1>
    qc1 = QuantumCircuit(1, 1)
    qc1.x(0)
    qc1.measure(0, 0)
    counts1 = measure_circuit(qc1, shots)
    print(f"|1> state counts: {counts1}")
    
    # |+>
    qcp = QuantumCircuit(1, 1)
    qcp.h(0)
    qcp.measure(0, 0)
    countsp = measure_circuit(qcp, shots)
    print(f"|+> state counts: {countsp}")
    
    # |->
    qcm = QuantumCircuit(1, 1)
    qcm.x(0)
    qcm.h(0)
    qcm.measure(0, 0)
    countsm = measure_circuit(qcm, shots)
    print(f"|-> state counts: {countsm}")

if __name__ == "__main__":
    manual_sanity_check()

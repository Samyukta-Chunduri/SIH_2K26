from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

def measure_circuit(circuit: QuantumCircuit, shots: int = 1000) -> dict[str, int]:
    """
    Executes a prepared quantum circuit using Qiskit AerSimulator and returns the measurement counts.
    
    Args:
        circuit: A QuantumCircuit that has already been prepared with operations and measurements.
        shots: The number of times to execute the circuit.
        
    Returns:
        A dictionary mapping measurement outcomes (e.g., '0', '1') to counts.
    """
    simulator = AerSimulator()
    result = simulator.run(circuit, shots=shots).result()
    counts = result.get_counts(circuit)
    return counts

def empirical_probabilities(counts: dict[str, int]) -> dict[str, float]:
    """
    Calculates empirical probabilities from measurement counts.
    
    Args:
        counts: A dictionary of measurement outcomes and their counts.
        
    Returns:
        A dictionary mapping outcomes to their empirical probabilities.
        
    Raises:
        ValueError: If there are no shots (counts sum to 0).
    """
    total_shots = sum(counts.values())
    if total_shots == 0:
        raise ValueError("No measurement shots to calculate probabilities from.")
    return {state: count / total_shots for state, count in counts.items()}

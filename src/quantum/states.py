import numpy as np

def zero_state() -> np.ndarray:
    """Returns the |0> computational basis state vector."""
    return np.array([1.0, 0.0], dtype=np.complex128)

def one_state() -> np.ndarray:
    """Returns the |1> computational basis state vector."""
    return np.array([0.0, 1.0], dtype=np.complex128)

def plus_state() -> np.ndarray:
    """Returns the |+> superposition state vector."""
    return np.array([1.0 / np.sqrt(2), 1.0 / np.sqrt(2)], dtype=np.complex128)

def minus_state() -> np.ndarray:
    """Returns the |-> superposition state vector."""
    return np.array([1.0 / np.sqrt(2), -1.0 / np.sqrt(2)], dtype=np.complex128)

def is_normalized(state: np.ndarray, tolerance: float = 1e-9) -> bool:
    """
    Checks if a quantum state vector is normalized within a given tolerance.
    """
    try:
        norm_squared = np.sum(np.abs(state)**2)
        return bool(np.isclose(norm_squared, 1.0, atol=tolerance))
    except (TypeError, ValueError):
        return False

def computational_probabilities(state: np.ndarray) -> tuple[float, float]:
    """
    Calculates the computational-basis measurement probabilities P(0) and P(1)
    for a given single-qubit state vector.
    
    Raises:
        ValueError: If the state does not have exactly two amplitudes or is not normalized.
        TypeError: If the state amplitudes are not numeric.
    """
    state = np.asarray(state)
    if state.shape != (2,):
        raise ValueError("State must have exactly two amplitudes.")
    
    if not np.issubdtype(state.dtype, np.number):
        raise TypeError("State amplitudes must be numeric.")
    
    if not is_normalized(state):
        raise ValueError("State is not normalized.")
    
    p0 = float(np.abs(state[0])**2)
    p1 = float(np.abs(state[1])**2)
    
    return p0, p1

import numpy as np
import pytest
from src.quantum.states import (
    zero_state, one_state, plus_state, minus_state,
    is_normalized, computational_probabilities
)

def test_zero_state():
    state = zero_state()
    np.testing.assert_allclose(state, [1, 0])
    assert is_normalized(state)

def test_one_state():
    state = one_state()
    np.testing.assert_allclose(state, [0, 1])
    assert is_normalized(state)

def test_plus_state():
    state = plus_state()
    np.testing.assert_allclose(state, [1/np.sqrt(2), 1/np.sqrt(2)])
    assert is_normalized(state)

def test_minus_state():
    state = minus_state()
    np.testing.assert_allclose(state, [1/np.sqrt(2), -1/np.sqrt(2)])
    assert is_normalized(state)

def test_computational_probabilities_sum_to_one():
    for state in [zero_state(), one_state(), plus_state(), minus_state()]:
        p0, p1 = computational_probabilities(state)
        assert np.isclose(p0 + p1, 1.0)

def test_computational_probabilities_values():
    assert np.allclose(computational_probabilities(zero_state()), (1.0, 0.0))
    assert np.allclose(computational_probabilities(one_state()), (0.0, 1.0))
    assert np.allclose(computational_probabilities(plus_state()), (0.5, 0.5))
    assert np.allclose(computational_probabilities(minus_state()), (0.5, 0.5))

def test_invalid_state_detection():
    # Not normalized
    with pytest.raises(ValueError, match="State is not normalized"):
        computational_probabilities(np.array([1.0, 1.0]))
    
    # Not exactly two amplitudes
    with pytest.raises(ValueError, match="exactly two amplitudes"):
        computational_probabilities(np.array([1.0, 0.0, 0.0]))
        
    # Non-numeric
    with pytest.raises(TypeError, match="numeric"):
        computational_probabilities(np.array(["a", "b"]))

"""Q-SHIELD — Teleportation Verification Module (Milestone M7).

Provides mathematical verification for single-qubit quantum teleportation:
validates whether Bob's recovered quantum state matches Alice's intended
input state via pure-state overlap fidelity, numerical correctness tolerance,
and basis-dependent measurement distribution comparison.

Mathematical Model:
    1. Quantum State Overlap Fidelity:
       F(psi_in, psi_out) = |<psi_in | psi_out>|^2
                          = |vdot(psi_in, psi_out)|^2
       Properties:
         - F in [0.0, 1.0]
         - F = 1.0 if and only if psi_out = e^(i theta) psi_in (identical up to global phase)
         - F = 0.0 if and only if <psi_in | psi_out> = 0 (orthogonal states)
         - Strictly invariant under global phase shifts: |e^(i theta)|^2 = 1

    2. Numerical Correctness Criterion:
       verified <=> F >= (1.0 - tolerance)
       Where tolerance in [0.0, 1.0) represents allowable numerical floating-point error
       in double-precision statevector simulation (default: 1e-6).

    3. Measurement Distribution Comparison (Supporting Evidence):
       Given measurement basis B in {Z, X, Y}:
         P_in(x) = <psi_in | P_x | psi_in>
         P_out(x) = <psi_out | P_x | psi_out>
         Total Variation Distance: TVD = (1/2) sum_{x in B} |P_in(x) - P_out(x)|
         Max Difference: Delta_max = max_{x in B} |P_in(x) - P_out(x)|

Scientific Boundaries:
    - M7 verifies mathematical correctness of ideal quantum teleportation simulation.
    - Numerical tolerance is a floating-point precision bound, NOT a statistical security threshold.
    - Matching in a single measurement basis does NOT establish quantum state equivalence
      (e.g., |+> and |-> have identical 50/50 probabilities in the Z basis despite being orthogonal).
    - M7 does NOT compute a security score and does NOT implement threat detection,
      signatures, channel noise, or attacks (reserved for future milestones).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import math
from typing import Any
import numpy as np

from .measurements import projective_probabilities
from .states import (
    QubitState,
    get_standard_state,
    validate_state_vector,
)
from .teleportation import (
    TeleportationResult,
    calculate_teleportation_fidelity,
)

# Default numerical correctness tolerance for ideal statevector simulation
# Double precision float64 roundoff is typically ~1e-15; 1e-6 provides robust
# numerical headroom while strictly rejecting any non-trivial state divergence.
DEFAULT_VERIFICATION_TOLERANCE: float = 1e-6


def validate_verification_tolerance(tolerance: Any) -> float:
    """Validate that the verification tolerance is a valid, non-negative floating-point number.

    Args:
        tolerance: Numerical tolerance value. Must be a float or int, non-negative,
                   finite, and strictly less than 1.0.

    Returns:
        Validated tolerance as a float.

    Raises:
        TypeError: If tolerance is not numeric or is a boolean.
        ValueError: If tolerance is negative, NaN, infinite, or >= 1.0.
    """
    if isinstance(tolerance, bool) or not isinstance(tolerance, (int, float)):
        raise TypeError(
            f"Verification tolerance must be a numeric float or int, got {type(tolerance).__name__}."
        )

    tol = float(tolerance)

    if not math.isfinite(tol):
        raise ValueError(f"Verification tolerance must be finite, got {tol}.")

    if tol < 0.0:
        raise ValueError(
            f"Verification tolerance must be non-negative, got {tol}."
        )

    if tol >= 1.0:
        raise ValueError(
            f"Verification tolerance must be strictly less than 1.0, got {tol}."
        )

    return tol


@dataclass(frozen=True)
class TeleportationVerificationResult:
    """Immutable result of a teleportation verification assessment.

    Attributes:
        verified: True if fidelity >= fidelity_threshold, False otherwise.
        fidelity: Quantum state overlap fidelity F in [0.0, 1.0].
        tolerance: Configured numerical correctness tolerance epsilon in [0.0, 1.0).
        fidelity_threshold: Required fidelity threshold (1.0 - tolerance).
        input_state: Alice's normalized input state vector (2,).
        output_state: Bob's recovered normalized output state vector (2,).
    """

    verified: bool
    fidelity: float
    tolerance: float
    fidelity_threshold: float
    input_state: np.ndarray
    output_state: np.ndarray

    def __post_init__(self) -> None:
        """Enforce strict invariant validation on dataclass instantiation."""
        if not isinstance(self.verified, bool):
            raise TypeError(f"verified must be a bool, got {type(self.verified).__name__}.")

        if not isinstance(self.fidelity, (float, int)) or isinstance(self.fidelity, bool):
            raise TypeError(f"fidelity must be a float, got {type(self.fidelity).__name__}.")

        if not (0.0 <= self.fidelity <= 1.0 + 1e-7):
            raise ValueError(f"fidelity must be in [0.0, 1.0], got {self.fidelity}.")

        if not (0.0 <= self.tolerance < 1.0):
            raise ValueError(f"tolerance must be in [0.0, 1.0), got {self.tolerance}.")

        if not (0.0 <= self.fidelity_threshold <= 1.0 + 1e-7):
            raise ValueError(f"fidelity_threshold must be in [0.0, 1.0], got {self.fidelity_threshold}.")

        if self.input_state.shape != (2,):
            raise ValueError(f"input_state must have shape (2,), got {self.input_state.shape}.")

        if self.output_state.shape != (2,):
            raise ValueError(f"output_state must have shape (2,), got {self.output_state.shape}.")


@dataclass(frozen=True)
class MeasurementDistributionComparison:
    """Immutable result of comparing measurement probability distributions across a basis.

    Attributes:
        basis: Measurement basis used ('Z', 'X', or 'Y').
        input_probabilities: Theoretical Born probabilities for the input state.
        output_probabilities: Theoretical Born probabilities for the output state.
        total_variation_distance: TVD = 0.5 * sum |P_in(x) - P_out(x)| in [0.0, 1.0].
        max_probability_difference: max |P_in(x) - P_out(x)| in [0.0, 1.0].
        matches_within_tolerance: True if total_variation_distance <= tolerance.
    """

    basis: str
    input_probabilities: dict[str, float]
    output_probabilities: dict[str, float]
    total_variation_distance: float
    max_probability_difference: float
    matches_within_tolerance: bool

    def __post_init__(self) -> None:
        """Validate invariant constraints."""
        if self.basis not in ("Z", "X", "Y"):
            raise ValueError(f"basis must be 'Z', 'X', or 'Y', got {self.basis}.")
        if not (0.0 <= self.total_variation_distance <= 1.0 + 1e-7):
            raise ValueError(
                f"total_variation_distance must be in [0.0, 1.0], got {self.total_variation_distance}."
            )
        if not (0.0 <= self.max_probability_difference <= 1.0 + 1e-7):
            raise ValueError(
                f"max_probability_difference must be in [0.0, 1.0], got {self.max_probability_difference}."
            )


def _parse_state_vector(state: Any, arg_name: str) -> np.ndarray:
    """Parse and validate a single-qubit state input (label, QubitState, or array-like).

    Args:
        state: State identifier (str), QubitState, or array-like vector.
        arg_name: Argument name for clear error messaging.

    Returns:
        Validated 2-element complex numpy array.

    Raises:
        TypeError: If state is None, scalar, boolean, or has incompatible type.
        ValueError: If state is malformed, non-normalized, or unknown label.
    """
    if state is None:
        raise TypeError(f"{arg_name} cannot be None.")
    if isinstance(state, (int, float, bool)):
        raise TypeError(
            f"{arg_name} must be a state vector, standard state name, or QubitState; "
            f"got scalar {type(state).__name__}."
        )
    if isinstance(state, str):
        return get_standard_state(state)
    if isinstance(state, QubitState):
        return state.vector.copy()
    return validate_state_vector(state)


def verify_teleportation(
    input_state: Any,
    output_state: Any,
    tolerance: float = DEFAULT_VERIFICATION_TOLERANCE,
) -> TeleportationVerificationResult:
    """Verify whether Bob's recovered state matches Alice's input state.

    Mathematical Model:
        1. Parse and validate input_state and output_state as normalized pure states.
        2. Calculate fidelity: F = |<input_state | output_state>|^2 via np.vdot.
        3. Define threshold: T = 1.0 - tolerance.
        4. Evaluation: verified = True if F >= T else False.

    Args:
        input_state: Alice's intended input state (string label, QubitState, or array-like).
        output_state: Bob's recovered state (string label, QubitState, or array-like).
        tolerance: Numerical correctness tolerance epsilon in [0.0, 1.0). Default: 1e-6.

    Returns:
        TeleportationVerificationResult containing fidelity, tolerance, threshold, and status.

    Raises:
        TypeError: If tolerance or states have invalid types.
        ValueError: If states are malformed, non-finite, or non-normalized, or if tolerance is invalid.
    """
    tol = validate_verification_tolerance(tolerance)

    vec_in = _parse_state_vector(input_state, "input_state")
    vec_out = _parse_state_vector(output_state, "output_state")

    # Calculate fidelity using conjugate inner product: F = |<in|out>|^2
    fidelity = calculate_teleportation_fidelity(vec_in, vec_out)

    threshold = float(np.clip(1.0 - tol, 0.0, 1.0))
    # Account for machine-precision floating-point roundoff at the threshold boundary
    verified = bool(fidelity >= threshold or math.isclose(fidelity, threshold, abs_tol=1e-14))

    return TeleportationVerificationResult(
        verified=verified,
        fidelity=fidelity,
        tolerance=tol,
        fidelity_threshold=threshold,
        input_state=vec_in.copy(),
        output_state=vec_out.copy(),
    )


def verify_teleportation_result(
    result: TeleportationResult,
    tolerance: float = DEFAULT_VERIFICATION_TOLERANCE,
) -> TeleportationVerificationResult:
    """Verify a completed M6 TeleportationResult instance.

    Convenience wrapper extracting Alice's input state and Bob's output state
    from an M6 TeleportationResult dataclass.

    Args:
        result: TeleportationResult instance from M6 teleportation simulation.
        tolerance: Numerical correctness tolerance epsilon in [0.0, 1.0).

    Returns:
        TeleportationVerificationResult.

    Raises:
        TypeError: If result is not an instance of TeleportationResult.
    """
    if not isinstance(result, TeleportationResult):
        raise TypeError(
            f"Expected TeleportationResult instance, got {type(result).__name__}."
        )

    return verify_teleportation(
        input_state=result.input_state,
        output_state=result.output_state,
        tolerance=tolerance,
    )


def compare_measurement_distributions(
    input_state: Any,
    output_state: Any,
    basis: str = "Z",
    tolerance: float = DEFAULT_VERIFICATION_TOLERANCE,
) -> MeasurementDistributionComparison:
    """Compare projective measurement probability distributions between two single-qubit states.

    Calculates the exact Born-rule outcome probabilities for input_state and output_state
    in the specified basis (Z, X, or Y) and computes the Total Variation Distance (TVD)
    and maximum probability difference.

    Important Scientific Note:
        Measurement distribution comparison provides basis-dependent supporting evidence.
        Agreement in a single basis does NOT prove quantum state equivalence. For example,
        |+> and |-> yield identical outcome probabilities (0.5, 0.5) in the Z basis,
        yet they are mutually orthogonal (fidelity = 0.0).

    Args:
        input_state: First single-qubit state (name, QubitState, or array-like).
        output_state: Second single-qubit state (name, QubitState, or array-like).
        basis: Measurement basis ('Z', 'X', or 'Y'). Default is 'Z'.
        tolerance: Maximum acceptable TVD to qualify as matching within tolerance.

    Returns:
        MeasurementDistributionComparison containing probabilities, TVD, max difference,
        and match status.

    Raises:
        ValueError: If basis is unrecognized or states/tolerance are invalid.
        TypeError: If inputs have invalid types.
    """
    tol = validate_verification_tolerance(tolerance)

    # Validate basis
    norm_basis = basis.strip().upper()
    if norm_basis not in ("Z", "X", "Y"):
        raise ValueError(
            f"Measurement basis must be 'Z', 'X', or 'Y', got '{basis}'."
        )

    # Validate state vectors
    vec_in = _parse_state_vector(input_state, "input_state")
    vec_out = _parse_state_vector(output_state, "output_state")

    # Calculate exact Born probabilities
    probs_in = projective_probabilities(vec_in, basis=norm_basis)
    probs_out = projective_probabilities(vec_out, basis=norm_basis)

    # Compute Total Variation Distance: TVD = 0.5 * sum |P_in(x) - P_out(x)|
    labels = list(probs_in.keys())
    diffs = [abs(probs_in[k] - probs_out[k]) for k in labels]
    tvd = float(0.5 * sum(diffs))
    max_diff = float(max(diffs))

    matches = bool(tvd <= tol)

    return MeasurementDistributionComparison(
        basis=norm_basis,
        input_probabilities=probs_in,
        output_probabilities=probs_out,
        total_variation_distance=float(np.clip(tvd, 0.0, 1.0)),
        max_probability_difference=float(np.clip(max_diff, 0.0, 1.0)),
        matches_within_tolerance=matches,
    )

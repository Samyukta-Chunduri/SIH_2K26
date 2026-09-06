"""Q-SHIELD — Quantum Evidence & Telemetry API Routes (Milestone M19-B)."""

from __future__ import annotations

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status

from src.api.routes.security import get_service
from src.api.schemas import QuantumEvidenceResponse
from src.api.service import QShieldService

router = APIRouter(prefix="/api/quantum", tags=["Quantum Telemetry & Evidence"])


@router.get("/evidence/{event_id}", response_model=QuantumEvidenceResponse)
def get_quantum_evidence(
    event_id: str,
    service: Annotated[QShieldService, Depends(get_service)],
) -> QuantumEvidenceResponse:
    """Retrieve dedicated quantum channel telemetry and Bell correlation evidence for an event."""
    evidence = service.get_quantum_evidence(event_id)
    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quantum evidence for event '{event_id}' not found.",
        )
    return evidence

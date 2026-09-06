"""Q-SHIELD — Threat Evidence Inspection API Routes (Milestone M19-B)."""

from __future__ import annotations

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status

from src.api.routes.security import get_service
from src.api.schemas import ThreatEvidenceResponse
from src.api.service import QShieldService

router = APIRouter(prefix="/api/threats", tags=["Threat Evidence"])


@router.get("/{event_id}", response_model=ThreatEvidenceResponse)
def get_threat_evidence(
    event_id: str,
    service: Annotated[QShieldService, Depends(get_service)],
) -> ThreatEvidenceResponse:
    """Retrieve consolidated threat evidence across identity, authorization, and channel."""
    evidence = service.get_threat_evidence(event_id)
    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Threat evidence for event '{event_id}' not found.",
        )
    return evidence

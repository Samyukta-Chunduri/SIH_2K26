"""Q-SHIELD — Evidence Fusion & M12 Decision API Routes (Milestone M19-B)."""

from __future__ import annotations

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status

from src.api.routes.security import get_service
from src.api.schemas import FusionEvidenceResponse
from src.api.service import QShieldService

router = APIRouter(prefix="/api/fusion", tags=["Evidence Fusion & Decision Explainability"])


@router.get("/{event_id}", response_model=FusionEvidenceResponse)
def get_fusion_evidence(
    event_id: str,
    service: Annotated[QShieldService, Depends(get_service)],
) -> FusionEvidenceResponse:
    """Retrieve M16 fusion synthesis breakdown and M12 decision explainability for an event."""
    evidence = service.get_fusion_evidence(event_id)
    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fusion evidence for event '{event_id}' not found.",
        )
    return evidence

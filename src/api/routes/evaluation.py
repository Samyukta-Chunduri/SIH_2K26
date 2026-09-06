"""Q-SHIELD — M17 Security Evaluation API Routes (Milestone M19-B)."""

from __future__ import annotations

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.api.routes.security import get_service
from src.api.schemas import EvaluationRunDetailResponse, EvaluationRunSummaryResponse
from src.api.service import QShieldService

router = APIRouter(prefix="/api/evaluation", tags=["Security Evaluation (M17)"])


@router.get("/runs", response_model=list[EvaluationRunSummaryResponse])
def list_evaluation_runs(
    service: Annotated[QShieldService, Depends(get_service)],
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[EvaluationRunSummaryResponse]:
    """List historical M17 security evaluation suite runs."""
    return service.list_evaluation_runs(limit=limit, offset=offset)


@router.get("/runs/{run_id}", response_model=EvaluationRunDetailResponse)
def get_evaluation_run_detail(
    run_id: str,
    service: Annotated[QShieldService, Depends(get_service)],
) -> EvaluationRunDetailResponse:
    """Retrieve complete scenario-level results and confusion matrix for an evaluation run."""
    detail = service.get_evaluation_run(run_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation run '{run_id}' not found.",
        )
    return detail


@router.post("/run", response_model=EvaluationRunDetailResponse, status_code=status.HTTP_201_CREATED)
def trigger_evaluation_run(
    service: Annotated[QShieldService, Depends(get_service)],
    session_id: str | None = None,
) -> EvaluationRunDetailResponse:
    """Execute the standardized M17 baseline security evaluation suite and persist results."""
    try:
        return service.trigger_evaluation_run(session_id=session_id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute security evaluation suite.",
        ) from exc

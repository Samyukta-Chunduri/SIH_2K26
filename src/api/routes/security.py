"""Q-SHIELD — Security Verification & Events API Routes (Milestone M19-B)."""

from __future__ import annotations

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.api.schemas import (
    ScenarioTemplateResponse,
    SecurityEventDetailResponse,
    SecurityEventSummaryResponse,
    VerifyScenarioRequest,
)
from src.api.service import QShieldService


router = APIRouter(prefix="/api", tags=["Security Verification & Events"])


def get_service() -> QShieldService:
    """Dependency injector for QShieldService (overridden in application startup/tests)."""
    raise NotImplementedError("Service dependency must be overridden by app dependency_overrides.")


@router.get("/scenarios", response_model=list[ScenarioTemplateResponse])
def get_scenario_templates(
    service: Annotated[QShieldService, Depends(get_service)],
) -> list[ScenarioTemplateResponse]:
    """Retrieve available security scenario templates for client execution."""
    return service.list_scenario_templates()


@router.post("/security/verify", response_model=SecurityEventDetailResponse, status_code=status.HTTP_201_CREATED)
def verify_security_scenario(
    request: VerifyScenarioRequest,
    service: Annotated[QShieldService, Depends(get_service)],
) -> SecurityEventDetailResponse:
    """Execute a controlled scenario through the authoritative Q-SHIELD pipeline."""
    try:
        return service.verify_scenario(request)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during security scenario evaluation.",
        ) from exc


@router.get("/security/events", response_model=list[SecurityEventSummaryResponse])
def list_security_events(
    service: Annotated[QShieldService, Depends(get_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    verdict: Annotated[str | None, Query()] = None,
    session_id: Annotated[str | None, Query()] = None,
) -> list[SecurityEventSummaryResponse]:
    """Query paginated security verification history."""
    return service.list_events(limit=limit, offset=offset, verdict=verdict, session_id=session_id)


@router.get("/security/events/{event_id}", response_model=SecurityEventDetailResponse)
def get_security_event_detail(
    event_id: str,
    service: Annotated[QShieldService, Depends(get_service)],
) -> SecurityEventDetailResponse:
    """Retrieve complete decision details and evidence records for an event."""
    detail = service.get_event(event_id)
    if not detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Event '{event_id}' not found.")
    return detail

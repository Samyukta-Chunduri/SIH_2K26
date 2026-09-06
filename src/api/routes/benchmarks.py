"""Q-SHIELD — M18 Performance Benchmarks API Routes (Milestone M19-B)."""

from __future__ import annotations

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.api.routes.security import get_service
from src.api.schemas import BenchmarkRunDetailResponse, BenchmarkRunSummaryResponse
from src.api.service import QShieldService

router = APIRouter(prefix="/api/benchmarks", tags=["Performance Benchmarking (M18)"])


@router.get("", response_model=list[BenchmarkRunSummaryResponse])
def list_benchmark_runs(
    service: Annotated[QShieldService, Depends(get_service)],
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[BenchmarkRunSummaryResponse]:
    """List historical M18 benchmark suite executions."""
    return service.list_benchmark_runs(limit=limit, offset=offset)


@router.get("/{run_id}", response_model=BenchmarkRunDetailResponse)
def get_benchmark_run_detail(
    run_id: str,
    service: Annotated[QShieldService, Depends(get_service)],
) -> BenchmarkRunDetailResponse:
    """Retrieve full latency, throughput, and scaling metrics for a benchmark run."""
    detail = service.get_benchmark_run(run_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Benchmark run '{run_id}' not found.",
        )
    return detail


@router.post("/run", response_model=BenchmarkRunDetailResponse, status_code=status.HTTP_201_CREATED)
def trigger_benchmark_run(
    service: Annotated[QShieldService, Depends(get_service)],
    suite_id: str = "suite_qshield_benchmarks",
) -> BenchmarkRunDetailResponse:
    """Execute the standardized M18 benchmark suite and persist operational metrics."""
    try:
        return service.trigger_benchmark_run(suite_id=suite_id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute benchmark suite.",
        ) from exc

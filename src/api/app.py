"""Q-SHIELD — FastAPI Application Factory (Milestone M19-B).

Initializes the FastAPI application, configures CORS, structured error handlers,
dependency injection, and registers all API routers.
"""

from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.routes.benchmarks import router as benchmarks_router
from src.api.routes.evaluation import router as evaluation_router
from src.api.routes.fusion import router as fusion_router
from src.api.routes.quantum import router as quantum_router
from src.api.routes.security import get_service, router as security_router
from src.api.routes.threats import router as threats_router
from src.api.schemas import HealthResponse
from src.api.service import QShieldService
from src.persistence.database import DEFAULT_DB_PATH, DatabaseManager
from src.persistence.repository import SecurityRepository


from contextlib import asynccontextmanager
from typing import AsyncGenerator

def create_app(db_path: str = DEFAULT_DB_PATH) -> FastAPI:
    """Create and configure a FastAPI application instance.

    Args:
        db_path: SQLite database file path (or ':memory:' for tests).

    Returns:
        Configured FastAPI application.
    """
    db_mgr = DatabaseManager(db_path=db_path)
    repository = SecurityRepository(db_mgr)
    service = QShieldService(repository)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        yield
        db_mgr.close()

    app = FastAPI(
        title="Q-SHIELD Security & Verification API",
        description="FastAPI service boundary exposing the Q-SHIELD Quantum Cyber Threat Detection Pipeline.",
        version="0.1.0",
        lifespan=lifespan,
    )

    # 1. CORS Configuration (for local frontend development)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 2. Dependency Injection Setup
    app.dependency_overrides[get_service] = lambda: service

    # 3. Global Exception Handlers (Clean, sanitized responses without leaking stack traces)
    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc)},
        )

    # 4. Root Health Check Endpoint
    @app.get("/health", response_model=HealthResponse, tags=["Health"])
    def health_check() -> HealthResponse:
        return HealthResponse(status="ok", service="q-shield-api", version="0.1.0")

    # 5. Include Domain Routers
    app.include_router(security_router)
    app.include_router(quantum_router)
    app.include_router(threats_router)
    app.include_router(fusion_router)
    app.include_router(evaluation_router)
    app.include_router(benchmarks_router)

    return app


# Default application instance for Uvicorn ASGI runner
app = create_app()

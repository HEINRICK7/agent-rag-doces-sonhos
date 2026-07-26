"""Liveness and readiness endpoints."""

from fastapi import APIRouter, Request, Response

from app.shared.infrastructure.observability.health import ReadinessReport

router = APIRouter(tags=["health"])


@router.get("/health", summary="Verifica a disponibilidade da API")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready", summary="Verifica as dependências da aplicação")
async def readiness(request: Request, response: Response) -> ReadinessReport:
    report: ReadinessReport = await request.app.state.infrastructure_health.check()
    if report["status"] != "ready":
        response.status_code = 503
    return report

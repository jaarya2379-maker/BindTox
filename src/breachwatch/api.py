from __future__ import annotations

from fastapi import FastAPI

from .repository import build_alert_repository
from .schemas import BreachCheckRequest
from .service import BreachWatchService


app = FastAPI(title="BreachWatch API", version="0.1.0")
service = BreachWatchService(repository=build_alert_repository())


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "breachwatch"}


@app.post("/breach-check")
def breach_check(request: BreachCheckRequest):
    return service.check_email(request)


@app.get("/dashboard")
def dashboard():
    return service.dashboard_summary()


@app.get("/alerts")
def alerts(limit: int = 10):
    return service.repository.list_alerts(limit=limit)


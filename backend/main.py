"""
Minimal ASGI app for Vercel Services (routePrefix /_/backend).

Chart data is built offline into frontend/public/data; this service is for
health checks and future APIs only.
"""

from fastapi import FastAPI

app = FastAPI(title="BadgerNet 4.0 backend", version="4.0")


@app.get("/_/backend")
async def backend_root() -> dict[str, str]:
    return {
        "service": "badgernet-backend",
        "detail": "Static JSON is served from the Vite frontend build.",
    }


@app.get("/_/backend/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

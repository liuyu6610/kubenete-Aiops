from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from config import settings
from core.errors import APIError, setup_logger
from core.dependencies import state
from services.prometheus_service import PrometheusService
from services.loki_service import LokiService
from services.llm_service import LLMService
from services.k8s_service import K8sService
from services.db_service import DatabaseService
from services.notification_service import NotificationService

# Routers
from api.stats import router as stats_router
from api.health import router as health_router
from api.alerts import router as alerts_router
from api.ws import router as ws_router
from api.n8n import router as n8n_router

logger = setup_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing KubeSentinel Core Services...")
    state.prom_service = PrometheusService()
    state.loki_service = LokiService()
    state.llm_service = LLMService()
    state.notify_service = NotificationService()
    import os
    os.makedirs("data", exist_ok=True)
    state.db_service = DatabaseService(db_path="data/kubesentinel.db")
    try:
        state.k8s_service = K8sService()
    except Exception as e:
        if getattr(settings, 'K8S_IN_CLUSTER', False):
            # In cluster K8s client init...
            pass
        else:
            logger.warning(f"K8s init failed (expected if not running in cluster): {e}")

    # Postgres and Redis Initialization
    try:
        logger.info("Initializing PostgreSQL and Redis connections...")
        await state.db_service.init_db()
        logger.info("Database schemas ready and Redis connected.")
    except Exception as e:
        logger.error(f"Failed to bind Database Services: {str(e)}")

    logger.info("KubeSentinel Core Services initialized successfully.")

    yield
    # Shutdown
    logger.info("Shutting down KubeSentinel Core Services...")
    # Add cleanup logic if necessary

app = FastAPI(title="KubeSentinel AI Engine", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handlers
@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError):
    logger.error(f"APIError: {exc.message} - {exc.details}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message, "details": exc.details}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "message": "An unexpected error occurred."}
    )

# Include Routers
app.include_router(health_router, tags=["Health"])
app.include_router(stats_router, tags=["Dashboard Stats"])
app.include_router(alerts_router, tags=["Alerts & Webhooks"])
app.include_router(ws_router, tags=["Realtime WebSocket"])
app.include_router(n8n_router, tags=["n8n Workflow Automation"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

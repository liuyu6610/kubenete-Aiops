from fastapi import APIRouter, Depends
from core.dependencies import get_prom_service, get_k8s_service
from services.prometheus_service import PrometheusService
from services.k8s_service import K8sService
from core.errors import setup_logger, APIError
from config import settings

logger = setup_logger(__name__)
router = APIRouter()

@router.get("/healthz")
async def health_check(
    prom: PrometheusService = Depends(get_prom_service),
    k8s: K8sService = Depends(get_k8s_service)
):
    """Enhanced health check with dependency status."""
    try:
        status = {
            "status": "ok",
            "version": "2.0.0",
            "components": {
                "prometheus": prom.is_healthy() if prom else False,
                "k8s_operator": k8s is not None,
                "llm_provider": settings.LLM_PROVIDER,
                "llm_configured": bool(settings.DASHSCOPE_API_KEY or settings.OPENAI_API_KEY),
                "feishu_configured": bool(settings.FEISHU_WEBHOOK_URL),
            }
        }
        return status
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise APIError("Health check failed due to internal error", status_code=503)

@router.get("/api/v1/cluster/stats")
async def get_cluster_stats(prom: PrometheusService = Depends(get_prom_service)):
    """Get real-time cluster stats from Prometheus."""
    try:
        if prom:
            return prom.get_cluster_stats()
        return {"status": "unavailable", "reason": "Prometheus service not initialized"}
    except Exception as e:
        logger.error(f"Failed to fetch cluster stats: {e}")
        raise APIError("Failed to fetch cluster stats")

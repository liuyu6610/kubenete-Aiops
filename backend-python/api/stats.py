from fastapi import APIRouter, Depends
from models import StatsResponse
from services.db_service import DatabaseService
from core.errors import setup_logger, APIError
from core.dependencies import get_db_service

logger = setup_logger(__name__)
router = APIRouter()

def get_db():
    return get_db_service()

@router.get("/api/v1/stats", response_model=StatsResponse)
async def get_stats(db: DatabaseService = Depends(get_db)):
    """Dashboard statistics endpoint with robust error handling, backed by Redis & Postgres."""
    try:
        auto_healed = await db.get_auto_healed_count()
        success_rate = await db.get_healing_success_rate()
        action_dist = await db.get_action_distribution()
        total_alerts = await db.get_today_alert_count()
        pending = await db.get_pending_approval_count()
        
        return StatsResponse(
            total_alerts_today=total_alerts,
            auto_healed_count=auto_healed,
            success_rate=success_rate,
            pending_approval=pending,
            recent_actions=action_dist,
        )
    except Exception as e:
        logger.error(f"Error retrieving stats: {e}")
        raise APIError("Failed to retrieve dashboard statistics") from e

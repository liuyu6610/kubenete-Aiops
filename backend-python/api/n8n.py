from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from typing import Optional
from core.dependencies import (
    get_db_service, get_k8s_service, get_notify_service
)
from services.db_service import DatabaseService
from services.k8s_service import K8sService
from services.notification_service import NotificationService
from models import HealingDecision
from core.errors import setup_logger, APIError, NotFoundError
from config import settings

logger = setup_logger(__name__)
router = APIRouter()

class N8nCallbackPayload(BaseModel):
    alert_id: int
    action_type: str  # "approve" | "reject"
    comment: Optional[str] = "Approved via n8n automated workflow."
    operator: Optional[str] = "n8n_engine"

@router.post("/api/v1/n8n/callback")
async def handle_n8n_callback(
    payload: N8nCallbackPayload,
    x_kubesentinel_token: Optional[str] = Header(None, alias="X-KubeSentinel-Token"),
    db: DatabaseService = Depends(get_db_service),
    k8s: K8sService = Depends(get_k8s_service),
    notify: NotificationService = Depends(get_notify_service)
):
    """
    Standard Callback Webhook for n8n.
    Secured tightly via X-KubeSentinel-Token pattern validation (czlonkowski/n8n-skills).
    """
    if x_kubesentinel_token != settings.N8N_SECRET_TOKEN:
        logger.warning("n8n Webhook Auth Failed: Token mismatch.")
        raise HTTPException(status_code=401, detail="Invalid security token")

    try:
        alert = await db.get_alert_by_id(payload.alert_id)
        if not alert:
            raise NotFoundError("Alert ID not found")
        
        if alert['status'] != '待审批':
            raise APIError("Alert is no longer waiting for workflow execution.")

        if payload.action_type == "approve":
            logger.info(f"n8n Workflow authorized healing for Alert {payload.alert_id} ({alert['action']})")
            
            if k8s:
                decision = HealingDecision(
                    analysis=alert['analysis'],
                    confidence=alert['confidence'],
                    action=alert['action'],
                    target={"resource_type": "deployment", "name": alert['target'], "namespace": alert['namespace']}
                )
                rule_name = k8s.create_healing_rule(decision)
                await db.update_alert_status(payload.alert_id, "n8n工作流授权执行")
                await db.record_audit(
                    title=f"n8n 编排授权引擎执行了针对 {alert['target']} 的自愈",
                    description=f"触发了 CRD: {rule_name}. 附言: {payload.comment}",
                    operator=payload.operator,
                    log_type="warning"
                )
                notify.notify_healing_action(
                    alert_name=alert['alertname'], target=alert['target'], namespace=alert['namespace'],
                    action=alert['action'], confidence=alert['confidence'], analysis=alert['analysis'],
                    status="n8n工作流授权执行"
                )
                return {"status": "success", "message": f"Orchestration triggered CRD: {rule_name}"}

            await db.update_alert_status(payload.alert_id, "n8n工作流执行完毕 (本地无K8s)")
            return {"status": "success", "message": "Simulated n8n orchestrator success"}

        elif payload.action_type == "reject":
            await db.update_alert_status(payload.alert_id, "n8n工作流已否决")
            await db.record_audit(
                title=f"n8n 编排判定否决了 {alert['target']} 的自愈",
                description=f"附言: {payload.comment}",
                operator=payload.operator,
                log_type="info"
            )
            return {"status": "success", "message": "Action rejected by n8n execution pipeline."}
        else:
            raise APIError(f"Unsupported action variant: {payload.action_type}")
            
    except APIError:
        raise
    except Exception as e:
        logger.error(f"Error orchestrating n8n callback state: {e}", exc_info=True)
        raise APIError("Failed to process n8n pipeline callback")

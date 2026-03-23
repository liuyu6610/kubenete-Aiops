from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from models import AlertPayload, AlertmanagerWebhook, HealingDecision
from core.dependencies import (
    get_db_service, get_prom_service, get_loki_service, get_llm_service,
    get_k8s_service, get_notify_service
)
from services.db_service import DatabaseService
from services.prometheus_service import PrometheusService
from services.loki_service import LokiService
from services.llm_service import LLMService
from services.k8s_service import K8sService
from services.notification_service import NotificationService
from services.n8n_service import n8n_svc
from core.errors import setup_logger, APIError, NotFoundError, ValidationError
import asyncio
from config import settings
from api.ws import manager

logger = setup_logger(__name__)
router = APIRouter()

@router.get("/api/v1/alerts")
async def get_alerts(db: DatabaseService = Depends(get_db_service)):
    try:
        return await db.get_recent_alerts()
    except Exception as e:
        logger.error(f"Error fetching alerts: {e}")
        raise APIError("Failed to fetch alerts")

@router.get("/api/v1/audit")
async def get_audits(db: DatabaseService = Depends(get_db_service)):
    try:
        return await db.get_audit_logs()
    except Exception as e:
        logger.error(f"Error fetching audits: {e}")
        raise APIError("Failed to fetch audits")

@router.post("/api/v1/alerts/{alert_id}/approve")
async def approve_alert_action(
    alert_id: int,
    db: DatabaseService = Depends(get_db_service),
    k8s: K8sService = Depends(get_k8s_service),
    notify: NotificationService = Depends(get_notify_service)
):
    try:
        alert = await db.get_alert_by_id(alert_id)
        if not alert:
            raise NotFoundError("Alert not found")
        if alert['status'] != '待审批':
            raise ValidationError("Alert is not in pending state")
        
        logger.info(f"Human authorized execution for alert {alert_id}: {alert['action']}")
        
        if k8s:
            decision = HealingDecision(
                analysis=alert['analysis'],
                confidence=alert['confidence'],
                action=alert['action'],
                target={"resource_type": "deployment", "name": alert['target'], "namespace": alert['namespace']}
            )
            rule_name = k8s.create_healing_rule(decision)
            await db.update_alert_status(alert_id, "手动授权执行中")
            await db.record_audit(
                title=f"管理员手动授权对 {alert['target']} 的 {alert['action']}",
                description=f"人工介入。触发了 CRD: {rule_name}",
                operator="Admin (Vue)",
                log_type="warning"
            )
            notify.notify_healing_action(
                alert_name=alert['alertname'], target=alert['target'], namespace=alert['namespace'],
                action=alert['action'], confidence=alert['confidence'], analysis=alert['analysis'],
                status="人工授权执行中"
            )
            return {"status": "success", "message": f"Action triggered. Created HealingRule: {rule_name}"}
        
        await db.update_alert_status(alert_id, "手动授权完毕 (无K8s)")
        return {"status": "success", "message": "Simulated approval success (K8s not running)"}
    except APIError:
        raise
    except Exception as e:
        logger.error(f"Error approving alert: {e}")
        raise APIError("Failed to approve alert")

@router.post("/api/v1/alerts/{alert_id}/reject")
async def reject_alert_action(alert_id: int, db: DatabaseService = Depends(get_db_service)):
    try:
        alert = await db.get_alert_by_id(alert_id)
        if not alert:
            raise NotFoundError("Alert not found")

        await db.update_alert_status(alert_id, "已拒绝")
        await db.record_audit(
            title=f"管理员拒绝了对 {alert['target']} 的 {alert['action']}",
            description=f"AI 分析为: {alert['analysis']}",
            operator="Admin (Vue)",
            log_type="info"
        )
        return {"status": "success"}
    except APIError:
        raise
    except Exception as e:
        logger.error(f"Error rejecting alert: {e}")
        raise APIError("Failed to reject alert")

@router.post("/api/v1/webhook/alert")
async def receive_alert(
    payload: AlertmanagerWebhook,
    db: DatabaseService = Depends(get_db_service),
    prom: PrometheusService = Depends(get_prom_service),
    loki: LokiService = Depends(get_loki_service),
    llm: LLMService = Depends(get_llm_service),
    k8s: K8sService = Depends(get_k8s_service),
    notify: NotificationService = Depends(get_notify_service),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    try:
        alert = payload.alerts[0] if payload.alerts and payload.alerts[0].status == "firing" else None
        if not alert and payload.status == "firing":
            alert = AlertPayload(
                status=payload.status, labels=payload.labels or {}, 
                annotations=payload.annotations or {}, startsAt=payload.startsAt, endsAt=payload.endsAt
            )
        
        if not alert or alert.status != "firing":
            return {"status": "ignored", "message": "Alert is resolved or not firing"}

        alert_name = alert.labels.get("alertname", "Unknown Alert")
        pod_name = alert.labels.get("pod", "unknown-pod")
        namespace = alert.labels.get("namespace", "default")

        await manager.broadcast_alert({
            "event": "NEW_ALERT_RECEIVED",
            "alertname": alert_name,
            "pod": pod_name,
            "namespace": namespace
        })

        if await db.check_cooldown(pod_name, namespace):
            logger.info(f"Cooldown active for {pod_name}/{namespace}, skipping.")
            await db.record_audit(
                title=f"告警 {alert_name} 被冷却机制过滤",
                description=f"目标 {pod_name} 在冷却期内，跳过重复处理",
                operator="Cooldown Filter", log_type="info"
            )
            return {"status": "skipped", "message": f"Target {pod_name} is in cooldown."}

        summary = f"Alert: {alert_name}\nPod: {pod_name}\nNamespace: {namespace}\nDetails: {alert.annotations.get('description', '')}"

        metrics_context = prom.get_pod_metrics_context(pod_name, namespace) if prom else "No metrics available"
        logs_context = loki.query_pod_logs(pod_name, namespace) if loki else "No logs available"

        await db.record_audit(
            title=f"收到告警 {alert_name}，开始 AI 诊断",
            description=f"目标节点/Pod: {pod_name}", operator="System/Prometheus", log_type="primary"
        )
        
        loop = asyncio.get_event_loop()
        decision = await loop.run_in_executor(
            None, lambda: llm.analyze_alert(summary, metrics_context, logs_context)
        )

        logger.info(f"AI Decision: [{decision.action}] target={decision.target.name} confidence={decision.confidence}")
        
        needs_approval = decision.human_approval_required
        if decision.risk_level == "high" and settings.HIGH_RISK_REQUIRE_APPROVAL:
            needs_approval = True
        if decision.confidence < settings.HEALING_CONFIDENCE_THRESHOLD:
            needs_approval = True

        if decision.action in {"no_action", "investigate", "none"}:
            await db.record_alert(alert_name, decision, "无需自愈动作")
            await manager.broadcast_alert({"event": "ALERT_ANALYZED", "status": "无需自愈动作"})
            return {"status": "success", "message": "No action required", "decision": decision.model_dump()}

        if not needs_approval:
            await db.record_alert(alert_name, decision, "已下发自动执行")
            await manager.broadcast_alert({"event": "ALERT_ANALYZED", "status": "已自动执行", "decision": decision.model_dump()})
            if k8s:
                rule_name = k8s.create_healing_rule(decision)
                await db.record_audit(
                    title=f"自动下发针对 {decision.target.name} 的自愈动作",
                    description=f"置信度 {decision.confidence:.0%}，风险 {decision.risk_level}。CRD: {rule_name}",
                    operator="KubeSentinel AI", log_type="success"
                )
                notify.notify_healing_action(
                    alert_name=alert_name, target=decision.target.name, namespace=decision.target.namespace,
                    action=decision.action, confidence=decision.confidence, analysis=decision.analysis,
                    summary=decision.summary_for_notification, status="已自动执行"
                )
                return {"status": "success", "message": f"Action triggered. Created HealingRule: {rule_name}", "decision": decision.model_dump()}
            return {"status": "skipped", "message": "K8s service not initialized.", "decision": decision.model_dump()}

        alert_id = await db.record_alert(alert_name, decision, "待审批")
        await manager.broadcast_alert({"event": "ALERT_ANALYZED", "status": "待审批", "decision": decision.model_dump()})
        await db.record_audit(
            title=f"拦截 {decision.target.name} 的 {decision.action} 动作 (需审批)",
            description=f"置信度 {decision.confidence:.0%}，风险 {decision.risk_level}。分析: {decision.analysis[:100]}",
            operator="Safety Interceptor", log_type="warning"
        )
        
        # Fire off workflow orchestration payload directly to n8n framework
        background_tasks.add_task(
            n8n_svc.trigger_workflow, 
            "approval_needed", 
            {
                "alert_id": alert_id,
                "alert_name": alert_name,
                "target": decision.target.name,
                "namespace": decision.target.namespace,
                "action": decision.action,
                "risk_level": decision.risk_level,
                "confidence": decision.confidence,
                "analysis": decision.analysis
            }
        )

        notify.notify_approval_needed(
            alert_name=alert_name, target=decision.target.name, namespace=decision.target.namespace,
            action=decision.action, confidence=decision.confidence, analysis=decision.analysis
        )
        return {"status": "queued", "message": "Queued for n8n/human execution.", "decision": decision.model_dump()}

    except Exception as e:
        logger.error(f"Failed to process alert: {e}", exc_info=True)
        raise APIError("Failed to process webhook alert") from e

@router.post("/api/v1/test-alert")
async def send_test_alert(db: DatabaseService = Depends(get_db_service), prom: PrometheusService = Depends(get_prom_service), loki: LokiService = Depends(get_loki_service), llm: LLMService = Depends(get_llm_service), k8s: K8sService = Depends(get_k8s_service), notify: NotificationService = Depends(get_notify_service)):
    simulated_payload = AlertmanagerWebhook(
        status="firing",
        alerts=[
            AlertPayload(
                status="firing",
                labels={"alertname": "PodCpuHighUsage", "namespace": "default", "pod": "order-service-test", "severity": "critical", "container": "order-service"},
                annotations={"summary": "Pod CPU usage exceeded 85% for 2 minutes", "description": "Simulated high CPU alert for testing."}
            )
        ]
    )
    return await receive_alert(simulated_payload, db, prom, loki, llm, k8s, notify)

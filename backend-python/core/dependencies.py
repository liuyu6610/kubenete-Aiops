from typing import Optional
from services.prometheus_service import PrometheusService
from services.loki_service import LokiService
from services.llm_service import LLMService
from services.k8s_service import K8sService
from services.notification_service import NotificationService
from services.db_service import DatabaseService
from core.errors import setup_logger

logger = setup_logger(__name__)

class AppState:
    prom_service: Optional[PrometheusService] = None
    loki_service: Optional[LokiService] = None
    llm_service: Optional[LLMService] = None
    k8s_service: Optional[K8sService] = None
    notify_service: Optional[NotificationService] = None
    db_service: Optional[DatabaseService] = None

state = AppState()

def get_prom_service():
    return state.prom_service

def get_loki_service():
    return state.loki_service

def get_llm_service():
    return state.llm_service

def get_k8s_service():
    return state.k8s_service

def get_notify_service():
    return state.notify_service

def get_db_service():
    return state.db_service

import logging
import uuid
import datetime
from kubernetes import client, config
from models import HealingDecision
from config import settings

logger = logging.getLogger(__name__)

class K8sService:
    def __init__(self):
        try:
            if settings.IN_CLUSTER:
                config.load_incluster_config()
                logger.info("Loaded in-cluster Kubernetes configuration.")
            else:
                config.load_kube_config()
                logger.info("Loaded local kubeconfig.")
            
            self.dynamic_client = client.ApiClient()
            self.custom_api = client.CustomObjectsApi(self.dynamic_client)
            
        except Exception as e:
            logger.error(f"Failed to initialize Kubernetes client: {e}")
            raise

    def create_healing_rule(self, decision: HealingDecision) -> str:
        """
        Translates the LLM HealingDecision into a kubesentinel.io/v1beta1 HealingRule CRD
        and applies it to the cluster, where the Go Operator will pick it up.
        """
        
        # We use a unique ID for each rule to avoid collisions on multiple alerts
        rule_name = f"heal-{decision.target.name}-{uuid.uuid4().hex[:6]}"
        namespace = decision.target.namespace

        # Build the CRD Dict
        crd_body = {
            "apiVersion": "kubesentinel.io/v1beta1",
            "kind": "HealingRule",
            "metadata": {
                "name": rule_name,
                "namespace": namespace,
                "labels": {
                    "kubesentinel.io/created-by": "ai-backend"
                }
            },
            "spec": {
                "action": decision.action,
                "targetResource": decision.target.name,
                "targetNamespace": namespace,
                "triggerAlert": decision.analysis[:100], # Trucate analysis for trigger context
                "aiConfidence": decision.confidence
            }
        }

        logger.info(f"Creating HealingRule CRD: {rule_name} in {namespace}")
        
        try:
            response = self.custom_api.create_namespaced_custom_object(
                group="kubesentinel.io",
                version="v1beta1",
                namespace=namespace,
                plural="healingrules",
                body=crd_body
            )
            logger.info(f"Successfully created HealingRule: {response['metadata']['name']}")
            return response['metadata']['name']
            
        except client.exceptions.ApiException as e:
            logger.error(f"Kubernetes API Exception when creating HealingRule: {e.reason} ({e.status})\n{e.body}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating HealingRule: {e}")
            raise

    def get_pod_logs(self, namespace: str, pod_name: str, tail_lines: int = 50) -> str:
        """Fetch recent logs from a specific pod."""
        logger.info(f"Fetching logs for pod {pod_name} in {namespace}")
        try:
            core_v1 = client.CoreV1Api(self.dynamic_client)
            logs = core_v1.read_namespaced_pod_log(name=pod_name, namespace=namespace, tail_lines=tail_lines)
            return logs
        except Exception as e:
            logger.error(f"Error fetching logs for {pod_name}: {e}")
            return f"Error fetching logs: {e}"

    def get_pod_events(self, namespace: str, pod_name: str) -> str:
        """Fetch recent events for a specific pod."""
        logger.info(f"Fetching events for pod {pod_name} in {namespace}")
        try:
            core_v1 = client.CoreV1Api(self.dynamic_client)
            events = core_v1.list_namespaced_event(namespace=namespace, field_selector=f"involvedObject.name={pod_name}")
            if not events.items:
                return "No events found."
            event_strs = [f"[{e.type}] {e.reason}: {e.message}" for e in events.items[-10:]]
            return "\n".join(event_strs)
        except Exception as e:
            logger.error(f"Error fetching events for {pod_name}: {e}")
            return f"Error fetching events: {e}"

    def describe_pod(self, namespace: str, pod_name: str) -> dict:
        """Fetch detailed status and configuration of a pod."""
        logger.info(f"Describing pod {pod_name} in {namespace}")
        try:
            core_v1 = client.CoreV1Api(self.dynamic_client)
            pod = core_v1.read_namespaced_pod(name=pod_name, namespace=namespace)
            return {
                "phase": pod.status.phase,
                "conditions": [{"type": c.type, "status": c.status, "message": c.message} for c in pod.status.conditions] if pod.status.conditions else [],
                "container_statuses": [{"name": c.name, "ready": c.ready, "restart_count": c.restart_count, "state": str(c.state)} for c in pod.status.container_statuses] if pod.status.container_statuses else [],
                "node_name": pod.spec.node_name
            }
        except Exception as e:
            logger.error(f"Error describing pod {pod_name}: {e}")
            return {"error": str(e)}

    def delete_pod(self, namespace: str, pod_name: str) -> str:
        """Restart a pod by deleting it (Deployment constraints will recreate it)."""
        logger.info(f"Deleting pod {pod_name} in {namespace}")
        try:
            core_v1 = client.CoreV1Api(self.dynamic_client)
            core_v1.delete_namespaced_pod(name=pod_name, namespace=namespace)
            return f"Pod {pod_name} deleted successfully (will be recreated if managed by ReplicaSet)."
        except Exception as e:
            logger.error(f"Error deleting pod {pod_name}: {e}")
            return f"Error deleting pod: {e}"

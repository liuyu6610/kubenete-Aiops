import logging
import httpx
from typing import Dict, Any
from config import settings

logger = logging.getLogger(__name__)

class N8nService:
    """
    Dedicated HTTP Service to trigger No-Code/Low-Code n8n workflows.
    Complies with czlonkowski/n8n-skills@n8n-workflow-patterns for secure bi-directional webhooks.
    """
    def __init__(self):
        self.webhook_url = settings.N8N_WEBHOOK_URL
        self.secret_token = settings.N8N_SECRET_TOKEN
        self.client = httpx.AsyncClient(timeout=10.0)

    async def trigger_workflow(self, event_type: str, payload: Dict[str, Any]) -> bool:
        """
        Emits actionable JSON payloads to n8n endpoints when the GLM-5 Engine yields complex operations.
        """
        if not self.webhook_url:
            logger.warning("n8n Webhook URL missing. Bypassing n8n workflow trigger.")
            return False

        headers = {
            "Content-Type": "application/json",
            "X-KubeSentinel-Token": self.secret_token,
            "X-Event-Type": event_type
        }
        
        try:
            logger.info(f"Transmitting '{event_type}' payload to n8n workflow engine...")
            response = await self.client.post(
                self.webhook_url,
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            logger.info(f"n8n workflow triggered successfully [{response.status_code}].")
            return True
        except httpx.HTTPError as e:
            logger.error(f"n8n webhook POST failed: {e}")
            return False
            
    async def close(self):
        """Clean up the http client on application shutdown"""
        await self.client.aclose()

n8n_svc = N8nService()

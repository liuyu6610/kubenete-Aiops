import logging
import requests
from datetime import datetime, timedelta
from typing import Optional
from config import settings

logger = logging.getLogger(__name__)

class LokiService:
    def __init__(self):
        self.base_url = settings.LOKI_URL

    def query_pod_logs(self, pod_name: str, namespace: str = "default", minutes: int = 10, limit: int = 200) -> str:
        """Fetch recent logs for a pod within a time range"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=minutes)
        start_ns = int(start_time.timestamp() * 1e9)
        end_ns = int(end_time.timestamp() * 1e9)

        query = f'{{namespace="{namespace}", pod=~"{pod_name}.*"}}'
        params = {
            "query": query,
            "limit": limit,
            "start": start_ns,
            "end": end_ns
        }

        logger.info(f"Querying Loki logs: {query}")
        try:
            response = requests.get(f"{self.base_url}/loki/api/v1/query_range", params=params, timeout=8)
            response.raise_for_status()
            data = response.json()
            if data.get("status") != "success":
                return "No log data available."

            result = data.get("data", {}).get("result", [])
            if not result:
                return "No log data available."

            logs = []
            for stream in result:
                values = stream.get("values", [])
                for _, line in values:
                    logs.append(line.strip())

            if not logs:
                return "No log data available."

            tail_logs = logs[-50:]
            return "\n".join(tail_logs)
        except Exception as e:
            logger.error(f"Loki query failed: {e}")
            return f"Error fetching logs: {str(e)}"

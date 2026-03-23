import requests
import logging
from config import settings

logger = logging.getLogger(__name__)

class PrometheusService:
    def __init__(self):
        self.base_url = settings.PROMETHEUS_URL

    def _query(self, promql: str, timeout: int = 5) -> dict:
        logger.info(f"Executing PromQL: {promql}")
        try:
            response = requests.get(f"{self.base_url}/api/v1/query", params={"query": promql}, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Prometheus query failed for [{promql}]: {e}")
            return {"status": "error", "data": {"result": []}}

    def is_healthy(self) -> bool:
        """Check if Prometheus is reachable."""
        try:
            resp = requests.get(f"{self.base_url}/-/healthy", timeout=3)
            return resp.status_code == 200
        except Exception:
            return False

    def get_pod_metrics_context(self, pod_name: str, namespace: str = "default", time_range: str = "5m") -> str:
        """Fetch a summarized metrics context for LLM (CPU/Memory/Restart/Network)"""
        try:
            cpu_query = f'rate(container_cpu_usage_seconds_total{{pod=~"{pod_name}.*", namespace="{namespace}", container!=""}}[{time_range}])'
            mem_query = f'container_memory_working_set_bytes{{pod=~"{pod_name}.*", namespace="{namespace}", container!=""}}'
            restart_query = f'kube_pod_container_status_restarts_total{{pod=~"{pod_name}.*", namespace="{namespace}"}}'
            net_rx_query = f'rate(container_network_receive_bytes_total{{pod=~"{pod_name}.*", namespace="{namespace}"}}[{time_range}])'
            net_tx_query = f'rate(container_network_transmit_bytes_total{{pod=~"{pod_name}.*", namespace="{namespace}"}}[{time_range}])'

            cpu_data = self._query(cpu_query)
            mem_data = self._query(mem_query)
            restart_data = self._query(restart_query)
            net_rx_data = self._query(net_rx_query)
            net_tx_data = self._query(net_tx_query)

            def format_result(data, unit, formatter=lambda v: f"{v:.4f}"):
                if data.get("status") != "success" or not data.get("data", {}).get("result"):
                    return ["No data"]
                results = []
                for r in data["data"]["result"]:
                    metric = r.get("metric", {})
                    name = metric.get("pod", metric.get("container", "unknown"))
                    value = float(r.get("value", [0, 0])[1])
                    results.append(f"{name}: {formatter(value)} {unit}")
                return results

            cpu_summary = format_result(cpu_data, "cores")
            mem_summary = format_result(mem_data, "MB", formatter=lambda v: f"{v/1024/1024:.2f}")
            restart_summary = format_result(restart_data, "restarts", formatter=lambda v: f"{v:.0f}")
            net_rx_summary = format_result(net_rx_data, "KB/s", formatter=lambda v: f"{v/1024:.2f}")
            net_tx_summary = format_result(net_tx_data, "KB/s", formatter=lambda v: f"{v/1024:.2f}")

            sections = [
                "[CPU] " + ", ".join(cpu_summary),
                "[Memory] " + ", ".join(mem_summary),
                "[Restarts] " + ", ".join(restart_summary),
                "[Net RX] " + ", ".join(net_rx_summary),
                "[Net TX] " + ", ".join(net_tx_summary)
            ]
            return "\n".join(sections)
        except Exception as e:
            logger.error(f"Prometheus query failed: {e}")
            return f"Error fetching metrics: {str(e)}"

    def get_pod_status(self, namespace: str = "default") -> list:
        """Fetch pod status info from kube-state-metrics."""
        query = f'kube_pod_status_phase{{namespace="{namespace}"}}'
        data = self._query(query)
        pods = []
        if data.get("status") == "success":
            for r in data.get("data", {}).get("result", []):
                metric = r.get("metric", {})
                value = float(r.get("value", [0, 0])[1])
                if value == 1:  # Only include active phases
                    pods.append({
                        "pod": metric.get("pod", "unknown"),
                        "phase": metric.get("phase", "unknown"),
                        "namespace": metric.get("namespace", namespace),
                    })
        return pods

    def get_cluster_stats(self) -> dict:
        """Get cluster-level stats for dashboard display."""
        stats = {
            "total_pods_running": 0,
            "total_nodes": 0,
            "nodes_ready": 0,
            "cpu_usage_avg": 0.0,
            "memory_usage_avg": 0.0,
        }

        # Total running pods
        pod_data = self._query('count(kube_pod_status_phase{phase="Running"})')
        if pod_data.get("status") == "success" and pod_data.get("data", {}).get("result"):
            stats["total_pods_running"] = int(float(pod_data["data"]["result"][0].get("value", [0, 0])[1]))

        # Total nodes
        node_data = self._query('count(kube_node_info)')
        if node_data.get("status") == "success" and node_data.get("data", {}).get("result"):
            stats["total_nodes"] = int(float(node_data["data"]["result"][0].get("value", [0, 0])[1]))

        # Nodes ready
        ready_data = self._query('count(kube_node_status_condition{condition="Ready",status="true"})')
        if ready_data.get("status") == "success" and ready_data.get("data", {}).get("result"):
            stats["nodes_ready"] = int(float(ready_data["data"]["result"][0].get("value", [0, 0])[1]))

        # Avg CPU usage
        cpu_data = self._query('avg(rate(container_cpu_usage_seconds_total{container!=""}[5m])) * 100')
        if cpu_data.get("status") == "success" and cpu_data.get("data", {}).get("result"):
            stats["cpu_usage_avg"] = round(float(cpu_data["data"]["result"][0].get("value", [0, 0])[1]), 2)

        # Avg memory usage
        mem_data = self._query('avg(container_memory_working_set_bytes{container!=""}) / 1024 / 1024')
        if mem_data.get("status") == "success" and mem_data.get("data", {}).get("result"):
            stats["memory_usage_avg"] = round(float(mem_data["data"]["result"][0].get("value", [0, 0])[1]), 2)

        return stats

    def execute_promql(self, promql: str) -> dict:
        """Expose raw PromQL querying for the GLM-5 Agent to analyze metrics autonomously."""
        return self._query(promql)

import logging
import datetime
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from services.prometheus_service import PrometheusService

logger = logging.getLogger(__name__)

class AIOpsService:
    """
    Advanced AIOps Fortification Service powered by Scikit-Learn
    Focuses on proactive anomaly detection using multivariate analysis (Isolation Forest).
    """
    def __init__(self):
        self.prom_svc = PrometheusService()

    def detect_anomalies_for_pod(self, namespace: str, pod_name: str, duration_minutes: int = 60) -> dict:
        """
        Uses an Isolation Forest to detect multivariate anomalies across CPU & Memory 
        for a specific Pod over the given time window, reducing complex false positives.
        """
        try:
            client = getattr(self.prom_svc, 'client', None)
            if not client:
                return {"error": "Prometheus client not initialized. Cannot fetch training data."}

            end_time = datetime.datetime.now()
            start_time = end_time - datetime.timedelta(minutes=duration_minutes)
            step = "1m"

            # 1. Fetch historical data representing operational baseline
            cpu_query = f'rate(container_cpu_usage_seconds_total{{namespace="{namespace}", pod="{pod_name}"}}[5m])'
            mem_query = f'container_memory_usage_bytes{{namespace="{namespace}", pod="{pod_name}"}}'

            # Note: custom_query_range provides time-series arrays
            cpu_data = client.custom_query_range(query=cpu_query, start_time=start_time, end_time=end_time, step=step)
            mem_data = client.custom_query_range(query=mem_query, start_time=start_time, end_time=end_time, step=step)

            if not cpu_data or not mem_data:
                return {"error": f"Insufficient historical data metrics to train ML models for Pod {pod_name}."}

            # 2. Extract and format values into a Pandas DataFrame
            cpu_vals = cpu_data[0].get('values', [])
            mem_vals = mem_data[0].get('values', [])

            df_cpu = pd.DataFrame(cpu_vals, columns=['timestamp', 'cpu'])
            df_mem = pd.DataFrame(mem_vals, columns=['timestamp', 'mem'])

            # Align timestamps (inner join)
            df = pd.merge(df_cpu, df_mem, on='timestamp', how='inner')
            if df.empty:
                return {"error": "Metric vectors empty after timestamp alignment."}

            df['cpu'] = pd.to_numeric(df['cpu'], errors='coerce')
            df['mem'] = pd.to_numeric(df['mem'], errors='coerce')
            df.dropna(inplace=True)

            if len(df) < 10: # Need minimal sample size for reasonable ML bounds
                return {"error": "Too few overlapping data points (minimum 10 needed)."}

            # 3. Fit Isolation Forest to detect uncharacteristic spikes/drops
            features = df[['cpu', 'mem']].values
            model = IsolationForest(contamination=0.05, random_state=42)
            df['anomaly'] = model.fit_predict(features)

            # Map anomalies: IsolationForest outputs -1 for outliers and 1 for inliers.
            anomalies = df[df['anomaly'] == -1]

            if not anomalies.empty:
                last_anomaly = anomalies.iloc[-1]
                
                # Format a rich RCA context payload for the GLM-5 Engine
                return {
                    "status": "anomalous",
                    "confidence_score": "High (Out of Bounds detected)",
                    "anomaly_count": len(anomalies),
                    "latest_anomaly": {
                        "timestamp": last_anomaly['timestamp'],
                        "cpu_value": float(last_anomaly['cpu']),
                        "mem_value": float(last_anomaly['mem'])
                    },
                    "details": f"Isolation Forest flagged {len(anomalies)} points as multivariate anomalies in the past {duration_minutes}m."
                }
            else:
                return {
                    "status": "normal",
                    "details": f"No Multivariate anomalies detected in the last {duration_minutes}m tracking window."
                }

        except Exception as e:
            logger.error(f"Isolation Forest Analysis Failed: {e}")
            return {"error": f"AIOps Engine Failure: {str(e)}"}

aiops_svc = AIOpsService()

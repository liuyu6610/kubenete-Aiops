import requests
import json
import time

# 配置你的本地 Python AI Backend 地址
WEBHOOK_URL = "http://localhost:8000/api/v1/webhook/alert"

def simulate_alert(alert_type, pod_name="order-service-abcdef"):
    
    # 基础模板
    payload = {
        "status": "firing",
        "labels": {
            "alertname": alert_type,
            "severity": "critical",
            "pod": pod_name,
            "namespace": "default"
        },
        "annotations": {}
    }
    
    if alert_type == "HighCpuUsage":
        payload["annotations"]["description"] = f"Pod {pod_name} CPU usage is critically high (> 85% for 5m). Possible goroutine leak or infinite loop."
    elif alert_type == "NetworkIngressSurge":
        payload["annotations"]["description"] = f"Pod {pod_name} is receiving an unusually high amount of network traffic. Possible CC attack or spike in user requests."
        payload["labels"]["severity"] = "warning"
    elif alert_type == "NodeNotReady":
        payload["annotations"]["description"] = f"Underlying Node is reporting NotReady status. System needs to evict pods."
        payload["labels"]["pod"] = "node-worker-01" # Target node name
    
    print(f"[{time.strftime('%H:%M:%S')}] 發送模擬告警: {alert_type} on {payload['labels']['pod']}")
    print(json.dumps(payload, indent=2))
    
    try:
        response = requests.post(WEBHOOK_URL, json=payload, headers={"Content-Type": "application/json"})
        print(f"\n[Response Status]: {response.status_code}")
        print(f"[Response Body]:\n{json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"请求失败: {e}")

if __name__ == "__main__":
    print("=== KubeSentinel AI 引擎一键靶机打靶测试器 ===")
    print("1. 发送 高 CPU 负载告警 (预期 AI 判定: Rolling Restart)")
    print("2. 发送 突发异常流量告警 (预期 AI 判定: 置信度低，抛给管理员审批 Scale Up)")
    
    while True:
        choice = input("\n请选择要发送的告警号 (1 or 2, q to quit): ").strip()
        if choice == '1':
            simulate_alert("HighCpuUsage", "order-service")
        elif choice == '2':
            simulate_alert("NetworkIngressSurge", "frontend-gateway")
        elif choice.lower() == 'q':
            break
        else:
            print("无效输入，请重试")

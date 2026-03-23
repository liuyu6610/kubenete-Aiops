# KubeSentinel - 用户 Prompt 模板
# 版本: v1.0
# 用途: 动态注入告警数据和集群上下文，构建发送给 LLM 的用户消息
# 使用方式: 在 n8n 的 Code 节点或 Expression 中渲染此模板

## 模板说明

此模板在 n8n 工作流中动态渲染，将 `{{ }}` 占位符替换为实际数据。
渲染后的内容作为 `user` 消息发送给 LLM。

---

## Prompt 模板正文

```
请根据以下 Kubernetes 集群告警信息和实时上下文，输出标准化的 JSON 修复方案。

## 一、原始告警数据

**告警名称:** {{ $json.alert_name }}
**告警级别:** {{ $json.severity }}
**告警状态:** {{ $json.status }}  {# firing = 正在发生, resolved = 已恢复 #}
**触发时间:** {{ $json.fired_at }}
**告警摘要:** {{ $json.summary }}
**告警描述:** {{ $json.description }}

**告警标签:**
```json
{{ $json.labels | tojson(indent=2) }}
```

## 二、受影响资源信息

- **命名空间:** {{ $json.namespace }}
- **Pod 名称:** {{ $json.pod_name }}
- **Deployment:** {{ $json.deployment_name }}
- **容器:** {{ $json.container_name }}

## 三、实时资源指标（来自 Prometheus 查询）

| 指标 | 当前值 | 阈值 |
|---|---|---|
| CPU 使用率 | {{ $json.current_cpu_usage }}% | {{ $json.cpu_threshold }}% |
| 内存使用率 | {{ $json.current_memory_usage }}% | {{ $json.memory_threshold }}% |
| Pod 重启次数（过去30min） | {{ $json.restart_count_30m }} 次 | 3 次 |
| 就绪副本数 / 期望副本数 | {{ $json.ready_replicas }} / {{ $json.desired_replicas }} | — |

## 四、历史告警记录（过去 24 小时）

{{ $json.alert_history_summary }}
{# 示例: "过去24小时，该 Pod 曾在 01:32 触发过一次 PodCpuHighUsage 告警，持续12分钟后自动恢复" #}

## 五、最近部署历史

{{ $json.recent_deploy_history }}
{# 示例: "最近一次 Deployment 更新发生在 2小时前，镜像从 v1.2.3 升级到 v1.2.4" #}

## 六、相关 Pod 日志摘要（最近 50 行关键日志）

```
{{ $json.pod_log_snippet }}
```

---

**请严格按照 system prompt 中定义的 JSON schema 输出你的分析结论和修复方案。**
```

---

## n8n Code 节点渲染示例

在 n8n Code 节点（JavaScript）中构建上述 Prompt：

```javascript
// 从 Alertmanager Webhook 中提取关键字段
const alert = $input.first().json.alerts[0];
const labels = alert.labels || {};
const annotations = alert.annotations || {};

// 构建发送给 LLM 的消息体
const userMessage = `
请根据以下 Kubernetes 集群告警信息和实时上下文，输出标准化的 JSON 修复方案。

## 一、原始告警数据

**告警名称:** ${labels.alertname}
**告警级别:** ${labels.severity}
**告警状态:** ${alert.status}
**触发时间:** ${alert.startsAt}
**告警摘要:** ${annotations.summary}
**告警描述:** ${annotations.description}

## 二、受影响资源信息

- **命名空间:** ${labels.namespace}
- **Pod 名称:** ${labels.pod || '未知'}
- **Deployment:** ${labels.deployment || labels.pod?.replace(/-[a-z0-9]+-[a-z0-9]+$/, '') || '未知'}
- **容器:** ${labels.container || '未知'}

## 三、实时资源指标

（此处在实际工作流中，应先通过 HTTP Request 节点查询 Prometheus API 获取）
- CPU 使用率: 待查询
- 内存使用率: 待查询
- 重启次数: 待查询

**请基于告警信息进行分析，输出 JSON 修复方案。**
`;

return [{
  json: {
    messages: [
      {
        role: "user",
        content: userMessage
      }
    ]
  }
}];
```

---

## Prometheus 补充查询示例

在 n8n 的 HTTP Request 节点中查询 Prometheus API 获取实时指标：

```
# 查询 Pod CPU 使用率
GET http://kube-prometheus-stack-prometheus:9090/api/v1/query
参数: query=rate(container_cpu_usage_seconds_total{pod="{{ pod_name }}"}[5m])

# 查询 Pod 内存使用率
GET http://kube-prometheus-stack-prometheus:9090/api/v1/query
参数: query=container_memory_working_set_bytes{pod="{{ pod_name }}"}

# 查询 Pod 重启次数（30分钟内）
GET http://kube-prometheus-stack-prometheus:9090/api/v1/query
参数: query=increase(kube_pod_container_status_restarts_total{pod="{{ pod_name }}"}[30m])
```

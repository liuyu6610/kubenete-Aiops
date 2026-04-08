# KubeSentinel 毕业设计 — 架构分析与交付物

## 项目概述

**KubeSentinel** 是一个基于大语言模型的 Kubernetes 智能自愈与 AIOps 平台。核心使命是通过将 LLM 推理能力与 DAG 工作流编排深度融合，实现从"秒级异常发现"到"全自动修复闭环"的无人值守运维。

---

## 系统五层架构图

```mermaid
flowchart TB
    subgraph L1["前端展示层"]
        direction LR
        Vue["Vue 3 控制台"]
        Copilot["AI Copilot 副驾驶"]
        ECharts["ECharts 数据可视化"]
        WS["WebSocket 实时推送"]
    end

    subgraph L2["智能决策层 (FastAPI)"]
        direction LR
        API["API Routers"]
        LLM["LLM Service\n(GLM-5/DeepSeek)"]
        ML["AIOps ML\n(IsolationForest)"]
        DB["DatabaseService\n(PostgreSQL + Redis)"]
        PromSvc["Prometheus\nService"]
        LokiSvc["Loki\nService"]
        K8sSvc["K8s Service"]
        MCP["FastMCP Server"]
    end

    subgraph L3["工作流编排层"]
        direction LR
        N8n["n8n Webhook"]
        Switch["Switch 风险分级"]
        Notify["飞书/钉钉通知"]
        Callback["Callback 回传"]
    end

    subgraph L4["自愈执行层 (Go Operator)"]
        direction LR
        CRD["HealingRule CRD"]
        Reconcile["Reconcile 控制器"]
        Actions["8种自愈动作\n重启/扩缩/回滚/驱逐..."]
    end

    subgraph L5["可观测基础层"]
        direction LR
        Prom["Prometheus"]
        AM["Alertmanager"]
        Loki["Loki 日志"]
        Grafana["Grafana"]
        KSM["kube-state-metrics"]
        Demo["demo-app 靶机"]
    end

    L1 --> L2
    L2 --> L3
    L2 --> L4
    L5 --> L2

    Demo --> Prom
    Prom --> AM
    AM -->|"Webhook"| API
    API --> LLM
    API --> ML
    API --> DB
    K8sSvc -->|"创建 CRD"| CRD
    CRD --> Reconcile
    Reconcile --> Actions
    API --> N8n
    N8n --> Switch --> Notify
    Callback -->|"审批结果"| API

    style L1 fill:#1e293b,stroke:#6366f1,color:#f8fafc
    style L2 fill:#1e293b,stroke:#06b6d4,color:#f8fafc
    style L3 fill:#1e293b,stroke:#f59e0b,color:#f8fafc
    style L4 fill:#1e293b,stroke:#10b981,color:#f8fafc
    style L5 fill:#1e293b,stroke:#f43f5e,color:#f8fafc
```

---

## 告警自愈时序图

```mermaid
sequenceDiagram
    autonumber
    participant Prom as Prometheus
    participant AM as Alertmanager
    participant API as FastAPI 后端
    participant Redis as Redis 缓存
    participant LLM as LLM Provider
    participant DB as PostgreSQL
    participant N8n as n8n 审批流
    participant K8s as Kubernetes API
    participant Op as Go Operator

    Prom->>AM: 检测到指标异常 → Alert firing
    AM->>API: POST /api/v1/webhook/alert
    API->>Redis: 检查冷却期 (300s)
    alt 冷却期内
        API-->>AM: 跳过重复处理
    else 非冷却期
        API->>Prom: 查询窗口期 CPU/内存/网络/重启指标
        API->>API: 查询 Loki 日志上下文
        API->>LLM: 发送 告警+指标+日志 → 请求分析
        LLM-->>API: 返回 HealingDecision JSON
        API->>DB: 写入告警记录与审计日志
        alt 低风险 & 置信度>0.75
            API->>K8s: 创建 HealingRule CRD
            K8s-->>Op: Watch → Reconcile
            Op->>K8s: 执行自愈动作 (重启/扩缩/回滚)
            Op-->>API: HTTP callback 回报结果
        else 高风险 | 置信度不足
            API->>N8n: 触发审批工作流
            N8n-->>API: 人工 approve/reject
            alt 审批通过
                API->>K8s: 创建 HealingRule CRD
            end
        end
    end
```

---

## 数据模型

```mermaid
erDiagram
    ALERTS {
        int id PK
        string alertname
        string status
        string namespace
        string target
        string action
        float confidence
        string analysis
        string risk_level
        datetime created_at
    }
    AUDIT_LOGS {
        int id PK
        string title
        string description
        string operator
        string log_type
        datetime created_at
    }
    HEALING_RULES {
        string name PK
        string action
        string targetResource
        string targetNamespace
        float aiConfidence
        string phase
        string message
        datetime executionTime
    }

    ALERTS ||--o{ AUDIT_LOGS : "审计记录"
    ALERTS ||--o| HEALING_RULES : "触发 CRD"
```

---

## 项目技术栈总览

| 层级 | 技术栈 | 核心文件 |
|---|---|---|
| **前端** | Vue 3 + Element Plus + ECharts + WebSocket | [Dashboard.vue](file:///c:/Users/liudeyu/my-project/kubenete-Aiops/frontend-vue/src/views/Dashboard.vue), [AICopilot.vue](file:///c:/Users/liudeyu/my-project/kubenete-Aiops/frontend-vue/src/components/AICopilot.vue) |
| **后端** | FastAPI + asyncpg + Redis + LLM API | [main.py](file:///c:/Users/liudeyu/my-project/kubenete-Aiops/backend-python/main.py), [alerts.py](file:///c:/Users/liudeyu/my-project/kubenete-Aiops/backend-python/api/alerts.py) |
| **AI 引擎** | GLM-5/DeepSeek + IsolationForest | [llm_service.py](file:///c:/Users/liudeyu/my-project/kubenete-Aiops/backend-python/services/llm_service.py), [aiops_service.py](file:///c:/Users/liudeyu/my-project/kubenete-Aiops/backend-python/services/aiops_service.py) |
| **Operator** | Go + Kubebuilder + controller-runtime | [healingrule_controller.go](file:///c:/Users/liudeyu/my-project/kubenete-Aiops/operator-go/internal/controller/healingrule_controller.go) |
| **CRD** | HealingRule (kubesentinel.io/v1beta1) | [healingrule-crd.yaml](file:///c:/Users/liudeyu/my-project/kubenete-Aiops/k8s-manifests/kubesentinel-v2/healingrule-crd.yaml) |
| **工作流** | n8n Webhook + Switch + Callback | [approval_workflow.json](file:///c:/Users/liudeyu/my-project/kubenete-Aiops/n8n/kubesentinel_approval_workflow.json) |
| **MCP** | FastMCP Server | [mcp_server.py](file:///c:/Users/liudeyu/my-project/kubenete-Aiops/backend-python/mcp_server.py) |
| **部署** | Docker Compose + K8s Manifests | [docker-compose.yml](file:///c:/Users/liudeyu/my-project/kubenete-Aiops/docker-compose.yml) |

---

## 交付物

### PPT 文件
- 路径: [KubeSentinel-GraduationDefense.pptx](file:///c:/Users/liudeyu/my-project/kubenete-Aiops/docs/KubeSentinel-GraduationDefense.pptx)
- 页数: **14 页**
- 编码验证: ✅ 中文无乱码 (UTF-8)

### PPT 内容目录

| 页码 | 章节 | 内容 |
|:---:|---|---|
| 1 | 封面 | KubeSentinel 项目名称、副标题、答辩信息 |
| 2 | 目录 | 12 个章节的导航 |
| 3 | 研究背景与意义 | 行业痛点数据 + 研究意义 |
| 4 | 研究目的与目标 | 6 大核心目标卡片 |
| 5 | 国内外研究现状 | 对比表格 + 创新定位 |
| 6 | 关键技术分析 | 6 大技术栈详解 |
| 7 | 系统总体架构 | 五层架构分层图 |
| 8 | 核心模块设计 | 4 大核心模块详解 |
| 9 | OODA 智能闭环 | 观察-定位-决策-执行四阶段 |
| 10 | 前端可视化展示 | Dashboard/Alerts/Copilot/History |
| 11 | n8n 工作流编排 | 流程图 + 安全门控策略 |
| 12 | 混沌工程验证 | 注入工具 + 验证流程 |
| 13 | 创新点与贡献 | 5 大创新点 |
| 14 | 总结与展望 | 项目总结 + 未来方向 + Q&A |

### 生成脚本
- 路径: [create-ppt.js](file:///c:/Users/liudeyu/my-project/kubenete-Aiops/docs/create-ppt.js)
- 可通过 `node docs/create-ppt.js` 重新生成

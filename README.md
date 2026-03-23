# 🛡️ KubeSentinel: 基于大语言模型与 DAG 工作流的 Kubernetes 智能自愈 AIOps 系统

<div align="center">

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Kubernetes](https://img.shields.io/badge/Kubernetes-1.26+-326CE5?logo=kubernetes&logoColor=white)
![Prometheus](https://img.shields.io/badge/Prometheus-2.x-E6522C?logo=prometheus&logoColor=white)
![n8n](https://img.shields.io/badge/n8n-Workflow-EA4B71?logo=n8n&logoColor=white)
![LLM](https://img.shields.io/badge/LLM-DeepSeek%20%7C%20Qwen-7C3AED)
![Status](https://img.shields.io/badge/Status-Active%20Development-brightgreen)

**将 AI 大脑注入 Kubernetes 集群，实现从"被动告警"到"自主修复"的范式跃迁。**

[📖 项目背景](#-项目背景与核心痛点) · [🏗️ 系统架构](#️-系统架构) · [🚀 快速开始](#-快速开始) · [📂 目录结构](#-项目目录结构) · [🗺️ 开发路线图](#️-开发路线图)

</div>

---

## 📖 项目背景与核心痛点

### 现代云原生运维的困境

随着企业全面拥抱云原生架构，微服务系统的规模与复杂度呈指数级增长。在一个典型的生产 Kubernetes 集群中，可能同时运行着数百个 Pod，服务间的调用链路错综复杂，任何一个微小的故障都可能触发**雪崩效应**，最终演变成业务中断。

传统的运维模式面临以下根本性矛盾：

| 传统运维痛点 | 具体表现 |
|:---|:---|
| 🚨 **告警风暴** | 一个底层故障可能触发数十条关联告警，On-call 工程师疲于奔命，难以找到真正根因 |
| 🐢 **MTTR 居高不下** | 从发现告警 → 登录系统 → 排查日志 → 执行操作，往往需要 15-60 分钟甚至更长 |
| 🧠 **知识沉淀难** | 优秀工程师的运维经验难以系统化复用，高度依赖个人能力 |
| 😴 **人工值班成本** | 7×24 小时监控消耗大量人力资源，深夜告警严重影响工程师生活质量 |

### KubeSentinel 的解法

**KubeSentinel** (意为"哨兵") 是一套**轻量级、非侵入式**的 Kubernetes 智能自愈原型系统（Proof of Concept），专为解决上述痛点而生。它的核心理念是：

> **将经验丰富的 SRE 工程师的决策能力，通过大语言模型（LLM）结构化地编码进系统，并借助 n8n 工作流引擎自动执行。**

系统通过以下三个维度实现 AIOps 的真正价值：
- **📊 可观测性增强**：不仅收集指标，更将指标转化成 LLM 可理解的自然语言上下文。
- **🧠 智能决策**：LLM 扮演"超级 SRE"角色，综合分析告警历史、Pod 状态、资源使用率，给出有理有据的修复建议。
- **⚙️ 自动化执行**：n8n 将 LLM 决策翻译成具体的 Kubernetes API 调用，完成端到端闭环。

---

## 🏗️ 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        KubeSentinel 智能自愈闭环                              │
│                                                                               │
│  ┌──────────────┐    Metrics    ┌─────────────────────────────────────────┐  │
│  │              │◄──────────────│          Kubernetes Cluster              │  │
│  │  Prometheus  │               │  ┌─────────┐  ┌──────────┐  ┌───────┐  │  │
│  │              │               │  │frontend │  │  order-  │  │ redis │  │  │
│  └──────┬───────┘               │  │ (nginx) │  │ service  │  │       │  │  │
│         │ AlertRule fired       │  └─────────┘  └──────────┘  └───────┘  │  │
│         ▼                       └─────────────────────────────────────────┘  │
│  ┌──────────────┐   Webhook     ┌──────────────────────────────────────────┐ │
│  │ Alertmanager │──────────────►│              n8n Workflow Engine          │ │
│  └──────────────┘               │                                           │ │
│                                 │  [Webhook] → [Parse] → [Build Prompt]    │ │
│  ┌──────────────┐   LLM API     │       ↓                                  │ │
│  │  LLM 大脑     │◄─────────────►│  [LLM Request] → [Parse JSON Response]  │ │
│  │(Qwen/DeepSeek│               │       ↓                                  │ │
│  │   /GPT-4)   │               │  [K8s API Execute] → [Notify Feishu]     │ │
│  └──────────────┘               └──────────────────────────────────────────┘ │
│                                           │ kubectl / K8s API                 │
│  ┌──────────────┐                         ▼                                  │
│  │   Grafana    │◄────────────── K8s API Server                              │
│  │  Dashboard   │                                                             │
│  └──────────────┘                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### OODA 自愈闭环：四阶段工作流

本系统遵循军事决策理论中的 **OODA 循环（观察-定向-决策-行动）** 设计理念：

#### 1️⃣ 观察 (Observe) — 可观测性底座

- `kube-state-metrics` 持续导出 K8s 对象状态（Pod 状态、Deployment 副本数、Node 就绪状态等）
- `node-exporter` 采集宿主机 CPU、内存、磁盘、网络指标
- `Prometheus` 按配置的采集间隔（默认 15s）拉取上述指标，存储为时序数据
- `Grafana` 提供可视化仪表盘，让运维人员实时洞察集群状态

#### 2️⃣ 触发 (Orient) — 告警规则引擎

- `Prometheus` 持续评估 PromQL 告警规则（如 `container_cpu_usage_seconds_total > 0.85`）
- 当规则满足条件且持续超过 `for` 时间窗口，`Alertmanager` 生成告警
- `Alertmanager` 通过 **Webhook** 方式，将结构化 JSON 告警数据推送给 `n8n`

**告警 Payload 示例：**
```json
{
  "status": "firing",
  "labels": {
    "alertname": "PodCpuHighUsage",
    "namespace": "default",
    "pod": "order-service-7d9f8b-xxxxx",
    "severity": "critical"
  },
  "annotations": {
    "summary": "Pod CPU usage exceeded 85% for 2 minutes",
    "description": "Pod order-service CPU usage is 92.3% (threshold: 85%)"
  }
}
```

#### 3️⃣ 决策 (Decide) — 自研 AI 诊断调度后端 (Python)

- **自研调度中枢** 接收告警后，通过 Python 代码主动从 Prometheus 查询高级指标和日志。
- 将采集到的上下文信息组装到 Prompt 模板中。
- 调用大语言模型 API（支持通义千问/DeepSeek），利用模型的运维知识库进行推理。
- **严格约束输出格式**：将非结构化的文本提取转化为标准化的修复指令对象（JSON）。
- **人工干预拦截**：当 AI 的置信度低于预设阈值（例如 70%）时，挂起自动执行，推送至 **自研大屏控制台 (Vue.js)** 弹窗请求人工审批。

**LLM 输出示例：**
```json
{
  "analysis": "Pod order-service CPU持续高负载，判断为程序内存泄露或请求积压，建议滚动重启并观察",
  "confidence": 0.87,
  "action": "rolling_restart",
  "target": {
    "resource_type": "deployment",
    "name": "order-service",
    "namespace": "default"
  },
  "fallback": "scale_up",
  "notify": true
}
```

#### 4️⃣ 执行 (Act) — 自研 KubeSentinel Operator (Go)

- Python 调度中枢将决策转化为定制的 `HealingRule` (CRD) 对象或直接下发 Webhook 指令。
- **自定义 K8s Controller (Go 编写)** 监听到 CRD 变更或指令后，执行真正的 K8s 资管操作：
  - `rolling_restart` → 操作 Deployment 滚更重启
  - `scale_up` → 调整 Deployment 副本数 / 修改 HPA
  - `rollback` → 寻找上一个稳定的 ReplicaSet 并回滚
  - `cordon_node` → 将节点状态设为 SchedulingDisabled 以隔离故障源
- **全景可视**：整个自愈流程、历史日志与操作审计，均可在 **KubeSentinel 自研大屏前端 (Vue3)** 中实时查看。执行结果同时推送至飞书/钉钉。

---

## 🛠️ 技术栈选型

| 层级 | 技术 / 工具 | 版本 | 核心作用 |
|:---|:---|:---|:---|
| **核心自研引擎** | **Python (FastAPI)** | 3.10+ | AI 诊断大枢纽，全异步处理，接收告警、检索日志、组装 Prompt |
| **持久化与缓存** | **PostgreSQL & Redis** | 15+ / 7+ | 采用 asyncpg 持久化告警与审计日志；Redis 提供限流与极速缓存 |
| **自定义算子** | **Go (Kubebuilder)** | 1.20+ | `AutoHealer` Operator，原生的集群状态控制 |
| **自研可视化大屏** | **Vue 3 + Element Plus** | 3.x | 引入全局玻璃拟态与暗黑主题，提供 AI Copilot 侧边栏交互 |
| **E2E 质量守护** | **Playwright** | 1.x | 自动化冒烟测试守护 Vue 动态渲染与前端高可用性 |
| **AI 生态拓展** | **FastMCP (MCP)** | 1.x | 标准化暴露 KubeSentinel 集群诊断能力给外部通用大模型终端 |
| **监控与时序探测**| Prometheus & Sklearn | 2.x | Prometheus 时序存储，结合 IsolationForest 隔离森林进行异常预测 |
| **告警路由** | Alertmanager | 0.26+ | 告警聚合、抑制、Webhook 路由至 n8n |
| **工作流自动化** | n8n | 1.x | 零代码双向工作流，负责审批下发与企微/飞书富文本拦截触达 |
| **大语言模型大脑**| ZhipuAI (GLM-5) / DeepSeek | — | 赋予 Senior SRE Persona，遵循严密思维链进行 Tool Calling 排障 |
| **业务靶机** | Nginx + 自定义 API | — | 模拟真实微服务，作为故障注入目标 |

---

## 📂 项目目录结构 (v2.0 代码驱动版)

```text
KubeSentinel-aiops/
│
├── 📁 backend-python/                  # ✨ [新增] 自研 AI 调度决策中心 (FastAPI)
├── 📁 operator-go/                     # ✨ [新增] 自定义 K8s 集群控制算子 (Kubebuilder)
├── 📁 frontend-vue/                    # ✨ [新增] 自研可视化大屏控制台 (Vue3)
│
├── 📄 README.md                        # 项目总览与快速入门
├── 📄 CHANGELOG.md                     # 版本变更记录
├── 📄 LICENSE                          # MIT 开源协议
├── 📄 Makefile                         # 便捷命令集（make help 查看全部）
├── 📄 docker-compose.yml               # 本地开发全栈（无需 K8s 即可调试）
├── 📄 .env.example                     # 环境变量模板（复制为 .env 后填写）
├── 📄 .gitignore                       # 防止 API Key 等敏感文件被提交
│
├── 📁 docker/                          # docker-compose 配套配置文件
│   ├── prometheus/prometheus.yml       # Prometheus 本地采集配置
│   ├── alertmanager/alertmanager.yml   # Alertmanager 本地路由配置
│   └── grafana/provisioning/           # Grafana 数据源自动装配
│
├── 📁 docs/                            # 项目文档与资产
│   ├── architecture.md                 # 系统架构详细设计与数据流
│   ├── deployment-guide.md             # 分步部署指南
│   ├── demo-walkthrough.md             # 答辩演示流程（含 MTTR 对比表）
│   ├── n8n-setup-guide.md              # n8n 工作流配置操作手册
│   ├── llm-integration.md              # LLM 接入指南与 Prompt 调优记录
│   ├── thesis-data-collection.md       # 📊 论文实验数据收集模板（4 组实验）
│   └── runbooks/                       # 故障处置运维手册
│       ├── cpu-high.md                 # CPU 高负载处置指南
│       ├── crash-loop.md               # CrashLoopBackOff 处置指南
│       └── oom-memory.md               # OOM 内存溢出处置指南
│
├── 📁 k8s-manifests/                   # Kubernetes 资源清单（核心）
│
│   ├── 📁 demo-app/
│   │   └── demo-app.yaml               # frontend + order-service + redis（含 HPA + 探针）
│   ├── 📁 monitoring/
│   │   ├── alerting-rules.yaml         # PrometheusRule：8 条自定义告警规则
│   │   ├── alertmanager-config.yaml    # Alertmanager：路由与抑制配置
│   │   ├── grafana-dashboard.json      # Grafana 仪表盘骨架（6 个面板占位）
│   │   └── prometheus-additional-scrape.yaml  # 自定义采集配置模板
│   ├── 📁 n8n/
│   │   ├── n8n-deployment.yaml         # n8n Deployment + Service + ConfigMap
│   │   └── n8n-secret.yaml             # 凭据 Secret 模板（填写 REPLACE_ME）
│   └── 📁 rbac/
│       └── n8n-rbac.yaml               # n8n ServiceAccount + ClusterRole（最小权限）
│
├── 📁 n8n-workflows/                   # n8n 自动化工作流（可直接导入 GUI）
│   ├── main-healing-flow.json          # 主力自愈工作流（Webhook→LLM→K8s→通知）
│   └── notify-flow.json                # 飞书 + 钉钉通知子工作流
│
├── 📁 prompts/                         # 💡 LLM 提示词工程（核心智慧）
│   ├── system-prompt.md                # LLM 角色定义 + JSON Schema + 安全约束
│   ├── user-template.md                # 动态注入告警数据的 Prompt 模板
│   └── few-shot-examples.md            # Few-Shot 示例库（待实测后填写）
│
└── 📁 scripts/                         # 运维与测试辅助脚本
    ├── setup-cluster.sh                # 一键初始化集群环境与监控底座
    ├── chaos-inject.sh                 # 混沌工程：5 种故障注入场景
    └── validate-setup.sh               # 环境健康检查（PASS/WARN/FAIL 输出）
```

---

## 🚀 快速开始

### 前置要求

在开始之前，请确保你的环境已安装以下工具：

```bash
# 验证工具安装
kubectl version --client   # >= 1.26
helm version               # >= 3.10
docker version             # >= 20.x（如使用 Minikube）

# 可选：Minikube（本地开发）
minikube version
```

### Step 1：启动 Kubernetes 集群

```bash
# 方式 A：使用 Minikube（推荐本地开发）
minikube start --memory=8192 --cpus=4 --driver=docker

# 方式 B：使用 K3s（推荐云服务器部署）
curl -sfL https://get.k3s.io | sh -
```

### Step 2：一键初始化监控底座

```bash
# 执行初始化脚本：创建命名空间 + 部署 kube-prometheus-stack + n8n
chmod +x scripts/setup-cluster.sh
./scripts/setup-cluster.sh
```

### Step 3：部署微服务靶机

```bash
# 部署 demo-app（frontend + order-service + redis）
kubectl apply -f k8s-manifests/demo-app/demo-app.yaml

# 验证 Pod 状态
kubectl get pods -n default -w

# 访问前端（如使用 Minikube）
minikube service frontend-service --url
```

### Step 4：配置 n8n 工作流

```bash
# 获取 n8n 访问地址
kubectl get svc -n monitoring | grep n8n

# 在浏览器打开 n8n，导入工作流
# 菜单 → Import → 选择 n8n-workflows/main-healing-flow.json
```

### Step 5：触发故障演示

```bash
# 注入 CPU 压力故障（触发自愈流程）
chmod +x scripts/chaos-inject.sh
./scripts/chaos-inject.sh --target order-service --type cpu-stress --duration 120
```

---

## 🗺️ 开发路线图

### ✅ 第一阶段：基础设施底座重构

- [x] 项目结构初始化与 Python FastAPI 全异步重构
- [x] 基于 PostgreSQL (asyncpg) 与 Redis 的企业级存储解耦
- [x] Vue3 前端 UI 焕新（暗黑玻璃拟态美学设计）

### ✅ 第二阶段：GLM-5 智能与 ML 预测联调

- [x] 引入 IsolationForest (隔离森林) 进行多维指标主动异常预测
- [x] GLM-5 深度 Tool Calling 接入 (原生抓取 K8s / Prometheus 数据)
- [x] 注入 Senior SRE 角色提示词与推断式链条 (Chain of Thought) 排障逻辑

### ✅ 第三阶段：n8n 自动化与质量守护

- [x] 研发双向 n8n Webhook HTTP 回调路由机制与原生 JSON 工作流脚手架
- [x] 实现并部署飞书/Slack 的人工审批与通知卡片流
- [x] 基于 Playwright 实现 Dashboard 核心组件与智能侧边栏的 E2E 自动化探活测试

### ✅ 第四阶段：全球化 AI 生态拓展与交付

- [x] 引入 FastMCP 协议，实现 `mcp_server.py` 将自愈集群诊断能力暴露给 Cursor 等通用端
- [x] 端到端故障注入 (OOM/CPU) 触发 GLM-5 智能自愈链路测试闭环
- [x] KubeSentinel 核心架构文档、里程碑及演进状态 100% 对齐更新

---

## 🧪 故障场景覆盖

| 故障类型 | 触发方式 | LLM 预期动作 | K8s 执行操作 |
|:---|:---|:---|:---|
| Pod CPU 满载 | stress-ng 注入 | rolling_restart | kubectl rollout restart |
| Pod 内存溢出 (OOM) | 内存压力注入 | scale_up | 增加 replicas + 调整 limits |
| Pod 崩溃循环 (CrashLoopBackOff) | 错误配置注入 | investigate + rollback | kubectl rollout undo |
| 服务不可用 (0/1 Ready) | 删除 Pod | scale_up | 增加副本数 |
| 节点资源耗尽 | node stress | cordon_node | kubectl cordon + 调度迁移 |

---

## 🔐 安全说明

> ⚠️ **重要提示**：本项目为毕业设计 PoC 原型，在安全性上进行了适当简化。**请勿直接用于生产环境。**

生产环境使用前需要考虑：
- 使用 Kubernetes Secrets 管理 LLM API Key
- 为 n8n 配置最小权限 RBAC（限制可操作的命名空间和资源类型）
- 对 n8n Webhook 端点启用认证（HMAC 签名验证）
- 对 LLM 输出进行人工确认的 Approval 流程（Human-in-the-loop）

---

## 📜 许可证

本项目采用 [MIT License](LICENSE) 开源协议。

---

## 🙏 致谢

- [kube-prometheus-stack](https://github.com/prometheus-community/helm-charts) — 开箱即用的监控底座
- [n8n](https://n8n.io/) — 强大的低代码工作流引擎
- [阿里云通义千问](https://www.aliyun.com/product/bailian) / [DeepSeek](https://www.deepseek.com/) — 高性价比的 LLM API

---

<div align="center">

**🛡️ KubeSentinel — 让 Kubernetes 集群拥有自我修复的能力**

Made with ❤️ for Graduation Thesis 2025

</div>

### 一、 核心开发清单（你要写什么代码/配什么东西）

这个项目虽然借力了开源工具和现成 API，但核心的**“胶水层”和“业务逻辑”**需要你亲自动手：

1. **基础设施编排文件 (YAML)**：

- 微服务 Demo 的部署文件（Deployment, Service, Ingress）。
- 监控栈的自定义配置（Prometheus 采集规则、告警规则文件 `alerting_rules.yaml`）。

2. **大模型提示词模板 (Prompt Engineering)**：

- 你需要调优出 3-5 个极其稳定的 Prompt，确保模型每次都能根据告警信息输出标准化的 JSON（例如 `{"action": "restart", "pod_name": "cart-service"}`），而不是一堆废话。

3. **n8n 工作流编排 (JSON/可视化界面)**：

- n8n 的核心是拖拽节点，但你需要编写 Webhook 解析逻辑、HTTP Request 节点的调用参数（对接大模型 API）以及 K8s API 的认证与调用。

4. **故障注入脚本 (Shell/Python)**：

- 用于答辩演示的脚本，一键制造 CPU 满载或 Pod 挂掉的假象，以触发自愈流程。

---

### 二、 开发计划分解

采用敏捷思路，先跑通最简单的一条线，再慢慢丰富。

- **第一阶段：底座搭建 (基础环境)**
- 准备一个 K8s 集群（本地 Minikube/K3s 或云上轻量级集群均可）。
- 部署一套简单的微服务 Demo（推荐 Google 的 `microservices-demo` 或者是几个简单的 SpringBoot 互相调用）。
- 部署 `kube-prometheus-stack`，确保能在 Grafana 看到数据。

- **第二阶段：告警与“大脑”联调 (核心逻辑)**
- 在 Prometheus 中配置一条测试告警（例如：某个 Pod CPU 使用率 > 80%）。
- 编写 Python/Node.js 脚本或直接使用 Postman，测试大模型 API（如通义千问/DeepSeek），输入告警 JSON，调整 Prompt 直到它能输出正确的修复建议。

- **第三阶段：n8n 自动化“双手”接入 (流程串联)**
- 部署 n8n（可以使用 Docker 快速起一个）。
- 在 n8n 配置工作流：`Webhook (接收告警) -> HTTP Request (请求大模型) -> 逻辑判断 (解析模型输出的 JSON) -> HTTP Request (调用 K8s API 执行重启/扩容)`。

- **第四阶段：闭环测试与文档完善 (答辩准备)**
- 运行故障注入脚本，观察全链路：故障发生 -> 触发告警 -> n8n 接收 -> 模型决策 -> n8n 执行 -> 故障恢复。
- 记录耗时、成功率等数据，填入论文。整理代码仓库。

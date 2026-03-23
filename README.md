# 🛡️ KubeSentinel: 基于大模型的下一代 Kubernetes 智能自愈与 AIOps 平台 🚀

> [!NOTE] 💡 **核心使命**
> KubeSentinel 致力于终结现代云原生集群中无休止的“告警风暴”，通过将 **大语言模型 (LLM)** 的推理能力与 **DAG 工作流 (n8n)** 编排深度融合，打造从“秒级异常发现”到“全自动修复闭环”的无人值守运维基石。

---

## 📖 诞生背景与痛点 (Why KubeSentinel?)

随着企业微服务架构的指数级膨胀，现代 SRE（站点可靠性工程师）面临着前所未有的严峻挑战：
1. 🚨 **告警风暴与上下文割裂**：一个底层网络抖动可能触发上百条连环报错。工程师必须在 Grafana、Kibana、Terminal 之间疯狂切换，以寻找蛛丝马迹。
2. 🐢 **MTTR 居高不下**：由于排查路径极度依赖个人经验，从发现问题到敲定修复命令的平均修复时间 (MTTR) 往往超过 30 分钟。
3. 📉 **隐性性能衰退难以察觉**：传统的静态阈值告警（如 CPU > 80%）无法捕捉极其缓慢的内存泄漏或网络 I/O 异常波动。

**KubeSentinel 就是为此而生！** 它是将顶级 SRE 排障脑图（Playbooks）进行了 100% 数字化与智能化的超级辅助大脑。它可以像一位拥有 10 年经验的架构师一样，在告警发生的第一秒，从海量时序数据与容器日志中精准剥离出真正的诱因！

---

## ✨ 核心特性大赏 🌟 (Core Features)

为了彻底根治上述结症，KubeSentinel 将最新技术范式武装到了牙齿，为您提供降维打击般的集群掌控力：

### 🧠 1. 大模型驱动的深度根因分析 (LLM RCA Engine)
原生集成 **GLM-5 / DeepSeek** 等顶尖大语言模型，并赋予其专门调优的 **"Senior SRE"** 角色身份。
* **原生推断式链条 (Chain-of-Thought)**：大模型绝不会盲目瞎编，它会通过后端的 `Tool Calling`（原生工具调用）机制，自主决定是否需要先拉取 Pod 日志、调取 K8s Events、或是分析 Prometheus，反复循环论证直到揪出真正的崩溃元凶！

### 🔮 2. 主动式机器学习异常预测 (ML Anomaly Detection)
不再被动等待那根迟到的报警红线！系统后端内置了基于 `scikit-learn` 的 **IsolationForest (隔离森林)** 算法。
* **时序洞察**：24 小时不断采集 Prometheus 的多维指标（CPU/内存/网络流）进行高维聚类，主动嗅觉敏锐地捕获隐藏在暗处的微小降级（Degradation），在真正的雪崩前完成系统告警！🌲

### ⚡ 3. 零代码 DAG 自动治愈工作流 (Zero-code Healing)
* **n8n 深度双向联动**：复杂的运维修复策略（如降级、回滚、切流）再也不需要用 Python 硬编码拉跨实现！通过系统导出的 n8n JSON 配置，您可以直接在可视化界面拖拽生成坚若磐石的审批流。
* **飞书/Slack 企微通知审批**：遇到敏感环境的高危重载（例如：强制逐出整个 Node 节点）？KubeSentinel 会自动触发互动的卡片推送到您的手机上，只需高管团队点击“授权 (Approve)”，余下的一切交由 KubeSentinel 底层的 Go 算子自动执行！📱

### 🎨 4. 超感官的异域风控制大屏与 AI Copilot (Vue 3 Glassmorphism)
完全打破传统监控后台“枯燥、死板、反直觉”的刻板印象：
* 采用最前沿的 **暗黑玻璃拟态 (Glassmorphism)** 顶层 UI 美学。这套充满动态光泽与极客科技感的大屏能够将您集群中错综复杂的告警吞吐速率以最具张力的数据可视化方式呈现出来。
* **桌面级悬挂 AI Copilot**：右侧常驻的超级智能副驾驶助手！随时用自然语言闲聊提问（如：“*帮我查一下 default 名字空间下为什么订单服务挂了？*”），它将即刻接管您的屏幕视角，把有理有据的诊断书与代码级修复方案通过流式打字效果霸气呈现在您的眼前。💬

### 🌐 5. MCP 协议全网络节点直通 (FastMCP Integration)
* **AI 代理新生态接口**：内置最高级的 **FastMCP Server**！您可以直接使您的本地 Cursor 编辑器、或者是 Claude Desktop 客户端，无缝接入此监控节点！让它们直接直接具备随时洞悉和修复 Kubernetes 目标集群的能力，扩展了无穷的本地自动化空间！🚀

### 🏎️ 6. 极速全异步高并发骨架 (Asynchronous Backend)
* 整个核心枢纽放弃同步架构，全栈基于 **FastAPI + asyncpg (持久化 PostgreSQL) + redis.asyncio** 构建。这种彻底的非阻塞循环不仅实现了海量 OOM 日志的风暴过滤，更确保了即使每秒万级错误上报，也能将预冷判定与限流过滤稳定控制在毫秒级别！🌊

---

## 🏗️ 全景运转：现代 OODA 指挥环 🗺️

KubeSentinel 将经典的博弈学和军事指挥理论 **OODA 循环 (Observe-Orient-Decide-Act)**，重构为了机器微服务的自动化闭环：

1. 📡 **观察神经网 (Observe)**：以 `kube-state-metrics` 与 `node-exporter` 作为遍布集群的物理探针，每隔数秒就将集群深处的上百种遥测体征数据喂入 Prometheus 时序库。
2. 🎯 **定位哨兵站 (Orient)**：Alertmanager 或是内置的 ML 孤立森林算法模型一旦察觉异动，即刻将指标异变提取过滤，封装为标注高亮权重的标准化 Webhook JSON 刺入 Python 后端的高并发 API 路由矩阵中。
3. 🤔 **参谋决策层 (Decide)**：后端 AI 决策中枢立刻组装全景历史档案，并唤醒大模型进入冥想。大模型借助 `k8s_service` 等工具作为它的眼睛和触须，主动深入异常容器挖掘证据链，并输出诸如“*这属于 OOMKilled，必须将 resources.limits 上浮至 2Gi 并执行滚动重启*”的带有明确成功置信度的执行 JSON。
4. 🛠️ **特种执行队 (Act)**：一切决断将立刻下发落成为一项专属的 Kubernetes 自定义资源 `HealingRule` (CRD)。一直隐藏在节点深处的 **Go 语言级别 Kubebuilder Operator (控制算子)** 接收到 API Server 的变更信号，如臂使指般以极低的系统开销向目标 Pod 实施精准的外科手术式物理修复动作！

---

## 📂 极尽严谨的大型工程结构 📦

```text
KubeSentinel-aiops/
├── 📁 backend-python/                  # ✨ 脑干中枢: FastAPI 全异步 AI 调度中心 + MCP Server 🧠
├── 📁 frontend-vue/                    # ✨ 颜值担当: Vue 3 + Element Plus 构建的暗黑玻璃大屏 🎨
├── 📁 operator-go/                     # ✨ 物理抓手: Kubernetes Operator 算子核心 (Go 语言) 🛠️
├── 📁 k8s-manifests/                   # 📜 K8s 资源清单: 靶机部署、监控基建部署与 CRD 注册表
├── 📁 n8n/                             # 🔗 自动化大脑: 导出的免代码审批流 JSON 配置模板
├── 📁 tests/                           # 🧪 质量堡垒: 基于 Playwright 的 Web 端到端高可用守护
├── 📁 docs/                            # 📚 知识宝库: 系统架构推演与研发过程日志
├── 📁 docker/                          # 🐳 丝滑体验: 本地极速拉起的全栈 Compose 开发基建
├── 📁 prompts/                         # 💡 AI 灵魂: 使大模型化身 Senior SRE 的顶级提示词指令集
└── 📁 scripts/                         # ⚙️ 演练靶机: 混沌工程 (CPU打满/内存泄漏) 注入器
```

---

## 🏁 五步见证未来：从零快速起航 🛳️

### 📌 运行环境要求

- ☸️ Kubernetes 1.26+ 集群 (推荐本地使用 Minikube 或简易云服务器版 K3s)
- 🪖 Helm 3.10+
- 🐍 Python 3.10+ & 🟢 Node.js 18+ (若是希望跑在开发热重载模式下)

### 🛠️ 一键点火部署圣经

> [!IMPORTANT] ⚠️ **极度警告：密钥配置优先**
> 核心推理引擎强依赖商业顶级大语言模型 API。在开启整个系统前，请务必将源码根目录下的 `.env.example` 唤醒并重命名为 `.env`，并在其中认真填入您专属的 `ZHIPUAI_API_KEY` 等关键通信凭证。🔑

1. **🏰 组装坚不可摧的监控底盘**  
   只需一条脚本，我们将自动在集群为您掘地三尺开辟基准 Namespace，并宏伟地盖下监控巨无霸 `kube-prometheus-stack`：
   ```bash
   chmod +x scripts/setup-cluster.sh
   ./scripts/setup-cluster.sh
   ```

2. **💣 布置您的第一块演练靶场**  
   这套容器存在刻意漏洞的残次品 `order-service`，它就是我们稍后要实施降维打击与自愈施救的重症病人：
   ```bash
   kubectl apply -f k8s-manifests/demo-app/demo-app.yaml
   ```

3. **🗄️ 点亮高可用持久化存储层**  
   利用 Compose 技术一键编排并挂载系统级依赖包——PostgreSQL 企业级数据仓库与 Redis 高速缓存列阵：
   ```bash
   docker-compose up -d
   ```

4. **🧠 唤醒核心 Python AI 大脑**
   ```bash
   cd backend-python
   pip install -r requirements.txt
   uvicorn main:app --reload --port 8000
   ```

5. **🖥️ 视界展开：启动沉浸式前端**
   ```bash
   cd frontend-vue
   npm install
   npm run dev
   ```

---

## 🌪️ 混沌演练实战：绝地求生与自动逢源 🛡️

所有骨架已经拼装就位！现在让我们向其中注入一些“绝望的错误”，亲自见证 AI 是如何接管一切逆风翻盘的！只需执行我们准备的混沌压测利器：

```bash
./scripts/chaos-inject.sh --target order-service --type cpu-stress --duration 120
```

> [!TIP] 🎯 **终极黑客式浪漫与隐藏彩蛋**
> 代码执行数秒后，伴随着 `stress-ng` 的疯狂噬咬，您的玻璃拟态大屏将即刻跳红！全屏警报开始闪烁！
> 此时此刻，请您稳如泰山地唤出位于界面右边缘那把悬浮已久的 **AI Copilot**，用一种指挥官的骄傲口吻向其中键入：“*这个订单服务怎么突然告警了？给我个解释，并把局势控制住。*”
> 接下来，请把双手离开键盘。欣赏大模型在后台飞速拆卸出数十行关键报错信息作为推理食粮，以光速完成一场逻辑辩证推演，并将这份带着人类智慧结晶与 K8s kubectl 热修复原语的最终审判书，“锵”地一声递送在您的视野正中吧！🤯

# Changelog

所有版本的重要变更记录。格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)。

---

## [Unreleased] - 开发中

### 待完成（第四阶段）
- [ ] 端到端故障注入 → 自愈全链路测试
- [ ] MTTR 实验数据收集（见 docs/thesis-data-collection.md）
- [ ] 答辩演示视频录制
- [ ] 论文数据整理

---

## [0.3.0] - Phase 3 核心功能完善 - 2026-03-22

### Backend Python 增强
- **`llm_service.py`** — 完全重写：对齐 `system-prompt.md` JSON Schema，支持 DashScope + OpenAI 兼容 API（DeepSeek/GPT-4），3次重试逻辑，鲁棒 JSON 提取（正则+括号匹配），失败安全回退
- **`models.py`** — 扩展 `HealingDecision` 模型：增加 `root_cause`、`risk_level`、`human_approval_required`、`params`、`summary_for_notification` 字段；新增 `StatsResponse` 模型
- **`config.py`** — 增加 LLM Provider 切换、OpenAI 配置、冷却时间/重试次数/审批配置
- **`notification_service.py`** — 新增飞书富文本卡片通知 + 钉钉 Markdown 通知（自愈通知 + 审批通知）
- **`prometheus_service.py`** — 增加 `is_healthy()`/`get_pod_status()`/`get_cluster_stats()` 方法
- **`db_service.py`** — 增加统计方法（今日告警数、自愈次数、成功率、动作分布饼图、冷却检查）
- **`main.py`** — 增加 `GET /api/v1/stats`（Dashboard 统计）、`POST /api/v1/test-alert`（本地调试）、`GET /api/v1/cluster/stats`（Prometheus 集群数据）；集成冷却机制和通知服务；增强 `/healthz`

### Go Operator 增强
- **`healingrule_controller.go`** — 新增 5 种自愈动作：`rollback`（ReplicaSet 历史回滚）、`delete_pod`、`scale_down`、`adjust_hpa`、`evict_pods`；增加执行结果回调 Python 后端
- **`healingrule-crd.yaml`** — CRD action enum 扩展至 8 种

### Frontend Vue 增强
- **`Dashboard.vue`** — 接入真实 `/api/v1/stats` API；集成 ECharts：告警趋势折线图 + 故障原因分布饼图；4 统计卡片（告警数/自愈数/成功率/待审批）；新增调试工具面板（发送模拟告警）
- **`Alerts.vue`** — 增加状态筛选下拉框；相对时间+tooltip；风险等级标签；动作中文标签；详情查看；`el-descriptions` 审批弹窗布局
- **`History.vue`** — 增加加载/空状态；时间格式化；类型标签；记录计数
- **`MainLayout.vue`** — 实时后端健康检测（定时 ping `/healthz`）；Engine Online/Offline 指示器；LLM Provider 信息；侧边栏版本信息
- **`kubesentinel.js`** — 增加 `getStats()`/`getClusterStats()`/`healthCheck()`/`sendTestAlert()` 方法；响应错误拦截器
- **`main.js`** — 注册 vue-echarts（树摇 ECharts 组件）；启用 Pinia 状态管理

### Docker & 配置
- **`docker-compose.yml`** — 新增 Loki 日志聚合容器
- **`alertmanager.yml`** — 重写：主告警路由到 Python 后端；保留 n8n 次要路由；增加告警抑制规则

---

## [0.2.0] - Phase 2 骨架 - 2026-03-11

### 新增
- `.env.example` — 所有环境变量配置模板
- `.gitignore` — 防止密钥提交
- `Makefile` — 20+ 便捷项目管理命令
- `docker-compose.yml` — 本地开发全栈（n8n + Prometheus + Grafana + Alertmanager + Redis）
- `docker/` — Docker Compose 配套配置文件
- `k8s-manifests/n8n/n8n-deployment.yaml` — 从 Secret 读取凭据的完整 n8n 部署
- `k8s-manifests/n8n/n8n-secret.yaml` — 凭据 Secret 模板
- `k8s-manifests/monitoring/grafana-dashboard.json` — 仪表盘骨架（6个面板）
- `k8s-manifests/monitoring/prometheus-additional-scrape.yaml` — 采集配置模板
- `scripts/validate-setup.sh` — 环境健康检查脚本
- `docs/llm-integration.md` — LLM 接入指南骨架
- `docs/n8n-setup-guide.md` — n8n 配置操作指南
- `docs/thesis-data-collection.md` — 论文实验数据收集模板
- `docs/runbooks/cpu-high.md` — CPU 高负载运维手册
- `docs/runbooks/crash-loop.md` — 崩溃循环运维手册
- `docs/runbooks/oom-memory.md` — OOM 内存溢出运维手册
- `prompts/few-shot-examples.md` — LLM Few-Shot 示例库骨架
- `LICENSE` — MIT 开源协议

---

## [0.1.0] - Phase 1 基础骨架 - 2026-03-11

### 新增
- `README.md` — 超级扩展（280+ 行），含架构图/技术栈/路线图
- `docs/architecture.md` — 系统架构详细设计
- `docs/deployment-guide.md` — 详细部署指南
- `docs/demo-walkthrough.md` — 答辩演示流程脚本（含 MTTR 对比表）
- `k8s-manifests/demo-app/demo-app.yaml` — 三微服务靶机（含 resources + probes + HPA）
- `k8s-manifests/monitoring/alerting-rules.yaml` — 8 条 Prometheus 告警规则
- `k8s-manifests/monitoring/alertmanager-config.yaml` — 告警路由与抑制配置
- `k8s-manifests/rbac/n8n-rbac.yaml` — 最小权限 RBAC 配置
- `n8n-workflows/main-healing-flow.json` — 主力自愈工作流（可直接导入 n8n）
- `n8n-workflows/notify-flow.json` — 飞书+钉钉通知子工作流
- `prompts/system-prompt.md` — LLM 系统提示词（含 JSON Schema 约束和安全阈值）
- `prompts/user-template.md` — 告警数据注入模板（含 n8n 代码示例）
- `scripts/setup-cluster.sh` — 一键初始化监控底座
- `scripts/chaos-inject.sh` — 5 种故障注入场景

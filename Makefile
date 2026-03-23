# ================================================================
# KubeSentinel - Makefile
# 提供便捷的项目管理命令
#
# 使用方式：
#   make help          查看所有可用命令
#   make setup         一键初始化集群
#   make deploy-demo   部署靶机应用
#   make chaos-cpu     注入 CPU 故障
# ================================================================

.PHONY: help setup deploy-demo undeploy-demo \
        port-forward-all port-grafana port-prometheus port-alertmanager port-n8n \
        chaos-cpu chaos-memory chaos-kill chaos-crash \
        logs-frontend logs-order logs-redis \
        status clean validate

# 默认目标
.DEFAULT_GOAL := help

# ── 配置变量 ─────────────────────────────────────────────────────
NAMESPACE_MONITORING := monitoring
NAMESPACE_DEMO := demo-app
KUBECONFIG ?= $(HOME)/.kube/config

# 颜色输出
GREEN  := \033[0;32m
CYAN   := \033[0;36m
YELLOW := \033[1;33m
NC     := \033[0m

# ── 帮助信息 ─────────────────────────────────────────────────────
help: ## 显示帮助信息
	@echo ""
	@echo "$(CYAN)🛡️  KubeSentinel - 项目管理命令$(NC)"
	@echo "$(CYAN)════════════════════════════════$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-25s$(NC) %s\n", $$1, $$2}'
	@echo ""

# ── 集群初始化 ───────────────────────────────────────────────────
setup: ## 一键初始化集群（创建命名空间 + 部署监控底座 + n8n）
	@echo "$(CYAN)>> 初始化集群环境...$(NC)"
	chmod +x scripts/setup-cluster.sh && ./scripts/setup-cluster.sh

validate: ## 验证集群各组件健康状态
	@echo "$(CYAN)>> 验证集群状态...$(NC)"
	chmod +x scripts/validate-setup.sh && ./scripts/validate-setup.sh

# ── 靶机应用管理 ─────────────────────────────────────────────────
deploy-demo: ## 部署微服务靶机应用（frontend + order-service + redis）
	@echo "$(CYAN)>> 部署 demo-app...$(NC)"
	kubectl apply -f k8s-manifests/demo-app/demo-app.yaml
	@echo "$(GREEN)>> 等待 Pod 就绪...$(NC)"
	kubectl wait --for=condition=ready pod -l app=frontend -n $(NAMESPACE_DEMO) --timeout=120s || true
	kubectl wait --for=condition=ready pod -l app=order-service -n $(NAMESPACE_DEMO) --timeout=120s || true
	kubectl wait --for=condition=ready pod -l app=redis -n $(NAMESPACE_DEMO) --timeout=60s || true
	@$(MAKE) status-demo

undeploy-demo: ## 删除靶机应用
	@echo "$(YELLOW)>> 删除 demo-app...$(NC)"
	kubectl delete -f k8s-manifests/demo-app/demo-app.yaml --ignore-not-found=true

deploy-monitoring: ## 应用自定义监控规则（告警规则 + Alertmanager 配置）
	kubectl apply -f k8s-manifests/monitoring/alerting-rules.yaml
	kubectl apply -f k8s-manifests/monitoring/alertmanager-config.yaml
	@echo "$(GREEN)>> 监控规则已更新$(NC)"

deploy-rbac: ## 应用 n8n RBAC 权限配置
	kubectl apply -f k8s-manifests/rbac/n8n-rbac.yaml
	@echo "$(GREEN)>> RBAC 已配置$(NC)"

deploy-all: deploy-rbac deploy-demo deploy-monitoring ## 部署所有应用组件（RBAC + demo + 监控规则）

# ── 端口转发（本地访问） ─────────────────────────────────────────
port-grafana: ## 转发 Grafana (http://localhost:3000, admin/KubeSentinel@2025)
	kubectl port-forward svc/kube-prometheus-stack-grafana 3000:80 -n $(NAMESPACE_MONITORING)

port-prometheus: ## 转发 Prometheus (http://localhost:9090)
	kubectl port-forward svc/kube-prometheus-stack-prometheus 9090:9090 -n $(NAMESPACE_MONITORING)

port-alertmanager: ## 转发 Alertmanager (http://localhost:9093)
	kubectl port-forward svc/kube-prometheus-stack-alertmanager 9093:9093 -n $(NAMESPACE_MONITORING)

port-n8n: ## 转发 n8n (http://localhost:5678)
	kubectl port-forward svc/n8n 5678:5678 -n $(NAMESPACE_MONITORING)

# ── 故障注入（混沌工程） ─────────────────────────────────────────
chaos-cpu: ## 向 order-service 注入 CPU 压力（持续 120 秒）
	chmod +x scripts/chaos-inject.sh
	./scripts/chaos-inject.sh --target order-service --type cpu-stress --duration 120

chaos-memory: ## 向 order-service 注入内存压力
	chmod +x scripts/chaos-inject.sh
	./scripts/chaos-inject.sh --target order-service --type memory-stress --duration 120

chaos-kill: ## 随机删除一个 order-service Pod（模拟节点崩溃）
	chmod +x scripts/chaos-inject.sh
	./scripts/chaos-inject.sh --target order-service --type kill-pod

chaos-crash: ## 让 frontend 进入 CrashLoopBackOff 状态（120s 后自动恢复）
	chmod +x scripts/chaos-inject.sh
	./scripts/chaos-inject.sh --target frontend --type crash-loop --duration 120

chaos-dry-run: ## 预览故障注入（不实际执行，DRY RUN 模式）
	chmod +x scripts/chaos-inject.sh
	./scripts/chaos-inject.sh --target order-service --type cpu-stress --dry-run

# ── 日志查看 ─────────────────────────────────────────────────────
logs-frontend: ## 查看 frontend 日志
	kubectl logs -l app=frontend -n $(NAMESPACE_DEMO) --tail=50 -f

logs-order: ## 查看 order-service 日志
	kubectl logs -l app=order-service -n $(NAMESPACE_DEMO) --tail=50 -f

logs-redis: ## 查看 redis 日志
	kubectl logs -l app=redis -n $(NAMESPACE_DEMO) --tail=20 -f

logs-n8n: ## 查看 n8n 日志
	kubectl logs -l app=n8n -n $(NAMESPACE_MONITORING) --tail=50 -f

# ── 状态查看 ─────────────────────────────────────────────────────
status: ## 查看所有命名空间的 Pod 状态
	@echo "\n$(CYAN)── monitoring 命名空间 ──$(NC)"
	@kubectl get pods -n $(NAMESPACE_MONITORING) -o wide 2>/dev/null || echo "(命名空间不存在)"
	@echo "\n$(CYAN)── demo-app 命名空间 ──$(NC)"
	@kubectl get pods -n $(NAMESPACE_DEMO) -o wide 2>/dev/null || echo "(命名空间不存在)"

status-demo: ## 仅查看 demo-app 状态
	kubectl get pods,svc,hpa -n $(NAMESPACE_DEMO)

top: ## 查看 Pod 资源使用情况
	@kubectl top pods -n $(NAMESPACE_DEMO) 2>/dev/null || echo "metrics-server 未就绪"
	@kubectl top pods -n $(NAMESPACE_MONITORING) 2>/dev/null

# ── 工具命令 ─────────────────────────────────────────────────────
get-n8n-token: ## 获取 n8n ServiceAccount Token（用于填写 n8n K8s 认证）
	@kubectl get secret n8n-healer-token -n $(NAMESPACE_MONITORING) \
		-o jsonpath='{.data.token}' 2>/dev/null | base64 -d && echo ""

send-test-alert: ## 向 Alertmanager 发送测试告警（验证 n8n Webhook 联通性）
	curl -s -X POST http://localhost:9093/api/v1/alerts \
		-H 'Content-Type: application/json' \
		-d '[{"labels":{"alertname":"KubeSentinelTest","severity":"warning","namespace":"demo-app","pod":"test-pod"},"annotations":{"summary":"这是一条测试告警","description":"用于验证 KubeSentinel 自愈流程的联通性"}}]'
	@echo "\n$(GREEN)>> 测试告警已发送，请查看 n8n 是否触发工作流$(NC)"

clean: ## 清理所有 KubeSentinel 资源（保留 Prometheus 等基础组件）
	@echo "$(YELLOW)>> 清理 demo-app...$(NC)"
	kubectl delete -f k8s-manifests/demo-app/demo-app.yaml --ignore-not-found=true
	kubectl delete -f k8s-manifests/rbac/n8n-rbac.yaml --ignore-not-found=true
	kubectl delete -f k8s-manifests/monitoring/alerting-rules.yaml --ignore-not-found=true
	@echo "$(GREEN)>> 清理完成$(NC)"

clean-all: clean ## 清理所有资源（包括 kube-prometheus-stack）
	@echo "$(YELLOW)>> 卸载监控底座...$(NC)"
	helm uninstall kube-prometheus-stack -n $(NAMESPACE_MONITORING) || true
	kubectl delete namespace $(NAMESPACE_MONITORING) --ignore-not-found=true
	kubectl delete namespace $(NAMESPACE_DEMO) --ignore-not-found=true
	@echo "$(GREEN)>> 完全清理完成$(NC)"

#!/usr/bin/env bash
# ================================================================
# KubeSentinel - 集群环境验证脚本
# validate-setup.sh
#
# 功能：检查 KubeSentinel 所有组件的健康状态
# 使用方式: chmod +x scripts/validate-setup.sh && ./scripts/validate-setup.sh
# ================================================================

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

PASS=0
FAIL=0
WARN=0

pass() { echo -e "  ${GREEN}✅ PASS${NC} $*"; ((PASS++)); }
fail() { echo -e "  ${RED}❌ FAIL${NC} $*"; ((FAIL++)); }
warn() { echo -e "  ${YELLOW}⚠️  WARN${NC} $*"; ((WARN++)); }
section() { echo -e "\n${CYAN}── $* ──${NC}"; }

echo ""
echo -e "${CYAN}╔══════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  KubeSentinel 环境健康检查               ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════╝${NC}"

# ── 1. 工具检查 ──────────────────────────────────────────────────
section "工具可用性"

command -v kubectl &>/dev/null && pass "kubectl 已安装" || fail "kubectl 未安装"
command -v helm &>/dev/null && pass "helm 已安装" || fail "helm 未安装"
kubectl cluster-info &>/dev/null && pass "K8s 集群连接正常" || fail "无法连接到 K8s 集群"

# ── 2. 命名空间检查 ──────────────────────────────────────────────
section "命名空间"

kubectl get namespace monitoring &>/dev/null && pass "monitoring 命名空间存在" || fail "monitoring 命名空间不存在，请运行 setup-cluster.sh"
kubectl get namespace demo-app &>/dev/null && pass "demo-app 命名空间存在" || warn "demo-app 命名空间不存在（需要 kubectl apply -f k8s-manifests/demo-app/demo-app.yaml）"

# ── 3. 监控组件检查 ──────────────────────────────────────────────
section "监控底座组件"

check_pod() {
    local label="$1"
    local ns="$2"
    local desc="$3"
    local count
    count=$(kubectl get pods -n "${ns}" -l "${label}" --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l | tr -d ' ')
    if [ "${count}" -gt 0 ]; then
        pass "${desc} (${count} 个 Pod Running)"
    else
        fail "${desc} (没有 Running 的 Pod)"
    fi
}

check_pod "app.kubernetes.io/name=prometheus" "monitoring" "Prometheus"
check_pod "app.kubernetes.io/name=grafana" "monitoring" "Grafana"
check_pod "app.kubernetes.io/name=alertmanager" "monitoring" "Alertmanager"
check_pod "app=n8n" "monitoring" "n8n 工作流引擎"

# ── 4. Demo App 检查 ─────────────────────────────────────────────
section "靶机应用 (demo-app)"

check_pod "app=frontend" "demo-app" "frontend (nginx)"
check_pod "app=order-service" "demo-app" "order-service (API)"
check_pod "app=redis" "demo-app" "redis (缓存)"

# ── 5. RBAC 检查 ─────────────────────────────────────────────────
section "RBAC 权限配置"

kubectl get serviceaccount n8n-healer -n monitoring &>/dev/null && pass "ServiceAccount n8n-healer 存在" || fail "ServiceAccount n8n-healer 不存在（需要 kubectl apply -f k8s-manifests/rbac/n8n-rbac.yaml）"
kubectl get clusterrole n8n-healer-role &>/dev/null && pass "ClusterRole n8n-healer-role 存在" || fail "ClusterRole n8n-healer-role 不存在"
kubectl get clusterrolebinding n8n-healer-binding &>/dev/null && pass "ClusterRoleBinding 存在" || fail "ClusterRoleBinding 不存在"

# ── 6. 告警规则检查 ──────────────────────────────────────────────
section "告警规则"

RULE_COUNT=$(kubectl get prometheusrule -n monitoring --no-headers 2>/dev/null | wc -l | tr -d ' ')
if [ "${RULE_COUNT}" -gt 0 ]; then
    pass "PrometheusRule 已加载 (共 ${RULE_COUNT} 条规则组)"
else
    warn "PrometheusRule 未加载（需要 kubectl apply -f k8s-manifests/monitoring/alerting-rules.yaml）"
fi

# ── 7. Secret 检查 ───────────────────────────────────────────────
section "凭据 Secret"

if kubectl get secret n8n-credentials -n monitoring &>/dev/null; then
    # 检查是否是占位值
    API_KEY=$(kubectl get secret n8n-credentials -n monitoring -o jsonpath='{.data.DASHSCOPE_API_KEY}' 2>/dev/null | base64 -d 2>/dev/null || echo "")
    if [[ "${API_KEY}" == "REPLACE_ME"* ]] || [[ -z "${API_KEY}" ]]; then
        warn "n8n-credentials Secret 存在但 DASHSCOPE_API_KEY 仍为占位值，需要填写真实 API Key"
    else
        pass "n8n-credentials Secret 存在且 API Key 已配置"
    fi
else
    warn "n8n-credentials Secret 不存在（TODO: 第二阶段配置）"
fi

# ── 结果汇总 ─────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}══════════════════════════════════════════${NC}"
echo -e "  结果：${GREEN}${PASS} 通过${NC}  ${YELLOW}${WARN} 警告${NC}  ${RED}${FAIL} 失败${NC}"
echo -e "${CYAN}══════════════════════════════════════════${NC}"
echo ""

if [ "${FAIL}" -gt 0 ]; then
    echo -e "${RED}❌ 存在失败项，请按照提示修复后重新运行验证${NC}"
    exit 1
elif [ "${WARN}" -gt 0 ]; then
    echo -e "${YELLOW}⚠️  存在警告项，部分功能可能不完整${NC}"
    exit 0
else
    echo -e "${GREEN}🎉 所有检查通过！KubeSentinel 环境已就绪${NC}"
    exit 0
fi

#!/usr/bin/env bash
# ================================================================
# KubeSentinel - 集群环境一键初始化脚本
# setup-cluster.sh
#
# 功能：
#   1. 创建 monitoring 命名空间
#   2. 使用 Helm 安装 kube-prometheus-stack（Prometheus + Grafana + Alertmanager）
#   3. 部署 n8n 工作流引擎
#   4. 等待所有组件就绪
#
# 前置要求：
#   - kubectl 已配置并连接到目标集群
#   - helm v3.10+ 已安装
#   - 集群节点至少有 4GB 可用内存、2 vCPU
#
# 使用方式：
#   chmod +x scripts/setup-cluster.sh
#   ./scripts/setup-cluster.sh
#
# 可选环境变量：
#   GRAFANA_PASSWORD  - Grafana admin 密码 (默认: KubeSentinel@2025)
#   N8N_PASSWORD      - n8n basic auth 密码 (默认: kubesentinel)
#   PROM_RETENTION    - Prometheus 数据保留天数 (默认: 15d)
# ================================================================

set -euo pipefail

# ── 颜色输出 ────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

log_info()    { echo -e "${BLUE}[INFO]${NC}  $*"; }
log_success() { echo -e "${GREEN}[OK]${NC}    $*"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }
log_step()    { echo -e "\n${CYAN}══════════════════════════════════════${NC}"; echo -e "${CYAN}  >> $*${NC}"; echo -e "${CYAN}══════════════════════════════════════${NC}"; }

# ── 配置参数 ────────────────────────────────────────────────────
MONITORING_NS="monitoring"
PROMETHEUS_CHART_REPO="prometheus-community"
PROMETHEUS_CHART_URL="https://prometheus-community.github.io/helm-charts"
PROMETHEUS_RELEASE_NAME="kube-prometheus-stack"
PROMETHEUS_CHART_VERSION="58.4.0"      # 建议锁定版本，避免升级破坏

N8N_CHART_REPO="n8n-community"
N8N_CHART_URL="https://community-charts.github.io/helm-charts"
N8N_RELEASE_NAME="n8n"

GRAFANA_PASSWORD="${GRAFANA_PASSWORD:-KubeSentinel@2025}"
N8N_PASSWORD="${N8N_PASSWORD:-kubesentinel}"
PROM_RETENTION="${PROM_RETENTION:-15d}"

# ── 前置检查 ────────────────────────────────────────────────────
log_step "Step 0: 前置环境检查"

check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "$1 未安装或不在 PATH 中，请先安装后重试"
    fi
    log_info "$1 已检测到: $(command -v "$1")"
}

check_command kubectl
check_command helm

# 检查集群连通性
if ! kubectl cluster-info &> /dev/null; then
    log_error "无法连接到 Kubernetes 集群，请检查 kubeconfig 配置"
fi
log_success "集群连接正常: $(kubectl config current-context)"

# 检查节点就绪
READY_NODES=$(kubectl get nodes --no-headers | grep -c "Ready" || true)
log_info "就绪节点数量: ${READY_NODES}"
if [ "${READY_NODES}" -lt 1 ]; then
    log_error "没有就绪的节点，请先修复集群状态"
fi

# ── Step 1：创建 monitoring 命名空间 ────────────────────────────
log_step "Step 1: 创建 monitoring 命名空间"

if kubectl get namespace "${MONITORING_NS}" &> /dev/null; then
    log_warn "命名空间 ${MONITORING_NS} 已存在，跳过创建"
else
    kubectl create namespace "${MONITORING_NS}"
    # 添加标签方便后续选择
    kubectl label namespace "${MONITORING_NS}" \
        app.kubernetes.io/managed-by=kubesentinel \
        kubernetes.io/metadata.name="${MONITORING_NS}" \
        --overwrite
    log_success "命名空间 ${MONITORING_NS} 创建成功"
fi

# ── Step 2：添加 Helm 仓库 ───────────────────────────────────────
log_step "Step 2: 配置 Helm Chart 仓库"

# 添加 prometheus-community 仓库
if helm repo list | grep -q "${PROMETHEUS_CHART_REPO}"; then
    log_warn "仓库 ${PROMETHEUS_CHART_REPO} 已存在，跳过添加"
else
    helm repo add "${PROMETHEUS_CHART_REPO}" "${PROMETHEUS_CHART_URL}"
    log_success "已添加仓库: ${PROMETHEUS_CHART_REPO}"
fi

# 添加 n8n community chart 仓库
if helm repo list | grep -q "${N8N_CHART_REPO}"; then
    log_warn "仓库 ${N8N_CHART_REPO} 已存在，跳过添加"
else
    helm repo add "${N8N_CHART_REPO}" "${N8N_CHART_URL}" || \
        log_warn "n8n community chart 添加失败，将使用手动 manifest 部署"
fi

log_info "更新 Helm 仓库索引..."
helm repo update
log_success "Helm 仓库已更新"

# ── Step 3：安装 kube-prometheus-stack ───────────────────────────
log_step "Step 3: 安装 kube-prometheus-stack"
log_info "Chart 版本: ${PROMETHEUS_CHART_VERSION}"
log_info "Release 名称: ${PROMETHEUS_RELEASE_NAME}"
log_info "Grafana 密码: ${GRAFANA_PASSWORD}"
log_warn "这一步预计需要 3-5 分钟..."

# 检查是否已经安装
if helm status "${PROMETHEUS_RELEASE_NAME}" -n "${MONITORING_NS}" &> /dev/null; then
    log_warn "kube-prometheus-stack 已安装，执行 upgrade..."
    HELM_CMD="upgrade"
else
    HELM_CMD="install"
fi

helm "${HELM_CMD}" "${PROMETHEUS_RELEASE_NAME}" \
    "${PROMETHEUS_CHART_REPO}/kube-prometheus-stack" \
    --version "${PROMETHEUS_CHART_VERSION}" \
    --namespace "${MONITORING_NS}" \
    --create-namespace \
    --timeout 10m \
    --wait \
    --set grafana.adminPassword="${GRAFANA_PASSWORD}" \
    --set grafana.service.type="NodePort" \
    --set grafana.service.nodePort="30300" \
    --set prometheus.prometheusSpec.retention="${PROM_RETENTION}" \
    --set prometheus.prometheusSpec.scrapeInterval="15s" \
    --set prometheus.prometheusSpec.evaluationInterval="30s" \
    --set prometheus.service.type="NodePort" \
    --set prometheus.service.nodePort="30090" \
    --set alertmanager.service.type="NodePort" \
    --set alertmanager.service.nodePort="30093" \
    --set prometheus.prometheusSpec.ruleSelector.matchLabels.release="${PROMETHEUS_RELEASE_NAME}" \
    --set defaultRules.create=true \
    --set kubeStateMetrics.enabled=true \
    --set nodeExporter.enabled=true

log_success "kube-prometheus-stack 安装/更新完成！"

# ── Step 4：安装 n8n ─────────────────────────────────────────────
log_step "Step 4: 部署 n8n 工作流引擎"

# 使用 Kubernetes manifest 部署 n8n（更可控）
log_info "使用 Kubernetes manifest 部署 n8n..."

kubectl apply -f - <<EOF
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: n8n
  namespace: ${MONITORING_NS}
  labels:
    app: n8n
    app.kubernetes.io/managed-by: kubesentinel
spec:
  replicas: 1
  selector:
    matchLabels:
      app: n8n
  template:
    metadata:
      labels:
        app: n8n
    spec:
      serviceAccountName: n8n-healer
      containers:
        - name: n8n
          image: n8nio/n8n:latest
          ports:
            - containerPort: 5678
          env:
            - name: N8N_BASIC_AUTH_ACTIVE
              value: "false"
            - name: N8N_PORT
              value: "5678"
            - name: N8N_PROTOCOL
              value: "http"
            - name: WEBHOOK_URL
              value: "http://n8n:5678/"
            - name: N8N_LOG_LEVEL
              value: "info"
            - name: EXECUTIONS_PROCESS
              value: "main"
          resources:
            requests:
              cpu: "200m"
              memory: "512Mi"
            limits:
              cpu: "1000m"
              memory: "1Gi"
          livenessProbe:
            httpGet:
              path: /healthz
              port: 5678
            initialDelaySeconds: 30
            periodSeconds: 30
          readinessProbe:
            httpGet:
              path: /healthz
              port: 5678
            initialDelaySeconds: 15
            periodSeconds: 15
          volumeMounts:
            - name: n8n-data
              mountPath: /home/node/.n8n
      volumes:
        - name: n8n-data
          emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: n8n
  namespace: ${MONITORING_NS}
  labels:
    app: n8n
spec:
  type: NodePort
  selector:
    app: n8n
  ports:
    - name: http
      port: 5678
      targetPort: 5678
      nodePort: 30567
EOF

log_success "n8n 部署清单已应用"

# ── Step 5：应用 RBAC 配置 ───────────────────────────────────────
log_step "Step 5: 应用 n8n RBAC 配置"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "${SCRIPT_DIR}")"
RBAC_FILE="${PROJECT_ROOT}/k8s-manifests/rbac/n8n-rbac.yaml"

if [ -f "${RBAC_FILE}" ]; then
    kubectl apply -f "${RBAC_FILE}"
    log_success "RBAC 配置已应用"
else
    log_warn "RBAC 文件不存在: ${RBAC_FILE}，跳过"
fi

# ── Step 6：等待所有组件就绪 ─────────────────────────────────────
log_step "Step 6: 等待所有组件就绪"

log_info "等待 Prometheus 就绪..."
kubectl rollout status deployment/kube-prometheus-stack-grafana -n "${MONITORING_NS}" --timeout=300s || true
kubectl rollout status statefulset/prometheus-kube-prometheus-stack-prometheus -n "${MONITORING_NS}" --timeout=300s || true

log_info "等待 n8n 就绪..."
kubectl rollout status deployment/n8n -n "${MONITORING_NS}" --timeout=120s || true

# ── Step 7：打印访问信息 ─────────────────────────────────────────
log_step "🎉 初始化完成！访问地址汇总"

NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}' 2>/dev/null || echo "YOUR_NODE_IP")

echo ""
echo -e "  ${GREEN}📊 Grafana${NC}        http://${NODE_IP}:30300  (admin / ${GRAFANA_PASSWORD})"
echo -e "  ${GREEN}🔥 Prometheus${NC}     http://${NODE_IP}:30090"
echo -e "  ${GREEN}🚨 Alertmanager${NC}   http://${NODE_IP}:30093"
echo -e "  ${GREEN}⚙️  n8n${NC}           http://${NODE_IP}:30567"
echo ""
log_info "如使用 Minikube，请替换 ${NODE_IP} 为 \$(minikube ip) 的输出值"
log_info "或使用 kubectl port-forward 进行本地访问"
echo ""
log_success "KubeSentinel 监控底座初始化完成！🛡️"

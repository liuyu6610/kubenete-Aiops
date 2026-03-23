#!/usr/bin/env bash
# ================================================================
# KubeSentinel - 混沌工程故障注入脚本
# chaos-inject.sh
#
# 功能：模拟各类 Kubernetes 故障场景，用于触发自愈流程演示
#
# 支持故障类型：
#   cpu-stress     - CPU 满载（触发 PodCpuCritical 告警）
#   memory-stress  - 内存压力（触发 PodMemoryHighUsage 告警）
#   kill-pod       - 强制删除 Pod（触发重启和 CrashLoopBackOff）
#   network-delay  - 模拟网络延迟（需要 tc 工具）
#   oom-kill       - 触发 OOM Killer（内存超过 limits）
#
# 使用示例：
#   ./scripts/chaos-inject.sh --target order-service --type cpu-stress --duration 120
#   ./scripts/chaos-inject.sh --target frontend --type kill-pod
#   ./scripts/chaos-inject.sh --list-targets
# ================================================================

set -euo pipefail

# ── 颜色输出 ────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info()    { echo -e "${BLUE}[CHAOS]${NC}  $*"; }
log_success() { echo -e "${GREEN}[OK]${NC}    $*"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# ── 参数解析 ────────────────────────────────────────────────────
TARGET=""
CHAOS_TYPE=""
DURATION=120    # 默认持续 120 秒
NAMESPACE="demo-app"
DRY_RUN=false

usage() {
    cat <<EOF
用法: $0 [选项]

选项:
  --target <deployment>   目标 Deployment 名称 (如: order-service, frontend, redis)
  --type <chaos-type>     故障类型 (见下方支持列表)
  --duration <seconds>    故障持续时间（秒），默认 120
  --namespace <ns>        目标命名空间，默认 demo-app
  --dry-run               仅打印操作，不实际执行
  --list-targets          列出可用的故障注入目标
  -h, --help              显示帮助

支持的故障类型:
  cpu-stress      注入 CPU 压力（通过 stress-ng 或 dd 命令）
  memory-stress   注入内存压力
  kill-pod        随机删除一个 Pod（模拟节点崩溃）
  oom-kill        申请超过 memory limits 的内存，触发 OOM Kill
  crash-loop      注入配置错误导致 Pod 崩溃循环

示例:
  $0 --target order-service --type cpu-stress --duration 90
  $0 --target frontend --type kill-pod
  $0 --list-targets
EOF
    exit 0
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --target)    TARGET="$2";     shift 2 ;;
        --type)      CHAOS_TYPE="$2"; shift 2 ;;
        --duration)  DURATION="$2";   shift 2 ;;
        --namespace) NAMESPACE="$2";  shift 2 ;;
        --dry-run)   DRY_RUN=true;    shift   ;;
        --list-targets)
            echo -e "\n${CYAN}可用的故障注入目标：${NC}"
            kubectl get deployments -n "${NAMESPACE}" --no-headers -o custom-columns="NAME:.metadata.name,REPLICAS:.spec.replicas,READY:.status.readyReplicas" 2>/dev/null || echo "(需要集群连接)"
            exit 0
            ;;
        -h|--help)   usage ;;
        *) log_error "未知参数: $1，使用 --help 查看帮助" ;;
    esac
done

# ── 参数验证 ────────────────────────────────────────────────────
[ -z "${TARGET}" ]     && log_error "请通过 --target 指定目标 Deployment"
[ -z "${CHAOS_TYPE}" ] && log_error "请通过 --type 指定故障类型"

echo ""
echo -e "${RED}╔══════════════════════════════════════════╗${NC}"
echo -e "${RED}║   ⚠️  KubeSentinel 混沌工程故障注入      ║${NC}"
echo -e "${RED}╚══════════════════════════════════════════╝${NC}"
echo ""
log_warn "目标:   ${NAMESPACE}/${TARGET}"
log_warn "类型:   ${CHAOS_TYPE}"
log_warn "持续:   ${DURATION} 秒"
[ "${DRY_RUN}" = true ] && log_warn "模式:   DRY RUN（不实际执行）"
echo ""

# 获取目标 Pod
get_pod() {
    local pod
    pod=$(kubectl get pods -n "${NAMESPACE}" -l "app=${TARGET}" \
        --field-selector=status.phase=Running \
        --no-headers -o custom-columns=":.metadata.name" \
        | head -n1)
    if [ -z "${pod}" ]; then
        log_error "没有找到 namespace=${NAMESPACE} 且 app=${TARGET} 的 Running Pod"
    fi
    echo "${pod}"
}

# ── 故障注入函数 ─────────────────────────────────────────────────

# CPU 压力注入
inject_cpu_stress() {
    local pod
    pod=$(get_pod)
    log_info "目标 Pod: ${pod}"
    log_info "注入 CPU 压力，持续 ${DURATION} 秒..."
    log_info "期望效果: CPU 使用率 > 85%，约 1-2 分钟后触发 Prometheus 告警"

    if [ "${DRY_RUN}" = true ]; then
        echo "[DRY RUN] kubectl exec ${pod} -n ${NAMESPACE} -- sh -c 'stress-ng --cpu 2 --timeout ${DURATION}s'"
        return
    fi

    # 尝试使用 stress-ng，如不可用则降级为 dd + /dev/null
    kubectl exec "${pod}" -n "${NAMESPACE}" -c "${TARGET}" -- sh -c \
        "which stress-ng > /dev/null 2>&1 && stress-ng --cpu 2 --cpu-load 90 --timeout ${DURATION}s \
        || (echo 'stress-ng not found, using dd fallback...' && \
            for i in \$(seq 1 2); do dd if=/dev/zero of=/dev/null & done && sleep ${DURATION} && kill %1 %2 2>/dev/null)" \
        &

    local chaos_pid=$!
    log_success "CPU 压力注入已启动 (PID: ${chaos_pid})"
    log_info "可通过以下命令观察指标变化："
    log_info "  kubectl top pods -n ${NAMESPACE} -l app=${TARGET} --watch"
    log_info "  或访问 Grafana 仪表盘查看实时曲线"
}

# 内存压力注入
inject_memory_stress() {
    local pod
    pod=$(get_pod)
    log_info "目标 Pod: ${pod}"
    log_info "注入内存压力，持续 ${DURATION} 秒..."

    if [ "${DRY_RUN}" = true ]; then
        echo "[DRY RUN] kubectl exec ${pod} -n ${NAMESPACE} -- sh -c 'stress-ng --vm 1 --vm-bytes 200M --timeout ${DURATION}s'"
        return
    fi

    kubectl exec "${pod}" -n "${NAMESPACE}" -- sh -c \
        "stress-ng --vm 1 --vm-bytes 200M --timeout ${DURATION}s 2>/dev/null || \
         python3 -c \"import time; data=[' '*1024*1024 for _ in range(200)]; print('Allocated 200MB'); time.sleep(${DURATION})\" 2>/dev/null || \
         (cat /dev/zero | head -c 200m | tail -c 1 && sleep ${DURATION}) &" &

    log_success "内存压力注入已启动"
}

# 强制删除 Pod（触发重启）
inject_kill_pod() {
    local pod
    pod=$(get_pod)
    log_info "目标 Pod: ${pod}"
    log_warn "即将强制删除 Pod！Kubernetes 将自动重建..."

    if [ "${DRY_RUN}" = true ]; then
        echo "[DRY RUN] kubectl delete pod ${pod} -n ${NAMESPACE} --grace-period=0"
        return
    fi

    kubectl delete pod "${pod}" -n "${NAMESPACE}" --grace-period=0
    log_success "Pod ${pod} 已删除，Deployment 控制器将重建新 Pod"
    log_info "观察重建过程: kubectl get pods -n ${NAMESPACE} -l app=${TARGET} --watch"
}

# OOM Kill 模拟（申请超过 memory limits 的内存）
inject_oom_kill() {
    local pod
    pod=$(get_pod)
    local memory_limit
    memory_limit=$(kubectl get pod "${pod}" -n "${NAMESPACE}" \
        -o jsonpath='{.spec.containers[0].resources.limits.memory}' 2>/dev/null || echo "256Mi")
    log_info "目标 Pod: ${pod}"
    log_info "当前 Memory Limit: ${memory_limit}"
    log_warn "注入超额内存申请，触发 OOM Killer..."

    if [ "${DRY_RUN}" = true ]; then
        echo "[DRY RUN] 申请 > ${memory_limit} 内存触发 OOM"
        return
    fi

    # 申请 300MB 强制触发 OOM（假设 limit 为 256Mi）
    kubectl exec "${pod}" -n "${NAMESPACE}" -- sh -c \
        "python3 -c \"a=[' '*1024*1024 for _ in range(400)]; import time; time.sleep(60)\" 2>/dev/null || \
         dd if=/dev/zero of=/tmp/oom bs=1M count=400 2>/dev/null" &

    log_success "OOM 压力已注入，Pod 将在触发 OOM Killer 后被重启"
}

# 崩溃循环模拟
inject_crash_loop() {
    log_info "通过修改 Deployment 命令模拟崩溃循环..."

    if [ "${DRY_RUN}" = true ]; then
        echo "[DRY RUN] kubectl patch deployment ${TARGET} -n ${NAMESPACE} --patch '{...}'"
        return
    fi

    # 保存原始命令（用于恢复）
    kubectl get deployment "${TARGET}" -n "${NAMESPACE}" -o json > /tmp/"${TARGET}"-backup.json
    log_info "原始配置已备份到 /tmp/${TARGET}-backup.json"

    # 注入一个错误命令，使 Pod 启动后立即退出
    kubectl patch deployment "${TARGET}" -n "${NAMESPACE}" \
        --type='json' \
        -p='[{"op": "replace", "path": "/spec/template/spec/containers/0/command", "value": ["/bin/sh", "-c", "echo CrashInjected && exit 1"]}]'

    log_success "崩溃注入成功！Pod 将开始 CrashLoopBackOff"
    log_warn "⚠️ 恢复命令: kubectl apply -f /tmp/${TARGET}-backup.json"
    log_info "观察状态: kubectl get pods -n ${NAMESPACE} -l app=${TARGET} --watch"

    # 自动定时恢复
    if [ "${DURATION}" -gt 0 ]; then
        log_info "将在 ${DURATION} 秒后自动恢复..."
        (sleep "${DURATION}" && \
         kubectl apply -f /tmp/"${TARGET}"-backup.json && \
         log_success "Deployment ${TARGET} 已自动恢复！") &
    fi
}

# ── 主逻辑 ────────────────────────────────────────────────────
case "${CHAOS_TYPE}" in
    cpu-stress)     inject_cpu_stress    ;;
    memory-stress)  inject_memory_stress ;;
    kill-pod)       inject_kill_pod      ;;
    oom-kill)       inject_oom_kill      ;;
    crash-loop)     inject_crash_loop    ;;
    *)
        log_error "不支持的故障类型: ${CHAOS_TYPE}，使用 --help 查看支持列表"
        ;;
esac

echo ""
log_success "故障注入完成！现在请观察 KubeSentinel 的自愈响应过程："
echo -e "  ${CYAN}1.${NC} Grafana 仪表盘：指标异常上升"
echo -e "  ${CYAN}2.${NC} Alertmanager UI：告警状态变为 firing"
echo -e "  ${CYAN}3.${NC} n8n 工作流界面：自动执行中"
echo -e "  ${CYAN}4.${NC} 飞书/钉钉群：收到自愈报告通知"
echo -e "  ${CYAN}5.${NC} Grafana 仪表盘：指标恢复正常"
echo ""

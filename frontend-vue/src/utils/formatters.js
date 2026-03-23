/**
 * Format utilities — plain utility functions (NOT composables)
 * Per vue-best-practices: keep pure utilities as plain functions
 */

const ACTION_LABELS = {
  rolling_restart: '滚动重启',
  scale_up: '扩容',
  scale_down: '缩容',
  rollback: '版本回滚',
  cordon_node: '节点封锁',
  delete_pod: '删除Pod',
  adjust_hpa: '调整HPA',
  investigate: '仅调查',
  evict_pods: '驱逐Pod',
  no_action: '无需操作',
}

export function formatRelativeTime(timestamp) {
  if (!timestamp) return ''
  const diff = Math.floor((Date.now() - new Date(timestamp).getTime()) / 1000)
  if (diff < 60) return `${diff}s ago`
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return `${Math.floor(diff / 86400)}d ago`
}

export function formatAbsoluteTime(timestamp) {
  if (!timestamp) return ''
  const d = new Date(timestamp)
  return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

export function getActionLabel(action) {
  return ACTION_LABELS[action] || action
}

export function getConfidenceColor(val) {
  if (val < 0.6) return '#ef4444'
  if (val < 0.75) return '#f59e0b'
  return '#10b981'
}

export function getConfidenceGradient(val) {
  if (val < 0.6) return 'linear-gradient(90deg, #ef4444, #f97316)'
  if (val < 0.75) return 'linear-gradient(90deg, #f59e0b, #eab308)'
  return 'linear-gradient(90deg, #10b981, #06b6d4)'
}

export function getRiskType(level) {
  if (level === 'high') return 'danger'
  if (level === 'medium') return 'warning'
  return 'success'
}

export function getRiskLabel(level) {
  if (level === 'high') return '高风险'
  if (level === 'medium') return '中风险'
  return '低风险'
}

export function getActionColor(action) {
  const destructive = ['rolling_restart', 'rollback', 'delete_pod', 'evict_pods']
  if (destructive.includes(action)) return 'danger'
  if (['scale_up', 'scale_down', 'adjust_hpa'].includes(action)) return 'warning'
  if (action === 'no_action') return 'success'
  return 'info'
}

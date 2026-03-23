<template>
  <div class="alerts-page">
    <!-- Header & Filters -->
    <div class="alerts-header glass-card animate-in">
      <div class="alerts-header__left">
        <h2 class="alerts-header__title">
          <span class="panel-title__icon">🔔</span>
          告警与自愈决策流
        </h2>
        <span class="alerts-header__count">
          共 {{ filteredData.length }} 条告警记录
        </span>
      </div>
      <div class="alerts-header__right">
        <div class="filter-group">
          <button 
            v-for="filter in statusFilters" 
            :key="filter.value" 
            class="filter-btn"
            :class="{ 'filter-btn--active': statusFilter === filter.value }"
            @click="statusFilter = filter.value"
          >
            <span v-if="filter.dot" class="filter-dot" :class="filter.dot"></span>
            {{ filter.label }}
            <span v-if="getStatusCount(filter.value) > 0" class="filter-count">
              {{ getStatusCount(filter.value) }}
            </span>
          </button>
        </div>
        <button class="action-btn action-btn--ghost" @click="fetchAlerts">
          🔄 刷新
        </button>
      </div>
    </div>

    <!-- Alerts Table -->
    <div class="alerts-table glass-card animate-in animate-in-delay-2">
      <el-table
        :data="filteredData"
        style="width: 100%"
        v-loading="loading"
        stripe
        :row-class-name="getRowClass"
        @row-click="handleRowClick"
      >
        <el-table-column prop="timestamp" label="告警时间" width="160">
          <template #default="scope">
            <div class="cell-time">
              <span class="time-relative">{{ formatRelativeTime(scope.row.timestamp) }}</span>
              <span class="time-absolute">{{ formatAbsoluteTime(scope.row.timestamp) }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="alertname" label="告警名称" width="200">
          <template #default="scope">
            <span class="cell-alertname">{{ scope.row.alertname }}</span>
          </template>
        </el-table-column>

        <el-table-column label="故障目标" width="200">
          <template #default="scope">
            <div class="cell-target">
              <span class="target-name">{{ scope.row.target }}</span>
              <span class="target-ns">{{ scope.row.namespace }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="AI 置信度" width="160">
          <template #default="scope">
            <div class="cell-confidence">
              <div class="confidence-bar">
                <div 
                  class="confidence-bar__fill" 
                  :style="{ 
                    width: (scope.row.confidence * 100) + '%',
                    background: getConfidenceGradient(scope.row.confidence)
                  }"
                ></div>
              </div>
              <span class="confidence-value" :style="{ color: getConfidenceColor(scope.row.confidence) }">
                {{ (scope.row.confidence * 100).toFixed(0) }}%
              </span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="风险" width="90">
          <template #default="scope">
            <span class="status-badge" :class="'status-badge--' + getRiskType(scope.row.risk_level)">
              {{ getRiskLabel(scope.row.risk_level) }}
            </span>
          </template>
        </el-table-column>

        <el-table-column label="AI 建议动作" width="140">
          <template #default="scope">
            <span class="action-tag" :class="'action-tag--' + getActionColor(scope.row.action)">
              {{ getActionLabel(scope.row.action) }}
            </span>
          </template>
        </el-table-column>

        <el-table-column label="状态" width="150">
          <template #default="scope">
            <div class="cell-status">
              <span class="glow-dot" :class="getStatusDotClass(scope.row.status)" style="width:6px;height:6px;"></span>
              <span>{{ scope.row.status }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column fixed="right" label="" width="100">
          <template #default="scope">
            <button 
              v-if="scope.row.status === '待审批'" 
              class="action-btn action-btn--primary" 
              style="padding: 6px 14px; font-size: 12px;"
              @click.stop="openApprovalDialog(scope.row)"
            >
              审批
            </button>
            <button 
              v-else 
              class="action-btn action-btn--ghost" 
              style="padding: 6px 14px; font-size: 12px;"
              @click.stop="openDetailDialog(scope.row)"
            >
              详情
            </button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- Approval / Detail Dialog -->
    <el-dialog 
      v-model="dialogVisible" 
      :title="dialogTitle" 
      width="620px"
      class="dark-dialog"
      destroy-on-close
    >
      <div v-if="activeAlert" class="dialog-body">
        <!-- Info Grid -->
        <div class="info-grid">
          <div class="info-item">
            <span class="info-label">告警名称</span>
            <span class="info-value">{{ activeAlert.alertname }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">故障目标</span>
            <span class="info-value">{{ activeAlert.target }} <span class="target-ns">{{ activeAlert.namespace }}</span></span>
          </div>
          <div class="info-item">
            <span class="info-label">AI 置信度</span>
            <span class="info-value" :style="{ color: getConfidenceColor(activeAlert.confidence) }">
              {{ (activeAlert.confidence * 100).toFixed(1) }}%
            </span>
          </div>
          <div class="info-item">
            <span class="info-label">风险等级</span>
            <span class="status-badge" :class="'status-badge--' + getRiskType(activeAlert.risk_level)">
              {{ getRiskLabel(activeAlert.risk_level) }}
            </span>
          </div>
        </div>

        <div class="info-item info-item--full">
          <span class="info-label">建议动作</span>
          <span class="action-tag action-tag--danger" style="font-size: 14px; padding: 6px 16px;">
            {{ getActionLabel(activeAlert.action) }}
          </span>
        </div>

        <!-- AI Analysis -->
        <div class="analysis-section">
          <h4><span>🧠</span> AI 分析过程</h4>
          <div class="analysis-box">{{ activeAlert.analysis }}</div>
        </div>

        <div v-if="activeAlert.root_cause" class="analysis-section">
          <h4><span>🎯</span> 根因判断</h4>
          <div class="analysis-box analysis-box--warning">{{ activeAlert.root_cause }}</div>
        </div>
      </div>

      <template #footer v-if="activeAlert && activeAlert.status === '待审批'">
        <div class="dialog-actions">
          <button class="action-btn action-btn--ghost" @click="handleReject">
            ✕ 拒绝执行
          </button>
          <button class="action-btn action-btn--danger" @click="handleApprove">
            ⚡ 授权执行
          </button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api/kubesentinel'

const loading = ref(false)
const dialogVisible = ref(false)
const activeAlert = ref(null)
const tableData = ref([])
const statusFilter = ref('')
let pollInterval = null

const statusFilters = [
  { label: '全部', value: '' },
  { label: '待审批', value: '待审批', dot: 'glow-dot--warning' },
  { label: '已执行', value: '已下发自动执行', dot: 'glow-dot--success' },
  { label: '已拒绝', value: '已拒绝', dot: 'glow-dot--danger' },
]

const dialogTitle = computed(() => {
  if (!activeAlert.value) return ''
  return activeAlert.value.status === '待审批' ? '⚠️ 人工审批介入' : '📋 告警详情'
})

const filteredData = computed(() => {
  if (!statusFilter.value) return tableData.value
  return tableData.value.filter(row => row.status.includes(statusFilter.value))
})

const getStatusCount = (status) => {
  if (!status) return tableData.value.length
  return tableData.value.filter(row => row.status.includes(status)).length
}

const ACTION_LABELS = {
  rolling_restart: '滚动重启', scale_up: '扩容', scale_down: '缩容',
  rollback: '版本回滚', cordon_node: '节点封锁', delete_pod: '删除Pod',
  adjust_hpa: '调整HPA', investigate: '仅调查', evict_pods: '驱逐Pod',
  no_action: '无需操作',
}

const fetchAlerts = async () => {
  loading.value = true
  try {
    const response = await api.getAlerts()
    tableData.value = response.data
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchAlerts()
  pollInterval = setInterval(fetchAlerts, 5000)
})
onUnmounted(() => { if (pollInterval) clearInterval(pollInterval) })

const formatRelativeTime = (timestamp) => {
  if (!timestamp) return ''
  const diff = Math.floor((Date.now() - new Date(timestamp).getTime()) / 1000)
  if (diff < 60) return `${diff}s ago`
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return `${Math.floor(diff / 86400)}d ago`
}

const formatAbsoluteTime = (timestamp) => {
  if (!timestamp) return ''
  const d = new Date(timestamp)
  return `${d.getMonth()+1}/${d.getDate()} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`
}

const getConfidenceColor = (val) => {
  if (val < 0.6) return '#ef4444'
  if (val < 0.75) return '#f59e0b'
  return '#10b981'
}
const getConfidenceGradient = (val) => {
  if (val < 0.6) return 'linear-gradient(90deg, #ef4444, #f97316)'
  if (val < 0.75) return 'linear-gradient(90deg, #f59e0b, #eab308)'
  return 'linear-gradient(90deg, #10b981, #06b6d4)'
}

const getRiskType = (level) => {
  if (level === 'high') return 'danger'
  if (level === 'medium') return 'warning'
  return 'success'
}
const getRiskLabel = (level) => {
  if (level === 'high') return '高风险'
  if (level === 'medium') return '中风险'
  return '低风险'
}

const getActionLabel = (action) => ACTION_LABELS[action] || action
const getActionColor = (action) => {
  const destructive = ['rolling_restart', 'rollback', 'delete_pod', 'evict_pods']
  if (destructive.includes(action)) return 'danger'
  if (['scale_up', 'scale_down', 'adjust_hpa'].includes(action)) return 'warning'
  if (action === 'no_action') return 'success'
  return 'info'
}

const getStatusDotClass = (status) => {
  if (status === '待审批') return 'glow-dot--warning'
  if (status === '已拒绝') return 'glow-dot--danger'
  return 'glow-dot--success'
}

const getRowClass = ({ row }) => {
  if (row.status === '待审批') return 'row-pending'
  return ''
}

const handleRowClick = (row) => {
  if (row.status === '待审批') openApprovalDialog(row)
  else openDetailDialog(row)
}

const openApprovalDialog = (row) => { activeAlert.value = row; dialogVisible.value = true }
const openDetailDialog = (row) => { activeAlert.value = row; dialogVisible.value = true }

const handleApprove = async () => {
  try {
    const res = await api.approveAction(activeAlert.value.id)
    ElMessage.success(`操作成功: ${res.data.message}`)
    dialogVisible.value = false
    fetchAlerts()
  } catch (error) {
    ElMessage.error('授权执行失败: ' + (error.response?.data?.detail || error.message))
  }
}

const handleReject = async () => {
  try {
    await api.rejectAction(activeAlert.value.id)
    ElMessage.info('已拒绝执行')
    dialogVisible.value = false
    fetchAlerts()
  } catch (error) {
    ElMessage.error('拒绝操作失败')
  }
}
</script>

<style scoped>
.alerts-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* Header */
.alerts-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
}
.alerts-header__title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}
.alerts-header__count {
  font-size: 12px;
  color: var(--text-muted);
  margin-left: 12px;
}
.alerts-header__right {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* Filters */
.filter-group {
  display: flex;
  gap: 4px;
  background: rgba(255, 255, 255, 0.03);
  padding: 3px;
  border-radius: var(--radius-md);
}
.filter-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border: none;
  border-radius: 7px;
  background: transparent;
  color: var(--text-muted);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
  font-family: var(--font-sans);
}
.filter-btn:hover { color: var(--text-primary); }
.filter-btn--active {
  background: rgba(99, 102, 241, 0.15);
  color: var(--accent-primary-light);
}
.filter-dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
.filter-dot.glow-dot--warning { background: var(--color-warning); }
.filter-dot.glow-dot--success { background: var(--color-success); }
.filter-dot.glow-dot--danger { background: var(--color-danger); }
.filter-count {
  background: rgba(255, 255, 255, 0.08);
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 11px;
  font-family: var(--font-mono);
}

/* Table */
.alerts-table {
  padding: 0;
  overflow: hidden;
}
.cell-time {
  display: flex;
  flex-direction: column;
}
.time-relative {
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--text-primary);
}
.time-absolute {
  font-size: 11px;
  color: var(--text-muted);
}
.cell-alertname {
  font-weight: 600;
  font-size: 13px;
  color: var(--text-primary);
}
.cell-target {
  display: flex;
  flex-direction: column;
}
.target-name {
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--text-primary);
}
.target-ns {
  font-size: 11px;
  color: var(--text-muted);
  font-family: var(--font-mono);
}
.cell-confidence {
  display: flex;
  align-items: center;
  gap: 10px;
}
.confidence-bar {
  flex: 1;
  height: 6px;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 3px;
  overflow: hidden;
}
.confidence-bar__fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.5s ease;
}
.confidence-value {
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 600;
  min-width: 36px;
  text-align: right;
}
.cell-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--text-secondary);
}

/* Action Tags */
.action-tag {
  display: inline-flex;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
}
.action-tag--danger { background: var(--color-danger-bg); color: var(--color-danger); }
.action-tag--warning { background: var(--color-warning-bg); color: var(--color-warning); }
.action-tag--success { background: var(--color-success-bg); color: var(--color-success); }
.action-tag--info { background: var(--color-info-bg); color: var(--color-info); }

/* Pending row highlight */
:deep(.row-pending) {
  background: rgba(245, 158, 11, 0.03) !important;
}

/* Dialog */
.dialog-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.info-item--full { margin-top: 4px; }
.info-label {
  font-size: 12px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 600;
}
.info-value {
  font-size: 14px;
  color: var(--text-primary);
  font-weight: 500;
}
.analysis-section h4 {
  font-size: 14px;
  color: var(--text-primary);
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
}
.analysis-box {
  padding: 14px 16px;
  background: rgba(99, 102, 241, 0.06);
  border: 1px solid rgba(99, 102, 241, 0.12);
  border-radius: var(--radius-md);
  font-size: 13px;
  line-height: 1.7;
  color: var(--text-secondary);
}
.analysis-box--warning {
  background: rgba(245, 158, 11, 0.06);
  border-color: rgba(245, 158, 11, 0.12);
}
.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
.action-btn--danger {
  background: linear-gradient(135deg, #ef4444, #dc2626);
  color: white;
  border: none;
  padding: 8px 20px;
  border-radius: var(--radius-md);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  font-family: var(--font-sans);
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
}
.action-btn--danger:hover {
  box-shadow: 0 6px 20px rgba(239, 68, 68, 0.45);
}
</style>

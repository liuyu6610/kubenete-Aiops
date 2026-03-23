<template>
  <div class="history-page">
    <!-- Header -->
    <div class="history-header glass-card animate-in">
      <div class="history-header__left">
        <h2 class="history-header__title">
          <span class="panel-title__icon">📋</span>
          操作审计日志
        </h2>
        <span class="history-header__count">
          共 {{ activities.length }} 条操作记录
        </span>
      </div>
      <button class="action-btn action-btn--ghost" @click="fetchAuditLogs">
        🔄 刷新
      </button>
    </div>

    <!-- Timeline -->
    <div class="timeline-container glass-card animate-in animate-in-delay-2">
      <!-- Loading -->
      <div v-if="loading" class="timeline-loading">
        <div class="spinner"></div>
        <span>加载审计记录中...</span>
      </div>

      <!-- Empty -->
      <div v-else-if="activities.length === 0" class="timeline-empty">
        <div class="empty-icon">📭</div>
        <p>暂无审计记录</p>
        <span>当系统处理告警或执行自愈操作时，操作记录将出现在这里</span>
      </div>

      <!-- Timeline Items -->
      <div v-else class="timeline">
        <div class="timeline-line"></div>
        <div 
          v-for="(item, index) in activities" 
          :key="index" 
          class="timeline-item animate-in"
          :style="{ animationDelay: `${Math.min(index * 0.06, 0.5)}s` }"
        >
          <div class="timeline-dot" :class="'timeline-dot--' + item.type">
            <span>{{ getTypeIcon(item.type) }}</span>
          </div>
          <div class="timeline-content">
            <div class="timeline-content__header">
              <span class="status-badge" :class="'status-badge--' + getStatusType(item.type)">
                {{ getTypeLabel(item.type) }}
              </span>
              <span class="timeline-time">{{ formatTime(item.timestamp) }}</span>
            </div>
            <h4 class="timeline-title">{{ item.title }}</h4>
            <p class="timeline-desc" v-if="item.description">{{ item.description }}</p>
            <div class="timeline-meta" v-if="item.operator">
              <span class="meta-tag">
                <span class="meta-icon">👤</span>
                {{ item.operator }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import api from '@/api/kubesentinel'

const activities = ref([])
const loading = ref(true)
let pollInterval = null

const fetchAuditLogs = async () => {
  loading.value = true
  try {
    const response = await api.getAuditLogs()
    activities.value = response.data.map(log => ({
      title: log.action_title,
      description: log.description,
      operator: log.operator,
      timestamp: log.timestamp,
      type: log.type || 'info',
    }))
  } catch (error) {
    console.error('Failed to fetch audit logs:', error)
  } finally {
    loading.value = false
  }
}

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const d = new Date(timestamp)
  const now = new Date()
  const diff = Math.floor((now - d) / 1000)
  if (diff < 60) return `${diff}s ago`
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

const getTypeIcon = (type) => {
  const icons = { success: '✅', warning: '⚠️', primary: '🔷', danger: '🔴', info: 'ℹ️' }
  return icons[type] || 'ℹ️'
}
const getTypeLabel = (type) => {
  const labels = { success: '成功', warning: '警告', primary: '系统', danger: '严重', info: '信息' }
  return labels[type] || type
}
const getStatusType = (type) => {
  const map = { success: 'success', warning: 'warning', primary: 'info', danger: 'danger', info: 'info' }
  return map[type] || 'info'
}

onMounted(() => {
  fetchAuditLogs()
  pollInterval = setInterval(fetchAuditLogs, 5000)
})
onUnmounted(() => { if (pollInterval) clearInterval(pollInterval) })
</script>

<style scoped>
.history-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.history-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
}
.history-header__left {
  display: flex;
  align-items: center;
}
.history-header__title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}
.history-header__count {
  font-size: 12px;
  color: var(--text-muted);
  margin-left: 12px;
}

/* Timeline Container */
.timeline-container {
  padding: 24px;
  min-height: 400px;
}

/* Loading */
.timeline-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  min-height: 300px;
  color: var(--text-muted);
}
.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid rgba(99, 102, 241, 0.15);
  border-top-color: var(--accent-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Empty */
.timeline-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  text-align: center;
}
.empty-icon { font-size: 48px; margin-bottom: 16px; }
.timeline-empty p {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 4px;
}
.timeline-empty span {
  font-size: 13px;
  color: var(--text-muted);
}

/* Timeline */
.timeline {
  position: relative;
  padding-left: 48px;
}
.timeline-line {
  position: absolute;
  left: 19px;
  top: 0;
  bottom: 0;
  width: 2px;
  background: linear-gradient(to bottom, var(--accent-primary), rgba(99, 102, 241, 0.08));
}

.timeline-item {
  position: relative;
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}
.timeline-item:last-child { margin-bottom: 0; }

.timeline-dot {
  position: absolute;
  left: -48px;
  top: 4px;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  border: 2px solid var(--bg-card);
  z-index: 1;
}
.timeline-dot--success { background: var(--color-success-bg); }
.timeline-dot--warning { background: var(--color-warning-bg); }
.timeline-dot--danger { background: var(--color-danger-bg); }
.timeline-dot--primary { background: var(--color-info-bg); }
.timeline-dot--info { background: rgba(148, 163, 184, 0.1); }

.timeline-content {
  flex: 1;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 14px 18px;
  transition: border-color var(--transition-fast);
}
.timeline-content:hover {
  border-color: var(--border-color-hover);
}
.timeline-content__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.timeline-time {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text-muted);
}
.timeline-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 6px 0;
  line-height: 1.4;
}
.timeline-desc {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
  margin: 0 0 8px 0;
}
.timeline-meta {
  display: flex;
  gap: 8px;
}
.meta-tag {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--text-muted);
  background: rgba(255, 255, 255, 0.03);
  padding: 3px 10px;
  border-radius: 4px;
}
.meta-icon { font-size: 11px; }
</style>

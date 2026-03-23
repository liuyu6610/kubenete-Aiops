<template>
  <div class="dashboard">
    <!-- Hero Stats Row -->
    <div class="stats-grid animate-in">
      <div 
        v-for="(stat, index) in statistics" 
        :key="stat.title" 
        class="stat-card glass-card animate-in"
        :class="'animate-in-delay-' + (index + 1)"
      >
        <div class="stat-card__header">
          <div class="stat-card__icon" :style="{ background: stat.gradient }">
            <el-icon :size="22"><component :is="stat.icon" /></el-icon>
          </div>
          <div class="stat-card__trend" v-if="stat.trend">
            <span :class="stat.trend > 0 ? 'trend-up' : 'trend-down'">
              {{ stat.trend > 0 ? '↑' : '↓' }} {{ Math.abs(stat.trend) }}%
            </span>
          </div>
        </div>
        <div class="stat-card__value counter-value">{{ stat.value }}</div>
        <div class="stat-card__label">{{ stat.title }}</div>
        <!-- Decorative shimmer -->
        <div class="stat-card__shimmer"></div>
      </div>
    </div>

    <!-- Charts Row -->
    <div class="charts-grid">
      <!-- Main trend chart -->
      <div class="chart-panel glass-card animate-in animate-in-delay-2">
        <div class="panel-header">
          <div class="panel-title">
            <span class="panel-title__icon">📈</span>
            <span>告警与自愈趋势</span>
          </div>
          <div class="panel-actions">
            <button 
              v-for="range in timeRanges" 
              :key="range.value" 
              class="time-btn" 
              :class="{ 'time-btn--active': selectedRange === range.value }"
              @click="selectedRange = range.value"
            >
              {{ range.label }}
            </button>
          </div>
        </div>
        <v-chart class="chart-main" :option="lineChartOption" autoresize />
      </div>

      <!-- Side panels -->
      <div class="side-panels">
        <!-- Pie chart -->
        <div class="chart-panel glass-card animate-in animate-in-delay-3">
          <div class="panel-header">
            <div class="panel-title">
              <span class="panel-title__icon">🔬</span>
              <span>故障类型分布</span>
            </div>
          </div>
          <v-chart class="chart-pie" :option="pieChartOption" autoresize />
        </div>

        <!-- Success Rate Gauge -->
        <div class="chart-panel glass-card animate-in animate-in-delay-4">
          <div class="panel-header">
            <div class="panel-title">
              <span class="panel-title__icon">🎯</span>
              <span>自愈成功率</span>
            </div>
          </div>
          <v-chart class="chart-gauge" :option="gaugeOption" autoresize />
        </div>
      </div>
    </div>

    <!-- Quick Actions Bar -->
    <div class="actions-bar glass-card animate-in animate-in-delay-4">
      <div class="actions-bar__left">
        <span class="actions-bar__title">🔧 快速操作</span>
        <span class="actions-bar__desc">调试与测试工具</span>
      </div>
      <div class="actions-bar__right">
        <button class="action-btn action-btn--primary" @click="sendTestAlert" :disabled="testLoading">
          <span v-if="testLoading" class="action-btn__spinner"></span>
          <span v-else>⚡</span>
          发送模拟告警
        </button>
        <button class="action-btn action-btn--ghost" @click="fetchStats">
          🔄 刷新数据
        </button>
      </div>
      <transition name="slide-fade">
        <div v-if="testResult" class="test-result" :class="testResult.type">
          {{ testResult.text }}
        </div>
      </transition>
    </div>
  </div>
</template>

<script setup>
import { shallowRef, computed } from 'vue'
import { Warning, MagicStick, CircleCheck, Bell } from '@element-plus/icons-vue'
import { useStats } from '@/composables/useStats'
import { getActionLabel } from '@/utils/formatters'
import api from '@/api/kubesentinel'

// Composable — per vue-best-practices skill
const { stats: statsData, totalAlerts, autoHealedCount, successRate, pendingApproval, recentActions, refresh: fetchStats } = useStats()

const testLoading = shallowRef(false)
const testResult = shallowRef(null)
const selectedRange = shallowRef('7d')

const timeRanges = [
  { label: '24h', value: '24h' },
  { label: '7天', value: '7d' },
  { label: '30天', value: '30d' },
]

const statistics = computed(() => [
  { 
    title: '今日告警', 
    value: totalAlerts.value, 
    icon: 'Warning', 
    gradient: 'linear-gradient(135deg, #f59e0b, #f97316)',
    trend: 12, 
  },
  { 
    title: 'AI 自愈次数', 
    value: autoHealedCount.value, 
    icon: 'MagicStick', 
    gradient: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
    trend: 8, 
  },
  { 
    title: '自愈成功率', 
    value: successRate.value + '%', 
    icon: 'CircleCheck', 
    gradient: 'linear-gradient(135deg, #10b981, #06b6d4)',
    trend: 3,
  },
  { 
    title: '待审批工单', 
    value: pendingApproval.value, 
    icon: 'Bell', 
    gradient: 'linear-gradient(135deg, #ef4444, #ec4899)',
    trend: -5,
  },
])



// Line chart
const lineChartOption = computed(() => {
  const days = []
  const alertCounts = []
  const healCounts = []
  const numDays = selectedRange.value === '24h' ? 1 : selectedRange.value === '7d' ? 7 : 30

  for (let i = numDays - 1; i >= 0; i--) {
    const d = new Date()
    d.setDate(d.getDate() - i)
    days.push(numDays <= 1 
      ? `${String(d.getHours()).padStart(2, '0')}:00` 
      : `${d.getMonth() + 1}/${d.getDate()}`)
    if (i === 0) {
      alertCounts.push(totalAlerts.value)
      healCounts.push(autoHealedCount.value)
    } else {
      alertCounts.push(Math.floor(Math.random() * 18 + 3))
      healCounts.push(Math.floor(Math.random() * 14 + 2))
    }
  }

  return {
    tooltip: { 
      trigger: 'axis',
      backgroundColor: 'rgba(26, 31, 53, 0.95)',
      borderColor: 'rgba(148, 163, 184, 0.15)',
      textStyle: { color: '#f1f5f9', fontSize: 13 },
    },
    legend: { 
      data: ['告警数', '自愈执行'], 
      bottom: 0, 
      textStyle: { color: '#94a3b8', fontSize: 12 },
      itemGap: 24,
    },
    grid: { top: 16, right: 24, bottom: 44, left: 48 },
    xAxis: { 
      type: 'category', 
      data: days, 
      boundaryGap: false,
      axisLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.1)' } },
      axisLabel: { color: '#64748b', fontSize: 11 },
    },
    yAxis: { 
      type: 'value', 
      minInterval: 1,
      axisLine: { show: false },
      splitLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.06)' } },
      axisLabel: { color: '#64748b', fontSize: 11 },
    },
    series: [
      {
        name: '告警数',
        type: 'line',
        data: alertCounts,
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: { width: 2.5, color: '#f59e0b' },
        itemStyle: { color: '#f59e0b', borderColor: '#0a0e1a', borderWidth: 2 },
        areaStyle: {
          color: {
            type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(245, 158, 11, 0.25)' },
              { offset: 1, color: 'rgba(245, 158, 11, 0)' },
            ],
          },
        },
      },
      {
        name: '自愈执行',
        type: 'line',
        data: healCounts,
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: { width: 2.5, color: '#6366f1' },
        itemStyle: { color: '#6366f1', borderColor: '#0a0e1a', borderWidth: 2 },
        areaStyle: {
          color: {
            type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(99, 102, 241, 0.25)' },
              { offset: 1, color: 'rgba(99, 102, 241, 0)' },
            ],
          },
        },
      },
    ],
  }
})

// Pie chart
const pieChartOption = computed(() => {
  const data = recentActions.value.map(item => ({
    name: getActionLabel(item.name),
    value: item.value,
  }))
  const chartData = data.length > 0 ? data : [{ name: '暂无数据', value: 1 }]

  return {
    tooltip: { 
      trigger: 'item', 
      formatter: '{b}: {c} ({d}%)',
      backgroundColor: 'rgba(26, 31, 53, 0.95)',
      borderColor: 'rgba(148, 163, 184, 0.15)',
      textStyle: { color: '#f1f5f9' },
    },
    series: [{
      type: 'pie',
      radius: ['45%', '72%'],
      center: ['50%', '50%'],
      avoidLabelOverlap: true,
      itemStyle: { borderRadius: 6, borderColor: '#1a1f35', borderWidth: 2 },
      label: { show: true, color: '#94a3b8', fontSize: 11, formatter: '{b}\n{d}%' },
      labelLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.3)' } },
      data: chartData,
      color: ['#6366f1', '#ef4444', '#f59e0b', '#10b981', '#06b6d4', '#ec4899'],
    }],
  }
})

// Gauge
const gaugeOption = computed(() => ({
  series: [{
    type: 'gauge',
    startAngle: 200,
    endAngle: -20,
    min: 0,
    max: 100,
    splitNumber: 4,
    center: ['50%', '60%'],
    radius: '90%',
    itemStyle: {
      color: {
        type: 'linear', x: 0, y: 0, x2: 1, y2: 0,
        colorStops: [
          { offset: 0, color: '#ef4444' },
          { offset: 0.5, color: '#f59e0b' },
          { offset: 1, color: '#10b981' },
        ],
      },
    },
    progress: { show: true, width: 12, roundCap: true },
    pointer: { show: false },
    axisLine: { lineStyle: { width: 12, color: [[1, 'rgba(148, 163, 184, 0.08)']] }, roundCap: true },
    axisTick: { show: false },
    splitLine: { show: false },
    axisLabel: { show: false },
    title: { show: false },
    detail: {
      fontSize: 28,
      fontFamily: "'Space Mono', monospace",
      fontWeight: 700,
      color: '#f1f5f9',
      offsetCenter: [0, '10%'],
      formatter: '{value}%',
    },
    data: [{ value: successRate.value || 0 }],
  }],
}))



const sendTestAlert = async () => {
  testLoading.value = true
  testResult.value = null
  try {
    const response = await api.sendTestAlert()
    testResult.value = { type: 'success', text: `✅ ${response.data.status}: ${response.data.message}` }
    setTimeout(fetchStats, 1000)
  } catch (error) {
    testResult.value = { type: 'error', text: '❌ ' + (error.response?.data?.detail || error.message) }
  } finally {
    testLoading.value = false
    setTimeout(() => { testResult.value = null }, 5000)
  }
}
</script>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* ---- Stats Grid ---- */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}
.stat-card {
  padding: 24px;
  position: relative;
  overflow: hidden;
  cursor: default;
  transition: transform var(--transition-base), box-shadow var(--transition-base);
}
.stat-card:hover {
  transform: translateY(-2px);
}
.stat-card__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.stat-card__icon {
  width: 44px;
  height: 44px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}
.stat-card__trend {
  font-size: 12px;
  font-weight: 600;
  font-family: var(--font-mono);
}
.trend-up { color: var(--color-success); }
.trend-down { color: var(--color-danger); }
.stat-card__value {
  margin-bottom: 4px;
}
.stat-card__label {
  font-size: 13px;
  color: var(--text-muted);
  font-weight: 500;
}
.stat-card__shimmer {
  position: absolute;
  top: 0;
  left: -100%;
  width: 60%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.02), transparent);
  animation: shimmer 4s infinite;
}

/* ---- Charts Grid ---- */
.charts-grid {
  display: grid;
  grid-template-columns: 1fr 400px;
  gap: 16px;
  min-height: 380px;
}
.side-panels {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.chart-panel {
  padding: 20px;
}
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.panel-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}
.panel-title__icon {
  font-size: 18px;
}
.panel-actions {
  display: flex;
  gap: 4px;
}
.time-btn {
  background: none;
  border: 1px solid var(--border-color);
  color: var(--text-muted);
  padding: 4px 12px;
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
  transition: all var(--transition-fast);
  font-family: var(--font-sans);
}
.time-btn:hover {
  border-color: var(--accent-primary);
  color: var(--text-primary);
}
.time-btn--active {
  background: rgba(99, 102, 241, 0.15);
  border-color: var(--accent-primary);
  color: var(--accent-primary-light);
}
.chart-main { height: 340px; width: 100%; }
.chart-pie { height: 220px; width: 100%; }
.chart-gauge { height: 180px; width: 100%; }

/* ---- Actions Bar ---- */
.actions-bar {
  display: flex;
  align-items: center;
  padding: 16px 24px;
  gap: 24px;
  position: relative;
}
.actions-bar__left {
  display: flex;
  flex-direction: column;
}
.actions-bar__title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}
.actions-bar__desc {
  font-size: 12px;
  color: var(--text-muted);
}
.actions-bar__right {
  display: flex;
  gap: 10px;
  margin-left: auto;
}
.action-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 20px;
  border-radius: var(--radius-md);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
  border: none;
  font-family: var(--font-sans);
}
.action-btn--primary {
  background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
  color: white;
  box-shadow: 0 4px 16px rgba(99, 102, 241, 0.3);
}
.action-btn--primary:hover:not(:disabled) {
  box-shadow: 0 6px 24px rgba(99, 102, 241, 0.45);
  transform: translateY(-1px);
}
.action-btn--primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.action-btn--ghost {
  background: transparent;
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
}
.action-btn--ghost:hover {
  border-color: var(--accent-primary);
  color: var(--text-primary);
}
.action-btn__spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.test-result {
  position: absolute;
  right: 24px;
  bottom: -36px;
  font-size: 12px;
  font-weight: 500;
  padding: 6px 14px;
  border-radius: 6px;
}
.test-result.success { color: var(--color-success); background: var(--color-success-bg); }
.test-result.error { color: var(--color-danger); background: var(--color-danger-bg); }

.slide-fade-enter-active { transition: all 0.3s ease; }
.slide-fade-leave-active { transition: all 0.2s ease; }
.slide-fade-enter-from { opacity: 0; transform: translateY(8px); }
.slide-fade-leave-to { opacity: 0; transform: translateY(-8px); }
</style>

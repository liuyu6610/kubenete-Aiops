<template>
  <div class="layout-wrapper">
    <!-- Decorative background elements -->
    <div class="bg-grid"></div>
    <div class="bg-glow bg-glow--1"></div>
    <div class="bg-glow bg-glow--2"></div>
    
    <el-container class="layout-container">
      <!-- Sidebar -->
      <aside class="sidebar">
        <!-- Logo -->
        <div class="sidebar-logo">
          <div class="logo-icon">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            </svg>
          </div>
          <div class="logo-text">
            <span class="logo-title">KubeSentinel</span>
            <span class="logo-version">AIOps v2.0</span>
          </div>
        </div>

        <!-- Nav Items -->
        <nav class="sidebar-nav">
          <router-link 
            v-for="item in navItems" 
            :key="item.path"
            :to="item.path"
            class="nav-item"
            :class="{ 'nav-item--active': isActive(item.path) }"
          >
            <div class="nav-icon">
              <el-icon :size="20"><component :is="item.icon" /></el-icon>
            </div>
            <span class="nav-label">{{ item.label }}</span>
            <span v-if="item.badge" class="nav-badge">{{ item.badge }}</span>
          </router-link>
        </nav>

        <!-- Sidebar Footer -->
        <div class="sidebar-footer">
          <div class="engine-status" :class="engineOnline ? 'engine-status--online' : 'engine-status--offline'">
            <div class="glow-dot" :class="engineOnline ? 'glow-dot--success' : 'glow-dot--danger'"></div>
            <span>{{ engineOnline ? 'AI 引擎在线' : 'AI 引擎离线' }}</span>
          </div>
          <div class="sidebar-meta">
            <span>{{ llmProvider }}</span>
          </div>
        </div>
      </aside>

      <!-- Main Content -->
      <div class="main-wrapper">
        <!-- Header -->
        <header class="top-header">
          <div class="header-left">
            <h1 class="page-title">{{ currentRouteName }}</h1>
            <span class="page-subtitle">KubeSentinel 智能运维控制台</span>
          </div>
          <div class="header-right">
            <div class="header-stat" v-if="pendingApproval > 0">
              <span class="header-stat__badge status-badge status-badge--warning">
                <span class="glow-dot glow-dot--warning" style="width:6px;height:6px;"></span>
                {{ pendingApproval }} 待审批
              </span>
            </div>
            <div class="header-time">
              <el-icon><Timer /></el-icon>
              <span>{{ currentTime }}</span>
            </div>
          </div>
        </header>

        <!-- Content Area -->
        <main class="main-content">
          <router-view v-slot="{ Component }">
            <transition name="page-slide" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </main>
      </div>
    </el-container>
    
    <!-- AI Copilot Integration -->
    <AICopilot />
  </div>
</template>

<script setup>
import { shallowRef, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { DataLine, Bell, Document, Timer } from '@element-plus/icons-vue'
import { ElNotification } from 'element-plus'
import { useHealthCheck } from '@/composables/useHealthCheck'
import { useStats } from '@/composables/useStats'
import { useWebSocket } from '@/composables/useWebSocket'
import AICopilot from '@/components/AICopilot.vue'

const route = useRoute()

// Composables — per vue-best-practices skill
const { engineOnline, llmProvider } = useHealthCheck()
const { pendingApproval, refresh: refreshStats } = useStats({ pollInterval: 15000 })
const { connect, onMessage, isConnected } = useWebSocket()

const currentRouteName = computed(() => route.meta.title || route.name)
const isActive = (path) => route.path === path
const currentTime = shallowRef('')

const navItems = computed(() => [
  { path: '/dashboard', label: '监控总览', icon: 'DataLine' },
  { path: '/alerts', label: '告警中心', icon: 'Bell', badge: pendingApproval.value > 0 ? pendingApproval.value : null },
  { path: '/history', label: '操作审计', icon: 'Document' },
])

let timeInterval = null
const updateTime = () => {
  const now = new Date()
  currentTime.value = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`
}

onMounted(() => {
  updateTime()
  timeInterval = setInterval(updateTime, 1000)

  // Real-time integration
  connect()
  onMessage((data) => {
    if (data.event === 'NEW_ALERT_RECEIVED') {
      ElNotification({
        title: '新告警到达',
        message: `[${data.namespace}] ${data.pod} 触发了 ${data.alertname} 告警，AI引擎正在分析...`,
        type: 'warning',
        duration: 6000,
        customClass: 'glass-notification'
      })
      refreshStats()
    } else if (data.event === 'ALERT_ANALYZED') {
      const type = data.status === '已自动执行' ? 'success' : 'info'
      ElNotification({
        title: 'AI 分析完毕',
        message: `诊断结果: ${data.status}`,
        type: type,
        duration: 6000,
        customClass: 'glass-notification'
      })
      refreshStats()
    }
  })
})

onUnmounted(() => {
  clearInterval(timeInterval)
})
</script>

<style scoped>
/* ---- Layout Wrapper ---- */
.layout-wrapper {
  position: relative;
  height: 100vh;
  overflow: hidden;
}

/* ---- Background Effects ---- */
.bg-grid {
  position: absolute;
  inset: 0;
  background-image: 
    linear-gradient(rgba(148, 163, 184, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(148, 163, 184, 0.03) 1px, transparent 1px);
  background-size: 60px 60px;
  z-index: 0;
  pointer-events: none;
}
.bg-glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(120px);
  z-index: 0;
  pointer-events: none;
}
.bg-glow--1 {
  width: 500px;
  height: 500px;
  background: rgba(99, 102, 241, 0.06);
  top: -100px;
  right: -100px;
}
.bg-glow--2 {
  width: 400px;
  height: 400px;
  background: rgba(6, 182, 212, 0.04);
  bottom: -80px;
  left: 200px;
}

/* ---- Container ---- */
.layout-container {
  position: relative;
  z-index: 1;
  height: 100vh;
}

/* ---- Sidebar ---- */
.sidebar {
  width: 240px;
  min-width: 240px;
  background: var(--bg-sidebar);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  position: relative;
  z-index: 10;
}

.sidebar-logo {
  padding: 24px 20px;
  display: flex;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid var(--border-color);
}
.logo-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}
.logo-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
  display: block;
  line-height: 1.2;
}
.logo-version {
  font-size: 11px;
  color: var(--text-muted);
  font-weight: 500;
  letter-spacing: 0.05em;
}

/* ---- Navigation ---- */
.sidebar-nav {
  flex: 1;
  padding: 16px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  transition: all var(--transition-fast);
  position: relative;
}
.nav-item:hover {
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-primary);
}
.nav-item--active {
  background: rgba(99, 102, 241, 0.12) !important;
  color: var(--accent-primary-light) !important;
}
.nav-item--active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 60%;
  background: var(--accent-primary);
  border-radius: 0 4px 4px 0;
}
.nav-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
}
.nav-badge {
  margin-left: auto;
  background: var(--color-danger);
  color: white;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 10px;
  min-width: 20px;
  text-align: center;
}

/* ---- Sidebar Footer ---- */
.sidebar-footer {
  padding: 16px 20px;
  border-top: 1px solid var(--border-color);
}
.engine-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 500;
}
.engine-status--online { color: var(--color-success); }
.engine-status--offline { color: var(--color-danger); }
.sidebar-meta {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 4px;
  padding-left: 16px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* ---- Main Wrapper ---- */
.main-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

/* ---- Top Header ---- */
.top-header {
  height: 64px;
  padding: 0 28px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--border-color);
  background: rgba(10, 14, 26, 0.6);
  backdrop-filter: blur(12px);
  flex-shrink: 0;
}
.page-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}
.page-subtitle {
  font-size: 12px;
  color: var(--text-muted);
  margin-left: 12px;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}
.header-time {
  display: flex;
  align-items: center;
  gap: 6px;
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--text-secondary);
}

/* ---- Main Content ---- */
.main-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px 28px;
}

/* ---- Page Transitions ---- */
.page-slide-enter-active {
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}
.page-slide-leave-active {
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}
.page-slide-enter-from {
  opacity: 0;
  transform: translateY(12px);
}
.page-slide-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>

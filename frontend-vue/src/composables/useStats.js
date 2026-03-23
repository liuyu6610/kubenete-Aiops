/**
 * useStats — Dashboard statistics composable
 * Fetches and manages stats data with polling
 */
import { shallowRef, computed, readonly } from 'vue'
import api from '@/api/kubesentinel'
import { usePolling } from './usePolling'

export function useStats(options = {}) {
  const { pollInterval = 10000 } = options

  const _data = shallowRef({
    total_alerts_today: 0,
    auto_healed_count: 0,
    success_rate: 0,
    pending_approval: 0,
    recent_actions: [],
  })

  const totalAlerts = computed(() => _data.value.total_alerts_today)
  const autoHealedCount = computed(() => _data.value.auto_healed_count)
  const successRate = computed(() => _data.value.success_rate)
  const pendingApproval = computed(() => _data.value.pending_approval)
  const recentActions = computed(() => _data.value.recent_actions)

  async function fetchStats() {
    const response = await api.getStats()
    _data.value = response.data
  }

  const { loading, error, execute: refresh } = usePolling(fetchStats, {
    interval: pollInterval,
  })

  return {
    stats: readonly(_data),
    totalAlerts,
    autoHealedCount,
    successRate,
    pendingApproval,
    recentActions,
    loading,
    error,
    refresh,
  }
}

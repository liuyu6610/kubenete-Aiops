/**
 * useAlerts — Alert data composable
 * Manages alert list, filtering, and approval actions
 */
import { shallowRef, ref, computed, readonly } from 'vue'
import api from '@/api/kubesentinel'
import { usePolling } from './usePolling'

export function useAlerts(options = {}) {
  const { pollInterval = 5000 } = options

  const _alerts = ref([])
  const statusFilter = shallowRef('')

  const filteredAlerts = computed(() => {
    if (!statusFilter.value) return _alerts.value
    return _alerts.value.filter(row => row.status.includes(statusFilter.value))
  })

  function getStatusCount(status) {
    if (!status) return _alerts.value.length
    return _alerts.value.filter(row => row.status.includes(status)).length
  }

  async function fetchAlerts() {
    const response = await api.getAlerts()
    _alerts.value = response.data
  }

  async function approveAction(id) {
    return api.approveAction(id)
  }

  async function rejectAction(id) {
    return api.rejectAction(id)
  }

  const { loading, error, execute: refresh } = usePolling(fetchAlerts, {
    interval: pollInterval,
  })

  return {
    alerts: readonly(_alerts),
    statusFilter,
    filteredAlerts,
    getStatusCount,
    loading,
    error,
    refresh,
    approveAction,
    rejectAction,
  }
}

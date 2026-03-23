/**
 * useHealthCheck — Engine health monitoring composable
 */
import { shallowRef } from 'vue'
import api from '@/api/kubesentinel'
import { usePolling } from './usePolling'

export function useHealthCheck(options = {}) {
  const { pollInterval = 15000 } = options

  const engineOnline = shallowRef(false)
  const llmProvider = shallowRef('N/A')

  async function checkHealth() {
    try {
      const resp = await api.healthCheck()
      engineOnline.value = true
      llmProvider.value = resp.data.components?.llm_provider || 'dashscope'
    } catch {
      engineOnline.value = false
      llmProvider.value = 'N/A'
    }
  }

  const { execute: refresh } = usePolling(checkHealth, {
    interval: pollInterval,
  })

  return { engineOnline, llmProvider, refresh }
}

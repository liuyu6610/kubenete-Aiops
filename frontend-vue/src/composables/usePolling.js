/**
 * usePolling — Composable for periodic data fetching
 * Manages interval lifecycle automatically (mount/unmount)
 */
import { shallowRef, onMounted, onUnmounted } from 'vue'

export function usePolling(fetchFn, options = {}) {
  const { interval = 10000, immediate = true } = options
  const loading = shallowRef(false)
  const error = shallowRef(null)
  let timer = null

  async function execute() {
    loading.value = true
    error.value = null
    try {
      await fetchFn()
    } catch (err) {
      error.value = err
      console.error('[usePolling] Error:', err)
    } finally {
      loading.value = false
    }
  }

  function start() {
    if (timer) return
    timer = setInterval(execute, interval)
  }

  function stop() {
    if (timer) {
      clearInterval(timer)
      timer = null
    }
  }

  onMounted(() => {
    if (immediate) execute()
    start()
  })

  onUnmounted(stop)

  return { loading, error, execute, start, stop }
}

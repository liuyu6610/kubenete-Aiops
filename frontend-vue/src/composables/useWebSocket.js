import { ref, onMounted, onUnmounted } from 'vue'

const isConnected = ref(false)
const socket = ref(null)
const listeners = new Set()

export function useWebSocket() {
  const wsUrl = `ws://${window.location.hostname}:8000/ws/alerts`

  const connect = () => {
    if (socket.value) return

    socket.value = new WebSocket(wsUrl)

    socket.value.onopen = () => {
      isConnected.value = true
      console.log('KubeSentinel WebSocket Connected (Smooth Integration Active)')
    }

    socket.value.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        listeners.forEach(callback => callback(data))
      } catch (e) {
        console.error('Error parsing WS message:', e)
      }
    }

    socket.value.onclose = () => {
      isConnected.value = false
      socket.value = null
      console.log('WS Disconnected. Reconnecting in 3s...')
      setTimeout(connect, 3000)
    }
  }

  const onMessage = (callback) => {
    listeners.add(callback)
    onUnmounted(() => {
      listeners.delete(callback)
    })
  }

  const send = (msg) => {
    if (socket.value && isConnected.value) {
      socket.value.send(typeof msg === 'string' ? msg : JSON.stringify(msg))
    }
  }

  return {
    isConnected,
    connect,
    onMessage,
    send
  }
}

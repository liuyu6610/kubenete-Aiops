import axios from 'axios'

const apiClient = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json'
  },
  timeout: 10000,
})

// Response interceptor for error handling
apiClient.interceptors.response.use(
  response => response,
  error => {
    console.error('[KubeSentinel API Error]', error.message)
    return Promise.reject(error)
  }
)

export default {
  // Alerts
  getAlerts() {
    return apiClient.get('/alerts')
  },
  getAuditLogs() {
    return apiClient.get('/audit')
  },
  approveAction(alertId) {
    return apiClient.post(`/alerts/${alertId}/approve`)
  },
  rejectAction(alertId) {
    return apiClient.post(`/alerts/${alertId}/reject`)
  },

  // Dashboard stats
  getStats() {
    return apiClient.get('/stats')
  },
  getClusterStats() {
    return apiClient.get('/cluster/stats')
  },

  // Health check
  healthCheck() {
    return apiClient.get('/healthz', { baseURL: 'http://localhost:8000' })
  },

  // Debug tools
  sendTestAlert() {
    return apiClient.post('/test-alert')
  },
}

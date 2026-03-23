import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '@/layout/MainLayout.vue'
import Dashboard from '@/views/Dashboard.vue'
import Alerts from '@/views/Alerts.vue'
import History from '@/views/History.vue'

const routes = [
  {
    path: '/',
    component: MainLayout,
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: Dashboard,
        meta: { title: '监控总览' }
      },
      {
        path: 'alerts',
        name: 'Alerts',
        component: Alerts,
        meta: { title: '告警中心' }
      },
      {
        path: 'history',
        name: 'History',
        component: History,
        meta: { title: '操作审计' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Update document title on navigation
router.beforeEach((to) => {
  document.title = `${to.meta.title || 'KubeSentinel'} — KubeSentinel AIOps`
})

export default router

import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/ledgers',
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/AuthPages.vue'),
      meta: { requiresAuth: false },
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/AuthPages.vue'),
      meta: { requiresAuth: false },
    },
    {
      path: '/password-reset',
      name: 'password-reset',
      component: () => import('@/views/AuthPages.vue'),
      meta: { requiresAuth: false },
    },
    {
      path: '/password-reset/confirm',
      name: 'password-reset-confirm',
      component: () => import('@/views/AuthPages.vue'),
      meta: { requiresAuth: false },
    },
    {
      path: '/ledgers',
      name: 'ledger-list',
      component: () => import('@/views/LedgerList.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/ledgers/:id',
      name: 'ledger-detail',
      component: () => import('@/views/LedgerDetail.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/ledgers/:id/settings',
      name: 'ledger-settings',
      component: () => import('@/views/Settings.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/ledgers/:id/budget',
      name: 'budget-wizard',
      component: () => import('@/views/BudgetWizard.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/ledgers/:id/summary',
      name: 'ledger-summary',
      component: () => import('@/views/SummaryView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/ledgers/:id/recurring',
      name: 'ledger-recurring',
      component: () => import('@/views/RecurringView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/suggestions',
      name: 'suggestions',
      component: () => import('@/views/SuggestionsView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/admin',
      name: 'admin',
      component: () => import('@/views/AdminPanel.vue'),
      meta: { requiresAuth: true, requiresAdmin: true },
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      redirect: '/',
    },
  ],
})

// 路由守卫：未登录重定向到登录页
router.beforeEach(async (to, _from, next) => {
  const authStore = useAuthStore()
  const requiresAuth = to.meta.requiresAuth !== false

  if (requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'login', query: { redirect: to.fullPath } })
    return
  }

  if (requiresAuth && authStore.isAuthenticated && !authStore.hasFetchedUser) {
    await authStore.fetchCurrentUser()
  }

  if (to.meta.requiresAdmin && !authStore.isAdmin) {
    next({ name: 'ledger-list' })
    return
  }

  next()
})

export default router

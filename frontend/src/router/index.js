import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { requiresGuest: true },
    },
    {
      path: '/',
      component: () => import('@/layouts/MainLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'dashboard',
          component: () => import('@/views/DashboardView.vue'),
        },
        {
          path: '/compliance',
          name: 'Compliance',
          component: () => import('@/views/ComplianceView.vue'),
          meta: { requiresAuth: true },
        },
        {
          path: '/budgets',
          name: 'Budgets',
          component: () => import('@/views/BudgetView.vue'),
          meta: { requiresAuth: true },
        },
        {
          path: '/air',
          name: 'Air',
          component: () => import('@/views/AirView.vue'),
          meta: { requiresAuth: true },
        },
        {
          path: '/accommodation',
          name: 'Accommodation',
          component: () => import('@/views/AccommodationView.vue'),
          meta: { requiresAuth: true }
        },
        {
          path: '/car-hire',
          name: 'CarHire',
          component: () => import('@/views/CarHireView.vue'),
          meta: { requiresAuth: true }
        },
        {
          path: '/service-fees',
          name: 'ServiceFees',
          component: () => import('@/views/ServiceFeesView.vue'),
          meta: { requiresAuth: true }
        },
        {
          path: 'bookings',
          name: 'bookings',
          component: () => import('@/views/BookingsView.vue'),
        },
      ],
    },
  ],
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'login' })
  } else if (to.meta.requiresGuest && authStore.isAuthenticated) {
    next({ name: 'dashboard' })
  } else {
    next()
  }
})

export default router

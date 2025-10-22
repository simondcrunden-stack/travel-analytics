import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { 
        requiresGuest: true,
        title: 'Login'
      },
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
          meta: {
            title: 'Dashboard',
            breadcrumbs: [
              { label: 'Dashboard', path: '/' }
            ]
          }
        },
        {
          path: '/compliance',
          name: 'Compliance',
          component: () => import('@/views/ComplianceView.vue'),
          meta: { 
            requiresAuth: true,
            title: 'Compliance',
            breadcrumbs: [
              { label: 'Dashboard', path: '/' },
              { label: 'Compliance', path: '/compliance' }
            ]
          },
        },
        {
          path: '/budgets',
          name: 'Budgets',
          component: () => import('@/views/BudgetView.vue'),
          meta: { 
            requiresAuth: true,
            title: 'Budgets',
            breadcrumbs: [
              { label: 'Dashboard', path: '/' },
              { label: 'Budgets', path: '/budgets' }
            ]
          },
        },
        {
          path: '/air',
          name: 'Air',
          component: () => import('@/views/AirView.vue'),
          meta: { 
            requiresAuth: true,
            title: 'Air Travel',
            breadcrumbs: [
              { label: 'Dashboard', path: '/' },
              { label: 'Air Travel', path: '/air' }
            ]
          },
        },
        {
          path: '/accommodation',
          name: 'Accommodation',
          component: () => import('@/views/AccommodationView.vue'),
          meta: { 
            requiresAuth: true,
            title: 'Accommodation',
            breadcrumbs: [
              { label: 'Dashboard', path: '/' },
              { label: 'Accommodation', path: '/accommodation' }
            ]
          }
        },
        {
          path: '/car-hire',
          name: 'CarHire',
          component: () => import('@/views/CarHireView.vue'),
          meta: { 
            requiresAuth: true,
            title: 'Car Hire',
            breadcrumbs: [
              { label: 'Dashboard', path: '/' },
              { label: 'Car Hire', path: '/car-hire' }
            ]
          }
        },
        {
          path: '/service-fees',
          name: 'ServiceFees',
          component: () => import('@/views/ServiceFeesView.vue'),
          meta: { 
            requiresAuth: true,
            title: 'Service Fees',
            breadcrumbs: [
              { label: 'Dashboard', path: '/' },
              { label: 'Service Fees', path: '/service-fees' }
            ]
          }
        },
        {
          path: 'bookings',
          name: 'bookings',
          component: () => import('@/views/BookingsView.vue'),
          meta: {
            title: 'Bookings',
            breadcrumbs: [
              { label: 'Dashboard', path: '/' },
              { label: 'Bookings', path: '/bookings' }
            ]
          }
        },
        /* {
          path: 'bookings/:id',
          name: 'booking-detail',
          component: () => import('@/views/BookingDetailView.vue'),
          meta: {
            title: 'Booking Details',
            breadcrumbs: [
              { label: 'Dashboard', path: '/' },
              { label: 'Bookings', path: '/bookings' },
              { label: 'Details', path: '' }
            ]
          }
        },
        {
          path: '/analytics',
          name: 'analytics',
          component: () => import('@/views/AnalyticsView.vue'),
          meta: {
            requiresAuth: true,
            title: 'Analytics',
            breadcrumbs: [
              { label: 'Dashboard', path: '/' },
              { label: 'Analytics', path: '/analytics' }
            ]
          }
        },
        {
          path: '/travelers',
          name: 'travelers',
          component: () => import('@/views/TravelersView.vue'),
          meta: {
            requiresAuth: true,
            title: 'Travelers',
            breadcrumbs: [
              { label: 'Dashboard', path: '/' },
              { label: 'Travelers', path: '/travelers' }
            ]
          }
        },
        {
          path: '/reports',
          name: 'reports',
          component: () => import('@/views/ReportsView.vue'),
          meta: {
            requiresAuth: true,
            title: 'Reports',
            breadcrumbs: [
              { label: 'Dashboard', path: '/' },
              { label: 'Reports', path: '/reports' }
            ]
          }
        },
        {
          path: '/policies',
          name: 'policies',
          component: () => import('@/views/PoliciesView.vue'),
          meta: {
            requiresAuth: true,
            title: 'Travel Policies',
            breadcrumbs: [
              { label: 'Dashboard', path: '/' },
              { label: 'Policies', path: '/policies' }
            ]
          }
        },
        {
          path: '/settings',
          name: 'settings',
          component: () => import('@/views/SettingsView.vue'),
          meta: {
            requiresAuth: true,
            title: 'Settings',
            breadcrumbs: [
              { label: 'Dashboard', path: '/' },
              { label: 'Settings', path: '/settings' }
            ]
          }
        },
        {
          path: '/help',
          name: 'help',
          component: () => import('@/views/HelpView.vue'),
          meta: {
            requiresAuth: true,
            title: 'Help & Support',
            breadcrumbs: [
              { label: 'Dashboard', path: '/' },
              { label: 'Help & Support', path: '/help' }
            ]
          }
        },
        */
      ],
    },
    /* {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('@/views/NotFoundView.vue'),
      meta: {
        title: '404 - Page Not Found'
      }
    } */
  ],
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
})

// Navigation Guards
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  // Set page title
  document.title = to.meta.title 
    ? `${to.meta.title} | Travel Analytics` 
    : 'Travel Analytics'

  // Authentication checks
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'login' })
  } else if (to.meta.requiresGuest && authStore.isAuthenticated) {
    next({ name: 'dashboard' })
  } else {
    next()
  }
})

export default router
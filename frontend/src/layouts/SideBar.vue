<!-- Complete SideBar Component with MDI Icons -->
<!-- Location: frontend/src/layouts/SideBar.vue -->

<template>
  <aside
    :class="[
      'bg-gray-900 text-white transition-all duration-300 ease-in-out',
      'fixed lg:relative inset-y-0 left-0 z-40',
      'flex flex-col',
      navigationStore.isSidebarCollapsed ? 'w-16' : 'w-64'
    ]"
  >
    <!-- Logo Section -->
    <div class="flex items-center justify-between h-16 px-4 border-b border-gray-800">
      <div v-if="!navigationStore.isSidebarCollapsed" class="flex items-center space-x-2">
        <span class="text-xl font-bold">Travel Analytics</span>
      </div>
      <div v-else class="flex items-center justify-center w-full">
        <span class="text-xl font-bold">TA</span>
      </div>
    </div>

    <!-- Navigation Menu -->
    <nav class="flex-1 overflow-y-auto py-4">
      <ul class="space-y-1 px-2">
        <li v-for="item in menuItems" :key="item.path">
          <router-link
            :to="item.path"
            :class="[
              'flex items-center px-3 py-2.5 rounded-lg transition-colors duration-200',
              'hover:bg-gray-800',
              isActiveRoute(item.path)
                ? 'bg-blue-600 text-white'
                : 'text-gray-300 hover:text-white'
            ]"
            @click="onNavItemClick(item)"
          >
            <!-- MDI Icon -->
            <span :class="['mdi', item.icon, 'text-xl']"></span>

            <!-- Label (hidden when collapsed) -->
            <span
              v-if="!navigationStore.isSidebarCollapsed"
              class="ml-3 text-sm font-medium"
            >
              {{ item.name }}
            </span>

            <!-- Admin Badge (optional) -->
            <span
              v-if="item.adminOnly && !navigationStore.isSidebarCollapsed"
              class="ml-auto px-2 py-0.5 text-xs font-medium bg-purple-500 text-white rounded-full"
            >
              Admin
            </span>

            <!-- Badge (optional) -->
            <span
              v-if="item.badge && !navigationStore.isSidebarCollapsed"
              :class="[
                'ml-auto px-2 py-0.5 text-xs font-medium rounded-full',
                item.badgeClass || 'bg-red-500 text-white'
              ]"
            >
              {{ item.badge }}
            </span>
          </router-link>
        </li>
      </ul>
    </nav>

    <!-- User Section (Bottom) -->
    <div class="border-t border-gray-800 p-4">
      <div
        v-if="!navigationStore.isSidebarCollapsed"
        class="flex items-center space-x-3"
      >
        <div class="flex-shrink-0">
          <div class="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center">
            <span class="text-sm font-medium">{{ userInitials }}</span>
          </div>
        </div>
        <div class="flex-1 min-w-0">
          <p class="text-sm font-medium text-white truncate">
            {{ currentUser?.username || 'Guest' }}
          </p>
          <p class="text-xs text-gray-400 truncate">
            {{ currentUser?.email || 'Not logged in' }}
          </p>
        </div>
      </div>
      <div v-else class="flex justify-center">
        <div class="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center">
          <span class="text-sm font-medium">{{ userInitials }}</span>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useNavigationStore } from '@/stores/navigation'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const navigationStore = useNavigationStore()
const authStore = useAuthStore()

// Base menu items configuration with MDI icons
const baseMenuItems = [
  {
    name: 'Summary',  // Changed from 'Dashboard'
    path: '/',
    icon: 'mdi-view-dashboard',
    badge: null
  },
  {
    name: 'Bookings',
    path: '/bookings',
    icon: 'mdi-wallet-travel',
    badge: null
  },
  {
    name: 'Air Travel',
    path: '/air',
    icon: 'mdi-airplane',
    badge: null
  },
  {
    name: 'Accommodation',
    path: '/accommodation',
    icon: 'mdi-bed',
    badge: null
  },
  {
    name: 'Car Hire',
    path: '/car-hire',
    icon: 'mdi-car',
    badge: null
  },
  {
    name: 'Service Fees',
    path: '/service-fees',
    icon: 'mdi-room-service-outline',
    badge: null
  },
  {
    name: 'Compliance',
    path: '/compliance',
    icon: 'mdi-shield-check',
    badge: '3' // Example: 3 violations
  },
  {
    name: 'Budgets',
    path: '/budgets',
    icon: 'mdi-wallet',
    badge: null
  }
]

// Admin-only menu items
const adminMenuItems = [
  {
    name: 'Organization Structure',
    path: '/organization-structure',
    icon: 'mdi-office-building-cog',
    badge: 'Admin',
    badgeClass: 'bg-purple-600 text-white'
  }
]

// Computed menu items based on user type
const menuItems = computed(() => {
  const items = [...baseMenuItems]
  if (authStore.userType === 'ADMIN') {
    items.push(...adminMenuItems)
  }
  return items
})

// Get current user from auth store
const currentUser = computed(() => authStore.user)

// Get user initials for avatar
const userInitials = computed(() => {
  if (!currentUser.value?.username) return 'G'
  const username = currentUser.value.username
  return username.substring(0, 2).toUpperCase()
})

// Check if route is active
const isActiveRoute = (path) => {
  if (path === '/') {
    return route.path === '/'
  }
  return route.path.startsWith(path)
}

// Handle navigation item click
const onNavItemClick = (item) => {
  // Add to recent pages
  navigationStore.addRecentPage({
    name: item.name,
    path: item.path,
    icon: item.icon
  })
  
  // Close sidebar on mobile after navigation
  if (!navigationStore.isDesktop) {
    navigationStore.toggleSidebar()
  }
}
</script>

<style scoped>
/* Custom scrollbar for navigation */
nav::-webkit-scrollbar {
  width: 6px;
}

nav::-webkit-scrollbar-track {
  background: transparent;
}

nav::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 3px;
}

nav::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.3);
}
</style>
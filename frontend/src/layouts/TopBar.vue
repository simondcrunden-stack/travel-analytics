<!-- TopBar Component - Without Missing Routes -->
<!-- Location: frontend/src/layouts/TopBar.vue -->

<template>
  <header class="bg-white shadow-sm">
    <div class="flex items-center justify-between h-16 px-6">
      <!-- Left: Hamburger Menu & Breadcrumbs -->
      <div class="flex items-center space-x-4">
        <!-- Hamburger Menu Button -->
        <button
          @click="toggleSidebar"
          class="p-2 rounded-lg hover:bg-gray-100 transition-colors"
          aria-label="Toggle sidebar"
        >
          <span class="mdi mdi-menu text-2xl text-gray-600"></span>
        </button>

        <!-- Breadcrumbs -->
        <nav class="hidden md:flex items-center space-x-2 text-sm">
          <router-link
            to="/"
            class="text-gray-500 hover:text-gray-700 transition-colors"
          >
            Home
          </router-link>
          <span v-if="breadcrumbs.length > 0" class="text-gray-400">/</span>
          <span
            v-for="(crumb, index) in breadcrumbs"
            :key="index"
            class="flex items-center"
          >
            <span
              :class="[
                index === breadcrumbs.length - 1
                  ? 'text-gray-900 font-medium'
                  : 'text-gray-500 hover:text-gray-700'
              ]"
            >
              {{ crumb }}
            </span>
            <span
              v-if="index < breadcrumbs.length - 1"
              class="text-gray-400 mx-2"
            >
              /
            </span>
          </span>
        </nav>
      </div>

      <!-- Right: Search, Notifications, User Menu -->
      <div class="flex items-center space-x-4">
        <!-- Search Button (optional) -->
        <button
          class="p-2 rounded-lg hover:bg-gray-100 transition-colors hidden md:block"
          aria-label="Search"
          title="Search (coming soon)"
        >
          <span class="mdi mdi-magnify text-xl text-gray-600"></span>
        </button>

        <!-- Notifications -->
        <div class="relative">
          <button
            @click="toggleNotifications"
            class="p-2 rounded-lg hover:bg-gray-100 transition-colors relative"
            aria-label="Notifications"
          >
            <span class="mdi mdi-bell text-xl text-gray-600"></span>
            <!-- Notification badge -->
            <span
              v-if="notificationCount > 0"
              class="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"
            ></span>
          </button>

          <!-- Notifications Dropdown -->
          <div
            v-if="showNotifications"
            class="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-lg border border-gray-200 z-50"
          >
            <div class="p-4 border-b border-gray-200">
              <h3 class="text-sm font-semibold text-gray-900">Notifications</h3>
            </div>
            <div class="max-h-96 overflow-y-auto">
              <div
                v-if="notifications.length === 0"
                class="p-4 text-center text-gray-500 text-sm"
              >
                No new notifications
              </div>
              <div
                v-for="notification in notifications"
                :key="notification.id"
                class="p-4 hover:bg-gray-50 border-b border-gray-100 cursor-pointer"
              >
                <p class="text-sm text-gray-900">{{ notification.message }}</p>
                <p class="text-xs text-gray-500 mt-1">{{ notification.time }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- User Menu -->
        <div class="relative">
          <button
            @click="toggleUserMenu"
            class="flex items-center space-x-2 p-2 rounded-lg hover:bg-gray-100 transition-colors"
            aria-label="User menu"
          >
            <div class="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center">
              <span class="text-sm font-medium text-white">{{ userInitials }}</span>
            </div>
            <span class="hidden md:block text-sm font-medium text-gray-700">
              {{ currentUser?.username || 'Guest' }}
            </span>
            <span class="mdi mdi-chevron-down text-gray-600"></span>
          </button>

          <!-- User Menu Dropdown -->
          <div
            v-if="showUserMenu"
            class="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-lg border border-gray-200 z-50"
          >
            <div class="p-4 border-b border-gray-200">
              <p class="text-sm font-medium text-gray-900">
                {{ currentUser?.username || 'Guest' }}
              </p>
              <p class="text-xs text-gray-500 mt-1">
                {{ currentUser?.email || 'Not logged in' }}
              </p>
            </div>
            <div class="py-2">
              <button
                @click="handleLogout"
                class="w-full flex items-center px-4 py-2 text-sm text-red-600 hover:bg-gray-100"
              >
                <span class="mdi mdi-logout text-lg mr-3"></span>
                Logout
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useNavigationStore } from '@/stores/navigation'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const navigationStore = useNavigationStore()
const authStore = useAuthStore()

// State
const showNotifications = ref(false)
const showUserMenu = ref(false)

// Sample notifications (will come from API later)
const notifications = ref([
  { id: 1, message: 'Budget alert: Engineering dept at 85%', time: '5 min ago' },
  { id: 2, message: 'New booking requires approval', time: '1 hour ago' },
  { id: 3, message: 'Policy violation detected', time: '2 hours ago' }
])

// Computed
const currentUser = computed(() => authStore.user)

const userInitials = computed(() => {
  if (!currentUser.value?.username) return 'G'
  const username = currentUser.value.username
  return username.substring(0, 2).toUpperCase()
})

const notificationCount = computed(() => notifications.value.length)

const breadcrumbs = computed(() => {
  const path = route.path
  if (path === '/') return []
  
  const segments = path.split('/').filter(Boolean)
  return segments.map(segment => {
    // Convert kebab-case to Title Case
    return segment
      .split('-')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ')
  })
})

// Methods
const toggleSidebar = () => {
  navigationStore.toggleSidebar()
}

const toggleNotifications = () => {
  showNotifications.value = !showNotifications.value
  if (showNotifications.value) {
    showUserMenu.value = false
  }
}

const toggleUserMenu = () => {
  showUserMenu.value = !showUserMenu.value
  if (showUserMenu.value) {
    showNotifications.value = false
  }
}

const handleLogout = async () => {
  showUserMenu.value = false
  try {
    await authStore.logout()
    router.push('/login')
  } catch (error) {
    console.error('Logout error:', error)
  }
}

// Close dropdowns when clicking outside
const handleClickOutside = (event) => {
  const target = event.target
  const isNotificationButton = target.closest('[aria-label="Notifications"]')
  const isNotificationDropdown = target.closest('.absolute.right-0.mt-2.w-80')
  const isUserMenuButton = target.closest('[aria-label="User menu"]')
  const isUserMenuDropdown = target.closest('.absolute.right-0.mt-2.w-56')
  
  if (!isNotificationButton && !isNotificationDropdown) {
    showNotifications.value = false
  }
  
  if (!isUserMenuButton && !isUserMenuDropdown) {
    showUserMenu.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
/* Dropdown animations */
.absolute {
  animation: slideDown 0.2s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
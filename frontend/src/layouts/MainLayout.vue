<template>
  <div class="flex h-screen bg-gray-100">
    <!-- Sidebar -->
    <SideBar />

    <!-- Main Content Area -->
    <div class="flex-1 flex flex-col overflow-hidden">
      <!-- Top Bar -->
      <TopBar @toggle-sidebar="navigationStore.toggleSidebar" />
      
      <!-- Main Content -->
      <main class="flex-1 overflow-x-hidden overflow-y-auto bg-gray-100 p-6">
        <router-view />
      </main>
    </div>

    <!-- Mobile Overlay -->
    <div
      v-if="!navigationStore.isDesktop && !navigationStore.isSidebarCollapsed"
      class="fixed inset-0 bg-black bg-opacity-50 z-30 lg:hidden"
      @click="navigationStore.toggleSidebar"
    ></div>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue'
import SideBar from './SideBar.vue'
import TopBar from './TopBar.vue'
import { useNavigationStore } from '@/stores/navigation'
import { useKeyboardShortcuts } from '@/composables/useKeyboardShortcuts'
useKeyboardShortcuts() // Add this line

const navigationStore = useNavigationStore()

// Handle window resize for responsive behavior
const handleResize = () => {
  navigationStore.checkScreenSize()
}

onMounted(() => {
  // Initialize screen size
  navigationStore.checkScreenSize()
  
  // Add resize listener
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.main-layout {
  display: flex;
  min-height: 100vh;
  background-color: #f9fafb;
}

.main-layout__content {
  flex: 1;
  margin-left: 260px;
  display: flex;
  flex-direction: column;
  transition: margin-left 0.3s ease;
}

.main-layout--sidebar-collapsed .main-layout__content {
  margin-left: 70px;
}

.main-layout__main {
  flex: 1;
  padding: 2rem;
  overflow-y: auto;
}

.main-layout__footer {
  padding: 1.5rem 2rem;
  background-color: #ffffff;
  border-top: 1px solid #e5e7eb;
  text-align: center;
}

.main-layout__footer p {
  margin: 0;
  font-size: 0.875rem;
  color: #6b7280;
}

/* Responsive Design */
@media (max-width: 768px) {
  .main-layout__content {
    margin-left: 0;
  }

  .main-layout__main {
    padding: 1rem;
  }

  .main-layout__footer {
    padding: 1rem;
  }
}
</style>
<template>
  <div class="main-layout" :class="{ 'main-layout--sidebar-collapsed': isSidebarCollapsed }">
    <!-- Sidebar Navigation -->
    <SideBar @sidebar-toggle="handleSidebarToggle" />

    <!-- Main Content Area -->
    <div class="main-layout__content">
      <!-- Top Bar -->
      <TopBar />

      <!-- Page Content -->
      <main class="main-layout__main">
        <router-view />
      </main>

      <!-- Footer (Optional) -->
      <footer class="main-layout__footer">
        <p>&copy; {{ currentYear }} Travel Analytics. All rights reserved.</p>
      </footer>
    </div>
  </div>
</template>

<script>
import SideBar from './SideBar.vue'
import TopBar from './TopBar.vue'

export default {
  name: 'MainLayout',
  
  components: {
    SideBar,
    TopBar
  },

  data() {
    return {
      isSidebarCollapsed: false
    }
  },

  computed: {
    currentYear() {
      return new Date().getFullYear()
    }
  },

  methods: {
    handleSidebarToggle(collapsed) {
      this.isSidebarCollapsed = collapsed
    }
  }
}
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
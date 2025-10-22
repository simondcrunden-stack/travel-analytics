<template>
  <aside class="sidebar" :class="{ 'sidebar--collapsed': isCollapsed }">
    <!-- Sidebar Header -->
    <div class="sidebar__header">
      <div class="sidebar__logo">
        <span v-if="!isCollapsed" class="sidebar__logo-text">Travel Analytics</span>
        <span v-else class="sidebar__logo-icon">TA</span>
      </div>
      <button @click="toggleSidebar" class="sidebar__toggle" aria-label="Toggle sidebar">
        <i :class="isCollapsed ? 'mdi mdi-chevron-right' : 'mdi mdi-chevron-left'"></i>
      </button>
    </div>

    <!-- Navigation Menu -->
    <nav class="sidebar__nav">
      <ul class="nav-menu">
        <li v-for="item in mainNavItems" :key="item.path" class="nav-menu__item">
          <router-link 
            :to="item.path" 
            class="nav-menu__link"
            :class="{ 'nav-menu__link--active': isActiveRoute(item.path) }"
          >
            <i :class="item.icon" class="nav-menu__icon"></i>
            <span v-if="!isCollapsed" class="nav-menu__text">{{ item.label }}</span>
            <span v-if="item.badge && !isCollapsed" class="nav-menu__badge">{{ item.badge }}</span>
          </router-link>
        </li>
      </ul>

      <!-- Divider -->
      <div v-if="!isCollapsed" class="sidebar__divider"></div>

      <!-- Secondary Navigation -->
      <ul class="nav-menu nav-menu--secondary">
        <li v-for="item in secondaryNavItems" :key="item.path" class="nav-menu__item">
          <router-link 
            :to="item.path" 
            class="nav-menu__link"
            :class="{ 'nav-menu__link--active': isActiveRoute(item.path) }"
          >
            <i :class="item.icon" class="nav-menu__icon"></i>
            <span v-if="!isCollapsed" class="nav-menu__text">{{ item.label }}</span>
          </router-link>
        </li>
      </ul>
    </nav>

    <!-- Sidebar Footer -->
    <div class="sidebar__footer">
      <div v-if="!isCollapsed" class="sidebar__user">
        <img :src="userAvatar" alt="User" class="sidebar__user-avatar" />
        <div class="sidebar__user-info">
          <p class="sidebar__user-name">{{ userName }}</p>
          <p class="sidebar__user-role">{{ userRole }}</p>
        </div>
      </div>
      <button v-else class="sidebar__user-icon">
        <img :src="userAvatar" alt="User" class="sidebar__user-avatar" />
      </button>
    </div>
  </aside>
</template>

<script>
export default {
  name: 'Sidebar',
  
  data() {
    return {
      isCollapsed: false,
      mainNavItems: [
        { path: '/', label: 'Dashboard', icon: 'mdi mdi-view-dashboard' },
        { path: '/air', label: 'Air Travel', icon: 'mdi mdi-airplane' },
        { path: '/bookings', label: 'Bookings', icon: 'mdi mdi-calendar', badge: null },
        { path: '/accommodation', label: 'Accommodation', icon: 'mdi mdi-home' },
        { path: '/car-hire', label: 'Car Hire', icon: 'mdi mdi-car' },
        { path: '/service-fees', label: 'Service Fees', icon: 'mdi mdi-credit-card' },
        { path: '/compliance', label: 'Compliance', icon: 'mdi mdi-shield-check' },
        { path: '/budgets', label: 'Budgets', icon: 'mdi mdi-currency-usd' },
        // Comment out until views are created
        // { path: '/analytics', label: 'Analytics', icon: 'icon-chart' },
        // { path: '/travelers', label: 'Travelers', icon: 'icon-users' },
        // { path: '/reports', label: 'Reports', icon: 'icon-file-text' },
        // { path: '/policies', label: 'Policies', icon: 'icon-clipboard' }
      ],
      secondaryNavItems: [
        // Commented out until the views are created
        // { path: '/settings', label: 'Settings', icon: 'icon-settings' },
        // { path: '/help', label: 'Help & Support', icon: 'icon-help-circle' }
      ],
      userName: 'John Doe',
      userRole: 'Travel Manager',
      userAvatar: 'https://ui-avatars.com/api/?name=John+Doe&background=3b82f6&color=fff'
    }
  },

  computed: {
    currentRoute() {
      return this.$route.path
    }
  },

  methods: {
    toggleSidebar() {
      this.isCollapsed = !this.isCollapsed
      this.$emit('sidebar-toggle', this.isCollapsed)
      // Store preference in localStorage
      localStorage.setItem('sidebarCollapsed', this.isCollapsed)
    },

    isActiveRoute(path) {
      return this.currentRoute.startsWith(path)
    }
  },

  mounted() {
    // Restore sidebar state from localStorage
    const savedState = localStorage.getItem('sidebarCollapsed')
    if (savedState !== null) {
      this.isCollapsed = savedState === 'true'
    }
  }
}
</script>

<style scoped>
.sidebar {
  width: 260px;
  height: 100vh;
  background-color: #1a1d29;
  color: #ffffff;
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
  position: fixed;
  left: 0;
  top: 0;
  z-index: 1000;
}

.sidebar--collapsed {
  width: 70px;
}

/* Header */
.sidebar__header {
  padding: 1.5rem 1rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.sidebar__logo {
  flex: 1;
}

.sidebar__logo-full {
  height: 32px;
  width: auto;
}

.sidebar__logo-icon {
  height: 32px;
  width: 32px;
}

.sidebar__toggle {
  background: none;
  border: none;
  color: #ffffff;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.sidebar__toggle:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

/* Navigation */
.sidebar__nav {
  flex: 1;
  padding: 1rem 0;
  overflow-y: auto;
}

.nav-menu {
  list-style: none;
  padding: 0;
  margin: 0;
}

.nav-menu--secondary {
  margin-top: 1rem;
}

.nav-menu__item {
  margin: 0;
}

.nav-menu__link {
  display: flex;
  align-items: center;
  padding: 0.75rem 1rem;
  color: #a0aec0;
  text-decoration: none;
  transition: all 0.2s;
  position: relative;
}

.nav-menu__link:hover {
  background-color: rgba(255, 255, 255, 0.05);
  color: #ffffff;
}

.nav-menu__link--active {
  background-color: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
}

.nav-menu__link--active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background-color: #3b82f6;
}

.nav-menu__icon {
  font-size: 1.25rem;
  min-width: 1.5rem;
  margin-right: 0.75rem;
}

.sidebar--collapsed .nav-menu__icon {
  margin-right: 0;
}

.nav-menu__text {
  font-size: 0.9rem;
  font-weight: 500;
}

.nav-menu__badge {
  margin-left: auto;
  background-color: #ef4444;
  color: #ffffff;
  font-size: 0.75rem;
  padding: 0.125rem 0.5rem;
  border-radius: 12px;
  font-weight: 600;
}

/* Divider */
.sidebar__divider {
  height: 1px;
  background-color: rgba(255, 255, 255, 0.1);
  margin: 1rem 0;
}

/* Footer */
.sidebar__footer {
  padding: 1rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.sidebar__user {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.sidebar__user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
}

.sidebar__user-info {
  flex: 1;
  min-width: 0;
}

.sidebar__user-name {
  font-size: 0.875rem;
  font-weight: 600;
  margin: 0;
  color: #ffffff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sidebar__user-role {
  font-size: 0.75rem;
  margin: 0;
  color: #a0aec0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sidebar__user-icon {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
}

/* Scrollbar Styling */
.sidebar__nav::-webkit-scrollbar {
  width: 4px;
}

.sidebar__nav::-webkit-scrollbar-track {
  background: transparent;
}

.sidebar__nav::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
}

.sidebar__nav::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.3);
}
</style>
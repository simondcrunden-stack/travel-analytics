<template>
  <header class="topbar">
    <div class="topbar__left">
      <!-- Breadcrumbs -->
      <nav class="breadcrumbs">
        <ul class="breadcrumbs__list">
          <li v-for="(crumb, index) in breadcrumbs" :key="index" class="breadcrumbs__item">
            <router-link 
              v-if="index < breadcrumbs.length - 1" 
              :to="crumb.path"
              class="breadcrumbs__link"
            >
              {{ crumb.label }}
            </router-link>
            <span v-else class="breadcrumbs__current">{{ crumb.label }}</span>
            <i v-if="index < breadcrumbs.length - 1" class="breadcrumbs__separator mdi mdi-chevron-right"></i>
          </li>
        </ul>
      </nav>
    </div>

    <div class="topbar__right">
      <!-- Search -->
      <div class="topbar__search">
        <input 
          type="text" 
          placeholder="Search bookings, travelers..." 
          class="topbar__search-input"
          v-model="searchQuery"
          @focus="showSearchResults = true"
          @blur="hideSearchResults"
        />
        <i class="mdi mdi-magnify topbar__search-icon"></i>
        
        <!-- Search Results Dropdown -->
        <div v-if="showSearchResults && searchQuery" class="search-results">
          <div v-if="filteredResults.length > 0">
            <div 
              v-for="result in filteredResults" 
              :key="result.id"
              class="search-results__item"
              @click="navigateTo(result.path)"
            >
              <i :class="result.icon" class="search-results__icon"></i>
              <div class="search-results__content">
                <p class="search-results__title">{{ result.title }}</p>
                <p class="search-results__subtitle">{{ result.subtitle }}</p>
              </div>
            </div>
          </div>
          <div v-else class="search-results__empty">
            No results found
          </div>
        </div>
      </div>

      <!-- Notifications -->
      <div class="topbar__notifications">
        <button class="topbar__icon-btn" @click="toggleNotifications">
          <i class="mdi mdi-bell"></i>
          <span v-if="unreadCount > 0" class="topbar__badge">{{ unreadCount }}</span>
        </button>
        
        <!-- Notifications Dropdown -->
        <div v-if="showNotifications" class="notifications-dropdown">
          <div class="notifications-dropdown__header">
            <h3>Notifications</h3>
            <button @click="markAllAsRead" class="notifications-dropdown__mark-read">
              Mark all as read
            </button>
          </div>
          <div class="notifications-dropdown__list">
            <div 
              v-for="notification in notifications" 
              :key="notification.id"
              class="notification-item"
              :class="{ 'notification-item--unread': !notification.read }"
            >
              <div class="notification-item__icon">
                <i :class="notification.icon"></i>
              </div>
              <div class="notification-item__content">
                <p class="notification-item__title">{{ notification.title }}</p>
                <p class="notification-item__message">{{ notification.message }}</p>
                <p class="notification-item__time">{{ notification.time }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- User Menu -->
      <div class="topbar__user">
        <button class="topbar__user-btn" @click="toggleUserMenu">
          <img :src="userAvatar" alt="User" class="topbar__user-avatar" />
          <span class="topbar__user-name">{{ userName }}</span>
          <i class="mdi mdi-chevron-down topbar__user-chevron"></i>
        </button>
        
        <!-- User Menu Dropdown -->
        <div v-if="showUserMenu" class="user-menu-dropdown">
          <div class="user-menu-dropdown__header">
            <img :src="userAvatar" alt="User" class="user-menu-dropdown__avatar" />
            <div>
              <p class="user-menu-dropdown__name">{{ userName }}</p>
              <p class="user-menu-dropdown__email">{{ userEmail }}</p>
            </div>
          </div>
          <ul class="user-menu-dropdown__list">
            <li v-for="item in userMenuItems" :key="item.path">
              <router-link :to="item.path" class="user-menu-dropdown__link">
                <i :class="item.icon"></i>
                {{ item.label }}
              </router-link>
            </li>
          </ul>
          <div class="user-menu-dropdown__footer">
            <button @click="logout" class="user-menu-dropdown__logout">
              <i class="mdi mdi-logout"></i>
              Sign Out
            </button>
          </div>
        </div>
      </div>
    </div>
  </header>
</template>

<script>
export default {
  name: 'TopBar',
  
  data() {
    return {
      searchQuery: '',
      showSearchResults: false,
      showNotifications: false,
      showUserMenu: false,
      unreadCount: 3,
      userName: 'John Doe',
      userEmail: 'john.doe@company.com',
      userAvatar: 'https://ui-avatars.com/api/?name=John+Doe&background=3b82f6&color=fff',
      notifications: [
        {
          id: 1,
          icon: 'mdi mdi-alert-circle',
          title: 'Policy Violation',
          message: 'Booking #12345 exceeds policy limits',
          time: '5 minutes ago',
          read: false
        },
        {
          id: 2,
          icon: 'mdi mdi-check-circle',
          title: 'Booking Confirmed',
          message: 'Flight to Sydney confirmed',
          time: '1 hour ago',
          read: false
        },
        {
          id: 3,
          icon: 'mdi mdi-information',
          title: 'New Report Available',
          message: 'Q3 Travel Analytics Report is ready',
          time: '3 hours ago',
          read: true
        }
      ],
      userMenuItems: [
        // Commented out until views are created
        // { path: '/profile', label: 'My Profile', icon: 'mdi mdi-account' },
        // { path: '/settings', label: 'Settings', icon: 'mdi mdi-account' },
        // { path: '/preferences', label: 'Preferences', icon: 'mdi mdi-tune' }
      ],
      searchResults: [
        {
          id: 1,
          title: 'Booking #12345',
          subtitle: 'Sydney to Melbourne - John Smith',
          icon: 'mdi mdi-calendar',
          path: '/bookings/12345'
        },
        {
          id: 2,
          title: 'Jane Cooper',
          subtitle: 'Frequent Traveler',
          icon: 'icon-user',
          path: '/travelers/jane-cooper'
        }
      ]
    }
  },

  computed: {
    breadcrumbs() {
      const route = this.$route
      const breadcrumbs = []
      
      // Build breadcrumbs from route meta or path
      if (route.meta && route.meta.breadcrumbs) {
        return route.meta.breadcrumbs
      }
      
      // Default breadcrumb generation
      const paths = route.path.split('/').filter(p => p)
      paths.forEach((path, index) => {
        const routePath = '/' + paths.slice(0, index + 1).join('/')
        breadcrumbs.push({
          label: path.charAt(0).toUpperCase() + path.slice(1),
          path: routePath
        })
      })
      
      return breadcrumbs
    },

    filteredResults() {
      if (!this.searchQuery) return []
      const query = this.searchQuery.toLowerCase()
      return this.searchResults.filter(result => 
        result.title.toLowerCase().includes(query) ||
        result.subtitle.toLowerCase().includes(query)
      )
    }
  },

  methods: {
    toggleNotifications() {
      this.showNotifications = !this.showNotifications
      this.showUserMenu = false
    },

    toggleUserMenu() {
      this.showUserMenu = !this.showUserMenu
      this.showNotifications = false
    },

    hideSearchResults() {
      setTimeout(() => {
        this.showSearchResults = false
      }, 200)
    },

    navigateTo(path) {
      this.$router.push(path)
      this.showSearchResults = false
      this.searchQuery = ''
    },

    markAllAsRead() {
      this.notifications.forEach(n => n.read = true)
      this.unreadCount = 0
    },

    logout() {
      // Implement logout logic
      console.log('Logging out...')
      this.$router.push('/login')
    }
  }
}
</script>

<style scoped>
.topbar {
  height: 64px;
  background-color: #ffffff;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 1.5rem;
  position: sticky;
  top: 0;
  z-index: 900;
}

.topbar__left,
.topbar__right {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

/* Breadcrumbs */
.breadcrumbs__list {
  display: flex;
  align-items: center;
  list-style: none;
  padding: 0;
  margin: 0;
  gap: 0.5rem;
}

.breadcrumbs__item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.breadcrumbs__link {
  color: #6b7280;
  text-decoration: none;
  font-size: 0.875rem;
  transition: color 0.2s;
}

.breadcrumbs__link:hover {
  color: #3b82f6;
}

.breadcrumbs__current {
  color: #111827;
  font-size: 0.875rem;
  font-weight: 600;
}

.breadcrumbs__separator {
  font-size: 0.75rem;
  color: #9ca3af;
}

/* Search */
.topbar__search {
  position: relative;
  width: 320px;
}

.topbar__search-input {
  width: 100%;
  padding: 0.5rem 1rem 0.5rem 2.5rem;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-size: 0.875rem;
  transition: all 0.2s;
}

.topbar__search-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.topbar__search-icon {
  position: absolute;
  left: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  color: #9ca3af;
  pointer-events: none;
}

.search-results {
  position: absolute;
  top: calc(100% + 0.5rem);
  left: 0;
  right: 0;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  max-height: 400px;
  overflow-y: auto;
  z-index: 1000;
}

.search-results__item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  cursor: pointer;
  transition: background-color 0.2s;
}

.search-results__item:hover {
  background-color: #f9fafb;
}

.search-results__icon {
  font-size: 1.25rem;
  color: #6b7280;
}

.search-results__content {
  flex: 1;
}

.search-results__title {
  font-size: 0.875rem;
  font-weight: 600;
  color: #111827;
  margin: 0 0 0.25rem 0;
}

.search-results__subtitle {
  font-size: 0.75rem;
  color: #6b7280;
  margin: 0;
}

.search-results__empty {
  padding: 2rem 1rem;
  text-align: center;
  color: #6b7280;
  font-size: 0.875rem;
}

/* Icon Button */
.topbar__icon-btn {
  position: relative;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 8px;
  color: #6b7280;
  transition: all 0.2s;
}

.topbar__icon-btn:hover {
  background-color: #f9fafb;
  color: #111827;
}

.topbar__badge {
  position: absolute;
  top: 0.25rem;
  right: 0.25rem;
  background-color: #ef4444;
  color: #ffffff;
  font-size: 0.625rem;
  padding: 0.125rem 0.375rem;
  border-radius: 10px;
  font-weight: 600;
}

/* Notifications Dropdown */
.topbar__notifications {
  position: relative;
}

.notifications-dropdown {
  position: absolute;
  top: calc(100% + 0.5rem);
  right: 0;
  width: 360px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  z-index: 1000;
}

.notifications-dropdown__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  border-bottom: 1px solid #e5e7eb;
}

.notifications-dropdown__header h3 {
  font-size: 1rem;
  font-weight: 600;
  margin: 0;
}

.notifications-dropdown__mark-read {
  background: none;
  border: none;
  color: #3b82f6;
  font-size: 0.75rem;
  cursor: pointer;
  font-weight: 500;
}

.notifications-dropdown__list {
  max-height: 400px;
  overflow-y: auto;
}

.notification-item {
  display: flex;
  gap: 0.75rem;
  padding: 1rem;
  border-bottom: 1px solid #f3f4f6;
  transition: background-color 0.2s;
}

.notification-item:hover {
  background-color: #f9fafb;
}

.notification-item--unread {
  background-color: #eff6ff;
}

.notification-item__icon {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background-color: #dbeafe;
  color: #3b82f6;
  display: flex;
  align-items: center;
  justify-content: center;
}

.notification-item__content {
  flex: 1;
}

.notification-item__title {
  font-size: 0.875rem;
  font-weight: 600;
  margin: 0 0 0.25rem 0;
}

.notification-item__message {
  font-size: 0.75rem;
  color: #6b7280;
  margin: 0 0 0.25rem 0;
}

.notification-item__time {
  font-size: 0.625rem;
  color: #9ca3af;
  margin: 0;
}

/* User Menu */
.topbar__user {
  position: relative;
}

.topbar__user-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.25rem 0.5rem;
  border-radius: 8px;
  transition: background-color 0.2s;
}

.topbar__user-btn:hover {
  background-color: #f9fafb;
}

.topbar__user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  object-fit: cover;
}

.topbar__user-name {
  font-size: 0.875rem;
  font-weight: 500;
  color: #111827;
}

.topbar__user-chevron {
  font-size: 0.75rem;
  color: #6b7280;
}

.user-menu-dropdown {
  position: absolute;
  top: calc(100% + 0.5rem);
  right: 0;
  width: 240px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  z-index: 1000;
}

.user-menu-dropdown__header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem;
  border-bottom: 1px solid #e5e7eb;
}

.user-menu-dropdown__avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  object-fit: cover;
}

.user-menu-dropdown__name {
  font-size: 0.875rem;
  font-weight: 600;
  margin: 0 0 0.25rem 0;
}

.user-menu-dropdown__email {
  font-size: 0.75rem;
  color: #6b7280;
  margin: 0;
}

.user-menu-dropdown__list {
  list-style: none;
  padding: 0.5rem 0;
  margin: 0;
}

.user-menu-dropdown__link {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  color: #374151;
  text-decoration: none;
  font-size: 0.875rem;
  transition: background-color 0.2s;
}

.user-menu-dropdown__link:hover {
  background-color: #f9fafb;
}

.user-menu-dropdown__footer {
  padding: 0.5rem;
  border-top: 1px solid #e5e7eb;
}

.user-menu-dropdown__logout {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  background: none;
  border: none;
  color: #ef4444;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  border-radius: 6px;
  transition: background-color 0.2s;
}

.user-menu-dropdown__logout:hover {
  background-color: #fef2f2;
}
</style>
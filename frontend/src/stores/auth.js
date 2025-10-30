import { defineStore } from 'pinia'
import authService from '@/services/authService'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: JSON.parse(localStorage.getItem('user')) || null,
    accessToken: localStorage.getItem('access_token') || null,
    refreshToken: localStorage.getItem('refresh_token') || null,
    loading: false,
    error: null,
  }),

  getters: {
    isAuthenticated: (state) => !!state.accessToken,
    userType: (state) => state.user?.user_type || null,
    userName: (state) => {
      if (!state.user) return ''
      return `${state.user.first_name} ${state.user.last_name}`.trim() || state.user.username
    },
  },

  actions: {
    async login(username, password) {
      this.loading = true
      this.error = null

      try {
        const data = await authService.login(username, password)
        
        this.accessToken = data.access
        this.refreshToken = data.refresh
        
        localStorage.setItem('access_token', data.access)
        localStorage.setItem('refresh_token', data.refresh)

        await this.fetchCurrentUser()

        return true
      } catch (error) {
        this.error = error.response?.data?.detail || 'Login failed'
        throw error
      } finally {
        this.loading = false
      }
    },

    async fetchCurrentUser() {
      try {
        const user = await authService.getCurrentUser()
        this.user = user
        localStorage.setItem('user', JSON.stringify(user))
      } catch (error) {
        console.error('Failed to fetch user:', error)
        this.logout()
      }
    },

    logout() {
      this.user = null
      this.accessToken = null
      this.refreshToken = null
      authService.logout()
    },
  },
})

import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor - add JWT token to all requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor - handle token expiry
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        const refreshToken = localStorage.getItem('refresh_token')
        const response = await axios.post(
          'http://localhost:8000/api/v1/auth/refresh/',
          { refresh: refreshToken }
        )

        const { access } = response.data
        localStorage.setItem('access_token', access)

        originalRequest.headers.Authorization = `Bearer ${access}`
        return api(originalRequest)
      } catch (refreshError) {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)

// ============================================================================
// BOOKING SERVICE
// ============================================================================

export const bookingService = {
  async getBookings(params = {}) {
    const response = await api.get('/bookings/', { params })
    return response.data
  },

  async getBooking(id) {
    const response = await api.get(`/bookings/${id}/`)
    return response.data
  },

  async getSummary(params = {}) {
    const response = await api.get('/bookings/summary/', { params })
    return response.data
  },

  async getAirBookings(params = {}) {
    const response = await api.get('/bookings/', {
      params: { ...params, booking_type: 'AIR' },
    })
    return response.data
  },

  async getAccommodationBookings(params = {}) {
    const response = await api.get('/bookings/', {
      params: { ...params, booking_type: 'HOTEL' },
    })
    return response.data
  },

  async getCarHireBookings(params = {}) {
    const response = await api.get('/bookings/', {
      params: { ...params, booking_type: 'CAR' },
    })
    return response.data
  },

  async getServiceFees(params = {}) {
    const response = await api.get('/service-fees/', { params })
    return response.data
  },

  async getAvailableCountries(params = {}) {
    const response = await api.get('/bookings/available_countries/', { params })
    return response.data
  },
}

// ============================================================================
// USER SERVICE
// ============================================================================

export const userService = {
  async getFilterPreferences() {
    const response = await api.get('/users/filter_preferences/')
    return response.data
  },

  async saveFilterPreferences(filters, homeCountry = 'AU') {
    const response = await api.put('/users/filter_preferences/', {
      default_filters: filters,
      home_country: homeCountry,
    })
    return response.data
  },

  async getProfile() {
    const response = await api.get('/users/me/')
    return response.data
  },
}

// ============================================================================
// AUTH SERVICE
// ============================================================================

export const authService = {
  async login(credentials) {
    const response = await api.post('/auth/login/', credentials)
    return response.data
  },

  async logout() {
    const refreshToken = localStorage.getItem('refresh_token')
    if (refreshToken) {
      await api.post('/auth/logout/', { refresh: refreshToken })
    }
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  },

  async refresh() {
    const refreshToken = localStorage.getItem('refresh_token')
    const response = await api.post('/auth/refresh/', { refresh: refreshToken })
    return response.data
  },
}

// Export the base api instance as default
export default api
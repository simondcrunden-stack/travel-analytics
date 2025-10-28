// src/services/bookingService.js
import api from './api'

export default {
  // Main bookings list with filtering
  async getBookings(params = {}) {
    const response = await api.get('/bookings/', { params })
    return response.data
  },

  // Get single booking detail
  async getBooking(id) {
    const response = await api.get(`/bookings/${id}/`)
    return response.data
  },

  // Dashboard summary statistics
  async getSummary(params = {}) {
    const response = await api.get('/bookings/summary/', { params })
    return response.data
  },

  // Carbon emissions report
  async getCarbonReport(params = {}) {
    const response = await api.get('/bookings/carbon_report/', { params })
    return response.data
  },

  // Airline spend analysis
  async getAirlineSpend(params = {}) {
    const response = await api.get('/bookings/', {
      params: {
        booking_type: 'AIR',
        ...params
      }
    })
    return response.data
  },

  // Accommodation spend analysis
  async getAccommodationSpend(params = {}) {
    const response = await api.get('/bookings/', {
      params: {
        booking_type: 'HOTEL',
        ...params
      }
    })
    return response.data
  },

  // Car hire spend analysis
  async getCarHireSpend(params = {}) {
    const response = await api.get('/bookings/', {
      params: {
        booking_type: 'CAR',
        ...params
      }
    })
    return response.data
  },

  // Service fees
  async getServiceFees(params = {}) {
    const response = await api.get('/service-fees/', { params })
    return response.data
  },

  // Budget tracking
  async getBudgets(params = {}) {
    const response = await api.get('/budgets/', { params })
    return response.data
  },

  // Compliance violations
  async getViolations(params = {}) {
    const response = await api.get('/compliance-violations/', { params })
    return response.data
  },

  // Travellers
  async getTravellers(params = {}) {
    const response = await api.get('/travellers/', { params })
    return response.data
  },

  // Traveller bookings
  async getTravellerBookings(travellerId) {
    const response = await api.get(`/travellers/${travellerId}/bookings/`)
    return response.data
  },

  // Get airports for reference
  async getAirports(params = {}) {
    const response = await api.get('/airports/', { params })
    return response.data
  },

  // Get airlines for reference
  async getAirlines(params = {}) {
    const response = await api.get('/airlines/', { params })
    return response.data
  },

  // Get available countries (countries that have booking data)
  async getAvailableCountries(params = {}) {
    const response = await api.get('/countries/available/', { params })
    return response.data
  },

  // Get all countries
  async getCountries(params = {}) {
    const response = await api.get('/countries/', { params })
    return response.data
  },

  // Helper: Calculate totals from bookings
  calculateTotals(bookings) {
    return bookings.reduce((acc, booking) => {
      acc.total += parseFloat(booking.total_amount || 0)
      acc.count += 1
      return acc
    }, { total: 0, count: 0 })
  },

  // Helper: Group bookings by field
  groupBy(bookings, field) {
    return bookings.reduce((acc, booking) => {
      const key = booking[field] || 'Unknown'
      if (!acc[key]) {
        acc[key] = []
      }
      acc[key].push(booking)
      return acc
    }, {})
  },

  // Helper: Format currency
  formatCurrency(amount, currency = 'AUD') {
    return new Intl.NumberFormat('en-AU', {
      style: 'currency',
      currency: currency,
    }).format(amount)
  },

  // Helper: Format date
  formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-AU', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  },
}
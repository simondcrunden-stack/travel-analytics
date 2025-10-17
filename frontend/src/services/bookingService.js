import api from './api'

export default {
  async getBookings(params = {}) {
    const response = await api.get('/bookings/', { params })
    return response.data
  },

  async getBooking(id) {
    const response = await api.get(`/bookings/${id}/`)
    return response.data
  },

  async getBookingSummary(params = {}) {
    const response = await api.get('/bookings/summary/', { params })
    return response.data
  },

  async getOrganizations() {
    const response = await api.get('/organizations/')
    return response.data
  },

  async getTravellers(params = {}) {
    const response = await api.get('/travellers/', { params })
    return response.data
  },
}

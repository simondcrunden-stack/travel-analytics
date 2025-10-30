import api from './api'

export default {
  /**
   * Get comprehensive dashboard statistics
   * @param {Object} params - Filter parameters
   * @param {string} params.start_date - Start date (YYYY-MM-DD)
   * @param {string} params.end_date - End date (YYYY-MM-DD)
   * @param {string} params.organization - Organization ID
   * @returns {Promise} Dashboard stats
   */
  async getDashboardStats(params = {}) {
    const response = await api.get('/bookings/summary/', { params })
    return response.data
  },

  /**
   * Get spend breakdown by category
   */
  async getSpendBreakdown(params = {}) {
    const response = await api.get('/bookings/', { params })
    const bookings = response.data.results || response.data

    // Calculate totals by category
    const breakdown = {
      total: 0,
      air: 0,
      accommodation: 0,
      car: 0,
      service_fees: 0,
      other: 0,
      bookings_count: bookings.length,
    }

    bookings.forEach((booking) => {
      const amount = parseFloat(booking.total_amount) || 0
      breakdown.total += amount

      switch (booking.booking_type) {
        case 'AIR':
          breakdown.air += amount
          break
        case 'HOTEL':
          breakdown.accommodation += amount
          break
        case 'CAR':
          breakdown.car += amount
          break
        default:
          breakdown.other += amount
      }
    })

    return breakdown
  },

  /**
   * Get transaction summary
   */
  async getTransactionSummary(params = {}) {
    const response = await api.get('/bookings/', { params })
    const bookings = response.data.results || response.data

    const summary = {
      total_bookings: bookings.length,
      hotel_nights: 0,
      car_hire_days: 0,
      service_fees: 0,
    }

    // Calculate hotel nights and car hire days
    bookings.forEach((booking) => {
      if (booking.booking_type === 'HOTEL' && booking.accommodation_details) {
        summary.hotel_nights += booking.accommodation_details.number_of_nights || 0
      }
      if (booking.booking_type === 'CAR' && booking.car_hire_details) {
        summary.car_hire_days += booking.car_hire_details.number_of_days || 0
      }
    })

    return summary
  },

  /**
   * Get compliance metrics
   */
  async getComplianceMetrics(params = {}) {
    // TODO: This will use the compliance violations API once available
    // For now, return mock data structure
    return {
      total_bookings: 0,
      compliant_bookings: 0,
      compliance_rate: 0,
      online_booking_rate: 0,
      cost_of_change: 0,
      lowest_fare_compliance: 0,
    }
  },
}
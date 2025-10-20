import api from './api'

/**
 * Get compliance summary metrics
 */
export async function getComplianceSummary(params = {}) {
  try {
    const response = await api.get('/bookings/', { params })
    const bookings = response.data.results || response.data

    const summary = {
      total_bookings: bookings.length,
      compliant_bookings: 0,
      non_compliant_bookings: 0,
      compliance_rate: 0,
      
      // Detailed metrics
      online_booking_count: 0,
      online_booking_rate: 0,
      
      lowest_fare_compliant: 0,
      lowest_fare_rate: 0,
      
      advance_booking_compliant: 0,
      advance_booking_rate: 0,
      
      // Financial impact
      cost_of_change: 0,
      out_of_policy_spend: 0,
      potential_savings: 0,
    }

    bookings.forEach((booking) => {
      // Overall compliance (placeholder - will use violations API later)
      const isCompliant = booking.policy_compliant !== false
      if (isCompliant) {
        summary.compliant_bookings++
      } else {
        summary.non_compliant_bookings++
      }

      // Online booking compliance (mock - need to add field)
      // Assuming 89% are booked online based on your screenshot
      if (Math.random() > 0.11) {
        summary.online_booking_count++
      }

      // Advance booking compliance
      if (booking.advance_booking_days && booking.advance_booking_days >= 7) {
        summary.advance_booking_compliant++
      }

      // Lowest fare compliance (mock - need violations data)
      if (booking.booking_type === 'AIR' && isCompliant) {
        summary.lowest_fare_compliant++
      }
    })

    // Calculate rates
    if (summary.total_bookings > 0) {
      summary.compliance_rate = (summary.compliant_bookings / summary.total_bookings) * 100
      summary.online_booking_rate = (summary.online_booking_count / summary.total_bookings) * 100
      
      const airBookings = bookings.filter(b => b.booking_type === 'AIR').length
      if (airBookings > 0) {
        summary.lowest_fare_rate = (summary.lowest_fare_compliant / airBookings) * 100
        summary.advance_booking_rate = (summary.advance_booking_compliant / airBookings) * 100
      }
    }

    // Mock financial data (will be calculated from violations)
    summary.cost_of_change = 3015445.64
    summary.out_of_policy_spend = 1245380.22
    summary.potential_savings = 892450.00

    return summary
  } catch (error) {
    console.error('Error fetching compliance summary:', error)
    throw error
  }
}

/**
 * Get detailed compliance violations
 */
export async function getComplianceViolations(params = {}) {
  try {
    const response = await api.get('/compliance/violations/', { params })
    return response.data
  } catch (error) {
    console.error('Error fetching compliance violations:', error)
    // Return empty array if endpoint doesn't exist yet
    return []
  }
}

export default {
  getComplianceSummary,
  getComplianceViolations,
}
<template>
  <div class="booking-details">
    <!-- Air Segments Section -->
    <div v-if="booking.air_bookings?.length > 0" class="detail-section">
      <h4 class="detail-section-title">
        <span class="mdi mdi-airplane"></span>
        Air Travel ({{ totalAirSegments }} segment{{ totalAirSegments > 1 ? 's' : '' }})
      </h4>
      <div class="detail-grid">
        <div v-for="segment in allAirSegments" :key="segment.id" class="detail-card">
          <div class="detail-row">
            <span class="detail-label">Route:</span>
            <span class="detail-value">{{ segment.origin_airport_iata_code }} → {{ segment.destination_airport_iata_code }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Airline:</span>
            <span class="detail-value">{{ segment.airline_name }} ({{ segment.flight_number }})</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Date:</span>
            <span class="detail-value">{{ formatDate(segment.departure_date) }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Time:</span>
            <span class="detail-value">{{ formatTime(segment.departure_time) }} - {{ formatTime(segment.arrival_time) }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Class:</span>
            <span class="detail-value">{{ segment.booking_class }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Distance:</span>
            <span class="detail-value">{{ segment.distance_km?.toLocaleString() }} km</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Carbon:</span>
            <span class="detail-value font-semibold text-emerald-600">{{ segment.carbon_emissions_kg }} kg CO₂</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Accommodation Section -->
    <div v-if="booking.accommodation_bookings?.length > 0" class="detail-section">
      <h4 class="detail-section-title">
        <span class="mdi mdi-hotel"></span>
        Accommodation ({{ booking.accommodation_bookings.length }} hotel{{ booking.accommodation_bookings.length > 1 ? 's' : '' }})
      </h4>
      <div class="detail-grid">
        <div v-for="hotel in booking.accommodation_bookings" :key="hotel.id" class="detail-card">
          <div class="detail-row">
            <span class="detail-label">Hotel:</span>
            <span class="detail-value">{{ hotel.hotel_name }}</span>
          </div>
          <div class="detail-row" v-if="hotel.hotel_chain">
            <span class="detail-label">Chain:</span>
            <span class="detail-value">{{ hotel.hotel_chain }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Location:</span>
            <span class="detail-value">{{ hotel.city }}, {{ hotel.country }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Check-in:</span>
            <span class="detail-value">{{ formatDate(hotel.check_in_date) }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Check-out:</span>
            <span class="detail-value">{{ formatDate(hotel.check_out_date) }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Nights:</span>
            <span class="detail-value">{{ hotel.number_of_nights }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Room Type:</span>
            <span class="detail-value">{{ hotel.room_type }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Nightly Rate:</span>
            <span class="detail-value">{{ formatCurrency(hotel.nightly_rate, hotel.currency) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Car Hire Section -->
    <div v-if="booking.car_hire_bookings?.length > 0" class="detail-section">
      <h4 class="detail-section-title">
        <span class="mdi mdi-car"></span>
        Car Hire ({{ booking.car_hire_bookings.length }} rental{{ booking.car_hire_bookings.length > 1 ? 's' : '' }})
      </h4>
      <div class="detail-grid">
        <div v-for="car in booking.car_hire_bookings" :key="car.id" class="detail-card">
          <div class="detail-row">
            <span class="detail-label">Company:</span>
            <span class="detail-value">{{ car.rental_company }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Vehicle:</span>
            <span class="detail-value">{{ car.vehicle_make_model || car.vehicle_category }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Type:</span>
            <span class="detail-value">{{ car.vehicle_type }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Pick-up:</span>
            <span class="detail-value">{{ car.pickup_city }} - {{ formatDate(car.pickup_date) }} {{ formatTime(car.pickup_time) }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Drop-off:</span>
            <span class="detail-value">{{ car.dropoff_city }} - {{ formatDate(car.dropoff_date) }} {{ formatTime(car.dropoff_time) }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Days:</span>
            <span class="detail-value">{{ car.number_of_days }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Daily Rate:</span>
            <span class="detail-value">{{ formatCurrency(car.daily_rate, car.currency) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-if="!hasAnySegments" class="text-center py-8 text-gray-500">
      <span class="mdi mdi-information-outline text-4xl mb-2 block"></span>
      <p>No detailed segment information available for this booking.</p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  booking: {
    type: Object,
    required: true
  }
})

// Computed properties
const allAirSegments = computed(() => {
  const segments = []
  if (props.booking.air_bookings) {
    props.booking.air_bookings.forEach(airBooking => {
      if (airBooking.segments) {
        segments.push(...airBooking.segments)
      }
    })
  }
  return segments
})

const totalAirSegments = computed(() => allAirSegments.value.length)

const hasAnySegments = computed(() => {
  return (props.booking.air_bookings?.length > 0) ||
         (props.booking.accommodation_bookings?.length > 0) ||
         (props.booking.car_hire_bookings?.length > 0)
})

// Helper functions
const formatCurrency = (amount, currency = 'AUD') => {
  if (!amount) return '-'
  return new Intl.NumberFormat('en-AU', {
    style: 'currency',
    currency: currency || 'AUD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(amount)
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString('en-AU', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

const formatTime = (timeString) => {
  if (!timeString) return '-'
  // Handle HH:MM:SS format
  const parts = timeString.split(':')
  if (parts.length >= 2) {
    return `${parts[0]}:${parts[1]}`
  }
  return timeString
}
</script>

<style scoped>
.booking-details {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  padding: 1rem 0;
}

.detail-section {
  border-left: 3px solid #3b82f6;
  padding-left: 1rem;
}

.detail-section-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1rem;
  font-weight: 600;
  color: #374151;
  margin-bottom: 0.75rem;
}

.detail-section-title .mdi {
  font-size: 1.25rem;
  color: #3b82f6;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 1rem;
}

.detail-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 1rem;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  padding: 0.5rem 0;
  border-bottom: 1px solid #f3f4f6;
}

.detail-row:last-child {
  border-bottom: none;
}

.detail-label {
  font-size: 0.875rem;
  color: #6b7280;
  font-weight: 500;
}

.detail-value {
  font-size: 0.875rem;
  color: #111827;
  font-weight: 400;
  text-align: right;
}
</style>
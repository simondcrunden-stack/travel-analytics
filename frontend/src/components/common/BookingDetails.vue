<template>
  <div class="booking-details">
    <!-- Trip Segments Section -->
    <div v-if="allSegments.length > 0" class="detail-section">
      <h4 class="detail-section-title">
        <span class="mdi mdi-map-marker-path"></span>
        Trip Itinerary ({{ allSegments.length }} item{{ allSegments.length > 1 ? 's' : '' }})
      </h4>

      <!-- Segments Table -->
      <div class="overflow-x-auto">
        <table class="segments-table">
          <thead>
            <tr>
              <th>Type</th>
              <th>Date</th>
              <th>Details</th>
              <th>Duration/Nights/Days</th>
              <th>Amount</th>
              <th>Carbon</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="segment in sortedSegments" :key="segment.id" class="segment-row">
              <!-- Type Column -->
              <td>
                <div class="flex items-center">
                  <span class="mdi" :class="getTypeIcon(segment.type)"></span>
                  <span class="ml-2 font-medium">{{ segment.typeName }}</span>
                </div>
              </td>

              <!-- Date Column -->
              <td>
                <div class="text-sm">{{ formatDate(segment.date) }}</div>
              </td>

              <!-- Details Column -->
              <td>
                <!-- Air Segment -->
                <div v-if="segment.type === 'air'" class="segment-details">
                  <div class="font-medium">{{ segment.data.origin_airport_iata_code }} → {{ segment.data.destination_airport_iata_code }}</div>
                  <div class="text-xs text-gray-500">
                    {{ segment.data.origin_city }} → {{ segment.data.destination_city }}
                  </div>
                  <div class="text-xs text-gray-500">
                    {{ segment.data.airline_name }} {{ segment.data.flight_number }} • {{ segment.data.booking_class }}
                  </div>
                </div>

                <!-- Accommodation Segment -->
                <div v-else-if="segment.type === 'accommodation'" class="segment-details">
                  <div class="font-medium">{{ segment.data.hotel_name }}</div>
                  <div class="text-xs text-gray-500">{{ segment.data.city }}, {{ segment.data.country }}</div>
                  <div class="text-xs text-gray-500">{{ segment.data.room_type }}</div>
                </div>

                <!-- Car Hire Segment -->
                <div v-else-if="segment.type === 'car'" class="segment-details">
                  <div class="font-medium">{{ segment.data.rental_company }}</div>
                  <div class="text-xs text-gray-500">{{ segment.data.vehicle_make_model || segment.data.vehicle_category }}</div>
                  <div class="text-xs text-gray-500">{{ segment.data.pickup_city }}</div>
                </div>
              </td>

              <!-- Duration/Nights/Days Column -->
              <td>
                <span v-if="segment.type === 'air'" class="text-sm">
                  {{ formatTime(segment.data.departure_time) }} - {{ formatTime(segment.data.arrival_time) }}
                </span>
                <span v-else-if="segment.type === 'accommodation'" class="text-sm">
                  {{ segment.data.number_of_nights }} night{{ segment.data.number_of_nights > 1 ? 's' : '' }}
                </span>
                <span v-else-if="segment.type === 'car'" class="text-sm">
                  {{ segment.data.number_of_days }} day{{ segment.data.number_of_days > 1 ? 's' : '' }}
                </span>
              </td>

              <!-- Amount Column -->
              <td>
                <span v-if="segment.amount" class="text-sm font-medium">
                  {{ formatCurrency(segment.amount, segment.currency) }}
                </span>
                <span v-else class="text-xs text-gray-400">-</span>
              </td>

              <!-- Carbon Column -->
              <td>
                <span v-if="segment.carbon" class="text-sm text-emerald-600 font-medium">
                  {{ segment.carbon }} kg
                </span>
                <span v-else class="text-xs text-gray-400">-</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Service Fees Section -->
    <div v-if="booking.service_fees?.length > 0" class="detail-section mt-6">
      <h4 class="detail-section-title">
        <span class="mdi mdi-cash-multiple"></span>
        Service Fees ({{ booking.service_fees.length }})
      </h4>

      <div class="overflow-x-auto">
        <table class="segments-table">
          <thead>
            <tr>
              <th>Fee Type</th>
              <th>Date</th>
              <th>Invoice #</th>
              <th>Channel</th>
              <th>GST</th>
              <th>Total</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="fee in booking.service_fees" :key="fee.id" class="segment-row">
              <td>
                <div class="text-sm font-medium">{{ formatFeeType(fee.fee_type) }}</div>
                <div v-if="fee.description" class="text-xs text-gray-500">{{ fee.description }}</div>
              </td>
              <td class="text-sm">{{ formatDate(fee.fee_date) }}</td>
              <td class="text-sm">{{ fee.invoice_number || '-' }}</td>
              <td class="text-sm">{{ fee.booking_channel || '-' }}</td>
              <td class="text-sm">{{ formatCurrency(fee.gst_amount, fee.currency) }}</td>
              <td class="text-sm font-medium">{{ formatCurrency(fee.fee_amount, fee.currency) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Transactions Section -->
    <div v-if="booking.transactions?.length > 0" class="detail-section mt-6">
      <h4 class="detail-section-title">
        <span class="mdi mdi-swap-horizontal"></span>
        Transactions ({{ booking.transactions.length }})
      </h4>

      <div class="overflow-x-auto">
        <table class="segments-table">
          <thead>
            <tr>
              <th>Type</th>
              <th>Date</th>
              <th>Reference</th>
              <th>Status</th>
              <th>Base</th>
              <th>Taxes</th>
              <th>Fees</th>
              <th>Total</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="transaction in sortedTransactions" :key="transaction.id" class="segment-row">
              <td>
                <div class="text-sm font-medium">{{ formatTransactionType(transaction.transaction_type) }}</div>
                <div v-if="transaction.reason" class="text-xs text-gray-500">{{ transaction.reason }}</div>
                <div v-if="transaction.notes" class="text-xs text-gray-400 mt-1">{{ transaction.notes }}</div>
              </td>
              <td class="text-sm">{{ formatDate(transaction.transaction_date) }}</td>
              <td class="text-sm">{{ transaction.transaction_reference || '-' }}</td>
              <td>
                <span :class="getTransactionStatusClass(transaction.status)">
                  {{ transaction.status }}
                </span>
              </td>
              <td class="text-sm" :class="{ 'text-red-600': transaction.base_amount < 0 }">
                {{ formatCurrency(transaction.base_amount, transaction.currency) }}
              </td>
              <td class="text-sm" :class="{ 'text-red-600': transaction.taxes < 0 }">
                {{ formatCurrency(transaction.taxes, transaction.currency) }}
              </td>
              <td class="text-sm" :class="{ 'text-red-600': transaction.fees < 0 }">
                {{ formatCurrency(transaction.fees, transaction.currency) }}
              </td>
              <td class="text-sm font-medium" :class="{ 'text-red-600': transaction.total_amount < 0, 'text-green-600': transaction.total_amount > 0 }">
                {{ formatCurrency(transaction.total_amount, transaction.currency) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Empty State -->
    <div v-if="!hasAnyData" class="text-center py-8 text-gray-500">
      <span class="mdi mdi-information-outline text-4xl mb-2 block"></span>
      <p>No detailed information available for this booking.</p>
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

// Build unified segments array
const allSegments = computed(() => {
  const segments = []

  // Add air segments
  if (props.booking.air_bookings) {
    props.booking.air_bookings.forEach(airBooking => {
      if (airBooking.segments) {
        airBooking.segments.forEach(segment => {
          segments.push({
            id: `air-${segment.id}`,
            type: 'air',
            typeName: 'Flight',
            date: segment.departure_date,
            data: segment,
            amount: null, // Air segments don't have individual amounts
            carbon: segment.carbon_emissions_kg,
            currency: airBooking.currency,
            sortOrder: 1 // Air first
          })
        })
      }
    })
  }

  // Add accommodation bookings
  if (props.booking.accommodation_bookings) {
    props.booking.accommodation_bookings.forEach(accom => {
      segments.push({
        id: `accom-${accom.id}`,
        type: 'accommodation',
        typeName: 'Hotel',
        date: accom.check_in_date,
        data: accom,
        amount: accom.nightly_rate ? accom.nightly_rate * accom.number_of_nights : accom.total_amount_base,
        carbon: null,
        currency: accom.currency,
        sortOrder: 2 // Accommodation second
      })
    })
  }

  // Add car hire bookings
  if (props.booking.car_hire_bookings) {
    props.booking.car_hire_bookings.forEach(car => {
      segments.push({
        id: `car-${car.id}`,
        type: 'car',
        typeName: 'Car Hire',
        date: car.pickup_date,
        data: car,
        amount: car.daily_rate ? car.daily_rate * car.number_of_days : car.total_amount_base,
        carbon: null,
        currency: car.currency,
        sortOrder: 3 // Car third
      })
    })
  }

  return segments
})

// Sort segments by type (air, hotel, car) and then by date
const sortedSegments = computed(() => {
  return [...allSegments.value].sort((a, b) => {
    // First sort by type order
    if (a.sortOrder !== b.sortOrder) {
      return a.sortOrder - b.sortOrder
    }
    // Then sort by date within same type
    return new Date(a.date) - new Date(b.date)
  })
})

// Sort transactions by date
const sortedTransactions = computed(() => {
  if (!props.booking.transactions) return []
  return [...props.booking.transactions].sort((a, b) => {
    return new Date(a.transaction_date) - new Date(b.transaction_date)
  })
})

const hasAnyData = computed(() => {
  return allSegments.value.length > 0 ||
         props.booking.service_fees?.length > 0 ||
         props.booking.transactions?.length > 0
})

// Helper functions
const getTypeIcon = (type) => {
  switch(type) {
    case 'air': return 'mdi-airplane'
    case 'accommodation': return 'mdi-hotel'
    case 'car': return 'mdi-car'
    default: return 'mdi-help'
  }
}

const formatCurrency = (amount, currency = 'AUD') => {
  if (!amount && amount !== 0) return '-'
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

const formatFeeType = (feeType) => {
  return feeType.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, l => l.toUpperCase())
}

const formatTransactionType = (transactionType) => {
  return transactionType.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, l => l.toUpperCase())
}

const getTransactionStatusClass = (status) => {
  const baseClasses = 'px-2 py-1 text-xs font-medium rounded-full'
  switch(status) {
    case 'CONFIRMED':
      return `${baseClasses} bg-green-100 text-green-800`
    case 'PENDING':
      return `${baseClasses} bg-yellow-100 text-yellow-800`
    case 'CANCELLED':
      return `${baseClasses} bg-red-100 text-red-800`
    case 'REFUNDED':
      return `${baseClasses} bg-blue-100 text-blue-800`
    default:
      return `${baseClasses} bg-gray-100 text-gray-800`
  }
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

.segments-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
}

.segments-table thead {
  background: #f9fafb;
  border-bottom: 2px solid #e5e7eb;
}

.segments-table th {
  padding: 0.75rem 1rem;
  text-align: left;
  font-size: 0.75rem;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.segment-row {
  border-bottom: 1px solid #f3f4f6;
  transition: background-color 0.15s;
}

.segment-row:hover {
  background-color: #f9fafb;
}

.segment-row:last-child {
  border-bottom: none;
}

.segment-row td {
  padding: 0.75rem 1rem;
  vertical-align: top;
}

.segment-details {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}
</style>

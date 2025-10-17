<template>
  <div>
    <div class="px-4 sm:px-0">
      <h1 class="text-2xl font-bold text-gray-900">Dashboard</h1>
      <p class="mt-1 text-sm text-gray-600">Overview of your travel analytics</p>
    </div>

    <!-- Stats Cards -->
    <div class="mt-6 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
      <!-- Total Bookings -->
      <div class="bg-white overflow-hidden shadow rounded-lg">
        <div class="p-5">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <div class="text-3xl">✈️</div>
            </div>
            <div class="ml-5 w-0 flex-1">
              <dl>
                <dt class="text-sm font-medium text-gray-500 truncate">Total Bookings</dt>
                <dd class="text-2xl font-semibold text-gray-900">
                  {{ loading ? '...' : summary.total_bookings || 0 }}
                </dd>
              </dl>
            </div>
          </div>
        </div>
      </div>

      <!-- Total Spend -->
      <div class="bg-white overflow-hidden shadow rounded-lg">
        <div class="p-5">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <div class="text-3xl">💰</div>
            </div>
            <div class="ml-5 w-0 flex-1">
              <dl>
                <dt class="text-sm font-medium text-gray-500 truncate">Total Spend</dt>
                <dd class="text-2xl font-semibold text-gray-900">
                  {{ loading ? '...' : formatCurrency(summary.total_spend) }}
                </dd>
              </dl>
            </div>
          </div>
        </div>
      </div>

      <!-- Air Travel -->
      <div class="bg-white overflow-hidden shadow rounded-lg">
        <div class="p-5">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <div class="text-3xl">🛫</div>
            </div>
            <div class="ml-5 w-0 flex-1">
              <dl>
                <dt class="text-sm font-medium text-gray-500 truncate">Air Bookings</dt>
                <dd class="text-2xl font-semibold text-gray-900">
                  {{ loading ? '...' : summary.air_bookings || 0 }}
                </dd>
              </dl>
            </div>
          </div>
        </div>
      </div>

      <!-- Hotels -->
      <div class="bg-white overflow-hidden shadow rounded-lg">
        <div class="p-5">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <div class="text-3xl">🏨</div>
            </div>
            <div class="ml-5 w-0 flex-1">
              <dl>
                <dt class="text-sm font-medium text-gray-500 truncate">Hotel Bookings</dt>
                <dd class="text-2xl font-semibold text-gray-900">
                  {{ loading ? '...' : summary.hotel_bookings || 0 }}
                </dd>
              </dl>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Recent Bookings -->
    <div class="mt-8">
      <h2 class="text-lg font-medium text-gray-900 mb-4">Recent Bookings</h2>
      <div class="bg-white shadow overflow-hidden sm:rounded-lg">
        <div v-if="loading" class="p-6 text-center text-gray-500">
          Loading bookings...
        </div>
        <div v-else-if="bookings.length === 0" class="p-6 text-center text-gray-500">
          No bookings found
        </div>
        <ul v-else class="divide-y divide-gray-200">
          <li v-for="booking in bookings" :key="booking.id" class="p-4 hover:bg-gray-50">
            <div class="flex items-center justify-between">
              <div class="flex-1">
                <p class="text-sm font-medium text-primary-600">
                  {{ booking.agent_booking_reference }}
                </p>
                <p class="text-sm text-gray-600">
                  {{ booking.traveller?.first_name }} {{ booking.traveller?.last_name }}
                </p>
                <p class="text-xs text-gray-500">
                  {{ formatDate(booking.travel_date) }}
                </p>
              </div>
              <div class="text-right">
                <p class="text-sm font-semibold text-gray-900">
                  {{ booking.currency }} {{ booking.total_amount }}
                </p>
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                      :class="getBookingTypeClass(booking.booking_type)">
                  {{ booking.booking_type }}
                </span>
              </div>
            </div>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import bookingService from '@/services/bookingService'

const loading = ref(true)
const summary = ref({})
const bookings = ref([])

const fetchData = async () => {
  try {
    loading.value = true
    const [summaryData, bookingsData] = await Promise.all([
      bookingService.getBookingSummary(),
      bookingService.getBookings({ page_size: 10 })
    ])
    summary.value = summaryData
    bookings.value = bookingsData.results || bookingsData
  } catch (error) {
    console.error('Failed to fetch data:', error)
  } finally {
    loading.value = false
  }
}

const formatCurrency = (amount) => {
  if (!amount) return 'AUD $0.00'
  return `AUD $${parseFloat(amount).toLocaleString('en-AU', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('en-AU', { 
    year: 'numeric', 
    month: 'short', 
    day: 'numeric' 
  })
}

const getBookingTypeClass = (type) => {
  const classes = {
    'AIR': 'bg-blue-100 text-blue-800',
    'HOTEL': 'bg-purple-100 text-purple-800',
    'CAR': 'bg-green-100 text-green-800',
    'OTHER': 'bg-gray-100 text-gray-800',
  }
  return classes[type] || classes['OTHER']
}

onMounted(() => {
  fetchData()
})
</script>

<template>
  <div>
    <div class="px-4 sm:px-0">
      <h1 class="text-2xl font-bold text-gray-900">All Bookings</h1>
      <p class="mt-1 text-sm text-gray-600">Complete list of travel bookings</p>
    </div>

    <!-- Filters -->
    <div class="mt-6 bg-white p-4 rounded-lg shadow">
      <div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Booking Type</label>
          <select 
            v-model="filters.booking_type" 
            @change="fetchBookings"
            class="w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
          >
            <option value="">All Types</option>
            <option value="AIR">Air Travel</option>
            <option value="HOTEL">Hotels</option>
            <option value="CAR">Car Hire</option>
            <option value="OTHER">Other</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Status</label>
          <select 
            v-model="filters.status" 
            @change="fetchBookings"
            class="w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
          >
            <option value="">All Status</option>
            <option value="CONFIRMED">Confirmed</option>
            <option value="CANCELLED">Cancelled</option>
            <option value="PENDING">Pending</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Search</label>
          <input 
            v-model="filters.search" 
            @input="fetchBookings"
            type="text" 
            placeholder="Reference, traveller..."
            class="w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
          />
        </div>
      </div>
    </div>

    <!-- Bookings Table -->
    <div class="mt-6 bg-white shadow overflow-hidden sm:rounded-lg">
      <div v-if="loading" class="p-6 text-center text-gray-500">
        Loading bookings...
      </div>
      <div v-else-if="bookings.length === 0" class="p-6 text-center text-gray-500">
        No bookings found
      </div>
      <table v-else class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Reference</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Traveller</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Travel Date</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-for="booking in bookings" :key="booking.id" class="hover:bg-gray-50">
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-primary-600">
              {{ booking.agent_booking_reference }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
              {{ booking.traveller?.first_name }} {{ booking.traveller?.last_name }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                    :class="getBookingTypeClass(booking.booking_type)">
                {{ booking.booking_type }}
              </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
              {{ formatDate(booking.travel_date) }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-semibold">
              {{ booking.currency }} ${{ booking.total_amount }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                    :class="getStatusClass(booking.status)">
                {{ booking.status }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import bookingService from '@/services/bookingService'

const loading = ref(true)
const bookings = ref([])
const filters = reactive({
  booking_type: '',
  status: '',
  search: '',
})

const fetchBookings = async () => {
  try {
    loading.value = true
    const params = {}
    if (filters.booking_type) params.booking_type = filters.booking_type
    if (filters.status) params.status = filters.status
    if (filters.search) params.search = filters.search

    const data = await bookingService.getBookings(params)
    bookings.value = data.results || data
  } catch (error) {
    console.error('Failed to fetch bookings:', error)
  } finally {
    loading.value = false
  }
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

const getStatusClass = (status) => {
  const classes = {
    'CONFIRMED': 'bg-green-100 text-green-800',
    'CANCELLED': 'bg-red-100 text-red-800',
    'PENDING': 'bg-yellow-100 text-yellow-800',
  }
  return classes[status] || classes['PENDING']
}

onMounted(() => {
  fetchBookings()
})
</script>

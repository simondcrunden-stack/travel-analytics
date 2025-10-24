<template>
  <div class="min-h-screen bg-gray-50 p-8">
    <div class="mx-auto max-w-7xl">
      <!-- Header -->
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900">Accommodation Analytics</h1>
        <p class="mt-2 text-gray-600">Analyze hotel bookings, spending patterns, and rates</p>
      </div>

      <!-- Filters Section -->
      <div class="mb-8 rounded-2xl bg-white p-6 shadow-sm">
        <h3 class="mb-4 text-lg font-semibold text-gray-900">Filters</h3>
        <div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
          <!-- City Filter -->
          <div>
            <label for="city" class="block text-sm font-medium text-gray-700">City</label>
            <input
              id="city"
              v-model="filters.city"
              type="text"
              placeholder="Enter city name"
              class="mt-1 block w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-purple-500 focus:ring-purple-500"
            />
          </div>

          <!-- Hotel Chain Filter -->
          <div>
            <label for="hotelChain" class="block text-sm font-medium text-gray-700">Hotel Chain</label>
            <input
              id="hotelChain"
              v-model="filters.hotelChain"
              type="text"
              placeholder="Enter hotel chain"
              class="mt-1 block w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-purple-500 focus:ring-purple-500"
            />
          </div>

          <!-- Date From Filter -->
          <div>
            <label for="dateFrom" class="block text-sm font-medium text-gray-700">Date From</label>
            <input
              id="dateFrom"
              v-model="filters.dateFrom"
              type="date"
              class="mt-1 block w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-purple-500 focus:ring-purple-500"
            />
          </div>

          <!-- Date To Filter -->
          <div>
            <label for="dateTo" class="block text-sm font-medium text-gray-700">Date To</label>
            <input
              id="dateTo"
              v-model="filters.dateTo"
              type="date"
              class="mt-1 block w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-purple-500 focus:ring-purple-500"
            />
          </div>
        </div>

        <!-- Clear Filters Button -->
        <div class="mt-4">
          <button
            @click="clearFilters"
            class="rounded-lg bg-gray-200 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-300"
          >
            Clear Filters
          </button>
        </div>
      </div>

      <!-- Stats Cards - Note the mb-6 class added -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
        <!-- Total Spend -->
        <div class="rounded-2xl bg-white p-6 shadow-sm">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-600">Total Spend</p>
              <p class="mt-2 text-3xl font-bold text-gray-900">
                ${{ formatNumber(stats.totalSpend) }}
              </p>
            </div>
            <div class="rounded-full bg-purple-100 p-3">
              <svg class="h-6 w-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
              </svg>
            </div>
          </div>
        </div>

        <!-- Total Bookings -->
        <div class="rounded-2xl bg-white p-6 shadow-sm">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-600">Total Bookings</p>
              <p class="mt-2 text-3xl font-bold text-gray-900">
                {{ stats.totalBookings }}
              </p>
            </div>
            <div class="rounded-full bg-blue-100 p-3">
              <svg class="h-6 w-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
            </div>
          </div>
        </div>

        <!-- Total Nights -->
        <div class="rounded-2xl bg-white p-6 shadow-sm">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-600">Total Nights</p>
              <p class="mt-2 text-3xl font-bold text-gray-900">
                {{ stats.totalNights }}
              </p>
            </div>
            <div class="rounded-full bg-green-100 p-3">
              <svg class="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
        </div>

        <!-- Average Nightly Rate -->
        <div class="rounded-2xl bg-white p-6 shadow-sm">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-600">Avg Nightly Rate</p>
              <p class="mt-2 text-3xl font-bold text-gray-900">
                ${{ formatNumber(stats.avgRate) }}
              </p>
            </div>
            <div class="rounded-full bg-amber-100 p-3">
              <svg class="h-6 w-6 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
        </div>
      </div>

      <!-- Chart Components Grid -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <HotelChainSpendChart :filters="filters" />
        <CityBookingsChart :filters="filters" />
      </div>

      <NightlyRateChart :filters="filters" class="mb-6" />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import api from '@/services/api'  // This line is important!
import HotelChainSpendChart from '@/components/accommodation/HotelChainSpendChart.vue'
import CityBookingsChart from '@/components/accommodation/CityBookingsChart.vue'
import NightlyRateChart from '@/components/accommodation/NightlyRateChart.vue'

// Filters
const filters = reactive({
  city: '',
  hotelChain: '',
  dateFrom: '',
  dateTo: '',
})

// Stats
const stats = reactive({
  totalSpend: 0,
  totalBookings: 0,
  totalNights: 0,
  avgRate: 0,
})

// Format number helper
const formatNumber = (num) => {
  return new Intl.NumberFormat('en-AU').format(num || 0)
}

// Clear filters
const clearFilters = () => {
  filters.city = ''
  filters.hotelChain = ''
  filters.dateFrom = ''
  filters.dateTo = ''
}

// Load stats
// Load stats
const loadStats = async () => {
  try {
    const params = {
      booking_type: 'HOTEL',
    }

    if (filters.dateFrom) params.travel_date__gte = filters.dateFrom
    if (filters.dateTo) params.travel_date__lte = filters.dateTo
    if (filters.city) params.destination__icontains = filters.city
    if (filters.hotelChain) params.vendor__icontains = filters.hotelChain

    const response = await api.get('/bookings/', { params })
    
    const bookings = response.data.results || []
    
    // Calculate stats from bookings with accommodation_details
    stats.totalBookings = bookings.length
    stats.totalSpend = bookings.reduce((sum, b) => sum + parseFloat(b.total_amount || 0), 0)
    
    // Sum nights from accommodation_details
    stats.totalNights = bookings.reduce((sum, b) => {
      return sum + (b.accommodation_details?.number_of_nights || 0)
    }, 0)
    
    // Calculate average nightly rate
    stats.avgRate = stats.totalNights > 0 ? Math.round(stats.totalSpend / stats.totalNights) : 0
  } catch (error) {
    console.error('Error loading accommodation stats:', error)
  }
}

// Watch filters
watch(filters, () => {
  loadStats()
}, { deep: true })

// Load data on mount
onMounted(() => {
  loadStats()
})
</script>
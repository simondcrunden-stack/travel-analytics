<template>
  <div class="min-h-screen bg-gray-50 p-8">
    <div class="mx-auto max-w-7xl">
      <!-- Header -->
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900">Car Hire Analytics</h1>
        <p class="mt-2 text-gray-600">Analyze rental company spending and vehicle preferences</p>
      </div>

      <!-- Filters Section -->
      <div class="mb-8 rounded-2xl bg-white p-6 shadow-sm">
        <h3 class="mb-4 text-lg font-semibold text-gray-900">Filters</h3>
        <div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
          <!-- Pickup From Filter -->
          <div>
            <label for="pickupFrom" class="block text-sm font-medium text-gray-700">Pickup From</label>
            <input
              id="pickupFrom"
              v-model="filters.pickupFrom"
              type="date"
              class="mt-1 block w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-green-500 focus:ring-green-500"
            />
          </div>

          <!-- Pickup To Filter -->
          <div>
            <label for="pickupTo" class="block text-sm font-medium text-gray-700">Pickup To</label>
            <input
              id="pickupTo"
              v-model="filters.pickupTo"
              type="date"
              class="mt-1 block w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-green-500 focus:ring-green-500"
            />
          </div>

          <!-- Rental Company Filter -->
          <div>
            <label for="rentalCompany" class="block text-sm font-medium text-gray-700">Rental Company</label>
            <input
              id="rentalCompany"
              v-model="filters.rentalCompany"
              type="text"
              placeholder="Enter rental company"
              class="mt-1 block w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-green-500 focus:ring-green-500"
            />
          </div>

          <!-- Vehicle Type Filter -->
          <div>
            <label for="vehicleType" class="block text-sm font-medium text-gray-700">Vehicle Type</label>
            <input
              id="vehicleType"
              v-model="filters.vehicleType"
              type="text"
              placeholder="Enter vehicle type"
              class="mt-1 block w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-green-500 focus:ring-green-500"
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
            <div class="rounded-full bg-green-100 p-3">
              <svg class="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
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

        <!-- Total Rental Days -->
        <div class="rounded-2xl bg-white p-6 shadow-sm">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-600">Total Rental Days</p>
              <p class="mt-2 text-3xl font-bold text-gray-900">
                {{ stats.totalDays }}
              </p>
            </div>
            <div class="rounded-full bg-amber-100 p-3">
              <svg class="h-6 w-6 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
          </div>
        </div>

        <!-- Average Daily Rate -->
        <div class="rounded-2xl bg-white p-6 shadow-sm">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-600">Avg Daily Rate</p>
              <p class="mt-2 text-3xl font-bold text-gray-900">
                ${{ formatNumber(stats.avgRate) }}
              </p>
            </div>
            <div class="rounded-full bg-purple-100 p-3">
              <svg class="h-6 w-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
        </div>
      </div>

      <!-- Chart Components Grid -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <RentalCompanySpendChart :filters="filters" />
        <VehicleTypeChart :filters="filters" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import api from '@/services/api'
import RentalCompanySpendChart from '@/components/car/RentalCompanySpendChart.vue'
import VehicleTypeChart from '@/components/car/VehicleTypeChart.vue'

// Filters
const filters = reactive({
  pickupFrom: '',
  pickupTo: '',
  rentalCompany: '',
  vehicleType: '',
})

// Stats
const stats = reactive({
  totalSpend: 0,
  totalBookings: 0,
  totalDays: 0,
  avgRate: 0,
})

// Format number helper
const formatNumber = (num) => {
  return new Intl.NumberFormat('en-AU').format(Math.round(num || 0))
}

// Clear filters
const clearFilters = () => {
  filters.pickupFrom = ''
  filters.pickupTo = ''
  filters.rentalCompany = ''
  filters.vehicleType = ''
}

// Load stats
const loadStats = async () => {
  try {
    const params = {
      booking_type: 'CAR',
    }

    if (filters.pickupFrom) params.travel_date__gte = filters.pickupFrom
    if (filters.pickupTo) params.travel_date__lte = filters.pickupTo
    if (filters.rentalCompany) params.vendor__icontains = filters.rentalCompany
    if (filters.vehicleType) params.car_hire_details__vehicle_type__icontains = filters.vehicleType

    const response = await api.get('/bookings/', { params })
    
    const bookings = response.data.results || []
    
    stats.totalBookings = bookings.length
    stats.totalSpend = bookings.reduce((sum, b) => sum + parseFloat(b.total_amount || 0), 0)
    
    // Sum rental days from car_hire_details
    stats.totalDays = bookings.reduce((sum, b) => {
      return sum + (b.car_hire_details?.number_of_days || 0)
    }, 0)
    
    // Calculate average daily rate
    stats.avgRate = stats.totalDays > 0 ? Math.round(stats.totalSpend / stats.totalDays) : 0
  } catch (error) {
    console.error('Error loading car hire stats:', error)
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
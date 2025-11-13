<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import bookingService from '@/services/bookingService'
import { Chart, registerables } from 'chart.js'
import UniversalFilters from '@/components/common/UniversalFilters.vue'

// Register Chart.js components
Chart.register(...registerables)

// State
const loading = ref(true)
const error = ref(null)
const bookings = ref([])
const summary = ref({
  total_spend: 0,
  total_emissions: 0,
  compliance_rate: 0,
  booking_count: 0
})
const currentFilters = ref({})
const currentPage = ref(1)
const itemsPerPage = ref(20)

// Chart refs
const locationChartRef = ref(null)
const rentalCompanyChartRef = ref(null)
let locationChart = null
let rentalCompanyChart = null

// Car hire bookings computed (backend filters, we just display car ones)
const carHireBookings = computed(() => {
  return bookings.value.filter(b => b.car_hire_bookings && b.car_hire_bookings.length > 0)
})

// Summary stats - Calculate from CAR HIRE ONLY (not total booking amount)
const summaryStats = computed(() => {
  let totalCarHireSpend = 0
  let totalDays = 0
  let totalCarHireBookings = 0

  carHireBookings.value.forEach(booking => {
    booking.car_hire_bookings.forEach(car => {
      // Use car.total_amount_base for car hire-specific spend
      totalCarHireSpend += parseFloat(car.total_amount_base || 0)
      totalDays += car.number_of_days || 0
      totalCarHireBookings++
    })
  })

  const avgDailyRate = totalDays > 0 ? totalCarHireSpend / totalDays : 0

  return {
    total_bookings: totalCarHireBookings,
    total_spend: totalCarHireSpend,
    avg_spend: totalCarHireBookings > 0 ? totalCarHireSpend / totalCarHireBookings : 0,
    total_days: totalDays,
    avg_daily_rate: avgDailyRate,
  }
})

// Removed availableCities, availableRentalCompanies, availableVehicleTypes - not needed with UniversalFilters

// Handle filter changes from UniversalFilters
const handleFiltersChanged = async (filters) => {
  console.log('🚗 [CarHireView] Filters changed:', filters)
  currentFilters.value = filters
  await loadData(filters)
}

// Methods
const loadData = async (filters = {}) => {
  try {
    loading.value = true
    error.value = null

    console.log('🌐 [CarHireView] Loading car hire data with filters:', filters)

    // bookingService handles filter transformation automatically
    const data = await bookingService.getBookings(filters)
    bookings.value = data.results || []

    // Use backend summary statistics
    if (data.summary) {
      summary.value = data.summary
      console.log('📊 [CarHireView] Backend summary:', summary.value)
    }

    console.log('✅ [CarHireView] Loaded', bookings.value.length, 'bookings,', carHireBookings.value.length, 'with car hires')

  } catch (err) {
    console.error('❌ [CarHireView] Error loading data:', err)
    error.value = 'Failed to load booking data. Please try again.'
  } finally {
    loading.value = false
    await nextTick()
    await nextTick()
    renderCharts()
  }
}

const renderCharts = () => {
  // Destroy existing charts
  if (locationChart) locationChart.destroy()
  if (rentalCompanyChart) rentalCompanyChart.destroy()

  // Location Chart Data - Calculate from CAR HIRE ONLY
  const locationChartData = {}
  carHireBookings.value.forEach(booking => {
    booking.car_hire_bookings.forEach(car => {
      const city = car.pickup_city || 'Unknown'
      if (!locationChartData[city]) {
        locationChartData[city] = 0
      }
      // Use car.total_amount_base instead of booking.total_amount
      const amount = parseFloat(car.total_amount_base || 0)
      locationChartData[city] += amount
    })
  })

  const topLocations = Object.entries(locationChartData)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)

  if (locationChartRef.value) {
    const ctx = locationChartRef.value.getContext('2d')
    locationChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: topLocations.map(l => l[0]),
        datasets: [{
          label: 'Spend (AUD)',
          data: topLocations.map(l => l[1]),
          backgroundColor: '#3b82f6'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (context) => formatCurrency(context.parsed.y)
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              callback: (value) => formatCurrency(value)
            }
          }
        }
      }
    })
  }

  // Rental Company Chart Data - Calculate from CAR HIRE ONLY
  const rentalCompanyChartData = {}
  carHireBookings.value.forEach(booking => {
    booking.car_hire_bookings.forEach(car => {
      const company = car.rental_company || 'Unknown'
      if (!rentalCompanyChartData[company]) {
        rentalCompanyChartData[company] = 0
      }
      // Use car.total_amount_base instead of booking.total_amount
      const amount = parseFloat(car.total_amount_base || 0)
      rentalCompanyChartData[company] += amount
    })
  })

  const topCompanies = Object.entries(rentalCompanyChartData)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)

  if (rentalCompanyChartRef.value) {
    const ctx = rentalCompanyChartRef.value.getContext('2d')
    rentalCompanyChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: topCompanies.map(c => c[0]),
        datasets: [{
          label: 'Spend (AUD)',
          data: topCompanies.map(c => c[1]),
          backgroundColor: '#8b5cf6'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (context) => formatCurrency(context.parsed.y)
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              callback: (value) => formatCurrency(value)
            }
          }
        }
      }
    })
  }
}

// Removed clearFilters - UniversalFilters handles this now

const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-AU', {
    style: 'currency',
    currency: 'AUD',
  }).format(amount)
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('en-AU', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

// Pagination
const totalPages = computed(() => {
  return Math.ceil(carHireBookings.value.length / itemsPerPage.value)
})

const startIndex = computed(() => {
  return (currentPage.value - 1) * itemsPerPage.value
})

const endIndex = computed(() => {
  return currentPage.value * itemsPerPage.value
})

const paginatedCarHireBookings = computed(() => {
  return carHireBookings.value.slice(startIndex.value, endIndex.value)
})

// Helper functions updated for array handling
const getRentalInfo = (booking) => {
  if (!booking.car_hire_bookings || booking.car_hire_bookings.length === 0) {
    return 'N/A'
  }

  if (booking.car_hire_bookings.length === 1) {
    return booking.car_hire_bookings[0].rental_company || 'Unknown'
  } else {
    return `Multi-city (${booking.car_hire_bookings.length} rentals)`
  }
}

const getCarHireAmount = (booking) => {
  // Return total of all car hire amounts for this booking
  if (!booking.car_hire_bookings || booking.car_hire_bookings.length === 0) return 0

  return booking.car_hire_bookings.reduce((total, car) => {
    return total + parseFloat(car.total_amount_base || 0)
  }, 0)
}

const getCityInfo = (booking) => {
  if (!booking.car_hire_bookings || booking.car_hire_bookings.length === 0) {
    return 'N/A'
  }
  
  const cities = booking.car_hire_bookings
    .map(car => car.pickup_city)
    .filter(city => city)
  
  if (cities.length === 0) return 'Unknown'
  if (cities.length === 1) return cities[0]
  
  const uniqueCities = [...new Set(cities)]
  if (uniqueCities.length === 1) return uniqueCities[0]
  return `${uniqueCities[0]} +${uniqueCities.length - 1}`
}

const getVehicleInfo = (booking) => {
  if (!booking.car_hire_bookings || booking.car_hire_bookings.length === 0) {
    return 'N/A'
  }
  
  const vehicles = booking.car_hire_bookings
    .map(car => car.vehicle_type)
    .filter(type => type)
  
  if (vehicles.length === 0) return 'Unknown'
  if (vehicles.length === 1) return vehicles[0]
  return `${vehicles[0]} +${vehicles.length - 1}`
}

const getTotalDays = (booking) => {
  if (!booking.car_hire_bookings || booking.car_hire_bookings.length === 0) {
    return 0
  }
  
  return booking.car_hire_bookings.reduce((sum, car) => 
    sum + (car.number_of_days || 0), 0)
}

const getPickupDate = (booking) => {
  if (!booking.car_hire_bookings || booking.car_hire_bookings.length === 0) {
    return 'N/A'
  }
  
  // Get earliest pickup date
  const dates = booking.car_hire_bookings
    .map(car => car.pickup_date)
    .filter(date => date)
    .sort()
  
  return dates.length > 0 ? formatDate(dates[0]) : 'N/A'
}

// Lifecycle
onMounted(async () => {
  await loadData()
})
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div>
      <h1 class="text-2xl font-bold text-gray-900">Car Hire Analytics</h1>
      <p class="mt-1 text-sm text-gray-500">Analyze car rental bookings, spending patterns, and vehicle preferences</p>
    </div>

    <!-- Universal Filters -->
    <UniversalFilters
      :show-traveller="true"
      :show-date-range="true"
      :show-destinations="true"
      :show-organization="true"
      :show-status="false"
      :show-supplier="true"
      supplier-label="Rental Company"
      supplier-placeholder="Hertz, Avis, Budget..."
      @filters-changed="handleFiltersChanged"
    />

    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center items-center py-12">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-lg p-4">
      <p class="text-red-800">{{ error }}</p>
      <button @click="loadData" class="mt-2 text-sm text-red-600 hover:text-red-800 underline">Retry</button>
    </div>

    <!-- Summary Cards -->
    <div v-if="!loading && !error" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <!-- Total Bookings -->
      <div class="bg-white rounded-xl shadow-sm p-6">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-gray-600">Total Bookings</p>
            <p class="text-3xl font-bold text-gray-900 mt-2">{{ summaryStats.total_bookings }}</p>
          </div>
          <div class="bg-blue-100 p-3 rounded-full">
            <span class="mdi mdi-car text-blue-600 text-2xl"></span>
          </div>
        </div>
      </div>

      <!-- Total Spend -->
      <div class="bg-white rounded-xl shadow-sm p-6">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-gray-600">Total Spend</p>
            <p class="text-3xl font-bold text-gray-900 mt-2">{{ formatCurrency(summaryStats.total_spend) }}</p>
          </div>
          <div class="bg-green-100 p-3 rounded-full">
            <span class="mdi mdi-currency-usd text-green-600 text-2xl"></span>
          </div>
        </div>
      </div>

      <!-- Total Rental Days -->
      <div class="bg-white rounded-xl shadow-sm p-6">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-gray-600">Total Rental Days</p>
            <p class="text-3xl font-bold text-gray-900 mt-2">{{ summaryStats.total_days }}</p>
          </div>
          <div class="bg-purple-100 p-3 rounded-full">
            <span class="mdi mdi-calendar-range text-purple-600 text-2xl"></span>
          </div>
        </div>
      </div>

      <!-- Avg Daily Rate -->
      <div class="bg-white rounded-xl shadow-sm p-6">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-gray-600">Avg Daily Rate</p>
            <p class="text-3xl font-bold text-gray-900 mt-2">{{ formatCurrency(summaryStats.avg_daily_rate) }}</p>
          </div>
          <div class="bg-orange-100 p-3 rounded-full">
            <span class="mdi mdi-chart-line text-orange-600 text-2xl"></span>
          </div>
        </div>
      </div>
    </div>

    <!-- Charts -->
    <div v-if="!loading && !error" class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Location Chart -->
      <div class="bg-white rounded-xl shadow-sm overflow-hidden">
        <div class="border-b border-gray-200 px-6 py-4">
          <h3 class="text-lg font-semibold text-gray-900">Spend by Location</h3>
        </div>
        <div class="p-6" style="height: 400px;">
          <canvas ref="locationChartRef"></canvas>
        </div>
      </div>

      <!-- Rental Company Chart -->
      <div class="bg-white rounded-xl shadow-sm overflow-hidden">
        <div class="border-b border-gray-200 px-6 py-4">
          <h3 class="text-lg font-semibold text-gray-900">Spend by Rental Company</h3>
        </div>
        <div class="p-6" style="height: 400px;">
          <canvas ref="rentalCompanyChartRef"></canvas>
        </div>
      </div>
    </div>

    <!-- Bookings Table -->
    <div v-if="!loading && !error" class="bg-white rounded-xl shadow-sm overflow-hidden">
      <!-- Table Controls -->
      <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
        <div class="flex items-center space-x-4">
          <span class="text-sm text-gray-700">
            Showing {{ startIndex + 1 }}-{{ Math.min(endIndex, carHireBookings.length) }} of {{ carHireBookings.length }} bookings
          </span>
        </div>
        <div class="flex items-center space-x-2">
          <label class="text-sm text-gray-700">Per page:</label>
          <select
            v-model="itemsPerPage"
            class="border border-gray-300 rounded-md px-2 py-1 text-sm"
          >
            <option :value="10">10</option>
            <option :value="20">20</option>
            <option :value="30">30</option>
            <option :value="40">40</option>
            <option :value="50">50</option>
          </select>
        </div>
      </div>

      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Reference</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Traveller</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Rental Company</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">City</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Vehicle</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Pickup</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Days</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="booking in paginatedCarHireBookings" :key="booking.id" class="hover:bg-gray-50">
              <td class="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900">{{ booking.agent_booking_reference }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{{ booking.traveller_name }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ getRentalInfo(booking) }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ getCityInfo(booking) }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ getVehicleInfo(booking) }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ getPickupDate(booking) }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-center">{{ getTotalDays(booking) }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-900">{{ formatCurrency(getCarHireAmount(booking)) }}</td>
            </tr>
          </tbody>
        </table>

        <div v-if="carHireBookings.length === 0" class="text-center py-12">
          <span class="mdi mdi-car-off text-gray-300 text-6xl"></span>
          <p class="text-gray-500 mt-4">No car hire bookings found</p>
        </div>
      </div>

      <!-- Pagination -->
      <div class="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <span class="text-sm text-gray-700">Rows per page:</span>
          <select v-model="itemsPerPage" class="border border-gray-300 rounded-md px-2 py-1 text-sm">
            <option :value="10">10</option>
            <option :value="20">20</option>
            <option :value="30">30</option>
            <option :value="40">40</option>
            <option :value="50">50</option>
          </select>
        </div>

        <div class="flex items-center gap-4">
          <span class="text-sm text-gray-700">
            {{ (currentPage - 1) * itemsPerPage + 1 }}-{{ Math.min(currentPage * itemsPerPage, carHireBookings.length) }}
            of {{ carHireBookings.length }}
          </span>

          <div class="flex gap-2">
            <button
              @click="currentPage > 1 && currentPage--"
              :disabled="currentPage === 1"
              class="px-3 py-1 border border-gray-300 rounded-md text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              Previous
            </button>
            <button
              @click="currentPage < totalPages && currentPage++"
              :disabled="currentPage === totalPages"
              class="px-3 py-1 border border-gray-300 rounded-md text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Minimal scoped styles - most styling uses Tailwind classes */
</style>
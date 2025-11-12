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

// Chart refs
const airlineChartRef = ref(null)
const classChartRef = ref(null)
const routeChartRef = ref(null)
let airlineChart = null
let classChart = null
let routeChart = null

// Air bookings computed (backend filters, we just display air ones)
const airBookings = computed(() => {
  return bookings.value.filter(b => b.air_bookings && b.air_bookings.length > 0)
})

// Summary stats from backend
const summaryStats = computed(() => {
  return {
    total_bookings: summary.value.booking_count || airBookings.value.length,
    total_spend: summary.value.total_spend || 0,
    avg_spend: summary.value.booking_count > 0 ? summary.value.total_spend / summary.value.booking_count : 0,
    total_carbon_kg: summary.value.total_emissions || 0,
  }
})

// Removed availableAirlines and availableDestinations - not needed with UniversalFilters

// Handle filter changes from UniversalFilters
const handleFiltersChanged = async (filters) => {
  console.log('✈️ [AirView] Filters changed:', filters)
  currentFilters.value = filters
  await loadData(filters)
}

// Methods
const loadData = async (filters = {}) => {
  try {
    loading.value = true
    error.value = null

    console.log('🌐 [AirView] Loading air travel data with filters:', filters)

    // bookingService handles filter transformation automatically
    const data = await bookingService.getBookings(filters)
    bookings.value = data.results || []

    // Use backend summary statistics
    if (data.summary) {
      summary.value = data.summary
      console.log('📊 [AirView] Backend summary:', summary.value)
    }

    console.log('✅ [AirView] Loaded', bookings.value.length, 'bookings,', airBookings.value.length, 'with flights')

  } catch (err) {
    console.error('❌ [AirView] Error loading data:', err)
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
  if (airlineChart) airlineChart.destroy()
  if (classChart) classChart.destroy()
  if (routeChart) routeChart.destroy()

  // Airline Distribution Chart
  const airlineData = {}
  airBookings.value.forEach(booking => {
    (booking.air_bookings || []).forEach(air => {
      const airline = air.primary_airline_name || 'Unknown'
      if (!airlineData[airline]) {
        airlineData[airline] = 0
      }
      const amount = parseFloat(booking.total_amount || 0) / booking.air_bookings.length
      airlineData[airline] += amount
    })
  })

  const topAirlines = Object.entries(airlineData)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)

  if (airlineChartRef.value) {
    const ctx = airlineChartRef.value.getContext('2d')
    airlineChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: topAirlines.map(a => a[0]),
        datasets: [{
          label: 'Spend (AUD)',
          data: topAirlines.map(a => a[1]),
          backgroundColor: '#0ea5e9'
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

  // Travel Class Distribution Chart
  const classData = {}
  airBookings.value.forEach(booking => {
    (booking.air_bookings || []).forEach(air => {
      const travelClass = air.travel_class || 'Unknown'
      if (!classData[travelClass]) {
        classData[travelClass] = 0
      }
      const amount = parseFloat(booking.total_amount || 0) / booking.air_bookings.length
      classData[travelClass] += amount
    })
  })

  if (classChartRef.value) {
    const ctx = classChartRef.value.getContext('2d')
    classChart = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: Object.keys(classData),
        datasets: [{
          data: Object.values(classData),
          backgroundColor: [
            '#0ea5e9',
            '#8b5cf6',
            '#ec4899',
            '#f59e0b'
          ]
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'right'
          },
          tooltip: {
            callbacks: {
              label: (context) => {
                const label = context.label || ''
                const value = formatCurrency(context.parsed)
                return `${label}: ${value}`
              }
            }
          }
        }
      }
    })
  }

  // Top Routes Chart
  const routeData = {}
  airBookings.value.forEach(booking => {
    (booking.air_bookings || []).forEach(air => {
      const route = `${air.origin_airport_iata_code || '?'} → ${air.destination_airport_iata_code || '?'}`
      if (!routeData[route]) {
        routeData[route] = 0
      }
      const amount = parseFloat(booking.total_amount || 0) / booking.air_bookings.length
      routeData[route] += amount
    })
  })

  const topRoutes = Object.entries(routeData)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)

  if (routeChartRef.value) {
    const ctx = routeChartRef.value.getContext('2d')
    routeChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: topRoutes.map(r => r[0]),
        datasets: [{
          label: 'Spend (AUD)',
          data: topRoutes.map(r => r[1]),
          backgroundColor: '#a855f7'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        indexAxis: 'y',
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (context) => formatCurrency(context.parsed.x)
            }
          }
        },
        scales: {
          x: {
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

// Helper functions for table display
const getRoute = (booking) => {
  if (!booking.air_bookings || booking.air_bookings.length === 0) return 'N/A → N/A'
  
  if (booking.air_bookings.length === 1) {
    const air = booking.air_bookings[0]
    return `${air.origin_airport_iata_code || 'N/A'} → ${air.destination_airport_iata_code || 'N/A'}`
  } else {
    return `Multi-city (${booking.air_bookings.length} flights)`
  }
}

const getAirline = (booking) => {
  if (!booking.air_bookings || booking.air_bookings.length === 0) return 'Unknown'
  
  const airlines = booking.air_bookings
    .map(air => air.primary_airline_name)
    .filter(name => name)
  
  if (airlines.length === 0) return 'Unknown'
  if (airlines.length === 1) return airlines[0]
  
  const uniqueAirlines = [...new Set(airlines)]
  if (uniqueAirlines.length === 1) return uniqueAirlines[0]
  return `${uniqueAirlines[0]} +${uniqueAirlines.length - 1}`
}

const getTravelClass = (booking) => {
  if (!booking.air_bookings || booking.air_bookings.length === 0) return 'N/A'
  
  const classMap = {
    'ECONOMY': 'Economy',
    'PREMIUM_ECONOMY': 'Premium Economy',
    'BUSINESS': 'Business',
    'FIRST': 'First Class'
  }
  
  return classMap[booking.air_bookings[0].travel_class] || 'N/A'
}

const getTotalCarbon = (booking) => {
  if (!booking.air_bookings || booking.air_bookings.length === 0) return '0.00'
  
  const total = booking.air_bookings.reduce((airSum, air) => {
    const segmentCarbon = (air.segments || []).reduce((segSum, seg) => 
      segSum + (parseFloat(seg.carbon_emissions_kg) || 0), 0)
    return airSum + segmentCarbon
  }, 0)
  
  return total.toFixed(2)
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
      <h1 class="text-2xl font-bold text-gray-900">Air Travel Analytics</h1>
      <p class="mt-1 text-sm text-gray-500">Analyze flight bookings, airline spending, and carbon emissions</p>
    </div>

    <!-- Universal Filters -->
    <UniversalFilters
      :show-traveller="true"
      :show-date-range="true"
      :show-destinations="true"
      :show-organization="false"
      :show-status="true"
      :show-supplier="false"
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
      <!-- Total Flights -->
      <div class="bg-white rounded-xl shadow-sm p-6">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-gray-600">Total Flights</p>
            <p class="text-3xl font-bold text-gray-900 mt-2">{{ summaryStats.total_bookings }}</p>
          </div>
          <div class="bg-blue-100 p-3 rounded-full">
            <span class="mdi mdi-airplane text-blue-600 text-2xl"></span>
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

      <!-- Average Spend -->
      <div class="bg-white rounded-xl shadow-sm p-6">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-gray-600">Average Spend</p>
            <p class="text-3xl font-bold text-gray-900 mt-2">{{ formatCurrency(summaryStats.avg_spend) }}</p>
          </div>
          <div class="bg-purple-100 p-3 rounded-full">
            <span class="mdi mdi-chart-line text-purple-600 text-2xl"></span>
          </div>
        </div>
      </div>

      <!-- Carbon Emissions -->
      <div class="bg-white rounded-xl shadow-sm p-6">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-gray-600">Carbon Emissions</p>
            <p class="text-3xl font-bold text-gray-900 mt-2">{{ summaryStats.total_carbon_kg.toFixed(0) }}</p>
            <p class="text-xs text-gray-500 mt-1">kg CO₂</p>
          </div>
          <div class="bg-orange-100 p-3 rounded-full">
            <span class="mdi mdi-leaf text-orange-600 text-2xl"></span>
          </div>
        </div>
      </div>
    </div>

    <!-- Charts -->
    <div v-if="!loading && !error" class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Airline Chart -->
      <div class="bg-white rounded-xl shadow-sm overflow-hidden">
        <div class="border-b border-gray-200 px-6 py-4">
          <h3 class="text-lg font-semibold text-gray-900">Spend by Airline</h3>
        </div>
        <div class="p-6" style="height: 400px;">
          <canvas ref="airlineChartRef"></canvas>
        </div>
      </div>

      <!-- Class Chart -->
      <div class="bg-white rounded-xl shadow-sm overflow-hidden">
        <div class="border-b border-gray-200 px-6 py-4">
          <h3 class="text-lg font-semibold text-gray-900">Cabin Class Distribution</h3>
        </div>
        <div class="p-6" style="height: 400px;">
          <canvas ref="classChartRef"></canvas>
        </div>
      </div>
    </div>

    <!-- Routes Chart (Full Width) -->
    <div v-if="!loading && !error" class="bg-white rounded-xl shadow-sm overflow-hidden">
      <div class="border-b border-gray-200 px-6 py-4">
        <h3 class="text-lg font-semibold text-gray-900">Top Routes by Spend</h3>
      </div>
      <div class="p-6" style="height: 400px;">
        <canvas ref="routeChartRef"></canvas>
      </div>
    </div>

    <!-- Bookings Table -->
    <div v-if="!loading && !error" class="bg-white rounded-xl shadow-sm overflow-hidden">
      <div class="border-b border-gray-200 px-6 py-4 flex justify-between items-center">
        <h3 class="text-lg font-semibold text-gray-900">Flight Bookings</h3>
        <span class="text-sm text-gray-500">{{ airBookings.length }} bookings</span>
      </div>

      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Reference</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Traveller</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Route</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Airline</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Class</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Travel Date</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Carbon (kg)</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="booking in airBookings" :key="booking.id" class="hover:bg-gray-50">
              <td class="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900">{{ booking.agent_booking_reference }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{{ booking.traveller_name }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ getRoute(booking) }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ getAirline(booking) }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ getTravelClass(booking) }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ formatDate(booking.travel_date) }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-900">{{ formatCurrency(booking.total_amount) }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-right">{{ getTotalCarbon(booking) }}</td>
            </tr>
          </tbody>
        </table>

        <div v-if="airBookings.length === 0" class="text-center py-12">
          <span class="mdi mdi-airplane-off text-gray-300 text-6xl"></span>
          <p class="text-gray-500 mt-4">No flight bookings found</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Minimal scoped styles - most styling uses Tailwind classes */
</style>
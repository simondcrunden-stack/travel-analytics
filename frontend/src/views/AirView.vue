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

// Summary stats - Calculate from AIR FARE ONLY (not total booking amount)
const summaryStats = computed(() => {
  let totalAirSpend = 0
  let totalFlights = 0
  let totalCarbon = 0

  airBookings.value.forEach(booking => {
    (booking.air_bookings || []).forEach(air => {
      // Use air.total_fare for air-specific spend
      totalAirSpend += parseFloat(air.total_fare || 0)
      totalFlights++
      totalCarbon += parseFloat(air.total_carbon_kg || 0)
    })
  })

  return {
    total_bookings: totalFlights,
    total_spend: totalAirSpend,
    avg_spend: totalFlights > 0 ? totalAirSpend / totalFlights : 0,
    total_carbon_kg: totalCarbon,
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

  // Airline Distribution Chart - Calculate from AIR FARE ONLY
  const airlineData = {}
  airBookings.value.forEach(booking => {
    (booking.air_bookings || []).forEach(air => {
      const airline = air.primary_airline_name || 'Unknown'
      if (!airlineData[airline]) {
        airlineData[airline] = 0
      }
      // Use air.total_fare instead of booking.total_amount
      const amount = parseFloat(air.total_fare || 0)
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

  // Travel Class Distribution Chart - Calculate from AIR FARE ONLY
  const classData = {}
  airBookings.value.forEach(booking => {
    (booking.air_bookings || []).forEach(air => {
      const travelClass = air.travel_class || 'Unknown'
      if (!classData[travelClass]) {
        classData[travelClass] = 0
      }
      // Use air.total_fare instead of booking.total_amount
      const amount = parseFloat(air.total_fare || 0)
      classData[travelClass] += amount
    })
  })

  // Format cabin class labels to Camel Case
  const formatCabinClass = (className) => {
    const classMap = {
      'ECONOMY': 'Economy',
      'PREMIUM_ECONOMY': 'Premium Economy',
      'BUSINESS': 'Business',
      'FIRST': 'First Class',
      'RESTRICTED_ECONOMY': 'Restricted Economy'
    }
    return classMap[className] || className
  }

  if (classChartRef.value) {
    const ctx = classChartRef.value.getContext('2d')
    classChart = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: Object.keys(classData).map(formatCabinClass),
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

  // Top Routes Chart - Calculate from AIR FARE ONLY, limit to 10
  const routeData = {}
  airBookings.value.forEach(booking => {
    (booking.air_bookings || []).forEach(air => {
      const route = `${air.origin_airport_iata_code || '?'} → ${air.destination_airport_iata_code || '?'}`
      if (!routeData[route]) {
        routeData[route] = 0
      }
      // Use air.total_fare instead of booking.total_amount
      const amount = parseFloat(air.total_fare || 0)
      routeData[route] += amount
    })
  })

  const topRoutes = Object.entries(routeData)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)  // Already limited to 10

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

// Pagination
const totalPages = computed(() => {
  return Math.ceil(airBookings.value.length / itemsPerPage.value)
})

const startIndex = computed(() => {
  return (currentPage.value - 1) * itemsPerPage.value
})

const endIndex = computed(() => {
  return currentPage.value * itemsPerPage.value
})

const paginatedAirBookings = computed(() => {
  return airBookings.value.slice(startIndex.value, endIndex.value)
})

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

const getAirFare = (booking) => {
  // Return total of all air fares for this booking
  if (!booking.air_bookings || booking.air_bookings.length === 0) return 0

  return booking.air_bookings.reduce((total, air) => {
    return total + parseFloat(air.total_fare || 0)
  }, 0)
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
      :show-supplier="true"
      supplier-label="Airline"
      supplier-placeholder="Qantas Airways, Emirates..."
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
      <!-- Table Controls -->
      <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
        <div class="flex items-center space-x-4">
          <span class="text-sm text-gray-700">
            Showing {{ startIndex + 1 }}-{{ Math.min(endIndex, airBookings.length) }} of {{ airBookings.length }} bookings
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
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Route</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Airline</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Class</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Travel Date</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Carbon (kg)</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="booking in paginatedAirBookings" :key="booking.id" class="hover:bg-gray-50">
              <td class="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900">{{ booking.agent_booking_reference }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{{ booking.traveller_name }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ getRoute(booking) }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ getAirline(booking) }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ getTravelClass(booking) }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ formatDate(booking.travel_date) }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-900">{{ formatCurrency(getAirFare(booking)) }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-right">{{ getTotalCarbon(booking) }}</td>
            </tr>
          </tbody>
        </table>

        <div v-if="airBookings.length === 0" class="text-center py-12">
          <span class="mdi mdi-airplane-off text-gray-300 text-6xl"></span>
          <p class="text-gray-500 mt-4">No flight bookings found</p>
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
            {{ (currentPage - 1) * itemsPerPage + 1 }}-{{ Math.min(currentPage * itemsPerPage, airBookings.length) }}
            of {{ airBookings.length }}
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
<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import bookingService from '@/services/bookingService'
import preferredAirlineService from '@/services/preferredAirlineService'
import { Chart, registerables } from 'chart.js'
import UniversalFilters from '@/components/common/UniversalFilters.vue'
import { useAuthStore } from '@/stores/auth'

// Register Chart.js components
Chart.register(...registerables)

// Get user organization from auth store
const authStore = useAuthStore()

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

// Preferred Airlines state
const loadingPreferredAirlines = ref(false)
const complianceData = ref(null)
const marketShareData = ref(null)
const showComplianceSection = ref(true)
const showMarketShareSection = ref(true)

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
  await Promise.all([
    loadData(filters),
    loadPreferredAirlineData(filters)
  ])
}

// Methods
const loadData = async (filters = {}) => {
  try {
    loading.value = true
    error.value = null

    console.log('🌐 [AirView] Loading air travel data with filters:', filters)

    // Add booking_type filter to only get air bookings
    const airFilters = {
      ...filters,
      booking_type: 'AIR'
    }

    // bookingService handles filter transformation automatically
    const data = await bookingService.getBookings(airFilters)
    bookings.value = data.results || []

    // Use backend summary statistics (now includes transactions)
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

// Load preferred airline data
const loadPreferredAirlineData = async (filters = {}) => {
  if (!authStore.user || !authStore.user.organization) {
    console.log('⚠️ [AirView] No organization found for user, skipping preferred airline data')
    return
  }

  try {
    loadingPreferredAirlines.value = true

    const params = {
      organization: authStore.user.organization.id,
      ...filters
    }

    console.log('🔍 [AirView] Loading preferred airline data with params:', params)

    // Load compliance report and market share performance in parallel
    const [compliance, marketShare] = await Promise.all([
      preferredAirlineService.getComplianceReport(params),
      preferredAirlineService.getMarketSharePerformance(params)
    ])

    complianceData.value = compliance
    marketShareData.value = marketShare

    console.log('✅ [AirView] Preferred airline data loaded:', {
      compliance: compliance.summary,
      marketShare: marketShare.totals
    })

  } catch (err) {
    console.error('❌ [AirView] Error loading preferred airline data:', err)
    console.error('❌ [AirView] Error response:', err.response?.data)
    console.error('❌ [AirView] Error status:', err.response?.status)
    console.error('❌ [AirView] Request params that were sent:', params)
    // Don't show error to user - just hide sections if no data
    complianceData.value = null
    marketShareData.value = null
  } finally {
    loadingPreferredAirlines.value = false
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
  await Promise.all([
    loadData(),
    loadPreferredAirlineData()
  ])
})
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Air Booking Records</h1>
        <p class="mt-1 text-sm text-gray-500">Analyze flight bookings, airline spending, and carbon emissions</p>
      </div>
    </div>

    <!-- Universal Filters -->
    <UniversalFilters
      :show-traveller="true"
      :show-date-range="true"
      :show-destinations="true"
      :show-organization="true"
      :show-status="true"
      :show-supplier="true"
      supplier-label="Airline"
      supplier-placeholder="Qantas Airways, Emirates..."
      supplier-type="airline"
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
            <p class="text-3xl font-bold text-gray-900 mt-2">{{ (summary.booking_count || 0).toLocaleString() }}</p>
          </div>
          <div class="bg-blue-100 p-3 rounded-full">
            <span class="mdi mdi-airplane text-blue-600 text-2xl"></span>
          </div>
        </div>
      </div>

      <!-- Total Spend (includes transactions) -->
      <div class="bg-white rounded-xl shadow-sm p-6">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-gray-600">Total Spend</p>
            <p class="text-3xl font-bold text-gray-900 mt-2">{{ formatCurrency(summary.total_spend) }}</p>
            <p class="text-xs text-gray-500 mt-1">incl. exchanges & refunds</p>
          </div>
          <div class="bg-green-100 p-3 rounded-full">
            <span class="mdi mdi-currency-usd text-green-600 text-2xl"></span>
          </div>
        </div>
      </div>

      <!-- Average Spend (includes transactions) -->
      <div class="bg-white rounded-xl shadow-sm p-6">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-gray-600">Average Spend</p>
            <p class="text-3xl font-bold text-gray-900 mt-2">{{ formatCurrency(summary.booking_count > 0 ? summary.total_spend / summary.booking_count : 0) }}</p>
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
            <p class="text-3xl font-bold text-gray-900 mt-2">{{ Math.round(summary.total_emissions || 0).toLocaleString() }}</p>
            <p class="text-xs text-gray-500 mt-1">kg CO₂</p>
          </div>
          <div class="bg-orange-100 p-3 rounded-full">
            <span class="mdi mdi-leaf text-orange-600 text-2xl"></span>
          </div>
        </div>
      </div>
    </div>

    <!-- Preferred Airline Compliance Section -->
    <div v-if="!loading && !error && complianceData && complianceData.summary.total_bookings > 0" class="space-y-6">
      <!-- Section Header -->
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-xl font-bold text-gray-900">Preferred Airline Compliance</h2>
          <p class="text-sm text-gray-500 mt-1">Track bookings on and off preferred airlines</p>
        </div>
        <button
          @click="showComplianceSection = !showComplianceSection"
          class="text-gray-400 hover:text-gray-600"
        >
          <span class="mdi" :class="showComplianceSection ? 'mdi-chevron-up' : 'mdi-chevron-down'"></span>
        </button>
      </div>

      <div v-show="showComplianceSection" class="space-y-6">
        <!-- Compliance Summary Cards -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          <!-- Overall Compliance Rate -->
          <div class="bg-white rounded-xl shadow-sm p-6">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm font-medium text-gray-600">Compliance Rate</p>
                <p class="text-3xl font-bold mt-2" :class="complianceData.summary.compliance_rate >= 80 ? 'text-green-600' : complianceData.summary.compliance_rate >= 60 ? 'text-yellow-600' : 'text-red-600'">
                  {{ complianceData.summary.compliance_rate.toFixed(1) }}%
                </p>
              </div>
              <div :class="['p-3', 'rounded-full', complianceData.summary.compliance_rate >= 80 ? 'bg-green-100' : complianceData.summary.compliance_rate >= 60 ? 'bg-yellow-100' : 'bg-red-100']">
                <span :class="['mdi', 'mdi-check-circle', 'text-2xl', complianceData.summary.compliance_rate >= 80 ? 'text-green-600' : complianceData.summary.compliance_rate >= 60 ? 'text-yellow-600' : 'text-red-600']"></span>
              </div>
            </div>
            <div class="mt-4 text-xs text-gray-500">
              {{ complianceData.summary.preferred_bookings }} of {{ complianceData.summary.total_bookings }} bookings on preferred airlines
            </div>
          </div>

          <!-- Preferred Spend -->
          <div class="bg-white rounded-xl shadow-sm p-6">
            <p class="text-sm font-medium text-gray-600">Preferred Airline Spend</p>
            <p class="text-2xl font-bold text-green-600 mt-2">
              {{ formatCurrency(complianceData.summary.preferred_spend) }}
            </p>
            <div class="mt-2 text-xs text-gray-500">
              of {{ formatCurrency(complianceData.summary.total_spend) }} total
            </div>
          </div>

          <!-- Non-Preferred Spend -->
          <div class="bg-white rounded-xl shadow-sm p-6">
            <p class="text-sm font-medium text-gray-600">Off-Preferred Spend</p>
            <p class="text-2xl font-bold text-red-600 mt-2">
              {{ formatCurrency(complianceData.summary.non_preferred_spend) }}
            </p>
            <div class="mt-2 text-xs text-gray-500">
              {{ complianceData.summary.non_preferred_bookings }} bookings
            </div>
          </div>
        </div>

        <!-- Worst Offending Cost Centers -->
        <div v-if="complianceData.by_cost_center && complianceData.by_cost_center.length > 0" class="bg-white rounded-xl shadow-sm overflow-hidden">
          <div class="border-b border-gray-200 px-6 py-4">
            <h3 class="text-lg font-semibold text-gray-900">Compliance by Cost Center</h3>
            <p class="text-sm text-gray-500 mt-1">Cost centers with highest off-preferred spend</p>
          </div>
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Cost Center</th>
                  <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Total Spend</th>
                  <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Off-Preferred</th>
                  <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Compliance Rate</th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                <tr v-for="cc in complianceData.by_cost_center.slice(0, 5)" :key="cc.cost_center" class="hover:bg-gray-50">
                  <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{{ cc.cost_center }}</td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900">{{ formatCurrency(cc.total_spend) }}</td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-right text-red-600 font-semibold">{{ formatCurrency(cc.non_preferred_spend) }}</td>
                  <td class="px-6 py-4 whitespace-nowrap text-right">
                    <span class="px-2 py-1 text-xs font-semibold rounded-full" :class="cc.compliance_rate >= 80 ? 'bg-green-100 text-green-800' : cc.compliance_rate >= 60 ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'">
                      {{ cc.compliance_rate.toFixed(1) }}%
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Worst Offending Travelers -->
        <div v-if="complianceData.by_traveller && complianceData.by_traveller.length > 0" class="bg-white rounded-xl shadow-sm overflow-hidden">
          <div class="border-b border-gray-200 px-6 py-4">
            <h3 class="text-lg font-semibold text-gray-900">Compliance by Traveller</h3>
            <p class="text-sm text-gray-500 mt-1">Travelers with highest off-preferred spend</p>
          </div>
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Traveller</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Cost Center</th>
                  <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Total Spend</th>
                  <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Off-Preferred</th>
                  <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Compliance Rate</th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                <tr v-for="t in complianceData.by_traveller.slice(0, 5)" :key="t.traveller_id" class="hover:bg-gray-50">
                  <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{{ t.traveller_name }}</td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ t.cost_center }}</td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900">{{ formatCurrency(t.total_spend) }}</td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-right text-red-600 font-semibold">{{ formatCurrency(t.non_preferred_spend) }}</td>
                  <td class="px-6 py-4 whitespace-nowrap text-right">
                    <span class="px-2 py-1 text-xs font-semibold rounded-full" :class="t.compliance_rate >= 80 ? 'bg-green-100 text-green-800' : t.compliance_rate >= 60 ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'">
                      {{ t.compliance_rate.toFixed(1) }}%
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- Market Share Performance Section -->
    <div v-if="!loading && !error && marketShareData && marketShareData.preferred_airlines.length > 0" class="space-y-6">
      <!-- Section Header -->
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-xl font-bold text-gray-900">Market Share Performance</h2>
          <p class="text-sm text-gray-500 mt-1">Target vs actual performance for preferred airlines</p>
        </div>
        <button
          @click="showMarketShareSection = !showMarketShareSection"
          class="text-gray-400 hover:text-gray-600"
        >
          <span class="mdi" :class="showMarketShareSection ? 'mdi-chevron-up' : 'mdi-chevron-down'"></span>
        </button>
      </div>

      <div v-show="showMarketShareSection" class="space-y-6">
        <!-- Market Share Cards -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div v-for="airline in marketShareData.preferred_airlines" :key="airline.airline_code" class="bg-white rounded-xl shadow-sm p-6">
            <div class="flex items-center justify-between mb-4">
              <div>
                <h3 class="text-lg font-semibold text-gray-900">{{ airline.airline_name }}</h3>
                <p class="text-xs text-gray-500">{{ airline.market_type }}</p>
              </div>
              <span class="px-2 py-1 text-xs font-semibold rounded-full" :class="
                airline.performance_status === 'EXCEEDING' ? 'bg-green-100 text-green-800' :
                airline.performance_status === 'MEETING' ? 'bg-blue-100 text-blue-800' :
                'bg-red-100 text-red-800'
              ">
                {{ airline.performance_status === 'EXCEEDING' ? 'Exceeding' : airline.performance_status === 'MEETING' ? 'Meeting' : 'Below Target' }}
              </span>
            </div>

            <!-- Market Share Progress -->
            <div class="space-y-2">
              <div class="flex justify-between text-sm">
                <span class="text-gray-600">Market Share</span>
                <span class="font-semibold" :class="airline.market_share_variance >= 0 ? 'text-green-600' : 'text-red-600'">
                  {{ airline.actual_market_share.toFixed(1) }}% / {{ airline.target_market_share.toFixed(1) }}%
                </span>
              </div>
              <div class="w-full bg-gray-200 rounded-full h-2">
                <div class="h-2 rounded-full transition-all" :class="airline.market_share_variance >= 0 ? 'bg-green-500' : 'bg-red-500'"
                  :style="{ width: Math.min((airline.actual_market_share / airline.target_market_share * 100), 100) + '%' }">
                </div>
              </div>
              <p class="text-xs" :class="airline.market_share_variance >= 0 ? 'text-green-600' : 'text-red-600'">
                {{ airline.market_share_variance > 0 ? '+' : '' }}{{ airline.market_share_variance.toFixed(1) }}% variance
              </p>
            </div>

            <!-- Revenue -->
            <div class="mt-4 pt-4 border-t border-gray-200">
              <div class="flex justify-between text-sm">
                <span class="text-gray-600">Revenue</span>
                <span class="font-semibold text-gray-900">{{ formatCurrency(airline.actual_revenue) }}</span>
              </div>
              <div v-if="airline.target_revenue" class="text-xs text-gray-500 mt-1">
                Target: {{ formatCurrency(airline.target_revenue) }}
                <span v-if="airline.revenue_variance" :class="airline.revenue_variance >= 0 ? 'text-green-600' : 'text-red-600'">
                  ({{ airline.revenue_variance > 0 ? '+' : '' }}{{ formatCurrency(airline.revenue_variance) }})
                </span>
              </div>
              <div class="text-xs text-gray-500 mt-1">
                {{ airline.booking_count }} bookings
              </div>
            </div>
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
      <!-- Table Header -->
      <div class="p-6 border-b border-gray-200">
        <h2 class="text-lg font-semibold text-gray-900">Air Booking Records</h2>
        <p class="text-sm text-gray-600 mt-1">{{ airBookings.length }} bookings found</p>
      </div>

      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Reference
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Traveller
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Route
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Airline
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Class
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Travel Date
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Amount
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Carbon (kg)
              </th>
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
<template>
  <div class="space-y-6">
    <!-- Header -->
    <div>
      <h1 class="text-2xl font-bold text-gray-900">Airline Spend Analysis</h1>
      <p class="mt-1 text-sm text-gray-500">
        Detailed breakdown of air travel expenses
      </p>
    </div>

    <!-- Filters -->
    <div class="bg-white p-4 rounded-lg shadow">
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Start Date
          </label>
          <input
            v-model="filters.start_date"
            type="date"
            class="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
            @change="loadData"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            End Date
          </label>
          <input
            v-model="filters.end_date"
            type="date"
            class="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
            @change="loadData"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Travel Class
          </label>
          <select
            v-model="filters.travel_class"
            class="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
            @change="loadData"
          >
            <option value="">All Classes</option>
            <option value="ECONOMY">Economy</option>
            <option value="PREMIUM_ECONOMY">Premium Economy</option>
            <option value="BUSINESS">Business</option>
            <option value="FIRST">First Class</option>
          </select>
        </div>
        <div class="flex items-end">
          <button
            @click="resetFilters"
            class="w-full px-4 py-2 text-sm border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Reset Filters
          </button>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center items-center py-12">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-lg p-4">
      <p class="text-red-800">{{ error }}</p>
      <button 
        @click="loadData" 
        class="mt-2 text-sm text-red-600 hover:text-red-800 underline"
      >
        Try Again
      </button>
    </div>

    <!-- Content -->
    <div v-else>
      <!-- Summary Cards -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6 mt-6">
        <div class="bg-white rounded-lg shadow p-6">
          <p class="text-sm font-medium text-gray-600">Total Air Spend</p>
          <p class="text-2xl font-bold text-gray-900 mt-2">
            {{ formatCurrency(totalSpend) }}
          </p>
          <p class="text-xs text-gray-500 mt-1">
            {{ airBookings.length }} flights
          </p>
        </div>

        <div class="bg-white rounded-lg shadow p-6">
          <p class="text-sm font-medium text-gray-600">Average Fare</p>
          <p class="text-2xl font-bold text-gray-900 mt-2">
            {{ formatCurrency(averageFare) }}
          </p>
          <p class="text-xs text-gray-500 mt-1">
            Per booking
          </p>
        </div>

        <div class="bg-white rounded-lg shadow p-6">
          <p class="text-sm font-medium text-gray-600">Total Carbon</p>
          <p class="text-2xl font-bold text-gray-900 mt-2">
            {{ formatNumber(totalCarbon) }} kg
          </p>
          <p class="text-xs text-gray-500 mt-1">
            CO2 emissions
          </p>
        </div>

        <div class="bg-white rounded-lg shadow p-6">
          <p class="text-sm font-medium text-gray-600">Compliance Rate</p>
          <p class="text-2xl font-bold text-gray-900 mt-2">
            {{ complianceRate }}%
          </p>
          <p class="text-xs text-gray-500 mt-1">
            {{ compliantBookings }} compliant
          </p>
        </div>
      </div>

      <!-- Charts -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <AirlineSpendChart :filters="filters" />
        <TravelClassChart :filters="filters" />
      </div>

      <AdvancePurchaseChart :filters="filters" class="mb-6" />

      <!-- Bookings Table -->
      <div class="bg-white rounded-lg shadow mt-6">
        <div class="p-6 border-b border-gray-200">
          <h2 class="text-lg font-semibold text-gray-900">All Air Bookings</h2>
        </div>
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Reference
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Traveller
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Route
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Airline
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Class
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Travel Date
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Amount
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Carbon (kg)
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Status
                </th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="booking in airBookings" :key="booking.id" class="hover:bg-gray-50">
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {{ booking.agent_booking_reference }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {{ booking.traveller_name }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {{ getRoute(booking) }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {{ getAirline(booking) }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {{ getTravelClass(booking) }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {{ formatDate(booking.travel_date) }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {{ formatCurrency(booking.total_amount) }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {{ getCarbon(booking) }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span :class="getStatusClass(booking.status)">
                    {{ booking.status }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import AirlineSpendChart from '@/components/air/AirlineSpendChart.vue'
import TravelClassChart from '@/components/air/TravelClassChart.vue'
import AdvancePurchaseChart from '@/components/air/AdvancePurchaseChart.vue'
import { ref, computed, onMounted, nextTick } from 'vue'
import bookingService from '@/services/bookingService'

// State
const loading = ref(true)
const error = ref(null)
const airBookings = ref([])

// Filters
const filters = ref({
  start_date: '',
  end_date: '',
  travel_class: ''
})

// Charts
const airlineChart = ref(null)
const routeChart = ref(null)
let airlineChartInstance = null
let routeChartInstance = null

// Computed
const totalSpend = computed(() => {
  return airBookings.value.reduce((sum, b) => sum + parseFloat(b.total_amount || 0), 0)
})

const averageFare = computed(() => {
  return airBookings.value.length > 0 ? totalSpend.value / airBookings.value.length : 0
})

const totalCarbon = computed(() => {
  return airBookings.value.reduce((sum, b) => {
    const carbon = b.air_details?.segments?.reduce((s, seg) => 
      s + parseFloat(seg.carbon_emissions_kg || 0), 0) || 0
    return sum + carbon
  }, 0)
})

const compliantBookings = computed(() => {
  return airBookings.value.filter(b => 
    b.violations?.length === 0 || !b.violations
  ).length
})

const complianceRate = computed(() => {
  return airBookings.value.length > 0 
    ? Math.round((compliantBookings.value / airBookings.value.length) * 100)
    : 0
})

// Methods
const loadData = async () => {
  try {
    loading.value = true
    error.value = null

    const params = {
      booking_type: 'AIR'
    }

    if (filters.value.start_date) {
      params.travel_date_after = filters.value.start_date
    }
    if (filters.value.end_date) {
      params.travel_date_before = filters.value.end_date
    }

    const response = await bookingService.getAirlineSpend(params)
    airBookings.value = response.results || response

    // Filter by travel class if selected
    if (filters.value.travel_class) {
      airBookings.value = airBookings.value.filter(b => 
        b.air_details?.travel_class === filters.value.travel_class
      )
    }

    await nextTick()
    renderCharts()

  } catch (err) {
    console.error('Error loading airline data:', err)
    error.value = 'Failed to load airline spend data. Please try again.'
  } finally {
    loading.value = false
  }
}

const renderCharts = () => {
  // Group by airline
  const airlineGroups = {}
  airBookings.value.forEach(booking => {
    const airline = booking.air_details?.primary_airline_name || 'Unknown'
    if (!airlineGroups[airline]) {
      airlineGroups[airline] = 0
    }
    airlineGroups[airline] += parseFloat(booking.total_amount || 0)
  })

  // Airline Chart
  if (airlineChartInstance) airlineChartInstance.destroy()
  if (airlineChart.value) {
    const ctx = airlineChart.value.getContext('2d')
    airlineChartInstance = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: Object.keys(airlineGroups),
        datasets: [{
          label: 'Spend (AUD)',
          data: Object.values(airlineGroups),
          backgroundColor: '#0ea5e9'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false }
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

  // Route Chart
  const routeGroups = {}
  airBookings.value.forEach(booking => {
    const route = getRoute(booking)
    if (!routeGroups[route]) {
      routeGroups[route] = 0
    }
    routeGroups[route] += parseFloat(booking.total_amount || 0)
  })

  // Get top 10 routes
  const topRoutes = Object.entries(routeGroups)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)

  if (routeChartInstance) routeChartInstance.destroy()
  if (routeChart.value) {
    const ctx = routeChart.value.getContext('2d')
    routeChartInstance = new Chart(ctx, {
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
          legend: { display: false }
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

const resetFilters = () => {
  filters.value = {
    start_date: '',
    end_date: '',
    travel_class: ''
  }
  loadData()
}

const getRoute = (booking) => {
  const origin = booking.air_details?.origin || 'N/A'
  const destination = booking.air_details?.destination || 'N/A'
  return `${origin} → ${destination}`
}

const getAirline = (booking) => {
  return booking.air_details?.primary_airline_name || 'Unknown'
}

const getTravelClass = (booking) => {
  const classMap = {
    'ECONOMY': 'Economy',
    'PREMIUM_ECONOMY': 'Premium Economy',
    'BUSINESS': 'Business',
    'FIRST': 'First Class'
  }
  return classMap[booking.air_details?.travel_class] || 'N/A'
}

const getCarbon = (booking) => {
  const carbon = booking.air_details?.segments?.reduce((sum, seg) => 
    sum + parseFloat(seg.carbon_emissions_kg || 0), 0) || 0
  return carbon > 0 ? formatNumber(carbon) : 'N/A'
}

const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-AU', {
    style: 'currency',
    currency: 'AUD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(amount || 0)
}

const formatNumber = (num) => {
  return new Intl.NumberFormat('en-AU', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2
  }).format(num || 0)
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('en-AU', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

const getStatusClass = (status) => {
  const classes = {
    'CONFIRMED': 'px-2 py-1 text-xs rounded-full bg-green-100 text-green-800',
    'CANCELLED': 'px-2 py-1 text-xs rounded-full bg-red-100 text-red-800',
    'PENDING': 'px-2 py-1 text-xs rounded-full bg-yellow-100 text-yellow-800',
    'REFUNDED': 'px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800'
  }
  return classes[status] || classes['PENDING']
}

// Lifecycle
onMounted(() => {
  loadData()
})
</script>
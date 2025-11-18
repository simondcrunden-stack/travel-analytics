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
const cityChartRef = ref(null)
const hotelChainChartRef = ref(null)
let cityChart = null
let hotelChainChart = null

// Accommodation bookings computed (backend filters, we just display hotel ones)
const accommodationBookings = computed(() => {
  return bookings.value.filter(b => b.accommodation_bookings && b.accommodation_bookings.length > 0)
})

// Summary stats - Calculate from ACCOMMODATION ONLY (not total booking amount)
const summaryStats = computed(() => {
  let totalAccommodationSpend = 0
  let totalNights = 0
  let totalAccommodationBookings = 0

  accommodationBookings.value.forEach(booking => {
    booking.accommodation_bookings.forEach(hotel => {
      // Use hotel.total_amount_base for accommodation-specific spend
      totalAccommodationSpend += parseFloat(hotel.total_amount_base || 0)
      totalNights += hotel.number_of_nights || 0
      totalAccommodationBookings++
    })
  })

  const avgNightlyRate = totalNights > 0 ? totalAccommodationSpend / totalNights : 0

  return {
    total_bookings: totalAccommodationBookings,
    total_spend: totalAccommodationSpend,
    avg_spend: totalAccommodationBookings > 0 ? totalAccommodationSpend / totalAccommodationBookings : 0,
    total_nights: totalNights,
    avg_nightly_rate: avgNightlyRate,
  }
})

// Removed availableCities and availableHotelChains - not needed with UniversalFilters

// Handle filter changes from UniversalFilters
const handleFiltersChanged = async (filters) => {
  console.log('🏨 [AccommodationView] Filters changed:', filters)
  currentFilters.value = filters
  await loadData(filters)
}

// Methods
const loadData = async (filters = {}) => {
  try {
    loading.value = true
    error.value = null

    console.log('🌐 [AccommodationView] Loading accommodation data with filters:', filters)

    // bookingService handles filter transformation automatically
    const data = await bookingService.getBookings(filters)
    bookings.value = data.results || []

    // Use backend summary statistics
    if (data.summary) {
      summary.value = data.summary
      console.log('📊 [AccommodationView] Backend summary:', summary.value)
    }

    console.log('✅ [AccommodationView] Loaded', bookings.value.length, 'bookings,', accommodationBookings.value.length, 'with accommodation')

  } catch (err) {
    console.error('❌ [AccommodationView] Error loading data:', err)
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
  if (cityChart) cityChart.destroy()
  if (hotelChainChart) hotelChainChart.destroy()

  // City Chart Data - Calculate from ACCOMMODATION ONLY
  const cityChartData = {}
  accommodationBookings.value.forEach(booking => {
    booking.accommodation_bookings.forEach(hotel => {
      const city = hotel.city || 'Unknown'
      if (!cityChartData[city]) {
        cityChartData[city] = 0
      }
      // Use hotel.total_amount_base instead of booking.total_amount
      const amount = parseFloat(hotel.total_amount_base || 0)
      cityChartData[city] += amount
    })
  })

  const topCities = Object.entries(cityChartData)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)

  if (cityChartRef.value) {
    const ctx = cityChartRef.value.getContext('2d')
    cityChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: topCities.map(c => c[0]),
        datasets: [{
          label: 'Spend (AUD)',
          data: topCities.map(c => c[1]),
          backgroundColor: '#10b981'
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

  // Hotel Chain Chart Data - Calculate from ACCOMMODATION ONLY
  const hotelChainChartData = {}
  accommodationBookings.value.forEach(booking => {
    booking.accommodation_bookings.forEach(hotel => {
      const chain = hotel.hotel_chain || 'Independent'
      if (!hotelChainChartData[chain]) {
        hotelChainChartData[chain] = 0
      }
      // Use hotel.total_amount_base instead of booking.total_amount
      const amount = parseFloat(hotel.total_amount_base || 0)
      hotelChainChartData[chain] += amount
    })
  })

  if (hotelChainChartRef.value) {
    const ctx = hotelChainChartRef.value.getContext('2d')
    hotelChainChart = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: Object.keys(hotelChainChartData),
        datasets: [{
          data: Object.values(hotelChainChartData),
          backgroundColor: [
            '#10b981',
            '#3b82f6',
            '#8b5cf6',
            '#f59e0b',
            '#ef4444'
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
  return Math.ceil(accommodationBookings.value.length / itemsPerPage.value)
})

const startIndex = computed(() => {
  return (currentPage.value - 1) * itemsPerPage.value
})

const endIndex = computed(() => {
  return currentPage.value * itemsPerPage.value
})

const paginatedAccommodationBookings = computed(() => {
  return accommodationBookings.value.slice(startIndex.value, endIndex.value)
})

// Helper functions for table display
const getHotelInfo = (booking) => {
  if (!booking.accommodation_bookings || booking.accommodation_bookings.length === 0) {
    return 'N/A'
  }

  if (booking.accommodation_bookings.length === 1) {
    return booking.accommodation_bookings[0].hotel_name || 'Unknown'
  } else {
    return `Multi-city (${booking.accommodation_bookings.length} hotels)`
  }
}

const getAccommodationAmount = (booking) => {
  // Return total of all accommodation amounts for this booking
  if (!booking.accommodation_bookings || booking.accommodation_bookings.length === 0) return 0

  return booking.accommodation_bookings.reduce((total, hotel) => {
    return total + parseFloat(hotel.total_amount_base || 0)
  }, 0)
}

const getCityInfo = (booking) => {
  if (!booking.accommodation_bookings || booking.accommodation_bookings.length === 0) {
    return 'N/A'
  }
  
  const cities = booking.accommodation_bookings
    .map(hotel => hotel.city)
    .filter(city => city)
  
  if (cities.length === 0) return 'Unknown'
  if (cities.length === 1) return cities[0]
  
  const uniqueCities = [...new Set(cities)]
  if (uniqueCities.length === 1) return uniqueCities[0]
  return `${uniqueCities[0]} +${uniqueCities.length - 1}`
}

const getTotalNights = (booking) => {
  if (!booking.accommodation_bookings || booking.accommodation_bookings.length === 0) {
    return 0
  }
  
  return booking.accommodation_bookings.reduce((sum, hotel) => 
    sum + (hotel.number_of_nights || 0), 0)
}

const getCheckInDate = (booking) => {
  if (!booking.accommodation_bookings || booking.accommodation_bookings.length === 0) {
    return 'N/A'
  }
  
  // Get earliest check-in date
  const dates = booking.accommodation_bookings
    .map(hotel => hotel.check_in_date)
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
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Accommodation Records</h1>
        <p class="mt-1 text-sm text-gray-500">Analyze hotel bookings, spending patterns, and lodging preferences</p>
      </div>
    </div>

    <!-- Universal Filters -->
    <UniversalFilters
      :show-traveller="true"
      :show-date-range="true"
      :show-destinations="true"
      :show-organization="true"
      :show-status="false"
      :show-supplier="true"
      supplier-label="Hotel Name"
      supplier-placeholder="Hyatt Regency, InterContinental, Novotel..."
      supplier-type="hotel"
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
            <span class="mdi mdi-bed text-blue-600 text-2xl"></span>
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

      <!-- Total Nights -->
      <div class="bg-white rounded-xl shadow-sm p-6">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-gray-600">Total Nights</p>
            <p class="text-3xl font-bold text-gray-900 mt-2">{{ summaryStats.total_nights }}</p>
          </div>
          <div class="bg-purple-100 p-3 rounded-full">
            <span class="mdi mdi-calendar-range text-purple-600 text-2xl"></span>
          </div>
        </div>
      </div>

      <!-- Avg Nightly Rate -->
      <div class="bg-white rounded-xl shadow-sm p-6">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-gray-600">Avg Nightly Rate</p>
            <p class="text-3xl font-bold text-gray-900 mt-2">{{ formatCurrency(summaryStats.avg_nightly_rate) }}</p>
          </div>
          <div class="bg-orange-100 p-3 rounded-full">
            <span class="mdi mdi-chart-line text-orange-600 text-2xl"></span>
          </div>
        </div>
      </div>
    </div>

    <!-- Charts -->
    <div v-if="!loading && !error" class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Cities Chart -->
      <div class="bg-white rounded-xl shadow-sm overflow-hidden">
        <div class="border-b border-gray-200 px-6 py-4">
          <h3 class="text-lg font-semibold text-gray-900">Top Cities by Spend</h3>
        </div>
        <div class="p-6" style="height: 400px;">
          <canvas ref="cityChartRef"></canvas>
        </div>
      </div>

      <!-- Hotel Chain Chart -->
      <div class="bg-white rounded-xl shadow-sm overflow-hidden">
        <div class="border-b border-gray-200 px-6 py-4">
          <h3 class="text-lg font-semibold text-gray-900">Spend by Hotel Chain</h3>
        </div>
        <div class="p-6" style="height: 400px;">
          <canvas ref="hotelChainChartRef"></canvas>
        </div>
      </div>
    </div>

    <!-- Bookings Table -->
    <div v-if="!loading && !error" class="bg-white rounded-xl shadow-sm overflow-hidden">
      <!-- Table Header -->
      <div class="p-6 border-b border-gray-200">
        <h2 class="text-lg font-semibold text-gray-900">Accommodation Records</h2>
        <p class="text-sm text-gray-600 mt-1">{{ accommodationBookings.length }} bookings found</p>
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
                Hotel
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                City
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Check-in
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Nights
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Amount
              </th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="booking in paginatedAccommodationBookings" :key="booking.id" class="hover:bg-gray-50">
              <td class="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900">{{ booking.agent_booking_reference }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{{ booking.traveller_name }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ getHotelInfo(booking) }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ getCityInfo(booking) }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ getCheckInDate(booking) }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-center">{{ getTotalNights(booking) }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-900">{{ formatCurrency(getAccommodationAmount(booking)) }}</td>
            </tr>
          </tbody>
        </table>

        <div v-if="accommodationBookings.length === 0" class="text-center py-12">
          <span class="mdi mdi-bed-empty text-gray-300 text-6xl"></span>
          <p class="text-gray-500 mt-4">No accommodation bookings found</p>
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
            {{ (currentPage - 1) * itemsPerPage + 1 }}-{{ Math.min(currentPage * itemsPerPage, accommodationBookings.length) }}
            of {{ accommodationBookings.length }}
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
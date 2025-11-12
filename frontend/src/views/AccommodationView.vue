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
const cityChartRef = ref(null)
const hotelChainChartRef = ref(null)
let cityChart = null
let hotelChainChart = null

// Accommodation bookings computed (backend filters, we just display hotel ones)
const accommodationBookings = computed(() => {
  return bookings.value.filter(b => b.accommodation_bookings && b.accommodation_bookings.length > 0)
})

// Summary stats from backend + view-specific calculations
const summaryStats = computed(() => {
  // Sum nights from accommodation bookings (view-specific metric)
  const totalNights = accommodationBookings.value.reduce((sum, b) => {
    const bookingNights = b.accommodation_bookings.reduce((nightSum, hotel) =>
      nightSum + (hotel.number_of_nights || 0), 0)
    return sum + bookingNights
  }, 0)

  const totalSpend = summary.value.total_spend || 0
  const avgNightlyRate = totalNights > 0 ? totalSpend / totalNights : 0

  return {
    total_bookings: summary.value.booking_count || accommodationBookings.value.length,
    total_spend: totalSpend,
    avg_spend: summary.value.booking_count > 0 ? totalSpend / summary.value.booking_count : 0,
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

  // City Chart Data
  const cityChartData = {}
  accommodationBookings.value.forEach(booking => {
    booking.accommodation_bookings.forEach(hotel => {
      const city = hotel.city || 'Unknown'
      if (!cityChartData[city]) {
        cityChartData[city] = 0
      }
      const amount = parseFloat(booking.total_amount || 0) / booking.accommodation_bookings.length
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

  // Hotel Chain Chart Data
  const hotelChainChartData = {}
  accommodationBookings.value.forEach(booking => {
    booking.accommodation_bookings.forEach(hotel => {
      const chain = hotel.hotel_chain || 'Independent'
      if (!hotelChainChartData[chain]) {
        hotelChainChartData[chain] = 0
      }
      const amount = parseFloat(booking.total_amount || 0) / booking.accommodation_bookings.length
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
  <div class="accommodation-view">
    <!-- Header -->
    <div class="page-header">
      <h1 class="text-3xl font-bold text-gray-800">Accommodation Analytics</h1>
      <p class="text-gray-600 mt-2">Analyze hotel bookings, spending patterns, and lodging preferences</p>
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
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Loading accommodation data...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-state">
      <span class="mdi mdi-alert-circle text-red-500 text-4xl"></span>
      <p class="text-red-600 mt-2">{{ error }}</p>
      <button @click="loadData" class="retry-btn">Retry</button>
    </div>

    <!-- Content -->
    <div v-else>
      <!-- Summary Cards -->
      <div class="summary-cards">
        <div class="summary-card">
          <div class="summary-card__icon bg-blue-100">
            <span class="mdi mdi-bed text-blue-600"></span>
          </div>
          <div class="summary-card__content">
            <p class="summary-card__label">Total Bookings</p>
            <p class="summary-card__value">{{ summaryStats.total_bookings }}</p>
          </div>
        </div>

        <div class="summary-card">
          <div class="summary-card__icon bg-green-100">
            <span class="mdi mdi-currency-usd text-green-600"></span>
          </div>
          <div class="summary-card__content">
            <p class="summary-card__label">Total Spend</p>
            <p class="summary-card__value">{{ formatCurrency(summaryStats.total_spend) }}</p>
          </div>
        </div>

        <div class="summary-card">
          <div class="summary-card__icon bg-purple-100">
            <span class="mdi mdi-calendar-range text-purple-600"></span>
          </div>
          <div class="summary-card__content">
            <p class="summary-card__label">Total Nights</p>
            <p class="summary-card__value">{{ summaryStats.total_nights }}</p>
          </div>
        </div>

        <div class="summary-card">
          <div class="summary-card__icon bg-orange-100">
            <span class="mdi mdi-chart-line text-orange-600"></span>
          </div>
          <div class="summary-card__content">
            <p class="summary-card__label">Avg Nightly Rate</p>
            <p class="summary-card__value">{{ formatCurrency(summaryStats.avg_nightly_rate) }}</p>
          </div>
        </div>
      </div>

      <!-- Charts -->
      <div class="charts-section">
        <div class="chart-container">
          <div class="chart-header">
            <h3 class="chart-title">Top Cities by Spend</h3>
          </div>
          <div class="chart-content">
            <canvas ref="cityChartRef"></canvas>
          </div>
        </div>

        <div class="chart-container">
          <div class="chart-header">
            <h3 class="chart-title">Spend by Hotel Chain</h3>
          </div>
          <div class="chart-content">
            <canvas ref="hotelChainChartRef"></canvas>
          </div>
        </div>
      </div>

      <!-- Bookings Table -->
      <div class="table-section">
        <div class="table-header">
          <h3 class="text-xl font-semibold text-gray-800">Accommodation Bookings</h3>
          <span class="text-sm text-gray-500">{{ accommodationBookings.length }} bookings</span>
        </div>

        <div class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>Reference</th>
                <th>Traveller</th>
                <th>Hotel</th>
                <th>City</th>
                <th>Check-in</th>
                <th>Nights</th>
                <th>Amount</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="booking in accommodationBookings" :key="booking.id">
                <td class="font-mono text-sm">{{ booking.agent_booking_reference }}</td>
                <td>{{ booking.traveller_name }}</td>
                <td>{{ getHotelInfo(booking) }}</td>
                <td>{{ getCityInfo(booking) }}</td>
                <td>{{ getCheckInDate(booking) }}</td>
                <td class="text-center">{{ getTotalNights(booking) }}</td>
                <td class="font-semibold">{{ formatCurrency(booking.total_amount) }}</td>
              </tr>
            </tbody>
          </table>

          <div v-if="accommodationBookings.length === 0" class="empty-state">
            <span class="mdi mdi-bed-empty text-gray-300 text-6xl"></span>
            <p class="text-gray-500 mt-4">No accommodation bookings found</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.accommodation-view {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 2rem;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 4px solid #f3f4f6;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem;
}

.retry-btn {
  margin-top: 1rem;
  padding: 0.5rem 1.5rem;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.retry-btn:hover {
  background: #2563eb;
}

.filters-card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  margin-bottom: 2rem;
}

.filters-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.clear-filters-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: #f3f4f6;
  border: none;
  border-radius: 6px;
  color: #6b7280;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
}

.clear-filters-btn:hover {
  background: #e5e7eb;
  color: #374151;
}

.filters-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.filter-group {
  display: flex;
  flex-direction: column;
}

.filter-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
  margin-bottom: 0.5rem;
}

.filter-input {
  padding: 0.5rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.875rem;
}

.filter-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.summary-card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  gap: 1rem;
}

.summary-card__icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  flex-shrink: 0;
}

.summary-card__content {
  flex: 1;
}

.summary-card__label {
  color: #6b7280;
  font-size: 0.875rem;
  margin-bottom: 0.25rem;
}

.summary-card__value {
  color: #111827;
  font-size: 1.75rem;
  font-weight: 700;
  line-height: 1;
}

.charts-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.chart-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.chart-header {
  padding: 1.5rem;
  border-bottom: 1px solid #e5e7eb;
}

.chart-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #111827;
}

.chart-content {
  padding: 1.5rem;
  height: 400px;
}

.table-section {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.table-header {
  padding: 1.5rem;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.table-container {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th {
  text-align: left;
  padding: 1rem 1.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: #6b7280;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}

.data-table td {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #e5e7eb;
  font-size: 0.875rem;
}

.empty-state {
  padding: 4rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

@media (max-width: 768px) {
  .accommodation-view {
    padding: 1rem;
  }

  .summary-cards {
    grid-template-columns: 1fr;
  }

  .charts-section {
    grid-template-columns: 1fr;
  }

  .filters-grid {
    grid-template-columns: 1fr;
  }
}
</style>
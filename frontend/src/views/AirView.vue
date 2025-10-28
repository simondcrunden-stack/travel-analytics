<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import bookingService from '@/services/bookingService'
import { Chart, registerables } from 'chart.js'

// Register Chart.js components
Chart.register(...registerables)

// State
const loading = ref(true)
const error = ref(null)
const bookings = ref([])

// Chart refs
const airlineChartRef = ref(null)
const classChartRef = ref(null)
const routeChartRef = ref(null)
let airlineChart = null
let classChart = null
let routeChart = null

// Filters
const filters = ref({
  startDate: '',
  endDate: '',
  airline: '',
  travelClass: '',
  destination: '',
})

// Computed
const airBookings = computed(() => {
  return bookings.value.filter(b => {
    // A booking has air if it has air_bookings array with items
    if (!b.air_bookings || b.air_bookings.length === 0) return false
    
    // Apply filters
    if (filters.value.startDate && b.travel_date < filters.value.startDate) return false
    if (filters.value.endDate && b.travel_date > filters.value.endDate) return false
    
    // Filter on any of the air_bookings
    if (filters.value.airline) {
      const hasAirline = b.air_bookings.some(air => 
        air.primary_airline_name?.toLowerCase().includes(filters.value.airline.toLowerCase())
      )
      if (!hasAirline) return false
    }
    
    if (filters.value.travelClass) {
      const hasClass = b.air_bookings.some(air => 
        air.travel_class === filters.value.travelClass
      )
      if (!hasClass) return false
    }
    
    if (filters.value.destination) {
      const hasDestination = b.air_bookings.some(air =>
        air.destination_airport_iata_code?.includes(filters.value.destination.toUpperCase())
      )
      if (!hasDestination) return false
    }
    
    return true
  })
})

const summaryStats = computed(() => {
  const total = airBookings.value.length
  const totalSpend = airBookings.value.reduce((sum, b) => sum + parseFloat(b.total_amount || 0), 0)
  const avgSpend = total > 0 ? totalSpend / total : 0
  
  // Sum carbon from ALL air_bookings in each booking
  const totalCarbon = airBookings.value.reduce((sum, b) => {
    const bookingCarbon = (b.air_bookings || []).reduce((airSum, air) => {
      const segmentCarbon = (air.segments || []).reduce((segSum, seg) => 
        segSum + (parseFloat(seg.carbon_emissions_kg) || 0), 0)
      return airSum + segmentCarbon
    }, 0)
    return sum + bookingCarbon
  }, 0)

  return {
    total_bookings: total,
    total_spend: totalSpend,
    avg_spend: avgSpend,
    total_carbon_kg: totalCarbon,
  }
})

// Get unique airlines from all air_bookings
const availableAirlines = computed(() => {
  const airlines = new Set()
  bookings.value.forEach(b => {
    if (b.air_bookings) {
      b.air_bookings.forEach(air => {
        if (air.primary_airline_name) {
          airlines.add(air.primary_airline_name)
        }
      })
    }
  })
  return Array.from(airlines).sort()
})

// Get unique destinations from all air_bookings
const availableDestinations = computed(() => {
  const destinations = new Set()
  bookings.value.forEach(b => {
    if (b.air_bookings) {
      b.air_bookings.forEach(air => {
        if (air.destination_airport_iata_code) {
          destinations.add(air.destination_airport_iata_code)
        }
      })
    }
  })
  return Array.from(destinations).sort()
})

// Methods
const loadData = async () => {
  try {
    loading.value = true
    error.value = null

    const params = {}
    
    if (filters.value.startDate) {
      params.travel_date_after = filters.value.startDate
    }
    if (filters.value.endDate) {
      params.travel_date_before = filters.value.endDate
    }

    const response = await bookingService.getBookings(params)
    bookings.value = response.results || response

  } catch (err) {
    console.error('Error loading booking data:', err)
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

const clearFilters = () => {
  filters.value = {
    startDate: '',
    endDate: '',
    airline: '',
    travelClass: '',
    destination: '',
  }
  loadData()
}

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
  <div class="air-travel-view">
    <!-- Header -->
    <div class="page-header">
      <h1 class="text-3xl font-bold text-gray-800">Air Travel Analytics</h1>
      <p class="text-gray-600 mt-2">Analyze flight bookings, airline spending, and carbon emissions</p>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Loading air travel data...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-state">
      <span class="mdi mdi-alert-circle text-red-500 text-4xl"></span>
      <p class="text-red-600 mt-2">{{ error }}</p>
      <button @click="loadData" class="retry-btn">Retry</button>
    </div>

    <!-- Content -->
    <div v-else>
      <!-- Filters -->
      <div class="filters-card">
        <div class="filters-header">
          <h3 class="text-lg font-semibold text-gray-700">Filters</h3>
          <button @click="clearFilters" class="clear-filters-btn">
            <span class="mdi mdi-filter-off"></span>
            Clear All
          </button>
        </div>

        <div class="filters-grid">
          <div class="filter-group">
            <label class="filter-label">Start Date</label>
            <input v-model="filters.startDate" @change="loadData" type="date" class="filter-input" />
          </div>

          <div class="filter-group">
            <label class="filter-label">End Date</label>
            <input v-model="filters.endDate" @change="loadData" type="date" class="filter-input" />
          </div>

          <div class="filter-group">
            <label class="filter-label">Airline</label>
            <select v-model="filters.airline" class="filter-input">
              <option value="">All Airlines</option>
              <option v-for="airline in availableAirlines" :key="airline" :value="airline">
                {{ airline }}
              </option>
            </select>
          </div>

          <div class="filter-group">
            <label class="filter-label">Travel Class</label>
            <select v-model="filters.travelClass" class="filter-input">
              <option value="">All Classes</option>
              <option value="ECONOMY">Economy</option>
              <option value="PREMIUM_ECONOMY">Premium Economy</option>
              <option value="BUSINESS">Business</option>
              <option value="FIRST">First Class</option>
            </select>
          </div>

          <div class="filter-group">
            <label class="filter-label">Destination</label>
            <select v-model="filters.destination" class="filter-input">
              <option value="">All Destinations</option>
              <option v-for="dest in availableDestinations" :key="dest" :value="dest">
                {{ dest }}
              </option>
            </select>
          </div>
        </div>
      </div>

      <!-- Summary Cards -->
      <div class="summary-cards">
        <div class="summary-card">
          <div class="summary-card__icon bg-blue-100">
            <span class="mdi mdi-airplane text-blue-600"></span>
          </div>
          <div class="summary-card__content">
            <p class="summary-card__label">Total Flights</p>
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
            <span class="mdi mdi-chart-line text-purple-600"></span>
          </div>
          <div class="summary-card__content">
            <p class="summary-card__label">Average Spend</p>
            <p class="summary-card__value">{{ formatCurrency(summaryStats.avg_spend) }}</p>
          </div>
        </div>

        <div class="summary-card">
          <div class="summary-card__icon bg-orange-100">
            <span class="mdi mdi-leaf text-orange-600"></span>
          </div>
          <div class="summary-card__content">
            <p class="summary-card__label">Carbon Emissions</p>
            <p class="summary-card__value">{{ summaryStats.total_carbon_kg.toFixed(0) }} kg</p>
            <p class="summary-card__subtitle">CO₂ equivalent</p>
          </div>
        </div>
      </div>

      <!-- Charts -->
      <div class="charts-section">
        <div class="chart-container">
          <div class="chart-header">
            <h3 class="chart-title">Spend by Airline</h3>
          </div>
          <div class="chart-content">
            <canvas ref="airlineChartRef"></canvas>
          </div>
        </div>

        <div class="chart-container">
          <div class="chart-header">
            <h3 class="chart-title">Cabin Class Distribution</h3>
          </div>
          <div class="chart-content">
            <canvas ref="classChartRef"></canvas>
          </div>
        </div>

        <div class="chart-container full-width">
          <div class="chart-header">
            <h3 class="chart-title">Top Routes by Spend</h3>
          </div>
          <div class="chart-content">
            <canvas ref="routeChartRef"></canvas>
          </div>
        </div>
      </div>

      <!-- Bookings Table -->
      <div class="table-section">
        <div class="table-header">
          <h3 class="text-xl font-semibold text-gray-800">Flight Bookings</h3>
          <span class="text-sm text-gray-500">{{ airBookings.length }} bookings</span>
        </div>

        <div class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>Reference</th>
                <th>Traveller</th>
                <th>Route</th>
                <th>Airline</th>
                <th>Class</th>
                <th>Travel Date</th>
                <th>Amount</th>
                <th>Carbon (kg)</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="booking in airBookings" :key="booking.id">
                <td class="font-mono text-sm">{{ booking.agent_booking_reference }}</td>
                <td>{{ booking.traveller_name }}</td>
                <td>{{ getRoute(booking) }}</td>
                <td>{{ getAirline(booking) }}</td>
                <td>{{ getTravelClass(booking) }}</td>
                <td>{{ formatDate(booking.travel_date) }}</td>
                <td class="font-semibold">{{ formatCurrency(booking.total_amount) }}</td>
                <td class="text-right">{{ getTotalCarbon(booking) }}</td>
              </tr>
            </tbody>
          </table>

          <div v-if="airBookings.length === 0" class="empty-state">
            <span class="mdi mdi-airplane-off text-gray-300 text-6xl"></span>
            <p class="text-gray-500 mt-4">No flight bookings found</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.air-travel-view {
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

.summary-card__subtitle {
  color: #9ca3af;
  font-size: 0.75rem;
  margin-top: 0.25rem;
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

.chart-container.full-width {
  grid-column: 1 / -1;
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
  .air-travel-view {
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
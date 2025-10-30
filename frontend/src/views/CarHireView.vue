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
const locationChartRef = ref(null)
const rentalCompanyChartRef = ref(null)
let locationChart = null
let rentalCompanyChart = null

// Filters
const filters = ref({
  startDate: '',
  endDate: '',
  city: '',
  rentalCompany: '',
  vehicleType: '',
})

// Computed
const carHireBookings = computed(() => {
  return bookings.value.filter(b => {
    // NEW: A booking has car hire if it has car_hire_bookings array with items
    if (!b.car_hire_bookings || b.car_hire_bookings.length === 0) return false
    
    // Apply filters
    if (filters.value.startDate && b.travel_date < filters.value.startDate) return false
    if (filters.value.endDate && b.travel_date > filters.value.endDate) return false
    
    // NEW: Filter on any of the car_hire_bookings
    if (filters.value.city) {
      const hasCity = b.car_hire_bookings.some(car => 
        car.pickup_city?.toLowerCase().includes(filters.value.city.toLowerCase())
      )
      if (!hasCity) return false
    }
    
    if (filters.value.rentalCompany) {
      const hasCompany = b.car_hire_bookings.some(car => 
        car.rental_company?.toLowerCase().includes(filters.value.rentalCompany.toLowerCase())
      )
      if (!hasCompany) return false
    }
    
    if (filters.value.vehicleType) {
      const hasType = b.car_hire_bookings.some(car => 
        car.vehicle_type?.toLowerCase().includes(filters.value.vehicleType.toLowerCase())
      )
      if (!hasType) return false
    }
    
    return true
  })
})

const summaryStats = computed(() => {
  const total = carHireBookings.value.length
  const totalSpend = carHireBookings.value.reduce((sum, b) => sum + parseFloat(b.total_amount || 0), 0)
  const avgSpend = total > 0 ? totalSpend / total : 0
  
  // NEW: Sum rental days from ALL car_hire_bookings in each booking
  const totalDays = carHireBookings.value.reduce((sum, b) => {
    const bookingDays = b.car_hire_bookings.reduce((daySum, car) => 
      daySum + (car.number_of_days || 0), 0)
    return sum + bookingDays
  }, 0)
  
  const avgDailyRate = totalDays > 0 ? totalSpend / totalDays : 0

  return {
    total_bookings: total,
    total_spend: totalSpend,
    avg_spend: avgSpend,
    total_days: totalDays,
    avg_daily_rate: avgDailyRate,
  }
})

// NEW: Get unique cities from all car_hire_bookings
const availableCities = computed(() => {
  const cities = new Set()
  carHireBookings.value.forEach(b => {
    b.car_hire_bookings.forEach(car => {
      if (car.pickup_city) {
        cities.add(car.pickup_city)
      }
    })
  })
  return Array.from(cities).sort()
})

// NEW: Get unique rental companies from all car_hire_bookings
const availableRentalCompanies = computed(() => {
  const companies = new Set()
  carHireBookings.value.forEach(b => {
    b.car_hire_bookings.forEach(car => {
      if (car.rental_company) {
        companies.add(car.rental_company)
      }
    })
  })
  return Array.from(companies).sort()
})

// NEW: Get unique vehicle types from all car_hire_bookings
const availableVehicleTypes = computed(() => {
  const types = new Set()
  carHireBookings.value.forEach(b => {
    b.car_hire_bookings.forEach(car => {
      if (car.vehicle_type) {
        types.add(car.vehicle_type)
      }
    })
  })
  return Array.from(types).sort()
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
  if (locationChart) locationChart.destroy()
  if (rentalCompanyChart) rentalCompanyChart.destroy()

  // Location Chart Data
  const locationChartData = {}
  carHireBookings.value.forEach(booking => {
    booking.car_hire_bookings.forEach(car => {
      const city = car.pickup_city || 'Unknown'
      if (!locationChartData[city]) {
        locationChartData[city] = 0
      }
      const amount = parseFloat(booking.total_amount || 0) / booking.car_hire_bookings.length
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

  // Rental Company Chart Data
  const rentalCompanyChartData = {}
  carHireBookings.value.forEach(booking => {
    booking.car_hire_bookings.forEach(car => {
      const company = car.rental_company || 'Unknown'
      if (!rentalCompanyChartData[company]) {
        rentalCompanyChartData[company] = 0
      }
      const amount = parseFloat(booking.total_amount || 0) / booking.car_hire_bookings.length
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

const clearFilters = () => {
  filters.value = {
    startDate: '',
    endDate: '',
    city: '',
    rentalCompany: '',
    vehicleType: '',
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

// NEW: Helper functions updated for array handling
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
  <div class="car-hire-view">
    <!-- Header -->
    <div class="page-header">
      <h1 class="text-3xl font-bold text-gray-800">Car Hire Analytics</h1>
      <p class="text-gray-600 mt-2">Analyze car rental bookings, spending patterns, and vehicle preferences</p>
    </div>

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
          <input v-model="filters.startDate" type="date" class="filter-input" />
        </div>

        <div class="filter-group">
          <label class="filter-label">End Date</label>
          <input v-model="filters.endDate" type="date" class="filter-input" />
        </div>

        <div class="filter-group">
          <label class="filter-label">City</label>
          <select v-model="filters.city" class="filter-input">
            <option value="">All Cities</option>
            <option v-for="city in availableCities" :key="city" :value="city">
              {{ city }}
            </option>
          </select>
        </div>

        <div class="filter-group">
          <label class="filter-label">Rental Company</label>
          <select v-model="filters.rentalCompany" class="filter-input">
            <option value="">All Companies</option>
            <option v-for="company in availableRentalCompanies" :key="company" :value="company">
              {{ company }}
            </option>
          </select>
        </div>

        <div class="filter-group">
          <label class="filter-label">Vehicle Type</label>
          <select v-model="filters.vehicleType" class="filter-input">
            <option value="">All Types</option>
            <option v-for="type in availableVehicleTypes" :key="type" :value="type">
              {{ type }}
            </option>
          </select>
        </div>

        <div class="filter-group" style="display: flex; align-items: flex-end;">
          <button @click="loadData" class="filter-input" style="background: #3b82f6; color: white; border: none; cursor: pointer; font-weight: 600;">
            Apply Filters
          </button>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-state">
      <div class="loading-spinner"></div>
      <p>Loading car hire data...</p>
    </div>

    <!-- Error State -->
    <div v-if="error" class="error-state">
      <span class="mdi mdi-alert-circle"></span>
      <p>{{ error }}</p>
    </div>

    <!-- Content -->
    <div v-if="!loading && !error">
      <!-- Summary Cards -->
      <div class="summary-cards">
        <div class="summary-card">
          <div class="summary-card__icon bg-blue-100">
            <span class="mdi mdi-car text-blue-600"></span>
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
            <p class="summary-card__label">Total Rental Days</p>
            <p class="summary-card__value">{{ summaryStats.total_days }}</p>
          </div>
        </div>

        <div class="summary-card">
          <div class="summary-card__icon bg-orange-100">
            <span class="mdi mdi-chart-line text-orange-600"></span>
          </div>
          <div class="summary-card__content">
            <p class="summary-card__label">Avg Daily Rate</p>
            <p class="summary-card__value">{{ formatCurrency(summaryStats.avg_daily_rate) }}</p>
          </div>
        </div>
      </div>

      <!-- Charts -->
      <div class="charts-section">
        <div class="chart-container">
          <div class="chart-header">
            <h3 class="chart-title">Spend by Location</h3>
          </div>
          <div class="chart-content">
            <canvas ref="locationChartRef"></canvas>
          </div>
        </div>

        <div class="chart-container">
          <div class="chart-header">
            <h3 class="chart-title">Spend by Rental Company</h3>
          </div>
          <div class="chart-content">
            <canvas ref="rentalCompanyChartRef"></canvas>
          </div>
        </div>
      </div>

      <!-- Bookings Table -->
      <div class="table-section">
        <div class="table-header">
          <h3 class="text-xl font-semibold text-gray-800">Car Hire Bookings</h3>
          <span class="text-sm text-gray-500">{{ carHireBookings.length }} bookings</span>
        </div>

        <div class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>Reference</th>
                <th>Traveller</th>
                <th>Rental Company</th>
                <th>City</th>
                <th>Vehicle</th>
                <th>Pickup</th>
                <th>Days</th>
                <th>Amount</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="booking in carHireBookings" :key="booking.id">
                <td class="font-mono text-sm">{{ booking.agent_booking_reference }}</td>
                <td>{{ booking.traveller_name }}</td>
                <td>{{ getRentalInfo(booking) }}</td>
                <td>{{ getCityInfo(booking) }}</td>
                <td>{{ getVehicleInfo(booking) }}</td>
                <td>{{ getPickupDate(booking) }}</td>
                <td class="text-center">{{ getTotalDays(booking) }}</td>
                <td class="font-semibold">{{ formatCurrency(booking.total_amount) }}</td>
              </tr>
            </tbody>
          </table>

          <div v-if="carHireBookings.length === 0" class="empty-state">
            <span class="mdi mdi-car-off text-gray-300 text-6xl"></span>
            <p class="text-gray-500 mt-4">No car hire bookings found</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Same styles as other views */
.car-hire-view {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 2rem;
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

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem;
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-state {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem 1.5rem;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  color: #dc2626;
  margin-bottom: 2rem;
}

.error-state .mdi {
  font-size: 1.5rem;
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
  .car-hire-view {
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
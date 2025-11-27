<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import bookingService from '@/services/bookingService'
import preferredCarHireService from '@/services/preferredCarHireService'
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
const complianceData = ref(null)
const performanceData = ref(null)
const expiringCarHireCount = ref(0)
const complianceViewMode = ref('cost_center') // 'cost_center' or 'traveller'

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

    // Load bookings first
    const bookingsData = await bookingService.getBookings(filters)

    // Load compliance and performance data only if organization is specified
    let complianceResponse = null
    let performanceResponse = null

    if (filters.organization) {
      const carHireParams = {
        organization: filters.organization,
        ...filters
      }

      try {
        const [complianceRes, performanceRes, expiringRes] = await Promise.all([
          preferredCarHireService.getComplianceReport(carHireParams),
          preferredCarHireService.getPerformanceDashboard(carHireParams),
          preferredCarHireService.getExpiringSoon(30, carHireParams).catch(() => [])
        ])
        complianceResponse = complianceRes
        performanceResponse = performanceRes
        expiringCarHireCount.value = expiringRes.length
        console.log('✅ [CarHireView] Loaded compliance, performance, and expiring data')
      } catch (err) {
        console.warn('⚠️ [CarHireView] Could not load compliance/performance data:', err)
      }
    } else {
      console.log('ℹ️ [CarHireView] No organization selected, skipping compliance and performance data')
      expiringCarHireCount.value = 0
    }

    bookings.value = bookingsData.results || []
    complianceData.value = complianceResponse
    performanceData.value = performanceResponse

    // Use backend summary statistics
    if (bookingsData.summary) {
      summary.value = bookingsData.summary
      console.log('📊 [CarHireView] Backend summary:', summary.value)
    }

    console.log('✅ [CarHireView] Loaded', bookings.value.length, 'bookings,', carHireBookings.value.length, 'with car hires')
    if (complianceResponse) {
      console.log('✅ [CarHireView] Loaded compliance data:', complianceResponse)
    }

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
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Car Hire Records</h1>
        <p class="mt-1 text-sm text-gray-500">Analyze car rental bookings, spending patterns, and vehicle preferences</p>
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
      supplier-label="Rental Company"
      supplier-placeholder="Hertz, Avis, Budget..."
      supplier-type="car_rental"
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

    <!-- Compliance Section -->
    <div v-if="!loading && !error && complianceData" class="bg-white rounded-xl shadow-sm overflow-hidden">
      <!-- Section Header with Toggle -->
      <div class="border-b border-gray-200 px-6 py-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div>
              <h3 class="text-lg font-semibold text-gray-900">Preferred Supplier Compliance</h3>
              <p class="text-sm text-gray-600 mt-1">
                {{ complianceViewMode === 'cost_center' ? 'Compliance by Cost Center' : 'Compliance by Traveller' }}
              </p>
            </div>
            <!-- Expiry Alert Badge -->
            <div v-if="expiringCarHireCount > 0" class="flex items-center gap-2 px-3 py-1 bg-red-100 border border-red-300 rounded-full">
              <span class="mdi mdi-alert-circle text-red-600" style="font-size: 16px;"></span>
              <span class="text-xs font-semibold text-red-700">{{ expiringCarHireCount }} expiring soon</span>
            </div>
          </div>
          <div class="flex gap-2">
            <button
              @click="complianceViewMode = 'cost_center'"
              :class="[
                'px-4 py-2 text-sm font-medium rounded-lg transition-colors',
                complianceViewMode === 'cost_center'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              ]"
            >
              Cost Center
            </button>
            <button
              @click="complianceViewMode = 'traveller'"
              :class="[
                'px-4 py-2 text-sm font-medium rounded-lg transition-colors',
                complianceViewMode === 'traveller'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              ]"
            >
              Traveller
            </button>
          </div>
        </div>
      </div>

      <!-- Compliance Summary -->
      <div class="border-b border-gray-200 px-6 py-4 bg-gray-50">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <p class="text-xs text-gray-600">Compliance Rate</p>
            <p class="text-2xl font-bold text-gray-900">{{ complianceData.summary.compliance_rate }}%</p>
          </div>
          <div>
            <p class="text-xs text-gray-600">Total Spend</p>
            <p class="text-2xl font-bold text-gray-900">{{ formatCurrency(complianceData.summary.total_spend) }}</p>
          </div>
          <div>
            <p class="text-xs text-gray-600">Preferred Spend</p>
            <p class="text-2xl font-bold text-green-600">{{ formatCurrency(complianceData.summary.preferred_spend) }}</p>
          </div>
          <div>
            <p class="text-xs text-gray-600">Total Rental Days</p>
            <p class="text-2xl font-bold text-gray-900">{{ complianceData.summary.total_rental_days }}</p>
          </div>
        </div>
      </div>

      <!-- Compliance Table - By Cost Center -->
      <div v-if="complianceViewMode === 'cost_center'" class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Cost Center</th>
              <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Total Spend</th>
              <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Preferred Spend</th>
              <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Rental Days</th>
              <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Compliance Rate</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="item in complianceData.by_cost_center" :key="item.cost_center" class="hover:bg-gray-50">
              <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{{ item.cost_center }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">{{ formatCurrency(item.total_spend) }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-green-600 text-right">{{ formatCurrency(item.preferred_spend) }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">{{ item.total_rental_days }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-right">
                <span :class="[
                  'px-2 py-1 rounded-full text-xs font-medium',
                  item.compliance_rate >= 80 ? 'bg-green-100 text-green-800' :
                  item.compliance_rate >= 60 ? 'bg-yellow-100 text-yellow-800' :
                  'bg-red-100 text-red-800'
                ]">
                  {{ item.compliance_rate }}%
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Compliance Table - By Traveller -->
      <div v-if="complianceViewMode === 'traveller'" class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Traveller</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Cost Center</th>
              <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Total Spend</th>
              <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Preferred Spend</th>
              <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Rental Days</th>
              <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Compliance Rate</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="item in complianceData.by_traveller" :key="item.traveller_id" class="hover:bg-gray-50">
              <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{{ item.traveller_name }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{{ item.cost_center }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">{{ formatCurrency(item.total_spend) }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-green-600 text-right">{{ formatCurrency(item.preferred_spend) }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">{{ item.total_rental_days }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-right">
                <span :class="[
                  'px-2 py-1 rounded-full text-xs font-medium',
                  item.compliance_rate >= 80 ? 'bg-green-100 text-green-800' :
                  item.compliance_rate >= 60 ? 'bg-yellow-100 text-yellow-800' :
                  'bg-red-100 text-red-800'
                ]">
                  {{ item.compliance_rate }}%
                </span>
              </td>
            </tr>
          </tbody>
        </table>
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

    <!-- Performance Dashboard Section -->
    <div v-if="!loading && !error && performanceData && performanceData.contracts.length > 0" class="space-y-6">
      <!-- Section Header -->
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-xl font-bold text-gray-900">Contract Performance Dashboard</h2>
          <p class="text-sm text-gray-500 mt-1">Actual vs target metrics for preferred car hire contracts</p>
        </div>
      </div>

      <!-- Performance Content -->
      <div class="bg-white rounded-xl shadow-sm overflow-hidden">
        <!-- Performance Summary Cards -->
        <div class="border-b border-gray-200 px-6 py-4 bg-gray-50">
          <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <p class="text-xs text-gray-600">Target Rental Days</p>
              <p class="text-2xl font-bold text-gray-900">{{ performanceData.totals.target_rental_days?.toLocaleString() || 'N/A' }}</p>
            </div>
            <div>
              <p class="text-xs text-gray-600">Actual Rental Days</p>
              <p class="text-2xl font-bold text-gray-900">{{ performanceData.totals.actual_rental_days?.toLocaleString() || 0 }}</p>
            </div>
            <div>
              <p class="text-xs text-gray-600">Target Revenue</p>
              <p class="text-2xl font-bold text-gray-900">{{ formatCurrency(performanceData.totals.target_revenue || 0) }}</p>
            </div>
            <div>
              <p class="text-xs text-gray-600">Actual Revenue</p>
              <p class="text-2xl font-bold text-green-600">{{ formatCurrency(performanceData.totals.actual_revenue || 0) }}</p>
            </div>
          </div>
        </div>

        <!-- Performance Table -->
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Supplier</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Market</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Car Category</th>
                <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Target Rental Days</th>
                <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actual Rental Days</th>
                <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Days Variance</th>
                <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Target Revenue</th>
                <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actual Revenue</th>
                <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Revenue Variance</th>
                <th class="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="contract in performanceData.contracts" :key="contract.supplier + contract.market" class="hover:bg-gray-50">
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{{ contract.supplier }}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{{ contract.market_display }}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{{ contract.car_category_display }}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">
                  {{ contract.target_rental_days !== null ? contract.target_rental_days.toLocaleString() : '-' }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">
                  {{ contract.actual_rental_days.toLocaleString() }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-right">
                  <span v-if="contract.rental_days_variance !== null" :class="contract.rental_days_variance >= 0 ? 'text-green-600' : 'text-red-600'">
                    {{ contract.rental_days_variance > 0 ? '+' : '' }}{{ contract.rental_days_variance.toLocaleString() }}
                  </span>
                  <span v-else class="text-gray-400">-</span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">
                  {{ contract.target_revenue !== null ? formatCurrency(contract.target_revenue) : '-' }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">
                  {{ formatCurrency(contract.actual_revenue) }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-right">
                  <span v-if="contract.revenue_variance !== null" :class="contract.revenue_variance >= 0 ? 'text-green-600' : 'text-red-600'">
                    {{ contract.revenue_variance >= 0 ? '+' : '' }}{{ formatCurrency(contract.revenue_variance) }}
                  </span>
                  <span v-else class="text-gray-400">-</span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-center">
                  <span :class="[
                    'px-2 py-1 rounded-full text-xs font-medium',
                    contract.performance_status === 'ABOVE_TARGET' ? 'bg-green-100 text-green-800' :
                    contract.performance_status === 'ON_TARGET' ? 'bg-blue-100 text-blue-800' :
                    'bg-red-100 text-red-800'
                  ]">
                    {{ contract.performance_status === 'ABOVE_TARGET' ? 'Above Target' :
                       contract.performance_status === 'ON_TARGET' ? 'On Target' :
                       'Below Target' }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Bookings Table -->
    <div v-if="!loading && !error" class="bg-white rounded-xl shadow-sm overflow-hidden">
      <!-- Table Header -->
      <div class="p-6 border-b border-gray-200">
        <h2 class="text-lg font-semibold text-gray-900">Car Hire Records</h2>
        <p class="text-sm text-gray-600 mt-1">{{ carHireBookings.length }} bookings found</p>
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
                Rental Company
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                City
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Vehicle
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Pickup
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Days
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Amount
              </th>
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
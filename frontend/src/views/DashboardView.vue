<template>
  <div class="space-y-6">
    <!-- Header -->
    <div>
      <h1 class="text-2xl font-bold text-gray-900">Summary Dashboard</h1>
      <p class="mt-1 text-sm text-gray-500">
        Overview of your travel data
      </p>
    </div>

    <!-- Universal Filters -->
    <UniversalFilters
      :show-traveller="true"
      :show-date-range="true"
      :show-destinations="true"
      :show-organization="true"
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
      <button 
        @click="loadData" 
        class="mt-2 text-sm text-red-600 hover:text-red-800 underline"
      >
        Try Again
      </button>
    </div>

    <!-- Dashboard Content -->
    <div v-else>
      <!-- Stats Cards -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <!-- Total Spend -->
        <div class="bg-white rounded-lg shadow p-6">
          <div class="flex items-center justify-between">
            <div class="flex-1">
              <p class="text-sm font-medium text-gray-600">Total Spend</p>
              <p class="text-2xl font-bold text-gray-900 mt-2">
                {{ formatCurrency(summary.total_spend) }}
              </p>
            </div>
            <div class="bg-blue-100 p-3 rounded-full">
              <svg class="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
          <div class="mt-3 flex items-center justify-between text-xs">
            <div>
              <span class="text-gray-500">Domestic:</span>
              <span class="font-semibold text-gray-700 ml-1">{{ formatCurrency(summary.total_spend_domestic) }}</span>
            </div>
            <div>
              <span class="text-gray-500">International:</span>
              <span class="font-semibold text-gray-700 ml-1">{{ formatCurrency(summary.total_spend_international) }}</span>
            </div>
          </div>
          <p class="text-xs text-gray-500 mt-2 pt-2 border-t border-gray-100">
            {{ summary.total_bookings }} bookings
          </p>
        </div>

        <!-- Air Travel -->
        <div class="bg-white rounded-lg shadow p-6">
          <div class="flex items-center justify-between">
            <div class="flex-1">
              <p class="text-sm font-medium text-gray-600">Air Travel</p>
              <p class="text-2xl font-bold text-gray-900 mt-2">
                {{ formatCurrency(summary.air_spend) }}
              </p>
            </div>
            <div class="bg-sky-100 p-3 rounded-full">
              <svg class="w-6 h-6 text-sky-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            </div>
          </div>
          <div class="mt-3 flex items-center justify-between text-xs">
            <div>
              <span class="text-gray-500">Domestic:</span>
              <span class="font-semibold text-gray-700 ml-1">{{ formatCurrency(summary.air_spend_domestic) }}</span>
            </div>
            <div>
              <span class="text-gray-500">International:</span>
              <span class="font-semibold text-gray-700 ml-1">{{ formatCurrency(summary.air_spend_international) }}</span>
            </div>
          </div>
          <p class="text-xs text-gray-500 mt-2 pt-2 border-t border-gray-100">
            {{ summary.air_bookings }} bookings
          </p>
        </div>

        <!-- Accommodation -->
        <div class="bg-white rounded-lg shadow p-6">
          <div class="flex items-center justify-between">
            <div class="flex-1">
              <p class="text-sm font-medium text-gray-600">Accommodation</p>
              <p class="text-2xl font-bold text-gray-900 mt-2">
                {{ formatCurrency(summary.accommodation_spend) }}
              </p>
            </div>
            <div class="bg-amber-100 p-3 rounded-full">
              <svg class="w-6 h-6 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
            </div>
          </div>
          <div class="mt-3 flex items-center justify-between text-xs">
            <div>
              <span class="text-gray-500">Domestic:</span>
              <span class="font-semibold text-gray-700 ml-1">{{ formatCurrency(summary.accommodation_spend_domestic) }}</span>
            </div>
            <div>
              <span class="text-gray-500">International:</span>
              <span class="font-semibold text-gray-700 ml-1">{{ formatCurrency(summary.accommodation_spend_international) }}</span>
            </div>
          </div>
          <p class="text-xs text-gray-500 mt-2 pt-2 border-t border-gray-100">
            {{ summary.accommodation_bookings }} bookings
          </p>
        </div>

        <!-- Car Hire -->
        <div class="bg-white rounded-lg shadow p-6">
          <div class="flex items-center justify-between">
            <div class="flex-1">
              <p class="text-sm font-medium text-gray-600">Car Hire</p>
              <p class="text-2xl font-bold text-gray-900 mt-2">
                {{ formatCurrency(summary.car_hire_spend) }}
              </p>
            </div>
            <div class="bg-emerald-100 p-3 rounded-full">
              <svg class="w-6 h-6 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
              </svg>
            </div>
          </div>
          <div class="mt-3 flex items-center justify-between text-xs">
            <div>
              <span class="text-gray-500">Domestic:</span>
              <span class="font-semibold text-gray-700 ml-1">{{ formatCurrency(summary.car_hire_spend_domestic) }}</span>
            </div>
            <div>
              <span class="text-gray-500">International:</span>
              <span class="font-semibold text-gray-700 ml-1">{{ formatCurrency(summary.car_hire_spend_international) }}</span>
            </div>
          </div>
          <p class="text-xs text-gray-500 mt-2 pt-2 border-t border-gray-100">
            {{ summary.car_hire_bookings }} bookings
          </p>
        </div>
      </div>

      <!-- Compliance & Emissions Summary -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mt-6">
        <!-- Compliance Rate -->
        <div class="bg-white rounded-lg shadow p-6">
          <div class="flex items-center justify-between">
            <div class="flex-1">
              <p class="text-sm font-medium text-gray-600">Compliance Rate</p>
              <p class="text-3xl font-bold mt-2" :class="summary.compliance_rate >= 80 ? 'text-green-600' : summary.compliance_rate >= 60 ? 'text-amber-600' : 'text-red-600'">
                {{ summary.compliance_rate.toFixed(1) }}%
              </p>
            </div>
            <div :class="summary.compliance_rate >= 80 ? 'bg-green-100' : summary.compliance_rate >= 60 ? 'bg-amber-100' : 'bg-red-100'" class="p-3 rounded-full">
              <svg class="w-6 h-6" :class="summary.compliance_rate >= 80 ? 'text-green-600' : summary.compliance_rate >= 60 ? 'text-amber-600' : 'text-red-600'" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
          <div class="mt-3 pt-3 border-t border-gray-100">
            <div class="flex items-center justify-between text-xs">
              <span class="text-gray-500">Total Violations:</span>
              <span class="font-semibold text-gray-700">{{ summary.violation_count }}</span>
            </div>
            <div class="flex items-center justify-between text-xs mt-1" v-if="summary.critical_violations > 0">
              <span class="text-red-600">Critical:</span>
              <span class="font-semibold text-red-700">{{ summary.critical_violations }}</span>
            </div>
          </div>
        </div>

        <!-- Carbon Emissions -->
        <div class="bg-white rounded-lg shadow p-6">
          <div class="flex items-center justify-between">
            <div class="flex-1">
              <p class="text-sm font-medium text-gray-600">Carbon Emissions</p>
              <p class="text-3xl font-bold text-gray-900 mt-2">
                {{ (summary.total_carbon_kg / 1000).toFixed(1) }}
              </p>
              <p class="text-xs text-gray-500 mt-1">tonnes CO₂</p>
            </div>
            <div class="bg-green-100 p-3 rounded-full">
              <svg class="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
          <div class="mt-3 pt-3 border-t border-gray-100">
            <div class="text-xs text-gray-500">
              {{ summary.air_bookings > 0 ? (summary.total_carbon_kg / summary.air_bookings).toFixed(0) : 0 }} kg per flight
            </div>
          </div>
        </div>

        <!-- Policy Compliance Status -->
        <div class="bg-white rounded-lg shadow p-6">
          <div class="flex items-center justify-between">
            <div class="flex-1">
              <p class="text-sm font-medium text-gray-600">Policy Status</p>
              <p class="text-lg font-bold mt-2" :class="summary.compliance_rate >= 90 ? 'text-green-600' : summary.compliance_rate >= 75 ? 'text-amber-600' : 'text-red-600'">
                {{ summary.compliance_rate >= 90 ? 'Excellent' : summary.compliance_rate >= 75 ? 'Good' : summary.compliance_rate >= 60 ? 'Fair' : 'Needs Attention' }}
              </p>
            </div>
            <div :class="summary.compliance_rate >= 90 ? 'bg-green-100' : summary.compliance_rate >= 75 ? 'bg-amber-100' : 'bg-red-100'" class="p-3 rounded-full">
              <svg class="w-6 h-6" :class="summary.compliance_rate >= 90 ? 'text-green-600' : summary.compliance_rate >= 75 ? 'text-amber-600' : 'text-red-600'" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
            </div>
          </div>
          <div class="mt-3 pt-3 border-t border-gray-100">
            <div class="text-xs">
              <span class="text-gray-500">Compliant Bookings:</span>
              <span class="font-semibold text-gray-700 ml-1">{{ summary.total_bookings - summary.violation_count }}/{{ summary.total_bookings }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Charts Row -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
        <!-- Spend by Category Chart -->
        <div class="bg-white rounded-lg shadow p-6">
          <h2 class="text-lg font-semibold text-gray-900 mb-4">
            Spend by Category
          </h2>
          <div class="h-64">
            <canvas ref="categoryChart"></canvas>
          </div>
        </div>

        <!-- Monthly Trend Chart -->
        <div class="bg-white rounded-lg shadow p-6">
          <h2 class="text-lg font-semibold text-gray-900 mb-4">
            Monthly Spend Trend
          </h2>
          <div class="h-64">
            <canvas ref="trendChart"></canvas>
          </div>
        </div>
      </div>

      <!-- Recent Bookings -->
      <div class="bg-white rounded-lg shadow mt-6">
        <div class="p-6 border-b border-gray-200">
          <h2 class="text-lg font-semibold text-gray-900">Recent Bookings</h2>
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
                  Type
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Amount
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="booking in recentBookings" :key="booking.id" class="hover:bg-gray-50">
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {{ booking.agent_booking_reference }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {{ booking.traveller_name }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span :class="getBookingTypeClass(booking.booking_type)">
                    {{ booking.booking_type }}
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {{ formatDate(booking.travel_date) }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {{ formatCurrency(booking.total_amount) }}
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
import { ref, onMounted, nextTick } from 'vue'
import { Chart } from 'chart.js/auto'
import bookingService from '@/services/bookingService'
import UniversalFilters from '@/components/common/UniversalFilters.vue'

// State
const loading = ref(true)
const error = ref(null)
const summary = ref({
  total_spend: 0,
  total_spend_domestic: 0,
  total_spend_international: 0,
  total_bookings: 0,
  air_spend: 0,
  air_spend_domestic: 0,
  air_spend_international: 0,
  air_bookings: 0,
  accommodation_spend: 0,
  accommodation_spend_domestic: 0,
  accommodation_spend_international: 0,
  accommodation_bookings: 0,
  car_hire_spend: 0,
  car_hire_spend_domestic: 0,
  car_hire_spend_international: 0,
  car_hire_bookings: 0,
  total_carbon_kg: 0,
  compliance_rate: 0,
  violation_count: 0,
  critical_violations: 0
})
const recentBookings = ref([])
const monthlyData = ref([])

// Filter state
const activeFilters = ref({})

// Chart refs
const categoryChart = ref(null)
const trendChart = ref(null)
let categoryChartInstance = null
let trendChartInstance = null

// Handle filter changes from UniversalFilters
const handleFiltersChanged = (newFilters) => {
  console.log('📊 Dashboard filters changed:', newFilters)
  activeFilters.value = newFilters
  loadData()
}

// Load data
const loadData = async () => {
  loading.value = true
  error.value = null

  try {
    console.log('🌐 [DashboardView] Loading dashboard data with filters:', activeFilters.value)

    // Call new dashboard summary endpoint for aggregated metrics
    const summaryData = await bookingService.getDashboardSummary(activeFilters.value)
    summary.value = summaryData

    console.log('✅ [DashboardView] Dashboard summary loaded:', summaryData)

    // Get recent bookings for the table
    const data = await bookingService.getBookings(activeFilters.value)
    const bookings = data.results || data

    // Get recent bookings (last 10)
    recentBookings.value = bookings
      .sort((a, b) => new Date(b.travel_date) - new Date(a.travel_date))
      .slice(0, 10)

    // Process monthly trend data
    processMonthlyData(bookings)

    console.log('Summary:', summary.value)
    console.log('Recent bookings:', recentBookings.value.length)
    console.log('Monthly data points:', monthlyData.value.length)

  } catch (err) {
    console.error('Error loading dashboard data:', err)
    error.value = 'Failed to load dashboard data. Please try again.'
  } finally {
    loading.value = false

    // Wait for v-else content to render AFTER loading becomes false
    await nextTick()
    await nextTick()

    console.log('Rendering charts...')
    renderCharts()
  }
}

const processMonthlyData = (bookings) => {
  // Group bookings by month
  const monthGroups = {}
  
  bookings.forEach(booking => {
    const date = new Date(booking.travel_date)
    const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
    
    if (!monthGroups[monthKey]) {
      monthGroups[monthKey] = {
        month: monthKey,
        total: 0,
        count: 0
      }
    }
    
    monthGroups[monthKey].total += parseFloat(booking.total_amount || 0)
    monthGroups[monthKey].count += 1
  })
  
  // Convert to sorted array
  monthlyData.value = Object.values(monthGroups).sort((a, b) => 
    a.month.localeCompare(b.month)
  )
}

const renderCharts = () => {
  console.log('Rendering charts...')
  
  // Category Chart
  if (categoryChartInstance) {
    categoryChartInstance.destroy()
  }
  
  if (categoryChart.value) {
    const ctx = categoryChart.value.getContext('2d')
    
    const categoryData = [
      summary.value.air_spend,
      summary.value.accommodation_spend,
      summary.value.car_hire_spend
    ]
    
    console.log('Category chart data:', categoryData)
    
    categoryChartInstance = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: ['Air Travel', 'Accommodation', 'Car Hire'],
        datasets: [{
          data: categoryData,
          backgroundColor: [
            '#0ea5e9', // sky-500
            '#f59e0b', // amber-500
            '#10b981'  // emerald-500
          ]
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom'
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                const label = context.label || ''
                const value = context.parsed || 0
                return `${label}: ${formatCurrency(value)}`
              }
            }
          }
        }
      }
    })
  }

  // Trend Chart
  if (trendChartInstance) {
    trendChartInstance.destroy()
  }
  
  if (trendChart.value && monthlyData.value.length > 0) {
    const ctx = trendChart.value.getContext('2d')
    
    console.log('Trend chart labels:', monthlyData.value.map(d => d.month))
    console.log('Trend chart data:', monthlyData.value.map(d => d.total))
    
    trendChartInstance = new Chart(ctx, {
      type: 'line',
      data: {
        labels: monthlyData.value.map(d => {
          const [year, month] = d.month.split('-')
          return new Date(year, month - 1).toLocaleDateString('en-AU', { 
            month: 'short', 
            year: 'numeric' 
          })
        }),
        datasets: [{
          label: 'Monthly Spend',
          data: monthlyData.value.map(d => d.total),
          borderColor: '#2563eb',
          backgroundColor: 'rgba(37, 99, 235, 0.1)',
          tension: 0.4,
          fill: true
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                return `Spend: ${formatCurrency(context.parsed.y)}`
              }
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
  } else {
    console.log('Skipping trend chart - no data available')
  }
}

const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-AU', {
    style: 'currency',
    currency: 'AUD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(amount || 0)
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('en-AU', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

const getBookingTypeClass = (type) => {
  const classes = {
    'AIR': 'px-2 py-1 text-xs rounded-full bg-sky-100 text-sky-800',
    'ACCOMMODATION': 'px-2 py-1 text-xs rounded-full bg-amber-100 text-amber-800',
    'CAR': 'px-2 py-1 text-xs rounded-full bg-emerald-100 text-emerald-800',
    'OTHER': 'px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-800'
  }
  return classes[type] || classes['OTHER']
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
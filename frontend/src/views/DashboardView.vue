<template>
  <div class="space-y-6">
    <!-- Header -->
    <div>
      <h1 class="text-2xl font-bold text-gray-900">Summary Dashboard</h1>
      <p class="mt-1 text-sm text-gray-500">
        Overview of your travel data
      </p>
    </div>

    <!-- Simple Date Range Filter (Temporary until we add UniversalFilters) -->
    <div class="bg-white rounded-2xl shadow-sm p-4">
      <div class="flex flex-wrap gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Start Date
          </label>
          <input
            v-model="filters.start_date"
            type="date"
            class="border border-gray-300 rounded-md px-3 py-2 text-sm"
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
            class="border border-gray-300 rounded-md px-3 py-2 text-sm"
            @change="loadData"
          />
        </div>
        <div class="flex items-end">
          <button
            @click="resetFilters"
            class="px-4 py-2 text-sm border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Reset
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

    <!-- Dashboard Content -->
    <div v-else>
      <!-- Stats Cards -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <!-- Total Spend -->
        <div class="bg-white rounded-lg shadow p-6">
          <div class="flex items-center justify-between">
            <div>
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
          <p class="text-xs text-gray-500 mt-2">
            {{ summary.total_bookings }} bookings
          </p>
        </div>

        <!-- Air Travel -->
        <div class="bg-white rounded-lg shadow p-6">
          <div class="flex items-center justify-between">
            <div>
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
          <p class="text-xs text-gray-500 mt-2">
            {{ summary.air_bookings }} flights
          </p>
        </div>

        <!-- Accommodation -->
        <div class="bg-white rounded-lg shadow p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-600">Accommodation</p>
              <p class="text-2xl font-bold text-gray-900 mt-2">
                {{ formatCurrency(summary.hotel_spend) }}
              </p>
            </div>
            <div class="bg-purple-100 p-3 rounded-full">
              <svg class="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
              </svg>
            </div>
          </div>
          <p class="text-xs text-gray-500 mt-2">
            {{ summary.hotel_bookings }} stays
          </p>
        </div>

        <!-- Car Hire -->
        <div class="bg-white rounded-lg shadow p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-600">Car Hire</p>
              <p class="text-2xl font-bold text-gray-900 mt-2">
                {{ formatCurrency(summary.car_spend) }}
              </p>
            </div>
            <div class="bg-green-100 p-3 rounded-full">
              <svg class="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
              </svg>
            </div>
          </div>
          <p class="text-xs text-gray-500 mt-2">
            {{ summary.car_bookings }} rentals
          </p>
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

// State
const loading = ref(true)
const error = ref(null)
const summary = ref({
  total_spend: 0,
  total_bookings: 0,
  air_spend: 0,
  air_bookings: 0,
  hotel_spend: 0,
  hotel_bookings: 0,
  car_spend: 0,
  car_bookings: 0
})
const recentBookings = ref([])
const monthlyData = ref([])

// Filter state
const filters = ref({
  start_date: '',
  end_date: ''
})

// Chart refs
const categoryChart = ref(null)
const trendChart = ref(null)
let categoryChartInstance = null
let trendChartInstance = null

// Load data
const loadData = async () => {
  loading.value = true
  error.value = null
  
  try {
    console.log('Loading dashboard data...')
    
    // Build query params from filters
    const params = {}
    if (filters.value.start_date) {
      params.travel_date__gte = filters.value.start_date
    }
    if (filters.value.end_date) {
      params.travel_date__lte = filters.value.end_date
    }
    
    // Load ALL bookings (we'll calculate summary from this)
    const allBookingsData = await bookingService.getBookings({
      ...params,
      limit: 1000
    })
    console.log('All bookings:', allBookingsData)
    
    const data = await bookingService.getBookings(params)

    // Handle paginated response (data.results) or direct array
    const bookings = data.results || data

    console.log('Bookings loaded:', bookings.length)
    console.log('First booking:', bookings[0])
    console.log('Booking types:', bookings.map(b => b.booking_type))

    // Calculate summary from bookings
    summary.value = {
      total_spend: 0,
      total_bookings: bookings.length,
      air_spend: 0,
      air_bookings: 0,
      hotel_spend: 0,
      hotel_bookings: 0,
      car_spend: 0,
      car_bookings: 0
    }

    bookings.forEach(booking => {
      const amount = parseFloat(booking.total_amount) || 0
      summary.value.total_spend += amount

      if (booking.primary_booking_type === 'AIR') {
        summary.value.air_spend += amount
        summary.value.air_bookings++
      } else if (booking.primary_booking_type === 'HOTEL') {
        summary.value.hotel_spend += amount
        summary.value.hotel_bookings++
      } else if (booking.primary_booking_type === 'CAR') {
        summary.value.car_spend += amount
        summary.value.car_bookings++
      }
    })

    // Get recent bookings (last 10)
    recentBookings.value = bookings
      .sort((a, b) => new Date(b.travel_date) - new Date(a.travel_date))
      .slice(0, 10)

    // Process monthly trend data
    processMonthlyData(bookings)

    console.log('Summary calculated:', summary.value)
    console.log('Monthly data points:', monthlyData.value.length)
    console.log('Processed monthly data:', monthlyData.value)

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

  console.log('Processed monthly data:', monthlyData.value)
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
      summary.value.hotel_spend,
      summary.value.car_spend
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
            '#a855f7', // purple-500
            '#22c55e'  // green-500
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

const resetFilters = () => {
  filters.value.start_date = ''
  filters.value.end_date = ''
  loadData()
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
    'HOTEL': 'px-2 py-1 text-xs rounded-full bg-purple-100 text-purple-800',
    'CAR': 'px-2 py-1 text-xs rounded-full bg-green-100 text-green-800',
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
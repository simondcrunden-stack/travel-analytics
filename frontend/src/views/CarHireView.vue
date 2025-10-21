<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'
import {
  Chart,
  BarController,
  DoughnutController,
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js'

Chart.register(
  BarController,
  DoughnutController,
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
)

const router = useRouter()
const bookings = ref([])
const loading = ref(true)
const error = ref(null)

const companyChartCanvas = ref(null)
const vehicleTypeChartCanvas = ref(null)
let companyChart = null
let vehicleTypeChart = null

const showFilters = ref(false)
const selectedLocation = ref('all')
const selectedCompany = ref('all')
const pickupFrom = ref('')
const pickupTo = ref('')

onMounted(async () => {
  await fetchCarHireBookings()
})

const fetchCarHireBookings = async () => {
  try {
    loading.value = true
    error.value = null
    
    const params = {
      booking_type: 'CAR'
    }
    
    if (pickupFrom.value) params.travel_date__gte = pickupFrom.value
    if (pickupTo.value) params.travel_date__lte = pickupTo.value
    
    const response = await api.get('/bookings/', { params })
    bookings.value = response.data.results || []
  } catch (err) {
    error.value = 'Failed to load car hire bookings'
    console.error('Error fetching car hire bookings:', err)
  } finally {
    loading.value = false
  }
}

const locations = computed(() => {
  const locs = new Set()
  bookings.value.forEach(booking => {
    if (booking.car_hire_details?.pickup_city) {
      locs.add(booking.car_hire_details.pickup_city)
    }
  })
  return Array.from(locs).sort()
})

const companies = computed(() => {
  const comps = new Set()
  bookings.value.forEach(booking => {
    if (booking.car_hire_details?.rental_company) {
      comps.add(booking.car_hire_details.rental_company)
    }
  })
  return Array.from(comps).sort()
})

const filteredBookings = computed(() => {
  return bookings.value.filter(booking => {
    if (selectedLocation.value !== 'all' && 
        booking.car_hire_details?.pickup_city !== selectedLocation.value) {
      return false
    }
    
    if (selectedCompany.value !== 'all' && 
        booking.car_hire_details?.rental_company !== selectedCompany.value) {
      return false
    }
    
    return true
  })
})

const totalBookings = computed(() => filteredBookings.value.length)

const totalSpend = computed(() => {
  return filteredBookings.value.reduce((sum, booking) => {
    return sum + parseFloat(booking.total_amount || 0)
  }, 0)
})

const totalDays = computed(() => {
  return filteredBookings.value.reduce((sum, booking) => {
    return sum + parseInt(booking.car_hire_details?.number_of_days || 0)
  }, 0)
})

const avgDailyRate = computed(() => {
  if (totalDays.value === 0) return 0
  return totalSpend.value / totalDays.value
})

const spendBySupplier = computed(() => {
  const supplierMap = {}
  
  filteredBookings.value.forEach(booking => {
    const supplier = booking.car_hire_details?.rental_company || 'Unknown'
    const amount = parseFloat(booking.total_amount || 0)
    
    if (!supplierMap[supplier]) {
      supplierMap[supplier] = {
        supplier,
        total: 0,
        count: 0
      }
    }
    
    supplierMap[supplier].total += amount
    supplierMap[supplier].count += 1
  })
  
  return Object.values(supplierMap).sort((a, b) => b.total - a.total)
})

const spendByVehicleType = computed(() => {
  const vehicleMap = {}
  
  filteredBookings.value.forEach(booking => {
    const vehicleType = booking.car_hire_details?.vehicle_type || 'Unknown'
    const amount = parseFloat(booking.total_amount || 0)
    const days = parseInt(booking.car_hire_details?.number_of_days || 0)
    const dailyRate = parseFloat(booking.car_hire_details?.daily_rate || 0)
    
    if (!vehicleMap[vehicleType]) {
      vehicleMap[vehicleType] = {
        vehicleType,
        total: 0,
        count: 0,
        days: 0,
        rates: []
      }
    }
    
    vehicleMap[vehicleType].total += amount
    vehicleMap[vehicleType].count += 1
    vehicleMap[vehicleType].days += days
    if (dailyRate > 0) {
      vehicleMap[vehicleType].rates.push(dailyRate)
    }
  })
  
  return Object.values(vehicleMap).map(vehicle => {
    const rates = vehicle.rates
    return {
      vehicleType: vehicle.vehicleType,
      total: vehicle.total,
      count: vehicle.count,
      days: vehicle.days,
      avgRate: rates.length > 0 ? rates.reduce((a, b) => a + b, 0) / rates.length : 0,
      minRate: rates.length > 0 ? Math.min(...rates) : 0,
      maxRate: rates.length > 0 ? Math.max(...rates) : 0
    }
  }).sort((a, b) => b.total - a.total)
})

const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-AU', {
    style: 'currency',
    currency: 'AUD'
  }).format(amount)
}

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleDateString('en-AU', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

const viewBookingDetail = (bookingId) => {
  router.push(`/bookings/${bookingId}`)
}

const applyFilters = () => {
  showFilters.value = false
  fetchCarHireBookings()
}

const clearFilters = () => {
  selectedLocation.value = 'all'
  selectedCompany.value = 'all'
  pickupFrom.value = ''
  pickupTo.value = ''
  fetchCarHireBookings()
}

const toggleFilters = () => {
  showFilters.value = !showFilters.value
}

watch([() => filteredBookings.value], () => {
  nextTick(() => {
    updateCharts()
  })
}, { deep: true })

const updateCharts = () => {
  if (!companyChartCanvas.value || !vehicleTypeChartCanvas.value) return
  
  if (companyChart) companyChart.destroy()
  if (vehicleTypeChart) vehicleTypeChart.destroy()
  
  const companyCtx = companyChartCanvas.value.getContext('2d')
  const companyData = spendBySupplier.value.slice(0, 10)
  
  companyChart = new Chart(companyCtx, {
    type: 'bar',
    data: {
      labels: companyData.map(item => item.supplier),
      datasets: [{
        label: 'Total Spend',
        data: companyData.map(item => item.total),
        backgroundColor: 'rgba(59, 130, 246, 0.8)',
        borderColor: 'rgb(59, 130, 246)',
        borderWidth: 1
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
              return formatCurrency(context.parsed.y)
            }
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            callback: function(value) {
              return '$' + (value / 1000).toFixed(0) + 'K'
            }
          }
        }
      }
    }
  })
  
  const vehicleCtx = vehicleTypeChartCanvas.value.getContext('2d')
  const vehicleData = spendByVehicleType.value
  
  const colors = [
    'rgba(59, 130, 246, 0.8)',
    'rgba(16, 185, 129, 0.8)',
    'rgba(245, 158, 11, 0.8)',
    'rgba(139, 92, 246, 0.8)',
    'rgba(236, 72, 153, 0.8)',
    'rgba(20, 184, 166, 0.8)',
    'rgba(251, 146, 60, 0.8)',
    'rgba(100, 116, 139, 0.8)'
  ]
  
  vehicleTypeChart = new Chart(vehicleCtx, {
    type: 'doughnut',
    data: {
      labels: vehicleData.map(item => item.vehicleType),
      datasets: [{
        data: vehicleData.map(item => item.count),
        backgroundColor: colors,
        borderColor: colors.map(color => color.replace('0.8', '1')),
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'right',
          labels: {
            padding: 15,
            font: {
              size: 12
            }
          }
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              const label = context.label || ''
              const value = context.parsed || 0
              const total = context.dataset.data.reduce((a, b) => a + b, 0)
              const percentage = ((value / total) * 100).toFixed(1)
              return label + ': ' + value + ' bookings (' + percentage + '%)'
            }
          }
        }
      }
    }
  })
}
</script>

<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-2xl font-bold text-gray-900">Car Hire Analytics</h1>
      <p class="mt-1 text-sm text-gray-500">
        Analyze car hire bookings and vehicle usage
      </p>
    </div>

    <div class="bg-white rounded-lg shadow">
      <button 
        @click="toggleFilters"
        class="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
      >
        <div class="flex items-center gap-2">
          <svg class="h-5 w-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
          </svg>
          <span class="text-lg font-semibold text-gray-900">Filters</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="text-sm text-blue-600 font-medium">
            {{ showFilters ? 'Hide Filters' : 'Edit Filters' }}
          </span>
          <svg 
            class="h-5 w-5 text-blue-600 transform transition-transform" 
            :class="{ 'rotate-180': showFilters }"
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      <div 
        v-show="showFilters"
        class="border-t border-gray-200 p-6"
      >
        <div class="mb-4">
          <p class="text-sm text-gray-600">Refine your car hire data</p>
          <button 
            @click="clearFilters"
            class="text-sm text-blue-600 hover:text-blue-700 font-medium mt-1"
          >
            Clear All
          </button>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Car Hire Location
            </label>
            <select 
              v-model="selectedLocation"
              class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            >
              <option value="all">All Locations</option>
              <option v-for="location in locations" :key="location" :value="location">
                {{ location }}
              </option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Car Hire Company
            </label>
            <select 
              v-model="selectedCompany"
              class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            >
              <option value="all">All Companies</option>
              <option v-for="company in companies" :key="company" :value="company">
                {{ company }}
              </option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Pick Up From
            </label>
            <input 
              v-model="pickupFrom"
              type="date"
              placeholder="dd/mm/yyyy"
              class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Drop Off To
            </label>
            <input 
              v-model="pickupTo"
              type="date"
              placeholder="dd/mm/yyyy"
              class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            />
          </div>
        </div>

        <div class="mt-6 flex gap-3">
          <button 
            @click="applyFilters"
            class="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 font-medium"
          >
            Apply Filters
          </button>
          <button 
            @click="clearFilters"
            class="px-6 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 font-medium"
          >
            Clear Filters
          </button>
        </div>
      </div>
    </div>

    <div v-if="loading" class="text-center py-12">
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      <p class="mt-2 text-sm text-gray-500">Loading car hire data...</p>
    </div>

    <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-lg p-4">
      <p class="text-red-800">{{ error }}</p>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-4 gap-6">
      <div class="bg-white rounded-lg shadow p-6">
        <div class="flex items-center">
          <div class="flex-shrink-0 bg-blue-100 rounded-md p-3">
            <svg class="h-6 w-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 012-2h4.586a1 1 0 01.707.293l4.414 4.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-2M8 7H6a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2v-2" />
            </svg>
          </div>
          <div class="ml-4">
            <p class="text-sm font-medium text-gray-500">Total Bookings</p>
            <p class="text-2xl font-semibold text-gray-900">{{ totalBookings }}</p>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-lg shadow p-6">
        <div class="flex items-center">
          <div class="flex-shrink-0 bg-green-100 rounded-md p-3">
            <svg class="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div class="ml-4">
            <p class="text-sm font-medium text-gray-500">Total Spend</p>
            <p class="text-2xl font-semibold text-gray-900">{{ formatCurrency(totalSpend) }}</p>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-lg shadow p-6">
        <div class="flex items-center">
          <div class="flex-shrink-0 bg-purple-100 rounded-md p-3">
            <svg class="h-6 w-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
          <div class="ml-4">
            <p class="text-sm font-medium text-gray-500">Total Hire Days</p>
            <p class="text-2xl font-semibold text-gray-900">{{ totalDays }}</p>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-lg shadow p-6">
        <div class="flex items-center">
          <div class="flex-shrink-0 bg-orange-100 rounded-md p-3">
            <svg class="h-6 w-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
            </svg>
          </div>
          <div class="ml-4">
            <p class="text-sm font-medium text-gray-500">Avg Daily Rate</p>
            <p class="text-2xl font-semibold text-gray-900">{{ formatCurrency(avgDailyRate) }}</p>
          </div>
        </div>
      </div>
    </div>

    <div v-if="!loading && !error" class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="bg-white rounded-lg shadow p-6">
        <h2 class="text-lg font-semibold text-gray-900 mb-4">Total Spend by Car Hire Company</h2>
        <div class="h-80">
          <canvas ref="companyChartCanvas"></canvas>
        </div>
      </div>

      <div class="bg-white rounded-lg shadow p-6">
        <h2 class="text-lg font-semibold text-gray-900 mb-4">Bookings by Vehicle Type</h2>
        <div class="h-80 flex items-center justify-center">
          <canvas ref="vehicleTypeChartCanvas"></canvas>
        </div>
      </div>
    </div>

    <div v-if="!loading && !error" class="bg-white rounded-lg shadow">
      <div class="px-6 py-4 border-b border-gray-200">
        <h2 class="text-lg font-semibold text-gray-900">Spend by Vehicle Type</h2>
      </div>
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Vehicle Type
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Bookings
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Hire Days
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Total Spend
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Avg Rate
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Min Rate
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Max Rate
              </th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="vehicle in spendByVehicleType" :key="vehicle.vehicleType" class="hover:bg-gray-50">
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm font-medium text-gray-900">{{ vehicle.vehicleType }}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm text-gray-900">{{ vehicle.count }}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm text-gray-900">{{ vehicle.days }}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm font-medium text-gray-900">{{ formatCurrency(vehicle.total) }}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm text-gray-900">{{ formatCurrency(vehicle.avgRate) }}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm text-gray-500">{{ formatCurrency(vehicle.minRate) }}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm text-gray-500">{{ formatCurrency(vehicle.maxRate) }}</div>
              </td>
            </tr>
            <tr v-if="spendByVehicleType.length === 0">
              <td colspan="7" class="px-6 py-4 text-center text-sm text-gray-500">
                No vehicle type data available
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-if="!loading && !error" class="bg-white rounded-lg shadow">
      <div class="px-6 py-4 border-b border-gray-200">
        <h2 class="text-lg font-semibold text-gray-900">Spend by Supplier</h2>
      </div>
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Supplier
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Bookings
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Total Spend
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Avg per Booking
              </th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="supplier in spendBySupplier" :key="supplier.supplier" class="hover:bg-gray-50">
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm font-medium text-gray-900">{{ supplier.supplier }}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm text-gray-900">{{ supplier.count }}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm font-medium text-gray-900">{{ formatCurrency(supplier.total) }}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm text-gray-500">{{ formatCurrency(supplier.total / supplier.count) }}</div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-if="!loading && !error" class="bg-white rounded-lg shadow">
      <div class="px-6 py-4 border-b border-gray-200">
        <h2 class="text-lg font-semibold text-gray-900">Recent Car Hire Bookings</h2>
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
                Supplier
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Vehicle Type
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Pickup Date
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Days
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Amount
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="booking in filteredBookings.slice(0, 10)" :key="booking.id" class="hover:bg-gray-50">
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm font-medium text-gray-900">{{ booking.agent_booking_reference }}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm text-gray-900">
                  {{ booking.traveller ? booking.traveller.first_name + ' ' + booking.traveller.last_name : 'N/A' }}
                </div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm text-gray-900">
                  {{ booking.car_hire_details?.rental_company || 'N/A' }}
                </div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm text-gray-900">
                  {{ booking.car_hire_details?.vehicle_type || 'N/A' }}
                </div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm text-gray-900">
                  {{ formatDate(booking.car_hire_details?.pickup_date) }}
                </div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm text-gray-900">
                  {{ booking.car_hire_details?.number_of_days || 'N/A' }}
                </div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm font-medium text-gray-900">
                  {{ formatCurrency(booking.total_amount) }}
                </div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm">
                <button 
                  @click="viewBookingDetail(booking.id)"
                  class="text-blue-600 hover:text-blue-900 font-medium"
                >
                  View Details
                </button>
              </td>
            </tr>
            <tr v-if="filteredBookings.length === 0">
              <td colspan="8" class="px-6 py-4 text-center text-sm text-gray-500">
                No car hire bookings found
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
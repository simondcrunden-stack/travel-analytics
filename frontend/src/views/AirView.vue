<template>
  <div class="min-h-screen bg-gray-50 p-6">
    <!-- Header -->
    <div class="mb-6">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-3xl font-bold text-gray-900">Air Travel Dashboard</h1>
          <p class="text-gray-600 mt-1">Airline spend and flight booking analysis</p>
        </div>
        
        <!-- Export Button -->
        <button
          @click="exportReport"
          class="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <svg class="w-5 h-5" :d="mdiDownload" />
          <span>Export Report</span>
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-12">
      <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      <p class="mt-4 text-gray-600">Loading air travel data...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-lg p-4">
      <p class="text-red-800">{{ error }}</p>
    </div>

    <!-- Main Content -->
    <div v-else>
      <!-- Summary Cards -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
        <div class="bg-white rounded-2xl shadow-sm p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-gray-600 text-sm">Total Air Spend</p>
              <p class="text-3xl font-bold text-gray-900 mt-1">
                {{ formatCurrency(stats.totalSpend) }}
              </p>
            </div>
            <div class="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
              <svg class="w-6 h-6 text-blue-600" :d="mdiAirplane" />
            </div>
          </div>
        </div>

        <div class="bg-white rounded-2xl shadow-sm p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-gray-600 text-sm">Total Bookings</p>
              <p class="text-3xl font-bold text-gray-900 mt-1">{{ stats.totalBookings }}</p>
            </div>
            <div class="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center">
              <svg class="w-6 h-6 text-purple-600" :d="mdiTicket" />
            </div>
          </div>
        </div>

        <div class="bg-white rounded-2xl shadow-sm p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-gray-600 text-sm">Avg. Fare</p>
              <p class="text-3xl font-bold text-gray-900 mt-1">
                {{ formatCurrency(stats.avgFare) }}
              </p>
            </div>
            <div class="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center">
              <svg class="w-6 h-6 text-green-600" :d="mdiCurrencyUsd" />
            </div>
          </div>
        </div>

        <div class="bg-white rounded-2xl shadow-sm p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-gray-600 text-sm">CO₂ Emissions</p>
              <p class="text-3xl font-bold text-gray-900 mt-1">
                {{ formatNumber(stats.totalEmissions) }}
                <span class="text-sm text-gray-600">kg</span>
              </p>
            </div>
            <div class="w-12 h-12 bg-orange-100 rounded-xl flex items-center justify-center">
              <svg class="w-6 h-6 text-orange-600" :d="mdiLeaf" />
            </div>
          </div>
        </div>
      </div>

      <!-- Filters -->
      <div class="bg-white rounded-2xl shadow-sm mb-6 overflow-hidden">
        <!-- Filter Header -->
        <div class="px-6 py-4 flex items-center justify-between border-b border-gray-200">
          <div class="flex items-center gap-3">
            <svg class="w-5 h-5 text-gray-600" :d="mdiFilter" />
            <h2 class="text-lg font-semibold text-gray-900">Filters</h2>
            <span v-if="activeFilterCount > 0" class="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded-full">
              {{ activeFilterCount }} active
            </span>
          </div>
          <button
            @click="filtersOpen = !filtersOpen"
            class="flex items-center gap-2 px-4 py-2 text-sm font-medium text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-lg transition-colors"
          >
            <svg class="w-4 h-4" :d="filtersOpen ? mdiEyeOff : mdiPencil" />
            <span>{{ filtersOpen ? 'Hide Filters' : 'Edit Filters' }}</span>
          </button>
        </div>

        <!-- Filter Content -->
        <div v-show="filtersOpen" class="p-6">
          <div class="flex items-center justify-between mb-4">
            <p class="text-sm text-gray-600">Refine your air travel data</p>
            <button
              @click="clearFilters"
              class="text-sm text-blue-600 hover:text-blue-700 font-medium"
            >
              Clear All
            </button>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-5 gap-4">
            <!-- Trip Type -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">Trip Type</label>
              <select
                v-model="filters.tripType"
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">All Types</option>
                <option value="domestic">Domestic</option>
                <option value="international">International</option>
              </select>
            </div>

            <!-- Travel Class -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">Travel Class</label>
              <select
                v-model="filters.travelClass"
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">All Classes</option>
                <option value="ECONOMY">Economy</option>
                <option value="PREMIUM_ECONOMY">Premium Economy</option>
                <option value="BUSINESS">Business</option>
                <option value="FIRST">First Class</option>
              </select>
            </div>

            <!-- Airline -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">Airline</label>
              <select
                v-model="filters.airline"
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">All Airlines</option>
                <option value="Qantas">Qantas</option>
                <option value="Virgin Australia">Virgin Australia</option>
                <option value="Singapore Airlines">Singapore Airlines</option>
                <option value="Air New Zealand">Air New Zealand</option>
                <option value="Emirates">Emirates</option>
                <option value="Jetstar">Jetstar</option>
                <option value="United Airlines">United Airlines</option>
              </select>
            </div>

            <!-- Date From -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">From Date</label>
              <input
                type="date"
                v-model="filters.dateFrom"
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <!-- Date To -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">To Date</label>
              <input
                type="date"
                v-model="filters.dateTo"
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Two Column Layout -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <!-- Airline Spend Chart -->
        <div class="bg-white rounded-2xl shadow-sm p-6">
          <h2 class="text-lg font-semibold text-gray-900 mb-4">Spend by Airline</h2>
          <canvas ref="airlineChartCanvas"></canvas>
        </div>

        <!-- Class of Travel Chart -->
        <div class="bg-white rounded-2xl shadow-sm p-6">
          <h2 class="text-lg font-semibold text-gray-900 mb-4">Bookings by Travel Class</h2>
          <canvas ref="classChartCanvas"></canvas>
        </div>
      </div>

      <!-- Advance Purchase Analysis -->
      <div class="bg-white rounded-2xl shadow-sm p-6 mb-6">
        <div class="flex items-center justify-between mb-4">
          <div>
            <h2 class="text-lg font-semibold text-gray-900">Average Fare by Advance Purchase Period</h2>
            <p class="text-sm text-gray-600 mt-1">Book earlier to save more</p>
          </div>
          <div class="text-right">
            <p class="text-sm text-gray-600">Potential Savings</p>
            <p class="text-2xl font-bold text-green-600">{{ formatCurrency(advancePurchaseSavings) }}</p>
          </div>
        </div>
        <canvas ref="advancePurchaseChartCanvas"></canvas>
      </div>

      <!-- Top Routes Table -->
      <div class="bg-white rounded-2xl shadow-sm overflow-hidden mb-6">
        <div class="p-6 border-b border-gray-200">
          <h2 class="text-lg font-semibold text-gray-900">Top 10 Routes</h2>
          <p class="text-sm text-gray-600 mt-1">Most frequently traveled routes</p>
        </div>

        <div class="overflow-x-auto">
          <table class="w-full">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Rank
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Route
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Bookings
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Total Spend
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Avg. Fare
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  CO₂ Emissions
                </th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr
                v-for="(route, index) in topRoutes"
                :key="index"
                class="hover:bg-gray-50 transition-colors"
              >
                <td class="px-6 py-4 whitespace-nowrap">
                  <span
                    :class="getRankBadgeClass(index + 1)"
                    class="inline-flex items-center justify-center w-8 h-8 rounded-full font-semibold"
                  >
                    {{ index + 1 }}
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="flex items-center gap-2">
                    <span class="font-medium text-gray-900">{{ route.origin }}</span>
                    <svg class="w-4 h-4 text-gray-400" :d="mdiArrowRight" />
                    <span class="font-medium text-gray-900">{{ route.destination }}</span>
                  </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span
                    :class="route.type === 'Domestic' ? 'bg-blue-100 text-blue-800' : 'bg-purple-100 text-purple-800'"
                    class="px-2 py-1 text-xs font-medium rounded-full"
                  >
                    {{ route.type }}
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {{ route.bookings }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {{ formatCurrency(route.totalSpend) }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {{ formatCurrency(route.avgFare) }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                  {{ formatNumber(route.emissions) }} kg
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Recent Bookings -->
      <div class="bg-white rounded-2xl shadow-sm overflow-hidden">
        <div class="p-6 border-b border-gray-200">
          <h2 class="text-lg font-semibold text-gray-900">Recent Air Bookings</h2>
          <p class="text-sm text-gray-600 mt-1">Latest flight bookings</p>
        </div>

        <div class="overflow-x-auto">
          <table class="w-full">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date
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
                  Fare
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Booking Ref
                </th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr
                v-for="booking in recentBookings"
                :key="booking.id"
                class="hover:bg-gray-50 transition-colors cursor-pointer"
                @click="viewBooking(booking)"
              >
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {{ formatDate(booking.date) }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="text-sm font-medium text-gray-900">{{ booking.traveller }}</div>
                  <div class="text-sm text-gray-500">{{ booking.organization }}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="flex items-center gap-2">
                    <span class="text-sm font-medium text-gray-900">{{ booking.origin }}</span>
                    <svg class="w-4 h-4 text-gray-400" :d="mdiArrowRight" />
                    <span class="text-sm font-medium text-gray-900">{{ booking.destination }}</span>
                  </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {{ booking.airline }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span :class="getClassBadgeClass(booking.class)">
                    {{ booking.class }}
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {{ formatCurrency(booking.fare) }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                  {{ booking.reference }}
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
import { ref, computed, onMounted, nextTick, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  BarController,
  ArcElement,
  DoughnutController,
  Title,
  Tooltip,
  Legend
} from 'chart.js'
import {
  mdiAirplane,
  mdiTicket,
  mdiCurrencyUsd,
  mdiLeaf,
  mdiDownload,
  mdiArrowRight,
  mdiFilter,
  mdiChevronDown,
} from '@mdi/js'

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  BarController,
  ArcElement,
  DoughnutController,
  Title,
  Tooltip,
  Legend
)

const router = useRouter()

// State
const loading = ref(true)
const error = ref(null)
const airlineChartCanvas = ref(null)
const classChartCanvas = ref(null)
const advancePurchaseChartCanvas = ref(null)
let airlineChart = null
let classChart = null
let advancePurchaseChart = null

// Filters
const filters = ref({
  tripType: '',
  travelClass: '',
  airline: '',
  dateFrom: '',
  dateTo: '',
})
const filtersOpen = ref(false)

// Stats
const stats = ref({
  totalSpend: 0,
  totalBookings: 0,
  avgFare: 0,
  totalEmissions: 0,
})

// Data
const airlineData = ref([])
const classData = ref([])
const advancePurchaseData = ref([])
const topRoutes = ref([])
const recentBookings = ref([])

// Fetch data
const fetchAirData = async () => {
  try {
    loading.value = true
    error.value = null

    // Generate sample data
    generateSampleData()
    
    console.log('Airline Data:', airlineData.value)
    console.log('Class Data:', classData.value)
  } catch (err) {
    error.value = 'Failed to load air travel data'
    console.error('Error:', err)
  } finally {
    loading.value = false
  }
}

// Generate sample data
const generateSampleData = () => {
  // Stats
  stats.value = {
    totalSpend: 458750,
    totalBookings: 156,
    avgFare: 2940,
    totalEmissions: 12450,
  }

  // Airline data
  airlineData.value = [
    { airline: 'Qantas', spend: 185000, bookings: 68 },
    { airline: 'Virgin Australia', spend: 98000, bookings: 42 },
    { airline: 'Singapore Airlines', spend: 75000, bookings: 18 },
    { airline: 'Air New Zealand', spend: 52000, bookings: 15 },
    { airline: 'Emirates', spend: 48750, bookings: 13 },
  ]

  // Class data
  classData.value = [
    { class: 'Economy', bookings: 132, percentage: 85 },
    { class: 'Premium Economy', bookings: 15, percentage: 10 },
    { class: 'Business', bookings: 8, percentage: 5 },
    { class: 'First', bookings: 1, percentage: 0.6 },
  ]

  // Advance purchase data
  advancePurchaseData.value = [
    { period: '0-2 days', avgFare: 613.65, bookings: 12, color: '#EF4444' },
    { period: '3-7 days', avgFare: 624.69, bookings: 18, color: '#F59E0B' },
    { period: '8-15 days', avgFare: 575.58, bookings: 25, color: '#F59E0B' },
    { period: '16-21 days', avgFare: 491.90, bookings: 32, color: '#10B981' },
    { period: '22-30 days', avgFare: 590.73, bookings: 38, color: '#10B981' },
    { period: '31+ days', avgFare: 530.93, bookings: 31, color: '#10B981' },
  ]

  // Top routes
  topRoutes.value = [
    { origin: 'SYD', destination: 'MEL', type: 'Domestic', bookings: 45, totalSpend: 98500, avgFare: 2189, emissions: 31500 },
    { origin: 'MEL', destination: 'BNE', type: 'Domestic', bookings: 28, totalSpend: 52800, avgFare: 1886, emissions: 19600 },
    { origin: 'SYD', destination: 'SIN', type: 'International', bookings: 18, totalSpend: 75000, avgFare: 4167, emissions: 36000 },
    { origin: 'BNE', destination: 'AKL', type: 'International', bookings: 15, totalSpend: 52000, avgFare: 3467, emissions: 22500 },
    { origin: 'SYD', destination: 'PER', type: 'Domestic', bookings: 12, totalSpend: 42000, avgFare: 3500, emissions: 48000 },
    { origin: 'MEL', destination: 'SYD', type: 'Domestic', bookings: 10, totalSpend: 22000, avgFare: 2200, emissions: 7050 },
    { origin: 'SYD', destination: 'LAX', type: 'International', bookings: 8, totalSpend: 65000, avgFare: 8125, emissions: 80000 },
    { origin: 'SYD', destination: 'NRT', type: 'International', bookings: 6, totalSpend: 45000, avgFare: 7500, emissions: 54000 },
    { origin: 'BNE', destination: 'SYD', type: 'Domestic', bookings: 5, totalSpend: 9500, avgFare: 1900, emissions: 3525 },
    { origin: 'MEL', destination: 'PER', type: 'Domestic', bookings: 5, totalSpend: 18500, avgFare: 3700, emissions: 17500 },
  ]

  // Recent bookings
  recentBookings.value = [
    { id: 1, date: '2025-10-18', traveller: 'Jennifer Wilson', organization: 'TechCorp Australia', origin: 'SYD', destination: 'MEL', airline: 'Qantas', class: 'Economy', fare: 485, reference: 'QF4356' },
    { id: 2, date: '2025-10-17', traveller: 'David Anderson', organization: 'TechCorp Australia', origin: 'MEL', destination: 'BNE', airline: 'Virgin Australia', class: 'Economy', fare: 420, reference: 'VA823' },
    { id: 3, date: '2025-10-15', traveller: 'Sophie Martinez', organization: 'TechCorp Australia', origin: 'SYD', destination: 'SIN', airline: 'Singapore Airlines', class: 'Economy', fare: 1850, reference: 'SQ231' },
    { id: 4, date: '2025-10-14', traveller: 'Robert Thompson', organization: 'TechCorp Australia', origin: 'SYD', destination: 'NRT', airline: 'Qantas', class: 'Business', fare: 5680, reference: 'QF25' },
    { id: 5, date: '2025-10-12', traveller: 'Emily White', organization: 'Retail Solutions Group', origin: 'BNE', destination: 'AKL', airline: 'Air New Zealand', class: 'Economy', fare: 1240, reference: 'NZ145' },
  ]
}

// Create charts
const createCharts = () => {
  console.log('createCharts() called')
  
  // Destroy existing charts
  if (airlineChart) {
    airlineChart.destroy()
    airlineChart = null
  }
  if (classChart) {
    classChart.destroy()
    classChart = null
  }
  if (advancePurchaseChart) {
    advancePurchaseChart.destroy()
    advancePurchaseChart = null
  }

  // Airline Chart
  if (airlineChartCanvas.value) {
    const ctx = airlineChartCanvas.value.getContext('2d')
    airlineChart = new ChartJS(ctx, {
      type: 'bar',
      data: {
        labels: airlineData.value.map(d => d.airline),
        datasets: [{
          label: 'Spend',
          data: airlineData.value.map(d => d.spend),
          backgroundColor: '#3B82F6',
          borderRadius: 8,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (context) => `Spend: ${formatCurrency(context.parsed.y)}`
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              callback: (value) => `$${value / 1000}k`
            }
          }
        }
      }
    })
    console.log('Airline chart created')
  }

  // Class Chart
  if (classChartCanvas.value) {
    const ctx = classChartCanvas.value.getContext('2d')
    classChart = new ChartJS(ctx, {
      type: 'doughnut',
      data: {
        labels: classData.value.map(d => d.class),
        datasets: [{
          data: classData.value.map(d => d.bookings),
          backgroundColor: ['#3B82F6', '#8B5CF6', '#F59E0B', '#EF4444'],
          borderWidth: 2,
          borderColor: '#fff',
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              padding: 15,
              font: { size: 12 }
            }
          },
          tooltip: {
            callbacks: {
              label: (context) => {
                const label = context.label
                const value = context.parsed
                const total = context.dataset.data.reduce((a, b) => a + b, 0)
                const percentage = Math.round((value / total) * 100)
                return `${label}: ${value} (${percentage}%)`
              }
            }
          }
        }
      }
    })
    console.log('Class chart created')
  }

  // Advance Purchase Chart
  console.log('Creating advance purchase chart...')
  if (advancePurchaseChartCanvas.value) {
    const ctx = advancePurchaseChartCanvas.value.getContext('2d')
    advancePurchaseChart = new ChartJS(ctx, {
      type: 'bar',
      data: {
        labels: advancePurchaseData.value.map(d => d.period),
        datasets: [{
          label: 'Avg. Fare',
          data: advancePurchaseData.value.map(d => d.avgFare),
          backgroundColor: advancePurchaseData.value.map(d => d.color),
          borderRadius: 8,
        }]
      },
      options: {
        indexAxis: 'y', // Horizontal bars
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (context) => {
                const fare = formatCurrency(context.parsed.x)
                const bookings = advancePurchaseData.value[context.dataIndex].bookings
                return [`Avg. Fare: ${fare}`, `Bookings: ${bookings}`]
              }
            }
          }
        },
        scales: {
          x: {
            beginAtZero: true,
            ticks: {
              callback: (value) => `$${value}`
            }
          }
        }
      }
    })
    console.log('Advance purchase chart created!')
  } else {
    console.error('Advance purchase canvas not found!')
  }
}

// Computed: Active filter count
const activeFilterCount = computed(() => {
  let count = 0
  if (filters.value.tripType) count++
  if (filters.value.travelClass) count++
  if (filters.value.airline) count++
  if (filters.value.dateFrom) count++
  if (filters.value.dateTo) count++
  return count
})

// Computed: Advance purchase savings
const advancePurchaseSavings = computed(() => {
  if (advancePurchaseData.value.length === 0) return 0
  const maxFare = Math.max(...advancePurchaseData.value.map(d => d.avgFare))
  const minFare = Math.min(...advancePurchaseData.value.map(d => d.avgFare))
  return maxFare - minFare
})
const formatCurrency = (value) => {
  return new Intl.NumberFormat('en-AU', {
    style: 'currency',
    currency: 'AUD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value)
}

const formatNumber = (value) => {
  return new Intl.NumberFormat('en-AU').format(value)
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('en-AU', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

const getRankBadgeClass = (rank) => {
  if (rank === 1) return 'bg-yellow-100 text-yellow-800'
  if (rank === 2) return 'bg-gray-200 text-gray-800'
  if (rank === 3) return 'bg-orange-100 text-orange-800'
  return 'bg-gray-100 text-gray-700'
}

const getClassBadgeClass = (travelClass) => {
  const classes = {
    Economy: 'px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800',
    'Premium Economy': 'px-2 py-1 text-xs font-medium rounded-full bg-purple-100 text-purple-800',
    Business: 'px-2 py-1 text-xs font-medium rounded-full bg-orange-100 text-orange-800',
    First: 'px-2 py-1 text-xs font-medium rounded-full bg-red-100 text-red-800',
  }
  return classes[travelClass] || classes.Economy
}

const clearFilters = () => {
  filters.value = {
    tripType: '',
    travelClass: '',
    airline: '',
    dateFrom: '',
    dateTo: '',
  }
}

const viewBooking = (booking) => {
  console.log('View booking:', booking)
  // router.push(`/bookings/${booking.id}`)
}

const exportReport = () => {
  console.log('Exporting air travel report...')
}

// Lifecycle
onMounted(async () => {
  console.log('Component mounted')
  await fetchAirData()
  console.log('Data fetched')
  
  // Wait a bit longer for DOM to be ready
  setTimeout(() => {
    console.log('Timeout fired - checking canvas refs')
    console.log('Timeout - Canvas refs:', {
      airline: airlineChartCanvas.value,
      class: classChartCanvas.value,
      advancePurchase: advancePurchaseChartCanvas.value
    })
    console.log('Advance Purchase Data:', advancePurchaseData.value)
    
    console.log('Calling createCharts()...')
    createCharts()
    console.log('createCharts() finished')
  }, 150)
})

onBeforeUnmount(() => {
  if (airlineChart) airlineChart.destroy()
  if (classChart) classChart.destroy()
  if (advancePurchaseChart) advancePurchaseChart.destroy()
})
</script>
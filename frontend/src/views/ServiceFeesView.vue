<template>
  <div class="min-h-screen bg-gray-50 p-6">
    <!-- Header -->
    <div class="mb-6">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-3xl font-bold text-gray-900">Service Fees Dashboard</h1>
          <p class="text-gray-600 mt-1">Travel agency service fees and transaction analysis</p>
        </div>
        
        <!-- Export Button -->
        <button
          @click="exportReport"
          class="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
            <path d="M5,20H19V18H5M19,9H15V3H9V9H5L12,16L19,9Z" />
          </svg>
          <span>Export Report</span>
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-12">
      <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      <p class="mt-4 text-gray-600">Loading service fees data...</p>
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
              <p class="text-gray-600 text-sm">Total Service Fees</p>
              <p class="text-3xl font-bold text-gray-900 mt-1">
                {{ formatCurrency(stats.totalFees) }}
              </p>
            </div>
            <div class="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
              <svg class="w-6 h-6 text-blue-600" fill="currentColor" viewBox="0 0 24 24">
                <path d="M7,15H9C9,16.08 10.37,17 12,17C13.63,17 15,16.08 15,15C15,13.9 13.96,13.5 11.76,12.97C9.64,12.44 7,11.78 7,9C7,7.21 8.47,5.69 10.5,5.18V3H13.5V5.18C15.53,5.69 17,7.21 17,9H15C15,7.92 13.63,7 12,7C10.37,7 9,7.92 9,9C9,10.1 10.04,10.5 12.24,11.03C14.36,11.56 17,12.22 17,15C17,16.79 15.53,18.31 13.5,18.82V21H10.5V18.82C8.47,18.31 7,16.79 7,15Z" />
              </svg>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-2xl shadow-sm p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-gray-600 text-sm">Total Transactions</p>
              <p class="text-3xl font-bold text-gray-900 mt-1">{{ stats.totalTransactions }}</p>
            </div>
            <div class="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center">
              <svg class="w-6 h-6 text-purple-600" fill="currentColor" viewBox="0 0 24 24">
                <path d="M3,6H21V18H3V6M12,9A3,3 0 0,1 15,12A3,3 0 0,1 12,15A3,3 0 0,1 9,12A3,3 0 0,1 12,9M7,8A2,2 0 0,1 5,10V14A2,2 0 0,1 7,16H17A2,2 0 0,1 19,14V10A2,2 0 0,1 17,8H7Z" />
              </svg>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-2xl shadow-sm p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-gray-600 text-sm">Avg. Fee per Transaction</p>
              <p class="text-3xl font-bold text-gray-900 mt-1">
                {{ formatCurrency(stats.avgFeePerTransaction) }}
              </p>
            </div>
            <div class="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center">
              <svg class="w-6 h-6 text-green-600" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12,8A4,4 0 0,1 16,12A4,4 0 0,1 12,16A4,4 0 0,1 8,12A4,4 0 0,1 12,8M12,10A2,2 0 0,0 10,12A2,2 0 0,0 12,14A2,2 0 0,0 14,12A2,2 0 0,0 12,10M7,22A1,1 0 0,1 6,21V19.5C4.8,18.9 4,17.6 4,16V15C4,14.4 4.4,14 5,14H6V9A1,1 0 0,1 7,8H9V6H15V8H17A1,1 0 0,1 18,9V14H19C19.6,14 20,14.4 20,15V16C20,17.6 19.2,18.9 18,19.5V21A1,1 0 0,1 17,22H16V20H8V22H7M8,9V14H16V9H8M9,16V18H15V16H9Z" />
              </svg>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-2xl shadow-sm p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-gray-600 text-sm">Online Booking %</p>
              <p class="text-3xl font-bold text-gray-900 mt-1">{{ stats.onlineBookingPct }}%</p>
              <p class="text-xs text-gray-500 mt-1">vs {{ 100 - stats.onlineBookingPct }}% offline</p>
            </div>
            <div class="w-12 h-12 bg-orange-100 rounded-xl flex items-center justify-center">
              <svg class="w-6 h-6 text-orange-600" fill="currentColor" viewBox="0 0 24 24">
                <path d="M17,7H22V17H17V19A1,1 0 0,0 18,20H20V22H17.5C16.95,22 16,21.55 16,21C16,21.55 15.05,22 14.5,22H12V20H14A1,1 0 0,0 15,19V5A1,1 0 0,0 14,4H12V2H14.5C15.05,2 16,2.45 16,3C16,2.45 16.95,2 17.5,2H20V4H18A1,1 0 0,0 17,5V7M2,7H13V9H4V15H13V17H2V7M20,15V9H17V15H20Z" />
              </svg>
            </div>
          </div>
        </div>
      </div>

      <!-- Filters -->
      <div class="bg-white rounded-2xl shadow-sm mb-6 overflow-hidden">
        <div class="px-6 py-4 flex items-center justify-between border-b border-gray-200">
          <div class="flex items-center gap-3">
            <svg class="w-5 h-5 text-gray-600" fill="currentColor" viewBox="0 0 24 24">
              <path d="M14,12V19.88C14.04,20.18 13.94,20.5 13.71,20.71C13.32,21.1 12.69,21.1 12.3,20.71L10.29,18.7C10.06,18.47 9.96,18.16 10,17.87V12H9.97L4.21,4.62C3.87,4.19 3.95,3.56 4.38,3.22C4.57,3.08 4.78,3 5,3V3H19V3C19.22,3 19.43,3.08 19.62,3.22C20.05,3.56 20.13,4.19 19.79,4.62L14.03,12H14Z" />
            </svg>
            <h2 class="text-lg font-semibold text-gray-900">Filters</h2>
            <span v-if="activeFilterCount > 0" class="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded-full">
              {{ activeFilterCount }} active
            </span>
          </div>
          <button
            @click="filtersOpen = !filtersOpen"
            class="flex items-center gap-2 px-4 py-2 text-sm font-medium text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-lg transition-colors"
          >
            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
              <path d="M20.71,7.04C21.1,6.65 21.1,6 20.71,5.63L18.37,3.29C18,2.9 17.35,2.9 16.96,3.29L15.12,5.12L18.87,8.87M3,17.25V21H6.75L17.81,9.93L14.06,6.18L3,17.25Z" />
            </svg>
            <span>{{ filtersOpen ? 'Hide Filters' : 'Edit Filters' }}</span>
          </button>
        </div>

        <div v-show="filtersOpen" class="p-6">
          <div class="flex items-center justify-between mb-4">
            <p class="text-sm text-gray-600">Refine your service fees data</p>
            <button
              @click="clearFilters"
              class="text-sm text-blue-600 hover:text-blue-700 font-medium"
            >
              Clear All
            </button>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">Fee Type</label>
              <select
                v-model="filters.feeType"
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">All Types</option>
                <option value="BOOKING_ONLINE_DOM">Online - Domestic</option>
                <option value="BOOKING_ONLINE_INTL">Online - International</option>
                <option value="BOOKING_OFFLINE_DOM">Offline - Domestic</option>
                <option value="BOOKING_OFFLINE_INTL">Offline - International</option>
                <option value="CHANGE_FEE">Change Fee</option>
                <option value="REFUND_FEE">Refund Fee</option>
              </select>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">Booking Channel</label>
              <select
                v-model="filters.channel"
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">All Channels</option>
                <option value="online">Online</option>
                <option value="offline">Offline</option>
              </select>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">Date From</label>
              <input
                type="date"
                v-model="filters.dateFrom"
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">Date To</label>
              <input
                type="date"
                v-model="filters.dateTo"
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Charts -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div class="bg-white rounded-2xl shadow-sm p-6">
          <h2 class="text-lg font-semibold text-gray-900 mb-4">Fees by Type</h2>
          <canvas ref="feeTypeChartCanvas"></canvas>
        </div>

        <div class="bg-white rounded-2xl shadow-sm p-6">
          <h2 class="text-lg font-semibold text-gray-900 mb-4">Online vs Offline Bookings</h2>
          <canvas ref="channelChartCanvas"></canvas>
        </div>
      </div>

      <div class="bg-white rounded-2xl shadow-sm p-6 mb-6">
        <div class="flex items-center justify-between mb-4">
          <div>
            <h2 class="text-lg font-semibold text-gray-900">Service Fee Trends</h2>
            <p class="text-sm text-gray-600 mt-1">Monthly fee revenue over time</p>
          </div>
        </div>
        <canvas ref="trendChartCanvas"></canvas>
      </div>

      <!-- Fee Type Breakdown Table -->
      <div class="bg-white rounded-2xl shadow-sm overflow-hidden mb-6">
        <div class="p-6 border-b border-gray-200">
          <h2 class="text-lg font-semibold text-gray-900">Fee Type Breakdown</h2>
          <p class="text-sm text-gray-600 mt-1">Detailed analysis by fee category</p>
        </div>

        <div class="overflow-x-auto">
          <table class="w-full">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Fee Type</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Transactions</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total Fees</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Avg. Fee</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">% of Total</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="feeType in feeBreakdown" :key="feeType.type" class="hover:bg-gray-50">
                <td class="px-6 py-4">
                  <span class="px-2 py-1 text-xs font-medium rounded-full" :class="getFeeTypeBadgeClass(feeType.type)">
                    {{ feeType.label }}
                  </span>
                </td>
                <td class="px-6 py-4 text-sm text-gray-900">{{ feeType.transactions }}</td>
                <td class="px-6 py-4 text-sm font-medium text-gray-900">{{ formatCurrency(feeType.totalFees) }}</td>
                <td class="px-6 py-4 text-sm text-gray-900">{{ formatCurrency(feeType.avgFee) }}</td>
                <td class="px-6 py-4">
                  <div class="flex items-center gap-3">
                    <div class="flex-1 bg-gray-200 rounded-full h-2">
                      <div class="bg-blue-600 h-2 rounded-full" :style="{ width: feeType.percentage + '%' }"></div>
                    </div>
                    <span class="text-sm font-medium text-gray-900 w-12">{{ feeType.percentage }}%</span>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Recent Transactions -->
      <div class="bg-white rounded-2xl shadow-sm overflow-hidden">
        <div class="p-6 border-b border-gray-200">
          <h2 class="text-lg font-semibold text-gray-900">Recent Service Fee Transactions</h2>
          <p class="text-sm text-gray-600 mt-1">Latest fee charges</p>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Traveller</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Fee Type</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Channel</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Booking Type</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Fee Amount</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Booking Ref</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="transaction in recentTransactions" :key="transaction.id" class="hover:bg-gray-50 cursor-pointer" @click="viewTransaction(transaction)">
                <td class="px-6 py-4 text-sm">{{ formatDate(transaction.date) }}</td>
                <td class="px-6 py-4">
                  <div class="text-sm font-medium">{{ transaction.traveller }}</div>
                  <div class="text-sm text-gray-500">{{ transaction.organization }}</div>
                </td>
                <td class="px-6 py-4">
                  <span class="px-2 py-1 text-xs font-medium rounded-full" :class="getFeeTypeBadgeClass(transaction.feeType)">
                    {{ transaction.feeTypeLabel }}
                  </span>
                </td>
                <td class="px-6 py-4">
                  <span class="px-2 py-1 text-xs font-medium rounded-full" :class="transaction.channel === 'Online' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'">
                    {{ transaction.channel }}
                  </span>
                </td>
                <td class="px-6 py-4 text-sm">{{ transaction.bookingType }}</td>
                <td class="px-6 py-4 text-sm font-medium">{{ formatCurrency(transaction.fee) }}</td>
                <td class="px-6 py-4 text-sm text-gray-600">{{ transaction.reference }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  BarController,
  ArcElement,
  DoughnutController,
  LineElement,
  LineController,
  PointElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, BarElement, BarController, ArcElement, DoughnutController, LineElement, LineController, PointElement, Title, Tooltip, Legend)

const loading = ref(true)
const error = ref(null)
const feeTypeChartCanvas = ref(null)
const channelChartCanvas = ref(null)
const trendChartCanvas = ref(null)
let feeTypeChart = null
let channelChart = null
let trendChart = null

const filters = ref({ feeType: '', channel: '', dateFrom: '', dateTo: '' })
const filtersOpen = ref(false)

const stats = ref({ totalFees: 0, totalTransactions: 0, avgFeePerTransaction: 0, onlineBookingPct: 0 })
const feeTypeData = ref([])
const channelData = ref([])
const trendData = ref([])
const feeBreakdown = ref([])
const recentTransactions = ref([])

const fetchServiceFeesData = async () => {
  try {
    loading.value = true
    
    stats.value = {
      totalFees: 18450,
      totalTransactions: 156,
      avgFeePerTransaction: 118,
      onlineBookingPct: 68
    }
    
    feeTypeData.value = [
      { type: 'Online Domestic', amount: 5850 },
      { type: 'Online International', amount: 6200 },
      { type: 'Offline Domestic', amount: 2800 },
      { type: 'Offline International', amount: 3200 },
      { type: 'Change Fees', amount: 400 }
    ]
    
    channelData.value = [
      { channel: 'Online', bookings: 106, percentage: 68 },
      { channel: 'Offline', bookings: 50, percentage: 32 }
    ]
    
    trendData.value = [
      { month: 'Jul', fees: 2800 },
      { month: 'Aug', fees: 3100 },
      { month: 'Sep', fees: 2950 },
      { month: 'Oct', fees: 3200 }
    ]
    
    feeBreakdown.value = [
      { type: 'online_dom', label: 'Online Booking - Domestic', transactions: 58, totalFees: 5850, avgFee: 101, percentage: 32 },
      { type: 'online_intl', label: 'Online Booking - International', transactions: 48, totalFees: 6200, avgFee: 129, percentage: 34 },
      { type: 'offline_dom', label: 'Offline Booking - Domestic', transactions: 22, totalFees: 2800, avgFee: 127, percentage: 15 },
      { type: 'offline_intl', label: 'Offline Booking - International', transactions: 18, totalFees: 3200, avgFee: 178, percentage: 17 },
      { type: 'change', label: 'Change Fee', transactions: 8, totalFees: 320, avgFee: 40, percentage: 2 },
      { type: 'refund', label: 'Refund Fee', transactions: 2, totalFees: 80, avgFee: 40, percentage: 0 }
    ]
    
    recentTransactions.value = [
      { id: 1, date: '2025-10-20', traveller: 'Jennifer Wilson', organization: 'TechCorp', feeType: 'online_dom', feeTypeLabel: 'Online Domestic', channel: 'Online', bookingType: 'Air', fee: 95, reference: 'QF4356' },
      { id: 2, date: '2025-10-19', traveller: 'Sophie Martinez', organization: 'TechCorp', feeType: 'online_intl', feeTypeLabel: 'Online International', channel: 'Online', bookingType: 'Air', fee: 125, reference: 'SQ231' },
      { id: 3, date: '2025-10-17', traveller: 'David Anderson', organization: 'TechCorp', feeType: 'offline_dom', feeTypeLabel: 'Offline Domestic', channel: 'Offline', bookingType: 'Air', fee: 145, reference: 'VA823' },
      { id: 4, date: '2025-10-15', traveller: 'Emily White', organization: 'Retail Solutions', feeType: 'online_intl', feeTypeLabel: 'Online International', channel: 'Online', bookingType: 'Air', fee: 135, reference: 'NZ145' },
      { id: 5, date: '2025-10-14', traveller: 'Robert Thompson', organization: 'TechCorp', feeType: 'change', feeTypeLabel: 'Change Fee', channel: 'Offline', bookingType: 'Air', fee: 45, reference: 'QF25' }
    ]
    
  } finally {
    loading.value = false
  }
}

const createCharts = () => {
  if (feeTypeChart) feeTypeChart.destroy()
  if (channelChart) channelChart.destroy()
  if (trendChart) trendChart.destroy()

  if (feeTypeChartCanvas.value) {
    const ctx = feeTypeChartCanvas.value.getContext('2d')
    feeTypeChart = new ChartJS(ctx, {
      type: 'bar',
      data: {
        labels: feeTypeData.value.map(d => d.type),
        datasets: [{
          label: 'Fees',
          data: feeTypeData.value.map(d => d.amount),
          backgroundColor: ['#3B82F6', '#8B5CF6', '#F59E0B', '#EF4444', '#10B981'],
          borderRadius: 8
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (context) => `Fees: ${formatCurrency(context.parsed.y)}`
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: { callback: (value) => `$${value / 1000}k` }
          }
        }
      }
    })
  }

  if (channelChartCanvas.value) {
    const ctx = channelChartCanvas.value.getContext('2d')
    channelChart = new ChartJS(ctx, {
      type: 'doughnut',
      data: {
        labels: channelData.value.map(d => d.channel),
        datasets: [{
          data: channelData.value.map(d => d.bookings),
          backgroundColor: ['#10B981', '#6B7280'],
          borderWidth: 2,
          borderColor: '#fff'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: {
            position: 'bottom',
            labels: { padding: 15, font: { size: 12 } }
          },
          tooltip: {
            callbacks: {
              label: (context) => {
                const label = context.label
                const value = context.parsed
                const percentage = channelData.value[context.dataIndex].percentage
                return `${label}: ${value} (${percentage}%)`
              }
            }
          }
        }
      }
    })
  }

  if (trendChartCanvas.value) {
    const ctx = trendChartCanvas.value.getContext('2d')
    trendChart = new ChartJS(ctx, {
      type: 'line',
      data: {
        labels: trendData.value.map(d => d.month),
        datasets: [{
          label: 'Monthly Fees',
          data: trendData.value.map(d => d.fees),
          borderColor: '#3B82F6',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          tension: 0.4,
          fill: true,
          pointRadius: 4,
          pointHoverRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (context) => `Fees: ${formatCurrency(context.parsed.y)}`
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: { callback: (value) => `$${value / 1000}k` }
          }
        }
      }
    })
  }
}

const activeFilterCount = computed(() => {
  let count = 0
  if (filters.value.feeType) count++
  if (filters.value.channel) count++
  if (filters.value.dateFrom) count++
  if (filters.value.dateTo) count++
  return count
})

const formatCurrency = (value) => {
  return new Intl.NumberFormat('en-AU', {
    style: 'currency',
    currency: 'AUD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(value)
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('en-AU', {
    day: '2-digit',
    month: 'short',
    year: 'numeric'
  })
}

const getFeeTypeBadgeClass = (type) => {
  const classes = {
    online_dom: 'bg-blue-100 text-blue-800',
    online_intl: 'bg-purple-100 text-purple-800',
    offline_dom: 'bg-orange-100 text-orange-800',
    offline_intl: 'bg-red-100 text-red-800',
    change: 'bg-yellow-100 text-yellow-800',
    refund: 'bg-gray-100 text-gray-800'
  }
  return classes[type] || classes.online_dom
}

const clearFilters = () => {
  filters.value = { feeType: '', channel: '', dateFrom: '', dateTo: '' }
}

const viewTransaction = (transaction) => {
  console.log('View transaction:', transaction)
}

const exportReport = () => {
  console.log('Exporting service fees report...')
}

onMounted(async () => {
  await fetchServiceFeesData()
  setTimeout(() => {
    createCharts()
  }, 150)
})

onBeforeUnmount(() => {
  if (feeTypeChart) feeTypeChart.destroy()
  if (channelChart) channelChart.destroy()
  if (trendChart) trendChart.destroy()
})
</script>
<template>
  <div class="min-h-screen bg-gray-50 p-6">
    <!-- Header -->
    <div class="mb-6">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-3xl font-bold text-gray-900">Accommodation Dashboard</h1>
          <p class="text-gray-600 mt-1">Hotel spend and booking analysis</p>
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
      <p class="mt-4 text-gray-600">Loading accommodation data...</p>
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
              <p class="text-gray-600 text-sm">Total Accommodation Spend</p>
              <p class="text-3xl font-bold text-gray-900 mt-1">
                {{ formatCurrency(stats.totalSpend) }}
              </p>
            </div>
            <div class="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
              <svg class="w-6 h-6 text-blue-600" fill="currentColor" viewBox="0 0 24 24">
                <path d="M19,7H11V14H3V5H1V20H3V17H21V20H23V11A4,4 0 0,0 19,7M7,13A3,3 0 0,0 10,10A3,3 0 0,0 7,7A3,3 0 0,0 4,10A3,3 0 0,0 7,13Z" />
              </svg>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-2xl shadow-sm p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-gray-600 text-sm">Total Hotel Nights</p>
              <p class="text-3xl font-bold text-gray-900 mt-1">{{ stats.totalNights }}</p>
            </div>
            <div class="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center">
              <svg class="w-6 h-6 text-purple-600" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12,20A8,8 0 0,1 4,12A8,8 0 0,1 12,4A8,8 0 0,1 20,12A8,8 0 0,1 12,20M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,12.5A1.5,1.5 0 0,1 10.5,11A1.5,1.5 0 0,1 12,9.5A1.5,1.5 0 0,1 13.5,11A1.5,1.5 0 0,1 12,12.5M12,7.2C9.9,7.2 8.2,8.9 8.2,11C8.2,14 12,17.5 12,17.5C12,17.5 15.8,14 15.8,11C15.8,8.9 14.1,7.2 12,7.2Z" />
              </svg>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-2xl shadow-sm p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-gray-600 text-sm">Avg. Nightly Rate</p>
              <p class="text-3xl font-bold text-gray-900 mt-1">
                {{ formatCurrency(stats.avgNightlyRate) }}
              </p>
            </div>
            <div class="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center">
              <svg class="w-6 h-6 text-green-600" fill="currentColor" viewBox="0 0 24 24">
                <path d="M7,15H9C9,16.08 10.37,17 12,17C13.63,17 15,16.08 15,15C15,13.9 13.96,13.5 11.76,12.97C9.64,12.44 7,11.78 7,9C7,7.21 8.47,5.69 10.5,5.18V3H13.5V5.18C15.53,5.69 17,7.21 17,9H15C15,7.92 13.63,7 12,7C10.37,7 9,7.92 9,9C9,10.1 10.04,10.5 12.24,11.03C14.36,11.56 17,12.22 17,15C17,16.79 15.53,18.31 13.5,18.82V21H10.5V18.82C8.47,18.31 7,16.79 7,15Z" />
              </svg>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-2xl shadow-sm p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-gray-600 text-sm">Hotel Attachment Rate</p>
              <p class="text-3xl font-bold text-gray-900 mt-1">{{ stats.attachmentRate }}%</p>
              <p class="text-xs text-gray-500 mt-1">{{ stats.hotelNightsBooked }}/{{ stats.potentialNights }} nights</p>
            </div>
            <div class="w-12 h-12 rounded-xl flex items-center justify-center"
                 :class="getAttachmentRateClass(stats.attachmentRate)">
              <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                <path d="M9,20.42L2.79,14.21L5.62,11.38L9,14.77L18.88,4.88L21.71,7.71L9,20.42Z" />
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
            <p class="text-sm text-gray-600">Refine your accommodation data</p>
            <button
              @click="clearFilters"
              class="text-sm text-blue-600 hover:text-blue-700 font-medium"
            >
              Clear All
            </button>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">City</label>
              <select
                v-model="filters.city"
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">All Cities</option>
                <option value="Sydney">Sydney</option>
                <option value="Melbourne">Melbourne</option>
                <option value="Brisbane">Brisbane</option>
                <option value="Perth">Perth</option>
                <option value="Singapore">Singapore</option>
                <option value="Auckland">Auckland</option>
              </select>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">Hotel Chain</label>
              <select
                v-model="filters.hotelChain"
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">All Chains</option>
                <option value="Hilton">Hilton</option>
                <option value="Marriott">Marriott</option>
                <option value="Hyatt">Hyatt</option>
                <option value="InterContinental">InterContinental</option>
                <option value="Accor">Accor</option>
              </select>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">Check-in From</label>
              <input
                type="date"
                v-model="filters.dateFrom"
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">Check-in To</label>
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
          <h2 class="text-lg font-semibold text-gray-900 mb-4">Spend by Hotel Chain</h2>
          <canvas ref="chainChartCanvas"></canvas>
        </div>

        <div class="bg-white rounded-2xl shadow-sm p-6">
          <h2 class="text-lg font-semibold text-gray-900 mb-4">Bookings by City</h2>
          <canvas ref="cityChartCanvas"></canvas>
        </div>
      </div>

      <div class="bg-white rounded-2xl shadow-sm p-6 mb-6">
        <h2 class="text-lg font-semibold text-gray-900 mb-4">Average Nightly Rate by City</h2>
        <canvas ref="rateChartCanvas"></canvas>
      </div>

      <!-- Top Hotels Table -->
      <div class="bg-white rounded-2xl shadow-sm overflow-hidden mb-6">
        <div class="p-6 border-b border-gray-200">
          <h2 class="text-lg font-semibold text-gray-900">Top 10 Hotels</h2>
          <p class="text-sm text-gray-600 mt-1">Most frequently booked properties</p>
        </div>

        <div class="overflow-x-auto">
          <table class="w-full">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Rank</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Hotel</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">City</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Chain</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Bookings</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Nights</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Avg. Rate</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="(hotel, index) in topHotels" :key="index" class="hover:bg-gray-50">
                <td class="px-6 py-4">
                  <span :class="getRankBadgeClass(index + 1)" class="inline-flex items-center justify-center w-8 h-8 rounded-full font-semibold">
                    {{ index + 1 }}
                  </span>
                </td>
                <td class="px-6 py-4 font-medium text-gray-900">{{ hotel.name }}</td>
                <td class="px-6 py-4 text-sm text-gray-900">{{ hotel.city }}</td>
                <td class="px-6 py-4">
                  <span class="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">
                    {{ hotel.chain }}
                  </span>
                </td>
                <td class="px-6 py-4 text-sm">{{ hotel.bookings }}</td>
                <td class="px-6 py-4 text-sm">{{ hotel.totalNights }}</td>
                <td class="px-6 py-4 text-sm font-medium">{{ formatCurrency(hotel.totalSpend) }}</td>
                <td class="px-6 py-4 text-sm">{{ formatCurrency(hotel.avgRate) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Destinations Analysis -->
      <div class="bg-white rounded-2xl shadow-sm overflow-hidden">
        <div class="p-6 border-b border-gray-200">
          <h2 class="text-lg font-semibold text-gray-900">Destinations Analysis</h2>
          <p class="text-sm text-gray-600 mt-1">Accommodation metrics by destination</p>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Destination</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Room Nights</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total Spend</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Avg Rate</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Max Rate</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Min Rate</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Attachment Rate</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="destination in destinationsData" :key="destination.city" class="hover:bg-gray-50">
                <td class="px-6 py-4">
                  <div class="flex items-center gap-2">
                    <svg class="w-4 h-4 text-gray-400" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M12,11.5A2.5,2.5 0 0,1 9.5,9A2.5,2.5 0 0,1 12,6.5A2.5,2.5 0 0,1 14.5,9A2.5,2.5 0 0,1 12,11.5M12,2A7,7 0 0,0 5,9C5,14.25 12,22 12,22C12,22 19,14.25 19,9A7,7 0 0,0 12,2Z" />
                    </svg>
                    <span class="font-medium text-gray-900">{{ destination.city }}</span>
                    <span class="text-xs text-gray-500">{{ destination.country }}</span>
                  </div>
                </td>
                <td class="px-6 py-4 text-sm text-gray-900">{{ destination.roomNights }}</td>
                <td class="px-6 py-4 text-sm font-medium text-gray-900">{{ formatCurrency(destination.totalSpend) }}</td>
                <td class="px-6 py-4 text-sm text-gray-900">{{ formatCurrency(destination.avgRate) }}</td>
                <td class="px-6 py-4 text-sm text-gray-900">{{ formatCurrency(destination.maxRate) }}</td>
                <td class="px-6 py-4 text-sm text-gray-900">{{ formatCurrency(destination.minRate) }}</td>
                <td class="px-6 py-4">
                  <div class="flex items-center gap-2">
                    <span class="text-sm font-medium text-gray-900">{{ destination.attachmentRate }}%</span>
                    <span class="px-2 py-1 text-xs font-medium rounded-full"
                          :class="getAttachmentRateBadgeClass(destination.attachmentRate)">
                      {{ getAttachmentRateLabel(destination.attachmentRate) }}
                    </span>
                  </div>
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
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
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

ChartJS.register(CategoryScale, LinearScale, BarElement, BarController, ArcElement, DoughnutController, Title, Tooltip, Legend)

const loading = ref(true)
const error = ref(null)
const chainChartCanvas = ref(null)
const cityChartCanvas = ref(null)
const rateChartCanvas = ref(null)
let chainChart = null
let cityChart = null
let rateChart = null

const filters = ref({ city: '', hotelChain: '', dateFrom: '', dateTo: '' })
const filtersOpen = ref(false)

const stats = ref({ totalSpend: 0, totalNights: 0, avgNightlyRate: 0, attachmentRate: 0, hotelNightsBooked: 0, potentialNights: 0 })
const chainData = ref([])
const cityData = ref([])
const rateData = ref([])
const topHotels = ref([])
const destinationsData = ref([])

const fetchAccommodationData = async () => {
  try {
    loading.value = true
    
    // Overall stats including attachment rate
    stats.value = { 
      totalSpend: 98500, 
      totalNights: 156, 
      avgNightlyRate: 285,
      attachmentRate: 67,  // 67% attachment rate overall
      hotelNightsBooked: 156,
      potentialNights: 233  // Based on air travel requiring overnight stays
    }
    
    chainData.value = [
      { chain: 'Hilton', spend: 28500 },
      { chain: 'Marriott', spend: 24800 },
      { chain: 'Hyatt', spend: 18200 },
      { chain: 'InterContinental', spend: 15600 },
      { chain: 'Accor', spend: 11400 }
    ]
    
    cityData.value = [
      { city: 'Melbourne', bookings: 42 },
      { city: 'Sydney', bookings: 38 },
      { city: 'Singapore', bookings: 28 },
      { city: 'Brisbane', bookings: 18 },
      { city: 'Auckland', bookings: 12 }
    ]
    
    rateData.value = [
      { city: 'Sydney', avgRate: 320 },
      { city: 'Singapore', avgRate: 298 },
      { city: 'Melbourne', avgRate: 275 },
      { city: 'Brisbane', avgRate: 245 },
      { city: 'Perth', avgRate: 235 },
      { city: 'Auckland', avgRate: 268 }
    ]
    
    topHotels.value = [
      { name: 'Hilton Sydney', city: 'Sydney', chain: 'Hilton', bookings: 18, totalNights: 42, totalSpend: 15400, avgRate: 367 },
      { name: 'Marriott Melbourne', city: 'Melbourne', chain: 'Marriott', bookings: 16, totalNights: 38, totalSpend: 12800, avgRate: 337 },
      { name: 'Marina Bay Sands', city: 'Singapore', chain: 'Independent', bookings: 14, totalNights: 35, totalSpend: 14500, avgRate: 414 },
      { name: 'Hyatt Regency Sydney', city: 'Sydney', chain: 'Hyatt', bookings: 12, totalNights: 28, totalSpend: 9500, avgRate: 339 },
      { name: 'InterContinental Melbourne', city: 'Melbourne', chain: 'InterContinental', bookings: 10, totalNights: 24, totalSpend: 8200, avgRate: 342 },
      { name: 'Sofitel Brisbane', city: 'Brisbane', chain: 'Accor', bookings: 9, totalNights: 22, totalSpend: 6800, avgRate: 309 },
      { name: 'Hilton Auckland', city: 'Auckland', chain: 'Hilton', bookings: 8, totalNights: 18, totalSpend: 5400, avgRate: 300 },
      { name: 'Shangri-La Sydney', city: 'Sydney', chain: 'Shangri-La', bookings: 7, totalNights: 16, totalSpend: 6200, avgRate: 388 },
      { name: 'Crown Towers Melbourne', city: 'Melbourne', chain: 'Crown', bookings: 6, totalNights: 14, totalSpend: 5800, avgRate: 414 },
      { name: 'Swissôtel Singapore', city: 'Singapore', chain: 'Accor', bookings: 5, totalNights: 12, totalSpend: 4200, avgRate: 350 }
    ]
    
    // Destinations with attachment rates
    destinationsData.value = [
      { 
        city: 'Sydney', 
        country: 'Australia',
        roomNights: 52, 
        totalSpend: 18200, 
        avgRate: 350, 
        maxRate: 425, 
        minRate: 285,
        attachmentRate: 72  // Excellent - well above 60%
      },
      { 
        city: 'Melbourne', 
        country: 'Australia',
        roomNights: 48, 
        totalSpend: 14600, 
        avgRate: 304, 
        maxRate: 385, 
        minRate: 245,
        attachmentRate: 68  // Excellent - above 60%
      },
      { 
        city: 'Singapore', 
        country: 'Singapore',
        roomNights: 35, 
        totalSpend: 14500, 
        avgRate: 414, 
        maxRate: 550, 
        minRate: 320,
        attachmentRate: 42  // Good - above 30% average
      },
      { 
        city: 'Brisbane', 
        country: 'Australia',
        roomNights: 28, 
        totalSpend: 7800, 
        avgRate: 279, 
        maxRate: 340, 
        minRate: 220,
        attachmentRate: 55  // Good - approaching excellent
      },
      { 
        city: 'Auckland', 
        country: 'New Zealand',
        roomNights: 22, 
        totalSpend: 6400, 
        avgRate: 291, 
        maxRate: 360, 
        minRate: 235,
        attachmentRate: 18  // Critical - well below 20%!
      },
      { 
        city: 'Perth', 
        country: 'Australia',
        roomNights: 18, 
        totalSpend: 4800, 
        avgRate: 267, 
        maxRate: 320, 
        minRate: 215,
        attachmentRate: 25  // Poor - below 30% average
      }
    ]
    
  } finally {
    loading.value = false
  }
}

const createCharts = () => {
  if (chainChart) chainChart.destroy()
  if (cityChart) cityChart.destroy()
  if (rateChart) rateChart.destroy()

  if (chainChartCanvas.value) {
    const ctx = chainChartCanvas.value.getContext('2d')
    chainChart = new ChartJS(ctx, {
      type: 'bar',
      data: {
        labels: chainData.value.map(d => d.chain),
        datasets: [{
          label: 'Spend',
          data: chainData.value.map(d => d.spend),
          backgroundColor: '#3B82F6',
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
              label: (context) => `Spend: ${formatCurrency(context.parsed.y)}`
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: { callback: (value) => `${value / 1000}k` }
          }
        }
      }
    })
  }

  if (cityChartCanvas.value) {
    const ctx = cityChartCanvas.value.getContext('2d')
    cityChart = new ChartJS(ctx, {
      type: 'doughnut',
      data: {
        labels: cityData.value.map(d => d.city),
        datasets: [{
          data: cityData.value.map(d => d.bookings),
          backgroundColor: ['#3B82F6', '#8B5CF6', '#F59E0B', '#EF4444', '#10B981'],
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
          }
        }
      }
    })
  }

  if (rateChartCanvas.value) {
    const ctx = rateChartCanvas.value.getContext('2d')
    rateChart = new ChartJS(ctx, {
      type: 'bar',
      data: {
        labels: rateData.value.map(d => d.city),
        datasets: [{
          label: 'Avg. Nightly Rate',
          data: rateData.value.map(d => d.avgRate),
          backgroundColor: '#8B5CF6',
          borderRadius: 8
        }]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (context) => `Avg. Rate: ${formatCurrency(context.parsed.x)}`
            }
          }
        },
        scales: {
          x: {
            beginAtZero: true,
            ticks: { callback: (value) => `${value}` }
          }
        }
      }
    })
  }
}

const activeFilterCount = computed(() => {
  let count = 0
  if (filters.value.city) count++
  if (filters.value.hotelChain) count++
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

const getRankBadgeClass = (rank) => {
  if (rank === 1) return 'bg-yellow-100 text-yellow-800'
  if (rank === 2) return 'bg-gray-200 text-gray-800'
  if (rank === 3) return 'bg-orange-100 text-orange-800'
  return 'bg-gray-100 text-gray-700'
}

const getAttachmentRateClass = (rate) => {
  if (rate >= 60) return 'bg-green-100 text-green-600'
  if (rate >= 30) return 'bg-orange-100 text-orange-600'
  return 'bg-red-100 text-red-600'
}

const getAttachmentRateBadgeClass = (rate) => {
  if (rate >= 60) return 'bg-green-100 text-green-800'
  if (rate >= 30) return 'bg-orange-100 text-orange-800'
  return 'bg-red-100 text-red-800'
}

const getAttachmentRateLabel = (rate) => {
  if (rate >= 60) return 'Excellent'
  if (rate >= 30) return 'Good'
  if (rate >= 20) return 'Poor'
  return 'Critical'
}

const clearFilters = () => {
  filters.value = { city: '', hotelChain: '', dateFrom: '', dateTo: '' }
}

const viewBooking = (booking) => {
  console.log('View booking:', booking)
}

const exportReport = () => {
  console.log('Exporting accommodation report...')
}

onMounted(async () => {
  await fetchAccommodationData()
  setTimeout(() => {
    createCharts()
  }, 150)
})

onBeforeUnmount(() => {
  if (chainChart) chainChart.destroy()
  if (cityChart) cityChart.destroy()
  if (rateChart) rateChart.destroy()
})
</script>
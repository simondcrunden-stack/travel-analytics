<template>
  <div class="space-y-6">
    <!-- Header -->
    <div>
      <h1 class="text-2xl font-bold text-gray-900">Bookings</h1>
      <p class="mt-1 text-sm text-gray-500">
        Complete list of all travel bookings
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

    <!-- Summary Cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <!-- Total Bookings -->
      <div class="bg-white rounded-xl shadow-sm p-6">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-gray-600">Total Bookings</p>
            <p class="text-3xl font-bold text-gray-900 mt-2">{{ sortedBookings.length }}</p>
          </div>
          <div class="bg-blue-100 p-3 rounded-full">
            <svg class="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
          </div>
        </div>
      </div>

      <!-- Total Spend -->
      <div class="bg-white rounded-xl shadow-sm p-6">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-gray-600">Total Spend</p>
            <p class="text-3xl font-bold text-gray-900 mt-2">{{ formatCurrency(totalSpend) }}</p>
          </div>
          <div class="bg-green-100 p-3 rounded-full">
            <svg class="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
        </div>
      </div>

      <!-- Total Emissions -->
      <div class="bg-white rounded-xl shadow-sm p-6">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-gray-600">Carbon Emissions</p>
            <p class="text-3xl font-bold text-gray-900 mt-2">{{ totalEmissions }}</p>
            <p class="text-xs text-gray-500 mt-1">kg CO₂</p>
          </div>
          <div class="bg-emerald-100 p-3 rounded-full">
            <svg class="w-6 h-6 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
        </div>
      </div>

      <!-- Compliance Rate -->
      <div class="bg-white rounded-xl shadow-sm p-6">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-gray-600">Compliance Rate</p>
            <p class="text-3xl font-bold text-gray-900 mt-2">{{ complianceRate }}%</p>
          </div>
          <div class="bg-purple-100 p-3 rounded-full">
            <svg class="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
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
        @click="loadBookings" 
        class="mt-2 text-sm text-red-600 hover:text-red-800 underline"
      >
        Try Again
      </button>
    </div>

    <!-- Bookings Table -->
    <div v-else class="bg-white rounded-xl shadow-sm overflow-hidden">
      <!-- Table Controls -->
      <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
        <div class="flex items-center space-x-4">
          <span class="text-sm text-gray-700">
            Showing {{ startIndex + 1 }}-{{ Math.min(endIndex, sortedBookings.length) }} of {{ sortedBookings.length }} bookings
          </span>
        </div>
        <div class="flex items-center space-x-2">
          <label class="text-sm text-gray-700">Per page:</label>
          <select 
            v-model="itemsPerPage" 
            class="border border-gray-300 rounded-md px-2 py-1 text-sm"
          >
            <option :value="10">10</option>
            <option :value="25">25</option>
            <option :value="50">50</option>
            <option :value="100">100</option>
          </select>
        </div>
      </div>

      <!-- Table -->
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th 
                @click="sortBy('agent_booking_reference')"
                class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
              >
                Reference
                <span v-if="sortField === 'agent_booking_reference'">
                  {{ sortDirection === 'asc' ? '↑' : '↓' }}
                </span>
              </th>
              <th 
                @click="sortBy('traveller_name')"
                class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
              >
                Traveller
                <span v-if="sortField === 'traveller_name'">
                  {{ sortDirection === 'asc' ? '↑' : '↓' }}
                </span>
              </th>
              <th 
                @click="sortBy('travel_date')"
                class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
              >
                Travel Date
                <span v-if="sortField === 'travel_date'">
                  {{ sortDirection === 'asc' ? '↑' : '↓' }}
                </span>
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Duration
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Destinations
              </th>
              <th 
                @click="sortBy('total_amount')"
                class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
              >
                Amount
                <span v-if="sortField === 'total_amount'">
                  {{ sortDirection === 'asc' ? '↑' : '↓' }}
                </span>
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Carbon
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Compliance
              </th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <template v-for="booking in paginatedBookings" :key="booking.id">
              <!-- Main booking row - clickable -->
              <tr 
                @click="toggleBooking(booking.id)" 
                class="hover:bg-gray-50 cursor-pointer transition-colors"
                :class="{ 'bg-blue-50': isExpanded(booking.id) }"
              >
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  <div class="flex items-center">
                    <span class="mdi mr-2 text-gray-400" :class="isExpanded(booking.id) ? 'mdi-chevron-down' : 'mdi-chevron-right'"></span>
                    {{ booking.agent_booking_reference }}
                  </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {{ booking.traveller_name }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {{ formatDate(booking.travel_date) }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {{ getDuration(booking) }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {{ getDestinations(booking) }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {{ formatCurrency(booking.total_amount) }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {{ getCarbonEmissions(booking) }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span :class="getComplianceClass(booking.policy_compliant)">
                    {{ booking.policy_compliant !== undefined ? (booking.policy_compliant ? 'Compliant' : 'Non-Compliant') : 'N/A' }}
                  </span>
                </td>
              </tr>
              
              <!-- Expanded detail row -->
              <tr v-if="isExpanded(booking.id)" class="bg-gray-50">
                <td colspan="8" class="px-6 py-4">
                  <BookingDetails :booking="booking" />
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div class="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
        <button
          @click="currentPage > 1 && currentPage--"
          :disabled="currentPage === 1"
          class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Previous
        </button>
        <span class="text-sm text-gray-700">
          Page {{ currentPage }} of {{ totalPages }}
        </span>
        <button
          @click="currentPage < totalPages && currentPage++"
          :disabled="currentPage === totalPages"
          class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Next
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import bookingService from '@/services/bookingService'
import UniversalFilters from '@/components/common/UniversalFilters.vue'
import BookingDetails from '@/components/common/BookingDetails.vue'

// State
const bookings = ref([])
const summary = ref({
  total_spend: 0,
  total_emissions: 0,
  compliance_rate: 0,
  booking_count: 0
})
const loading = ref(true)
const error = ref(null)
const currentPage = ref(1)
const itemsPerPage = ref(25)
const sortField = ref('travel_date')
const sortDirection = ref('desc')
const currentFilters = ref({})
const expandedBookings = ref(new Set())

// Methods
const loadBookings = async (filters = {}) => {
  try {
    loading.value = true
    error.value = null

    console.log('🌐 [BookingsView] Loading bookings with filters:', filters)

    const data = await bookingService.getBookings(filters)

    // API returns { results: [...], summary: {...} } structure
    bookings.value = data.results || []

    // Extract summary statistics from backend
    if (data.summary) {
      summary.value = data.summary
      console.log('📊 [BookingsView] Summary statistics from backend:', summary.value)
    }

    console.log('✅ [BookingsView] Loaded', bookings.value.length, 'bookings')
  } catch (err) {
    console.error('❌ [BookingsView] Error loading bookings:', err)
    error.value = 'Failed to load bookings. Please try again.'
  } finally {
    loading.value = false
  }
}

const handleFiltersChanged = async (filters) => {
  console.log('📥 [BookingsView] Received filters:', filters)
  currentFilters.value = filters
  currentPage.value = 1
  // Load bookings with new filters from backend
  // Backend handles ALL filtering logic - no client-side filtering needed!
  await loadBookings(filters)
}

// Computed - Sorted bookings (backend does filtering, we just sort for display)
const sortedBookings = computed(() => {
  const sorted = [...bookings.value]

  // Apply sorting
  sorted.sort((a, b) => {
    let aVal = a[sortField.value]
    let bVal = b[sortField.value]

    // Handle numeric values
    if (sortField.value === 'total_amount') {
      aVal = parseFloat(aVal) || 0
      bVal = parseFloat(bVal) || 0
    }

    if (sortDirection.value === 'asc') {
      return aVal > bVal ? 1 : -1
    } else {
      return aVal < bVal ? 1 : -1
    }
  })

  return sorted
})

// Use summary statistics from backend (calculated on filtered data)
const totalSpend = computed(() => {
  return summary.value.total_spend || 0
})

const totalEmissions = computed(() => {
  return summary.value.total_emissions || 0
})

const complianceRate = computed(() => {
  return summary.value.compliance_rate || 0
})

const totalPages = computed(() => {
  return Math.ceil(sortedBookings.value.length / itemsPerPage.value)
})

const startIndex = computed(() => {
  return (currentPage.value - 1) * itemsPerPage.value
})

const endIndex = computed(() => {
  return currentPage.value * itemsPerPage.value
})

const paginatedBookings = computed(() => {
  return sortedBookings.value.slice(startIndex.value, endIndex.value)
})

// Table helpers
const sortBy = (field) => {
  if (sortField.value === field) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortField.value = field
    sortDirection.value = 'asc'
  }
}

const toggleBooking = (bookingId) => {
  if (expandedBookings.value.has(bookingId)) {
    expandedBookings.value.delete(bookingId)
  } else {
    expandedBookings.value.add(bookingId)
  }
  // Force reactivity update
  expandedBookings.value = new Set(expandedBookings.value)
}

const isExpanded = (bookingId) => {
  return expandedBookings.value.has(bookingId)
}

const getDuration = (booking) => {
  if (!booking.return_date) return '-'
  const travel = new Date(booking.travel_date)
  const returnDate = new Date(booking.return_date)
  const days = Math.ceil((returnDate - travel) / (1000 * 60 * 60 * 24))
  return days === 0 ? 'Same day' : `${days} day${days > 1 ? 's' : ''}`
}

const getDestinations = (booking) => {
  // Check air bookings first
  if (booking.air_bookings && booking.air_bookings.length > 0) {
    const airBooking = booking.air_bookings[0]
    const origin = airBooking.origin_airport_iata_code
    const destination = airBooking.destination_airport_iata_code
    
    // If multiple air bookings, show "Multi-city"
    if (booking.air_bookings.length > 1) {
      return 'Multi-city'
    }
    
    return `${origin} → ${destination}`
  }
  
  // Check accommodation bookings
  if (booking.accommodation_bookings && booking.accommodation_bookings.length > 0) {
    const cities = booking.accommodation_bookings.map(h => h.city).filter(c => c)
    if (cities.length > 1) {
      return cities.slice(0, 2).join(', ') + (cities.length > 2 ? '...' : '')
    }
    return cities[0] || '-'
  }
  
  // Check car hire bookings
  if (booking.car_hire_bookings && booking.car_hire_bookings.length > 0) {
    const car = booking.car_hire_bookings[0]
    return car.pickup_city || '-'
  }
  
  return '-'
}

const getCarbonEmissions = (booking) => {
  let totalCarbon = 0
  
  // Sum carbon from all air bookings
  if (booking.air_bookings && booking.air_bookings.length > 0) {
    booking.air_bookings.forEach(airBooking => {
      if (airBooking.total_carbon_kg) {
        totalCarbon += parseFloat(airBooking.total_carbon_kg)
      }
    })
  }
  
  if (totalCarbon > 0) {
    // Format large values as tonnes
    if (totalCarbon >= 1000) {
      return `${(totalCarbon / 1000).toFixed(1)} t`
    }
    return `${Math.round(totalCarbon)} kg`
  }
  
  return '-'
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

const getComplianceClass = (isCompliant) => {
  if (isCompliant === true) {
    return 'px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800'
  } else if (isCompliant === false) {
    return 'px-2 py-1 text-xs font-medium rounded-full bg-red-100 text-red-800'
  } else {
    // Undefined or null - show gray for N/A
    return 'px-2 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-800'
  }
}

// Lifecycle
onMounted(() => {
  loadBookings()
})
</script>
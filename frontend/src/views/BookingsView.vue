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
            <p class="text-3xl font-bold text-gray-900 mt-2">{{ filteredBookings.length }}</p>
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
            Showing {{ startIndex + 1 }}-{{ Math.min(endIndex, filteredBookings.length) }} of {{ filteredBookings.length }} bookings
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
                @click="sortBy('booking_type')"
                class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
              >
                Type
                <span v-if="sortField === 'booking_type'">
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
              <th 
                @click="sortBy('status')"
                class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
              >
                Status
                <span v-if="sortField === 'status'">
                  {{ sortDirection === 'asc' ? '↑' : '↓' }}
                </span>
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Compliance
              </th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="booking in paginatedBookings" :key="booking.id" class="hover:bg-gray-50">
              <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                {{ booking.agent_booking_reference }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
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
                <span :class="getStatusClass(booking.status)">
                  {{ booking.status }}
                </span>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <span :class="getComplianceClass(booking.policy_compliant)">
                  {{ booking.policy_compliant ? '✓ Compliant' : '✗ Non-compliant' }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div class="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
        <button
          @click="currentPage--"
          :disabled="currentPage === 1"
          class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Previous
        </button>
        <div class="flex items-center space-x-2">
          <span class="text-sm text-gray-700">
            Page {{ currentPage }} of {{ totalPages }}
          </span>
        </div>
        <button
          @click="currentPage++"
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
import UniversalFilters from '@/components/common/UniversalFilters.vue'
import bookingService from '@/services/bookingService'

// State
const loading = ref(true)
const error = ref(null)
const bookings = ref([])
const currentFilters = ref({})

// Pagination
const currentPage = ref(1)
const itemsPerPage = ref(25)

// Sorting
const sortField = ref('travel_date')
const sortDirection = ref('desc')

// Methods
const loadBookings = async () => {
  loading.value = true
  error.value = null
  
  try {
    console.log('Loading bookings...')
    
    // Build API params from filters
    const params = {}
    
    // Date filters
    if (currentFilters.value.dateFrom) {
      params.travel_date__gte = currentFilters.value.dateFrom
    }
    if (currentFilters.value.dateTo) {
      params.travel_date__lte = currentFilters.value.dateTo
    }
    
    // Other filters
    if (currentFilters.value.traveller) {
      params.traveller = currentFilters.value.traveller
    }
    if (currentFilters.value.organization) {
      params.organization = currentFilters.value.organization
    }
    if (currentFilters.value.status) {
      params.status = currentFilters.value.status
    }
    
    console.log('Fetching bookings with params:', params)
    
    // Load all bookings (we'll filter destinations client-side)
    const response = await bookingService.getBookings({ ...params, limit: 1000 })
    const allBookings = response.results || response
    
    console.log('Loaded bookings:', allBookings.length)
    bookings.value = allBookings
    
  } catch (err) {
    console.error('Error loading bookings:', err)
    error.value = 'Failed to load bookings. Please try again.'
  } finally {
    loading.value = false
  }
}

const handleFiltersChanged = (filters) => {
  console.log('Filters changed:', filters)
  currentFilters.value = filters
  currentPage.value = 1 // Reset to first page
  loadBookings()
}

// Client-side destination filtering
const filteredBookings = computed(() => {
  let filtered = [...bookings.value]
  
  // Apply destination filters (client-side)
  if (currentFilters.value.destinationPreset) {
    filtered = applyDestinationPreset(filtered, currentFilters.value.destinationPreset)
  }
  
  if (currentFilters.value.country) {
    filtered = filtered.filter(booking => {
      if (booking.booking_type === 'AIR' && booking.air_details) {
        return booking.air_details.origin_country === currentFilters.value.country ||
               booking.air_details.destination_country === currentFilters.value.country
      }
      return true
    })
  }
  
  if (currentFilters.value.city) {
    const citySearch = currentFilters.value.city.toLowerCase()
    filtered = filtered.filter(booking => {
      if (booking.booking_type === 'AIR' && booking.air_details) {
        return booking.air_details.origin_airport_code?.toLowerCase().includes(citySearch) ||
               booking.air_details.destination_airport_code?.toLowerCase().includes(citySearch)
      }
      if (booking.booking_type === 'HOTEL' && booking.accommodation_details) {
        return booking.accommodation_details.city?.toLowerCase().includes(citySearch)
      }
      if (booking.booking_type === 'CAR' && booking.car_hire_details) {
        return booking.car_hire_details.pickup_location?.toLowerCase().includes(citySearch)
      }
      return false
    })
  }
  
  // Apply sorting
  filtered.sort((a, b) => {
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
  
  return filtered
})

const applyDestinationPreset = (bookings, preset) => {
  const australianAirports = ['SYD', 'MEL', 'BNE', 'PER', 'ADL', 'CNS', 'DRW', 'HBA', 'CBR', 'OOL']
  const usAirports = ['LAX', 'SFO', 'JFK', 'ORD', 'DFW', 'ATL', 'MIA', 'SEA', 'DEN', 'LAS']
  const nzAirports = ['AKL', 'CHC', 'WLG', 'ZQN']
  const asianAirports = ['SIN', 'HKG', 'BKK', 'NRT', 'ICN', 'KUL', 'MNL', 'CGK']
  
  return bookings.filter(booking => {
    if (booking.booking_type !== 'AIR' || !booking.air_details) return true
    
    const origin = booking.air_details.origin_airport_code
    const dest = booking.air_details.destination_airport_code
    
    switch (preset) {
      case 'within_australia':
        return australianAirports.includes(origin) && australianAirports.includes(dest)
      case 'outside_australia':
        return !australianAirports.includes(origin) || !australianAirports.includes(dest)
      case 'aus_usa':
        return (australianAirports.includes(origin) && usAirports.includes(dest)) ||
               (usAirports.includes(origin) && australianAirports.includes(dest))
      case 'aus_nz':
        return (australianAirports.includes(origin) && nzAirports.includes(dest)) ||
               (nzAirports.includes(origin) && australianAirports.includes(dest))
      case 'aus_asia':
        return (australianAirports.includes(origin) && asianAirports.includes(dest)) ||
               (asianAirports.includes(origin) && australianAirports.includes(dest))
      default:
        return true
    }
  })
}

// Computed
const totalSpend = computed(() => {
  return filteredBookings.value.reduce((sum, booking) => {
    return sum + (parseFloat(booking.total_amount) || 0)
  }, 0)
})

const totalEmissions = computed(() => {
  const total = filteredBookings.value.reduce((sum, booking) => {
    if (booking.booking_type === 'AIR' && booking.air_details?.carbon_emissions_kg) {
      return sum + parseFloat(booking.air_details.carbon_emissions_kg)
    }
    return sum
  }, 0)
  return Math.round(total)
})

const complianceRate = computed(() => {
  if (filteredBookings.value.length === 0) return 0
  const compliant = filteredBookings.value.filter(b => b.policy_compliant === true).length
  return Math.round((compliant / filteredBookings.value.length) * 100)
})

const totalPages = computed(() => {
  return Math.ceil(filteredBookings.value.length / itemsPerPage.value)
})

const startIndex = computed(() => {
  return (currentPage.value - 1) * itemsPerPage.value
})

const endIndex = computed(() => {
  return currentPage.value * itemsPerPage.value
})

const paginatedBookings = computed(() => {
  return filteredBookings.value.slice(startIndex.value, endIndex.value)
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

const getDuration = (booking) => {
  if (!booking.return_date) return '-'
  const travel = new Date(booking.travel_date)
  const returnDate = new Date(booking.return_date)
  const days = Math.ceil((returnDate - travel) / (1000 * 60 * 60 * 24))
  return days === 0 ? 'Same day' : `${days} day${days > 1 ? 's' : ''}`
}

const getDestinations = (booking) => {
  if (booking.booking_type === 'AIR' && booking.air_details) {
    return `${booking.air_details.origin_airport_code} → ${booking.air_details.destination_airport_code}`
  }
  if (booking.booking_type === 'HOTEL' && booking.accommodation_details) {
    return booking.accommodation_details.city || '-'
  }
  if (booking.booking_type === 'CAR' && booking.car_hire_details) {
    return booking.car_hire_details.pickup_location || '-'
  }
  return '-'
}

const getCarbonEmissions = (booking) => {
  if (booking.booking_type === 'AIR' && booking.air_details?.carbon_emissions_kg) {
    return `${Math.round(booking.air_details.carbon_emissions_kg)} kg`
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

const getBookingTypeClass = (type) => {
  const classes = {
    'AIR': 'px-2 py-1 text-xs font-medium rounded-full bg-sky-100 text-sky-800',
    'HOTEL': 'px-2 py-1 text-xs font-medium rounded-full bg-purple-100 text-purple-800',
    'CAR': 'px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800',
    'OTHER': 'px-2 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-800'
  }
  return classes[type] || classes['OTHER']
}

const getStatusClass = (status) => {
  const classes = {
    'CONFIRMED': 'px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800',
    'CANCELLED': 'px-2 py-1 text-xs font-medium rounded-full bg-red-100 text-red-800',
    'PENDING': 'px-2 py-1 text-xs font-medium rounded-full bg-yellow-100 text-yellow-800',
    'REFUNDED': 'px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800'
  }
  return classes[status] || classes['PENDING']
}

const getComplianceClass = (isCompliant) => {
  if (isCompliant === true) {
    return 'px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800'
  } else {
    return 'px-2 py-1 text-xs font-medium rounded-full bg-red-100 text-red-800'
  }
}

// Lifecycle
onMounted(() => {
  loadBookings()
})
</script>
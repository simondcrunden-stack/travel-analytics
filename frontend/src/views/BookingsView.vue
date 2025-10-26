<template>
  <div>
    <!-- Page Header -->
    <div class="mb-6">
      <h1 class="text-3xl font-bold text-gray-900">All Bookings</h1>
      <p class="mt-2 text-sm text-gray-600">Complete list of travel bookings across all types</p>
    </div>

    <!-- Summary Cards -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
      <!-- Total Bookings -->
      <div class="rounded-2xl bg-white p-6 shadow-sm">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-gray-600">Total Bookings</p>
            <p class="mt-2 text-3xl font-semibold text-gray-900">{{ summaryStats.totalBookings }}</p>
          </div>
          <div class="rounded-full bg-blue-100 p-3">
            <span class="mdi mdi-wallet-travel text-2xl text-blue-600"></span>
          </div>
        </div>
      </div>

      <!-- Total Spend -->
      <div class="rounded-2xl bg-white p-6 shadow-sm">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-gray-600">Total Spend</p>
            <p class="mt-2 text-3xl font-semibold text-gray-900">{{ formatCurrency(summaryStats.totalSpend) }}</p>
          </div>
          <div class="rounded-full bg-green-100 p-3">
            <span class="mdi mdi-cash-multiple text-2xl text-green-600"></span>
          </div>
        </div>
      </div>

      <!-- Total Emissions -->
      <div class="rounded-2xl bg-white p-6 shadow-sm">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-gray-600">Total Emissions</p>
            <p class="mt-2 text-3xl font-semibold text-gray-900">{{ formatEmissions(summaryStats.totalEmissions) }}</p>
          </div>
          <div class="rounded-full bg-amber-100 p-3">
            <span class="mdi mdi-leaf text-2xl text-amber-600"></span>
          </div>
        </div>
      </div>

      <!-- Compliance Rate -->
      <div class="rounded-2xl bg-white p-6 shadow-sm">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-gray-600">Compliance Rate</p>
            <p class="mt-2 text-3xl font-semibold text-gray-900">{{ summaryStats.complianceRate }}%</p>
          </div>
          <div class="rounded-full bg-purple-100 p-3">
            <span class="mdi mdi-shield-check text-2xl text-purple-600"></span>
          </div>
        </div>
      </div>
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

    <!-- Bookings Table -->
    <div class="rounded-2xl bg-white shadow-sm overflow-hidden">
      <!-- Loading State -->
      <div v-if="loading" class="flex items-center justify-center p-12">
        <div class="h-12 w-12 animate-spin rounded-full border-4 border-blue-600 border-t-transparent"></div>
      </div>

      <!-- Empty State -->
      <div v-else-if="bookings.length === 0" class="p-12 text-center">
        <div class="mx-auto w-24 h-24 rounded-full bg-gray-100 flex items-center justify-center mb-4">
          <span class="mdi mdi-wallet-travel text-4xl text-gray-400"></span>
        </div>
        <h3 class="text-lg font-semibold text-gray-900 mb-2">No bookings found</h3>
        <p class="text-sm text-gray-600">Try adjusting your filters to see more results</p>
      </div>

      <!-- Table with Data -->
      <div v-else class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th
                scope="col"
                class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                @click="sortBy('agent_booking_reference')"
              >
                Reference
                <span v-if="sortField === 'agent_booking_reference'" class="mdi" :class="sortDirection === 'asc' ? 'mdi-arrow-up' : 'mdi-arrow-down'"></span>
              </th>
              <th
                scope="col"
                class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                Traveller
              </th>
              <th
                scope="col"
                class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                Type
              </th>
              <th
                scope="col"
                class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                @click="sortBy('travel_date')"
              >
                Travel Date
                <span v-if="sortField === 'travel_date'" class="mdi" :class="sortDirection === 'asc' ? 'mdi-arrow-up' : 'mdi-arrow-down'"></span>
              </th>
              <th
                scope="col"
                class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                Duration
              </th>
              <th
                scope="col"
                class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                Destinations
              </th>
              <th
                scope="col"
                class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                @click="sortBy('total_amount')"
              >
                Amount
                <span v-if="sortField === 'total_amount'" class="mdi" :class="sortDirection === 'asc' ? 'mdi-arrow-up' : 'mdi-arrow-down'"></span>
              </th>
              <th
                scope="col"
                class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                Carbon
              </th>
              <th
                scope="col"
                class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                Compliance
              </th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr
              v-for="booking in paginatedBookings"
              :key="booking.id"
              class="hover:bg-gray-50 cursor-pointer transition-colors"
              @click="viewBookingDetails(booking.id)"
            >
              <!-- Reference -->
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm font-medium text-blue-600">
                  {{ booking.agent_booking_reference }}
                </div>
              </td>

              <!-- Traveller -->
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm font-medium text-gray-900">
                  {{ booking.traveller_name }}
                </div>
                <div class="text-xs text-gray-500">
                  {{ booking.organization_name }}
                </div>
              </td>

              <!-- Type -->
              <td class="px-6 py-4 whitespace-nowrap">
                <span
                  class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                  :class="getBookingTypeClass(booking.booking_type)"
                >
                  {{ formatBookingType(booking.booking_type) }}
                </span>
              </td>

              <!-- Travel Date -->
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                {{ formatDate(booking.travel_date) }}
              </td>

              <!-- Duration -->
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                {{ calculateDuration(booking) }}
              </td>

              <!-- Destinations -->
              <td class="px-6 py-4 text-sm text-gray-900">
                <div class="max-w-xs">
                  {{ formatDestinations(booking) }}
                </div>
              </td>

              <!-- Amount -->
              <td class="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-900">
                {{ booking.currency }} {{ formatAmount(booking.total_amount) }}
              </td>

              <!-- Carbon Emissions -->
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                {{ formatEmissions(calculateEmissions(booking)) }}
              </td>

              <!-- Compliance -->
              <td class="px-6 py-4 whitespace-nowrap">
                <span
                  class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                  :class="booking.policy_compliant ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'"
                >
                  <span class="mdi mr-1" :class="booking.policy_compliant ? 'mdi-check-circle' : 'mdi-alert-circle'"></span>
                  {{ booking.policy_compliant ? 'Compliant' : 'Violation' }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div v-if="bookings.length > 0" class="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
        <div class="flex items-center space-x-2">
          <span class="text-sm text-gray-700">Show</span>
          <select
            v-model="itemsPerPage"
            @change="handlePageSizeChange"
            class="rounded-md border-gray-300 text-sm focus:ring-blue-500 focus:border-blue-500"
          >
            <option :value="25">25</option>
            <option :value="50">50</option>
            <option :value="100">100</option>
          </select>
          <span class="text-sm text-gray-700">
            Showing {{ startIndex + 1 }} to {{ endIndex }} of {{ bookings.length }} results
          </span>
        </div>

        <div class="flex items-center space-x-2">
          <button
            @click="previousPage"
            :disabled="currentPage === 1"
            class="px-3 py-1 rounded-md border border-gray-300 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Previous
          </button>
          <span class="text-sm text-gray-700">
            Page {{ currentPage }} of {{ totalPages }}
          </span>
          <button
            @click="nextPage"
            :disabled="currentPage === totalPages"
            class="px-3 py-1 rounded-md border border-gray-300 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import UniversalFilters from '@/components/common/UniversalFilters.vue'
import api from '@/services/api'

const router = useRouter()

// State
const loading = ref(true)
const bookings = ref([])
const currentFilters = ref({})
const sortField = ref('travel_date')
const sortDirection = ref('desc')
const currentPage = ref(1)
const itemsPerPage = ref(25)

// Summary statistics
const summaryStats = computed(() => {
  const totalBookings = bookings.value.length
  const totalSpend = bookings.value.reduce((sum, b) => sum + parseFloat(b.total_amount || 0), 0)
  const totalEmissions = bookings.value.reduce((sum, b) => sum + calculateEmissions(b), 0)
  const compliantBookings = bookings.value.filter(b => b.policy_compliant).length
  const complianceRate = totalBookings > 0 ? Math.round((compliantBookings / totalBookings) * 100) : 0

  return {
    totalBookings,
    totalSpend,
    totalEmissions,
    complianceRate,
  }
})

// Pagination
const totalPages = computed(() => Math.ceil(bookings.value.length / itemsPerPage.value))
const startIndex = computed(() => (currentPage.value - 1) * itemsPerPage.value)
const endIndex = computed(() => Math.min(startIndex.value + itemsPerPage.value, bookings.value.length))

const paginatedBookings = computed(() => {
  const sorted = [...bookings.value].sort((a, b) => {
    let aVal = a[sortField.value]
    let bVal = b[sortField.value]

    // Handle numeric sorting
    if (sortField.value === 'total_amount') {
      aVal = parseFloat(aVal || 0)
      bVal = parseFloat(bVal || 0)
    }

    // Handle date sorting
    if (sortField.value === 'travel_date') {
      aVal = new Date(aVal)
      bVal = new Date(bVal)
    }

    if (sortDirection.value === 'asc') {
      return aVal > bVal ? 1 : -1
    } else {
      return aVal < bVal ? 1 : -1
    }
  })

  return sorted.slice(startIndex.value, endIndex.value)
})

// Methods
const fetchBookings = async () => {
  try {
    loading.value = true
    const params = {}

    // Handle all filter types
    if (currentFilters.value.traveller) {
      params.traveller = currentFilters.value.traveller
    }

    // Date range filters - use travel_date field
    if (currentFilters.value.dateFrom) {
      params.travel_date__gte = currentFilters.value.dateFrom
    }
    if (currentFilters.value.dateTo) {
      params.travel_date__lte = currentFilters.value.dateTo
    }

    // Organization filter
    if (currentFilters.value.organization) {
      params.organization = currentFilters.value.organization
    }

    // Status filter
    if (currentFilters.value.status) {
      params.status = currentFilters.value.status
    }

    // Destination filters - these will need custom handling
    // For now, we'll just pass them through and handle client-side
    const destinationPreset = currentFilters.value.destinationPreset
    const country = currentFilters.value.country
    const city = currentFilters.value.city

    console.log('Fetching bookings with params:', params)
    console.log('Destination filters:', { destinationPreset, country, city })

    const response = await api.get('/bookings/', { params })
    let allBookings = response.data.results || response.data

    // Apply client-side destination filtering if needed
    if (destinationPreset || country || city) {
      allBookings = filterByDestination(allBookings, { destinationPreset, country, city })
    }

    bookings.value = allBookings
    console.log('Loaded bookings:', bookings.value.length)
  } catch (error) {
    console.error('Failed to fetch bookings:', error)
    console.error('Error details:', error.response?.data)
  } finally {
    loading.value = false
  }
}

// Client-side destination filtering
const filterByDestination = (bookingsList, filters) => {
  let filtered = [...bookingsList]

  // Country filter
  if (filters.country) {
    filtered = filtered.filter(booking => {
      if (booking.booking_type === 'AIR' && booking.air_details) {
        const origin = booking.air_details.origin_airport_code || ''
        const dest = booking.air_details.destination_airport_code || ''
        // Simple country code matching (you might need more sophisticated logic)
        return origin.includes(filters.country) || dest.includes(filters.country)
      }
      if (booking.booking_type === 'HOTEL' && booking.accommodation_details) {
        // Would need country field in accommodation_details
        return true // For now, show all hotels
      }
      return true
    })
  }

  // City filter
  if (filters.city) {
    const cityLower = filters.city.toLowerCase()
    filtered = filtered.filter(booking => {
      if (booking.booking_type === 'AIR' && booking.air_details) {
        const origin = (booking.air_details.origin_airport_code || '').toLowerCase()
        const dest = (booking.air_details.destination_airport_code || '').toLowerCase()
        return origin.includes(cityLower) || dest.includes(cityLower)
      }
      if (booking.booking_type === 'HOTEL' && booking.accommodation_details) {
        const city = (booking.accommodation_details.city || '').toLowerCase()
        return city.includes(cityLower)
      }
      if (booking.booking_type === 'CAR' && booking.car_hire_details) {
        const location = (booking.car_hire_details.pickup_location || '').toLowerCase()
        return location.includes(cityLower)
      }
      return true
    })
  }

  // Destination presets
  if (filters.destinationPreset) {
    filtered = filtered.filter(booking => {
      if (booking.booking_type !== 'AIR' || !booking.air_details) {
        return false // Presets only apply to air bookings
      }

      const origin = booking.air_details.origin_airport_code || ''
      const dest = booking.air_details.destination_airport_code || ''

      // Australian airport codes typically start with 'Y' or specific 3-letter codes
      const ausAirports = ['SYD', 'MEL', 'BNE', 'PER', 'ADL', 'CBR', 'HBA', 'DRW', 'OOL']
      const isOriginAus = ausAirports.some(code => origin.includes(code))
      const isDestAus = ausAirports.some(code => dest.includes(code))

      switch (filters.destinationPreset) {
        case 'within_australia':
          return isOriginAus && isDestAus
        case 'outside_australia':
          return !isOriginAus || !isDestAus
        case 'aus_usa':
          return (isOriginAus || isDestAus) && (origin.startsWith('US') || dest.startsWith('US') || origin === 'LAX' || dest === 'LAX')
        case 'aus_nz':
          return (isOriginAus || isDestAus) && (origin.startsWith('NZ') || dest.startsWith('NZ') || origin === 'AKL' || dest === 'AKL')
        case 'aus_asia':
          const asiaAirports = ['SIN', 'NRT', 'HND', 'HKG', 'BKK', 'KUL']
          const isAsia = asiaAirports.some(code => origin.includes(code) || dest.includes(code))
          return (isOriginAus || isDestAus) && isAsia
        default:
          return true
      }
    })
  }

  return filtered
}

const handleFiltersChanged = (filters) => {
  currentFilters.value = filters
  currentPage.value = 1 // Reset to first page when filters change
  fetchBookings()
}

const sortBy = (field) => {
  if (sortField.value === field) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortField.value = field
    sortDirection.value = 'asc'
  }
}

const previousPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--
  }
}

const nextPage = () => {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
  }
}

const handlePageSizeChange = () => {
  currentPage.value = 1 // Reset to first page when page size changes
}

const viewBookingDetails = (bookingId) => {
  // Navigate to booking detail page (to be implemented)
  console.log('View booking:', bookingId)
  // router.push(`/bookings/${bookingId}`)
}

// Formatting helpers
const formatDate = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString('en-AU', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-AU', {
    style: 'currency',
    currency: 'AUD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount)
}

const formatAmount = (amount) => {
  return new Intl.NumberFormat('en-AU', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount)
}

const formatEmissions = (kg) => {
  if (!kg || kg === 0) return '-'
  return `${Math.round(kg)} kg`
}

const formatBookingType = (type) => {
  const types = {
    AIR: 'Air',
    HOTEL: 'Hotel',
    CAR: 'Car',
    OTHER: 'Other',
  }
  return types[type] || type
}

const getBookingTypeClass = (type) => {
  const classes = {
    AIR: 'bg-blue-100 text-blue-800',
    HOTEL: 'bg-purple-100 text-purple-800',
    CAR: 'bg-green-100 text-green-800',
    OTHER: 'bg-gray-100 text-gray-800',
  }
  return classes[type] || classes.OTHER
}

const calculateDuration = (booking) => {
  if (!booking.return_date || !booking.travel_date) return '-'

  const start = new Date(booking.travel_date)
  const end = new Date(booking.return_date)
  const days = Math.ceil((end - start) / (1000 * 60 * 60 * 24))

  if (days === 0) return 'Same day'
  if (days === 1) return '1 day'
  return `${days} days`
}

const formatDestinations = (booking) => {
  // Air bookings - show origin → destination
  if (booking.booking_type === 'AIR' && booking.air_details) {
    const origin = booking.air_details.origin_airport_code || 'Unknown'
    const destination = booking.air_details.destination_airport_code || 'Unknown'
    return `${origin} → ${destination}`
  }

  // Hotel bookings - show city
  if (booking.booking_type === 'HOTEL' && booking.accommodation_details) {
    return booking.accommodation_details.city || 'Unknown'
  }

  // Car hire - show pickup location
  if (booking.booking_type === 'CAR' && booking.car_hire_details) {
    return booking.car_hire_details.pickup_location || 'Unknown'
  }

  return '-'
}

const calculateEmissions = (booking) => {
  // Only air bookings have carbon emissions
  if (booking.booking_type !== 'AIR' || !booking.air_details) {
    return 0
  }

  // If API already calculated it, use that
  if (booking.air_details.carbon_emissions_kg) {
    return parseFloat(booking.air_details.carbon_emissions_kg)
  }

  return 0
}

// Lifecycle
onMounted(() => {
  fetchBookings()
})
</script>
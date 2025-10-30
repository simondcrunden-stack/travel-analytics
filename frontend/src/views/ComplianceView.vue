<template>
  <div class="min-h-screen bg-gray-50 p-6">
    <!-- Header -->
    <div class="mb-6">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-3xl font-bold text-gray-900">Compliance Dashboard</h1>
          <p class="text-gray-600 mt-1">Policy violations and compliance tracking</p>
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

    <!-- Violation Detail Modal -->
    <div
      v-if="selectedViolation"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
      @click.self="closeModal"
    >
      <div class="bg-white rounded-2xl shadow-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        <!-- Modal Header -->
        <div class="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <div>
            <h2 class="text-xl font-bold text-gray-900">Violation Details</h2>
            <p class="text-sm text-gray-600 mt-1">{{ selectedViolation.booking_reference }}</p>
          </div>
          <button
            @click="closeModal"
            class="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg class="w-6 h-6" :d="mdiClose" />
          </button>
        </div>

        <!-- Modal Content -->
        <div class="p-6 space-y-6">
          <!-- Severity Badge -->
          <div class="flex items-center gap-3">
            <span :class="getSeverityBadgeClass(selectedViolation.severity)" class="text-base px-4 py-2">
              {{ selectedViolation.severity }}
            </span>
            <span class="text-sm text-gray-600">
              Detected on {{ formatDate(selectedViolation.detected_at) }}
            </span>
          </div>

          <!-- Violation Type -->
          <div>
            <h3 class="text-sm font-medium text-gray-700 mb-2">Violation Type</h3>
            <p class="text-base text-gray-900">{{ formatViolationType(selectedViolation.violation_type) }}</p>
          </div>

          <!-- Description -->
          <div>
            <h3 class="text-sm font-medium text-gray-700 mb-2">Description</h3>
            <p class="text-base text-gray-900">{{ selectedViolation.violation_description }}</p>
          </div>

          <!-- Financial Impact -->
          <div v-if="selectedViolation.variance_amount" class="bg-red-50 border border-red-200 rounded-lg p-4">
            <h3 class="text-sm font-medium text-red-900 mb-3">Financial Impact</h3>
            <div class="grid grid-cols-3 gap-4 mt-3">
              <div>
                <p class="text-xs text-red-700">Expected Amount</p>
                <p class="text-lg font-bold text-red-900">
                  {{ formatCurrency(selectedViolation.expected_amount || 0) }}
                </p>
              </div>
              <div>
                <p class="text-xs text-red-700">Actual Amount</p>
                <p class="text-lg font-bold text-red-900">
                  {{ formatCurrency(selectedViolation.actual_amount || 0) }}
                </p>
              </div>
              <div>
                <p class="text-xs text-red-700">Variance</p>
                <p class="text-lg font-bold text-red-900">
                  {{ formatCurrency(selectedViolation.variance_amount) }}
                </p>
              </div>
            </div>
          </div>

          <!-- Traveller Information -->
          <div class="border border-gray-200 rounded-lg p-4">
            <h3 class="text-sm font-medium text-gray-900 mb-3">Traveller Information</h3>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <p class="text-xs text-gray-600">Name</p>
                <p class="text-sm font-medium text-gray-900">{{ selectedViolation.traveller_name }}</p>
              </div>
              <div>
                <p class="text-xs text-gray-600">Organization</p>
                <p class="text-sm font-medium text-gray-900">{{ selectedViolation.organization_name }}</p>
              </div>
            </div>
          </div>

          <!-- Booking Information -->
          <div class="border border-gray-200 rounded-lg p-4">
            <h3 class="text-sm font-medium text-gray-900 mb-3">Booking Information</h3>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <p class="text-xs text-gray-600">Booking Reference</p>
                <p class="text-sm font-medium text-gray-900">{{ selectedViolation.booking_reference }}</p>
              </div>
              <div>
                <p class="text-xs text-gray-600">Booking Type</p>
                <p class="text-sm font-medium text-gray-900">Air Travel</p>
              </div>
            </div>
          </div>

          <!-- Actions -->
          <div class="flex items-center gap-3 pt-4 border-t border-gray-200">
            <button
              @click="waiveViolation"
              class="flex-1 px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors"
            >
              Waive Violation
            </button>
            <button
              @click="viewBooking"
              class="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              View Full Booking
            </button>
            <button
              @click="closeModal"
              class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-12">
      <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      <p class="mt-4 text-gray-600">Loading compliance data...</p>
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
              <p class="text-gray-600 text-sm">Total Violations</p>
              <p class="text-3xl font-bold text-gray-900 mt-1">{{ stats.totalViolations }}</p>
            </div>
            <div class="w-12 h-12 bg-red-100 rounded-xl flex items-center justify-center">
              <svg class="w-6 h-6 text-red-600" :d="mdiAlertCircle" />
            </div>
          </div>
        </div>

        <div class="bg-white rounded-2xl shadow-sm p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-gray-600 text-sm">Financial Impact</p>
              <p class="text-3xl font-bold text-gray-900 mt-1">
                {{ formatCurrency(stats.totalImpact) }}
              </p>
            </div>
            <div class="w-12 h-12 bg-orange-100 rounded-xl flex items-center justify-center">
              <svg class="w-6 h-6 text-orange-600" :d="mdiCurrencyUsd" />
            </div>
          </div>
        </div>

        <div class="bg-white rounded-2xl shadow-sm p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-gray-600 text-sm">Compliance Rate</p>
              <p class="text-3xl font-bold text-gray-900 mt-1">{{ stats.complianceRate }}%</p>
            </div>
            <div class="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center">
              <svg class="w-6 h-6 text-green-600" :d="mdiCheckCircle" />
            </div>
          </div>
        </div>

        <div class="bg-white rounded-2xl shadow-sm p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-gray-600 text-sm">Critical Violations</p>
              <p class="text-3xl font-bold text-red-600 mt-1">{{ stats.criticalCount }}</p>
            </div>
            <div class="w-12 h-12 bg-red-100 rounded-xl flex items-center justify-center">
              <svg class="w-6 h-6 text-red-600" :d="mdiAlert" />
            </div>
          </div>
        </div>
      </div>

      <!-- Filters -->
      <div class="bg-white rounded-2xl shadow-sm p-6 mb-6">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold text-gray-900">Filters</h2>
          <button
            @click="clearFilters"
            class="text-sm text-blue-600 hover:text-blue-700"
          >
            Clear All
          </button>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
          <!-- Severity Filter -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Severity</label>
            <select
              v-model="filters.severity"
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">All Severities</option>
              <option value="INFO">Info</option>
              <option value="WARNING">Warning</option>
              <option value="BREACH">Breach</option>
              <option value="CRITICAL">Critical</option>
            </select>
          </div>

          <!-- Type Filter -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Violation Type</label>
            <select
              v-model="filters.type"
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">All Types</option>
              <option value="LOWEST_FARE">Lowest Fare</option>
              <option value="ADVANCE_BOOKING">Advance Booking</option>
              <option value="TRAVEL_CLASS">Travel Class</option>
              <option value="PREFERRED_SUPPLIER">Preferred Supplier</option>
              <option value="BOOKING_CHANNEL">Booking Channel</option>
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

        <!-- Search -->
        <div class="mt-4">
          <label class="block text-sm font-medium text-gray-700 mb-2">Search</label>
          <input
            type="text"
            v-model="filters.search"
            placeholder="Search by traveller name, booking reference..."
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
      </div>

      <!-- Violations Table -->
      <div class="bg-white rounded-2xl shadow-sm overflow-hidden">
        <div class="p-6 border-b border-gray-200">
          <h2 class="text-lg font-semibold text-gray-900">Policy Violations</h2>
          <p class="text-sm text-gray-600 mt-1">{{ filteredViolations.length }} violations found</p>
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
                  Booking Ref
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Violation Type
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Severity
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Financial Impact
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Description
                </th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr
                v-for="violation in paginatedViolations"
                :key="violation.id"
                class="hover:bg-gray-50 transition-colors cursor-pointer"
                @click="viewViolationDetail(violation)"
              >
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {{ formatDate(violation.detected_at) }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="text-sm font-medium text-gray-900">
                    {{ violation.traveller_name }}
                  </div>
                  <div class="text-sm text-gray-500">{{ violation.organization_name }}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {{ violation.booking_reference }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {{ formatViolationType(violation.violation_type) }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span :class="getSeverityBadgeClass(violation.severity)">
                    {{ violation.severity }}
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm">
                  <span v-if="violation.variance_amount" class="text-red-600 font-medium">
                    {{ formatCurrency(violation.variance_amount) }}
                  </span>
                  <span v-else class="text-gray-400">-</span>
                </td>
                <td class="px-6 py-4 text-sm text-gray-600">
                  {{ violation.violation_description }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination -->
        <div class="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
          <div class="text-sm text-gray-600">
            Showing {{ (currentPage - 1) * itemsPerPage + 1 }} to 
            {{ Math.min(currentPage * itemsPerPage, filteredViolations.length) }} of 
            {{ filteredViolations.length }} violations
          </div>
          <div class="flex gap-2">
            <button
              @click="currentPage--"
              :disabled="currentPage === 1"
              class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <button
              @click="currentPage++"
              :disabled="currentPage >= totalPages"
              class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'
import {
  mdiAlertCircle,
  mdiCurrencyUsd,
  mdiCheckCircle,
  mdiAlert,
  mdiDownload,
  mdiClose,
  mdiAccount,
  mdiAirplane,
} from '@mdi/js'

const router = useRouter()

// State
const loading = ref(true)
const error = ref(null)
const violations = ref([])
const selectedViolation = ref(null)
const stats = ref({
  totalViolations: 0,
  totalImpact: 0,
  complianceRate: 0,
  criticalCount: 0,
})

// Filters
const filters = ref({
  severity: '',
  type: '',
  dateFrom: '',
  dateTo: '',
  search: '',
})

// Pagination
const currentPage = ref(1)
const itemsPerPage = ref(20)

// Fetch data
const fetchViolations = async () => {
  try {
    loading.value = true
    error.value = null

    // In a real app, this would be an API call
    // For now, we'll generate sample data
    violations.value = generateSampleViolations()
    calculateStats()
  } catch (err) {
    error.value = 'Failed to load compliance data'
    console.error(err)
  } finally {
    loading.value = false
  }
}

// Generate sample violations (replace with actual API call)
const generateSampleViolations = () => {
  const types = ['LOWEST_FARE', 'ADVANCE_BOOKING', 'TRAVEL_CLASS', 'PREFERRED_SUPPLIER']
  const severities = ['INFO', 'WARNING', 'BREACH', 'CRITICAL']
  const travellers = [
    { name: 'Jennifer Wilson', org: 'TechCorp Australia' },
    { name: 'David Anderson', org: 'TechCorp Australia' },
    { name: 'Sophie Martinez', org: 'TechCorp Australia' },
    { name: 'Emily White', org: 'Retail Solutions Group' },
  ]

  const sampleViolations = []
  for (let i = 0; i < 50; i++) {
    const traveller = travellers[Math.floor(Math.random() * travellers.length)]
    const type = types[Math.floor(Math.random() * types.length)]
    const severity = severities[Math.floor(Math.random() * severities.length)]
    
    sampleViolations.push({
      id: i + 1,
      detected_at: new Date(2025, 9, Math.floor(Math.random() * 20) + 1).toISOString(),
      traveller_name: traveller.name,
      organization_name: traveller.org,
      booking_reference: `BK${1000 + i}`,
      violation_type: type,
      severity: severity,
      expected_amount: Math.floor(Math.random() * 1000) + 500,
      actual_amount: Math.floor(Math.random() * 1500) + 500,
      variance_amount: severity === 'INFO' ? null : Math.floor(Math.random() * 500) + 50,
      violation_description: getViolationDescription(type),
    })
  }
  return sampleViolations
}

const getViolationDescription = (type) => {
  const descriptions = {
    LOWEST_FARE: 'Did not select the lowest available fare option',
    ADVANCE_BOOKING: 'Booking made less than required advance notice period',
    TRAVEL_CLASS: 'Higher class of travel booked than policy permits',
    PREFERRED_SUPPLIER: 'Non-preferred supplier selected without approval',
  }
  return descriptions[type] || 'Policy violation detected'
}

// Calculate statistics
const calculateStats = () => {
  stats.value.totalViolations = violations.value.length
  stats.value.totalImpact = violations.value.reduce((sum, v) => sum + (v.variance_amount || 0), 0)
  stats.value.criticalCount = violations.value.filter(v => v.severity === 'CRITICAL').length
  
  // Compliance rate (assuming total bookings = violations * 5 for demo)
  const totalBookings = violations.value.length * 5
  const compliantBookings = totalBookings - violations.value.length
  stats.value.complianceRate = Math.round((compliantBookings / totalBookings) * 100)
}

// Filtered violations
const filteredViolations = computed(() => {
  return violations.value.filter(v => {
    if (filters.value.severity && v.severity !== filters.value.severity) return false
    if (filters.value.type && v.violation_type !== filters.value.type) return false
    if (filters.value.search) {
      const search = filters.value.search.toLowerCase()
      if (!v.traveller_name.toLowerCase().includes(search) &&
          !v.booking_reference.toLowerCase().includes(search)) {
        return false
      }
    }
    return true
  })
})

// Paginated violations
const totalPages = computed(() => Math.ceil(filteredViolations.value.length / itemsPerPage.value))
const paginatedViolations = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage.value
  return filteredViolations.value.slice(start, start + itemsPerPage.value)
})

// Utility functions
const formatCurrency = (value) => {
  return new Intl.NumberFormat('en-AU', {
    style: 'currency',
    currency: 'AUD',
  }).format(value)
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('en-AU', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

const formatViolationType = (type) => {
  return type.split('_').map(word => 
    word.charAt(0) + word.slice(1).toLowerCase()
  ).join(' ')
}

const getSeverityBadgeClass = (severity) => {
  const classes = {
    INFO: 'px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800',
    WARNING: 'px-2 py-1 text-xs font-medium rounded-full bg-yellow-100 text-yellow-800',
    BREACH: 'px-2 py-1 text-xs font-medium rounded-full bg-orange-100 text-orange-800',
    CRITICAL: 'px-2 py-1 text-xs font-medium rounded-full bg-red-100 text-red-800',
  }
  return classes[severity] || classes.INFO
}

const clearFilters = () => {
  filters.value = {
    severity: '',
    type: '',
    dateFrom: '',
    dateTo: '',
    search: '',
  }
  currentPage.value = 1
}

const viewViolationDetail = (violation) => {
  selectedViolation.value = violation
}

const closeModal = () => {
  selectedViolation.value = null
}

const waiveViolation = () => {
  console.log('Waiving violation:', selectedViolation.value)
  // In real app: API call to waive violation
  alert('Violation waived successfully!')
  closeModal()
}

const viewBooking = () => {
  console.log('Viewing booking:', selectedViolation.value.booking_reference)
  // In real app: navigate to booking detail
  // router.push(`/bookings/${selectedViolation.value.booking_id}`)
  alert('Navigate to booking detail page')
}

const exportReport = () => {
  console.log('Exporting compliance report...')
  // Implement CSV/PDF export
}

// Watch filters and reset pagination
watch(filters, () => {
  currentPage.value = 1
}, { deep: true })

// Lifecycle
onMounted(() => {
  fetchViolations()
})
</script>
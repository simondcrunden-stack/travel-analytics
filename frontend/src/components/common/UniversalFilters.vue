<template>
  <div class="bg-white rounded-2xl shadow-sm p-6 mb-6">
    <!-- Filter Header -->
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center space-x-3">
        <h3 class="text-lg font-semibold text-gray-900">Filters</h3>
        <span
          v-if="activeFilterCount > 0"
          class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
        >
          {{ activeFilterCount }} active
        </span>
      </div>
      <div class="flex items-center space-x-2">
        <button
          v-if="activeFilterCount > 0"
          @click="clearAllFilters"
          class="text-sm text-gray-600 hover:text-gray-900 font-medium"
        >
          Clear All
        </button>
        <button
          @click="toggleCollapse"
          class="p-1 rounded-lg hover:bg-gray-100 transition-colors"
          :aria-label="isCollapsed ? 'Expand filters' : 'Collapse filters'"
        >
          <span class="mdi text-xl text-gray-600" :class="isCollapsed ? 'mdi-chevron-down' : 'mdi-chevron-up'"></span>
        </button>
      </div>
    </div>

    <!-- Filter Content (Collapsible) -->
    <div v-show="!isCollapsed" class="space-y-4">
      <!-- Row 1: Traveller, Date Range -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <!-- Traveller Filter -->
        <div v-if="showTraveller">
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Traveller
          </label>
          <select
            v-model="localFilters.traveller"
            @change="emitFilters"
            class="w-full rounded-lg border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">All Travellers</option>
            <option v-for="traveller in travellers" :key="traveller.id" :value="traveller.id">
              {{ traveller.first_name }} {{ traveller.last_name }}
            </option>
          </select>
        </div>

        <!-- Date From -->
        <div v-if="showDateRange">
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Travel Date From
          </label>
          <input
            v-model="localFilters.dateFrom"
            @change="emitFilters"
            type="date"
            class="w-full rounded-lg border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        <!-- Date To -->
        <div v-if="showDateRange">
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Travel Date To
          </label>
          <input
            v-model="localFilters.dateTo"
            @change="emitFilters"
            type="date"
            class="w-full rounded-lg border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      </div>

      <!-- Row 2: Destinations, Organization -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <!-- Destination Preset -->
        <div v-if="showDestinations">
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Destination Filter
          </label>
          <select
            v-model="localFilters.destinationPreset"
            @change="emitFilters"
            class="w-full rounded-lg border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">All Destinations</option>
            <option value="within_australia">Within Australia</option>
            <option value="outside_australia">Outside Australia</option>
            <option value="aus_usa">Australia ↔ USA</option>
            <option value="aus_nz">Australia ↔ New Zealand</option>
            <option value="aus_asia">Australia ↔ Asia</option>
          </select>
        </div>

        <!-- Country Filter -->
        <div v-if="showDestinations">
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Country
          </label>
          <select
            v-model="localFilters.country"
            @change="emitFilters"
            class="w-full rounded-lg border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">All Countries</option>
            <option value="AU">Australia</option>
            <option value="NZ">New Zealand</option>
            <option value="US">United States</option>
            <option value="SG">Singapore</option>
            <option value="JP">Japan</option>
            <option value="UK">United Kingdom</option>
          </select>
        </div>

        <!-- City/Location Filter -->
        <div v-if="showDestinations">
          <label class="block text-sm font-medium text-gray-700 mb-1">
            City/Location
          </label>
          <input
            v-model="localFilters.city"
            @input="emitFilters"
            type="text"
            placeholder="Sydney, Melbourne..."
            class="w-full rounded-lg border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      </div>

      <!-- Row 3: Organization, Status, Supplier -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <!-- Organization Filter -->
        <div v-if="showOrganization">
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Organization
          </label>
          <select
            v-model="localFilters.organization"
            @change="emitFilters"
            class="w-full rounded-lg border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">All Organizations</option>
            <option v-for="org in organizations" :key="org.id" :value="org.id">
              {{ org.name }}
            </option>
          </select>
        </div>

        <!-- Status Filter -->
        <div v-if="showStatus">
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Status
          </label>
          <select
            v-model="localFilters.status"
            @change="emitFilters"
            class="w-full rounded-lg border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">All Status</option>
            <option value="CONFIRMED">Confirmed</option>
            <option value="PENDING">Pending</option>
            <option value="CANCELLED">Cancelled</option>
          </select>
        </div>

        <!-- Supplier Filter (for Air, Accommodation, Car Hire) -->
        <div v-if="showSupplier">
          <label class="block text-sm font-medium text-gray-700 mb-1">
            {{ supplierLabel }}
          </label>
          <input
            v-model="localFilters.supplier"
            @input="emitFilters"
            type="text"
            :placeholder="supplierPlaceholder"
            class="w-full rounded-lg border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      </div>

      <!-- Quick Date Presets -->
      <div v-if="showDateRange" class="flex flex-wrap gap-2 pt-2 border-t border-gray-200">
        <span class="text-sm font-medium text-gray-700 mr-2">Quick Dates:</span>
        <button
          v-for="preset in datePresets"
          :key="preset.value"
          @click="applyDatePreset(preset.value)"
          class="px-3 py-1 text-xs font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-full transition-colors"
        >
          {{ preset.label }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, reactive, watch, onMounted } from 'vue'
import api from '@/services/api'

// Props
const props = defineProps({
  showTraveller: {
    type: Boolean,
    default: true,
  },
  showDateRange: {
    type: Boolean,
    default: true,
  },
  showDestinations: {
    type: Boolean,
    default: true,
  },
  showOrganization: {
    type: Boolean,
    default: true,
  },
  showStatus: {
    type: Boolean,
    default: true,
  },
  showSupplier: {
    type: Boolean,
    default: false,
  },
  supplierLabel: {
    type: String,
    default: 'Supplier',
  },
  supplierPlaceholder: {
    type: String,
    default: 'Supplier name...',
  },
  initialFilters: {
    type: Object,
    default: () => ({}),
  },
})

// Emits
const emit = defineEmits(['filters-changed'])

// State
const isCollapsed = ref(false)
const travellers = ref([])
const organizations = ref([])

// Local filters object
const localFilters = reactive({
  traveller: '',
  dateFrom: '',
  dateTo: '',
  destinationPreset: '',
  country: '',
  city: '',
  organization: '',
  status: '',
  supplier: '',
  ...props.initialFilters,
})

// Date presets
const datePresets = [
  { label: 'Today', value: 'today' },
  { label: 'This Week', value: 'week' },
  { label: 'This Month', value: 'month' },
  { label: 'This Quarter', value: 'quarter' },
  { label: 'This Year', value: 'year' },
  { label: 'Last 30 Days', value: 'last30' },
  { label: 'Last 90 Days', value: 'last90' },
]

// Computed
const activeFilterCount = computed(() => {
  let count = 0
  if (localFilters.traveller) count++
  if (localFilters.dateFrom) count++
  if (localFilters.dateTo) count++
  if (localFilters.destinationPreset) count++
  if (localFilters.country) count++
  if (localFilters.city) count++
  if (localFilters.organization) count++
  if (localFilters.status) count++
  if (localFilters.supplier) count++
  return count
})

// Methods
const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value
}

const clearAllFilters = () => {
  localFilters.traveller = ''
  localFilters.dateFrom = ''
  localFilters.dateTo = ''
  localFilters.destinationPreset = ''
  localFilters.country = ''
  localFilters.city = ''
  localFilters.organization = ''
  localFilters.status = ''
  localFilters.supplier = ''
  emitFilters()
}

const emitFilters = () => {
  // Create a clean object with only non-empty values
  const activeFilters = {}
  Object.keys(localFilters).forEach((key) => {
    if (localFilters[key]) {
      activeFilters[key] = localFilters[key]
    }
  })
  emit('filters-changed', activeFilters)
}

const applyDatePreset = (preset) => {
  const today = new Date()
  let dateFrom = null
  let dateTo = null

  switch (preset) {
    case 'today':
      dateFrom = dateTo = today
      break
    case 'week':
      dateFrom = new Date(today.getFullYear(), today.getMonth(), today.getDate() - today.getDay())
      dateTo = new Date(today.getFullYear(), today.getMonth(), today.getDate() + (6 - today.getDay()))
      break
    case 'month':
      dateFrom = new Date(today.getFullYear(), today.getMonth(), 1)
      dateTo = new Date(today.getFullYear(), today.getMonth() + 1, 0)
      break
    case 'quarter':
      const quarter = Math.floor(today.getMonth() / 3)
      dateFrom = new Date(today.getFullYear(), quarter * 3, 1)
      dateTo = new Date(today.getFullYear(), quarter * 3 + 3, 0)
      break
    case 'year':
      dateFrom = new Date(today.getFullYear(), 0, 1)
      dateTo = new Date(today.getFullYear(), 11, 31)
      break
    case 'last30':
      dateFrom = new Date(today.getFullYear(), today.getMonth(), today.getDate() - 30)
      dateTo = today
      break
    case 'last90':
      dateFrom = new Date(today.getFullYear(), today.getMonth(), today.getDate() - 90)
      dateTo = today
      break
  }

  if (dateFrom && dateTo) {
    localFilters.dateFrom = dateFrom.toISOString().split('T')[0]
    localFilters.dateTo = dateTo.toISOString().split('T')[0]
    emitFilters()
  }
}

// Load travellers for dropdown
const loadTravellers = async () => {
  try {
    const response = await api.get('/travellers/')
    // Handle both paginated and non-paginated responses
    const travellerData = response.data.results || response.data
    console.log('Loaded travellers:', travellerData)
    travellers.value = Array.isArray(travellerData) ? travellerData : []
  } catch (error) {
    console.error('Failed to load travellers:', error)
    console.error('Error details:', error.response?.data)
    travellers.value = []
  }
}

// Load organizations for dropdown
const loadOrganizations = async () => {
  try {
    const response = await api.get('/organizations/')
    // Handle both paginated and non-paginated responses
    const orgData = response.data.results || response.data
    console.log('Loaded organizations:', orgData)
    organizations.value = Array.isArray(orgData) ? orgData : []
  } catch (error) {
    console.error('Failed to load organizations:', error)
    console.error('Error details:', error.response?.data)
    organizations.value = []
  }
}

// Lifecycle
onMounted(() => {
  if (props.showTraveller) loadTravellers()
  if (props.showOrganization) loadOrganizations()
})

// Expose methods for parent components
defineExpose({
  clearAllFilters,
  applyDatePreset,
})
</script>

<style scoped>
/* Ensure consistent spacing and alignment */
select,
input[type='text'],
input[type='date'] {
  height: 38px;
}

/* Custom styling for active filter badge */
.bg-blue-100 {
  background-color: rgba(59, 130, 246, 0.1);
}

.text-blue-800 {
  color: rgb(30, 64, 175);
}
</style>
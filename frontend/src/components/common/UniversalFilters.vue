<template>
  <div class="mb-6">
    <!-- Filter Button & Active Filters Display -->
    <div class="flex items-center justify-between rounded-2xl bg-white p-4 shadow-sm">
      <!-- Active Filters Summary -->
      <div class="flex flex-wrap items-center gap-3">
        <span class="text-sm font-medium text-gray-700">Active Filters:</span>
        
        <!-- Date Range Badge -->
        <div v-if="localFilters.dateFrom || localFilters.dateTo" class="flex items-center gap-2 rounded-lg bg-blue-50 px-3 py-1.5 text-sm">
          <MdiIcon :path="mdiCalendarRange" :size="16" class="text-blue-600" />
          <span class="font-medium text-blue-900">{{ formattedDateRange }}</span>
        </div>

        <!-- Travellers Badge (Multi-Select) -->
        <div v-if="localFilters.travellers.length > 0" class="flex items-center gap-2 rounded-lg bg-indigo-50 px-3 py-1.5 text-sm">
          <MdiIcon :path="mdiAccount" :size="16" class="text-indigo-600" />
          <span class="font-medium text-indigo-900">{{ selectedTravellersText }}</span>
          <button @click="clearTravellers" class="text-indigo-600 hover:text-indigo-800">
            <MdiIcon :path="mdiClose" :size="16" />
          </button>
        </div>

        <!-- Organization Badge -->
        <div v-if="localFilters.organization" class="flex items-center gap-2 rounded-lg bg-purple-50 px-3 py-1.5 text-sm">
          <MdiIcon :path="mdiOfficeBuilding" :size="16" class="text-purple-600" />
          <span class="font-medium text-purple-900">{{ selectedOrgName }}</span>
          <button @click="clearOrganization" class="text-purple-600 hover:text-purple-800">
            <MdiIcon :path="mdiClose" :size="16" />
          </button>
        </div>

        <!-- Destination Preset Badge -->
        <div v-if="localFilters.destinationPreset" class="flex items-center gap-2 rounded-lg bg-emerald-50 px-3 py-1.5 text-sm">
          <MdiIcon :path="mdiMapMarker" :size="16" class="text-emerald-600" />
          <span class="font-medium text-emerald-900">{{ destinationPresetLabel }}</span>
          <button @click="clearDestinationPreset" class="text-emerald-600 hover:text-emerald-800">
            <MdiIcon :path="mdiClose" :size="16" />
          </button>
        </div>

        <!-- Countries Badge (Multi-Select) -->
        <div v-if="localFilters.countries.length > 0" class="flex items-center gap-2 rounded-lg bg-amber-50 px-3 py-1.5 text-sm">
          <MdiIcon :path="mdiEarth" :size="16" class="text-amber-600" />
          <span class="font-medium text-amber-900">{{ selectedCountriesText }}</span>
          <button @click="clearCountries" class="text-amber-600 hover:text-amber-800">
            <MdiIcon :path="mdiClose" :size="16" />
          </button>
        </div>

        <!-- City Badge -->
        <div v-if="localFilters.city" class="flex items-center gap-2 rounded-lg bg-teal-50 px-3 py-1.5 text-sm">
          <MdiIcon :path="mdiCity" :size="16" class="text-teal-600" />
          <span class="font-medium text-teal-900">{{ localFilters.city }}</span>
          <button @click="clearCity" class="text-teal-600 hover:text-teal-800">
            <MdiIcon :path="mdiClose" :size="16" />
          </button>
        </div>

        <!-- Status Badge -->
        <div v-if="localFilters.status" class="flex items-center gap-2 rounded-lg bg-cyan-50 px-3 py-1.5 text-sm">
          <MdiIcon :path="mdiCheckCircle" :size="16" class="text-cyan-600" />
          <span class="font-medium text-cyan-900">{{ localFilters.status }}</span>
          <button @click="clearStatus" class="text-cyan-600 hover:text-cyan-800">
            <MdiIcon :path="mdiClose" :size="16" />
          </button>
        </div>

        <!-- Supplier Badge -->
        <div v-if="localFilters.supplier" class="flex items-center gap-2 rounded-lg bg-rose-50 px-3 py-1.5 text-sm">
          <MdiIcon :path="mdiDomain" :size="16" class="text-rose-600" />
          <span class="font-medium text-rose-900">{{ localFilters.supplier }}</span>
          <button @click="clearSupplier" class="text-rose-600 hover:text-rose-800">
            <MdiIcon :path="mdiClose" :size="16" />
          </button>
        </div>

        <!-- Clear All -->
        <button
          v-if="hasActiveFilters"
          @click="clearAllFilters"
          class="text-sm text-gray-500 hover:text-gray-700 underline"
        >
          Clear all
        </button>
      </div>

      <!-- Action Buttons -->
      <div class="flex items-center gap-2">
        <!-- Save as Default Button -->
        <button
          v-if="showSaveButton && hasActiveFilters"
          @click="saveAsDefault"
          :disabled="isSaving"
          class="flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-emerald-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          <MdiIcon :path="mdiContentSave" :size="20" />
          {{ isSaving ? 'Saving...' : 'Save as Default' }}
        </button>

        <!-- Filter Toggle Button -->
        <button
          @click="toggleFilters"
          class="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700"
        >
          <MdiIcon :path="mdiTune" :size="20" class="text-white" />
          {{ showFilters ? 'Hide Filters' : 'Edit Filters' }}
        </button>
      </div>
    </div>

    <!-- Collapsible Filter Panel -->
    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0 -translate-y-2"
      enter-to-class="opacity-100 translate-y-0"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100 translate-y-0"
      leave-to-class="opacity-0 -translate-y-2"
    >
      <div v-if="showFilters" class="mt-4 rounded-2xl bg-white p-6 shadow-sm">
        <div class="grid grid-cols-1 gap-4 md:grid-cols-4">
          <!-- Organization Filter -->
          <div v-if="showOrganization">
            <label class="mb-2 block text-sm font-medium text-gray-700">Organization</label>
            <select
              v-model="localFilters.organization"
              class="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              @change="emitFilters"
            >
              <option value="">All Organizations</option>
              <option v-for="org in organizations" :key="org.id" :value="org.id">
                {{ org.name }}
              </option>
            </select>
          </div>

          <!-- Traveller Filter (Multi-Select) -->
          <div v-if="showTraveller">
            <label class="mb-2 block text-sm font-medium text-gray-700">
              Travellers
              <span v-if="localFilters.travellers.length > 0" class="text-xs text-blue-600">
                ({{ localFilters.travellers.length }} selected)
              </span>
            </label>
            <MultiSelect
              :model-value="localFilters.travellers"
              @update:model-value="handleTravellerChange"
              :options="travellerOptions"
              label-key="label"
              reduce-key="value"
              placeholder="Select travellers..."
            />
          </div>

          <!-- Date From -->
          <div v-if="showDateRange">
            <label class="mb-2 block text-sm font-medium text-gray-700">Travel Date From</label>
            <input
              v-model="localFilters.dateFrom"
              type="date"
              class="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              @change="emitFilters"
            />
          </div>

          <!-- Date To -->
          <div v-if="showDateRange">
            <label class="mb-2 block text-sm font-medium text-gray-700">Travel Date To</label>
            <input
              v-model="localFilters.dateTo"
              type="date"
              class="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              @change="emitFilters"
            />
          </div>

          <!-- Destination Preset -->
          <div v-if="showDestinations">
            <label class="mb-2 block text-sm font-medium text-gray-700">Destination Pre-Sets</label>
            <select
              v-model="localFilters.destinationPreset"
              class="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              @change="emitFilters"
            >
              <option value="">All Destinations</option>
              <option value="within_user_country">Domestic</option>
              <option value="outside_user_country">International</option>
              <option value="north_america">North America</option>
              <option value="europe">Europe</option>
              <option value="asia">Asia</option>
              <option value="oceania">Oceania</option>
              <option value="middle_east">Middle East</option>
              <option value="south_america">South America</option>
              <option value="africa">Africa</option>
              <option value="other">Other</option>
            </select>
          </div>

          <!-- Country Filter (Multi-Select)-->
          <div v-if="showDestinations">
            <label class="mb-2 block text-sm font-medium text-gray-700">
              Countries
              <span v-if="isLoadingCountries" class="text-xs text-gray-500">(loading...)</span>
              <span v-else-if="localFilters.countries.length > 0" class="text-xs text-blue-600">
                ({{ localFilters.countries.length }} selected)
              </span>
            </label>
            <MultiSelect
              :model-value="localFilters.countries"
              @update:model-value="handleCountryChange"
              :options="countryOptions"
              label-key="label"
              reduce-key="value"
              :disabled="isLoadingCountries"
              placeholder="Select countries..."
              no-options-text="No countries with bookings"
            />
          </div>

          <!-- City/Location Filter -->
          <div v-if="showDestinations">
            <label class="mb-2 block text-sm font-medium text-gray-700">City/Location</label>
            <input
              v-model="localFilters.city"
              type="text"
              placeholder="Sydney, Melbourne..."
              class="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              @input="emitFilters"
            />
          </div>

          <!-- Status Filter -->
          <div v-if="showStatus">
            <label class="mb-2 block text-sm font-medium text-gray-700">Status</label>
            <select
              v-model="localFilters.status"
              class="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              @change="emitFilters"
            >
              <option value="">All Status</option>
              <option value="CONFIRMED">Confirmed</option>
              <option value="PENDING">Pending</option>
              <option value="CANCELLED">Cancelled</option>
            </select>
          </div>

          <!-- Supplier Filter -->
          <div v-if="showSupplier">
            <label class="mb-2 block text-sm font-medium text-gray-700">{{ supplierLabel || 'Supplier' }}</label>
            <input
              v-model="localFilters.supplier"
              type="text"
              :placeholder="supplierPlaceholder || 'Supplier name...'"
              class="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              @input="emitFilters"
            />
          </div>
        </div>

        <!-- Quick Date Presets -->
        <div v-if="showDateRange" class="mt-4 border-t border-gray-200 pt-4">
          <span class="mb-2 block text-sm font-medium text-gray-700">Quick Date Ranges:</span>
          <div class="flex flex-wrap gap-2">
            <button
              @click="applyDatePreset('today')"
              class="rounded-lg bg-gray-100 px-3 py-1.5 text-sm text-gray-700 transition-colors hover:bg-gray-200"
            >
              Today
            </button>
            <button
              @click="applyDatePreset('week')"
              class="rounded-lg bg-gray-100 px-3 py-1.5 text-sm text-gray-700 transition-colors hover:bg-gray-200"
            >
              This Week
            </button>
            <button
              @click="applyDatePreset('month')"
              class="rounded-lg bg-gray-100 px-3 py-1.5 text-sm text-gray-700 transition-colors hover:bg-gray-200"
            >
              This Month
            </button>
            <button
              @click="applyDatePreset('quarter')"
              class="rounded-lg bg-gray-100 px-3 py-1.5 text-sm text-gray-700 transition-colors hover:bg-gray-200"
            >
              This Quarter
            </button>
            <button
              @click="applyDatePreset('year')"
              class="rounded-lg bg-gray-100 px-3 py-1.5 text-sm text-gray-700 transition-colors hover:bg-gray-200"
            >
              This Year
            </button>
            <button
              @click="applyDatePreset('last30')"
              class="rounded-lg bg-gray-100 px-3 py-1.5 text-sm text-gray-700 transition-colors hover:bg-gray-200"
            >
              Last 30 Days
            </button>
            <button
              @click="applyDatePreset('last90')"
              class="rounded-lg bg-gray-100 px-3 py-1.5 text-sm text-gray-700 transition-colors hover:bg-gray-200"
            >
              Last 90 Days
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import MdiIcon from '@/components/common/MdiIcon.vue'
import {
  mdiTune,
  mdiCalendarRange,
  mdiAccount,
  mdiOfficeBuilding,
  mdiMapMarker,
  mdiEarth,
  mdiCity,
  mdiCheckCircle,
  mdiDomain,
  mdiClose,
  mdiContentSave,
} from '@mdi/js'
import api from '@/services/api'
import { bookingService, userService } from '@/services/api'
import MultiSelect from './MultiSelect.vue'

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
})

// Emits
const emit = defineEmits(['filters-changed'])

// State
const showFilters = ref(false)
const travellers = ref([])
const organizations = ref([])
const countries = ref([])
const isLoadingCountries = ref(false)
const showSaveButton = ref(false)
const isSaving = ref(false)
const homeCountry = ref('AU')

const localFilters = reactive({
  traveller: props.filters?.traveller || '',
  travellers: props.filters?.travellers || [],
  dateFrom: props.filters?.dateFrom || '',
  dateTo: props.filters?.dateTo || '',
  destinationPreset: props.filters?.destinationPreset || '',
  country: props.filters?.country || '',
  countries: props.filters?.countries || [],
  city: props.filters?.city || '',
  organization: props.filters?.organization || '',
  status: props.filters?.status || '',
  supplier: props.filters?.supplier || '',
})

// Computed
const formattedDateRange = computed(() => {
  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('en-AU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    })
  }
  if (localFilters.dateFrom && localFilters.dateTo) {
    return `${formatDate(localFilters.dateFrom)} - ${formatDate(localFilters.dateTo)}`
  } else if (localFilters.dateFrom) {
    return `From ${formatDate(localFilters.dateFrom)}`
  } else {
    return `Until ${formatDate(localFilters.dateTo)}`
  }
})

const selectedTravellerName = computed(() => {
  if (!localFilters.traveller) return ''
  const traveller = travellers.value.find((t) => t.id === localFilters.traveller)
  return traveller ? traveller.full_name : ''
})

const selectedOrgName = computed(() => {
  if (!localFilters.organization) return ''
  const org = organizations.value.find((o) => o.id === localFilters.organization)
  return org ? org.name : ''
})

const destinationPresetLabel = computed(() => {
  const labels = {
    within_user_country: 'Domestic',
    outside_user_country: 'International',
    north_america: 'North America',
    europe: 'Europe',
    asia: 'Asia',
    oceania: 'Oceania',
    middle_east: 'Middle East',
    south_america: 'South America',
    africa: 'Africa',
    other: 'Other',
  }
  return labels[localFilters.destinationPreset] || localFilters.destinationPreset
})

const hasActiveFilters = computed(() => {
  return !!(
    localFilters.traveller ||
    localFilters.dateFrom ||
    localFilters.dateTo ||
    localFilters.destinationPreset ||
    localFilters.country ||
    localFilters.city ||
    localFilters.organization ||
    localFilters.status ||
    localFilters.supplier
  )
})

// Computed for displaying selected travellers
const selectedTravellersText = computed(() => {
  if (localFilters.travellers.length === 0) return ''
  if (localFilters.travellers.length === 1) {
    const traveller = travellers.value.find(t => t.id === localFilters.travellers[0])
    return traveller ? traveller.full_name : ''
  }
  return `${localFilters.travellers.length} travellers`
})

// Computed for displaying selected countries
const selectedCountriesText = computed(() => {
  if (localFilters.countries.length === 0) return ''
  if (localFilters.countries.length === 1) {
    return getCountryName(localFilters.countries[0])
  }
  return `${localFilters.countries.length} countries`
})

// Transform travellers for MultiSelect component
const travellerOptions = computed(() => {
  return travellers.value.map(t => ({
    value: t.id,
    label: t.full_name
  }))
})

// Transform countries for MultiSelect component
const countryOptions = computed(() => {
  return countries.value.map(c => ({
    value: c.code,
    label: c.name
  }))
})

// Watch for organization changes to cascade filter options
watch(
  () => localFilters.organization,
  (newOrg, oldOrg) => {
    if (newOrg !== oldOrg) {
      console.log('🏢 Organization changed from', oldOrg, 'to', newOrg)

      // Clear dependent filters when organization changes
      if (localFilters.travellers.length > 0) {
        console.log('🧹 Clearing travellers due to organization change')
        localFilters.travellers = []
      }
      if (localFilters.countries.length > 0) {
        console.log('🧹 Clearing countries due to organization change')
        localFilters.countries = []
      }

      // Reload filtered options
      if (props.showTraveller) loadTravellers()
      if (props.showDestinations) loadAvailableCountries()
    }
  }
)

// Watch for filter changes to show "Save as Default" button
watch(
  localFilters,
  () => {
    showSaveButton.value = true
  },
  { deep: true }
)

// Methods
const toggleFilters = () => {
  showFilters.value = !showFilters.value
}

const handleTravellerChange = (newValue) => {
  console.log('🎯 [UniversalFilters] Traveller selection changed:', newValue)
  localFilters.travellers = newValue || []
  console.log('📝 [UniversalFilters] Updated localFilters.travellers:', localFilters.travellers)
  emitFilters()
}

const handleCountryChange = (newValue) => {
  console.log('🌍 [UniversalFilters] Country selection changed:', newValue)
  localFilters.countries = newValue || []
  console.log('📝 [UniversalFilters] Updated localFilters.countries:', localFilters.countries)
  emitFilters()
}

const getCountryName = (code) => {
  const country = countries.value.find((c) => c.code === code)
  return country ? country.name : code
}

const clearTravellers = () => {
  localFilters.travellers = []
  emitFilters()
}

const clearOrganization = () => {
  localFilters.organization = ''
  emitFilters()
}

const clearDestinationPreset = () => {
  localFilters.destinationPreset = ''
  emitFilters()
}

const clearCountries = () => {
  localFilters.countries = []
  emitFilters()
}

const clearCity = () => {
  localFilters.city = ''
  emitFilters()
}

const clearStatus = () => {
  localFilters.status = ''
  emitFilters()
}

const clearSupplier = () => {
  localFilters.supplier = ''
  emitFilters()
}

const clearAllFilters = () => {
  localFilters.traveller = ''
  localFilters.travellers = []
  localFilters.dateFrom = ''
  localFilters.dateTo = ''
  localFilters.destinationPreset = ''
  localFilters.country = ''
  localFilters.countries = []
  localFilters.city = ''
  localFilters.organization = ''
  localFilters.status = ''
  localFilters.supplier = ''
  emitFilters()
}

const emitFilters = () => {
  console.log('🔍 [UniversalFilters] emitFilters called')
  console.log('📊 [UniversalFilters] Current localFilters:', JSON.stringify(localFilters, null, 2))
  
  // Create a clean object with only non-empty values
  const activeFilters = {}
  Object.keys(localFilters).forEach((key) => {
    const value = localFilters[key]
    // Include arrays if they have items, strings if not empty
    if (Array.isArray(value) ? value.length > 0 : value) {
      activeFilters[key] = value
    }
  })
  
  console.log('📤 [UniversalFilters] Emitting filters:', JSON.stringify(activeFilters, null, 2))
  emit('filters-changed', activeFilters)
  console.log('✅ [UniversalFilters] Event emitted')
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

const applyDestinationPreset = (preset) => {
  localFilters.destinationPreset = preset
  emitFilters()
}

// Load travellers for dropdown
const loadTravellers = async () => {
  try {
    const params = {}

    // Filter by organization if selected
    if (localFilters.organization) {
      params.organization = localFilters.organization
      console.log('🏢 Loading travellers for organization:', localFilters.organization)
    }

    const response = await api.get('/travellers/', { params })
    const travellerData = response.data.results || response.data
    console.log(`✅ Loaded ${travellerData.length} travellers`, params.organization ? `for organization ${params.organization}` : '')
    travellers.value = Array.isArray(travellerData) ? travellerData : []
  } catch (error) {
    console.error('Failed to load travellers:', error)
    travellers.value = []
  }
}

// Load organizations for dropdown
const loadOrganizations = async () => {
  try {
    const response = await api.get('/organizations/')
    const orgData = response.data.results || response.data
    console.log('Loaded organizations:', orgData)
    organizations.value = Array.isArray(orgData) ? orgData : []
  } catch (error) {
    console.error('Failed to load organizations:', error)
    organizations.value = []
  }
}

// Load available countries dynamically from backend
const loadAvailableCountries = async () => {
  if (!props.showDestinations) return

  try {
    isLoadingCountries.value = true

    const filters = {}

    // Filter by organization if selected
    if (localFilters.organization) {
      filters.organization = localFilters.organization
      console.log('🏢 Loading countries for organization:', localFilters.organization)
    }

    const data = await bookingService.getAvailableCountries(filters)
    countries.value = data
    console.log(`✅ Loaded ${data.length} countries`, filters.organization ? `for organization ${filters.organization}` : 'with booking data')
  } catch (error) {
    console.error('Failed to load countries:', error)
    countries.value = []
  } finally {
    isLoadingCountries.value = false
  }
}

// Load user's saved filter preferences
const loadUserPreferences = async () => {
  try {
    const data = await userService.getFilterPreferences()

    // Set home country
    homeCountry.value = data.home_country || 'AU'
    console.log(`🏠 User home country: ${homeCountry.value}`)

    // Apply saved filters if they exist
    if (data.default_filters && Object.keys(data.default_filters).length > 0) {
      Object.assign(localFilters, data.default_filters)
      emitFilters()
      showSaveButton.value = false // Don't show save button for loaded preferences
      console.log('✅ Applied saved filter preferences:', data.default_filters)
    }
  } catch (error) {
    console.error('Failed to load filter preferences:', error)
  }
}

// Save current filters as user's default preferences
const saveAsDefault = async () => {
  try {
    isSaving.value = true
    await userService.saveFilterPreferences(localFilters, homeCountry.value)
    showSaveButton.value = false
    console.log('✅ Filter preferences saved successfully')
    // TODO: Show success toast notification
  } catch (error) {
    console.error('❌ Failed to save filter preferences:', error)
    // TODO: Show error toast notification
  } finally {
    isSaving.value = false
  }
}

// Lifecycle
onMounted(() => {
  if (props.showTraveller) loadTravellers()
  if (props.showOrganization) loadOrganizations()
  loadAvailableCountries()
  loadUserPreferences()
})

// Expose methods for parent components
defineExpose({
  clearAllFilters,
  applyDatePreset,
  saveAsDefault,
})
</script>
<template>
  <div class="mb-6">
    <!-- Filter Button & Active Filters Display -->
    <div class="flex items-center justify-between rounded-2xl bg-white p-4 shadow-sm">
      <!-- Active Filters Summary -->
      <div class="flex flex-wrap items-center gap-3">
        <span class="text-sm font-medium text-gray-700">Active Filters:</span>
        
        <!-- Date Range Badge -->
        <div class="flex items-center gap-2 rounded-lg bg-blue-50 px-3 py-1.5 text-sm">
          <MdiIcon :path="mdiCalendarRange" :size="16" class="text-blue-600" />
          <span class="font-medium text-blue-900">{{ formattedDateRange }}</span>
        </div>

        <!-- Organization Badge -->
        <div v-if="localOrganization" class="flex items-center gap-2 rounded-lg bg-purple-50 px-3 py-1.5 text-sm">
          <MdiIcon :path="mdiOfficeBuilding" :size="16" class="text-purple-600" />
          <span class="font-medium text-purple-900">{{ selectedOrgName }}</span>
          <button @click="clearOrganization" class="text-purple-600 hover:text-purple-800">
            <MdiIcon :path="mdiClose" :size="16" />
          </button>
        </div>

        <!-- Origin Country Badge -->
        <div v-if="localOriginCountry" class="flex items-center gap-2 rounded-lg bg-emerald-50 px-3 py-1.5 text-sm">
          <MdiIcon :path="mdiMapMarker" :size="16" class="text-emerald-600" />
          <span class="font-medium text-emerald-900">From: {{ getCountryName(localOriginCountry) }}</span>
          <button @click="clearOriginCountry" class="text-emerald-600 hover:text-emerald-800">
            <MdiIcon :path="mdiClose" :size="16" />
          </button>
        </div>

        <!-- Destination Country Badge -->
        <div v-if="localDestinationCountry" class="flex items-center gap-2 rounded-lg bg-amber-50 px-3 py-1.5 text-sm">
          <MdiIcon :path="mdiMapMarker" :size="16" class="text-amber-600" />
          <span class="font-medium text-amber-900">To: {{ getCountryName(localDestinationCountry) }}</span>
          <button @click="clearDestinationCountry" class="text-amber-600 hover:text-amber-800">
            <MdiIcon :path="mdiClose" :size="16" />
          </button>
        </div>

        <!-- Travel Type Badge (Domestic/International) -->
        <div 
          v-if="travelType" 
          class="flex items-center gap-2 rounded-lg bg-indigo-50 px-3 py-1.5 text-sm"
        >
          <MdiIcon :path="mdiEarth" :size="16" class="text-indigo-600" />
          <span class="font-medium text-indigo-900">{{ travelType }}</span>
          <button @click="clearTravelType" class="text-indigo-600 hover:text-indigo-800">
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

      <!-- Filter Toggle Button -->
      <button
        @click="toggleFilters"
        class="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700"
      >
        <MdiIcon :path="mdiTune" :size="20" class="text-white" />
        {{ showFilters ? 'Hide Filters' : 'Edit Filters' }}
      </button>
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
          <!-- Date Range Picker -->
          <div>
            <label class="mb-2 block text-sm font-medium text-gray-700">Date Range</label>
            <Datepicker
              v-model="localDateRange"
              range
              :enable-time-picker="false"
              :format="dateFormat"
              :preset-ranges="presetRanges"
              placeholder="Select date range"
              class="w-full"
              @update:model-value="handleDateChange"
            />
          </div>

          <!-- Organization Selector -->
          <div>
            <label class="mb-2 block text-sm font-medium text-gray-700">Organization</label>
            <select
              v-model="localOrganization"
              class="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              @change="handleOrganizationChange"
            >
              <option value="">All Organizations</option>
              <option 
                v-for="org in organizations" 
                :key="org?.id || Math.random()" 
                :value="org?.id"
              >
                {{ org?.name || 'Unknown' }}
              </option>
            </select>
          </div>

          <!-- Origin Country -->
          <div>
            <label class="mb-2 block text-sm font-medium text-gray-700">Origin Country</label>
            <select
              v-model="localOriginCountry"
              class="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              @change="handleCountryChange"
            >
              <option value="">All Countries</option>
              <option v-for="country in countries" :key="country.code" :value="country.code">
                {{ country.name }}
              </option>
            </select>
          </div>

          <!-- Destination Country -->
          <div>
            <label class="mb-2 block text-sm font-medium text-gray-700">Destination Country</label>
            <select
              v-model="localDestinationCountry"
              class="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              @change="handleCountryChange"
            >
              <option value="">All Countries</option>
              <option v-for="country in countries" :key="country.code" :value="country.code">
                {{ country.name }}
              </option>
            </select>
          </div>
        </div>

        <!-- Quick Filters / Presets -->
        <div class="mt-6 border-t border-gray-100 pt-4">
          <div class="flex flex-wrap items-center gap-3">
            <span class="text-sm font-medium text-gray-700">Quick Filters:</span>
            
            <!-- Date Filters -->
            <div class="flex items-center gap-2">
              <button
                v-for="preset in quickFilters.filter(f => f.type === 'date')"
                :key="preset.label"
                class="rounded-lg border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 hover:border-gray-400"
                @click="applyQuickFilter(preset)"
              >
                {{ preset.label }}
              </button>
            </div>

            <!-- Divider -->
            <div class="h-6 w-px bg-gray-300"></div>

            <!-- Travel Type Filters -->
            <div class="flex items-center gap-2">
              <button
                v-for="preset in quickFilters.filter(f => f.type === 'domestic' || f.type === 'international')"
                :key="preset.label"
                class="rounded-lg border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 hover:border-gray-400"
                @click="applyQuickFilter(preset)"
              >
                {{ preset.label }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import Datepicker from '@vuepic/vue-datepicker'
import '@vuepic/vue-datepicker/dist/main.css'
import MdiIcon from '@/components/ui/MdiIcon.vue'
import {
  mdiTune,
  mdiCalendarRange,
  mdiOfficeBuilding,
  mdiMapMarker,
  mdiClose,
  mdiEarth,
} from '@mdi/js'

const props = defineProps({
  dateRange: {
    type: Array,
    default: () => [],
  },
  organization: {
    type: String,
    default: '',
  },
  originCountry: {
    type: String,
    default: '',
  },
  destinationCountry: {
    type: String,
    default: '',
  },
  travelType: {
    type: String,
    default: ''
  },
  organizations: {
    type: [Array, Object],
    default: () => [],
  },
})

const emit = defineEmits([
  'update:dateRange',
  'update:organization',
  'update:originCountry',
  'update:travelType'
])

// Local state
const showFilters = ref(false)
const localDateRange = ref(props.dateRange)
const localOrganization = ref(props.organization)
const localOriginCountry = ref(props.originCountry)
const localDestinationCountry = ref(props.destinationCountry)

// Countries list
const countries = [
  { code: 'AU', name: 'Australia' },
  { code: 'NZ', name: 'New Zealand' },
  { code: 'SG', name: 'Singapore' },
  { code: 'US', name: 'United States' },
  { code: 'GB', name: 'United Kingdom' },
  { code: 'JP', name: 'Japan' },
  { code: 'HK', name: 'Hong Kong' },
]

// Computed
const formattedDateRange = computed(() => {
  if (!localDateRange.value || localDateRange.value.length === 0) return 'All Time'
  const [start, end] = localDateRange.value
  const formatDate = (date) => {
    return new Intl.DateTimeFormat('en-AU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    }).format(date)
  }
  return `${formatDate(start)} - ${formatDate(end)}`
})

const selectedOrgName = computed(() => {
  if (!localOrganization.value) return ''
  const org = props.organizations.find((o) => o.id === localOrganization.value)
  return org ? org.name : ''
})

const hasActiveFilters = computed(() => {
  return !!(localOrganization.value || localOriginCountry.value || localDestinationCountry.value)
})

// Methods
const toggleFilters = () => {
  showFilters.value = !showFilters.value
}

const getCountryName = (code) => {
  const country = countries.find((c) => c.code === code)
  return country ? country.name : code
}

const clearOrganization = () => {
  localOrganization.value = ''
  emitFilters()
}

const clearOriginCountry = () => {
  localOriginCountry.value = ''
  emitFilters()
}

const clearDestinationCountry = () => {
  localDestinationCountry.value = ''
  emitFilters()
}

const clearAllFilters = () => {
  localOrganization.value = ''
  localOriginCountry.value = ''
  localDestinationCountry.value = ''
  // Keep date range as default (last 3 months)
  emitFilters()
}

// Date format
const dateFormat = (dates) => {
  if (!dates || dates.length === 0) return ''
  const [start, end] = dates
  const formatDate = (date) => {
    return new Intl.DateTimeFormat('en-AU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    }).format(date)
  }
  return `${formatDate(start)} - ${formatDate(end)}`
}

// Preset date ranges
const presetRanges = [
  {
    label: 'Last 3 Months',
    range: [
      new Date(new Date().setMonth(new Date().getMonth() - 3)),
      new Date(),
    ],
  },
  {
    label: 'Last 6 Months',
    range: [
      new Date(new Date().setMonth(new Date().getMonth() - 6)),
      new Date(),
    ],
  },
  {
    label: 'This Year',
    range: [new Date(new Date().getFullYear(), 0, 1), new Date()],
  },
]

// Quick filters
const quickFilters = [
  { label: 'This Month', days: 30 },
  { label: 'Last Quarter', days: 90 },
  { label: 'This Year', days: 365 },
  { label: 'Domestic', type: 'domestic' },
  { label: 'International', type: 'international' },
]

// Emit filter changes
const emitFilters = () => {
  const filters = {
    dateRange: localDateRange.value,
    organization: localOrganization.value,
    originCountry: localOriginCountry.value,
    destinationCountry: localDestinationCountry.value,
  }
  emit('update:filters', filters)
}

const handleDateChange = () => {
  emitFilters()
}

const handleOrganizationChange = () => {
  emitFilters()
}

const handleCountryChange = () => {
  emitFilters()
}

const applyQuickFilter = (preset) => {
  if (preset.type === 'date') {
    // Date-based quick filter
    const endDate = new Date()
    const startDate = new Date()
    startDate.setDate(startDate.getDate() - preset.days)
    localDateRange.value = [startDate, endDate]
  } else if (preset.type === 'domestic') {
    // Domestic travel (within Australia)
    localOriginCountry.value = 'AU'
    localDestinationCountry.value = 'AU'
  } else if (preset.type === 'international') {
    // International travel (from Australia to anywhere else, or vice versa)
    // Set origin to Australia, clear destination to show all international
    localOriginCountry.value = 'AU'
    localDestinationCountry.value = '' // This will show all non-AU destinations
  }
  
  emitFilters()
}
</script>
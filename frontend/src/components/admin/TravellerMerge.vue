<template>
  <div class="p-6">
    <!-- Header -->
    <div class="mb-6">
      <h2 class="text-xl font-semibold text-gray-900">Traveller Merge</h2>
      <p class="mt-1 text-sm text-gray-600">
        Select travellers to merge within the selected organization
      </p>
    </div>

    <!-- Controls -->
    <div class="mb-6 flex items-center justify-between">
      <div class="flex items-center gap-4">
        <button
          @click="loadAllTravellers"
          :disabled="loading || !selectedOrganization"
          class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
        >
          <span class="mdi mdi-refresh mr-2"></span>
          {{ loading ? 'Loading...' : 'Load Travellers' }}
        </button>

        <button
          @click="findDuplicates"
          :disabled="loading || allTravellers.length === 0"
          class="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md shadow-sm text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
        >
          <span class="mdi mdi-magnify mr-2"></span>
          {{ showingDuplicates ? 'Show All' : 'Find Duplicates' }}
        </button>

        <div v-if="!showingDuplicates" class="flex items-center gap-2">
          <label class="text-sm font-medium text-gray-700">Similarity:</label>
          <input
            v-model.number="minSimilarity"
            type="range"
            min="0.5"
            max="1.0"
            step="0.05"
            class="w-32"
          />
          <span class="text-sm text-gray-600">{{ (minSimilarity * 100).toFixed(0) }}%</span>
        </div>
      </div>

      <button
        v-if="selectedTravellers.length >= 2"
        @click="openMergeModal"
        class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
      >
        <span class="mdi mdi-merge mr-2"></span>
        Merge Selected ({{ selectedTravellers.length }})
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-12">
      <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      <p class="mt-4 text-sm text-gray-600">Loading travellers...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="rounded-md bg-red-50 p-4">
      <div class="flex">
        <span class="mdi mdi-alert-circle text-red-400 text-xl"></span>
        <div class="ml-3">
          <h3 class="text-sm font-medium text-red-800">Error</h3>
          <p class="mt-1 text-sm text-red-700">{{ error }}</p>
        </div>
      </div>
    </div>

    <!-- No Data State -->
    <div v-else-if="allTravellers.length === 0 && !loading" class="text-center py-12">
      <span class="mdi mdi-information-outline text-6xl text-gray-400"></span>
      <h3 class="mt-4 text-lg font-medium text-gray-900">No travellers found</h3>
      <p class="mt-2 text-sm text-gray-600">
        {{ selectedOrganization ? 'Click "Load Travellers" to view traveller records.' : 'Please select an organization first.' }}
      </p>
    </div>

    <!-- Travellers Table -->
    <div v-else class="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
      <!-- Filter Info -->
      <div v-if="showingDuplicates" class="bg-blue-50 border-b border-blue-200 px-4 py-3">
        <div class="flex items-center justify-between">
          <div class="flex items-center">
            <span class="mdi mdi-filter text-blue-600 mr-2"></span>
            <span class="text-sm text-blue-900">
              Showing {{ duplicateGroups.length }} similarity groups ({{ displayedTravellers.length }} travellers)
            </span>
          </div>
          <button
            @click="clearDuplicateFilter"
            class="text-sm text-blue-700 hover:text-blue-900 underline"
          >
            Clear Filter
          </button>
        </div>
      </div>

      <!-- Table -->
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th scope="col" class="w-12 px-6 py-3 text-left">
                <input
                  type="checkbox"
                  :checked="allDisplayedSelected"
                  @change="toggleSelectAll"
                  class="form-checkbox h-4 w-4 text-indigo-600 rounded"
                />
              </th>
              <th v-if="showingDuplicates" scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Group
              </th>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Name
              </th>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Email
              </th>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Phone
              </th>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Bookings
              </th>
              <th v-if="showingDuplicates" scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Similarity
              </th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr
              v-for="traveller in displayedTravellers"
              :key="traveller.id"
              :class="getRowClass(traveller)"
              class="hover:bg-gray-50"
            >
              <td class="px-6 py-4 whitespace-nowrap">
                <input
                  type="checkbox"
                  :value="traveller.id"
                  v-model="selectedTravellers"
                  class="form-checkbox h-4 w-4 text-indigo-600 rounded"
                />
              </td>
              <td v-if="showingDuplicates" class="px-6 py-4 whitespace-nowrap">
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium" :class="getGroupBadgeClass(traveller.groupIndex)">
                  Group {{ traveller.groupIndex + 1 }}
                </span>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm font-medium text-gray-900">
                  {{ traveller.first_name }} {{ traveller.last_name }}
                </div>
                <div v-if="traveller.employee_id" class="text-xs text-gray-500">
                  ID: {{ traveller.employee_id }}
                </div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm text-gray-900">{{ traveller.email || '-' }}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm text-gray-900">{{ traveller.phone || '-' }}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm text-gray-900">{{ traveller.booking_count || 0 }}</div>
              </td>
              <td v-if="showingDuplicates" class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm text-gray-600">
                  {{ traveller.similarity ? (traveller.similarity * 100).toFixed(0) + '%' : '100%' }}
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Table Footer -->
      <div class="bg-gray-50 px-6 py-3 border-t border-gray-200">
        <div class="text-sm text-gray-700">
          Showing {{ displayedTravellers.length }} traveller{{ displayedTravellers.length !== 1 ? 's' : '' }}
          <span v-if="selectedTravellers.length > 0" class="ml-4 font-medium text-indigo-600">
            {{ selectedTravellers.length }} selected
          </span>
        </div>
      </div>
    </div>

    <!-- Merge Modal -->
    <div v-if="showMergeModal" class="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <!-- Modal Header -->
        <div class="bg-gray-50 px-6 py-4 border-b border-gray-200">
          <h3 class="text-lg font-medium text-gray-900">Merge Traveller Records</h3>
        </div>

        <!-- Modal Body -->
        <div class="px-6 py-4">
          <!-- Primary Traveller Selection -->
          <div class="mb-6">
            <h4 class="text-sm font-medium text-gray-900 mb-3">Select primary record (will be kept):</h4>
            <div class="space-y-2">
              <label
                v-for="traveller in selectedTravellerData"
                :key="traveller.id"
                class="flex items-start p-3 border-2 rounded cursor-pointer hover:bg-gray-50"
                :class="primaryTravellerId === traveller.id ? 'border-indigo-500 bg-indigo-50' : 'border-gray-200'"
              >
                <input
                  type="radio"
                  :value="traveller.id"
                  v-model="primaryTravellerId"
                  class="form-radio h-4 w-4 text-indigo-600 mr-3 mt-1"
                />
                <div class="flex-1">
                  <div class="text-sm font-medium text-gray-900">
                    {{ traveller.first_name }} {{ traveller.last_name }}
                  </div>
                  <div class="text-xs text-gray-600 mt-1">
                    <span v-if="traveller.email">{{ traveller.email }}</span>
                    <span v-if="traveller.phone" class="ml-3">{{ traveller.phone }}</span>
                    <span class="ml-3">{{ traveller.booking_count || 0 }} bookings</span>
                  </div>
                </div>
              </label>
            </div>
          </div>

          <!-- Records to Merge -->
          <div class="mb-6">
            <h4 class="text-sm font-medium text-gray-900 mb-2">Records that will be merged:</h4>
            <div class="bg-gray-50 rounded-lg p-4 space-y-2">
              <div v-for="traveller in mergeTravellers" :key="traveller.id" class="text-sm">
                <span class="text-gray-900 font-medium">{{ traveller.first_name }} {{ traveller.last_name }}</span>
                <span class="text-gray-500 ml-2">({{ traveller.booking_count || 0 }} bookings will be reassigned)</span>
              </div>
            </div>
            <p class="mt-2 text-sm text-gray-600">
              Total: <strong>{{ totalBookings }}</strong> bookings will be reassigned to the primary record
            </p>
          </div>

          <!-- Name Selection -->
          <div class="mb-6">
            <h4 class="text-sm font-medium text-gray-900 mb-3">Choose display name:</h4>
            <div class="space-y-2 mb-4">
              <label
                v-for="traveller in selectedTravellerData"
                :key="'name-' + traveller.id"
                class="flex items-center p-3 border-2 rounded cursor-pointer hover:bg-gray-50"
                :class="selectedDisplayName === `${traveller.first_name} ${traveller.last_name}` ? 'border-indigo-500 bg-indigo-50' : 'border-gray-200'"
              >
                <input
                  type="radio"
                  :value="`${traveller.first_name} ${traveller.last_name}`"
                  v-model="selectedDisplayName"
                  class="form-radio h-4 w-4 text-indigo-600 mr-3"
                />
                <span class="text-sm text-gray-900">{{ traveller.first_name }} {{ traveller.last_name }}</span>
              </label>
            </div>

            <!-- Custom name option -->
            <div class="border-2 rounded p-3" :class="customDisplayName ? 'border-indigo-500 bg-indigo-50' : 'border-gray-200'">
              <label class="flex items-start cursor-pointer">
                <input
                  type="radio"
                  value=""
                  v-model="selectedDisplayName"
                  @change="focusCustomNameInput"
                  class="form-radio h-4 w-4 text-indigo-600 mr-3 mt-1"
                />
                <div class="flex-1">
                  <span class="text-sm font-medium text-gray-900 block mb-2">Use custom name</span>
                  <input
                    ref="customNameInput"
                    v-model="customDisplayName"
                    @focus="selectedDisplayName = ''"
                    type="text"
                    placeholder="Enter custom name..."
                    class="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  />
                </div>
              </label>
            </div>
          </div>

          <!-- Merge Explanation -->
          <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div class="flex">
              <span class="mdi mdi-information text-blue-600 text-xl mr-3"></span>
              <div class="text-sm text-blue-900">
                <p class="font-medium mb-1">What happens when you merge:</p>
                <ul class="list-disc list-inside space-y-1 text-blue-800">
                  <li>All {{ totalBookings }} bookings will be reassigned to the primary traveller</li>
                  <li>The {{ mergeTravellers.length }} duplicate record(s) will be deleted</li>
                  <li>An audit record will be created for tracking</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        <!-- Modal Footer -->
        <div class="bg-gray-50 px-6 py-4 border-t border-gray-200 flex items-center justify-end gap-3">
          <button
            @click="closeMergeModal"
            class="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            Cancel
          </button>
          <button
            @click="confirmMerge"
            :disabled="!canMerge"
            class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
          >
            <span class="mdi mdi-check mr-2"></span>
            Confirm Merge
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import api from '@/services/api'

const props = defineProps({
  selectedOrganization: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['duplicates-updated'])

// Reactive state
const minSimilarity = ref(0.7)
const loading = ref(false)
const error = ref('')
const allTravellers = ref([])
const duplicateGroups = ref([])
const showingDuplicates = ref(false)
const selectedTravellers = ref([])
const showMergeModal = ref(false)
const primaryTravellerId = ref(null)
const selectedDisplayName = ref('')
const customDisplayName = ref('')
const customNameInput = ref(null)

// Computed
const displayedTravellers = computed(() => {
  if (showingDuplicates.value) {
    // Flatten duplicate groups with group info
    const result = []
    duplicateGroups.value.forEach((group, groupIndex) => {
      // Add primary
      result.push({
        ...group.primary,
        groupIndex,
        similarity: 1.0
      })
      // Add matches
      group.matches.forEach(traveller => {
        result.push({
          ...traveller,
          groupIndex
        })
      })
    })
    return result
  } else {
    return allTravellers.value
  }
})

const allDisplayedSelected = computed(() => {
  return displayedTravellers.value.length > 0 &&
         displayedTravellers.value.every(t => selectedTravellers.value.includes(t.id))
})

const selectedTravellerData = computed(() => {
  return selectedTravellers.value.map(id => {
    const found = allTravellers.value.find(t => t.id === id)
    return found || null
  }).filter(t => t !== null)
})

const mergeTravellers = computed(() => {
  return selectedTravellerData.value.filter(t => t.id !== primaryTravellerId.value)
})

const totalBookings = computed(() => {
  return mergeTravellers.value.reduce((sum, t) => sum + (t.booking_count || 0), 0)
})

const canMerge = computed(() => {
  return primaryTravellerId.value !== null &&
         (customDisplayName.value.trim() !== '' || selectedDisplayName.value !== '')
})

// Methods
const loadAllTravellers = async () => {
  if (!props.selectedOrganization) {
    error.value = 'Please select an organization first.'
    return
  }

  loading.value = true
  error.value = ''
  showingDuplicates.value = false
  selectedTravellers.value = []

  try {
    const params = { organization_id: props.selectedOrganization }
    const response = await api.get('/data-management/traveller-merge/all_travellers/', { params })
    allTravellers.value = response.data.travellers
  } catch (err) {
    console.error('Error loading travellers:', err)
    error.value = err.response?.data?.error || 'Failed to load travellers'
  } finally {
    loading.value = false
  }
}

const findDuplicates = async () => {
  if (showingDuplicates.value) {
    clearDuplicateFilter()
    return
  }

  loading.value = true
  error.value = ''

  try {
    const params = {
      organization_id: props.selectedOrganization,
      min_similarity: minSimilarity.value
    }

    const response = await api.get('/data-management/traveller-merge/find_duplicates/', { params })
    duplicateGroups.value = response.data.duplicates
    showingDuplicates.value = true
  } catch (err) {
    console.error('Error finding duplicates:', err)
    error.value = err.response?.data?.error || 'Failed to find duplicates'
  } finally {
    loading.value = false
  }
}

const clearDuplicateFilter = () => {
  showingDuplicates.value = false
  duplicateGroups.value = []
}

const toggleSelectAll = () => {
  if (allDisplayedSelected.value) {
    selectedTravellers.value = []
  } else {
    selectedTravellers.value = displayedTravellers.value.map(t => t.id)
  }
}

const getRowClass = (traveller) => {
  if (!showingDuplicates.value) return ''

  const colors = [
    'bg-blue-50',
    'bg-green-50',
    'bg-yellow-50',
    'bg-purple-50',
    'bg-pink-50',
    'bg-indigo-50'
  ]
  return colors[traveller.groupIndex % colors.length]
}

const getGroupBadgeClass = (groupIndex) => {
  const colors = [
    'bg-blue-100 text-blue-800',
    'bg-green-100 text-green-800',
    'bg-yellow-100 text-yellow-800',
    'bg-purple-100 text-purple-800',
    'bg-pink-100 text-pink-800',
    'bg-indigo-100 text-indigo-800'
  ]
  return colors[groupIndex % colors.length]
}

const openMergeModal = () => {
  // Pre-select first traveller as primary
  primaryTravellerId.value = selectedTravellers.value[0]

  // Pre-select first name as display name
  const firstTraveller = selectedTravellerData.value[0]
  if (firstTraveller) {
    selectedDisplayName.value = `${firstTraveller.first_name} ${firstTraveller.last_name}`
  }

  customDisplayName.value = ''
  showMergeModal.value = true
}

const closeMergeModal = () => {
  showMergeModal.value = false
  primaryTravellerId.value = null
  selectedDisplayName.value = ''
  customDisplayName.value = ''
}

const focusCustomNameInput = () => {
  setTimeout(() => {
    customNameInput.value?.focus()
  }, 100)
}

const confirmMerge = async () => {
  const finalName = customDisplayName.value.trim() || selectedDisplayName.value

  if (!finalName || !primaryTravellerId.value) {
    error.value = 'Please select a primary record and display name'
    return
  }

  const mergeData = {
    primary_id: primaryTravellerId.value,
    merge_ids: selectedTravellers.value.filter(id => id !== primaryTravellerId.value),
    chosen_name: customDisplayName.value.trim()
  }

  try {
    const response = await api.post('/data-management/traveller-merge/merge/', mergeData)

    closeMergeModal()

    // Show success message
    alert(`Successfully merged ${response.data.merged_count} traveller record(s). ${response.data.bookings_reassigned} booking(s) reassigned.`)

    // Clear selections and reload
    selectedTravellers.value = []
    await loadAllTravellers()

    emit('duplicates-updated')
  } catch (err) {
    console.error('Error merging travellers:', err)
    error.value = err.response?.data?.error || 'Failed to merge travellers'
  }
}
</script>

<template>
  <div class="p-6">
    <!-- Header -->
    <div class="mb-6">
      <h2 class="text-xl font-semibold text-gray-900">Travel Consultant Merge</h2>
      <p class="mt-1 text-sm text-gray-600">
        Select consultant names to merge and standardize across bookings
      </p>
    </div>

    <!-- Controls -->
    <div class="mb-6 flex items-center justify-between">
      <div class="flex items-center gap-4">
        <button
          @click="loadAllConsultants"
          :disabled="loading || (!selectedTravelAgent && !selectedOrganization)"
          class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
        >
          <span class="mdi mdi-refresh mr-2"></span>
          {{ loading ? 'Loading...' : 'Load Consultants' }}
        </button>

        <button
          @click="findDuplicates"
          :disabled="loading || allConsultants.length === 0"
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
        v-if="selectedConsultants.length >= 2"
        @click="openMergeModal"
        class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
      >
        <span class="mdi mdi-merge mr-2"></span>
        Merge Selected ({{ selectedConsultants.length }})
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-12">
      <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      <p class="mt-4 text-sm text-gray-600">Loading consultants...</p>
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
    <div v-else-if="allConsultants.length === 0 && !loading" class="text-center py-12">
      <span class="mdi mdi-information-outline text-6xl text-gray-400"></span>
      <h3 class="mt-4 text-lg font-medium text-gray-900">No consultants found</h3>
      <p class="mt-2 text-sm text-gray-600">
        {{ selectedTravelAgent || selectedOrganization ? 'Click "Load Consultants" to view consultant names.' : 'Please select a travel agent or organization first.' }}
      </p>
    </div>

    <!-- Consultants Table -->
    <div v-else class="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
      <!-- Filter Info -->
      <div v-if="showingDuplicates" class="bg-blue-50 border-b border-blue-200 px-4 py-3">
        <div class="flex items-center justify-between">
          <div class="flex items-center">
            <span class="mdi mdi-filter text-blue-600 mr-2"></span>
            <span class="text-sm text-blue-900">
              Showing {{ duplicateGroups.length }} similarity groups ({{ displayedConsultants.length }} consultants)
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
                Consultant Name
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
              v-for="consultant in displayedConsultants"
              :key="consultant.name"
              :class="getRowClass(consultant)"
              class="hover:bg-gray-50"
            >
              <td class="px-6 py-4 whitespace-nowrap">
                <input
                  type="checkbox"
                  :value="consultant.name"
                  v-model="selectedConsultants"
                  class="form-checkbox h-4 w-4 text-indigo-600 rounded"
                />
              </td>
              <td v-if="showingDuplicates" class="px-6 py-4 whitespace-nowrap">
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium" :class="getGroupBadgeClass(consultant.groupIndex)">
                  Group {{ consultant.groupIndex + 1 }}
                </span>
              </td>
              <td class="px-6 py-4">
                <div class="text-sm text-gray-900">{{ consultant.name }}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm text-gray-900">{{ consultant.booking_count }}</div>
              </td>
              <td v-if="showingDuplicates" class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm text-gray-600">
                  {{ consultant.similarity ? (consultant.similarity * 100).toFixed(0) + '%' : '100%' }}
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Table Footer -->
      <div class="bg-gray-50 px-6 py-3 border-t border-gray-200">
        <div class="text-sm text-gray-700">
          Showing {{ displayedConsultants.length }} consultant{{ displayedConsultants.length !== 1 ? 's' : '' }}
          <span v-if="selectedConsultants.length > 0" class="ml-4 font-medium text-indigo-600">
            {{ selectedConsultants.length }} selected
          </span>
        </div>
      </div>
    </div>

    <!-- Merge Modal -->
    <div v-if="showMergeModal" class="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <!-- Modal Header -->
        <div class="bg-gray-50 px-6 py-4 border-b border-gray-200">
          <h3 class="text-lg font-medium text-gray-900">Merge Consultant Names</h3>
        </div>

        <!-- Modal Body -->
        <div class="px-6 py-4">
          <!-- What's Being Merged -->
          <div class="mb-6">
            <h4 class="text-sm font-medium text-gray-900 mb-2">Consultant names to be merged:</h4>
            <div class="bg-gray-50 rounded-lg p-4 space-y-2">
              <div v-for="consultant in selectedConsultantData" :key="consultant.name" class="flex items-center justify-between text-sm">
                <span class="text-gray-900">{{ consultant.name }}</span>
                <span class="text-gray-500">({{ consultant.booking_count }} bookings)</span>
              </div>
            </div>
            <p class="mt-2 text-sm text-gray-600">
              Total: <strong>{{ totalSelectedBookings }}</strong> bookings will be updated
            </p>
          </div>

          <!-- Standard Name Selection -->
          <div class="mb-6">
            <h4 class="text-sm font-medium text-gray-900 mb-3">Choose standard name:</h4>
            <div class="space-y-2 mb-4">
              <label
                v-for="consultant in selectedConsultantData"
                :key="'name-' + consultant.name"
                class="flex items-center p-3 border-2 rounded cursor-pointer hover:bg-gray-50"
                :class="selectedStandardName === consultant.name ? 'border-indigo-500 bg-indigo-50' : 'border-gray-200'"
              >
                <input
                  type="radio"
                  :value="consultant.name"
                  v-model="selectedStandardName"
                  class="form-radio h-4 w-4 text-indigo-600 mr-3"
                />
                <span class="text-sm text-gray-900">{{ consultant.name }}</span>
              </label>
            </div>

            <!-- Custom name option -->
            <div class="border-2 rounded p-3" :class="customStandardName ? 'border-indigo-500 bg-indigo-50' : 'border-gray-200'">
              <label class="flex items-start cursor-pointer">
                <input
                  type="radio"
                  value="__custom__"
                  :checked="customStandardName !== ''"
                  @change="selectedStandardName = ''"
                  class="form-radio h-4 w-4 text-indigo-600 mr-3 mt-1"
                />
                <div class="flex-1">
                  <span class="text-sm text-gray-900 font-medium">Use custom name</span>
                  <input
                    v-model="customStandardName"
                    @focus="selectedStandardName = ''"
                    type="text"
                    placeholder="Enter custom name"
                    class="mt-2 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  />
                </div>
              </label>
            </div>
          </div>

          <!-- Warning -->
          <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div class="flex">
              <span class="mdi mdi-alert text-yellow-400 text-xl"></span>
              <div class="ml-3">
                <p class="text-sm text-yellow-800">
                  <strong>Warning:</strong> This will standardize {{ selectedConsultants.length }} consultant name{{ selectedConsultants.length !== 1 ? 's' : '' }}.
                  All bookings with these names will be updated to use the standard name.
                </p>
                <p class="text-sm text-yellow-700 mt-1">
                  You can undo this operation from the Audit Trail tab.
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- Modal Footer -->
        <div class="bg-gray-50 px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
          <button
            @click="closeMergeModal"
            :disabled="merging"
            class="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            @click="confirmMerge"
            :disabled="merging || (!selectedStandardName && !customStandardName)"
            class="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50"
          >
            <span v-if="merging" class="mdi mdi-loading mdi-spin mr-2"></span>
            {{ merging ? 'Merging...' : 'Confirm Merge' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Success Message -->
    <div
      v-if="successMessage"
      class="fixed bottom-4 right-4 bg-green-50 border border-green-200 rounded-lg p-4 shadow-lg z-50 max-w-md"
    >
      <div class="flex items-start">
        <span class="mdi mdi-check-circle text-green-400 text-xl"></span>
        <div class="ml-3">
          <p class="text-sm font-medium text-green-800">{{ successMessage }}</p>
        </div>
        <button
          @click="successMessage = ''"
          class="ml-auto -mr-1 -mt-1 text-green-400 hover:text-green-600"
        >
          <span class="mdi mdi-close"></span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import api from '@/services/api'

const props = defineProps({
  selectedTravelAgent: {
    type: String,
    default: ''
  },
  selectedOrganization: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['duplicates-updated'])

// State
const allConsultants = ref([])
const loading = ref(false)
const error = ref(null)
const minSimilarity = ref(0.7)
const selectedConsultants = ref([])
const showingDuplicates = ref(false)
const duplicateGroups = ref([])
const showMergeModal = ref(false)
const selectedStandardName = ref('')
const customStandardName = ref('')
const merging = ref(false)
const successMessage = ref('')

// Color classes for group badges (6 colors cycling)
const groupColors = [
  { bg: 'bg-blue-100', text: 'text-blue-800', border: 'border-blue-200' },
  { bg: 'bg-green-100', text: 'text-green-800', border: 'border-green-200' },
  { bg: 'bg-yellow-100', text: 'text-yellow-800', border: 'border-yellow-200' },
  { bg: 'bg-purple-100', text: 'text-purple-800', border: 'border-purple-200' },
  { bg: 'bg-pink-100', text: 'text-pink-800', border: 'border-pink-200' },
  { bg: 'bg-indigo-100', text: 'text-indigo-800', border: 'border-indigo-200' }
]

// Computed
const displayedConsultants = computed(() => {
  if (showingDuplicates.value) {
    // Flatten duplicate groups with group index and similarity
    const flattened = []
    duplicateGroups.value.forEach((group, groupIndex) => {
      // Add primary - normalize 'text' field to 'name'
      flattened.push({
        name: group.primary.text,
        booking_count: group.primary.booking_count,
        groupIndex,
        similarity: 1.0
      })
      // Add matches - normalize 'text' field to 'name'
      group.matches.forEach(match => {
        flattened.push({
          name: match.text,
          booking_count: match.booking_count,
          groupIndex,
          similarity: match.similarity_score
        })
      })
    })
    return flattened
  }
  return allConsultants.value
})

const allDisplayedSelected = computed(() => {
  return displayedConsultants.value.length > 0 &&
    displayedConsultants.value.every(consultant => selectedConsultants.value.includes(consultant.name))
})

const selectedConsultantData = computed(() => {
  return allConsultants.value.filter(c => selectedConsultants.value.includes(c.name))
})

const totalSelectedBookings = computed(() => {
  return selectedConsultantData.value.reduce((sum, c) => sum + c.booking_count, 0)
})

// Methods
const loadAllConsultants = async () => {
  if (!props.selectedTravelAgent && !props.selectedOrganization) {
    error.value = 'Please select a travel agent or organization first.'
    return
  }

  loading.value = true
  error.value = null
  selectedConsultants.value = []
  showingDuplicates.value = false

  try {
    const params = {}
    if (props.selectedTravelAgent) {
      params.travel_agent_id = props.selectedTravelAgent
    } else if (props.selectedOrganization) {
      params.organization_id = props.selectedOrganization
    }

    const response = await api.get('/data-management/consultant-merge/all_consultants/', { params })
    allConsultants.value = response.data.consultants || []
  } catch (err) {
    console.error('Error loading consultants:', err)
    allConsultants.value = []

    if (err.response?.status === 403) {
      error.value = 'Permission denied. You must be an admin to access this feature.'
    } else if (err.response?.status === 401) {
      error.value = 'Not authenticated. Please log in.'
    } else {
      error.value = err.response?.data?.error || err.message || 'Failed to load consultants'
    }
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
  error.value = null

  try {
    const params = {
      min_similarity: minSimilarity.value
    }
    if (props.selectedTravelAgent) {
      params.travel_agent_id = props.selectedTravelAgent
    } else if (props.selectedOrganization) {
      params.organization_id = props.selectedOrganization
    }

    const response = await api.get('/data-management/consultant-merge/find_duplicates/', { params })
    duplicateGroups.value = response.data.duplicate_groups || []
    showingDuplicates.value = true
    emit('duplicates-updated', duplicateGroups.value.length)
  } catch (err) {
    console.error('Error finding duplicates:', err)
    error.value = err.response?.data?.error || err.message || 'Failed to find duplicates'
  } finally {
    loading.value = false
  }
}

const clearDuplicateFilter = () => {
  showingDuplicates.value = false
  duplicateGroups.value = []
  selectedConsultants.value = []
  emit('duplicates-updated', 0)
}

const toggleSelectAll = () => {
  if (allDisplayedSelected.value) {
    selectedConsultants.value = []
  } else {
    selectedConsultants.value = displayedConsultants.value.map(c => c.name)
  }
}

const getRowClass = (consultant) => {
  if (!showingDuplicates.value) return ''
  const color = groupColors[consultant.groupIndex % groupColors.length]
  return `border-l-4 ${color.border}`
}

const getGroupBadgeClass = (groupIndex) => {
  const color = groupColors[groupIndex % groupColors.length]
  return `${color.bg} ${color.text}`
}

const openMergeModal = () => {
  // Pre-select first consultant as standard name
  if (selectedConsultants.value.length > 0) {
    selectedStandardName.value = selectedConsultants.value[0]
  }
  customStandardName.value = ''
  showMergeModal.value = true
}

const closeMergeModal = () => {
  showMergeModal.value = false
  selectedStandardName.value = ''
  customStandardName.value = ''
}

const confirmMerge = async () => {
  const finalName = customStandardName.value || selectedStandardName.value

  if (!finalName || selectedConsultants.value.length < 2) {
    return
  }

  merging.value = true

  try {
    // Remember if we were in duplicate view mode
    const wasShowingDuplicates = showingDuplicates.value

    // Determine primary and merge texts
    const primaryText = selectedConsultants.value[0]
    const mergeTexts = selectedConsultants.value.slice(1)

    const mergeData = {
      primary_text: primaryText,
      merge_texts: mergeTexts,
      chosen_text: finalName
    }

    if (props.selectedTravelAgent) {
      mergeData.travel_agent_id = props.selectedTravelAgent
    } else if (props.selectedOrganization) {
      mergeData.organization_id = props.selectedOrganization
    }

    const response = await api.post('/data-management/consultant-merge/merge/', mergeData)

    successMessage.value = `Successfully merged ${selectedConsultants.value.length} consultant names. ${response.data.bookings_updated} bookings updated.`

    // Close modal first
    closeMergeModal()

    // Clear selections
    selectedConsultants.value = []

    // Reload all consultants
    loading.value = true
    const params = {}
    if (props.selectedTravelAgent) {
      params.travel_agent_id = props.selectedTravelAgent
    } else if (props.selectedOrganization) {
      params.organization_id = props.selectedOrganization
    }

    const consultantsResponse = await api.get('/data-management/consultant-merge/all_consultants/', { params })
    allConsultants.value = consultantsResponse.data.consultants || []

    // If we were showing duplicates, refresh them
    if (wasShowingDuplicates) {
      const duplicatesParams = {
        ...params,
        min_similarity: minSimilarity.value
      }
      const duplicatesResponse = await api.get('/data-management/consultant-merge/find_duplicates/', { params: duplicatesParams })
      duplicateGroups.value = duplicatesResponse.data.duplicate_groups || []
      showingDuplicates.value = true
      emit('duplicates-updated', duplicateGroups.value.length)
    } else {
      showingDuplicates.value = false
      duplicateGroups.value = []
    }

    loading.value = false

    // Clear success message after 5 seconds
    setTimeout(() => {
      successMessage.value = ''
    }, 5000)
  } catch (err) {
    console.error('Error merging consultants:', err)
    error.value = err.response?.data?.error || 'Failed to merge consultant names'
    loading.value = false
  } finally {
    merging.value = false
  }
}
</script>

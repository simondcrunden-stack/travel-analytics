<template>
  <div class="p-6">
    <!-- Header -->
    <div class="mb-6">
      <h2 class="text-xl font-semibold text-gray-900">Service Fee Description Merge</h2>
      <p class="mt-1 text-sm text-gray-600">
        Select descriptions to merge and standardize across service fees
      </p>
    </div>

    <!-- Controls -->
    <div class="mb-6 flex items-center justify-between">
      <div class="flex items-center gap-4">
        <button
          @click="loadAllDescriptions"
          :disabled="loading || (!selectedTravelAgent && !selectedOrganization)"
          class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
        >
          <span class="mdi mdi-refresh mr-2"></span>
          {{ loading ? 'Loading...' : 'Load Descriptions' }}
        </button>

        <button
          @click="findDuplicates"
          :disabled="loading || allDescriptions.length === 0"
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
        v-if="selectedDescriptions.length >= 2"
        @click="openMergeModal"
        class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
      >
        <span class="mdi mdi-merge mr-2"></span>
        Merge Selected ({{ selectedDescriptions.length }})
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-12">
      <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      <p class="mt-4 text-sm text-gray-600">Loading descriptions...</p>
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
    <div v-else-if="allDescriptions.length === 0 && !loading" class="text-center py-12">
      <span class="mdi mdi-information-outline text-6xl text-gray-400"></span>
      <h3 class="mt-4 text-lg font-medium text-gray-900">No descriptions found</h3>
      <p class="mt-2 text-sm text-gray-600">
        {{ selectedTravelAgent || selectedOrganization ? 'Click "Load Descriptions" to view service fee descriptions.' : 'Please select a travel agent or organization first.' }}
      </p>
    </div>

    <!-- Descriptions Table -->
    <div v-else class="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
      <!-- Filter Info -->
      <div v-if="showingDuplicates" class="bg-blue-50 border-b border-blue-200 px-4 py-3">
        <div class="flex items-center justify-between">
          <div class="flex items-center">
            <span class="mdi mdi-filter text-blue-600 mr-2"></span>
            <span class="text-sm text-blue-900">
              Showing {{ duplicateGroups.length }} similarity groups ({{ displayedDescriptions.length }} descriptions)
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
                Description
              </th>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Fees Count
              </th>
              <th v-if="showingDuplicates" scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Similarity
              </th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr
              v-for="desc in displayedDescriptions"
              :key="desc.description"
              :class="getRowClass(desc)"
              class="hover:bg-gray-50"
            >
              <td class="px-6 py-4 whitespace-nowrap">
                <input
                  type="checkbox"
                  :value="desc.description"
                  v-model="selectedDescriptions"
                  class="form-checkbox h-4 w-4 text-indigo-600 rounded"
                />
              </td>
              <td v-if="showingDuplicates" class="px-6 py-4 whitespace-nowrap">
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium" :class="getGroupBadgeClass(desc.groupIndex)">
                  Group {{ desc.groupIndex + 1 }}
                </span>
              </td>
              <td class="px-6 py-4">
                <div class="text-sm text-gray-900">{{ desc.description }}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm text-gray-900">{{ desc.count }}</div>
              </td>
              <td v-if="showingDuplicates" class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm text-gray-600">
                  {{ desc.similarity ? (desc.similarity * 100).toFixed(0) + '%' : '100%' }}
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Table Footer -->
      <div class="bg-gray-50 px-6 py-3 border-t border-gray-200">
        <div class="text-sm text-gray-700">
          Showing {{ displayedDescriptions.length }} description{{ displayedDescriptions.length !== 1 ? 's' : '' }}
          <span v-if="selectedDescriptions.length > 0" class="ml-4 font-medium text-indigo-600">
            {{ selectedDescriptions.length }} selected
          </span>
        </div>
      </div>
    </div>

    <!-- Merge Modal -->
    <div v-if="showMergeModal" class="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <!-- Modal Header -->
        <div class="bg-gray-50 px-6 py-4 border-b border-gray-200">
          <h3 class="text-lg font-medium text-gray-900">Merge Service Fee Descriptions</h3>
        </div>

        <!-- Modal Body -->
        <div class="px-6 py-4">
          <!-- What's Being Merged -->
          <div class="mb-6">
            <h4 class="text-sm font-medium text-gray-900 mb-2">Descriptions to be merged:</h4>
            <div class="bg-gray-50 rounded-lg p-4 space-y-2">
              <div v-for="desc in selectedDescriptionData" :key="desc.description" class="flex items-center justify-between text-sm">
                <span class="text-gray-900">{{ desc.description }}</span>
                <span class="text-gray-500">({{ desc.count }} fees)</span>
              </div>
            </div>
            <p class="mt-2 text-sm text-gray-600">
              Total: <strong>{{ totalSelectedFees }}</strong> service fees will be updated
            </p>
          </div>

          <!-- Standard Description Selection -->
          <div class="mb-6">
            <h4 class="text-sm font-medium text-gray-900 mb-3">Choose standard description:</h4>

            <!-- Radio options for existing descriptions -->
            <div class="space-y-2 mb-4">
              <label
                v-for="desc in selectedDescriptionData"
                :key="desc.description"
                class="flex items-center p-3 border-2 rounded cursor-pointer hover:bg-gray-50"
                :class="selectedStandardDescription === desc.description ? 'border-indigo-500 bg-indigo-50' : 'border-gray-200'"
              >
                <input
                  type="radio"
                  :value="desc.description"
                  v-model="selectedStandardDescription"
                  class="form-radio h-4 w-4 text-indigo-600 mr-3"
                />
                <span class="text-sm text-gray-900">{{ desc.description }}</span>
              </label>
            </div>

            <!-- Custom description option -->
            <div class="border-2 rounded p-3" :class="customDescription ? 'border-indigo-500 bg-indigo-50' : 'border-gray-200'">
              <label class="flex items-start cursor-pointer">
                <input
                  type="radio"
                  value=""
                  v-model="selectedStandardDescription"
                  @change="focusCustomInput"
                  class="form-radio h-4 w-4 text-indigo-600 mr-3 mt-1"
                />
                <div class="flex-1">
                  <span class="text-sm font-medium text-gray-900 block mb-2">Use custom description</span>
                  <input
                    ref="customDescriptionInput"
                    v-model="customDescription"
                    @focus="selectedStandardDescription = ''"
                    type="text"
                    placeholder="Enter new standardized description..."
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
                  <li>All {{ totalSelectedFees }} service fees will be updated to use the chosen description</li>
                  <li>Standardization rules will be created automatically for future imports</li>
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

// Reactive state
const minSimilarity = ref(0.7)
const loading = ref(false)
const error = ref('')
const allDescriptions = ref([])
const duplicateGroups = ref([])
const showingDuplicates = ref(false)
const selectedDescriptions = ref([])
const showMergeModal = ref(false)
const selectedStandardDescription = ref('')
const customDescription = ref('')
const customDescriptionInput = ref(null)

// Computed
const displayedDescriptions = computed(() => {
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
      // Add similar descriptions
      group.similar.forEach(desc => {
        result.push({
          ...desc,
          groupIndex
        })
      })
    })
    return result
  } else {
    return allDescriptions.value
  }
})

const allDisplayedSelected = computed(() => {
  return displayedDescriptions.value.length > 0 &&
         displayedDescriptions.value.every(desc => selectedDescriptions.value.includes(desc.description))
})

const selectedDescriptionData = computed(() => {
  return selectedDescriptions.value.map(desc => {
    const found = allDescriptions.value.find(d => d.description === desc)
    return found || { description: desc, count: 0 }
  })
})

const totalSelectedFees = computed(() => {
  return selectedDescriptionData.value.reduce((sum, desc) => sum + desc.count, 0)
})

const canMerge = computed(() => {
  return customDescription.value.trim() !== '' || selectedStandardDescription.value !== ''
})

// Methods
const loadAllDescriptions = async () => {
  if (!props.selectedTravelAgent && !props.selectedOrganization) {
    error.value = 'Please select a travel agent or organization first.'
    return
  }

  loading.value = true
  error.value = ''
  showingDuplicates.value = false
  selectedDescriptions.value = []

  try {
    const params = {}
    if (props.selectedTravelAgent) {
      params.travel_agent_id = props.selectedTravelAgent
    } else if (props.selectedOrganization) {
      params.organization_id = props.selectedOrganization
    }

    const response = await api.get('/data-management/service-fee-merge/all_descriptions/', { params })
    allDescriptions.value = response.data.descriptions
  } catch (err) {
    console.error('Error loading descriptions:', err)
    error.value = err.response?.data?.error || 'Failed to load descriptions'
  } finally {
    loading.value = false
  }
}

const findDuplicates = async () => {
  if (showingDuplicates.value) {
    // Clear filter
    clearDuplicateFilter()
    return
  }

  loading.value = true
  error.value = ''

  try {
    const params = { min_similarity: minSimilarity.value }
    if (props.selectedTravelAgent) {
      params.travel_agent_id = props.selectedTravelAgent
    } else if (props.selectedOrganization) {
      params.organization_id = props.selectedOrganization
    }

    const response = await api.get('/data-management/service-fee-merge/find_duplicates/', { params })
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
    selectedDescriptions.value = []
  } else {
    selectedDescriptions.value = displayedDescriptions.value.map(d => d.description)
  }
}

const getRowClass = (desc) => {
  if (!showingDuplicates.value) return ''

  // Alternating colors for different groups
  const colors = [
    'bg-blue-50',
    'bg-green-50',
    'bg-yellow-50',
    'bg-purple-50',
    'bg-pink-50',
    'bg-indigo-50'
  ]
  return colors[desc.groupIndex % colors.length]
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
  // Pre-select first description
  selectedStandardDescription.value = selectedDescriptions.value[0]
  customDescription.value = ''
  showMergeModal.value = true
}

const closeMergeModal = () => {
  showMergeModal.value = false
  selectedStandardDescription.value = ''
  customDescription.value = ''
}

const focusCustomInput = () => {
  setTimeout(() => {
    customDescriptionInput.value?.focus()
  }, 100)
}

const confirmMerge = async () => {
  const finalDescription = customDescription.value.trim() || selectedStandardDescription.value

  if (!finalDescription) {
    error.value = 'Please select or enter a standard description'
    return
  }

  const mergeData = {
    primary_description: selectedDescriptions.value[0],
    merge_descriptions: selectedDescriptions.value,
    chosen_description: customDescription.value.trim()
  }

  if (props.selectedTravelAgent) {
    mergeData.travel_agent_id = props.selectedTravelAgent
  } else if (props.selectedOrganization) {
    mergeData.organization_id = props.selectedOrganization
  }

  try {
    const response = await api.post('/data-management/service-fee-merge/merge/', mergeData)

    closeMergeModal()

    // Show success message
    alert(`Successfully standardized ${response.data.merged_count} description(s) across ${response.data.fees_updated} service fees. ${response.data.rules_created} standardization rule(s) created.`)

    // Clear selections and reload
    selectedDescriptions.value = []
    await loadAllDescriptions()

    emit('duplicates-updated')
  } catch (err) {
    console.error('Error merging descriptions:', err)
    error.value = err.response?.data?.error || 'Failed to merge descriptions'
  }
}
</script>

<template>
  <div class="p-6">
    <!-- Header -->
    <div class="mb-6">
      <h2 class="text-xl font-semibold text-gray-900">Service Fee Description Merge</h2>
      <p class="mt-1 text-sm text-gray-600">
        Find and standardize duplicate service fee description variations
      </p>
    </div>

    <!-- Controls -->
    <div class="mb-6 flex items-center gap-4">
      <button
        @click="loadDuplicates"
        :disabled="loading || (!selectedTravelAgent && !selectedOrganization)"
        class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
      >
        <span class="mdi mdi-refresh mr-2"></span>
        {{ loading ? 'Searching...' : 'Find Duplicates' }}
      </button>

      <div class="flex items-center gap-2">
        <label class="text-sm font-medium text-gray-700">Similarity Threshold:</label>
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

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-12">
      <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      <p class="mt-4 text-sm text-gray-600">Searching for duplicates...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="rounded-md bg-red-50 p-4">
      <div class="flex">
        <span class="mdi mdi-alert-circle text-red-400 text-xl"></span>
        <div class="ml-3">
          <h3 class="text-sm font-medium text-red-800">Error loading duplicates</h3>
          <p class="mt-1 text-sm text-red-700">{{ error }}</p>
        </div>
      </div>
    </div>

    <!-- No Duplicates Found -->
    <div v-else-if="duplicateGroups.length === 0 && !loading" class="text-center py-12">
      <span class="mdi mdi-check-circle text-6xl text-green-500"></span>
      <h3 class="mt-4 text-lg font-medium text-gray-900">No duplicates found</h3>
      <p class="mt-2 text-sm text-gray-600">All service fee descriptions appear to be unique.</p>
    </div>

    <!-- Manual Merge Section -->
    <div v-if="!loading" class="mb-8 bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
      <div class="bg-indigo-50 px-4 py-3 border-b border-indigo-200">
        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-sm font-medium text-indigo-900">Manual Merge Override</h3>
            <p class="text-xs text-indigo-700 mt-1">
              Manually select descriptions to merge that weren't automatically grouped
            </p>
          </div>
          <button
            @click="toggleManualMerge"
            class="inline-flex items-center px-3 py-1.5 border border-indigo-300 text-xs font-medium rounded text-indigo-700 bg-white hover:bg-indigo-50"
          >
            <span class="mdi" :class="showManualMerge ? 'mdi-chevron-up' : 'mdi-chevron-down'"></span>
            {{ showManualMerge ? 'Hide' : 'Show' }}
          </button>
        </div>
      </div>

      <div v-if="showManualMerge" class="p-4">
        <!-- Search and Select Descriptions -->
        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Search and select descriptions to merge:
          </label>
          <div class="relative" ref="searchContainer">
            <input
              v-model="descriptionSearchQuery"
              @input="filterDescriptions"
              @focus="showDescriptionDropdown = true"
              type="text"
              placeholder="Type to search descriptions..."
              class="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            />
            <span class="absolute right-3 top-2.5 mdi mdi-magnify text-gray-400"></span>

            <!-- Dropdown with filtered descriptions -->
            <div v-if="showDescriptionDropdown && filteredDescriptions.length > 0" class="absolute z-10 mt-1 w-full max-h-60 overflow-y-auto border border-gray-300 rounded-md bg-white shadow-lg">
              <label
                v-for="desc in filteredDescriptions"
                :key="desc.description"
                class="flex items-center px-3 py-2 hover:bg-gray-50 cursor-pointer border-b border-gray-100 last:border-b-0"
                @click.stop
              >
                <input
                  type="checkbox"
                  :value="desc.description"
                  v-model="manuallySelectedDescriptions"
                  class="form-checkbox h-4 w-4 text-indigo-600 rounded mr-3"
                  @click.stop
                />
                <div class="flex-1">
                  <span class="text-sm text-gray-900">{{ desc.description }}</span>
                  <span class="ml-2 text-xs text-gray-500">({{ desc.count }} fees)</span>
                </div>
              </label>
            </div>
          </div>
        </div>

        <!-- Selected Descriptions -->
        <div v-if="manuallySelectedDescriptions.length > 0" class="mb-4">
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Selected descriptions ({{ manuallySelectedDescriptions.length }}):
          </label>
          <div class="flex flex-wrap gap-2">
            <span
              v-for="desc in manuallySelectedDescriptions"
              :key="desc"
              class="inline-flex items-center px-3 py-1 rounded-full text-sm bg-indigo-100 text-indigo-800"
            >
              {{ desc }}
              <button
                @click="removeManualSelection(desc)"
                class="ml-2 text-indigo-600 hover:text-indigo-800"
              >
                <span class="mdi mdi-close-circle text-sm"></span>
              </button>
            </span>
          </div>
        </div>

        <!-- Merge Button -->
        <div v-if="manuallySelectedDescriptions.length >= 2" class="flex items-center justify-between bg-gray-50 border border-gray-200 rounded p-3">
          <p class="text-sm text-gray-700">
            Ready to merge {{ manuallySelectedDescriptions.length }} descriptions
          </p>
          <button
            @click="openManualMergeDialog"
            class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700"
          >
            <span class="mdi mdi-merge mr-2"></span>
            Standardize Selected
          </button>
        </div>
        <div v-else class="bg-yellow-50 border border-yellow-200 rounded p-3">
          <p class="text-xs text-yellow-800">
            <span class="mdi mdi-information"></span>
            Select at least 2 descriptions to merge
          </p>
        </div>
      </div>
    </div>

    <!-- Duplicate Groups -->
    <div v-else class="space-y-6">
      <div
        v-for="(group, index) in duplicateGroups"
        :key="index"
        class="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden"
      >
        <!-- Group Header -->
        <div class="bg-gray-50 px-4 py-3 border-b border-gray-200">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-sm font-medium text-gray-900">
                Potential Duplicate Group {{ index + 1 }}
              </h3>
              <p class="text-xs text-gray-500 mt-1">
                {{ group.similar.length + 1 }} similar variations found
                <span v-if="selectedMergeDescriptions[index] && selectedMergeDescriptions[index].length > 0" class="text-indigo-600 font-medium">
                  • {{ selectedMergeDescriptions[index].length }} selected for merge
                </span>
              </p>
            </div>
            <button
              @click="openMergeDialog(group, index)"
              :disabled="!selectedMergeDescriptions[index] || selectedMergeDescriptions[index].length === 0"
              class="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span class="mdi mdi-merge mr-1"></span>
              Standardize Descriptions
            </button>
          </div>
        </div>

        <!-- Instruction -->
        <div v-if="!selectedMergeDescriptions[index] || selectedMergeDescriptions[index].length === 0" class="px-4 py-2 bg-yellow-50 border-b border-yellow-100">
          <p class="text-xs text-yellow-800">
            <span class="mdi mdi-information"></span>
            <strong>Step 1:</strong> Check the boxes next to the description variations you want to standardize
          </p>
        </div>

        <!-- Description Variations -->
        <div class="p-4">
          <div class="space-y-2">
            <!-- Primary Description -->
            <label class="flex items-center p-3 border-2 border-indigo-500 bg-indigo-50 rounded cursor-pointer">
              <input
                type="checkbox"
                :value="group.primary.description"
                v-model="selectedMergeDescriptions[index]"
                class="form-checkbox h-4 w-4 text-indigo-600 rounded"
              />
              <div class="ml-3 flex-1">
                <span class="font-semibold text-gray-900">{{ group.primary.description }}</span>
                <span class="ml-2 text-xs text-gray-500">({{ group.primary.count }} fees)</span>
                <span class="ml-2 px-2 py-0.5 bg-indigo-100 text-indigo-800 text-xs rounded-full">Primary</span>
              </div>
            </label>

            <!-- Similar Descriptions -->
            <label
              v-for="desc in group.similar"
              :key="desc.description"
              class="flex items-center p-3 border border-gray-300 rounded cursor-pointer hover:bg-gray-50"
            >
              <input
                type="checkbox"
                :value="desc.description"
                v-model="selectedMergeDescriptions[index]"
                class="form-checkbox h-4 w-4 text-indigo-600 rounded"
              />
              <div class="ml-3 flex-1">
                <span class="font-medium text-gray-900">{{ desc.description }}</span>
                <span class="ml-2 text-xs text-gray-500">({{ desc.count }} fees)</span>
                <span class="ml-2 px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-full">
                  {{ (desc.similarity * 100).toFixed(0) }}% match
                </span>
              </div>
            </label>
          </div>
        </div>
      </div>
    </div>

    <!-- Merge Dialog -->
    <div v-if="showMergeDialog" class="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg shadow-xl max-w-lg w-full mx-4">
        <div class="px-6 py-4 border-b border-gray-200">
          <h3 class="text-lg font-medium text-gray-900">Standardize Service Fee Descriptions</h3>
        </div>

        <div class="px-6 py-4">
          <p class="text-sm text-gray-600 mb-4">
            You are about to standardize {{ mergeSelection.length }} description variation(s) across
            <strong>{{ totalFeeCount }}</strong> service fees.
          </p>

          <div class="space-y-3 mb-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">
                Choose the standard description:
              </label>
              <div class="space-y-2">
                <label
                  v-for="desc in mergeSelection"
                  :key="desc.description"
                  class="flex items-center p-2 border rounded cursor-pointer hover:bg-gray-50"
                  :class="selectedStandardDescription === desc.description ? 'border-indigo-500 bg-indigo-50' : 'border-gray-300'"
                >
                  <input
                    type="radio"
                    :value="desc.description"
                    v-model="selectedStandardDescription"
                    class="form-radio h-4 w-4 text-indigo-600"
                  />
                  <span class="ml-2 text-sm">{{ desc.description }}</span>
                  <span class="ml-auto text-xs text-gray-500">({{ desc.count }} fees)</span>
                </label>
              </div>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">
                Or enter a custom description:
              </label>
              <input
                v-model="customDescription"
                type="text"
                placeholder="Enter custom description..."
                class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              />
            </div>
          </div>

          <div class="bg-yellow-50 border border-yellow-200 rounded p-3">
            <p class="text-xs text-yellow-800">
              <span class="mdi mdi-alert"></span>
              This action will update all service fee records with the selected variations to use the standard description.
            </p>
          </div>
        </div>

        <div class="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-end gap-2">
          <button
            @click="closeMergeDialog"
            class="px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            @click="confirmMerge"
            :disabled="!selectedStandardDescription && !customDescription"
            class="px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50"
          >
            Standardize Descriptions
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
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
const duplicateGroups = ref([])
const selectedMergeDescriptions = ref({})
const showMergeDialog = ref(false)
const selectedGroup = ref(null)
const selectedGroupIndex = ref(null)
const mergeSelection = ref([])
const selectedStandardDescription = ref('')
const customDescription = ref('')

// Manual merge state
const showManualMerge = ref(false)
const allDescriptions = ref([])
const filteredDescriptions = ref([])
const descriptionSearchQuery = ref('')
const showDescriptionDropdown = ref(false)
const manuallySelectedDescriptions = ref([])
const isManualMerge = ref(false)
const searchContainer = ref(null)

// Computed
const totalFeeCount = computed(() => {
  return mergeSelection.value.reduce((sum, desc) => sum + desc.count, 0)
})

// Methods
const loadDuplicates = async () => {
  if (!props.selectedTravelAgent && !props.selectedOrganization) {
    error.value = 'Please select a travel agent or organization first.'
    return
  }

  loading.value = true
  error.value = ''

  const params = {
    min_similarity: minSimilarity.value
  }

  if (props.selectedTravelAgent) {
    params.travel_agent_id = props.selectedTravelAgent
  } else if (props.selectedOrganization) {
    params.organization_id = props.selectedOrganization
  }

  try {
    const response = await api.get('/data-management/service-fee-merge/find_duplicates/', {
      params
    })

    duplicateGroups.value = response.data.duplicates
    emit('duplicates-updated', duplicateGroups.value.length)

    // Initialize selected merge descriptions
    selectedMergeDescriptions.value = {}
    duplicateGroups.value.forEach((group, index) => {
      selectedMergeDescriptions.value[index] = []
    })
  } catch (err) {
    console.error('Error loading duplicates:', err)
    error.value = err.response?.data?.error || 'Failed to load duplicate descriptions'
    emit('duplicates-updated', 0)
  } finally {
    loading.value = false
  }
}

const openMergeDialog = (group, index) => {
  selectedGroup.value = group
  selectedGroupIndex.value = index

  // Build merge selection from checked items
  const selectedDescs = selectedMergeDescriptions.value[index] || []
  mergeSelection.value = [
    { description: group.primary.description, count: group.primary.count },
    ...group.similar.filter(d => selectedDescs.includes(d.description))
  ]

  // Pre-select primary as standard
  selectedStandardDescription.value = group.primary.description
  customDescription.value = ''

  showMergeDialog.value = true
}

const closeMergeDialog = () => {
  showMergeDialog.value = false
  selectedGroup.value = null
  selectedGroupIndex.value = null
  mergeSelection.value = []
  selectedStandardDescription.value = ''
  customDescription.value = ''
}

const confirmMerge = async () => {
  const chosenDescription = customDescription.value || selectedStandardDescription.value

  let mergeData

  if (isManualMerge.value) {
    // Manual merge - use manually selected descriptions
    mergeData = {
      primary_description: manuallySelectedDescriptions.value[0],
      merge_descriptions: manuallySelectedDescriptions.value,
      chosen_description: customDescription.value
    }
  } else {
    // Auto merge - use group-based selection
    mergeData = {
      primary_description: selectedGroup.value.primary.description,
      merge_descriptions: mergeSelection.value.map(d => d.description),
      chosen_description: customDescription.value
    }
  }

  if (props.selectedTravelAgent) {
    mergeData.travel_agent_id = props.selectedTravelAgent
  } else if (props.selectedOrganization) {
    mergeData.organization_id = props.selectedOrganization
  }

  try {
    const response = await api.post('/data-management/service-fee-merge/merge/', mergeData)

    closeMergeDialog()

    // Show success message and reload
    alert(`Successfully standardized ${response.data.merged_count} description(s) across ${response.data.fees_updated} service fees. ${response.data.rules_created} standardization rule(s) created.`)

    // Clear manual selections if it was a manual merge
    if (isManualMerge.value) {
      manuallySelectedDescriptions.value = []
      descriptionSearchQuery.value = ''
      isManualMerge.value = false
    }

    loadDuplicates()
  } catch (err) {
    console.error('Error merging descriptions:', err)
    error.value = err.response?.data?.error || 'Failed to merge descriptions'
  }
}

// Manual merge methods
const toggleManualMerge = async () => {
  showManualMerge.value = !showManualMerge.value

  if (showManualMerge.value && allDescriptions.value.length === 0) {
    await loadAllDescriptions()
  }
}

const loadAllDescriptions = async () => {
  if (!props.selectedTravelAgent && !props.selectedOrganization) {
    error.value = 'Please select a travel agent or organization first.'
    return
  }

  try {
    const params = {}

    if (props.selectedTravelAgent) {
      params.travel_agent_id = props.selectedTravelAgent
    } else if (props.selectedOrganization) {
      params.organization_id = props.selectedOrganization
    }

    const response = await api.get('/data-management/service-fee-merge/all_descriptions/', {
      params
    })

    allDescriptions.value = response.data.descriptions
    filteredDescriptions.value = allDescriptions.value
  } catch (err) {
    console.error('Error loading descriptions:', err)
    error.value = err.response?.data?.error || 'Failed to load descriptions'
  }
}

const filterDescriptions = () => {
  const query = descriptionSearchQuery.value.toLowerCase()

  if (!query) {
    filteredDescriptions.value = allDescriptions.value
  } else {
    filteredDescriptions.value = allDescriptions.value.filter(desc =>
      desc.description.toLowerCase().includes(query)
    )
  }

  showDescriptionDropdown.value = true
}

const removeManualSelection = (description) => {
  manuallySelectedDescriptions.value = manuallySelectedDescriptions.value.filter(d => d !== description)
}

const openManualMergeDialog = () => {
  isManualMerge.value = true

  // Build merge selection from manually selected descriptions
  const selectedDescs = manuallySelectedDescriptions.value.map(desc => {
    const found = allDescriptions.value.find(d => d.description === desc)
    return found || { description: desc, count: 0 }
  })

  mergeSelection.value = selectedDescs

  // Pre-select first description as standard
  selectedStandardDescription.value = manuallySelectedDescriptions.value[0]
  customDescription.value = ''

  showMergeDialog.value = true
}

// Close dropdown when clicking outside
const handleClickOutside = (event) => {
  if (searchContainer.value && !searchContainer.value.contains(event.target)) {
    showDescriptionDropdown.value = false
  }
}

// Add/remove event listener on mount/unmount
onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

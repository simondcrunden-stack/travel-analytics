<template>
  <div class="p-6">
    <!-- Header -->
    <div class="mb-6">
      <h2 class="text-xl font-semibold text-gray-900">Travel Consultant Merge</h2>
      <p class="mt-1 text-sm text-gray-600">
        Find and standardize duplicate consultant name variations in the selected organization
      </p>
    </div>

    <!-- Controls -->
    <div class="mb-6 flex items-center gap-4">
      <button
        @click="loadDuplicates"
        :disabled="loading || !selectedOrganization"
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
      <p class="mt-2 text-sm text-gray-600">All consultant names appear to be unique.</p>
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
                {{ group.matches.length + 1 }} similar variations found
                <span v-if="selectedMergeTexts[index] && selectedMergeTexts[index].length > 0" class="text-indigo-600 font-medium">
                  • {{ selectedMergeTexts[index].length }} selected for merge
                </span>
              </p>
            </div>
            <button
              @click="openMergeDialog(group, index)"
              :disabled="!selectedMergeTexts[index] || selectedMergeTexts[index].length === 0"
              class="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span class="mdi mdi-merge mr-1"></span>
              Standardize Names
            </button>
          </div>
        </div>

        <!-- Instruction -->
        <div v-if="!selectedMergeTexts[index] || selectedMergeTexts[index].length === 0" class="px-4 py-2 bg-yellow-50 border-b border-yellow-100">
          <p class="text-xs text-yellow-800">
            <span class="mdi mdi-information"></span>
            <strong>Step 1:</strong> Check the boxes next to the name variations you want to standardize
          </p>
        </div>

        <!-- Name Variations -->
        <div class="divide-y divide-gray-200">
          <!-- Primary Variation -->
          <div class="px-4 py-3 bg-blue-50">
            <div class="flex items-start">
              <input
                type="radio"
                :name="`group-${index}-primary`"
                :checked="true"
                disabled
                class="mt-1 h-4 w-4 text-indigo-600 border-gray-300"
              />
              <div class="ml-3 flex-1">
                <div class="flex items-center justify-between">
                  <div>
                    <p class="text-sm font-medium text-gray-900">
                      {{ group.primary.text }}
                      <span class="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                        Primary
                      </span>
                    </p>
                  </div>
                  <div class="text-right">
                    <p class="text-xs text-gray-500">{{ group.primary.booking_count }} bookings</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Matching Variations -->
          <div
            v-for="match in group.matches"
            :key="match.text"
            class="px-4 py-3 hover:bg-gray-50"
          >
            <div class="flex items-start">
              <input
                type="checkbox"
                :value="match.text"
                v-model="selectedMergeTexts[index]"
                class="mt-1 h-4 w-4 text-indigo-600 border-gray-300 rounded"
              />
              <div class="ml-3 flex-1">
                <div class="flex items-center justify-between">
                  <div>
                    <p class="text-sm font-medium text-gray-900">
                      {{ match.text }}
                      <span class="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800">
                        {{ (match.similarity_score * 100).toFixed(0) }}% similar
                      </span>
                    </p>
                  </div>
                  <div class="text-right">
                    <p class="text-xs text-gray-500">{{ match.booking_count }} bookings</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Merge Confirmation Dialog -->
    <div
      v-if="showMergeDialog"
      class="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50"
      @click.self="closeMergeDialog"
    >
      <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <!-- Dialog Header -->
        <div class="px-6 py-4 border-b border-gray-200">
          <h3 class="text-lg font-medium text-gray-900">Standardize Consultant Names</h3>
          <p class="mt-1 text-sm text-gray-600">
            Review and confirm the standardization operation
          </p>
        </div>

        <!-- Dialog Content -->
        <div class="px-6 py-4 space-y-4">
          <!-- Primary Name -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Primary name (will be kept)</label>
            <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p class="font-medium text-gray-900">{{ selectedGroup?.primary.text }}</p>
              <p class="text-sm text-gray-600 mt-1">{{ selectedGroup?.primary.booking_count }} bookings</p>
            </div>
          </div>

          <!-- Variations to Standardize -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Variations to standardize ({{ mergeSelection.length }})
            </label>
            <div class="space-y-2">
              <div
                v-for="variation in mergeSelection"
                :key="variation.text"
                class="bg-gray-50 border border-gray-200 rounded-lg p-3"
              >
                <p class="text-sm font-medium text-gray-900">{{ variation.text }}</p>
                <p class="text-xs text-gray-600">{{ variation.booking_count }} bookings will be updated</p>
              </div>
            </div>
          </div>

          <!-- Standard Name Selection -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Choose standard name</label>
            <select
              v-model="mergeOptions.chosenText"
              class="mt-1 block w-full pl-3 pr-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md bg-white"
            >
              <option value="">Keep primary name</option>
              <option
                v-for="variation in allVariationsInMerge"
                :key="variation.text"
                :value="variation.text"
              >
                {{ variation.text }}
              </option>
              <option value="__custom__">Enter custom name...</option>
            </select>

            <input
              v-if="mergeOptions.chosenText === '__custom__'"
              v-model="mergeOptions.customText"
              type="text"
              placeholder="Enter standard name"
              class="mt-2 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            />
          </div>

          <!-- Warning -->
          <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div class="flex">
              <span class="mdi mdi-alert text-yellow-400 text-xl"></span>
              <div class="ml-3">
                <p class="text-sm text-yellow-800">
                  <strong>Warning:</strong> This action will standardize {{ mergeSelection.length }} name variation(s).
                  All bookings with these variations will be updated to use the standard name.
                </p>
                <p class="text-sm text-yellow-700 mt-1">
                  You can undo this operation from the Audit Trail tab.
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- Dialog Footer -->
        <div class="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-end gap-3">
          <button
            @click="closeMergeDialog"
            :disabled="merging"
            class="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            Cancel
          </button>
          <button
            @click="confirmMerge"
            :disabled="merging || mergeSelection.length === 0"
            class="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
          >
            <span v-if="merging" class="mdi mdi-loading mdi-spin mr-2"></span>
            {{ merging ? 'Standardizing...' : 'Confirm Standardization' }}
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
  selectedOrganization: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['duplicates-updated'])

// State
const duplicateGroups = ref([])
const loading = ref(false)
const error = ref(null)
const minSimilarity = ref(0.7)
const selectedMergeTexts = ref({})
const showMergeDialog = ref(false)
const selectedGroup = ref(null)
const selectedGroupIndex = ref(null)
const merging = ref(false)
const successMessage = ref('')

// Merge options
const mergeOptions = ref({
  chosenText: '',
  customText: ''
})

// Computed
const mergeSelection = computed(() => {
  if (!selectedGroup.value || selectedGroupIndex.value === null) return []
  const selectedTexts = selectedMergeTexts.value[selectedGroupIndex.value]
  const textsArray = Array.isArray(selectedTexts) ? selectedTexts : []
  return selectedGroup.value.matches.filter(m => textsArray.includes(m.text))
})

const allVariationsInMerge = computed(() => {
  if (!selectedGroup.value) return []
  return [selectedGroup.value.primary, ...selectedGroup.value.matches]
})

// Methods
const loadDuplicates = async () => {
  if (!props.selectedOrganization) {
    error.value = 'Please select an organization first.'
    return
  }

  loading.value = true
  error.value = null

  try {
    const response = await api.get('/data-management/consultant-merge/find_duplicates/', {
      params: {
        min_similarity: minSimilarity.value,
        organization_id: props.selectedOrganization
      }
    })

    duplicateGroups.value = response.data.duplicate_groups || []

    // Initialize selectedMergeTexts with empty arrays for each group
    const initialSelectedTexts = {}
    duplicateGroups.value.forEach((group, index) => {
      initialSelectedTexts[index] = []
    })
    selectedMergeTexts.value = initialSelectedTexts

    emit('duplicates-updated', duplicateGroups.value.length)
  } catch (err) {
    console.error('Error loading duplicates:', err)
    duplicateGroups.value = []
    emit('duplicates-updated', 0)

    if (err.response?.status === 403) {
      error.value = 'Permission denied. You must be an admin to access this feature.'
    } else if (err.response?.status === 401) {
      error.value = 'Not authenticated. Please log in.'
    } else {
      error.value = err.response?.data?.error || err.message || 'Failed to load duplicates'
    }
  } finally {
    loading.value = false
  }
}

const openMergeDialog = (group, index) => {
  selectedGroup.value = group
  selectedGroupIndex.value = duplicateGroups.value.indexOf(group)
  showMergeDialog.value = true
  mergeOptions.value = {
    chosenText: '',
    customText: ''
  }
}

const closeMergeDialog = () => {
  showMergeDialog.value = false
  selectedGroup.value = null
  selectedGroupIndex.value = null
}

const confirmMerge = async () => {
  if (mergeSelection.value.length === 0) {
    return
  }

  merging.value = true

  try {
    const chosenText = mergeOptions.value.chosenText === '__custom__'
      ? mergeOptions.value.customText
      : mergeOptions.value.chosenText

    const response = await api.post('/data-management/consultant-merge/merge/', {
      primary_text: selectedGroup.value.primary.text,
      merge_texts: mergeSelection.value.map(m => m.text),
      chosen_text: chosenText,
      organization_id: props.selectedOrganization
    })

    successMessage.value = `Successfully standardized consultant name across ${response.data.bookings_updated} booking(s).`

    // Remove the merged group from the list
    duplicateGroups.value.splice(selectedGroupIndex.value, 1)
    emit('duplicates-updated', duplicateGroups.value.length)

    closeMergeDialog()

    // Clear success message after 5 seconds
    setTimeout(() => {
      successMessage.value = ''
    }, 5000)
  } catch (err) {
    console.error('Error standardizing consultant names:', err)
    error.value = err.response?.data?.error || 'Failed to standardize consultant names'
  } finally {
    merging.value = false
  }
}
</script>

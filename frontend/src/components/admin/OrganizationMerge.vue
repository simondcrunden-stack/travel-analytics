<template>
  <div class="p-6">
    <!-- Header -->
    <div class="mb-6">
      <h2 class="text-xl font-semibold text-gray-900">Organization Merge</h2>
      <p class="mt-1 text-sm text-gray-600">
        Find and merge duplicate organizations. This will reassign all related data (travellers, bookings, budgets) to the primary organization.
      </p>
    </div>

    <!-- Controls -->
    <div class="mb-6 flex items-center gap-4">
      <button
        @click="loadDuplicates"
        :disabled="loading"
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
    <div v-else-if="duplicates.length === 0 && searched" class="text-center py-12">
      <span class="mdi mdi-check-circle text-6xl text-green-500"></span>
      <h3 class="mt-4 text-lg font-medium text-gray-900">No duplicates found</h3>
      <p class="mt-2 text-sm text-gray-600">All organizations appear to be unique.</p>
    </div>

    <!-- Duplicate Groups -->
    <div v-else class="space-y-6">
      <div
        v-for="(group, index) in duplicates"
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
                {{ group.total_records }} organizations found
              </p>
            </div>
            <button
              @click="performMerge"
              :disabled="merging || !mergeGroups[index]"
              class="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span class="mdi mdi-merge mr-1"></span>
              Merge Organizations
            </button>
          </div>
        </div>

        <!-- Organization List -->
        <div class="p-4">
          <div class="space-y-2">
            <!-- Primary Organization -->
            <label class="flex items-center p-3 border-2 border-indigo-500 bg-indigo-50 rounded cursor-pointer">
              <input
                type="radio"
                :name="`group-${index}`"
                :value="group.primary.id"
                v-model="selectedOrganizations[index]"
                class="form-radio h-4 w-4 text-indigo-600"
              />
              <div class="ml-3 flex-1">
                <div class="font-semibold text-gray-900">{{ group.primary.name }}</div>
                <div class="text-xs text-gray-500 mt-1">
                  Code: {{ group.primary.code }} •
                  {{ group.primary.traveller_count }} travellers •
                  {{ group.primary.booking_count }} bookings •
                  {{ group.primary.budget_count }} budgets
                </div>
              </div>
              <span class="ml-2 px-2 py-0.5 bg-indigo-100 text-indigo-800 text-xs rounded-full">Primary</span>
            </label>

            <!-- Similar Organizations -->
            <label
              v-for="org in group.similar"
              :key="org.id"
              class="flex items-center p-3 border border-gray-300 rounded cursor-pointer hover:bg-gray-50"
            >
              <input
                type="radio"
                :name="`group-${index}`"
                :value="org.id"
                v-model="selectedOrganizations[index]"
                class="form-radio h-4 w-4 text-indigo-600"
              />
              <div class="ml-3 flex-1">
                <div class="font-medium text-gray-900">{{ org.name }}</div>
                <div class="text-xs text-gray-500 mt-1">
                  Code: {{ org.code }} •
                  {{ org.traveller_count }} travellers •
                  {{ org.booking_count }} bookings •
                  {{ org.budget_count }} budgets
                </div>
              </div>
              <span class="ml-2 px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-full">
                {{ (org.similarity * 100).toFixed(0) }}% match
              </span>
            </label>
          </div>

          <!-- Merge Selection -->
          <div class="mt-4 bg-gray-50 border border-gray-200 rounded p-3">
            <label class="flex items-center">
              <input
                type="checkbox"
                v-model="mergeGroups[index]"
                class="form-checkbox h-4 w-4 text-indigo-600 rounded"
              />
              <span class="ml-2 text-sm font-medium text-gray-700">Select this group for merging</span>
            </label>
          </div>

          <!-- Custom Name Input -->
          <div v-if="mergeGroups[index]" class="mt-4">
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Custom Organization Name (optional)
            </label>
            <input
              v-model="customNames[index]"
              type="text"
              :placeholder="getSelectedOrgName(index, group)"
              class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            />
            <p class="text-xs text-gray-500 mt-1">
              Leave blank to use the selected organization's name
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Merge Button (bulk) -->
    <div v-if="canMerge && duplicates.length > 0" class="mt-6 flex justify-between items-center">
      <div class="text-sm text-gray-600">
        {{ selectedGroupCount }} group(s) selected
      </div>
      <button
        @click="performMerge"
        :disabled="merging"
        class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50"
      >
        <span v-if="merging" class="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></span>
        {{ merging ? 'Merging...' : `Merge ${selectedGroupCount} Group(s)` }}
      </button>
    </div>

    <!-- Success Message -->
    <div v-if="successMessage" class="mt-6 rounded-md bg-green-50 p-4">
      <div class="flex">
        <span class="mdi mdi-check-circle text-green-400 text-xl"></span>
        <div class="ml-3">
          <p class="text-sm font-medium text-green-800">{{ successMessage }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import api from '@/services/api'

const emit = defineEmits(['duplicates-updated'])

// Reactive state
const minSimilarity = ref(0.7)
const loading = ref(false)
const merging = ref(false)
const searched = ref(false)
const error = ref('')
const successMessage = ref('')
const duplicates = ref([])
const selectedOrganizations = ref({})
const mergeGroups = ref({})
const customNames = ref({})

// Computed properties
const canMerge = computed(() => {
  return Object.values(mergeGroups.value).some(v => v === true)
})

const selectedGroupCount = computed(() => {
  return Object.values(mergeGroups.value).filter(v => v === true).length
})

// Methods
const loadDuplicates = async () => {
  loading.value = true
  error.value = ''
  searched.value = false

  try {
    const response = await api.get('/data-management/organization-merge/find_duplicates/', {
      params: {
        min_similarity: minSimilarity.value
      }
    })

    duplicates.value = response.data.duplicates
    searched.value = true

    // Emit count for parent component
    emit('duplicates-updated', duplicates.value.length)

    // Initialize selections
    selectedOrganizations.value = {}
    mergeGroups.value = {}
    customNames.value = {}

    duplicates.value.forEach((group, index) => {
      selectedOrganizations.value[index] = group.primary.id
      mergeGroups.value[index] = false
      customNames.value[index] = ''
    })
  } catch (err) {
    console.error('Error loading duplicates:', err)
    error.value = err.response?.data?.error || 'Failed to load duplicates'
    emit('duplicates-updated', 0)
  } finally {
    loading.value = false
  }
}

const getSelectedOrgName = (index, group) => {
  const selectedId = selectedOrganizations.value[index]
  if (selectedId === group.primary.id) {
    return group.primary.name
  }
  const selected = group.similar.find(o => o.id === selectedId)
  return selected?.name || group.primary.name
}

const performMerge = async () => {
  merging.value = true
  error.value = ''
  successMessage.value = ''

  try {
    const mergePromises = []

    // Process each selected group
    for (let index = 0; index < duplicates.value.length; index++) {
      if (!mergeGroups.value[index]) continue

      const group = duplicates.value[index]
      const primaryId = selectedOrganizations.value[index]

      // Collect all organization IDs except the selected primary
      const allOrgs = [group.primary, ...group.similar]
      const mergeIds = allOrgs
        .filter(o => o.id !== primaryId)
        .map(o => o.id)

      if (mergeIds.length === 0) continue

      const mergeData = {
        primary_id: primaryId,
        merge_ids: mergeIds,
        chosen_name: customNames.value[index] || ''
      }

      mergePromises.push(
        api.post('/data-management/organization-merge/merge/', mergeData)
      )
    }

    const results = await Promise.all(mergePromises)

    const totalMerged = results.reduce((sum, r) => sum + r.data.merged_count, 0)
    const totalReassigned = results.reduce((sum, r) => {
      const reassigned = r.data.reassigned
      return sum + reassigned.travellers + reassigned.bookings + reassigned.budgets
    }, 0)

    successMessage.value = `Successfully merged ${totalMerged} organization(s) and reassigned ${totalReassigned} related record(s). Refreshing...`

    // Reload duplicates after a short delay
    setTimeout(() => {
      loadDuplicates()
      successMessage.value = ''
    }, 2000)

  } catch (err) {
    console.error('Error merging organizations:', err)
    error.value = err.response?.data?.error || 'Failed to merge organizations'
  } finally {
    merging.value = false
  }
}

// Watch for error to auto-clear
watch(error, (newError) => {
  if (newError) {
    setTimeout(() => {
      error.value = ''
    }, 5000)
  }
})
</script>

<template>
  <div class="organization-merge">
    <div class="mb-6">
      <h2 class="text-2xl font-semibold text-gray-900 mb-2">Organization Merge</h2>
      <p class="text-gray-600">
        Find and merge duplicate organizations. This will reassign all related data (travellers, bookings, budgets) to the primary organization.
      </p>
    </div>

    <!-- Find Duplicates Section -->
    <div class="bg-white border border-gray-200 rounded-lg p-6 mb-6 shadow-sm">
      <h3 class="text-lg font-medium text-gray-900 mb-4">Find Duplicate Organizations</h3>

      <div class="mb-4">
        <label class="block text-sm font-medium text-gray-700 mb-2">
          Minimum Similarity Score
        </label>
        <input
          v-model.number="minSimilarity"
          type="range"
          min="0.5"
          max="1.0"
          step="0.05"
          class="w-full"
        />
        <div class="text-sm text-gray-600 mt-1">
          Current: {{ (minSimilarity * 100).toFixed(0) }}% similarity
        </div>
      </div>

      <button
        @click="loadDuplicates"
        :disabled="loading"
        class="btn btn-primary"
      >
        <span v-if="loading" class="loading loading-spinner loading-sm"></span>
        {{ loading ? 'Searching...' : 'Find Duplicates' }}
      </button>
    </div>

    <!-- Error Display -->
    <div v-if="error" class="alert alert-error mb-6">
      <span>{{ error }}</span>
    </div>

    <!-- Duplicates List -->
    <div v-if="duplicates.length > 0" class="space-y-4">
      <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
        <p class="text-blue-800 font-medium">
          Found {{ duplicates.length }} group(s) of potentially duplicate organizations
        </p>
      </div>

      <div
        v-for="(group, index) in duplicates"
        :key="index"
        class="bg-white border border-gray-200 rounded-lg p-6 shadow-sm"
      >
        <div class="flex items-center justify-between mb-4">
          <h4 class="text-lg font-semibold text-gray-900">
            Duplicate Group {{ index + 1 }}
          </h4>
          <span class="badge badge-info">
            {{ group.total_records }} organizations
          </span>
        </div>

        <!-- Organization List -->
        <div class="space-y-2 mb-4">
          <!-- Primary Organization -->
          <label class="flex items-center p-3 border-2 border-blue-500 bg-blue-50 rounded cursor-pointer">
            <input
              type="radio"
              :name="`group-${index}`"
              :value="group.primary.id"
              v-model="selectedOrganizations[index]"
              class="radio radio-primary mr-3"
            />
            <div class="flex-1">
              <div class="font-semibold text-gray-900">{{ group.primary.name }}</div>
              <div class="text-sm text-gray-600">
                Code: {{ group.primary.code }} |
                {{ group.primary.traveller_count }} travellers |
                {{ group.primary.booking_count }} bookings |
                {{ group.primary.budget_count }} budgets
              </div>
            </div>
            <span class="badge badge-primary ml-2">Primary</span>
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
              class="radio radio-primary mr-3"
            />
            <div class="flex-1">
              <div class="font-semibold text-gray-900">{{ org.name }}</div>
              <div class="text-sm text-gray-600">
                Code: {{ org.code }} |
                {{ org.traveller_count }} travellers |
                {{ org.booking_count }} bookings |
                {{ org.budget_count }} budgets
              </div>
            </div>
            <span class="badge badge-outline ml-2">{{ (org.similarity * 100).toFixed(0) }}% match</span>
          </label>
        </div>

        <!-- Merge Selection -->
        <div class="bg-gray-50 border border-gray-200 rounded p-4 mb-4">
          <label class="flex items-center">
            <input
              type="checkbox"
              v-model="mergeGroups[index]"
              class="checkbox checkbox-primary mr-2"
            />
            <span class="font-medium">Select this group for merging</span>
          </label>
        </div>

        <!-- Custom Name Input -->
        <div v-if="mergeGroups[index]" class="mb-4">
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Custom Organization Name (optional)
          </label>
          <input
            v-model="customNames[index]"
            type="text"
            :placeholder="getSelectedOrgName(index, group)"
            class="input input-bordered w-full"
          />
          <p class="text-sm text-gray-500 mt-1">
            Leave blank to use the selected organization's name
          </p>
        </div>
      </div>
    </div>

    <!-- No Duplicates Message -->
    <div v-else-if="searched && duplicates.length === 0" class="bg-gray-50 border border-gray-200 rounded-lg p-6 text-center">
      <p class="text-gray-600">No duplicate organizations found. Try adjusting the similarity threshold.</p>
    </div>

    <!-- Merge Button -->
    <div v-if="canMerge" class="mt-6 flex justify-end">
      <button
        @click="performMerge"
        :disabled="merging"
        class="btn btn-success btn-lg"
      >
        <span v-if="merging" class="loading loading-spinner loading-sm"></span>
        {{ merging ? 'Merging...' : `Merge ${selectedGroupCount} Group(s)` }}
      </button>
    </div>

    <!-- Success Message -->
    <div v-if="successMessage" class="alert alert-success mt-6">
      <span>{{ successMessage }}</span>
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

<style scoped>
.organization-merge {
  max-width: 1200px;
}
</style>

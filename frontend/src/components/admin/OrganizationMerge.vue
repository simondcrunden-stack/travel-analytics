<template>
  <div class="p-6">
    <!-- Header -->
    <div class="mb-6">
      <h2 class="text-xl font-semibold text-gray-900">Organization Merge</h2>
      <p class="mt-1 text-sm text-gray-600">
        Select organizations to merge and reassign all related data
      </p>
    </div>

    <!-- Controls -->
    <div class="mb-6 flex items-center justify-between">
      <div class="flex items-center gap-4">
        <button
          @click="loadAllOrganizations"
          :disabled="loading"
          class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
        >
          <span class="mdi mdi-refresh mr-2"></span>
          {{ loading ? 'Loading...' : 'Load Organizations' }}
        </button>

        <button
          @click="findDuplicates"
          :disabled="loading || allOrganizations.length === 0"
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
        v-if="selectedOrganizations.length >= 2"
        @click="openMergeModal"
        class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
      >
        <span class="mdi mdi-merge mr-2"></span>
        Merge Selected ({{ selectedOrganizations.length }})
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-12">
      <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      <p class="mt-4 text-sm text-gray-600">Loading organizations...</p>
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
    <div v-else-if="allOrganizations.length === 0 && !loading" class="text-center py-12">
      <span class="mdi mdi-information-outline text-6xl text-gray-400"></span>
      <h3 class="mt-4 text-lg font-medium text-gray-900">No organizations found</h3>
      <p class="mt-2 text-sm text-gray-600">Click "Load Organizations" to view organization records.</p>
    </div>

    <!-- Organizations Table -->
    <div v-else class="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
      <!-- Filter Info -->
      <div v-if="showingDuplicates" class="bg-blue-50 border-b border-blue-200 px-4 py-3">
        <div class="flex items-center justify-between">
          <div class="flex items-center">
            <span class="mdi mdi-filter text-blue-600 mr-2"></span>
            <span class="text-sm text-blue-900">
              Showing {{ duplicateGroups.length }} similarity groups ({{ displayedOrganizations.length }} organizations)
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
                Code
              </th>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Travellers
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
              v-for="org in displayedOrganizations"
              :key="org.id"
              :class="getRowClass(org)"
              class="hover:bg-gray-50"
            >
              <td class="px-6 py-4 whitespace-nowrap">
                <input
                  type="checkbox"
                  :value="org.id"
                  v-model="selectedOrganizations"
                  class="form-checkbox h-4 w-4 text-indigo-600 rounded"
                />
              </td>
              <td v-if="showingDuplicates" class="px-6 py-4 whitespace-nowrap">
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium" :class="getGroupBadgeClass(org.groupIndex)">
                  Group {{ org.groupIndex + 1 }}
                </span>
              </td>
              <td class="px-6 py-4">
                <div class="text-sm font-medium text-gray-900">{{ org.name }}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm text-gray-900">{{ org.code || '-' }}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm text-gray-900">{{ org.traveller_count || 0 }}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm text-gray-900">{{ org.booking_count || 0 }}</div>
              </td>
              <td v-if="showingDuplicates" class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm text-gray-600">
                  {{ org.similarity ? (org.similarity * 100).toFixed(0) + '%' : '100%' }}
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Table Footer -->
      <div class="bg-gray-50 px-6 py-3 border-t border-gray-200">
        <div class="text-sm text-gray-700">
          Showing {{ displayedOrganizations.length}} organization{{ displayedOrganizations.length !== 1 ? 's' : '' }}
          <span v-if="selectedOrganizations.length > 0" class="ml-4 font-medium text-indigo-600">
            {{ selectedOrganizations.length }} selected
          </span>
        </div>
      </div>
    </div>

    <!-- Merge Modal -->
    <div v-if="showMergeModal" class="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <!-- Modal Header -->
        <div class="bg-gray-50 px-6 py-4 border-b border-gray-200">
          <h3 class="text-lg font-medium text-gray-900">Merge Organizations</h3>
        </div>

        <!-- Modal Body -->
        <div class="px-6 py-4">
          <!-- Primary Organization Selection -->
          <div class="mb-6">
            <h4 class="text-sm font-medium text-gray-900 mb-3">Select primary organization (will be kept):</h4>
            <div class="space-y-2">
              <label
                v-for="org in selectedOrganizationData"
                :key="org.id"
                class="flex items-start p-3 border-2 rounded cursor-pointer hover:bg-gray-50"
                :class="primaryOrganizationId === org.id ? 'border-indigo-500 bg-indigo-50' : 'border-gray-200'"
              >
                <input
                  type="radio"
                  :value="org.id"
                  v-model="primaryOrganizationId"
                  class="form-radio h-4 w-4 text-indigo-600 mr-3 mt-1"
                />
                <div class="flex-1">
                  <div class="text-sm font-medium text-gray-900">{{ org.name }}</div>
                  <div class="text-xs text-gray-600 mt-1">
                    <span>{{ org.traveller_count || 0 }} travellers</span>
                    <span class="ml-3">{{ org.booking_count || 0 }} bookings</span>
                  </div>
                </div>
              </label>
            </div>
          </div>

          <!-- Organizations to Merge -->
          <div class="mb-6">
            <h4 class="text-sm font-medium text-gray-900 mb-2">Organizations that will be merged:</h4>
            <div class="bg-gray-50 rounded-lg p-4 space-y-2">
              <div v-for="org in mergeOrganizations" :key="org.id" class="text-sm">
                <span class="text-gray-900 font-medium">{{ org.name }}</span>
                <span class="text-gray-500 ml-2">({{ org.traveller_count || 0 }} travellers, {{ org.booking_count || 0 }} bookings)</span>
              </div>
            </div>
            <p class="mt-2 text-sm text-gray-600">
              Total: <strong>{{ totalTravellers }}</strong> travellers and <strong>{{ totalBookings }}</strong> bookings will be reassigned
            </p>
          </div>

          <!-- Name Selection -->
          <div class="mb-6">
            <h4 class="text-sm font-medium text-gray-900 mb-3">Choose organization name:</h4>
            <div class="space-y-2 mb-4">
              <label
                v-for="org in selectedOrganizationData"
                :key="'name-' + org.id"
                class="flex items-center p-3 border-2 rounded cursor-pointer hover:bg-gray-50"
                :class="selectedOrganizationName === org.name ? 'border-indigo-500 bg-indigo-50' : 'border-gray-200'"
              >
                <input
                  type="radio"
                  :value="org.name"
                  v-model="selectedOrganizationName"
                  class="form-radio h-4 w-4 text-indigo-600 mr-3"
                />
                <span class="text-sm text-gray-900">{{ org.name }}</span>
              </label>
            </div>

            <!-- Custom name option -->
            <div class="border-2 rounded p-3" :class="customOrganizationName ? 'border-indigo-500 bg-indigo-50' : 'border-gray-200'">
              <label class="flex items-start cursor-pointer">
                <input
                  type="radio"
                  value=""
                  v-model="selectedOrganizationName"
                  @change="focusCustomNameInput"
                  class="form-radio h-4 w-4 text-indigo-600 mr-3 mt-1"
                />
                <div class="flex-1">
                  <span class="text-sm font-medium text-gray-900 block mb-2">Use custom name</span>
                  <input
                    ref="customNameInput"
                    v-model="customOrganizationName"
                    @focus="selectedOrganizationName = ''"
                    type="text"
                    placeholder="Enter custom organization name..."
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
                  <li>All {{ totalTravellers }} travellers will be reassigned to the primary organization</li>
                  <li>All {{ totalBookings }} bookings will be reassigned to the primary organization</li>
                  <li>The {{ mergeOrganizations.length }} duplicate organization(s) will be deleted</li>
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

const emit = defineEmits(['duplicates-updated'])

// Reactive state
const minSimilarity = ref(0.7)
const loading = ref(false)
const error = ref('')
const allOrganizations = ref([])
const duplicateGroups = ref([])
const showingDuplicates = ref(false)
const selectedOrganizations = ref([])
const showMergeModal = ref(false)
const primaryOrganizationId = ref(null)
const selectedOrganizationName = ref('')
const customOrganizationName = ref('')
const customNameInput = ref(null)

// Computed
const displayedOrganizations = computed(() => {
  if (showingDuplicates.value) {
    const result = []
    duplicateGroups.value.forEach((group, groupIndex) => {
      result.push({
        ...group.primary,
        groupIndex,
        similarity: 1.0
      })
      group.similar.forEach(org => {
        result.push({
          ...org,
          groupIndex
        })
      })
    })
    return result
  } else {
    return allOrganizations.value
  }
})

const allDisplayedSelected = computed(() => {
  return displayedOrganizations.value.length > 0 &&
         displayedOrganizations.value.every(org => selectedOrganizations.value.includes(org.id))
})

const selectedOrganizationData = computed(() => {
  return selectedOrganizations.value.map(id => {
    const found = allOrganizations.value.find(org => org.id === id)
    return found || null
  }).filter(org => org !== null)
})

const mergeOrganizations = computed(() => {
  return selectedOrganizationData.value.filter(org => org.id !== primaryOrganizationId.value)
})

const totalTravellers = computed(() => {
  return mergeOrganizations.value.reduce((sum, org) => sum + (org.traveller_count || 0), 0)
})

const totalBookings = computed(() => {
  return mergeOrganizations.value.reduce((sum, org) => sum + (org.booking_count || 0), 0)
})

const canMerge = computed(() => {
  return primaryOrganizationId.value !== null &&
         (customOrganizationName.value.trim() !== '' || selectedOrganizationName.value !== '')
})

// Methods
const loadAllOrganizations = async () => {
  loading.value = true
  error.value = ''
  showingDuplicates.value = false
  selectedOrganizations.value = []

  try {
    const response = await api.get('/data-management/organization-merge/all_organizations/')
    allOrganizations.value = response.data.organizations
  } catch (err) {
    console.error('Error loading organizations:', err)
    error.value = err.response?.data?.error || 'Failed to load organizations'
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
    const params = { min_similarity: minSimilarity.value }
    const response = await api.get('/data-management/organization-merge/find_duplicates/', { params })
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
    selectedOrganizations.value = []
  } else {
    selectedOrganizations.value = displayedOrganizations.value.map(org => org.id)
  }
}

const getRowClass = (org) => {
  if (!showingDuplicates.value) return ''

  const colors = [
    'bg-blue-50',
    'bg-green-50',
    'bg-yellow-50',
    'bg-purple-50',
    'bg-pink-50',
    'bg-indigo-50'
  ]
  return colors[org.groupIndex % colors.length]
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
  primaryOrganizationId.value = selectedOrganizations.value[0]
  const firstOrg = selectedOrganizationData.value[0]
  if (firstOrg) {
    selectedOrganizationName.value = firstOrg.name
  }
  customOrganizationName.value = ''
  showMergeModal.value = true
}

const closeMergeModal = () => {
  showMergeModal.value = false
  primaryOrganizationId.value = null
  selectedOrganizationName.value = ''
  customOrganizationName.value = ''
}

const focusCustomNameInput = () => {
  setTimeout(() => {
    customNameInput.value?.focus()
  }, 100)
}

const confirmMerge = async () => {
  const finalName = customOrganizationName.value.trim() || selectedOrganizationName.value

  if (!finalName || !primaryOrganizationId.value) {
    error.value = 'Please select a primary organization and name'
    return
  }

  const mergeData = {
    primary_id: primaryOrganizationId.value,
    merge_ids: selectedOrganizations.value.filter(id => id !== primaryOrganizationId.value),
    chosen_name: customOrganizationName.value.trim()
  }

  try {
    const response = await api.post('/data-management/organization-merge/merge/', mergeData)

    closeMergeModal()

    alert(`Successfully merged ${response.data.merged_count} organization(s). ${response.data.travellers_reassigned} traveller(s) and ${response.data.bookings_reassigned} booking(s) reassigned.`)

    selectedOrganizations.value = []
    await loadAllOrganizations()

    emit('duplicates-updated')
  } catch (err) {
    console.error('Error merging organizations:', err)
    error.value = err.response?.data?.error || 'Failed to merge organizations'
  }
}
</script>

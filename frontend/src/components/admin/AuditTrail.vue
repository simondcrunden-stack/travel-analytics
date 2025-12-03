<template>
  <div class="p-6">
    <div class="mb-6">
      <h2 class="text-xl font-semibold text-gray-900">Merge Audit Trail</h2>
      <p class="mt-1 text-sm text-gray-600">
        View all merge operations and undo changes if needed
      </p>
    </div>

    <!-- Search and Filters -->
    <div class="mb-6 space-y-4">
      <div class="flex flex-col sm:flex-row gap-4">
        <!-- Search -->
        <div class="flex-1">
          <div class="relative">
            <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <span class="mdi mdi-magnify text-gray-400"></span>
            </div>
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Search by name or description..."
              class="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              @input="debouncedSearch"
            />
          </div>
        </div>

        <!-- Merge Type Filter -->
        <div class="sm:w-48">
          <select
            v-model="mergeTypeFilter"
            @change="loadAudits"
            class="block w-full pl-3 pr-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md bg-white"
          >
            <option value="">All Types</option>
            <option value="TRAVELLER">Travellers</option>
            <option value="CONSULTANT">Consultants</option>
            <option value="ORGANIZATION">Organizations</option>
            <option value="SERVICE_FEE">Service Fees</option>
          </select>
        </div>

        <!-- Status Filter -->
        <div class="sm:w-40">
          <select
            v-model="statusFilter"
            @change="loadAudits"
            class="block w-full pl-3 pr-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md bg-white"
          >
            <option value="">All Status</option>
            <option value="COMPLETED">Completed</option>
            <option value="UNDONE">Undone</option>
          </select>
        </div>

        <!-- Clear Filters Button -->
        <div>
          <button
            v-if="searchQuery || mergeTypeFilter || statusFilter"
            @click="clearFilters"
            class="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            <span class="mdi mdi-filter-off mr-1"></span>
            Clear
          </button>
        </div>
      </div>

      <!-- Results Count -->
      <div v-if="!loading && audits.length > 0" class="flex items-center justify-between text-sm text-gray-600">
        <span>
          Showing <strong>{{ audits.length }}</strong> {{ audits.length === 1 ? 'result' : 'results' }}
        </span>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-12">
      <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      <p class="mt-4 text-sm text-gray-600">Loading audit trail...</p>
    </div>

    <!-- No Audits -->
    <div v-else-if="audits.length === 0" class="text-center py-12">
      <span class="mdi mdi-history text-6xl text-gray-300"></span>
      <h3 class="mt-4 text-lg font-medium text-gray-900">No merge operations yet</h3>
      <p class="mt-2 text-sm text-gray-600">
        Merge operations will appear here once you perform your first merge.
      </p>
    </div>

    <!-- Audit List -->
    <div v-else class="space-y-4">
      <div
        v-for="audit in audits"
        :key="audit.id"
        class="bg-white border border-gray-200 rounded-lg p-4 shadow-sm"
      >
        <div class="flex items-start justify-between">
          <div class="flex-1">
            <div class="flex items-center gap-2">
              <span class="mdi mdi-merge text-indigo-600 text-xl"></span>
              <h3 class="text-sm font-medium text-gray-900">
                {{ audit.merge_type_display }}
              </h3>
              <span
                :class="[
                  'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium',
                  audit.status === 'COMPLETED' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                ]"
              >
                {{ audit.status }}
              </span>
            </div>

            <p class="mt-2 text-sm text-gray-700">{{ audit.summary }}</p>

            <div class="mt-2 flex items-center gap-4 text-xs text-gray-500">
              <span>
                <span class="mdi mdi-account"></span> {{ audit.performed_by || 'Unknown' }}
              </span>
              <span>
                <span class="mdi mdi-calendar"></span> {{ formatDate(audit.created_at) }}
              </span>
              <span v-if="audit.organization">
                <span class="mdi mdi-domain"></span> {{ audit.organization }}
              </span>
              <span>
                <span class="mdi mdi-package-variant"></span> {{ audit.merged_count }} records merged
              </span>
            </div>

            <div v-if="audit.undone_at" class="mt-2 text-xs text-gray-600">
              <span class="mdi mdi-undo-variant text-orange-500"></span>
              Undone by {{ audit.undone_by }} on {{ formatDate(audit.undone_at) }}
            </div>
          </div>

          <div v-if="audit.status === 'COMPLETED'" class="ml-4">
            <button
              @click="undoMerge(audit.id)"
              class="inline-flex items-center px-3 py-1.5 border border-gray-300 text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50"
            >
              <span class="mdi mdi-undo-variant mr-1"></span>
              Undo
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'

const audits = ref([])
const loading = ref(false)
const searchQuery = ref('')
const mergeTypeFilter = ref('')
const statusFilter = ref('')

let searchTimeout = null

const loadAudits = async () => {
  loading.value = true
  try {
    const params = {}

    if (searchQuery.value.trim()) {
      params.search = searchQuery.value.trim()
    }

    if (mergeTypeFilter.value) {
      params.merge_type = mergeTypeFilter.value
    }

    if (statusFilter.value) {
      params.status = statusFilter.value
    }

    const response = await api.get('/data-management/merge-audit/', { params })
    audits.value = response.data.results || []
  } catch (err) {
    console.error('Error loading audit trail:', err)
  } finally {
    loading.value = false
  }
}

const debouncedSearch = () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    loadAudits()
  }, 500) // Wait 500ms after user stops typing
}

const clearFilters = () => {
  searchQuery.value = ''
  mergeTypeFilter.value = ''
  statusFilter.value = ''
  loadAudits()
}

const undoMerge = async (auditId) => {
  if (!confirm('Are you sure you want to undo this merge? This will restore the merged records.')) {
    return
  }

  try {
    await api.post(`/data-management/traveller-merge/${auditId}/undo/`)
    await loadAudits() // Reload the audit trail
    alert('Merge successfully undone!')
  } catch (err) {
    console.error('Error undoing merge:', err)
    alert('Failed to undo merge: ' + (err.response?.data?.error || 'Unknown error'))
  }
}

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleDateString('en-AU', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(() => {
  loadAudits()
})
</script>

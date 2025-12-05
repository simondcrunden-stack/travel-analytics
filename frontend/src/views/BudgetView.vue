<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Budget Dashboard</h1>
        <p class="mt-1 text-sm text-gray-500">Track spending against allocated budgets</p>
      </div>

      <div class="flex items-center gap-4">
        <!-- Fiscal Year Selector -->
        <select
          v-model="selectedFiscalYear"
          class="px-4 py-2.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option v-for="fy in fiscalYears" :key="fy.id" :value="fy.year_label">
            {{ fy.year_label }}
          </option>
        </select>

        <!-- Create Budget Button (Admin only) -->
        <button
          v-if="isAdmin"
          @click="openCreateModal"
          class="flex items-center gap-2 px-4 py-2.5 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          Create Budget
        </button>
      </div>
    </div>

    <!-- Universal Filters -->
    <UniversalFilters
      :show-traveller="false"
      :show-date-range="true"
      :show-destinations="false"
      :show-organization="true"
      :show-status="false"
      :show-supplier="false"
      @filters-changed="handleFiltersChanged"
    />

    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center items-center py-12">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-lg p-4">
      <p class="text-red-800">{{ error }}</p>
    </div>

    <!-- Organization Selection Required (Admin only) -->
    <div v-else-if="!shouldShowContent" class="bg-blue-50 border border-blue-200 rounded-xl p-8 text-center">
      <svg class="w-16 h-16 text-blue-600 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
      </svg>
      <h3 class="text-lg font-semibold text-gray-900 mb-2">Select an Organization</h3>
      <p class="text-gray-600 max-w-md mx-auto">
        Please select an organization from the filters above to view and manage budgets.
      </p>
    </div>

    <!-- Main Content -->
    <div v-else class="space-y-6">
      <!-- Summary Cards -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div class="bg-white rounded-xl shadow-sm p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-gray-600 text-sm">Total Budget</p>
              <p class="text-3xl font-bold text-gray-900 mt-1">
                {{ formatCurrency(summaryStats.totalBudget) }}
              </p>
            </div>
            <div class="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
              <svg class="w-6 h-6 text-blue-600" viewBox="0 0 24 24">
                <path fill="currentColor" :d="mdiCurrencyUsd" />
              </svg>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-xl shadow-sm p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-gray-600 text-sm">Total Spent</p>
              <p class="text-3xl font-bold text-gray-900 mt-1">
                {{ formatCurrency(summaryStats.totalSpent) }}
              </p>
            </div>
            <div class="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center">
              <svg class="w-6 h-6 text-purple-600" viewBox="0 0 24 24">
                <path fill="currentColor" :d="mdiChartLine" />
              </svg>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-xl shadow-sm p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-gray-600 text-sm">Remaining</p>
              <p class="text-3xl font-bold text-gray-900 mt-1">
                {{ formatCurrency(summaryStats.remaining) }}
              </p>
            </div>
            <div class="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center">
              <svg class="w-6 h-6 text-green-600" viewBox="0 0 24 24">
                <path fill="currentColor" :d="mdiWallet" />
              </svg>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-xl shadow-sm p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-gray-600 text-sm">Avg. Utilization</p>
              <p class="text-3xl font-bold text-gray-900 mt-1">
                {{ summaryStats.avgUtilization }}%
              </p>
            </div>
            <div class="w-12 h-12 bg-orange-100 rounded-xl flex items-center justify-center">
              <svg class="w-6 h-6 text-orange-600" viewBox="0 0 24 24">
                <path fill="currentColor" :d="mdiPercent" />
              </svg>
            </div>
          </div>
        </div>
      </div>

      <!-- Active Alerts -->
      <div v-if="activeAlerts.length > 0" class="bg-red-50 border border-red-200 rounded-xl p-6">
        <div class="flex items-center gap-2 mb-4">
          <svg class="w-6 h-6 text-red-600" viewBox="0 0 24 24">
            <path fill="currentColor" :d="mdiAlertCircle" />
          </svg>
          <h2 class="text-lg font-semibold text-red-900">Budget Alerts</h2>
          <span class="ml-auto px-3 py-1 bg-red-600 text-white text-sm font-medium rounded-full">
            {{ activeAlerts.length }}
          </span>
        </div>
        
        <div class="space-y-3">
          <div
            v-for="alert in activeAlerts"
            :key="alert.id"
            class="bg-white rounded-lg p-4 flex items-center justify-between"
          >
            <div>
              <p class="font-medium text-gray-900">{{ alert.costCenter }} - {{ alert.costCenterName }}</p>
              <p class="text-sm text-gray-600 mt-1">{{ alert.message }}</p>
            </div>
            <div class="text-right">
              <p class="text-lg font-bold text-red-600">{{ alert.percentage }}%</p>
              <p class="text-sm text-gray-600">{{ formatCurrency(alert.spent) }} spent</p>
            </div>
          </div>
        </div>
      </div>

      <!-- View-Specific Filters -->
      <div class="bg-white rounded-xl shadow-sm p-6">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">Budget Filters</h3>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <!-- Budget Status Filter -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Budget Status</label>
            <select
              v-model="viewFilters.status"
              class="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
            >
              <option value="">All Statuses</option>
              <option value="OK">OK (&lt;80%)</option>
              <option value="WARNING">Warning (80-95%)</option>
              <option value="CRITICAL">Critical (&gt;95%)</option>
            </select>
          </div>

          <!-- Business Unit Search -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Search Business Unit</label>
            <input
              type="text"
              v-model="viewFilters.search"
              placeholder="Search business units..."
              class="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
            />
          </div>
        </div>
      </div>

      <!-- Budget Table -->
      <div class="bg-white rounded-xl shadow-sm overflow-hidden">
        <!-- Table Header -->
        <div class="p-6 border-b border-gray-200">
          <h2 class="text-lg font-semibold text-gray-900">Budget Records</h2>
          <p class="text-sm text-gray-600 mt-1">{{ filteredBudgets.length }} business units found</p>
        </div>

        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Business Unit
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Organization
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Budget
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Spent
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Remaining
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Utilization
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th v-if="isAdmin" class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <!-- Empty State -->
              <tr v-if="filteredBudgets.length === 0">
                <td :colspan="isAdmin ? 7 : 6" class="px-6 py-12">
                  <div class="text-center">
                    <svg class="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 14l6-6m-5.5.5h.01m4.99 5h.01M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                    </svg>
                    <h3 class="text-lg font-semibold text-gray-900 mb-2">No Budgets Found</h3>
                    <p class="text-gray-600 mb-4">
                      {{ viewFilters.search || viewFilters.status ? 'No budgets match your current filters.' : 'No budgets have been created yet.' }}
                    </p>
                    <button
                      v-if="isAdmin && !viewFilters.search && !viewFilters.status"
                      @click="openCreateModal"
                      class="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
                    >
                      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                      </svg>
                      Create First Budget
                    </button>
                  </div>
                </td>
              </tr>

              <!-- Budget Rows -->
              <tr
                v-for="budget in paginatedBudgets"
                v-else
                :key="budget.id"
                class="hover:bg-gray-50 transition-colors"
              >
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="text-sm font-medium text-gray-900">{{ budget.costCenter }}</div>
                  <div class="text-sm text-gray-500">{{ budget.costCenterName }}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {{ budget.organization }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {{ formatCurrency(budget.total) }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {{ formatCurrency(budget.spent) }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {{ formatCurrency(budget.remaining) }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="flex items-center">
                    <div class="flex-1 max-w-[120px]">
                      <div class="w-full bg-gray-200 rounded-full h-2">
                        <div
                          :class="getProgressBarClass(budget.percentage)"
                          :style="{ width: `${Math.min(budget.percentage, 100)}%` }"
                          class="h-2 rounded-full"
                        ></div>
                      </div>
                    </div>
                    <span class="ml-3 text-sm font-medium text-gray-900">{{ budget.percentage }}%</span>
                  </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span :class="getStatusBadgeClass(budget.status)">
                    {{ budget.status }}
                  </span>
                </td>
                <td v-if="isAdmin" class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <button
                    @click="openEditModal(budget)"
                    class="text-blue-600 hover:text-blue-900 transition-colors"
                  >
                    Edit
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination -->
        <div class="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="text-sm text-gray-700">Rows per page:</span>
            <select v-model="itemsPerPage" class="border border-gray-300 rounded-md px-2 py-1 text-sm">
              <option :value="10">10</option>
              <option :value="20">20</option>
              <option :value="30">30</option>
              <option :value="40">40</option>
              <option :value="50">50</option>
            </select>
          </div>

          <div class="flex items-center gap-4">
            <span class="text-sm text-gray-700">
              {{ (currentPage - 1) * itemsPerPage + 1 }}-{{ Math.min(currentPage * itemsPerPage, filteredBudgets.length) }}
              of {{ filteredBudgets.length }}
            </span>

            <div class="flex gap-2">
              <button
                @click="prevPage"
                :disabled="currentPage === 1"
                class="px-3 py-1 border border-gray-300 rounded-md text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
              >
                Previous
              </button>
              <button
                @click="nextPage"
                :disabled="currentPage === totalPages"
                class="px-3 py-1 border border-gray-300 rounded-md text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
              >
                Next
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Budget Modal -->
    <BudgetModal
      :is-open="showBudgetModal"
      :budget="selectedBudget"
      @close="closeBudgetModal"
      @saved="handleBudgetSaved"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import UniversalFilters from '@/components/common/UniversalFilters.vue'
import BudgetModal from '@/components/budget/BudgetModal.vue'
import { transformFiltersForBackend } from '@/utils/filterTransformer'
import {
  mdiCurrencyUsd,
  mdiChartLine,
  mdiWallet,
  mdiPercent,
  mdiAlertCircle,
} from '@mdi/js'

// Stores
const authStore = useAuthStore()

// Computed
const isAdmin = computed(() => authStore.userType === 'ADMIN')

// Check if organization is selected (required for admins)
const selectedOrganization = computed(() => universalFilters.value?.organization || null)
const shouldShowContent = computed(() => {
  // For admins, organization must be selected
  if (isAdmin.value) {
    return !!selectedOrganization.value
  }
  // For non-admins, always show content
  return true
})

// State
const loading = ref(true)
const error = ref(null)
const budgets = ref([])
const fiscalYears = ref([])
const selectedFiscalYear = ref('')

// Modal state
const showBudgetModal = ref(false)
const selectedBudget = ref(null)

// Universal filters from UniversalFilters component
const universalFilters = ref({})

// View-specific filters
const viewFilters = ref({
  organization: '',
  status: '',
  search: '',
})

// Pagination
const currentPage = ref(1)
const itemsPerPage = ref(20)

// Handle UniversalFilters changes
const handleFiltersChanged = async (filters) => {
  console.log('💰 [BudgetView] Universal filters changed:', filters)
  universalFilters.value = filters
  currentPage.value = 1
  await fetchBudgets()
}

// Fetch fiscal years
const fetchFiscalYears = async () => {
  try {
    console.log('📅 [BudgetView] Fetching fiscal years')
    const response = await api.get('/fiscal-years/', {
      params: {
        is_active: true
      }
    })
    fiscalYears.value = response.data.results || []
    console.log('✅ [BudgetView] Loaded fiscal years:', fiscalYears.value.length)

    // Set default to current fiscal year if available
    const currentFY = fiscalYears.value.find(fy => fy.is_current)
    if (currentFY) {
      selectedFiscalYear.value = currentFY.year_label
    } else if (fiscalYears.value.length > 0) {
      // Default to first fiscal year if no current one is set
      selectedFiscalYear.value = fiscalYears.value[0].year_label
    }
  } catch (err) {
    console.error('Error loading fiscal years:', err)
  }
}

// Fetch data
const fetchBudgets = async () => {
  try {
    loading.value = true
    error.value = null

    const params = transformFiltersForBackend(universalFilters.value)

    // Add view-specific params
    if (viewFilters.value.search) params.search = viewFilters.value.search
    if (selectedFiscalYear.value) params.fiscal_year__year_label = selectedFiscalYear.value

    console.log('💰 [BudgetView] Fetching budgets with params:', params)

    const response = await api.get('/budgets/', { params })
    const budgetsData = response.data.results || []

    console.log('✅ [BudgetView] Loaded budgets:', budgetsData.length)
    console.log('First budget data:', budgetsData[0])

    // Transform backend data to frontend format
    budgets.value = budgetsData.map(budget => ({
      id: budget.id,
      organization: budget.organization_name,
      // Backend auto-populates cost_center from organizational_node, so use it consistently
      costCenter: budget.cost_center || 'N/A',
      costCenterName: budget.cost_center_name || '',
      total: parseFloat(budget.total_budget),
      spent: parseFloat(budget.budget_status.spent),
      remaining: parseFloat(budget.budget_status.remaining),
      percentage: Math.round(budget.budget_status.percentage),
      status: budget.budget_status.status,
    }))
  } catch (err) {
    error.value = 'Failed to load budget data'
    console.error('Error loading budgets:', err)
  } finally {
    loading.value = false
  }
}

// Summary statistics
const summaryStats = computed(() => {
  const total = budgets.value.reduce((sum, b) => sum + b.total, 0)
  const spent = budgets.value.reduce((sum, b) => sum + b.spent, 0)
  const remaining = total - spent
  const avgUtilization = Math.round((spent / total) * 100)

  return {
    totalBudget: total,
    totalSpent: spent,
    remaining,
    avgUtilization,
  }
})

// Active alerts
const activeAlerts = computed(() => {
  return budgets.value
    .filter(b => b.status === 'WARNING' || b.status === 'CRITICAL')
    .map(b => ({
      id: b.id,
      costCenter: b.costCenter,
      costCenterName: b.costCenterName,
      percentage: b.percentage,
      spent: b.spent,
      message: b.status === 'CRITICAL' 
        ? 'Budget critically exceeded - immediate action required'
        : 'Budget threshold exceeded - review spending',
    }))
})

// Filtered budgets
const filteredBudgets = computed(() => {
  return budgets.value.filter(b => {
    if (viewFilters.value.status && b.status !== viewFilters.value.status) return false
    if (viewFilters.value.search) {
      const search = viewFilters.value.search.toLowerCase()
      if (!b.costCenter.toLowerCase().includes(search) &&
          !b.costCenterName.toLowerCase().includes(search)) {
        return false
      }
    }
    return true
  })
})

// Paginated budgets
const totalPages = computed(() => Math.ceil(filteredBudgets.value.length / itemsPerPage.value))
const paginatedBudgets = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage.value
  const end = start + itemsPerPage.value
  return filteredBudgets.value.slice(start, end)
})

// Pagination controls
const goToPage = (page) => {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
  }
}

const nextPage = () => {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
  }
}

const prevPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--
  }
}

// Utility functions
const formatCurrency = (value) => {
  return new Intl.NumberFormat('en-AU', {
    style: 'currency',
    currency: 'AUD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value)
}

const getStatusBadgeClass = (status) => {
  const classes = {
    OK: 'px-3 py-1 text-sm font-medium rounded-full bg-green-100 text-green-800',
    WARNING: 'px-3 py-1 text-sm font-medium rounded-full bg-yellow-100 text-yellow-800',
    CRITICAL: 'px-3 py-1 text-sm font-medium rounded-full bg-red-100 text-red-800',
  }
  return classes[status] || classes.OK
}

const getProgressBarClass = (percentage) => {
  if (percentage >= 95) return 'bg-red-600'
  if (percentage >= 80) return 'bg-yellow-500'
  return 'bg-green-600'
}

const clearFilters = () => {
  viewFilters.value = {
    organization: '',
    status: '',
    search: '',
  }
}

// Modal methods
const openCreateModal = () => {
  selectedBudget.value = null
  showBudgetModal.value = true
}

const openEditModal = async (budget) => {
  try {
    // Fetch full budget details from API
    const response = await api.get(`/budgets/${budget.id}/`)
    selectedBudget.value = response.data
    showBudgetModal.value = true
  } catch (err) {
    console.error('Error loading budget details:', err)
    error.value = 'Failed to load budget details'
  }
}

const closeBudgetModal = () => {
  showBudgetModal.value = false
  selectedBudget.value = null
}

const handleBudgetSaved = async () => {
  await fetchBudgets()
}

// Watchers for view-specific filters
watch(selectedFiscalYear, () => {
  fetchBudgets()
})

watch(() => viewFilters.value.search, () => {
  fetchBudgets()
})

// Lifecycle
onMounted(async () => {
  // Load static fiscal years (not filter-dependent)
  await fetchFiscalYears()

  // Don't fetch budgets here! Wait for UniversalFilters to emit initial filters.
  // This prevents double-loading and ensures filters are applied correctly.
  // The handleFiltersChanged event will trigger fetchBudgets() with correct filters.
  console.log('📌 [BudgetView] Component mounted, waiting for filters from UniversalFilters')
})
</script>
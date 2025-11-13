<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Budget Dashboard</h1>
        <p class="mt-1 text-sm text-gray-500">Track spending against allocated budgets</p>
      </div>

      <!-- Fiscal Year Selector -->
      <select
        v-model="selectedFiscalYear"
        class="px-4 py-2.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
      >
        <option value="FY2024-25">FY 2024-25</option>
        <option value="FY2023-24">FY 2023-24</option>
      </select>
    </div>

    <!-- Universal Filters -->
    <UniversalFilters
      :show-traveller="true"
      :show-date-range="true"
      :show-destinations="false"
      :show-organization="false"
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
              <svg class="w-6 h-6 text-blue-600" :d="mdiCurrencyUsd" />
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
              <svg class="w-6 h-6 text-purple-600" :d="mdiChartLine" />
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
              <svg class="w-6 h-6 text-green-600" :d="mdiWallet" />
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
              <svg class="w-6 h-6 text-orange-600" :d="mdiPercent" />
            </div>
          </div>
        </div>
      </div>

      <!-- Active Alerts -->
      <div v-if="activeAlerts.length > 0" class="bg-red-50 border border-red-200 rounded-xl p-6">
        <div class="flex items-center gap-2 mb-4">
          <svg class="w-6 h-6 text-red-600" :d="mdiAlertCircle" />
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

        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <!-- Organization Filter -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Organization</label>
            <select
              v-model="viewFilters.organization"
              class="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
            >
              <option value="">All Organizations</option>
              <option value="TechCorp Australia">TechCorp Australia</option>
              <option value="Retail Solutions Group">Retail Solutions Group</option>
            </select>
          </div>

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

          <!-- Cost Centre Search -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Search Cost Centre</label>
            <input
              type="text"
              v-model="viewFilters.search"
              placeholder="Search cost centres..."
              class="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
            />
          </div>
        </div>
      </div>

      <!-- Budget List -->
      <div class="space-y-4">
        <div
          v-for="budget in filteredBudgets"
          :key="budget.id"
          class="bg-white rounded-xl shadow-sm overflow-hidden hover:shadow-md transition-shadow"
        >
          <div class="p-6">
            <!-- Header -->
            <div class="flex items-start justify-between mb-4">
              <div>
                <h3 class="text-lg font-semibold text-gray-900">
                  {{ budget.costCenter }} - {{ budget.costCenterName }}
                </h3>
                <p class="text-sm text-gray-600 mt-1">{{ budget.organization }}</p>
              </div>
              <span :class="getStatusBadgeClass(budget.status)">
                {{ budget.status }}
              </span>
            </div>

            <!-- Overall Progress -->
            <div class="mb-4">
              <div class="flex items-center justify-between mb-2">
                <span class="text-sm font-medium text-gray-700">Overall Budget</span>
                <span class="text-sm text-gray-600">
                  {{ formatCurrency(budget.spent) }} / {{ formatCurrency(budget.total) }}
                </span>
              </div>
              <div class="w-full bg-gray-200 rounded-full h-3">
                <div
                  :class="getProgressBarClass(budget.percentage)"
                  :style="{ width: `${Math.min(budget.percentage, 100)}%` }"
                  class="h-3 rounded-full transition-all duration-300"
                ></div>
              </div>
              <div class="flex items-center justify-between mt-2">
                <span class="text-sm text-gray-600">{{ budget.percentage }}% used</span>
                <span class="text-sm font-medium text-gray-900">
                  {{ formatCurrency(budget.remaining) }} remaining
                </span>
              </div>
            </div>

            <!-- Category Breakdown -->
            <div class="grid grid-cols-1 md:grid-cols-4 gap-4 pt-4 border-t border-gray-200">
              <!-- Air -->
              <div>
                <div class="flex items-center justify-between mb-2">
                  <span class="text-xs text-gray-600">Air</span>
                  <span class="text-xs font-medium text-gray-900">
                    {{ Math.round((budget.airSpent / budget.airBudget) * 100) }}%
                  </span>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-2">
                  <div
                    class="bg-blue-600 h-2 rounded-full"
                    :style="{ width: `${Math.min((budget.airSpent / budget.airBudget) * 100, 100)}%` }"
                  ></div>
                </div>
                <p class="text-xs text-gray-600 mt-1">
                  {{ formatCurrency(budget.airSpent) }} / {{ formatCurrency(budget.airBudget) }}
                </p>
              </div>

              <!-- Accommodation -->
              <div>
                <div class="flex items-center justify-between mb-2">
                  <span class="text-xs text-gray-600">Accommodation</span>
                  <span class="text-xs font-medium text-gray-900">
                    {{ Math.round((budget.hotelSpent / budget.hotelBudget) * 100) }}%
                  </span>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-2">
                  <div
                    class="bg-purple-600 h-2 rounded-full"
                    :style="{ width: `${Math.min((budget.hotelSpent / budget.hotelBudget) * 100, 100)}%` }"
                  ></div>
                </div>
                <p class="text-xs text-gray-600 mt-1">
                  {{ formatCurrency(budget.hotelSpent) }} / {{ formatCurrency(budget.hotelBudget) }}
                </p>
              </div>

              <!-- Car Hire -->
              <div>
                <div class="flex items-center justify-between mb-2">
                  <span class="text-xs text-gray-600">Car Hire</span>
                  <span class="text-xs font-medium text-gray-900">
                    {{ Math.round((budget.carSpent / budget.carBudget) * 100) }}%
                  </span>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-2">
                  <div
                    class="bg-green-600 h-2 rounded-full"
                    :style="{ width: `${Math.min((budget.carSpent / budget.carBudget) * 100, 100)}%` }"
                  ></div>
                </div>
                <p class="text-xs text-gray-600 mt-1">
                  {{ formatCurrency(budget.carSpent) }} / {{ formatCurrency(budget.carBudget) }}
                </p>
              </div>

              <!-- Other -->
              <div>
                <div class="flex items-center justify-between mb-2">
                  <span class="text-xs text-gray-600">Other</span>
                  <span class="text-xs font-medium text-gray-900">
                    {{ Math.round((budget.otherSpent / budget.otherBudget) * 100) }}%
                  </span>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-2">
                  <div
                    class="bg-orange-600 h-2 rounded-full"
                    :style="{ width: `${Math.min((budget.otherSpent / budget.otherBudget) * 100, 100)}%` }"
                  ></div>
                </div>
                <p class="text-xs text-gray-600 mt-1">
                  {{ formatCurrency(budget.otherSpent) }} / {{ formatCurrency(budget.otherBudget) }}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import UniversalFilters from '@/components/common/UniversalFilters.vue'
import {
  mdiCurrencyUsd,
  mdiChartLine,
  mdiWallet,
  mdiPercent,
  mdiAlertCircle,
} from '@mdi/js'

// State
const loading = ref(true)
const error = ref(null)
const budgets = ref([])
const selectedFiscalYear = ref('FY2024-25')

// Universal filters from UniversalFilters component
const universalFilters = ref({})

// View-specific filters
const viewFilters = ref({
  organization: '',
  status: '',
  search: '',
})

// Handle UniversalFilters changes
const handleFiltersChanged = async (filters) => {
  console.log('💰 [BudgetView] Universal filters changed:', filters)
  universalFilters.value = filters
  await fetchBudgets()
}

// Fetch data
const fetchBudgets = async () => {
  try {
    loading.value = true
    error.value = null

    // Generate sample budget data
    budgets.value = generateSampleBudgets()
  } catch (err) {
    error.value = 'Failed to load budget data'
    console.error(err)
  } finally {
    loading.value = false
  }
}

// Generate sample budgets
const generateSampleBudgets = () => {
  return [
    {
      id: 1,
      organization: 'TechCorp Australia',
      costCenter: 'ENG-001',
      costCenterName: 'Engineering Department',
      total: 150000,
      spent: 98500,
      remaining: 51500,
      percentage: 66,
      status: 'OK',
      airBudget: 100000,
      airSpent: 68000,
      hotelBudget: 35000,
      hotelSpent: 22000,
      carBudget: 10000,
      carSpent: 6500,
      otherBudget: 5000,
      otherSpent: 2000,
    },
    {
      id: 2,
      organization: 'TechCorp Australia',
      costCenter: 'SAL-001',
      costCenterName: 'Sales Department',
      total: 200000,
      spent: 168000,
      remaining: 32000,
      percentage: 84,
      status: 'WARNING',
      airBudget: 140000,
      airSpent: 115000,
      hotelBudget: 45000,
      hotelSpent: 38000,
      carBudget: 12000,
      carSpent: 11000,
      otherBudget: 3000,
      otherSpent: 4000,
    },
    {
      id: 3,
      organization: 'TechCorp Australia',
      costCenter: 'MKT-001',
      costCenterName: 'Marketing Department',
      total: 80000,
      spent: 78500,
      remaining: 1500,
      percentage: 98,
      status: 'CRITICAL',
      airBudget: 50000,
      airSpent: 49000,
      hotelBudget: 22000,
      hotelSpent: 21500,
      carBudget: 6000,
      carSpent: 6000,
      otherBudget: 2000,
      otherSpent: 2000,
    },
    {
      id: 4,
      organization: 'Retail Solutions Group',
      costCenter: 'STO-001',
      costCenterName: 'Store Operations',
      total: 80000,
      spent: 45200,
      remaining: 34800,
      percentage: 57,
      status: 'OK',
      airBudget: 50000,
      airSpent: 28000,
      hotelBudget: 22000,
      hotelSpent: 12000,
      carBudget: 6000,
      carSpent: 4000,
      otherBudget: 2000,
      otherSpent: 1200,
    },
    {
      id: 5,
      organization: 'Retail Solutions Group',
      costCenter: 'SUP-001',
      costCenterName: 'Supply Chain',
      total: 120000,
      spent: 102000,
      remaining: 18000,
      percentage: 85,
      status: 'WARNING',
      airBudget: 85000,
      airSpent: 72000,
      hotelBudget: 25000,
      hotelSpent: 21000,
      carBudget: 8000,
      carSpent: 7000,
      otherBudget: 2000,
      otherSpent: 2000,
    },
  ]
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
    if (viewFilters.value.organization && b.organization !== viewFilters.value.organization) return false
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

// Lifecycle
onMounted(() => {
  fetchBudgets()
})
</script>
<template>
  <div
    v-if="isOpen"
    class="fixed inset-0 z-50 overflow-y-auto"
    @click.self="handleClose"
  >
    <div class="flex min-h-screen items-center justify-center p-4">
      <!-- Backdrop -->
      <div class="fixed inset-0 bg-black/50 transition-opacity" @click="handleClose"></div>

      <!-- Modal -->
      <div class="relative w-full max-w-4xl bg-white rounded-2xl shadow-2xl transform transition-all">
        <!-- Header -->
        <div class="flex items-center justify-between border-b border-gray-200 px-8 py-6">
          <div>
            <h2 class="text-2xl font-bold text-gray-900">
              {{ isEditMode ? 'Edit Budget' : 'Create New Budget' }}
            </h2>
            <p class="mt-1 text-sm text-gray-600">
              {{ isEditMode ? 'Update budget allocation and thresholds' : 'Set up a new budget for an organizational node' }}
            </p>
          </div>
          <button
            @click="handleClose"
            class="rounded-lg p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-600 transition-colors"
          >
            <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Form -->
        <form @submit.prevent="handleSubmit" class="p-8">
          <!-- Error Message -->
          <div v-if="error" class="mb-6 rounded-lg bg-red-50 border border-red-200 p-4">
            <div class="flex items-center gap-2">
              <svg class="h-5 w-5 text-red-600" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
              </svg>
              <p class="text-sm font-medium text-red-800">{{ error }}</p>
            </div>
          </div>

          <div class="space-y-6">
            <!-- Organization and Fiscal Year -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">
                  Organization <span class="text-red-500">*</span>
                </label>
                <select
                  v-model="formData.organization"
                  @change="loadOrganizationalNodes"
                  required
                  :disabled="isEditMode"
                  class="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 disabled:bg-gray-100 disabled:cursor-not-allowed"
                >
                  <option value="">Select Organization</option>
                  <option v-for="org in organizations" :key="org.id" :value="org.id">
                    {{ org.name }}
                  </option>
                </select>
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">
                  Fiscal Year <span class="text-red-500">*</span>
                </label>
                <select
                  v-model="formData.fiscal_year"
                  required
                  :disabled="isEditMode"
                  class="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 disabled:bg-gray-100 disabled:cursor-not-allowed"
                >
                  <option value="">Select Fiscal Year</option>
                  <option v-for="fy in fiscalYears" :key="fy.id" :value="fy.id">
                    {{ fy.year_label }} ({{ formatDate(fy.start_date) }} - {{ formatDate(fy.end_date) }})
                  </option>
                </select>
              </div>
            </div>

            <!-- Organizational Node -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">
                Organizational Node (Cost Center / Business Unit)
              </label>
              <select
                v-model="formData.organizational_node"
                :disabled="!formData.organization || loadingNodes"
                class="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 disabled:bg-gray-100 disabled:cursor-not-allowed"
              >
                <option value="">None (Organization-level budget)</option>
                <option v-for="node in organizationalNodes" :key="node.id" :value="node.id">
                  {{ '  '.repeat(node.level) }}{{ node.code }} - {{ node.name }}
                </option>
              </select>
              <p class="mt-1 text-xs text-gray-500">
                Select an organizational node to create a node-specific budget
              </p>
            </div>

            <!-- Financial Budget Allocations -->
            <div class="rounded-lg border border-gray-200 p-6 bg-gray-50">
              <h3 class="text-lg font-semibold text-gray-900 mb-4">Budget Allocations</h3>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">
                    Total Budget <span class="text-red-500">*</span>
                  </label>
                  <input
                    type="number"
                    v-model.number="formData.total_budget"
                    required
                    min="0"
                    step="1"
                    class="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                    placeholder="0"
                  />
                </div>

                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">
                    Currency
                  </label>
                  <select
                    v-model="formData.currency"
                    class="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                  >
                    <option value="AUD">AUD - Australian Dollar</option>
                    <option value="USD">USD - US Dollar</option>
                    <option value="GBP">GBP - British Pound</option>
                    <option value="EUR">EUR - Euro</option>
                    <option value="NZD">NZD - New Zealand Dollar</option>
                  </select>
                </div>

                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">
                    Air Budget
                  </label>
                  <input
                    type="number"
                    v-model.number="formData.air_budget"
                    min="0"
                    step="1"
                    class="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                    placeholder="0"
                  />
                </div>

                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">
                    Accommodation Budget
                  </label>
                  <input
                    type="number"
                    v-model.number="formData.accommodation_budget"
                    min="0"
                    step="1"
                    class="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                    placeholder="0"
                  />
                </div>

                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">
                    Car Hire Budget
                  </label>
                  <input
                    type="number"
                    v-model.number="formData.car_hire_budget"
                    min="0"
                    step="1"
                    class="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                    placeholder="0"
                  />
                </div>

                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">
                    Other Budget
                  </label>
                  <input
                    type="number"
                    v-model.number="formData.other_budget"
                    min="0"
                    step="1"
                    class="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                    placeholder="0"
                  />
                </div>
              </div>
            </div>

            <!-- Carbon Budget -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">
                Carbon Budget (tonnes CO₂)
              </label>
              <input
                type="number"
                v-model.number="formData.carbon_budget"
                min="0"
                step="1"
                class="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                placeholder="0"
              />
              <p class="mt-1 text-xs text-gray-500">
                Annual carbon emissions budget in tonnes of CO₂
              </p>
            </div>

            <!-- Alert Thresholds -->
            <div class="rounded-lg border border-gray-200 p-6 bg-gray-50">
              <h3 class="text-lg font-semibold text-gray-900 mb-4">Alert Thresholds</h3>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">
                    Warning Threshold (%)
                  </label>
                  <input
                    type="number"
                    v-model.number="formData.warning_threshold"
                    min="0"
                    max="100"
                    class="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                    placeholder="80"
                  />
                  <p class="mt-1 text-xs text-gray-500">
                    Alert when budget usage reaches this percentage
                  </p>
                </div>

                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">
                    Critical Threshold (%)
                  </label>
                  <input
                    type="number"
                    v-model.number="formData.critical_threshold"
                    min="0"
                    max="100"
                    class="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                    placeholder="95"
                  />
                  <p class="mt-1 text-xs text-gray-500">
                    Critical alert when budget usage reaches this percentage
                  </p>
                </div>
              </div>
            </div>

            <!-- Notes -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">
                Notes
              </label>
              <textarea
                v-model="formData.notes"
                rows="3"
                class="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                placeholder="Add any additional notes or comments..."
              ></textarea>
            </div>

            <!-- Active Status -->
            <div class="flex items-center gap-2">
              <input
                type="checkbox"
                id="is_active"
                v-model="formData.is_active"
                class="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-2 focus:ring-blue-500/20"
              />
              <label for="is_active" class="text-sm font-medium text-gray-700">
                Active Budget
              </label>
            </div>
          </div>

          <!-- Footer -->
          <div class="mt-8 flex items-center justify-end gap-3 border-t border-gray-200 pt-6">
            <button
              type="button"
              @click="handleClose"
              class="px-6 py-2.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              :disabled="saving"
              class="px-6 py-2.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {{ saving ? 'Saving...' : (isEditMode ? 'Update Budget' : 'Create Budget') }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import api from '@/services/api'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  budget: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['close', 'saved'])

// State
const formData = ref({
  organization: '',
  fiscal_year: '',
  organizational_node: '',
  total_budget: 0,
  air_budget: 0,
  accommodation_budget: 0,
  car_hire_budget: 0,
  other_budget: 0,
  carbon_budget: 0,
  currency: 'AUD',
  warning_threshold: 80,
  critical_threshold: 95,
  notes: '',
  is_active: true
})

const organizations = ref([])
const fiscalYears = ref([])
const organizationalNodes = ref([])
const loadingNodes = ref(false)
const saving = ref(false)
const error = ref(null)

// Computed
const isEditMode = computed(() => !!props.budget)

// Methods
const loadOrganizations = async () => {
  try {
    const response = await api.get('/organizations/')
    organizations.value = response.data.results || []
  } catch (err) {
    console.error('Error loading organizations:', err)
  }
}

const loadFiscalYears = async () => {
  try {
    const response = await api.get('/fiscal-years/', {
      params: { is_active: true }
    })
    fiscalYears.value = response.data.results || []
  } catch (err) {
    console.error('Error loading fiscal years:', err)
  }
}

const loadOrganizationalNodes = async () => {
  if (!formData.value.organization) {
    organizationalNodes.value = []
    return
  }

  try {
    loadingNodes.value = true
    const response = await api.get('/organizational-nodes/', {
      params: {
        organization: formData.value.organization,
        is_active: true
      }
    })
    organizationalNodes.value = response.data.results || []
  } catch (err) {
    console.error('Error loading organizational nodes:', err)
  } finally {
    loadingNodes.value = false
  }
}

const resetForm = () => {
  formData.value = {
    organization: '',
    fiscal_year: '',
    organizational_node: '',
    total_budget: 0,
    air_budget: 0,
    accommodation_budget: 0,
    car_hire_budget: 0,
    other_budget: 0,
    carbon_budget: 0,
    currency: 'AUD',
    warning_threshold: 80,
    critical_threshold: 95,
    notes: '',
    is_active: true
  }
  error.value = null
}

const handleClose = () => {
  resetForm()
  emit('close')
}

const handleSubmit = async () => {
  try {
    saving.value = true
    error.value = null

    const payload = {
      organization_id: formData.value.organization,
      fiscal_year_id: formData.value.fiscal_year,
      total_budget: formData.value.total_budget,
      currency: formData.value.currency,
      air_budget: formData.value.air_budget || 0,
      accommodation_budget: formData.value.accommodation_budget || 0,
      car_hire_budget: formData.value.car_hire_budget || 0,
      other_budget: formData.value.other_budget || 0,
      carbon_budget: formData.value.carbon_budget || 0,
      warning_threshold: formData.value.warning_threshold,
      critical_threshold: formData.value.critical_threshold,
      notes: formData.value.notes,
      is_active: formData.value.is_active
    }

    // Add organizational_node_id if selected
    if (formData.value.organizational_node) {
      payload.organizational_node_id = formData.value.organizational_node
    }

    if (isEditMode.value) {
      await api.put(`/budgets/${props.budget.id}/`, payload)
    } else {
      await api.post('/budgets/', payload)
    }

    emit('saved')
    handleClose()
  } catch (err) {
    console.error('Error saving budget:', err)
    error.value = err.response?.data?.error || 'Failed to save budget. Please try again.'
  } finally {
    saving.value = false
  }
}

const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('en-AU', { day: 'numeric', month: 'short', year: 'numeric' })
}

// Watchers
watch(() => props.isOpen, async (newValue) => {
  if (newValue) {
    await loadOrganizations()
    await loadFiscalYears()

    if (props.budget) {
      // Edit mode - populate form
      formData.value = {
        organization: props.budget.organization?.id || '',
        fiscal_year: props.budget.fiscal_year?.id || '',
        organizational_node: props.budget.organizational_node?.id || '',
        total_budget: parseFloat(props.budget.total_budget || 0),
        air_budget: parseFloat(props.budget.air_budget || 0),
        accommodation_budget: parseFloat(props.budget.accommodation_budget || 0),
        car_hire_budget: parseFloat(props.budget.car_hire_budget || 0),
        other_budget: parseFloat(props.budget.other_budget || 0),
        carbon_budget: parseFloat(props.budget.carbon_budget || 0),
        currency: props.budget.currency || 'AUD',
        warning_threshold: props.budget.warning_threshold || 80,
        critical_threshold: props.budget.critical_threshold || 95,
        notes: props.budget.notes || '',
        is_active: props.budget.is_active !== false
      }

      // Load nodes for the selected organization
      if (formData.value.organization) {
        await loadOrganizationalNodes()
      }
    } else {
      resetForm()
    }
  }
})
</script>

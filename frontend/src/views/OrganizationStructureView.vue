<template>
  <div class="space-y-6">
    <!-- Header -->
    <div>
      <h1 class="text-2xl font-bold text-gray-900">Organization Structure</h1>
      <p class="mt-1 text-sm text-gray-500">
        Manage the organizational hierarchy and assign customer organizations to travel agents
      </p>
    </div>

    <!-- Selection Controls -->
    <div class="bg-white rounded-2xl shadow-sm p-6">
      <h2 class="text-lg font-semibold text-gray-900 mb-4">Select Organization</h2>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <!-- Travel Agent Selector -->
        <div>
          <label class="mb-2 block text-sm font-medium text-gray-700">Travel Agent</label>
          <select
            v-model="selectedTravelAgent"
            class="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
            @change="handleTravelAgentChange"
          >
            <option value="">Select a Travel Agent</option>
            <option v-for="agent in travelAgents" :key="agent.id" :value="agent.id">
              {{ agent.name }} ({{ agent.code }})
            </option>
          </select>
        </div>

        <!-- Customer Organization Selector -->
        <div>
          <label class="mb-2 block text-sm font-medium text-gray-700">Customer Organization</label>
          <select
            v-model="selectedOrganization"
            class="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
            :disabled="!selectedTravelAgent"
            @change="handleOrganizationChange"
          >
            <option value="">{{ selectedTravelAgent ? 'Select a Customer Organization' : 'Select a Travel Agent first' }}</option>
            <option v-for="org in customerOrganizations" :key="org.id" :value="org.id">
              {{ org.name }} ({{ org.code }})
            </option>
          </select>
        </div>
      </div>
    </div>

    <!-- Organization Details Card -->
    <div v-if="selectedOrganization && selectedOrgDetails" class="bg-white rounded-2xl shadow-sm p-6">
      <div class="flex items-center justify-between mb-6">
        <h2 class="text-lg font-semibold text-gray-900">Organization Details</h2>
        <span
          :class="[
            'px-3 py-1 rounded-full text-xs font-medium',
            selectedOrgDetails.is_active
              ? 'bg-green-100 text-green-800'
              : 'bg-red-100 text-red-800'
          ]"
        >
          {{ selectedOrgDetails.is_active ? 'Active' : 'Inactive' }}
        </span>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- Basic Information -->
        <div class="space-y-4">
          <h3 class="text-sm font-semibold text-gray-900 uppercase tracking-wide">Basic Information</h3>

          <div>
            <label class="text-xs font-medium text-gray-500">Organization Name</label>
            <p class="mt-1 text-sm text-gray-900">{{ selectedOrgDetails.name }}</p>
          </div>

          <div>
            <label class="text-xs font-medium text-gray-500">Organization Code</label>
            <p class="mt-1 text-sm text-gray-900">{{ selectedOrgDetails.code }}</p>
          </div>

          <div>
            <label class="text-xs font-medium text-gray-500">Organization Type</label>
            <p class="mt-1 text-sm text-gray-900">
              <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                {{ selectedOrgDetails.org_type === 'CUSTOMER' ? 'Customer Organization' : 'Travel Agent' }}
              </span>
            </p>
          </div>

          <div>
            <label class="text-xs font-medium text-gray-500">Assigned Travel Agent</label>
            <p class="mt-1 text-sm text-gray-900">
              {{ selectedOrgDetails.travel_agent_name || 'Not assigned' }}
            </p>
          </div>
        </div>

        <!-- Contact & Settings -->
        <div class="space-y-4">
          <h3 class="text-sm font-semibold text-gray-900 uppercase tracking-wide">Contact & Settings</h3>

          <div>
            <label class="text-xs font-medium text-gray-500">Contact Email</label>
            <p class="mt-1 text-sm text-gray-900">{{ selectedOrgDetails.contact_email || 'Not set' }}</p>
          </div>

          <div>
            <label class="text-xs font-medium text-gray-500">Contact Phone</label>
            <p class="mt-1 text-sm text-gray-900">{{ selectedOrgDetails.contact_phone || 'Not set' }}</p>
          </div>

          <div>
            <label class="text-xs font-medium text-gray-500">Base Currency</label>
            <p class="mt-1 text-sm text-gray-900">{{ selectedOrgDetails.base_currency || 'AUD' }}</p>
          </div>

          <div>
            <label class="text-xs font-medium text-gray-500">Subscription Status</label>
            <p class="mt-1 text-sm text-gray-900">
              <span
                :class="[
                  'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                  selectedOrgDetails.subscription_status === 'ACTIVE'
                    ? 'bg-green-100 text-green-800'
                    : selectedOrgDetails.subscription_status === 'TRIAL'
                    ? 'bg-blue-100 text-blue-800'
                    : 'bg-gray-100 text-gray-800'
                ]"
              >
                {{ selectedOrgDetails.subscription_status || 'Unknown' }}
              </span>
            </p>
          </div>
        </div>
      </div>

      <!-- Edit Note -->
      <div class="mt-6 p-4 bg-blue-50 rounded-lg">
        <div class="flex">
          <MdiIcon :path="mdiInformationOutline" :size="20" class="text-blue-600 flex-shrink-0" />
          <div class="ml-3">
            <p class="text-sm text-blue-800">
              To edit organization details or change the assigned travel agent, please use the Django Admin interface at
              <a href="/admin/organizations/organization/" class="font-medium underline hover:text-blue-900" target="_blank">
                /admin/organizations/organization/
              </a>
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Travel Agent's Customer Organizations List -->
    <div v-if="selectedTravelAgent && customerOrganizations.length > 0" class="bg-white rounded-2xl shadow-sm p-6">
      <h2 class="text-lg font-semibold text-gray-900 mb-4">
        Customer Organizations
        <span class="text-sm font-normal text-gray-500">({{ customerOrganizations.length }})</span>
      </h2>

      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Organization Name
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Code
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Contact Email
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr
              v-for="org in customerOrganizations"
              :key="org.id"
              :class="[
                'hover:bg-gray-50 cursor-pointer transition-colors',
                selectedOrganization === org.id ? 'bg-blue-50' : ''
              ]"
              @click="selectOrganization(org.id)"
            >
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm font-medium text-gray-900">{{ org.name }}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm text-gray-500">{{ org.code }}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm text-gray-500">{{ org.contact_email || 'Not set' }}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <span
                  :class="[
                    'px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full',
                    org.is_active
                      ? 'bg-green-100 text-green-800'
                      : 'bg-red-100 text-red-800'
                  ]"
                >
                  {{ org.is_active ? 'Active' : 'Inactive' }}
                </span>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                <button
                  @click.stop="selectOrganization(org.id)"
                  class="text-blue-600 hover:text-blue-900 font-medium"
                >
                  View Details
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Empty State -->
    <div v-if="!selectedTravelAgent" class="bg-white rounded-2xl shadow-sm p-12 text-center">
      <MdiIcon :path="mdiOfficeBuilding" :size="48" class="mx-auto text-gray-400" />
      <h3 class="mt-4 text-lg font-medium text-gray-900">No Travel Agent Selected</h3>
      <p class="mt-2 text-sm text-gray-500">
        Select a travel agent above to view and manage their customer organizations
      </p>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center items-center py-12">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import MdiIcon from '@/components/common/MdiIcon.vue'
import { mdiOfficeBuilding, mdiInformationOutline } from '@mdi/js'
import api from '@/services/api'

// State
const travelAgents = ref([])
const customerOrganizations = ref([])
const selectedTravelAgent = ref('')
const selectedOrganization = ref('')
const selectedOrgDetails = ref(null)
const loading = ref(false)

// Load all travel agents on mount
const loadTravelAgents = async () => {
  try {
    loading.value = true
    const response = await api.get('/organizations/', {
      params: { org_type: 'AGENT' }
    })
    const agentData = response.data.results || response.data
    travelAgents.value = Array.isArray(agentData) ? agentData : []
    console.log('✅ Loaded travel agents:', travelAgents.value.length)
  } catch (error) {
    console.error('❌ Failed to load travel agents:', error)
    travelAgents.value = []
  } finally {
    loading.value = false
  }
}

// Load customer organizations for selected travel agent
const loadCustomerOrganizations = async () => {
  if (!selectedTravelAgent.value) {
    customerOrganizations.value = []
    return
  }

  try {
    loading.value = true
    const response = await api.get('/organizations/', {
      params: {
        travel_agent: selectedTravelAgent.value,
        org_type: 'CUSTOMER'
      }
    })
    const orgData = response.data.results || response.data
    customerOrganizations.value = Array.isArray(orgData) ? orgData : []
    console.log('✅ Loaded customer organizations:', customerOrganizations.value.length)
  } catch (error) {
    console.error('❌ Failed to load customer organizations:', error)
    customerOrganizations.value = []
  } finally {
    loading.value = false
  }
}

// Load organization details
const loadOrganizationDetails = async () => {
  if (!selectedOrganization.value) {
    selectedOrgDetails.value = null
    return
  }

  try {
    loading.value = true
    const response = await api.get(`/organizations/${selectedOrganization.value}/`)
    selectedOrgDetails.value = response.data
    console.log('✅ Loaded organization details:', selectedOrgDetails.value)
  } catch (error) {
    console.error('❌ Failed to load organization details:', error)
    selectedOrgDetails.value = null
  } finally {
    loading.value = false
  }
}

// Handlers
const handleTravelAgentChange = () => {
  console.log('🔄 Travel agent changed to:', selectedTravelAgent.value)
  selectedOrganization.value = ''
  selectedOrgDetails.value = null
  loadCustomerOrganizations()
}

const handleOrganizationChange = () => {
  console.log('🔄 Organization changed to:', selectedOrganization.value)
  loadOrganizationDetails()
}

const selectOrganization = (orgId) => {
  selectedOrganization.value = orgId
  loadOrganizationDetails()
}

// Lifecycle
onMounted(() => {
  loadTravelAgents()
})
</script>

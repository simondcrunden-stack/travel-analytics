<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Page Header -->
    <div class="bg-white border-b border-gray-200 sticky top-0 z-10">
      <div class="px-4 sm:px-6 lg:px-8">
        <div class="py-6">
          <h1 class="text-3xl font-bold text-gray-900 flex items-center gap-3">
            <span class="mdi mdi-database-cog text-blue-600"></span>
            Data Management
          </h1>
          <p class="mt-2 text-sm text-gray-600">
            Merge duplicate records and maintain data quality across your organization
          </p>
        </div>
      </div>
    </div>

    <!-- Content -->
    <div class="px-4 sm:px-6 lg:px-8 py-8">
      <!-- Organization/Agent Filters -->
      <div class="mb-6 bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
        <h3 class="text-sm font-medium text-gray-900 mb-3">Filter by Organization</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <!-- Travel Agent Selection (Global Admin only) -->
          <div v-if="userType === 'ADMIN'">
            <label class="block text-sm font-medium text-gray-700 mb-2">Travel Agent</label>
            <select
              v-model="selectedTravelAgent"
              @change="onTravelAgentChange"
              class="block w-full pl-3 pr-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md bg-white"
            >
              <option value="">All Travel Agents</option>
              <option
                v-for="agent in travelAgents"
                :key="agent.id"
                :value="agent.id"
              >
                {{ agent.name }}
              </option>
            </select>
          </div>

          <!-- Organization Selection -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Organization</label>
            <select
              v-model="selectedOrganization"
              class="block w-full pl-3 pr-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md bg-white"
            >
              <option value="">Select an organization</option>
              <option
                v-for="org in organizations"
                :key="org.id"
                :value="org.id"
              >
                {{ org.name }}
              </option>
            </select>
          </div>
        </div>
      </div>

      <!-- Tab Navigation -->
      <div class="mb-6">
        <div class="border-b border-gray-200">
          <nav class="-mb-px flex space-x-8" aria-label="Tabs">
            <button
              @click="activeTab = 'travellers'"
              :class="[
                activeTab === 'travellers'
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
                'whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2'
              ]"
            >
              <span class="mdi mdi-account-multiple"></span>
              Travellers
              <span v-if="travellerDuplicateCount > 0" class="ml-2 bg-red-100 text-red-800 py-0.5 px-2 rounded-full text-xs font-medium">
                {{ travellerDuplicateCount }}
              </span>
            </button>
            <button
              @click="activeTab = 'consultants'"
              :class="[
                activeTab === 'consultants'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
                'whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2'
              ]"
            >
              <span class="mdi mdi-account-tie"></span>
              Travel Consultants
              <span v-if="consultantDuplicateCount > 0" class="ml-2 bg-red-100 text-red-800 py-0.5 px-2 rounded-full text-xs font-medium">
                {{ consultantDuplicateCount }}
              </span>
            </button>
            <button
              @click="activeTab = 'organizations'"
              :class="[
                activeTab === 'organizations'
                  ? 'border-purple-500 text-purple-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
                'whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2'
              ]"
            >
              <span class="mdi mdi-office-building"></span>
              Organizations
              <span v-if="organizationDuplicateCount > 0" class="ml-2 bg-red-100 text-red-800 py-0.5 px-2 rounded-full text-xs font-medium">
                {{ organizationDuplicateCount }}
              </span>
            </button>
            <button
              @click="activeTab = 'servicefees'"
              :class="[
                activeTab === 'servicefees'
                  ? 'border-green-500 text-green-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
                'whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2'
              ]"
            >
              <span class="mdi mdi-room-service-outline"></span>
              Service Fees
              <span v-if="serviceFeeDuplicateCount > 0" class="ml-2 bg-red-100 text-red-800 py-0.5 px-2 rounded-full text-xs font-medium">
                {{ serviceFeeDuplicateCount }}
              </span>
            </button>
            <button
              @click="activeTab = 'audit'"
              :class="[
                activeTab === 'audit'
                  ? 'border-gray-500 text-gray-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
                'whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2'
              ]"
            >
              <span class="mdi mdi-history"></span>
              Audit Trail
            </button>
          </nav>
        </div>
      </div>

      <!-- Tab Content -->
      <div class="bg-white rounded-lg shadow">
        <TravellerMerge
          v-if="activeTab === 'travellers'"
          :selected-organization="selectedOrganization"
          @duplicates-updated="updateTravellerCount"
        />
        <ConsultantMerge
          v-else-if="activeTab === 'consultants'"
          :selected-organization="selectedOrganization"
          @duplicates-updated="updateConsultantCount"
        />
        <OrganizationMerge
          v-else-if="activeTab === 'organizations'"
          :selected-organization="selectedOrganization"
          @duplicates-updated="updateOrganizationCount"
        />
        <ServiceFeeMerge
          v-else-if="activeTab === 'servicefees'"
          :selected-organization="selectedOrganization"
          @duplicates-updated="updateServiceFeeCount"
        />
        <AuditTrail
          v-else-if="activeTab === 'audit'"
          :selected-organization="selectedOrganization"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'
import TravellerMerge from '@/components/admin/TravellerMerge.vue'
import ConsultantMerge from '@/components/admin/ConsultantMerge.vue'
import OrganizationMerge from '@/components/admin/OrganizationMerge.vue'
import ServiceFeeMerge from '@/components/admin/ServiceFeeMerge.vue'
import AuditTrail from '@/components/admin/AuditTrail.vue'

const activeTab = ref('travellers')

// User and organization state
const userType = ref('')
const travelAgents = ref([])
const organizations = ref([])
const selectedTravelAgent = ref('')
const selectedOrganization = ref('')

// Duplicate counts (updated by child components)
const travellerDuplicateCount = ref(0)
const consultantDuplicateCount = ref(0)
const organizationDuplicateCount = ref(0)
const serviceFeeDuplicateCount = ref(0)

// Load user info
const loadUserInfo = async () => {
  try {
    const response = await api.get('/users/me/')
    userType.value = response.data.user_type
  } catch (err) {
    console.error('Error loading user info:', err)
  }
}

// Load travel agents
const loadTravelAgents = async () => {
  try {
    const response = await api.get('/organizations/', {
      params: { org_type: 'AGENT' }
    })
    travelAgents.value = response.data.results || response.data || []
  } catch (err) {
    console.error('Error loading travel agents:', err)
  }
}

// Load organizations
const loadOrganizations = async () => {
  try {
    const params = {}
    if (selectedTravelAgent.value) {
      params.travel_agent = selectedTravelAgent.value
      params.org_type = 'CUSTOMER'
    }

    const response = await api.get('/organizations/', { params })
    organizations.value = response.data.results || response.data || []
  } catch (err) {
    console.error('Error loading organizations:', err)
  }
}

// Handle travel agent change
const onTravelAgentChange = () => {
  selectedOrganization.value = ''
  loadOrganizations()
}

const updateTravellerCount = (count) => {
  travellerDuplicateCount.value = count
}

const updateConsultantCount = (count) => {
  consultantDuplicateCount.value = count
}

const updateOrganizationCount = (count) => {
  organizationDuplicateCount.value = count
}

const updateServiceFeeCount = (count) => {
  serviceFeeDuplicateCount.value = count
}

// Load initial data on mount
onMounted(async () => {
  await loadUserInfo()

  // Load travel agents if user is global admin
  if (userType.value === 'ADMIN') {
    await loadTravelAgents()
  }

  // Load organizations
  await loadOrganizations()
})
</script>

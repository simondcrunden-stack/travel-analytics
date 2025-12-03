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
        <TravellerMerge v-if="activeTab === 'travellers'" @duplicates-updated="updateTravellerCount" />
        <ConsultantMerge v-else-if="activeTab === 'consultants'" @duplicates-updated="updateConsultantCount" />
        <OrganizationMerge v-else-if="activeTab === 'organizations'" @duplicates-updated="updateOrganizationCount" />
        <ServiceFeeMerge v-else-if="activeTab === 'servicefees'" @duplicates-updated="updateServiceFeeCount" />
        <AuditTrail v-else-if="activeTab === 'audit'" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import TravellerMerge from '@/components/admin/TravellerMerge.vue'
import ConsultantMerge from '@/components/admin/ConsultantMerge.vue'
import OrganizationMerge from '@/components/admin/OrganizationMerge.vue'
import ServiceFeeMerge from '@/components/admin/ServiceFeeMerge.vue'
import AuditTrail from '@/components/admin/AuditTrail.vue'

const activeTab = ref('travellers')

// Duplicate counts (updated by child components)
const travellerDuplicateCount = ref(0)
const consultantDuplicateCount = ref(0)
const organizationDuplicateCount = ref(0)
const serviceFeeDuplicateCount = ref(0)

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
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Page Header -->
    <div class="bg-white border-b border-gray-200 sticky top-0 z-10">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="py-6">
          <h1 class="text-3xl font-bold text-gray-900 flex items-center gap-3">
            <span class="mdi mdi-chart-box text-blue-600"></span>
            Travel Agent Reports
          </h1>
          <p class="mt-2 text-sm text-gray-600">
            Comprehensive analytics for consultant performance and customer yield
          </p>
        </div>

        <!-- Filters -->
        <div class="pb-6">
          <UniversalFilters
            :available-filters="availableFilters"
            :initial-filters="activeFilters"
            @filters-changed="handleFiltersChanged"
          />
        </div>
      </div>
    </div>

    <!-- Content -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- Tab Navigation -->
      <div class="mb-6">
        <div class="border-b border-gray-200">
          <nav class="-mb-px flex space-x-8" aria-label="Tabs">
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
              Consultant Analysis
            </button>
            <button
              @click="activeTab = 'customers'"
              :class="[
                activeTab === 'customers'
                  ? 'border-purple-500 text-purple-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
                'whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2'
              ]"
            >
              <span class="mdi mdi-account-star"></span>
              Customer Analysis
            </button>
          </nav>
        </div>
      </div>

      <!-- Tab Content -->
      <div v-if="activeTab === 'consultants'">
        <ConsultantYieldAnalysis
          :organization="activeFilters.organization"
          :start-date="activeFilters.travel_date_after"
          :end-date="activeFilters.travel_date_before"
        />
      </div>

      <div v-if="activeTab === 'customers'">
        <CustomerYieldAnalysis
          :organization="activeFilters.organization"
          :start-date="activeFilters.travel_date_after"
          :end-date="activeFilters.travel_date_before"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import UniversalFilters from '@/components/UniversalFilters.vue'
import ConsultantYieldAnalysis from '@/components/ConsultantYieldAnalysis.vue'
import CustomerYieldAnalysis from '@/components/CustomerYieldAnalysis.vue'

const activeTab = ref('consultants')

const availableFilters = [
  'organization',
  'travel_date_range'
]

const activeFilters = ref({
  organization: null,
  travel_date_after: null,
  travel_date_before: null
})

const handleFiltersChanged = (filters) => {
  activeFilters.value = { ...filters }
}
</script>

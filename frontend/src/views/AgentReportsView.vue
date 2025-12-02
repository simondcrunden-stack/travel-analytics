<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Page Header -->
    <div class="bg-white border-b border-gray-200 sticky top-0 z-10">
      <div class="px-4 sm:px-6 lg:px-8">
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
            :show-traveller="false"
            :show-date-range="true"
            :show-destinations="true"
            :show-organization="true"
            :show-status="false"
            :show-supplier="false"
            :show-product-type="true"
            :date-label="'Booking Date'"
            :initial-filters="activeFilters"
            @filters-changed="handleFiltersChanged"
          />
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
              @click="activeTab = 'organizations'"
              :class="[
                activeTab === 'organizations'
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
                'whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2'
              ]"
            >
              <span class="mdi mdi-office-building"></span>
              Organizations
            </button>
            <button
              @click="activeTab = 'suppliers'"
              :class="[
                activeTab === 'suppliers'
                  ? 'border-teal-500 text-teal-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
                'whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2'
              ]"
            >
              <span class="mdi mdi-store"></span>
              Suppliers
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
              Travellers
            </button>
          </nav>
        </div>
      </div>

      <!-- Tab Content -->
      <div v-if="activeTab === 'organizations'">
        <OrganizationYieldAnalysis
          :organization="activeFilters.organization"
          :start-date="activeFilters.booking_date_after"
          :end-date="activeFilters.booking_date_before"
          :product-type="activeFilters.product_type"
        />
      </div>

      <div v-if="activeTab === 'suppliers'">
        <SupplierYieldAnalysis
          :organization="activeFilters.organization"
          :start-date="activeFilters.booking_date_after"
          :end-date="activeFilters.booking_date_before"
          :product-type="activeFilters.product_type"
        />
      </div>

      <div v-if="activeTab === 'consultants'">
        <ConsultantYieldAnalysis
          :organization="activeFilters.organization"
          :start-date="activeFilters.booking_date_after"
          :end-date="activeFilters.booking_date_before"
          :product-type="activeFilters.product_type"
        />
      </div>

      <div v-if="activeTab === 'customers'">
        <CustomerYieldAnalysis
          :organization="activeFilters.organization"
          :start-date="activeFilters.booking_date_after"
          :end-date="activeFilters.booking_date_before"
          :product-type="activeFilters.product_type"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import UniversalFilters from '@/components/common/UniversalFilters.vue'
import ConsultantYieldAnalysis from '@/components/ConsultantYieldAnalysis.vue'
import CustomerYieldAnalysis from '@/components/CustomerYieldAnalysis.vue'
import OrganizationYieldAnalysis from '@/components/OrganizationYieldAnalysis.vue'
import SupplierYieldAnalysis from '@/components/SupplierYieldAnalysis.vue'

const activeTab = ref('organizations')

const activeFilters = ref({
  organization: null,
  booking_date_after: null,
  booking_date_before: null,
  product_type: null
})

const handleFiltersChanged = (filters) => {
  // Map dateFrom/dateTo to booking_date_after/booking_date_before
  activeFilters.value = {
    organization: filters.organization || null,
    booking_date_after: filters.dateFrom || null,
    booking_date_before: filters.dateTo || null,
    product_type: filters.product_type || null
  }
}
</script>

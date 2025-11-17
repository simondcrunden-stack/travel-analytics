<template>
  <div class="space-y-6">
    <!-- Header -->
    <div>
      <h1 class="text-2xl font-bold text-gray-900">Summary Dashboard</h1>
      <p class="mt-1 text-sm text-gray-500">
        Overview of your travel data
      </p>
    </div>

    <!-- Universal Filters -->
    <UniversalFilters
      :show-traveller="true"
      :show-date-range="true"
      :show-destinations="true"
      :show-organization="true"
      :show-status="true"
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
      <button 
        @click="loadData" 
        class="mt-2 text-sm text-red-600 hover:text-red-800 underline"
      >
        Try Again
      </button>
    </div>

    <!-- Dashboard Content -->
    <div v-else>
      <!-- Stats Cards -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <!-- Total Spend -->
        <div class="bg-white rounded-lg shadow p-6">
          <div class="flex items-center justify-between">
            <div class="flex-1">
              <p class="text-sm font-medium text-gray-600">Total Spend</p>
              <p class="text-2xl font-bold text-gray-900 mt-2">
                {{ formatCurrency(summary.total_spend) }}
              </p>
            </div>
            <div class="bg-blue-100 p-3 rounded-full">
              <svg class="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
          <div class="mt-3 flex items-center justify-between text-xs">
            <div>
              <span class="text-gray-500">Domestic:</span>
              <span class="font-semibold text-gray-700 ml-1">{{ formatCurrency(summary.total_spend_domestic) }}</span>
            </div>
            <div>
              <span class="text-gray-500">International:</span>
              <span class="font-semibold text-gray-700 ml-1">{{ formatCurrency(summary.total_spend_international) }}</span>
            </div>
          </div>
          <p class="text-xs text-gray-500 mt-2 pt-2 border-t border-gray-100">
            {{ summary.total_bookings }} bookings
          </p>
        </div>

        <!-- Air Travel -->
        <div class="bg-white rounded-lg shadow p-6">
          <div class="flex items-center justify-between">
            <div class="flex-1">
              <p class="text-sm font-medium text-gray-600">Air Travel</p>
              <p class="text-2xl font-bold text-gray-900 mt-2">
                {{ formatCurrency(summary.air_spend) }}
              </p>
            </div>
            <div class="bg-sky-100 p-3 rounded-full">
              <svg class="w-6 h-6 text-sky-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            </div>
          </div>
          <div class="mt-3 flex items-center justify-between text-xs">
            <div>
              <span class="text-gray-500">Domestic:</span>
              <span class="font-semibold text-gray-700 ml-1">{{ formatCurrency(summary.air_spend_domestic) }}</span>
            </div>
            <div>
              <span class="text-gray-500">International:</span>
              <span class="font-semibold text-gray-700 ml-1">{{ formatCurrency(summary.air_spend_international) }}</span>
            </div>
          </div>
          <p class="text-xs text-gray-500 mt-2 pt-2 border-t border-gray-100">
            {{ summary.air_bookings }} bookings
          </p>
        </div>

        <!-- Accommodation -->
        <div class="bg-white rounded-lg shadow p-6">
          <div class="flex items-center justify-between">
            <div class="flex-1">
              <p class="text-sm font-medium text-gray-600">Accommodation</p>
              <p class="text-2xl font-bold text-gray-900 mt-2">
                {{ formatCurrency(summary.accommodation_spend) }}
              </p>
            </div>
            <div class="bg-amber-100 p-3 rounded-full">
              <svg class="w-6 h-6 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
            </div>
          </div>
          <div class="mt-3 flex items-center justify-between text-xs">
            <div>
              <span class="text-gray-500">Domestic:</span>
              <span class="font-semibold text-gray-700 ml-1">{{ formatCurrency(summary.accommodation_spend_domestic) }}</span>
            </div>
            <div>
              <span class="text-gray-500">International:</span>
              <span class="font-semibold text-gray-700 ml-1">{{ formatCurrency(summary.accommodation_spend_international) }}</span>
            </div>
          </div>
          <p class="text-xs text-gray-500 mt-2 pt-2 border-t border-gray-100">
            {{ summary.accommodation_bookings }} bookings
          </p>
        </div>

        <!-- Car Hire -->
        <div class="bg-white rounded-lg shadow p-6">
          <div class="flex items-center justify-between">
            <div class="flex-1">
              <p class="text-sm font-medium text-gray-600">Car Hire</p>
              <p class="text-2xl font-bold text-gray-900 mt-2">
                {{ formatCurrency(summary.car_hire_spend) }}
              </p>
            </div>
            <div class="bg-emerald-100 p-3 rounded-full">
              <svg class="w-6 h-6 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
              </svg>
            </div>
          </div>
          <div class="mt-3 flex items-center justify-between text-xs">
            <div>
              <span class="text-gray-500">Domestic:</span>
              <span class="font-semibold text-gray-700 ml-1">{{ formatCurrency(summary.car_hire_spend_domestic) }}</span>
            </div>
            <div>
              <span class="text-gray-500">International:</span>
              <span class="font-semibold text-gray-700 ml-1">{{ formatCurrency(summary.car_hire_spend_international) }}</span>
            </div>
          </div>
          <p class="text-xs text-gray-500 mt-2 pt-2 border-t border-gray-100">
            {{ summary.car_hire_bookings }} bookings
          </p>
        </div>
      </div>

      <!-- Compliance & Emissions Summary -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mt-6">
        <!-- Compliance Rate -->
        <div class="bg-white rounded-lg shadow p-6">
          <div class="flex items-center justify-between">
            <div class="flex-1">
              <p class="text-sm font-medium text-gray-600">Compliance Rate</p>
              <p class="text-3xl font-bold mt-2" :class="summary.compliance_rate >= 80 ? 'text-green-600' : summary.compliance_rate >= 60 ? 'text-amber-600' : 'text-red-600'">
                {{ summary.compliance_rate.toFixed(1) }}%
              </p>
            </div>
            <div :class="summary.compliance_rate >= 80 ? 'bg-green-100' : summary.compliance_rate >= 60 ? 'bg-amber-100' : 'bg-red-100'" class="p-3 rounded-full">
              <svg class="w-6 h-6" :class="summary.compliance_rate >= 80 ? 'text-green-600' : summary.compliance_rate >= 60 ? 'text-amber-600' : 'text-red-600'" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
          <div class="mt-3 pt-3 border-t border-gray-100">
            <div class="flex items-center justify-between text-xs">
              <span class="text-gray-500">Total Violations:</span>
              <span class="font-semibold text-gray-700">{{ summary.violation_count }}</span>
            </div>
            <div class="flex items-center justify-between text-xs mt-1" v-if="summary.critical_violations > 0">
              <span class="text-red-600">Critical:</span>
              <span class="font-semibold text-red-700">{{ summary.critical_violations }}</span>
            </div>
          </div>
        </div>

        <!-- Carbon Emissions -->
        <div class="bg-white rounded-lg shadow p-6">
          <div class="flex items-center justify-between">
            <div class="flex-1">
              <p class="text-sm font-medium text-gray-600">Carbon Emissions</p>
              <p class="text-3xl font-bold text-gray-900 mt-2">
                {{ (summary.total_carbon_kg / 1000).toFixed(1) }}
              </p>
              <p class="text-xs text-gray-500 mt-1">tonnes CO₂</p>
            </div>
            <div class="bg-green-100 p-3 rounded-full">
              <svg class="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
          <div class="mt-3 pt-3 border-t border-gray-100">
            <div class="text-xs text-gray-500">
              {{ summary.air_bookings > 0 ? (summary.total_carbon_kg / summary.air_bookings).toFixed(0) : 0 }} kg per flight
            </div>
          </div>
        </div>

        <!-- Policy Compliance Status -->
        <div class="bg-white rounded-lg shadow p-6">
          <div class="flex items-center justify-between">
            <div class="flex-1">
              <p class="text-sm font-medium text-gray-600">Policy Status</p>
              <p class="text-lg font-bold mt-2" :class="summary.compliance_rate >= 90 ? 'text-green-600' : summary.compliance_rate >= 75 ? 'text-amber-600' : 'text-red-600'">
                {{ summary.compliance_rate >= 90 ? 'Excellent' : summary.compliance_rate >= 75 ? 'Good' : summary.compliance_rate >= 60 ? 'Fair' : 'Needs Attention' }}
              </p>
            </div>
            <div :class="summary.compliance_rate >= 90 ? 'bg-green-100' : summary.compliance_rate >= 75 ? 'bg-amber-100' : 'bg-red-100'" class="p-3 rounded-full">
              <svg class="w-6 h-6" :class="summary.compliance_rate >= 90 ? 'text-green-600' : summary.compliance_rate >= 75 ? 'text-amber-600' : 'text-red-600'" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
            </div>
          </div>
          <div class="mt-3 pt-3 border-t border-gray-100">
            <div class="text-xs">
              <span class="text-gray-500">Compliant Bookings:</span>
              <span class="font-semibold text-gray-700 ml-1">{{ summary.total_bookings - summary.violation_count }}/{{ summary.total_bookings }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Budget Tracking -->
      <div class="mt-6" v-if="budgetSummary.total_budgets > 0">
        <h2 class="text-lg font-semibold text-gray-900 mb-4">Budget Tracking</h2>
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
          <!-- Overall Budget Status -->
          <div class="bg-white rounded-lg shadow p-6">
            <div class="flex items-center justify-between">
              <div class="flex-1">
                <p class="text-sm font-medium text-gray-600">Budget Utilization</p>
                <p class="text-3xl font-bold mt-2" :class="budgetSummary.overall_utilization > 95 ? 'text-red-600' : budgetSummary.overall_utilization > 80 ? 'text-amber-600' : 'text-green-600'">
                  {{ budgetSummary.overall_utilization.toFixed(1) }}%
                </p>
              </div>
              <div :class="budgetSummary.overall_utilization > 95 ? 'bg-red-100' : budgetSummary.overall_utilization > 80 ? 'bg-amber-100' : 'bg-green-100'" class="p-3 rounded-full">
                <svg class="w-6 h-6" :class="budgetSummary.overall_utilization > 95 ? 'text-red-600' : budgetSummary.overall_utilization > 80 ? 'text-amber-600' : 'text-green-600'" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                </svg>
              </div>
            </div>
            <div class="mt-3 pt-3 border-t border-gray-100">
              <div class="flex items-center justify-between text-xs">
                <span class="text-gray-500">Allocated:</span>
                <span class="font-semibold text-gray-700">{{ formatCurrency(budgetSummary.total_allocated) }}</span>
              </div>
              <div class="flex items-center justify-between text-xs mt-1">
                <span class="text-gray-500">Spent:</span>
                <span class="font-semibold text-gray-700">{{ formatCurrency(budgetSummary.total_spent) }}</span>
              </div>
              <div class="flex items-center justify-between text-xs mt-1">
                <span class="text-gray-500">Remaining:</span>
                <span class="font-semibold" :class="budgetSummary.total_remaining < 0 ? 'text-red-700' : 'text-green-700'">
                  {{ formatCurrency(budgetSummary.total_remaining) }}
                </span>
              </div>
            </div>
          </div>

          <!-- Budgets OK -->
          <div class="bg-white rounded-lg shadow p-6">
            <div class="flex items-center justify-between">
              <div class="flex-1">
                <p class="text-sm font-medium text-gray-600">On Track</p>
                <p class="text-3xl font-bold text-green-600 mt-2">
                  {{ budgetSummary.budgets_ok }}
                </p>
              </div>
              <div class="bg-green-100 p-3 rounded-full">
                <svg class="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
            <div class="mt-3 pt-3 border-t border-gray-100">
              <p class="text-xs text-gray-500">
                Cost centers within budget
              </p>
            </div>
          </div>

          <!-- Budgets Warning -->
          <div class="bg-white rounded-lg shadow p-6">
            <div class="flex items-center justify-between">
              <div class="flex-1">
                <p class="text-sm font-medium text-gray-600">At Risk</p>
                <p class="text-3xl font-bold text-amber-600 mt-2">
                  {{ budgetSummary.budgets_warning }}
                </p>
              </div>
              <div class="bg-amber-100 p-3 rounded-full">
                <svg class="w-6 h-6 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
            </div>
            <div class="mt-3 pt-3 border-t border-gray-100">
              <p class="text-xs text-gray-500">
                Approaching threshold (80-95%)
              </p>
            </div>
          </div>

          <!-- Budgets Critical/Exceeded -->
          <div class="bg-white rounded-lg shadow p-6">
            <div class="flex items-center justify-between">
              <div class="flex-1">
                <p class="text-sm font-medium text-gray-600">Overspend Alert</p>
                <p class="text-3xl font-bold text-red-600 mt-2">
                  {{ budgetSummary.budgets_critical + budgetSummary.budgets_exceeded }}
                </p>
              </div>
              <div class="bg-red-100 p-3 rounded-full">
                <svg class="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
            <div class="mt-3 pt-3 border-t border-gray-100">
              <div class="flex items-center justify-between text-xs">
                <span class="text-gray-500">Critical (95%+):</span>
                <span class="font-semibold text-red-700">{{ budgetSummary.budgets_critical }}</span>
              </div>
              <div class="flex items-center justify-between text-xs mt-1">
                <span class="text-gray-500">Exceeded (100%+):</span>
                <span class="font-semibold text-red-700">{{ budgetSummary.budgets_exceeded }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Critical Budgets Alert List -->
        <div v-if="budgetSummary.critical_budgets.length > 0" class="mt-4 bg-red-50 border border-red-200 rounded-lg p-4">
          <div class="flex items-start">
            <div class="flex-shrink-0">
              <svg class="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <div class="ml-3 flex-1">
              <h3 class="text-sm font-medium text-red-800">Critical Budget Alerts</h3>
              <div class="mt-2 text-sm text-red-700">
                <ul class="list-disc list-inside space-y-1">
                  <li v-for="budget in budgetSummary.critical_budgets.slice(0, 5)" :key="budget.cost_center">
                    <span class="font-semibold">{{ budget.cost_center_name || budget.cost_center }}</span>:
                    {{ formatCurrency(budget.spent) }} / {{ formatCurrency(budget.allocated) }}
                    <span class="font-bold">({{ budget.percentage.toFixed(1) }}%)</span>
                  </li>
                </ul>
                <p v-if="budgetSummary.critical_budgets.length > 5" class="mt-2 text-xs">
                  ... and {{ budgetSummary.critical_budgets.length - 5 }} more
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Top Rankings -->
      <div class="mt-6">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold text-gray-900">Top Performers</h2>
          <div class="flex items-center gap-4">
            <!-- Category Tabs -->
            <div class="flex bg-gray-100 rounded-lg p-1">
              <button
                @click="selectedRankingCategory = 'cost_centers'"
                :class="selectedRankingCategory === 'cost_centers' ? 'bg-white text-gray-900 shadow' : 'text-gray-600'"
                class="px-3 py-1.5 text-sm font-medium rounded-md transition-all"
              >
                Cost Centers
              </button>
              <button
                @click="selectedRankingCategory = 'travellers'"
                :class="selectedRankingCategory === 'travellers' ? 'bg-white text-gray-900 shadow' : 'text-gray-600'"
                class="px-3 py-1.5 text-sm font-medium rounded-md transition-all"
              >
                Travellers
              </button>
            </div>

            <!-- Metric Selector -->
            <select
              v-model="selectedRankingType"
              class="px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="trips">Most Trips</option>
              <option value="spend">Highest Spend</option>
              <option value="carbon">Highest Carbon</option>
              <option value="compliance">Best Compliance</option>
              <option value="lost_savings">Most Lost Savings</option>
            </select>
          </div>
        </div>

        <!-- Rankings Table -->
        <div class="bg-white rounded-lg shadow overflow-hidden">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Rank</th>
                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {{ selectedRankingCategory === 'cost_centers' ? 'Cost Center' : 'Traveller' }}
                </th>
                <th scope="col" class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Trips</th>
                <th scope="col" class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Total Spend</th>
                <th scope="col" class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Lost Savings</th>
                <th scope="col" class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Carbon (kg)</th>
                <th scope="col" class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Compliance</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr
                v-for="(item, index) in rankings[selectedRankingCategory][`by_${selectedRankingType}`]"
                :key="selectedRankingCategory === 'cost_centers' ? item.cost_center : item.traveller_id"
                :class="index === 0 ? 'bg-yellow-50' : index === 1 ? 'bg-gray-50' : index === 2 ? 'bg-orange-50' : ''"
              >
                <td class="px-6 py-4 whitespace-nowrap text-sm">
                  <span
                    class="inline-flex items-center justify-center w-8 h-8 rounded-full font-bold"
                    :class="index === 0 ? 'bg-yellow-400 text-yellow-900' : index === 1 ? 'bg-gray-400 text-gray-900' : index === 2 ? 'bg-orange-400 text-orange-900' : 'bg-gray-200 text-gray-700'"
                  >
                    {{ index + 1 }}
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="text-sm font-medium text-gray-900">
                    {{ selectedRankingCategory === 'cost_centers' ? item.cost_center : item.traveller_name }}
                  </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">
                  {{ item.trip_count }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">
                  {{ formatCurrency(item.total_spend) }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm">
                  <span v-if="item.lost_savings > 0" class="text-red-600 font-semibold">
                    {{ formatCurrency(item.lost_savings) }}
                  </span>
                  <span v-else class="text-gray-400">
                    -
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">
                  {{ item.total_carbon_kg.toFixed(0) }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-right">
                  <span
                    class="inline-flex px-2 py-1 text-xs font-semibold rounded-full"
                    :class="item.compliance_rate >= 80 ? 'bg-green-100 text-green-800' : item.compliance_rate >= 60 ? 'bg-amber-100 text-amber-800' : 'bg-red-100 text-red-800'"
                  >
                    {{ item.compliance_rate.toFixed(1) }}%
                  </span>
                </td>
              </tr>
              <tr v-if="rankings[selectedRankingCategory][`by_${selectedRankingType}`].length === 0">
                <td colspan="7" class="px-6 py-8 text-center text-sm text-gray-500">
                  No data available
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Charts Row -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
        <!-- Spend by Category Chart -->
        <div class="bg-white rounded-lg shadow p-6">
          <h2 class="text-lg font-semibold text-gray-900 mb-4">
            Spend by Category
          </h2>
          <div class="h-64">
            <canvas ref="categoryChart"></canvas>
          </div>
        </div>

        <!-- Monthly Trend Chart -->
        <div class="bg-white rounded-lg shadow p-6">
          <h2 class="text-lg font-semibold text-gray-900 mb-4">
            Monthly Spend Trend
          </h2>
          <div class="h-64">
            <canvas ref="trendChart"></canvas>
          </div>
        </div>
      </div>

      <!-- Recent Bookings -->
      <div class="bg-white rounded-lg shadow mt-6">
        <div class="p-6 border-b border-gray-200">
          <h2 class="text-lg font-semibold text-gray-900">Recent Bookings</h2>
        </div>
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Reference
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Traveller
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Amount
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="booking in recentBookings" :key="booking.id" class="hover:bg-gray-50">
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {{ booking.agent_booking_reference }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {{ booking.traveller_name }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span :class="getBookingTypeClass(booking.booking_type)">
                    {{ booking.booking_type }}
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {{ formatDate(booking.travel_date) }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {{ formatCurrency(booking.total_amount) }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span :class="getStatusClass(booking.status)">
                    {{ booking.status }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { Chart } from 'chart.js/auto'
import bookingService from '@/services/bookingService'
import UniversalFilters from '@/components/common/UniversalFilters.vue'

// State
const loading = ref(true)
const error = ref(null)
const summary = ref({
  total_spend: 0,
  total_spend_domestic: 0,
  total_spend_international: 0,
  total_bookings: 0,
  air_spend: 0,
  air_spend_domestic: 0,
  air_spend_international: 0,
  air_bookings: 0,
  accommodation_spend: 0,
  accommodation_spend_domestic: 0,
  accommodation_spend_international: 0,
  accommodation_bookings: 0,
  car_hire_spend: 0,
  car_hire_spend_domestic: 0,
  car_hire_spend_international: 0,
  car_hire_bookings: 0,
  total_carbon_kg: 0,
  compliance_rate: 0,
  violation_count: 0,
  critical_violations: 0
})
const budgetSummary = ref({
  total_budgets: 0,
  total_allocated: 0,
  total_spent: 0,
  total_remaining: 0,
  overall_utilization: 0,
  budgets_ok: 0,
  budgets_warning: 0,
  budgets_critical: 0,
  budgets_exceeded: 0,
  critical_budgets: []
})
const rankings = ref({
  cost_centers: {
    by_trips: [],
    by_spend: [],
    by_carbon: [],
    by_compliance: [],
    by_lost_savings: []
  },
  travellers: {
    by_trips: [],
    by_spend: [],
    by_carbon: [],
    by_compliance: [],
    by_lost_savings: []
  }
})
const selectedRankingType = ref('trips')  // trips, spend, carbon, compliance
const selectedRankingCategory = ref('cost_centers')  // cost_centers, travellers
const recentBookings = ref([])
const monthlyData = ref([])

// Filter state
const activeFilters = ref({})

// Chart refs
const categoryChart = ref(null)
const trendChart = ref(null)
let categoryChartInstance = null
let trendChartInstance = null

// Handle filter changes from UniversalFilters
const handleFiltersChanged = (newFilters) => {
  console.log('📊 Dashboard filters changed:', newFilters)
  activeFilters.value = newFilters
  loadData()
}

// Load data
const loadData = async () => {
  loading.value = true
  error.value = null

  try {
    console.log('🌐 [DashboardView] Loading dashboard data with filters:', activeFilters.value)

    // Call new dashboard summary endpoint for aggregated metrics
    const summaryData = await bookingService.getDashboardSummary(activeFilters.value)
    summary.value = summaryData

    console.log('✅ [DashboardView] Dashboard summary loaded:', summaryData)

    // Get budget summary (non-blocking - fail silently if no budgets exist)
    try {
      const budgetData = await bookingService.getBudgetSummary(activeFilters.value)
      budgetSummary.value = budgetData
      console.log('✅ [DashboardView] Budget summary loaded:', budgetData)
    } catch (budgetErr) {
      console.log('ℹ️ [DashboardView] No budget data available:', budgetErr.message)
      // Keep default empty budget summary
    }

    // Get top rankings (non-blocking - fail silently if no data)
    try {
      const rankingsData = await bookingService.getTopRankings({ ...activeFilters.value, limit: 5 })
      rankings.value = rankingsData
      console.log('✅ [DashboardView] Rankings loaded:', rankingsData)
    } catch (rankingsErr) {
      console.log('ℹ️ [DashboardView] No rankings data available:', rankingsErr.message)
      // Keep default empty rankings
    }

    // Get recent bookings for the table
    const data = await bookingService.getBookings(activeFilters.value)
    const bookings = data.results || data

    // Get recent bookings (last 10)
    recentBookings.value = bookings
      .sort((a, b) => new Date(b.travel_date) - new Date(a.travel_date))
      .slice(0, 10)

    // Process monthly trend data
    processMonthlyData(bookings)

    console.log('Summary:', summary.value)
    console.log('Recent bookings:', recentBookings.value.length)
    console.log('Monthly data points:', monthlyData.value.length)

  } catch (err) {
    console.error('Error loading dashboard data:', err)
    error.value = 'Failed to load dashboard data. Please try again.'
  } finally {
    loading.value = false

    // Wait for v-else content to render AFTER loading becomes false
    await nextTick()
    await nextTick()

    console.log('Rendering charts...')
    renderCharts()
  }
}

const processMonthlyData = (bookings) => {
  // Group bookings by month
  const monthGroups = {}
  
  bookings.forEach(booking => {
    const date = new Date(booking.travel_date)
    const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
    
    if (!monthGroups[monthKey]) {
      monthGroups[monthKey] = {
        month: monthKey,
        total: 0,
        count: 0
      }
    }
    
    monthGroups[monthKey].total += parseFloat(booking.total_amount || 0)
    monthGroups[monthKey].count += 1
  })
  
  // Convert to sorted array
  monthlyData.value = Object.values(monthGroups).sort((a, b) => 
    a.month.localeCompare(b.month)
  )
}

const renderCharts = () => {
  console.log('Rendering charts...')
  
  // Category Chart
  if (categoryChartInstance) {
    categoryChartInstance.destroy()
  }
  
  if (categoryChart.value) {
    const ctx = categoryChart.value.getContext('2d')
    
    const categoryData = [
      summary.value.air_spend,
      summary.value.accommodation_spend,
      summary.value.car_hire_spend
    ]
    
    console.log('Category chart data:', categoryData)
    
    categoryChartInstance = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: ['Air Travel', 'Accommodation', 'Car Hire'],
        datasets: [{
          data: categoryData,
          backgroundColor: [
            '#0ea5e9', // sky-500
            '#f59e0b', // amber-500
            '#10b981'  // emerald-500
          ]
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom'
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                const label = context.label || ''
                const value = context.parsed || 0
                return `${label}: ${formatCurrency(value)}`
              }
            }
          }
        }
      }
    })
  }

  // Trend Chart
  if (trendChartInstance) {
    trendChartInstance.destroy()
  }
  
  if (trendChart.value && monthlyData.value.length > 0) {
    const ctx = trendChart.value.getContext('2d')
    
    console.log('Trend chart labels:', monthlyData.value.map(d => d.month))
    console.log('Trend chart data:', monthlyData.value.map(d => d.total))
    
    trendChartInstance = new Chart(ctx, {
      type: 'line',
      data: {
        labels: monthlyData.value.map(d => {
          const [year, month] = d.month.split('-')
          return new Date(year, month - 1).toLocaleDateString('en-AU', { 
            month: 'short', 
            year: 'numeric' 
          })
        }),
        datasets: [{
          label: 'Monthly Spend',
          data: monthlyData.value.map(d => d.total),
          borderColor: '#2563eb',
          backgroundColor: 'rgba(37, 99, 235, 0.1)',
          tension: 0.4,
          fill: true
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                return `Spend: ${formatCurrency(context.parsed.y)}`
              }
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              callback: (value) => formatCurrency(value)
            }
          }
        }
      }
    })
  } else {
    console.log('Skipping trend chart - no data available')
  }
}

const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-AU', {
    style: 'currency',
    currency: 'AUD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(amount || 0)
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('en-AU', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

const getBookingTypeClass = (type) => {
  const classes = {
    'AIR': 'px-2 py-1 text-xs rounded-full bg-sky-100 text-sky-800',
    'ACCOMMODATION': 'px-2 py-1 text-xs rounded-full bg-amber-100 text-amber-800',
    'CAR': 'px-2 py-1 text-xs rounded-full bg-emerald-100 text-emerald-800',
    'OTHER': 'px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-800'
  }
  return classes[type] || classes['OTHER']
}

const getStatusClass = (status) => {
  const classes = {
    'CONFIRMED': 'px-2 py-1 text-xs rounded-full bg-green-100 text-green-800',
    'CANCELLED': 'px-2 py-1 text-xs rounded-full bg-red-100 text-red-800',
    'PENDING': 'px-2 py-1 text-xs rounded-full bg-yellow-100 text-yellow-800',
    'REFUNDED': 'px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800'
  }
  return classes[status] || classes['PENDING']
}

// Lifecycle
onMounted(() => {
  loadData()
})
</script>
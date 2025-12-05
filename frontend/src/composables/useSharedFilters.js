import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

/**
 * Composable for managing shared filter state across dashboards via URL query params
 *
 * This allows filters to:
 * - Persist when navigating between dashboards
 * - Be shareable via URL
 * - Survive page refreshes
 * - Work with browser back/forward buttons
 *
 * Usage in a dashboard component:
 * ```
 * import { useSharedFilters } from '@/composables/useSharedFilters'
 *
 * const { filters, updateFilters, clearFilters } = useSharedFilters()
 *
 * // filters is a reactive ref with current filter values
 * // updateFilters(newFilters) updates filters and URL
 * // clearFilters() removes all filters
 * ```
 */
export function useSharedFilters() {
  const route = useRoute()
  const router = useRouter()

  // Initialize filters from URL query params
  const initializeFiltersFromURL = () => {
    const query = route.query

    return {
      // Date range
      dateFrom: query.travel_date__gte || '',
      dateTo: query.travel_date__lte || '',

      // Organization/Agent
      organization: query.organization || '',
      travelAgent: query.travel_agent || '',

      // Travellers (multi-select)
      travellers: query.travellers ? query.travellers.split(',') : [],

      // Destinations
      countries: query.countries ? query.countries.split(',') : [],
      destinationPreset: query.destination_preset || '',
      city: query.city || '',

      // Booking details
      status: query.status || '',
      productType: query.booking_type || '',
      supplier: query.supplier || '',
      travelConsultant: query.travel_consultant || '',
      travelConsultants: query.travel_consultants ? query.travel_consultants.split(',') : [],
    }
  }

  // Create reactive filters ref
  const filters = ref(initializeFiltersFromURL())

  /**
   * Update filters and sync with URL
   * @param {Object} newFilters - Object with filter values to update
   */
  const updateFilters = async (newFilters) => {
    // Update local filters
    Object.assign(filters.value, newFilters)

    // Build query params from filters
    const query = {}

    // Add date range
    if (filters.value.dateFrom) query.travel_date__gte = filters.value.dateFrom
    if (filters.value.dateTo) query.travel_date__lte = filters.value.dateTo

    // Add organization/agent
    if (filters.value.organization) query.organization = filters.value.organization
    if (filters.value.travelAgent) query.travel_agent = filters.value.travelAgent

    // Add travellers (multi-select as comma-separated)
    if (filters.value.travellers && filters.value.travellers.length > 0) {
      query.travellers = filters.value.travellers.join(',')
    }

    // Add countries (multi-select as comma-separated)
    if (filters.value.countries && filters.value.countries.length > 0) {
      query.countries = filters.value.countries.join(',')
    }

    // Add destination preset
    if (filters.value.destinationPreset) query.destination_preset = filters.value.destinationPreset

    // Add city
    if (filters.value.city) query.city = filters.value.city

    // Add status
    if (filters.value.status) query.status = filters.value.status

    // Add product type
    if (filters.value.productType) query.booking_type = filters.value.productType

    // Add supplier
    if (filters.value.supplier) query.supplier = filters.value.supplier

    // Add travel consultant
    if (filters.value.travelConsultant) query.travel_consultant = filters.value.travelConsultant
    if (filters.value.travelConsultants && filters.value.travelConsultants.length > 0) {
      query.travel_consultants = filters.value.travelConsultants.join(',')
    }

    // Update URL with new query params (without reloading page)
    await router.replace({
      path: route.path,
      query
    })
  }

  /**
   * Clear all filters
   */
  const clearFilters = async () => {
    filters.value = {
      dateFrom: '',
      dateTo: '',
      organization: '',
      travelAgent: '',
      travellers: [],
      countries: [],
      destinationPreset: '',
      city: '',
      status: '',
      productType: '',
      supplier: '',
      travelConsultant: '',
      travelConsultants: [],
    }

    // Clear URL query params
    await router.replace({ path: route.path, query: {} })
  }

  /**
   * Get filters in API-ready format
   * @returns {Object} Filters formatted for API calls
   */
  const getAPIFilters = () => {
    const apiFilters = {}

    if (filters.value.dateFrom) apiFilters.travel_date__gte = filters.value.dateFrom
    if (filters.value.dateTo) apiFilters.travel_date__lte = filters.value.dateTo
    if (filters.value.organization) apiFilters.organization = filters.value.organization
    if (filters.value.travelAgent) apiFilters.travel_agent = filters.value.travelAgent
    if (filters.value.travellers && filters.value.travellers.length > 0) {
      apiFilters.travellers = filters.value.travellers.join(',')
    }
    if (filters.value.countries && filters.value.countries.length > 0) {
      apiFilters.countries = filters.value.countries.join(',')
    }
    if (filters.value.destinationPreset) apiFilters.destination_preset = filters.value.destinationPreset
    if (filters.value.city) apiFilters.city = filters.value.city
    if (filters.value.status) apiFilters.status = filters.value.status
    if (filters.value.productType) apiFilters.booking_type = filters.value.productType
    if (filters.value.supplier) apiFilters.supplier = filters.value.supplier
    if (filters.value.travelConsultant) apiFilters.travel_consultant = filters.value.travelConsultant
    if (filters.value.travelConsultants && filters.value.travelConsultants.length > 0) {
      apiFilters.travel_consultants = filters.value.travelConsultants.join(',')
    }

    return apiFilters
  }

  // Watch for route changes (e.g., browser back/forward)
  watch(() => route.query, () => {
    filters.value = initializeFiltersFromURL()
  }, { deep: true })

  return {
    filters,
    updateFilters,
    clearFilters,
    getAPIFilters
  }
}

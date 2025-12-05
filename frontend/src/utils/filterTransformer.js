/**
 * Filter Transformer Utility
 *
 * Converts UniversalFilters component output to backend API query parameters.
 * This ensures consistent filter parameter naming between frontend and backend.
 *
 * @module filterTransformer
 */

/**
 * Transform UniversalFilters output to backend API parameters
 *
 * Mapping:
 * - dateFrom/dateTo → travel_date__gte / travel_date__lte
 * - travellers (array) → travellers (comma-separated string)
 * - countries (array) → countries (comma-separated string)
 * - destinationPreset → destination_preset
 * - organization, status, city, supplier, booking_type → pass through as-is
 *
 * @param {Object} filters - Filters object from UniversalFilters component
 * @returns {Object} Transformed filters for backend API
 *
 * @example
 * const frontendFilters = {
 *   dateFrom: '2024-01-01',
 *   dateTo: '2024-12-31',
 *   travellers: [1, 2, 3],
 *   countries: ['AUS', 'NZL'],
 *   destinationPreset: 'within_user_country',
 *   organization: 5,
 *   status: 'CONFIRMED'
 * }
 *
 * const backendParams = transformFiltersForBackend(frontendFilters)
 * // Result:
 * // {
 * //   travel_date__gte: '2024-01-01',
 * //   travel_date__lte: '2024-12-31',
 * //   travellers: '1,2,3',
 * //   countries: 'AUS,NZL',
 * //   destination_preset: 'within_user_country',
 * //   organization: 5,
 * //   status: 'CONFIRMED'
 * // }
 */
export function transformFiltersForBackend(filters) {
  if (!filters || typeof filters !== 'object') {
    return {}
  }

  const backendParams = {}

  // Date range transformation (travel dates)
  if (filters.dateFrom) {
    backendParams.travel_date__gte = filters.dateFrom
  }
  if (filters.dateTo) {
    backendParams.travel_date__lte = filters.dateTo
  }

  // Booking date range transformation
  if (filters.booking_date_after) {
    backendParams.booking_date_after = filters.booking_date_after
  }
  if (filters.booking_date_before) {
    backendParams.booking_date_before = filters.booking_date_before
  }

  // Travellers - convert array to comma-separated string
  if (filters.travellers && Array.isArray(filters.travellers) && filters.travellers.length > 0) {
    backendParams.travellers = filters.travellers.join(',')
  }
  // Legacy single traveller support (for backwards compatibility)
  else if (filters.traveller) {
    backendParams.travellers = filters.traveller
  }

  // Countries - convert array to comma-separated string
  if (filters.countries && Array.isArray(filters.countries) && filters.countries.length > 0) {
    backendParams.countries = filters.countries.join(',')
  }
  // Legacy single country support (for backwards compatibility)
  else if (filters.country) {
    backendParams.countries = filters.country
  }

  // Destination preset - convert camelCase to snake_case
  if (filters.destinationPreset) {
    backendParams.destination_preset = filters.destinationPreset
  }

  // Travel Agent - convert camelCase to snake_case
  if (filters.travelAgent) {
    backendParams.travel_agent = filters.travelAgent
  }

  // Pass-through filters (no transformation needed)
  const passThroughFilters = ['organization', 'status', 'city', 'supplier', 'booking_type', 'product_type']
  passThroughFilters.forEach(key => {
    if (filters[key] !== undefined && filters[key] !== null && filters[key] !== '') {
      backendParams[key] = filters[key]
    }
  })

  return backendParams
}

/**
 * Transform backend API parameters back to UniversalFilters format
 * (Useful for initializing filters from URL params or saved preferences)
 *
 * @param {Object} backendParams - Backend API parameters
 * @returns {Object} Filters object for UniversalFilters component
 *
 * @example
 * const backendParams = {
 *   travel_date__gte: '2024-01-01',
 *   travel_date__lte: '2024-12-31',
 *   travellers: '1,2,3',
 *   countries: 'AUS,NZL'
 * }
 *
 * const frontendFilters = transformFiltersFromBackend(backendParams)
 * // Result:
 * // {
 * //   dateFrom: '2024-01-01',
 * //   dateTo: '2024-12-31',
 * //   travellers: [1, 2, 3],
 * //   countries: ['AUS', 'NZL']
 * // }
 */
export function transformFiltersFromBackend(backendParams) {
  if (!backendParams || typeof backendParams !== 'object') {
    return {}
  }

  const frontendFilters = {}

  // Date range transformation
  if (backendParams.travel_date__gte) {
    frontendFilters.dateFrom = backendParams.travel_date__gte
  }
  if (backendParams.travel_date__lte) {
    frontendFilters.dateTo = backendParams.travel_date__lte
  }

  // Travellers - convert comma-separated string to array
  if (backendParams.travellers) {
    const travellerStr = String(backendParams.travellers)
    frontendFilters.travellers = travellerStr.split(',').map(t => {
      const parsed = parseInt(t.trim(), 10)
      return isNaN(parsed) ? t.trim() : parsed
    })
  }

  // Countries - convert comma-separated string to array
  if (backendParams.countries) {
    const countryStr = String(backendParams.countries)
    frontendFilters.countries = countryStr.split(',').map(c => c.trim())
  }

  // Destination preset - convert snake_case to camelCase
  if (backendParams.destination_preset) {
    frontendFilters.destinationPreset = backendParams.destination_preset
  }

  // Travel Agent - convert snake_case to camelCase
  if (backendParams.travel_agent) {
    frontendFilters.travelAgent = backendParams.travel_agent
  }

  // Pass-through filters
  const passThroughFilters = ['organization', 'status', 'city', 'supplier', 'booking_type']
  passThroughFilters.forEach(key => {
    if (backendParams[key] !== undefined && backendParams[key] !== null && backendParams[key] !== '') {
      frontendFilters[key] = backendParams[key]
    }
  })

  return frontendFilters
}

/**
 * Build URL query string from filters
 *
 * @param {Object} filters - Filters from UniversalFilters component
 * @returns {string} URL query string (without leading '?')
 *
 * @example
 * const filters = { dateFrom: '2024-01-01', travellers: [1, 2] }
 * const queryString = buildQueryString(filters)
 * // Result: 'travel_date__gte=2024-01-01&travellers=1,2'
 */
export function buildQueryString(filters) {
  const backendParams = transformFiltersForBackend(filters)
  const params = new URLSearchParams()

  Object.entries(backendParams).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== '') {
      params.append(key, String(value))
    }
  })

  return params.toString()
}

/**
 * Count active filters (for displaying filter badge counts)
 *
 * @param {Object} filters - Filters from UniversalFilters component
 * @returns {number} Number of active filters
 */
export function countActiveFilters(filters) {
  if (!filters || typeof filters !== 'object') {
    return 0
  }

  let count = 0

  // Date range counts as 1 filter if either date is set
  if (filters.dateFrom || filters.dateTo) {
    count++
  }

  // Array filters
  if (filters.travellers?.length > 0) count++
  if (filters.countries?.length > 0) count++

  // Simple filters
  if (filters.destinationPreset) count++
  if (filters.organization) count++
  if (filters.status) count++
  if (filters.city) count++
  if (filters.supplier) count++
  if (filters.booking_type) count++

  return count
}

export default {
  transformFiltersForBackend,
  transformFiltersFromBackend,
  buildQueryString,
  countActiveFilters
}

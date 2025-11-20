// src/services/preferredAirlineService.js
import api from './api'
import { transformFiltersForBackend } from '@/utils/filterTransformer'

export default {
  // Get all preferred airlines
  async getPreferredAirlines(params = {}) {
    const response = await api.get('/preferred-airlines/', { params })
    return response.data
  },

  // Get single preferred airline
  async getPreferredAirline(id) {
    const response = await api.get(`/preferred-airlines/${id}/`)
    return response.data
  },

  // Create new preferred airline
  async createPreferredAirline(data) {
    const response = await api.post('/preferred-airlines/', data)
    return response.data
  },

  // Update preferred airline
  async updatePreferredAirline(id, data) {
    const response = await api.put(`/preferred-airlines/${id}/`, data)
    return response.data
  },

  // Delete preferred airline
  async deletePreferredAirline(id) {
    const response = await api.delete(`/preferred-airlines/${id}/`)
    return response.data
  },

  // Get active contracts
  async getActiveContracts(params = {}) {
    const response = await api.get('/preferred-airlines/active_contracts/', { params })
    return response.data
  },

  // Get contracts expiring soon
  async getExpiringSoon(days = 30, params = {}) {
    const response = await api.get('/preferred-airlines/expiring_soon/', {
      params: { days, ...params }
    })
    return response.data
  },

  // Activate contract
  async activateContract(id) {
    const response = await api.post(`/preferred-airlines/${id}/activate/`)
    return response.data
  },

  // Deactivate contract
  async deactivateContract(id) {
    const response = await api.post(`/preferred-airlines/${id}/deactivate/`)
    return response.data
  },

  // Get compliance report
  async getComplianceReport(params = {}) {
    const backendParams = transformFiltersForBackend(params)
    const response = await api.get('/preferred-airlines/compliance_report/', {
      params: backendParams
    })
    return response.data
  },

  // Get market share performance
  async getMarketSharePerformance(params = {}) {
    const backendParams = transformFiltersForBackend(params)
    const response = await api.get('/preferred-airlines/market_share_performance/', {
      params: backendParams
    })
    return response.data
  },

  // Helper: Format performance status badge class
  getPerformanceStatusClass(status) {
    const classes = {
      'EXCEEDING': 'bg-green-100 text-green-800',
      'MEETING': 'bg-blue-100 text-blue-800',
      'BELOW_TARGET': 'bg-red-100 text-red-800'
    }
    return classes[status] || 'bg-gray-100 text-gray-800'
  },

  // Helper: Format performance status display text
  getPerformanceStatusText(status) {
    const text = {
      'EXCEEDING': 'Exceeding',
      'MEETING': 'Meeting Target',
      'BELOW_TARGET': 'Below Target'
    }
    return text[status] || status
  },

  // Helper: Format contract status badge class
  getContractStatusClass(status) {
    const classes = {
      'ACTIVE': 'bg-green-100 text-green-800',
      'EXPIRED': 'bg-red-100 text-red-800',
      'FUTURE': 'bg-blue-100 text-blue-800',
      'INACTIVE': 'bg-gray-100 text-gray-800'
    }
    return classes[status] || 'bg-gray-100 text-gray-800'
  },

  // Helper: Format currency
  formatCurrency(amount, currency = 'AUD') {
    return new Intl.NumberFormat('en-AU', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount)
  },

  // Helper: Format percentage
  formatPercentage(value) {
    return `${value.toFixed(1)}%`
  }
}

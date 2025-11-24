// src/services/preferredCarHireService.js
import api from './api'
import { transformFiltersForBackend } from '@/utils/filterTransformer'

export default {
  // Get all preferred car hire contracts
  async getPreferredCarHires(params = {}) {
    const response = await api.get('/preferred-car-hires/', { params })
    return response.data
  },

  // Get single preferred car hire contract
  async getPreferredCarHire(id) {
    const response = await api.get(`/preferred-car-hires/${id}/`)
    return response.data
  },

  // Create new preferred car hire contract
  async createPreferredCarHire(data) {
    const response = await api.post('/preferred-car-hires/', data)
    return response.data
  },

  // Update preferred car hire contract
  async updatePreferredCarHire(id, data) {
    const response = await api.put(`/preferred-car-hires/${id}/`, data)
    return response.data
  },

  // Delete preferred car hire contract
  async deletePreferredCarHire(id) {
    const response = await api.delete(`/preferred-car-hires/${id}/`)
    return response.data
  },

  // Get active contracts
  async getActiveContracts(params = {}) {
    const response = await api.get('/preferred-car-hires/active_contracts/', { params })
    return response.data
  },

  // Get contracts expiring soon
  async getExpiringSoon(days = 30, params = {}) {
    const response = await api.get('/preferred-car-hires/expiring_soon/', {
      params: { days, ...params }
    })
    return response.data
  },

  // Activate contract
  async activateContract(id) {
    const response = await api.post(`/preferred-car-hires/${id}/activate/`)
    return response.data
  },

  // Deactivate contract
  async deactivateContract(id) {
    const response = await api.post(`/preferred-car-hires/${id}/deactivate/`)
    return response.data
  },

  // Get compliance report
  async getComplianceReport(params = {}) {
    console.log('🔍 [preferredCarHireService] getComplianceReport - input params:', params)
    const backendParams = transformFiltersForBackend(params)
    console.log('🔍 [preferredCarHireService] getComplianceReport - transformed params:', backendParams)
    const response = await api.get('/preferred-car-hires/compliance_report/', {
      params: backendParams
    })
    return response.data
  },

  // Get performance dashboard
  async getPerformanceDashboard(params = {}) {
    console.log('🔍 [preferredCarHireService] getPerformanceDashboard - input params:', params)
    const backendParams = transformFiltersForBackend(params)
    console.log('🔍 [preferredCarHireService] getPerformanceDashboard - transformed params:', backendParams)
    const response = await api.get('/preferred-car-hires/performance_dashboard/', {
      params: backendParams
    })
    return response.data
  },

  // Helper: Format performance status badge class
  getPerformanceStatusClass(status) {
    const classes = {
      'ABOVE_TARGET': 'bg-green-100 text-green-800',
      'ON_TARGET': 'bg-blue-100 text-blue-800',
      'BELOW_TARGET': 'bg-red-100 text-red-800'
    }
    return classes[status] || 'bg-gray-100 text-gray-800'
  },

  // Helper: Format performance status display text
  getPerformanceStatusText(status) {
    const text = {
      'ABOVE_TARGET': 'Above Target',
      'ON_TARGET': 'On Target',
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
  },

  // Helper: Format rental days
  formatRentalDays(days) {
    return new Intl.NumberFormat('en-AU').format(days)
  }
}

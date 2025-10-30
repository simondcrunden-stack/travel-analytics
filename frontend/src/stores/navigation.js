// Navigation Store - Complete Implementation
// Location: frontend/src/stores/navigation.js

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

export const useNavigationStore = defineStore('navigation', () => {
  const router = useRouter()
  
  // State
  const isSidebarCollapsed = ref(false)
  const isDesktop = ref(true)
  const recentPages = ref([])
  const maxRecentPages = 5
  
  // Computed
  const sidebarWidth = computed(() => {
    if (!isDesktop.value) return '256px' // Always full width on mobile
    return isSidebarCollapsed.value ? '64px' : '256px'
  })
  
  // Actions
  
  /**
   * Toggle sidebar collapsed state
   */
  function toggleSidebar() {
    isSidebarCollapsed.value = !isSidebarCollapsed.value
    // Save to localStorage
    localStorage.setItem('sidebarCollapsed', isSidebarCollapsed.value)
  }
  
  /**
   * Check screen size and update isDesktop flag
   */
  function checkScreenSize() {
    isDesktop.value = window.innerWidth >= 1024 // lg breakpoint
    
    // Auto-collapse on mobile
    if (!isDesktop.value && !isSidebarCollapsed.value) {
      isSidebarCollapsed.value = true
    }
  }
  
  /**
   * Add a page to recent pages history
   */
  function addRecentPage(page) {
    // Remove if already exists
    const index = recentPages.value.findIndex(p => p.path === page.path)
    if (index !== -1) {
      recentPages.value.splice(index, 1)
    }
    
    // Add to beginning
    recentPages.value.unshift(page)
    
    // Limit to maxRecentPages
    if (recentPages.value.length > maxRecentPages) {
      recentPages.value = recentPages.value.slice(0, maxRecentPages)
    }
    
    // Save to localStorage
    localStorage.setItem('recentPages', JSON.stringify(recentPages.value))
  }
  
  /**
   * Navigate to a route
   */
  function navigateTo(path) {
    router.push(path)
  }
  
  /**
   * Initialize store from localStorage
   */
  function initialize() {
    // Load sidebar state
    const savedSidebarState = localStorage.getItem('sidebarCollapsed')
    if (savedSidebarState !== null) {
      isSidebarCollapsed.value = savedSidebarState === 'true'
    }
    
    // Load recent pages
    const savedRecentPages = localStorage.getItem('recentPages')
    if (savedRecentPages) {
      try {
        recentPages.value = JSON.parse(savedRecentPages)
      } catch (e) {
        console.error('Error loading recent pages:', e)
        recentPages.value = []
      }
    }
    
    // Check initial screen size
    checkScreenSize()
  }
  
  // Initialize on store creation
  initialize()
  
  return {
    // State
    isSidebarCollapsed,
    isDesktop,
    recentPages,
    
    // Computed
    sidebarWidth,
    
    // Actions
    toggleSidebar,
    checkScreenSize,
    addRecentPage,
    navigateTo,
    initialize
  }
})
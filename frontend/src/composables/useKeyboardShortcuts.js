// Keyboard Shortcuts Composable
// Location: frontend/src/composables/useKeyboardShortcuts.js

import { onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useNavigationStore } from '@/stores/navigation'

export function useKeyboardShortcuts() {
  const router = useRouter()
  const navigationStore = useNavigationStore()
  
  // Track if we're in "go to" mode (after pressing 'g')
  let isGoMode = false
  let goModeTimeout = null
  
  // Shortcut definitions
  const shortcuts = {
    // Global shortcuts (Ctrl/Cmd + key)
    global: {
      'k': () => {
        navigationStore.toggleSidebar()
        showToast('Sidebar toggled')
      },
      'b': () => {
        router.push('/bookings')
        showToast('Navigate to Bookings')
      },
      'h': () => {
        router.push('/')
        showToast('Navigate to Dashboard')
      },
      '/': () => {
        showShortcutsHelp()
      }
    },
    
    // Navigation shortcuts (g + key)
    navigation: {
      'd': () => {
        router.push('/')
        showToast('Go to Dashboard')
      },
      'b': () => {
        router.push('/bookings')
        showToast('Go to Bookings')
      },
      'c': () => {
        router.push('/compliance')
        showToast('Go to Compliance')
      },
      'u': () => {
        router.push('/budgets')
        showToast('Go to Budgets')
      },
      'a': () => {
        router.push('/air')
        showToast('Go to Air Travel')
      },
      'h': () => {
        router.push('/accommodation')
        showToast('Go to Accommodation')
      },
      'r': () => {
        router.push('/car-hire')
        showToast('Go to Car Hire')
      },
      's': () => {
        router.push('/service-fees')
        showToast('Go to Service Fees')
      }
    }
  }
  
  // Handle keydown events
  const handleKeyDown = (event) => {
    // Don't trigger shortcuts when typing in inputs
    const target = event.target
    if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable) {
      return
    }
    
    const key = event.key.toLowerCase()
    const isCtrlOrCmd = event.ctrlKey || event.metaKey
    
    // Handle "go to" mode (press 'g' then another key)
    if (!isCtrlOrCmd && key === 'g' && !isGoMode) {
      isGoMode = true
      showToast('Go to...', 1000)
      
      // Reset go mode after 2 seconds
      if (goModeTimeout) clearTimeout(goModeTimeout)
      goModeTimeout = setTimeout(() => {
        isGoMode = false
      }, 2000)
      
      event.preventDefault()
      return
    }
    
    // Handle navigation shortcuts (g + key)
    if (isGoMode && shortcuts.navigation[key]) {
      shortcuts.navigation[key]()
      isGoMode = false
      if (goModeTimeout) clearTimeout(goModeTimeout)
      event.preventDefault()
      return
    }
    
    // Handle global shortcuts (Ctrl/Cmd + key)
    if (isCtrlOrCmd && shortcuts.global[key]) {
      shortcuts.global[key]()
      event.preventDefault()
      return
    }
    
    // Handle ESC key - close dropdowns/modals
    if (key === 'escape') {
      // You can emit an event here or call specific close functions
      showToast('ESC pressed')
      event.preventDefault()
      return
    }
  }
  
  // Show toast notification
  const showToast = (message, duration = 2000) => {
    // Create toast element
    const toast = document.createElement('div')
    toast.className = 'fixed bottom-4 right-4 bg-gray-900 text-white px-4 py-2 rounded-lg shadow-lg z-50 animate-slide-up'
    toast.textContent = message
    
    document.body.appendChild(toast)
    
    // Remove after duration
    setTimeout(() => {
      toast.classList.add('animate-fade-out')
      setTimeout(() => {
        document.body.removeChild(toast)
      }, 300)
    }, duration)
  }
  
  // Show shortcuts help modal
  const showShortcutsHelp = () => {
    const helpModal = document.createElement('div')
    helpModal.className = 'fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4'
    helpModal.innerHTML = `
      <div class="bg-white rounded-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto p-6">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-2xl font-bold text-gray-900">Keyboard Shortcuts</h2>
          <button class="close-modal p-2 hover:bg-gray-100 rounded-lg">
            <span class="mdi mdi-close text-2xl"></span>
          </button>
        </div>
        
        <div class="space-y-6">
          <!-- Global Shortcuts -->
          <div>
            <h3 class="text-lg font-semibold text-gray-900 mb-3">Global Shortcuts</h3>
            <div class="space-y-2">
              <div class="flex items-center justify-between py-2 border-b border-gray-100">
                <span class="text-gray-700">Toggle Sidebar</span>
                <kbd class="px-3 py-1 bg-gray-100 border border-gray-300 rounded text-sm font-mono">Ctrl + K</kbd>
              </div>
              <div class="flex items-center justify-between py-2 border-b border-gray-100">
                <span class="text-gray-700">Go to Bookings</span>
                <kbd class="px-3 py-1 bg-gray-100 border border-gray-300 rounded text-sm font-mono">Ctrl + B</kbd>
              </div>
              <div class="flex items-center justify-between py-2 border-b border-gray-100">
                <span class="text-gray-700">Go to Dashboard</span>
                <kbd class="px-3 py-1 bg-gray-100 border border-gray-300 rounded text-sm font-mono">Ctrl + H</kbd>
              </div>
              <div class="flex items-center justify-between py-2 border-b border-gray-100">
                <span class="text-gray-700">Show this help</span>
                <kbd class="px-3 py-1 bg-gray-100 border border-gray-300 rounded text-sm font-mono">Ctrl + /</kbd>
              </div>
            </div>
          </div>
          
          <!-- Navigation Shortcuts -->
          <div>
            <h3 class="text-lg font-semibold text-gray-900 mb-3">Navigation (Press G then...)</h3>
            <div class="space-y-2">
              <div class="flex items-center justify-between py-2 border-b border-gray-100">
                <span class="text-gray-700">Dashboard</span>
                <kbd class="px-3 py-1 bg-gray-100 border border-gray-300 rounded text-sm font-mono">G + D</kbd>
              </div>
              <div class="flex items-center justify-between py-2 border-b border-gray-100">
                <span class="text-gray-700">Bookings</span>
                <kbd class="px-3 py-1 bg-gray-100 border border-gray-300 rounded text-sm font-mono">G + B</kbd>
              </div>
              <div class="flex items-center justify-between py-2 border-b border-gray-100">
                <span class="text-gray-700">Compliance</span>
                <kbd class="px-3 py-1 bg-gray-100 border border-gray-300 rounded text-sm font-mono">G + C</kbd>
              </div>
              <div class="flex items-center justify-between py-2 border-b border-gray-100">
                <span class="text-gray-700">Budgets</span>
                <kbd class="px-3 py-1 bg-gray-100 border border-gray-300 rounded text-sm font-mono">G + U</kbd>
              </div>
              <div class="flex items-center justify-between py-2 border-b border-gray-100">
                <span class="text-gray-700">Air Travel</span>
                <kbd class="px-3 py-1 bg-gray-100 border border-gray-300 rounded text-sm font-mono">G + A</kbd>
              </div>
              <div class="flex items-center justify-between py-2 border-b border-gray-100">
                <span class="text-gray-700">Accommodation</span>
                <kbd class="px-3 py-1 bg-gray-100 border border-gray-300 rounded text-sm font-mono">G + H</kbd>
              </div>
              <div class="flex items-center justify-between py-2 border-b border-gray-100">
                <span class="text-gray-700">Car Hire</span>
                <kbd class="px-3 py-1 bg-gray-100 border border-gray-300 rounded text-sm font-mono">G + R</kbd>
              </div>
              <div class="flex items-center justify-between py-2 border-b border-gray-100">
                <span class="text-gray-700">Service Fees</span>
                <kbd class="px-3 py-1 bg-gray-100 border border-gray-300 rounded text-sm font-mono">G + S</kbd>
              </div>
            </div>
          </div>
          
          <!-- General -->
          <div>
            <h3 class="text-lg font-semibold text-gray-900 mb-3">General</h3>
            <div class="space-y-2">
              <div class="flex items-center justify-between py-2">
                <span class="text-gray-700">Close modal/dropdown</span>
                <kbd class="px-3 py-1 bg-gray-100 border border-gray-300 rounded text-sm font-mono">ESC</kbd>
              </div>
            </div>
          </div>
        </div>
        
        <div class="mt-6 pt-4 border-t border-gray-200">
          <p class="text-sm text-gray-500">
            💡 Tip: Use <kbd class="px-2 py-0.5 bg-gray-100 border border-gray-300 rounded text-xs font-mono">Cmd</kbd> on Mac instead of Ctrl
          </p>
        </div>
      </div>
    `
    
    document.body.appendChild(helpModal)
    
    // Close modal on click outside or close button
    helpModal.addEventListener('click', (e) => {
      if (e.target === helpModal || e.target.closest('.close-modal')) {
        helpModal.classList.add('animate-fade-out')
        setTimeout(() => {
          document.body.removeChild(helpModal)
        }, 200)
      }
    })
    
    // Close on ESC
    const closeOnEsc = (e) => {
      if (e.key === 'Escape') {
        helpModal.classList.add('animate-fade-out')
        setTimeout(() => {
          document.body.removeChild(helpModal)
        }, 200)
        document.removeEventListener('keydown', closeOnEsc)
      }
    }
    document.addEventListener('keydown', closeOnEsc)
  }
  
  // Register event listeners
  onMounted(() => {
    document.addEventListener('keydown', handleKeyDown)
  })
  
  onUnmounted(() => {
    document.removeEventListener('keydown', handleKeyDown)
    if (goModeTimeout) clearTimeout(goModeTimeout)
  })
  
  return {
    showShortcutsHelp
  }
}
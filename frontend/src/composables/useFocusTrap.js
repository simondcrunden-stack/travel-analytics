import { onMounted, onUnmounted, watch } from 'vue'

export function useFocusTrap(containerRef, isActive) {
  const FOCUSABLE_ELEMENTS = [
    'a[href]',
    'button:not([disabled])',
    'textarea:not([disabled])',
    'input:not([disabled])',
    'select:not([disabled])',
    '[tabindex]:not([tabindex="-1"])'
  ].join(',')

  const handleKeyDown = (event) => {
    if (!isActive.value || event.key !== 'Tab') return

    const container = containerRef.value
    if (!container) return

    const focusableElements = container.querySelectorAll(FOCUSABLE_ELEMENTS)
    const firstElement = focusableElements[0]
    const lastElement = focusableElements[focusableElements.length - 1]

    if (event.shiftKey) {
      // Shift + Tab
      if (document.activeElement === firstElement) {
        event.preventDefault()
        lastElement.focus()
      }
    } else {
      // Tab
      if (document.activeElement === lastElement) {
        event.preventDefault()
        firstElement.focus()
      }
    }
  }

  watch(isActive, (active) => {
    if (active) {
      // Focus first element when opened
      setTimeout(() => {
        const container = containerRef.value
        if (container) {
          const firstFocusable = container.querySelector(FOCUSABLE_ELEMENTS)
          if (firstFocusable) {
            firstFocusable.focus()
          }
        }
      }, 100)
    }
  })

  onMounted(() => {
    document.addEventListener('keydown', handleKeyDown)
  })

  onUnmounted(() => {
    document.removeEventListener('keydown', handleKeyDown)
  })
}
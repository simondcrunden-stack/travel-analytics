<template>
  <div class="fixed inset-0 z-50 overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
    <!-- Backdrop -->
    <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" @click="$emit('close')"></div>

    <!-- Modal -->
    <div class="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
      <div class="relative transform overflow-hidden rounded-lg bg-white text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg">
        <!-- Header -->
        <div class="bg-white px-6 pt-5 pb-4">
          <div class="flex items-center justify-between">
            <h3 class="text-lg font-medium text-gray-900" id="modal-title">
              {{ isEditMode ? 'Edit Node' : 'Add New Node' }}
            </h3>
            <button
              @click="$emit('close')"
              class="text-gray-400 hover:text-gray-500 focus:outline-none"
            >
              <span class="mdi mdi-close text-xl"></span>
            </button>
          </div>
        </div>

        <!-- Form -->
        <form @submit.prevent="handleSubmit" class="px-6 pb-4">
          <!-- Error Message -->
          <div v-if="error" class="mb-4 bg-red-50 border border-red-200 rounded-lg p-3">
            <div class="flex">
              <span class="mdi mdi-alert-circle text-red-600 text-lg mr-2"></span>
              <p class="text-sm text-red-700">{{ error }}</p>
            </div>
          </div>

          <!-- Code Field -->
          <div class="mb-4">
            <label for="code" class="block text-sm font-medium text-gray-700 mb-1">
              Code <span class="text-red-500">*</span>
            </label>
            <input
              id="code"
              v-model="formData.code"
              type="text"
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="e.g., VIC-001, ASPAC-SALES"
            />
            <p class="mt-1 text-xs text-gray-500">
              Unique identifier for this node
            </p>
          </div>

          <!-- Name Field -->
          <div class="mb-4">
            <label for="name" class="block text-sm font-medium text-gray-700 mb-1">
              Name <span class="text-red-500">*</span>
            </label>
            <input
              id="name"
              v-model="formData.name"
              type="text"
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="e.g., Victoria Sales Team, ASPAC Region"
            />
            <p class="mt-1 text-xs text-gray-500">
              Display name for this node
            </p>
          </div>

          <!-- Node Type Field -->
          <div class="mb-4">
            <label for="node_type" class="block text-sm font-medium text-gray-700 mb-1">
              Node Type <span class="text-red-500">*</span>
            </label>
            <select
              id="node_type"
              v-model="formData.node_type"
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">Select type...</option>
              <option value="COST_CENTER">Cost Center</option>
              <option value="BUSINESS_UNIT">Business Unit</option>
              <option value="REGION">Region</option>
              <option value="DEPARTMENT">Department</option>
              <option value="DIVISION">Division</option>
              <option value="GROUP">Group</option>
              <option value="OTHER">Other</option>
            </select>
            <p class="mt-1 text-xs text-gray-500">
              Classification of this organizational node
            </p>
          </div>

          <!-- Description Field -->
          <div class="mb-4">
            <label for="description" class="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              id="description"
              v-model="formData.description"
              rows="3"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Optional description or notes"
            ></textarea>
          </div>

          <!-- Parent Info (Read-only display) -->
          <div v-if="parentInfo" class="mb-4 bg-blue-50 border border-blue-200 rounded-lg p-3">
            <div class="flex items-start">
              <span class="mdi mdi-information text-blue-600 text-lg mr-2 mt-0.5"></span>
              <div class="flex-1">
                <p class="text-sm font-medium text-blue-900">Parent Node</p>
                <p class="text-sm text-blue-700 mt-1">{{ parentInfo }}</p>
              </div>
            </div>
          </div>

          <!-- Active Status (Edit mode only) -->
          <div v-if="isEditMode" class="mb-4">
            <label class="flex items-center">
              <input
                v-model="formData.is_active"
                type="checkbox"
                class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span class="ml-2 text-sm text-gray-700">Active</span>
            </label>
            <p class="mt-1 text-xs text-gray-500">
              Inactive nodes are hidden from the tree view
            </p>
          </div>

          <!-- Actions -->
          <div class="flex justify-end space-x-3 pt-4 border-t border-gray-200">
            <button
              type="button"
              @click="$emit('close')"
              class="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Cancel
            </button>
            <button
              type="submit"
              :disabled="saving"
              class="px-4 py-2 border border-transparent rounded-lg text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span v-if="saving" class="inline-flex items-center">
                <span class="animate-spin mdi mdi-loading mr-2"></span>
                Saving...
              </span>
              <span v-else>{{ isEditMode ? 'Update' : 'Create' }}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const props = defineProps({
  node: {
    type: Object,
    default: null
  },
  parentId: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['save', 'cancel'])

const authStore = useAuthStore()

// State
const saving = ref(false)
const error = ref(null)
const formData = ref({
  code: '',
  name: '',
  node_type: '',
  description: '',
  parent: null,
  is_active: true
})

// Computed
const isEditMode = computed(() => !!props.node)

const parentInfo = computed(() => {
  if (!props.parentId && !props.node?.parent_name) {
    return null
  }

  if (isEditMode.value && props.node?.parent_name) {
    return `This node is under: ${props.node.parent_name}`
  }

  if (props.parentId) {
    return 'This node will be created as a child node'
  }

  return null
})

// Methods
const handleSubmit = async () => {
  try {
    saving.value = true
    error.value = null

    // Validate
    if (!formData.value.code || !formData.value.name || !formData.value.node_type) {
      error.value = 'Please fill in all required fields'
      return
    }

    // Prepare data
    const payload = {
      code: formData.value.code.trim(),
      name: formData.value.name.trim(),
      node_type: formData.value.node_type,
      description: formData.value.description?.trim() || '',
      is_active: formData.value.is_active,
      organization: authStore.user.organization
    }

    // Add parent if provided
    if (props.parentId) {
      payload.parent = props.parentId
    } else if (isEditMode.value && props.node?.parent) {
      payload.parent = props.node.parent
    }

    // Emit save event
    emit('save', payload)
  } catch (err) {
    error.value = err.message || 'Failed to save node'
    console.error('Error saving node:', err)
  } finally {
    saving.value = false
  }
}

// Lifecycle
onMounted(() => {
  if (isEditMode.value && props.node) {
    // Populate form with existing node data
    formData.value = {
      code: props.node.code || '',
      name: props.node.name || '',
      node_type: props.node.node_type || '',
      description: props.node.description || '',
      parent: props.node.parent || null,
      is_active: props.node.is_active !== undefined ? props.node.is_active : true
    }
  }
})
</script>

<style scoped>
/* Override default input styles for better appearance */
input:focus,
select:focus,
textarea:focus {
  outline: none;
}

/* Smooth transitions */
.transition-opacity {
  transition: opacity 0.2s ease-in-out;
}
</style>

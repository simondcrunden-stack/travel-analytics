<template>
  <div class="organization-structure-view">
    <!-- Page Header -->
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-900">Organization Structure</h1>
      <p class="mt-1 text-sm text-gray-600">
        Manage your organizational hierarchy - cost centers, business units, departments, and divisions
      </p>
    </div>

    <!-- Organization Selector (for travel agents managing multiple customers) -->
    <div v-if="showOrganizationSelector" class="bg-white rounded-xl shadow-sm p-4 mb-6">
      <div class="flex items-center space-x-4">
        <label for="organization-select" class="text-sm font-medium text-gray-700 whitespace-nowrap">
          Select Customer:
        </label>
        <select
          id="organization-select"
          v-model="selectedOrganizationId"
          @change="onOrganizationChange"
          class="flex-1 max-w-md px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="">-- Select a customer organization --</option>
          <option
            v-for="org in organizations"
            :key="org.id"
            :value="org.id"
          >
            {{ org.name }}
          </option>
        </select>
      </div>
    </div>

    <!-- Action Bar -->
    <div class="bg-white rounded-xl shadow-sm p-4 mb-6">
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-4">
          <button
            @click="showAddRootNodeDialog = true"
            :disabled="!selectedOrganizationId"
            class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span class="mdi mdi-plus mr-2"></span>
            Add Root Node
          </button>
          <button
            @click="expandAll"
            :disabled="!selectedOrganizationId"
            class="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span class="mdi mdi-arrow-expand-all mr-2"></span>
            Expand All
          </button>
          <button
            @click="collapseAll"
            :disabled="!selectedOrganizationId"
            class="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span class="mdi mdi-arrow-collapse-all mr-2"></span>
            Collapse All
          </button>
        </div>
        <div class="flex items-center">
          <span class="text-sm text-gray-500 mr-2">
            Total Nodes: {{ totalNodes }}
          </span>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center items-center py-12">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-lg p-4">
      <div class="flex">
        <span class="mdi mdi-alert-circle text-red-600 text-xl mr-2"></span>
        <div>
          <h3 class="text-sm font-medium text-red-800">Error loading organization structure</h3>
          <p class="text-sm text-red-700 mt-1">{{ error }}</p>
        </div>
      </div>
    </div>

    <!-- Tree View -->
    <div v-else class="bg-white rounded-xl shadow-sm p-6">
      <!-- Empty state when no organization selected -->
      <div v-if="!selectedOrganizationId" class="text-center py-12">
        <span class="mdi mdi-domain text-gray-400 text-6xl"></span>
        <p class="mt-4 text-gray-500">Please select a customer organization above</p>
        <p class="text-sm text-gray-400">Choose which customer's organizational structure you want to manage</p>
      </div>
      <!-- Empty state when no structure defined -->
      <div v-else-if="treeData.length === 0" class="text-center py-12">
        <span class="mdi mdi-file-tree-outline text-gray-400 text-6xl"></span>
        <p class="mt-4 text-gray-500">No organizational structure defined yet</p>
        <p class="text-sm text-gray-400">Click "Add Root Node" to get started</p>
      </div>
      <div v-else>
        <tree-node
          v-for="node in treeData"
          :key="node.id"
          :node="node"
          :level="0"
          :expanded-nodes="expandedNodes"
          @toggle="toggleNode"
          @add-child="handleAddChild"
          @edit="handleEdit"
          @delete="handleDelete"
          @merge="handleMerge"
        />
      </div>
    </div>

    <!-- Add/Edit Node Dialog -->
    <node-dialog
      v-if="showNodeDialog"
      :node="selectedNode"
      :parent-id="parentId"
      :organization-id="selectedOrganizationId"
      @save="handleSaveNode"
      @cancel="showNodeDialog = false"
    />

    <!-- Merge Node Dialog -->
    <merge-dialog
      v-if="showMergeDialog"
      :source-node="selectedNode"
      :available-nodes="availableNodesForMerge"
      @merge="handleMergeConfirm"
      @cancel="showMergeDialog = false"
    />

    <!-- Add Root Node Dialog -->
    <node-dialog
      v-if="showAddRootNodeDialog"
      :node="null"
      :parent-id="null"
      :organization-id="selectedOrganizationId"
      @save="handleSaveNode"
      @cancel="showAddRootNodeDialog = false"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import TreeNode from '@/components/organization/TreeNode.vue'
import NodeDialog from '@/components/organization/NodeDialog.vue'
import MergeDialog from '@/components/organization/MergeDialog.vue'
import organizationService from '@/services/organizationService'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

// State
const loading = ref(true)
const error = ref(null)
const treeData = ref([])
const expandedNodes = ref(new Set())
const selectedNode = ref(null)
const parentId = ref(null)
const showNodeDialog = ref(false)
const showMergeDialog = ref(false)
const showAddRootNodeDialog = ref(false)

// Organization selector state
const organizations = ref([])
const selectedOrganizationId = ref('')

// Computed
const showOrganizationSelector = computed(() => {
  // Show selector for travel agents managing multiple customers
  return authStore.user && ['AGENT_ADMIN', 'AGENT_USER'].includes(authStore.user.user_type)
})

const totalNodes = computed(() => {
  const countNodes = (nodes) => {
    let count = nodes.length
    nodes.forEach(node => {
      if (node.children && node.children.length > 0) {
        count += countNodes(node.children)
      }
    })
    return count
  }
  return countNodes(treeData.value)
})

const availableNodesForMerge = computed(() => {
  if (!selectedNode.value) return []

  const allNodes = []
  const collectNodes = (nodes) => {
    nodes.forEach(node => {
      // Can only merge with nodes of the same type
      if (node.id !== selectedNode.value.id && node.node_type === selectedNode.value.node_type) {
        allNodes.push(node)
      }
      if (node.children && node.children.length > 0) {
        collectNodes(node.children)
      }
    })
  }
  collectNodes(treeData.value)
  return allNodes
})

// Methods
const loadOrganizations = async () => {
  try {
    const response = await api.get('/organizations/')
    organizations.value = response.data

    // Auto-select organization for customer users
    if (!showOrganizationSelector.value && authStore.user?.organization) {
      selectedOrganizationId.value = authStore.user.organization
    }
  } catch (err) {
    console.error('Error loading organizations:', err)
  }
}

const loadData = async () => {
  if (!selectedOrganizationId.value) {
    treeData.value = []
    loading.value = false
    return
  }

  try {
    loading.value = true
    error.value = null
    const response = await organizationService.getOrganizationTree({
      organization: selectedOrganizationId.value
    })
    treeData.value = response.data
  } catch (err) {
    error.value = err.message || 'Failed to load organization structure'
    console.error('Error loading organization structure:', err)
  } finally {
    loading.value = false
  }
}

const onOrganizationChange = () => {
  // Reset tree and reload data for selected organization
  treeData.value = []
  expandedNodes.value.clear()
  loadData()
}

const toggleNode = (nodeId) => {
  if (expandedNodes.value.has(nodeId)) {
    expandedNodes.value.delete(nodeId)
  } else {
    expandedNodes.value.add(nodeId)
  }
}

const expandAll = () => {
  const getAllNodeIds = (nodes) => {
    const ids = []
    nodes.forEach(node => {
      ids.push(node.id)
      if (node.children && node.children.length > 0) {
        ids.push(...getAllNodeIds(node.children))
      }
    })
    return ids
  }
  expandedNodes.value = new Set(getAllNodeIds(treeData.value))
}

const collapseAll = () => {
  expandedNodes.value.clear()
}

const handleAddChild = (parentNode) => {
  selectedNode.value = null
  parentId.value = parentNode.id
  showNodeDialog.value = true
}

const handleEdit = (node) => {
  selectedNode.value = node
  parentId.value = node.parent
  showNodeDialog.value = true
}

const handleDelete = async (node) => {
  if (!confirm(`Are you sure you want to delete "${node.name}"? This action cannot be undone.`)) {
    return
  }

  try {
    await organizationService.deleteOrganizationalNode(node.id)
    await loadData()
  } catch (err) {
    alert(`Error deleting node: ${err.message}`)
  }
}

const handleMerge = (node) => {
  selectedNode.value = node
  showMergeDialog.value = true
}

const handleSaveNode = async (nodeData) => {
  try {
    if (selectedNode.value) {
      // Update existing node
      await organizationService.updateOrganizationalNode(selectedNode.value.id, nodeData)
    } else {
      // Create new node
      await organizationService.createOrganizationalNode(nodeData)
    }

    showNodeDialog.value = false
    showAddRootNodeDialog.value = false
    await loadData()
  } catch (err) {
    alert(`Error saving node: ${err.message}`)
  }
}

const handleMergeConfirm = async (targetId) => {
  try {
    await organizationService.mergeOrganizationalNode(selectedNode.value.id, targetId)
    showMergeDialog.value = false
    await loadData()
  } catch (err) {
    alert(`Error merging nodes: ${err.message}`)
  }
}

// Lifecycle
onMounted(async () => {
  await loadOrganizations()
  if (selectedOrganizationId.value) {
    await loadData()
  } else {
    loading.value = false
  }
})
</script>

<style scoped>
.organization-structure-view {
  padding: 1.5rem;
}
</style>

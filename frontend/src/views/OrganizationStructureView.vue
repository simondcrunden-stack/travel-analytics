<template>
  <div class="organization-structure-view p-6 space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Organization Structure</h1>
        <p class="text-sm text-gray-600 mt-1">
          Manage organizational hierarchies for customer organizations
        </p>
      </div>
    </div>

    <!-- Travel Agent & Organization Selectors -->
    <div class="bg-white rounded-lg shadow p-6 space-y-4">
      <h2 class="text-lg font-semibold text-gray-900">Select Organization</h2>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <!-- Travel Agent Selector -->
        <div>
          <label for="travel-agent" class="block text-sm font-medium text-gray-700 mb-2">
            Travel Agent
          </label>
          <select
            id="travel-agent"
            v-model="selectedTravelAgent"
            @change="handleTravelAgentChange"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Select a Travel Agent</option>
            <option v-for="agent in travelAgents" :key="agent.id" :value="agent.id">
              {{ agent.name }} ({{ agent.code }})
            </option>
          </select>
        </div>

        <!-- Customer Organization Selector -->
        <div>
          <label for="organization" class="block text-sm font-medium text-gray-700 mb-2">
            Customer Organization
          </label>
          <select
            id="organization"
            v-model="selectedOrganization"
            :disabled="!selectedTravelAgent"
            @change="handleOrganizationChange"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
          >
            <option value="">
              {{ selectedTravelAgent ? 'Select a Customer Organization' : 'Select a Travel Agent first' }}
            </option>
            <option v-for="org in customerOrganizations" :key="org.id" :value="org.id">
              {{ org.name }} ({{ org.code }})
            </option>
          </select>
        </div>
      </div>

      <!-- Selected Organization Details -->
      <div v-if="selectedOrganization && selectedOrgDetails" class="mt-4 p-4 bg-blue-50 rounded-lg">
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <span class="text-gray-600">Name:</span>
            <span class="ml-2 font-medium">{{ selectedOrgDetails.name }}</span>
          </div>
          <div>
            <span class="text-gray-600">Code:</span>
            <span class="ml-2 font-medium">{{ selectedOrgDetails.code }}</span>
          </div>
          <div>
            <span class="text-gray-600">Type:</span>
            <span class="ml-2 font-medium">{{ selectedOrgDetails.org_type }}</span>
          </div>
          <div>
            <span class="text-gray-600">Status:</span>
            <span class="ml-2 font-medium">
              <span
                :class="[
                  'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium',
                  selectedOrgDetails.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                ]"
              >
                {{ selectedOrgDetails.is_active ? 'Active' : 'Inactive' }}
              </span>
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Organizational Hierarchy Tree -->
    <div v-if="selectedOrganization" class="bg-white rounded-lg shadow">
      <!-- Tree Header -->
      <div class="p-6 border-b border-gray-200">
        <div class="flex items-center justify-between">
          <h2 class="text-lg font-semibold text-gray-900">Department & Division Hierarchy</h2>
          <div class="flex items-center space-x-2">
            <button
              @click="expandAll"
              class="px-3 py-1.5 text-sm text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
            >
              <span class="mdi mdi-chevron-down mr-1"></span>
              Expand All
            </button>
            <button
              @click="collapseAll"
              class="px-3 py-1.5 text-sm text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
            >
              <span class="mdi mdi-chevron-up mr-1"></span>
              Collapse All
            </button>
            <button
              @click="handleAddRoot"
              class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <span class="mdi mdi-plus mr-1"></span>
              Add Root Node
            </button>
            <button
              @click="refreshTree"
              class="px-3 py-2 text-gray-600 hover:bg-gray-50 rounded-lg transition-colors"
            >
              <span class="mdi mdi-refresh"></span>
            </button>
          </div>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="p-12 text-center">
        <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <p class="mt-4 text-gray-600">Loading organizational hierarchy...</p>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="p-12 text-center">
        <span class="mdi mdi-alert-circle text-4xl text-red-500"></span>
        <p class="mt-4 text-red-600">{{ error }}</p>
        <button
          @click="refreshTree"
          class="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Retry
        </button>
      </div>

      <!-- Empty State -->
      <div v-else-if="!treeData || treeData.length === 0" class="p-12 text-center">
        <span class="mdi mdi-file-tree-outline text-4xl text-gray-400"></span>
        <p class="mt-4 text-gray-600">No organizational hierarchy found</p>
        <p class="text-sm text-gray-500 mt-2">
          Get started by adding a root node to create your organization structure
        </p>
        <button
          @click="handleAddRoot"
          class="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <span class="mdi mdi-plus mr-1"></span>
          Add Root Node
        </button>
      </div>

      <!-- Tree Display -->
      <div v-else class="p-6">
        <tree-node
          v-for="node in treeData"
          :key="node.id"
          :node="node"
          :level="0"
          :expanded-nodes="expandedNodes"
          @toggle="handleToggle"
          @add-child="handleAddChild"
          @edit="handleEdit"
          @delete="handleDelete"
          @merge="handleMerge"
        />
      </div>
    </div>

    <!-- Empty State (No Organization Selected) -->
    <div v-else class="bg-white rounded-lg shadow p-12 text-center">
      <span class="mdi mdi-office-building-outline text-6xl text-gray-300"></span>
      <p class="mt-4 text-gray-600 text-lg">Select an organization to view its hierarchy</p>
      <p class="text-sm text-gray-500 mt-2">
        Choose a travel agent and customer organization from the selectors above
      </p>
    </div>

    <!-- Node Dialog (Add/Edit) -->
    <node-dialog
      v-if="showNodeDialog"
      :node="selectedNode"
      :parent-node="parentNode"
      :organization-id="selectedOrganization"
      @close="closeNodeDialog"
      @saved="handleNodeSaved"
    />

    <!-- Merge Dialog -->
    <merge-dialog
      v-if="showMergeDialog"
      :source-node="nodeToMerge"
      :organization-id="selectedOrganization"
      @close="closeMergeDialog"
      @merged="handleNodeMerged"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api'
import organizationService from '@/services/organizationService'
import TreeNode from '@/components/organization/TreeNode.vue'
import NodeDialog from '@/components/organization/NodeDialog.vue'
import MergeDialog from '@/components/organization/MergeDialog.vue'

const authStore = useAuthStore()

// State
const travelAgents = ref([])
const customerOrganizations = ref([])
const selectedTravelAgent = ref('')
const selectedOrganization = ref('')
const selectedOrgDetails = ref(null)

const treeData = ref([])
const expandedNodes = ref(new Set())
const loading = ref(false)
const error = ref(null)

// Dialog State
const showNodeDialog = ref(false)
const showMergeDialog = ref(false)
const selectedNode = ref(null)
const parentNode = ref(null)
const nodeToMerge = ref(null)

// Check admin access
const isSystemAdmin = computed(() => {
  return authStore.userType === 'ADMIN'
})

// Lifecycle
onMounted(() => {
  if (!isSystemAdmin.value) {
    error.value = 'Access denied. System admin privileges required.'
    return
  }
  loadTravelAgents()
})

// Watchers
watch(selectedTravelAgent, (newValue) => {
  if (newValue) {
    selectedOrganization.value = ''
    selectedOrgDetails.value = null
    treeData.value = []
    loadCustomerOrganizations()
  } else {
    customerOrganizations.value = []
    selectedOrganization.value = ''
    selectedOrgDetails.value = null
    treeData.value = []
  }
})

watch(selectedOrganization, (newValue) => {
  if (newValue) {
    loadOrganizationDetails()
    loadOrganizationTree()
  } else {
    selectedOrgDetails.value = null
    treeData.value = []
  }
})

// Data Loading Methods
const loadTravelAgents = async () => {
  try {
    const response = await api.get('/organizations/', {
      params: { org_type: 'AGENT' }
    })
    travelAgents.value = Array.isArray(response.data.results || response.data)
      ? (response.data.results || response.data)
      : []
  } catch (err) {
    console.error('Error loading travel agents:', err)
    error.value = 'Failed to load travel agents'
  }
}

const loadCustomerOrganizations = async () => {
  try {
    const response = await api.get('/organizations/', {
      params: { travel_agent: selectedTravelAgent.value }
    })
    customerOrganizations.value = Array.isArray(response.data.results || response.data)
      ? (response.data.results || response.data)
      : []
  } catch (err) {
    console.error('Error loading customer organizations:', err)
    error.value = 'Failed to load customer organizations'
  }
}

const loadOrganizationDetails = async () => {
  try {
    const response = await api.get(`/organizations/${selectedOrganization.value}/`)
    selectedOrgDetails.value = response.data
  } catch (err) {
    console.error('Error loading organization details:', err)
  }
}

const loadOrganizationTree = async () => {
  loading.value = true
  error.value = null

  try {
    const response = await organizationService.getOrganizationTree({
      organization: selectedOrganization.value
    })

    // The API returns the tree structure directly
    treeData.value = Array.isArray(response.data) ? response.data : []

    // Auto-expand root nodes
    treeData.value.forEach(node => {
      expandedNodes.value.add(node.id)
    })
  } catch (err) {
    console.error('Error loading organization tree:', err)
    error.value = err.response?.data?.detail || 'Failed to load organizational hierarchy'
    treeData.value = []
  } finally {
    loading.value = false
  }
}

// Selector Handlers
const handleTravelAgentChange = () => {
  // Watcher will handle the reset and reload
}

const handleOrganizationChange = () => {
  // Watcher will handle loading the tree
}

// Tree Navigation
const handleToggle = (nodeId) => {
  if (expandedNodes.value.has(nodeId)) {
    expandedNodes.value.delete(nodeId)
  } else {
    expandedNodes.value.add(nodeId)
  }
  // Trigger reactivity
  expandedNodes.value = new Set(expandedNodes.value)
}

const expandAll = () => {
  const allIds = organizationService.getAllNodeIds(treeData.value)
  expandedNodes.value = new Set(allIds)
}

const collapseAll = () => {
  expandedNodes.value = new Set()
}

const refreshTree = () => {
  if (selectedOrganization.value) {
    loadOrganizationTree()
  }
}

// Node CRUD Operations
const handleAddRoot = () => {
  selectedNode.value = null
  parentNode.value = null
  showNodeDialog.value = true
}

const handleAddChild = (node) => {
  selectedNode.value = null
  parentNode.value = node
  showNodeDialog.value = true
}

const handleEdit = (node) => {
  selectedNode.value = node
  parentNode.value = null
  showNodeDialog.value = true
}

const handleDelete = async (node) => {
  // Check if node can be deleted
  if (node.children && node.children.length > 0) {
    alert('Cannot delete node with children. Please delete or move child nodes first.')
    return
  }

  if (node.traveller_count > 0 || node.budget_count > 0) {
    alert('Cannot delete node with associated travellers or budgets. Please reassign them first.')
    return
  }

  if (!confirm(`Are you sure you want to delete "${node.name}"?`)) {
    return
  }

  try {
    await organizationService.deleteOrganizationalNode(node.id)
    await refreshTree()
  } catch (err) {
    console.error('Error deleting node:', err)
    alert(err.response?.data?.detail || 'Failed to delete node')
  }
}

const handleMerge = (node) => {
  nodeToMerge.value = node
  showMergeDialog.value = true
}

// Dialog Handlers
const closeNodeDialog = () => {
  showNodeDialog.value = false
  selectedNode.value = null
  parentNode.value = null
}

const handleNodeSaved = () => {
  closeNodeDialog()
  refreshTree()
}

const closeMergeDialog = () => {
  showMergeDialog.value = false
  nodeToMerge.value = null
}

const handleNodeMerged = () => {
  closeMergeDialog()
  refreshTree()
}
</script>

<style scoped>
/* Add any view-specific styles here */
</style>

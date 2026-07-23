<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { projectService } from '@/services/project.service'
import { useUiStore } from '@/stores/ui'
import { useAuthStore } from '@/stores/auth'
import type { Project, ProjectCreate } from '@/types'

const uiStore = useUiStore()
const authStore = useAuthStore()

const projects = ref<Project[]>([])
const isLoading = ref(true)
const searchQuery = ref('')
const statusFilter = ref('')
const showCreateModal = ref(false)
const totalProjects = ref(0)
const currentPage = ref(1)

// Create form
const newProject = ref<ProjectCreate>({
  name: '',
  client: '',
  description: '',
})

const filteredProjects = computed(() => {
  return projects.value
})

async function loadProjects() {
  isLoading.value = true
  try {
    const result = await projectService.list({
      page: currentPage.value,
      search: searchQuery.value || undefined,
      status: statusFilter.value || undefined,
    })
    projects.value = result.items
    totalProjects.value = result.total
  } catch (err) {
    console.error('Failed to load projects:', err)
    // Show placeholder if API not ready
    projects.value = []
  } finally {
    isLoading.value = false
  }
}

async function createProject() {
  try {
    await projectService.create(newProject.value)
    uiStore.addToast({ type: 'success', title: 'Project created successfully' })
    showCreateModal.value = false
    newProject.value = { name: '', client: '', description: '' }
    await loadProjects()
  } catch (err: any) {
    uiStore.addToast({
      type: 'error',
      title: 'Failed to create project',
      message: err.response?.data?.detail || 'An error occurred',
    })
  }
}

async function deleteProject(id: string) {
  if (!confirm('Are you sure you want to delete this project?')) return

  try {
    await projectService.delete(id)
    uiStore.addToast({ type: 'success', title: 'Project deleted' })
    await loadProjects()
  } catch (err) {
    uiStore.addToast({ type: 'error', title: 'Failed to delete project' })
  }
}

function getStatusBadge(status: string) {
  switch (status) {
    case 'active': return 'badge-success'
    case 'archived': return 'badge-warning'
    case 'completed': return 'badge-info'
    default: return 'badge-info'
  }
}

onMounted(loadProjects)
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-surface-900 dark:text-white">Projects</h1>
        <p class="text-surface-500 mt-1">Manage your artwork production projects</p>
      </div>
      <button
        v-if="authStore.hasPermission('Project.Create')"
        @click="showCreateModal = true"
        class="btn-primary"
      >
        + New Project
      </button>
    </div>

    <!-- Filters -->
    <div class="flex items-center gap-3">
      <input
        v-model="searchQuery"
        @input="loadProjects"
        type="text"
        placeholder="Search projects..."
        class="input w-64"
      />
      <select v-model="statusFilter" @change="loadProjects" class="input w-40">
        <option value="">All Status</option>
        <option value="active">Active</option>
        <option value="archived">Archived</option>
        <option value="completed">Completed</option>
        <option value="on_hold">On Hold</option>
      </select>
      <span class="text-sm text-surface-500">{{ totalProjects }} projects</span>
    </div>

    <!-- Projects Table -->
    <div class="card overflow-hidden">
      <table v-if="!isLoading && projects.length > 0" class="w-full">
        <thead class="bg-surface-50 dark:bg-surface-800">
          <tr>
            <th class="text-left px-6 py-3 text-xs font-medium text-surface-500 uppercase tracking-wider">Name</th>
            <th class="text-left px-6 py-3 text-xs font-medium text-surface-500 uppercase tracking-wider">Client</th>
            <th class="text-left px-6 py-3 text-xs font-medium text-surface-500 uppercase tracking-wider">Status</th>
            <th class="text-left px-6 py-3 text-xs font-medium text-surface-500 uppercase tracking-wider">Owner</th>
            <th class="text-left px-6 py-3 text-xs font-medium text-surface-500 uppercase tracking-wider">Artworks</th>
            <th class="text-left px-6 py-3 text-xs font-medium text-surface-500 uppercase tracking-wider">Created</th>
            <th class="text-right px-6 py-3 text-xs font-medium text-surface-500 uppercase tracking-wider">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-surface-200 dark:divide-surface-700">
          <tr
            v-for="project in projects"
            :key="project.id"
            class="hover:bg-surface-50 dark:hover:bg-surface-800/50 transition-colors"
          >
            <td class="px-6 py-4">
              <p class="text-sm font-medium text-surface-900 dark:text-white">{{ project.name }}</p>
              <p v-if="project.description" class="text-xs text-surface-500 mt-0.5 truncate max-w-xs">{{ project.description }}</p>
            </td>
            <td class="px-6 py-4 text-sm text-surface-600 dark:text-surface-400">{{ project.client || '—' }}</td>
            <td class="px-6 py-4">
              <span :class="getStatusBadge(project.status)">{{ project.status }}</span>
            </td>
            <td class="px-6 py-4 text-sm text-surface-600 dark:text-surface-400">{{ project.owner_name || '—' }}</td>
            <td class="px-6 py-4 text-sm text-surface-600 dark:text-surface-400">{{ project.artwork_count }}</td>
            <td class="px-6 py-4 text-sm text-surface-500">{{ new Date(project.created_at).toLocaleDateString() }}</td>
            <td class="px-6 py-4 text-right">
              <button
                v-if="authStore.hasPermission('Project.Delete')"
                @click="deleteProject(project.id)"
                class="text-red-600 hover:text-red-700 text-sm"
              >
                Delete
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Loading -->
      <div v-if="isLoading" class="p-8">
        <div class="animate-pulse space-y-4">
          <div v-for="i in 5" :key="i" class="flex items-center gap-4">
            <div class="h-4 bg-surface-200 dark:bg-surface-700 rounded flex-1"></div>
            <div class="h-4 bg-surface-200 dark:bg-surface-700 rounded w-20"></div>
            <div class="h-4 bg-surface-200 dark:bg-surface-700 rounded w-16"></div>
          </div>
        </div>
      </div>

      <!-- Empty state -->
      <div v-if="!isLoading && projects.length === 0" class="p-12 text-center">
        <p class="text-4xl mb-3">📁</p>
        <h3 class="text-lg font-medium text-surface-900 dark:text-white">No projects yet</h3>
        <p class="text-surface-500 mt-1">Create your first project to get started.</p>
        <button @click="showCreateModal = true" class="btn-primary mt-4">Create Project</button>
      </div>
    </div>

    <!-- Create Modal -->
    <div v-if="showCreateModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div class="card w-full max-w-md p-6 m-4">
        <h2 class="text-lg font-semibold text-surface-900 dark:text-white mb-4">Create New Project</h2>
        <form @submit.prevent="createProject" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Project Name</label>
            <input v-model="newProject.name" required class="input" placeholder="My Project" />
          </div>
          <div>
            <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Client</label>
            <input v-model="newProject.client" class="input" placeholder="Client name (optional)" />
          </div>
          <div>
            <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Description</label>
            <textarea v-model="newProject.description" class="input" rows="3" placeholder="Project description (optional)"></textarea>
          </div>
          <div class="flex justify-end gap-3 pt-2">
            <button type="button" @click="showCreateModal = false" class="btn-secondary">Cancel</button>
            <button type="submit" class="btn-primary">Create Project</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

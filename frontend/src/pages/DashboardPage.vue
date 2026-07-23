<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { dashboardService } from '@/services/dashboard.service'
import type { DashboardStats, Activity } from '@/types'

const stats = ref<DashboardStats | null>(null)
const activities = ref<Activity[]>([])
const isLoading = ref(true)

const statCards = [
  { key: 'total_projects', label: 'Total Projects', icon: '📁', color: 'blue' },
  { key: 'pending_analysis', label: 'Pending Analysis', icon: '🔍', color: 'yellow' },
  { key: 'pending_generation', label: 'Pending Generation', icon: '✨', color: 'purple' },
  { key: 'pending_qa', label: 'Pending QA', icon: '✅', color: 'orange' },
  { key: 'completed_projects', label: 'Completed Jobs', icon: '🎉', color: 'green' },
  { key: 'storage_usage_bytes', label: 'Storage Usage', icon: '💾', color: 'slate' },
  { key: 'ai_credits', label: 'AI Credits', icon: '⚡', color: 'indigo' },
  { key: 'total_users', label: 'Active Users', icon: '👥', color: 'teal' },
]

function formatValue(key: string, value: number): string {
  if (key === 'storage_usage_bytes') {
    if (value === 0) return '0 B'
    const units = ['B', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(value) / Math.log(1024))
    return `${(value / Math.pow(1024, i)).toFixed(1)} ${units[i]}`
  }
  return value.toLocaleString()
}

function formatActivityTime(dateStr: string): string {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  if (minutes < 1) return 'Just now'
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  return date.toLocaleDateString()
}

onMounted(async () => {
  try {
    const [statsData, activityData] = await Promise.all([
      dashboardService.getStats(),
      dashboardService.getRecentActivity(),
    ])
    stats.value = statsData
    activities.value = activityData
  } catch (err) {
    console.error('Failed to load dashboard data:', err)
    // Use placeholder data
    stats.value = {
      total_projects: 12,
      active_projects: 8,
      completed_projects: 4,
      pending_analysis: 3,
      pending_generation: 5,
      pending_qa: 2,
      storage_usage_bytes: 1073741824,
      ai_credits: 1000,
      total_users: 6,
    }
  } finally {
    isLoading.value = false
  }
})
</script>

<template>
  <div class="space-y-6">
    <!-- Page Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-surface-900 dark:text-white">Dashboard</h1>
        <p class="text-surface-500 mt-1">Welcome back. Here's what's happening today.</p>
      </div>
    </div>

    <!-- Stats Grid -->
    <div v-if="!isLoading && stats" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <div
        v-for="card in statCards"
        :key="card.key"
        class="card p-5 hover:shadow-md transition-shadow"
      >
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-surface-500 dark:text-surface-400">{{ card.label }}</p>
            <p class="text-2xl font-bold text-surface-900 dark:text-white mt-1">
              {{ formatValue(card.key, (stats as any)[card.key] || 0) }}
            </p>
          </div>
          <div class="text-2xl">{{ card.icon }}</div>
        </div>
      </div>
    </div>

    <!-- Loading skeleton -->
    <div v-if="isLoading" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <div v-for="i in 8" :key="i" class="card p-5">
        <div class="animate-pulse">
          <div class="h-4 bg-surface-200 dark:bg-surface-700 rounded w-24 mb-3"></div>
          <div class="h-8 bg-surface-200 dark:bg-surface-700 rounded w-16"></div>
        </div>
      </div>
    </div>

    <!-- Charts and Activity -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Placeholder Chart -->
      <div class="lg:col-span-2 card p-6">
        <h3 class="text-lg font-semibold text-surface-900 dark:text-white mb-4">Production Overview</h3>
        <div class="h-64 flex items-center justify-center border-2 border-dashed border-surface-200 dark:border-surface-700 rounded-lg">
          <div class="text-center text-surface-400">
            <p class="text-4xl mb-2">📊</p>
            <p class="text-sm">Charts will be populated with production data</p>
          </div>
        </div>
      </div>

      <!-- Recent Activity -->
      <div class="card p-6">
        <h3 class="text-lg font-semibold text-surface-900 dark:text-white mb-4">Recent Activity</h3>
        <div v-if="activities.length > 0" class="space-y-3">
          <div
            v-for="activity in activities.slice(0, 8)"
            :key="activity.id"
            class="flex items-start gap-3 py-2 border-b border-surface-100 dark:border-surface-800 last:border-0"
          >
            <div class="w-2 h-2 mt-2 bg-primary-500 rounded-full flex-shrink-0"></div>
            <div class="flex-1 min-w-0">
              <p class="text-sm text-surface-700 dark:text-surface-300 truncate">
                {{ activity.action.replace('.', ' ').replace(/\b\w/g, (c: string) => c.toUpperCase()) }}
              </p>
              <p class="text-xs text-surface-500">{{ formatActivityTime(activity.created_at) }}</p>
            </div>
          </div>
        </div>
        <div v-else class="text-center py-8 text-surface-400">
          <p class="text-2xl mb-2">📝</p>
          <p class="text-sm">No recent activity</p>
        </div>
      </div>
    </div>

    <!-- Quick Actions -->
    <div class="card p-6">
      <h3 class="text-lg font-semibold text-surface-900 dark:text-white mb-4">Quick Actions</h3>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
        <router-link to="/projects" class="flex flex-col items-center gap-2 p-4 rounded-lg border border-surface-200 dark:border-surface-700 hover:bg-surface-50 dark:hover:bg-surface-800 transition-colors">
          <span class="text-2xl">📁</span>
          <span class="text-sm font-medium text-surface-700 dark:text-surface-300">New Project</span>
        </router-link>
        <router-link to="/artwork-library" class="flex flex-col items-center gap-2 p-4 rounded-lg border border-surface-200 dark:border-surface-700 hover:bg-surface-50 dark:hover:bg-surface-800 transition-colors">
          <span class="text-2xl">🖼️</span>
          <span class="text-sm font-medium text-surface-700 dark:text-surface-300">Upload Artwork</span>
        </router-link>
        <router-link to="/generation" class="flex flex-col items-center gap-2 p-4 rounded-lg border border-surface-200 dark:border-surface-700 hover:bg-surface-50 dark:hover:bg-surface-800 transition-colors">
          <span class="text-2xl">✨</span>
          <span class="text-sm font-medium text-surface-700 dark:text-surface-300">Generate</span>
        </router-link>
        <router-link to="/export" class="flex flex-col items-center gap-2 p-4 rounded-lg border border-surface-200 dark:border-surface-700 hover:bg-surface-50 dark:hover:bg-surface-800 transition-colors">
          <span class="text-2xl">📥</span>
          <span class="text-sm font-medium text-surface-700 dark:text-surface-300">Export</span>
        </router-link>
      </div>
    </div>
  </div>
</template>

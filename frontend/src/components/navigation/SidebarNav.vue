<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useUiStore } from '@/stores/ui'

const route = useRoute()
const uiStore = useUiStore()

const navigation = [
  { name: 'Dashboard', path: '/dashboard', icon: '🏠' },
  { name: 'Projects', path: '/projects', icon: '📁' },
  { name: 'Artwork Vault', path: '/artwork-library', icon: '🖼️' },
  { name: 'Artwork Analysis', path: '/analysis', icon: '🔍' },
  { name: 'Reconstruction', path: '/reconstruction', icon: '🧩' },
  { name: 'Production Planning', path: '/production-planning', icon: '📋' },
  { name: 'AI Production', path: '/generation', icon: '✨' },
  { name: 'Quality Assurance', path: '/quality', icon: '✅' },
  { name: 'Export Center', path: '/export', icon: '📥' },
  { name: 'Administration', path: '/administration', icon: '👥' },
  { name: 'Settings', path: '/settings', icon: '⚙️' },
]

const isActive = (path: string) => route.path === path
</script>

<template>
  <aside
    :class="[
      'flex flex-col border-r border-surface-200 dark:border-surface-800 bg-white dark:bg-surface-900 transition-all duration-300',
      uiStore.sidebarCollapsed ? 'w-16' : 'w-64'
    ]"
  >
    <!-- Logo -->
    <div class="flex h-16 items-center justify-center border-b border-surface-200 dark:border-surface-800 px-4">
      <div v-if="!uiStore.sidebarCollapsed" class="flex items-center gap-2">
        <div class="h-8 w-8 rounded-lg bg-primary-600 flex items-center justify-center">
          <span class="text-white font-bold text-sm">AI</span>
        </div>
        <span class="font-semibold text-surface-900 dark:text-white">Work Studio</span>
      </div>
      <div v-else class="h-8 w-8 rounded-lg bg-primary-600 flex items-center justify-center">
        <span class="text-white font-bold text-xs">AI</span>
      </div>
    </div>

    <!-- Navigation -->
    <nav class="flex-1 overflow-y-auto py-4 px-2">
      <ul class="space-y-1">
        <li v-for="item in navigation" :key="item.path">
          <router-link
            :to="item.path"
            :class="[
              'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
              isActive(item.path)
                ? 'bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-400'
                : 'text-surface-600 dark:text-surface-400 hover:bg-surface-100 dark:hover:bg-surface-800 hover:text-surface-900 dark:hover:text-white'
            ]"
            :title="uiStore.sidebarCollapsed ? item.name : undefined"
          >
            <span class="w-5 h-5 flex items-center justify-center text-lg">{{ item.icon }}</span>
            <span v-if="!uiStore.sidebarCollapsed">{{ item.name }}</span>
          </router-link>
        </li>
      </ul>
    </nav>

    <!-- Collapse toggle -->
    <div class="border-t border-surface-200 dark:border-surface-800 p-2">
      <button
        @click="uiStore.toggleSidebar"
        class="w-full flex items-center justify-center p-2 rounded-lg text-surface-500 hover:bg-surface-100 dark:hover:bg-surface-800 transition-colors"
      >
        <span v-if="uiStore.sidebarCollapsed">→</span>
        <span v-else>←</span>
      </button>
    </div>
  </aside>
</template>

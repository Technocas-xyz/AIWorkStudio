<script setup lang="ts">
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'

const route = useRoute()
const authStore = useAuthStore()
const themeStore = useThemeStore()

const searchQuery = ref('')
const showUserMenu = ref(false)
const showNotifications = ref(false)

const breadcrumbs = computed(() => {
  const parts = route.path.split('/').filter(Boolean)
  return parts.map((part, index) => ({
    name: part.replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()),
    path: '/' + parts.slice(0, index + 1).join('/'),
  }))
})

import { computed } from 'vue'
</script>

<template>
  <header class="flex h-16 items-center justify-between border-b border-surface-200 dark:border-surface-800 bg-white dark:bg-surface-900 px-6">
    <!-- Breadcrumbs -->
    <div class="flex items-center gap-2">
      <nav class="flex items-center gap-1 text-sm">
        <router-link to="/dashboard" class="text-surface-500 hover:text-surface-700 dark:hover:text-surface-300">
          Home
        </router-link>
        <template v-for="(crumb, index) in breadcrumbs" :key="crumb.path">
          <span class="text-surface-400">/</span>
          <router-link
            :to="crumb.path"
            :class="[
              index === breadcrumbs.length - 1
                ? 'text-surface-900 dark:text-white font-medium'
                : 'text-surface-500 hover:text-surface-700 dark:hover:text-surface-300'
            ]"
          >
            {{ crumb.name }}
          </router-link>
        </template>
      </nav>
    </div>

    <!-- Right side actions -->
    <div class="flex items-center gap-3">
      <!-- Quick Search -->
      <div class="relative">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search..."
          class="input w-48 pl-8"
        />
        <span class="absolute left-2.5 top-2.5 text-surface-400 text-sm">🔍</span>
      </div>

      <!-- Theme Toggle -->
      <button
        @click="themeStore.toggle"
        class="btn-ghost p-2"
        title="Toggle theme"
      >
        {{ themeStore.isDark ? '☀️' : '🌙' }}
      </button>

      <!-- Notifications -->
      <button
        @click="showNotifications = !showNotifications"
        class="btn-ghost p-2 relative"
      >
        🔔
        <span class="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
      </button>

      <!-- User Menu -->
      <div class="relative">
        <button
          @click="showUserMenu = !showUserMenu"
          class="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-surface-100 dark:hover:bg-surface-800 transition-colors"
        >
          <div class="w-8 h-8 rounded-full bg-primary-600 flex items-center justify-center">
            <span class="text-white text-xs font-medium">
              {{ authStore.user?.first_name?.[0] }}{{ authStore.user?.last_name?.[0] }}
            </span>
          </div>
          <span class="text-sm font-medium text-surface-700 dark:text-surface-300 hidden md:block">
            {{ authStore.user?.full_name }}
          </span>
        </button>

        <!-- Dropdown -->
        <div
          v-if="showUserMenu"
          class="absolute right-0 top-12 w-48 card p-1 shadow-lg z-50"
          @mouseleave="showUserMenu = false"
        >
          <div class="px-3 py-2 border-b border-surface-200 dark:border-surface-700">
            <p class="text-sm font-medium text-surface-900 dark:text-white">{{ authStore.user?.full_name }}</p>
            <p class="text-xs text-surface-500">{{ authStore.user?.role }}</p>
          </div>
          <button
            @click="authStore.logout()"
            class="w-full text-left px-3 py-2 text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg"
          >
            Sign out
          </button>
        </div>
      </div>
    </div>
  </header>
</template>

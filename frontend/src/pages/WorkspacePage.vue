<script setup lang="ts">
defineProps<{
  workspace: string
}>()
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-surface-900 dark:text-white">{{ workspace }}</h1>
        <p class="text-surface-500 mt-1">This workspace will be available in a future module.</p>
      </div>
    </div>

    <!-- Empty state -->
    <div class="card p-12 text-center">
      <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-surface-100 dark:bg-surface-800 mb-4">
        <span class="text-3xl">🚧</span>
      </div>
      <h3 class="text-lg font-medium text-surface-900 dark:text-white">Coming Soon</h3>
      <p class="text-surface-500 mt-2 max-w-md mx-auto">
        The {{ workspace }} workspace is under development.
        It will be activated in a future module update.
      </p>
    </div>

    <!-- Placeholder panels to demonstrate layout -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div class="lg:col-span-2 card p-6">
        <h3 class="text-sm font-medium text-surface-500 uppercase tracking-wider mb-4">Main Content Area</h3>
        <div class="h-48 border-2 border-dashed border-surface-200 dark:border-surface-700 rounded-lg flex items-center justify-center">
          <span class="text-surface-400 text-sm">Content will appear here</span>
        </div>
      </div>
      <div class="card p-6">
        <h3 class="text-sm font-medium text-surface-500 uppercase tracking-wider mb-4">Inspector Panel</h3>
        <div class="h-48 border-2 border-dashed border-surface-200 dark:border-surface-700 rounded-lg flex items-center justify-center">
          <span class="text-surface-400 text-sm">Properties</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-surface-50 dark:bg-surface-950">
    <div class="text-center">
      <p class="text-6xl mb-4">🔍</p>
      <h1 class="text-4xl font-bold text-surface-900 dark:text-white">404</h1>
      <p class="text-surface-500 mt-2">Page not found</p>
      <router-link to="/dashboard" class="btn-primary mt-6 inline-flex">
        Back to Dashboard
      </router-link>
    </div>
  </div>
</template>

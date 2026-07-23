<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'
import { ref, onMounted } from 'vue'

const authStore = useAuthStore()
const currentTime = ref('')

function updateTime() {
  currentTime.value = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

onMounted(() => {
  updateTime()
  setInterval(updateTime, 60000)
})
</script>

<template>
  <footer class="flex h-8 items-center justify-between border-t border-surface-200 dark:border-surface-800 bg-white dark:bg-surface-900 px-4 text-xs text-surface-500">
    <div class="flex items-center gap-4">
      <span class="flex items-center gap-1">
        <span class="w-2 h-2 bg-green-500 rounded-full"></span>
        Connected
      </span>
      <span>v1.0.0</span>
    </div>
    <div class="flex items-center gap-4">
      <span>{{ authStore.user?.role }}</span>
      <span>{{ currentTime }}</span>
    </div>
  </footer>
</template>

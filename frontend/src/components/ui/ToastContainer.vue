<script setup lang="ts">
import { useUiStore } from '@/stores/ui'

const uiStore = useUiStore()

function getToastClasses(type: string) {
  switch (type) {
    case 'success': return 'border-green-500 bg-green-50 dark:bg-green-900/20'
    case 'error': return 'border-red-500 bg-red-50 dark:bg-red-900/20'
    case 'warning': return 'border-yellow-500 bg-yellow-50 dark:bg-yellow-900/20'
    default: return 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
  }
}
</script>

<template>
  <div class="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm">
    <transition-group name="toast">
      <div
        v-for="toast in uiStore.toasts"
        :key="toast.id"
        :class="['card border-l-4 p-4 shadow-lg', getToastClasses(toast.type)]"
      >
        <div class="flex items-start justify-between gap-2">
          <div>
            <p class="text-sm font-medium text-surface-900 dark:text-white">{{ toast.title }}</p>
            <p v-if="toast.message" class="text-xs text-surface-600 dark:text-surface-400 mt-1">{{ toast.message }}</p>
          </div>
          <button
            @click="uiStore.removeToast(toast.id)"
            class="text-surface-400 hover:text-surface-600 text-lg leading-none"
          >
            ×
          </button>
        </div>
      </div>
    </transition-group>
  </div>
</template>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}
.toast-enter-from {
  opacity: 0;
  transform: translateX(100%);
}
.toast-leave-to {
  opacity: 0;
  transform: translateX(100%);
}
</style>

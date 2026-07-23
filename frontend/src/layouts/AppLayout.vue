<script setup lang="ts">
import { RouterView } from 'vue-router'
import SidebarNav from '@/components/navigation/SidebarNav.vue'
import TopToolbar from '@/components/navigation/TopToolbar.vue'
import StatusBar from '@/components/navigation/StatusBar.vue'
import ToastContainer from '@/components/ui/ToastContainer.vue'
import { useUiStore } from '@/stores/ui'
import { useThemeStore } from '@/stores/theme'
import { onMounted } from 'vue'

const uiStore = useUiStore()
const themeStore = useThemeStore()

onMounted(() => {
  themeStore.initialize()
})
</script>

<template>
  <div class="flex h-screen overflow-hidden bg-surface-50 dark:bg-surface-950">
    <!-- Sidebar -->
    <SidebarNav />

    <!-- Main Content Area -->
    <div class="flex flex-1 flex-col overflow-hidden">
      <!-- Top Toolbar -->
      <TopToolbar />

      <!-- Page Content -->
      <main class="flex-1 overflow-auto p-6">
        <RouterView />
      </main>

      <!-- Status Bar -->
      <StatusBar />
    </div>

    <!-- Toast notifications -->
    <ToastContainer />
  </div>
</template>

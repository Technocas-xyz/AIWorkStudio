<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { artworkService, type ArtworkItem } from '@/services/artwork.service'

const props = defineProps<{
  artwork: ArtworkItem
}>()

const emit = defineEmits<{
  close: []
  delete: [artwork: ArtworkItem]
  updated: []
}>()

const versions = ref<any[]>([])
const activeTab = ref<'general' | 'technical' | 'versions' | 'history'>('general')

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`
}

async function loadVersions() {
  try {
    versions.value = await artworkService.getVersions(props.artwork.id)
  } catch { versions.value = [] }
}

watch(() => props.artwork.id, loadVersions, { immediate: true })
</script>

<template>
  <aside class="w-80 border-l border-surface-200 dark:border-surface-800 bg-white dark:bg-surface-900 overflow-y-auto flex-shrink-0">
    <!-- Header -->
    <div class="flex items-center justify-between p-4 border-b border-surface-200 dark:border-surface-800">
      <h3 class="font-semibold text-surface-900 dark:text-white text-sm">Inspector</h3>
      <button @click="emit('close')" class="text-surface-400 hover:text-surface-600">×</button>
    </div>

    <!-- Preview -->
    <div class="p-4">
      <div class="aspect-video bg-surface-100 dark:bg-surface-800 rounded-lg overflow-hidden flex items-center justify-center">
        <img
          :src="artworkService.getPreviewUrl(artwork, 'medium')"
          :alt="artwork.original_filename"
          class="max-w-full max-h-full object-contain"
          @error="($event.target as HTMLImageElement).style.display = 'none'"
        />
      </div>
      <p class="text-sm font-medium text-surface-900 dark:text-white mt-3 truncate">{{ artwork.original_filename }}</p>
      <p class="text-xs text-surface-500">{{ artwork.artwork_id }}</p>
    </div>

    <!-- Tabs -->
    <div class="flex border-b border-surface-200 dark:border-surface-800 px-4">
      <button
        v-for="tab in ['general', 'technical', 'versions'] as const"
        :key="tab"
        @click="activeTab = tab"
        :class="[
          'px-3 py-2 text-xs font-medium border-b-2 -mb-px capitalize',
          activeTab === tab ? 'border-primary-500 text-primary-600' : 'border-transparent text-surface-500 hover:text-surface-700'
        ]"
      >{{ tab }}</button>
    </div>

    <!-- Tab Content -->
    <div class="p-4 space-y-3">
      <!-- General -->
      <template v-if="activeTab === 'general'">
        <div class="space-y-2">
          <div class="flex justify-between text-xs">
            <span class="text-surface-500">Filename</span>
            <span class="text-surface-800 dark:text-surface-200 truncate ml-2 max-w-[150px]">{{ artwork.original_filename }}</span>
          </div>
          <div class="flex justify-between text-xs">
            <span class="text-surface-500">Dimensions</span>
            <span class="text-surface-800 dark:text-surface-200">{{ artwork.width && artwork.height ? `${artwork.width} × ${artwork.height} px` : '—' }}</span>
          </div>
          <div class="flex justify-between text-xs">
            <span class="text-surface-500">Resolution</span>
            <span class="text-surface-800 dark:text-surface-200">{{ artwork.resolution_dpi ? `${artwork.resolution_dpi} DPI` : '—' }}</span>
          </div>
          <div class="flex justify-between text-xs">
            <span class="text-surface-500">File Size</span>
            <span class="text-surface-800 dark:text-surface-200">{{ formatFileSize(artwork.file_size) }}</span>
          </div>
          <div class="flex justify-between text-xs">
            <span class="text-surface-500">Format</span>
            <span class="text-surface-800 dark:text-surface-200 uppercase">{{ artwork.extension }}</span>
          </div>
          <div class="flex justify-between text-xs">
            <span class="text-surface-500">Status</span>
            <span class="badge-success text-[10px]">{{ artwork.status }}</span>
          </div>
          <div class="flex justify-between text-xs">
            <span class="text-surface-500">Uploaded</span>
            <span class="text-surface-800 dark:text-surface-200">{{ new Date(artwork.created_at).toLocaleDateString() }}</span>
          </div>
          <div class="flex justify-between text-xs">
            <span class="text-surface-500">Version</span>
            <span class="text-surface-800 dark:text-surface-200">v{{ artwork.current_version }}</span>
          </div>
        </div>
      </template>

      <!-- Technical -->
      <template v-if="activeTab === 'technical'">
        <div class="space-y-2">
          <div class="flex justify-between text-xs">
            <span class="text-surface-500">Color Space</span>
            <span class="text-surface-800 dark:text-surface-200">{{ artwork.color_space || '—' }}</span>
          </div>
          <div class="flex justify-between text-xs">
            <span class="text-surface-500">Bit Depth</span>
            <span class="text-surface-800 dark:text-surface-200">{{ artwork.bit_depth ? `${artwork.bit_depth}-bit` : '—' }}</span>
          </div>
          <div class="flex justify-between text-xs">
            <span class="text-surface-500">Alpha Channel</span>
            <span class="text-surface-800 dark:text-surface-200">{{ artwork.has_alpha_channel ? 'Yes' : 'No' }}</span>
          </div>
          <div class="flex justify-between text-xs">
            <span class="text-surface-500">Transparency</span>
            <span class="text-surface-800 dark:text-surface-200">{{ artwork.has_transparency ? 'Yes' : 'No' }}</span>
          </div>
          <div class="flex justify-between text-xs">
            <span class="text-surface-500">Orientation</span>
            <span class="text-surface-800 dark:text-surface-200 capitalize">{{ artwork.orientation || '—' }}</span>
          </div>
          <div class="flex justify-between text-xs">
            <span class="text-surface-500">MIME Type</span>
            <span class="text-surface-800 dark:text-surface-200">{{ artwork.mime_type }}</span>
          </div>
          <div class="flex justify-between text-xs">
            <span class="text-surface-500">Checksum</span>
            <span class="text-surface-800 dark:text-surface-200 font-mono text-[10px] truncate max-w-[140px]" :title="artwork.checksum">{{ artwork.checksum.slice(0, 16) }}...</span>
          </div>
          <div class="flex justify-between text-xs">
            <span class="text-surface-500">Storage</span>
            <span class="text-surface-800 dark:text-surface-200">{{ artwork.storage_bucket }}</span>
          </div>
        </div>
      </template>

      <!-- Versions -->
      <template v-if="activeTab === 'versions'">
        <div v-if="versions.length > 0" class="space-y-2">
          <div v-for="v in versions" :key="v.id" class="p-2 rounded-lg bg-surface-50 dark:bg-surface-800">
            <div class="flex items-center justify-between">
              <span class="text-xs font-medium text-surface-800 dark:text-surface-200">v{{ v.version_number }}</span>
              <span class="text-[10px] text-surface-500 capitalize">{{ v.version_type }}</span>
            </div>
            <p class="text-[10px] text-surface-500 mt-0.5">{{ v.created_at ? new Date(v.created_at).toLocaleString() : '' }}</p>
          </div>
        </div>
        <p v-else class="text-xs text-surface-500 text-center py-4">No version history</p>
      </template>
    </div>

    <!-- Actions -->
    <div class="p-4 border-t border-surface-200 dark:border-surface-800 space-y-2">
      <button @click="emit('delete', artwork)" class="btn-danger w-full text-xs">Delete Artwork</button>
    </div>
  </aside>
</template>

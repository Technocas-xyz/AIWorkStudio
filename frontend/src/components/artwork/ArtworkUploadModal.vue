<script setup lang="ts">
import { ref } from 'vue'
import { artworkService } from '@/services/artwork.service'
import { useUiStore } from '@/stores/ui'

const emit = defineEmits<{
  close: []
  complete: []
}>()

const uiStore = useUiStore()
const files = ref<File[]>([])
const isUploading = ref(false)
const uploadProgress = ref<Array<{ name: string; status: 'pending' | 'uploading' | 'done' | 'error'; error?: string }>>([])
const isDragOver = ref(false)

const SUPPORTED_EXTENSIONS = ['png', 'jpg', 'jpeg', 'webp', 'tiff', 'tif', 'bmp', 'psd', 'psb', 'svg', 'ai', 'eps', 'pdf']

function handleDrop(e: DragEvent) {
  isDragOver.value = false
  const dropped = e.dataTransfer?.files
  if (dropped) addFiles(Array.from(dropped))
}

function handleFileSelect(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files) addFiles(Array.from(input.files))
  input.value = ''
}

function addFiles(newFiles: File[]) {
  const valid = newFiles.filter(f => {
    const ext = f.name.split('.').pop()?.toLowerCase() || ''
    return SUPPORTED_EXTENSIONS.includes(ext)
  })
  files.value.push(...valid)
  if (valid.length < newFiles.length) {
    uiStore.addToast({
      type: 'warning',
      title: `${newFiles.length - valid.length} unsupported file(s) skipped`,
    })
  }
}

function removeFile(index: number) {
  files.value.splice(index, 1)
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1048576).toFixed(1) + ' MB'
}

async function startUpload() {
  if (files.value.length === 0) return
  isUploading.value = true
  uploadProgress.value = files.value.map(f => ({ name: f.name, status: 'pending' }))

  // Upload in batches of 3
  const batchSize = 3
  for (let i = 0; i < files.value.length; i += batchSize) {
    const batch = files.value.slice(i, i + batchSize)
    const promises = batch.map(async (file, batchIdx) => {
      const idx = i + batchIdx
      uploadProgress.value[idx].status = 'uploading'
      try {
        await artworkService.upload(file)
        uploadProgress.value[idx].status = 'done'
      } catch (err: any) {
        uploadProgress.value[idx].status = 'error'
        uploadProgress.value[idx].error = err.response?.data?.detail || 'Upload failed'
      }
    })
    await Promise.all(promises)
  }

  isUploading.value = false
  const successCount = uploadProgress.value.filter(p => p.status === 'done').length
  if (successCount > 0) {
    setTimeout(() => emit('complete'), 500)
  }
}
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
    <div class="card w-full max-w-2xl max-h-[80vh] flex flex-col m-4">
      <!-- Header -->
      <div class="flex items-center justify-between p-5 border-b border-surface-200 dark:border-surface-800">
        <h2 class="text-lg font-semibold text-surface-900 dark:text-white">Upload Artwork</h2>
        <button @click="emit('close')" class="text-surface-400 hover:text-surface-600 text-xl">×</button>
      </div>

      <!-- Content -->
      <div class="flex-1 overflow-auto p-5">
        <!-- Drop Zone -->
        <div
          v-if="!isUploading"
          @drop.prevent="handleDrop"
          @dragover.prevent="isDragOver = true"
          @dragleave="isDragOver = false"
          :class="[
            'border-2 border-dashed rounded-xl p-8 text-center transition-colors',
            isDragOver ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20' : 'border-surface-300 dark:border-surface-600'
          ]"
        >
          <p class="text-4xl mb-3">📁</p>
          <p class="font-medium text-surface-700 dark:text-surface-300">Drop files here or click to browse</p>
          <p class="text-sm text-surface-500 mt-1">PNG, JPG, WebP, SVG, PSD, PDF, TIFF, AI, EPS</p>
          <input
            type="file"
            multiple
            accept=".png,.jpg,.jpeg,.webp,.tiff,.tif,.bmp,.psd,.psb,.svg,.ai,.eps,.pdf"
            @change="handleFileSelect"
            class="absolute inset-0 opacity-0 cursor-pointer"
            style="position: relative; margin-top: 12px;"
          />
        </div>

        <!-- File List -->
        <div v-if="files.length > 0 && !isUploading" class="mt-4 space-y-2 max-h-60 overflow-auto">
          <div v-for="(file, idx) in files" :key="idx" class="flex items-center justify-between p-2 rounded-lg bg-surface-50 dark:bg-surface-800">
            <div class="flex items-center gap-2 min-w-0">
              <span class="text-lg">🖼️</span>
              <div class="min-w-0">
                <p class="text-sm text-surface-800 dark:text-surface-200 truncate">{{ file.name }}</p>
                <p class="text-xs text-surface-500">{{ formatSize(file.size) }}</p>
              </div>
            </div>
            <button @click="removeFile(idx)" class="text-surface-400 hover:text-red-500 ml-2">×</button>
          </div>
        </div>

        <!-- Upload Progress -->
        <div v-if="isUploading" class="space-y-2">
          <div v-for="(item, idx) in uploadProgress" :key="idx" class="flex items-center gap-3 p-2 rounded-lg bg-surface-50 dark:bg-surface-800">
            <span>
              {{ item.status === 'done' ? '✅' : item.status === 'error' ? '❌' : item.status === 'uploading' ? '⏳' : '⏸️' }}
            </span>
            <div class="flex-1 min-w-0">
              <p class="text-sm truncate" :class="item.status === 'error' ? 'text-red-600' : 'text-surface-800 dark:text-surface-200'">
                {{ item.name }}
              </p>
              <p v-if="item.error" class="text-xs text-red-500">{{ item.error }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="flex items-center justify-between p-5 border-t border-surface-200 dark:border-surface-800">
        <p class="text-sm text-surface-500">{{ files.length }} file(s) selected</p>
        <div class="flex gap-2">
          <button @click="emit('close')" class="btn-secondary" :disabled="isUploading">Cancel</button>
          <button @click="startUpload" class="btn-primary" :disabled="files.length === 0 || isUploading">
            {{ isUploading ? 'Uploading...' : `Upload ${files.length} File${files.length !== 1 ? 's' : ''}` }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

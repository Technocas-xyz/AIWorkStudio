<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { artworkService, type ArtworkItem } from '@/services/artwork.service'
import { useUiStore } from '@/stores/ui'
import { useAuthStore } from '@/stores/auth'
import ArtworkUploadModal from '@/components/artwork/ArtworkUploadModal.vue'
import ArtworkInspector from '@/components/artwork/ArtworkInspector.vue'

const uiStore = useUiStore()
const authStore = useAuthStore()

const artworks = ref<ArtworkItem[]>([])
const isLoading = ref(true)
const totalArtworks = ref(0)
const currentPage = ref(1)
const totalPages = ref(0)
const pageSize = ref(40)
const searchQuery = ref('')
const extensionFilter = ref('')
const viewMode = ref<'grid' | 'list'>('grid')
const showUploadModal = ref(false)
const selectedArtwork = ref<ArtworkItem | null>(null)
const sortBy = ref('created_at')
const sortOrder = ref('desc')

async function loadArtworks() {
  isLoading.value = true
  try {
    const result = await artworkService.list({
      page: currentPage.value,
      page_size: pageSize.value,
      search: searchQuery.value || undefined,
      extension: extensionFilter.value || undefined,
      sort_by: sortBy.value,
      sort_order: sortOrder.value,
    })
    artworks.value = result.items
    totalArtworks.value = result.total
    totalPages.value = result.total_pages
  } catch (err) {
    console.error('Failed to load artworks:', err)
    artworks.value = []
  } finally {
    isLoading.value = false
  }
}

function selectArtwork(artwork: ArtworkItem) {
  selectedArtwork.value = artwork
}

function closeInspector() {
  selectedArtwork.value = null
}

async function handleUploadComplete() {
  showUploadModal.value = false
  await loadArtworks()
  uiStore.addToast({ type: 'success', title: 'Upload complete' })
}

async function toggleFavorite(artwork: ArtworkItem) {
  try {
    const isFav = await artworkService.toggleFavorite(artwork.id)
    artwork.is_favorite = isFav
  } catch {
    uiStore.addToast({ type: 'error', title: 'Failed to update favorite' })
  }
}

async function deleteArtwork(artwork: ArtworkItem) {
  if (!confirm(`Delete "${artwork.original_filename}"?`)) return
  try {
    await artworkService.delete(artwork.id)
    uiStore.addToast({ type: 'success', title: 'Artwork deleted' })
    if (selectedArtwork.value?.id === artwork.id) selectedArtwork.value = null
    await loadArtworks()
  } catch {
    uiStore.addToast({ type: 'error', title: 'Failed to delete' })
  }
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`
}

function getPreviewUrl(artwork: ArtworkItem): string {
  return artworkService.getPreviewUrl(artwork, 'thumbnail')
}

let searchTimeout: number
function onSearchInput() {
  clearTimeout(searchTimeout)
  searchTimeout = window.setTimeout(() => {
    currentPage.value = 1
    loadArtworks()
  }, 300)
}

watch(extensionFilter, () => { currentPage.value = 1; loadArtworks() })

onMounted(loadArtworks)
</script>

<template>
  <div class="flex h-full gap-0 -m-6">
    <!-- Main Content -->
    <div class="flex-1 flex flex-col overflow-hidden p-6">
      <!-- Header -->
      <div class="flex items-center justify-between mb-6">
        <div>
          <h1 class="text-2xl font-bold text-surface-900 dark:text-white">Artwork Library</h1>
          <p class="text-surface-500 mt-0.5">{{ totalArtworks }} assets</p>
        </div>
        <button @click="showUploadModal = true" class="btn-primary">
          ⬆ Upload Artwork
        </button>
      </div>

      <!-- Toolbar -->
      <div class="flex items-center gap-3 mb-4">
        <div class="relative flex-1 max-w-md">
          <input
            v-model="searchQuery"
            @input="onSearchInput"
            type="text"
            placeholder="Search artworks..."
            class="input pl-8"
          />
          <span class="absolute left-2.5 top-2.5 text-surface-400 text-sm">🔍</span>
        </div>

        <select v-model="extensionFilter" class="input w-32">
          <option value="">All Types</option>
          <option value="png">PNG</option>
          <option value="jpg">JPG</option>
          <option value="jpeg">JPEG</option>
          <option value="webp">WebP</option>
          <option value="svg">SVG</option>
          <option value="psd">PSD</option>
          <option value="pdf">PDF</option>
          <option value="tiff">TIFF</option>
        </select>

        <select v-model="sortBy" @change="loadArtworks" class="input w-36">
          <option value="created_at">Date Added</option>
          <option value="original_filename">Name</option>
          <option value="file_size">Size</option>
        </select>

        <!-- View Toggle -->
        <div class="flex border border-surface-200 dark:border-surface-700 rounded-lg overflow-hidden">
          <button
            @click="viewMode = 'grid'"
            :class="['px-3 py-1.5 text-sm', viewMode === 'grid' ? 'bg-primary-600 text-white' : 'bg-white dark:bg-surface-800 text-surface-600']"
          >⊞</button>
          <button
            @click="viewMode = 'list'"
            :class="['px-3 py-1.5 text-sm', viewMode === 'list' ? 'bg-primary-600 text-white' : 'bg-white dark:bg-surface-800 text-surface-600']"
          >☰</button>
        </div>
      </div>

      <!-- Grid View -->
      <div v-if="!isLoading && artworks.length > 0 && viewMode === 'grid'" class="flex-1 overflow-auto">
        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3">
          <div
            v-for="artwork in artworks"
            :key="artwork.id"
            @click="selectArtwork(artwork)"
            :class="[
              'group card p-2 cursor-pointer hover:shadow-md transition-all',
              selectedArtwork?.id === artwork.id ? 'ring-2 ring-primary-500' : ''
            ]"
          >
            <!-- Thumbnail -->
            <div class="aspect-square bg-surface-100 dark:bg-surface-800 rounded-lg overflow-hidden mb-2 relative">
              <img
                :src="getPreviewUrl(artwork)"
                :alt="artwork.original_filename"
                class="w-full h-full object-cover"
                @error="($event.target as HTMLImageElement).style.display = 'none'"
              />
              <div class="absolute inset-0 flex items-center justify-center text-surface-400" v-if="!artwork.width">
                <span class="text-3xl">{{ artwork.extension === 'svg' ? '📐' : artwork.extension === 'pdf' ? '📄' : '🖼️' }}</span>
              </div>
              <!-- Favorite -->
              <button
                @click.stop="toggleFavorite(artwork)"
                class="absolute top-1 right-1 opacity-0 group-hover:opacity-100 transition-opacity text-lg"
              >
                {{ artwork.is_favorite ? '⭐' : '☆' }}
              </button>
            </div>
            <!-- Info -->
            <p class="text-xs font-medium text-surface-800 dark:text-surface-200 truncate">{{ artwork.original_filename }}</p>
            <div class="flex items-center justify-between mt-0.5">
              <span class="text-[10px] text-surface-500 uppercase">{{ artwork.extension }}</span>
              <span class="text-[10px] text-surface-500">{{ artwork.width && artwork.height ? `${artwork.width}×${artwork.height}` : formatFileSize(artwork.file_size) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- List View -->
      <div v-if="!isLoading && artworks.length > 0 && viewMode === 'list'" class="flex-1 overflow-auto">
        <table class="w-full">
          <thead class="bg-surface-50 dark:bg-surface-800 sticky top-0">
            <tr>
              <th class="text-left px-4 py-2 text-xs font-medium text-surface-500">Name</th>
              <th class="text-left px-4 py-2 text-xs font-medium text-surface-500">Type</th>
              <th class="text-left px-4 py-2 text-xs font-medium text-surface-500">Dimensions</th>
              <th class="text-left px-4 py-2 text-xs font-medium text-surface-500">Size</th>
              <th class="text-left px-4 py-2 text-xs font-medium text-surface-500">Version</th>
              <th class="text-left px-4 py-2 text-xs font-medium text-surface-500">Uploaded</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-surface-100 dark:divide-surface-800">
            <tr
              v-for="artwork in artworks"
              :key="artwork.id"
              @click="selectArtwork(artwork)"
              :class="['cursor-pointer hover:bg-surface-50 dark:hover:bg-surface-800/50', selectedArtwork?.id === artwork.id ? 'bg-primary-50 dark:bg-primary-900/20' : '']"
            >
              <td class="px-4 py-2 text-sm text-surface-800 dark:text-surface-200">{{ artwork.original_filename }}</td>
              <td class="px-4 py-2"><span class="badge-info">{{ artwork.extension.toUpperCase() }}</span></td>
              <td class="px-4 py-2 text-sm text-surface-500">{{ artwork.width && artwork.height ? `${artwork.width}×${artwork.height}` : '—' }}</td>
              <td class="px-4 py-2 text-sm text-surface-500">{{ formatFileSize(artwork.file_size) }}</td>
              <td class="px-4 py-2 text-sm text-surface-500">v{{ artwork.current_version }}</td>
              <td class="px-4 py-2 text-sm text-surface-500">{{ new Date(artwork.created_at).toLocaleDateString() }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Loading -->
      <div v-if="isLoading" class="flex-1 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3">
        <div v-for="i in 12" :key="i" class="card p-2 animate-pulse">
          <div class="aspect-square bg-surface-200 dark:bg-surface-700 rounded-lg mb-2"></div>
          <div class="h-3 bg-surface-200 dark:bg-surface-700 rounded w-3/4 mb-1"></div>
          <div class="h-2 bg-surface-200 dark:bg-surface-700 rounded w-1/2"></div>
        </div>
      </div>

      <!-- Empty state -->
      <div v-if="!isLoading && artworks.length === 0" class="flex-1 flex items-center justify-center">
        <div class="text-center">
          <p class="text-5xl mb-3">🖼️</p>
          <h3 class="text-lg font-medium text-surface-900 dark:text-white">No artworks yet</h3>
          <p class="text-surface-500 mt-1">Upload your first artwork to get started.</p>
          <button @click="showUploadModal = true" class="btn-primary mt-4">Upload Artwork</button>
        </div>
      </div>

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="flex items-center justify-center gap-2 pt-4 border-t border-surface-200 dark:border-surface-800 mt-4">
        <button @click="currentPage--; loadArtworks()" :disabled="currentPage <= 1" class="btn-secondary text-xs">← Prev</button>
        <span class="text-sm text-surface-500">Page {{ currentPage }} of {{ totalPages }}</span>
        <button @click="currentPage++; loadArtworks()" :disabled="currentPage >= totalPages" class="btn-secondary text-xs">Next →</button>
      </div>
    </div>

    <!-- Inspector Panel -->
    <ArtworkInspector
      v-if="selectedArtwork"
      :artwork="selectedArtwork"
      @close="closeInspector"
      @delete="deleteArtwork"
      @updated="loadArtworks"
    />

    <!-- Upload Modal -->
    <ArtworkUploadModal
      v-if="showUploadModal"
      @close="showUploadModal = false"
      @complete="handleUploadComplete"
    />
  </div>
</template>

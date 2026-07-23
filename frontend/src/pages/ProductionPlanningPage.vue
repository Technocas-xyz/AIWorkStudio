<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { artworkService, type ArtworkItem } from '@/services/artwork.service'
import { useUiStore } from '@/stores/ui'
import api from '@/services/api'
import ImageLightbox from '@/components/ui/ImageLightbox.vue'

const uiStore = useUiStore()
const artworks = ref<ArtworkItem[]>([])
const selectedArtwork = ref<ArtworkItem | null>(null)
const products = ref<any[]>([])
const selectedProduct = ref('')
const productionPlan = ref<any>(null)
const isCreating = ref(false)
const showLightbox = ref(false)
const placement = ref('center')

const PLACEMENTS = ['center', 'left_chest', 'right_chest', 'full_front', 'full_back', 'pocket', 'sleeve', 'all_over']

async function loadArtworks() {
  try { artworks.value = (await artworkService.list({ page_size: 100 })).items } catch {}
}

async function loadProducts() {
  try {
    const response = await api.get('/planning/products')
    products.value = response.data.data || []
    if (products.value.length > 0) selectedProduct.value = products.value[0].name
  } catch {}
}

function selectArtwork(artwork: ArtworkItem) {
  selectedArtwork.value = artwork
  productionPlan.value = null
}

async function createPlan() {
  if (!selectedArtwork.value || !selectedProduct.value) return
  isCreating.value = true
  try {
    const response = await api.post('/planning/create', {
      artwork_id: selectedArtwork.value.id,
      product: selectedProduct.value,
      placement: placement.value,
    })
    productionPlan.value = response.data.data
    uiStore.addToast({ type: 'success', title: 'Production plan created' })
  } catch (err: any) {
    uiStore.addToast({ type: 'error', title: 'Failed', message: err.response?.data?.detail || 'Error' })
  } finally { isCreating.value = false }
}

async function approvePlan() {
  if (!productionPlan.value) return
  try {
    await api.post('/planning/approve', { plan_id: productionPlan.value.id })
    productionPlan.value.status = 'approved'
    uiStore.addToast({ type: 'success', title: 'Production plan approved' })
  } catch {}
}

function formatSize(bytes: number): string {
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1048576).toFixed(1) + ' MB'
}

function getProductIcon(cat: string): string {
  const icons: Record<string, string> = { transfer: '🔥', apparel: '👕', print: '🖨️', accessory: '🎩' }
  return icons[cat] || '📦'
}

onMounted(() => { loadArtworks(); loadProducts() })
</script>

<template>
  <div class="flex h-full -m-6">
    <!-- Sidebar -->
    <aside class="w-60 border-r border-surface-200 dark:border-surface-800 bg-white dark:bg-surface-900 overflow-y-auto flex-shrink-0">
      <div class="p-4 border-b border-surface-200 dark:border-surface-800">
        <h3 class="text-sm font-semibold text-surface-900 dark:text-white">Select Artwork</h3>
      </div>
      <div class="p-2 space-y-1">
        <div v-for="art in artworks" :key="art.id" @click="selectArtwork(art)"
          :class="['flex items-center gap-2 p-2 rounded-lg cursor-pointer text-sm', selectedArtwork?.id === art.id ? 'bg-primary-50 dark:bg-primary-900/20 text-primary-700' : 'hover:bg-surface-50 dark:hover:bg-surface-800 text-surface-700 dark:text-surface-300']">
          <div class="w-8 h-8 rounded overflow-hidden bg-surface-100 dark:bg-surface-700">
            <img :src="artworkService.getPreviewUrl(art, 'thumbnail')" class="w-full h-full object-cover" @error="($event.target as HTMLImageElement).style.display='none'" />
          </div>
          <div class="flex-1 min-w-0">
            <p class="truncate text-xs font-medium">{{ art.original_filename }}</p>
            <p class="text-[10px] text-surface-500">{{ art.width }}×{{ art.height }}</p>
          </div>
        </div>
      </div>
    </aside>

    <!-- Main -->
    <div class="flex-1 overflow-y-auto p-6">
      <div v-if="!selectedArtwork" class="h-full flex items-center justify-center">
        <div class="text-center">
          <p class="text-5xl mb-3">📋</p>
          <h2 class="text-xl font-semibold text-surface-900 dark:text-white">Production Planning</h2>
          <p class="text-surface-500 mt-2">Select artwork to plan production for a specific product.</p>
        </div>
      </div>

      <div v-if="selectedArtwork" class="space-y-5">
        <!-- Artwork preview -->
        <div class="card p-4">
          <div class="flex items-start gap-4">
            <div @click="showLightbox = true" class="w-32 h-32 bg-surface-100 dark:bg-surface-800 rounded-lg overflow-hidden cursor-zoom-in flex-shrink-0 flex items-center justify-center">
              <img :src="artworkService.getPreviewUrl(selectedArtwork, 'medium')" class="max-w-full max-h-full object-contain" />
            </div>
            <div>
              <h2 class="text-lg font-bold text-surface-900 dark:text-white">{{ selectedArtwork.original_filename }}</h2>
              <p class="text-xs text-surface-500 mt-1">{{ selectedArtwork.width }}×{{ selectedArtwork.height }} · {{ selectedArtwork.extension.toUpperCase() }} · {{ formatSize(selectedArtwork.file_size) }}</p>
            </div>
          </div>
        </div>

        <!-- Product Selection -->
        <div class="card p-5">
          <h3 class="text-sm font-semibold text-surface-900 dark:text-white mb-3">🎯 Product Selection</h3>
          <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-2 mb-4">
            <button v-for="p in products" :key="p.name" @click="selectedProduct = p.name; productionPlan = null"
              :class="['p-3 rounded-lg border text-center transition-all', selectedProduct === p.name ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20 ring-1 ring-primary-500' : 'border-surface-200 dark:border-surface-700 hover:bg-surface-50 dark:hover:bg-surface-800']">
              <p class="text-lg">{{ getProductIcon(p.category) }}</p>
              <p class="text-[10px] font-medium text-surface-700 dark:text-surface-300 mt-1">{{ p.display_name }}</p>
              <p class="text-[9px] text-surface-400">{{ p.max_width }}"×{{ p.max_height }}"</p>
            </button>
          </div>

          <!-- Placement -->
          <div class="flex items-center gap-4 mb-4">
            <div>
              <label class="text-xs font-medium text-surface-600 dark:text-surface-400">Placement</label>
              <select v-model="placement" class="input mt-1 w-40">
                <option v-for="pl in PLACEMENTS" :key="pl" :value="pl">{{ pl.replace('_', ' ') }}</option>
              </select>
            </div>
          </div>

          <button @click="createPlan" :disabled="isCreating || !selectedProduct" class="btn-primary">
            {{ isCreating ? '⏳ Planning...' : '📋 Create Production Plan' }}
          </button>
        </div>

        <!-- Production Plan Result -->
        <div v-if="productionPlan" class="space-y-4">
          <div class="card p-5">
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-sm font-semibold text-surface-900 dark:text-white">🏭 Production Plan: {{ productionPlan.product_display }}</h3>
              <span :class="['badge text-[10px]', productionPlan.status === 'approved' ? 'badge-success' : 'badge-info']">{{ productionPlan.status }}</span>
            </div>

            <!-- Specs grid -->
            <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
              <div class="p-3 bg-surface-50 dark:bg-surface-800 rounded-lg text-center">
                <p class="text-[10px] text-surface-500">Print Size</p>
                <p class="text-sm font-bold text-surface-800 dark:text-white">{{ productionPlan.print_width }}" × {{ productionPlan.print_height }}"</p>
              </div>
              <div class="p-3 bg-surface-50 dark:bg-surface-800 rounded-lg text-center">
                <p class="text-[10px] text-surface-500">Aspect Ratio</p>
                <p class="text-sm font-bold text-surface-800 dark:text-white">{{ productionPlan.aspect_ratio }}</p>
              </div>
              <div class="p-3 bg-surface-50 dark:bg-surface-800 rounded-lg text-center">
                <p class="text-[10px] text-surface-500">Orientation</p>
                <p class="text-sm font-bold text-surface-800 dark:text-white capitalize">{{ productionPlan.orientation }}</p>
              </div>
              <div class="p-3 bg-surface-50 dark:bg-surface-800 rounded-lg text-center">
                <p class="text-[10px] text-surface-500">Scale</p>
                <p class="text-sm font-bold text-surface-800 dark:text-white">{{ (productionPlan.scale_factor * 100).toFixed(0) }}%</p>
              </div>
            </div>

            <!-- Specifications -->
            <div class="border border-surface-200 dark:border-surface-700 rounded-lg overflow-hidden">
              <table class="w-full text-xs">
                <tbody class="divide-y divide-surface-100 dark:divide-surface-800">
                  <tr v-for="(val, key) in productionPlan.specifications" :key="key">
                    <td class="px-4 py-2 font-medium text-surface-600 dark:text-surface-400 capitalize">{{ String(key).replace(/_/g, ' ') }}</td>
                    <td class="px-4 py-2 text-surface-800 dark:text-surface-200">{{ val }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Warnings -->
          <div v-if="productionPlan.warnings?.length > 0" class="card p-5">
            <h3 class="text-sm font-semibold text-surface-900 dark:text-white mb-3">⚠️ Warnings</h3>
            <div class="space-y-2">
              <div v-for="(w, i) in productionPlan.warnings" :key="i"
                :class="['p-3 rounded-lg border-l-4', w.severity === 'critical' ? 'border-red-500 bg-red-50 dark:bg-red-900/10' : w.severity === 'high' ? 'border-orange-500 bg-orange-50 dark:bg-orange-900/10' : 'border-yellow-500 bg-yellow-50 dark:bg-yellow-900/10']">
                <p class="text-xs text-surface-700 dark:text-surface-300">{{ w.message }}</p>
              </div>
            </div>
          </div>

          <!-- Approve -->
          <div v-if="productionPlan.status !== 'approved'" class="flex justify-end">
            <button @click="approvePlan" class="btn-primary px-6">✓ Approve Production Plan</button>
          </div>
        </div>
      </div>

      <ImageLightbox v-if="showLightbox" :src="artworkService.getPreviewUrl(selectedArtwork!, 'large')" @close="showLightbox = false" />
    </div>
  </div>
</template>

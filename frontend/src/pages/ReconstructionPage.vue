<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { artworkService, type ArtworkItem } from '@/services/artwork.service'
import { analysisService, type AnalysisReport } from '@/services/analysis.service'
import { useUiStore } from '@/stores/ui'
import api from '@/services/api'
import ImageLightbox from '@/components/ui/ImageLightbox.vue'

const uiStore = useUiStore()
const artworks = ref<ArtworkItem[]>([])
const selectedArtwork = ref<ArtworkItem | null>(null)
const analysisReport = ref<AnalysisReport | null>(null)
const plan = ref<any>(null)
const isLoading = ref(true)
const isCreating = ref(false)
const showLightbox = ref(false)

async function loadArtworks() {
  isLoading.value = true
  try { artworks.value = (await artworkService.list({ page_size: 100 })).items } catch {}
  finally { isLoading.value = false }
}

async function selectArtwork(artwork: ArtworkItem) {
  selectedArtwork.value = artwork
  plan.value = null
  analysisReport.value = null
  try {
    const report = await analysisService.getLatestForArtwork(artwork.id)
    if (report) analysisReport.value = report
  } catch {}
}

async function createPlan() {
  if (!selectedArtwork.value) return
  isCreating.value = true
  try {
    const response = await api.post('/reconstruction/create', { artwork_id: selectedArtwork.value.id })
    plan.value = response.data.data
    uiStore.addToast({ type: 'success', title: 'Reconstruction plan created' })
  } catch (err: any) {
    uiStore.addToast({ type: 'error', title: 'Failed', message: err.response?.data?.detail || 'Error' })
  } finally { isCreating.value = false }
}

async function toggleOperation(op: any) {
  op.enabled = !op.enabled
  // Save updated operations to backend
  if (plan.value?.id) {
    try {
      await api.put(`/reconstruction/${plan.value.id}`, { operations: plan.value.operations })
    } catch {}
  }
}

async function approvePlan() {
  if (!plan.value) return
  try {
    await api.post('/reconstruction/approve', { plan_id: plan.value.id })
    plan.value.status = 'approved'
    uiStore.addToast({ type: 'success', title: 'Plan approved — ready for AI Production' })
  } catch {}
}

function formatSize(bytes: number): string {
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1048576).toFixed(1) + ' MB'
}

onMounted(loadArtworks)
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
          <p class="text-5xl mb-3">🧩</p>
          <h2 class="text-xl font-semibold text-surface-900 dark:text-white">Reconstruction Workspace</h2>
          <p class="text-surface-500 mt-2">Select artwork to build a reconstruction strategy.</p>
        </div>
      </div>

      <div v-if="selectedArtwork" class="space-y-5">
        <!-- Header + Preview -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <!-- Original Preview -->
          <div class="card p-4">
            <p class="text-xs font-medium text-surface-500 uppercase mb-2">Original Artwork</p>
            <div @click="showLightbox = true" class="bg-surface-100 dark:bg-surface-800 rounded-lg overflow-hidden flex items-center justify-center cursor-zoom-in" style="height: 280px;">
              <img :src="artworkService.getPreviewUrl(selectedArtwork, 'large')" class="max-h-[270px] object-contain" />
            </div>
            <p class="text-[10px] text-surface-500 text-center mt-2">{{ selectedArtwork.width }}×{{ selectedArtwork.height }} · {{ selectedArtwork.extension.toUpperCase() }} · {{ formatSize(selectedArtwork.file_size) }}</p>
          </div>

          <!-- Analysis Summary -->
          <div class="card p-4">
            <p class="text-xs font-medium text-surface-500 uppercase mb-2">Analysis Summary</p>
            <div v-if="analysisReport" class="space-y-2 text-xs">
              <div class="flex justify-between"><span class="text-surface-500">Score</span><span class="font-medium">{{ analysisReport.overall_score }}/100</span></div>
              <div class="flex justify-between"><span class="text-surface-500">Risk Level</span><span class="font-medium capitalize">{{ analysisReport.risk_level }}</span></div>
              <div class="flex justify-between"><span class="text-surface-500">Artwork Type</span><span class="font-medium capitalize">{{ analysisReport.visual_analysis?.artwork_type }}</span></div>
              <div class="flex justify-between"><span class="text-surface-500">Background</span><span class="font-medium capitalize">{{ analysisReport.visual_analysis?.background?.type }}</span></div>
              <div class="flex justify-between"><span class="text-surface-500">DPI</span><span class="font-medium">{{ analysisReport.production_analysis?.effective_dpi }}</span></div>
              <div class="flex justify-between"><span class="text-surface-500">Difficulty</span><span class="font-medium capitalize">{{ analysisReport.production_analysis?.production_difficulty }}</span></div>
              <div class="flex justify-between"><span class="text-surface-500">Recommended</span><span class="font-medium">{{ analysisReport.generation_plan?.recommended_model }}</span></div>
            </div>
            <div v-else class="text-center py-8">
              <p class="text-xs text-surface-500">No analysis available. Run analysis first.</p>
            </div>
            <button v-if="!plan" @click="createPlan" :disabled="isCreating || !analysisReport" class="btn-primary w-full mt-4 text-xs">
              {{ isCreating ? '⏳ Building...' : '🧩 Build Reconstruction Plan' }}
            </button>
          </div>
        </div>

        <!-- Reconstruction Plan -->
        <div v-if="plan" class="space-y-4">
          <!-- Strategy -->
          <div class="card p-5">
            <div class="flex items-center justify-between mb-3">
              <h3 class="text-sm font-semibold text-surface-900 dark:text-white">📋 Reconstruction Strategy</h3>
              <span :class="['badge text-[10px]', plan.status === 'approved' ? 'badge-success' : 'badge-warning']">{{ plan.status }}</span>
            </div>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
              <div class="p-2 bg-surface-50 dark:bg-surface-800 rounded text-center">
                <p class="text-[10px] text-surface-500">Est. Time</p>
                <p class="text-sm font-bold text-surface-800 dark:text-white">{{ plan.estimates?.time_seconds }}s</p>
              </div>
              <div class="p-2 bg-surface-50 dark:bg-surface-800 rounded text-center">
                <p class="text-[10px] text-surface-500">Est. Quality</p>
                <p class="text-sm font-bold text-green-600">{{ plan.estimates?.quality_score }}/100</p>
              </div>
              <div class="p-2 bg-surface-50 dark:bg-surface-800 rounded text-center">
                <p class="text-[10px] text-surface-500">Similarity</p>
                <p class="text-sm font-bold text-surface-800 dark:text-white">{{ plan.estimates?.similarity }}%</p>
              </div>
              <div class="p-2 bg-surface-50 dark:bg-surface-800 rounded text-center">
                <p class="text-[10px] text-surface-500">Credits</p>
                <p class="text-sm font-bold text-surface-800 dark:text-white">{{ plan.estimates?.credits }}</p>
              </div>
            </div>
          </div>

          <!-- Operations Queue -->
          <div class="card p-5">
            <h3 class="text-sm font-semibold text-surface-900 dark:text-white mb-3">⚡ Operations Queue</h3>
            <div class="space-y-2">
              <div v-for="op in plan.operations" :key="op.id"
                :class="['flex items-center gap-3 p-3 rounded-lg border transition-colors', op.enabled ? 'border-primary-200 dark:border-primary-800 bg-primary-50 dark:bg-primary-900/10' : 'border-surface-200 dark:border-surface-700']">
                <input type="checkbox" :checked="op.enabled" @change="toggleOperation(op)" class="rounded border-surface-400 text-primary-600 focus:ring-primary-500" />
                <div class="flex-1">
                  <div class="flex items-center gap-2">
                    <span class="text-xs font-medium text-surface-800 dark:text-surface-200">{{ op.label }}</span>
                    <span class="text-[9px] px-1.5 py-0.5 rounded bg-surface-200 dark:bg-surface-700 text-surface-500">{{ op.confidence * 100 }}%</span>
                  </div>
                  <p class="text-[10px] text-surface-500 mt-0.5">{{ op.description }}</p>
                </div>
                <span class="text-[10px] text-surface-400">~{{ op.estimated_time }}s</span>
              </div>
            </div>
          </div>

          <!-- Prompt Preview (summary, never actual prompt) -->
          <div class="card p-5">
            <h3 class="text-sm font-semibold text-surface-900 dark:text-white mb-3">🤖 AI Strategy Preview</h3>
            <div class="bg-surface-50 dark:bg-surface-800 rounded-lg p-4 text-xs space-y-1 text-surface-700 dark:text-surface-300">
              <p v-if="plan.operations?.find((o: any) => o.id === 'canvas_expansion' && o.enabled)">• Canvas will be expanded to add safe margins</p>
              <p v-if="plan.operations?.find((o: any) => o.id === 'background_removal' && o.enabled)">• Background will be removed for transparent output</p>
              <p v-if="plan.operations?.find((o: any) => o.id === 'super_resolution' && o.enabled)">• Image will be upscaled to meet 300 DPI standard</p>
              <p v-if="plan.operations?.find((o: any) => o.id === 'edge_refinement' && o.enabled)">• Edges will be refined and smoothed</p>
              <p v-if="plan.operations?.find((o: any) => o.id === 'reconstruction' && o.enabled)">• Damaged areas will be reconstructed by AI</p>
              <p v-if="plan.operations?.find((o: any) => o.id === 'noise_reduction' && o.enabled)">• Noise and artifacts will be cleaned</p>
              <p v-if="plan.operations?.find((o: any) => o.id === 'text_preservation' && o.enabled)">• All typography will be preserved exactly</p>
              <p v-if="plan.strategy?.preserve_colors">• Subject colors will remain unchanged</p>
              <p v-if="plan.strategy?.preserve_composition">• Composition and layout will be maintained</p>
              <p class="pt-2 text-surface-500">Primary Model: <span class="font-medium">{{ plan.ai_model_primary }}</span></p>
            </div>
          </div>

          <!-- Approve -->
          <div v-if="plan.status !== 'approved'" class="flex justify-end">
            <button @click="approvePlan" class="btn-primary px-6">✓ Approve & Send to AI Production</button>
          </div>
          <div v-else class="card p-4 border-l-4 border-green-500 bg-green-50 dark:bg-green-900/10">
            <p class="text-sm font-medium text-green-700 dark:text-green-400">✓ Plan Approved — Ready for AI Production</p>
          </div>
        </div>
      </div>

      <ImageLightbox v-if="showLightbox" :src="artworkService.getPreviewUrl(selectedArtwork!, 'large')" @close="showLightbox = false" />
    </div>
  </div>
</template>

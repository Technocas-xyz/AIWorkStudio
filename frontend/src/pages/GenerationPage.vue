<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { artworkService, type ArtworkItem } from '@/services/artwork.service'
import { generationService, type GenerationJob, type Candidate, type AIModelInfo } from '@/services/generation.service'
import { useUiStore } from '@/stores/ui'
import api from '@/services/api'
import ImageLightbox from '@/components/ui/ImageLightbox.vue'

const uiStore = useUiStore()
const artworks = ref<ArtworkItem[]>([])
const selectedArtwork = ref<ArtworkItem | null>(null)
const isLoading = ref(true)
const isGenerating = ref(false)
const currentJob = ref<GenerationJob | null>(null)
const candidates = ref<Candidate[]>([])
const showLightbox = ref(false)
const lightboxSrc = ref('')
const selectedCandidate = ref<Candidate | null>(null)

// Plans from upstream modules
const reconstructionPlan = ref<any>(null)
const productionPlan = ref<any>(null)
const hasApprovedPlans = computed(() => reconstructionPlan.value?.status === 'approved' || productionPlan.value?.status === 'approved')

// Derived settings from plans
const operations = computed(() => {
  if (!reconstructionPlan.value?.operations) return []
  return reconstructionPlan.value.operations.filter((o: any) => o.enabled)
})

const aiModel = computed(() => reconstructionPlan.value?.ai_model_primary || 'gpt_image')

const primaryMode = computed(() => {
  const ops = operations.value
  if (ops.find((o: any) => o.id === 'reconstruction')) return 'reconstruction'
  if (ops.find((o: any) => o.id === 'background_removal')) return 'background_cleanup'
  if (ops.find((o: any) => o.id === 'super_resolution')) return 'upscaling'
  if (ops.find((o: any) => o.id === 'edge_refinement')) return 'edge_refinement'
  return 'enhancement'
})

const productInfo = computed(() => {
  if (!productionPlan.value) return null
  return {
    product: productionPlan.value.product_display || productionPlan.value.product,
    printSize: `${productionPlan.value.print_width}" × ${productionPlan.value.print_height}"`,
    aspectRatio: productionPlan.value.aspect_ratio,
    orientation: productionPlan.value.orientation,
    scale: productionPlan.value.scale_factor,
  }
})

async function loadArtworks() {
  isLoading.value = true
  try { artworks.value = (await artworkService.list({ page_size: 100 })).items } catch {}
  finally { isLoading.value = false }
}

async function selectArtwork(artwork: ArtworkItem) {
  selectedArtwork.value = artwork
  candidates.value = []
  currentJob.value = null
  selectedCandidate.value = null
  reconstructionPlan.value = null
  productionPlan.value = null

  // Load existing generation history (previously generated candidates)
  try {
    const historyResponse = await api.get(`/generation/artwork/${artwork.id}/history`)
    const history = historyResponse.data.data
    if (history && history.candidates && history.candidates.length > 0) {
      candidates.value = history.candidates
      selectedCandidate.value = history.candidates[0]
      if (history.job) {
        currentJob.value = history.job as any
      }
    }
  } catch {}

  // Load approved reconstruction plan
  try {
    const response = await api.post('/reconstruction/create', { artwork_id: artwork.id })
    const plan = response.data.data
    reconstructionPlan.value = plan
  } catch {}

  // Load production plan if exists
  try {
    const ppResponse = await api.get(`/planning/artwork/${artwork.id}/latest`)
    if (ppResponse.data.data) {
      productionPlan.value = ppResponse.data.data
    }
  } catch {}
}

async function startGeneration() {
  if (!selectedArtwork.value) return
  isGenerating.value = true
  currentJob.value = null

  // Build operations dict from reconstruction plan
  const opsDict: Record<string, boolean> = {}
  for (const op of operations.value) {
    opsDict[op.id] = true
  }

  const targetRatio = productionPlan.value?.aspect_ratio || ''

  try {
    const result = await generationService.startGeneration(
      selectedArtwork.value.id,
      aiModel.value,
      primaryMode.value,
      opsDict,
      targetRatio,
      ''
    )
    currentJob.value = result

    if (result.status === 'completed' && result.candidate) {
      candidates.value.push(result.candidate)
      selectedCandidate.value = result.candidate
      uiStore.addToast({ type: 'success', title: 'Generation complete', message: `Similarity: ${result.candidate.similarity_score}%` })
    } else if (result.status === 'failed') {
      uiStore.addToast({ type: 'error', title: 'Generation failed', message: result.error || 'Unknown error' })
    }
  } catch (err: any) {
    uiStore.addToast({ type: 'error', title: 'Generation failed', message: err.response?.data?.detail || 'Error' })
  } finally {
    isGenerating.value = false
  }
}

async function regenerate() {
  if (!currentJob.value) {
    await startGeneration()
    return
  }
  isGenerating.value = true
  try {
    const result = await generationService.retry(currentJob.value.job_id)
    if (result.candidate) {
      candidates.value.push(result.candidate)
      selectedCandidate.value = result.candidate
      uiStore.addToast({ type: 'success', title: 'New candidate generated' })
    }
  } catch (err: any) {
    uiStore.addToast({ type: 'error', title: 'Retry failed' })
  } finally { isGenerating.value = false }
}

async function approveCandidate(candidate: Candidate) {
  if (!currentJob.value) return
  try {
    const result = await generationService.approve(currentJob.value.job_id, candidate.id)
    candidate.status = 'approved'
    uiStore.addToast({ type: 'success', title: '✓ Master Artwork Approved', message: `Version ${result.version}` })
  } catch {}
}

async function rejectCandidate(candidate: Candidate) {
  if (!currentJob.value) return
  try {
    await generationService.reject(currentJob.value.job_id, candidate.id)
    candidate.status = 'rejected'
  } catch {}
}

function openLightbox(src: string) {
  lightboxSrc.value = src
  showLightbox.value = true
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
          <p class="text-5xl mb-3">✨</p>
          <h2 class="text-xl font-semibold text-surface-900 dark:text-white">AI Production</h2>
          <p class="text-surface-500 mt-2">Select artwork to execute the approved Reconstruction Plan.</p>
          <p class="text-xs text-surface-400 mt-1">Build plans in Reconstruction & Production Planning workspaces first.</p>
        </div>
      </div>

      <div v-if="selectedArtwork" class="space-y-5">
        <!-- Header -->
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-lg font-bold text-surface-900 dark:text-white">{{ selectedArtwork.original_filename }}</h1>
            <p class="text-xs text-surface-500">{{ selectedArtwork.artwork_id }} · {{ selectedArtwork.width }}×{{ selectedArtwork.height }}</p>
          </div>
        </div>

        <!-- Plan Summary Cards -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <!-- Reconstruction Plan Summary -->
          <div class="card p-4">
            <div class="flex items-center justify-between mb-2">
              <h4 class="text-xs font-semibold text-surface-900 dark:text-white uppercase">🧩 Reconstruction Plan</h4>
              <span v-if="reconstructionPlan" class="badge-success text-[9px]">Ready</span>
              <span v-else class="badge-warning text-[9px]">Not Created</span>
            </div>
            <div v-if="reconstructionPlan" class="space-y-1.5 text-xs">
              <div class="flex justify-between"><span class="text-surface-500">Model</span><span class="font-medium">{{ reconstructionPlan.ai_model_primary }}</span></div>
              <div class="flex justify-between"><span class="text-surface-500">Operations</span><span class="font-medium">{{ operations.length }} active</span></div>
              <div class="flex justify-between"><span class="text-surface-500">Est. Quality</span><span class="font-medium text-green-600">{{ reconstructionPlan.estimates?.quality_score }}/100</span></div>
              <div class="flex justify-between"><span class="text-surface-500">Est. Time</span><span class="font-medium">{{ reconstructionPlan.estimates?.time_seconds }}s</span></div>
              <div class="mt-2 flex flex-wrap gap-1">
                <span v-for="op in operations" :key="op.id" class="text-[9px] px-1.5 py-0.5 rounded bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-400">
                  {{ op.label }}
                </span>
              </div>
            </div>
            <p v-else class="text-[10px] text-surface-500">Go to Reconstruction workspace to create a plan.</p>
          </div>

          <!-- Production Plan Summary -->
          <div class="card p-4">
            <div class="flex items-center justify-between mb-2">
              <h4 class="text-xs font-semibold text-surface-900 dark:text-white uppercase">📋 Production Plan</h4>
              <span v-if="productInfo" class="badge-success text-[9px]">Ready</span>
              <span v-else class="badge-info text-[9px]">Optional</span>
            </div>
            <div v-if="productInfo" class="space-y-1.5 text-xs">
              <div class="flex justify-between"><span class="text-surface-500">Product</span><span class="font-medium">{{ productInfo.product }}</span></div>
              <div class="flex justify-between"><span class="text-surface-500">Print Size</span><span class="font-medium">{{ productInfo.printSize }}</span></div>
              <div class="flex justify-between"><span class="text-surface-500">Aspect Ratio</span><span class="font-medium">{{ productInfo.aspectRatio }}</span></div>
              <div class="flex justify-between"><span class="text-surface-500">Orientation</span><span class="font-medium capitalize">{{ productInfo.orientation }}</span></div>
            </div>
            <p v-else class="text-[10px] text-surface-500">Go to Production Planning workspace to set product & sizing. Generation will use original dimensions.</p>
          </div>
        </div>

        <!-- Generate Button -->
        <div class="card p-4 flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-surface-800 dark:text-white">Execute AI Production</p>
            <p class="text-[10px] text-surface-500">Mode: <span class="font-medium capitalize">{{ primaryMode.replace('_', ' ') }}</span> · Model: <span class="font-medium">{{ aiModel }}</span> · {{ operations.length }} operations</p>
          </div>
          <div class="flex gap-2">
            <button v-if="candidates.length > 0" @click="regenerate" :disabled="isGenerating" class="btn-secondary text-xs">🔄 Regenerate</button>
            <button @click="startGeneration" :disabled="isGenerating || !reconstructionPlan" class="btn-primary px-6">
              {{ isGenerating ? '⏳ Generating...' : '🚀 Generate Master Artwork' }}
            </button>
          </div>
        </div>

        <!-- Progress -->
        <div v-if="isGenerating" class="card p-5">
          <div class="flex items-center justify-between mb-2">
            <span class="text-sm font-medium text-surface-700 dark:text-surface-300">AI Generation in progress...</span>
            <span class="animate-pulse text-primary-600 text-sm">●</span>
          </div>
          <div class="w-full h-2 bg-surface-200 dark:bg-surface-700 rounded-full overflow-hidden">
            <div class="h-full bg-gradient-to-r from-primary-500 to-emerald-500 rounded-full animate-pulse" style="width: 60%"></div>
          </div>
        </div>

        <!-- Error -->
        <div v-if="currentJob?.status === 'failed' && !isGenerating" class="card p-4 border-l-4 border-red-500">
          <p class="text-sm font-medium text-red-600">Generation Failed</p>
          <p class="text-xs text-surface-600 mt-1">{{ currentJob.error }}</p>
          <button @click="regenerate" class="btn-secondary text-xs mt-2">🔄 Retry</button>
        </div>

        <!-- Side-by-side Comparison -->
        <div v-if="candidates.length > 0" class="space-y-4">
          <h3 class="text-sm font-semibold text-surface-900 dark:text-white">🎯 Original vs Generated</h3>

          <div class="card p-4">
            <div class="grid grid-cols-2 gap-4">
              <!-- Original -->
              <div>
                <p class="text-[10px] font-medium text-surface-500 text-center mb-1 uppercase">Original</p>
                <div @click="openLightbox(artworkService.getPreviewUrl(selectedArtwork!, 'large'))"
                  class="bg-surface-100 dark:bg-surface-800 rounded-lg overflow-hidden flex items-center justify-center cursor-zoom-in" style="height: 350px;">
                  <img :src="artworkService.getPreviewUrl(selectedArtwork!, 'large')" class="max-h-[340px] object-contain" />
                </div>
                <p class="text-[10px] text-surface-500 text-center mt-1">{{ selectedArtwork!.width }}×{{ selectedArtwork!.height }} · {{ formatSize(selectedArtwork!.file_size) }}</p>
              </div>

              <!-- Generated -->
              <div>
                <p class="text-[10px] font-medium text-surface-500 text-center mb-1 uppercase">Generated — #{{ (selectedCandidate || candidates[candidates.length - 1]).candidate_number }}</p>
                <div @click="openLightbox(generationService.getCandidateImageUrl(selectedCandidate || candidates[candidates.length - 1]))"
                  class="bg-surface-100 dark:bg-surface-800 rounded-lg overflow-hidden flex items-center justify-center cursor-zoom-in" style="height: 350px;">
                  <img :src="generationService.getCandidateImageUrl(selectedCandidate || candidates[candidates.length - 1])" class="max-h-[340px] object-contain" @error="($event.target as HTMLImageElement).style.display='none'" />
                </div>
                <p class="text-[10px] text-surface-500 text-center mt-1">{{ (selectedCandidate || candidates[candidates.length - 1]).width }}×{{ (selectedCandidate || candidates[candidates.length - 1]).height }} · {{ formatSize((selectedCandidate || candidates[candidates.length - 1]).file_size) }}</p>
              </div>
            </div>
          </div>

          <!-- Candidates -->
          <div class="grid grid-cols-3 md:grid-cols-4 xl:grid-cols-6 gap-3">
            <div v-for="c in candidates" :key="c.id" @click="selectedCandidate = c"
              :class="['card overflow-hidden cursor-pointer transition-all', c.status === 'approved' ? 'ring-2 ring-green-500' : '', (selectedCandidate || candidates[candidates.length - 1]).id === c.id ? 'ring-2 ring-primary-500' : '']">
              <div class="aspect-square bg-surface-100 dark:bg-surface-800 relative">
                <img :src="generationService.getCandidateImageUrl(c)" class="w-full h-full object-contain" @error="($event.target as HTMLImageElement).style.display='none'" />
                <div v-if="c.status === 'approved'" class="absolute top-1 right-1 bg-green-500 text-white text-[7px] font-bold px-1 py-0.5 rounded">MASTER</div>
              </div>
              <div class="p-2">
                <div class="flex justify-between text-[10px]">
                  <span class="font-medium">#{{ c.candidate_number }}</span>
                  <span :class="c.similarity_score >= 90 ? 'text-green-600' : 'text-yellow-600'">{{ c.similarity_score }}%</span>
                </div>
                <div v-if="c.status === 'generated'" class="flex gap-1 mt-1.5">
                  <button @click.stop="approveCandidate(c)" class="flex-1 text-[9px] py-1 bg-green-600 text-white rounded hover:bg-green-700">✓ Approve</button>
                  <button @click.stop="rejectCandidate(c)" class="flex-1 text-[9px] py-1 bg-surface-200 dark:bg-surface-700 text-surface-600 rounded hover:bg-surface-300">✗</button>
                </div>
                <p v-else-if="c.status === 'approved'" class="text-[9px] text-green-600 text-center mt-1">Master ✓</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <ImageLightbox v-if="showLightbox" :src="lightboxSrc" @close="showLightbox = false" />
    </div>
  </div>
</template>

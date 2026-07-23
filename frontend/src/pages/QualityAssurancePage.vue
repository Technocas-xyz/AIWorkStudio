<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { artworkService, type ArtworkItem } from '@/services/artwork.service'
import { useUiStore } from '@/stores/ui'
import api from '@/services/api'
import ImageLightbox from '@/components/ui/ImageLightbox.vue'

const uiStore = useUiStore()
const artworks = ref<ArtworkItem[]>([])
const selectedArtwork = ref<ArtworkItem | null>(null)
const qaReport = ref<any>(null)
const isInspecting = ref(false)
const showLightbox = ref(false)
const approvalNotes = ref('')

async function loadArtworks() {
  try { artworks.value = (await artworkService.list({ page_size: 100 })).items } catch {}
}

function selectArtwork(artwork: ArtworkItem) {
  selectedArtwork.value = artwork
  qaReport.value = null
}

async function startInspection() {
  if (!selectedArtwork.value) return
  isInspecting.value = true
  try {
    const response = await api.post('/qa/start', { artwork_id: selectedArtwork.value.id })
    qaReport.value = response.data.data
    uiStore.addToast({ type: 'success', title: 'QA Inspection complete', message: `Score: ${qaReport.value.overall_score}/100` })
  } catch (err: any) {
    uiStore.addToast({ type: 'error', title: 'Inspection failed', message: err.response?.data?.detail || 'Error' })
  } finally { isInspecting.value = false }
}

async function approve() {
  if (!qaReport.value) return
  try {
    await api.post(`/qa/${qaReport.value.id}/approve`, { notes: approvalNotes.value })
    qaReport.value.status = 'approved'
    uiStore.addToast({ type: 'success', title: '✓ QA Approved', message: 'Artwork cleared for production' })
  } catch {}
}

async function reject() {
  if (!qaReport.value) return
  try {
    await api.post(`/qa/${qaReport.value.id}/reject`, { notes: approvalNotes.value })
    qaReport.value.status = 'rejected'
    uiStore.addToast({ type: 'error', title: 'QA Rejected' })
  } catch {}
}

async function sendBack(target: string) {
  if (!qaReport.value) return
  try {
    await api.post(`/qa/${qaReport.value.id}/send-back`, { target, notes: approvalNotes.value })
    qaReport.value.status = 'sent_back'
    uiStore.addToast({ type: 'warning', title: `Sent back to ${target.replace('_', ' ')}` })
  } catch {}
}

function scoreColor(score: number): string {
  if (score >= 90) return 'text-green-600'
  if (score >= 70) return 'text-yellow-600'
  return 'text-red-600'
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
          <p class="text-5xl mb-3">✅</p>
          <h2 class="text-xl font-semibold text-surface-900 dark:text-white">Quality Assurance</h2>
          <p class="text-surface-500 mt-2">Select artwork to run QA inspection.</p>
        </div>
      </div>

      <div v-if="selectedArtwork" class="space-y-5">
        <!-- Header + Preview -->
        <div class="card p-4">
          <div class="flex items-start gap-4">
            <div @click="showLightbox = true" class="w-24 h-24 bg-surface-100 dark:bg-surface-800 rounded-lg overflow-hidden cursor-zoom-in flex-shrink-0 flex items-center justify-center">
              <img :src="artworkService.getPreviewUrl(selectedArtwork, 'medium')" class="max-w-full max-h-full object-contain" />
            </div>
            <div class="flex-1">
              <h2 class="text-lg font-bold text-surface-900 dark:text-white">{{ selectedArtwork.original_filename }}</h2>
              <p class="text-xs text-surface-500">{{ selectedArtwork.artwork_id }} · {{ selectedArtwork.width }}×{{ selectedArtwork.height }}</p>
            </div>
            <button @click="startInspection" :disabled="isInspecting" class="btn-primary">
              {{ isInspecting ? '⏳ Inspecting...' : qaReport ? '🔄 Re-inspect' : '✅ Run QA Inspection' }}
            </button>
          </div>
        </div>

        <!-- QA Report -->
        <div v-if="qaReport" class="space-y-4">
          <!-- Score Summary -->
          <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
            <div class="card p-3 text-center">
              <p class="text-[10px] text-surface-500">Overall</p>
              <p class="text-2xl font-bold" :class="scoreColor(qaReport.overall_score)">{{ Math.round(qaReport.overall_score) }}</p>
            </div>
            <div class="card p-3 text-center">
              <p class="text-[10px] text-surface-500">Production Ready</p>
              <p class="text-lg font-bold" :class="qaReport.production_ready ? 'text-green-600' : 'text-red-600'">{{ qaReport.production_ready ? 'YES' : 'NO' }}</p>
            </div>
            <div class="card p-3 text-center">
              <p class="text-[10px] text-surface-500">Critical</p>
              <p class="text-lg font-bold" :class="qaReport.critical_issues === 0 ? 'text-green-600' : 'text-red-600'">{{ qaReport.critical_issues }}</p>
            </div>
            <div class="card p-3 text-center">
              <p class="text-[10px] text-surface-500">Similarity</p>
              <p class="text-lg font-bold" :class="scoreColor(qaReport.scores?.similarity || 0)">{{ Math.round(qaReport.scores?.similarity || 0) }}%</p>
            </div>
            <div class="card p-3 text-center">
              <p class="text-[10px] text-surface-500">Print</p>
              <p class="text-lg font-bold" :class="scoreColor(qaReport.scores?.print_quality || 0)">{{ Math.round(qaReport.scores?.print_quality || 0) }}%</p>
            </div>
            <div class="card p-3 text-center">
              <p class="text-[10px] text-surface-500">Transparency</p>
              <p class="text-lg font-bold" :class="scoreColor(qaReport.scores?.transparency || 0)">{{ Math.round(qaReport.scores?.transparency || 0) }}%</p>
            </div>
            <div class="card p-3 text-center">
              <p class="text-[10px] text-surface-500">Edge</p>
              <p class="text-lg font-bold" :class="scoreColor(qaReport.scores?.edge || 0)">{{ Math.round(qaReport.scores?.edge || 0) }}%</p>
            </div>
          </div>

          <!-- Inspection Checks -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <!-- Visual Inspection -->
            <div class="card p-4">
              <h4 class="text-xs font-semibold text-surface-900 dark:text-white uppercase mb-2">🔬 Visual Inspection</h4>
              <div class="space-y-1.5">
                <div v-for="check in qaReport.visual_inspection?.checks || []" :key="check.name" class="flex items-center justify-between text-xs">
                  <span class="text-surface-600 dark:text-surface-400">{{ check.name }}</span>
                  <span :class="check.pass ? 'text-green-600' : 'text-red-600'" class="font-medium">{{ check.pass ? '✓ PASS' : '✗ FAIL' }}</span>
                </div>
              </div>
            </div>

            <!-- Print Inspection -->
            <div class="card p-4">
              <h4 class="text-xs font-semibold text-surface-900 dark:text-white uppercase mb-2">🖨️ Print Inspection</h4>
              <div class="space-y-1.5">
                <div v-for="check in qaReport.print_inspection?.checks || []" :key="check.name" class="flex items-center justify-between text-xs">
                  <span class="text-surface-600 dark:text-surface-400">{{ check.name }}</span>
                  <div class="flex items-center gap-2">
                    <span class="text-[10px] text-surface-500">{{ check.value }}</span>
                    <span :class="check.pass ? 'text-green-600' : 'text-red-600'" class="font-medium">{{ check.pass ? '✓' : '✗' }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Product Validation -->
          <div v-if="qaReport.product_validation" class="card p-4">
            <h4 class="text-xs font-semibold text-surface-900 dark:text-white uppercase mb-2">🎯 Product Validation: {{ qaReport.product_validation.product }}</h4>
            <div class="flex flex-wrap gap-2">
              <span v-for="check in qaReport.product_validation.checks || []" :key="check.name"
                :class="['text-[10px] px-2 py-1 rounded font-medium', check.pass ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400']">
                {{ check.pass ? '✓' : '✗' }} {{ check.name }}
              </span>
            </div>
          </div>

          <!-- Issues -->
          <div v-if="qaReport.issues?.length > 0" class="card p-4">
            <h4 class="text-xs font-semibold text-surface-900 dark:text-white uppercase mb-2">⚠️ Issues ({{ qaReport.issues.length }})</h4>
            <div class="space-y-2">
              <div v-for="(issue, idx) in qaReport.issues" :key="idx"
                :class="['p-3 rounded-lg border-l-4', issue.severity === 'critical' ? 'border-red-500 bg-red-50 dark:bg-red-900/10' : issue.severity === 'high' ? 'border-orange-500 bg-orange-50 dark:bg-orange-900/10' : 'border-yellow-500 bg-yellow-50 dark:bg-yellow-900/10']">
                <div class="flex items-center gap-2">
                  <span class="text-xs font-medium text-surface-800 dark:text-surface-200">{{ issue.title }}</span>
                  <span class="text-[9px] px-1.5 py-0.5 rounded bg-surface-200 dark:bg-surface-700 text-surface-500 uppercase">{{ issue.severity }}</span>
                </div>
                <p class="text-[10px] text-surface-600 dark:text-surface-400 mt-1">{{ issue.description }}</p>
                <p v-if="issue.recommendation" class="text-[10px] text-primary-600 mt-1">💡 {{ issue.recommendation }}</p>
              </div>
            </div>
          </div>

          <!-- Recommendations -->
          <div v-if="qaReport.recommendations?.length > 0" class="card p-4">
            <h4 class="text-xs font-semibold text-surface-900 dark:text-white uppercase mb-2">💡 Recommendations</h4>
            <div class="space-y-1.5">
              <div v-for="(rec, idx) in qaReport.recommendations" :key="idx" class="flex items-center gap-2 text-xs">
                <span class="text-[9px] px-1.5 py-0.5 rounded bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-400">{{ rec.module }}</span>
                <span class="text-surface-700 dark:text-surface-300">{{ rec.action }}</span>
              </div>
            </div>
          </div>

          <!-- Approval Panel -->
          <div class="card p-5">
            <h4 class="text-xs font-semibold text-surface-900 dark:text-white uppercase mb-3">📝 Approval Decision</h4>

            <div v-if="qaReport.status === 'approved'" class="p-4 bg-green-50 dark:bg-green-900/10 rounded-lg border border-green-200 dark:border-green-800">
              <p class="text-sm font-medium text-green-700 dark:text-green-400">✓ QA Approved — Artwork cleared for Variant Generation & Export</p>
            </div>
            <div v-else-if="qaReport.status === 'rejected'" class="p-4 bg-red-50 dark:bg-red-900/10 rounded-lg border border-red-200 dark:border-red-800">
              <p class="text-sm font-medium text-red-700 dark:text-red-400">✗ QA Rejected</p>
            </div>
            <div v-else-if="qaReport.status === 'sent_back'" class="p-4 bg-yellow-50 dark:bg-yellow-900/10 rounded-lg border border-yellow-200 dark:border-yellow-800">
              <p class="text-sm font-medium text-yellow-700 dark:text-yellow-400">↩ Sent back for corrections</p>
            </div>
            <div v-else>
              <textarea v-model="approvalNotes" class="input mb-3" rows="2" placeholder="Reviewer notes (optional)..."></textarea>
              <div class="flex flex-wrap gap-2">
                <button @click="approve" class="btn-primary text-xs px-4">✓ Approve</button>
                <button @click="reject" class="btn-danger text-xs px-4">✗ Reject</button>
                <button @click="sendBack('reconstruction')" class="btn-secondary text-xs">↩ Send to Reconstruction</button>
                <button @click="sendBack('ai_production')" class="btn-secondary text-xs">↩ Send to AI Production</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <ImageLightbox v-if="showLightbox" :src="artworkService.getPreviewUrl(selectedArtwork!, 'large')" @close="showLightbox = false" />
    </div>
  </div>
</template>

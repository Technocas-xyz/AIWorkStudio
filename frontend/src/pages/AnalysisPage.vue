<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { artworkService, type ArtworkItem } from '@/services/artwork.service'
import { analysisService, type AnalysisReport } from '@/services/analysis.service'
import { useUiStore } from '@/stores/ui'
import AnalysisReportView from '@/components/analysis/AnalysisReportView.vue'
import ImageLightbox from '@/components/ui/ImageLightbox.vue'

const uiStore = useUiStore()
const artworks = ref<ArtworkItem[]>([])
const selectedArtwork = ref<ArtworkItem | null>(null)
const isLoading = ref(true)
const isAnalyzing = ref(false)
const analysisStep = ref('')
const selectedEngine = ref<'pillow' | 'gpt' | 'both'>('pillow')
const showLightbox = ref(false)

// Reports for each engine
const pillowReport = ref<AnalysisReport | null>(null)
const gptReport = ref<AnalysisReport | null>(null)

// Active view mode
const viewMode = ref<'single' | 'compare'>('single')

const currentReport = computed(() => {
  if (viewMode.value === 'compare') return pillowReport.value
  if (selectedEngine.value === 'gpt') return gptReport.value
  return pillowReport.value
})

const savedReports = ref<Array<{ id: string; engine: string; version: number; score: number; date: string }>>([])

async function loadArtworks() {
  isLoading.value = true
  try {
    const result = await artworkService.list({ page_size: 100 })
    artworks.value = result.items
  } catch { artworks.value = [] }
  finally { isLoading.value = false }
}

async function selectArtwork(artwork: ArtworkItem) {
  selectedArtwork.value = artwork
  pillowReport.value = null
  gptReport.value = null
  viewMode.value = 'single'
  // Load saved reports for this artwork
  await loadSavedReports(artwork.id)
}

async function loadSavedReports(artworkId: string) {
  try {
    const report = await analysisService.getLatestForArtwork(artworkId)
    if (report) {
      pillowReport.value = report
      // Check engine_used
      const engineUsed = report.visual_analysis?.engine_used
      if (engineUsed === 'gpt') {
        gptReport.value = report
        pillowReport.value = null
      }
    }
  } catch {}
}

async function runAnalysis() {
  if (!selectedArtwork.value) return
  isAnalyzing.value = true
  analysisStep.value = 'Starting...'

  try {
    if (selectedEngine.value === 'both') {
      // Run both engines
      analysisStep.value = 'Running Pillow analysis...'
      const pillowResult = await analysisService.startAnalysis(selectedArtwork.value.id, 'pillow')
      if (pillowResult.status === 'completed') {
        pillowReport.value = await analysisService.getReport(pillowResult.job_id)
      }

      analysisStep.value = 'Running GPT-5.5 analysis...'
      const gptResult = await analysisService.startAnalysis(selectedArtwork.value.id, 'gpt')
      if (gptResult.status === 'completed') {
        gptReport.value = await analysisService.getReport(gptResult.job_id)
      }

      viewMode.value = 'compare'
      uiStore.addToast({ type: 'success', title: 'Comparison complete', message: 'Both engines analyzed successfully' })
    } else {
      // Run single engine
      analysisStep.value = `Running ${selectedEngine.value === 'gpt' ? 'GPT-5.5' : 'Pillow'} analysis...`
      const result = await analysisService.startAnalysis(selectedArtwork.value.id, selectedEngine.value)

      if (result.status === 'completed') {
        const report = await analysisService.getReport(result.job_id)
        if (selectedEngine.value === 'gpt') {
          gptReport.value = report
        } else {
          pillowReport.value = report
        }
        viewMode.value = 'single'
        uiStore.addToast({ type: 'success', title: 'Analysis complete', message: `Score: ${report.overall_score}/100` })
      } else {
        uiStore.addToast({ type: 'error', title: 'Analysis failed', message: result.error || 'Unknown error' })
      }
    }
  } catch (err: any) {
    uiStore.addToast({ type: 'error', title: 'Analysis failed', message: err.response?.data?.detail || 'An error occurred' })
  } finally {
    isAnalyzing.value = false
  }
}

function saveReport(report: AnalysisReport) {
  // Download as JSON
  const data = JSON.stringify({
    artwork_id: selectedArtwork.value?.artwork_id,
    filename: selectedArtwork.value?.original_filename,
    analyzed_at: new Date().toISOString(),
    overall_score: report.overall_score,
    risk_level: report.risk_level,
    engine: report.visual_analysis?.engine_used || 'pillow',
    file_inspection: report.file_inspection,
    visual_analysis: report.visual_analysis,
    geometry_analysis: report.geometry_analysis,
    production_analysis: report.production_analysis,
    product_compatibility: report.product_compatibility,
    risk_assessment: report.risk_assessment,
    decision_plan: report.decision_plan,
    generation_plan: report.generation_plan,
  }, null, 2)

  const blob = new Blob([data], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `analysis_${selectedArtwork.value?.artwork_id || 'report'}_${report.visual_analysis?.engine_used || 'pillow'}_v${report.version}.json`
  a.click()
  URL.revokeObjectURL(url)
  uiStore.addToast({ type: 'success', title: 'Report saved', message: 'JSON file downloaded' })
}

function saveComparison() {
  if (!pillowReport.value || !gptReport.value) return
  const data = JSON.stringify({
    artwork_id: selectedArtwork.value?.artwork_id,
    filename: selectedArtwork.value?.original_filename,
    compared_at: new Date().toISOString(),
    pillow: {
      overall_score: pillowReport.value.overall_score,
      risk_level: pillowReport.value.risk_level,
      visual_analysis: pillowReport.value.visual_analysis,
      generation_plan: pillowReport.value.generation_plan,
    },
    gpt: {
      overall_score: gptReport.value.overall_score,
      risk_level: gptReport.value.risk_level,
      visual_analysis: gptReport.value.visual_analysis,
      generation_plan: gptReport.value.generation_plan,
    },
  }, null, 2)

  const blob = new Blob([data], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `comparison_${selectedArtwork.value?.artwork_id || 'report'}.json`
  a.click()
  URL.revokeObjectURL(url)
  uiStore.addToast({ type: 'success', title: 'Comparison saved', message: 'JSON file downloaded' })
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1048576).toFixed(1) + ' MB'
}

onMounted(loadArtworks)
</script>

<template>
  <div class="flex h-full -m-6">
    <!-- Artwork Selector Panel -->
    <aside class="w-64 border-r border-surface-200 dark:border-surface-800 bg-white dark:bg-surface-900 overflow-y-auto flex-shrink-0">
      <div class="p-4 border-b border-surface-200 dark:border-surface-800">
        <h3 class="text-sm font-semibold text-surface-900 dark:text-white">Select Artwork</h3>
        <p class="text-xs text-surface-500 mt-0.5">Choose artwork to analyze</p>
      </div>
      <div class="p-2 space-y-1">
        <div
          v-for="art in artworks"
          :key="art.id"
          @click="selectArtwork(art)"
          :class="[
            'flex items-center gap-2 p-2 rounded-lg cursor-pointer text-sm transition-colors',
            selectedArtwork?.id === art.id ? 'bg-primary-50 dark:bg-primary-900/20 text-primary-700' : 'hover:bg-surface-50 dark:hover:bg-surface-800 text-surface-700 dark:text-surface-300'
          ]"
        >
          <div class="w-8 h-8 bg-surface-100 dark:bg-surface-700 rounded flex items-center justify-center text-xs overflow-hidden">
            <img :src="artworkService.getPreviewUrl(art, 'thumbnail')" class="w-full h-full object-cover rounded" @error="($event.target as HTMLImageElement).style.display='none'" />
          </div>
          <div class="flex-1 min-w-0">
            <p class="truncate text-xs font-medium">{{ art.original_filename }}</p>
            <p class="text-[10px] text-surface-500">{{ art.width }}×{{ art.height }}</p>
          </div>
        </div>
        <p v-if="artworks.length === 0 && !isLoading" class="text-xs text-surface-500 text-center py-4">No artworks uploaded yet</p>
      </div>
    </aside>

    <!-- Main Content -->
    <div class="flex-1 overflow-y-auto p-6">
      <!-- No artwork selected -->
      <div v-if="!selectedArtwork" class="h-full flex items-center justify-center">
        <div class="text-center">
          <p class="text-5xl mb-3">🧠</p>
          <h2 class="text-xl font-semibold text-surface-900 dark:text-white">Artwork Intelligence Engine</h2>
          <p class="text-surface-500 mt-2">Select an artwork from the left panel to begin analysis.</p>
        </div>
      </div>

      <!-- Artwork selected -->
      <div v-if="selectedArtwork" class="space-y-6">
        <!-- Header -->
        <div class="flex items-center justify-between flex-wrap gap-3">
          <div>
            <h1 class="text-xl font-bold text-surface-900 dark:text-white">{{ selectedArtwork.original_filename }}</h1>
            <p class="text-sm text-surface-500">{{ selectedArtwork.artwork_id }} · {{ selectedArtwork.width }}×{{ selectedArtwork.height }} · {{ selectedArtwork.extension.toUpperCase() }} · {{ formatSize(selectedArtwork.file_size) }}</p>
          </div>
          <div class="flex items-center gap-3">
            <!-- Engine Selector -->
            <div class="flex items-center border border-surface-200 dark:border-surface-700 rounded-lg overflow-hidden">
              <button
                @click="selectedEngine = 'pillow'"
                :class="['px-3 py-2 text-sm font-medium transition-colors', selectedEngine === 'pillow' ? 'bg-primary-600 text-white' : 'bg-white dark:bg-surface-800 text-surface-600 dark:text-surface-400 hover:bg-surface-50 dark:hover:bg-surface-700']"
              >
                🖼️ Pillow
              </button>
              <button
                @click="selectedEngine = 'gpt'"
                :class="['px-3 py-2 text-sm font-medium transition-colors', selectedEngine === 'gpt' ? 'bg-emerald-600 text-white' : 'bg-white dark:bg-surface-800 text-surface-600 dark:text-surface-400 hover:bg-surface-50 dark:hover:bg-surface-700']"
              >
                🧠 GPT-5.5
              </button>
              <button
                @click="selectedEngine = 'both'"
                :class="['px-3 py-2 text-sm font-medium transition-colors', selectedEngine === 'both' ? 'bg-violet-600 text-white' : 'bg-white dark:bg-surface-800 text-surface-600 dark:text-surface-400 hover:bg-surface-50 dark:hover:bg-surface-700']"
              >
                ⚔️ Compare
              </button>
            </div>
            <button
              @click="runAnalysis"
              :disabled="isAnalyzing"
              class="btn-primary"
            >
              {{ isAnalyzing ? '⏳ Analyzing...' : (pillowReport || gptReport) ? '🔄 Re-analyze' : '🧠 Run Analysis' }}
            </button>
          </div>
        </div>

        <!-- Original Artwork Preview -->
        <div class="card p-4">
          <p class="text-xs font-medium text-surface-500 uppercase mb-2">Original Artwork</p>
          <div
            @click="showLightbox = true"
            class="relative cursor-zoom-in bg-surface-100 dark:bg-surface-800 rounded-lg overflow-hidden flex items-center justify-center"
            style="max-height: 350px;"
          >
            <img
              :src="artworkService.getPreviewUrl(selectedArtwork, 'large')"
              :alt="selectedArtwork.original_filename"
              class="max-h-[350px] object-contain"
              @error="($event.target as HTMLImageElement).src = artworkService.getPreviewUrl(selectedArtwork, 'medium')"
            />
            <div class="absolute bottom-2 right-2 bg-black/60 text-white text-[10px] px-2 py-0.5 rounded">Click to enlarge</div>
          </div>
        </div>

        <!-- Lightbox -->
        <ImageLightbox
          v-if="showLightbox"
          :src="artworkService.getPreviewUrl(selectedArtwork, 'large')"
          :alt="selectedArtwork.original_filename"
          @close="showLightbox = false"
        />

        <!-- Analysis Progress -->
        <div v-if="isAnalyzing" class="card p-6">
          <div class="flex items-center justify-between mb-2">
            <span class="text-sm font-medium text-surface-700 dark:text-surface-300">{{ analysisStep }}</span>
            <span class="animate-pulse text-primary-600">●</span>
          </div>
          <div class="w-full h-2 bg-surface-200 dark:bg-surface-700 rounded-full overflow-hidden">
            <div class="h-full bg-primary-600 rounded-full animate-pulse" style="width: 60%"></div>
          </div>
        </div>

        <!-- Comparison View -->
        <div v-if="viewMode === 'compare' && pillowReport && gptReport && !isAnalyzing" class="space-y-6">
          <!-- Comparison Header -->
          <div class="flex items-center justify-between">
            <h2 class="text-lg font-semibold text-surface-900 dark:text-white">⚔️ Engine Comparison</h2>
            <button @click="saveComparison" class="btn-secondary text-xs">
              💾 Save Comparison
            </button>
          </div>

          <!-- Score Comparison -->
          <div class="grid grid-cols-2 gap-4">
            <div class="card p-5 border-2 border-primary-200 dark:border-primary-800">
              <div class="flex items-center justify-between mb-3">
                <span class="text-sm font-semibold text-primary-700 dark:text-primary-400">🖼️ Pillow (Heuristic)</span>
                <button @click="saveReport(pillowReport!)" class="text-xs text-surface-500 hover:text-primary-600">💾 Save</button>
              </div>
              <div class="grid grid-cols-2 gap-3">
                <div class="text-center">
                  <p class="text-xs text-surface-500">Score</p>
                  <p class="text-2xl font-bold" :class="pillowReport.overall_score! >= 70 ? 'text-green-600' : 'text-yellow-600'">{{ pillowReport.overall_score }}</p>
                </div>
                <div class="text-center">
                  <p class="text-xs text-surface-500">Risk</p>
                  <p class="text-sm font-medium mt-1 capitalize">{{ pillowReport.risk_level }}</p>
                </div>
                <div class="text-center">
                  <p class="text-xs text-surface-500">Type</p>
                  <p class="text-sm font-medium capitalize">{{ pillowReport.visual_analysis?.artwork_type }}</p>
                </div>
                <div class="text-center">
                  <p class="text-xs text-surface-500">Style</p>
                  <p class="text-sm font-medium capitalize">{{ pillowReport.visual_analysis?.artistic_style }}</p>
                </div>
              </div>
            </div>

            <div class="card p-5 border-2 border-emerald-200 dark:border-emerald-800">
              <div class="flex items-center justify-between mb-3">
                <span class="text-sm font-semibold text-emerald-700 dark:text-emerald-400">🧠 GPT-5.5 (AI Vision)</span>
                <button @click="saveReport(gptReport!)" class="text-xs text-surface-500 hover:text-emerald-600">💾 Save</button>
              </div>
              <div class="grid grid-cols-2 gap-3">
                <div class="text-center">
                  <p class="text-xs text-surface-500">Score</p>
                  <p class="text-2xl font-bold" :class="gptReport.overall_score! >= 70 ? 'text-green-600' : 'text-yellow-600'">{{ gptReport.overall_score }}</p>
                </div>
                <div class="text-center">
                  <p class="text-xs text-surface-500">Risk</p>
                  <p class="text-sm font-medium mt-1 capitalize">{{ gptReport.risk_level }}</p>
                </div>
                <div class="text-center">
                  <p class="text-xs text-surface-500">Type</p>
                  <p class="text-sm font-medium capitalize">{{ gptReport.visual_analysis?.artwork_type }}</p>
                </div>
                <div class="text-center">
                  <p class="text-xs text-surface-500">Style</p>
                  <p class="text-sm font-medium capitalize">{{ gptReport.visual_analysis?.artistic_style }}</p>
                </div>
              </div>
            </div>
          </div>

          <!-- Detailed Comparison Table -->
          <div class="card overflow-hidden">
            <table class="w-full text-sm">
              <thead class="bg-surface-50 dark:bg-surface-800">
                <tr>
                  <th class="text-left px-4 py-2 text-xs font-medium text-surface-500">Attribute</th>
                  <th class="text-center px-4 py-2 text-xs font-medium text-primary-600">🖼️ Pillow</th>
                  <th class="text-center px-4 py-2 text-xs font-medium text-emerald-600">🧠 GPT-5.5</th>
                  <th class="text-center px-4 py-2 text-xs font-medium text-surface-500">Match</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-surface-100 dark:divide-surface-800">
                <tr>
                  <td class="px-4 py-2 font-medium">Artwork Type</td>
                  <td class="px-4 py-2 text-center capitalize">{{ pillowReport.visual_analysis?.artwork_type }}</td>
                  <td class="px-4 py-2 text-center capitalize">{{ gptReport.visual_analysis?.artwork_type }}</td>
                  <td class="px-4 py-2 text-center">{{ pillowReport.visual_analysis?.artwork_type === gptReport.visual_analysis?.artwork_type ? '✅' : '❌' }}</td>
                </tr>
                <tr>
                  <td class="px-4 py-2 font-medium">Artistic Style</td>
                  <td class="px-4 py-2 text-center capitalize">{{ pillowReport.visual_analysis?.artistic_style }}</td>
                  <td class="px-4 py-2 text-center capitalize">{{ gptReport.visual_analysis?.artistic_style }}</td>
                  <td class="px-4 py-2 text-center">{{ pillowReport.visual_analysis?.artistic_style === gptReport.visual_analysis?.artistic_style ? '✅' : '❌' }}</td>
                </tr>
                <tr>
                  <td class="px-4 py-2 font-medium">Background</td>
                  <td class="px-4 py-2 text-center capitalize">{{ pillowReport.visual_analysis?.background?.type }}</td>
                  <td class="px-4 py-2 text-center capitalize">{{ gptReport.visual_analysis?.background?.type }}</td>
                  <td class="px-4 py-2 text-center">{{ pillowReport.visual_analysis?.background?.type === gptReport.visual_analysis?.background?.type ? '✅' : '❌' }}</td>
                </tr>
                <tr>
                  <td class="px-4 py-2 font-medium">Has Text</td>
                  <td class="px-4 py-2 text-center">{{ pillowReport.visual_analysis?.typography?.has_text ? 'Yes' : 'No' }}</td>
                  <td class="px-4 py-2 text-center">{{ gptReport.visual_analysis?.typography?.has_text ? 'Yes' : 'No' }}</td>
                  <td class="px-4 py-2 text-center">{{ pillowReport.visual_analysis?.typography?.has_text === gptReport.visual_analysis?.typography?.has_text ? '✅' : '❌' }}</td>
                </tr>
                <tr>
                  <td class="px-4 py-2 font-medium">Color Complexity</td>
                  <td class="px-4 py-2 text-center capitalize">{{ pillowReport.visual_analysis?.color_analysis?.color_complexity }}</td>
                  <td class="px-4 py-2 text-center capitalize">{{ gptReport.visual_analysis?.color_analysis?.color_complexity }}</td>
                  <td class="px-4 py-2 text-center">{{ pillowReport.visual_analysis?.color_analysis?.color_complexity === gptReport.visual_analysis?.color_analysis?.color_complexity ? '✅' : '❌' }}</td>
                </tr>
                <tr>
                  <td class="px-4 py-2 font-medium">Overall Score</td>
                  <td class="px-4 py-2 text-center font-bold">{{ pillowReport.overall_score }}</td>
                  <td class="px-4 py-2 text-center font-bold">{{ gptReport.overall_score }}</td>
                  <td class="px-4 py-2 text-center text-xs text-surface-500">Δ {{ Math.abs((pillowReport.overall_score || 0) - (gptReport.overall_score || 0)) }}</td>
                </tr>
                <tr>
                  <td class="px-4 py-2 font-medium">Risk Level</td>
                  <td class="px-4 py-2 text-center capitalize">{{ pillowReport.risk_level }}</td>
                  <td class="px-4 py-2 text-center capitalize">{{ gptReport.risk_level }}</td>
                  <td class="px-4 py-2 text-center">{{ pillowReport.risk_level === gptReport.risk_level ? '✅' : '❌' }}</td>
                </tr>
                <tr>
                  <td class="px-4 py-2 font-medium">BG Removal Needed</td>
                  <td class="px-4 py-2 text-center">{{ pillowReport.generation_plan?.needs_background_removal ? 'Yes' : 'No' }}</td>
                  <td class="px-4 py-2 text-center">{{ gptReport.generation_plan?.needs_background_removal ? 'Yes' : 'No' }}</td>
                  <td class="px-4 py-2 text-center">{{ pillowReport.generation_plan?.needs_background_removal === gptReport.generation_plan?.needs_background_removal ? '✅' : '❌' }}</td>
                </tr>
                <tr>
                  <td class="px-4 py-2 font-medium">Super Resolution</td>
                  <td class="px-4 py-2 text-center">{{ pillowReport.generation_plan?.needs_super_resolution ? 'Yes' : 'No' }}</td>
                  <td class="px-4 py-2 text-center">{{ gptReport.generation_plan?.needs_super_resolution ? 'Yes' : 'No' }}</td>
                  <td class="px-4 py-2 text-center">{{ pillowReport.generation_plan?.needs_super_resolution === gptReport.generation_plan?.needs_super_resolution ? '✅' : '❌' }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- GPT Quality Notes (if available) -->
          <div v-if="gptReport.visual_analysis?.quality_notes" class="card p-5">
            <h3 class="text-sm font-semibold text-surface-900 dark:text-white mb-2">🧠 GPT-5.5 Quality Assessment</h3>
            <p class="text-sm text-surface-700 dark:text-surface-300 italic">{{ gptReport.visual_analysis.quality_notes }}</p>
          </div>

          <!-- Aspect Ratio Comparison -->
          <div v-if="pillowReport.geometry_analysis?.aspect_ratio && gptReport.geometry_analysis?.aspect_ratio" class="card p-5">
            <h3 class="text-sm font-semibold text-surface-900 dark:text-white mb-1">📐 DTF Aspect Ratio Comparison</h3>
            <div class="flex flex-wrap gap-4 text-xs text-surface-500 mb-4">
              <span>Current: <span class="font-mono font-medium text-surface-800 dark:text-surface-200">{{ pillowReport.geometry_analysis.aspect_ratio.current_ratio_display }}</span> · {{ pillowReport.geometry_analysis.aspect_ratio.current_orientation }}</span>
              <span>Max DTF: <span class="font-medium text-surface-800 dark:text-surface-200">{{ pillowReport.geometry_analysis.aspect_ratio.max_dtf_area }}</span></span>
              <span>Max @300dpi: <span class="font-medium text-surface-800 dark:text-surface-200">{{ pillowReport.geometry_analysis.aspect_ratio.max_print_at_300dpi }}</span></span>
            </div>

            <div class="overflow-auto">
              <table class="w-full text-xs">
                <thead class="bg-surface-50 dark:bg-surface-800">
                  <tr>
                    <th class="text-left px-3 py-2 font-medium text-surface-500">DTF Size</th>
                    <th class="text-center px-3 py-2 font-medium text-surface-500">Print Size</th>
                    <th class="text-center px-3 py-2 font-medium text-primary-600">🖼️ Pillow</th>
                    <th class="text-center px-3 py-2 font-medium text-emerald-600">🧠 GPT</th>
                    <th class="text-center px-3 py-2 font-medium text-surface-500">Δ</th>
                    <th class="text-center px-3 py-2 font-medium text-primary-600">Pillow Status</th>
                    <th class="text-center px-3 py-2 font-medium text-emerald-600">GPT Status</th>
                    <th class="text-center px-3 py-2 font-medium text-surface-500">DPI</th>
                    <th class="text-center px-3 py-2 font-medium text-surface-500">Crop Loss</th>
                    <th class="text-center px-3 py-2 font-medium text-surface-500">AI Expand</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-surface-100 dark:divide-surface-800">
                  <tr
                    v-for="(pillowRec, idx) in pillowReport.geometry_analysis.aspect_ratio.recommendations"
                    :key="pillowRec.name"
                    :class="pillowRec.status === 'not_recommended' && gptReport.geometry_analysis.aspect_ratio.recommendations[idx]?.status === 'not_recommended' ? 'opacity-40' : ''"
                  >
                    <td class="px-3 py-2">
                      <span class="font-medium text-surface-800 dark:text-surface-200">{{ pillowRec.name }}</span>
                      <p class="text-[10px] text-surface-400 mt-0.5">{{ pillowRec.use_cases.slice(0, 2).join(', ') }}</p>
                    </td>
                    <td class="px-3 py-2 text-center font-mono text-surface-700 dark:text-surface-300">{{ pillowRec.max_print_size }}</td>
                    <td class="px-3 py-2 text-center">
                      <span class="font-bold" :class="pillowRec.score >= 80 ? 'text-green-600' : pillowRec.score >= 60 ? 'text-yellow-600' : pillowRec.score >= 35 ? 'text-orange-500' : 'text-red-500'">
                        {{ pillowRec.score }}
                      </span>
                    </td>
                    <td class="px-3 py-2 text-center">
                      <span class="font-bold" :class="(gptReport.geometry_analysis.aspect_ratio.recommendations[idx]?.score || 0) >= 80 ? 'text-green-600' : (gptReport.geometry_analysis.aspect_ratio.recommendations[idx]?.score || 0) >= 60 ? 'text-yellow-600' : (gptReport.geometry_analysis.aspect_ratio.recommendations[idx]?.score || 0) >= 35 ? 'text-orange-500' : 'text-red-500'">
                        {{ gptReport.geometry_analysis.aspect_ratio.recommendations[idx]?.score || '—' }}
                      </span>
                    </td>
                    <td class="px-3 py-2 text-center text-[10px] text-surface-500">
                      {{ Math.abs(pillowRec.score - (gptReport.geometry_analysis.aspect_ratio.recommendations[idx]?.score || 0)) }}
                    </td>
                    <td class="px-3 py-2 text-center">
                      <span :class="[
                        'inline-block px-1.5 py-0.5 rounded text-[10px] font-medium',
                        pillowRec.status === 'recommended' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' :
                        pillowRec.status === 'possible' ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400' :
                        pillowRec.status === 'risky' ? 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400' :
                        'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                      ]">{{ pillowRec.status }}</span>
                    </td>
                    <td class="px-3 py-2 text-center">
                      <span :class="[
                        'inline-block px-1.5 py-0.5 rounded text-[10px] font-medium',
                        gptReport.geometry_analysis.aspect_ratio.recommendations[idx]?.status === 'recommended' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' :
                        gptReport.geometry_analysis.aspect_ratio.recommendations[idx]?.status === 'possible' ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400' :
                        gptReport.geometry_analysis.aspect_ratio.recommendations[idx]?.status === 'risky' ? 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400' :
                        'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                      ]">{{ gptReport.geometry_analysis.aspect_ratio.recommendations[idx]?.status || '—' }}</span>
                    </td>
                    <td class="px-3 py-2 text-center">
                      <span :class="pillowRec.dpi_quality === 'excellent' || pillowRec.dpi_quality === 'good' ? 'text-green-600' : pillowRec.dpi_quality === 'acceptable' ? 'text-yellow-600' : 'text-red-500'">
                        {{ pillowRec.effective_dpi }}
                      </span>
                      <p class="text-[9px] capitalize" :class="pillowRec.dpi_quality === 'excellent' || pillowRec.dpi_quality === 'good' ? 'text-green-500' : 'text-yellow-500'">{{ pillowRec.dpi_quality }}</p>
                    </td>
                    <td class="px-3 py-2 text-center" :class="pillowRec.crop_loss_pct > 20 ? 'text-red-600 font-medium' : 'text-surface-600'">
                      {{ pillowRec.crop_loss_pct }}%
                    </td>
                    <td class="px-3 py-2 text-center" :class="pillowRec.canvas_expand_pct > 30 ? 'text-orange-600 font-medium' : 'text-surface-600'">
                      {{ pillowRec.canvas_expand_pct > 0 ? pillowRec.canvas_expand_pct + '%' : '—' }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Summary -->
            <div class="mt-4 grid grid-cols-2 gap-4">
              <div class="p-3 rounded-lg bg-primary-50 dark:bg-primary-900/10 border border-primary-200 dark:border-primary-800">
                <p class="text-[10px] font-medium text-primary-700 dark:text-primary-400 uppercase">Pillow Summary</p>
                <p class="text-xs text-surface-700 dark:text-surface-300 mt-1">{{ pillowReport.geometry_analysis.aspect_ratio.summary }}</p>
              </div>
              <div class="p-3 rounded-lg bg-emerald-50 dark:bg-emerald-900/10 border border-emerald-200 dark:border-emerald-800">
                <p class="text-[10px] font-medium text-emerald-700 dark:text-emerald-400 uppercase">GPT Summary</p>
                <p class="text-xs text-surface-700 dark:text-surface-300 mt-1">{{ gptReport.geometry_analysis.aspect_ratio.summary }}</p>
              </div>
            </div>
          </div>

          <!-- Full reports expandable -->
          <details class="card">
            <summary class="p-4 cursor-pointer text-sm font-medium text-surface-700 dark:text-surface-300 hover:bg-surface-50 dark:hover:bg-surface-800">
              📄 View Full Pillow Report
            </summary>
            <div class="p-4 border-t border-surface-200 dark:border-surface-800">
              <AnalysisReportView :report="pillowReport" :artwork="selectedArtwork!" />
            </div>
          </details>

          <details class="card">
            <summary class="p-4 cursor-pointer text-sm font-medium text-surface-700 dark:text-surface-300 hover:bg-surface-50 dark:hover:bg-surface-800">
              📄 View Full GPT-5.5 Report
            </summary>
            <div class="p-4 border-t border-surface-200 dark:border-surface-800">
              <AnalysisReportView :report="gptReport" :artwork="selectedArtwork!" />
            </div>
          </details>
        </div>

        <!-- Single Report View -->
        <div v-if="viewMode === 'single' && (pillowReport || gptReport) && !isAnalyzing" class="space-y-4">
          <!-- Save button -->
          <div class="flex justify-end">
            <button
              @click="saveReport(selectedEngine === 'gpt' && gptReport ? gptReport : pillowReport!)"
              class="btn-secondary text-xs"
              v-if="(selectedEngine === 'gpt' ? gptReport : pillowReport)"
            >
              💾 Save Analysis Report
            </button>
          </div>

          <AnalysisReportView
            v-if="selectedEngine === 'gpt' && gptReport"
            :report="gptReport"
            :artwork="selectedArtwork!"
          />
          <AnalysisReportView
            v-else-if="pillowReport"
            :report="pillowReport"
            :artwork="selectedArtwork!"
          />
        </div>

        <!-- No report yet -->
        <div v-if="!pillowReport && !gptReport && !isAnalyzing" class="card p-12 text-center">
          <p class="text-4xl mb-3">🔍</p>
          <h3 class="text-lg font-medium text-surface-900 dark:text-white">No Analysis Available</h3>
          <p class="text-surface-500 mt-1">Choose an engine and click "Run Analysis" to start.</p>
          <p class="text-xs text-surface-400 mt-3">Tip: Use "⚔️ Compare" to run both engines and see differences side-by-side.</p>
        </div>
      </div>
    </div>
  </div>
</template>

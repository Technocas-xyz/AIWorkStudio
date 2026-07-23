<script setup lang="ts">
import { computed } from 'vue'
import type { AnalysisReport } from '@/services/analysis.service'
import type { ArtworkItem } from '@/services/artwork.service'
import AnalysisChatPanel from '@/components/analysis/AnalysisChatPanel.vue'

const props = defineProps<{
  report: AnalysisReport
  artwork: ArtworkItem
}>()

const plan = computed(() => props.report.generation_plan)
const risks = computed(() => props.report.risk_assessment?.risks || [])
const products = computed(() => props.report.product_compatibility || {})
const decisions = computed(() => props.report.decision_plan || {})
const aspectRatio = computed(() => props.report.geometry_analysis?.aspect_ratio || null)

function scoreColor(score: number): string {
  if (score >= 80) return 'text-green-600'
  if (score >= 60) return 'text-yellow-600'
  if (score >= 40) return 'text-orange-600'
  return 'text-red-600'
}

function riskBadge(level: string): string {
  switch (level) {
    case 'minimal': return 'badge-success'
    case 'low': return 'badge-success'
    case 'medium': return 'badge-warning'
    case 'high': return 'badge-danger'
    case 'critical': return 'badge-danger'
    default: return 'badge-info'
  }
}

function severityColor(sev: string): string {
  switch (sev) {
    case 'critical': return 'border-red-500 bg-red-50 dark:bg-red-900/10'
    case 'high': return 'border-orange-500 bg-orange-50 dark:bg-orange-900/10'
    case 'medium': return 'border-yellow-500 bg-yellow-50 dark:bg-yellow-900/10'
    default: return 'border-blue-500 bg-blue-50 dark:bg-blue-900/10'
  }
}
</script>

<template>
  <div class="space-y-6">
    <!-- Overview Cards -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div class="card p-4 text-center">
        <p class="text-xs text-surface-500 uppercase">Overall Score</p>
        <p :class="['text-3xl font-bold mt-1', scoreColor(report.overall_score || 0)]">{{ report.overall_score }}</p>
        <p class="text-xs text-surface-500 mt-1">/ 100</p>
      </div>
      <div class="card p-4 text-center">
        <p class="text-xs text-surface-500 uppercase">Risk Level</p>
        <p class="mt-2"><span :class="riskBadge(report.risk_level || '')">{{ report.risk_level }}</span></p>
      </div>
      <div class="card p-4 text-center">
        <p class="text-xs text-surface-500 uppercase">Artwork Type</p>
        <p class="text-lg font-semibold mt-1 text-surface-800 dark:text-white capitalize">{{ report.visual_analysis?.artwork_type || 'Unknown' }}</p>
      </div>
      <div class="card p-4 text-center">
        <p class="text-xs text-surface-500 uppercase">Recommended</p>
        <p class="text-sm font-medium mt-1 text-surface-800 dark:text-white">{{ plan?.recommended_model || 'N/A' }}</p>
      </div>
    </div>

    <!-- Decision Summary -->
    <div class="card p-5">
      <h3 class="text-sm font-semibold text-surface-900 dark:text-white mb-3">🧠 AI Decisions</h3>
      <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-2">
        <div v-for="(val, key) in decisions" :key="key" class="p-2 rounded-lg border" :class="val.value ? 'border-primary-300 bg-primary-50 dark:bg-primary-900/10' : 'border-surface-200 dark:border-surface-700'">
          <div class="flex items-center gap-1">
            <span class="text-xs">{{ val.value ? '✅' : '⬜' }}</span>
            <span class="text-[10px] font-medium text-surface-700 dark:text-surface-300 capitalize">{{ String(key).replace(/_/g, ' ').replace('needs ', '').replace('preserve ', '🔒 ') }}</span>
          </div>
          <p class="text-[9px] text-surface-500 mt-0.5">{{ Math.round((val.confidence || 0) * 100) }}% confident</p>
        </div>
      </div>
    </div>

    <!-- Production Analysis -->
    <div class="card p-5">
      <h3 class="text-sm font-semibold text-surface-900 dark:text-white mb-3">🏭 Production Analysis</h3>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div>
          <p class="text-xs text-surface-500">Print Size (safe)</p>
          <p class="text-sm font-medium text-surface-800 dark:text-white">{{ report.production_analysis?.safe_print_width_inches }}" × {{ report.production_analysis?.safe_print_height_inches }}"</p>
        </div>
        <div>
          <p class="text-xs text-surface-500">Max Print Size</p>
          <p class="text-sm font-medium text-surface-800 dark:text-white">{{ report.production_analysis?.max_print_width_inches }}" × {{ report.production_analysis?.max_print_height_inches }}"</p>
        </div>
        <div>
          <p class="text-xs text-surface-500">Effective DPI</p>
          <p class="text-sm font-medium text-surface-800 dark:text-white">{{ report.production_analysis?.effective_dpi }}</p>
        </div>
        <div>
          <p class="text-xs text-surface-500">Difficulty</p>
          <p class="text-sm font-medium text-surface-800 dark:text-white capitalize">{{ report.production_analysis?.production_difficulty }}</p>
        </div>
      </div>
    </div>

    <!-- Image Quality Analysis -->
    <div v-if="report.production_analysis?.image_quality" class="card p-5">
      <div class="flex items-center justify-between mb-3">
        <h3 class="text-sm font-semibold text-surface-900 dark:text-white">🔬 Image Quality Analysis</h3>
        <div class="flex items-center gap-2">
          <span class="text-xs text-surface-500">Quality Score:</span>
          <span class="text-lg font-bold" :class="report.production_analysis.image_quality.quality_score >= 80 ? 'text-green-600' : report.production_analysis.image_quality.quality_score >= 55 ? 'text-yellow-600' : 'text-red-600'">
            {{ report.production_analysis.image_quality.quality_score }}/100
          </span>
          <span class="badge text-[10px]" :class="report.production_analysis.image_quality.overall_quality === 'excellent' ? 'badge-success' : report.production_analysis.image_quality.overall_quality === 'good' ? 'badge-success' : report.production_analysis.image_quality.overall_quality === 'fair' ? 'badge-warning' : 'badge-danger'">
            {{ report.production_analysis.image_quality.overall_quality }}
          </span>
        </div>
      </div>

      <!-- Quality Metrics Grid -->
      <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-2 mb-4">
        <div class="p-2 rounded-lg border" :class="report.production_analysis.image_quality.halftone.detected ? 'border-red-300 bg-red-50 dark:bg-red-900/10' : 'border-surface-200 dark:border-surface-700'">
          <p class="text-[10px] font-medium text-surface-500">Halftone</p>
          <p class="text-xs font-semibold" :class="report.production_analysis.image_quality.halftone.detected ? 'text-red-600' : 'text-green-600'">
            {{ report.production_analysis.image_quality.halftone.detected ? '⚠ Detected' : '✓ Clean' }}
          </p>
        </div>
        <div class="p-2 rounded-lg border" :class="report.production_analysis.image_quality.blackout.detected ? 'border-orange-300 bg-orange-50 dark:bg-orange-900/10' : 'border-surface-200 dark:border-surface-700'">
          <p class="text-[10px] font-medium text-surface-500">Blackout</p>
          <p class="text-xs font-semibold" :class="report.production_analysis.image_quality.blackout.detected ? 'text-orange-600' : 'text-green-600'">
            {{ report.production_analysis.image_quality.blackout.detected ? `⚠ ${report.production_analysis.image_quality.blackout.areas_pct}%` : '✓ OK' }}
          </p>
        </div>
        <div class="p-2 rounded-lg border" :class="report.production_analysis.image_quality.noise.detected ? 'border-yellow-300 bg-yellow-50 dark:bg-yellow-900/10' : 'border-surface-200 dark:border-surface-700'">
          <p class="text-[10px] font-medium text-surface-500">Noise</p>
          <p class="text-xs font-semibold" :class="report.production_analysis.image_quality.noise.detected ? 'text-yellow-600' : 'text-green-600'">
            {{ report.production_analysis.image_quality.noise.detected ? `⚠ ${report.production_analysis.image_quality.noise.level}` : '✓ Clean' }}
          </p>
        </div>
        <div class="p-2 rounded-lg border" :class="report.production_analysis.image_quality.blur.detected ? 'border-yellow-300 bg-yellow-50 dark:bg-yellow-900/10' : 'border-surface-200 dark:border-surface-700'">
          <p class="text-[10px] font-medium text-surface-500">Sharpness</p>
          <p class="text-xs font-semibold" :class="report.production_analysis.image_quality.blur.detected ? 'text-yellow-600' : 'text-green-600'">
            {{ report.production_analysis.image_quality.blur.quality || (report.production_analysis.image_quality.blur.detected ? '⚠ Soft' : '✓ Sharp') }}
          </p>
        </div>
        <div class="p-2 rounded-lg border" :class="report.production_analysis.image_quality.banding.detected ? 'border-orange-300 bg-orange-50 dark:bg-orange-900/10' : 'border-surface-200 dark:border-surface-700'">
          <p class="text-[10px] font-medium text-surface-500">Banding</p>
          <p class="text-xs font-semibold" :class="report.production_analysis.image_quality.banding.detected ? 'text-orange-600' : 'text-green-600'">
            {{ report.production_analysis.image_quality.banding.detected ? '⚠ Detected' : '✓ Smooth' }}
          </p>
        </div>
        <div class="p-2 rounded-lg border" :class="report.production_analysis.image_quality.jpeg_artifacts.severity !== 'none' && report.production_analysis.image_quality.jpeg_artifacts.detected ? 'border-yellow-300 bg-yellow-50 dark:bg-yellow-900/10' : 'border-surface-200 dark:border-surface-700'">
          <p class="text-[10px] font-medium text-surface-500">JPEG Artifacts</p>
          <p class="text-xs font-semibold" :class="report.production_analysis.image_quality.jpeg_artifacts.detected && report.production_analysis.image_quality.jpeg_artifacts.severity !== 'none' ? 'text-yellow-600' : 'text-green-600'">
            {{ report.production_analysis.image_quality.jpeg_artifacts.detected && report.production_analysis.image_quality.jpeg_artifacts.severity !== 'none' ? `⚠ ${report.production_analysis.image_quality.jpeg_artifacts.severity}` : '✓ Clean' }}
          </p>
        </div>
        <div class="p-2 rounded-lg border" :class="report.production_analysis.image_quality.posterization.detected ? 'border-orange-300 bg-orange-50 dark:bg-orange-900/10' : 'border-surface-200 dark:border-surface-700'">
          <p class="text-[10px] font-medium text-surface-500">Posterization</p>
          <p class="text-xs font-semibold" :class="report.production_analysis.image_quality.posterization.detected ? 'text-orange-600' : 'text-green-600'">
            {{ report.production_analysis.image_quality.posterization.detected ? '⚠ Detected' : '✓ Smooth' }}
          </p>
        </div>
        <div class="p-2 rounded-lg border" :class="report.production_analysis.image_quality.edge_quality.severity !== 'none' ? 'border-yellow-300 bg-yellow-50 dark:bg-yellow-900/10' : 'border-surface-200 dark:border-surface-700'">
          <p class="text-[10px] font-medium text-surface-500">Edge Quality</p>
          <p class="text-xs font-semibold" :class="report.production_analysis.image_quality.edge_quality.severity !== 'none' ? 'text-yellow-600' : 'text-green-600'">
            {{ report.production_analysis.image_quality.edge_quality.halos ? '⚠ Halos' : report.production_analysis.image_quality.edge_quality.jagged ? '⚠ Jagged' : '✓ Clean' }}
          </p>
        </div>
        <div class="p-2 rounded-lg border border-surface-200 dark:border-surface-700">
          <p class="text-[10px] font-medium text-surface-500">Contrast</p>
          <p class="text-xs font-semibold text-surface-700 dark:text-surface-300 capitalize">{{ report.production_analysis.image_quality.contrast.level?.replace('_', ' ') }}</p>
        </div>
        <div class="p-2 rounded-lg border border-surface-200 dark:border-surface-700">
          <p class="text-[10px] font-medium text-surface-500">Saturation</p>
          <p class="text-xs font-semibold text-surface-700 dark:text-surface-300 capitalize">{{ report.production_analysis.image_quality.saturation.level?.replace('_', ' ') }}</p>
        </div>
        <div class="p-2 rounded-lg border border-surface-200 dark:border-surface-700">
          <p class="text-[10px] font-medium text-surface-500">Dynamic Range</p>
          <p class="text-xs font-semibold text-surface-700 dark:text-surface-300 capitalize">{{ report.production_analysis.image_quality.dynamic_range.quality }} ({{ report.production_analysis.image_quality.dynamic_range.range }})</p>
        </div>
        <div class="p-2 rounded-lg border" :class="report.production_analysis.image_quality.whiteout.detected ? 'border-yellow-300 bg-yellow-50 dark:bg-yellow-900/10' : 'border-surface-200 dark:border-surface-700'">
          <p class="text-[10px] font-medium text-surface-500">Whiteout</p>
          <p class="text-xs font-semibold" :class="report.production_analysis.image_quality.whiteout.detected ? 'text-yellow-600' : 'text-green-600'">
            {{ report.production_analysis.image_quality.whiteout.detected ? `⚠ ${report.production_analysis.image_quality.whiteout.areas_pct}%` : '✓ OK' }}
          </p>
        </div>
      </div>

      <!-- Issues List -->
      <div v-if="report.production_analysis.image_quality.issues && report.production_analysis.image_quality.issues.length > 0">
        <p class="text-xs font-medium text-surface-600 dark:text-surface-400 mb-2">Detected Issues:</p>
        <div class="space-y-1.5">
          <div v-for="(issue, idx) in report.production_analysis.image_quality.issues" :key="idx" class="flex items-start gap-2 text-xs">
            <span :class="issue.severity === 'critical' || issue.severity === 'high' ? 'text-red-500' : issue.severity === 'medium' ? 'text-orange-500' : 'text-yellow-500'">●</span>
            <div>
              <span class="font-medium text-surface-800 dark:text-surface-200">{{ issue.title }}:</span>
              <span class="text-surface-600 dark:text-surface-400 ml-1">{{ issue.detail }}</span>
            </div>
          </div>
        </div>
      </div>
      <p v-else class="text-xs text-green-600 mt-2">✓ No quality issues detected — image is production-ready.</p>
    </div>

    <!-- Risk Assessment -->
    <div v-if="risks.length > 0" class="card p-5">
      <h3 class="text-sm font-semibold text-surface-900 dark:text-white mb-3">⚠️ Risk Assessment ({{ risks.length }} issues)</h3>
      <div class="space-y-2">
        <div v-for="risk in risks" :key="risk.id" :class="['border-l-4 p-3 rounded-r-lg', severityColor(risk.severity)]">
          <div class="flex items-center gap-2">
            <span :class="riskBadge(risk.severity)" class="text-[10px]">{{ risk.severity }}</span>
            <span class="text-sm font-medium text-surface-800 dark:text-surface-200">{{ risk.title }}</span>
          </div>
          <p class="text-xs text-surface-600 dark:text-surface-400 mt-1">{{ risk.description }}</p>
          <p class="text-xs text-surface-500 mt-1">💡 {{ risk.recommendation }}</p>
        </div>
      </div>
    </div>

    <!-- Product Compatibility -->
    <div class="card p-5">
      <h3 class="text-sm font-semibold text-surface-900 dark:text-white mb-3">🎯 Product Compatibility</h3>
      <div class="grid grid-cols-2 md:grid-cols-5 gap-2">
        <div v-for="(prod, key) in products" :key="key" class="p-2 rounded-lg border border-surface-200 dark:border-surface-700 text-center">
          <p class="text-[10px] font-medium text-surface-700 dark:text-surface-300">{{ prod.product }}</p>
          <p class="text-lg font-bold mt-0.5" :class="prod.status === 'recommended' ? 'text-green-600' : prod.status === 'compatible' ? 'text-yellow-600' : 'text-red-500'">
            {{ prod.status === 'recommended' ? '✓' : prod.status === 'compatible' ? '~' : '✗' }}
          </p>
          <p class="text-[9px] text-surface-500 capitalize">{{ prod.status }}</p>
        </div>
      </div>
    </div>

    <!-- Aspect Ratio Recommendations -->
    <div v-if="aspectRatio" class="card p-5">
      <h3 class="text-sm font-semibold text-surface-900 dark:text-white mb-1">📐 DTF Aspect Ratio Intelligence</h3>
      <div class="flex flex-wrap gap-4 text-xs text-surface-500 mb-4">
        <span>Current: <span class="font-mono font-medium text-surface-800 dark:text-surface-200">{{ aspectRatio.current_ratio_display }}</span> · {{ aspectRatio.current_orientation }}</span>
        <span>Max DTF: <span class="font-medium text-surface-800 dark:text-surface-200">{{ aspectRatio.max_dtf_area }}</span></span>
        <span>Max Print @300dpi: <span class="font-medium text-surface-800 dark:text-surface-200">{{ aspectRatio.max_print_at_300dpi }}</span></span>
        <span>Best: <span class="font-medium text-green-600">{{ aspectRatio.best_match }}</span></span>
      </div>
      <p class="text-xs italic text-surface-500 mb-3">{{ aspectRatio.summary }}</p>

      <!-- DTF Ratio recommendation grid -->
      <div class="overflow-auto">
        <table class="w-full text-xs">
          <thead class="bg-surface-50 dark:bg-surface-800">
            <tr>
              <th class="text-left px-3 py-2 font-medium text-surface-500">DTF Size</th>
              <th class="text-center px-3 py-2 font-medium text-surface-500">Print Size</th>
              <th class="text-center px-3 py-2 font-medium text-surface-500">Score</th>
              <th class="text-center px-3 py-2 font-medium text-surface-500">Status</th>
              <th class="text-center px-3 py-2 font-medium text-surface-500">DPI</th>
              <th class="text-center px-3 py-2 font-medium text-surface-500">Crop Loss</th>
              <th class="text-center px-3 py-2 font-medium text-surface-500">AI Expand</th>
              <th class="text-left px-3 py-2 font-medium text-surface-500">Method</th>
              <th class="text-left px-3 py-2 font-medium text-surface-500">Risks</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-surface-100 dark:divide-surface-800">
            <tr v-for="rec in aspectRatio.recommendations" :key="rec.name"
                :class="rec.status === 'not_recommended' ? 'opacity-50' : ''">
              <td class="px-3 py-2">
                <span class="font-medium text-surface-800 dark:text-surface-200">{{ rec.name }}</span>
                <p class="text-[10px] text-surface-400 mt-0.5">{{ rec.use_cases.slice(0, 2).join(', ') }}</p>
              </td>
              <td class="px-3 py-2 text-center font-mono text-surface-700 dark:text-surface-300">{{ rec.max_print_size }}</td>
              <td class="px-3 py-2 text-center">
                <span class="font-bold" :class="rec.score >= 80 ? 'text-green-600' : rec.score >= 60 ? 'text-yellow-600' : rec.score >= 35 ? 'text-orange-500' : 'text-red-500'">
                  {{ rec.score }}
                </span>
              </td>
              <td class="px-3 py-2 text-center">
                <span :class="[
                  'inline-block px-1.5 py-0.5 rounded text-[10px] font-medium',
                  rec.status === 'recommended' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' :
                  rec.status === 'possible' ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400' :
                  rec.status === 'risky' ? 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400' :
                  'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                ]">{{ rec.status }}</span>
              </td>
              <td class="px-3 py-2 text-center">
                <span :class="rec.dpi_quality === 'excellent' ? 'text-green-600' : rec.dpi_quality === 'good' ? 'text-green-500' : rec.dpi_quality === 'acceptable' ? 'text-yellow-600' : 'text-red-500'">
                  {{ rec.effective_dpi }}
                </span>
                <p class="text-[9px] capitalize" :class="rec.dpi_quality === 'excellent' || rec.dpi_quality === 'good' ? 'text-green-500' : rec.dpi_quality === 'acceptable' ? 'text-yellow-500' : 'text-red-400'">{{ rec.dpi_quality }}</p>
              </td>
              <td class="px-3 py-2 text-center">
                <span v-if="rec.crop_loss_pct > 0" :class="rec.crop_loss_pct > 20 ? 'text-red-600 font-medium' : 'text-surface-600'">
                  {{ rec.crop_loss_pct }}%
                </span>
                <span v-else class="text-green-600">0%</span>
              </td>
              <td class="px-3 py-2 text-center">
                <span v-if="rec.canvas_expand_pct > 0" :class="rec.canvas_expand_pct > 30 ? 'text-orange-600 font-medium' : 'text-surface-600'">
                  {{ rec.canvas_expand_pct }}%
                </span>
                <span v-else class="text-green-600">—</span>
              </td>
              <td class="px-3 py-2 text-surface-600 dark:text-surface-400">
                {{ rec.method }}
              </td>
              <td class="px-3 py-2">
                <div v-if="rec.risks.length > 0" class="space-y-0.5">
                  <p v-for="(risk, i) in rec.risks" :key="i" class="text-[10px] text-red-600 dark:text-red-400">⚠ {{ risk }}</p>
                </div>
                <span v-else class="text-green-600 text-[10px]">✓ Safe</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Analysis Chat -->
    <AnalysisChatPanel
      v-if="report.job_id"
      :job-id="report.job_id"
      :artwork-name="artwork.original_filename"
    />

    <!-- Generation Plan JSON -->
    <div class="card p-5">
      <h3 class="text-sm font-semibold text-surface-900 dark:text-white mb-3">📋 Generation Plan (Module 4 Input)</h3>
      <pre class="text-xs bg-surface-50 dark:bg-surface-800 p-4 rounded-lg overflow-auto max-h-64 font-mono text-surface-700 dark:text-surface-300">{{ JSON.stringify(plan, null, 2) }}</pre>
    </div>
  </div>
</template>

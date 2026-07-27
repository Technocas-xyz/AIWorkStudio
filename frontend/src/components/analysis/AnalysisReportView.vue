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

    <!-- Pixel Geometry -->
    <div class="card p-5">
      <h3 class="text-sm font-semibold text-surface-900 dark:text-white mb-3">📏 Pixel Geometry</h3>
      <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
        <div class="p-2 bg-surface-50 dark:bg-surface-800 rounded-lg">
          <p class="text-[10px] text-surface-500">Width</p>
          <p class="text-sm font-bold text-surface-800 dark:text-white">{{ (artwork.width / (report.file_inspection?.dpi || 72)).toFixed(2) }}"</p>
          <p class="text-[9px] text-surface-400">{{ artwork.width }}px</p>
        </div>
        <div class="p-2 bg-surface-50 dark:bg-surface-800 rounded-lg">
          <p class="text-[10px] text-surface-500">Height</p>
          <p class="text-sm font-bold text-surface-800 dark:text-white">{{ (artwork.height / (report.file_inspection?.dpi || 72)).toFixed(2) }}"</p>
          <p class="text-[9px] text-surface-400">{{ artwork.height }}px</p>
        </div>
        <div class="p-2 bg-surface-50 dark:bg-surface-800 rounded-lg">
          <p class="text-[10px] text-surface-500">Aspect Ratio</p>
          <p class="text-sm font-bold text-primary-600">{{ report.geometry_analysis?.aspect_ratio?.current_ratio_display || '—' }}</p>
          <p class="text-[9px] text-surface-500">{{ report.geometry_analysis?.aspect_ratio?.current_category }}</p>
        </div>
        <div class="p-2 bg-surface-50 dark:bg-surface-800 rounded-lg">
          <p class="text-[10px] text-surface-500">Orientation</p>
          <p class="text-sm font-bold text-surface-800 dark:text-white">{{ report.geometry_analysis?.aspect_ratio?.current_orientation || report.geometry_analysis?.aspect_ratio?.current_orientation || '—' }}</p>
        </div>
        <div class="p-2 bg-surface-50 dark:bg-surface-800 rounded-lg">
          <p class="text-[10px] text-surface-500">DPI</p>
          <p class="text-sm font-bold text-surface-800 dark:text-white">{{ report.file_inspection?.dpi || '72' }}</p>
        </div>
        <div class="p-2 bg-surface-50 dark:bg-surface-800 rounded-lg">
          <p class="text-[10px] text-surface-500">Color Space</p>
          <p class="text-sm font-bold text-surface-800 dark:text-white">{{ report.file_inspection?.color_space || '—' }}</p>
        </div>
        <div class="p-2 bg-surface-50 dark:bg-surface-800 rounded-lg">
          <p class="text-[10px] text-surface-500">Bit Depth</p>
          <p class="text-sm font-bold text-surface-800 dark:text-white">{{ report.file_inspection?.bit_depth ? report.file_inspection.bit_depth + '-bit' : '—' }}</p>
        </div>
        <div class="p-2 bg-surface-50 dark:bg-surface-800 rounded-lg">
          <p class="text-[10px] text-surface-500">Alpha Channel</p>
          <p class="text-sm font-bold" :class="report.file_inspection?.has_alpha ? 'text-green-600' : 'text-red-500'">{{ report.file_inspection?.has_alpha ? 'Yes' : 'No' }}</p>
        </div>
        <div class="p-2 bg-surface-50 dark:bg-surface-800 rounded-lg">
          <p class="text-[10px] text-surface-500">Transparency</p>
          <p class="text-sm font-bold" :class="report.file_inspection?.has_transparency ? 'text-green-600' : 'text-surface-600'">{{ report.file_inspection?.has_transparency ? 'Yes' : 'No' }}</p>
        </div>
        <div class="p-2 bg-surface-50 dark:bg-surface-800 rounded-lg">
          <p class="text-[10px] text-surface-500">ICC Profile</p>
          <p class="text-sm font-bold text-surface-800 dark:text-white capitalize">{{ report.file_inspection?.icc_profile || '—' }}</p>
        </div>
        <div class="p-2 bg-surface-50 dark:bg-surface-800 rounded-lg">
          <p class="text-[10px] text-surface-500">Format</p>
          <p class="text-sm font-bold text-surface-800 dark:text-white">{{ report.file_inspection?.file_format || artwork.extension?.toUpperCase() }}</p>
        </div>
        <div class="p-2 bg-surface-50 dark:bg-surface-800 rounded-lg">
          <p class="text-[10px] text-surface-500">Compression</p>
          <p class="text-sm font-bold text-surface-800 dark:text-white capitalize">{{ report.file_inspection?.compression || '—' }}</p>
        </div>
      </div>

      <!-- Geometry Details -->
      <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3 mt-3 pt-3 border-t border-surface-200 dark:border-surface-700">
        <div class="p-2 bg-surface-50 dark:bg-surface-800 rounded-lg">
          <p class="text-[10px] text-surface-500">Subject Coverage</p>
          <p class="text-sm font-bold text-surface-800 dark:text-white">{{ report.geometry_analysis?.subject_coverage_pct?.toFixed(1) || '100' }}%</p>
        </div>
        <div class="p-2 bg-surface-50 dark:bg-surface-800 rounded-lg">
          <p class="text-[10px] text-surface-500">Empty Space</p>
          <p class="text-sm font-bold text-surface-800 dark:text-white">{{ report.geometry_analysis?.empty_space_pct?.toFixed(1) || '0' }}%</p>
        </div>
        <div class="p-2 bg-surface-50 dark:bg-surface-800 rounded-lg">
          <p class="text-[10px] text-surface-500">Transparent Area</p>
          <p class="text-sm font-bold text-surface-800 dark:text-white">{{ report.geometry_analysis?.transparent_area_pct?.toFixed(1) || '0' }}%</p>
        </div>
        <div class="p-2 bg-surface-50 dark:bg-surface-800 rounded-lg">
          <p class="text-[10px] text-surface-500">Subject Centered</p>
          <p class="text-sm font-bold" :class="report.geometry_analysis?.subject_centered ? 'text-green-600' : 'text-yellow-600'">{{ report.geometry_analysis?.subject_centered ? 'Yes' : 'No' }}</p>
        </div>
        <div class="p-2 bg-surface-50 dark:bg-surface-800 rounded-lg">
          <p class="text-[10px] text-surface-500">Cropping Risk</p>
          <p class="text-sm font-bold" :class="report.geometry_analysis?.cropping_risk ? 'text-red-500' : 'text-green-600'">{{ report.geometry_analysis?.cropping_risk ? 'Yes' : 'No' }}</p>
        </div>
        <div class="p-2 bg-surface-50 dark:bg-surface-800 rounded-lg">
          <p class="text-[10px] text-surface-500">Safe Margins</p>
          <p class="text-[10px] font-mono text-surface-700 dark:text-surface-300" v-if="report.geometry_analysis?.safe_margins">
            T:{{ report.geometry_analysis.safe_margins.top }} R:{{ report.geometry_analysis.safe_margins.right }} B:{{ report.geometry_analysis.safe_margins.bottom }} L:{{ report.geometry_analysis.safe_margins.left }}
          </p>
          <p v-else class="text-sm text-surface-500">—</p>
        </div>
      </div>

      <!-- Edge Contact -->
      <div v-if="report.geometry_analysis?.edge_contact" class="flex items-center gap-3 mt-3 pt-3 border-t border-surface-200 dark:border-surface-700">
        <span class="text-[10px] text-surface-500">Edge Contact:</span>
        <span v-for="(val, side) in report.geometry_analysis.edge_contact" :key="side"
          :class="['text-[10px] px-1.5 py-0.5 rounded font-medium', val ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' : 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400']">
          {{ side }}: {{ val ? '⚠ Yes' : '✓ No' }}
        </span>
      </div>
    </div>

    <!-- GPT Production Intelligence (only shown when GPT analysis is available) -->
    <div v-if="report.visual_analysis?.production_intelligence" class="card p-5">
      <h3 class="text-sm font-semibold text-surface-900 dark:text-white mb-3">🏭 Production Intelligence (GPT)</h3>
      <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
        <div class="p-2 bg-surface-50 dark:bg-surface-800 rounded-lg">
          <p class="text-[10px] text-surface-500">Complexity</p>
          <p class="text-sm font-bold text-surface-800 dark:text-white">{{ report.visual_analysis.production_intelligence.complexity_score }}/10</p>
          <p class="text-[9px] text-surface-500">{{ report.visual_analysis.production_intelligence.complexity_reason }}</p>
        </div>
        <div class="p-2 bg-surface-50 dark:bg-surface-800 rounded-lg">
          <p class="text-[10px] text-surface-500">White Ink Needed</p>
          <p class="text-sm font-bold text-surface-800 dark:text-white">{{ report.visual_analysis.production_intelligence.white_ink_percentage }}%</p>
        </div>
        <div class="p-2 bg-surface-50 dark:bg-surface-800 rounded-lg">
          <p class="text-[10px] text-surface-500">Weeding Difficulty</p>
          <p class="text-sm font-bold text-surface-800 dark:text-white capitalize">{{ report.visual_analysis.production_intelligence.weeding_difficulty }}</p>
        </div>
        <div class="p-2 bg-surface-50 dark:bg-surface-800 rounded-lg">
          <p class="text-[10px] text-surface-500">Recommended Size</p>
          <p class="text-sm font-bold text-surface-800 dark:text-white">{{ report.visual_analysis.production_intelligence.recommended_size_inches }}</p>
        </div>
        <div class="p-2 bg-surface-50 dark:bg-surface-800 rounded-lg col-span-2">
          <p class="text-[10px] text-surface-500">Recommended Placement</p>
          <div class="flex flex-wrap gap-1 mt-1">
            <span v-for="p in (report.visual_analysis.production_intelligence.recommended_placement || [])" :key="p" class="text-[10px] px-1.5 py-0.5 rounded bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-400">{{ p.replace('_', ' ') }}</span>
          </div>
        </div>
        <div class="p-2 bg-surface-50 dark:bg-surface-800 rounded-lg">
          <p class="text-[10px] text-surface-500">Target Audience</p>
          <p class="text-xs text-surface-700 dark:text-surface-300">{{ report.visual_analysis.production_intelligence.target_audience }}</p>
        </div>
        <div class="p-2 bg-surface-50 dark:bg-surface-800 rounded-lg">
          <p class="text-[10px] text-surface-500">Seasonal</p>
          <p class="text-xs text-surface-700 dark:text-surface-300">{{ report.visual_analysis.production_intelligence.seasonal_relevance }}</p>
        </div>
      </div>
      <div v-if="report.visual_analysis.production_intelligence.production_notes" class="mt-3 p-3 bg-blue-50 dark:bg-blue-900/10 rounded-lg border border-blue-200 dark:border-blue-800">
        <p class="text-[10px] font-medium text-blue-700 dark:text-blue-400 uppercase">Production Notes</p>
        <p class="text-xs text-surface-700 dark:text-surface-300 mt-1">{{ report.visual_analysis.production_intelligence.production_notes }}</p>
      </div>
    </div>

    <!-- OCR / Typography (GPT) -->
    <div v-if="report.visual_analysis?.typography?.detected_text" class="card p-5">
      <h3 class="text-sm font-semibold text-surface-900 dark:text-white mb-3">📝 Text Detection (OCR)</h3>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <p class="text-[10px] text-surface-500 uppercase mb-1">Detected Text</p>
          <p class="text-sm text-surface-800 dark:text-surface-200 font-mono bg-surface-50 dark:bg-surface-800 p-2 rounded">{{ report.visual_analysis.typography.detected_text || 'None' }}</p>
        </div>
        <div class="space-y-2">
          <div class="flex justify-between text-xs">
            <span class="text-surface-500">Language</span>
            <span class="font-medium text-surface-800 dark:text-white">{{ report.visual_analysis.typography.language || '—' }}</span>
          </div>
          <div class="flex justify-between text-xs">
            <span class="text-surface-500">Text Blocks</span>
            <span class="font-medium text-surface-800 dark:text-white">{{ report.visual_analysis.typography.text_blocks }}</span>
          </div>
          <div class="flex justify-between text-xs">
            <span class="text-surface-500">Font Complexity</span>
            <span class="font-medium text-surface-800 dark:text-white capitalize">{{ report.visual_analysis.typography.font_complexity }}</span>
          </div>
          <div class="flex justify-between text-xs">
            <span class="text-surface-500">Curved Text</span>
            <span class="font-medium" :class="report.visual_analysis.typography.curved_text ? 'text-yellow-600' : 'text-green-600'">{{ report.visual_analysis.typography.curved_text ? 'Yes' : 'No' }}</span>
          </div>
          <div v-if="report.visual_analysis.typography.spelling_issues" class="flex justify-between text-xs">
            <span class="text-surface-500">Spelling Issues</span>
            <span class="font-medium text-red-600">{{ report.visual_analysis.typography.spelling_issues }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Color Analysis (GPT) -->
    <div v-if="report.visual_analysis?.color_analysis?.dominant_colors?.length > 0 && report.visual_analysis?.color_analysis?.dominant_colors[0]?.startsWith?.('#')" class="card p-5">
      <h3 class="text-sm font-semibold text-surface-900 dark:text-white mb-3">🎨 Color Analysis (GPT)</h3>
      <div class="flex items-center gap-2 mb-3">
        <div v-for="color in report.visual_analysis.color_analysis.dominant_colors" :key="color"
          class="w-8 h-8 rounded-lg border border-surface-200 dark:border-surface-700" :style="{backgroundColor: color}" :title="color"></div>
        <span class="text-[10px] text-surface-500 ml-2">{{ report.visual_analysis.color_analysis.color_count_estimate }} colors estimated</span>
      </div>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div class="text-xs"><span class="text-surface-500">Complexity:</span> <span class="font-medium capitalize">{{ report.visual_analysis.color_analysis.color_complexity }}</span></div>
        <div class="text-xs"><span class="text-surface-500">Tone:</span> <span class="font-medium capitalize">{{ report.visual_analysis.color_analysis.dominant_tone }}</span></div>
        <div class="text-xs"><span class="text-surface-500">Monochrome:</span> <span class="font-medium">{{ report.visual_analysis.color_analysis.is_monochrome ? 'Yes' : 'No' }}</span></div>
        <div v-if="report.visual_analysis.color_analysis.pantone_suggestions?.length" class="text-xs"><span class="text-surface-500">Pantone:</span> <span class="font-medium">{{ report.visual_analysis.color_analysis.pantone_suggestions.join(', ') }}</span></div>
      </div>
    </div>

    <!-- Color Separation -->
    <div v-if="report.visual_analysis?.color_separation" class="card p-5">
      <h3 class="text-sm font-semibold text-surface-900 dark:text-white mb-3">🔬 Color Separation</h3>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div class="p-2 bg-surface-50 dark:bg-surface-800 rounded-lg text-center">
          <p class="text-[10px] text-surface-500">Spot Colors</p>
          <p class="text-sm font-bold text-surface-800 dark:text-white">{{ report.visual_analysis.color_separation.estimated_spot_colors }}</p>
        </div>
        <div class="p-2 bg-surface-50 dark:bg-surface-800 rounded-lg text-center">
          <p class="text-[10px] text-surface-500">Spot Possible</p>
          <p class="text-sm font-bold" :class="report.visual_analysis.color_separation.spot_colors_possible ? 'text-green-600' : 'text-red-500'">{{ report.visual_analysis.color_separation.spot_colors_possible ? 'Yes' : 'No' }}</p>
        </div>
        <div class="p-2 bg-surface-50 dark:bg-surface-800 rounded-lg text-center">
          <p class="text-[10px] text-surface-500">CMYK Safe</p>
          <p class="text-sm font-bold" :class="report.visual_analysis.color_separation.cmyk_suitable ? 'text-green-600' : 'text-yellow-600'">{{ report.visual_analysis.color_separation.cmyk_suitable ? 'Yes' : 'Caution' }}</p>
        </div>
        <div class="p-2 bg-surface-50 dark:bg-surface-800 rounded-lg text-center">
          <p class="text-[10px] text-surface-500">Needs White Base</p>
          <p class="text-sm font-bold" :class="report.visual_analysis.color_separation.needs_white_base ? 'text-yellow-600' : 'text-green-600'">{{ report.visual_analysis.color_separation.needs_white_base ? 'Yes' : 'No' }}</p>
        </div>
      </div>
    </div>

    <!-- Copyright Flags -->
    <div v-if="report.visual_analysis?.copyright_flags?.has_known_brands || report.visual_analysis?.copyright_flags?.has_known_characters" class="card p-5 border-l-4 border-red-500">
      <h3 class="text-sm font-semibold text-red-600 mb-2">⚠️ Copyright / Trademark Warning</h3>
      <p class="text-xs text-surface-700 dark:text-surface-300">{{ report.visual_analysis.copyright_flags.details }}</p>
    </div>

    <!-- Product Description -->
    <div v-if="report.visual_analysis?.product_description" class="card p-5">
      <h3 class="text-sm font-semibold text-surface-900 dark:text-white mb-2">🏷️ Auto-Generated Product Description</h3>
      <p class="text-sm text-surface-700 dark:text-surface-300 italic">{{ report.visual_analysis.product_description }}</p>
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

    <!-- Print Readiness -->
    <div v-if="report.production_analysis?.print_readiness" class="card p-5">
      <div class="flex items-center justify-between mb-3">
        <h3 class="text-sm font-semibold text-surface-900 dark:text-white">🖨️ Print Readiness</h3>
        <span class="text-xs text-surface-500">
          {{ report.production_analysis.print_readiness.summary?.ready_count }}/{{ report.production_analysis.print_readiness.summary?.total_methods }} methods ready
          · Best: <span class="font-medium text-green-600">{{ report.production_analysis.print_readiness.summary?.best_method }}</span>
        </span>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        <div v-for="(method, key) in report.production_analysis.print_readiness.print_methods" :key="key"
          :class="['p-3 rounded-lg border', method.ready ? 'border-green-200 bg-green-50 dark:bg-green-900/10 dark:border-green-800' : method.status === 'needs_work' ? 'border-yellow-200 bg-yellow-50 dark:bg-yellow-900/10 dark:border-yellow-800' : 'border-red-200 bg-red-50 dark:bg-red-900/10 dark:border-red-800']">
          <div class="flex items-center justify-between mb-1.5">
            <span class="text-xs font-semibold text-surface-800 dark:text-surface-200">{{ method.method_name }}</span>
            <span :class="['text-[10px] font-bold px-1.5 py-0.5 rounded', method.ready ? 'bg-green-200 text-green-800' : method.status === 'needs_work' ? 'bg-yellow-200 text-yellow-800' : 'bg-red-200 text-red-800']">
              {{ method.ready ? '✓ READY' : method.status === 'needs_work' ? '⚠ FIXABLE' : '✗ N/A' }}
            </span>
          </div>
          <div class="flex items-center gap-2 mb-2">
            <div class="flex-1 h-1.5 bg-surface-200 dark:bg-surface-700 rounded-full overflow-hidden">
              <div :class="['h-full rounded-full', method.score >= 80 ? 'bg-green-500' : method.score >= 50 ? 'bg-yellow-500' : 'bg-red-500']" :style="{width: method.score + '%'}"></div>
            </div>
            <span class="text-[10px] font-medium text-surface-600">{{ method.score }}%</span>
          </div>

          <!-- Issues -->
          <div v-if="method.issues.length > 0" class="space-y-0.5 mb-2">
            <p v-for="(issue, i) in method.issues" :key="i" class="text-[10px] text-red-600 dark:text-red-400">✗ {{ issue }}</p>
          </div>

          <!-- Fixes -->
          <div v-if="method.fixes.length > 0" class="space-y-0.5">
            <p v-for="(fix, i) in method.fixes" :key="i" class="text-[10px] text-primary-600 dark:text-primary-400">💡 {{ fix }}</p>
          </div>

          <!-- All good -->
          <p v-if="method.ready && method.issues.length === 0" class="text-[10px] text-green-600">✓ Ready for production</p>

          <p class="text-[9px] text-surface-400 mt-1.5 italic">{{ method.notes }}</p>
        </div>
      </div>
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

import api from './api'
import type { APIResponse } from '@/types'

export interface AnalysisJob {
  job_id: string
  artwork_id: string
  status: string
  progress: number
  current_step: string
  version: number
  started_at?: string
  completed_at?: string
  duration_seconds?: number
  error?: string
}

export interface AnalysisReport {
  id: string
  job_id: string
  artwork_id: string
  version: number
  overall_score: number
  risk_level: string
  file_inspection: any
  visual_analysis: any
  geometry_analysis: any
  production_analysis: any
  product_compatibility: any
  risk_assessment: any
  decision_plan: any
  generation_plan: any
}

export const analysisService = {
  async startAnalysis(artworkId: string, engine: string = 'pillow'): Promise<AnalysisJob> {
    const response = await api.post<APIResponse<AnalysisJob>>('/analysis/start', { artwork_id: artworkId, engine })
    return response.data.data!
  },

  async getJob(jobId: string): Promise<AnalysisJob> {
    const response = await api.get<APIResponse<AnalysisJob>>(`/analysis/${jobId}`)
    return response.data.data!
  },

  async getReport(jobId: string): Promise<AnalysisReport> {
    const response = await api.get<APIResponse<AnalysisReport>>(`/analysis/${jobId}/report`)
    return response.data.data!
  },

  async getPlan(jobId: string): Promise<any> {
    const response = await api.get<APIResponse<any>>(`/analysis/${jobId}/plan`)
    return response.data.data!
  },

  async getLatestForArtwork(artworkId: string): Promise<AnalysisReport | null> {
    const response = await api.get<APIResponse<AnalysisReport>>(`/analysis/artwork/${artworkId}/latest`)
    return response.data.data || null
  },
}

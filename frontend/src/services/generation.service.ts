import api from './api'
import type { APIResponse } from '@/types'

export interface GenerationJob {
  job_id: string
  status: string
  progress: number
  current_step: string
  model_name: string
  mode: string
  duration_seconds?: number
  error?: string
  candidate?: Candidate
}

export interface Candidate {
  id: string
  candidate_number: number
  model_name: string
  storage_path: string
  file_size: number
  width: number
  height: number
  similarity_score: number
  quality_score: number
  status: string
  post_processed: boolean
}

export interface AIModelInfo {
  name: string
  display_name: string
  provider: string
  is_available: boolean
  supported_modes: string[]
  max_resolution: number
}

export const generationService = {
  async startGeneration(artworkId: string, modelName: string = 'gpt_image', mode: string = 'enhancement',
                        operations: Record<string, boolean> = {}, targetRatio: string = '', customInstructions: string = ''): Promise<GenerationJob> {
    const response = await api.post<APIResponse<GenerationJob>>('/generation/start', {
      artwork_id: artworkId, model_name: modelName, mode,
      operations, target_ratio: targetRatio, custom_instructions: customInstructions,
    })
    return response.data.data!
  },

  async getJob(jobId: string): Promise<GenerationJob> {
    const response = await api.get<APIResponse<GenerationJob>>(`/generation/${jobId}`)
    return response.data.data!
  },

  async getCandidates(jobId: string): Promise<Candidate[]> {
    const response = await api.get<APIResponse<Candidate[]>>(`/generation/${jobId}/candidates`)
    return response.data.data!
  },

  async approve(jobId: string, candidateId: string): Promise<any> {
    const response = await api.post<APIResponse>(`/generation/${jobId}/approve`, { candidate_id: candidateId })
    return response.data.data
  },

  async reject(jobId: string, candidateId: string): Promise<void> {
    await api.post(`/generation/${jobId}/reject`, { candidate_id: candidateId })
  },

  async retry(jobId: string): Promise<GenerationJob> {
    const response = await api.post<APIResponse<GenerationJob>>(`/generation/${jobId}/retry`)
    return response.data.data!
  },

  async cancel(jobId: string): Promise<void> {
    await api.post(`/generation/${jobId}/cancel`)
  },

  async getModels(): Promise<AIModelInfo[]> {
    const response = await api.get<APIResponse<AIModelInfo[]>>('/generation/models/list')
    return response.data.data!
  },

  getCandidateImageUrl(candidate: Candidate): string {
    return `/uploads/${candidate.storage_path}`
  },
}

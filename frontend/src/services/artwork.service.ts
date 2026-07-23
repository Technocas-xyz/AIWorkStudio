import api from './api'
import type { APIResponse } from '@/types'

export interface ArtworkItem {
  id: string
  artwork_id: string
  filename: string
  original_filename: string
  extension: string
  mime_type: string
  width: number | null
  height: number | null
  resolution_dpi: number | null
  color_space: string | null
  bit_depth: number | null
  has_transparency: boolean
  has_alpha_channel: boolean
  orientation: string | null
  file_size: number
  checksum: string
  storage_bucket: string
  storage_path: string
  status: string
  processing_status: string
  current_version: number
  project_id: string | null
  owner_id: string
  is_favorite: boolean
  created_at: string
  updated_at: string
}

export interface ArtworkListResponse {
  items: ArtworkItem[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface UploadResult {
  success: Array<{ filename: string; id: string; artwork_id: string }>
  failed: Array<{ filename: string; error: string }>
}

export const artworkService = {
  async list(params?: {
    page?: number
    page_size?: number
    search?: string
    extension?: string
    project_id?: string
    status?: string
    sort_by?: string
    sort_order?: string
  }): Promise<ArtworkListResponse> {
    const response = await api.get<APIResponse<ArtworkListResponse>>('/artworks', { params })
    return response.data.data!
  },

  async get(id: string): Promise<ArtworkItem> {
    const response = await api.get<APIResponse<ArtworkItem>>(`/artworks/${id}`)
    return response.data.data!
  },

  async upload(file: File, projectId?: string): Promise<any> {
    const formData = new FormData()
    formData.append('file', file)
    if (projectId) formData.append('project_id', projectId)
    const response = await api.post<APIResponse>('/artworks/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },

  async bulkUpload(files: File[], projectId?: string): Promise<UploadResult> {
    const formData = new FormData()
    files.forEach(file => formData.append('files', file))
    if (projectId) formData.append('project_id', projectId)
    const response = await api.post<APIResponse<UploadResult>>('/artworks/bulk-upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data.data!
  },

  async update(id: string, data: Record<string, unknown>): Promise<ArtworkItem> {
    const response = await api.put<APIResponse<ArtworkItem>>(`/artworks/${id}`, data)
    return response.data.data!
  },

  async delete(id: string): Promise<void> {
    await api.delete(`/artworks/${id}`)
  },

  async getVersions(id: string): Promise<any[]> {
    const response = await api.get<APIResponse<any[]>>(`/artworks/${id}/versions`)
    return response.data.data!
  },

  async toggleFavorite(id: string): Promise<boolean> {
    const response = await api.post<APIResponse<{ is_favorite: boolean }>>(`/artworks/${id}/favorite`)
    return response.data.data!.is_favorite
  },

  getPreviewUrl(artwork: ArtworkItem, type: 'thumbnail' | 'medium' | 'large' = 'thumbnail'): string {
    const apiUrl = import.meta.env.VITE_API_URL || ''
    return `${apiUrl}/uploads/previews/${artwork.id}/${type}.png`
  },
}

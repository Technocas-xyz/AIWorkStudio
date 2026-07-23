import api from './api'
import type { Project, ProjectCreate, ProjectUpdate, PaginatedResponse, APIResponse } from '@/types'

export const projectService = {
  async list(params?: {
    page?: number
    page_size?: number
    search?: string
    status?: string
  }): Promise<PaginatedResponse<Project>> {
    const response = await api.get<APIResponse<PaginatedResponse<Project>>>('/projects', { params })
    return response.data.data!
  },

  async create(data: ProjectCreate): Promise<Project> {
    const response = await api.post<APIResponse<Project>>('/projects', data)
    return response.data.data!
  },

  async update(id: string, data: ProjectUpdate): Promise<Project> {
    const response = await api.put<APIResponse<Project>>(`/projects/${id}`, data)
    return response.data.data!
  },

  async delete(id: string): Promise<void> {
    await api.delete(`/projects/${id}`)
  },
}

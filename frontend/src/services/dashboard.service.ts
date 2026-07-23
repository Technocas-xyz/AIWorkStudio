import api from './api'
import type { DashboardStats, Activity, APIResponse } from '@/types'

export const dashboardService = {
  async getStats(): Promise<DashboardStats> {
    const response = await api.get<APIResponse<DashboardStats>>('/dashboard/stats')
    return response.data.data!
  },

  async getRecentActivity(): Promise<Activity[]> {
    const response = await api.get<APIResponse<Activity[]>>('/dashboard/recent-activity')
    return response.data.data!
  },
}

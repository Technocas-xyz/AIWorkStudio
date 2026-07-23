// Core types for AI Work Studio

export interface User {
  id: string
  email: string
  username: string
  first_name: string
  last_name: string
  full_name: string
  is_active: boolean
  is_verified: boolean
  role_id: string
  role_name?: string
  avatar_url?: string
  last_login?: string
  created_at: string
  updated_at: string
}

export interface AuthUser {
  id: string
  email: string
  username: string
  first_name: string
  last_name: string
  full_name: string
  role: string
  permissions: string[]
  avatar_url?: string
  is_active: boolean
}

export interface LoginCredentials {
  email: string
  password: string
  remember_me: boolean
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface Project {
  id: string
  name: string
  client?: string
  description?: string
  status: ProjectStatus
  production_status: ProductionStatus
  owner_id: string
  owner_name?: string
  created_by_id: string
  artwork_count: number
  created_at: string
  updated_at: string
}

export type ProjectStatus = 'active' | 'archived' | 'completed' | 'on_hold'
export type ProductionStatus = 'not_started' | 'in_progress' | 'in_review' | 'approved' | 'completed'

export interface ProjectCreate {
  name: string
  client?: string
  description?: string
}

export interface ProjectUpdate {
  name?: string
  client?: string
  description?: string
  status?: ProjectStatus
  production_status?: ProductionStatus
}

export interface DashboardStats {
  total_projects: number
  active_projects: number
  completed_projects: number
  pending_analysis: number
  pending_generation: number
  pending_qa: number
  storage_usage_bytes: number
  ai_credits: number
  total_users: number
}

export interface Activity {
  id: string
  action: string
  resource_type: string
  resource_id?: string
  user_id?: string
  details?: Record<string, unknown>
  created_at: string
}

export interface APIResponse<T = unknown> {
  success: boolean
  message: string
  data?: T
  errors: string[]
  code: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface NavigationItem {
  name: string
  path: string
  icon: string
  permission?: string
}

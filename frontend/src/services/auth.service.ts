import api from './api'
import type { LoginCredentials, TokenResponse, AuthUser, APIResponse } from '@/types'

export const authService = {
  async login(credentials: LoginCredentials): Promise<TokenResponse> {
    const response = await api.post<APIResponse<TokenResponse>>('/auth/login', credentials)
    return response.data.data!
  },

  async logout(): Promise<void> {
    await api.post('/auth/logout')
  },

  async getMe(): Promise<AuthUser> {
    const response = await api.get<APIResponse<AuthUser>>('/auth/me')
    return response.data.data!
  },

  async refreshToken(refreshToken: string): Promise<TokenResponse> {
    const response = await api.post<APIResponse<TokenResponse>>('/auth/refresh', {
      refresh_token: refreshToken,
    })
    return response.data.data!
  },

  async requestPasswordReset(email: string): Promise<void> {
    await api.post('/auth/password-reset', { email })
  },
}

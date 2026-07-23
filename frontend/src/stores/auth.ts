import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authService } from '@/services/auth.service'
import type { AuthUser, LoginCredentials } from '@/types'
import router from '@/router'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<AuthUser | null>(null)
  const isLoading = ref(false)
  const isInitialized = ref(false)

  const isAuthenticated = computed(() => !!user.value)
  const userPermissions = computed(() => user.value?.permissions || [])
  const userRole = computed(() => user.value?.role || '')

  function hasPermission(permission: string): boolean {
    return userPermissions.value.includes(permission)
  }

  async function initialize() {
    const token = localStorage.getItem('access_token')
    if (token) {
      try {
        user.value = await authService.getMe()
      } catch {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
      }
    }
    isInitialized.value = true
  }

  async function login(credentials: LoginCredentials) {
    isLoading.value = true
    try {
      const tokens = await authService.login(credentials)
      localStorage.setItem('access_token', tokens.access_token)
      localStorage.setItem('refresh_token', tokens.refresh_token)
      user.value = await authService.getMe()
      await router.push('/dashboard')
    } finally {
      isLoading.value = false
    }
  }

  async function logout() {
    try {
      await authService.logout()
    } catch {
      // Continue logout even if API call fails
    }
    user.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    await router.push('/login')
  }

  return {
    user,
    isLoading,
    isInitialized,
    isAuthenticated,
    userPermissions,
    userRole,
    hasPermission,
    initialize,
    login,
    logout,
  }
})

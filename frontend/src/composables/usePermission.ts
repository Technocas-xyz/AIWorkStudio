import { useAuthStore } from '@/stores/auth'

/**
 * Composable for checking user permissions in components.
 */
export function usePermission() {
  const authStore = useAuthStore()

  function can(permission: string): boolean {
    return authStore.hasPermission(permission)
  }

  function canAny(permissions: string[]): boolean {
    return permissions.some((p) => authStore.hasPermission(p))
  }

  function canAll(permissions: string[]): boolean {
    return permissions.every((p) => authStore.hasPermission(p))
  }

  return { can, canAny, canAll }
}

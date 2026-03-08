/**
 * Custom Auth Hook
 *
 * Provides a convenient hook that combines auth store state and React Query
 */

import { useAuthStore } from '../features/auth/auth.store'

/**
 * Hook for authentication
 * Returns auth state and actions in a single hook
 */
export function useAuth() {
  const token = useAuthStore((state) => state.token)
  const login = useAuthStore((state) => state.login)
  const logout = useAuthStore((state) => state.logout)

  const isAuthenticated = !!token

  return {
    token,
    isAuthenticated,
    login,
    logout,
  }
}

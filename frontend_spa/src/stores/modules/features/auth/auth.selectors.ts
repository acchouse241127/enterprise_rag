/**
 * Auth Selectors
 *
 * Computed properties for auth state
 * Provides performant access to auth state without causing re-renders
 */

import { useAuthStore, selectIsAuthenticated, selectToken, selectUsername } from './auth.store'

/**
 * Selector: Check if user is authenticated
 */
export function useIsAuthenticated() {
  return selectIsAuthenticated(useAuthStore())
}

/**
 * Selector: Get authentication token
 */
export function useAuthToken() {
  return selectToken(useAuthStore())
}

/**
 * Selector: Get current username
 */
export function useAuthUser() {
  return selectUsername(useAuthStore())
}

/**
 * Selector: Get auth state object (for components that need multiple auth values)
 */
export function useAuthState() {
  const token = useAuthToken()
  const isAuthenticated = useIsAuthenticated()
  const username = useAuthUser()

  return {
    token,
    isAuthenticated,
    username,
  }
}

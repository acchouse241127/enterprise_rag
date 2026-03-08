/**
 * Auth Store module
 *
 * Authentication state management with selectors for optimal performance
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AuthState {
  token: string | null
  username: string | null
  login: (token: string, username: string) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      username: null,
      login: (token, username) => set({ token, username }),
      logout: () => {
        set({ token: null, username: null })
        // Clear auth from localStorage (handled by persist middleware)
        window.location.href = '/login'
      },
    }),
    {
      name: 'enterprise-rag-auth',
      version: 1,
    }
  )
)

// Selectors
export const selectIsAuthenticated = (state: AuthState) => !!state.token
export const selectToken = (state: AuthState) => state.token
export const selectUsername = (state: AuthState) => state.username

export default useAuthStore

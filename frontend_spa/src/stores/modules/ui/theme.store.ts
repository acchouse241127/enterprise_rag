/**
 * UI State - Theme module
 *
 * Manages app theme (light/dark)
 */

import { create } from 'zustand'

interface ThemeState {
  theme: 'light' | 'dark'
  setTheme: (theme: 'light' | 'dark') => void
}

export const useThemeStore = create<ThemeState>()(
  (set) => ({
    theme: 'light',
    setTheme: (theme: 'light' | 'dark') => set({ theme }),
  })
)

export default useThemeStore

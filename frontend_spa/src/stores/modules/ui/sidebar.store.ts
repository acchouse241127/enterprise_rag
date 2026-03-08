/**
 * UI State - Sidebar module
 *
 * Manages sidebar collapsed state
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface SidebarState {
  collapsed: boolean
  toggleSidebar: () => void
  setSidebarCollapsed: (collapsed: boolean) => void
}

export const useSidebarStore = create<SidebarState>()(
  persist(
    (set) => ({
      collapsed: false,
      toggleSidebar: () => set((state) => ({ collapsed: !state.collapsed })),
      setSidebarCollapsed: (collapsed) => set({ collapsed }),
    }),
    {
      name: 'enterprise-rag-sidebar',
      version: 1,
      partialize: (state) => ({ collapsed: state.collapsed }),
    }
  )
)

export default useSidebarStore

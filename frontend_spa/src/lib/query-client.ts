/**
 * React Query Configuration
 */
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'

// Create QueryClient instance
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Default cache time: 5 minutes
      staleTime: 5 * 60 * 1000,
      // Default cache time: 10 minutes
      gcTime: 10 * 60 * 1000,
      // Retry failed requests up to 3 times
      retry: 3,
      // Retry on network errors only (not on 4xx errors)
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
      // Refetch on window focus
      refetchOnWindowFocus: false,
      // Refetch on reconnect
      refetchOnReconnect: true,
    },
    mutations: {
      // Retry failed mutations
      retry: 1,
    },
  },
})

// QueryClientProvider component for React
export function ReactQueryProvider({ children }: { children: React.ReactNode }) {
  return React.createElement(QueryClientProvider, { client: queryClient }, children)
}

// DevTools are included in development mode via vite.config.ts
if (typeof window !== 'undefined' && (window as any).__DEV__) {
  // DevTools are imported in vite.config.ts
}

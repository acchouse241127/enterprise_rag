/**
 * React Query client configuration for distributed data fetching
 *
 * Features:
 * - Automatic caching with configurable stale time
 * - Background refetching on window focus
 * - Garbage collection for stale queries
 * - Request deduplication
 * - Optimistic updates support
 */

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'

// Cache configuration
const STALE_TIME_MS = 5 * 60 * 1000  // 5 minutes
const GC_TIME_MS = 10 * 60 * 1000  // 10 minutes
const REFETCH_ON_WINDOW_FOCUS = true
const DEFAULT_QUERY_STALE_TIME_MS = 3 * 60 * 1000  // 3 minutes for queries that update frequently

/**
 * Create and configure React Query client
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Time in milliseconds after which data is considered stale
      staleTime: (query) => {
        // QA queries update more frequently, shorter stale time
        if (query.queryKey && query.queryKey[0] === 'qa-message') {
          return DEFAULT_QUERY_STALE_TIME_MS
        }
        return STALE_TIME_MS
      },

      // Number of times a query should be retried before showing error
      retry: (failureCount, error) => {
        // Don't retry on 4xx errors (client errors)
        // Note: error is an Error object, we need to check if it's an AxiosError
        const axiosError = error as any
        if (axiosError?.response?.status && axiosError.response.status >= 400 && axiosError.response.status < 500) {
          return false
        }
        // Retry 3 times by default
        return failureCount < 3
      },

      // Time to wait before retrying (ms)
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),

      // Refetch data when window regains focus
      refetchOnWindowFocus: REFETCH_ON_WINDOW_FOCUS,

      // Garbage collection time - remove unused data from cache
      gcTime: GC_TIME_MS,

      // Deduplicate in-flight requests with the same key
      networkMode: 'online',

      // Data transformation
      structuralSharing: true,

      // Query key function to create stable keys
      queryKeyHashFn: (queryKey) => {
        return JSON.stringify(queryKey)
      },
    },

    mutations: {
      // Retry failed mutations
      retry: (failureCount) => failureCount < 3,
    },
  },
})

/**
 * Invalidate and refetch utility functions
 */

/**
 * Invalidate all queries (useful after login/logout)
 */
export function invalidateAllQueries() {
  queryClient.invalidateQueries()
}

/**
 * Refetch queries on window focus (manual trigger)
 */
export function refetchOnFocus() {
  queryClient.refetchQueries()
}

/**
 * Prefetch queries for navigation optimization
 */
export function prefetchKnowledgeBaseQueries() {
  // Prefetch frequently accessed data
  queryClient.prefetchQuery({
    queryKey: ['knowledge-bases'],
    queryFn: async () => {
      const { getKnowledgeBases } = await import('@/api/knowledge-base')
      return getKnowledgeBases()
    },
  })
}

/**
 * Configure query defaults for specific query types
 */

// Frequently changing data (shorter stale time)
export const frequentlyUpdatingQueryOptions = {
  staleTime: DEFAULT_QUERY_STALE_TIME_MS,
  refetchInterval: 30 * 1000, // 30 seconds
}

// Rarely changing data (longer stale time)
export const rarelyUpdatingQueryOptions = {
  staleTime: STALE_TIME_MS,
  refetchInterval: 5 * 60 * 1000, // 5 minutes
}

// ReactQueryProvider component for React
export function ReactQueryProvider({ children }: { children: React.ReactNode }) {
  return React.createElement(QueryClientProvider, { client: queryClient }, children)
}

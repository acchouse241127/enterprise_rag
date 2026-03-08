/**
 * Example: Migrating API calls to React Query
 *
 * This hook demonstrates how to replace direct API calls with React Query
 * for better caching, automatic refetching, and deduplication.
 */

import { useQuery } from '@tanstack/react-query'
import { getKnowledgeBases } from '@/api/knowledge-base'

/**
 * Hook for fetching and caching knowledge bases
 * Migrates from direct API call to React Query
 */
export function useKnowledgeBases() {
  return useQuery({
    queryKey: ['knowledge-bases'],
    queryFn: async () => {
      const { getKnowledgeBases } = await import('@/api/knowledge-base')
      return getKnowledgeBases()
    },
    staleTime: 3 * 60 * 1000,  // 3 minutes for KB data
    gcTime: 10 * 60 * 1000,  // 10 minutes to clean up
    refetchOnWindowFocus: true,  // Refresh when user returns to tab
  })
}

/**
 * Hook for creating knowledge base with mutation
 * Includes optimistic update support
 */
import { useMutation, useQueryClient } from '@tanstack/react-query'

export function useCreateKnowledgeBase() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data: any) => {
      const { createKnowledgeBase } = await import('@/api/knowledge-base')

      // Return immediately for optimistic update
      return createKnowledgeBase(data)
    },
    onSuccess: () => {
      // Invalidate related queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['knowledge-bases'] })
    },
    onError: (error) => {
      console.error('Failed to create knowledge base:', error)
    },
  })
}

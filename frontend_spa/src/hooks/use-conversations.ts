/**
 * React Query hooks for Conversation API
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  getConversations,
  getConversation,
  deleteConversation,
  shareConversation,
  getSharedConversation,
  exportConversationFile,
} from '@/api'

// Query keys
export const conversationKeys = {
  all: ['conversations'] as const,
  lists: (params?: { knowledge_base_id?: number | string; limit?: number; offset?: number }) =>
    [...conversationKeys.all, 'list', params] as const,
  detail: (id: number) => [...conversationKeys.all, 'detail', id] as const,
  shared: (shareId: string) => [...conversationKeys.all, 'shared', shareId] as const,
}

// ============ Conversations ============

export function useConversations(params?: {
  knowledge_base_id?: number | string;
  limit?: number;
  offset?: number;
}) {
  return useQuery({
    queryKey: conversationKeys.lists(params),
    queryFn: () => getConversations(params),
  })
}

export function useConversation(id: number) {
  return useQuery({
    queryKey: conversationKeys.detail(id),
    queryFn: () => getConversation(id),
    enabled: !!id,
  })
}

export function useDeleteConversation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => deleteConversation(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: conversationKeys.all })
    },
  })
}

export function useShareConversation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, expiresInDays }: { id: number; expiresInDays?: number }) =>
      shareConversation(id, expiresInDays),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: conversationKeys.lists() })
    },
  })
}

export function useGetSharedConversation(shareId: string) {
  return useQuery({
    queryKey: conversationKeys.shared(shareId),
    queryFn: () => getSharedConversation(shareId),
    enabled: !!shareId,
  })
}

export function useExportConversation() {
  return useMutation({
    mutationFn: ({ id, format }: { id: number; format: 'markdown' | 'pdf' | 'docx' }) =>
      exportConversationFile(id, format),
  })
}

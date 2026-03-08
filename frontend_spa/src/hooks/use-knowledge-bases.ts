/**
 * React Query hooks for Knowledge Base API
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  getKnowledgeBases,
  getKnowledgeBase,
  createKnowledgeBase,
  updateKnowledgeBase,
  deleteKnowledgeBase,
  getDocuments,
  uploadDocument,
  importUrl as importUrlApi,
  deleteDocument,
  reparseDocument,
  type KnowledgeBase,
  type CreateKnowledgeBaseRequest,
  type KnowledgeBasesResponse,
  type DocumentsResponse,
} from '@/api'

// Query keys
export const knowledgeBaseKeys = {
  all: ['knowledge-bases'] as const,
  lists: () => [...knowledgeBaseKeys.all, 'list'] as const,
  list: (id?: number) => [...knowledgeBaseKeys.lists(), id] as const,
  detail: (id: number) => [...knowledgeBaseKeys.all, 'detail', id] as const,
  documents: (kbId: number) => [...knowledgeBaseKeys.all, kbId, 'documents'] as const,
}

// ============ Knowledge Bases ============

export function useKnowledgeBases() {
  return useQuery({
    queryKey: knowledgeBaseKeys.lists(),
    queryFn: getKnowledgeBases,
    select: (data: KnowledgeBasesResponse) => data.data || [],
  })
}

export function useKnowledgeBase(id: number | null) {
  return useQuery({
    queryKey: knowledgeBaseKeys.detail(id || 0),
    queryFn: () => {
      if (!id) return Promise.resolve({ data: null } as any)
      return getKnowledgeBase(id)
    },
    select: (data: any) => data.data,
    enabled: !!id,
  })
}

export function useCreateKnowledgeBase() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateKnowledgeBaseRequest) => createKnowledgeBase(data),
    onSuccess: () => {
      // Invalidate knowledge bases list
      queryClient.invalidateQueries({ queryKey: knowledgeBaseKeys.lists() })
    },
  })
}

export function useUpdateKnowledgeBase() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<KnowledgeBase> }) =>
      updateKnowledgeBase(id, data),
    onSuccess: (_, { id }) => {
      // Invalidate knowledge bases list and detail
      queryClient.invalidateQueries({ queryKey: knowledgeBaseKeys.lists() })
      queryClient.invalidateQueries({ queryKey: knowledgeBaseKeys.detail(id) })
    },
  })
}

export function useDeleteKnowledgeBase() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => deleteKnowledgeBase(id),
    onSuccess: () => {
      // Invalidate knowledge bases list
      queryClient.invalidateQueries({ queryKey: knowledgeBaseKeys.lists() })
    },
  })
}

// ============ Documents ============

export function useDocuments(kbId: number, enabled = true) {
  return useQuery({
    queryKey: knowledgeBaseKeys.documents(kbId),
    queryFn: () => getDocuments(kbId),
    select: (data: DocumentsResponse) => data.data || [],
    enabled: enabled && !!kbId,
  })
}

export function useUploadDocument(kbId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (file: File) => uploadDocument(kbId, file),
    onSuccess: () => {
      // Invalidate documents list
      queryClient.invalidateQueries({ queryKey: knowledgeBaseKeys.documents(kbId) })
    },
  })
}

export function useImportUrl(kbId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (url: string) => importUrlApi(kbId, url),
    onSuccess: () => {
      // Invalidate documents list
      queryClient.invalidateQueries({ queryKey: knowledgeBaseKeys.documents(kbId) })
    },
  })
}

export function useDeleteDocument(kbId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (docId: number) => deleteDocument(kbId, docId),
    onSuccess: () => {
      // Invalidate documents list
      queryClient.invalidateQueries({ queryKey: knowledgeBaseKeys.documents(kbId) })
    },
  })
}

export function useReparseDocument(kbId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (docId: number) => reparseDocument(kbId, docId),
    onSuccess: () => {
      // Invalidate documents list
      queryClient.invalidateQueries({ queryKey: knowledgeBaseKeys.documents(kbId) })
    },
  })
}

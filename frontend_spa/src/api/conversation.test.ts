/**
 * Conversation API tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import * as conversation from './conversation'

// Mock global fetch
const mockFetch = vi.fn()
global.fetch = mockFetch as any

// Mock the apiClient
vi.mock('./client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
  getToken: vi.fn(() => 'test-token'),
  API_BASE: '',
  logout: vi.fn(),
}))

import { apiClient, logout } from './client'

const mockedApiClient = vi.mocked(apiClient)

describe('conversation API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getConversations', () => {
    it('should call GET /api/conversations without params', async () => {
      const mockResponse = { data: [{ id: 1, title: 'test' }] }
      mockedApiClient.get.mockResolvedValue(mockResponse)

      const result = await conversation.getConversations()

      expect(mockedApiClient.get).toHaveBeenCalledWith('/api/conversations')
      expect(result).toEqual(mockResponse.data)
    })

    it('should include knowledge_base_id in query', async () => {
      const mockResponse = { data: [{ id: 1, title: 'test' }] }
      mockedApiClient.get.mockResolvedValue(mockResponse)

      await conversation.getConversations({ knowledge_base_id: 1 })

      expect(mockedApiClient.get).toHaveBeenCalledWith('/api/conversations?knowledge_base_id=1')
    })

    it('should include pagination params in query', async () => {
      const mockResponse = { data: [{ id: 1, title: 'test' }] }
      mockedApiClient.get.mockResolvedValue(mockResponse)

      await conversation.getConversations({ limit: 10, offset: 20 })

      expect(mockedApiClient.get).toHaveBeenCalledWith('/api/conversations?limit=10&offset=20')
    })

    it('should include all params in query', async () => {
      const mockResponse = { data: [{ id: 1, title: 'test' }] }
      mockedApiClient.get.mockResolvedValue(mockResponse)

      await conversation.getConversations({
        knowledge_base_id: 1,
        limit: 10,
        offset: 20,
      })

      expect(mockedApiClient.get).toHaveBeenCalledWith(
        '/api/conversations?knowledge_base_id=1&limit=10&offset=20'
      )
    })
  })

  describe('getConversation', () => {
    it('should call GET /api/conversations/:id', async () => {
      const mockResponse = { data: { id: 1, title: 'test' } }
      mockedApiClient.get.mockResolvedValue(mockResponse)

      const result = await conversation.getConversation(1)

      expect(mockedApiClient.get).toHaveBeenCalledWith('/api/conversations/1')
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('deleteConversation', () => {
    it('should call DELETE /api/conversations/:id', async () => {
      mockedApiClient.delete.mockResolvedValue({ data: null } as any)

      await conversation.deleteConversation(1)

      expect(mockedApiClient.delete).toHaveBeenCalledWith('/api/conversations/1')
    })
  })

  describe('shareConversation', () => {
    it('should call POST /api/conversations/:id/share without expiration', async () => {
      const mockResponse = { data: { share_token: 'abc123' } }
      mockedApiClient.post.mockResolvedValue(mockResponse)

      const result = await conversation.shareConversation(1)

      expect(mockedApiClient.post).toHaveBeenCalledWith('/api/conversations/1/share', {})
      expect(result).toEqual(mockResponse.data)
    })

    it('should call POST /api/conversations/:id/share with expiration', async () => {
      const mockResponse = { data: { share_token: 'abc123', expires_at: '2024-01-01' } }
      mockedApiClient.post.mockResolvedValue(mockResponse)

      const result = await conversation.shareConversation(1, 7)

      expect(mockedApiClient.post).toHaveBeenCalledWith('/api/conversations/1/share', {
        expires_in_days: 7,
      })
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('getSharedConversation', () => {
    it('should call GET /api/conversations/share/:shareId', async () => {
      const mockResponse = { data: { id: 1, title: 'test' } }
      mockedApiClient.get.mockResolvedValue(mockResponse)

      const result = await conversation.getSharedConversation('abc123')

      expect(mockedApiClient.get).toHaveBeenCalledWith('/api/conversations/share/abc123')
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('exportConversationFile', () => {
    it('should call GET /api/conversations/:id/export/:format for markdown', async () => {
      const mockBlob = new Blob(['test content'])
      mockFetch.mockResolvedValue({
        ok: true,
        blob: async () => mockBlob,
        headers: {
          get: () => 'Content-Disposition: attachment; filename="test.md"',
        },
      } as any)

      const result = await conversation.exportConversationFile(1, 'markdown')

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/conversations/1/export/markdown',
        expect.objectContaining({
          method: 'GET',
          headers: expect.any(Object),
        })
      )
      expect(result.blob).toBe(mockBlob)
    })

    it('should call GET /api/conversations/:id/export/:format for pdf', async () => {
      const mockBlob = new Blob(['pdf content'])
      mockFetch.mockResolvedValue({
        ok: true,
        blob: async () => mockBlob,
        headers: {
          get: () => 'Content-Disposition: attachment; filename="test.pdf"',
        },
      } as any)

      const result = await conversation.exportConversationFile(1, 'pdf')

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/conversations/1/export/pdf',
        expect.any(Object)
      )
    })

    it('should call GET /api/conversations/:id/export/:format for docx', async () => {
      const mockBlob = new Blob(['docx content'])
      mockFetch.mockResolvedValue({
        ok: true,
        blob: async () => mockBlob,
        headers: {
          get: () => 'Content-Disposition: attachment; filename="test.docx"',
        },
      } as any)

      const result = await conversation.exportConversationFile(1, 'docx')

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/conversations/1/export/docx',
        expect.any(Object)
      )
    })

    it('should handle 401 response by calling logout', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 401,
        statusText: 'Unauthorized',
        text: async () => 'Unauthorized',
      } as any)

      await expect(conversation.exportConversationFile(1, 'markdown')).rejects.toThrow(
        '未登录或已过期'
      )
      expect(logout).toHaveBeenCalled()
    })

    it('should parse filename from Content-Disposition header', async () => {
      const mockBlob = new Blob(['test content'])
      mockFetch.mockResolvedValue({
        ok: true,
        blob: async () => mockBlob,
        headers: {
          get: (name) => {
            if (name === 'Content-Disposition') {
              return 'attachment; filename*=UTF-8\'\'%E6%B5%8B%E8%AF%95.md'
            }
            return null
          },
        },
      } as any)

      const result = await conversation.exportConversationFile(1, 'markdown')

      expect(result.filename).toBe('测试.md')
    })

    it('should use default filename when no Content-Disposition header', async () => {
      const mockBlob = new Blob(['test content'])
      mockFetch.mockResolvedValue({
        ok: true,
        blob: async () => mockBlob,
        headers: {
          get: () => null,
        },
      } as any)

      const result = await conversation.exportConversationFile(1, 'markdown')

      expect(result.filename).toBe('conversation_1.md')
    })

    it('should handle API errors', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        text: async () => 'Internal Server Error',
      } as any)

      await expect(conversation.exportConversationFile(1, 'markdown')).rejects.toThrow(
        'Internal Server Error'
      )
    })
  })
})

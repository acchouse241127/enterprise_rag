/**
 * Knowledge Base API tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import * as kb from './knowledge-base'

// Mock the apiClient
vi.mock('./client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
  getToken: vi.fn(() => 'test-token'),
  API_BASE: '',
  logout: vi.fn(),
}))

// Mock global fetch
const mockFetch = vi.fn()
global.fetch = mockFetch as any

import { apiClient, logout } from './client'

const mockedApiClient = vi.mocked(apiClient)

describe('knowledge base API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getKnowledgeBases', () => {
    it('should call GET /api/knowledge-bases', async () => {
      const mockResponse = { data: { items: [] } }
      mockedApiClient.get.mockResolvedValue(mockResponse)

      const result = await kb.getKnowledgeBases()

      expect(mockedApiClient.get).toHaveBeenCalledWith('/api/knowledge-bases')
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('createKnowledgeBase', () => {
    it('should call POST /api/knowledge-bases with data', async () => {
      const mockResponse = { data: { id: 1, name: 'test' } }
      const data = { name: 'test', chunk_mode: 'char' }
      mockedApiClient.post.mockResolvedValue(mockResponse)

      const result = await kb.createKnowledgeBase(data)

      expect(mockedApiClient.post).toHaveBeenCalledWith('/api/knowledge-bases', data)
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('getKnowledgeBase', () => {
    it('should call GET /api/knowledge-bases/:id', async () => {
      const mockResponse = { data: { id: 1, name: 'test' } }
      mockedApiClient.get.mockResolvedValue(mockResponse)

      const result = await kb.getKnowledgeBase(1)

      expect(mockedApiClient.get).toHaveBeenCalledWith('/api/knowledge-bases/1')
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('updateKnowledgeBase', () => {
    it('should call PUT /api/knowledge-bases/:id with data', async () => {
      const mockResponse = { data: { id: 1, name: 'updated' } }
      const data = { name: 'updated' }
      mockedApiClient.put.mockResolvedValue(mockResponse)

      const result = await kb.updateKnowledgeBase(1, data)

      expect(mockedApiClient.put).toHaveBeenCalledWith('/api/knowledge-bases/1', data)
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('deleteKnowledgeBase', () => {
    it('should call DELETE /api/knowledge-bases/:id', async () => {
      mockedApiClient.delete.mockResolvedValue({ data: null } as any)

      await kb.deleteKnowledgeBase(1)

      expect(mockedApiClient.delete).toHaveBeenCalledWith('/api/knowledge-bases/1')
    })
  })

  describe('getDocuments', () => {
    it('should call GET /api/knowledge-bases/:kbId/documents', async () => {
      const mockResponse = { data: { items: [] } }
      mockedApiClient.get.mockResolvedValue(mockResponse)

      const result = await kb.getDocuments(1)

      expect(mockedApiClient.get).toHaveBeenCalledWith('/api/knowledge-bases/1/documents')
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('uploadDocument', () => {
    it('should call POST /api/knowledge-bases/:kbId/documents with file', async () => {
      const mockFile = new File(['test content'], 'test.txt')
      const mockResponse = { id: 1, filename: 'test.txt' }
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockResponse,
      } as any)

      const result = await kb.uploadDocument(1, mockFile)

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/knowledge-bases/1/documents',
        expect.objectContaining({
          method: 'POST',
          headers: expect.any(Object),
        })
      )
    })

    it('should handle 401 response by calling logout', async () => {
      const mockFile = new File(['test'], 'test.txt')
      mockFetch.mockResolvedValue({
        ok: false,
        status: 401,
        statusText: 'Unauthorized',
        text: async () => 'Unauthorized',
      } as any)

      await expect(kb.uploadDocument(1, mockFile)).rejects.toThrow('未登录或已过期')
      expect(logout).toHaveBeenCalled()
    })

    it('should handle API errors', async () => {
      const mockFile = new File(['test'], 'test.txt')
      mockFetch.mockResolvedValue({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        text: async () => 'Internal Server Error',
      } as any)

      await expect(kb.uploadDocument(1, mockFile)).rejects.toThrow('Internal Server Error')
    })
  })

  describe('importUrl', () => {
    it('should call POST /api/knowledge-bases/:kbId/documents/from-url', async () => {
      const mockResponse = { data: { id: 1, filename: 'imported.txt' } }
      mockedApiClient.post.mockResolvedValue(mockResponse)

      const result = await kb.importUrl(1, 'http://example.com/file.txt')

      expect(mockedApiClient.post).toHaveBeenCalledWith('/api/knowledge-bases/1/documents/from-url', {
        url: 'http://example.com/file.txt',
      })
      expect(result).toEqual(mockResponse.data)
    })

    it('should throw error when response code is not 0', async () => {
      mockedApiClient.post.mockResolvedValue({
        data: { code: 1, detail: 'Import failed' },
      } as any)

      await expect(kb.importUrl(1, 'http://example.com/file.txt')).rejects.toThrow('Import failed')
    })

    it('should throw error with message when code is not 0', async () => {
      mockedApiClient.post.mockResolvedValue({
        data: { code: 1, message: 'Custom error' },
      } as any)

      await expect(kb.importUrl(1, 'http://example.com/file.txt')).rejects.toThrow('Custom error')
    })
  })

  describe('getDocument', () => {
    it('should call GET /api/documents/:docId', async () => {
      const mockResponse = { data: { id: 1, filename: 'test.txt' } }
      mockedApiClient.get.mockResolvedValue(mockResponse)

      const result = await kb.getDocument(1, 1)

      expect(mockedApiClient.get).toHaveBeenCalledWith('/api/documents/1')
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('getDocumentContent', () => {
    it('should call GET /api/knowledge-bases/documents/:docId/content', async () => {
      const mockResponse = { data: { content: 'test content' } }
      mockedApiClient.get.mockResolvedValue(mockResponse)

      const result = await kb.getDocumentContent(1, 1)

      expect(mockedApiClient.get).toHaveBeenCalledWith('/api/knowledge-bases/documents/1/content')
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('updateDocumentContent', () => {
    it('should call PUT /api/knowledge-bases/documents/:docId/content', async () => {
      const mockResponse = { data: { id: 1, content: 'updated' } }
      mockedApiClient.put.mockResolvedValue(mockResponse)

      const result = await kb.updateDocumentContent(1, 1, 'new content')

      expect(mockedApiClient.put).toHaveBeenCalledWith('/api/knowledge-bases/documents/1/content', {
        content: 'new content',
      })
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('deleteDocument', () => {
    it('should call DELETE /api/documents/:docId', async () => {
      mockedApiClient.delete.mockResolvedValue({ data: null } as any)

      await kb.deleteDocument(1, 1)

      expect(mockedApiClient.delete).toHaveBeenCalledWith('/api/documents/1')
    })
  })

  describe('reparseDocument', () => {
    it('should call POST /api/documents/:docId/reparse', async () => {
      const mockResponse = { data: { id: 1, status: 'processing' } }
      mockedApiClient.post.mockResolvedValue(mockResponse)

      const result = await kb.reparseDocument(1, 1)

      expect(mockedApiClient.post).toHaveBeenCalledWith('/api/documents/1/reparse')
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('rechunkDocument', () => {
    it('should call POST /api/knowledge-bases/documents/:docId/rechunk', async () => {
      const mockResponse = { data: { id: 1, status: 'processing' } }
      mockedApiClient.post.mockResolvedValue(mockResponse)

      const result = await kb.rechunkDocument(1, 1)

      expect(mockedApiClient.post).toHaveBeenCalledWith('/api/knowledge-bases/documents/1/rechunk')
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('getDocumentPreview', () => {
    it('should call GET /api/documents/:docId/preview', async () => {
      const mockResponse = { data: { preview: 'test preview' } }
      mockedApiClient.get.mockResolvedValue(mockResponse)

      const result = await kb.getDocumentPreview(1)

      expect(mockedApiClient.get).toHaveBeenCalledWith('/api/documents/1/preview')
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('downloadDocumentFile', () => {
    it('should call GET /api/documents/:docId/download', async () => {
      const mockBlob = new Blob(['test content'])
      mockFetch.mockResolvedValue({
        ok: true,
        blob: async () => mockBlob,
        headers: {
          get: () => 'Content-Disposition: attachment; filename="test.txt"',
        },
      } as any)

      const result = await kb.downloadDocumentFile(1)

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/documents/1/download',
        expect.objectContaining({
          method: 'GET',
        })
      )
      expect(result.blob).toBe(mockBlob)
    })

    it('should handle 401 response by calling logout', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 401,
        statusText: 'Unauthorized',
        text: async () => 'Unauthorized',
      } as any)

      await expect(kb.downloadDocumentFile(1)).rejects.toThrow('未登录或已过期')
      expect(logout).toHaveBeenCalled()
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

      const result = await kb.downloadDocumentFile(1)

      expect(result.filename).toBe('document_1')
    })
  })

  describe('getDocumentVersions', () => {
    it('should call GET /api/documents/:docId/versions', async () => {
      const mockResponse = { data: { items: [] } }
      mockedApiClient.get.mockResolvedValue(mockResponse)

      const result = await kb.getDocumentVersions(1)

      expect(mockedApiClient.get).toHaveBeenCalledWith('/api/documents/1/versions')
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('activateDocumentVersion', () => {
    it('should call POST /api/documents/:docId/activate', async () => {
      const mockResponse = { data: { id: 1, active: true } }
      mockedApiClient.post.mockResolvedValue(mockResponse)

      const result = await kb.activateDocumentVersion(1)

      expect(mockedApiClient.post).toHaveBeenCalledWith('/api/documents/1/activate')
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('getFolderSyncConfig', () => {
    it('should call GET /api/knowledge-bases/:kbId/folder-sync', async () => {
      const mockResponse = { data: { enabled: false } }
      mockedApiClient.get.mockResolvedValue(mockResponse)

      const result = await kb.getFolderSyncConfig(1)

      expect(mockedApiClient.get).toHaveBeenCalledWith('/api/knowledge-bases/1/folder-sync')
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('updateFolderSyncConfig', () => {
    it('should call POST /api/knowledge-bases/:kbId/folder-sync with config', async () => {
      const mockResponse = { data: { enabled: true } }
      const config = {
        directory_path: '/path/to/folder',
        enabled: true,
        sync_interval_minutes: 30,
      }
      mockedApiClient.post.mockResolvedValue(mockResponse)

      const result = await kb.updateFolderSyncConfig(1, config)

      expect(mockedApiClient.post).toHaveBeenCalledWith('/api/knowledge-bases/1/folder-sync', config)
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('deleteFolderSyncConfig', () => {
    it('should call DELETE /api/knowledge-bases/:kbId/folder-sync', async () => {
      const mockResponse = { data: { success: true } }
      mockedApiClient.delete.mockResolvedValue(mockResponse)

      const result = await kb.deleteFolderSyncConfig(1)

      expect(mockedApiClient.delete).toHaveBeenCalledWith('/api/knowledge-bases/1/folder-sync')
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('syncFolderNow', () => {
    it('should call POST /api/knowledge-bases/:kbId/folder-sync/trigger', async () => {
      const mockResponse = { data: { status: 'syncing' } }
      mockedApiClient.post.mockResolvedValue(mockResponse)

      const result = await kb.syncFolderNow(1)

      expect(mockedApiClient.post).toHaveBeenCalledWith('/api/knowledge-bases/1/folder-sync/trigger')
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('getFolderSyncLogs', () => {
    it('should call GET /api/knowledge-bases/:kbId/folder-sync/logs with default limit', async () => {
      const mockResponse = { data: { items: [] } }
      mockedApiClient.get.mockResolvedValue(mockResponse)

      const result = await kb.getFolderSyncLogs(1)

      expect(mockedApiClient.get).toHaveBeenCalledWith('/api/knowledge-bases/1/folder-sync/logs?limit=20')
      expect(result).toEqual(mockResponse.data)
    })

    it('should call GET with custom limit', async () => {
      const mockResponse = { data: { items: [] } }
      mockedApiClient.get.mockResolvedValue(mockResponse)

      const result = await kb.getFolderSyncLogs(1, 10)

      expect(mockedApiClient.get).toHaveBeenCalledWith('/api/knowledge-bases/1/folder-sync/logs?limit=10')
      expect(result).toEqual(mockResponse.data)
    })
  })
})

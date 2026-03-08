/**
 * QA API tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { getStrategies, getExpansionMeta, streamQa } from './qa'

// Mock global fetch
global.fetch = vi.fn() as any

// Mock getToken
vi.mock('./client', () => ({
  getToken: vi.fn(() => 'test-token'),
  API_BASE: '',
}))

describe('QA API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getStrategies', () => {
    it('should fetch strategies successfully', async () => {
      const mockResponse = { strategies: ['smart', 'precise', 'fast'] }
      vi.mocked(fetch).mockResolvedValue({
        ok: true,
        json: async () => mockResponse,
      } as any)

      const result = await getStrategies()

      expect(fetch).toHaveBeenCalledWith('/api/qa/strategies', {
        headers: {
          Authorization: 'Bearer test-token',
        },
      })
      expect(result).toEqual(mockResponse)
    })

    it('should throw error on failed request', async () => {
      vi.mocked(fetch).mockResolvedValue({
        ok: false,
        statusText: 'Unauthorized',
      } as any)

      await expect(getStrategies()).rejects.toThrow('Unauthorized')
    })
  })

  describe('getExpansionMeta', () => {
    it('should fetch expansion meta successfully', async () => {
      const mockResponse = { enabled: true, targets: ['all'] }
      vi.mocked(fetch).mockResolvedValue({
        ok: true,
        json: async () => mockResponse,
      } as any)

      const result = await getExpansionMeta()

      expect(fetch).toHaveBeenCalledWith('/api/qa/expansion-meta', {
        headers: {
          Authorization: 'Bearer test-token',
        },
      })
      expect(result).toEqual(mockResponse)
    })

    it('should throw error on failed request', async () => {
      vi.mocked(fetch).mockResolvedValue({
        ok: false,
        statusText: 'Not Found',
      } as any)

      await expect(getExpansionMeta()).rejects.toThrow('Not Found')
    })
  })

  describe('streamQa', () => {
    it('should start streaming and return cancel function', () => {
      const mockStream = new ReadableStream({
        start(controller) {
          controller.enqueue(new TextEncoder().encode('data: {"type":"answer","delta":"Hello"}\n'))
          controller.enqueue(new TextEncoder().encode('data: [DONE]\n'))
          controller.close()
        },
      })

      vi.mocked(fetch).mockResolvedValue({
        ok: true,
        body: mockStream,
      } as any)

      const onAnswer = vi.fn()
      const onDone = vi.fn()
      const cancel = streamQa(1, 'test question', { onAnswer, onDone })

      expect(typeof cancel).toBe('function')

      // Cancel the stream
      cancel()
    })

    it('should handle answer chunks', async () => {
      const chunks = ['data: {"type":"answer","delta":"Hello"}\n', 'data: [DONE]\n']
      const mockStream = new ReadableStream({
        start(controller) {
          chunks.forEach(chunk => {
            controller.enqueue(new TextEncoder().encode(chunk))
          })
          controller.close()
        },
      })

      vi.mocked(fetch).mockResolvedValue({
        ok: true,
        body: mockStream,
      } as any)

      const onAnswer = vi.fn()
      const onDone = vi.fn()
      streamQa(1, 'test', { onAnswer, onDone })

      // Wait a bit for the stream to be processed
      await new Promise(resolve => setTimeout(resolve, 100))

      expect(onAnswer).toHaveBeenCalledWith('Hello')
      expect(onDone).toHaveBeenCalled()
    })

    it('should handle citations', async () => {
      const chunks = [
        'data: {"type":"citations","data":[{"id":1,"text":"test"}]}\n',
        'data: [DONE]\n',
      ]
      const mockStream = new ReadableStream({
        start(controller) {
          chunks.forEach(chunk => {
            controller.enqueue(new TextEncoder().encode(chunk))
          })
          controller.close()
        },
      })

      vi.mocked(fetch).mockResolvedValue({
        ok: true,
        body: mockStream,
      } as any)

      const onCitations = vi.fn()
      const onDone = vi.fn()
      streamQa(1, 'test', { onCitations, onDone })

      await new Promise(resolve => setTimeout(resolve, 100))

      expect(onCitations).toHaveBeenCalledWith([{ id: 1, text: 'test' }])
    })

    it('should handle retrieval log id', async () => {
      const chunks = [
        'data: {"type":"retrieval_log_id","data":123}\n',
        'data: [DONE]\n',
      ]
      const mockStream = new ReadableStream({
        start(controller) {
          chunks.forEach(chunk => {
            controller.enqueue(new TextEncoder().encode(chunk))
          })
          controller.close()
        },
      })

      vi.mocked(fetch).mockResolvedValue({
        ok: true,
        body: mockStream,
      } as any)

      const onRetrievalLogId = vi.fn()
      streamQa(1, 'test', { onRetrievalLogId })

      await new Promise(resolve => setTimeout(resolve, 100))

      expect(onRetrievalLogId).toHaveBeenCalledWith(123)
    })

    it('should handle verification event', async () => {
      const chunks = [
        'data: {"type":"verification","data":{"is_factual":true}}\n',
        'data: [DONE]\n',
      ]
      const mockStream = new ReadableStream({
        start(controller) {
          chunks.forEach(chunk => {
            controller.enqueue(new TextEncoder().encode(chunk))
          })
          controller.close()
        },
      })

      vi.mocked(fetch).mockResolvedValue({
        ok: true,
        body: mockStream,
      } as any)

      const onVerification = vi.fn()
      streamQa(1, 'test', { onVerification })

      await new Promise(resolve => setTimeout(resolve, 100))

      expect(onVerification).toHaveBeenCalledWith({ is_factual: true })
    })

    it('should handle refused event', async () => {
      const chunks = [
        'data: {"type":"refused","data":{"reason":"safety"}}\n',
        'data: [DONE]\n',
      ]
      const mockStream = new ReadableStream({
        start(controller) {
          chunks.forEach(chunk => {
            controller.enqueue(new TextEncoder().encode(chunk))
          })
          controller.close()
        },
      })

      vi.mocked(fetch).mockResolvedValue({
        ok: true,
        body: mockStream,
      } as any)

      const onRefused = vi.fn()
      streamQa(1, 'test', { onRefused })

      await new Promise(resolve => setTimeout(resolve, 100))

      expect(onRefused).toHaveBeenCalledWith({ reason: 'safety' })
    })

    it('should handle error events', async () => {
      const chunks = [
        'data: {"type":"error","message":"Something went wrong"}\n',
      ]
      const mockStream = new ReadableStream({
        start(controller) {
          chunks.forEach(chunk => {
            controller.enqueue(new TextEncoder().encode(chunk))
          })
          controller.close()
        },
      })

      vi.mocked(fetch).mockResolvedValue({
        ok: true,
        body: mockStream,
      } as any)

      const onError = vi.fn()
      streamQa(1, 'test', { onError })

      await new Promise(resolve => setTimeout(resolve, 100))

      expect(onError).toHaveBeenCalledWith('Something went wrong')
    })

    it('should handle HTTP errors', async () => {
      vi.mocked(fetch).mockResolvedValue({
        ok: false,
        text: async () => 'Unauthorized',
      } as any)

      const onError = vi.fn()
      streamQa(1, 'test', { onError })

      await new Promise(resolve => setTimeout(resolve, 100))

      expect(onError).toHaveBeenCalledWith('Unauthorized')
    })

    it('should handle missing response body', async () => {
      vi.mocked(fetch).mockResolvedValue({
        ok: true,
        body: null,
      } as any)

      const onError = vi.fn()
      streamQa(1, 'test', { onError })

      await new Promise(resolve => setTimeout(resolve, 100))

      expect(onError).toHaveBeenCalledWith('无响应体')
    })

    it('should include strategy option in request body', () => {
      const mockStream = new ReadableStream({
        start(controller) {
          controller.enqueue(new TextEncoder().encode('data: [DONE]\n'))
          controller.close()
        },
      })

      vi.mocked(fetch).mockResolvedValue({
        ok: true,
        body: mockStream,
      } as any)

      streamQa(1, 'test', { onAnswer: vi.fn() }, { strategy: 'smart' })

      expect(fetch).toHaveBeenCalledWith('/api/qa/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: 'Bearer test-token',
        },
        body: expect.stringContaining('"strategy":"smart"'),
        signal: expect.any(AbortSignal),
      })
    })

    it('should include conversationId option in request body', () => {
      const mockStream = new ReadableStream({
        start(controller) {
          controller.enqueue(new TextEncoder().encode('data: [DONE]\n'))
          controller.close()
        },
      })

      vi.mocked(fetch).mockResolvedValue({
        ok: true,
        body: mockStream,
      } as any)

      streamQa(1, 'test', { onAnswer: vi.fn() }, { conversationId: 123 })

      expect(fetch).toHaveBeenCalledWith('/api/qa/stream', {
        method: 'POST',
        headers: expect.any(Object),
        body: expect.stringContaining('"conversation_id":123'),
        signal: expect.any(AbortSignal),
      })
    })

    it('should cancel stream when abort is called', () => {
      const abortSpy = vi.fn()
      const mockStream = new ReadableStream({
        start(controller) {
          // Never close the stream
        },
      })

      vi.mocked(fetch).mockImplementation(() => {
        return Promise.resolve({
          ok: true,
          body: mockStream,
        } as any)
      })

      const cancel = streamQa(1, 'test', { onAnswer: vi.fn() })

      // Abort the request
      cancel()
    })
  })
})

/**
 * Dashboard API tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'
import * as dashboard from './dashboard'

vi.mock('axios', () => ({
  create: vi.fn(() => ({
    get: vi.fn(),
    post: vi.fn(),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
  })),
}))

// Mock the apiClient
vi.mock('./client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}))

import { apiClient } from './client'

const mockedApiClient = vi.mocked(apiClient)

describe('dashboard API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getRetrievalStats', () => {
    it('should call API without params', async () => {
      mockedApiClient.get.mockResolvedValue({ data: { total: 10 } } as any)

      const result = await dashboard.getRetrievalStats()

      expect(mockedApiClient.get).toHaveBeenCalledWith('/api/retrieval/stats')
      expect(result).toEqual({ total: 10 })
    })

    it('should include knowledgeBaseId in query', async () => {
      mockedApiClient.get.mockResolvedValue({ data: { total: 5 } } as any)

      await dashboard.getRetrievalStats({ knowledgeBaseId: 1 })

      expect(mockedApiClient.get).toHaveBeenCalledWith('/api/retrieval/stats?knowledge_base_id=1')
    })

    it('should include date range in query', async () => {
      mockedApiClient.get.mockResolvedValue({ data: { total: 5 } } as any)

      await dashboard.getRetrievalStats({ startDate: '2024-01-01', endDate: '2024-01-31' })

      expect(mockedApiClient.get).toHaveBeenCalledWith(
        expect.stringContaining('start_date=2024-01-01')
      )
      expect(mockedApiClient.get).toHaveBeenCalledWith(
        expect.stringContaining('end_date=2024-01-31')
      )
    })

    it('should include all params in query', async () => {
      mockedApiClient.get.mockResolvedValue({ data: { total: 5 } } as any)

      await dashboard.getRetrievalStats({
        knowledgeBaseId: 1,
        startDate: '2024-01-01',
        endDate: '2024-01-31',
      })

      expect(mockedApiClient.get).toHaveBeenCalledWith(
        '/api/retrieval/stats?knowledge_base_id=1&start_date=2024-01-01&end_date=2024-01-31'
      )
    })
  })

  describe('getStatsByDate', () => {
    it('should call API without params', async () => {
      mockedApiClient.get.mockResolvedValue({ data: { stats: [] } } as any)

      const result = await dashboard.getStatsByDate()

      expect(mockedApiClient.get).toHaveBeenCalledWith('/api/retrieval/stats/by-date')
    })

    it('should include knowledgeBaseId in query', async () => {
      mockedApiClient.get.mockResolvedValue({ data: { stats: [] } } as any)

      await dashboard.getStatsByDate({ knowledgeBaseId: 1 })

      expect(mockedApiClient.get).toHaveBeenCalledWith('/api/retrieval/stats/by-date?knowledge_base_id=1')
    })

    it('should include days in query', async () => {
      mockedApiClient.get.mockResolvedValue({ data: { stats: [] } } as any)

      await dashboard.getStatsByDate({ days: 7 })

      expect(mockedApiClient.get).toHaveBeenCalledWith('/api/retrieval/stats/by-date?days=7')
    })
  })

  describe('getStatsByKnowledgeBase', () => {
    it('should call API without params', async () => {
      mockedApiClient.get.mockResolvedValue({ data: { kbs: [] } } as any)

      await dashboard.getStatsByKnowledgeBase()

      expect(mockedApiClient.get).toHaveBeenCalledWith('/api/retrieval/stats/by-knowledge-base')
    })

    it('should include date range in query', async () => {
      mockedApiClient.get.mockResolvedValue({ data: { kbs: [] } } as any)

      await dashboard.getStatsByKnowledgeBase({
        startDate: '2024-01-01',
        endDate: '2024-01-31',
      })

      expect(mockedApiClient.get).toHaveBeenCalledWith(
        '/api/retrieval/stats/by-knowledge-base?start_date=2024-01-01&end_date=2024-01-31'
      )
    })
  })

  describe('getRetrievalLogs', () => {
    it('should call API without params', async () => {
      mockedApiClient.get.mockResolvedValue({ data: { logs: [] } } as any)

      await dashboard.getRetrievalLogs()

      expect(mockedApiClient.get).toHaveBeenCalledWith('/api/retrieval/logs')
    })

    it('should include knowledgeBaseId in query', async () => {
      mockedApiClient.get.mockResolvedValue({ data: { logs: [] } } as any)

      await dashboard.getRetrievalLogs({ knowledgeBaseId: 1 })

      expect(mockedApiClient.get).toHaveBeenCalledWith('/api/retrieval/logs?knowledge_base_id=1')
    })

    it('should include hasFeedback in query', async () => {
      mockedApiClient.get.mockResolvedValue({ data: { logs: [] } } as any)

      await dashboard.getRetrievalLogs({ hasFeedback: true })

      expect(mockedApiClient.get).toHaveBeenCalledWith('/api/retrieval/logs?has_feedback=true')
    })

    it('should include feedbackType in query', async () => {
      mockedApiClient.get.mockResolvedValue({ data: { logs: [] } } as any)

      await dashboard.getRetrievalLogs({ feedbackType: 'helpful' })

      expect(mockedApiClient.get).toHaveBeenCalledWith('/api/retrieval/logs?feedback_type=helpful')
    })

    it('should include pagination params', async () => {
      mockedApiClient.get.mockResolvedValue({ data: { logs: [] } } as any)

      await dashboard.getRetrievalLogs({ limit: 10, offset: 20 })

      expect(mockedApiClient.get).toHaveBeenCalledWith('/api/retrieval/logs?limit=10&offset=20')
    })
  })

  describe('getRetrievalLogDetail', () => {
    it('should call API with logId', async () => {
      mockedApiClient.get.mockResolvedValue({ data: { id: 1, query: 'test' } } as any)

      const result = await dashboard.getRetrievalLogDetail(1)

      expect(mockedApiClient.get).toHaveBeenCalledWith('/api/retrieval/logs/1')
      expect(result).toEqual({ id: 1, query: 'test' })
    })
  })

  describe('addFeedback', () => {
    it('should call POST API with data', async () => {
      const feedbackData = { log_id: 1, type: 'helpful' }
      mockedApiClient.post.mockResolvedValue({ data: { success: true } } as any)

      await dashboard.addFeedback(feedbackData)

      expect(mockedApiClient.post).toHaveBeenCalledWith('/api/retrieval/feedback', feedbackData)
    })
  })

  describe('markFeedbackAsSample', () => {
    it('should call POST API with sample flag', async () => {
      mockedApiClient.post.mockResolvedValue({ data: { success: true } } as any)

      await dashboard.markFeedbackAsSample(1, true)

      expect(mockedApiClient.post).toHaveBeenCalledWith('/api/retrieval/feedback/1/mark-sample', {
        is_sample: true,
      })
    })
  })

  describe('getProblemSamples', () => {
    it('should call API without params', async () => {
      mockedApiClient.get.mockResolvedValue({ data: { samples: [] } } as any)

      await dashboard.getProblemSamples()

      expect(mockedApiClient.get).toHaveBeenCalledWith('/api/retrieval/samples')
    })

    it('should include knowledgeBaseId in query', async () => {
      mockedApiClient.get.mockResolvedValue({ data: { samples: [] } } as any)

      await dashboard.getProblemSamples({ knowledgeBaseId: 1 })

      expect(mockedApiClient.get).toHaveBeenCalledWith('/api/retrieval/samples?knowledge_base_id=1')
    })

    it('should include pagination params', async () => {
      mockedApiClient.get.mockResolvedValue({ data: { samples: [] } } as any)

      await dashboard.getProblemSamples({ limit: 10, offset: 20 })

      expect(mockedApiClient.get).toHaveBeenCalledWith('/api/retrieval/samples?limit=10&offset=20')
    })
  })

  describe('getDashboardStats', () => {
    it('should call API without params', async () => {
      mockedApiClient.get.mockResolvedValue({ data: { total: 10 } } as any)

      const result = await dashboard.getDashboardStats()

      expect(mockedApiClient.get).toHaveBeenCalledWith('/api/retrieval/dashboard')
      expect(result).toEqual({ total: 10 })
    })

    it('should include kbId in query', async () => {
      mockedApiClient.get.mockResolvedValue({ data: { total: 5 } } as any)

      await dashboard.getDashboardStats({ kbId: 1 })

      expect(mockedApiClient.get).toHaveBeenCalledWith('/api/retrieval/dashboard?knowledge_base_id=1')
    })

    it('should include date range in query', async () => {
      mockedApiClient.get.mockResolvedValue({ data: { total: 5 } } as any)

      await dashboard.getDashboardStats({
        startDate: '2024-01-01',
        endDate: '2024-01-31',
      })

      expect(mockedApiClient.get).toHaveBeenCalledWith(
        '/api/retrieval/dashboard?start_date=2024-01-01&end_date=2024-01-31'
      )
    })
  })
})

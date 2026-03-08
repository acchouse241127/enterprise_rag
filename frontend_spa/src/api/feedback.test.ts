/**
 * Feedback API tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import * as feedback from './feedback'

// Mock the apiClient
vi.mock('./client', () => ({
  apiClient: {
    post: vi.fn(),
    get: vi.fn(),
  },
}))

import { apiClient } from './client'

const mockedApiClient = vi.mocked(apiClient)

describe('feedback API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('submitFeedback', () => {
    it('should call POST /api/retrieval/feedback with thumbs_up rating', async () => {
      const mockResponse = { data: { success: true } }
      mockedApiClient.post.mockResolvedValue(mockResponse)

      const result = await feedback.submitFeedback(1, 'thumbs_up', 'Great answer')

      expect(mockedApiClient.post).toHaveBeenCalledWith('/api/retrieval/feedback', {
        retrieval_log_id: 1,
        feedback_type: 'helpful',
        rating: 1,
        reason: 'Great answer',
        comment: 'Great answer',
      })
      expect(result).toEqual(mockResponse.data)
    })

    it('should call POST /api/retrieval/feedback with thumbs_down rating', async () => {
      const mockResponse = { data: { success: true } }
      mockedApiClient.post.mockResolvedValue(mockResponse)

      const result = await feedback.submitFeedback(1, 'thumbs_down', 'Bad answer')

      expect(mockedApiClient.post).toHaveBeenCalledWith('/api/retrieval/feedback', {
        retrieval_log_id: 1,
        feedback_type: 'not_helpful',
        rating: -1,
        reason: 'Bad answer',
        comment: 'Bad answer',
      })
    })

    it('should call POST without reason when not provided', async () => {
      const mockResponse = { data: { success: true } }
      mockedApiClient.post.mockResolvedValue(mockResponse)

      const result = await feedback.submitFeedback(1, 'thumbs_up')

      expect(mockedApiClient.post).toHaveBeenCalledWith('/api/retrieval/feedback', {
        retrieval_log_id: 1,
        feedback_type: 'helpful',
        rating: 1,
      })
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('getFeedback', () => {
    it('should return null when no feedbacks array', async () => {
      mockedApiClient.get.mockResolvedValue({
        data: { code: 200, data: { feedbacks: [] } },
      } as any)

      const result = await feedback.getFeedback(1)

      expect(result).toBeNull()
    })

    it('should return null when response has no data', async () => {
      mockedApiClient.get.mockResolvedValue({
        data: { code: 200 },
      } as any)

      const result = await feedback.getFeedback(1)

      expect(result).toBeNull()
    })

    it('should return feedback data when helpful', async () => {
      mockedApiClient.get.mockResolvedValue({
        data: {
          code: 200,
          data: {
            feedbacks: [
              {
                feedback_type: 'helpful',
                comment: 'Great answer',
                created_at: '2024-01-01T00:00:00Z',
              },
            ],
          },
        },
      } as any)

      const result = await feedback.getFeedback(1)

      expect(result).toEqual({
        data: {
          rating: 'thumbs_up',
          reason: 'Great answer',
          created_at: '2024-01-01T00:00:00Z',
        },
      })
    })

    it('should return feedback data when not_helpful', async () => {
      mockedApiClient.get.mockResolvedValue({
        data: {
          code: 200,
          data: {
            feedbacks: [
              {
                feedback_type: 'not_helpful',
                comment: 'Bad answer',
                created_at: '2024-01-01T00:00:00Z',
              },
            ],
          },
        },
      } as any)

      const result = await feedback.getFeedback(1)

      expect(result).toEqual({
        data: {
          rating: 'thumbs_down',
          reason: 'Bad answer',
          created_at: '2024-01-01T00:00:00Z',
        },
      })
    })

    it('should return empty reason when comment is missing', async () => {
      mockedApiClient.get.mockResolvedValue({
        data: {
          code: 200,
          data: {
            feedbacks: [
              {
                feedback_type: 'helpful',
                created_at: '2024-01-01T00:00:00Z',
              },
            ],
          },
        },
      } as any)

      const result = await feedback.getFeedback(1)

      expect(result?.data.reason).toBe('')
    })

    it('should return null on API error', async () => {
      mockedApiClient.get.mockRejectedValue(new Error('API Error'))

      const result = await feedback.getFeedback(1)

      expect(result).toBeNull()
    })
  })
})

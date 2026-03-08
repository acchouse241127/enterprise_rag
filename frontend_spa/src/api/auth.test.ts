/**
 * Auth API tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import * as auth from './auth'

// Mock the apiClient
vi.mock('./client', () => ({
  apiClient: {
    post: vi.fn(),
    get: vi.fn(),
  },
}))

import { apiClient } from './client'

const mockedApiClient = vi.mocked(apiClient)

describe('auth API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('login', () => {
    it('should call POST /api/auth/login with credentials', async () => {
      const mockResponse = {
        data: { access_token: 'test-token', user: { id: 1, username: 'test' } }
      }
      mockedApiClient.post.mockResolvedValue(mockResponse)

      const result = await auth.login('testuser', 'testpass')

      expect(mockedApiClient.post).toHaveBeenCalledWith('/api/auth/login', {
        username: 'testuser',
        password: 'testpass',
      })
      expect(result).toEqual(mockResponse.data)
    })

    it('should handle API errors', async () => {
      const error = new Error('Invalid credentials')
      mockedApiClient.post.mockRejectedValue(error)

      await expect(auth.login('wrong', 'wrong')).rejects.toThrow('Invalid credentials')
    })
  })

  describe('getMe', () => {
    it('should call GET /api/auth/me', async () => {
      const mockResponse = {
        data: { id: 1, username: 'test', email: 'test@example.com' }
      }
      mockedApiClient.get.mockResolvedValue(mockResponse)

      const result = await auth.getMe()

      expect(mockedApiClient.get).toHaveBeenCalledWith('/api/auth/me')
      expect(result).toEqual(mockResponse.data)
    })

    it('should handle API errors', async () => {
      const error = new Error('Unauthorized')
      mockedApiClient.get.mockRejectedValue(error)

      await expect(auth.getMe()).rejects.toThrow('Unauthorized')
    })
  })
})

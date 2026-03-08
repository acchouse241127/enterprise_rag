/**
 * Auth store tests
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useAuthStore } from './auth-store'

// Mock window.location for logout
const mockLocation = { href: '' }
Object.defineProperty(global.window, 'location', {
  writable: true,
  value: mockLocation,
})

describe('AuthStore', () => {
  beforeEach(() => {
    // Reset store state before each test
    useAuthStore.setState({ token: null, username: null })
    vi.clearAllMocks()
  })

  it('initializes with unauthenticated state', () => {
    const { result } = renderHook(() => useAuthStore())

    expect(result.current.token).toBeNull()
    expect(result.current.username).toBeNull()
    expect(result.current.isAuthenticated()).toBe(false)
  })

  it('has correct structure', () => {
    const { result } = renderHook(() => useAuthStore())

    expect(result.current).toHaveProperty('token')
    expect(result.current).toHaveProperty('username')
    expect(result.current).toHaveProperty('login')
    expect(result.current).toHaveProperty('logout')
    expect(result.current).toHaveProperty('isAuthenticated')
  })

  it('has login action', () => {
    const { result } = renderHook(() => useAuthStore())

    expect(typeof result.current.login).toBe('function')
  })

  it('has logout action', () => {
    const { result } = renderHook(() => useAuthStore())

    expect(typeof result.current.logout).toBe('function')
  })

  it('sets token and username on login', () => {
    const { result } = renderHook(() => useAuthStore())

    act(() => {
      result.current.login('test-token', 'test-user')
    })

    expect(result.current.token).toBe('test-token')
    expect(result.current.username).toBe('test-user')
    expect(result.current.isAuthenticated()).toBe(true)
  })

  it('clears token and username on logout', () => {
    const { result } = renderHook(() => useAuthStore())

    // First login
    act(() => {
      result.current.login('test-token', 'test-user')
    })
    expect(result.current.isAuthenticated()).toBe(true)

    // Then logout
    act(() => {
      result.current.logout()
    })

    expect(result.current.token).toBeNull()
    expect(result.current.username).toBeNull()
    expect(result.current.isAuthenticated()).toBe(false)
  })

  it('redirects to login on logout', () => {
    const { result } = renderHook(() => useAuthStore())

    act(() => {
      result.current.logout()
    })

    expect(mockLocation.href).toBe('/login')
  })
})

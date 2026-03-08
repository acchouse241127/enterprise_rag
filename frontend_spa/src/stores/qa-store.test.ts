/**
 * QA store tests
 */
import { describe, it, expect, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useQAStore } from './qa-store'

describe('QAStore', () => {
  beforeEach(() => {
    // Reset store state before each test
    useQAStore.setState({
      messages: [],
      streaming: false,
      currentAnswer: '',
      currentCitations: [],
      currentRetrievalLogId: undefined,
      currentVerification: null,
      currentRefused: null,
      conversationId: undefined,
      error: null,
    })
  })

  it('initializes with empty state', () => {
    const { result } = renderHook(() => useQAStore())

    expect(result.current.messages).toEqual([])
    expect(result.current.currentAnswer).toBe('')
    expect(result.current.currentCitations).toEqual([])
    expect(result.current.error).toBeNull()
    expect(result.current.streaming).toBe(false)
  })

  it('has correct initial state structure', () => {
    const { result } = renderHook(() => useQAStore())

    expect(result.current).toHaveProperty('messages')
    expect(result.current).toHaveProperty('streaming')
    expect(result.current).toHaveProperty('currentAnswer')
    expect(result.current).toHaveProperty('currentCitations')
    expect(result.current).toHaveProperty('error')
    expect(result.current).toHaveProperty('currentRetrievalLogId')
    expect(result.current).toHaveProperty('currentVerification')
    expect(result.current).toHaveProperty('currentRefused')
    expect(result.current).toHaveProperty('conversationId')
  })

  it('provides actions', () => {
    const { result } = renderHook(() => useQAStore())

    expect(typeof result.current.addUserMessage).toBe('function')
    expect(typeof result.current.appendAnswer).toBe('function')
    expect(typeof result.current.setCitations).toBe('function')
    expect(typeof result.current.resetChat).toBe('function')
    expect(typeof result.current.setFeedback).toBe('function')
    expect(typeof result.current.setError).toBe('function')
    expect(typeof result.current.setStreaming).toBe('function')
    expect(typeof result.current.finalizeAnswer).toBe('function')
    expect(typeof result.current.setRetrievalLogId).toBe('function')
    expect(typeof result.current.setVerification).toBe('function')
    expect(typeof result.current.setRefused).toBe('function')
  })

  it('adds user message', () => {
    const { result } = renderHook(() => useQAStore())

    act(() => {
      result.current.addUserMessage('Test question')
    })

    expect(result.current.messages).toHaveLength(1)
    expect(result.current.messages[0].role).toBe('user')
    expect(result.current.messages[0].content).toBe('Test question')
    expect(result.current.streaming).toBe(true)
  })

  it('appends answer text', () => {
    const { result } = renderHook(() => useQAStore())

    act(() => {
      result.current.addUserMessage('Test question')
      result.current.appendAnswer('Hello')
      result.current.appendAnswer(' world')
    })

    expect(result.current.currentAnswer).toBe('Hello world')
  })

  it('sets citations', () => {
    const { result } = renderHook(() => useQAStore())
    const citations = [{ id: 1, filename: 'test.pdf', snippet: 'test' }]

    act(() => {
      result.current.setCitations(citations)
    })

    expect(result.current.currentCitations).toEqual(citations)
  })

  it('sets verification data', () => {
    const { result } = renderHook(() => useQAStore())
    const verification = {
      confidence_score: 0.9,
      confidence_level: 'high' as const,
      faithfulness_score: 0.85,
      has_hallucination: false,
      citation_accuracy: 0.95,
    }

    act(() => {
      result.current.setVerification(verification)
    })

    expect(result.current.currentVerification).toEqual(verification)
  })

  it('sets refused info and stops streaming', () => {
    const { result } = renderHook(() => useQAStore())
    const refusedInfo = {
      reason: 'low_relevance' as const,
      message: 'Not enough relevant content',
    }

    act(() => {
      result.current.setRefused(refusedInfo)
    })

    expect(result.current.currentRefused).toEqual(refusedInfo)
    expect(result.current.streaming).toBe(false)
  })

  it('sets error', () => {
    const { result } = renderHook(() => useQAStore())

    act(() => {
      result.current.setError('test error')
    })

    expect(result.current.error).toBe('test error')
  })

  it('sets streaming state', () => {
    const { result } = renderHook(() => useQAStore())

    act(() => {
      result.current.setStreaming(true)
    })

    expect(result.current.streaming).toBe(true)

    act(() => {
      result.current.setStreaming(false)
    })

    expect(result.current.streaming).toBe(false)
  })

  it('resets chat', () => {
    const { result } = renderHook(() => useQAStore())

    // Add some state
    act(() => {
      result.current.addUserMessage('Test')
      result.current.appendAnswer('Answer')
      result.current.setError('Error')
    })

    expect(result.current.messages.length).toBeGreaterThan(0)
    expect(result.current.currentAnswer).not.toBe('')
    expect(result.current.error).not.toBeNull()

    // Reset
    act(() => {
      result.current.resetChat()
    })

    expect(result.current.messages).toEqual([])
    expect(result.current.currentAnswer).toBe('')
    expect(result.current.error).toBeNull()
    expect(result.current.streaming).toBe(false)
  })

  it('finalizes normal answer', () => {
    const { result } = renderHook(() => useQAStore())
    const citations = [{ id: 1, filename: 'test.pdf', snippet: 'test' }]

    act(() => {
      result.current.addUserMessage('Test question')
      result.current.appendAnswer('Test answer')
      result.current.setCitations(citations)
      result.current.setRetrievalLogId(123)
      result.current.setVerification({
        confidence_score: 0.9,
        confidence_level: 'high' as const,
        faithfulness_score: 0.85,
        has_hallucination: false,
        citation_accuracy: 0.95,
      })
    })

    act(() => {
      result.current.finalizeAnswer()
    })

    // Message should be added to messages array
    expect(result.current.messages).toHaveLength(2)
    expect(result.current.messages[1].role).toBe('assistant')
    expect(result.current.messages[1].content).toBe('Test answer')
    expect(result.current.messages[1].citations).toEqual(citations)
    expect(result.current.messages[1].retrievalLogId).toBe(123)
    expect(result.current.messages[1].verification).toBeDefined()

    // Current answer should be cleared
    expect(result.current.currentAnswer).toBe('')
    expect(result.current.streaming).toBe(false)
  })

  it('finalizes refused answer', () => {
    const { result } = renderHook(() => useQAStore())
    const refusedInfo = {
      reason: 'empty_retrieval' as const,
      message: 'No relevant content found',
    }

    act(() => {
      result.current.addUserMessage('Test question')
      result.current.setRefused(refusedInfo)
    })

    act(() => {
      result.current.finalizeAnswer()
    })

    // Refused message should be added to messages array
    expect(result.current.messages).toHaveLength(2)
    expect(result.current.messages[1].role).toBe('assistant')
    expect(result.current.messages[1].content).toBe('No relevant content found')
    expect(result.current.messages[1].refused).toEqual(refusedInfo)

    // Current answer should be cleared
    expect(result.current.currentAnswer).toBe('')
    expect(result.current.streaming).toBe(false)
  })

  it('finalizes empty answer (only stops streaming)', () => {
    const { result } = renderHook(() => useQAStore())

    act(() => {
      result.current.addUserMessage('Test question')
    })

    expect(result.current.streaming).toBe(true)

    act(() => {
      result.current.finalizeAnswer()
    })

    // No message should be added
    expect(result.current.messages).toHaveLength(1)

    // Streaming should stop
    expect(result.current.streaming).toBe(false)
  })

  it('sets feedback on message', () => {
    const { result } = renderHook(() => useQAStore())

    act(() => {
      result.current.addUserMessage('Test')
    })

    const messageId = result.current.messages[0].id

    act(() => {
      result.current.setFeedback(messageId, 'thumbs_up')
    })

    expect(result.current.messages[0].feedback).toBe('thumbs_up')
  })

  it('sets feedback to thumbs_down', () => {
    const { result } = renderHook(() => useQAStore())

    act(() => {
      result.current.addUserMessage('Test')
    })

    const messageId = result.current.messages[0].id

    act(() => {
      result.current.setFeedback(messageId, 'thumbs_down')
    })

    expect(result.current.messages[0].feedback).toBe('thumbs_down')
  })

  it('sets error with null', () => {
    const { result } = renderHook(() => useQAStore())

    act(() => {
      result.current.setError('test error')
    })

    expect(result.current.error).toBe('test error')

    act(() => {
      result.current.setError(null)
    })

    expect(result.current.error).toBeNull()
  })

  it('adds multiple messages in sequence', () => {
    const { result } = renderHook(() => useQAStore())

    act(() => {
      result.current.addUserMessage('Question 1')
      result.current.appendAnswer('Answer 1')
      result.current.finalizeAnswer()
      result.current.addUserMessage('Question 2')
      result.current.appendAnswer('Answer 2')
      result.current.finalizeAnswer()
    })

    expect(result.current.messages).toHaveLength(4)
    expect(result.current.messages[0].role).toBe('user')
    expect(result.current.messages[1].role).toBe('assistant')
    expect(result.current.messages[2].role).toBe('user')
    expect(result.current.messages[3].role).toBe('assistant')
  })

  it('updates existing message feedback', () => {
    const { result } = renderHook(() => useQAStore())

    act(() => {
      result.current.addUserMessage('Test')
    })

    const messageId = result.current.messages[0].id

    act(() => {
      result.current.setFeedback(messageId, 'thumbs_up')
    })
    expect(result.current.messages[0].feedback).toBe('thumbs_up')

    act(() => {
      result.current.setFeedback(messageId, 'thumbs_down')
    })
    expect(result.current.messages[0].feedback).toBe('thumbs_down')
  })

  it('does not update message with non-existent id', () => {
    const { result } = renderHook(() => useQAStore())

    act(() => {
      result.current.addUserMessage('Test')
      result.current.setFeedback('non-existent-id', 'thumbs_up')
    })

    // Original feedback should remain null
    expect(result.current.messages[0].feedback).toBeUndefined()
  })

  it('preserves message data when setting feedback', () => {
    const { result } = renderHook(() => useQAStore())

    act(() => {
      result.current.addUserMessage('Test question')
      result.current.appendAnswer('Answer')
      const citations = [{ id: 1, filename: 'test.pdf', snippet: 'test' }]
      result.current.setCitations(citations)
      result.current.setRetrievalLogId(123)
    })

    const messageId = result.current.messages[0].id

    act(() => {
      result.current.setFeedback(messageId, 'thumbs_up')
    })

    const updatedMessage = result.current.messages[0]
    expect(updatedMessage.id).toBe(messageId)
    expect(updatedMessage.content).toBe('Test question')
    expect(updatedMessage.role).toBe('user')
    expect(updatedMessage.feedback).toBe('thumbs_up')
  })

  it('sets verification to null', () => {
    const { result } = renderHook(() => useQAStore())

    act(() => {
      result.current.setVerification({
        confidence_score: 0.9,
        confidence_level: 'high' as const,
        faithfulness_score: 0.85,
        has_hallucination: false,
        citation_accuracy: 0.95,
      })
    })

    expect(result.current.currentVerification).not.toBeNull()

    act(() => {
      result.current.setVerification(null)
    })

    expect(result.current.currentVerification).toBeNull()
  })

  it('resets conversationId to undefined', () => {
    const { result } = renderHook(() => useQAStore())

    act(() => {
      result.current.resetChat()
    })

    // After resetChat, conversationId should be undefined
    expect(result.current.conversationId).toBeUndefined()
  })
})

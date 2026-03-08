/**
 * Custom QA Hook
 *
 * Provides a convenient hook that combines QA store state and React Query
 */

import { useCallback } from 'react'
import { useQAStore } from '../features/qa/qa.store'

/**
 * Hook for QA operations
 * Returns QA state and common actions in a single hook
 */
export function useQA() {
  const messages = useQAStore((state) => state.messages)
  const hasMessages = useQAStore((state) => state.messages.length > 0)
  const isStreaming = useQAStore((state) => state.streaming)
  const currentAnswer = useQAStore((state) => state.currentAnswer)
  const hasError = useQAStore((state) => !!state.error)

  const addUserMessage = useCallback(
    (content: string) => {
      const { addUserMessage } = useQAStore.getState()
      return addUserMessage(content)
    },
    [hasMessages]
  )

  const resetChat = useCallback(() => {
      const { resetChat } = useQAStore.getState()
      resetChat()
    }, [hasMessages])

  const setFeedback = useCallback(
    (messageId: string, feedback: 'thumbs_up' | 'thumbs_down') => {
      const { setFeedback } = useQAStore.getState()
      setFeedback(messageId, feedback)
    },
    [messages]
  )

  return {
    messages,
    hasMessages,
    isStreaming,
    currentAnswer,
    hasError,
    addUserMessage,
    resetChat,
    setFeedback,
  }
}

/**
 * QA Selectors
 *
 * Computed properties for QA state
 * Provides performant access to QA state without causing re-renders
 */

import {
  selectMessages,
  selectHasMessages,
  selectLastUserMessage,
  selectIsStreaming,
  selectCurrentAnswer,
  selectHasError,
  selectConversationId,
} from './qa.store'
import { useQAStore } from './qa.store'

/**
 * Selector: Get all messages
 */
export function useMessages() {
  return selectMessages(useQAStore())
}

/**
 * Selector: Check if there are messages
 */
export function useHasMessages() {
  return selectHasMessages(useQAStore())
}

/**
 * Selector: Get last user message (if any)
 */
export function useLastUserMessage() {
  return selectLastUserMessage(useQAStore())
}

/**
 * Selector: Check if QA is streaming
 */
export function useIsQAStreaming() {
  return selectIsStreaming(useQAStore())
}

/**
 * Selector: Get current assistant answer (while streaming or finalized)
 */
export function useCurrentAnswer() {
  return selectCurrentAnswer(useQAStore())
}

/**
 * Selector: Check if there is an error
 */
export function useQAHasError() {
  return selectHasError(useQAStore())
}

/**
 * Selector: Get current conversation ID
 */
export function useConversationId() {
  return selectConversationId(useQAStore())
}

/**
 * Selector: Get QA state object (for components that need multiple QA values)
 */
export function useQAState() {
  const messages = useMessages()
  const hasMessages = useHasMessages()
  const isStreaming = useIsQAStreaming()
  const currentAnswer = useCurrentAnswer()
  const hasError = useQAHasError()

  return {
    messages,
    hasMessages,
    isStreaming,
    currentAnswer,
    hasError,
  }
}

/**
 * QA Store module
 *
 * QA conversation state management with selectors for optimal performance
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Message, VerificationResult, RefusalInfo, Citation } from '@/stores/qa-store'

interface QAState {
  messages: Message[]
  currentAnswer: string
  currentCitations: Citation[]
  streaming: boolean
  error: string | null
  currentRetrievalLogId?: number
  currentVerification: VerificationResult | null
  currentRefused: RefusalInfo | null
  conversationId: string | undefined
  addUserMessage: (content: string) => string
  appendAnswer: (delta: string) => void
  setCitations: (citations: Citation[]) => void
  setFeedback: (messageId: string, feedback: 'thumbs_up' | 'thumbs_down') => void
  setError: (error: string | null) => void
  setStreaming: (streaming: boolean) => void
  resetChat: () => void
  finalizeAnswer: () => void
  setRetrievalLogId: (id: number) => void
  setVerification: (v: VerificationResult) => void
  setRefused: (info: RefusalInfo) => void
}

export const useQAStore = create<QAState>()(
  persist(
    (set, get) => ({
      messages: [],
      currentAnswer: '',
      currentCitations: [],
      streaming: false,
      error: null,
      currentRetrievalLogId: undefined,
      currentVerification: null,
      currentRefused: null,
      conversationId: undefined,
      addUserMessage: (content) => {
        const id = Date.now().toString()
        set({
          messages: [...get().messages, { id, role: 'user', content }],
          currentAnswer: '',
          currentCitations: [],
          streaming: true,
          error: null,
          currentRetrievalLogId: undefined,
          currentVerification: null,
          currentRefused: null,
        })
        return id
      },
      appendAnswer: (delta) => set((state) => ({
        currentAnswer: state.currentAnswer + delta,
      })),
      setCitations: (citations) => set({ currentCitations: citations }),
      setFeedback: (messageId, feedback) => set((state) => ({
        messages: state.messages.map((msg) =>
          msg.id === messageId ? { ...msg, feedback } : msg
        ),
      })),
      setError: (error) => set({ error, streaming: false }),
      setStreaming: (streaming) => set({ streaming }),
      resetChat: () => set({
        messages: [],
        currentAnswer: '',
        currentCitations: [],
        streaming: false,
        error: null,
        currentRetrievalLogId: undefined,
        currentVerification: null,
        currentRefused: null,
        conversationId: undefined,
      }),
      finalizeAnswer: () => {
        const state = get()
        const answer = state.currentAnswer.trim()

        if (state.currentRefused) {
          // 拒答消息
          const refusedMessage: Message = {
            id: `${Date.now()}_refused`,
            role: 'assistant',
            content: state.currentRefused.message,
            refused: state.currentRefused,
          }
          set({
            messages: [...state.messages, refusedMessage],
            streaming: false,
            currentAnswer: '',
            currentRefused: null,
          })
        } else if (answer) {
          // 正常回答
          const assistantMessage: Message = {
            id: `${Date.now()}_assistant`,
            role: 'assistant',
            content: answer,
            citations: state.currentCitations,
            retrievalLogId: state.currentRetrievalLogId,
            verification: state.currentVerification || undefined,
          }
          set({
            messages: [...state.messages, assistantMessage],
            streaming: false,
            currentAnswer: '',
            currentCitations: [],
            currentRetrievalLogId: undefined,
            currentVerification: null,
          })
        } else {
          set({ streaming: false })
        }
      },
      setRetrievalLogId: (id) => set({ currentRetrievalLogId: id }),
      setVerification: (v) => set({ currentVerification: v }),
      setRefused: (info) => set({ currentRefused: info, streaming: false }),
    }),
    {
      name: 'enterprise-rag-qa',
      version: 1,
    }
  )
)

// Selectors
export const selectMessages = (state: QAState) => state.messages
export const selectHasMessages = (state: QAState) => state.messages.length > 0
export const selectLastUserMessage = (state: QAState) => {
  const userMessages = state.messages.filter((m) => m.role === 'user')
  return userMessages[userMessages.length - 1] || null
}
export const selectIsStreaming = (state: QAState) => state.streaming
export const selectCurrentAnswer = (state: QAState) => state.currentAnswer
export const selectHasError = (state: QAState) => !!state.error
export const selectConversationId = (state: QAState) => state.conversationId

export default useQAStore

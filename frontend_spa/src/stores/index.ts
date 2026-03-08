/**
 * Stores Index - Backward compatible exports
 *
 * This file maintains backward compatibility by re-exporting from the new modular structure.
 * New code should import from @/stores/modules/index.ts directly.
 */

// Auth stores
export { useAuthStore } from './modules/features/auth/auth.store'

// Auth selectors (for components that need computed properties)
export function selectIsAuthenticated() {
  const store = require('./modules/features/auth/auth.store')
  return store.selectIsAuthenticated(store.getState())
}

export function selectToken() {
  const store = require('./modules/features/auth/auth.store')
  return store.selectToken(store.getState())
}

export function selectUsername() {
  const store = require('./modules/features/auth/auth.store')
  return store.selectUsername(store.getState())
}

// QA stores
export { useQAStore } from './modules/features/qa/qa.store'

// QA selectors
export function selectMessages() {
  const store = require('./modules/features/qa/qa.store')
  return store.selectMessages(store.getState())
}

export function selectHasMessages() {
  const store = require('./modules/features/qa/qa.store')
  return store.selectHasMessages(store.getState())
}

export function selectLastUserMessage() {
  const store = require('./modules/features/qa/qa.store')
  return store.selectLastUserMessage(store.getState())
}

export function selectIsStreaming() {
  const store = require('./modules/features/qa/qa.store')
  return store.selectIsStreaming(store.getState())
}

export function selectCurrentAnswer() {
  const store = require('./modules/features/qa/qa.store')
  return store.selectCurrentAnswer(store.getState())
}

export function selectHasError() {
  const store = require('./modules/features/qa/qa.store')
  return store.selectHasError(store.getState())
}

// UI stores (lazy export for optional modules)
export const useSidebarStore = () => {
  const store = require('./modules/ui/sidebar.store')
  return store.useSidebarStore()
}

export const useThemeStore = () => {
  const store = require('./modules/ui/theme.store')
  return store.useThemeStore()
}

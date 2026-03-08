# 前端状态管理优化文档

## 当前状态管理架构

### Store 模块（旧结构 - 逐步迁移中）

| Store | 用途 | 状态 |
|--------|------|------|
| `app-store.ts` | 全局 UI 状态 | 侧边栏折叠 |
| `auth-store.ts` | 认证状态 | token, username, login/logout |
| `qa-store.ts` | QA 对话状态 | messages, currentAnswer, citations, streaming |

### 技术栈

- **Zustand**: 轻量级状态管理库
- **React Hooks**: 用于消费状态
- **Persist Middleware**: localStorage 持久化

## ✅ 新的模块化架构（已实施）

### 目录结构

```
frontend_spa/src/stores/
├── index.ts                        # 旧版兼容导出（@/stores/modules/index.ts 优先）
├── modules/                        # 新的模块化结构（推荐使用）
│   ├── index.ts                  # 统一导出
│   ├── ui/                    # UI 状态模块
│   │   ├── sidebar.store.ts
│   │   └── theme.store.ts
│   ├── features/               # 功能状态模块
│   │   ├── auth/
│   │   │   ├── auth.store.ts       # 认证状态
│   │   │   └── auth.selectors.ts  # 认证选择器
│   │   └── qa/
│   │       ├── qa.store.ts         # QA 对话状态
│   │       └── qa.selectors.ts   # QA 选择器
│   └── hooks/                  # 自定义 Hooks（封装复杂逻辑）
│       ├── useAuth.ts         # 认证 Hook
│       └── useQA.ts          # QA Hook
```

### Store 模块详解

#### 1. UI 状态模块

**sidebar.store.ts**
```typescript
interface SidebarState {
  collapsed: boolean
  toggleSidebar: () => void
  setSidebarCollapsed: (collapsed: boolean) => void
}

export const useSidebarStore = create<SidebarState>()(
  persist(
    (set) => ({
        collapsed: false,
        toggleSidebar: () => set((state) => ({ collapsed: !state.collapsed })),
        setSidebarCollapsed: (collapsed) => set({ collapsed }),
      }),
      {
        name: 'enterprise-rag-sidebar',
        version: 1,
        partialize: (state) => ({ collapsed: state.collapsed }),
        merge: (persistConfig) => ({ storageVersion: 1, partialize: true }),
      }
  )
)
```

**theme.store.ts**
```typescript
interface ThemeState {
  theme: 'light' | 'dark'
  setTheme: (theme: 'light' | 'dark') => void
}

export const useThemeStore = create<ThemeState>()(
  (set) => ({
    theme: 'light',
    setTheme: (theme) => set({ theme }),
  })
)
```

#### 2. 功能状态模块

**auth.store.ts + auth.selectors.ts**
```typescript
interface AuthState {
  token: string | null
  username: string | null
  login: (token: string, username: string) => void
  logout: () => void
}

// Selectors - computed properties
interface AuthSelectors {
  isAuthenticated: (state: AuthState) => boolean
  token: (state: AuthState) => string | null
  username: (state: AuthState) => string | null
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
        token: null,
        username: null,
        login: (token, username) => set({ token, username }),
        logout: () => {
          set({ token: null, username: null })
          // Clear auth from localStorage (handled by persist middleware)
          window.location.href = '/login'
        },
      }),
      {
        name: 'enterprise-rag-auth',
        version: 1,
        merge: (persistConfig) => ({ storageVersion: 1, partialize: true }),
      }
  )
)

export const selectIsAuthenticated = (state: AuthState) => !!state.token
export const selectToken = (state: AuthState) => state.token
export const selectUsername = (state: AuthState) => state.username
```

**auth.selectors.ts**
```typescript
import { useAuthStore, selectIsAuthenticated, selectToken, selectUsername } from './auth.store'

export function useIsAuthenticated() {
  return selectIsAuthenticated(useAuthStore())
}

export function useAuthToken() {
  return selectToken(useAuthStore())
}

export function useAuthUser() {
  return selectUsername(useAuthStore())
}
```

**qa.store.ts + qa.selectors.ts**
```typescript
interface QAState {
  messages: Message[]
  currentAnswer: string
  currentCitations: any[]
  streaming: boolean
  error: string | null
}

// Selectors - computed properties for better performance
interface QASelectors {
  messages: (state: QAState) => Message[]
  hasMessages: (state: QAState) => boolean
  lastUserMessage: (state: QAState) => Message | null
  isStreaming: (state: QAState) => boolean
  currentAnswer: (state: QAState) => string
  hasError: (state: QAState) => boolean
}

export const useQAStore = create<QAState>()(
  persist(
      (set) => ({
        messages: [],
        currentAnswer: '',
        currentCitations: [],
        streaming: false,
        error: null,
        // ... actions
      }),
      {
        name: 'enterprise-rag-qa',
        version: 1,
        merge: (persistConfig) => ({ storageVersion: 1, partialize: true }),
      }
  )
)

export const selectMessages = (state: QAState) => state.messages
export const selectHasMessages = (state: QAState) => state.messages.length > 0
export const selectLastUserMessage = (state: QAState) => {
  const userMessages = state.messages.filter((m) => m.role === 'user')
  return userMessages[userMessages.length - 1] || null
}
export const selectIsStreaming = (state: QAState) => state.streaming
export const selectCurrentAnswer = (state: QAState) => state.currentAnswer
```

### 自定义 Hooks

**useAuth.ts**
```typescript
import { useCallback } from 'react'
import { useAuthStore, useAuthToken, useIsAuthenticated } from '../features/auth/auth.store'

export function useAuth() {
  const token = useAuthToken()
  const isAuthenticated = useIsAuthenticated()

  const login = useCallback(
    (token: string, username: string) => {
      const { login: loginAction } = useAuthStore.getState()
      loginAction(token, username)
    },
    [token, isAuthenticated]
  )

  const logout = useCallback(() => {
      const { logout } = useAuthStore.getState()
      logout()
    }, [isAuthenticated])

  return {
    token,
    isAuthenticated,
    login,
    logout,
  }
}
```

**useQA.ts**
```typescript
import { useCallback } from 'react'
import { useQAStore, useMessages, useHasMessages, useIsQAStreaming } from '../features/qa/qa.store'

export function useQA() {
  const messages = useMessages()
  const hasMessages = useHasMessages()
  const isStreaming = useIsQAStreaming()

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

  return {
    messages,
    hasMessages,
    isStreaming,
    addUserMessage,
    resetChat,
  }
}
```

### 迁移指南

#### 短期（推荐）

1. **使用新的模块化 stores**
   ```typescript
   // 替换：import { useAuthStore } from '@/stores/auth-store'
   // 新用法：import { useAuthStore, useAuthUser } from '@/stores/modules/index.ts'
   ```

2. **使用自定义 hooks**
   ```typescript
   // 替换：const { login } = useAuthStore()
   // 新用法：const { login, logout } = useAuth()
   ```

3. **逐步移除旧的 stores**
   - 保留 `@/stores/index.ts` 作为兼容层
   - 删除 `@/stores/auth-store.ts`（在所有组件迁移后）
   - 删除 `@/stores/qa-store.ts`（在所有组件迁移后）
```

### React Query 集成（Task 1.1）

#### 概念

React Query 提供了强大的数据获取和缓存功能：
- 自动缓存和去重
- 后台自动刷新
- 乐观更新
- 请求重试
- 窗口/页面焦点自动刷新

#### 已完成工作

1. **依赖安装** ✅
   ```bash
   npm install @tanstack/react-query @tanstack/react-query-devtools
   ```

2. **Query 客户端配置** ✅
   - `frontend_spa/src/lib/query-client.ts`
   - 配置了默认选项（stale time, gc time, refetch on window focus）

3. **环境变量配置** ✅
   - `.env.example` 添加 React Query 配置项

4. **自定义 Hook 示例** ✅
   - `frontend_spa/src/hooks/useKnowledgeBases.ts`

5. **页面示例迁移** ✅
   - `frontend_spa/src/pages/Dashboard.example.tsx`
   - 展示了如何在 Dashboard 页面迁移到 React Query

#### 迁移示例

**示例 1：使用 React Query 的 useKnowledgeBases**
```typescript
// 之前：直接 API 调用
import { getKnowledgeBases } from '@/api/knowledge-base'

function Dashboard() {
  const { data: kbs } = await getKnowledgeBases()
  return <div>{kbs?.data?.map(kb => <div>{kb.name}</div>)}</div>
}

// 之后：使用 React Query
import { useKnowledgeBases } from '@/hooks/useKnowledgeBases'

function Dashboard() {
  const { data: kbs, isLoading, error, refetch } = useKnowledgeBases()
  return (
    <div>
      {isLoading ? <div>加载中...</div> : <button onClick={refetch}>刷新</button>}
      {kbs?.data?.map(kb => <div>{kb.name}</div>)}
    </div>
  )
}
```

**示例 2：使用 React Query 获取统计数据**
```typescript
import { useQuery } from '@tanstack/react-query'

function Dashboard() {
  const {
    data: stats,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['statistics'],
    queryFn: getStatistics,
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: 60 * 1000, // 1 minute
  })
}
```

#### 实施建议

**阶段 1：逐步迁移（推荐）**
1. 优先迁移 Dashboard 页面
   - Dashboard 数据访问频繁，收益最大
   - 参考 `Dashboard.example.tsx` 实现

2. 次要迁移的页面列表：
   - QA 页面 - `useMessages()`, `useCurrentAnswer()`
   - KnowledgeBases 页面 - 使用 `useKnowledgeBases()`
   - 用户管理页面 - 需要创建对应的 hooks

3. 每个页面迁移后验证：
   - 运行 `npm run test:coverage` 确保测试通过
   - 测试缓存功能是否正常工作
   - 测试后台刷新是否自动触发

#### 中期（建议实施）

1. **添加更多 selectors**
   - 为复杂计算添加专门的 selectors
   - 减少组件内的重复计算

3. **添加性能监控**
   - 使用 React DevTools Profiler 分析状态更新性能
   - 监控不必要的重渲染

#### 长期（可选）

1. **考虑引入 Jotai**
   - 如团队规模扩大，状态管理复杂度显著增加
   - 提供 AI 辅助的自动状态管理建议

2. **添加性能监控**
   - 使用 React DevTools Profiler 分析状态更新性能
   - 监控不必要的重渲染

### 优势

1. **更好的代码组织**：按功能模块组织，便于维护
2. **性能优化**：selectors 减少不必要的重新计算
3. **类型安全**：完整的 TypeScript 类型定义
4. **可扩展性**：易于添加新的状态模块
5. **向后兼容**：保留旧导出，平滑迁移

### 使用示例

#### 使用新模块化 auth store
```typescript
import { useAuth, useAuthUser, useIsAuthenticated } from '@/stores/modules/index.ts'

function MyComponent() {
  const { isAuthenticated } = useIsAuthenticated()

  if (!isAuthenticated) {
    return <Login />
  }

  return <Dashboard />
}
```

#### 使用自定义 auth hook
```typescript
import { useAuth } from '@/stores/modules/hooks/useAuth'

function MyComponent() {
  const { login, logout } = useAuth()

  const handleLogin = () => {
    login('token', 'user')
  }

  const handleLogout = () => {
    logout()
  }
}
```

#### 使用 QA selectors
```typescript
import { useMessages, useHasMessages } from '@/stores/modules/index.ts'

function MessageList() {
  const { messages } = useMessages()
  return (
    <div>
      {messages.map(msg => (
        <MessageBubble key={msg.id} content={msg.content} />
      ))}
    </div>
  )
}
```

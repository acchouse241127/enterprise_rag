# React Query 集成指南

## 已完成的集成

1. ✅ 安装依赖
   ```bash
   npm install @tanstack/react-query @tanstack/react-query-devtools
   ```

2. ✅ 配置 QueryClient
   - 文件：`src/lib/react-query.tsx`
   - 功能：全局配置、默认重试策略、缓存时间、开发工具

3. ✅ 集成到应用
   - 修改：`src/main.tsx`
   - 使用 `ReactQueryProvider` 包裹应用

4. ✅ 创建 hooks
   - `src/hooks/use-knowledge-bases.ts` - 知识库 API hooks
   - `src/hooks/use-dashboard.ts` - 仪表板 API hooks

## 使用示例

### 基础用法

```tsx
import { useKnowledgeBases, useCreateKnowledgeBase } from '@/hooks/use-knowledge-bases'

function MyComponent() {
  // 获取知识库列表
  const { data: kbs, isLoading, error } = useKnowledgeBases()

  // 创建知识库
  const createMutation = useCreateKnowledgeBase()

  const handleCreate = async (name: string) => {
    await createMutation.mutateAsync({ name, chunk_mode: 'char' })
  }

  if (isLoading) return <p>加载中...</p>
  if (error) return <p>加载失败</p>

  return (
    <div>
      {kbs?.map(kb => <div key={kb.id}>{kb.name}</div>)}
      <button onClick={() => handleCreate('新知识库')}>
        创建
      </button>
    </div>
  )
}
```

### 自动缓存和重试

```tsx
import { useDocuments } from '@/hooks/use-knowledge-bases'

function DocumentList({ kbId }: { kbId: number }) {
  const { data: documents, isLoading, refetch } = useDocuments(kbId)

  // 数据会自动缓存 5 分钟
  // 失败会自动重试 3 次
  // 网络重连后会自动刷新

  return (
    <div>
      <button onClick={() => refetch()}>手动刷新</button>
      {isLoading ? <p>加载中...</p> : (
        <ul>
          {documents?.map(doc => <li key={doc.id}>{doc.filename}</li>)}
        </ul>
      )}
    </div>
  )
}
```

### 乐观更新

```tsx
import { useDeleteDocument } from '@/hooks/use-knowledge-bases'

function DocumentItem({ kbId, document }) {
  const deleteMutation = useDeleteDocument(kbId)

  const handleDelete = async () => {
    // 删除后自动刷新文档列表
    await deleteMutation.mutateAsync(document.id)
  }

  return (
    <div>
      <span>{document.filename}</span>
      <button onClick={handleDelete} disabled={deleteMutation.isPending}>
        {deleteMutation.isPending ? '删除中...' : '删除'}
      </button>
    </div>
  )
}
```

### 仪表板统计

```tsx
import { useRetrievalStats, useRetrievalLogs } from '@/hooks/use-dashboard'

function Dashboard() {
  // 获取检索统计
  const { data: stats, isLoading: statsLoading } = useRetrievalStats()

  // 获取检索日志
  const { data: logsData, isLoading: logsLoading } = useRetrievalLogs({
    limit: 20,
  })

  return (
    <div>
      <h2>统计</h2>
      {statsLoading ? <p>加载中...</p> : (
        <div>
          <p>总查询数: {stats?.total_queries || 0}</p>
          <p>平均响应时间: {stats?.avg_response_time_ms || 0}ms</p>
        </div>
      )}

      <h2>最近日志</h2>
      {logsLoading ? <p>加载中...</p> : (
        <ul>
          {logsData?.items.map(log => (
            <li key={log.id}>{log.query}</li>
          ))}
        </ul>
      )}
    </div>
  )
}
```

## 迁移指南

将现有代码迁移到 React Query：

### 1. 替换 useState + useEffect

**之前：**
```tsx
const [kbs, setKbs] = useState([])
const [loading, setLoading] = useState(true)

useEffect(() => {
  const load = async () => {
    setLoading(true)
    try {
      const res = await getKnowledgeBases()
      setKbs(res.items || [])
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }
  load()
}, [])
```

**之后：**
```tsx
const { data: kbs, isLoading, error } = useKnowledgeBases()

if (error) console.error(error)
```

### 2. 替换手动 API 调用

**之前：**
```tsx
const handleSubmit = async (name: string) => {
  const res = await createKnowledgeBase({ name, chunk_mode: 'char' })
  setKbs([...kbs, res.data])
}
```

**之后：**
```tsx
const createMutation = useCreateKnowledgeBase()

const handleSubmit = async (name: string) => {
  await createMutation.mutateAsync({ name, chunk_mode: 'char' })
  // 列表会自动刷新
}
```

## 高级功能

### 查询键（Query Keys）

```ts
// 知识库相关
knowledgeBaseKeys.all          // 所有知识库
knowledgeBaseKeys.lists()     // 知识库列表
knowledgeBaseKeys.detail(1)    // 知识库详情
knowledgeBaseKeys.documents(1) // 知识库的文档

// 仪表板相关
dashboardKeys.stats({ kbId: 1 })     // 统计数据
dashboardKeys.logs({ limit: 20 })     // 日志列表
dashboardKeys.samples({ kbId: 1 })  // 问题样本
```

### 手动失效缓存

```tsx
import { useQueryClient } from '@tanstack/react-query'

function MyComponent() {
  const queryClient = useQueryClient()

  const handleRefresh = () => {
    // 失效特定查询
    queryClient.invalidateQueries({
      queryKey: knowledgeBaseKeys.lists()
    })

    // 失效所有知识库相关查询
    queryClient.invalidateQueries({
      queryKey: knowledgeBaseKeys.all
    })
  }

  return <button onClick={handleRefresh}>刷新</button>
}
```

## 性能优化

1. **自动去重**：相同请求只会发送一次
2. **后台刷新**：数据过期时自动在后台更新
3. **选择性渲染**：只在数据变化时重新渲染组件
4. **离线支持**：失败请求自动重试

## 开发工具

React Query DevTools 已集成，开发模式下自动启用：
- 查看所有查询状态
- 手动触发/失效查询
- 查看查询键和依赖
- 测试加载和错误状态

访问：点击页面右下角的 React Query 图标

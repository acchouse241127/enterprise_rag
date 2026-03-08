/**
 * Dashboard page - React Query integration example
 *
 * This file demonstrates how to migrate existing API calls to React Query
 * for better caching, automatic refetching, and deduplication.
 */

import { useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getKnowledgeBases, getStatistics } from '@/api'
import { useKnowledgeBases as useKnowledgeBasesQuery } from '@/hooks/useKnowledgeBases'

/**
 * Dashboard page using React Query for data fetching
 *
 * Replaces direct API calls with React Query:
 * Before: const { data: kbs } = await getKnowledgeBases()
 * After: const { data: kbs, isLoading, error, refetch } = useKnowledgeBases()
 */
export default function Dashboard() {
  // Fetch knowledge bases with React Query
  const {
    data: kbs,
    isLoading: kbsLoading,
    error: kbsError,
    refetch: refetchKbs,
  } = useKnowledgeBases()

  // Fetch statistics with React Query
  const {
    data: stats,
    isLoading: statsLoading,
    error: statsError,
    refetch: refetchStats,
  } = useQuery({
    queryKey: ['statistics'],
    queryFn: async () => {
      const { getStatistics } = await import('@/api/dashboard')
      return getStatistics()
    },
    staleTime: 30 * 1000, // 30 seconds for stats
    refetchInterval: 60 * 1000, // 1 minute auto-refresh
  })

  // Refresh data on window focus (automatic refetch)
  useEffect(() => {
    refetchKbs()
    refetchStats()
  }, [refetchKbs, refetchStats])

  return (
    <div className="container">
      <h1>仪表板</h1>

      {/* Knowledge Bases with React Query */}
      <div className="mb-6">
        <h2>知识库</h2>
        {kbsLoading ? (
          <div>加载中...</div>
        ) : kbsError ? (
          <div className="error">加载失败: {kbsError.message}</div>
        ) : (
          <>
            <button onClick={() => refetchKbs()}>刷新</button>
            <div className="grid">
              {kbs?.data?.map((kb) => (
                <div key={kb.id} className="kb-card">
                  <h3>{kb.name}</h3>
                  <p>{kb.description}</p>
                  <small>{kb.document_count || 0} 文档</small>
                </div>
              ))}
            </div>
          </>
        )}
      </div>

      {/* Statistics with React Query */}
      <div className="mb-6">
        <h2>统计数据</h2>
        {statsLoading ? (
          <div>加载中...</div>
        ) : statsError ? (
          <div className="error">加载失败: {statsError.message}</div>
        ) : stats.data && (
          <div className="stats-grid">
            <div className="stat-card">
              <h3>总知识库</h3>
              <p className="stat-value">{stats.data.total_kbs || 0}</p>
            </div>
            <div className="stat-card">
              <h3>总文档</h3>
              <p className="stat-value">{stats.data.total_documents || 0}</p>
            </div>
            <div className="stat-card">
              <h3>总查询</h3>
              <p className="stat-value">{stats.data.total_queries || 0}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

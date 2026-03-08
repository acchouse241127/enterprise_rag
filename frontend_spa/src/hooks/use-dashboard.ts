/**
 * React Query hooks for Dashboard API
 */
import { useQuery } from '@tanstack/react-query'
import {
  getRetrievalStats,
  getStatsByDate,
  getStatsByKnowledgeBase,
  getRetrievalLogs,
  getRetrievalLogDetail,
  getProblemSamples,
  type RetrievalStatsResponse,
  type DailyStatsResponse,
  type KbStatsResponse,
  type RetrievalLogsResponse,
  type RetrievalLogDetailResponse,
  type ProblemSamplesResponse,
  type RetrievalStats as RetrievalStatsType,
} from '@/api'

// Parameter types (inline from dashboard.ts)
export type RetrievalStatsParams = {
  knowledgeBaseId?: number;
  startDate?: string;
  endDate?: string;
}

export type DailyStatsParams = {
  knowledgeBaseId?: number;
  days?: number;
}

export type KbStatsParams = {
  startDate?: string;
  endDate?: string;
}

export type RetrievalLogsParams = {
  knowledgeBaseId?: number;
  hasFeedback?: boolean;
  feedbackType?: "helpful" | "not_helpful";
  limit?: number;
  offset?: number;
}

export type ProblemSamplesParams = {
  knowledgeBaseId?: number;
  limit?: number;
  offset?: number;
}

// Query keys
export const dashboardKeys = {
  all: ['dashboard'] as const,
  stats: (params?: RetrievalStatsParams) => [...dashboardKeys.all, 'stats', params] as const,
  statsByDate: (params?: DailyStatsParams) => [...dashboardKeys.all, 'stats-by-date', params] as const,
  statsByKb: (params?: KbStatsParams) => [...dashboardKeys.all, 'stats-by-kb', params] as const,
  logs: (params?: RetrievalLogsParams) => [...dashboardKeys.all, 'logs', params] as const,
  logDetail: (id: number) => [...dashboardKeys.all, 'log-detail', id] as const,
  samples: (params?: ProblemSamplesParams) => [...dashboardKeys.all, 'samples', params] as const,
}

// ============ Stats ============

export function useRetrievalStats(params?: RetrievalStatsParams) {
  return useQuery({
    queryKey: dashboardKeys.stats(params),
    queryFn: () => getRetrievalStats(params),
    select: (data: RetrievalStatsResponse) => data.data as RetrievalStatsType,
  })
}

export function useStatsByDate(params?: DailyStatsParams) {
  return useQuery({
    queryKey: dashboardKeys.statsByDate(params),
    queryFn: () => getStatsByDate(params),
    select: (data: DailyStatsResponse) => data.data || [],
  })
}

export function useStatsByKnowledgeBase(params?: KbStatsParams) {
  return useQuery({
    queryKey: dashboardKeys.statsByKb(params),
    queryFn: () => getStatsByKnowledgeBase(params),
    select: (data: KbStatsResponse) => data.data || [],
  })
}

// ============ Logs ============

export function useRetrievalLogs(params?: RetrievalLogsParams) {
  return useQuery({
    queryKey: dashboardKeys.logs(params),
    queryFn: () => getRetrievalLogs(params),
    select: (data: RetrievalLogsResponse) => data,
    enabled: true,
  })
}

export function useRetrievalLogDetail(logId: number | null) {
  return useQuery({
    queryKey: dashboardKeys.logDetail(logId!),
    queryFn: () => getRetrievalLogDetail(logId!),
    select: (data: RetrievalLogDetailResponse) => data.data,
    enabled: logId !== null,
  })
}

// ============ Problem Samples ============

export function useProblemSamples(params?: ProblemSamplesParams) {
  return useQuery({
    queryKey: dashboardKeys.samples(params),
    queryFn: () => getProblemSamples(params),
    select: (data: ProblemSamplesResponse) => data,
    enabled: true,
  })
}

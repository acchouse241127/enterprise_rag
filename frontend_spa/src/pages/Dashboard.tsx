import { useEffect, useState, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
} from "recharts";
import {
  RefreshCw,
  MessageSquare,
  Star,
  Clock,
  ThumbsDown,
  ThumbsUp,
  Bookmark,
  FileText,
  ChevronLeft,
  ChevronRight,
  AlertCircle,
  Info,
  Loader2,
} from "lucide-react";
import {
  getRetrievalStats,
  getStatsByDate,
  getStatsByKnowledgeBase,
  getRetrievalLogs,
  addFeedback,
  markFeedbackAsSample,
  getProblemSamples,
} from "@/api/dashboard";
import { getKnowledgeBases } from "@/api/knowledge-base";
import type {
  RetrievalStats,
  DailyStats,
  KbStats,
  RetrievalLog,
  ProblemSample,
  KnowledgeBase,
} from "@/api/types";

const TIME_RANGE_OPTIONS = [
  { label: "7 天", value: 7 },
  { label: "14 天", value: 14 },
  { label: "30 天", value: 30 },
];

const FEEDBACK_FILTER_OPTIONS = [
  { label: "全部", value: "all" },
  { label: "有反馈", value: "has_feedback" },
  { label: "无反馈", value: "no_feedback" },
  { label: "有用", value: "helpful" },
  { label: "无用", value: "not_helpful" },
];

const PAGE_SIZE_OPTIONS = [10, 20, 50];

function formatNumber(val: number | null | undefined, decimals = 3): string {
  if (val === null || val === undefined) return "-";
  return val.toFixed(decimals);
}

function formatDate(dateStr: string): string {
  return dateStr?.slice(0, 16) || "";
}

export default function Dashboard() {
  // 筛选状态
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [selectedKbId, setSelectedKbId] = useState<number | null>(null);
  const [selectedDays, setSelectedDays] = useState(7);
  const [feedbackFilter, setFeedbackFilter] = useState("all");
  const [pageSize, setPageSize] = useState(10);
  const [logPage, setLogPage] = useState(0);

  // 数据状态
  const [stats, setStats] = useState<RetrievalStats | null>(null);
  const [dailyStats, setDailyStats] = useState<DailyStats[]>([]);
  const [kbStats, setKbStats] = useState<KbStats[]>([]);
  const [logs, setLogs] = useState<RetrievalLog[]>([]);
  const [logsTotal, setLogsTotal] = useState(0);
  const [samples, setSamples] = useState<ProblemSample[]>([]);
  const [samplesTotal, setSamplesTotal] = useState(0);

  // 加载状态
  const [loadingStats, setLoadingStats] = useState(true);
  const [loadingDaily, setLoadingDaily] = useState(false);
  const [loadingKb, setLoadingKb] = useState(false);
  const [loadingLogs, setLoadingLogs] = useState(false);
  const [loadingSamples, setLoadingSamples] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 操作状态
  const [actioningLogId, setActioningLogId] = useState<number | null>(null);

  // 获取知识库列表
  useEffect(() => {
    getKnowledgeBases()
      .then((res) => {
        if (res.data) {
          setKnowledgeBases(res.data);
        }
      })
      .catch(console.error);
  }, []);

  // 获取统计数据
  const fetchStats = useCallback(async () => {
    setLoadingStats(true);
    setError(null);
    try {
      const params: { knowledgeBaseId?: number } = {};
      if (selectedKbId) params.knowledgeBaseId = selectedKbId;
      const res = await getRetrievalStats(params);
      if (res.code === 0 && res.data) {
        setStats(res.data);
      } else {
        setStats(null);
      }
    } catch (err) {
      console.error(err);
      setError("加载统计数据失败");
    } finally {
      setLoadingStats(false);
    }
  }, [selectedKbId]);

  // 获取每日统计
  const fetchDailyStats = useCallback(async () => {
    setLoadingDaily(true);
    try {
      const params: { knowledgeBaseId?: number; days?: number } = { days: selectedDays };
      if (selectedKbId) params.knowledgeBaseId = selectedKbId;
      const res = await getStatsByDate(params);
      if (res.code === 0 && res.data) {
        setDailyStats(res.data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingDaily(false);
    }
  }, [selectedKbId, selectedDays]);

  // 获取按知识库统计
  const fetchKbStats = useCallback(async () => {
    setLoadingKb(true);
    try {
      const res = await getStatsByKnowledgeBase({});
      if (res.code === 0 && res.data) {
        setKbStats(res.data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingKb(false);
    }
  }, []);

  // 获取日志列表
  const fetchLogs = useCallback(async () => {
    setLoadingLogs(true);
    try {
      const params: {
        knowledgeBaseId?: number;
        hasFeedback?: boolean;
        feedbackType?: "helpful" | "not_helpful";
        limit?: number;
        offset?: number;
      } = { limit: pageSize, offset: logPage * pageSize };

      if (selectedKbId) params.knowledgeBaseId = selectedKbId;
      if (feedbackFilter === "has_feedback") params.hasFeedback = true;
      if (feedbackFilter === "no_feedback") params.hasFeedback = false;
      if (feedbackFilter === "helpful") params.feedbackType = "helpful";
      if (feedbackFilter === "not_helpful") params.feedbackType = "not_helpful";

      const res = await getRetrievalLogs(params);
      if (res.code === 0 && res.data) {
        setLogs(res.data.items || []);
        setLogsTotal(res.data.total || 0);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingLogs(false);
    }
  }, [selectedKbId, feedbackFilter, pageSize, logPage]);

  // 获取问题样本
  const fetchSamples = useCallback(async () => {
    setLoadingSamples(true);
    try {
      const params: { knowledgeBaseId?: number; limit: number; offset: number } = {
        limit: 20,
        offset: 0,
      };
      if (selectedKbId) params.knowledgeBaseId = selectedKbId;
      const res = await getProblemSamples(params);
      if (res.code === 0 && res.data) {
        setSamples(res.data.items || []);
        setSamplesTotal(res.data.total || 0);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingSamples(false);
    }
  }, [selectedKbId]);

  // 初始加载
  useEffect(() => {
    fetchStats();
    fetchDailyStats();
    fetchKbStats();
    fetchLogs();
    fetchSamples();
  }, [fetchStats, fetchDailyStats, fetchKbStats, fetchLogs, fetchSamples]);

  // 刷新所有数据
  const handleRefresh = () => {
    fetchStats();
    fetchDailyStats();
    fetchKbStats();
    fetchLogs();
    fetchSamples();
  };

  // 添加反馈
  const handleAddFeedback = async (logId: number, feedbackType: "helpful" | "not_helpful") => {
    setActioningLogId(logId);
    try {
      const res = await addFeedback({
        retrieval_log_id: logId,
        feedback_type: feedbackType,
        rating: feedbackType === "helpful" ? 5 : 1,
      });
      if (res.code === 0) {
        fetchStats();
        fetchLogs();
        fetchSamples();
      }
    } catch (err) {
      console.error(err);
    } finally {
      setActioningLogId(null);
    }
  };

  // 标记/取消问题样本
  const handleMarkSample = async (log: RetrievalLog, isMarked: boolean) => {
    if (!log.feedbacks || log.feedbacks.length === 0) {
      alert("请先添加反馈（有用/无用）后再标记样本");
      return;
    }
    const feedbackId = log.feedbacks[0].id;
    setActioningLogId(log.id);
    try {
      const res = await markFeedbackAsSample(feedbackId, !isMarked);
      if (res.code === 0) {
        fetchStats();
        fetchLogs();
        fetchSamples();
      }
    } catch (err) {
      console.error(err);
    } finally {
      setActioningLogId(null);
    }
  };

  // 指标卡片配置
  const statCards = [
    {
      title: "总查询数",
      value: stats?.total_queries ?? 0,
      icon: MessageSquare,
      color: "text-blue-600",
    },
    {
      title: "平均最高分",
      value: formatNumber(stats?.avg_top_score),
      icon: Star,
      color: "text-yellow-600",
    },
    {
      title: "平均响应时间",
      value: stats?.avg_response_time_ms ? `${Math.round(stats.avg_response_time_ms)} ms` : "-",
      icon: Clock,
      color: "text-green-600",
    },
    {
      title: "无用反馈率",
      value: stats?.not_helpful_ratio !== undefined ? `${(stats.not_helpful_ratio * 100).toFixed(1)}%` : "-",
      icon: ThumbsDown,
      color: "text-red-600",
    },
    {
      title: "有用反馈",
      value: stats?.helpful_count ?? 0,
      icon: ThumbsUp,
      color: "text-emerald-600",
    },
    {
      title: "无用反馈",
      value: stats?.not_helpful_count ?? 0,
      icon: ThumbsDown,
      color: "text-rose-600",
    },
    {
      title: "问题样本",
      value: stats?.sample_count ?? 0,
      icon: Bookmark,
      color: "text-purple-600",
    },
    {
      title: "平均返回块数",
      value: formatNumber(stats?.avg_chunks_returned, 1),
      icon: FileText,
      color: "text-cyan-600",
    },
  ];

  // 分页计算
  const totalPages = Math.ceil(logsTotal / pageSize) || 1;
  const currentPage = logPage + 1;

  // 无数据提示
  const showNoDataHint = stats?.total_queries === 0 && stats?.retrieval_log_enabled === true;
  const showDisabledHint = stats?.retrieval_log_enabled === false;

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">检索质量看板</h1>
      </div>

      {/* 筛选器 */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">筛选条件</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap items-end gap-4">
            <div className="w-48">
              <label className="text-sm text-muted-foreground mb-1 block">知识库</label>
              <Select
                value={selectedKbId?.toString() || "all"}
                onValueChange={(v) => {
                  setSelectedKbId(v === "all" ? null : Number(v));
                  setLogPage(0);
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="全部知识库" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部知识库</SelectItem>
                  {knowledgeBases.map((kb) => (
                    <SelectItem key={kb.id} value={kb.id.toString()}>
                      {kb.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="w-32">
              <label className="text-sm text-muted-foreground mb-1 block">时间范围</label>
              <Select
                value={selectedDays.toString()}
                onValueChange={(v) => setSelectedDays(Number(v))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {TIME_RANGE_OPTIONS.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value.toString()}>
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <Button onClick={handleRefresh} variant="outline" className="gap-2">
              <RefreshCw className="h-4 w-4" />
              刷新
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 无数据提示 */}
      {loadingStats ? (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin mr-2" />
          <span className="text-muted-foreground">加载统计数据...</span>
        </div>
      ) : error ? (
        <Card className="border-destructive">
          <CardContent className="flex items-center gap-2 py-4 text-destructive">
            <AlertCircle className="h-5 w-5" />
            {error}
          </CardContent>
        </Card>
      ) : showDisabledHint ? (
        <Card className="border-yellow-500">
          <CardContent className="py-4">
            <div className="flex items-start gap-2 text-yellow-600">
              <AlertCircle className="h-5 w-5 mt-0.5" />
              <div>
                <p className="font-medium">检索日志未启用</p>
                <p className="text-sm text-muted-foreground mt-1">
                  在后端 .env 中设置 RETRIEVAL_LOG_ENABLED=true 并重启后端。
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      ) : showNoDataHint ? (
        <Card>
          <CardContent className="py-4">
            <div className="flex items-start gap-2">
              <Info className="h-5 w-5 mt-0.5 text-blue-500" />
              <div>
                <p className="font-medium">无数据时的排查步骤</p>
                <ol className="text-sm text-muted-foreground mt-2 space-y-1 list-decimal list-inside">
                  <li>确认已成功完成至少一次 RAG 问答：在「问答对话」页选择知识库并提问</li>
                  <li>选择「全部知识库」：避免因筛选到未产生问答的知识库而看不到数据</li>
                  <li>点击本页筛选区右侧的「刷新」按钮（缓存约 10 秒）</li>
                  <li>若仍无数据：查看后端控制台/日志，搜索 retrieval_log create failed</li>
                  <li>确认 .env 未设置 RETRIEVAL_LOG_ENABLED=false</li>
                </ol>
              </div>
            </div>
          </CardContent>
        </Card>
      ) : null}

      {/* 核心指标卡片 */}
      {!showDisabledHint && !loadingStats && !error && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {statCards.map((card) => (
            <Card key={card.title}>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  {card.title}
                </CardTitle>
                <card.icon className={`h-4 w-4 ${card.color}`} />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{card.value}</div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* 查询趋势 */}
      {!showDisabledHint && !loadingStats && !error && (
        <Card>
          <CardHeader>
            <CardTitle>查询趋势</CardTitle>
          </CardHeader>
          <CardContent>
            {loadingDaily ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin" />
              </div>
            ) : dailyStats.length > 0 ? (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div>
                  <p className="text-sm text-muted-foreground mb-4">每日查询量</p>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={dailyStats}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis
                          dataKey="date"
                          tick={{ fontSize: 12 }}
                          tickFormatter={(v) => v.slice(5)}
                        />
                        <YAxis />
                        <Tooltip />
                        <Bar dataKey="query_count" fill="#3b82f6" name="查询数" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground mb-4">每日平均分数</p>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={dailyStats}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis
                          dataKey="date"
                          tick={{ fontSize: 12 }}
                          tickFormatter={(v) => v.slice(5)}
                        />
                        <YAxis domain={[0, 1]} />
                        <Tooltip />
                        <Line
                          type="monotone"
                          dataKey="avg_score"
                          stroke="#10b981"
                          name="平均分数"
                          dot={{ r: 4 }}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center py-8 text-muted-foreground">
                <Info className="h-5 w-5 mr-2" />
                暂无趋势数据
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* 检索日志列表 */}
      {!showDisabledHint && !loadingStats && !error && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>检索日志</CardTitle>
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <label className="text-sm text-muted-foreground">反馈状态</label>
                  <Select value={feedbackFilter} onValueChange={(v) => {
                    setFeedbackFilter(v);
                    setLogPage(0);
                  }}>
                    <SelectTrigger className="w-28">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {FEEDBACK_FILTER_OPTIONS.map((opt) => (
                        <SelectItem key={opt.value} value={opt.value}>
                          {opt.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex items-center gap-2">
                  <label className="text-sm text-muted-foreground">每页</label>
                  <Select
                    value={pageSize.toString()}
                    onValueChange={(v) => {
                      setPageSize(Number(v));
                      setLogPage(0);
                    }}
                  >
                    <SelectTrigger className="w-20">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {PAGE_SIZE_OPTIONS.map((size) => (
                        <SelectItem key={size} value={size.toString()}>
                          {size}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>
            <p className="text-sm text-muted-foreground">共 {logsTotal} 条记录</p>
          </CardHeader>
          <CardContent>
            {loadingLogs ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin" />
              </div>
            ) : logs.length > 0 ? (
              <div className="space-y-4">
                {logs.map((log) => {
                  const isSampleMarked = log.feedbacks?.some((fb) => fb.is_sample_marked);
                  const isActioning = actioningLogId === log.id;

                  return (
                    <div
                      key={log.id}
                      className="border rounded-lg p-4 hover:bg-muted/50 transition-colors"
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1 min-w-0">
                          <p className="font-medium truncate" title={log.query}>
                            Q: {log.query.length > 100 ? `${log.query.slice(0, 100)}...` : log.query}
                          </p>
                          <p className="text-sm text-muted-foreground mt-1">
                            ID: {log.id} | 时间: {formatDate(log.created_at)}
                          </p>
                          <p className="text-sm text-muted-foreground mt-1">
                            最高分: {formatNumber(log.top_chunk_score)} | 耗时:{" "}
                            {log.total_time_ms ? `${Math.round(log.total_time_ms)} ms` : "-"} | 块数:{" "}
                            {log.chunks_after_rerank ?? "-"}
                          </p>
                          {log.feedbacks && log.feedbacks.length > 0 && (
                            <div className="flex items-center gap-2 mt-2">
                              <span className="text-sm text-muted-foreground">反馈:</span>
                              {log.feedbacks.map((fb) => (
                                <span key={fb.id} className="flex items-center gap-1">
                                  {fb.feedback_type === "helpful" ? (
                                    <ThumbsUp className="h-4 w-4 text-emerald-600" />
                                  ) : (
                                    <ThumbsDown className="h-4 w-4 text-rose-600" />
                                  )}
                                  {fb.is_sample_marked && (
                                    <Bookmark className="h-4 w-4 text-purple-600" />
                                  )}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                        <div className="flex items-center gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleAddFeedback(log.id, "helpful")}
                            disabled={isActioning}
                            title="标记为有用"
                          >
                            {isActioning ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <ThumbsUp className="h-4 w-4" />
                            )}
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleAddFeedback(log.id, "not_helpful")}
                            disabled={isActioning}
                            title="标记为无用"
                          >
                            {isActioning ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <ThumbsDown className="h-4 w-4" />
                            )}
                          </Button>
                          <Button
                            size="sm"
                            variant={isSampleMarked ? "secondary" : "outline"}
                            onClick={() => handleMarkSample(log, !!isSampleMarked)}
                            disabled={isActioning || !log.feedbacks?.length}
                            title={isSampleMarked ? "取消问题样本标记" : "标记为问题样本"}
                          >
                            {isActioning ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <Bookmark className="h-4 w-4" />
                            )}
                          </Button>
                        </div>
                      </div>
                    </div>
                  );
                })}

                {/* 分页 */}
                <div className="flex items-center justify-between pt-4 border-t">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setLogPage((p) => p - 1)}
                    disabled={currentPage <= 1}
                  >
                    <ChevronLeft className="h-4 w-4 mr-1" />
                    上一页
                  </Button>
                  <span className="text-sm text-muted-foreground">
                    第 {currentPage} / {totalPages} 页
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setLogPage((p) => p + 1)}
                    disabled={currentPage >= totalPages}
                  >
                    下一页
                    <ChevronRight className="h-4 w-4 ml-1" />
                  </Button>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center py-8 text-muted-foreground">
                <Info className="h-5 w-5 mr-2" />
                暂无检索日志
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* 按知识库统计 */}
      {!showDisabledHint && !loadingStats && !error && (
        <Card>
          <CardHeader>
            <CardTitle>按知识库统计</CardTitle>
          </CardHeader>
          <CardContent>
            {loadingKb ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin" />
              </div>
            ) : kbStats.length > 0 ? (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>知识库</TableHead>
                    <TableHead className="text-right">查询数</TableHead>
                    <TableHead className="text-right">平均分数</TableHead>
                    <TableHead className="text-right">平均耗时(ms)</TableHead>
                    <TableHead className="text-right">有用反馈</TableHead>
                    <TableHead className="text-right">无用反馈</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {kbStats.map((kb) => (
                    <TableRow key={kb.knowledge_base_id}>
                      <TableCell>{kb.knowledge_base_name}</TableCell>
                      <TableCell className="text-right">{kb.query_count}</TableCell>
                      <TableCell className="text-right">{formatNumber(kb.avg_score)}</TableCell>
                      <TableCell className="text-right">
                        {kb.avg_time_ms ? Math.round(kb.avg_time_ms) : "-"}
                      </TableCell>
                      <TableCell className="text-right">{kb.helpful_count}</TableCell>
                      <TableCell className="text-right">{kb.not_helpful_count}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            ) : (
              <div className="flex items-center justify-center py-8 text-muted-foreground">
                <Info className="h-5 w-5 mr-2" />
                暂无按知识库统计数据
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* 问题样本列表 */}
      {!showDisabledHint && !loadingStats && !error && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>问题样本列表</CardTitle>
              <Button variant="outline" size="sm" onClick={fetchSamples} className="gap-2">
                <RefreshCw className="h-4 w-4" />
                刷新样本
              </Button>
            </div>
            <p className="text-sm text-muted-foreground">共 {samplesTotal} 个问题样本</p>
          </CardHeader>
          <CardContent>
            {loadingSamples ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin" />
              </div>
            ) : samples.length > 0 ? (
              <div className="space-y-4">
                {samples.map((sample) => (
                  <div
                    key={sample.id}
                    className="border rounded-lg p-4 hover:bg-muted/50 transition-colors"
                  >
                    <p className="font-medium truncate" title={sample.query}>
                      Q: {sample.query.length > 150 ? `${sample.query.slice(0, 150)}...` : sample.query}
                    </p>
                    <p className="text-sm text-muted-foreground mt-1">
                      ID: {sample.id} | 分数: {formatNumber(sample.top_chunk_score)} | 时间:{" "}
                      {formatDate(sample.created_at)}
                    </p>
                    {sample.feedbacks && sample.feedbacks.length > 0 && (
                      <div className="flex flex-wrap gap-2 mt-2">
                        {sample.feedbacks.map((fb) => (
                          <span
                            key={fb.id}
                            className="text-xs px-2 py-1 rounded bg-muted"
                          >
                            {fb.feedback_type === "helpful" ? "有用" : "无用"}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex items-center justify-center py-8 text-muted-foreground">
                <Info className="h-5 w-5 mr-2" />
                暂无问题样本（在看板中点击书签可标记问题样本）
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

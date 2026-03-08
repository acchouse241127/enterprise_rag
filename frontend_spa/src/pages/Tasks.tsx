import { useEffect, useState } from "react";
import { getTasks, cancelTask, Task } from "@/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { XCircle } from "lucide-react";

const STATUS_CONFIG: Record<string, { label: string; variant: "default" | "secondary" | "destructive" | "outline" }> = {
  pending: { label: "等待中", variant: "secondary" },
  running: { label: "进行中", variant: "default" },
  completed: { label: "已完成", variant: "outline" },
  failed: { label: "失败", variant: "destructive" },
  cancelled: { label: "已取消", variant: "secondary" },
};

export default function Tasks() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");

  const loadTasks = () => {
    setLoading(true);
    const params = statusFilter !== "all" ? { status: statusFilter } : undefined;
    getTasks(params)
      .then((res) => setTasks(res.tasks || []))
      .catch((e) => setError(e instanceof Error ? e.message : "加载失败"))
      .finally(() => setLoading(false));
  };

  useEffect(loadTasks, [statusFilter]);

  const handleCancel = async (taskId: number) => {
    try {
      await cancelTask(taskId);
      loadTasks();
    } catch (e) {
      setError(e instanceof Error ? e.message : "取消失败");
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString("zh-CN");
  };

  const formatDuration = (startTime?: string, endTime?: string) => {
    if (!startTime || !endTime) return "-";
    const start = new Date(startTime).getTime();
    const end = new Date(endTime).getTime();
    const seconds = Math.floor((end - start) / 1000);
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
    return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold">异步任务</h1>
        <div className="flex gap-3">
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="筛选状态" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部</SelectItem>
              <SelectItem value="pending">等待中</SelectItem>
              <SelectItem value="running">进行中</SelectItem>
              <SelectItem value="completed">已完成</SelectItem>
              <SelectItem value="failed">失败</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {error && (
        <p className="text-destructive p-3 bg-destructive/10 rounded">{error}</p>
      )}

      {loading ? (
        <p className="text-muted-foreground">加载中...</p>
      ) : tasks.length === 0 ? (
        <p className="text-muted-foreground">暂无任务</p>
      ) : (
        <div className="space-y-3">
          {tasks.map((task) => (
            <Card key={task.id}>
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">
                        {task.filename || task.name || task.task_type}
                      </span>
                      <Badge variant={STATUS_CONFIG[task.status]?.variant || "outline"}>
                        {STATUS_CONFIG[task.status]?.label || task.status}
                      </Badge>
                    </div>
                    <div className="mt-2 text-sm text-muted-foreground space-y-1">
                      <p>类型: {task.task_type}</p>
                      <p>创建时间: {formatDate(task.created_at)}</p>
                      {task.started_at && task.completed_at && (
                        <p>耗时: {formatDuration(task.started_at, task.completed_at)}</p>
                      )}
                      {task.error_message && (
                        <p className="text-destructive">错误: {task.error_message}</p>
                      )}
                    </div>
                    {task.status === "running" && task.progress > 0 && (
                      <div className="mt-3">
                        <Progress value={task.progress} className="h-2" />
                        <p className="text-xs text-muted-foreground mt-1">
                          {task.progress}%
                        </p>
                      </div>
                    )}
                  </div>
                  <div className="flex gap-2">
                    {task.status === "running" && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleCancel(task.id)}
                      >
                        <XCircle className="h-4 w-4 mr-1" />
                        取消
                      </Button>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

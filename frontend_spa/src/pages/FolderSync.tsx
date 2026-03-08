import { useState, useEffect, useCallback } from "react";
import {
  getKnowledgeBases,
  getFolderSyncConfig,
  updateFolderSyncConfig,
  deleteFolderSyncConfig,
  syncFolderNow,
  getFolderSyncLogs,
  getDockerStatus,
  mountDockerVolume,
} from "@/api";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  RefreshCw,
  CheckCircle,
  XCircle,
  Loader2,
  Trash2,
  Edit,
  Plus,
  Clock,
  FolderOpen,
  Info,
  FolderSearch,
  Copy,
  Terminal,
  Check,
  Container,
} from "lucide-react";
import type {
  KnowledgeBase,
  FolderSyncConfig,
  FolderSyncLog,
} from "@/api/types";
import {
  generateContainerPath,
  generateDockerGuide,
  copyToClipboard,
} from "@/lib/docker";

// 同步状态图标
const STATUS_ICONS: Record<string, { icon: typeof CheckCircle; color: string }> = {
  idle: { icon: Clock, color: "text-gray-500" },
  running: { icon: RefreshCw, color: "text-blue-500 animate-spin" },
  success: { icon: CheckCircle, color: "text-green-500" },
  failed: { icon: XCircle, color: "text-red-500" },
};

export default function FolderSyncPage() {
  // 知识库
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [selectedKbId, setSelectedKbId] = useState<number | null>(null);
  const [loadingKbs, setLoadingKbs] = useState(true);

  // 配置
  const [config, setConfig] = useState<FolderSyncConfig | null>(null);
  const [loadingConfig, setLoadingConfig] = useState(false);

  // 表单
  const [directoryPath, setDirectoryPath] = useState("");
  const [syncInterval, setSyncInterval] = useState(30);
  const [filePatterns, setFilePatterns] = useState(
    "*.txt,*.md,*.pdf,*.docx,*.xlsx,*.pptx,*.png,*.jpg,*.jpeg"
  );
  const [enabled, setEnabled] = useState(true);

  // 日志
  const [logs, setLogs] = useState<FolderSyncLog[]>([]);
  const [loadingLogs, setLoadingLogs] = useState(false);

  // 状态
  const [isEditing, setIsEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [folderPickerSupported, setFolderPickerSupported] = useState(false);

  // Docker 相关状态
  const [showDockerGuide, setShowDockerGuide] = useState(false);
  const [copiedRun, setCopiedRun] = useState(false);
  const [copiedCompose, setCopiedCompose] = useState(false);
  const [dockerStatus, setDockerStatus] = useState<any>(null);
  const [mounting, setMounting] = useState(false);
  const [showDockerStatus, setShowDockerStatus] = useState(false);

  // 获取当前选中的知识库信息
  const selectedKb = knowledgeBases.find((kb) => kb.id === selectedKbId);

  // 检查是否支持文件夹选择器
  useEffect(() => {
    setFolderPickerSupported("showDirectoryPicker" in window);
  }, []);

  // 加载 Docker 状态
  useEffect(() => {
    const loadDockerStatus = async () => {
      try {
        const res = await getDockerStatus();
        if (res.data) {
          setDockerStatus(res.data);
          setShowDockerStatus(res.data.enabled);
        }
      } catch (err) {
        console.error("加载 Docker 状态失败:", err);
      }
    };
    loadDockerStatus();
  }, []);

  // 选择本地文件夹
  const handleSelectFolder = async () => {
    try {
      const dirHandle = await window.showDirectoryPicker({
        mode: "read",
      });
      if (dirHandle) {
        // 获取文件夹路径（如果可用）
        // 注意：出于安全考虑，浏览器可能不会返回完整路径
        // 我们使用 name 作为显示，用户可能需要手动调整
        const path = dirHandle.name;
        setDirectoryPath(path);
        setSuccess(`已选择文件夹: ${path}。如需完整路径请手动编辑。`);
      }
    } catch (err) {
      // 用户取消选择不报错
      if (err instanceof Error && err.name !== "AbortError") {
        setError("选择文件夹失败: " + err.message);
      }
    }
  };

  // 生成容器内路径
  const handleGenerateContainerPath = () => {
    if (!selectedKbId) return;
    const containerPath = generateContainerPath(selectedKbId);
    setDirectoryPath(containerPath);
    setShowDockerGuide(true);
    setSuccess(`已自动生成容器内路径: ${containerPath}`);
  };

  // 复制 Docker 命令
  const handleCopyDockerRun = async () => {
    if (!selectedKbId || !directoryPath) return;
    const guide = generateDockerGuide({
      hostPath: directoryPath,
      containerPath: generateContainerPath(selectedKbId),
      kbId: selectedKbId,
      kbName: selectedKb?.name,
    });
    const success = await copyToClipboard(guide.runCommand);
    if (success) {
      setCopiedRun(true);
      setTimeout(() => setCopiedRun(false), 2000);
    }
  };

  // 复制 docker-compose 片段
  const handleCopyDockerCompose = async () => {
    if (!selectedKbId || !directoryPath) return;
    const guide = generateDockerGuide({
      hostPath: directoryPath,
      containerPath: generateContainerPath(selectedKbId),
      kbId: selectedKbId,
      kbName: selectedKb?.name,
    });
    const success = await copyToClipboard(guide.composeSnippet);
    if (success) {
      setCopiedCompose(true);
      setTimeout(() => setCopiedCompose(false), 2000);
    }
  };

  // 自动挂载到 Docker
  const handleAutoMount = async () => {
    if (!selectedKbId || !directoryPath) {
      setError("请先选择文件夹");
      return;
    }

    setMounting(true);
    setError("");
    setSuccess("");

    try {
      const res = await mountDockerVolume(
        selectedKbId,
        directoryPath,
        generateContainerPath(selectedKbId)
      );

      if (res.data?.success) {
        setSuccess(`挂载成功！容器 ${res.data.container_name} 已重新创建。预计 10-30 秒后服务恢复。`);
        // 刷新 Docker 状态
        const statusRes = await getDockerStatus();
        if (statusRes.data) {
          setDockerStatus(statusRes.data);
        }
      } else {
        setError(res.data?.message || "挂载失败");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "挂载失败");
    } finally {
      setMounting(false);
    }
  };

  // 加载知识库列表
  useEffect(() => {
    setLoadingKbs(true);
    getKnowledgeBases()
      .then((res) => {
        if (res.data) {
          setKnowledgeBases(res.data);
          if (res.data.length > 0 && !selectedKbId) {
            setSelectedKbId(res.data[0].id);
          }
        }
      })
      .catch(console.error)
      .finally(() => setLoadingKbs(false));
  }, []);

  // 加载配置
  const loadConfig = useCallback(async () => {
    if (!selectedKbId) return;
    setLoadingConfig(true);
    setError("");
    try {
      const res = await getFolderSyncConfig(selectedKbId);
      if (res.code === 0 && res.data) {
        setConfig(res.data);
        setDirectoryPath(res.data.directory_path);
        setSyncInterval(res.data.sync_interval_minutes);
        setFilePatterns(res.data.file_patterns);
        setEnabled(res.data.enabled);
        setIsEditing(false);
      } else {
        setConfig(null);
        setDirectoryPath("");
        setSyncInterval(30);
        setFilePatterns("*.txt,*.md,*.pdf,*.docx,*.xlsx,*.pptx,*.png,*.jpg,*.jpeg");
        setEnabled(true);
        setIsEditing(true);
      }
    } catch (err) {
      console.error(err);
      setError("加载配置失败");
    } finally {
      setLoadingConfig(false);
    }
  }, [selectedKbId]);

  // 加载日志
  const loadLogs = useCallback(async () => {
    if (!selectedKbId) return;
    setLoadingLogs(true);
    try {
      const res = await getFolderSyncLogs(selectedKbId, 20);
      if (res.code === 0 && res.data) {
        setLogs(res.data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingLogs(false);
    }
  }, [selectedKbId]);

  // 选择知识库后加载配置和日志
  useEffect(() => {
    if (selectedKbId) {
      loadConfig();
      loadLogs();
    }
  }, [selectedKbId, loadConfig, loadLogs]);

  // 保存配置
  const handleSave = async () => {
    if (!selectedKbId) return;
    if (!directoryPath.trim()) {
      setError("请输入同步目录");
      return;
    }
    setSaving(true);
    setError("");
    setSuccess("");
    try {
      const res = await updateFolderSyncConfig(selectedKbId, {
        directory_path: directoryPath.trim(),
        enabled,
        sync_interval_minutes: syncInterval,
        file_patterns: filePatterns,
      });
      if (res.code === 0) {
        setSuccess("配置保存成功");
        loadConfig();
        loadLogs();
      } else {
        setError(res.message || "保存失败");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "保存失败");
    } finally {
      setSaving(false);
    }
  };

  // 立即同步
  const handleSyncNow = async () => {
    if (!selectedKbId || !config) return;
    setSyncing(true);
    setError("");
    setSuccess("");
    try {
      const res = await syncFolderNow(selectedKbId);
      if (res.code === 0) {
        const data = res.data;
        setSuccess(
          `同步完成！扫描 ${data.files_scanned} 文件，新增 ${data.files_added}，更新 ${data.files_updated}，耗时 ${data.duration_seconds.toFixed(1)} 秒`
        );
        loadConfig();
        loadLogs();
      } else {
        setError(res.message || "同步失败");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "同步失败");
    } finally {
      setSyncing(false);
    }
  };

  // 删除配置
  const handleDelete = async () => {
    if (!selectedKbId || !config) return;
    if (!confirm("确定要删除此同步配置吗？")) return;
    setDeleting(true);
    setError("");
    try {
      const res = await deleteFolderSyncConfig(selectedKbId);
      if (res.code === 0) {
        setSuccess("配置已删除");
        setConfig(null);
        setIsEditing(true);
        setDirectoryPath("");
        loadLogs();
      } else {
        setError(res.message || "删除失败");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "删除失败");
    } finally {
      setDeleting(false);
    }
  };

  const getStatusIcon = (status: string) => {
    const config = STATUS_ICONS[status] || STATUS_ICONS.idle;
    const Icon = config.icon;
    return <Icon className={`h-4 w-4 ${config.color}`} />;
  };

  if (loadingKbs) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="h-6 w-6 animate-spin mr-2" />
        <span className="text-muted-foreground">加载中...</span>
      </div>
    );
  }

  if (knowledgeBases.length === 0) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-semibold">文件夹同步</h1>
        <Card>
          <CardContent className="py-8 text-center text-muted-foreground">
            暂无知识库，请先创建知识库
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold">文件夹同步</h1>
      </div>

      {/* 提示信息 */}
      {error && (
        <div className="flex items-center gap-2 p-3 bg-destructive/10 text-destructive rounded">
          <XCircle className="h-4 w-4" />
          {error}
        </div>
      )}
      {success && (
        <div className="flex items-center gap-2 p-3 bg-green-100 text-green-700 rounded">
          <CheckCircle className="h-4 w-4" />
          {success}
        </div>
      )}

      {/* 选择知识库 */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">选择知识库</CardTitle>
        </CardHeader>
        <CardContent>
          <Select
            value={selectedKbId?.toString() || ""}
            onValueChange={(v) => setSelectedKbId(Number(v))}
          >
            <SelectTrigger className="w-64">
              <SelectValue placeholder="选择知识库" />
            </SelectTrigger>
            <SelectContent>
              {knowledgeBases.map((kb) => (
                <SelectItem key={kb.id} value={kb.id.toString()}>
                  {kb.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      {/* Docker 状态卡片 */}
      {showDockerStatus && dockerStatus && (
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">Docker 状态</CardTitle>
              <div className="flex items-center gap-2 text-xs">
                <span className="text-muted-foreground">版本: {dockerStatus.docker_version || "未知"}</span>
                {dockerStatus.backend?.running ? (
                  <span className="flex items-center gap-1 text-green-600">
                    <CheckCircle className="h-3 w-3" />
                    Backend 运行中
                  </span>
                ) : (
                  <span className="flex items-center gap-1 text-red-600">
                    <XCircle className="h-3 w-3" />
                    Backend 未运行
                  </span>
                )}
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Info className="h-4 w-4" />
              <span>
                {dockerStatus.enabled
                  ? "自动挂载功能已启用。点击「自动挂载」可直接将文件夹挂载到容器（会重新创建容器）。"
                  : "自动挂载功能未启用，请手动执行 Docker 命令完成挂载。"}
              </span>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 配置区域 */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>同步配置</CardTitle>
              {config && !isEditing && (
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setIsEditing(true)}
                  >
                    <Edit className="h-4 w-4 mr-1" />
                    修改
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleDelete}
                    disabled={deleting}
                  >
                    <Trash2 className="h-4 w-4 mr-1" />
                    删除
                  </Button>
                </div>
              )}
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {loadingConfig ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin" />
              </div>
            ) : config && !isEditing ? (
              <>
                {/* 显示当前配置 */}
                <div className="space-y-3 p-4 bg-muted/50 rounded-lg">
                  <div className="flex items-center gap-2">
                    <FolderOpen className="h-4 w-4 text-muted-foreground" />
                    <span className="font-medium">同步目录:</span>
                    <code className="text-sm bg-background px-2 py-0.5 rounded">
                      {config.directory_path}
                    </code>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    文件模式: {config.file_patterns}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    同步间隔: {config.sync_interval_minutes} 分钟
                  </div>
                  <div className="text-sm">
                    状态:{" "}
                    <span
                      className={
                        config.enabled ? "text-green-600" : "text-red-600"
                      }
                    >
                      {config.enabled ? "已启用" : "已禁用"}
                    </span>
                  </div>
                </div>

                {/* 最近同步状态 */}
                {config.last_sync_at && (
                  <div className="space-y-2 p-4 border rounded-lg">
                    <div className="flex items-center gap-2 font-medium">
                      {getStatusIcon(config.last_sync_status || "idle")}
                      最近同步: {config.last_sync_status || "未知"}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      时间: {config.last_sync_at.slice(0, 16)}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      新增: {config.last_sync_files_added || 0} | 更新:{" "}
                      {config.last_sync_files_updated || 0} | 删除:{" "}
                      {config.last_sync_files_deleted || 0}
                    </div>
                    {config.last_sync_message && (
                      <div className="text-sm text-muted-foreground">
                        消息: {config.last_sync_message.slice(0, 80)}
                      </div>
                    )}
                  </div>
                )}

                {/* 操作按钮 */}
                <div className="flex gap-3 pt-2">
                  <Button onClick={handleSyncNow} disabled={syncing}>
                    {syncing ? (
                      <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                    ) : (
                      <RefreshCw className="h-4 w-4 mr-1" />
                    )}
                    {syncing ? "同步中..." : "立即同步"}
                  </Button>
                </div>
              </>
            ) : (
              <>
                {/* 创建/编辑表单 */}
                <div className="flex items-start gap-2 p-3 bg-blue-50 text-blue-700 rounded text-sm">
                  <Info className="h-4 w-4 mt-0.5 shrink-0" />
                  <div className="space-y-1">
                    <p>路径为服务端路径；Docker 部署时为容器内路径。</p>
                    {folderPickerSupported && (
                      <p>点击「选择文件夹」可浏览本地目录。</p>
                    )}
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>同步目录 *</Label>
                  <div className="flex flex-wrap gap-2">
                    <Input
                      value={directoryPath}
                      onChange={(e) => setDirectoryPath(e.target.value)}
                      placeholder="例如: /data/docs 或 C:\Documents\MyKnowledge"
                      className="flex-1 min-w-[200px]"
                    />
                    {folderPickerSupported && (
                      <Button
                        type="button"
                        variant="outline"
                        onClick={handleSelectFolder}
                        title="选择本地文件夹"
                      >
                        <FolderSearch className="h-4 w-4 mr-1" />
                        选择文件夹
                      </Button>
                    )}
                    <Button
                      type="button"
                      variant="outline"
                      onClick={handleGenerateContainerPath}
                      title="自动生成容器内路径"
                    >
                      <Container className="h-4 w-4 mr-1" />
                      生成容器路径
                    </Button>
                    {showDockerStatus && dockerStatus?.enabled && (
                      <Button
                        type="button"
                        variant="outline"
                        onClick={handleAutoMount}
                        disabled={mounting || !directoryPath}
                        title="自动挂载到 Docker 容器"
                      >
                        {mounting ? (
                          <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                        ) : (
                          <Terminal className="h-4 w-4 mr-1" />
                        )}
                        {mounting ? "挂载中..." : "自动挂载"}
                      </Button>
                    )}
                  </div>
                  {!folderPickerSupported && (
                    <p className="text-xs text-muted-foreground">
                      当前浏览器不支持文件夹选择，请手动输入路径
                    </p>
                  )}
                  <p className="text-xs text-muted-foreground">
                    Docker 部署：点击「生成容器路径」自动生成容器内路径（/data/sync/{selectedKbId}）
                  </p>
                </div>

                {/* Docker 挂载命令指南 */}
                {showDockerGuide && selectedKbId && directoryPath && (
                  <div className="space-y-3 p-4 bg-amber-50 border border-amber-200 rounded-lg">
                    <div className="flex items-center gap-2 text-amber-800 font-medium">
                      <Terminal className="h-4 w-4" />
                      Docker 挂载命令
                    </div>
                    <p className="text-sm text-amber-700">
                      您选择的路径将在容器内使用。请复制以下命令在宿主机执行以完成挂载：
                    </p>
                    
                    {/* docker run 命令 */}
                    <div className="space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-medium text-amber-800">docker run 方式:</span>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={handleCopyDockerRun}
                          className="h-6 px-2"
                        >
                          {copiedRun ? (
                            <Check className="h-3 w-3 text-green-600" />
                          ) : (
                            <Copy className="h-3 w-3" />
                          )}
                          {copiedRun ? "已复制" : "复制"}
                        </Button>
                      </div>
                      <pre className="text-xs bg-white p-2 rounded border overflow-x-auto whitespace-pre-wrap">
                        {generateDockerGuide({
                          hostPath: directoryPath,
                          containerPath: generateContainerPath(selectedKbId),
                          kbId: selectedKbId,
                          kbName: selectedKb?.name,
                        }).runCommand}
                      </pre>
                    </div>

                    {/* docker-compose 片段 */}
                    <div className="space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-medium text-amber-800">docker-compose 方式:</span>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={handleCopyDockerCompose}
                          className="h-6 px-2"
                        >
                          {copiedCompose ? (
                            <Check className="h-3 w-3 text-green-600" />
                          ) : (
                            <Copy className="h-3 w-3" />
                          )}
                          {copiedCompose ? "已复制" : "复制"}
                        </Button>
                      </div>
                      <pre className="text-xs bg-white p-2 rounded border overflow-x-auto whitespace-pre-wrap">
                        {generateDockerGuide({
                          hostPath: directoryPath,
                          containerPath: generateContainerPath(selectedKbId),
                          kbId: selectedKbId,
                          kbName: selectedKb?.name,
                        }).composeSnippet}
                      </pre>
                    </div>

                    {/* 操作步骤 */}
                    <div className="text-xs text-amber-700 space-y-1">
                      <p className="font-medium">操作步骤：</p>
                      <ol className="list-decimal list-inside space-y-0.5">
                        {generateDockerGuide({
                          hostPath: directoryPath,
                          containerPath: generateContainerPath(selectedKbId),
                          kbId: selectedKbId,
                        }).instructions.map((inst, i) => (
                          <li key={i}>{inst}</li>
                        ))}
                      </ol>
                    </div>
                  </div>
                )}

                <div className="space-y-2">
                  <Label>同步间隔（分钟）</Label>
                  <Input
                    type="number"
                    value={syncInterval}
                    onChange={(e) => setSyncInterval(Number(e.target.value))}
                    min={5}
                    max={1440}
                  />
                </div>

                <div className="space-y-2">
                  <Label>文件模式</Label>
                  <Input
                    value={filePatterns}
                    onChange={(e) => setFilePatterns(e.target.value)}
                    placeholder="*.pdf,*.docx,*.txt"
                  />
                  <p className="text-xs text-muted-foreground">
                    逗号分隔的文件匹配模式
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="enabled"
                    checked={enabled}
                    onChange={(e) => setEnabled(e.target.checked)}
                    className="h-4 w-4"
                  />
                  <Label htmlFor="enabled">立即启用</Label>
                </div>

                <div className="flex gap-3 pt-2">
                  <Button onClick={handleSave} disabled={saving}>
                    {saving ? (
                      <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                    ) : (
                      <Plus className="h-4 w-4 mr-1" />
                    )}
                    {saving ? "保存中..." : config ? "保存配置" : "创建配置"}
                  </Button>
                  {config && (
                    <Button
                      variant="outline"
                      onClick={() => setIsEditing(false)}
                    >
                      取消
                    </Button>
                  )}
                </div>
              </>
            )}
          </CardContent>
        </Card>

        {/* 同步日志 */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>同步日志</CardTitle>
              <Button
                variant="ghost"
                size="sm"
                onClick={loadLogs}
                disabled={loadingLogs}
              >
                <RefreshCw
                  className={`h-4 w-4 ${loadingLogs ? "animate-spin" : ""}`}
                />
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {loadingLogs ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin" />
              </div>
            ) : logs.length === 0 ? (
              <div className="flex items-center justify-center py-8 text-muted-foreground">
                <Info className="h-5 w-5 mr-2" />
                暂无同步日志
              </div>
            ) : (
              <div className="space-y-3 max-h-[500px] overflow-auto">
                {logs.map((log) => (
                  <div
                    key={log.id}
                    className="p-3 border rounded-lg hover:bg-muted/50 transition-colors"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        {getStatusIcon(log.status)}
                        <span className="font-medium capitalize">
                          {log.status}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {log.triggered_by === "manual" ? "手动" : "定时"}
                        </span>
                      </div>
                      <span className="text-xs text-muted-foreground">
                        {log.created_at.slice(0, 16)}
                      </span>
                    </div>
                    <div className="text-sm text-muted-foreground mb-1">
                      耗时: {log.duration_seconds.toFixed(1)}s | 扫描:{" "}
                      {log.files_scanned} | 新增: {log.files_added} | 更新:{" "}
                      {log.files_updated} | 删除: {log.files_deleted}
                      {log.files_failed > 0 && (
                        <span className="text-red-500">
                          {" "}
                          | 失败: {log.files_failed}
                        </span>
                      )}
                    </div>
                    {log.message && (
                      <div className="text-xs text-muted-foreground truncate">
                        {log.message}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

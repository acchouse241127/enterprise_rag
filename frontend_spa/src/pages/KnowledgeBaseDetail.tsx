import { useState, useRef } from "react";
import { useParams, Link } from "react-router-dom";
import {
  Document,
  getDocumentPreview,
  downloadDocumentFile,
  getDocumentVersions,
  activateDocumentVersion,
} from "@/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
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
  ChevronLeft,
  Upload,
  Link as LinkIcon,
  Eye,
  Download,
  History,
  RotateCcw,
  Trash2,
  FileText,
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
  useKnowledgeBase,
  useDocuments,
  useUploadDocument,
  useImportUrl,
  useDeleteDocument,
  useReparseDocument,
} from "@/hooks/use-knowledge-bases";

const STATUS_CONFIG: Record<string, { label: string; variant: "default" | "secondary" | "destructive" | "outline" }> = {
  pending: { label: "等待中", variant: "secondary" },
  parsing: { label: "解析中", variant: "default" },
  parsed: { label: "已解析", variant: "outline" },
  vectorized: { label: "已完成", variant: "outline" },
  parse_failed: { label: "解析失败", variant: "destructive" },
  parser_not_implemented: { label: "不支持", variant: "secondary" },
};

export default function KnowledgeBaseDetail() {
  const { id } = useParams<{ id: string }>();
  const kbId = Number(id);

  // 使用 React Query hooks
  const { data: kb, isLoading: kbLoading, error: kbError } = useKnowledgeBase(kbId || null);
  const { data: docs = [], isLoading: docsLoading, refetch: refetchDocs } = useDocuments(kbId, !!kbId);
  const uploadMutation = useUploadDocument(kbId);
  const importMutation = useImportUrl(kbId);
  const deleteMutation = useDeleteDocument(kbId);
  const reparseMutation = useReparseDocument(kbId);

  // URL 导入
  const [importUrlInput, setImportUrlInput] = useState("");

  // 上传
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);

  // 状态筛选
  const [statusFilter, setStatusFilter] = useState<string>("");

  // 预览
  const [previewContent, setPreviewContent] = useState<string>("");
  const [previewFilename, setPreviewFilename] = useState<string>("");
  const [showPreview, setShowPreview] = useState(false);
  const [previewLoading, setPreviewLoading] = useState(false);

  // 版本
  const [versions, setVersions] = useState<Document[]>([]);
  const [showVersions, setShowVersions] = useState(false);
  const [versionsLoading, setVersionsLoading] = useState(false);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      await uploadMutation.mutateAsync(file);
      if (fileInputRef.current) fileInputRef.current.value = "";
      refetchDocs();
    } catch (err) {
      console.error("上传失败:", err);
    }
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (!file) return;
    try {
      await uploadMutation.mutateAsync(file);
      refetchDocs();
    } catch (err) {
      console.error("上传失败:", err);
    }
  };

  const handleImportUrl = async () => {
    let url = importUrlInput.trim();
    if (!url) return;
    if (!url.startsWith("http://") && !url.startsWith("https://")) {
      url = "https://" + url;
    }
    try {
      await importMutation.mutateAsync(url);
      setImportUrlInput("");
      refetchDocs();
    } catch (err: unknown) {
      const res = (err as { response?: { status?: number; data?: { detail?: string; message?: string } } })
        ?.response;
      const msg =
        res?.data?.detail ??
        res?.data?.message ??
        (res?.status === 404
          ? "接口返回 404，请检查后端服务与 Nginx 代理是否正常（/api 是否转发到后端）"
          : err instanceof Error
            ? err.message
            : "导入失败");
      console.error("导入失败:", msg);
    }
  };

  const handleDelete = async (docId: number, filename: string) => {
    if (!window.confirm(`确定删除「${filename}」吗？`)) return;
    try {
      await deleteMutation.mutateAsync(docId);
    } catch (err) {
      console.error("删除失败:", err);
    }
  };

  const handleReparse = async (docId: number) => {
    try {
      await reparseMutation.mutateAsync(docId);
      refetchDocs();
    } catch (err) {
      console.error("重新解析失败:", err);
    }
  };

  const handlePreview = async (docId: number) => {
    setPreviewLoading(true);
    setPreviewContent("");
    setPreviewFilename("");
    setShowPreview(true);
    try {
      const res = await getDocumentPreview(docId);
      setPreviewContent(res.data?.content || "（暂无内容）");
      setPreviewFilename(res.data?.filename || "");
    } catch (e) {
      setPreviewContent(e instanceof Error ? e.message : "预览失败");
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleDownload = async (docId: number) => {
    try {
      const { blob, filename } = await downloadDocumentFile(docId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error("下载失败:", e);
    }
  };

  const handleShowVersions = async (docId: number) => {
    setVersionsLoading(true);
    setVersions([]);
    setShowVersions(true);
    try {
      const res = await getDocumentVersions(docId);
      setVersions(res.data || []);
    } catch (e) {
      console.error("获取版本失败:", e);
    } finally {
      setVersionsLoading(false);
    }
  };

  const handleActivateVersion = async (docId: number) => {
    try {
      await activateDocumentVersion(docId);
      refetchDocs();
      setShowVersions(false);
    } catch (e) {
      console.error("激活失败:", e);
    }
  };

  const formatSize = (bytes?: number) => {
    if (!bytes) return "-";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  };

  const filteredDocs = statusFilter === "all" || !statusFilter
    ? docs
    : docs.filter((d) => d.status === statusFilter);

  const loading = kbLoading || docsLoading;

  if (loading && !kb)
    return <p className="text-muted-foreground">加载中...</p>;

  if (kbError && !kb)
    return (
      <div className="space-y-4">
        <p className="text-destructive">{kbError.message || "加载失败"}</p>
        <Link to="/kb" className="text-primary hover:underline">
          返回知识库列表
        </Link>
      </div>
    );

  return (
    <div className="space-y-6">
      {/* 面包屑 */}
      <div className="flex items-center gap-2 text-sm">
        <Link to="/kb" className="text-primary hover:underline flex items-center gap-1">
          <ChevronLeft className="h-4 w-4" />
          返回知识库列表
        </Link>
      </div>

      <div>
        <h1 className="text-2xl font-semibold">{kb?.name || "知识库"} - 文档管理</h1>
        {kb?.description && <p className="text-muted-foreground mt-1">{kb.description}</p>}
      </div>

      {/* 错误提示 */}
      {uploadMutation.error && (
        <p className="text-destructive p-3 bg-destructive/10 rounded">
          上传失败: {uploadMutation.error instanceof Error ? uploadMutation.error.message : "未知错误"}
        </p>
      )}
      {importMutation.error && (
        <p className="text-destructive p-3 bg-destructive/10 rounded">
          导入失败: {importMutation.error instanceof Error ? importMutation.error.message : "未知错误"}
        </p>
      )}
      {deleteMutation.error && (
        <p className="text-destructive p-3 bg-destructive/10 rounded">
          删除失败: {deleteMutation.error instanceof Error ? deleteMutation.error.message : "未知错误"}
        </p>
      )}
      {reparseMutation.error && (
        <p className="text-destructive p-3 bg-destructive/10 rounded">
          重新解析失败: {reparseMutation.error instanceof Error ? reparseMutation.error.message : "未知错误"}
        </p>
      )}

      {/* 上传区域 */}
      <div
        className={cn(
          "border-2 border-dashed rounded-lg p-10 text-center transition-all",
          dragOver ? "border-primary bg-primary/5" : "border-muted-foreground/25 bg-muted/30"
        )}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".txt,.md,.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.png,.jpg,.jpeg,.mp3,.wav,.m4a,.flac,.mp4,.webm,.mov"
          onChange={handleUpload}
          className="hidden"
          id="file-upload"
        />
        <div className="mb-4">
          <Upload className="h-12 w-12 mx-auto text-muted-foreground" />
        </div>
        <p className="text-muted-foreground mb-4">
          拖拽文件到此处，或
          <label
            htmlFor="file-upload"
            className="text-primary cursor-pointer font-medium mx-1 hover:underline"
          >
            点击上传
          </label>
        </p>
        <p className="text-xs text-muted-foreground">
          支持: PDF, DOCX, TXT, MD, XLSX, PNG, JPG, MP3, MP4 等格式
        </p>
        {uploadMutation.isPending && <p className="mt-4 text-primary">上传中...</p>}
      </div>

      {/* URL 导入 */}
      <div className="flex gap-3">
        <div className="relative flex-1 max-w-md">
          <LinkIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            type="url"
            value={importUrlInput}
            onChange={(e) => setImportUrlInput(e.target.value)}
            placeholder="从 URL 导入（输入网址）"
            className="pl-10"
          />
        </div>
        <Button onClick={handleImportUrl} disabled={importMutation.isPending || !importUrlInput.trim()}>
          {importMutation.isPending ? "导入中..." : "导入"}
        </Button>
      </div>

      {/* 文档列表 */}
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-semibold">文档列表 ({filteredDocs.length})</h2>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="状态筛选" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="">全部</SelectItem>
            <SelectItem value="pending">等待中</SelectItem>
            <SelectItem value="parsing">解析中</SelectItem>
            <SelectItem value="vectorized">已完成</SelectItem>
            <SelectItem value="parse_failed">失败</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {filteredDocs.length === 0 ? (
        <p className="text-muted-foreground">暂无文档，上传文件或导入网址开始</p>
      ) : (
        <Card>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>文件名</TableHead>
                <TableHead className="w-24">类型</TableHead>
                <TableHead className="w-24">大小</TableHead>
                <TableHead className="w-28">状态</TableHead>
                <TableHead className="w-52">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredDocs.map((doc) => (
                <TableRow key={doc.id}>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <FileText className="h-4 w-4 text-muted-foreground" />
                      <span className="font-medium">{doc.title || doc.filename}</span>
                    </div>
                    {doc.parser_message && (
                      <p className="text-xs text-muted-foreground mt-1">{doc.parser_message}</p>
                    )}
                  </TableCell>
                  <TableCell className="text-muted-foreground">{doc.file_type || "-"}</TableCell>
                  <TableCell className="text-muted-foreground">{formatSize(doc.file_size)}</TableCell>
                  <TableCell>
                    <Badge variant={STATUS_CONFIG[doc.status]?.variant || "outline"}>
                      {STATUS_CONFIG[doc.status]?.label || doc.status}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-1">
                      <Button variant="outline" size="sm" onClick={() => handlePreview(doc.id)}>
                        <Eye className="h-3 w-3" />
                      </Button>
                      <Button variant="outline" size="sm" onClick={() => handleDownload(doc.id)}>
                        <Download className="h-3 w-3" />
                      </Button>
                      <Button variant="outline" size="sm" onClick={() => handleShowVersions(doc.id)}>
                        <History className="h-3 w-3" />
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleReparse(doc.id)}
                        disabled={doc.status === "parsing" || reparseMutation.isPending}
                      >
                        <RotateCcw className="h-3 w-3" />
                      </Button>
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => handleDelete(doc.id, doc.filename)}
                        disabled={deleteMutation.isPending}
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>
      )}

      {/* 预览弹窗 */}
      <Dialog open={showPreview} onOpenChange={setShowPreview}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-auto">
          <DialogHeader>
            <DialogTitle>{previewFilename || "文档预览"}</DialogTitle>
          </DialogHeader>
          {previewLoading ? (
            <p className="text-muted-foreground">加载中...</p>
          ) : (
            <pre className="whitespace-pre-wrap leading-relaxed text-sm">{previewContent}</pre>
          )}
        </DialogContent>
      </Dialog>

      {/* 版本弹窗 */}
      <Dialog open={showVersions} onOpenChange={setShowVersions}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>版本历史</DialogTitle>
          </DialogHeader>
          {versionsLoading ? (
            <p className="text-muted-foreground">加载中...</p>
          ) : versions.length === 0 ? (
            <p className="text-muted-foreground">暂无版本记录</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>版本</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead>操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {versions.map((v) => (
                  <TableRow key={v.id}>
                    <TableCell>v{v.version || 1}</TableCell>
                    <TableCell>
                      <Badge variant={STATUS_CONFIG[v.status]?.variant || "outline"}>
                        {STATUS_CONFIG[v.status]?.label || v.status}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Button variant="outline" size="sm" onClick={() => handleActivateVersion(v.id)}>
                        激活此版本
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

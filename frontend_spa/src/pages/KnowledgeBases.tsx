import { useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Plus, Search, Edit, Trash2, Database } from "lucide-react";
import { ChunkModeSelect } from "@/components/knowledge-base/ChunkModeSelect";
import { ParentRetrievalConfig } from "@/components/knowledge-base/ParentRetrievalConfig";
import { RetrievalStrategySelect } from "@/components/knowledge-base/RetrievalStrategySelect";
import {
  useKnowledgeBases,
  useCreateKnowledgeBase,
  useDeleteKnowledgeBase,
} from "@/hooks/use-knowledge-bases";

type ChunkMode = "char" | "sentence" | "token" | "chinese_recursive";
type RetrievalStrategy = "smart" | "precise" | "fast" | "deep";

interface CreateFormData {
  name: string;
  description: string;
  chunk_mode: ChunkMode;
  parent_retrieval_mode: "physical" | "dynamic" | "off";
  dynamic_expand_n: number;
  default_retrieval_strategy: RetrievalStrategy | "";
}

export default function KnowledgeBases() {
  // 使用 React Query hooks
  const { data: list, isLoading: loading, error: fetchError } = useKnowledgeBases();
  const createMutation = useCreateKnowledgeBase();
  const deleteMutation = useDeleteKnowledgeBase();

  const [searchQuery, setSearchQuery] = useState("");

  // 创建表单状态
  const [showCreate, setShowCreate] = useState(false);
  const [formData, setFormData] = useState<CreateFormData>({
    name: "",
    description: "",
    chunk_mode: "chinese_recursive",
    parent_retrieval_mode: "dynamic",
    dynamic_expand_n: 2,
    default_retrieval_strategy: "",
  });

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim()) return;

    try {
      await createMutation.mutateAsync({
        name: formData.name.trim(),
        description: formData.description.trim() || undefined,
        chunk_mode: formData.chunk_mode,
        parent_retrieval_mode: formData.parent_retrieval_mode,
        dynamic_expand_n: formData.dynamic_expand_n,
        default_retrieval_strategy: formData.default_retrieval_strategy || undefined,
      });
      setFormData({
        name: "",
        description: "",
        chunk_mode: "chinese_recursive",
        parent_retrieval_mode: "dynamic",
        dynamic_expand_n: 2,
        default_retrieval_strategy: "",
      });
      setShowCreate(false);
    } catch (e) {
      console.error("创建知识库失败:", e);
    }
  };

  const handleDelete = async (id: number, name: string) => {
    if (!window.confirm(`确定删除知识库「${name}」吗？此操作不可恢复。`)) return;
    try {
      await deleteMutation.mutateAsync(id);
    } catch (e) {
      console.error("删除知识库失败:", e);
    }
  };

  const filteredList = list?.filter(
    (kb) =>
      kb.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      kb.description?.toLowerCase().includes(searchQuery.toLowerCase())
  ) || [];

  if (loading) return <p className="text-muted-foreground">加载中...</p>;
  if (fetchError && !list)
    return <p className="text-destructive">{fetchError.message || "加载失败"}</p>;

  return (
    <div>
      {/* 头部 */}
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-semibold">知识库管理</h1>
        <Button onClick={() => setShowCreate(true)}>
          <Plus className="h-4 w-4 mr-1" />
          新建知识库
        </Button>
      </div>

      {/* 搜索框 */}
      <div className="mb-6">
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            type="text"
            placeholder="搜索知识库..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      {createMutation.error && (
        <p className="text-destructive mb-4">
          {createMutation.error instanceof Error ? createMutation.error.message : "创建失败"}
        </p>
      )}

      {deleteMutation.error && (
        <p className="text-destructive mb-4">
          {deleteMutation.error instanceof Error ? deleteMutation.error.message : "删除失败"}
        </p>
      )}

      {/* 知识库列表 */}
      {filteredList.length === 0 ? (
        <p className="text-muted-foreground">
          {searchQuery
            ? "未找到匹配的知识库"
            : "暂无知识库，点击上方按钮创建第一个知识库"}
        </p>
      ) : (
        <div className="space-y-3">
          {filteredList.map((kb) => (
            <div
              key={kb.id}
              className="flex items-center justify-between p-4 bg-card border rounded-lg shadow-sm hover:shadow transition-shadow"
            >
              <div className="flex-1">
                <Link
                  to={`/kb/${kb.id}`}
                  className="text-lg font-semibold text-primary hover:underline flex items-center gap-2"
                >
                  <Database className="h-5 w-5" />
                  {kb.name}
                </Link>
                {kb.description && (
                  <p className="mt-1 text-sm text-muted-foreground">
                    {kb.description}
                  </p>
                )}
                <div className="mt-2 flex items-center gap-4 text-xs text-muted-foreground">
                  {kb.created_at && (
                    <span>创建于 {new Date(kb.created_at).toLocaleDateString("zh-CN")}</span>
                  )}
                  {kb.chunk_mode && (
                    <span>分块模式: {kb.chunk_mode}</span>
                  )}
                  {kb.parent_retrieval_mode && (
                    <span>父文档检索: {kb.parent_retrieval_mode}</span>
                  )}
                </div>
              </div>
              <div className="flex gap-2">
                <Link to={`/kb/${kb.id}/edit`}>
                  <Button variant="outline" size="sm" disabled={deleteMutation.isPending}>
                    <Edit className="h-4 w-4 mr-1" />
                    编辑
                  </Button>
                </Link>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => handleDelete(kb.id, kb.name)}
                  disabled={deleteMutation.isPending}
                >
                  <Trash2 className="h-4 w-4 mr-1" />
                  删除
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 创建表单弹窗 */}
      <Dialog open={showCreate} onOpenChange={setShowCreate}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>新建知识库</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreate} className="space-y-4">
            <div className="space-y-2">
              <Label>
                名称 <span className="text-destructive">*</span>
              </Label>
              <Input
                value={formData.name}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, name: e.target.value }))
                }
                placeholder="输入知识库名称"
                required
              />
            </div>
            <div className="space-y-2">
              <Label>描述（可选）</Label>
              <Textarea
                value={formData.description}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, description: e.target.value }))
                }
                placeholder="输入知识库描述"
                rows={2}
              />
            </div>

            {/* V2.0 新增：分块模式 */}
            <div className="space-y-2">
              <Label>分块模式</Label>
              <ChunkModeSelect
                value={formData.chunk_mode}
                onChange={(v) =>
                  setFormData((prev) => ({ ...prev, chunk_mode: v as ChunkMode }))
                }
              />
            </div>

            {/* V2.0 新增：父文档检索配置 */}
            <ParentRetrievalConfig
              mode={formData.parent_retrieval_mode}
              expandN={formData.dynamic_expand_n}
              onModeChange={(v) =>
                setFormData((prev) => ({ ...prev, parent_retrieval_mode: v }))
              }
              onExpandNChange={(v) =>
                setFormData((prev) => ({ ...prev, dynamic_expand_n: v }))
              }
            />

            {/* V2.0 新增：默认检索策略 */}
            <div className="space-y-2">
              <Label>默认检索策略（可选）</Label>
              <RetrievalStrategySelect
                value={formData.default_retrieval_strategy}
                onChange={(v) =>
                  setFormData((prev) => ({ ...prev, default_retrieval_strategy: v as RetrievalStrategy | "" }))
                }
              />
              <p className="text-xs text-muted-foreground">
                设置后，在该知识库下问答时默认使用此策略
              </p>
            </div>

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowCreate(false)}
              >
                取消
              </Button>
              <Button type="submit" disabled={createMutation.isPending}>
                {createMutation.isPending ? "创建中..." : "创建"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}

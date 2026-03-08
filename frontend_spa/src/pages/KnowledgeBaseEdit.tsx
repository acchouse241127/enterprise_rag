import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import {
  getKnowledgeBase,
  getDocuments,
  getDocumentContent,
  updateDocumentContent,
  updateKnowledgeBase,
  rechunkDocument,
  KnowledgeBase,
  Document,
} from "@/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ChevronLeft, Save, RefreshCw, AlertCircle } from "lucide-react";
import { ChunkModeSelect } from "@/components/knowledge-base/ChunkModeSelect";
import { ParentRetrievalConfig } from "@/components/knowledge-base/ParentRetrievalConfig";
import { RetrievalStrategySelect } from "@/components/knowledge-base/RetrievalStrategySelect";

export default function KnowledgeBaseEdit() {
  const { id } = useParams<{ id: string }>();
  const kbId = Number(id);

  const [kb, setKb] = useState<KnowledgeBase | null>(null);
  const [docs, setDocs] = useState<Document[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<number | "">("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // 编辑状态
  const [content, setContent] = useState("");
  const [saving, setSaving] = useState(false);
  const [rechunking, setRechunking] = useState(false);

  // 分块设置
  const [chunkSize, setChunkSize] = useState(512);
  const [chunkOverlap, setChunkOverlap] = useState(50);
  // V2.0 新增
  const [chunkMode, setChunkMode] = useState("chinese_recursive");
  const [parentRetrievalMode, setParentRetrievalMode] = useState<"physical" | "dynamic" | "off">("dynamic");
  const [dynamicExpandN, setDynamicExpandN] = useState(2);
  const [defaultRetrievalStrategy, setDefaultRetrievalStrategy] = useState<string>("");
  const [settingsSaving, setSettingsSaving] = useState(false);

  useEffect(() => {
    loadKb();
  }, [kbId]);

  useEffect(() => {
    if (selectedDocId) {
      loadDocumentContent();
    }
  }, [selectedDocId]);

  const loadKb = async () => {
    if (!kbId) return;
    setLoading(true);
    try {
      const [kbRes, docsRes] = await Promise.all([
        getKnowledgeBase(kbId),
        getDocuments(kbId),
      ]);
      setKb(kbRes.data);
      setDocs(docsRes.data || []);
      if (kbRes.data) {
        setChunkSize(kbRes.data.chunk_size || 512);
        setChunkOverlap(kbRes.data.chunk_overlap || 50);
        setChunkMode(kbRes.data.chunk_mode || "chinese_recursive");
        setParentRetrievalMode(kbRes.data.parent_retrieval_mode || "dynamic");
        setDynamicExpandN(kbRes.data.dynamic_expand_n || 2);
        setDefaultRetrievalStrategy(kbRes.data.default_retrieval_strategy || "");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "加载失败");
    } finally {
      setLoading(false);
    }
  };

  const loadDocumentContent = async () => {
    if (!kbId || !selectedDocId) return;
    try {
      const res = await getDocumentContent(kbId, Number(selectedDocId));
      setContent(res.data?.content || "");
    } catch (e) {
      setError(e instanceof Error ? e.message : "加载文档内容失败");
    }
  };

  const handleSaveAndRevectorize = async () => {
    if (!kbId || !selectedDocId) return;
    setSaving(true);
    setError("");
    setSuccess("");
    try {
      await updateDocumentContent(kbId, Number(selectedDocId), content);
      await rechunkDocument(kbId, Number(selectedDocId));
      setSuccess("保存并重新向量化成功");
    } catch (e) {
      setError(e instanceof Error ? e.message : "操作失败");
    } finally {
      setSaving(false);
    }
  };

  const handleRechunkOnly = async () => {
    if (!kbId || !selectedDocId) return;
    setRechunking(true);
    setError("");
    setSuccess("");
    try {
      await rechunkDocument(kbId, Number(selectedDocId));
      setSuccess("重新分块成功");
    } catch (e) {
      setError(e instanceof Error ? e.message : "重新分块失败");
    } finally {
      setRechunking(false);
    }
  };

  const handleSaveSettings = async () => {
    if (!kbId) return;
    setSettingsSaving(true);
    setError("");
    setSuccess("");
    try {
      await updateKnowledgeBase(kbId, {
        chunk_size: chunkSize,
        chunk_overlap: chunkOverlap,
        chunk_mode: chunkMode as "char" | "sentence" | "token" | "chinese_recursive",
        parent_retrieval_mode: parentRetrievalMode,
        dynamic_expand_n: dynamicExpandN,
        default_retrieval_strategy: (defaultRetrievalStrategy || undefined) as "smart" | "precise" | "fast" | "deep" | undefined,
      });
      setSuccess("设置保存成功");
    } catch (e) {
      setError(e instanceof Error ? e.message : "保存失败");
    } finally {
      setSettingsSaving(false);
    }
  };

  if (loading) {
    return <p className="text-muted-foreground p-6">加载中...</p>;
  }

  if (!kb) {
    return (
      <div className="p-6">
        <p className="text-destructive">{error || "知识库不存在"}</p>
        <Link to="/kb" className="text-primary hover:underline">
          返回知识库列表
        </Link>
      </div>
    );
  }

  const vectorizedDocs = docs.filter((d) => d.status === "vectorized");

  return (
    <div>
      {/* 面包屑 */}
      <div className="flex items-center gap-2 mb-6 text-sm">
        <Link to="/kb" className="text-primary hover:underline flex items-center gap-1">
          <ChevronLeft className="h-4 w-4" />
          返回
        </Link>
        <span className="text-muted-foreground">/</span>
        <span className="text-muted-foreground">{kb.name}</span>
        <span className="text-muted-foreground">/</span>
        <span>知识库编辑</span>
      </div>

      <h1 className="text-2xl font-semibold mb-6">知识库编辑</h1>

      {error && (
        <div className="flex items-center gap-2 p-3 mb-4 bg-destructive/10 text-destructive rounded">
          <AlertCircle className="h-4 w-4" />
          {error}
        </div>
      )}
      {success && (
        <div className="p-3 mb-4 bg-green-100 text-green-800 rounded">
          {success}
        </div>
      )}

      <Tabs defaultValue="edit" className="space-y-6">
        <TabsList>
          <TabsTrigger value="edit">文档编辑</TabsTrigger>
          <TabsTrigger value="settings">检索与分块设置</TabsTrigger>
          <TabsTrigger value="batch">批量重分块</TabsTrigger>
        </TabsList>

        <TabsContent value="edit" className="space-y-4">
          {/* 选择文档 */}
          <div className="space-y-2">
            <Label>选择文档</Label>
            <Select
              value={String(selectedDocId)}
              onValueChange={(v) => setSelectedDocId(v ? Number(v) : "")}
            >
              <SelectTrigger className="max-w-md">
                <SelectValue placeholder="请选择文档" />
              </SelectTrigger>
              <SelectContent>
                {vectorizedDocs.map((doc) => (
                  <SelectItem key={doc.id} value={String(doc.id)}>
                    {doc.title || doc.filename}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {selectedDocId ? (
            <>
              {/* 编辑区域 */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">文档内容</CardTitle>
                </CardHeader>
                <CardContent>
                  <Textarea
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    className="min-h-[400px] font-mono text-sm"
                    placeholder="选择文档后显示内容..."
                  />
                </CardContent>
              </Card>

              {/* 操作按钮 */}
              <div className="flex gap-3">
                <Button onClick={handleSaveAndRevectorize} disabled={saving}>
                  <Save className="h-4 w-4 mr-1" />
                  {saving ? "保存中..." : "保存并重新向量化"}
                </Button>
                <Button variant="outline" onClick={handleRechunkOnly} disabled={rechunking}>
                  <RefreshCw className="h-4 w-4 mr-1" />
                  {rechunking ? "处理中..." : "仅重新分块"}
                </Button>
              </div>
            </>
          ) : (
            <p className="text-muted-foreground">请选择一个已向量化的文档进行编辑</p>
          )}
        </TabsContent>

        <TabsContent value="settings" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">分块设置</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>分块大小（字符数）</Label>
                  <Input
                    type="number"
                    value={chunkSize}
                    onChange={(e) => setChunkSize(Number(e.target.value))}
                    min={100}
                    max={4000}
                  />
                </div>
                <div className="space-y-2">
                  <Label>分块重叠（字符数）</Label>
                  <Input
                    type="number"
                    value={chunkOverlap}
                    onChange={(e) => setChunkOverlap(Number(e.target.value))}
                    min={0}
                    max={500}
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* V2.0 新增：分块模式 */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">分块模式</CardTitle>
            </CardHeader>
            <CardContent>
              <ChunkModeSelect value={chunkMode} onChange={setChunkMode} />
            </CardContent>
          </Card>

          {/* V2.0 新增：父文档检索配置 */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">父文档检索</CardTitle>
            </CardHeader>
            <CardContent>
              <ParentRetrievalConfig
                mode={parentRetrievalMode}
                expandN={dynamicExpandN}
                onModeChange={setParentRetrievalMode}
                onExpandNChange={setDynamicExpandN}
              />
            </CardContent>
          </Card>

          {/* V2.0 新增：默认检索策略 */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">默认检索策略</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <RetrievalStrategySelect
                value={defaultRetrievalStrategy}
                onChange={setDefaultRetrievalStrategy}
              />
              <p className="text-xs text-muted-foreground">
                设置后，在该知识库下问答时默认使用此策略。不设置则使用全局默认策略。
              </p>
            </CardContent>
          </Card>

          <p className="text-sm text-muted-foreground">
            修改设置后，新上传的文档将使用新的设置。已有文档需要手动触发重新分块。
          </p>

          <Button onClick={handleSaveSettings} disabled={settingsSaving}>
            <Save className="h-4 w-4 mr-1" />
            {settingsSaving ? "保存中..." : "保存设置"}
          </Button>
        </TabsContent>

        <TabsContent value="batch">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">批量重分块</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-muted-foreground">
                对知识库中的所有文档重新进行分块和向量化处理。
              </p>
              <p>
                当前共有 <strong>{vectorizedDocs.length}</strong> 个文档需要处理。
              </p>
              <Button variant="destructive">
                <RefreshCw className="h-4 w-4 mr-1" />
                批量重新分块
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

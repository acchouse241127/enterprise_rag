import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  getConversations,
  deleteConversation,
  shareConversation,
  exportConversationFile,
  Conversation,
} from "@/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Trash2, Share2, Download, MessageSquare, Search } from "lucide-react";

export default function Conversations() {
  // conversationId 参数保留用于后续扩展（查看对话详情功能）
  const params = useParams<{ id: string }>();
  void params.id; // 明确标记为有意忽略
  
  const [list, setList] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [shareUrl, setShareUrl] = useState("");
  const [shareDialogOpen, setShareDialogOpen] = useState(false);

  const loadList = () => {
    setLoading(true);
    getConversations()
      .then((res) => setList(Array.isArray(res) ? res : []))
      .catch((e) => setError(e instanceof Error ? e.message : "加载失败"))
      .finally(() => setLoading(false));
  };

  useEffect(loadList, []);

  const handleDelete = async (id: number) => {
    if (!window.confirm("确定删除该对话吗？")) return;
    try {
      await deleteConversation(id);
      loadList();
    } catch (e) {
      setError(e instanceof Error ? e.message : "删除失败");
    }
  };

  const handleShare = async (id: number) => {
    try {
      const res = await shareConversation(id);
      const shareToken = res.data.share_token;
      const url = `${window.location.origin}/share/${shareToken}`;
      setShareUrl(url);
      setShareDialogOpen(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "分享失败");
    }
  };

  const handleExport = async (id: number, format: "markdown" | "pdf" | "docx") => {
    try {
      const { blob, filename } = await exportConversationFile(id, format);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError(e instanceof Error ? e.message : "导出失败");
    }
  };

  const filteredList = list.filter(
    (c) =>
      c.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.conversation_id.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const copyShareUrl = () => {
    navigator.clipboard.writeText(shareUrl);
  };

  if (loading) return <p className="text-muted-foreground">加载中...</p>;

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-semibold">对话记录</h1>
      </div>

      {error && (
        <p className="text-destructive mb-4 p-3 bg-destructive/10 rounded">
          {error}
        </p>
      )}

      {/* 搜索框 */}
      <div className="mb-6">
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            type="text"
            placeholder="搜索对话..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      {filteredList.length === 0 ? (
        <p className="text-muted-foreground">
          {searchQuery ? "未找到匹配的对话" : "暂无对话记录"}
        </p>
      ) : (
        <div className="space-y-3">
          {filteredList.map((conv) => (
            <Card key={conv.id} className="hover:shadow-sm transition-shadow">
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <MessageSquare className="h-4 w-4 text-muted-foreground" />
                      <h3 className="font-medium">
                        {conv.title || `对话 #${conv.conversation_id.slice(0, 8)}`}
                      </h3>
                    </div>
                    <div className="mt-1 text-sm text-muted-foreground space-y-1">
                      <p>
                        创建于: {new Date(conv.created_at).toLocaleString("zh-CN")}
                      </p>
                      {conv.updated_at && (
                        <p>
                          更新于: {new Date(conv.updated_at).toLocaleString("zh-CN")}
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Link to={`/conversations/${conv.id}`}>
                      <Button variant="outline" size="sm">
                        查看
                      </Button>
                    </Link>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleShare(conv.id)}
                    >
                      <Share2 className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleExport(conv.id, "markdown")}
                    >
                      <Download className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => handleDelete(conv.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* 分享链接弹窗 */}
      <Dialog open={shareDialogOpen} onOpenChange={setShareDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>分享链接</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <Input value={shareUrl} readOnly />
            <Button onClick={copyShareUrl} className="w-full">
              复制链接
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

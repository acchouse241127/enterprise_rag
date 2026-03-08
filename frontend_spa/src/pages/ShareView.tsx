import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getSharedConversation, SharedConversation } from "@/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { MessageSquare, Calendar, Database, AlertCircle } from "lucide-react";

export default function ShareView() {
  const { shareId } = useParams<{ shareId: string }>();
  const [conversation, setConversation] = useState<SharedConversation | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!shareId) return;
    setLoading(true);
    getSharedConversation(shareId)
      .then((res) => setConversation(res.data))
      .catch((e) => setError(e instanceof Error ? e.message : "加载失败"))
      .finally(() => setLoading(false));
  }, [shareId]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-muted/30">
        <p className="text-muted-foreground">加载中...</p>
      </div>
    );
  }

  if (error || !conversation) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-muted/30 p-4">
        <Card className="max-w-md">
          <CardContent className="pt-6 text-center">
            <AlertCircle className="h-12 w-12 mx-auto text-destructive mb-4" />
            <h2 className="text-xl font-semibold mb-2">无法加载对话</h2>
            <p className="text-muted-foreground">
              {error || "该对话可能已被删除或链接已失效"}
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-muted/30 p-4">
      <div className="max-w-3xl mx-auto">
        <Card>
          <CardHeader>
            <div className="flex items-start justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <MessageSquare className="h-5 w-5" />
                  {conversation.title || "共享对话"}
                </CardTitle>
                <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
                  {conversation.knowledge_base_name && (
                    <span className="flex items-center gap-1">
                      <Database className="h-4 w-4" />
                      {conversation.knowledge_base_name}
                    </span>
                  )}
                  <span className="flex items-center gap-1">
                    <Calendar className="h-4 w-4" />
                    {new Date(conversation.created_at).toLocaleString("zh-CN")}
                  </span>
                </div>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {conversation.messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                    msg.role === "user"
                      ? "bg-blue-50 rounded-br-sm"
                      : "bg-white border rounded-bl-sm"
                  }`}
                >
                  <div className="text-xs text-muted-foreground mb-2">
                    {msg.role === "user" ? "用户" : "助手"}
                  </div>
                  <div className="whitespace-pre-wrap leading-relaxed text-sm">
                    {msg.content}
                  </div>
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="mt-3 space-y-1">
                      <p className="text-xs text-muted-foreground">引用来源</p>
                      {msg.citations.map((cite, cidx) => (
                        <div
                          key={cidx}
                          className="p-2 bg-muted rounded text-xs"
                        >
                          [{cite.id}] {cite.filename || `文档 ${cite.document_id}`}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        <p className="text-center text-muted-foreground text-sm mt-4">
          由 Enterprise RAG 生成
        </p>
      </div>
    </div>
  );
}

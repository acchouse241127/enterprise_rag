import { useEffect, useState, useRef } from "react";
import { useQAStore } from "@/stores/qa-store";
import { useStreamQA } from "@/hooks/use-stream-qa";
import {
  getKnowledgeBases,
  getStrategies,
  KnowledgeBase,
  Strategy,
} from "@/api";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { TooltipProvider } from "@/components/ui/tooltip";
import { RefreshCw } from "lucide-react";
import {
  ChatMessage,
  ChatInput,
  QASettingsSheet,
  type QASettings,
} from "@/components/qa";
import type { Citation } from "@/api/types";

export default function QA() {
  const [kbs, setKbs] = useState<KnowledgeBase[]>([]);
  const [kbId, setKbId] = useState<number | "">("");
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [showSettings, setShowSettings] = useState(false);
  const [settings, setSettings] = useState<QASettings>({
    strategy: "",
    retrievalMode: "hybrid",
    topK: 5,
    systemPromptVersion: "C",
    queryExpansionMode: "rule",
  });

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { ask, stop, streaming, error } = useStreamQA();
  const {
    messages,
    currentAnswer,
    currentCitations,
    setFeedback,
    resetChat,
  } = useQAStore();

  // 当前正在生成的消息引用
  const currentAnswerRef = useRef("");
  const currentCitationsRef = useRef<Citation[]>([]);

  useEffect(() => {
    getKnowledgeBases()
      .then((res) => {
        setKbs(res.data || []);
        if (res.data && res.data.length > 0 && !kbId) {
          setKbId(res.data[0].id);
        }
      })
      .catch(() => {});

    getStrategies()
      .then((res) => setStrategies(res.data || []))
      .catch(() => {});
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, currentAnswer]);

  useEffect(() => {
    currentAnswerRef.current = currentAnswer;
    currentCitationsRef.current = currentCitations;
  }, [currentAnswer, currentCitations]);

  const handleSend = (question: string) => {
    if (!kbId) return;

    ask(question, Number(kbId), {
      strategy: settings.strategy || undefined,
      topK: settings.topK,
      systemPromptVersion: settings.systemPromptVersion,
      queryExpansionMode: settings.queryExpansionMode,
      retrievalMode: settings.retrievalMode,
    });
  };

  const handleNewChat = () => {
    resetChat();
  };

  return (
    <TooltipProvider>
      <div className="flex flex-col h-[calc(100vh-56px-48px)]">
        {/* 头部 */}
        <div className="flex justify-between items-center mb-4">
          <h1 className="text-2xl font-semibold">智能问答</h1>
          <div className="flex items-center gap-4">
            <Select
              value={String(kbId)}
              onValueChange={(v) => setKbId(v ? Number(v) : "")}
            >
              <SelectTrigger className="w-48">
                <SelectValue placeholder="选择知识库" />
              </SelectTrigger>
              <SelectContent>
                {kbs.map((kb) => (
                  <SelectItem key={kb.id} value={String(kb.id)}>
                    {kb.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button variant="secondary" onClick={handleNewChat}>
              <RefreshCw className="h-4 w-4 mr-1" />
              新对话
            </Button>
          </div>
        </div>

        {/* 对话区域 */}
        <div className="flex-1 overflow-auto p-4 bg-muted/30 rounded-lg mb-4">
          {messages.length === 0 && !currentAnswer ? (
            <div className="text-center py-12">
              <div className="text-5xl mb-4">💬</div>
              <p className="text-muted-foreground">开始提问吧！选择知识库后输入问题。</p>
            </div>
          ) : (
            <>
              {messages.map((msg) => (
                <ChatMessage
                  key={msg.id}
                  message={msg}
                  onFeedback={setFeedback}
                />
              ))}

              {/* 正在生成的内容 */}
              {currentAnswer && (
                <div className="flex mb-6 justify-start">
                  <div className="max-w-[70%] rounded-2xl px-4 py-3 shadow-sm bg-white rounded-bl-sm border">
                    <div className="text-xs text-muted-foreground mb-2">助手</div>
                    <div className="whitespace-pre-wrap leading-relaxed text-sm">
                      {currentAnswer}
                      {streaming && <span className="animate-blink">|</span>}
                    </div>
                    {currentCitations.length > 0 && (
                      <div className="mt-3 space-y-1">
                        <p className="text-xs text-muted-foreground">引用来源</p>
                        {currentCitations.map((cite, idx) => (
                          <div
                            key={idx}
                            className="p-2 bg-muted rounded text-xs"
                          >
                            [{cite.id}] {cite.filename || `文档 ${cite.document_id}`}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* 错误提示 */}
        {error && (
          <p className="text-destructive mb-4 p-3 bg-destructive/10 rounded">
            {error}
          </p>
        )}

        {/* 输入区域 */}
        <div className="bg-card rounded-lg p-4 shadow-sm border">
          <ChatInput
            onSend={handleSend}
            onStop={stop}
            onToggleSettings={() => setShowSettings(!showSettings)}
            disabled={!kbId}
            streaming={streaming}
          />

          {/* 设置面板 */}
          {showSettings && (
            <div className="mt-4 pt-4 border-t">
              <QASettingsSheet
                settings={settings}
                onChange={setSettings}
                strategies={strategies}
                inline
              />
            </div>
          )}
        </div>
      </div>
    </TooltipProvider>
  );
}

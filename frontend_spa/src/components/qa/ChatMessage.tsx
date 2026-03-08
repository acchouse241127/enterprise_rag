import { cn } from "@/lib/utils";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ConfidenceBadge } from "./ConfidenceBadge";
import { RefusalAlert } from "./RefusalAlert";
import { FeedbackPanel } from "./FeedbackPanel";
import { CitationPopover } from "./CitationPopover";
import type { Message } from "@/stores/qa-store";
import type { Citation } from "@/api/types";

interface ChatMessageProps {
  message: Message;
  onFeedback: (messageId: string, feedback: "thumbs_up" | "thumbs_down") => void;
}

// 渲染答案中的引用标注
function renderAnswerWithCitations(
  text: string,
  citations: Citation[]
): React.ReactNode {
  if (!text) return null;
  const parts = text.split(/\[ID:(\d+)\]/g);
  return parts.map((part, idx) => {
    if (idx % 2 === 1) {
      const citeId = parseInt(part, 10);
      const cite = citations.find((c) => c.id === citeId);
      return (
        <span
          key={idx}
          className="text-primary font-medium cursor-pointer hover:underline"
          title={cite?.snippet || cite?.reason || `引用 ${citeId}`}
        >
          [{citeId}]
        </span>
      );
    }
    return part;
  });
}

export function ChatMessage({ message, onFeedback }: ChatMessageProps) {
  const isUser = message.role === "user";

  // 拒答消息特殊处理
  if (message.refused) {
    return (
      <RefusalAlert reason={message.refused.reason} message={message.refused.message} />
    );
  }

  return (
    <TooltipProvider>
      <div className={cn("flex mb-6", isUser ? "justify-end" : "justify-start")}>
        <div
          className={cn(
            "max-w-[70%] rounded-2xl px-4 py-3 shadow-sm",
            isUser
              ? "bg-blue-50 rounded-br-sm"
              : "bg-white rounded-bl-sm border"
          )}
        >
          {/* 角色标签 */}
          <div className="text-xs text-muted-foreground mb-2">
            {isUser ? "用户" : "助手"}
          </div>

          {/* 消息内容 */}
          <div className="whitespace-pre-wrap leading-relaxed text-sm">
            {isUser
              ? message.content
              : renderAnswerWithCitations(message.content, message.citations || [])}
          </div>

          {/* 引用来源 */}
          {!isUser && message.citations && message.citations.length > 0 && (
            <div className="mt-3 space-y-1">
              <p className="text-xs text-muted-foreground">引用来源</p>
              {message.citations.map((cite, idx) => (
                <CitationPopover key={idx} citation={cite} />
              ))}
            </div>
          )}

          {/* 置信度标签 - V2.0 新增 */}
          {!isUser && message.verification && (
            <div className="mt-3">
              <ConfidenceBadge
                level={message.verification.confidence_level}
                score={message.verification.confidence_score}
              />
            </div>
          )}

          {/* 反馈按钮 */}
          {!isUser && message.retrievalLogId && (
            <FeedbackPanel
              retrievalLogId={message.retrievalLogId}
              currentFeedback={message.feedback}
              onFeedbackSubmitted={(fb) => onFeedback(message.id, fb)}
            />
          )}
        </div>
      </div>
    </TooltipProvider>
  );
}

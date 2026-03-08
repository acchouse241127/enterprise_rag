import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { ThumbsUp, ThumbsDown } from "lucide-react";
import { submitFeedback } from "@/api/feedback";

interface FeedbackPanelProps {
  retrievalLogId: number;
  currentFeedback?: "thumbs_up" | "thumbs_down";
  onFeedbackSubmitted: (feedback: "thumbs_up" | "thumbs_down") => void;
}

export function FeedbackPanel({
  retrievalLogId,
  currentFeedback,
  onFeedbackSubmitted,
}: FeedbackPanelProps) {
  const [reason, setReason] = useState("");
  const [reasonOpen, setReasonOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleThumbsUp = async () => {
    setLoading(true);
    try {
      await submitFeedback(retrievalLogId, "thumbs_up");
      onFeedbackSubmitted("thumbs_up");
    } catch (e) {
      console.error("Feedback error:", e);
    } finally {
      setLoading(false);
    }
  };

  const handleThumbsDown = async () => {
    setLoading(true);
    try {
      await submitFeedback(retrievalLogId, "thumbs_down", reason || undefined);
      onFeedbackSubmitted("thumbs_down");
      setReasonOpen(false);
      setReason("");
    } catch (e) {
      console.error("Feedback error:", e);
    } finally {
      setLoading(false);
    }
  };

  if (currentFeedback) {
    return (
      <span className="text-xs text-muted-foreground">
        {currentFeedback === "thumbs_up" ? "👍 已标记为有帮助" : "👎 已标记为无帮助"}
      </span>
    );
  }

  return (
    <div className="flex items-center gap-1 mt-2">
      <Button
        variant="ghost"
        size="sm"
        className="h-7 px-2"
        onClick={handleThumbsUp}
        disabled={loading}
      >
        <ThumbsUp className="h-3.5 w-3.5" />
      </Button>
      <Popover open={reasonOpen} onOpenChange={setReasonOpen}>
        <PopoverTrigger asChild>
          <Button
            variant="ghost"
            size="sm"
            className="h-7 px-2"
            disabled={loading}
          >
            <ThumbsDown className="h-3.5 w-3.5" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-72">
          <div className="space-y-2">
            <p className="text-sm font-medium">请告诉我们哪里不好</p>
            <Textarea
              placeholder="可选：描述具体问题..."
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="min-h-[60px]"
            />
            <Button
              size="sm"
              className="w-full"
              onClick={handleThumbsDown}
              disabled={loading}
            >
              提交反馈
            </Button>
          </div>
        </PopoverContent>
      </Popover>
    </div>
  );
}

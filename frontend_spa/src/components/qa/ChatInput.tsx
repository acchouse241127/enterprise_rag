import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Send, Square, Settings } from "lucide-react";

interface ChatInputProps {
  onSend: (message: string) => void;
  onStop: () => void;
  onToggleSettings: () => void;
  disabled: boolean;
  streaming: boolean;
}

export function ChatInput({
  onSend,
  onStop,
  onToggleSettings,
  disabled,
  streaming,
}: ChatInputProps) {
  const [value, setValue] = useState("");

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (value.trim() && !disabled && !streaming) {
        onSend(value.trim());
        setValue("");
      }
    }
  };

  const handleSend = () => {
    if (value.trim() && !disabled && !streaming) {
      onSend(value.trim());
      setValue("");
    }
  };

  return (
    <div className="flex gap-2 items-end">
      <Button
        variant="outline"
        size="icon"
        onClick={onToggleSettings}
        title="检索设置"
      >
        <Settings className="h-4 w-4" />
      </Button>
      <Textarea
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="输入问题..."
        rows={2}
        className="flex-1 resize-none"
      />
      {streaming ? (
        <Button variant="destructive" onClick={onStop}>
          <Square className="h-4 w-4 mr-1" />
          停止
        </Button>
      ) : (
        <Button onClick={handleSend} disabled={!value.trim() || disabled} title={disabled ? "请先选择知识库" : "发送"}>
          <Send className="h-4 w-4 mr-1" />
          发送
        </Button>
      )}
    </div>
  );
}

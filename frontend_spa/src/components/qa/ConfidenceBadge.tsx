import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { ShieldCheck, ShieldAlert, ShieldX, ShieldOff } from "lucide-react";

interface ConfidenceBadgeProps {
  level: "high" | "medium" | "low" | "refused";
  score?: number;
}

const CONFIG = {
  high: {
    icon: ShieldCheck,
    className: "bg-green-100 text-green-800 border-green-200",
    text: "高置信度",
  },
  medium: {
    icon: ShieldAlert,
    className: "bg-yellow-100 text-yellow-800 border-yellow-200",
    text: "中置信度",
  },
  low: {
    icon: ShieldX,
    className: "bg-red-100 text-red-800 border-red-200",
    text: "低置信度",
  },
  refused: {
    icon: ShieldOff,
    className: "bg-gray-100 text-gray-600 border-gray-200",
    text: "拒绝回答",
  },
} as const;

export function ConfidenceBadge({ level, score }: ConfidenceBadgeProps) {
  const config = CONFIG[level];
  const Icon = config.icon;

  return (
    <Badge variant="outline" className={cn("gap-1 font-normal", config.className)}>
      <Icon className="h-3 w-3" />
      {config.text}
      {score !== undefined && ` ${(score * 100).toFixed(0)}%`}
    </Badge>
  );
}

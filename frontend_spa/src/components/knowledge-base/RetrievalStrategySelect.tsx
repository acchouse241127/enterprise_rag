import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface RetrievalStrategySelectProps {
  value: string | null | undefined;
  onChange: (value: string) => void;
  placeholder?: string;
}

const STRATEGIES = [
  {
    value: "smart",
    label: "智能（推荐）",
    desc: "平衡召回与精度，适合大多数场景",
  },
  {
    value: "precise",
    label: "精准",
    desc: "优先答案准确性，减少噪音",
  },
  {
    value: "fast",
    label: "快速",
    desc: "优先响应速度，适合实时场景",
  },
  {
    value: "deep",
    label: "深度",
    desc: "最大召回范围，适合探索性查询",
  },
];

export function RetrievalStrategySelect({
  value,
  onChange,
  placeholder = "使用全局默认策略（可选）"
}: RetrievalStrategySelectProps) {
  return (
    <Select value={value || ""} onValueChange={onChange}>
      <SelectTrigger className="w-full">
        <SelectValue placeholder={placeholder} />
      </SelectTrigger>
      <SelectContent>
        {STRATEGIES.map((strategy) => (
          <SelectItem key={strategy.value} value={strategy.value}>
            <div>
              <div className="font-medium">{strategy.label}</div>
              <div className="text-xs text-muted-foreground">{strategy.desc}</div>
            </div>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

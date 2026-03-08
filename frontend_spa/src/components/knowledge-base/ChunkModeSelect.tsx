import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface ChunkModeSelectProps {
  value: string;
  onChange: (value: string) => void;
}

const MODES = [
  {
    value: "chinese_recursive",
    label: "中文递归分块",
    desc: "按中文语义边界递归切分，推荐",
  },
  {
    value: "token",
    label: "Token 级分块",
    desc: "按 Token 数控制大小，贴合 LLM 上下文",
  },
  {
    value: "sentence",
    label: "句子边界分块",
    desc: "按句子和段落边界切分",
  },
  {
    value: "char",
    label: "字符滑动窗口",
    desc: "固定大小滑动窗口，V1 兼容模式",
  },
];

export function ChunkModeSelect({ value, onChange }: ChunkModeSelectProps) {
  return (
    <Select value={value} onValueChange={onChange}>
      <SelectTrigger className="w-full">
        <SelectValue placeholder="选择分块模式" />
      </SelectTrigger>
      <SelectContent>
        {MODES.map((mode) => (
          <SelectItem key={mode.value} value={mode.value}>
            <div>
              <div className="font-medium">{mode.label}</div>
              <div className="text-xs text-muted-foreground">{mode.desc}</div>
            </div>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

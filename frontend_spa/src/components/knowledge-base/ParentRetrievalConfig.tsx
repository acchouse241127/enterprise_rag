import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface ParentRetrievalConfigProps {
  mode: "physical" | "dynamic" | "off";
  expandN: number;
  onModeChange: (mode: "physical" | "dynamic" | "off") => void;
  onExpandNChange: (n: number) => void;
}

export function ParentRetrievalConfig({
  mode,
  expandN,
  onModeChange,
  onExpandNChange,
}: ParentRetrievalConfigProps) {
  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label>父文档检索模式</Label>
        <Select value={mode} onValueChange={(v) => onModeChange(v as typeof mode)}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="dynamic">
              动态扩展（推荐，无需重新索引）
            </SelectItem>
            <SelectItem value="physical">
              物理双层（精确，需重新索引）
            </SelectItem>
            <SelectItem value="off">关闭（V1 兼容模式）</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {mode === "dynamic" && (
        <div className="space-y-2">
          <Label>扩展相邻 chunk 数</Label>
          <Input
            type="number"
            min={1}
            max={5}
            value={expandN}
            onChange={(e) => onExpandNChange(Number(e.target.value))}
          />
          <p className="text-xs text-muted-foreground">
            检索命中后，向前后各扩展 N 个相邻 chunk 作为完整上下文
          </p>
        </div>
      )}
    </div>
  );
}

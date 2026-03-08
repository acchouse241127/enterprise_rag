import { useState, useEffect } from "react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Settings, ChevronDown, ChevronUp } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Strategy } from "@/api/types";

export interface QASettings {
  strategy: string;
  retrievalMode: "vector" | "bm25" | "hybrid";
  topK: number;
  systemPromptVersion: "A" | "B" | "C";
  queryExpansionMode: "rule" | "llm" | "hybrid";
}

interface QASettingsSheetProps {
  settings: QASettings;
  onChange: (settings: QASettings) => void;
  strategies: Strategy[];
  /** 为 true 时只渲染表单内容（无 Sheet、无第二个设置图标），用于页面内展开 */
  inline?: boolean;
}

// 本地兜底策略（后端未连接时使用）
const STRATEGIES_FALLBACK: Strategy[] = [
  {
    name: "smart",
    display_name: "智能（推荐）",
    description: "平衡召回与精度，适合大多数场景",
    top_k: 8,
    expansion_enabled: true,
    expansion_mode: "hybrid",
    keyword_enabled: true,
    retrieval_mode: "hybrid",
    reranker_candidate_k: 20,
  },
  {
    name: "precise",
    display_name: "精准",
    description: "优先答案准确性，减少噪音",
    top_k: 5,
    expansion_enabled: false,
    expansion_mode: "none",
    keyword_enabled: false,
    retrieval_mode: "hybrid",
    reranker_candidate_k: 12,
  },
  {
    name: "fast",
    display_name: "快速",
    description: "优先响应速度，适合实时场景",
    top_k: 4,
    expansion_enabled: false,
    expansion_mode: "none",
    keyword_enabled: false,
    retrieval_mode: "vector",
    reranker_candidate_k: 8,
  },
  {
    name: "deep",
    display_name: "深度",
    description: "最大召回范围，适合探索性查询",
    top_k: 12,
    expansion_enabled: true,
    expansion_mode: "llm",
    keyword_enabled: true,
    retrieval_mode: "hybrid",
    reranker_candidate_k: 30,
  },
  {
    name: "enhanced",
    display_name: "增强（多模态）",
    description: "多模态感知检索，针对图表、表格、图片优化",
    top_k: 8,
    expansion_enabled: true,
    expansion_mode: "hybrid",
    keyword_enabled: true,
    retrieval_mode: "hybrid",
    reranker_candidate_k: 20,
  },
];

const RETRIEVAL_MODES = [
  { value: "hybrid", label: "混合检索", desc: "BM25 + 向量检索 + RRF 融合（推荐）" },
  { value: "vector", label: "向量检索", desc: "纯语义相似度检索" },
  { value: "bm25", label: "BM25 检索", desc: "关键词全文检索" },
];

const PROMPT_VERSIONS = [
  { value: "C", label: "C 折中", desc: "平衡严谨与友好" },
  { value: "A", label: "A 严谨", desc: "更严谨的回答风格" },
  { value: "B", label: "B 友好", desc: "更友好的回答风格" },
];

const EXPANSION_MODES = [
  { value: "rule", label: "规则版", desc: "基于规则的查询扩展" },
  { value: "llm", label: "LLM 版", desc: "基于 LLM 的查询扩展" },
  { value: "hybrid", label: "混合版", desc: "规则 + LLM 结合" },
];

function QASettingsContent({
  settings,
  onChange,
  strategies,
}: Pick<QASettingsSheetProps, "settings" | "onChange" | "strategies">) {
  const [showAdvanced, setShowAdvanced] = useState(false);

  // 使用后端策略或本地兜底
  const effectiveStrategies = strategies.length > 0 ? strategies : STRATEGIES_FALLBACK;

  // 获取当前选中策略的完整配置
  const currentStrategy = effectiveStrategies.find((s) => s.name === settings.strategy) || effectiveStrategies[0];

  // 策略是否启用扩展
  const expansionEnabled = currentStrategy?.expansion_enabled ?? true;
  const strategyRetrievalMode = currentStrategy?.retrieval_mode ?? "hybrid";
  const strategyTopK = currentStrategy?.top_k ?? 8;

  // 当策略切换时，自动应用内置配置（仅当高级选项未展开时）
  useEffect(() => {
    if (!showAdvanced && currentStrategy) {
      const updates: Partial<QASettings> = {};
      
      // 如果策略禁用扩展，重置扩展模式为 rule（避免无效值）
      if (!expansionEnabled && settings.queryExpansionMode !== "rule") {
        updates.queryExpansionMode = "rule";
      }
      
      if (Object.keys(updates).length > 0) {
        onChange({ ...settings, ...updates });
      }
    }
  }, [settings.strategy, expansionEnabled, showAdvanced]);

  const update = <K extends keyof QASettings>(
    key: K,
    value: QASettings[K]
  ) => onChange({ ...settings, [key]: value });

  return (
    <div className="space-y-6">
      {/* 检索策略 - 主选项 */}
      <div className="space-y-2">
        <Label className="text-base font-medium">检索策略</Label>
        <Select
          value={settings.strategy || "smart"}
          onValueChange={(v) => update("strategy", v)}
        >
          <SelectTrigger className="h-auto">
            <SelectValue placeholder="选择策略" />
          </SelectTrigger>
          <SelectContent>
            {effectiveStrategies.map((s) => (
              <SelectItem key={s.name} value={s.name}>
                <div>
                  <div className="font-medium">{s.display_name}</div>
                  <div className="text-xs text-muted-foreground">
                    {s.description}
                  </div>
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <p className="text-xs text-muted-foreground">
          {currentStrategy?.display_name}：{currentStrategy?.description}
        </p>
      </div>

      {/* 回答风格 - 独立于策略 */}
      <div className="space-y-2">
        <Label>回答风格</Label>
        <Select
          value={settings.systemPromptVersion}
          onValueChange={(v) =>
            update("systemPromptVersion", v as QASettings["systemPromptVersion"])
          }
        >
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {PROMPT_VERSIONS.map((pv) => (
              <SelectItem key={pv.value} value={pv.value}>
                <div>
                  <div className="font-medium">{pv.label}</div>
                  <div className="text-xs text-muted-foreground">{pv.desc}</div>
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* 高级选项切换 */}
      <div className="pt-2 border-t">
        <button
          type="button"
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          {showAdvanced ? (
            <ChevronUp className="h-4 w-4" />
          ) : (
            <ChevronDown className="h-4 w-4" />
          )}
          <span>高级选项</span>
          {!showAdvanced && (
            <span className="text-xs text-muted-foreground/60">
              （自定义检索模式、扩展方式、数量）
            </span>
          )}
        </button>
      </div>

      {/* 高级选项区域 */}
      <div
        className={cn(
          "space-y-6 overflow-hidden transition-all duration-300",
          showAdvanced ? "max-h-[600px] opacity-100" : "max-h-0 opacity-0"
        )}
      >
        {/* 检索模式 */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label>检索模式</Label>
            <span className="text-xs text-muted-foreground">
              策略默认：{RETRIEVAL_MODES.find((m) => m.value === strategyRetrievalMode)?.label || "混合检索"}
            </span>
          </div>
          <Select
            value={settings.retrievalMode}
            onValueChange={(v) =>
              update("retrievalMode", v as QASettings["retrievalMode"])
            }
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {RETRIEVAL_MODES.map((mode) => (
                <SelectItem key={mode.value} value={mode.value}>
                  <div>
                    <div className="font-medium">{mode.label}</div>
                    <div className="text-xs text-muted-foreground">{mode.desc}</div>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* 查询扩展模式 */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label>查询扩展模式</Label>
            {!expansionEnabled && (
              <span className="text-xs text-amber-600 dark:text-amber-500">
                当前策略已禁用扩展
              </span>
            )}
          </div>
          <Select
            value={settings.queryExpansionMode}
            onValueChange={(v) =>
              update("queryExpansionMode", v as QASettings["queryExpansionMode"])
            }
            disabled={!expansionEnabled}
          >
            <SelectTrigger className={!expansionEnabled ? "opacity-50" : ""}>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {EXPANSION_MODES.map((em) => (
                <SelectItem key={em.value} value={em.value}>
                  <div>
                    <div className="font-medium">{em.label}</div>
                    <div className="text-xs text-muted-foreground">{em.desc}</div>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {!expansionEnabled && (
            <p className="text-xs text-muted-foreground">
              「{currentStrategy?.display_name}」策略已禁用查询扩展，选择器不可用
            </p>
          )}
        </div>

        {/* TopK */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label>检索数量（TopK）</Label>
            <span className="text-xs text-muted-foreground">
              策略默认：{strategyTopK}
            </span>
          </div>
          <Select
            value={String(settings.topK)}
            onValueChange={(v) => update("topK", Number(v))}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {[3, 5, 8, 10, 12, 15, 20].map((k) => (
                <SelectItem key={k} value={String(k)}>
                  {k} 条
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>
    </div>
  );
}

export function QASettingsSheet(props: QASettingsSheetProps) {
  const { inline = false, settings, onChange, strategies } = props;
  if (inline) {
    return <QASettingsContent settings={settings} onChange={onChange} strategies={strategies} />;
  }
  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="outline" size="icon" title="检索设置">
          <Settings className="h-4 w-4" />
        </Button>
      </SheetTrigger>
      <SheetContent>
        <SheetHeader>
          <SheetTitle>检索设置</SheetTitle>
        </SheetHeader>
        <div className="mt-6">
          <QASettingsContent settings={settings} onChange={onChange} strategies={strategies} />
        </div>
      </SheetContent>
    </Sheet>
  );
}

import { getToken, API_BASE } from "./client";
import type {
  Citation,
  StrategiesResponse,
  QueryExpansionMetaResponse,
  StreamQaOptions,
  VerificationResult,
  RefusalInfo,
} from "./types";

// ========== Strategies ==========

export async function getStrategies(): Promise<StrategiesResponse> {
  const res = await fetch(`${API_BASE}/api/qa/strategies`, {
    headers: {
      ...(getToken() ? { Authorization: `Bearer ${getToken()}` } : {}),
    },
  });
  if (!res.ok) throw new Error(res.statusText);
  return res.json();
}

export async function getExpansionMeta(): Promise<QueryExpansionMetaResponse> {
  const res = await fetch(`${API_BASE}/api/qa/expansion-meta`, {
    headers: {
      ...(getToken() ? { Authorization: `Bearer ${getToken()}` } : {}),
    },
  });
  if (!res.ok) throw new Error(res.statusText);
  return res.json();
}

// ========== Stream QA ==========

export interface StreamQaCallbacks {
  onAnswer: (text: string) => void;
  onCitations?: (citations: Citation[]) => void;
  onRetrievalLogId?: (id: number) => void;
  onError?: (msg: string) => void;
  onDone?: () => void;
  // V2.0 新增
  onVerification?: (data: VerificationResult) => void;
  onRefused?: (data: RefusalInfo) => void;
}

export function streamQa(
  kbId: number,
  question: string,
  callbacks: StreamQaCallbacks,
  options?: StreamQaOptions
): () => void {
  const token = getToken();
  const body: Record<string, unknown> = {
    knowledge_base_id: kbId,
    question,
  };

  if (options?.strategy) body.strategy = options.strategy;
  if (options?.conversationId) body.conversation_id = options.conversationId;
  if (options?.topK) body.top_k = options.topK;
  if (options?.systemPromptVersion) body.system_prompt_version = options.systemPromptVersion;
  if (options?.queryExpansionMode) body.query_expansion_mode = options.queryExpansionMode;
  if (options?.queryExpansionTarget) body.query_expansion_target = options.queryExpansionTarget;
  if (options?.queryExpansionLlm) body.query_expansion_llm = options.queryExpansionLlm;
  // V2.0 新增
  if (options?.retrievalMode) body.retrieval_mode = options.retrievalMode;

  const controller = new AbortController();

  fetch(`${API_BASE}/api/qa/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(body),
    signal: controller.signal,
  })
    .then(async (res) => {
      if (!res.ok) {
        const text = await res.text().catch(() => res.statusText);
        callbacks.onError?.(text);
        return;
      }
      const reader = res.body?.getReader();
      if (!reader) {
        callbacks.onError?.("无响应体");
        return;
      }
      const dec = new TextDecoder();
      let buf = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += dec.decode(value, { stream: true });
        const lines = buf.split("\n");
        buf = lines.pop() || "";
        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const jsonStr = line.slice(6).trim();
          if (jsonStr === "[DONE]") {
            callbacks.onDone?.();
            return;
          }
          try {
            const obj = JSON.parse(jsonStr);
            switch (obj.type) {
              case "answer":
                if (obj.delta) callbacks.onAnswer(obj.delta);
                break;
              case "citations":
                if (obj.data) callbacks.onCitations?.(obj.data);
                break;
              case "retrieval_log_id":
                if (typeof obj.data === "number") callbacks.onRetrievalLogId?.(obj.data);
                break;
              case "verification":
                // V2.0 新增：验证结果
                if (obj.data) callbacks.onVerification?.(obj.data);
                break;
              case "refused":
                // V2.0 新增：拒答事件
                if (obj.data) callbacks.onRefused?.(obj.data);
                break;
              case "error":
                callbacks.onError?.(obj.message);
                break;
            }
          } catch {
            // ignore parse errors
          }
        }
      }
    })
    .catch((e) => {
      if (e.name !== "AbortError") {
        callbacks.onError?.(e instanceof Error ? e.message : "请求失败");
      }
    });

  return () => controller.abort();
}

import { useRef, useCallback } from "react";
import { useQAStore } from "@/stores/qa-store";
import { streamQa } from "@/api/qa";
import type { StreamQaOptions } from "@/api/types";

interface UseStreamQAReturn {
  ask: (question: string, kbId: number, options?: StreamQaOptions) => void;
  stop: () => void;
  streaming: boolean;
  error: string | null;
}

export function useStreamQA(): UseStreamQAReturn {
  const abortRef = useRef<(() => void) | null>(null);

  const {
    addUserMessage,
    appendAnswer,
    setCitations,
    setRetrievalLogId,
    setVerification,
    setRefused,
    finalizeAnswer,
    setError,
    streaming,
    error,
  } = useQAStore();

  const ask = useCallback(
    (question: string, kbId: number, options?: StreamQaOptions) => {
      // 添加用户消息
      addUserMessage(question);

      // 开始流式请求
      abortRef.current = streamQa(kbId, question, {
        onAnswer: (text) => appendAnswer(text),
        onCitations: (cites) => setCitations(cites),
        onRetrievalLogId: (id) => setRetrievalLogId(id),
        onVerification: (v) => setVerification(v),
        onRefused: (info) => setRefused(info),
        onError: (msg) => setError(msg),
        onDone: () => finalizeAnswer(),
      }, options);
    },
    [addUserMessage, appendAnswer, setCitations, setRetrievalLogId, setVerification, setRefused, setError, finalizeAnswer]
  );

  const stop = useCallback(() => {
    if (abortRef.current) {
      abortRef.current();
      abortRef.current = null;
    }
    finalizeAnswer();
  }, [finalizeAnswer]);

  return { ask, stop, streaming, error };
}

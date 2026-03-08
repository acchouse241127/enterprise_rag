import { create } from "zustand";
import type { Citation } from "../api/types";

export type { Citation };

// V2.0 新增：验证结果
export interface VerificationResult {
  confidence_score: number;
  confidence_level: "high" | "medium" | "low";
  faithfulness_score: number;
  has_hallucination: boolean;
  citation_accuracy: number;
}

// V2.0 新增：拒答信息
export interface RefusalInfo {
  reason: "empty_retrieval" | "low_relevance" | "low_faithfulness";
  message: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  retrievalLogId?: number;
  feedback?: "thumbs_up" | "thumbs_down";
  // V2.0 新增
  verification?: VerificationResult;
  refused?: RefusalInfo;
}

interface QAState {
  messages: Message[];
  streaming: boolean;
  currentAnswer: string;
  currentCitations: Citation[];
  currentRetrievalLogId?: number;
  currentVerification: VerificationResult | null;
  currentRefused: RefusalInfo | null;
  conversationId: string | undefined;
  error: string | null;

  // Actions
  addUserMessage: (content: string) => string;
  appendAnswer: (delta: string) => void;
  setCitations: (citations: Citation[]) => void;
  setRetrievalLogId: (id: number) => void;
  setVerification: (v: VerificationResult) => void;
  setRefused: (info: RefusalInfo) => void;
  finalizeAnswer: () => void;
  setFeedback: (messageId: string, feedback: "thumbs_up" | "thumbs_down") => void;
  setError: (error: string | null) => void;
  setStreaming: (streaming: boolean) => void;
  resetChat: () => void;
}

export const useQAStore = create<QAState>()((set, get) => ({
  messages: [],
  streaming: false,
  currentAnswer: "",
  currentCitations: [],
  currentRetrievalLogId: undefined,
  currentVerification: null,
  currentRefused: null,
  conversationId: undefined,
  error: null,

  addUserMessage: (content: string) => {
    const id = Date.now().toString();
    set((state) => ({
      messages: [
        ...state.messages,
        { id, role: "user", content },
      ],
      streaming: true,
      currentAnswer: "",
      currentCitations: [],
      currentRetrievalLogId: undefined,
      currentVerification: null,
      currentRefused: null,
      error: null,
    }));
    return id;
  },

  appendAnswer: (delta: string) => {
    set((state) => ({
      currentAnswer: state.currentAnswer + delta,
    }));
  },

  setCitations: (citations: Citation[]) => {
    set({ currentCitations: citations });
  },

  setRetrievalLogId: (id: number) => {
    set({ currentRetrievalLogId: id });
  },

  setVerification: (v: VerificationResult) => {
    set({ currentVerification: v });
  },

  setRefused: (info: RefusalInfo) => {
    set({ currentRefused: info, streaming: false });
  },

  finalizeAnswer: () => {
    const state = get();
    const answer = state.currentAnswer.trim();

    if (state.currentRefused) {
      // 拒答消息
      const refusedMessage: Message = {
        id: `${Date.now()}_refused`,
        role: "assistant",
        content: state.currentRefused.message,
        refused: state.currentRefused,
      };
      set((state) => ({
        messages: [...state.messages, refusedMessage],
        streaming: false,
        currentAnswer: "",
        currentRefused: null,
      }));
    } else if (answer) {
      // 正常回答
      const assistantMessage: Message = {
        id: `${Date.now()}_assistant`,
        role: "assistant",
        content: answer,
        citations: state.currentCitations,
        retrievalLogId: state.currentRetrievalLogId,
        verification: state.currentVerification || undefined,
      };
      set((state) => ({
        messages: [...state.messages, assistantMessage],
        streaming: false,
        currentAnswer: "",
        currentCitations: [],
        currentRetrievalLogId: undefined,
        currentVerification: null,
      }));
    } else {
      set({ streaming: false });
    }
  },

  setFeedback: (messageId: string, feedback: "thumbs_up" | "thumbs_down") => {
    set((state) => ({
      messages: state.messages.map((msg) =>
        msg.id === messageId ? { ...msg, feedback } : msg
      ),
    }));
  },

  setError: (error: string | null) => {
    set({ error, streaming: false });
  },

  setStreaming: (streaming: boolean) => {
    set({ streaming });
  },

  resetChat: () => {
    set({
      messages: [],
      streaming: false,
      currentAnswer: "",
      currentCitations: [],
      currentRetrievalLogId: undefined,
      currentVerification: null,
      currentRefused: null,
      conversationId: undefined,
      error: null,
    });
  },
}));

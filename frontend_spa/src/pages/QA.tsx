import { useEffect, useState } from "react";
import { getKnowledgeBases } from "../api";
import { getToken } from "../auth";

export default function QA() {
  const [kbId, setKbId] = useState<number | "">("");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [kbs, setKbs] = useState<Array<{ id: number; name: string }>>([]);

  useEffect(() => {
    getKnowledgeBases()
      .then((res) => setKbs((res as { data?: Array<{ id: number; name: string }> }).data || []))
      .catch(() => {});
  }, []);

  async function handleAsk() {
    if (!kbId || !question.trim()) return;
    setErr("");
    setAnswer("");
    setLoading(true);
    const token = getToken();
    try {
      const res = await fetch(`/api/qa/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
        body: JSON.stringify({ knowledge_base_id: Number(kbId), question: question.trim() }),
      });
      if (!res.ok) throw new Error(await res.text());
      const reader = res.body?.getReader();
      const dec = new TextDecoder();
      if (!reader) throw new Error("无响应体");
      let text = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        text += dec.decode(value, { stream: true });
        const lines = text.split("\n");
        text = lines.pop() || "";
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const obj = JSON.parse(line.slice(6));
              if (obj.type === "chunk" && obj.content) setAnswer((a) => a + obj.content);
            } catch { /* ignore */ }
          }
        }
      }
    } catch (e) {
      setErr(e instanceof Error ? e.message : "请求失败");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ padding: 24, maxWidth: 720 }}>
      <h1>问答</h1>
      <div style={{ marginBottom: 12 }}>
        <select value={kbId} onChange={(e) => setKbId(e.target.value ? Number(e.target.value) : "")}>
          <option value="">选择知识库</option>
          {kbs.map((kb) => (
            <option key={kb.id} value={kb.id}>{kb.name}</option>
          ))}
        </select>
      </div>
      <div style={{ marginBottom: 12 }}>
        <textarea value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="输入问题" rows={2} style={{ width: "100%", padding: 8 }} />
      </div>
      <button type="button" onClick={handleAsk} disabled={loading}>{loading ? "生成中..." : "提问"}</button>
      {err && <p style={{ color: "red" }}>{err}</p>}
      {answer && <div style={{ marginTop: 24, whiteSpace: "pre-wrap", border: "1px solid #eee", padding: 16 }}>{answer}</div>}
    </div>
  );
}

import { useEffect, useState } from "react";
import { getKnowledgeBases } from "../api";

export default function KnowledgeBases() {
  const [list, setList] = useState<Array<{ id: number; name: string }>>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  useEffect(() => {
    getKnowledgeBases()
      .then((res) => {
        const data = res as { data?: Array<{ id: number; name: string }> };
        setList(data.data || []);
      })
      .catch((e) => setErr(e instanceof Error ? e.message : "加载失败"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p>加载中...</p>;
  if (err) return <p style={{ color: "red" }}>{err}</p>;
  return (
    <div style={{ padding: 24 }}>
      <h1>知识库列表</h1>
      <ul>
        {list.map((kb) => (
          <li key={kb.id}>{kb.name} (ID: {kb.id})</li>
        ))}
      </ul>
      {list.length === 0 && <p>暂无知识库</p>}
    </div>
  );
}
